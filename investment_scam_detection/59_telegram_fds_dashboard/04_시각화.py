"""
04_시각화.py — 텔레그램 주식 정보방 FDS 모니터링 대시보드

새로운 계산은 하지 않습니다. 03_스코어링.py의 score()/summary()/alert_list()를
그대로 불러 화면에 보여주기만 하며, 사이드바에서 임계값을 바꾸면 그때만 다시
채점합니다(03과 같은 함수를 쓰므로 결과가 항상 일치합니다).

실행: streamlit run 04_시각화.py
"""

import importlib
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import common as C

scoring = importlib.import_module("03_스코어링")

st.set_page_config(
    page_title="텔레그램 주식 정보방 FDS",
    page_icon="🚨",
    layout="wide",
)

C.set_korean_font()


# ---------------------------------------------------------------------------
# 데이터 읽기 — 파일 읽기에만 캐시
# ---------------------------------------------------------------------------
@st.cache_data
def load_clean(path):
    return pd.read_parquet(path)


@st.cache_data
def load_event_detail(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if not C.CLEAN_PARQUET.exists():
    st.error("전처리 결과가 없습니다. 먼저 02_전처리.py를 실행하세요.")
    st.code("python 02_전처리.py && python 03_스코어링.py", language="bash")
    st.stop()

data = load_clean(C.CLEAN_PARQUET)

# ---------------------------------------------------------------------------
# 사이드바 — 임계값 슬라이더 + 조회 범위
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("판정 임계값")
    st.caption(
        "본 프로젝트는 가중치 합산 점수를 쓰지 않습니다(PRD 설계 원칙). "
        "여기서 바꾼 임계값은 **화면에서만** telegram_fds_event.ipynb 8단계 규칙을 다시 적용합니다."
    )

    thresholds = {}
    for name, (column, unit, help_text) in C.RULES.items():
        low, high, step = C.SLIDER_RANGE[name]
        thresholds[name] = st.slider(
            f"{name} ({unit})" if unit else name,
            low, high, C.THRESHOLDS[name], step,
            help=help_text,
        )

    st.header("조회 범위")
    sessions_all = sorted(data["mention_session"].dropna().unique())
    pick_sessions = st.multiselect("언급 세션", sessions_all, default=sessions_all)

    days = sorted(data["event_date"].dropna().unique())
    if days:
        start_day, end_day = st.select_slider(
            "언급일 기간", options=days, value=(days[0], days[-1]),
            format_func=lambda d: f"{d:%m-%d}",
        )
    else:
        start_day, end_day = None, None

    st.divider()
    st.caption(f"원본: `{C.RAW_CSV.name}` · 분석 기간 {C.ANALYSIS_WINDOW[0]} ~ {C.ANALYSIS_WINDOW[1]}")
    st.caption(f"시가총액 기준일 {C.BATCH_REFERENCE_DATE} · {C.TARGET_MARKET} 시가총액 300억 원 미만")

# ---------------------------------------------------------------------------
# 필터 적용 + 재채점
# ---------------------------------------------------------------------------
if not pick_sessions:
    st.warning("언급 세션을 하나 이상 선택해 주세요.")
    st.stop()

view_raw = data[
    data["mention_session"].isin(pick_sessions)
    & (data["event_date"] >= start_day)
    & (data["event_date"] <= end_day)
]
if view_raw.empty:
    st.warning("선택한 조건에 해당하는 사건이 없습니다. 조회 범위를 넓혀 주세요.")
    st.stop()

view = scoring.score(view_raw, thresholds)
alerts = scoring.alert_list(view)
stats = scoring.summary(view)

# ---------------------------------------------------------------------------
# 본문 상단 — 제목 · 캡션 · KPI · 배너
# ---------------------------------------------------------------------------
st.title("🚨 텔레그램 주식 정보방 FDS 모니터링")
st.caption(
    f"{start_day:%Y-%m-%d} ~ {end_day:%Y-%m-%d} · {len(pick_sessions)}개 언급 세션 · "
    f"{len(view):,}개 사건 · telegram_fds_event.ipynb 11단계 결과를 읽어 표시"
)
st.warning(
    "이 화면이 표시하는 상태는 참고 신호입니다. 불법·사기·시세조종 여부, 기업의 우량·부실 여부, "
    "매수·매도 적정성을 판정하지 않습니다. (PRD 10번 Constraints)",
    icon="⚠️",
)

kpi = st.columns(5)
kpi[0].metric("점검한 사건", f"{stats['점검한 사건']:,}", f"판단보류 {stats['판단보류']}", delta_color="off")
kpi[1].metric("주의 패턴 관찰", f"{stats['이상 발생']}건", f"{stats['발생 비율(%)']}%", delta_color="off")
kpi[2].metric("판단 가능 비율", f"{stats['판단 가능 비율(%)']}%")
kpi[3].metric(
    "평균 거래량배율(주의군)",
    f"{stats['평균 거래량배율(주의군)']}×" if stats["평균 거래량배율(주의군)"] is not None else "—",
)
hero_val = "—"
if stats["주의군 사후 평균(%p)"] is not None and stats["미관찰군 사후 평균(%p)"] is not None:
    hero_val = f"{stats['주의군 사후 평균(%p)']:+.1f}%p / {stats['미관찰군 사후 평균(%p)']:+.1f}%p"
kpi[4].metric("사후 검증(주의군/미관찰군)", hero_val, help="사후 15거래일 코스닥 대비 평균 상대수익률 — 북극성 지표(유효 위험 신호 적중률)의 참고 근거")

if alerts.empty:
    st.success("현재 기준을 넘은 사건이 없습니다.")
else:
    worst = alerts.sort_values("post_relative_return_pct", na_position="last").iloc[0]
    post_txt = (
        f"사후 {worst['post_relative_return_pct']:+.1f}%p"
        if pd.notna(worst["post_relative_return_pct"]) else "사후 관찰 미완료"
    )
    st.error(
        f"**[{worst['등급']}] 사건 {worst['사건ID']} · {pd.Timestamp(worst['event_anchor_at']):%m-%d %H시} · "
        f"{worst['mention_session']} · 거래량 {worst['event_max_volume_ratio']:.1f}× · "
        f"사건구간 초과수익률 {worst['event_peak_abnormal_return_pct']:+.1f}%p · {post_txt}** "
        f"→ {worst['액션']}"
    )

# ---------------------------------------------------------------------------
# 탭
# ---------------------------------------------------------------------------
tab_detail, tab_list, tab_chart, tab_data = st.tabs(
    ["🔎 사건 상세", "📋 경보 (익명)", "📊 그래프", "🗂 데이터"]
)

# ---- 🔎 사건 상세 -------------------------------------------------------
with tab_detail:
    st.caption(
        "목록은 사건 ID만 표시합니다(PRD 익명화 원칙). 사건을 하나 선택하면 오른쪽에 "
        "실제 조사에 필요한 종목명·시세·뉴스·공시가 함께 열립니다 — 목록을 훑을 때는 "
        "종목명이 판단을 앞서가지 않도록 가리고, 상세 검수 단계에서만 신원을 드러내는 설계입니다."
    )

    status_counts = view["pattern_status"].value_counts()
    status_options = ["전체"] + C.ALL_GRADES
    status_labels = {"전체": f"전체 ({len(view)})"}
    status_labels.update({s: f"{s} ({int(status_counts.get(s, 0))})" for s in C.ALL_GRADES})
    picked_status = st.pills(
        "상태 필터", status_options, default="전체",
        format_func=lambda s: status_labels[s], key="detail_status_filter",
    )
    detail_pool = view if picked_status == "전체" else view[view["pattern_status"] == picked_status]

    col_list, col_detail = st.columns([3, 2])

    with col_list:
        detail_view = detail_pool.copy()
        detail_view["사건ID"] = detail_view["event_id"].map(C.short_event_id)
        detail_view["등급"] = detail_view["pattern_status"].astype(str)
        picked = st.dataframe(
            detail_view[["사건ID", "event_anchor_at", "mention_session", "등급",
                         "event_max_volume_ratio", "post_relative_return_pct"]],
            hide_index=True, width="stretch", height=460,
            column_config={
                "사건ID": st.column_config.TextColumn("사건 ID"),
                "event_anchor_at": st.column_config.DatetimeColumn("언급 시각", format="YYYY-MM-DD HH:mm"),
                "mention_session": st.column_config.TextColumn("세션"),
                "등급": st.column_config.TextColumn("등급"),
                "event_max_volume_ratio": st.column_config.NumberColumn("거래량 배율", format="%.1f×"),
                "post_relative_return_pct": st.column_config.NumberColumn("사후 상대수익률(%)", format="%.1f"),
            },
            on_select="rerun", selection_mode="single-row", key="detail_table",
        )
        st.caption(f"{len(detail_view)}건 표시 — 행을 클릭하면 오른쪽에 상세가 열립니다.")

    selected_rows = picked["selection"]["rows"] if picked else []
    if selected_rows:
        sel = detail_view.iloc[selected_rows[0]]
    elif len(detail_view):
        sel = detail_view.iloc[0]
    else:
        sel = None

    with col_detail:
        if sel is None:
            st.info("선택한 상태에 해당하는 사건이 없습니다.")
        elif not C.EVENT_DETAIL_JSON.exists():
            st.warning("사건 상세(시세·뉴스·공시) 데이터 파일이 없습니다: event_market_news_disclosures.json")
        else:
            event_id = sel["event_id"]
            grade_color = C.GRADE_COLORS.get(sel["등급"], C.MUTED)
            st.markdown(f"#### {sel['stock_name']} · `{sel['ticker']}`")
            cap = int(sel["market_cap_krw"]) if pd.notna(sel.get("market_cap_krw")) else None
            st.caption(
                f"사건ID {sel['사건ID']} · "
                + (f"시가총액 {cap / 1e8:,.1f}억 원 (기준일 {C.BATCH_REFERENCE_DATE}) · " if cap else "")
                + f"{sel['mention_session']} 언급 · {sel['등급']}"
            )

            detail_data = load_event_detail(C.EVENT_DETAIL_JSON)
            series = detail_data["marketByEvent"].get(event_id)
            if series:
                s_df = pd.DataFrame(series)
                s_df["d"] = pd.to_datetime(s_df["d"])
                base_date = pd.to_datetime(sel.get("market_event_date"))
                base_row = s_df[s_df["d"] <= base_date].tail(1) if pd.notna(base_date) else s_df.tail(1)
                if base_row.empty:
                    base_row = s_df.head(1)
                base_c = float(base_row["c"].iloc[0])
                base_ix = float(base_row["ix"].iloc[0])
                base_date = base_row["d"].iloc[0]

                fig, (ax1, ax2) = plt.subplots(
                    2, 1, figsize=(6, 3.6), sharex=True,
                    gridspec_kw={"height_ratios": [2, 1]},
                )
                ax1.plot(s_df["d"], s_df["c"] / base_c * 100, color=C.BLUE, label="종목 가격(지수화)")
                ax1.plot(s_df["d"], s_df["ix"] / base_ix * 100, color=C.ORANGE, label="코스닥지수(지수화)")
                ax1.axvline(base_date, color=C.RED, linestyle="--", linewidth=1, label="반응 기준일")
                ax1.legend(fontsize=7, loc="upper left")
                C.style_axis(ax1, f"{base_date:%Y-%m-%d} = 100 기준")

                vol_colors = [C.RED if d == base_date else C.MUTED for d in s_df["d"]]
                ax2.bar(s_df["d"], s_df["v"], color=vol_colors, width=1.0)
                C.style_axis(ax2, None, "거래량")
                fig.autofmt_xdate(rotation=45)
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("이 사건은 시장 시계열 데이터가 없습니다(사건 구간 거래량 없음 등).")

            st.markdown("**판정 근거**")
            badges = [b for b in str(sel.get("reason_badges", "")).split("; ") if b]
            chip_html = "".join(
                f'<span style="display:inline-block;background:{grade_color}22;color:{grade_color};'
                f'border:1px solid {grade_color}55;border-radius:12px;padding:2px 10px;'
                f'margin:2px 4px 2px 0;font-size:0.82rem;">{b}</span>'
                for b in badges
            )
            st.markdown(chip_html or "표시할 근거가 없습니다.", unsafe_allow_html=True)

            st.divider()
            disc = detail_data["discByEvent"].get(event_id, [])
            st.markdown(f"**관련 공시 (OPEN DART)** · {len(disc)}건")
            if disc:
                for item in disc[:5]:
                    st.markdown(f"- [{item['r']}]({item['u']}) — {item['d']}")
            else:
                st.caption("관찰 기간 내 확인된 공시가 없습니다.")

            news = detail_data["newsByEvent"].get(event_id, [])
            st.markdown(f"**관련 뉴스** · {len(news)}건")
            if news:
                for item in news[:5]:
                    st.markdown(f"- [{item['t']}]({item['u']}) — {item['d']} · {item['p']}")
            else:
                st.caption("사건 전후로 확인된 뉴스가 없습니다.")

# ---- 📋 경보 -----------------------------------------------------------
with tab_list:
    st.caption("목록은 사건 ID만 표시합니다(PRD 익명화 원칙) — 종목명은 실무에서 상세 조회 시스템에서만 확인합니다.")
    if alerts.empty:
        st.info("기준을 넘은 사건이 없습니다.")
    else:
        col_sort, col_min_vol = st.columns(2)
        f_sort = col_sort.selectbox("정렬", ["거래량배율 높은 순", "사후수익률 낮은 순(최악부터)", "최신순"])
        f_min_vol = col_min_vol.slider("거래량배율 최소", 0.0, float(max(alerts["event_max_volume_ratio"].max(), 1.0)), 0.0)

        shown = alerts[alerts["event_max_volume_ratio"] >= f_min_vol]
        if f_sort == "거래량배율 높은 순":
            shown = shown.sort_values("event_max_volume_ratio", ascending=False)
        elif f_sort == "사후수익률 낮은 순(최악부터)":
            shown = shown.sort_values("post_relative_return_pct", na_position="last")
        else:
            shown = shown.sort_values("event_anchor_at", ascending=False)

        st.dataframe(
            shown.drop(columns=["event_id"]),
            hide_index=True, width="stretch", height=420,
            column_config={
                "사건ID": st.column_config.TextColumn("사건 ID"),
                "event_anchor_at": st.column_config.DatetimeColumn("언급 시각", format="YYYY-MM-DD HH:mm"),
                "mention_session": st.column_config.TextColumn("세션"),
                "등급": st.column_config.TextColumn("등급"),
                "event_max_volume_ratio": st.column_config.ProgressColumn(
                    "거래량 배율", format="%.1f×", min_value=0,
                    max_value=float(max(alerts["event_max_volume_ratio"].max(), 1.0)),
                ),
                "event_peak_abnormal_return_pct": st.column_config.NumberColumn("사건구간 초과수익률(%p)", format="%.1f"),
                "post_relative_return_pct": st.column_config.NumberColumn("사후 상대수익률(%)", format="%.1f"),
                "post_max_drawdown_pct": st.column_config.NumberColumn("사후 최대낙폭(%)", format="%.1f"),
                "mention_count": st.column_config.NumberColumn("언급 수"),
                "channel_count": st.column_config.NumberColumn("채널 수"),
                "reason_badges": st.column_config.TextColumn("판정 근거", width="large"),
                "액션": st.column_config.TextColumn("다음 행동", width="medium"),
            },
        )
        st.caption(f"{len(shown)}건 표시 · 전체 주의 패턴 관찰 {len(alerts)}건")

        st.download_button(
            "이 목록 CSV로 내려받기",
            shown.to_csv(index=False).encode("utf-8-sig"),
            file_name="telegram_fds_alerts.csv", mime="text/csv",
        )

        st.divider()
        st.markdown("**무엇부터 확인하나**")
        for rule, guide in C.CHECKLIST.items():
            if rule not in view.columns:
                continue
            hit = int(view.loc[view["pattern_status"] == "주의 패턴 관찰", rule].sum())
            if hit:
                st.markdown(f"- **{rule}** ({hit}건) — {guide}")

# ---- 📊 그래프 -----------------------------------------------------------
with tab_chart:
    left, right = st.columns([3, 2])

    with left:
        daily = (
            view[view["pattern_status"] == "주의 패턴 관찰"]
            .groupby("event_date").size()
        )
        all_days = pd.Index(sorted(view["event_date"].unique()), name="event_date")
        daily = daily.reindex(all_days, fill_value=0)

        fig, ax = plt.subplots(figsize=(8, 3.2))
        ax.bar(range(len(daily)), daily.values,
               color=[C.RED_STRONG if v else C.MUTED for v in daily.values])
        ax.set_xticks(range(0, len(daily), max(1, len(daily) // 10)))
        ax.set_xticklabels(
            [f"{d:%m-%d}" for d in daily.index[::max(1, len(daily) // 10)]], rotation=45, ha="right",
        )
        title = "날짜별 주의 패턴 관찰 발생 건수"
        if daily.max() > 0:
            peak_day = daily.idxmax()
            title = f"{peak_day:%m-%d}에 주의 패턴 관찰이 {int(daily.max())}건으로 가장 많았다"
        C.style_axis(ax, title, "건수")
        st.pyplot(fig)
        plt.close(fig)

    with right:
        grp = (
            view.groupby("pattern_status", observed=True)["post_relative_return_pct"]
            .mean().reindex(C.ALL_GRADES)
        )
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        colors = [C.GRADE_COLORS[g] if pd.notna(v) else C.MUTED for g, v in grp.items()]
        bars = ax.barh(grp.index, grp.fillna(0).values, color=colors)
        ax.bar_label(bars, labels=[f"{v:+.1f}%p" if pd.notna(v) else "—" for v in grp.values], padding=3)
        ax.axvline(0, color="#333333", linewidth=1)
        C.style_axis(ax, "패턴 상태별 사후 평균 상대수익률 — 북극성 지표 근거")
        st.pyplot(fig)
        plt.close(fig)
        st.caption("사후 15거래일, 코스닥 대비 평균 상대수익률. 참고 지표이며 인과관계 증명은 아닙니다.")

    st.divider()

    days_in_view = sorted(view["event_date"].unique())
    default_day = daily.idxmax() if daily.max() > 0 else days_in_view[0]
    pick_day = st.selectbox(
        "날짜", days_in_view, index=days_in_view.index(default_day),
        format_func=lambda d: f"{d:%Y-%m-%d}",
    )
    one_day = view[view["event_date"] == pick_day].sort_values("event_anchor_at")
    st.markdown(f"**{pick_day:%Y-%m-%d}에 언급된 사건 {len(one_day)}건**")
    st.dataframe(
        one_day[["event_id", "event_anchor_at", "mention_session", "pattern_status",
                 "event_max_volume_ratio", "post_relative_return_pct"]]
        .assign(event_id=one_day["event_id"].map(C.short_event_id))
        .rename(columns={"event_id": "사건ID", "event_anchor_at": "언급 시각",
                          "mention_session": "세션", "pattern_status": "상태",
                          "event_max_volume_ratio": "거래량 배율", "post_relative_return_pct": "사후 상대수익률(%)"}),
        hide_index=True, width="stretch",
    )
    st.caption("여러 사건이 겹쳐 나온 날은 특정 채널의 집중 언급이거나, 시황성 언급이 몰린 날일 수 있습니다.")

    st.divider()

    grades = view["pattern_status"].value_counts().reindex(C.ALL_GRADES).fillna(0).astype(int)
    fig, ax = plt.subplots(figsize=(11, 2.8))
    bars = ax.bar(grades.index, grades.values, color=[C.GRADE_COLORS[g] for g in grades.index])
    ax.bar_label(bars, fmt="%d", padding=3)
    C.style_axis(ax, "등급별 사건 수", "사건 수")
    if grades.max() > 0:
        ax.set_yscale("symlog")
    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(
        pd.DataFrame({
            "등급": C.ALL_GRADES,
            "사건 수": grades.values,
            "액션": [C.ACTIONS[g] for g in C.ALL_GRADES],
        }),
        hide_index=True, width="stretch",
    )

# ---- 🗂 데이터 -----------------------------------------------------------
with tab_data:
    st.markdown("**열 목록과 자료형**")
    st.dataframe(
        pd.DataFrame({"열": data.columns, "자료형": data.dtypes.astype(str).values}),
        hide_index=True, width="stretch", height=280,
    )

    st.markdown("**앞부분 미리보기 (원본, 필터 적용 전)**")
    st.dataframe(data.head(30), hide_index=True, width="stretch")

    st.info(
        f"이 데이터는 실시간이 아니라 telegram_fds_event.ipynb의 2026-06 배치 실행 결과입니다 "
        f"(시가총액 기준일 {C.BATCH_REFERENCE_DATE}). 노트북을 다시 돌린 뒤 새 raw_data.csv로 "
        f"교체하고 아래를 실행하면 최신화됩니다."
    )
    st.code("python 02_전처리.py && python 03_스코어링.py", language="bash")
