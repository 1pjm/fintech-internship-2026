"""
실서비스용 모델을 학습해서 dashboard/model/ 에 저장한다.
modeling/전세사기예측_AUC 비교.ipynb 에서 검증된 파이프라인 그대로 사용:
stratify 분할 -> 수치형 StandardScaler -> LGBM(scale_pos_weight).

사용법:
    cd dashboard
    python3 train_model.py
"""
import json
import os

import joblib
import lightgbm as lgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA_PATH = "../data/전세보증대위변제현황_깡통라벨.xlsx"
MODEL_DIR = "model"


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # 깡통전세여부는 깡통지수(임대보증금액+선순위채권금액)/주택가액)와 중복인 파생 라벨이라 제외
    df = pd.read_excel(DATA_PATH).drop(columns=["일련번호", "깡통전세여부"])
    dt = pd.to_datetime(df["보증완료월"])
    df["보증완료_연도"] = dt.dt.year
    df["보증완료_월"] = dt.dt.month
    df = df.drop(columns=["보증완료월"])

    df = pd.get_dummies(df, columns=["시도", "주택구분"], drop_first=True)

    X = df.drop(columns="대위변제여부")
    y = df["대위변제여부"].astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=1, stratify=y)

    dummy_cols = [c for c in X.columns if c.startswith("시도_") or c.startswith("주택구분_")]
    numeric_cols = [c for c in X.columns if c not in dummy_cols]

    scaler = StandardScaler()
    X_tr = X_tr.copy()
    X_te = X_te.copy()
    X_tr[numeric_cols] = scaler.fit_transform(X_tr[numeric_cols])
    X_te[numeric_cols] = scaler.transform(X_te[numeric_cols])

    scale_pos_weight = len(y[y == 0]) / len(y[y == 1])
    model = lgb.LGBMClassifier(random_state=1, verbose=-1, scale_pos_weight=scale_pos_weight)
    model.fit(X_tr, y_tr)

    from sklearn.metrics import f1_score, roc_auc_score

    proba = model.predict_proba(X_te)[:, 1]
    print("검증용 F1(threshold=0.5):", round(f1_score(y_te, (proba >= 0.5).astype(int)), 3))
    print("검증용 AUC:", round(roc_auc_score(y_te, proba), 3))

    # 서빙 시 필요한 전부를 저장: 모델, 스케일러, 컬럼 순서/목록, 원-핫 기준 카테고리 값
    joblib.dump(model, f"{MODEL_DIR}/lgbm_model.joblib")
    joblib.dump(scaler, f"{MODEL_DIR}/scaler.joblib")

    sido_values = sorted(pd.read_excel(DATA_PATH)["시도"].unique().tolist())
    housetype_values = sorted(pd.read_excel(DATA_PATH)["주택구분"].unique().tolist())

    meta = {
        "feature_columns": X.columns.tolist(),  # 학습에 쓰인 최종 컬럼 순서 (원-핫 포함)
        "numeric_columns": numeric_cols,
        "dummy_columns": dummy_cols,
        "sido_values": sido_values,          # get_dummies(drop_first=True) 기준값 복원용
        "housetype_values": housetype_values,
        "scale_pos_weight": scale_pos_weight,
    }
    with open(f"{MODEL_DIR}/meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {MODEL_DIR}/lgbm_model.joblib, scaler.joblib, meta.json")


if __name__ == "__main__":
    main()
