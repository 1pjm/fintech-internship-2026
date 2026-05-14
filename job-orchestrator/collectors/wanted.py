import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import httpx

from config import config

logger = logging.getLogger(__name__)

# 원티드 직군 카테고리 ID (기획·PM 계열)
WANTED_CATEGORY_IDS = [
    "3",   # 기획·PM
    "11",  # IT·개발 (AI/LLM 포함)
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobCollector/1.0)",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.wanted.co.kr/",
    "wantedlySessionV2": "",
}


async def _fetch_page(client: httpx.AsyncClient, category_id: str, offset: int) -> dict:
    params = {
        "job_category_id": category_id,
        "country": "kr",
        "job_sort": "job.latest_order",
        "limit": 100,
        "offset": offset,
        "tag_type_names": "",
    }
    headers = dict(HEADERS)
    if config.WANTED_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {config.WANTED_ACCESS_TOKEN}"

    resp = await client.get(config.WANTED_BASE_URL, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _parse_job(item: dict) -> dict:
    job = item.get("job", item)
    company = job.get("company", {})
    return {
        "job_id": str(job.get("id", "")),
        "company_name": company.get("name", ""),
        "job_title": job.get("position", ""),
        "job_description": job.get("detail", {}).get("intro", "") + "\n" + job.get("detail", {}).get("requirements", ""),
        "tags": [t.get("title", "") for t in job.get("tags", [])],
        "deadline": job.get("due_time", ""),
        "posted_at": job.get("open_date", ""),
        "url": f"https://www.wanted.co.kr/wd/{job.get('id', '')}",
        "source": "wanted",
        "collected_at": datetime.utcnow().isoformat(),
    }


async def collect(retries: int = config.MAX_RETRIES) -> list[dict]:
    jobs: list[dict] = []
    attempt = 0

    while attempt <= retries:
        try:
            async with httpx.AsyncClient() as client:
                for category_id in WANTED_CATEGORY_IDS:
                    offset = 0
                    while True:
                        data = await _fetch_page(client, category_id, offset)
                        items = data.get("data", [])
                        if not items:
                            break
                        for item in items:
                            jobs.append(_parse_job(item))
                        if len(items) < 100:
                            break
                        offset += 100
            break
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 403):
                logger.warning("원티드 차단 감지: %s", e)
                raise
            logger.warning("원티드 HTTP 오류 (시도 %d/%d): %s", attempt + 1, retries, e)
        except Exception as e:
            logger.warning("원티드 수집 오류 (시도 %d/%d): %s", attempt + 1, retries, e)

        attempt += 1
        if attempt <= retries:
            wait = config.RETRY_BACKOFF[min(attempt - 1, len(config.RETRY_BACKOFF) - 1)]
            await asyncio.sleep(wait)

    _save_raw(jobs)
    return jobs


def _save_raw(jobs: list[dict]) -> None:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    path = config.REPORTS_RAW_DIR / "wanted" / f"{ts}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jobs, ensure_ascii=False, indent=2))
