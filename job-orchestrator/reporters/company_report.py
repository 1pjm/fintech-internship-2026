import logging

import httpx

from config import config

logger = logging.getLogger(__name__)

_CIRCLE_NUMS = ["①", "②", "③", "④", "⑤"]


def build_html(report: dict, articles: list[dict]) -> str:
    company_name = report.get("company_name", "")
    company_size = report.get("company_size", "정보 없음")
    employee_count = report.get("employee_count", "정보 없음")
    founded_year = report.get("founded_year") or report.get("company_founded_year", "")
    series = report.get("company_series") or report.get("series", "정보 없음")
    investors = report.get("company_investors") or report.get("investors", [])
    if isinstance(investors, list):
        investors_str = ", ".join(investors) if investors else "정보 없음"
    else:
        investors_str = investors or "정보 없음"
    ai_news_summary = report.get("ai_news_summary", "정보 없음")
    job_title = report.get("job_title", "")
    d_day = report.get("d_day", "")
    job_url = report.get("url", "")

    news_lines = []
    for i, article in enumerate(articles[:5]):
        num = _CIRCLE_NUMS[i]
        title = article.get("title", "")
        url = article.get("url", "")
        date = article.get("date", "")
        source = article.get("source", "")
        meta = " | ".join(filter(None, [source, date]))
        if url:
            line = f'  {num} <a href="{url}">{title}</a>'
        else:
            line = f"  {num} {title}"
        if meta:
            line += f"\n      {meta}"
        news_lines.append(line)
    news_section = "\n".join(news_lines) if news_lines else "  관련 뉴스 없음"

    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🏢 기업분석 리포트",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"<b>{company_name}</b>",
        f"{company_size} | 직원 {employee_count}" + (f" | 설립 {founded_year}" if founded_year else ""),
        "",
        "📊 <b>투자 현황</b>",
        f"  투자단계: {series}",
        f"  주요투자사: {investors_str}",
        "",
        "🤖 <b>AI · 기술 동향</b>",
        f"  {ai_news_summary}",
        "",
        "📰 <b>최근 핵심 뉴스</b>",
        news_section,
    ]

    if job_title:
        d_day_str = f"D-{d_day}" if isinstance(d_day, int) and d_day >= 0 else ""
        lines += [
            "",
            "💼 <b>채용 포지션</b>",
            f"  {job_title}" + (f"  ⏰ {d_day_str}" if d_day_str else ""),
            f'  <a href="{job_url}">공고 바로가기 →</a>' if job_url else "",
        ]

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(l for l in lines if l is not None)


async def send(report: dict, articles: list[dict]) -> bool:
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return False

    text = build_html(report, articles)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=20,
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("기업분석 리포트 발송 실패 (%s): %s", report.get("company_name", ""), e)
        return False


async def analyze_company(company_name: str) -> bool:
    """enrichment + 뉴스 수집 후 리포트 발송 (공고 없이 기업만)."""
    from enricher.company_enricher import enrich
    from enricher.news_search import fetch_articles
    import asyncio

    try:
        info = await enrich(company_name)
        articles = await asyncio.get_event_loop().run_in_executor(
            None, lambda: fetch_articles(company_name)
        )
        report = {
            "company_name": company_name,
            "company_size": info.get("size", "정보 없음"),
            "employee_count": info.get("employee_count", "정보 없음"),
            "founded_year": info.get("founded_year", ""),
            "series": info.get("series", "정보 없음"),
            "investors": info.get("investors", []),
            "ai_news_summary": info.get("ai_news_summary", "정보 없음"),
        }
        return await send(report, articles)
    except Exception as e:
        logger.error("기업 단독 분석 실패 (%s): %s", company_name, e)
        return False
