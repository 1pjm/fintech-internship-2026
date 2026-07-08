"""
인천/광주/전남이 왜 계속 0건으로 나오는지 확인하기 위해, API 응답을 가공 없이 그대로 찍어보는 스크립트.

사용법:
    set SERVICE_KEY_APT=...
    python debug_one_call.py
"""
import json
import os

import requests

from house_type_map import API_ENDPOINTS

cases = [
    ("apt", "29200", "202201", "광주 광산구 아파트 2022-01"),
    ("apt", "29200", "202312", "광주 광산구 아파트 2023-12"),
    ("apt", "29200", "202406", "광주 광산구 아파트 2024-06"),
    ("apt", "46220", "202201", "여수시 아파트 2022-01"),
    ("apt", "46220", "202312", "여수시 아파트 2023-12"),
    ("apt", "46220", "202406", "여수시 아파트 2024-06"),
]

service_key = os.environ.get("SERVICE_KEY_APT")
if not service_key:
    raise SystemExit("SERVICE_KEY_APT 환경변수를 먼저 set 하세요.")

for api_type, lawd_cd, deal_ymd, label in cases:
    params = {
        "serviceKey": service_key,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "pageNo": 1,
        "numOfRows": 10,
        "_type": "json",
    }
    print("=" * 60)
    print(f"{label} ({api_type}, LAWD_CD={lawd_cd}, DEAL_YMD={deal_ymd})")
    resp = requests.get(API_ENDPOINTS[api_type], params=params, timeout=20)
    print("HTTP status:", resp.status_code)
    print("실제 요청 URL:", resp.url)
    try:
        data = resp.json()
        print("응답 JSON:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    except Exception:
        print("JSON 파싱 실패. raw text:")
        print(resp.text[:2000])
    print()
