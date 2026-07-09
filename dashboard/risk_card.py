"""
SHAP 값 -> 사용자에게 보여줄 "위험도 카드" 데이터로 변환하는 파이프라인.

    SHAP 값 계산 (노트북에서 이미 계산됨)
      -> 위험도를 올린/낮춘 변수 TOP3 추출
      -> 변수명을 사용자 언어로 변환 (feature_explain_map.py)
      -> 설명 문장 생성
      -> 체크리스트 연결

등급 경계값(0.80)은 임의로 정한 게 아니라, 노트북 6장(AUC vs F1)에서 실제로
F1이 최대가 되는 임계값(best_t=0.80)을 그대로 가져온 것이다 — "몇 점 이상을
위험으로 볼지"의 운영 정책 근거를 모델 검증 결과와 일치시킨 것.
"""
import pandas as pd

from feature_explain_map import explain_feature

# 노트북 실행 결과(6장)에서 확인된 F1 최적 임계값. 운영 정책(위험 등급 컷오프)에 그대로 사용.
DANGER_THRESHOLD = 0.80
CAUTION_THRESHOLD = 0.30


def grade_from_probability(prob: float) -> str:
    if prob >= DANGER_THRESHOLD:
        return "위험"
    if prob >= CAUTION_THRESHOLD:
        return "주의"
    return "낮음"


def build_risk_card(prob: float, shap_row: pd.Series, top_n: int = 3) -> dict:
    """
    prob: model.predict_proba(...)의 대위변제(양성) 확률
    shap_row: 해당 매물 1건의 SHAP 값 (pd.Series, index=피처명)
    """
    ranked = shap_row.sort_values(ascending=False)

    risk_up = [explain_feature(f, v) for f, v in ranked[ranked > 0].head(top_n).items()]
    risk_down = [explain_feature(f, v) for f, v in ranked[ranked < 0].tail(top_n).sort_values().items()]

    checklist = []
    seen = set()
    for item in risk_up:
        c = item["checklist"]
        if c != "-" and c not in seen:
            checklist.append(c)
            seen.add(c)

    return {
        "risk_score": round(prob * 100, 1),
        "risk_grade": grade_from_probability(prob),
        "risk_up_factors": risk_up,
        "risk_down_factors": risk_down,
        "checklist": checklist,
    }
