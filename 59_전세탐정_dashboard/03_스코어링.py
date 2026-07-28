"""03 스코어링 — clean.parquet을 읽어, 이미 학습된 LightGBM 모델(dashboard/model/)로
위험도점수(0~100)를 매겨 scored.parquet으로 저장한다.

여기서는 모델을 다시 학습하지 않는다 — dashboard/train_model.py가 만든 모델을 그대로 불러와 쓴다.
04_시각화.py는 이 결과를 새로 계산하지 않고 읽기만 하며, 사이드바 슬라이더로는 등급 재분류만 한다.

실행:
    python 03_스코어링.py
"""
import json

import joblib
import pandas as pd

import common as C


def load_model_bundle():
    model = joblib.load(C.MODEL_PATH)
    scaler = joblib.load(C.SCALER_PATH)
    meta = json.load(open(C.META_PATH, encoding="utf-8"))
    return model, scaler, meta


def build_model_input(df, meta):
    X = df.rename(columns={"보증완료월": "보증완료_월", "보증완료연도": "보증완료_연도"})
    X = X.drop(columns=["일련번호", "대위변제여부", "선순위채권비율"])
    X = pd.get_dummies(X, columns=["시도", "주택구분"], drop_first=True)
    for c in meta["feature_columns"]:
        if c not in X.columns:
            X[c] = False
    return X[meta["feature_columns"]]


def main():
    df = pd.read_parquet(C.CLEAN_PARQUET)
    model, scaler, meta = load_model_bundle()

    X = build_model_input(df, meta)
    X[meta["numeric_columns"]] = scaler.transform(X[meta["numeric_columns"]])

    prob = model.predict_proba(X)[:, 1]
    df["위험도점수"] = (prob * 100).round(1)

    df.to_parquet(C.SCORED_PARQUET, index=False)

    gate_ok = df["거래량"] >= C.GATE_MIN_TRADE_COUNT
    print(f"채점 완료: {len(df):,}건 (Gate 통과 {gate_ok.sum():,} / 판단보류 {(~gate_ok).sum()})")
    print(f"평균 위험도점수: {df['위험도점수'].mean():.1f}")
    print(f"정답(실제 대위변제) 평균 점수: {df.loc[df['대위변제여부'] == 1, '위험도점수'].mean():.1f}")
    print(f"정상 평균 점수: {df.loc[df['대위변제여부'] == 0, '위험도점수'].mean():.1f}")
    print(f"저장: {C.SCORED_PARQUET}")


if __name__ == "__main__":
    main()
