import logging
import re

import httpx

from config import config

logger = logging.getLogger(__name__)

_JOBS_URL = "https://www.wanted.co.kr/api/v4/jobs"
_COMPANY_URL = "https://www.wanted.co.kr/api/v4/companies"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobCollector/1.0)",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.wanted.co.kr/",
}

_SERIES_RE = re.compile(r"(Series [A-F]|시리즈 [A-F]|Pre-[A-Z]+|Seed|IPO|상장|Pre-IPO)", re.IGNORECASE)


def _parse_employee(raw) -> tuple[str, str]:
    """(employee_count, size) 반환"""
    if not raw:
        return "", ""
    s = str(raw).replace(",", "").replace("명", "").strip()
    try:
        count = int(s)
        size = "startup" if count < 100 else ("smb" if count < 1000 else "enterprise")
        return f"{count:,}명", size
    except ValueError:
        return str(raw), ""


async def fetch(company_name: str) -> dict:
    headers = dict(_HEADERS)
    if config.WANTED_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {config.WANTED_ACCESS_TOKEN}"

    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
            # 1단계: 잡 검색으로 회사 ID 획득
            resp = await client.get(
                _JOBS_URL,
                params={"query": company_name, "country": "kr", "limit": 5},
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("Wanted jobs 검색 응답 (%s): %s", company_name, str(data)[:500])

            company_id = None
            company_data: dict = {}

            for item in data.get("data", []):
                job = item.get("job", item)
                company = job.get("company", {})
                if company_name in company.get("name", ""):
                    company_id = company.get("id")
                    company_data = company
                    break

            if not company_id:
                logger.info("Wanted 회사 ID 없음 (%s)", company_name)
                return {}

            result: dict = {}

            # 잡 응답 내 company 필드에서 직접 추출
            emp, size = _parse_employee(
                company_data.get("employees")
                or company_data.get("employee_count")
                or company_data.get("member_count")
            )
            if emp:
                result["employee_count"] = emp
                result["size"] = size

            founded = company_data.get("established_at") or company_data.get("founded_at")
            if founded:
                m = re.search(r"(19|20)\d{2}", str(founded))
                if m:
                    result["founded_year"] = int(m.group())

            # 2단계: 회사 상세 API
            try:
                detail_resp = await client.get(f"{_COMPANY_URL}/{company_id}")
                detail_resp.raise_for_status()
                detail = detail_resp.json()
                logger.info("Wanted 회사 상세 (%s): %s", company_name, str(detail)[:500])

                d = detail.get("data", detail)

                if not result.get("employee_count"):
                    emp, size = _parse_employee(
                        d.get("employees") or d.get("employee_count") or d.get("member_count")
                    )
                    if emp:
                        result["employee_count"] = emp
                        result["size"] = size

                if not result.get("founded_year"):
                    founded = d.get("established_at") or d.get("founded_at")
                    if founded:
                        m = re.search(r"(19|20)\d{2}", str(founded))
                        if m:
                            result["founded_year"] = int(m.group())

                # 투자단계
                for field in ["funding_status", "last_funding_type", "industry_name", "description"]:
                    text = str(d.get(field, ""))
                    m = _SERIES_RE.search(text)
                    if m:
                        result["series"] = m.group(1)
                        break

            except Exception as e:
                logger.warning("Wanted 회사 상세 실패 (%s id=%s): %s", company_name, company_id, e)

            logger.info("Wanted 회사정보 (%s): %s", company_name, result)
            return result

    except Exception as e:
        logger.warning("Wanted 회사정보 조회 실패 (%s): %s", company_name, e)
        return {}
