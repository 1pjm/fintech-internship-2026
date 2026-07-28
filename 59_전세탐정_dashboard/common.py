"""전세탐정 모니터링 대시보드 공용 모듈 — 경로·기준·색·점수 함수.

02(전처리)·03(스코어링)·04(시각화)가 전부 이 파일을 가져다 쓴다.
규칙을 하나 추가하고 싶으면 RULES에 한 줄만 넣으면 04의 사이드바·체크리스트에도 그대로 반영된다.
"""
from pathlib import Path

import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_XLSX = BASE_DIR.parent / "data" / "전세보증대위변제현황_깡통라벨.xlsx"
CLEAN_PARQUET = DATA_DIR / "clean.parquet"
SCORED_PARQUET = DATA_DIR / "scored.parquet"

# 이미 학습된 모델(전세사기예측_AUC 비교.ipynb와 같은 파이프라인)을 그대로 가져다 쓴다 — 재학습하지 않는다.
MODEL_DIR = BASE_DIR.parent / "dashboard" / "model"
MODEL_PATH = MODEL_DIR / "lgbm_model.joblib"
SCALER_PATH = MODEL_DIR / "scaler.joblib"
META_PATH = MODEL_DIR / "meta.json"

# 등급 컷오프 기본값. 0.80은 코드 파일(전세사기예측_AUC 비교.ipynb)에서 F1이 최대가 되는 임계값(best_t)을
# 100점 만점으로 옮긴 것이다 — 임의로 정한 숫자가 아니다.
DEFAULT_CAUTION_CUTOFF = 30.0
DEFAULT_DANGER_CUTOFF = 80.0

# Gate: 이 미만이면 그 시도x주택유형x월 그룹의 실거래 표본이 너무 적어 그룹 통계(시세 등) 자체가
# 불안정하다고 보고 "판단보류"로 뺀다.
GATE_MIN_TRADE_COUNT = 100

ALL_GRADES = ["판단보류", "안전", "주의", "위험"]
GRADE_COLORS = {"판단보류": "#8B8272", "안전": "#0072B2", "주의": "#E69F00", "위험": "#D55E00"}
ACTIONS = {
    "판단보류": "그룹 표본 부족 — 개별 실거래가·등기부 직접 확인",
    "안전": "정기 모니터링만",
    "주의": "등기부 선순위채권·주변 시세 재확인 권고",
    "위험": "보증보험(HUG) 가입 여부·선순위채권 우선 확인, 현장 확인 우선순위 상향",
}

# 체크리스트 규칙: {규칙이름: (컬럼, SHAP 전역중요도 기준 가중치, 확인 안내문구)}
# 가중치는 실제 가중합에 쓰는 값이 아니라 "이 규칙이 실제로 얼마나 중요했는지"를 보여주는 참고값이다 —
# LightGBM은 39개 피처의 비선형 조합을 쓰기 때문에 사람이 짠 가중합과 다르다.
RULES = {
    "깡통지수 과다": ("깡통지수", 0.32, "등기부등본 근저당권·선순위채권 설정 확인"),
    "선순위채권 과다": ("선순위채권비율", 0.15, "선순위채권 설정 여부 확인"),
    "갱신요구권 저조": ("갱신요구권행사비율", 0.06, "임대인의 과거 세입자 교체 이력 확인"),
    "전세가율 과다": ("전세가율", 0.04, "시세 대비 보증금 직접 재계산"),
}

RED = "#D55E00"
ORANGE = "#E69F00"
BLUE = "#0072B2"
MUTED = "#C9D2DC"


def set_korean_font():
    import koreanize_matplotlib  # noqa: F401  import만으로 한글 폰트가 자동 적용된다
    plt.rcParams["axes.unicode_minus"] = False


def style_axis(ax, title=None, ylabel=None):
    if title:
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)


def grade_from_score(s, gate_ok, caution_cutoff, danger_cutoff):
    if not gate_ok:
        return "판단보류"
    if s >= danger_cutoff:
        return "위험"
    if s >= caution_cutoff:
        return "주의"
    return "안전"


def score(view, caution_cutoff, danger_cutoff):
    """03이 이미 매긴 위험도점수·거래량을 바탕으로 등급만 다시 매긴다.
    사이드바 슬라이더가 바뀔 때마다 04에서 호출되지만, 모델 재추론은 없다 — 재분류(bucketing)만 한다."""
    out = view.copy()
    gate_ok = out["거래량"] >= GATE_MIN_TRADE_COUNT
    out["등급"] = [
        grade_from_score(s, ok, caution_cutoff, danger_cutoff)
        for s, ok in zip(out["위험도점수"], gate_ok)
    ]
    return out


def alert_list(view):
    return view[view["등급"] == "위험"].sort_values("위험도점수", ascending=False)


def summary(view):
    n = len(view)
    danger = int((view["등급"] == "위험").sum())
    hold = int((view["등급"] == "판단보류").sum())
    return {
        "점검한 계약수": n,
        "판단보류": hold,
        "위험 발생": danger,
        "발생 비율(%)": round(danger / n * 100, 2) if n else 0.0,
        "주의 발생": int((view["등급"] == "주의").sum()),
        "평균 위험도점수": round(view["위험도점수"].mean(), 1) if n else 0.0,
        "실제 대위변제 비율(%)": round(view["대위변제여부"].mean() * 100, 2) if n else 0.0,
    }
