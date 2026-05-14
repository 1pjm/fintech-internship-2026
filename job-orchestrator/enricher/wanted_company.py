import logging
import re

import httpx

from config import config

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.wanted.co.kr/api/v4/companies"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobCollector/1.0)",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.wanted.co.kr/",
}

_SERIES_RE = re.compile(r"(Series [A-F]|시리즈 [A-F]|Pre-[A-Z]+|Seed|IPO|상장|Pre-IPO)", re.IGNORECASE)


async def fetch(company_name: str) -> dict:
    try:
        headers = dict(_HEADERS)
        if config.WANTED_ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {config.WANTED_ACCESS_TOKEN}"

        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
            # 회사 검색
            resp = await client.get(_SEARCH_URL, params={"query": company_name, "limit": 1})
            resp.raise_for_status()
            data = resp.json()

            companies = data.get("data", [])
            if not companies:
                return {}

            company = companies[0]
            company_id = company.get("id")
            if not company_id:
                return {}

            # 회사 상세 조회
            detail_resp = await client.get(f"{_SEARCH_URL}/{company_id}")
            detail_resp.raise_for_status()
            detail = detail_resp.json()

        result: dict = {}
        d = detail.get("data", detail)

        # 직원 수
        emp = d.get("employees") or d.get("employee_count") or d.get("member_count")
        if emp:
            try:
                count = int(str(emp).replace(",", "").replace("명", "").strip())
                result["employee_count"] = f"{count:,}명"
                result["size"] = "startup" if count < 100 else ("smb" if count < 1000 else "enterprise")
            except ValueError:
                result["employee_count"] = str(emp)

        # 설립연도
        founded = d.get("founded_at") or d.get("established_at")
        if founded:
            m = re.search(r"(19|20)\d{2}", str(founded))
            if m:
                result["founded_year"] = int(m.group())

        # 투자단계
        industry = d.get("industry_name", "") or ""
        if _SERIES_RE.search(industry):
            result["series"] = _SERIES_RE.search(industry).group(1)

        return result

    except Exception as e:
        logger.warning("Wanted 회사정보 조회 실패 (%s): %s", company_name, e)
        return {}
