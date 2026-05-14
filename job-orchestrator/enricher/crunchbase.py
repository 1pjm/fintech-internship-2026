import logging

import httpx

from config import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.crunchbase.com/api/v4"


async def fetch(company_name: str) -> dict:
    if not config.CRUNCHBASE_API_KEY:
        return {}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/searches/organizations",
                json={
                    "field_ids": ["short_description", "num_employees_enum", "founded_on", "last_funding_type", "investor_identifiers"],
                    "query": [{"type": "predicate", "field_id": "facet_ids", "operator_id": "includes", "values": ["company"]},
                              {"type": "predicate", "field_id": "name", "operator_id": "eq", "values": [company_name]}],
                    "limit": 1,
                },
                params={"user_key": config.CRUNCHBASE_API_KEY},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            entities = data.get("entities", [])
            if not entities:
                return {}
            props = entities[0].get("properties", {})
            return {
                "series": props.get("last_funding_type", ""),
                "investors": [i.get("value", "") for i in props.get("investor_identifiers", [])],
                "employee_count": props.get("num_employees_enum", ""),
                "founded_year": int(props["founded_on"]["value"][:4]) if props.get("founded_on") else None,
            }
    except Exception as e:
        logger.warning("Crunchbase 조회 실패 (%s): %s", company_name, e)
        return {}
