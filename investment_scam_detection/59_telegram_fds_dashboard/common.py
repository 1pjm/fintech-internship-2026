"""
common.py — 경로 · 임계치 · 규칙 · 등급 · 공통 스타일 함수.
02_전처리.py / 03_스코어링.py / 04_시각화.py 가 전부 이 파일을 import해서 씁니다.
규칙을 하나 고치면 이 파일만 고치면 됩니다 (04는 손대지 않습니다).

데이터 출처: telegram_fds_event.ipynb(v2.3, "6-A. 언론사 티어" 포함) 최종 산출물
(telegram_fds_event_overview.csv / telegram_fds_event_dashboard.xlsx, 2026-06 실행 결과, 494건).
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.font_manager as fm

# ---------------------------------------------------------------------------
# 경로
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_CSV = DATA_DIR / "raw_data.csv"
CLEAN_PARQUET = DATA_DIR / "clean.parquet"
SCORED_PARQUET = DATA_DIR / "scored.parquet"
# 사건별 일별 시세·코스닥지수·관련 뉴스·관련 공시 원문 목록 — dashboard_.html(최종 산출물)에
# 내장돼 있던 실데이터를 그대로 꺼내온 것(사건상세 CSV에는 요약 열만 있고 원본 시계열/기사
# 목록은 없음). "🔎 사건 상세" 탭에서만 사용 — 목록 화면(02/03 결과)에는 영향 없음.
EVENT_DETAIL_JSON = DATA_DIR / "event_market_news_disclosures.json"

# ---------------------------------------------------------------------------
# 분석 대상 · 배치 기준 정보 (PRD 9번 Scope / 노트북 0단계와 동일)
# ---------------------------------------------------------------------------
ANALYSIS_WINDOW = ("2026-06-01", "2026-07-01")
TARGET_MARKET = "코스닥 보통주"
TARGET_MAX_MARKET_CAP_KRW = 30_000_000_000  # 300억 원 미만
BATCH_REFERENCE_DATE = "2026-07-21"  # 이번 노트북 실행(시가총액 스냅샷) 기준일

# ---------------------------------------------------------------------------
# 규칙 — telegram_fds_event.ipynb 8단계 classify_event()를 그대로 이식.
# ---------------------------------------------------------------------------
# 본 프로젝트는 PRD 9번 Scope의 설계 원칙에 따라 "가중치 합산 점수"를 쓰지 않고
# 점수 없는 규칙 기반(불리언 AND/OR) 분류를 씁니다. 그래서 RULES는 (검사할 열,
# 단위, 슬라이더에 보여줄 설명) 3튜플이며, "가중치"는 없습니다 — 대신 03에서
# market_concentration(필수 게이트) · post_decline/multi_source(보조 OR 조건)
# 구조로 조합합니다. 슬라이더로 바꾸는 것은 각 열의 "임계값"입니다.
RULES = {
    "거래량 배율": (
        "event_max_volume_ratio", "배",
        "사건 구간 최고 거래량 / 기준 구간 중앙값 거래량. 이 배수 이상이면 '거래량 집중'",
    ),
    "거래량 MAD z-score": (
        "event_volume_robust_z", "",
        "로그 거래량의 MAD 기반 robust z-score. 표준편차 대신 MAD를 써서 급등 자체에 흔들리지 않게 함",
    ),
    "사건구간 초과수익률": (
        "event_peak_abnormal_return_pct", "%p",
        "사건 구간 고점 수익률 − 같은 기간 코스닥 지수 수익률. 이 값 이상이면 '가격 집중'",
    ),
    "사후 상대수익률 하락": (
        "post_relative_return_pct", "%",
        "사후 15거래일 코스닥 대비 상대수익률. 이 값 이하로 떨어지면 '사후 하락'",
    ),
    "사후 최대낙폭": (
        "post_max_drawdown_pct", "%",
        "사후 15거래일 중 고점 대비 최대 낙폭. 이 값 이하로 떨어지면 '사후 하락'",
    ),
}

# 노트북 9단계에 실제로 쓰인 기본값 (설정및한계 시트 그대로).
THRESHOLDS = {
    "거래량 배율": 3.0,
    "거래량 MAD z-score": 3.5,
    "사건구간 초과수익률": 7.0,
    "사후 상대수익률 하락": -10.0,
    "사후 최대낙폭": -15.0,
}

# 사이드바 슬라이더 범위 (low, high, step) — 전부 float로 통일 (Streamlit 슬라이더는
# min/max/value/step의 자료형이 섞이면 StreamlitAPIException이 납니다).
SLIDER_RANGE = {
    "거래량 배율": (1.0, 20.0, 0.5),
    "거래량 MAD z-score": (1.0, 10.0, 0.5),
    "사건구간 초과수익률": (1.0, 30.0, 0.5),
    "사후 상대수익률 하락": (-40.0, 0.0, 1.0),
    "사후 최대낙폭": (-60.0, 0.0, 1.0),
}

# 경보(사건ID 클릭 전) 목록에서 "무엇부터 확인하나" — 규칙과 짝인 확인 순서.
CHECKLIST = {
    "volume_ratio_anomaly": "기준 중앙값 대비 거래량이 실제로 튀었는지, 거래정지·신규상장 등 왜곡 요인은 없는지 확인",
    "price_concentrated": "코스닥 지수 대비 초과 상승폭이 실제로 임계값을 넘었는지 시장시계열로 재확인",
    "multi_source_concentrated": "평소엔 없던 거래량·뉴스 신호가 언급 시점에만 몰렸는지, 원래 이슈 종목은 아닌지 확인",
    "material_disclosure_observed": "공시 원문을 직접 열어 실제 중요 공시인지, 호재로 오인될 문구는 아닌지 확인",
    "low_tier_targeted_concentration": "포털 CP 매체 없이 저티어 매체에만 광고성 기사가 몰렸는지 원문으로 확인(개별 매체 단정 금지)",
}

# ---------------------------------------------------------------------------
# 등급 → 색상 → 액션  (pattern_status 5단계, PRD 9번 Scope "상태 분류"와 동일)
# ---------------------------------------------------------------------------
ALL_GRADES = [
    "주의 패턴 관찰",
    "단기 집중 패턴 관찰",
    "공식 정보 동반 변동",
    "특이 패턴 미관찰",
    "판단 불가",
]

# 58회차 색각 안전 팔레트를 그대로 쓰되, 상태별로 하나씩 배정합니다.
BLUE = "#0072B2"
ORANGE = "#E69F00"
RED = "#D55E00"
GREEN = "#2E8B57"
MUTED = "#8A8F99"
RED_STRONG = "#B23A24"

GRADE_COLORS = {
    "주의 패턴 관찰": RED_STRONG,
    "단기 집중 패턴 관찰": ORANGE,
    "공식 정보 동반 변동": BLUE,
    "특이 패턴 미관찰": GREEN,
    "판단 불가": MUTED,
}

ACTIONS = {
    "주의 패턴 관찰": "근거 배지·뉴스·공시 원문을 사람이 직접 검토 (사후 하락 또는 복수 신호 집중까지 확인된 상태)",
    "단기 집중 패턴 관찰": "사후 관찰을 계속 지켜본다 — 아직 하락·복수 신호까지는 확인되지 않음",
    "공식 정보 동반 변동": "공시 원문을 확인한다 — 공시 자체가 정상 호재라는 판정은 아님",
    "특이 패턴 미관찰": "정기 모니터링만 유지 — 안전/정상 확정은 아님",
    "판단 불가": "핵심 시장 데이터가 부족 — '정상'이 아니라 '모른다'는 뜻. 데이터 보강 후 재평가",
}

# ---------------------------------------------------------------------------
# 공통 스타일
# ---------------------------------------------------------------------------
FONT_FILE_CANDIDATES = [
    Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
]
FONT_NAME_CANDIDATES = ["NanumGothic", "Malgun Gothic", "Apple SD Gothic Neo", "AppleGothic"]


def set_korean_font():
    """앱 맨 위에서 한 번만 호출. 한글이 □□□로 깨지는 것을 막습니다."""
    for path in FONT_FILE_CANDIDATES:
        if path.exists():
            fm.fontManager.addfont(str(path))
            name = fm.FontProperties(fname=str(path)).get_name()
            mpl.rcParams["font.family"] = name
            mpl.rcParams["axes.unicode_minus"] = False
            return name
    installed = {f.name for f in fm.fontManager.ttflist}
    for name in FONT_NAME_CANDIDATES:
        if name in installed:
            mpl.rcParams["font.family"] = name
            mpl.rcParams["axes.unicode_minus"] = False
            return name
    mpl.rcParams["axes.unicode_minus"] = False
    return None


def style_axis(ax, title=None, ylabel=None):
    """부록 31 스타일: 왼쪽 정렬 굵은 제목, 위·오른쪽 테두리 제거, y축 그리드만."""
    if title:
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)


def short_event_id(event_id):
    """사건ID를 목록에서 짧게 표시 (EVT-XXXXXXXX -> XXXXXXXX)."""
    if not isinstance(event_id, str):
        return event_id
    return event_id.replace("EVT-", "")[:8]
