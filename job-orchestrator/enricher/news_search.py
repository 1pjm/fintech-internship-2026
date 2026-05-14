import logging
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

AI_KEYWORDS = ["AI", "LLM", "GPT", "생성형AI", "RAG", "인공지능", "ChatGPT"]
NAVER_NEWS_URL = "https://search.naver.com/search.naver"


def fetch_articles(company_name: str) -> list[dict]:
    """Scrape Naver News and return up to 5 structured articles for the given company."""
    query = company_name
    try:
        with httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "ko-KR,ko;q=0.9",
            },
            follow_redirects=True,
        ) as client:
            resp = client.get(
                NAVER_NEWS_URL,
                params={"where": "news", "query": query, "sort": "1", "ds": "", "de": ""},
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            articles: list[dict] = []
            for el in soup.select(".news_tit")[:5]:
                title = el.get_text(strip=True)
                url = el.get("href", "")

                # Find surrounding container for source and date
                container = el.find_parent("li") or el.find_parent("div")
                source = ""
                date = ""
                if container:
                    press_el = container.select_one(".press") or container.select_one(".info_group .press")
                    if press_el:
                        source = press_el.get_text(strip=True)
                    date_el = container.select_one(".date")
                    if date_el:
                        date = date_el.get_text(strip=True)

                articles.append({"title": title, "url": url, "date": date, "source": source})

            return articles
    except Exception as e:
        logger.warning("네이버 뉴스 기사 조회 실패 (%s): %s", company_name, e)
        return []


async def fetch(company_name: str) -> dict:
    query = f"{company_name} AI LLM 생성형AI"
    try:
        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "ko-KR,ko;q=0.9",
            },
            follow_redirects=True,
        ) as client:
            resp = await client.get(
                NAVER_NEWS_URL,
                params={"where": "news", "query": query, "sort": "1", "ds": "", "de": ""},
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            headlines: list[str] = []
            for el in soup.select(".news_tit")[:5]:
                text = el.get_text(strip=True)
                if any(kw.lower() in text.lower() for kw in AI_KEYWORDS):
                    headlines.append(text)

            has_ai = bool(headlines)
            summary = " / ".join(headlines[:3]) if headlines else "최근 AI 관련 뉴스 없음"
            return {"ai_products": has_ai, "ai_news_summary": summary}
    except Exception as e:
        logger.warning("네이버 뉴스 조회 실패 (%s): %s", company_name, e)
        return {"ai_products": False, "ai_news_summary": "정보 없음"}
