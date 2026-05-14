import logging
import re
import xml.etree.ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

AI_KEYWORDS = ["AI", "LLM", "GPT", "생성형AI", "RAG", "인공지능", "ChatGPT"]

_GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

_DATE_PATTERN = re.compile(r'\w+, \d+ \w+ \d{4}')


def _scrape_google_news(query: str, max_count: int = 5) -> list[dict]:
    try:
        with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            resp = client.get(
                _GOOGLE_NEWS_RSS,
                params={"q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"},
            )
            resp.raise_for_status()
    except Exception as e:
        logger.warning("Google 뉴스 요청 실패 (%s): %s", query, e)
        return []

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        logger.warning("Google 뉴스 XML 파싱 실패 (%s): %s", query, e)
        return []

    articles: list[dict] = []
    items = root.findall(".//item")
    logger.info("[뉴스] Google News RSS %d건 (쿼리: %s)", len(items), query)

    for item in items[:max_count]:
        title_el = item.find("title")
        link_el = item.find("link")
        pub_date_el = item.find("pubDate")
        source_el = item.find("source")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        url = link_el.text.strip() if link_el is not None and link_el.text else ""
        date = pub_date_el.text.strip() if pub_date_el is not None and pub_date_el.text else ""
        source = source_el.text.strip() if source_el is not None and source_el.text else ""

        # Google News RSS 날짜 형식 변환 (Mon, 14 May 2026 → 2026.05.14)
        m = re.search(r'(\d+) (\w+) (\d{4})', date)
        if m:
            month_map = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                         "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                         "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
            day, mon, year = m.group(1).zfill(2), month_map.get(m.group(2), "01"), m.group(3)
            date = f"{year}.{mon}.{day}"

        # 제목에서 출처 제거 (Google RSS: "제목 - 출처" 형식)
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title = parts[0].strip()
            if not source:
                source = parts[1].strip()

        if title and url:
            articles.append({"title": title, "url": url, "date": date, "source": source})

    return articles


def fetch_articles(company_name: str) -> list[dict]:
    """회사명으로 Google News 최신 기사 최대 5건 반환."""
    return _scrape_google_news(company_name, max_count=5)


async def fetch(company_name: str) -> dict:
    """AI 관련 뉴스 요약 반환. AI 뉴스 없으면 일반 뉴스로 대체."""
    ai_articles = _scrape_google_news(f"{company_name} AI", max_count=5)
    ai_hits = [a for a in ai_articles if any(kw.lower() in a["title"].lower() for kw in AI_KEYWORDS)]

    if ai_hits:
        summary = " / ".join(a["title"] for a in ai_hits[:3])
        return {"ai_products": True, "ai_news_summary": summary}

    general = _scrape_google_news(company_name, max_count=3)
    if general:
        summary = " / ".join(a["title"] for a in general[:3])
        return {"ai_products": False, "ai_news_summary": summary}

    return {"ai_products": False, "ai_news_summary": "최근 뉴스 없음"}
