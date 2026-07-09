"""
전세탐정 — Colab에서 실행하는 Gradio 버전.

로컬에 Flask 서버를 띄우는 대신, Google Colab에서 셀만 실행하면
`https://xxxxx.gradio.live` 공개 링크가 나와서 바로 접속할 수 있다.
계산 로직(analyze_core.analyze)은 app.py(Flask)와 완전히 동일한 것을 재사용한다.

Colab에서 실행:
    !git clone <repo>
    %cd <repo>/dashboard
    !pip install -q -r requirements.txt
    (SERVICE_KEY_* 환경변수 설정)
    !python gradio_app.py
"""
import gradio as gr

from analyze_core import META, analyze

GRADE_COLOR = {"낮음": "#2E8F58", "주의": "#AD7714", "위험": "#B23A34"}
GRADE_BG = {"낮음": "#E5F3EA", "주의": "#FAF0DC", "위험": "#FBE9E6"}


def _factor_block(title: str, factors: list, color: str, bg: str) -> str:
    if not factors:
        return f"<h4 style='color:{color};margin-bottom:6px'>{title}</h4><div style='color:#888;font-size:13px'>해당 없음</div>"
    items = "".join(
        f"<div style='background:{bg};border-radius:8px;padding:8px 12px;margin-bottom:6px'>"
        f"<div style='display:flex;justify-content:space-between;font-weight:700;color:{color};font-size:13px'>"
        f"<span>{f['feature']}</span><span>{f['shap_value']:+.3f}</span></div>"
        f"<div style='font-size:13px;color:#333;margin-top:2px'>{f['message']}</div>"
        f"</div>"
        for f in factors
    )
    return f"<h4 style='color:{color};margin-bottom:6px'>{title}</h4>{items}"


def run(address, house_type, contract_month, deposit, senior_debt, house_value):
    result = analyze(address, house_type, contract_month or None, deposit, senior_debt, house_value)

    if "errors" in result:
        msg = "<br>".join(result["errors"])
        return f"<div style='color:#B23A34;font-weight:600'>{msg}</div>", "", ""

    grade = result["risk_grade"]
    color = GRADE_COLOR[grade]
    header = (
        f"<div style='padding:18px 20px;border:1px solid #ddd;border-radius:12px'>"
        f"<div style='font-size:36px;font-weight:800'>{result['risk_score']}"
        f"<span style='font-size:14px;color:#888'> / 100</span></div>"
        f"<div style='font-weight:700;color:{color};margin-top:4px'>위험 등급 · {grade}</div>"
        f"<div style='font-size:13px;color:#888;margin-top:4px'>인식된 시/도: {result['resolved_sido']}"
        f" · 실거래가 API 실시간 계산 결과</div>"
        f"</div>"
    )

    warn_lines = []
    if result.get("fetch_error"):
        warn_lines.append(f"실거래가 조회 실패: {result['fetch_error']}")
    if result.get("filled_defaults"):
        warn_lines.append(f"다음 항목은 실시간 데이터를 가져오지 못해 중립값(0)으로 대체됐습니다: {', '.join(result['filled_defaults'])}")
    if warn_lines:
        header += (
            "<div style='margin-top:10px;padding:10px 12px;border-radius:8px;"
            "background:#FAF0DC;color:#AD7714;font-size:13px'>" + "<br>".join(warn_lines) + "</div>"
        )

    factors_html = (
        _factor_block("위험도를 높인 요인", result["risk_up_factors"], "#B23A34", "#FBE9E6")
        + "<div style='height:12px'></div>"
        + _factor_block("위험도를 낮춘 요인", result["risk_down_factors"], "#2E8F58", "#E5F3EA")
    )

    checklist = result["checklist"]
    checklist_items = (
        "".join(f"<div style='padding:4px 0'>☐ {c}</div>" for c in checklist)
        if checklist else "<div style='color:#888'>추가로 확인할 항목이 없습니다. 일반적인 계약 서류만 확인하세요.</div>"
    )
    checklist_html = f"<h4 style='margin-bottom:6px'>계약 전 확인해야 할 것</h4>{checklist_items}"

    return header, factors_html, checklist_html


with gr.Blocks(title="전세탐정 — 위험 진단") as demo:
    gr.Markdown(
        "## 전세탐정 — 전세 위험 진단\n"
        "주소·주택구분·계약 정보를 입력하면 국토부 실거래가 API로 시세·갱신계약 데이터를 실시간으로 가져와 "
        "위험도를 계산합니다. 임대보증금액·선순위채권금액·주택가액은 계약서·등기부등본 기준으로 직접 입력해야 합니다."
    )
    with gr.Row():
        address = gr.Textbox(label="주소", placeholder="예: 서울특별시 강남구 역삼동 123")
        house_type = gr.Dropdown(choices=META["housetype_values"], label="주택구분")
        contract_month = gr.Textbox(label="계약월 (YYYY-MM, 비워두면 이번 달)", placeholder="2024-06")
    with gr.Row():
        deposit = gr.Number(label="임대보증금액 (만원)")
        senior_debt = gr.Number(label="선순위채권금액 (만원)")
        house_value = gr.Number(label="주택가액 (만원)")
    btn = gr.Button("위험도 분석", variant="primary")

    result_header = gr.HTML()
    with gr.Row():
        factors_out = gr.HTML()
        checklist_out = gr.HTML()

    btn.click(
        run,
        inputs=[address, house_type, contract_month, deposit, senior_debt, house_value],
        outputs=[result_header, factors_out, checklist_out],
    )

if __name__ == "__main__":
    demo.launch(share=True)
