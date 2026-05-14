import json
import logging
from datetime import date, datetime, timezone

import anthropic

from config import config

logger = logging.getLogger(__name__)

_client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

JD_SUMMARY_PROMPT = """다음 채용 공고 JD를 읽고 핵심 내용을 2줄로 요약하세요. 반드시 한국어로, 줄바꿈 없이 " / "로 구분해 주세요."""


async def _summarize_jd(jd: str) -> str:
    try:
        msg = await _client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": f"{JD_SUMMARY_PROMPT}\n\nJD:\n{jd[:2000]}"}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        logger.warning("JD 요약 실패: %s", e)
        return "요약 정보 없음"


def _calc_d_day(deadline_str: str) -> tuple[str, int]:
    if not deadline_str:
        return "상시채용", 0
    try:
        if "T" in deadline_str:
            dl = datetime.fromisoformat(deadline_str.replace("Z", "+00:00")).date()
        else:
            dl = date.fromisoformat(deadline_str[:10])
        d_day = (dl - date.today()).days
        return dl.strftime("%Y-%m-%d"), d_day
    except Exception:
        return deadline_str, 0


async def build(job: dict) -> dict:
    info = job.get("company_info", {})
    screen = job.get("screen_result", {})
    deadline_str, d_day = _calc_d_day(job.get("deadline", ""))
    jd_summary = await _summarize_jd(job.get("job_description", ""))

    cond_map = {1: "업종 (핀테크/금융)", 2: "직무명 키워드", 3: "JD AI 기술 언급"}
    matched = screen.get("matched_condition")
    match_reason = cond_map.get(matched, screen.get("reason", ""))

    return {
        "job_title": job.get("job_title", ""),
        "company_name": job.get("company_name", ""),
        "company_size": info.get("size", "정보 없음"),
        "employee_count": info.get("employee_count", "정보 없음"),
        "company_series": info.get("series", "정보 없음"),
        "company_investors": info.get("investors", []),
        "ai_news_summary": info.get("ai_news_summary", "정보 없음"),
        "tags": job.get("tags", []),
        "deadline": deadline_str,
        "d_day": d_day,
        "jd_summary": jd_summary,
        "match_reason": match_reason,
        "ai_relevance_score": screen.get("ai_relevance_score", 0),
        "url": job.get("url", ""),
        "source": job.get("source", ""),
    }


async def build_batch(jobs: list[dict]) -> tuple[list[dict], int]:
    reports: list[dict] = []
    for job in jobs:
        try:
            report = await build(job)
            reports.append(report)
        except Exception as e:
            logger.error("리포트 생성 실패 (%s): %s", job.get("job_id"), e)
    return reports, len(reports)
