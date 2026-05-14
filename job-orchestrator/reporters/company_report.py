import logging

import httpx

from config import config

logger = logging.getLogger(__name__)

_CIRCLE_NUMS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]


def build_html(report: dict, articles: list[dict]) -> str:
    """Format a company analysis report in Telegram HTML style."""
    company_name = report.get("company_name", "")
    company_size = report.get("company_size", "")
    employee_count = report.get("employee_count", "")
    founded_year = report.get("founded_year", "")
    series = report.get("series", "")
    investors = report.get("investors", "")
    ai_news_summary = report.get("ai_news_summary", "")
    job_title = report.get("job_title", "")
    d_day = report.get("d_day", "")
    job_url = report.get("url", "")

    d_day_str = f"D-{d_day}" if d_day else ""

    news_lines = []
    for i, article in enumerate(articles[:5]):
        num = _CIRCLE_NUMS[i]
        title = article.get("title", "")
        url = article.get("url", "")
        date = article.get("date", "")
        if url:
            line = f'  {num} <a href="{url}">{title}</a>  {date}'.rstrip()
        else:
            line = f"  {num} {title}  {date}".rstrip()
        news_lines.append(line)
    news_section = "\n".join(news_lines) if news_lines else "  관련 뉴스 없음"

    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🏢 기업분석 리포트",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"<b>{company_name}</b>",
        f"{company_size} | 직원 {employee_count} | 설립 {founded_year}",
        "",
        "📊 <b>투자 현황</b>",
        f"  투자단계: {series}",
        f"  주요투자사: {investors}",
        "",
        "🤖 <b>AI · 기술 동향</b>",
        f"  {ai_news_summary}",
        "",
        "📰 <b>최근 핵심 뉴스</b>",
        news_section,
        "",
        "💼 <b>채용 포지션</b>",
        f"  {job_title}  ⏰ {d_day_str}",
        f'  <a href="{job_url}">공고 바로가기 →</a>',
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)


async def send(report: dict, articles: list[dict]) -> bool:
    """Send a company analysis report via Telegram."""
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        logger.warning("텔레그램 토큰 또는 채팅 ID 미설정 — 기업분석 리포트 발송 건너뜀")
        return False

    text = build_html(report, articles)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=20)
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("기업분석 리포트 발송 실패 (%s): %s", report.get("company_name", ""), e)
        return False
