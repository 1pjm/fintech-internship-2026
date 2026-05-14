import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

AI_KEYWORDS = ["AI", "LLM", "GPT", "생성형AI", "RAG", "인공지능", "ChatGPT"]

# 모바일 네이버 뉴스 검색 (정적 HTML에 뉴스 포함)
_MOBILE_URL = "https://m.search.naver.com/search.naver"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://m.naver.com/",
}

_DATE_PATTERN = re.compile(r'\d{4}\.\d{2}\.\d{2}|\d+분 전|\d+시간 전|어제|오늘|\d{2}\.\d{2}')


def _scrape_naver_news(query: str, max_count: int = 5) -> list[dict]:
    try:
        with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            resp = client.get(
                _MOBILE_URL,
                params={"where": "m_news", "query": query, "sort": "1"},
            )
            resp.raise_for_status()
    except Exception as e:
        logger.warning("네이버 뉴스 요청 실패 (%s): %s", query, e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles: list[dict] = []

    # 모바일 뉴스 구조: ul.list_news > li 또는 div.news_wrap
    containers = soup.select("ul.list_news > li")

    if not containers:
        containers = soup.select("div.news_wrap")

    if not containers:
        # 모바일 대체 구조
        containers = soup.select("li.bx")
        containers = [c for c in containers if c.select_one("a[href^='http']")]

    logger.info("[뉴스] 컨테이너 %d개 (쿼리: %s)", len(containers), query)

    for container in containers[:max_count]:
        # 제목 + URL
        title_el = (
            container.select_one("a.news_tit")
            or container.select_one("a.api_txt_lines")
            or container.select_one("a[class*='tit']")
            or container.select_one("a[href^='http']")
        )
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        url = title_el.get("href", "")
        if not title or not url.startswith("http"):
            continue

        # 출처
        source = ""
        for sel in ["a.info.press", ".press", ".source", "cite", ".info_group a", "a.info"]:
            el = container.select_one(sel)
            if el:
                source = el.get_text(strip=True)
                break

        # 날짜
        date = ""
        for el in container.select("span.info, span.date, span.time, .info_group span, span"):
            candidate = el.get_text(strip=True)
            if _DATE_PATTERN.search(candidate):
                date = candidate
                break

        articles.append({"title": title, "url": url, "date": date, "source": source})

    return articles


def fetch_articles(company_name: str) -> list[dict]:
    """회사명으로 네이버 뉴스 최신 기사 최대 5건 반환."""
    return _scrape_naver_news(company_name, max_count=5)


async def fetch(company_name: str) -> dict:
    """AI 관련 뉴스 요약 반환. AI 뉴스 없으면 일반 뉴스로 대체."""
    ai_articles = _scrape_naver_news(f"{company_name} AI", max_count=5)
    ai_hits = [a for a in ai_articles if any(kw.lower() in a["title"].lower() for kw in AI_KEYWORDS)]

    if ai_hits:
        summary = " / ".join(a["title"] for a in ai_hits[:3])
        return {"ai_products": True, "ai_news_summary": summary}

    general = _scrape_naver_news(company_name, max_count=3)
    if general:
        summary = " / ".join(a["title"] for a in general[:3])
        return {"ai_products": False, "ai_news_summary": summary}

    return {"ai_products": False, "ai_news_summary": "최근 뉴스 없음"}
