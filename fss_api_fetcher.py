"""
금융감독원 전세자금대출 API 수집기
전 권역 × 전 페이지 자동 순회 → baseList / optionList CSV 저장
"""

import os
import csv
import time
import json
import urllib.request
import urllib.parse
from datetime import date

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────

API_KEY   = os.environ.get("FSS_API_KEY", "YOUR_API_KEY_HERE")  # 환경변수 우선
BASE_URL  = "http://finlife.fss.or.kr/finlifeapi/rentHouseLoanProductsSearch.json"
OUT_DIR   = os.path.dirname(os.path.abspath(__file__))

# 이 프로젝트에서 필요한 권역 코드
# - 020000 : 은행  (시중은행·인터넷전문은행 전세대출 주요 공급처)
# - 030300 : 저축은행 (2금융권 DSR 50% 적용 대상)
# - 050000 : 보험  (보험사 전세 관련 상품)
SECTORS = {
    "020000": "은행",
    "030300": "저축은행",
    "050000": "보험",
}

# API 1회 조회 기본 100건 제한 → 페이지 순회로 전체 수집
DELAY_SEC = 0.5   # 요청 간 대기 (일일 허용횟수 초과 방지)


# ─────────────────────────────────────────────
# 응답 필드 → 프로젝트 컬럼 매핑
# ─────────────────────────────────────────────

# baseList (상품 기본정보) 에서 실제로 사용하는 필드
BASE_FIELDS = {
    "dcls_month"   : "공시제출월",
    "fin_co_no"    : "금융회사코드",
    "kor_co_nm"    : "금융회사명",
    "fin_prdt_cd"  : "금융상품코드",      # optionList 조인 키
    "fin_prdt_nm"  : "상품명",
    "join_way"     : "가입방법",
    "loan_inci_expn": "대출부대비용",
    "erly_rpay_fee": "중도상환수수료",
    "dly_rate"     : "연체이자율",
    "loan_lmt"     : "대출한도",          # → LimitCoverageScore 참고
    "dcls_strt_day": "공시시작일",
    "dcls_end_day" : "공시종료일",
}

# optionList (상품별 금리·상환 옵션) 에서 사용하는 필드
OPTION_FIELDS = {
    "fin_co_no"       : "금융회사코드",
    "fin_prdt_cd"     : "금융상품코드",   # baseList 조인 키
    "rpay_type"       : "상환유형코드",
    "rpay_type_nm"    : "상환유형명",     # → repayment_method
    "lend_rate_type"  : "금리유형코드",
    "lend_rate_type_nm": "금리유형명",    # → interest_rate_type
    "lend_rate_min"   : "금리최저",       # → InterestBenefitScore
    "lend_rate_max"   : "금리최고",
    "lend_rate_avg"   : "전월평균금리",   # → InterestBenefitScore 기준선
}


# ─────────────────────────────────────────────
# API 호출 함수
# ─────────────────────────────────────────────

def fetch_page(sector_code: str, page_no: int) -> dict:
    """단일 페이지 JSON 응답을 딕셔너리로 반환"""
    params = urllib.parse.urlencode({
        "auth"        : API_KEY,
        "topFinGrpNo" : sector_code,
        "pageNo"      : page_no,
    })
    url = f"{BASE_URL}?{params}"

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)
    return data.get("result", {})


def fetch_all_sectors() -> tuple[list[dict], list[dict]]:
    """
    전체 권역 × 전체 페이지 순회
    반환: (all_base, all_options)
    """
    all_base    = []
    all_options = []

    for code, name in SECTORS.items():
        print(f"\n▶ 권역: {name} ({code})")
        page = 1

        while True:
            print(f"   페이지 {page} 요청 중...", end=" ")
            result = fetch_page(code, page)

            err_cd = result.get("err_cd", "999")
            if err_cd != "000":
                print(f"오류 [{err_cd}] {result.get('err_msg')}")
                break

            base_list   = result.get("baseList", [])
            option_list = result.get("optionList", [])
            max_page    = int(result.get("max_page_no", 1))

            # 권역 코드 태깅 (조인·필터용)
            for row in base_list:
                row["top_fin_grp_no"]   = code
                row["top_fin_grp_nm"]   = name
            for row in option_list:
                row["top_fin_grp_no"]   = code
                row["top_fin_grp_nm"]   = name

            all_base.extend(base_list)
            all_options.extend(option_list)

            print(f"상품 {len(base_list)}건, 옵션 {len(option_list)}건 수신 "
                  f"(총 {max_page}페이지 중 {page}페이지)")

            if page >= max_page:
                break
            page += 1
            time.sleep(DELAY_SEC)

    return all_base, all_options


# ─────────────────────────────────────────────
# CSV 저장
# ─────────────────────────────────────────────

def save_csv(rows: list[dict], filename: str, field_order: list[str] | None = None):
    if not rows:
        print(f"[저장 생략] {filename} — 데이터 없음")
        return

    path = os.path.join(OUT_DIR, filename)
    fields = field_order if field_order else list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ 저장 완료: {filename}  ({len(rows)}행)")


# ─────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("⚠  FSS_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   export FSS_API_KEY=발급받은_32자리_키  후 재실행하세요.\n")

    print("=" * 55)
    print(f" 금융감독원 전세자금대출 API 수집 시작")
    print(f" 수집일: {date.today()}  |  권역: {list(SECTORS.values())}")
    print("=" * 55)

    base_rows, option_rows = fetch_all_sectors()

    today_str = date.today().strftime("%Y%m%d")

    # 기본정보 CSV
    base_fields = (
        ["top_fin_grp_no", "top_fin_grp_nm"]
        + list(BASE_FIELDS.keys())
    )
    save_csv(base_rows,   f"fss_jeonse_base_{today_str}.csv",   base_fields)

    # 옵션(금리) CSV
    option_fields = (
        ["top_fin_grp_no", "top_fin_grp_nm"]
        + list(OPTION_FIELDS.keys())
    )
    save_csv(option_rows, f"fss_jeonse_options_{today_str}.csv", option_fields)

    print(f"\n총 수집: 상품 {len(base_rows)}건 / 금리옵션 {len(option_rows)}건")
    print("수집한 데이터를 jeonse_product_catalog.csv 에 병합해 사용하세요.")
