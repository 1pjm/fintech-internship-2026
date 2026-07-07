# 갱신계약 피처 추가 (평균보증금인상률 / 갱신계약비율 / 갱신요구권행사비율)

`data/전세보증대위변제현황_피처추가.xlsx` (10컬럼, 50,054행)에 국토교통부 전월세 실거래가 API로
갱신계약 관련 피처 3개를 추가하는 파이프라인이다.

## 왜 이 API가 필요한가
현재 데이터셋에는 `일련번호/보증완료월/주택가액/임대보증금액/선순위채권금액/대위변제여부/시도/주택구분/전세가율/주택유형위험도`
뿐이라 갱신계약 여부, 종전 보증금, 갱신요구권 행사 여부를 알 수 없다. 이 3개 필드는
국토부 전월세 실거래가 API(아파트/연립다세대/단독다가구/오피스텔, 4종)에만 존재한다:
- `contractType` (신규/갱신) → 갱신계약비율
- `useRRRight` (Y/N) → 갱신요구권행사비율
- `deposit` vs `preDeposit` → 평균보증금인상률 (갱신계약만)

이 데이터는 개별 계약 단위라 학습데이터의 `일련번호` 1건씩과 직접 매칭은 안 되고,
**(시도, 주택구분, 계약연월) 단위로 집계한 값을 붙이는 방식**으로만 쓸 수 있다.

## 실행 순서

### 1. 실거래가 수집 (로컬 PC, 서비스키 필요 — 이 코드실행 환경은 apis.data.go.kr 호출이 막혀 있어서 여기선 못 돌림)
```bash
pip install requests
export SERVICE_KEY_APT=<아파트 API 디코딩 인증키>
export SERVICE_KEY_RH=<연립다세대 API 디코딩 인증키>
export SERVICE_KEY_SH=<단독다가구 API 디코딩 인증키>
export SERVICE_KEY_OFFI=<오피스텔 API 디코딩 인증키>
python fetch_realprice.py --start 202201 --end 202412 --out raw_transactions.csv
```
- 시도 17개 x 대표 시군구 1곳(`lawd_codes.py`) x 36개월 x API 4종 = 총 2,448회 호출.
- 데이터포털 트래픽 제한에 걸리면 `--sleep` 값을 늘릴 것.
- 마이페이지 URL이 `house_type_map.py`의 `API_ENDPOINTS`와 다르면 그 값으로 교체.
- **"디코딩(일반 인증키)"을 써야 함.** "인코딩" 키를 넣으면 이중 인코딩되어 인증 오류가 난다.
- 4개 API 중 일부가 아직 승인 대기라 403이 나면, 승인된 것만 `--types`로 지정해서 먼저 수집하고
  (예: `--types apt,rh,sh`), 나중에 나머지 승인되면 `--types offi`로 그 API만 같은 `--out` 파일에
  이어서 추가하면 된다(기존 apt/rh/sh 데이터는 중복 저장되지 않음).

### 2. 집계 (여기서 이어서 처리 가능, 인터넷 불필요)
```bash
python build_renewal_features.py --in raw_transactions.csv --out renewal_features.csv
```
`renewal_features_fine/coarse/national.csv` 3개 파일이 만들어진다 (세분화 단계별 대체용).

### 3. 원본 데이터에 merge
```bash
python merge_renewal_features.py \
    --base ../data/전세보증대위변제현황_피처추가.xlsx \
    --out ../data/전세보증대위변제현황_피처추가_갱신피처.xlsx
```
시도당 대표 시군구 1곳만 샘플링했기 때문에 (시도,주택구분,월) 조합이 비어있는 경우가 있다.
그럴 땐 (시도,API그룹,월) → (API그룹,월) 전국평균 → 전체평균 순으로 대체하고,
어느 단계에서 채워졌는지 `갱신피처_출처` 컬럼(`fine`/`coarse`/`national`/`overall_mean`)에 남긴다.

## 한계 (발표자료에 명시할 것)
- 시도당 대표 시군구 1곳만 조회 (17개 시도 전체 시군구 조회는 호출량이 너무 많아 샘플링함)
- 개별 계약 단위 매칭이 아니라 (시도,주택구분,월) 집계값을 붙인 것 — 같은 그룹 내 모든 건에 동일 값 부여
- 다중주택/주상복합은 API에 대응 유형이 없어 단독다가구 API 값으로 근사
