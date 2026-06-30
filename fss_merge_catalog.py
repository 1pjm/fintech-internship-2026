"""
FSS API 수집 결과 병합 스크립트
fss_jeonse_base_*.csv  +  fss_jeonse_options_*.csv
→ fss_jeonse_merged_YYYYMMDD.csv   (전체 컬럼 병합본)
→ jeonse_product_catalog.csv       (기존 카탈로그에 은행 상품 추가)
"""

import csv
import glob
import os
import re
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG  = os.path.join(BASE_DIR, "jeonse_product_catalog.csv")


# ─────────────────────────────────────────────
# 1. 최신 수집 파일 자동 탐색
# ─────────────────────────────────────────────

def find_latest(pattern: str) -> str:
    files = sorted(glob.glob(os.path.join(BASE_DIR, pattern)))
    if not files:
        raise FileNotFoundError(f"파일 없음: {pattern}\n먼저 fss_api_fetcher.py 를 실행하세요.")
    return files[-1]   # 날짜 오름차순 → 마지막 = 최신


# ─────────────────────────────────────────────
# 2. CSV 로더
# ─────────────────────────────────────────────

def load_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────
# 3. 대출한도 텍스트 → 숫자 파싱 (만원 단위)
#    예: "최대2.2억원" → 22000
#        "200백만원"   → 20000
#        "3억원"       → 30000
#        "최대 3억원"  → 30000
# ─────────────────────────────────────────────

def parse_loan_lmt(text: str) -> int:
    if not text:
        return 0
    text = text.replace(" ", "").replace(",", "")

    # N억N천만원 or N억원
    m = re.search(r"(\d+\.?\d*)억(\d+)?천?만?원?", text)
    if m:
        eok  = float(m.group(1))
        chun = float(m.group(2)) * 1000 if m.group(2) else 0
        return int(eok * 10000 + chun)

    # N백만원
    m = re.search(r"(\d+)백만원", text)
    if m:
        return int(m.group(1)) * 100

    # N만원
    m = re.search(r"(\d+)만원", text)
    if m:
        return int(m.group(1))

    return 0


# ─────────────────────────────────────────────
# 4. 옵션 집계
#    한 상품에 여러 옵션(고정/변동 × 만기일시/분할) → 상품 1행으로 요약
# ─────────────────────────────────────────────

def aggregate_options(option_rows: list[dict]) -> dict:
    """
    option_rows : 동일 fin_prdt_cd 에 속한 옵션 목록
    반환: 집계된 금리 정보 딕셔너리
    """
    rate_mins, rate_maxs, rate_avgs = [], [], []
    rpay_types, rate_types = set(), set()

    for o in option_rows:
        try: rate_mins.append(float(o["lend_rate_min"]))
        except (ValueError, TypeError): pass
        try: rate_maxs.append(float(o["lend_rate_max"]))
        except (ValueError, TypeError): pass
        try: rate_avgs.append(float(o["lend_rate_avg"]))
        except (ValueError, TypeError): pass
        if o.get("rpay_type_nm"): rpay_types.add(o["rpay_type_nm"])
        if o.get("lend_rate_type_nm"): rate_types.add(o["lend_rate_type_nm"])

    return {
        "base_rate_min"    : round(min(rate_mins), 2) if rate_mins else None,
        "base_rate_max"    : round(max(rate_maxs), 2) if rate_maxs else None,
        "lend_rate_avg"    : round(sum(rate_avgs) / len(rate_avgs), 2) if rate_avgs else None,
        "repayment_types"  : "|".join(sorted(rpay_types)),
        "interest_rate_types": "|".join(sorted(rate_types)),
        "option_count"     : len(option_rows),
    }


# ─────────────────────────────────────────────
# 5. 권역 코드 → DSR 한도·보증기관 추론
# ─────────────────────────────────────────────

SECTOR_META = {
    "020000": {"dsr_limit_pct": 40, "sector_label": "은행"},
    "030300": {"dsr_limit_pct": 50, "sector_label": "저축은행"},
    "050000": {"dsr_limit_pct": 40, "sector_label": "보험"},
}

def infer_guarantee(product_name: str) -> str:
    """상품명 키워드로 보증기관 추론"""
    nm = product_name
    if "주택보증" in nm or "HUG" in nm or "주택도시보증" in nm:
        return "HUG"
    if "주택금융" in nm or "HF" in nm:
        return "HF"
    if "서울보증" in nm or "SGI" in nm:
        return "SGI"
    return "HUG"   # 명시 없으면 HUG (은행 전세대출 가장 일반적)


# ─────────────────────────────────────────────
# 6. 메인 병합 로직
# ─────────────────────────────────────────────

def merge():
    # 6-1. 파일 탐색
    base_file   = find_latest("fss_jeonse_base_*.csv")
    option_file = find_latest("fss_jeonse_options_*.csv")
    print(f"기본정보 파일 : {os.path.basename(base_file)}")
    print(f"옵션     파일 : {os.path.basename(option_file)}")

    base_rows   = load_csv(base_file)
    option_rows = load_csv(option_file)
    print(f"  → 상품 {len(base_rows)}건 / 옵션 {len(option_rows)}건 로드")

    # 6-2. 옵션을 fin_prdt_cd 기준으로 그루핑
    option_map: dict[str, list[dict]] = {}
    for o in option_rows:
        key = o["fin_prdt_cd"]
        option_map.setdefault(key, []).append(o)

    # 6-3. base + option 병합
    merged = []
    for b in base_rows:
        prod_cd  = b["fin_prdt_cd"]
        opts     = option_map.get(prod_cd, [])
        agg      = aggregate_options(opts)
        sector   = b.get("top_fin_grp_no", "020000")
        meta     = SECTOR_META.get(sector, SECTOR_META["020000"])
        lmt_won  = parse_loan_lmt(b.get("loan_lmt", ""))

        row = {
            # ── 식별자 ──────────────────────────────
            "fin_co_no"          : b.get("fin_co_no"),
            "fin_prdt_cd"        : prod_cd,
            "top_fin_grp_no"     : sector,
            "top_fin_grp_nm"     : b.get("top_fin_grp_nm"),
            # ── 상품 기본정보 ────────────────────────
            "kor_co_nm"          : b.get("kor_co_nm"),
            "fin_prdt_nm"        : b.get("fin_prdt_nm"),
            "join_way"           : b.get("join_way"),
            "loan_lmt_text"      : b.get("loan_lmt"),
            "loan_lmt_man_won"   : lmt_won,           # 만원 파싱 결과
            "loan_inci_expn"     : b.get("loan_inci_expn"),
            "erly_rpay_fee"      : b.get("erly_rpay_fee"),
            "dly_rate"           : b.get("dly_rate"),
            "dcls_month"         : b.get("dcls_month"),
            "dcls_strt_day"      : b.get("dcls_strt_day"),
            "dcls_end_day"       : b.get("dcls_end_day"),
            # ── 집계된 금리·상환 옵션 ────────────────
            "base_rate_min"      : agg["base_rate_min"],
            "base_rate_max"      : agg["base_rate_max"],
            "lend_rate_avg"      : agg["lend_rate_avg"],
            "repayment_types"    : agg["repayment_types"],
            "interest_rate_types": agg["interest_rate_types"],
            "option_count"       : agg["option_count"],
            # ── 추론 필드 ────────────────────────────
            "guarantee_agency"   : infer_guarantee(b.get("fin_prdt_nm", "")),
            "dsr_limit_pct"      : meta["dsr_limit_pct"],
            "financial_sector"   : meta["sector_label"],
            # ── 카탈로그 호환 필드 (은행 상품은 자격조건 불명 → 기본값) ──
            "age_min"            : 19,
            "age_max"            : 99,
            "income_limit_single": 99999,
            "income_limit_couple": 99999,
            "net_asset_limit"    : 99999,
            "credit_score_min"   : 650,
            "ltv_limit_pct"      : 80,
            "max_area_sqm"       : 9999,
            "marriage_within_7y_required": "N",
            "newborn_within_2y_required" : "N",
            "youth_only"         : "N",
            "allowed_property_types": "아파트|연립|다세대|단독|오피스텔",
        }
        merged.append(row)

    return merged


# ─────────────────────────────────────────────
# 7. 병합본 CSV 저장
# ─────────────────────────────────────────────

def save_merged(merged: list[dict]):
    today  = date.today().strftime("%Y%m%d")
    path   = os.path.join(BASE_DIR, f"fss_jeonse_merged_{today}.csv")
    fields = list(merged[0].keys())

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(merged)

    print(f"\n✓ 병합 파일 저장: {os.path.basename(path)}  ({len(merged)}행)")
    return path


# ─────────────────────────────────────────────
# 8. 기존 jeonse_product_catalog.csv 에 은행 상품 추가
#    - 기존 A1~A5 정부지원 상품은 유지
#    - A6(일반 전세자금대출) 자리를 FSS 실제 상품으로 교체·확장
# ─────────────────────────────────────────────

def update_catalog(merged: list[dict]):
    # 기존 카탈로그 로드
    existing = load_csv(CATALOG)
    # 정부지원 상품(A1~A5)만 유지 — A6은 FSS 실제 데이터로 대체
    gov_products = [r for r in existing if r["product_id"] not in ("A6",)]

    # FSS 수집 상품을 카탈로그 스키마로 변환
    catalog_fields = list(existing[0].keys())   # 기존 컬럼 순서 그대로
    fss_products   = []

    for idx, m in enumerate(merged, start=1):
        # 대출한도: 수도권/비수도권 구분 정보가 API에 없으므로 동일 적용
        max_loan = m["loan_lmt_man_won"] if m["loan_lmt_man_won"] > 0 else 50000

        row = {
            "product_id"                 : f"B{idx:03d}",
            "product_name"               : f"{m['kor_co_nm']} {m['fin_prdt_nm']}",
            "product_type"               : "전세자금대출",
            "age_min"                    : m["age_min"],
            "age_max"                    : m["age_max"],
            "income_limit_single"        : m["income_limit_single"],
            "income_limit_couple"        : m["income_limit_couple"],
            "net_asset_limit"            : m["net_asset_limit"],
            "credit_score_min"           : m["credit_score_min"],
            "deposit_limit_capital"      : max_loan,
            "deposit_limit_non_capital"  : max_loan,
            "ltv_limit_pct"              : m["ltv_limit_pct"],
            "max_loan_capital"           : max_loan,
            "max_loan_non_capital"       : max_loan,
            "base_rate_min"              : m["base_rate_min"] if m["base_rate_min"] else "",
            "base_rate_max"              : m["base_rate_max"] if m["base_rate_max"] else "",
            "max_area_sqm"               : m["max_area_sqm"],
            "guarantee_agency"           : m["guarantee_agency"],
            "dsr_limit_pct"              : m["dsr_limit_pct"],
            "marriage_within_7y_required": m["marriage_within_7y_required"],
            "newborn_within_2y_required" : m["newborn_within_2y_required"],
            "youth_only"                 : m["youth_only"],
            "allowed_property_types"     : m["allowed_property_types"],
            "target_customer"            : f"{m['financial_sector']} 전세대출 이용 고객",
            "notes"                      : (
                f"가입방법:{m['join_way']} | "
                f"상환유형:{m['repayment_types']} | "
                f"금리유형:{m['interest_rate_types']} | "
                f"공시월:{m['dcls_month']}"
            ),
        }
        fss_products.append(row)

    all_products = gov_products + fss_products

    with open(CATALOG, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=catalog_fields)
        w.writeheader()
        w.writerows(all_products)

    print(f"✓ 카탈로그 업데이트: {CATALOG}")
    print(f"   정부지원 상품 {len(gov_products)}개 (유지)")
    print(f"   FSS 수집 상품  {len(fss_products)}개 (신규 추가)")
    print(f"   총 {len(all_products)}개 상품")


# ─────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print(" FSS 전세자금대출 데이터 병합")
    print("=" * 55)

    merged = merge()
    save_merged(merged)
    update_catalog(merged)

    print("\n완료. jeonse_rec_scoring.py 의 recommend() 에서")
    print("업데이트된 jeonse_product_catalog.csv 를 그대로 사용할 수 있습니다.")
