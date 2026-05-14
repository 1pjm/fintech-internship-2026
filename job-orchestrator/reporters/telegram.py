import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from config import config

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"


def _format_message(report: dict, today_count: int, total_count: int) -> str:
    investors = ", ".join(report.get("company_investors", [])) or "정보 없음"
    tags = " ".join(f"#{t.replace(' ', '')}" for t in report.get("tags", []) if t)
    d_day = report.get("d_day", 0)
    d_day_str = f"D-{d_day}" if d_day > 0 else ("D-Day" if d_day == 0 else "마감")
    score = report.get("ai_relevance_score", 0)
    stars = "⭐" * int(score) if score else ""

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>신규 공고 감지</b>\n\n"
        f"🏢 <b>{report['company_name']}</b>\n"
        f"   📊 규모: {report['company_size']} · 직원 {report['employee_count']}\n"
        f"   💰 투자: {report['company_series']} · {investors}\n"
        f"   🤖 AI동향: {report['ai_news_summary']}\n\n"
        f"📋 <b>{report['job_title']}</b>\n"
        f"🏷️ {tags}\n"
        f"⏰ 마감 {d_day_str} | {report['deadline']}\n\n"
        f"🔍 <b>JD 핵심 요약</b>\n"
        f"   {report['jd_summary']}\n\n"
        f"⭐ 매칭 사유: {report['match_reason']} {stars}\n"
        f"🔗 <a href=\"{report['url']}\">공고 바로가기</a>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📊 오늘 신규 <b>{today_count}</b>건 | 누적 <b>{total_count}</b>건"
    )


async def _send_message(text: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": config.TELEGRAM_CHAT_ID,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("텔레그램 발송 실패: %s", e)
        return False


async def _send_alert(text: str) -> None:
    await _send_message(f"⚠️ <b>[시스템 알림]</b>\n{text}")


def _save_unsent(report: dict) -> None:
    config.REPORTS_UNSENT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = config.REPORTS_UNSENT_DIR / f"{ts}_{report.get('company_name', 'unknown')}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2))


async def send_reports(reports: list[dict]) -> dict:
    stats = {"sent": 0, "failed": 0}
    total_count = _get_total_count()

    for i, report in enumerate(reports):
        msg = _format_message(report, len(reports), total_count + i + 1)
        ok = await _send_message(msg)
        if ok:
            stats["sent"] += 1
        else:
            stats["failed"] += 1
            _save_unsent(report)

    return stats


async def retry_unsent() -> int:
    unsent_dir = config.REPORTS_UNSENT_DIR
    if not unsent_dir.exists():
        return 0

    sent = 0
    for f in sorted(unsent_dir.glob("*.json")):
        try:
            report = json.loads(f.read_text())
            msg = _format_message(report, 1, _get_total_count())
            ok = await _send_message(msg)
            if ok:
                f.unlink()
                sent += 1
        except Exception as e:
            logger.warning("미발송 재시도 실패 (%s): %s", f.name, e)
    return sent


def _get_total_count() -> int:
    filtered_dir = config.REPORTS_FILTERED_DIR
    if not filtered_dir.exists():
        return 0
    count = 0
    for f in filtered_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            count += len(data) if isinstance(data, list) else 1
        except Exception:
            pass
    return count


async def send_block_alert(source: str) -> None:
    await _send_alert(f"{source} 수집 차단 감지. 해당 소스 6시간 일시 중단.")
