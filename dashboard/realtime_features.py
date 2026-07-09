"""
사용자가 입력한 (시도, 주택구분, 계약월)에 대해 국토부 실거래가 API를 그 자리에서 호출해서
그룹레벨 피처(시세비교/갱신계약/건물특성)를 실시간으로 계산한다.

renewal_features/ 에서 이미 검증한 API 스키마·LAWD코드·에러처리 로직을 그대로 재사용한다.
과거 데이터를 통째로 모으는 fetch_realprice.py와 달리, 이건 "지금 이 조합 하나"만
필요하기 때문에 매물 조회 버튼을 누를 때마다 몇 초 안에 끝난다.

주의: 이 코드실행 환경(샌드박스)은 apis.data.go.kr 접근이 막혀 있어 여기서 테스트할 수
없다. 로컬 PC에서 실행해야 한다.
"""
import os
import sys
from datetime import date

import pandas as pd
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "renewal_features"))
from house_type_map import API_ENDPOINTS, HOUSE_TYPE_TO_API  # noqa: E402
from lawd_codes import LAWD_CODES  # noqa: E402

SERVICE_KEYS = {
    "apt": os.environ.get("SERVICE_KEY_APT"),
    "rh": os.environ.get("SERVICE_KEY_RH"),
    "sh": os.environ.get("SERVICE_KEY_SH"),
    "offi": os.environ.get("SERVICE_KEY_OFFI"),
}

# 한 달 거래량이 적은 주택유형(다가구/오피스텔 등)은 표본이 너무 적을 수 있어서
# 최근 N개월을 모아서 평균을 낸다.
LOOKBACK_MONTHS = 6


def _recent_months(base_ym: str, n: int):
    y, m = int(base_ym[:4]), int(base_ym[4:])
    out = []
    for _ in range(n):
        out.append(f"{y:04d}{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return out


def _fetch_page(api_type, lawd_cd, deal_ymd, page_no=1, num_of_rows=1000):
    params = {
        "serviceKey": SERVICE_KEYS[api_type],
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "_type": "json",
    }
    resp = requests.get(API_ENDPOINTS[api_type], params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if "response" not in data:
        raise RuntimeError(f"예상치 못한 응답: {data}")
    header = data["response"].get("header", {})
    if header.get("resultCode") not in (None, "00", "000", "0"):
        raise RuntimeError(f"resultCode={header.get('resultCode')} {header.get('resultMsg')}")
    body = data["response"].get("body", {})
    items = body.get("items", "")
    if not items:
        return []
    item = items.get("item", []) if isinstance(items, dict) else []
    return [item] if isinstance(item, dict) else item


def fetch_recent_transactions(sido: str, house_type: str, base_ym: str) -> pd.DataFrame:
    api_type = HOUSE_TYPE_TO_API[house_type]
    if not SERVICE_KEYS[api_type]:
        raise RuntimeError(f"SERVICE_KEY_{api_type.upper()} 환경변수가 설정되지 않았습니다.")
    _, lawd_cd = LAWD_CODES[sido]

    rows = []
    for deal_ymd in _recent_months(base_ym, LOOKBACK_MONTHS):
        try:
            for item in _fetch_page(api_type, lawd_cd, deal_ymd):
                rows.append(item)
        except Exception as e:
            print(f"[WARN] {sido}/{api_type}/{deal_ymd} 조회 실패: {e}", file=sys.stderr)

    df = pd.DataFrame(rows)
    return df


def compute_group_features(sido: str, house_type: str, base_ym: str, deposit_krw_10k: float) -> dict:
    """
    deposit_krw_10k: 사용자가 입력한 이 계약의 임대보증금액 (만원 단위, 실거래가 API와 동일 단위)
    """
    df = fetch_recent_transactions(sido, house_type, base_ym)

    if df.empty:
        return {
            "시세_평균전세보증금": None,
            "시세대비보증금비율": None,
            "월세전환비율": None,
            "평균보증금인상률": None,
            "갱신계약비율": None,
            "갱신요구권행사비율": None,
            "평균건축연도": None,
            "평균전용면적": None,
            "거래량": 0,
        }

    def num(col):
        return pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce") if col in df else pd.Series(dtype=float)

    deposit = num("deposit")
    monthly_rent = num("monthlyRent")
    pre_deposit = num("preDeposit")
    build_year = num("buildYear")
    area = num("excluUseAr") if "excluUseAr" in df.columns else num("totalFloorAr")
    contract_type = df["contractType"].astype(str).str.strip() if "contractType" in df else pd.Series(dtype=str)
    use_rr = df["useRRRight"].astype(str).str.strip() if "useRRRight" in df else pd.Series(dtype=str)

    jeonse_mask = monthly_rent == 0
    avg_jeonse_deposit = deposit[jeonse_mask].mean()

    valid_ct = contract_type.isin(["신규", "갱신"])
    renewal_mask = valid_ct & (contract_type == "갱신")
    renewal_with_pre = renewal_mask & (pre_deposit > 0)
    increase_rate = ((deposit[renewal_with_pre] - pre_deposit[renewal_with_pre]) / pre_deposit[renewal_with_pre]).mean()

    return {
        "시세_평균전세보증금": None if pd.isna(avg_jeonse_deposit) else float(avg_jeonse_deposit) * 10000,
        "시세대비보증금비율": None if pd.isna(avg_jeonse_deposit) or avg_jeonse_deposit == 0
            else float(deposit_krw_10k / avg_jeonse_deposit),
        "월세전환비율": float((monthly_rent > 0).mean()),
        "평균보증금인상률": None if pd.isna(increase_rate) else float(increase_rate),
        "갱신계약비율": None if valid_ct.sum() == 0 else float(renewal_mask.sum() / valid_ct.sum()),
        "갱신요구권행사비율": float((use_rr == "사용").mean()),
        "평균건축연도": None if build_year.isna().all() else float(build_year.mean()),
        "평균전용면적": None if area.isna().all() else float(area.mean()),
        "거래량": int(len(df)),
    }


if __name__ == "__main__":
    today = date.today()
    ym = f"{today.year:04d}{today.month:02d}"
    result = compute_group_features("서울", "아파트", ym, deposit_krw_10k=50000)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
