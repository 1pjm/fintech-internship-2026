"""
전세탐정 백엔드. 로컬에서 실행:

    cd dashboard
    export SERVICE_KEY_APT=... SERVICE_KEY_RH=... SERVICE_KEY_SH=... SERVICE_KEY_OFFI=...
    python3 app.py

그 다음 브라우저에서 http://localhost:5000 접속.
"""
import datetime
import json

import joblib
import numpy as np
import pandas as pd
import shap
from flask import Flask, jsonify, request, send_from_directory

from address_parse import parse_sido
from house_type_risk import HOUSE_TYPE_RISK
from realtime_features import compute_group_features
from risk_card import build_risk_card

app = Flask(__name__, static_folder=None)

MODEL = joblib.load("model/lgbm_model.joblib")
SCALER = joblib.load("model/scaler.joblib")
with open("model/meta.json", encoding="utf-8") as f:
    META = json.load(f)
EXPLAINER = shap.TreeExplainer(MODEL)


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


@app.get("/api/meta")
def api_meta():
    return jsonify({
        "sido_values": META["sido_values"],
        "housetype_values": META["housetype_values"],
    })


@app.post("/api/analyze")
def api_analyze():
    payload = request.get_json(force=True)

    address = (payload.get("address") or "").strip()
    house_type = payload.get("house_type")
    deposit = payload.get("deposit")          # 임대보증금액 (만원)
    senior_debt = payload.get("senior_debt")  # 선순위채권금액 (만원)
    house_value = payload.get("house_value")  # 주택가액 (만원)
    contract_month = payload.get("contract_month")  # "YYYY-MM", 없으면 이번 달

    errors = []
    sido = parse_sido(address) if address else None
    if not sido:
        errors.append("주소에서 시/도를 인식하지 못했습니다. 시/도명을 포함해서 다시 입력해주세요 (예: '서울특별시 강남구...').")
    if house_type not in META["housetype_values"]:
        errors.append("주택구분을 올바르게 선택해주세요.")
    for label, val in [("임대보증금액", deposit), ("선순위채권금액", senior_debt), ("주택가액", house_value)]:
        if val is None or float(val) < 0:
            errors.append(f"{label}을(를) 올바르게 입력해주세요.")
    if errors:
        return jsonify({"errors": errors}), 400

    deposit = float(deposit)
    senior_debt = float(senior_debt)
    house_value = float(house_value)

    if contract_month:
        y, m = contract_month.split("-")
        base_ym = f"{y}{int(m):02d}"
    else:
        today = datetime.date.today()
        base_ym = f"{today.year:04d}{today.month:02d}"

    try:
        group_features = compute_group_features(sido, house_type, base_ym, deposit_krw_10k=deposit)
        fetch_error = None
    except Exception as e:
        fetch_error = str(e)
        group_features = {k: None for k in [
            "시세_평균전세보증금", "시세대비보증금비율", "월세전환비율", "평균보증금인상률",
            "갱신계약비율", "갱신요구권행사비율", "평균건축연도", "평균전용면적", "거래량",
        ]}

    # 실거래가 조회가 안 됐거나 표본이 없으면(None) 모델이 처리 가능한 중립값(0)으로 대체하고
    # 그 사실을 응답에 남긴다 — 조용히 틀린 값을 채우지 않기 위해서.
    filled_defaults = []
    for k, v in group_features.items():
        if v is None:
            filled_defaults.append(k)
            group_features[k] = 0.0

    row = {
        "주택가액": house_value,
        "임대보증금액": deposit,
        "선순위채권금액": senior_debt,
        "전세가율": (deposit / house_value) if house_value else 0.0,
        "주택유형위험도": HOUSE_TYPE_RISK.get(house_type, 0.0),
        **group_features,
        "보증완료_연도": int(base_ym[:4]),
        "보증완료_월": int(base_ym[4:]),
    }
    for c in META["dummy_columns"]:
        row[c] = False
    if f"시도_{sido}" in row:
        row[f"시도_{sido}"] = True
    if f"주택구분_{house_type}" in row:
        row[f"주택구분_{house_type}"] = True

    X = pd.DataFrame([row])[META["feature_columns"]]
    X[META["numeric_columns"]] = SCALER.transform(X[META["numeric_columns"]])

    prob = float(MODEL.predict_proba(X)[:, 1][0])
    shap_values = EXPLAINER.shap_values(X)
    shap_row = pd.Series(np.array(shap_values)[0], index=X.columns)

    card = build_risk_card(prob=prob, shap_row=shap_row)
    card["resolved_sido"] = sido
    card["group_features"] = group_features
    card["filled_defaults"] = filled_defaults
    card["fetch_error"] = fetch_error

    return jsonify(card)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
