# 전세탐정 — 위험 진단 대시보드

`전세사기예측_AUC비교_SHAP추가.ipynb` 실행 결과를 "서비스화된 XAI"로 구조화한 것.
그래프 6개를 그대로 보여주는 대신, **사용자용 화면(주소 입력 → 결과 카드 + 이유 3개 + 체크리스트)**과
**관리자용 화면(모델 전체 설명 + 검증 지표)** 두 개로 나눴다. 사용자 화면은 정적 예시가 아니라
실제로 학습된 모델을 호출하는 Flask 백엔드에 연결되어 있다.

## 구성

| 파일 | 역할 |
| --- | --- |
| `train_model.py` | `data/전세보증대위변제현황_피처완료_.xlsx`로 운영용 LightGBM 모델을 학습해 `model/`에 저장 |
| `address_parse.py` | 주소 문자열에서 시/도를 추출 (API 키 없이, 시도명·주요 시/군 이름 매칭) |
| `house_type_risk.py` | 주택구분별 고정 위험도 상수 (학습데이터에서 그대로 추출) |
| `realtime_features.py` | (시도, 주택구분, 계약월)에 대해 실거래가 API를 그 자리에서 호출해 시세·갱신계약·건물특성 그룹 피처 계산 |
| `feature_explain_map.py` | 모델 변수 → 사용자 언어 변환 테이블 (SHAP 부호에 따라 위험 높임/낮춤 문장 + 체크리스트 매핑, 원-핫 컬럼명도 처리) |
| `risk_card.py` | `build_risk_card(prob, shap_row)` — 확률 + SHAP 값을 받아 위험 등급·TOP3 요인·체크리스트로 변환 |
| `test_risk_card.py` | 노트북에 실제 출력된 매물(X_tr #17310)의 SHAP 값으로 파이프라인 검증 |
| `analyze_core.py` | "주소+계약정보 → 위험 카드" 계산 로직 본체 (모델 로드, 실거래가 조회, SHAP 계산). `app.py`와 `gradio_app.py`가 공유 |
| `app.py` | Flask 백엔드. `/api/meta`(주택구분 목록), `/api/analyze`(주소+계약정보 → 위험 카드) |
| `index.html` | 사용자가 실제로 입력하는 대시보드 (`/api/analyze` 호출), Artifact로도 게시됨 |
| `gradio_app.py` | Colab에서 로컬 설치 없이 실행하는 Gradio 버전. `analyze_core`를 그대로 재사용해 계산 로직은 Flask 버전과 동일 |
| `colab_run.ipynb` | Colab에서 셀 실행만으로 `gradio_app.py`를 띄우는 노트북 (클론 → 설치 → 키 입력 → 실행) |

## 자동으로 채워지는 값 vs 직접 입력해야 하는 값

주소만으로는 계약 고유 정보를 알 수 없기 때문에 입력을 두 종류로 나눴다.

- **직접 입력 (계약서·등기부등본 기준)**: 임대보증금액, 선순위채권금액, 주택가액, 계약월
- **자동 계산 (주소 + 주택구분 + 계약월 → 실거래가 API)**: 시세_평균전세보증금, 시세대비보증금비율,
  월세전환비율, 평균보증금인상률, 갱신계약비율, 갱신요구권행사비율, 평균건축연도, 평균전용면적, 거래량

실거래가 API 조회에 실패하면(키 미설정, 네트워크 오류, 해당 조합 표본 없음 등) 자동으로 값을
꾸며내지 않고 중립값(0)으로 대체한 뒤, 응답의 `fetch_error`/`filled_defaults`로 그 사실을
그대로 알린다 — 화면에는 경고 배너로 표시된다.

## 파이프라인

```
주소 입력 -> address_parse.parse_sido() -> 시/도
시/도 + 주택구분 + 계약월 -> realtime_features.compute_group_features() -> 그룹 피처 9종 (실시간 API 호출)
사용자 직접 입력(보증금/선순위채권/주택가액) + 그룹 피처 + house_type_risk 상수
  -> 학습된 LightGBM 모델(model.predict_proba) -> 위험 확률
  -> shap.TreeExplainer -> SHAP 값
  -> build_risk_card() -> 위험 등급·TOP3 요인·체크리스트
  -> feature_explain_map.py로 변수명을 사용자 언어로 변환
```

## 등급 컷오프의 근거

"위험" 등급 컷오프(0.80)는 임의로 정한 게 아니라, 노트북 6장(AUC vs F1)에서 실제로
F1이 최대가 되는 임계값(`best_t=0.80`)을 그대로 가져왔다.

## Colab에서 바로 실행하기 (설치 없이, 링크로 접속)

로컬에 아무것도 설치하지 않고, 링크만으로 접속 가능한 웹 데모가 필요할 때 쓰는 방법이다.

1. `dashboard/colab_run.ipynb`를 Colab에서 연다 —
   `https://colab.research.google.com/github/1pjm/fintech-internship-2026/blob/claude/renewal-contract-features-api-25d1gr/dashboard/colab_run.ipynb`
2. 셀을 위에서부터 순서대로 실행한다 (저장소 클론 → 패키지 설치 → API 키 입력 → 실행).
3. 마지막 셀 실행 후 출력되는 `https://xxxxx.gradio.live` 링크를 클릭하면 바로 접속된다.

**한계**: 이 링크는 Colab 세션이 켜져 있는 동안만 유효한 임시 링크다(무료 Colab은 유휴 시
자동 종료, 보통 최대 몇 시간). 계속 쓰려면 노트북을 다시 실행해야 하고, 매번 링크가 바뀐다.
저장소가 private이면 클론 단계에서 GitHub 토큰이 필요하다(노트북 안에 안내 있음).
UI는 `index.html`만큼 정교하지 않지만(Gradio 기본 컴포넌트), 계산 로직(`analyze_core.py`)은
Flask 버전과 완전히 동일하다.

항상 켜져 있는 고정 링크가 필요하면(발표 당일 안정적으로 쓰고 싶다면), Render나 Hugging Face
Spaces 같은 상시 호스팅에 Flask 앱(`app.py`)을 배포하는 쪽이 낫다 — 필요하면 그 설정 파일도
추가해줄 수 있다.

## 로컬에서 실행하기

```bash
cd dashboard
pip install -r requirements.txt

# 1) 모델 학습 (한 번만 하면 됨, model/ 에 결과 저장됨)
python3 train_model.py

# 2) 실거래가 API 키 설정 (국토부 공공데이터포털에서 발급, API 4종 모두 필요)
export SERVICE_KEY_APT=...   # 아파트
export SERVICE_KEY_RH=...    # 연립다세대
export SERVICE_KEY_SH=...    # 단독/다가구
export SERVICE_KEY_OFFI=...  # 오피스텔

# 3) 백엔드 실행
python3 app.py
```

브라우저에서 `http://localhost:5000` 접속 → "매물 진단" 탭에서 주소·주택구분·계약월·
임대보증금액·선순위채권금액·주택가액을 입력하고 "위험도 분석" 클릭.

API 키를 설정하지 않아도 서버는 정상 동작하지만, 그룹 피처가 전부 0으로 채워지고
경고 배너가 뜬다(파이프라인 검증용).

## 한계 / 다음 단계
- 주소 → 시/도 변환은 지오코딩 API 없이 문자열 매칭만 쓰기 때문에, 시/도명이 아예 빠진
  주소(예: "고성군"만 입력, 강원/경남 모두 있는 지명)는 정확하지 않을 수 있다.
- 실거래가 API는 (시/도, 주택구분, 월) 단위 그룹 통계만 제공하므로, "이 매물"이 아니라
  "이 지역·유형·시기의 평균적인 매물"에 대한 근사치다.
- Flask 개발 서버(`app.run(debug=True)`)는 로컬 프로토타입용이며, 실제 서비스 배포에는
  gunicorn 등 WSGI 서버와 HTTPS, 요청 검증 강화가 필요하다.
- `feature_explain_map.py`의 체크리스트는 상위 8개 변수만 채워뒀다. 하위 변수는 "-"로 비워둠.
