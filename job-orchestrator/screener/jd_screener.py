import asyncio
import json
import logging
import re
from datetime import datetime, timezone

from config import config
from db import is_job_seen, mark_job_seen, update_screen_result

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 채용 공고 분류 전문가입니다.
아래 기준 중 하나라도 해당하면 PASS, 아니면 FAIL을 반환하세요.
반드시 JSON으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

기준:
1. 업종이 핀테크/금융/페이먼트/인슈어테크
2. 직무명에 서비스기획/AX/AI기획 포함
3. JD 본문에 LLM/GPT/생성형AI/RAG 등 AI 기술 언급

응답 형식: {"result": "PASS"|"FAIL", "reason": "...", "matched_condition": 1|2|3|null, "ai_relevance_score": 1~5}"""


def _extract_retry_delay(error_str: str) -> int:
    m = re.search(r'retry_delay\s*\{[^}]*seconds:\s*(\d+)', error_str)
    return int(m.group(1)) + 2 if m else 30


async def _call_gemini(content: str, system: str, max_tokens: int = 300) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    for attempt in range(3):
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=content,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        max_output_tokens=max_tokens,
                        temperature=0.1,
                    ),
                ),
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                delay = _extract_retry_delay(str(e))
                logger.warning("Gemini 429 — %ds 후 재시도 (%d/3)", delay, attempt + 1)
                await asyncio.sleep(delay)
            else:
                raise


async def _call_ai(job: dict) -> dict:
    title = job.get("job_title", "")
    company = job.get("company_name", "")
    tags = ", ".join(job.get("tags", []))
    jd = job.get("job_description", "")[:3000]
    user_content = f"회사명: {company}\n직무명: {title}\n태그: {tags}\n\nJD:\n{jd}"

    if config.GEMINI_API_KEY:
        raw = await _call_gemini(user_content, SYSTEM_PROMPT, max_tokens=300)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    elif config.ANTHROPIC_API_KEY:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return json.loads(msg.content[0].text.strip())

    else:
        raise RuntimeError("GEMINI_API_KEY 또는 ANTHROPIC_API_KEY 중 하나가 필요합니다.")


def _quick_match(job: dict) -> bool:
    text = f"{job.get('job_title', '')} {' '.join(job.get('tags', []))}".lower()
    for kw in config.JOB_KEYWORDS + config.INDUSTRY_KEYWORDS:
        if kw.lower() in text:
            return True
    return False


async def screen(jobs: list[dict]) -> tuple[list[dict], dict]:
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
            job["screen_result"] = {
                "result": "PASS",
                "reason": "키워드 사전매칭",
                "matched_condition": 2,
                "ai_relevance_score": 3,
            }
            screened_at = datetime.now(timezone.utc).isoformat()
            await update_screen_result(job_id, source, "PASS", screened_at)
            stats["pass"] += 1
            stats["condition"][2] = stats["condition"].get(2, 0) + 1
            passed.append(job)
            continue

        if not config.GEMINI_API_KEY and not config.ANTHROPIC_API_KEY:
            stats["fail"] += 1
            continue

        try:
            result = await _call_ai(job)
            await asyncio.sleep(2)  # rate limit 방지
        except Exception as e:
            logger.error("AI 스크리닝 오류 (job_id=%s): %s", job_id, e)
            stats["claude_error"] += 1
            await asyncio.sleep(5)
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
