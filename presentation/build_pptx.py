"""전세탐정 발표자료 PPTX 빌더. HTML 덱(presentation/jeonse-detective-deck.html)과 동일한
케이스파일 톤(종이색 배경, 틸-잉크 accent, 위험도 시맨틱 컬러)을 파워포인트로 재현한다."""
import copy

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------- 팔레트 (HTML :root 라이트 테마 값 그대로) ----------
PAPER = RGBColor(0xF1, 0xED, 0xE4)
SURFACE = RGBColor(0xFF, 0xFF, 0xFF)
SURFACE2 = RGBColor(0xE8, 0xE1, 0xD1)
INK = RGBColor(0x20, 0x1C, 0x16)
INK_SOFT = RGBColor(0x5B, 0x53, 0x46)
INK_FAINT = RGBColor(0x8B, 0x82, 0x72)
BORDER = RGBColor(0xDE, 0xD6, 0xC4)
ACCENT = RGBColor(0x12, 0x61, 0x5D)
ACCENT_INK = RGBColor(0x0C, 0x47, 0x44)
ACCENT_SOFT = RGBColor(0xDC, 0xEB, 0xE7)
SAFE = RGBColor(0x2E, 0x8F, 0x58)
SAFE_SOFT = RGBColor(0xE5, 0xF3, 0xEA)
CAUTION = RGBColor(0xAD, 0x77, 0x14)
CAUTION_SOFT = RGBColor(0xFA, 0xF0, 0xDC)
DANGER = RGBColor(0xB2, 0x3A, 0x34)
DANGER_SOFT = RGBColor(0xFB, 0xE9, 0xE6)

FONT_UI = "맑은 고딕"
FONT_MONO = "Consolas"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN = Inches(0.55)
CONTENT_W = SLIDE_W - 2 * MARGIN

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]


def add_slide():
    s = prs.slides.add_slide(BLANK)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid(); bg.fill.fore_color.rgb = PAPER
    bg.line.fill.background()
    bg.shadow.inherit = False
    return s


def _set_run(r, text, size=14, color=INK, bold=False, italic=False, font=FONT_UI):
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    rPr = r._r.get_or_add_rPr()
    ea = rPr.makeelement(qn('a:ea'), {'typeface': font})
    rPr.append(ea)


def add_textbox(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
                 line_spacing=1.15, space_after=0):
    """runs: list of paragraphs, each a list of (text, kwargs) tuples."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    for i, para_runs in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        for text, kwargs in para_runs:
            r = p.add_run()
            _set_run(r, text, **kwargs)
    return tb


def add_rect(slide, x, y, w, h, fill=None, line_color=None, line_w=Pt(0.75), radius=None, shadow=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, x, y, w, h)
    if radius:
        try:
            shp.adjustments[0] = radius
        except IndexError:
            pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line_color is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line_color; shp.line.width = line_w
    shp.shadow.inherit = False
    if shadow:
        el = shp._element.spPr
        existing = el.find(qn('a:effectLst'))
        if existing is not None:
            el.remove(existing)
        effect = el.makeelement(qn('a:effectLst'), {})
        outer = effect.makeelement(qn('a:outerShdw'), {
            'blurRad': '90000', 'dist': '25000', 'dir': '5400000', 'rotWithShape': '0'
        })
        clr = outer.makeelement(qn('a:srgbClr'), {'val': '201C16'})
        alpha = clr.makeelement(qn('a:alpha'), {'val': '18000'})
        clr.append(alpha); outer.append(clr); effect.append(outer); el.append(effect)
    return shp


def add_header(slide, case_tag, case_ref):
    tag_w = Inches(0.28 + len(case_tag) * 0.082)
    tag = add_rect(slide, MARGIN, Inches(0.42), tag_w, Inches(0.34), fill=ACCENT_SOFT,
                   line_color=ACCENT, line_w=Pt(0.75), radius=0.18)
    tf = tag.text_frame; tf.word_wrap = False
    tf.margin_left = Inches(0.1); tf.margin_right = Inches(0.1)
    tf.margin_top = 0; tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); _set_run(r, case_tag, size=11, color=ACCENT_INK, bold=True, font=FONT_MONO)
    add_textbox(slide, SLIDE_W - MARGIN - Inches(2.2), Inches(0.44), Inches(2.2), Inches(0.3),
                [[(case_ref, dict(size=11, color=INK_FAINT, font=FONT_MONO))]], align=PP_ALIGN.RIGHT)


def add_title(slide, title, y=Inches(0.9), size=30):
    add_textbox(slide, MARGIN, y, CONTENT_W, Inches(0.65),
                [[(title, dict(size=size, color=INK, bold=True))]])


def add_lede(slide, text, y=Inches(1.55), size=14.5, h=Inches(0.75)):
    add_textbox(slide, MARGIN, y, CONTENT_W, h,
                [[(text, dict(size=size, color=INK_SOFT))]], line_spacing=1.25)


def add_card(slide, x, y, w, h, title=None, title_color=INK, body=None, body_size=12.5):
    add_rect(slide, x, y, w, h, fill=SURFACE, line_color=BORDER, line_w=Pt(0.75), radius=0.055, shadow=True)
    pad = Inches(0.18)
    cy = y + pad
    if title:
        add_textbox(slide, x + pad, cy, w - 2 * pad, Inches(0.32),
                    [[(title, dict(size=13.5, color=title_color, bold=True))]])
        cy += Inches(0.36)
    if body:
        add_textbox(slide, x + pad, cy, w - 2 * pad, y + h - cy - pad,
                     [[(body, dict(size=body_size, color=INK_SOFT))]], line_spacing=1.2)


def add_tag(slide, x, y, text, fg, bg, size=10.5, w=None):
    w = w or Inches(0.22 + len(text) * 0.078)
    shp = add_rect(slide, x, y, w, Inches(0.28), fill=bg, radius=0.4)
    tf = shp.text_frame; tf.word_wrap = False
    tf.margin_left = Inches(0.08); tf.margin_right = Inches(0.08)
    tf.margin_top = 0; tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); _set_run(r, text, size=size, color=fg, bold=True, font=FONT_MONO)
    return w


def add_stat(slide, x, y, w, h, num, label, color=ACCENT_INK):
    add_rect(slide, x, y, w, h, fill=SURFACE, line_color=BORDER, line_w=Pt(0.75), radius=0.08, shadow=True)
    pad = Inches(0.15)
    add_textbox(slide, x + pad, y + pad, w - 2 * pad, Inches(0.5),
                [[(num, dict(size=20, color=color, bold=True, font=FONT_MONO))]])
    add_textbox(slide, x + pad, y + h - Inches(0.5), w - 2 * pad, Inches(0.45),
                [[(label, dict(size=10, color=INK_FAINT, bold=True))]], line_spacing=1.1)


def add_stat_row(slide, x, y, w, h, items):
    n = len(items)
    gap = Inches(0.15)
    cw = (w - gap * (n - 1)) // n
    for i, (num, label, color) in enumerate(items):
        add_stat(slide, x + i * (cw + gap), y, cw, h, num, label, color)


def add_callout(slide, x, y, w, h, text, kind="accent"):
    bar_color = {"accent": ACCENT, "warn": CAUTION}[kind]
    bg = {"accent": ACCENT_SOFT, "warn": CAUTION_SOFT}[kind]
    fg = {"accent": ACCENT_INK, "warn": RGBColor(0x6B, 0x4A, 0x0C)}[kind]
    add_rect(slide, x, y, w, h, fill=bg)
    bar = add_rect(slide, x, y, Inches(0.05), h, fill=bar_color)
    add_textbox(slide, x + Inches(0.2), y + Inches(0.12), w - Inches(0.4), h - Inches(0.24),
                [[(text, dict(size=12.5, color=fg))]], line_spacing=1.25, anchor=MSO_ANCHOR.MIDDLE)


def style_table(tbl, header_fill=SURFACE2, header_color=INK_FAINT, body_color=INK_SOFT,
                 mono_cols=None, first_col_bold=False, row_colors=None, font_size=12):
    mono_cols = mono_cols or []
    n_rows = len(tbl.rows); n_cols = len(tbl.columns)
    for ci in range(n_cols):
        cell = tbl.cell(0, ci)
        cell.fill.solid(); cell.fill.fore_color.rgb = header_fill
        for p in cell.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(10.5); r.font.bold = True; r.font.color.rgb = header_color
                r.font.name = FONT_UI
        cell.margin_top = Pt(4); cell.margin_bottom = Pt(4)
        cell.margin_left = Pt(8); cell.margin_right = Pt(8)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    for ri in range(1, n_rows):
        rc = row_colors[ri - 1] if row_colors and (ri - 1) < len(row_colors) else None
        for ci in range(n_cols):
            cell = tbl.cell(ri, ci)
            cell.fill.solid(); cell.fill.fore_color.rgb = SURFACE
            font = FONT_MONO if ci in mono_cols else FONT_UI
            color = rc if rc else body_color
            for p in cell.text_frame.paragraphs:
                p.line_spacing = 1.1
                for r in p.runs:
                    r.font.size = Pt(font_size); r.font.color.rgb = color; r.font.name = font
                    if ci == 0 and first_col_bold:
                        r.font.bold = True
            cell.margin_top = Pt(5); cell.margin_bottom = Pt(5)
            cell.margin_left = Pt(8); cell.margin_right = Pt(8)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    # remove default banding / borders look by setting no-style
    tbl_pr = tbl._tbl.find(qn('a:tblPr'))
    if tbl_pr is not None:
        tbl_pr.set('firstRow', '0'); tbl_pr.set('bandRow', '0')


def add_table(slide, x, y, w, h, headers, rows, col_widths=None, **style_kwargs):
    gframe = slide.shapes.add_table(len(rows) + 1, len(headers), x, y, w, h)
    tbl = gframe.table
    if col_widths:
        total = sum(col_widths)
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = Emu(int(w * (cw / total)))
    for ci, htext in enumerate(headers):
        tbl.cell(0, ci).text = htext
    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            tbl.cell(ri, ci).text = str(val)
    style_table(tbl, **style_kwargs)
    return tbl


BODY_TOP = Inches(2.35)
BODY_BOTTOM = Inches(7.05)
BODY_H = BODY_BOTTOM - BODY_TOP

# ============================================================
# 01 표지
# ============================================================
s = add_slide()
add_textbox(s, MARGIN, Inches(0.42), Inches(4.5), Inches(0.34),
            [[("CASE FILE · 전세탐정 프로젝트", dict(size=11, color=ACCENT_INK, bold=True, font=FONT_MONO))]])
add_textbox(s, SLIDE_W - MARGIN - Inches(3), Inches(0.44), Inches(3), Inches(0.3),
            [[("2026.07 · 핀테크 인턴십", dict(size=11, color=INK_FAINT, font=FONT_MONO))]], align=PP_ALIGN.RIGHT)

add_textbox(s, MARGIN, Inches(2.1), Inches(9), Inches(1.3),
            [[("전세", dict(size=64, color=INK, bold=True)), ("탐정", dict(size=64, color=ACCENT, bold=True))]])
add_textbox(s, MARGIN, Inches(3.25), Inches(10.8), Inches(1.0),
            [[('깡통전세(전세보증금 미반환) 위험을 예측하고, "왜 위험한가"를 SHAP으로 설명하는 XAI 서비스. '
               '문제 정의부터 데이터 수집, 모델링, 서비스화까지의 기록.', dict(size=16, color=INK_SOFT))]],
            line_spacing=1.3)

prev = add_rect(s, MARGIN, Inches(4.45), Inches(4.6), Inches(1.15), fill=SURFACE, line_color=BORDER,
                 line_w=Pt(0.75), radius=0.08, shadow=True)
add_textbox(s, MARGIN + Inches(0.2), Inches(4.6), Inches(1.6), Inches(0.5),
            [[("78", dict(size=24, color=INK, bold=True, font=FONT_MONO)),
              ("/100", dict(size=11, color=INK_FAINT, font=FONT_MONO))]])
add_tag(s, MARGIN + Inches(2.9), Inches(4.62), "위험 등급 · 위험", DANGER, DANGER_SOFT, w=Inches(1.5))
add_textbox(s, MARGIN + Inches(0.2), Inches(5.1), Inches(4.2), Inches(0.4),
            [[("1. 전세가율이 높습니다 · 2. 선순위채권금액이 큽니다 · 3. 주택유형위험도가 높게 반영됐습니다",
               dict(size=9.5, color=INK_SOFT))]], line_spacing=1.2)

add_textbox(s, MARGIN, Inches(6.65), Inches(11), Inches(0.35),
            [[("담당 — 박지민 · 박소연 · 송예원 · 이다영          데이터 — HUG 전세보증 대위변제현황 50,054건",
               dict(size=11, color=INK_FAINT, font=FONT_MONO))]])

# ============================================================
# 02 문제 정의
# ============================================================
s = add_slide()
add_header(s, "CASE 01 · 문제 정의", "01 / 16")
add_title(s, "깡통전세란?")
add_lede(s, '전세보증금이 매매가를 웃도는 집. 최근 수년간 전셋값이 급등한 반면 거래 절벽으로 집값 상승세가 주춤하면서, '
             '깡통전세 피해를 우려하는 세입자가 늘고 있다 — 2021년부터 전세반환보증 가입이 급증하는 배경이다.')

half_w = (CONTENT_W - Inches(0.2)) // 2
add_card(s, MARGIN, BODY_TOP, half_w, Inches(1.5), title="경매 시 보증금 손실", title_color=DANGER,
         body="집주인이 대출 이자를 못 내거나 보증금을 못 돌려줘 집이 경매로 넘어가면, 은행 대출금이 세입자보다 "
              "먼저 변제된다. 낙찰가가 보증금보다 낮으면 세입자는 전세금 일부 또는 전부를 잃는다.")
add_card(s, MARGIN + half_w + Inches(0.2), BODY_TOP, half_w, Inches(1.5), title="매매가 하락 위험", title_color=DANGER,
         body="집값이 급락하면, 자기자본 없이 전세금으로 집을 산 집주인(갭투자)은 보증금을 반환할 능력 자체를 "
              "상실하게 된다.")

card_y = BODY_TOP + Inches(1.7)
add_card(s, MARGIN, card_y, Inches(6.0), Inches(1.65), title="깡통전세 계산법 — 전세가율")
add_textbox(s, MARGIN + Inches(0.18), card_y + Inches(0.55), Inches(5.6), Inches(0.4),
            [[("전세가율 = (전세보증금 ÷ 주택 매매가) × 100", dict(size=13.5, color=INK, font=FONT_MONO))]])
add_tag(s, MARGIN + Inches(0.18), card_y + Inches(1.05), "안전 · 50~60% 이하", SAFE, SAFE_SOFT, w=Inches(1.9))
add_tag(s, MARGIN + Inches(2.2), card_y + Inches(1.05), "주의·위험 · 70~80% 이상", DANGER, DANGER_SOFT, w=Inches(2.2))

# ============================================================
# 03 주제 선정
# ============================================================
s = add_slide()
add_header(s, "CASE 02 · 주제 선정", "02 / 16")
add_title(s, '왜 "깡통전세 위험 예측"인가')
add_lede(s, "기존 전세대출 스코어링 서비스를 개선하는 방향과 별개로, 새 예측 서비스 후보를 폭넓게 검토했다.")

add_card(s, MARGIN, BODY_TOP, CONTENT_W, Inches(2.5), title="검토했던 후보들")
candidates = [
    'Gate 탈락 사유 → "합격 시뮬레이터"(Counterfactual XAI)',
    "승인확률 예측 모델 + SHAP force plot으로 대체",
    "연체(상환위험) 예측 모델화, 고객 세그먼트의 soft segmentation화",
    "reason 필드를 SHAP + 자연어 설명으로 고도화",
    "깡통전세(보증금 미반환) 위험 예측 — 기존 컬럼 재사용 가능, 사회적 임팩트",
]
add_textbox(s, MARGIN + Inches(0.2), BODY_TOP + Inches(0.55), CONTENT_W - Inches(0.4), Inches(1.9),
            [[("•  " + c, dict(size=13.5, color=INK_SOFT if i < 4 else INK, bold=(i == 4)))]
             for i, c in enumerate(candidates)], line_spacing=1.55)

add_callout(s, MARGIN, BODY_TOP + Inches(2.7), CONTENT_W, Inches(1.1),
            '최종 확정 이유 — 실제 사례를 통해 추적해가는 설계가 쉽다("탐정" 컨셉과 자연스럽게 연결) · '
            '여러 서비스를 합치지 않고 깡통전세 하나에 집중 · 관련 법령·기사 자료 조사를 병행.')

# ============================================================
# 04 데이터 수집 전략
# ============================================================
s = add_slide()
add_header(s, "CASE 03 · 데이터 수집", "03 / 16")
add_title(s, "데이터는 어디서 가져왔나")
add_lede(s, "세 플랫폼을 조사했지만 성격이 뚜렷하게 달랐다 — 실제로 확인해본 뒤 역할을 나눠 정리했다.")

third_w = (CONTENT_W - Inches(0.4)) // 3
cols = [
    ("공공데이터포털", ACCENT_INK, "핵심 뼈대 데이터. 실거래가 API, HUG 보증사고 통계, 전세사기 피해 실태조사, "
                                  "악성임대인 현황, 등기부등본·건축물대장 연계 데이터."),
    ("AI 허브", INK_FAINT, "전세사기 전용 정형 데이터는 없음. 문서 OCR·합성 데이터 생성 기법 참고용으로만 활용."),
    ("Kaggle", INK_FAINT, "해외 사례라 직접 쓰긴 어렵지만, 금융사기 탐지 데이터셋의 불균형 처리 기법"
                          "(SMOTE, class weight)을 참고."),
]
for i, (title, color, body) in enumerate(cols):
    add_card(s, MARGIN + i * (third_w + Inches(0.2)), BODY_TOP, third_w, Inches(1.9),
             title=title, title_color=color, body=body)

add_callout(s, MARGIN, BODY_TOP + Inches(2.1), CONTENT_W, Inches(1.5),
            "정직하게 밝히는 한계 — 개별 사고 건(임대인–세입자 매칭) 단위 raw 데이터는 개인정보 문제로 비공개다. "
            'HUG도 "집계 통계"만 공개하므로, 실제로는 HUG가 만든 합성데이터로 모델을 만들고, 지역별·주택유형별 '
            "통계로 별도 교차검증하는 방식을 택했다.", kind="warn")

# ============================================================
# 05 원본 데이터
# ============================================================
s = add_slide()
add_header(s, "CASE 04 · 원본 데이터", "04 / 16")
add_title(s, "전세보증 대위변제현황 (HUG 합성데이터)")
add_lede(s, "모델링의 뼈대가 된 원본 데이터셋. 대위변제 = HUG가 집주인 대신 세입자에게 보증금을 지급한 사건.")

add_stat_row(s, MARGIN, BODY_TOP, CONTENT_W, Inches(1.0), [
    ("50,054", "전체 건수", ACCENT_INK),
    ("2022–2024", "3개년 (36개월)", ACCENT_INK),
    ("17 / 8", "시도 / 주택유형", ACCENT_INK),
    ("~7.5%", "대위변제(사고) 비율 · 불균형", ACCENT_INK),
])
add_card(s, MARGIN, BODY_TOP + Inches(1.2), CONTENT_W, Inches(1.65), title="라벨의 의미 — 정확히 짚고 가야 할 것",
         body='대위변제여부 = 1 는 "보증금 미반환 사고"지 "사기 판정"이 아니다. 사기(무자본 갭투자)뿐 아니라 '
              "역전세·임대인 파산으로도 발생하며, 데이터는 원인을 구분하지 않는다. 세입자 입장에선 원인이 "
              '무엇이든 피해가 동일하므로, 본 모델의 예측 대상은 "보증금 미반환 위험"으로 정의한다.', body_size=13)
add_card(s, MARGIN, BODY_TOP + Inches(3.0), CONTENT_W, Inches(0.85), title="원본 컬럼 8종")
add_textbox(s, MARGIN + Inches(0.18), BODY_TOP + Inches(3.5), CONTENT_W - Inches(0.4), Inches(0.3),
            [[("일련번호 · 보증완료월 · 주택가액 · 임대보증금액 · 선순위채권금액 · 대위변제여부 · 시도 · 주택구분",
               dict(size=12, color=INK_SOFT, font=FONT_MONO))]])

# ============================================================
# 06 피처 엔지니어링
# ============================================================
s = add_slide()
add_header(s, "CASE 05 · 피처 엔지니어링", "05 / 16")
add_title(s, "국토부 실거래가 API로 피처 3그룹 · 9종 추가", size=27)
add_lede(s, '원본 8개 컬럼만으론 "이 계약이 그 시기·그 동네 기준으로 정상적인지"를 알 수 없었다. 아파트·연립다세대·'
             "단독다가구·오피스텔 4종 API를 시도×주택유형×월 단위로 집계해 붙였다.")

add_table(s, MARGIN, BODY_TOP, CONTENT_W, Inches(1.7),
           ["그룹", "신규 컬럼", "왜 유용한가"],
           [["시세비교", "시세_평균전세보증금 · 시세대비보증금비율 · 월세전환비율",
             '"이 계약이 동네 시세보다 비싼가"를 직접 계산'],
            ["갱신계약", "평균보증금인상률 · 갱신계약비율 · 갱신요구권행사비율",
             "임대인이 세입자를 자주 교체하는 지역인지 신호"],
            ["건물특성", "평균건축연도 · 평균전용면적 · 거래량",
             '"신축빌라 갭투자" 패턴, 표본 신뢰도 가중치']],
           col_widths=[1.3, 4, 3.5], mono_cols=[1], first_col_bold=True)

add_card(s, MARGIN, BODY_TOP + Inches(1.95), CONTENT_W, Inches(0.85), title="파생 위험지표 — 깡통지수")
add_textbox(s, MARGIN + Inches(0.18), BODY_TOP + Inches(2.45), CONTENT_W - Inches(0.4), Inches(0.3),
            [[("깡통지수 = (임대보증금액 + 선순위채권금액) ÷ 주택가액", dict(size=13, color=INK, font=FONT_MONO))]])

add_callout(s, MARGIN, BODY_TOP + Inches(2.95), CONTENT_W, Inches(0.95),
            "2026년 7월 광주·전남 행정통합으로 법정동코드 체계가 개편되며 일부 지역 수집이 한때 막혔지만, 바뀐 "
            "지역코드를 다시 조사해 유효한 코드로 교체함으로써 해당 지역도 정상적으로 수집을 완료했다.", kind="warn")

# ============================================================
# 07 피처 검증
# ============================================================
s = add_slide()
add_header(s, "CASE 06 · 피처 검증", "06 / 16")
add_title(s, "새 피처, 실제로 통하는가")
add_lede(s, "피처를 추가하고 끝내지 않고, 실제 대위변제 여부와 맞아떨어지는지 직접 대조했다.")

add_stat_row(s, MARGIN, BODY_TOP, CONTENT_W, Inches(1.05), [
    ("15.0% vs 1.6%", "깡통지수 ≥0.8 매물 vs 미만 — 약 9배", DANGER),
    ("0.97 vs 0.71", "사고 건 vs 정상 건 전세가율 중앙값", ACCENT_INK),
    ("24.0% vs 2.2%", "전세가율 90%↑ vs 70%↓ 구간 사고율 (11배)", ACCENT_INK),
])
add_card(s, MARGIN, BODY_TOP + Inches(1.25), CONTENT_W, Inches(0.85), title="주택유형별 사고율",
         body="다세대 19.7% > 연립 13.5% > 오피스텔 10.2% ≫ 아파트 3.3%", body_size=13.5)
add_callout(s, MARGIN, BODY_TOP + Inches(2.25), CONTENT_W, Inches(1.65),
            "데이터만 보고 학습한 결정트리의 첫 분기가 전세가율로 나타났다 — \"깡통전세를 가르는 첫 기준은 "
            "전세가율\"이라는 도메인 상식에 모델이 스스로 도달한 것으로, 엉뚱한 패턴을 학습하지 않았다는 1차 "
            "검증이 된다. (이후 깡통지수를 추가하자 SHAP 1위가 전세가율에서 깡통지수로 교체됐다 — 더 강한 위험 "
            "신호였다는 뜻.)")

# ============================================================
# 08 모델링 과정
# ============================================================
s = add_slide()
add_header(s, "CASE 07 · 모델링", "07 / 16")
add_title(s, "불균형 데이터, 어떻게 다뤘나")
add_lede(s, '사고가 7.5%뿐인 데이터라 "전부 정상"이라고만 답해도 정확도 92%가 나온다 — 그래서 학습 전체를 불균형을 '
             "고려한 설계로 짰다.")

add_stat_row(s, MARGIN, BODY_TOP, CONTENT_W, Inches(1.05), [
    ("40,043 / 10,011", "학습 / 검증 (stratify, 양성비율 7.5% 그대로 유지)", ACCENT_INK),
    ("12.25", "scale_pos_weight — 정상이 사고의 약 12배라 사고에 가중치", ACCENT_INK),
    ("Optuna", "learning_rate 0.019 · num_leaves 104 · max_depth 9 등 사전 튜닝값 사용", ACCENT_INK),
])
add_card(s, MARGIN, BODY_TOP + Inches(1.25), CONTENT_W, Inches(1.55), title="정확도 대신 AUC와 F1을 같이 보는 이유")
add_table(s, MARGIN + Inches(0.18), BODY_TOP + Inches(1.6), CONTENT_W - Inches(0.36), Inches(1.1),
           ["지표", "값", "의미"],
           [["ROC-AUC", "0.89 (높음)", "임계값·클래스비율과 무관한 구분 실력 — 모델은 우수"],
            ["F1", "0.5 (낮음)", "양성 7.5% 불균형이 정밀도를 눌러서 낮게 나옴 — 모델이 나쁜 게 아님"]],
           col_widths=[1.3, 1.5, 6], mono_cols=[1], font_size=11.5)
add_callout(s, MARGIN, BODY_TOP + Inches(2.95), CONTENT_W, Inches(0.95),
            "불균형 데이터는 F1만 보면 모델을 과소평가하게 된다. PR 곡선을 보면 recall을 올릴수록 precision이 "
            '급락해 F1이 낮게 잡히는 구조라, ROC-AUC로 "모델 자체의 구분력"을 함께 확인해야 한다.')

# ============================================================
# 09 최종 모델 성능
# ============================================================
s = add_slide()
add_header(s, "CASE 08 · 모델 성능", "08 / 16")
add_title(s, "최종 채택 모델 — LightGBM")
add_lede(s, '서비스에 실제로 반영된 모델의 성능. "위험" 등급 컷오프는 임의의 숫자가 아니라 F1이 최대가 되는 임계값을 '
             "그대로 가져왔다.")

add_stat_row(s, MARGIN, BODY_TOP, CONTENT_W, Inches(1.05), [
    ("0.887", "ROC-AUC — 임계값 무관 구분력", ACCENT_INK),
    ("0.556", "PR-AUC — 불균형 보정 지표", ACCENT_INK),
    ("0.457", "F1 @ 0.5 (기본 임계값)", ACCENT_INK),
    ("0.547", "F1 @ 최적(0.80) — 운영 임계값 채택", ACCENT_INK),
])
add_callout(s, MARGIN, BODY_TOP + Inches(1.25), CONTENT_W, Inches(0.8),
            'F1 최적 임계값 0.80 → 위험 등급 "위험" 컷오프로 그대로 사용 → 0.30 이상은 "주의"')
add_card(s, MARGIN, BODY_TOP + Inches(2.25), CONTENT_W, Inches(1.65),
         body="참고 — 팀원별로 정상 건을 사고 건 수만큼 언더샘플링해 1:1로 균형화한 뒤 테스트하는 실험도 병행했다"
              "(F1 0.814 · Recall 0.81 · Precision 0.819 · ROC-AUC 0.894). 다만 이는 균형 테스트셋 기준 수치이며, "
              "서비스는 실제 세계의 불균형 분포(사고 7.5%)를 그대로 마주하므로 위 불균형 기준 지표를 운영 기준으로 "
              "채택했다.", body_size=13)

# ============================================================
# 10 XAI Global
# ============================================================
s = add_slide()
add_header(s, "CASE 09 · 설명가능AI — 전체", "09 / 16")
add_title(s, "모델은 전체적으로 무엇을 보고 판단하는가", size=27)
add_lede(s, "Global XAI — 발표·관리자 화면용. SHAP Summary Plot으로 전 국민 단위 위험 요인 순위를 뽑았다.")

add_table(s, MARGIN, BODY_TOP, CONTENT_W, Inches(2.3),
           ["순위", "변수", "해석"],
           [["1", "깡통지수", "압도적 1위 — 2위의 2배 이상"],
            ["2", "선순위채권금액", "앞선 빚이 많으면 경매 시 보증금 회수가 밀림"],
            ["3", "전세가율", "단일 지표로도 여전히 강한 신호"],
            ["4", "시도", "지역별 임대차 시장 긴장도"],
            ["5", "갱신요구권행사비율 · 시세대비보증금비율", "동네 시세 대비 과대 보증금 신호"]],
           col_widths=[0.9, 3.5, 5.5], mono_cols=[0], first_col_bold=True)

# ============================================================
# 11 XAI Local
# ============================================================
s = add_slide()
add_header(s, "CASE 10 · 설명가능AI — 개별", "10 / 16")
add_title(s, "이 매물은 왜 이런 위험도로 판단했는가", size=27)
add_lede(s, "Local XAI — 서비스의 진짜 핵심. 학습 데이터의 실제 매물 한 건(경남 · 아파트 · 전세가율 37% · 깡통지수 "
             "0.41)을 SHAP Force Plot으로 분해하면, 위험을 높인 요인과 낮춘 요인이 함께 드러난다.")

half_w = (CONTENT_W - Inches(0.2)) // 2
add_table(s, MARGIN, BODY_TOP, half_w, Inches(1.5),
           ["위험을 낮춘 요인", "값", "SHAP"],
           [["선순위채권금액", "428만원 (낮은 편)", "-1.118"],
            ["깡통지수", "0.41", "-0.774"],
            ["시세대비보증금비율", "0.20 (시세의 20%)", "-0.347"]],
           col_widths=[3, 2.5, 1], mono_cols=[2],
           row_colors=[SAFE, SAFE, SAFE])
add_table(s, MARGIN + half_w + Inches(0.2), BODY_TOP, half_w, Inches(1.5),
           ["위험을 높인 요인", "값", "SHAP"],
           [["시도", "경남", "+0.218"],
            ["시세_평균전세보증금", "약 1.97억원", "+0.065"],
            ["평균전용면적", "70.8㎡", "+0.056"]],
           col_widths=[3, 2.5, 1], mono_cols=[2],
           row_colors=[DANGER, DANGER, DANGER])
add_callout(s, MARGIN, BODY_TOP + Inches(1.75), CONTENT_W, Inches(1.15),
            "선순위채권이 거의 없고 깡통지수가 낮은 매물은, 지역·시세 요인이 다소 불리해도 전체적으로는 위험이 "
            '낮게 판단된다. 매물마다 이런 "위험을 높인/낮춘 요인 TOP3" 리포트를 자동 생성할 수 있다.')

# ============================================================
# 12 변수 -> 사용자 언어
# ============================================================
s = add_slide()
add_header(s, "CASE 11 · 서비스화", "11 / 16")
add_title(s, "SHAP 값을 사람의 말로 바꾸기", size=27)
add_lede(s, "서비스화의 핵심은 SHAP 그래프 자체가 아니라, 그 결과를 사용자가 이해할 수 있는 위험 점수·이유·행동 "
             "가이드로 바꾸는 변환 로직에 있다. 실제 데모(explain_factor)에 쓰인 문장을 그대로 옮기면:",
        h=Inches(0.85))

steps = ["TreeSHAP 기여도 계산", "날짜 제외 상위 6개 추출", "기여도 % 정규화", "요인별 설명 문장 생성", "등급별 권고 문구 연결"]
px = MARGIN
py = BODY_TOP + Inches(0.05)
for i, step in enumerate(steps):
    w = Inches(0.35 + len(step) * 0.11)
    add_rect(s, px, py, w, Inches(0.35), fill=SURFACE, line_color=BORDER, line_w=Pt(0.75), radius=0.2, shadow=True)
    tf = None
    add_textbox(s, px, py + Inches(0.055), w, Inches(0.25),
                [[(step, dict(size=10.5, color=INK, bold=True))]], align=PP_ALIGN.CENTER)
    px += w
    if i < len(steps) - 1:
        add_textbox(s, px, py + Inches(0.04), Inches(0.22), Inches(0.28),
                    [[("→", dict(size=13, color=INK_FAINT, font=FONT_MONO))]], align=PP_ALIGN.CENTER)
        px += Inches(0.22)

add_table(s, MARGIN, BODY_TOP + Inches(0.65), CONTENT_W, Inches(3.6),
           ["모델 변수", "실제 서비스가 사용자에게 보여주는 문장"],
           [["깡통지수", '"보증금과 선순위 빚을 합치면 집값의 OO%예요. 100%가 넘으면 집을 팔아도 보증금을 다 못 '
                        '돌려받는 깡통전세라, 가장 큰 위험 신호예요."'],
            ["선순위채권금액", '"나보다 먼저 돈을 받아 갈 권리가 있는 빚이에요. 집이 경매로 팔리면 은행이 먼저 '
                              '가져가고, 남은 돈에서 내 보증금을 받아요."'],
            ["전세가율", '"집값에서 보증금이 차지하는 비율이에요. 100%에 가까울수록 위험해요 — 경매로 팔려도 '
                       '돌려받을 여유가 거의 없거든요."'],
            ["시세대비보증금비율", '"주변 시세보다 비싸게 낸 보증금이면, 새 세입자를 구하기 어려워 보증금 반환이 '
                                 '늦어질 수 있어요."'],
            ["주택구분", '"아파트는 비교할 집이 많아 적정가를 알기 쉽지만, 오피스텔·빌라는 비교 대상이 적어 '
                        '보증금이 부풀려지기 쉬워요."'],
            ["갱신요구권행사비율", '"세입자가 계약갱신청구권을 쓴 비율이 낮으면, 집주인이 세입자를 자주 교체하는 '
                                 '갭투자 패턴일 수 있어요."']],
           col_widths=[2, 8], mono_cols=[0], first_col_bold=True, font_size=11)

# ============================================================
# 13 서비스 화면
# ============================================================
s = add_slide()
add_header(s, "CASE 12 · 서비스화", "12 / 16")
add_title(s, "실제로 만든 화면 — 입력 하나, 결과 하나", size=27)
add_lede(s, "관리자용 별도 화면은 만들지 않았다. 실제 구현은 Gradio 화면 하나 — 왼쪽 입력 패널과 오른쪽 결과 패널로 "
             "구성된다.")

half_w = (CONTENT_W - Inches(0.2)) // 2
add_card(s, MARGIN, BODY_TOP, half_w, Inches(3.3), title="왼쪽 · 입력 패널", title_color=ACCENT_INK,
         body='"주소 분석해서 채우기" 버튼 하나로 시도·주택구분·주택가액을 채우고, 보증금·선순위채권금액·계약연도/월만 '
              "더하면 준비 끝.")
input_items = ["주소 입력 → 주소 분석해서 채우기", "시도 · 주택구분 (자동 채움, 수정 가능)",
               "주택가액 (자동 채움, 수정 가능)", "임대보증금액 · 선순위채권금액 (직접 입력)",
               "계약연도 · 계약월 (직접 입력)"]
add_textbox(s, MARGIN + Inches(0.2), BODY_TOP + Inches(1.35), half_w - Inches(0.4), Inches(1.8),
            [[("•  " + it, dict(size=12.5, color=INK_SOFT))] for it in input_items], line_spacing=1.5)

rx = MARGIN + half_w + Inches(0.2)
add_card(s, rx, BODY_TOP, half_w, Inches(3.3), title="오른쪽 · 결과 패널", title_color=ACCENT_INK,
         body='"위험도 분석" 버튼을 누르면 같은 화면 오른쪽에 바로 뜬다.')
add_tag(s, rx + Inches(0.2), BODY_TOP + Inches(1.05), "안전 · 0~30점", SAFE, SAFE_SOFT, w=Inches(1.25))
add_tag(s, rx + Inches(1.55), BODY_TOP + Inches(1.05), "주의 · 30~60점", CAUTION, CAUTION_SOFT, w=Inches(1.25))
add_tag(s, rx + Inches(2.9), BODY_TOP + Inches(1.05), "위험 · 60~100점", DANGER, DANGER_SOFT, w=Inches(1.3))
add_textbox(s, rx + Inches(0.2), BODY_TOP + Inches(1.55), half_w - Inches(0.4), Inches(1.6),
            [[('"이 매물이 위험한 이유" — |SHAP| 기여도 상위 6개(날짜 제외)를 요인별 카드로 나열',
               dict(size=12, color=INK_SOFT))],
             [("", dict(size=6, color=INK_SOFT))],
             [("위험 등급 시 권고 — ", dict(size=12, color=INK_SOFT)),
              ('"⚠️ 전세보증보험(HUG) 가입 가능 여부 확인 필수 · 등기부 선순위채권 확인 · 계약 재검토 강력 권장"',
               dict(size=12, color=INK_SOFT, italic=True))]],
            line_spacing=1.35)

# ============================================================
# 14 실시간 자동화
# ============================================================
s = add_slide()
add_header(s, "CASE 13 · 실시간 자동화", "13 / 16")
add_title(s, "주소 한 줄로 어디까지 자동화되는가", size=27)
add_lede(s, "계약 고유 정보만 사용자가 입력하고, 나머지는 주소 하나로 그 자리에서 채운다.")

add_table(s, MARGIN, BODY_TOP, CONTENT_W, Inches(2.6),
           ["입력값", "자동화 수준", "방법"],
           [["시/도 · 주택유형 · 주택가액", "완전 자동", "행안부 주소검색(juso.go.kr) API로 법정동코드·건물명 인식 → "
             "아파트/연립다세대/오피스텔 매매 실거래가 API 교차검색 → 최근 3개월 중앙값 매매가로 자동 입력"],
            ["주소 인식 실패 시", "폴백", "내장 시/도·시/군/구 사전으로 주소 문자열 직접 매칭"],
            ["시세비교·갱신계약·건물특성 그룹 피처", "완전 자동", "시도×주택구분 평균으로 미리 만든 조회테이블에서 "
             "즉시 조회"],
            ["선순위채권금액", "오픈 API 없음", "등기부등본 열람 필요 — 사용자 직접 입력"],
            ["임대보증금액 · 계약연도/월", "사용자 입력", "계약 고유 정보라 대체 불가"]],
           col_widths=[2.6, 1.5, 6.3], font_size=10.5)

add_callout(s, MARGIN, BODY_TOP + Inches(2.8), CONTENT_W, Inches(1.25),
            '이전 프로토타입은 주소 → 시/도까지만 자동이었지만, 이번 Gradio 데모는 "주소 분석해서 채우기" 버튼 '
            "하나로 시도·주택유형·주택가액까지 한 번에 채운다 — 주소 인식(행안부 API) → 실거래가 교차검색(국토부 "
            "API) → 조회테이블 매칭을 하나의 흐름으로 연결했다. 실행 경로는 두 가지 — 로컬 Flask 프로토타입, "
            "그리고 설치 없이 링크로 여는 Colab + Gradio 데모.")

# ============================================================
# 15 한계
# ============================================================
s = add_slide()
add_header(s, "CASE 14 · 한계와 다음 단계", "14 / 16")
add_title(s, "솔직하게 남겨두는 한계", size=27)
add_lede(s, "기술적으로 되는 것과, 서비스로서 아직 부족한 것을 구분해서 밝힌다.")

limits = [
    ("라벨 재정의 필요", '"미반환 사고" ≠ "사기 판정" — 역전세·임대인 파산이 섞여 있어, 서비스 문구는 "사기 위험"이 '
                     '아니라 "미반환 위험"으로 표기해야 한다.'),
    ("합성데이터 기반", "개별 사고 원본 데이터는 개인정보로 비공개. HUG 합성데이터로 학습했고, 실데이터 확보 시 "
                     "재학습을 전제로 한다."),
    ("시세 해상도 낮음", "시세 변수가 시도 단위라 시군구·동 단위의 국지적 위험(특정 동네 시세 급락 등)은 아직 못 "
                     "잡는다."),
    ("임대인 축 부재", "다주택 보유, 악성임대인 명단 등 임대인 측 위험 신호가 미포함 — 실제 사기 사건의 핵심 축이라 "
                    "추가가 필요하다."),
]
half_w = (CONTENT_W - Inches(0.2)) // 2
positions = [(MARGIN, BODY_TOP), (MARGIN + half_w + Inches(0.2), BODY_TOP),
             (MARGIN, BODY_TOP + Inches(1.55)), (MARGIN + half_w + Inches(0.2), BODY_TOP + Inches(1.55))]
for (title, body), (x, y) in zip(limits, positions):
    add_rect(s, x, y, half_w, Inches(1.4), fill=SURFACE, line_color=BORDER, line_w=Pt(0.75), radius=0.06, shadow=True)
    add_rect(s, x + Inches(0.18), y + Inches(0.15), Inches(0.28 + len(title) * 0.1), Inches(0.3),
             fill=None, line_color=DANGER, line_w=Pt(1.2), radius=0.15)
    add_textbox(s, x + Inches(0.18), y + Inches(0.15), Inches(0.28 + len(title) * 0.1), Inches(0.3),
                [[(title, dict(size=10, color=DANGER, bold=True, font=FONT_MONO))]], align=PP_ALIGN.CENTER)
    add_textbox(s, x + Inches(0.18), y + Inches(0.55), half_w - Inches(0.36), Inches(0.8),
                [[(body, dict(size=11.5, color=INK_SOFT))]], line_spacing=1.25)

add_callout(s, MARGIN, BODY_TOP + Inches(3.1), CONTENT_W, Inches(0.85),
            "다음 단계 (우선순위 순) — 시군구 단위 시세 병합 → 임대인 위험 축 추가 → 확률 구간 기반 위험 등급 설계 "
            "→ 실사고·정상 라벨 확보 시 재학습.")

# ============================================================
# 16 결론
# ============================================================
s = add_slide()
add_header(s, "CASE FILE CLOSED", "15 / 16")
add_title(s, "세 문장으로 요약하면")

concl = [
    ("① 위험은 겹칠 때 증폭된다", "전세가율이 위험의 압도적 1순위이며(90% 이상 구간 사고율 24%, 70% 미만의 11배), "
                             "여기에 선순위채권·동네 시세 대비 과대 보증금이 겹칠 때 위험이 증폭된다."),
    ("② 정확도가 아니라 AUC·F1을 같이 봐야 보인다", "사고가 7.5%뿐인 불균형 데이터라 F1만 보면 모델을 과소평가하게 "
                                          "된다. 불균형을 보정한 트리 기반 LightGBM(scale_pos_weight)으로 "
                                          "ROC-AUC 0.887까지 끌어올렸고, 이 구분력이 있어야 조합 패턴을 설명 "
                                          "가능한 형태로 분해할 수 있었다."),
    ("③ 모든 판정을 설명할 수 있다", 'SHAP으로 모든 판정을 "위험 요인 1위: OO(기여도 +△)" 형식으로 분해할 수 있어, '
                              "'왜 위험한가'를 설명하는 탐정형 리포트가 기술적으로 구현 가능함을 확인했다."),
]
y = BODY_TOP
for title, body in concl:
    add_card(s, MARGIN, y, CONTENT_W, Inches(1.35), title=title, body=body, body_size=13)
    y += Inches(1.45)

add_textbox(s, MARGIN, y + Inches(0.05), CONTENT_W, Inches(0.3),
            [[("데이터 — 전세보증대위변제현황_깡통라벨.xlsx          코드 — 전세사기예측_AUC 비교.ipynb"
               "          대시보드 — 전세사기예측_대시보드 추가.ipynb",
               dict(size=10.5, color=INK_FAINT, font=FONT_MONO))]])
add_textbox(s, MARGIN, y + Inches(0.35), CONTENT_W, Inches(0.35),
            [[("전세탐정 팀 — 박지민 · 박소연 · 송예원 · 이다영          감사합니다",
               dict(size=12, color=INK_FAINT, font=FONT_MONO))]])

prs.save("/tmp/claude-0/-home-user-fintech-internship-2026/6cb84eed-7ff1-5d3c-9081-efae9253ced9/scratchpad/jeonse-detective-deck.pptx")
print("saved")
