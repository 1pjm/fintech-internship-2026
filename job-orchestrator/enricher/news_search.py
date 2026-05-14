import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

AI_KEYWORDS = ["AI", "LLM", "GPT", "생성형AI", "RAG", "인공지능", "ChatGPT"]
NAVER_NEWS_URL = "https://search.naver.com/search.naver"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.naver.com/",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
}

_DATE_PATTERN = re.compile(r'\d{4}\.\d{2}\.\d{2}|\d+분 전|\d+시간 전|어제|오늘|\d{2}\.\d{2}')


def _scrape_naver_news(query: str, max_count: int = 5) -> list[dict]:
    try:
        with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            resp = client.get(
                NAVER_NEWS_URL,
                params={"where": "news", "query": query, "sort": "1", "ds": "", "de": ""},
            )
            resp.raise_for_status()
    except Exception as e:
        logger.warning("네이버 뉴스 요청 실패 (%s): %s", query, e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles: list[dict] = []

    # 전략 1: li.bx 중 실제 뉴스 항목만 (news_area 포함된 것)
    containers = [c for c in soup.select("li.bx") if c.select_one("div.news_area")]

    # 전략 2: ul.list_news > li
    if not containers:
        containers = soup.select("ul.list_news li")

    # 전략 3: div.news_area 직접
    if not containers:
        containers = soup.select("div.news_area")

    logger.info("[뉴스 디버그] 뉴스 컨테이너 수: %d", len(containers))

    for container in containers[:max_count]:
        news_area = container.select_one("div.news_area") or container
        # 제목 + URL
        title_el = (
            news_area.select_one("a.news_tit")
            or news_area.select_one("a[class*='tit']")
            or news_area.select_one("a[href^='http']")
        )
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        url = title_el.get("href", "")
        if not title or not url.startswith("http"):
            continue

        # 출처
        source = ""
        for sel in ["a.info.press", ".press", "a.info[href*='news']", ".info_group a"]:
            el = container.select_one(sel)
            if el:
                source = el.get_text(strip=True)
                break

        # 날짜
        date = ""
        for el in container.select("span.info, span.date, .info_group span"):
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
