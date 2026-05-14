import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.jobplanet.co.kr/companies/search"

EMPLOYEE_RE = re.compile(r"(\d[\d,]*)\s*명")
FOUNDED_RE = re.compile(r"(19|20)\d{2}")


async def fetch(company_name: str) -> dict:
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; JobCollector/1.0)"},
            follow_redirects=True,
        ) as client:
            resp = await client.get(SEARCH_URL, params={"query": company_name}, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            result: dict = {}

            # 직원 수
            emp_el = soup.find(string=EMPLOYEE_RE)
            if emp_el:
                m = EMPLOYEE_RE.search(emp_el)
                if m:
                    count_str = m.group(1).replace(",", "")
                    count = int(count_str)
                    result["employee_count"] = f"{count:,}명"
                    if count < 100:
                        result["size"] = "startup"
                    elif count < 1000:
                        result["size"] = "smb"
                    else:
                        result["size"] = "enterprise"

            # 설립연도
            founded_el = soup.find(string=re.compile(r"설립"))
            if founded_el:
                m = FOUNDED_RE.search(str(founded_el.parent))
                if m:
                    result["founded_year"] = int(m.group())

            return result
    except Exception as e:
        logger.warning("잡플래닛 조회 실패 (%s): %s", company_name, e)
        return {}
