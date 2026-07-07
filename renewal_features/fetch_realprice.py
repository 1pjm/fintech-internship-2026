"""
국토교통부 전월세 실거래가 API 4종(아파트/연립다세대/단독다가구/오피스텔) 호출 스크립트.

주의: 이 코드실행 환경은 apis.data.go.kr 아웃바운드가 막혀 있어 여기서는 실행할 수 없다.
서비스키를 가진 사람이 로컬 PC에서 실행해서 raw_transactions.csv를 만든 뒤,
build_renewal_features.py / merge_renewal_features.py 는 다시 여기서 이어서 처리한다.

사용법:
    pip install requests
    export SERVICE_KEY_APT=발급받은_디코딩_인증키
    export SERVICE_KEY_RH=...
    export SERVICE_KEY_SH=...
    export SERVICE_KEY_OFFI=...
    python fetch_realprice.py --start 202201 --end 202412 --out raw_transactions.csv

주의(중요): 마이페이지에서 "일반 인증키(Decoding)"을 사용할 것.
"Encoding" 키를 그대로 넣으면 requests가 다시 URL 인코딩해서 이중 인코딩 오류(SERVICE_KEY_IS_NOT_REGISTERED_ERROR)가 난다.
"""
import argparse
import csv
import os
import sys
import time

import requests

from house_type_map import API_ENDPOINTS, API_TYPES
from lawd_codes import LAWD_CODES

FIELDNAMES = [
    "sido", "sigungu_name", "lawd_cd", "api_type", "house_type_raw",
    "deal_year", "deal_month", "deal_day",
    "deposit", "monthly_rent", "pre_deposit", "pre_monthly_rent",
    "contract_type", "use_rr_right", "build_year",
    "exclu_use_ar", "total_floor_ar",
]

NUM_OF_ROWS = 1000


def month_range(start_yyyymm: str, end_yyyymm: str):
    start_y, start_m = int(start_yyyymm[:4]), int(start_yyyymm[4:])
    end_y, end_m = int(end_yyyymm[:4]), int(end_yyyymm[4:])
    y, m = start_y, start_m
    while (y, m) <= (end_y, end_m):
        yield f"{y:04d}{m:02d}"
        m += 1
        if m == 13:
            m = 1
            y += 1


def fetch_one_page(session, api_type, service_key, lawd_cd, deal_ymd, page_no):
    params = {
        "serviceKey": service_key,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "pageNo": page_no,
        "numOfRows": NUM_OF_ROWS,
        "_type": "json",
    }
    resp = session.get(API_ENDPOINTS[api_type], params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    body = data.get("response", {}).get("body", {})
    total_count = int(body.get("totalCount", 0) or 0)
    items = body.get("items", "")
    if not items:
        return [], total_count
    item = items.get("item", []) if isinstance(items, dict) else []
    if isinstance(item, dict):
        item = [item]
    return item, total_count


def normalize_row(sido, sigungu_name, lawd_cd, api_type, item):
    def g(*keys, default=""):
        for k in keys:
            if k in item and item[k] not in (None, ""):
                return item[k]
        return default

    return {
        "sido": sido,
        "sigungu_name": sigungu_name,
        "lawd_cd": lawd_cd,
        "api_type": api_type,
        "house_type_raw": g("houseType"),
        "deal_year": g("dealYear"),
        "deal_month": g("dealMonth"),
        "deal_day": g("dealDay"),
        "deposit": str(g("deposit")).replace(",", "").strip(),
        "monthly_rent": str(g("monthlyRent")).replace(",", "").strip(),
        "pre_deposit": str(g("preDeposit")).replace(",", "").strip(),
        "pre_monthly_rent": str(g("preMonthlyRent")).replace(",", "").strip(),
        "contract_type": g("contractType"),
        "use_rr_right": g("useRRRight"),
        "build_year": g("buildYear"),
        "exclu_use_ar": g("excluUseAr"),
        "total_floor_ar": g("totalFloorAr"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="202201", help="YYYYMM")
    parser.add_argument("--end", default="202412", help="YYYYMM")
    parser.add_argument("--out", default="raw_transactions.csv")
    parser.add_argument("--sleep", type=float, default=0.2, help="호출 간 대기(초)")
    parser.add_argument(
        "--types", default=",".join(API_TYPES),
        help="쉼표로 구분한 API 종류 (apt,rh,sh,offi 중 일부). "
             "예: 오피스텔만 나중에 재수집할 때 --types offi",
    )
    args = parser.parse_args()
    selected_types = [t.strip() for t in args.types.split(",") if t.strip()]
    unknown = [t for t in selected_types if t not in API_TYPES]
    if unknown:
        sys.exit(f"알 수 없는 --types 값: {unknown} (apt/rh/sh/offi 중에서 선택)")

    service_keys = {
        "apt": os.environ.get("SERVICE_KEY_APT"),
        "rh": os.environ.get("SERVICE_KEY_RH"),
        "sh": os.environ.get("SERVICE_KEY_SH"),
        "offi": os.environ.get("SERVICE_KEY_OFFI"),
    }
    missing = [k for k in selected_types if not service_keys[k]]
    if missing:
        sys.exit(f"환경변수 누락: {missing} (SERVICE_KEY_APT/RH/SH/OFFI 를 export 하세요)")

    file_exists = os.path.exists(args.out)
    out_f = open(args.out, "a", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
    if not file_exists:
        writer.writeheader()

    session = requests.Session()
    months = list(month_range(args.start, args.end))
    total_calls = len(LAWD_CODES) * len(months) * len(selected_types)
    done = 0

    for sido, (sigungu_name, lawd_cd) in LAWD_CODES.items():
        for deal_ymd in months:
            for api_type in selected_types:
                done += 1
                try:
                    page_no = 1
                    collected = 0
                    while True:
                        items, total_count = fetch_one_page(
                            session, api_type, service_keys[api_type],
                            lawd_cd, deal_ymd, page_no,
                        )
                        for item in items:
                            writer.writerow(normalize_row(sido, sigungu_name, lawd_cd, api_type, item))
                        collected += len(items)
                        out_f.flush()
                        if collected >= total_count or not items:
                            break
                        page_no += 1
                        time.sleep(args.sleep)
                except Exception as e:
                    print(f"[WARN] {sido}/{api_type}/{deal_ymd} 실패: {e}", file=sys.stderr)
                time.sleep(args.sleep)
            print(f"진행 {done}/{total_calls}: {sido} {deal_ymd} 완료", file=sys.stderr)

    out_f.close()


if __name__ == "__main__":
    main()
