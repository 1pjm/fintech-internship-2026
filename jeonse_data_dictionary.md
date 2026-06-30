# 전세대출 샘플 데이터 컬럼 설명

---

## 1. `jeonse_customer_profiles.csv` — 고객 개인·재무 정보

| 컬럼명 | 설명 | 예시 | Gate 연관 항목 |
|---|---|---|---|
| `user_id` | 고객 고유 ID | U0001 | — |
| `age` | 만 나이 | 35 | 연령조건충족 |
| `birth_year` | 출생 연도 | 1991 | 연령조건충족 |
| `birth_month` | 출생 월 | 12 | 연령조건충족 |
| `gender` | 성별 (남/여) | 여 | — |
| `employment_type` | 고용 형태 (정규직/계약직/자영업/프리랜서/무직/학생) | 계약직 | — |
| `marital_status` | 혼인 상태 (미혼/기혼/이혼/사별) | 기혼 | 상품별필수조건충족 (A3) |
| `marriage_years` | 혼인 기간 (년) — 미혼이면 0 | 4 | 상품별필수조건충족 (A3, 7년 이내) |
| `has_newborn_within_2y` | 대출 접수일 기준 2년 내 출산 여부 (Y/N) | N | 상품별필수조건충족 (A4) |
| `is_household_head` | 세대주 또는 예비 세대주 여부 (Y/N) | Y | 세대주조건충족 |
| `is_homeless` | 세대원 전원 무주택 여부 (Y/N) | Y | 무주택조건충족 |
| `annual_income` | 본인 연소득 (만원) | 3609 | 소득조건충족 |
| `spouse_income` | 배우자 연소득 (만원) — 미혼이면 0 | 1294 | 소득조건충족 |
| `combined_annual_income` | 부부합산 연소득 (만원) = annual_income + spouse_income | 4903 | 소득조건충족, DSR기준이하 |
| `credit_score_kcb` | KCB 신용점수 (450~1000) | 795 | 신용점수기준충족 |
| `total_existing_debt` | 기존 부채 총액 (만원) — DSR 계산에 사용 | 6383 | DSR기준이하 |
| `net_asset` | 순자산 (만원) — 자산 - 부채 | 0 | 소득조건충족 (순자산 3.45억 이하 확인) |
| `has_existing_jeonse_loan` | 동일 보증기관 기존 전세대출 보유 여부 (Y/N) | N | 중복대출없음 |

---

## 2. `jeonse_property_gate.csv` — 임차 주택 및 전세계약 정보

| 컬럼명 | 설명 | 예시 | Gate 연관 항목 |
|---|---|---|---|
| `user_id` | 고객 고유 ID (profiles와 조인 키) | U0001 | — |
| `region` | 임차 주택 시·도 | 대전 | 보증금한도충족 (수도권/비수도권 차등) |
| `district` | 임차 주택 구·군 | 서구 | — |
| `is_capital_area` | 수도권 여부 (Y/N) — 서울·경기·인천 = Y | N | 보증금한도충족 |
| `property_type` | 주택 유형 (아파트/연립/다세대/단독/오피스텔) | 다세대 | 주택유형충족 |
| `exclusive_area_sqm` | 전용면적 (㎡) | 80.3 | 전용면적충족 (정부상품 85㎡ 이하) |
| `deposit_amount` | 전세 보증금 (만원) | 2627 | 보증금한도충족 |
| `market_price_estimate` | 임차 주택 시세 (만원) | 4558 | 깡통전세감점, 선순위채권감점 (RiskPenalty) |
| `senior_bond_amount` | 선순위채권 금액 (만원) | 1114 | 선순위채권감점 (RiskPenalty) |
| `loan_amount_requested` | 신청 대출금액 (만원) ≈ 보증금의 65~80% | 1842 | LimitCoverageScore, DSR 계산 |
| `deposit_to_market_ratio_pct` | 보증금/시세 비율 (%) | 57.6 | 깡통전세감점: 90% 초과 시 −20점 |
| `senior_plus_deposit_to_market_pct` | (선순위채권 + 보증금) / 시세 비율 (%) | 82.1 | 선순위채권감점: 80% 초과 시 −10점 |
| `settlement_date` | 잔금일 / 대출 실행 예정일 (YYYY-MM-DD) | 2026-10-01 | 정보완전성충족 |
| `repayment_method` | 상환 방식 (원리금균등/원금균등/만기일시) | 원리금균등 | DSR 계산 방식 결정 |
| `interest_rate_type` | 금리 방식 (고정/변동/혼합) | 고정 | PreferenceMatchScore |
| `financial_sector` | 금융권역 (은행/2금융권) | 은행 | DSR기준이하 (은행 40%, 2금융권 50%) |
| `dsr_estimated_pct` | 예상 DSR (%) = (기존+신규 연간 상환액) / 연소득 × 100 | 6.3 | DSR기준이하, AffordabilityScore |
| `info_completeness` | 필수 정보 완전 수집 여부 (Y/N) | Y | 정보완전성충족 |

---

## 3. `jeonse_product_catalog.csv` — 전세대출 상품 정보

| 컬럼명 | 설명 | 예시 |
|---|---|---|
| `product_id` | 상품 코드 (A1~A6) | A1 |
| `product_name` | 상품명 | 버팀목전세자금 |
| `product_type` | 상품 유형 (전세자금대출/월세보증금대출) | 전세자금대출 |
| `age_min` | 신청 가능 최소 연령 (만 나이) | 19 |
| `age_max` | 신청 가능 최대 연령 (만 나이) — 제한 없으면 99 | 99 |
| `income_limit_single` | 단독 소득 기준 연소득 상한 (만원) | 5000 |
| `income_limit_couple` | 부부합산 소득 기준 연소득 상한 (만원) | 5000 |
| `net_asset_limit` | 순자산 상한 (만원) — 34500 = 3.45억 | 34500 |
| `credit_score_min` | 최저 신용점수 기준 (KCB) | 600 |
| `deposit_limit_capital` | 수도권 보증금 상한 (만원) | 12000 |
| `deposit_limit_non_capital` | 비수도권 보증금 상한 (만원) | 8000 |
| `ltv_limit_pct` | LTV 한도 (%) — 보증금 대비 대출 비율 | 80 |
| `max_loan_capital` | 수도권 최대 대출 한도 (만원) | 12000 |
| `max_loan_non_capital` | 비수도권 최대 대출 한도 (만원) | 8000 |
| `base_rate_min` | 기본 금리 하한 (%) | 2.5 |
| `base_rate_max` | 기본 금리 상한 (%) | 3.5 |
| `max_area_sqm` | 전용면적 상한 (㎡) — 제한 없으면 9999 | 85 |
| `guarantee_agency` | 보증 기관 (HUG / HF / SGI) | HUG |
| `dsr_limit_pct` | DSR 한도 (%) | 40 |
| `marriage_within_7y_required` | 혼인 7년 이내 필수 여부 (Y/N) — A3 전용 | N |
| `newborn_within_2y_required` | 2년 내 출산 필수 여부 (Y/N) — A4 전용 | N |
| `youth_only` | 만 19~34세 청년 전용 여부 (Y/N) — A2·A5 전용 | N |
| `allowed_property_types` | 신청 가능 주택 유형 (`\|` 구분) | 아파트\|연립\|다세대\|단독\|오피스텔 |
| `target_customer` | 주요 대상 고객 설명 | 일반 무주택 세대주 |
| `notes` | 기타 특이사항 | 부부합산 연소득 5000만원 이하 무주택 세대주 |

---

### 상품 코드 요약

| 상품 코드 | 상품명 | 핵심 조건 |
|---|---|---|
| A1 | 버팀목전세자금 | 연소득 5000만원 이하, 일반 무주택 세대주 |
| A2 | 청년전용 버팀목전세자금 | 만 19~34세, 연소득 5000만원 이하 |
| A3 | 신혼부부 버팀목전세자금 | 혼인 7년 이내, 연소득 7500만원 이하 |
| A4 | 신생아특례 버팀목대출 | 2년 내 출산, 연소득 1.3억(맞벌이 2억) 이하 |
| A5 | 청년전용 보증부월세대출 | 만 19~34세, 단독세대주, 보증금 4500만원 이하 |
| A6 | 일반 전세자금대출(은행) | 소득·자산 제한 없음, 신용점수 650점 이상 |
