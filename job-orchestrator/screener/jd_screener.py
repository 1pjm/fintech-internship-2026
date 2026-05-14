import json
import logging
from datetime import datetime, timezone

import anthropic

from config import config
from db import is_job_seen, mark_job_seen, update_screen_result

logger = logging.getLogger(__name__)

_client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """당신은 채용 공고 분류 전문가입니다.
아래 기준 중 하나라도 해당하면 PASS, 아니면 FAIL을 반환하세요.
반드시 JSON으로만 응답하세요.

기준:
1. 업종이 핀테크/금융/페이먼트/인슈어테크
2. 직무명에 서비스기획/AX/AI기획 포함
3. JD 본문에 LLM/GPT/생성형AI/RAG 등 AI 기술 언급

응답 형식: {"result": "PASS"|"FAIL", "reason": "...", "matched_condition": 1|2|3|null, "ai_relevance_score": 1~5}"""


def _quick_match(job: dict) -> bool:
    """Claude API 호출 전 단순 키워드 사전 필터링."""
    text = f"{job.get('job_title', '')} {' '.join(job.get('tags', []))}".lower()
    for kw in config.JOB_KEYWORDS + config.INDUSTRY_KEYWORDS:
        if kw.lower() in text:
            return True
    return False


async def _call_claude(job: dict) -> dict:
    title = job.get("job_title", "")
    company = job.get("company_name", "")
    tags = ", ".join(job.get("tags", []))
    jd = job.get("job_description", "")[:3000]

    user_content = f"회사명: {company}\n직무명: {title}\n태그: {tags}\n\nJD:\n{jd}"

    msg = await _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.CLAUDE_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    raw = msg.content[0].text.strip()
    return json.loads(raw)


async def screen(jobs: list[dict]) -> tuple[list[dict], dict]:
    """
    Returns:
        passed: PASS 판정 공고 목록 (screen 결과 첨부)
        stats: 단계 요약 통계
    """
    passed: list[dict] = []
    stats = {"pass": 0, "fail": 0, "skip_dup": 0, "claude_error": 0, "condition": {1: 0, 2: 0, 3: 0}}

    for job in jobs:
        job_id = job.get("job_id", "")
        source = job.get("source", "")

        if await is_job_seen(job_id, source):
            stats["skip_dup"] += 1
            continue

        await mark_job_seen(job)

        if _quick_match(job):
            job["screen_result"] = {"result": "PASS", "reason": "키워드 사전매칭", "matched_condition": 2, "ai_relevance_score": 3}
            screened_at = datetime.now(timezone.utc).isoformat()
            await update_screen_result(job_id, source, "PASS", screened_at)
            stats["pass"] += 1
            cond = 2
            stats["condition"][cond] = stats["condition"].get(cond, 0) + 1
            passed.append(job)
            continue

        try:
            result = await _call_claude(job)
        except Exception as e:
            logger.error("Claude API 오류 (job_id=%s): %s", job_id, e)
            stats["claude_error"] += 1
            continue

        screened_at = datetime.now(timezone.utc).isoformat()
        await update_screen_result(job_id, source, result.get("result", "FAIL"), screened_at)

        if result.get("result") == "PASS":
            job["screen_result"] = result
            passed.append(job)
            stats["pass"] += 1
            cond = result.get("matched_condition")
            if cond in stats["condition"]:
                stats["condition"][cond] += 1
        else:
            stats["fail"] += 1

    return passed, stats
