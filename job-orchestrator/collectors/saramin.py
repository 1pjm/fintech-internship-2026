import asyncio
import json
import logging
from datetime import datetime

import httpx

from config import config

logger = logging.getLogger(__name__)

SEARCH_KEYWORDS = [
    "서비스 기획",
    "AI 기획",
    "AX 기획",
    "서비스 PM",
    "핀테크 기획",
]


async def _fetch_page(client: httpx.AsyncClient, keyword: str, start: int) -> dict:
    params = {
        "access-key": config.SARAMIN_API_KEY,
        "keywords": keyword,
        "fields": "expiration-date,posting-timestamp,job-title,company-name,job-category,job-type",
        "count": 110,
        "start": start,
        "sr": "directhire",
    }
    if config.CAREER_LEVEL == "entry":
        params["career_cond"] = "y"
        params["career_level"] = 0
    elif config.CAREER_LEVEL == "career":
        params["career_cond"] = "y"
        params["career_level"] = 1

    resp = await client.get(config.SARAMIN_BASE_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _parse_job(item: dict) -> dict:
    job_info = item.get("job", {})
    position = job_info.get("position", {})
    company = job_info.get("company", {}).get("detail", {})
    url_info = job_info.get("url", "")

    # 직무 설명 조합
    title = position.get("title", "")
    job_category = position.get("job-category", {}).get("name", "")
    industry = position.get("industry", {}).get("name", "")
    description = f"{title}\n{job_category}\n{industry}"

    return {
        "job_id": str(job_info.get("id", "")),
        "company_name": company.get("name", ""),
        "job_title": title,
        "job_description": description,
        "tags": [job_category, industry],
        "deadline": item.get("expiration-date", ""),
        "posted_at": item.get("posting-timestamp", ""),
        "url": url_info,
        "source": "saramin",
        "collected_at": datetime.utcnow().isoformat(),
    }


async def collect(retries: int = config.MAX_RETRIES) -> list[dict]:
    jobs: list[dict] = []
    seen_ids: set[str] = set()
    attempt = 0

    while attempt <= retries:
        try:
            async with httpx.AsyncClient() as client:
                for keyword in SEARCH_KEYWORDS:
                    start = 1
                    while True:
                        data = await _fetch_page(client, keyword, start)
                        items = data.get("jobs", {}).get("job", [])
                        if not items:
                            break
                        for item in items:
                            parsed = _parse_job(item)
                            if parsed["job_id"] and parsed["job_id"] not in seen_ids:
                                seen_ids.add(parsed["job_id"])
                                jobs.append(parsed)
                        total = int(data.get("jobs", {}).get("total", 0))
                        if start + 110 > total:
                            break
                        start += 110
            break
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 403):
                logger.warning("사람인 차단 감지: %s", e)
                raise
            logger.warning("사람인 HTTP 오류 (시도 %d/%d): %s", attempt + 1, retries, e)
        except Exception as e:
            logger.warning("사람인 수집 오류 (시도 %d/%d): %s", attempt + 1, retries, e)

        attempt += 1
        if attempt <= retries:
            wait = config.RETRY_BACKOFF[min(attempt - 1, len(config.RETRY_BACKOFF) - 1)]
            await asyncio.sleep(wait)

    _save_raw(jobs)
    return jobs


def _save_raw(jobs: list[dict]) -> None:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    path = config.REPORTS_RAW_DIR / "saramin" / f"{ts}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
