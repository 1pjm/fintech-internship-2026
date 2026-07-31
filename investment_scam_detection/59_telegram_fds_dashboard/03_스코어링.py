"""
03_스코어링.py — clean.parquet → scored.parquet

telegram_fds_event.ipynb 8단계 `classify_event()` / `build_reason_badges()`를
그대로 이식했습니다. PRD 9번 Scope의 설계 원칙에 따라 **가중합 점수를 쓰지
않습니다** — "거래량·가격이 함께 집중됐는가"라는 게이트를 통과한 사건만,
사후 하락·복수 소스 집중·공시 여부로 5개 상태 중 하나로 나눕니다.

- `score(df, thresholds)`: 04에서 슬라이더 값이 바뀔 때마다 다시 호출됩니다
  (03을 단독 실행하면 common.py의 기본 임계값으로 한 번 채점해 파일로 저장).
- `alert_list(df)`: "주의 패턴 관찰" 상태만 모은 경보 목록.
- `summary(df)`: KPI 카드 5장에 쓰는 숫자.

실행: python 03_스코어링.py  (clean.parquet을 기본 임계값으로 채점해 저장만 합니다)
"""

import numpy as np
import pandas as pd

import common as C


def _flag_columns(df, thresholds):
    """규칙별 열 이름 -> 임계값을 적용해 불리언 플래그 열을 만듭니다."""
    out = df.copy()

    out["volume_ratio_anomaly"] = out["event_max_volume_ratio"] >= thresholds["거래량 배율"]
    out["volume_robust_z_anomaly"] = out["event_volume_robust_z"] >= thresholds["거래량 MAD z-score"]
    out["volume_concentrated"] = out["volume_ratio_anomaly"] | out["volume_robust_z_anomaly"]

    out["price_concentrated"] = out["event_peak_abnormal_return_pct"] >= thresholds["사건구간 초과수익률"]

    post_ok = out["post_data_status"] == "15거래일 관찰 완료"
    out["post_underperformed"] = post_ok & (out["post_relative_return_pct"] <= thresholds["사후 상대수익률 하락"])
    out["post_large_drawdown"] = post_ok & (out["post_max_drawdown_pct"] <= thresholds["사후 최대낙폭"])

    out["multi_source_concentrated"] = (
        out["volume_concentrated"] & out["price_concentrated"] & out["news_concentrated"]
    )
    return out


def classify_event(row):
    """8단계 classify_event()와 동일한 판정 트리. Gate(시장 데이터 확인) 먼저."""
    if row["market_data_status"] != "확인":
        return "판단 불가"

    market_concentration = bool(row["volume_concentrated"]) and bool(row["price_concentrated"])
    post_decline = row["post_data_status"] == "15거래일 관찰 완료" and (
        bool(row["post_underperformed"]) or bool(row["post_large_drawdown"])
    )

    if market_concentration and (post_decline or bool(row["multi_source_concentrated"])):
        return "주의 패턴 관찰"
    if market_concentration and bool(row["material_disclosure_observed"]):
        return "공식 정보 동반 변동"
    if market_concentration:
        return "단기 집중 패턴 관찰"
    return "특이 패턴 미관찰"


def build_reason_badges(row):
    """build_reason_badges()와 동일. 판정에 쓰인 조건을 그대로 문장으로 노출."""
    badges = []

    if row["market_data_status"] != "확인":
        badges.append(f"시장 데이터: {row['market_data_status']}")
    else:
        if row["volume_ratio_anomaly"]:
            badges.append("기준 중앙값 대비 거래량 이상")
        if row["volume_robust_z_anomaly"]:
            badges.append("MAD 기준 거래량 이상치")
        if row["price_concentrated"]:
            badges.append("코스닥 대비 단기 초과상승")
        if row["post_data_status"] == "15거래일 관찰 완료":
            if row["post_underperformed"]:
                badges.append("언급 후 코스닥 대비 하락")
            if row["post_large_drawdown"]:
                badges.append("언급 후 고점 대비 큰 하락")
        else:
            badges.append(f"사후 데이터: {row['post_data_status']}")

    if row["channel_count"] >= 2:
        badges.append("복수 Telegram 채널 언급")
    if row["news_concentrated"]:
        badges.append("언급 시점 뉴스 집중")
    if row["similar_article_count"] >= 2:
        badges.append("유사 기사 반복 관찰")
    if row["press_release_expression_observed"]:
        badges.append("보도자료성 표현 관찰")

    # 언론사 티어(6-A) 배지 — 개별 매체를 단정하지 않고 "구성" 패턴만 표시.
    # PRD "언론사 티어 판정 원칙": pattern_status에는 반영하지 않음.
    if row.get("low_tier_targeted_concentration"):
        badges.append(
            f"포털 CP 매체 없이 저티어 매체에 광고성 표현 기사 집중"
            f"({int(row['low_tier_targeted_count'])}건, 공시 미확인)"
        )
    elif row.get("single_low_tier"):
        badges.append("단일 저티어(CP 미확인) 출처의 광고성 표현 기사(약한 정황)")

    if row["material_disclosure_observed"]:
        badges.append("중요 공시 후보 제목 관찰")
    else:
        badges.append(row["disclosure_status"])

    if row["news_status"] in {"미조회", "조회 실패", "기사 미확인", "데이터 부족"}:
        badges.append(f"뉴스: {row['news_status']}")

    if not badges:
        badges.append("현재 규칙의 특이 패턴 미관찰")
    return "; ".join(badges)


def score(df, thresholds=None):
    """clean 데이터를 임계값으로 다시 채점합니다. 04가 슬라이더를 바꿀 때마다 부릅니다."""
    thresholds = thresholds or C.THRESHOLDS
    out = _flag_columns(df, thresholds)

    # low_tier_* 보조 플래그 (노트북 6-A와 동일 — has_cp_source는 02에서 이미 bool로 정리됨).
    if "has_cp_source" in out.columns:
        out["low_tier_targeted_concentration"] = (
            (~out["has_cp_source"])
            & (out["low_tier_targeted_count"] >= 2)
            & (~out["material_disclosure_observed"])
        )
        out["single_low_tier"] = (
            (out["distinct_press"] == 1)
            & (~out["has_cp_source"])
            & (out["low_tier_targeted_count"] >= 1)
            & (~out["material_disclosure_observed"])
        )
    else:
        out["low_tier_targeted_concentration"] = False
        out["single_low_tier"] = False

    out["pattern_status"] = out.apply(classify_event, axis=1)
    out["pattern_status"] = pd.Categorical(
        out["pattern_status"], categories=C.ALL_GRADES, ordered=True
    )
    out["reason_badges"] = out.apply(build_reason_badges, axis=1)
    out["등급"] = out["pattern_status"].astype(str)
    out["액션"] = out["등급"].map(C.ACTIONS)

    return out.sort_values(["pattern_status", "event_anchor_at"]).reset_index(drop=True)


def alert_list(df):
    """경보 목록 — '주의 패턴 관찰' 상태만. 종목명은 빼고 사건ID만 남깁니다(익명화 원칙)."""
    alerts = df[df["pattern_status"] == "주의 패턴 관찰"].copy()
    alerts["사건ID"] = alerts["event_id"].map(C.short_event_id)
    cols = [
        "사건ID", "event_id", "event_anchor_at", "mention_session", "등급",
        "event_max_volume_ratio", "event_peak_abnormal_return_pct",
        "post_relative_return_pct", "post_max_drawdown_pct",
        "mention_count", "channel_count", "reason_badges", "액션",
    ]
    return alerts[[c for c in cols if c in alerts.columns]]


def summary(df):
    """KPI 카드 5장에 쓰는 숫자."""
    total = len(df)
    caution = int((df["pattern_status"] == "주의 패턴 관찰").sum())
    undecided = int((df["pattern_status"] == "판단 불가").sum())
    judged = total - undecided
    caution_df = df[df["pattern_status"] == "주의 패턴 관찰"]
    quiet_df = df[df["pattern_status"] == "특이 패턴 미관찰"]

    return {
        "점검한 사건": total,
        "판단보류": undecided,
        "이상 발생": caution,
        "발생 비율(%)": round(caution / total * 100, 1) if total else 0.0,
        "판단 가능 비율(%)": round(judged / total * 100, 1) if total else 0.0,
        "평균 거래량배율(주의군)": round(caution_df["event_max_volume_ratio"].mean(), 1) if len(caution_df) else None,
        "주의군 사후 평균(%p)": round(caution_df["post_relative_return_pct"].mean(), 1) if len(caution_df) else None,
        "미관찰군 사후 평균(%p)": round(quiet_df["post_relative_return_pct"].mean(), 1) if len(quiet_df) else None,
    }


def main():
    if not C.CLEAN_PARQUET.exists():
        print("clean.parquet이 없습니다. 먼저 02_전처리.py를 실행하세요.")
        raise SystemExit(1)

    df = pd.read_parquet(C.CLEAN_PARQUET)
    scored = score(df, C.THRESHOLDS)
    scored.to_parquet(C.SCORED_PARQUET, index=False)

    stats = summary(scored)
    print(f"채점 완료: {len(scored)}행 -> {C.SCORED_PARQUET}")
    print(scored["pattern_status"].value_counts().reindex(C.ALL_GRADES).to_string())
    print()
    for k, v in stats.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
