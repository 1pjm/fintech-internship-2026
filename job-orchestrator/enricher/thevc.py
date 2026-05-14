import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://thevc.kr/search"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://thevc.kr/",
}

_EMPLOYEE_RE = re.compile(r"(\d[\d,]+)\s*명")
_YEAR_RE = re.compile(r"(19|20)\d{2}")


async def fetch(company_name: str) -> dict:
    try:
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
            resp = await client.get(_SEARCH_URL, params={"query": company_name})
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 검색 결과 첫 번째 기업 링크 찾기
        result_link = (
            soup.select_one("a.search-result-item")
            or soup.select_one("a[href*='/companies/']")
            or soup.select_one("ul.search-list a")
            or soup.select_one(".result-item a")
        )
        if not result_link:
            return {}

        company_url = result_link.get("href", "")
        if not company_url.startswith("http"):
            company_url = "https://thevc.kr" + company_url

        # 기업 상세 페이지
        resp2 = await client.get(company_url)
        resp2.raise_for_status()
        detail = BeautifulSoup(resp2.text, "html.parser")

        result: dict = {}

        # 설립연도
        founded_el = detail.find(string=re.compile(r"설립"))
        if founded_el:
            m = _YEAR_RE.search(str(founded_el.parent))
            if m:
                result["founded_year"] = int(m.group())

        # 직원 수
        emp_el = detail.find(string=_EMPLOYEE_RE)
        if emp_el:
            m = _EMPLOYEE_RE.search(str(emp_el))
            if m:
                count = int(m.group(1).replace(",", ""))
                result["employee_count"] = f"{count:,}명"
                result["size"] = "startup" if count < 100 else ("smb" if count < 1000 else "enterprise")

        # 투자 단계
        series_el = (
            detail.select_one(".funding-stage")
            or detail.find(string=re.compile(r"Series [A-F]|시리즈 [A-F]|Pre-[A-Z]|Seed|IPO|상장"))
        )
        if series_el:
            text = series_el if isinstance(series_el, str) else series_el.get_text(strip=True)
            m = re.search(r"(Series [A-F]|시리즈 [A-F]|Pre-[A-Z]+|Seed|IPO|상장)", text, re.IGNORECASE)
            if m:
                result["series"] = m.group(1)

        # 투자사 목록
        investor_els = detail.select(".investor-name, .investor-item a, a[href*='/investors/']")
        if investor_els:
            result["investors"] = [el.get_text(strip=True) for el in investor_els[:5] if el.get_text(strip=True)]

        return result

    except Exception as e:
        logger.warning("TheVC 조회 실패 (%s): %s", company_name, e)
        return {}
