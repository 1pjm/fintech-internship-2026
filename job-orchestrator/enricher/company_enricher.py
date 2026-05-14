import json
import logging
from datetime import datetime, timezone

from db import get_cached_company, upsert_company
from enricher import wanted_company, news_search

logger = logging.getLogger(__name__)

_EMPTY = {
    "size": "정보 없음",
    "employee_count": "정보 없음",
    "founded_year": None,
    "series": "정보 없음",
    "investors": [],
    "ai_products": False,
    "ai_news_summary": "정보 없음",
}


async def enrich(company_name: str) -> dict:
    cached = await get_cached_company(company_name)
    if cached:
        cached["investors"] = json.loads(cached.get("investors", "[]"))
        cached["ai_products"] = bool(cached.get("ai_products", 0))
        return cached

    result: dict = {"company_name": company_name, **_EMPTY}

    wc_data = await wanted_company.fetch(company_name)
    result.update({k: v for k, v in wc_data.items() if v})

    news_data = await news_search.fetch(company_name)
    result.update({k: v for k, v in news_data.items() if v is not None})

    result["enriched_at"] = datetime.now(timezone.utc).isoformat()

    try:
        await upsert_company(result)
    except Exception as e:
        logger.warning("기업 캐시 저장 실패 (%s): %s", company_name, e)

    return result


async def enrich_batch(jobs: list[dict]) -> tuple[list[dict], dict]:
    stats = {"new": 0, "cached": 0, "failed": 0}
    enriched_jobs: list[dict] = []

    seen: dict[str, dict] = {}
    for job in jobs:
        company = job.get("company_name", "")
        if not company:
            job["company_info"] = {**_EMPTY, "company_name": company}
            enriched_jobs.append(job)
            continue

        if company in seen:
            job["company_info"] = seen[company]
            enriched_jobs.append(job)
            continue

        cached = await get_cached_company(company)
        if cached:
            cached["investors"] = json.loads(cached.get("investors", "[]"))
            cached["ai_products"] = bool(cached.get("ai_products", 0))
            seen[company] = cached
            job["company_info"] = cached
            enriched_jobs.append(job)
            stats["cached"] += 1
            continue

        try:
            info = await enrich(company)
            seen[company] = info
            job["company_info"] = info
            stats["new"] += 1
        except Exception as e:
            logger.error("기업 enrichment 실패 (%s): %s", company, e)
            info = {**_EMPTY, "company_name": company, "enriched_at": ""}
            seen[company] = info
            job["company_info"] = info
            stats["failed"] += 1

        enriched_jobs.append(job)

    return enriched_jobs, stats
