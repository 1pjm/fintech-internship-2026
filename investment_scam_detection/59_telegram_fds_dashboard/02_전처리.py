"""
02_전처리.py — raw_data.csv → clean.parquet

트랙 A(이전 분석 가져오기)입니다. `telegram_fds_event.ipynb`(v2.3)가 이미
Telegram 수집 → 종목 추출 → 사건 묶기 → 시장·뉴스·공시 정황 → 규칙 판정까지
전부 끝낸 뒤 내보낸 결과(사건상세 시트, 494건)를 raw_data.csv로 그대로 받습니다.

그래서 여기서 하는 "전처리"는 33회차의 1~4단계(수집·결측·중복·도메인 규칙)를
다시 하는 게 아니라, **스키마를 검증하고 자료형을 맞추는 것**입니다.
- 이상치를 지우지 않습니다 (33회차 원칙 ③ 보존 + 표시 — 거래량 41배 같은 값이
  바로 우리가 찾으려는 사건입니다).
- pattern_status·reason_badges는 03에서 임계값을 슬라이더로 바꿀 때마다 다시
  계산하므로, 여기서는 원본(노트북 계산값)을 "참고용" 그대로 들고만 갑니다.

실행: python 02_전처리.py
"""

import sys

import numpy as np
import pandas as pd

import common as C

# 사건상세 시트에서 반드시 있어야 하는 핵심 열 (없으면 이후 단계가 전부 깨짐).
REQUIRED_COLUMNS = [
    "event_id", "ticker", "stock_name", "event_anchor_at", "mention_session",
    "market_event_date", "market_data_status", "channel_count",
    "event_max_volume_ratio", "event_volume_robust_z",
    "event_peak_abnormal_return_pct",
    "post_data_status", "post_relative_return_pct", "post_max_drawdown_pct",
    "news_concentrated", "material_disclosure_observed",
    "distinct_press", "has_cp_source", "low_tier_targeted_count", "low_tier_ratio",
]

# tz-aware 문자열로 내려오는 시각 열 (사건상세 시트 기준 — event_start_at/end_at은
# 사건 지속시간 계산에만 쓰고 화면에는 event_anchor_at만 노출합니다).
DATETIME_COLUMNS = ["event_anchor_at", "event_start_at", "event_end_at"]
DATE_ONLY_COLUMNS = ["market_event_date"]


def load_raw(path):
    if not path.exists():
        print(f"원본 파일이 없습니다: {path}")
        print("telegram_fds_event.ipynb 11단계에서 만든 사건상세 데이터를 이 경로에 두세요.")
        sys.exit(1)
    return pd.read_csv(path, encoding="utf-8-sig", dtype={"ticker": str})


def validate_schema(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"필수 열이 없습니다: {missing}")


def clean(df):
    df = df.copy()

    # 업무 키(event_id)는 노트북에서 sha1 해시로 만들어 유일하지만, 재실행·재병합
    # 과정에서 중복이 섞였을 가능성을 대비해 한 번 더 확인합니다.
    before = len(df)
    df = df.drop_duplicates(subset=["event_id"], keep="last")
    dropped = before - len(df)
    if dropped:
        print(f"중복 event_id {dropped}건 제거")

    # 시각·날짜 열: 문자열로 읽혔으므로 datetime으로 변환합니다.
    for col in DATETIME_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=False)
    for col in DATE_ONLY_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.normalize()

    # 사건 언급일(정렬·필터용 파생 열) — 원본 열을 고치지 않고 새 열만 추가합니다.
    df["event_date"] = df["event_anchor_at"].dt.date

    # 시가총액: 정수, 결측은 "확인 안 됨"으로 남김(0으로 채우면 실제 소형주와
    # 구분이 안 됩니다).
    if "market_cap_krw" in df.columns:
        df["market_cap_krw"] = pd.to_numeric(df["market_cap_krw"], errors="coerce")

    # 카운트형 열은 정수로, 결측은 0 (해당 정황이 없었다는 뜻과 같음).
    count_cols = [
        "mention_count", "channel_count", "article_count",
        "near_event_article_count", "baseline_article_count",
        "similar_article_count", "distinct_press", "low_tier_targeted_count",
        "roundup_count", "disclosure_count", "material_disclosure_count",
    ]
    for col in count_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 불리언 열 (문자열 "True"/"False"로 읽혔을 수 있어 명시적으로 변환).
    bool_cols = [
        "news_concentrated", "material_disclosure_observed", "has_cp_source",
        "press_release_expression_observed",
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower().map(
                {"true": True, "false": False, "1": True, "0": False}
            ).fillna(False)

    # low_tier_ratio: 분모(distinct_press)가 0인 사건은 노트북에서 이미 0.0으로
    # 방어되어 있습니다 — 여기서는 방어가 유지됐는지만 확인합니다.
    if "low_tier_ratio" in df.columns:
        bad = df["low_tier_ratio"].isna().sum()
        if bad:
            print(f"low_tier_ratio 결측 {bad}건 — 0.0으로 채움 (분모 0 방어)")
            df["low_tier_ratio"] = df["low_tier_ratio"].fillna(0.0)

    return df


def main():
    df = load_raw(C.RAW_CSV)
    validate_schema(df)
    df = clean(df)

    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(C.CLEAN_PARQUET, index=False)

    print(f"전처리 완료: {len(df)}행 x {len(df.columns)}열 -> {C.CLEAN_PARQUET}")
    print("기간:", df["event_date"].min(), "~", df["event_date"].max())
    print("market_data_status 분포:")
    print(df["market_data_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
