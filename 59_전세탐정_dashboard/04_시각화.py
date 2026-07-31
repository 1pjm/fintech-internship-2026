"""04 시각화 — 전세탐정 위험 모니터링 대시보드.

새로운 계산은 하지 않는다. 03이 매긴 위험도점수를 읽어서 보여주고,
사이드바에서 등급 컷오프·체크리스트 기준을 바꾸면 그 값으로만 다시 분류한다.

실행:
    streamlit run 04_시각화.py
"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import common as C

st.set_page_config(page_title="전세탐정 — 위험 모니터링", page_icon="🏚️", layout="wide")
C.set_korean_font()


@st.cache_data
def load_scored(path):
    return pd.read_parquet(path)


if not C.SCORED_PARQUET.exists():
    st.error("03단계 결과가 없습니다. 앞 단계를 먼저 실행하세요.")
    st.code("python 02_전처리.py && python 03_스코어링.py", language="bash")
    st.stop()

data = load_scored(C.SCORED_PARQUET)
data["기간라벨"] = data["보증완료연도"].astype(
    str) + "-" + data["보증완료월"].astype(str).str.zfill(2)

with st.sidebar:
    st.header("등급 컷오프")
    st.caption("여기서 바꾼 값은 **화면에서만** 다시 등급을 매긴다 (모델 재추론 없음).")
    caution_cutoff = st.slider(
        "주의 컷오프(점)", 10.0, 60.0, C.DEFAULT_CAUTION_CUTOFF, 1.0)
    danger_cutoff = st.slider("위험 컷오프(점)", 60.0, 99.0,
                              C.DEFAULT_DANGER_CUTOFF, 1.0)

    st.header("체크리스트 기준")
    kkang_th = st.slider("깡통지수 과다 기준", 0.3, 1.5, 0.8, 0.05)
    senior_th = st.slider("선순위채권비율 과다 기준", 0.0, 0.5, 0.10, 0.01)

    st.header("조회 범위")
    sido_all = sorted(data["시도"].unique())
    pick_sido = st.multiselect("시도", sido_all, default=sido_all)

    house_all = sorted(data["주택구분"].unique())
    pick_house = st.multiselect("주택구분", house_all, default=house_all)

    month_labels = sorted(data["기간라벨"].unique())
    start_label, end_label = st.select_slider(
        "보증완료월 기간", options=month_labels, value=(month_labels[0], month_labels[-1]))

    st.divider()
    st.caption(f"읽는 파일: `{C.SCORED_PARQUET.name}`")

if not pick_sido or not pick_house:
    st.warning("시도와 주택구분을 하나 이상 선택해 주세요.")
    st.stop()

start_i, end_i = month_labels.index(start_label), month_labels.index(end_label)
allowed_labels = set(month_labels[start_i:end_i + 1])

view = data[data["시도"].isin(pick_sido) & data["주택구분"].isin(pick_house)
            & data["기간라벨"].isin(allowed_labels)]

if view.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

view = C.score(view, caution_cutoff, danger_cutoff)
alerts = C.alert_list(view)
stats = C.summary(view)

st.title("🏚️ 전세탐정 — 보증금 미반환 위험 모니터링")
st.caption(f"{start_label} ~ {end_label} · {len(pick_sido)}개 시도 · {len(pick_house)}개 주택구분 · "
           f"{len(view):,}건 · 03단계 결과(LightGBM 예측 확률)를 읽어 표시")

kpi = st.columns(5)
kpi[0].metric("점검한 계약수", f"{stats['점검한 계약수']:,}",
              f"판단보류 {stats['판단보류']}", delta_color="off")
kpi[1].metric("위험 등급", f"{stats['위험 발생']}건",
              f"{stats['발생 비율(%)']}%", delta_color="off")
kpi[2].metric("주의 등급", f"{stats['주의 발생']}건")
kpi[3].metric("평균 위험도점수", f"{stats['평균 위험도점수']}점")
kpi[4].metric("실제 대위변제 비율", f"{stats['실제 대위변제 비율(%)']}%")

if alerts.empty:
    st.success("현재 기준을 넘은 계약이 없습니다.")
else:
    top = alerts.iloc[0]
    st.error(
        f"**[{top['등급']} · {top['위험도점수']:.0f}점] {top['시도']} {top['주택구분']} · {top['기간라벨']}** "
        f"— 전세가율 {top['전세가율']:.0%} · 깡통지수 {top['깡통지수']:.2f} "
        f"→ {C.ACTIONS['위험']}"
    )

tab_list, tab_chart, tab_data = st.tabs(["📋 위험 매물 목록", "📊 그래프", "🗂 데이터"])

with tab_list:
    if alerts.empty:
        st.info("위험 등급 계약이 없습니다.")
    else:
        checks = {
            "깡통지수 과다": view["깡통지수"] >= kkang_th,
            "선순위채권 과다": view["선순위채권비율"] >= senior_th,
            "갱신요구권 저조": view["갱신요구권행사비율"] <= 0.10,
            "전세가율 과다": view["전세가율"] >= 0.90,
        }

        col_rule, col_sort = st.columns(2)
        f_rule = col_rule.selectbox("체크 규칙", ["전체"] + list(C.RULES))
        f_sort = col_sort.selectbox("정렬", ["위험도점수 높은 순", "최신순", "시도"])

        shown = alerts
        if f_rule != "전체":
            hit_idx = view.index[checks[f_rule]]
            shown = shown[shown.index.isin(hit_idx)]
        if f_sort == "최신순":
            shown = shown.sort_values(["보증완료연도", "보증완료월"], ascending=False)
        elif f_sort == "시도":
            shown = shown.sort_values(["시도", "위험도점수"], ascending=[True, False])

        st.dataframe(
            shown[["시도", "주택구분", "기간라벨", "전세가율", "깡통지수", "선순위채권비율",
                   "위험도점수", "등급", "대위변제여부"]],
            hide_index=True, width="stretch", height=420,
            column_config={
                "위험도점수": st.column_config.ProgressColumn(
                    "위험도점수", format="%.0f", min_value=0, max_value=100),
                "전세가율": st.column_config.NumberColumn("전세가율", format="%.2f"),
                "깡통지수": st.column_config.NumberColumn("깡통지수", format="%.2f"),
                "선순위채권비율": st.column_config.NumberColumn("선순위채권비율", format="%.2f"),
                "대위변제여부": st.column_config.NumberColumn("실제 대위변제"),
            },
        )
        st.caption(f"{len(shown)}건 표시 · 전체 위험 등급 {len(alerts)}건")

        st.download_button(
            "이 목록 CSV로 내려받기",
            shown.to_csv(index=False).encode("utf-8-sig"),
            file_name="위험매물_목록.csv", mime="text/csv",
        )

        st.divider()
        st.markdown("**무엇부터 확인하나**")
        for name, (col, weight, guide) in C.RULES.items():
            hit = int(checks[name].sum())
            if hit:
                st.markdown(
                    f"- **{name}** ({hit}건, SHAP 기여 {weight:.0%}) — {guide}")

with tab_chart:
    left, right = st.columns([3, 2])

    with left:
        rate = (
            view.groupby("시도", observed=True)
            .apply(lambda g: (g["등급"] == "위험").mean() * 100, include_groups=False)
            .sort_values()
        )
        avg_rate = rate.mean()
        fig, ax = plt.subplots(figsize=(8, 3.2))
        bars = ax.barh(rate.index, rate.values,
                       color=[C.RED if v >= avg_rate else C.MUTED for v in rate.values])
        ax.bar_label(bars, fmt="%.1f%%", padding=3)
        top_region = rate.idxmax() if not rate.empty else "-"
        C.style_axis(ax, f"{top_region} 지역이 위험 등급 비율이 가장 높다", "비율(%)")
        st.pyplot(fig)
        plt.close(fig)

    with right:
        grades = view["등급"].value_counts().reindex(
            C.ALL_GRADES).fillna(0).astype(int)
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        bars = ax.bar(grades.index, grades.values, color=[
                      C.GRADE_COLORS[g] for g in grades.index])
        ax.bar_label(bars, fmt="%d", padding=3)
        C.style_axis(
            ax, f"전체 {len(view):,}건 중 위험 {int(grades['위험']):,}건", "건수")
        ax.set_yscale("symlog")
        ax.set_ylim(top=grades.values.max() * 3)
        st.pyplot(fig)
        plt.close(fig)

    monthly = view.groupby("기간라벨")["위험도점수"].mean().sort_index()
    fig, ax = plt.subplots(figsize=(11, 3.2))
    ax.plot(monthly.index, monthly.values, marker="o",
            markersize=4, color=C.BLUE, label="평균 위험도점수")
    ax.axhline(danger_cutoff, color=C.RED, linestyle="--",
               label=f"위험 기준 {danger_cutoff:.0f}점")
    ax.axhline(caution_cutoff, color=C.ORANGE, linestyle="--",
               label=f"주의 기준 {caution_cutoff:.0f}점")
    over = monthly[monthly >= danger_cutoff]
    over_desc = ", ".join(over.index) if not over.empty else "없음"
    C.style_axis(ax, f"평균 위험도점수가 위험 기준을 넘은 달: {over_desc}", "위험도점수")
    step = max(1, len(monthly.index) // 12)
    ax.set_xticks(range(0, len(monthly.index), step))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.legend(frameon=False)
    st.pyplot(fig)
    plt.close(fig)

with tab_data:
    st.markdown("**열 목록과 자료형**")
    st.dataframe(
        pd.DataFrame(
            {"열": data.columns, "자료형": data.dtypes.astype(str).values}),
        hide_index=True, width="stretch", height=280,
    )

    st.markdown("**앞부분 미리보기**")
    st.dataframe(data.head(30), hide_index=True, width="stretch")

    st.info("원본 데이터가 바뀌었거나 전처리·모델을 다시 학습했다면 아래를 실행한 뒤 새로고침한다.")
    st.code("python 02_전처리.py && python 03_스코어링.py", language="bash")
