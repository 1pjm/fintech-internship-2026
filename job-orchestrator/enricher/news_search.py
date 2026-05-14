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

    # 전략 1: li.bx 컨테이너 기반 (최신 Naver 구조)
    containers = soup.select("li.bx")
    logger.info("[뉴스 디버그] li.bx: %d개", len(containers))

    # 전략 2: ul.list_news > li
    if not containers:
        containers = soup.select("ul.list_news li")
        logger.info("[뉴스 디버그] ul.list_news li: %d개", len(containers))

    # 전략 3: div.news_area 직접
    if not containers:
        containers = soup.select("div.news_area")
        logger.info("[뉴스 디버그] div.news_area: %d개", len(containers))

    # 전략 4: 응답 HTML 구조 샘플 출력
    if not containers:
        body = soup.find("body")
        if body:
            logger.warning("[뉴스 디버그] 컨테이너 없음 — body 첫 500자: %s", body.get_text()[:500])
        # 전략 4: 모든 <a> 중 뉴스처럼 보이는 것 추출
        all_links = soup.select("a[href^='https://n.news.naver.com'], a[href^='https://news.naver.com']")
        logger.info("[뉴스 디버그] 네이버 뉴스 링크 직접: %d개", len(all_links))
        for a in all_links[:max_count]:
            title = a.get_text(strip=True)
            url = a.get("href", "")
            if title and url:
                articles.append({"title": title, "url": url, "date": "", "source": ""})
        return articles

    # 첫 번째 컨테이너 내부 a 태그 구조 디버그
    if containers:
        first = containers[0]
        for a in first.find_all("a", href=True)[:5]:
            logger.info("[뉴스 디버그] a태그 class=%s href=%s", a.get("class"), a.get("href", "")[:80])

    for container in containers[:max_count]:
        # 제목 + URL
        title_el = (
            container.select_one("a.news_tit")
            or container.select_one("a[class*='tit']")
            or container.select_one("div.news_area a[href^='http']")
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
