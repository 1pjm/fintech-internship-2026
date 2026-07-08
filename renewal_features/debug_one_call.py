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
    ("apt", "28185", "202201", "인천 연수구 아파트 (기존 중구 대체 후보)"),
    ("apt", "29200", "202201", "광주 광산구 아파트 (기존 동구 대체 후보)"),
    ("apt", "46220", "202201", "여수시 아파트 (기존 목포시 대체 후보)"),
    ("apt", "11110", "202201", "서울(비교용, 정상 케이스)"),
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
