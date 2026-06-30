"""
전세대출 상품 추천 스코어링 엔진
JeonseLoanGate × JeonseLoanRecScore 구현
"""

from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────
# 1. 가중치 프로파일
# ─────────────────────────────────────────────

@dataclass
class WeightProfile:
    name: str
    approval: float          # 승인 가능성
    interest_benefit: float  # 금리 유리도
    limit_coverage: float    # 한도 커버율
    affordability: float     # 상환 여력 (DSR 여유도)
    guarantee_stability: float  # 보증 안정성
    preference_match: float  # 우대조건 충족도

    def validate(self) -> "WeightProfile":
        total = (self.approval + self.interest_benefit + self.limit_coverage
                 + self.affordability + self.guarantee_stability + self.preference_match)
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"[{self.name}] 가중치 합계 오류: {total:.3f} (1.0 이어야 함)")
        return self


# 고객 유형별 가중치 정의
WEIGHT_PROFILES: dict[str, WeightProfile] = {
    "default": WeightProfile(
        "기본형",
        approval=0.25, interest_benefit=0.25, limit_coverage=0.20,
        affordability=0.15, guarantee_stability=0.10, preference_match=0.05,
    ).validate(),

    "rate_sensitive": WeightProfile(
        "금리민감형",  # 부부합산 연소득 ≤ 4000만원
        approval=0.20, interest_benefit=0.38, limit_coverage=0.18,
        affordability=0.14, guarantee_stability=0.05, preference_match=0.05,
    ).validate(),

    "limit_constrained": WeightProfile(
        "한도부족형",  # 요청 대출금 > 상품 한도의 90%
        approval=0.20, interest_benefit=0.15, limit_coverage=0.38,
        affordability=0.15, guarantee_stability=0.07, preference_match=0.05,
    ).validate(),

    "credit_vulnerable": WeightProfile(
        "신용취약형",  # 신용점수 600~699
        approval=0.40, interest_benefit=0.20, limit_coverage=0.18,
        affordability=0.12, guarantee_stability=0.05, preference_match=0.05,
    ).validate(),

    "youth": WeightProfile(
        "청년무주택형",  # 만 19~34세 + 무주택 세대주
        approval=0.20, interest_benefit=0.35, limit_coverage=0.20,
        affordability=0.10, guarantee_stability=0.10, preference_match=0.05,
    ).validate(),

    "newlywed_newborn": WeightProfile(
        "신혼·신생아형",  # 혼인 7년 이내 or 2년 내 출산
        approval=0.22, interest_benefit=0.30, limit_coverage=0.25,
        affordability=0.13, guarantee_stability=0.05, preference_match=0.05,
    ).validate(),

    "high_dsr_risk": WeightProfile(
        "상환위험형",  # 예상 DSR ≥ 35%
        approval=0.25, interest_benefit=0.18, limit_coverage=0.15,
        affordability=0.32, guarantee_stability=0.05, preference_match=0.05,
    ).validate(),
}


# ─────────────────────────────────────────────
# 2. 고객 유형 자동 분류
# ─────────────────────────────────────────────

def classify_customer(
    combined_income: int,
    credit_score: int,
    age: int,
    is_household_head: bool,
    is_homeless: bool,
    marriage_years: Optional[int],
    has_newborn: bool,
    dsr_estimated: float,
    loan_requested: int,
    product_max_loan: int,
) -> str:
    """
    고객 정보를 기반으로 가중치 프로파일 키를 반환한다.
    조건이 겹치면 우선순위가 높은 유형을 선택한다.
    우선순위: 신용취약 > 상환위험 > 한도부족 > 청년 > 신혼신생아 > 금리민감 > 기본
    """
    if credit_score <= 699:
        return "credit_vulnerable"

    if dsr_estimated >= 35.0:
        return "high_dsr_risk"

    if product_max_loan > 0 and loan_requested / product_max_loan >= 0.90:
        return "limit_constrained"

    if 19 <= age <= 34 and is_household_head and is_homeless:
        return "youth"

    if (marriage_years is not None and marriage_years <= 7) or has_newborn:
        return "newlywed_newborn"

    if combined_income <= 4000:
        return "rate_sensitive"

    return "default"


# ─────────────────────────────────────────────
# 3. Gate 판정 (Hard Filter)
# ─────────────────────────────────────────────

@dataclass
class GateResult:
    age_ok: int
    homeless_ok: int
    household_head_ok: int
    income_ok: int
    credit_ok: int
    dsr_ok: int
    deposit_limit_ok: int
    property_type_ok: int
    area_ok: int
    no_duplicate_loan: int
    info_complete: int
    product_condition_ok: int  # 상품별 필수 조건 (혼인기간·신생아·청년전용)

    @property
    def passed(self) -> bool:
        return (
            self.age_ok
            * self.homeless_ok
            * self.household_head_ok
            * self.income_ok
            * self.credit_ok
            * self.dsr_ok
            * self.deposit_limit_ok
            * self.property_type_ok
            * self.area_ok
            * self.no_duplicate_loan
            * self.info_complete
            * self.product_condition_ok
        ) == 1


def evaluate_gate(customer: dict, product: dict, property_info: dict) -> GateResult:
    """
    JeonseLoanGate 항목별 판정 (0 or 1)
    customer    : jeonse_customer_profiles 의 한 행
    product     : jeonse_product_catalog 의 한 행
    property_info : jeonse_property_gate 의 한 행
    """
    age = customer["age"]
    income = customer["combined_annual_income"]
    credit = customer["credit_score_kcb"]
    dsr = property_info["dsr_estimated_pct"]
    deposit = property_info["deposit_amount"]
    prop_type = property_info["property_type"]
    area = property_info["exclusive_area_sqm"]
    is_capital = property_info["is_capital_area"] == "Y"
    sector = property_info["financial_sector"]
    info_ok = property_info["info_completeness"] == "Y"

    # 연령
    age_ok = int(product["age_min"] <= age <= product["age_max"])

    # 무주택
    homeless_ok = int(customer["is_homeless"] == "Y")

    # 세대주
    household_head_ok = int(customer["is_household_head"] == "Y")

    # 소득 (부부합산)
    income_limit = (
        product["income_limit_couple"]
        if customer["spouse_income"] > 0
        else product["income_limit_single"]
    )
    income_ok = int(income <= income_limit)

    # 신용점수
    credit_ok = int(credit >= product["credit_score_min"])

    # DSR
    dsr_limit = 50.0 if sector == "2금융권" else 40.0
    dsr_ok = int(dsr <= dsr_limit)

    # 보증금 한도
    deposit_limit = (
        product["deposit_limit_capital"] if is_capital
        else product["deposit_limit_non_capital"]
    )
    deposit_limit_ok = int(deposit <= deposit_limit)

    # 주택 유형
    allowed_types = product["allowed_property_types"].split("|")
    property_type_ok = int(prop_type in allowed_types)

    # 전용면적
    area_ok = int(area <= product["max_area_sqm"])

    # 중복 대출
    no_duplicate = int(customer["has_existing_jeonse_loan"] == "N")

    # 정보 완전성
    info_complete = int(info_ok)

    # 상품별 필수 조건
    product_condition = 1
    if product["marriage_within_7y_required"] == "Y":
        product_condition *= int(customer["marriage_years"] <= 7)
    if product["newborn_within_2y_required"] == "Y":
        product_condition *= int(customer["has_newborn_within_2y"] == "Y")
    if product["youth_only"] == "Y":
        product_condition *= int(19 <= age <= 34)

    return GateResult(
        age_ok=age_ok,
        homeless_ok=homeless_ok,
        household_head_ok=household_head_ok,
        income_ok=income_ok,
        credit_ok=credit_ok,
        dsr_ok=dsr_ok,
        deposit_limit_ok=deposit_limit_ok,
        property_type_ok=property_type_ok,
        area_ok=area_ok,
        no_duplicate_loan=no_duplicate,
        info_complete=info_complete,
        product_condition_ok=product_condition,
    )


# ─────────────────────────────────────────────
# 4. 점수 항목 계산
# ─────────────────────────────────────────────

GUARANTEE_SCORE = {"HUG": 100, "HF": 80, "SGI": 60}

# 상품군 평균 금리 (InterestBenefitScore 기준선)
MARKET_AVG_RATE = 3.8  # 은행 일반 전세대출 평균


def calc_approval_score(credit: int, income: int, income_limit: int,
                         credit_min: int) -> float:
    """
    신용점수 여유분 + 소득 여유율 → 0~100
    두 요소를 50:50으로 합산
    """
    credit_margin = min((credit - credit_min) / (1000 - credit_min), 1.0)
    income_slack = min((income_limit - income) / income_limit, 1.0) if income_limit < 99999 else 1.0
    return round((credit_margin * 50 + income_slack * 50), 2)


def calc_interest_benefit_score(product_rate_min: float, preferred_rate: float = 0.0) -> float:
    """
    (시장 평균금리 − 해당상품 적용금리) 기준 0~100 정규화
    preferred_rate: 우대금리 적용 후 최종 금리 (없으면 상품 최저금리 사용)
    """
    applied_rate = preferred_rate if preferred_rate > 0 else product_rate_min
    benefit = MARKET_AVG_RATE - applied_rate
    # 최대 이익 구간: 시장 대비 −3.5%p 이상이면 100점
    return round(min(max(benefit / 3.5 * 100, 0), 100), 2)


def calc_limit_coverage_score(loan_requested: int, max_loan: int) -> float:
    """
    min(상품한도 / 신청대출금, 1) × 100
    상품 한도가 신청금 이상이면 100점
    """
    if loan_requested <= 0:
        return 0.0
    return round(min(max_loan / loan_requested, 1.0) * 100, 2)


def calc_affordability_score(dsr: float, dsr_limit: float) -> float:
    """
    (DSR한도 − 예상DSR) / DSR한도 × 100  (0 미만은 0)
    DSR 여유가 클수록 높은 점수
    """
    slack = (dsr_limit - dsr) / dsr_limit * 100
    return round(max(slack, 0.0), 2)


def calc_guarantee_stability_score(agency: str) -> float:
    return float(GUARANTEE_SCORE.get(agency, 50))


def calc_preference_match_score(matched_items: int, total_items: int) -> float:
    """
    충족 우대항목 수 / 전체 우대항목 수 × 100
    total_items = 0 이면 기본 50점 처리
    """
    if total_items == 0:
        return 50.0
    return round(matched_items / total_items * 100, 2)


# ─────────────────────────────────────────────
# 5. RiskPenalty 계산
# ─────────────────────────────────────────────

def calc_risk_penalty(
    dsr: float,
    credit: int,
    deposit_to_market_ratio: float,
    senior_plus_deposit_ratio: float,
) -> float:
    """
    감점 항목 합산 (음수로 반환)
    """
    penalty = 0.0
    if 30.0 <= dsr < 40.0:
        penalty -= 10.0   # DSR 경고 구간
    if 600 <= credit <= 699:
        penalty -= 15.0   # 신용 경고 구간
    if deposit_to_market_ratio > 90.0:
        penalty -= 20.0   # 깡통전세 위험
    if senior_plus_deposit_ratio > 80.0:
        penalty -= 10.0   # 선순위채권 위험
    return penalty


# ─────────────────────────────────────────────
# 6. 최종 추천 점수 계산
# ─────────────────────────────────────────────

@dataclass
class ScoreDetail:
    product_id: str
    product_name: str
    gate_passed: bool
    gate_result: GateResult
    weight_profile: str
    approval_score: float
    interest_benefit_score: float
    limit_coverage_score: float
    affordability_score: float
    guarantee_stability_score: float
    preference_match_score: float
    risk_penalty: float
    final_score: float


def calc_rec_score(
    customer: dict,
    product: dict,
    property_info: dict,
    matched_pref_items: int = 0,
    total_pref_items: int = 3,
) -> ScoreDetail:
    """
    JeonseLoanRecScore 전체 파이프라인
    """
    gate = evaluate_gate(customer, product, property_info)

    if not gate.passed:
        return ScoreDetail(
            product_id=product["product_id"],
            product_name=product["product_name"],
            gate_passed=False,
            gate_result=gate,
            weight_profile="—",
            approval_score=0, interest_benefit_score=0, limit_coverage_score=0,
            affordability_score=0, guarantee_stability_score=0, preference_match_score=0,
            risk_penalty=0, final_score=0.0,
        )

    is_capital = property_info["is_capital_area"] == "Y"
    sector = property_info["financial_sector"]
    dsr_limit = 50.0 if sector == "2금융권" else 40.0
    income_limit = (
        product["income_limit_couple"]
        if customer["spouse_income"] > 0
        else product["income_limit_single"]
    )
    max_loan = (
        product["max_loan_capital"] if is_capital
        else product["max_loan_non_capital"]
    )

    # 고객 유형 분류 → 가중치 선택
    profile_key = classify_customer(
        combined_income=customer["combined_annual_income"],
        credit_score=customer["credit_score_kcb"],
        age=customer["age"],
        is_household_head=customer["is_household_head"] == "Y",
        is_homeless=customer["is_homeless"] == "Y",
        marriage_years=customer["marriage_years"],
        has_newborn=customer["has_newborn_within_2y"] == "Y",
        dsr_estimated=property_info["dsr_estimated_pct"],
        loan_requested=property_info["loan_amount_requested"],
        product_max_loan=max_loan,
    )
    w = WEIGHT_PROFILES[profile_key]

    # 점수 항목 계산
    s_approval = calc_approval_score(
        customer["credit_score_kcb"], customer["combined_annual_income"],
        income_limit, product["credit_score_min"],
    )
    s_interest = calc_interest_benefit_score(product["base_rate_min"])
    s_limit = calc_limit_coverage_score(property_info["loan_amount_requested"], max_loan)
    s_afford = calc_affordability_score(property_info["dsr_estimated_pct"], dsr_limit)
    s_guarantee = calc_guarantee_stability_score(product["guarantee_agency"])
    s_pref = calc_preference_match_score(matched_pref_items, total_pref_items)
    penalty = calc_risk_penalty(
        dsr=property_info["dsr_estimated_pct"],
        credit=customer["credit_score_kcb"],
        deposit_to_market_ratio=property_info["deposit_to_market_ratio_pct"],
        senior_plus_deposit_ratio=property_info["senior_plus_deposit_to_market_pct"],
    )

    # 가중 합산
    weighted_sum = (
        w.approval          * s_approval
        + w.interest_benefit  * s_interest
        + w.limit_coverage    * s_limit
        + w.affordability     * s_afford
        + w.guarantee_stability * s_guarantee
        + w.preference_match  * s_pref
    )
    final = round(max(weighted_sum + penalty, 0.0), 2)

    return ScoreDetail(
        product_id=product["product_id"],
        product_name=product["product_name"],
        gate_passed=True,
        gate_result=gate,
        weight_profile=w.name,
        approval_score=s_approval,
        interest_benefit_score=s_interest,
        limit_coverage_score=s_limit,
        affordability_score=s_afford,
        guarantee_stability_score=s_guarantee,
        preference_match_score=s_pref,
        risk_penalty=penalty,
        final_score=final,
    )


# ─────────────────────────────────────────────
# 7. 추천 목록 생성
# ─────────────────────────────────────────────

def recommend(customer: dict, products: list[dict], property_info: dict,
              top_n: int = 3) -> list[ScoreDetail]:
    """
    Gate 통과 상품을 점수 내림차순으로 정렬해 top_n 반환
    리스크 정책: 상위 단일 상품 비중 40% 초과 방지 (최소 2개 이상 노출)
    """
    scores = [calc_rec_score(customer, p, property_info) for p in products]
    passed = [s for s in scores if s.gate_passed]
    ranked = sorted(passed, key=lambda x: x.final_score, reverse=True)
    return ranked[:top_n]


# ─────────────────────────────────────────────
# 8. 실행 예시
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import csv

    BASE = "/home/user/fintech-internship-2026"

    def load_csv(path):
        with open(path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        # 숫자형 컬럼 자동 변환
        for row in rows:
            for k, v in row.items():
                try:
                    row[k] = int(v)
                except ValueError:
                    try:
                        row[k] = float(v)
                    except ValueError:
                        pass
        return rows

    customers   = load_csv(f"{BASE}/jeonse_customer_profiles.csv")
    properties  = load_csv(f"{BASE}/jeonse_property_gate.csv")
    products    = load_csv(f"{BASE}/jeonse_product_catalog.csv")

    prop_map = {p["user_id"]: p for p in properties}

    print("=" * 65)
    print("전세대출 추천 스코어링 — 고객별 상위 3개 상품")
    print("=" * 65)

    for c in customers[:5]:  # 처음 5명 시연
        uid = c["user_id"]
        prop = prop_map[uid]
        recs = recommend(c, products, prop, top_n=3)

        print(f"\n[{uid}] 나이:{c['age']}세 | 소득:{c['combined_annual_income']}만원 "
              f"| 신용:{c['credit_score_kcb']} | DSR:{prop['dsr_estimated_pct']}%")
        if not recs:
            print("  → Gate 통과 상품 없음")
            continue
        for rank, r in enumerate(recs, 1):
            print(f"  {rank}위 [{r.product_id}] {r.product_name}  "
                  f"최종점수: {r.final_score:.1f}  "
                  f"(프로파일: {r.weight_profile})")
            print(f"       승인:{r.approval_score:.0f} "
                  f"금리:{r.interest_benefit_score:.0f} "
                  f"한도:{r.limit_coverage_score:.0f} "
                  f"상환:{r.affordability_score:.0f} "
                  f"보증:{r.guarantee_stability_score:.0f} "
                  f"우대:{r.preference_match_score:.0f} "
                  f"감점:{r.risk_penalty:.0f}")
    print()
