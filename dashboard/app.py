"""
전세탐정 백엔드. 로컬에서 실행:

    cd dashboard
    export SERVICE_KEY_APT=... SERVICE_KEY_RH=... SERVICE_KEY_SH=... SERVICE_KEY_OFFI=...
    python3 app.py

그 다음 브라우저에서 http://localhost:5000 접속.
"""
from flask import Flask, jsonify, request, send_from_directory

from analyze_core import META, analyze

app = Flask(__name__, static_folder=None)


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
    result = analyze(
        address=payload.get("address"),
        house_type=payload.get("house_type"),
        contract_month=payload.get("contract_month"),
        deposit=payload.get("deposit"),
        senior_debt=payload.get("senior_debt"),
        house_value=payload.get("house_value"),
    )
    if "errors" in result:
        return jsonify(result), 400
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
