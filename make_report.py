import base64

charts = {}
for i in range(1, 11):
    with open(f'/home/user/fintech-internship-2026/report_charts/chart_{i:02d}.png', 'rb') as f:
        charts[i] = base64.b64encode(f.read()).decode()

def img(n, alt=''):
    return f'<img src="data:image/png;base64,{charts[n]}" alt="{alt}" style="width:100%;max-width:1200px;margin:16px auto;display:block;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.12);">'

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>경남 CSI — Static_Dimension EDA 분석 리포트</title>
<style>
/* ── 기본 리셋 & 폰트 ── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
  background: #f0f4f8;
  color: #1a2a3a;
  line-height: 1.75;
  font-size: 15px;
}}
a {{ color: #1565c0; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* ── 레이아웃 래퍼 ── */
.page-wrap {{
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 20px 60px;
}}

/* ── 헤더 ── */
.report-header {{
  background: linear-gradient(135deg, #0d2b55 0%, #0a4a7a 50%, #0b7ea8 100%);
  color: #fff;
  padding: 52px 48px 44px;
  border-radius: 0 0 18px 18px;
  margin-bottom: 36px;
  position: relative;
  overflow: hidden;
}}
.report-header::before {{
  content: '';
  position: absolute;
  top: -60px; right: -60px;
  width: 320px; height: 320px;
  background: rgba(255,255,255,0.05);
  border-radius: 50%;
}}
.report-header::after {{
  content: '';
  position: absolute;
  bottom: -80px; left: 40%;
  width: 400px; height: 400px;
  background: rgba(255,255,255,0.04);
  border-radius: 50%;
}}
.header-badge {{
  display: inline-block;
  background: rgba(255,255,255,0.18);
  border: 1px solid rgba(255,255,255,0.35);
  color: #e8f4fd;
  font-size: 12px;
  letter-spacing: 1.5px;
  padding: 4px 14px;
  border-radius: 20px;
  margin-bottom: 14px;
  text-transform: uppercase;
}}
.report-header h1 {{
  font-size: 2.1rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 10px;
  line-height: 1.3;
  position: relative;
  z-index: 1;
}}
.report-header .subtitle {{
  font-size: 1.05rem;
  color: #b8d8f0;
  position: relative;
  z-index: 1;
}}
.header-meta {{
  display: flex;
  gap: 32px;
  margin-top: 28px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}}
.meta-item {{
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}}
.meta-label {{
  font-size: 11px;
  color: #90c4e8;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}}
.meta-value {{
  font-size: 1.05rem;
  font-weight: 700;
  color: #fff;
}}

/* ── 목차 ── */
.toc-box {{
  background: #fff;
  border: 1px solid #d0e4f5;
  border-left: 5px solid #1565c0;
  border-radius: 10px;
  padding: 28px 32px;
  margin-bottom: 36px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}}
.toc-box h2 {{
  font-size: 1.05rem;
  font-weight: 700;
  color: #0d2b55;
  margin-bottom: 16px;
  letter-spacing: 0.3px;
}}
.toc-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 6px 24px;
}}
.toc-grid a {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.92rem;
  color: #1565c0;
  padding: 4px 0;
}}
.toc-grid a:hover {{ color: #0b4fa8; }}
.toc-num {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  background: #e3f0fd;
  color: #1565c0;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}}

/* ── 섹션 카드 ── */
.section {{
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 14px rgba(0,0,0,0.07);
  margin-bottom: 36px;
  overflow: hidden;
}}
.section-header {{
  padding: 22px 32px;
  display: flex;
  align-items: center;
  gap: 14px;
}}
.sh-executive {{ background: linear-gradient(90deg, #0d2b55, #1565c0); color: #fff; }}
.sh-blue      {{ background: linear-gradient(90deg, #1565c0, #1976d2); color: #fff; }}
.sh-teal      {{ background: linear-gradient(90deg, #00695c, #00897b); color: #fff; }}
.sh-purple    {{ background: linear-gradient(90deg, #4527a0, #5e35b1); color: #fff; }}
.sh-amber     {{ background: linear-gradient(90deg, #e65100, #ef6c00); color: #fff; }}
.sh-green     {{ background: linear-gradient(90deg, #2e7d32, #388e3c); color: #fff; }}
.sh-crimson   {{ background: linear-gradient(90deg, #880e4f, #ad1457); color: #fff; }}
.sh-navy      {{ background: linear-gradient(90deg, #0d2b55, #0a4a7a); color: #fff; }}
.sh-indigo    {{ background: linear-gradient(90deg, #283593, #3949ab); color: #fff; }}
.sh-brown     {{ background: linear-gradient(90deg, #4e342e, #6d4c41); color: #fff; }}
.sh-conclusion {{ background: linear-gradient(90deg, #1a237e, #283593); color: #fff; }}

.section-icon {{
  font-size: 1.6rem;
  line-height: 1;
}}
.section-header h2 {{
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.2px;
}}
.section-header .cell-badge {{
  margin-left: auto;
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.35);
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 12px;
  white-space: nowrap;
}}
.section-body {{
  padding: 28px 32px;
}}
.section-desc {{
  font-size: 0.97rem;
  color: #455a64;
  margin-bottom: 22px;
  border-left: 3px solid #90caf9;
  padding-left: 14px;
  line-height: 1.8;
}}

/* ── 차트 컨테이너 ── */
.chart-container {{
  margin: 20px 0 28px;
  text-align: center;
}}
.chart-caption {{
  font-size: 12px;
  color: #78909c;
  margin-top: 8px;
  font-style: italic;
}}

/* ── 통계 카드 그리드 ── */
.stats-title {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 700;
  color: #0d2b55;
  margin: 24px 0 14px;
}}
.stats-title::before {{
  content: '';
  width: 4px; height: 18px;
  background: #1565c0;
  border-radius: 2px;
}}
.stats-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}}
.stat-card {{
  background: #f0f7ff;
  border: 1px solid #d0e8fc;
  border-radius: 10px;
  padding: 14px 16px;
}}
.stat-card.green-card  {{ background: #f0fdf4; border-color: #c3e6cb; }}
.stat-card.amber-card  {{ background: #fff8e1; border-color: #ffe082; }}
.stat-card.red-card    {{ background: #fff5f5; border-color: #ffcdd2; }}
.stat-card.purple-card {{ background: #f3e5f5; border-color: #e1bee7; }}
.stat-card.teal-card   {{ background: #e0f2f1; border-color: #b2dfdb; }}
.stat-label {{
  font-size: 11px;
  color: #607d8b;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}}
.stat-value {{
  font-size: 1.35rem;
  font-weight: 800;
  color: #0d2b55;
  line-height: 1.1;
}}
.stat-unit {{
  font-size: 0.8rem;
  font-weight: 400;
  color: #607d8b;
  margin-left: 2px;
}}
.stat-sub {{
  font-size: 11.5px;
  color: #78909c;
  margin-top: 4px;
}}

/* ── 분석 박스 ── */
.analysis-box {{
  background: #fafcff;
  border: 1px solid #e3edf8;
  border-radius: 10px;
  padding: 20px 24px;
  margin: 18px 0;
}}
.analysis-box.green  {{ background: #f9fdf9; border-color: #c8e6c9; }}
.analysis-box.amber  {{ background: #fffdf0; border-color: #ffe082; }}
.analysis-box.purple {{ background: #fdf5ff; border-color: #e1bee7; }}
.analysis-box.red    {{ background: #fff8f8; border-color: #ffcdd2; }}
.analysis-heading {{
  font-size: 0.95rem;
  font-weight: 700;
  color: #0d2b55;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.analysis-box p, .analysis-box li {{
  font-size: 0.93rem;
  color: #37474f;
  line-height: 1.85;
}}
.analysis-box ul {{
  padding-left: 20px;
  margin-top: 6px;
}}
.analysis-box li {{ margin-bottom: 6px; }}

/* ── 배지 ── */
.badge {{
  display: inline-block;
  padding: 2px 9px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.6;
}}
.badge-blue   {{ background: #e3f2fd; color: #1565c0; }}
.badge-green  {{ background: #e8f5e9; color: #2e7d32; }}
.badge-amber  {{ background: #fff8e1; color: #e65100; }}
.badge-red    {{ background: #ffebee; color: #c62828; }}
.badge-purple {{ background: #f3e5f5; color: #6a1b9a; }}
.badge-teal   {{ background: #e0f2f1; color: #00695c; }}
.badge-gray   {{ background: #eceff1; color: #455a64; }}

/* ── 데이터 테이블 ── */
.data-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  margin: 14px 0;
}}
.data-table th {{
  background: #0d2b55;
  color: #fff;
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
}}
.data-table td {{
  padding: 9px 14px;
  border-bottom: 1px solid #e8edf2;
  vertical-align: middle;
}}
.data-table tr:nth-child(even) td {{ background: #f5f9ff; }}
.data-table tr:hover td {{ background: #e8f4fd; }}
.data-table .num {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}

/* ── 하이라이트 박스 ── */
.highlight-row {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin: 14px 0;
}}
.hl-chip {{
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #e8f4fd;
  border: 1px solid #b3d7f5;
  border-radius: 10px;
  padding: 10px 16px;
  min-width: 120px;
  text-align: center;
}}
.hl-chip .hl-val {{ font-size: 1.2rem; font-weight: 800; color: #1565c0; }}
.hl-chip .hl-lbl {{ font-size: 11.5px; color: #546e7a; margin-top: 3px; }}

/* ── CSI 활용 박스 ── */
.csi-box {{
  background: linear-gradient(135deg, #e8f5e9 0%, #e3f2fd 100%);
  border: 1px solid #a5d6a7;
  border-radius: 10px;
  padding: 20px 24px;
  margin-top: 18px;
}}
.csi-heading {{
  font-size: 0.95rem;
  font-weight: 700;
  color: #1b5e20;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.csi-box p, .csi-box li {{
  font-size: 0.92rem;
  color: #2e4a1e;
  line-height: 1.85;
}}
.csi-box ul {{ padding-left: 20px; margin-top: 6px; }}
.csi-box li {{ margin-bottom: 6px; }}

/* ── 결론 섹션 ── */
.conclusion-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  margin: 20px 0;
}}
.conclusion-card {{
  background: #f0f7ff;
  border-radius: 10px;
  padding: 18px 20px;
  border-top: 4px solid #1565c0;
}}
.conclusion-card.green  {{ background: #f0fdf4; border-top-color: #2e7d32; }}
.conclusion-card.amber  {{ background: #fffbf0; border-top-color: #e65100; }}
.conclusion-card.purple {{ background: #fdf5ff; border-top-color: #6a1b9a; }}
.conclusion-card h4 {{
  font-size: 0.95rem;
  font-weight: 700;
  color: #0d2b55;
  margin-bottom: 8px;
}}
.conclusion-card p {{
  font-size: 0.88rem;
  color: #37474f;
  line-height: 1.8;
}}

/* ── 풋터 ── */
.report-footer {{
  text-align: center;
  padding: 28px 0 12px;
  font-size: 12px;
  color: #90a4ae;
  border-top: 1px solid #e0e7ef;
  margin-top: 20px;
}}

/* ── 구분선 ── */
.divider {{
  height: 1px;
  background: linear-gradient(90deg, transparent, #d0e4f5, transparent);
  margin: 24px 0;
}}

/* ── 인쇄 ── */
@media print {{
  body {{ background: #fff; font-size: 12px; }}
  .section {{ box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }}
  .report-header {{ border-radius: 0; }}
  .toc-box {{ display: none; }}
  .section-header h2 {{ font-size: 1rem; }}
  img {{ max-width: 100% !important; }}
}}

/* ── 반응형 ── */
@media (max-width: 768px) {{
  .report-header {{ padding: 32px 22px 28px; }}
  .report-header h1 {{ font-size: 1.5rem; }}
  .section-body {{ padding: 20px 18px; }}
  .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
  .header-meta {{ gap: 18px; }}
}}
</style>
</head>
<body>
<div class="page-wrap">

<!-- ══════════════════════════════════════════
     HEADER
══════════════════════════════════════════ -->
<header class="report-header">
  <div class="header-badge">경남 CSI 인턴십 2026 · EDA 리포트</div>
  <h1>경상남도 CSI — Static_Dimension<br>탐색적 데이터 분석 리포트</h1>
  <p class="subtitle">관광객 유입 특성 데이터셋 심층 분석 | 유입유출비율 · 체류·숙박 · 업종소비액 · 관광취약도</p>
  <div class="header-meta">
    <div class="meta-item"><span class="meta-label">데이터셋</span><span class="meta-value">Static_Dimension</span></div>
    <div class="meta-item"><span class="meta-label">데이터 규모</span><span class="meta-value">1,457행 × 11열</span></div>
    <div class="meta-item"><span class="meta-label">수록 시군구</span><span class="meta-value">22개 (창원 5구 포함)</span></div>
    <div class="meta-item"><span class="meta-label">분석 기준일</span><span class="meta-value">2026년 5월 28일</span></div>
    <div class="meta-item"><span class="meta-label">분석 담당</span><span class="meta-value">경남 CSI 인턴십팀</span></div>
  </div>
</header>

<!-- ══════════════════════════════════════════
     목차
══════════════════════════════════════════ -->
<div class="toc-box">
  <h2>📋 목차 (Table of Contents)</h2>
  <div class="toc-grid">
    <a href="#executive"><span class="toc-num">★</span>핵심 요약 (Executive Summary)</a>
    <a href="#cell04"><span class="toc-num">1</span>셀 4 — 기본 통계 및 결측치 현황</a>
    <a href="#cell05"><span class="toc-num">2</span>셀 5 — 행 유형 분포</a>
    <a href="#cell06"><span class="toc-num">3</span>셀 6 — 시군구 커버리지</a>
    <a href="#cell07"><span class="toc-num">4</span>셀 7 — 데이터 품질 이슈</a>
    <a href="#cell09"><span class="toc-num">5</span>셀 9 — 유입유출비율 시군구 분석</a>
    <a href="#cell10"><span class="toc-num">6</span>셀 10 — 주요 유입 출발지 분석</a>
    <a href="#cell11"><span class="toc-num">7</span>셀 11 — 체류시간 및 숙박일수 분석</a>
    <a href="#cell12"><span class="toc-num">8</span>셀 12 — 업종별 소비액 분석</a>
    <a href="#cell13"><span class="toc-num">9</span>셀 13 — HHI 업종 집중도 분석</a>
    <a href="#cell14"><span class="toc-num">10</span>셀 14 — 관광취약도 점수 분석</a>
    <a href="#conclusion"><span class="toc-num">✓</span>종합 결론 및 제언</a>
  </div>
</div>

<!-- ══════════════════════════════════════════
     EXECUTIVE SUMMARY
══════════════════════════════════════════ -->
<section class="section" id="executive">
  <div class="section-header sh-executive">
    <span class="section-icon">⭐</span>
    <h2>핵심 요약 (Executive Summary)</h2>
  </div>
  <div class="section-body">
    <p class="section-desc">
      본 리포트는 경상남도 23개 시군구의 관광객 유입 특성을 수록한 <strong>Static_Dimension</strong> 데이터셋에 대한 탐색적 데이터 분석(EDA) 결과를 종합 정리한 문서입니다.
      유입유출비율, 체류·숙박 패턴, 업종별 소비액, 그리고 종합 관광취약도 점수를 중심으로 경남 각 지역의 관광 경쟁력을 진단하였습니다.
    </p>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">전체 데이터 행수</div>
        <div class="stat-value">1,457<span class="stat-unit">행</span></div>
        <div class="stat-sub">× 11개 컬럼</div>
      </div>
      <div class="stat-card green-card">
        <div class="stat-label">수록 시군구</div>
        <div class="stat-value">22<span class="stat-unit">개</span></div>
        <div class="stat-sub">창원시 5개구 포함</div>
      </div>
      <div class="stat-card amber-card">
        <div class="stat-label">최고 유입유출비율</div>
        <div class="stat-value">40.15</div>
        <div class="stat-sub">창원시 의창구</div>
      </div>
      <div class="stat-card purple-card">
        <div class="stat-label">관광취약도 최고</div>
        <div class="stat-value">59.7<span class="stat-unit">점</span></div>
        <div class="stat-sub">사천시 (100점 만점)</div>
      </div>
      <div class="stat-card red-card">
        <div class="stat-label">주요 결측률</div>
        <div class="stat-value">74.9<span class="stat-unit">%</span></div>
        <div class="stat-sub">업종대분류명·소비액</div>
      </div>
      <div class="stat-card teal-card">
        <div class="stat-label">1위 소비 업종</div>
        <div class="stat-value">37.3<span class="stat-unit">%</span></div>
        <div class="stat-sub">쇼핑업 (₩18.7B)</div>
      </div>
    </div>

    <div class="analysis-box">
      <div class="analysis-heading">🔑 5대 핵심 발견</div>
      <ul>
        <li><strong>높은 유입유출비율, 강한 관광 흡인력:</strong> 경남 시군구 평균 유입유출비율은 4.28로, 유입 관광객이 유출 인구를 크게 상회합니다. 창원시 의창구(40.15)·사천시(39.30)·산청군(32.40) 등 5개 지역은 "관광특화(30+)" 등급에 해당하며, 관광 수요가 집중적으로 발생하는 핵심 거점입니다.</li>
        <li><strong>체류·숙박의 균질성 — 차별화 과제:</strong> 전 시군구가 평균 2.7일 숙박, 20.7~21.3시간 체류라는 매우 좁은 범위에 집중되어 있어, 체류 연장을 유도할 킬러 콘텐츠 개발이 시급합니다.</li>
        <li><strong>소비 구조 편중 — 쇼핑·식음료 2분 체계:</strong> 전체 관광 소비의 약 67%가 쇼핑업(37.3%)과 식음료업(29.6%)에 집중되어 있어, 여가·체험·문화 소비로의 다각화가 필요합니다.</li>
        <li><strong>데이터 품질 이슈 — 전처리 필수:</strong> 업종대분류명·소비액 컬럼의 결측률이 74.9%이며, '함천군' 오타(16행)와 소비액 0 행(140개)이 존재해 분석 전 정제가 필수입니다.</li>
        <li><strong>관광취약도 격차:</strong> 사천시(59.7점)와 양산시(25.9점) 간 약 34점 차이는 관광 인프라·접근성·다양성 측면에서 지역 간 불균형이 심각함을 시사합니다.</li>
      </ul>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 전략적 시사점</div>
      <p>본 EDA 결과는 경남 관광 CSI 지수 설계에 있어 <strong>유입유출비율</strong>을 핵심 지표로 채택하고, 체류·숙박 지표는 보완 지표로 활용하는 근거를 제공합니다. 또한 업종 다양성(HHI)과 관광취약도 점수를 복합 가중치 설계에 통합함으로써, 단순 방문객 수 중심에서 탈피한 질적 성과 지표 체계를 구축할 수 있습니다.</p>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 4 — 기본 통계 및 결측치
══════════════════════════════════════════ -->
<section class="section" id="cell04">
  <div class="section-header sh-blue">
    <span class="section-icon">📊</span>
    <h2>셀 4 — 기본 통계 및 결측치 현황</h2>
    <span class="cell-badge">데이터셋 개요</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      Static_Dimension 데이터셋의 전반적인 구조를 파악하기 위해 각 컬럼의 결측률, 기초 통계량(평균·최대·분포)을 산출하였습니다.
      컬럼별 결측 패턴은 데이터가 여러 유형의 행으로 혼합 구성되어 있음을 시사하며, 이후 분석 전략 수립에 핵심 근거를 제공합니다.
    </p>

    <div class="stats-title">📊 주요 수치</div>
    <div class="stats-grid">
      <div class="stat-card amber-card">
        <div class="stat-label">업종대분류명 결측률</div>
        <div class="stat-value">74.9<span class="stat-unit">%</span></div>
        <div class="stat-sub">소비액도 동일 74.9%</div>
      </div>
      <div class="stat-card amber-card">
        <div class="stat-label">유입유출비율 결측률</div>
        <div class="stat-value">45.4<span class="stat-unit">%</span></div>
        <div class="stat-sub">절반 가까이 미수록</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">유입유출비율 평균</div>
        <div class="stat-value">4.28</div>
        <div class="stat-sub">최대값: 40.15</div>
      </div>
      <div class="stat-card green-card">
        <div class="stat-label">평균 체류시간</div>
        <div class="stat-value">1,253<span class="stat-unit">분</span></div>
        <div class="stat-sub">≈ 20.9시간</div>
      </div>
      <div class="stat-card purple-card">
        <div class="stat-label">소비액 평균</div>
        <div class="stat-value">137,044<span class="stat-unit">원</span></div>
        <div class="stat-sub">최대: ₩6,781,443</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">전체 행 수</div>
        <div class="stat-value">1,457<span class="stat-unit">행</span></div>
        <div class="stat-sub">× 11개 컬럼</div>
      </div>
    </div>

    <div class="analysis-box">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>업종대분류명과 소비액의 결측률이 동일하게 74.9%라는 사실은 이 두 컬럼이 구조적으로 연동되어 있음을 의미합니다. 즉, 소비액 행이 존재하지 않는 레코드는 업종 분류도 없는 형태로, 데이터셋 내에서 "업종 소비 행"과 "체류·유입 행"이 별도로 구분되어 있음을 시사합니다.</p>
      <p style="margin-top:10px;">유입유출비율의 결측 45.4%는 일부 시군구·OD 조합에서 해당 지표가 측정되지 않았거나, 특정 조건(예: 업종 소비액 레코드)에만 기록되는 구조적 이유에 기인합니다. 소비액 최대값 ₩6,781,443은 평균(₩137,044) 대비 49배에 달하는 극단값으로, 이상값 처리 전략이 필수적입니다.</p>
      <p style="margin-top:10px;">평균 체류시간 1,253분(약 20.9시간)은 대부분의 방문객이 1박 이상 체류함을 나타내며, 당일치기보다 숙박형 관광이 지배적임을 보여주는 중요한 베이스라인 수치입니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>결측 패턴 기반으로 데이터를 <strong>업종소비 행</strong>과 <strong>체류·유입 행</strong>으로 분리 처리하는 전처리 파이프라인을 설계합니다.</li>
        <li>유입유출비율과 소비액의 극단값 문제를 해결하기 위해 Q3+3IQR 기준 Winsorization 또는 로그 변환을 적용합니다.</li>
        <li>평균 체류시간(1,253분)을 CSI 체류 지표의 기준값(benchmark)으로 설정하여, 목표 지수 산정 시 가중치 조정에 활용합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 5 — 행 유형 분포
══════════════════════════════════════════ -->
<section class="section" id="cell05">
  <div class="section-header sh-teal">
    <span class="section-icon">🗂️</span>
    <h2>셀 5 — 행 유형 분포 분석</h2>
    <span class="cell-badge">chart_01</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      데이터셋 내 각 행은 포함된 컬럼 값의 조합에 따라 4가지 유형으로 분류됩니다.
      유형 분포를 파악하면 분석 목적별 서브셋 추출 전략을 수립할 수 있으며, 데이터 수집 과정의 구조적 특성도 이해할 수 있습니다.
    </p>

    <div class="chart-container">
      {img(1, '행 유형 분포 차트')}
      <div class="chart-caption">▲ 그림 1. Static_Dimension 데이터셋 행 유형별 분포 (n=1,457)</div>
    </div>

    <div class="stats-title">📊 주요 수치</div>
    <table class="data-table">
      <thead>
        <tr>
          <th>유형</th>
          <th>설명</th>
          <th class="num">행 수</th>
          <th class="num">비율</th>
        </tr>
      </thead>
      <tbody>
        <tr><td><span class="badge badge-blue">② 유입비율+체류숙박</span></td><td>유입유출비율 + 평균체류시간 + 숙박일수 모두 수록</td><td class="num">541</td><td class="num"><strong>37.1%</strong></td></tr>
        <tr><td><span class="badge badge-green">① 업종소비액</span></td><td>업종대분류명 + 소비액 수록</td><td class="num">366</td><td class="num"><strong>25.1%</strong></td></tr>
        <tr><td><span class="badge badge-amber">④ 체류숙박만</span></td><td>체류시간·숙박일수만 있고 유입비율 미수록</td><td class="num">295</td><td class="num"><strong>20.2%</strong></td></tr>
        <tr><td><span class="badge badge-purple">③ 유입비율만</span></td><td>유입유출비율만 있고 체류·숙박 미수록</td><td class="num">255</td><td class="num"><strong>17.5%</strong></td></tr>
      </tbody>
    </table>

    <div class="analysis-box">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>가장 많은 비중을 차지하는 유형 ②(37.1%)는 유입유출비율과 체류·숙박 정보가 동시에 수록된 "풀 레코드"로, 복합 분석에 가장 유용한 행입니다. 유형 ①(25.1%)은 업종별 소비 행으로, 유입 지표는 없지만 소비 패턴 분석의 핵심 데이터가 됩니다.</p>
      <p style="margin-top:10px;">유형 ④(20.2%, 체류숙박만)와 유형 ③(17.5%, 유입비율만)은 정보가 불완전한 행입니다. 두 유형을 합하면 전체의 37.7%로, 상당히 높은 비율의 레코드가 일부 지표만 포함합니다. 이는 데이터 수집 과정에서 측정 시스템의 불균형이 있었거나, 일부 OD쌍에서 특정 지표가 계산 불가능했음을 의미합니다.</p>
      <p style="margin-top:10px;">유형 구조를 이해하면 분석 목적에 따라 적절한 서브셋을 선택하는 것이 중요합니다. 예를 들어, 유입 경쟁력 분석은 유형 ②+③(총 796행), 소비 분석은 유형 ①(366행), 종합 프로파일링에는 유형 ②(541행)만 사용해야 정확도가 높아집니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>CSI 지수 산정 시 <strong>유형 ②(541행)</strong>를 기본 분석 단위로 사용하여 유입·체류·숙박을 동시에 고려하는 복합 지표를 산출합니다.</li>
        <li>업종 소비 분석에는 유형 ①(366행)을 별도 추출하여 지역별 소비 다양성 지수(HHI)를 계산합니다.</li>
        <li>유형 ④·③의 높은 비중은 일부 시군구에서 지표 취득 가능성이 낮음을 시사하므로, 결측 시군구에 대한 대체값(imputation) 전략도 함께 수립합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 6 — 시군구 커버리지
══════════════════════════════════════════ -->
<section class="section" id="cell06">
  <div class="section-header sh-purple">
    <span class="section-icon">🗺️</span>
    <h2>셀 6 — 시군구 커버리지 분석</h2>
    <span class="cell-badge">chart_02</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      경상남도 23개 시군구 중 데이터셋에 수록된 지역과 누락된 지역을 파악합니다.
      특히 창원시의 경우 통합시로 기록되는 대신 5개 행정구로 분리 수록되어 있어, 실질적 커버리지와 행정 단위 정합성 확인이 필요합니다.
    </p>

    <div class="chart-container">
      {img(2, '시군구 커버리지 차트')}
      <div class="chart-caption">▲ 그림 2. 시군구별 데이터 수록 현황 및 커버리지</div>
    </div>

    <div class="stats-title">📊 주요 수치</div>
    <div class="stats-grid">
      <div class="stat-card green-card">
        <div class="stat-label">수록 시군구 수</div>
        <div class="stat-value">22<span class="stat-unit">개</span></div>
        <div class="stat-sub">창원 5개구 포함</div>
      </div>
      <div class="stat-card amber-card">
        <div class="stat-label">누락 지역</div>
        <div class="stat-value">1<span class="stat-unit">개</span></div>
        <div class="stat-sub">창원시(통합) → 5구 분리</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">경남 전체 시군구</div>
        <div class="stat-value">23<span class="stat-unit">개</span></div>
        <div class="stat-sub">기본 행정단위 기준</div>
      </div>
    </div>

    <div class="analysis-box">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>데이터셋은 창원시를 통합 단위(1개)가 아닌 5개 행정구(의창구·성산구·마산합포구·마산회원구·진해구)로 분리 수록하고 있습니다. 이는 인구 규모와 관광 특성이 구별로 상이한 창원시의 내부 이질성을 반영하기 위한 설계로, 분석의 정밀도를 높일 수 있습니다.</p>
      <p style="margin-top:10px;">반면, 공식 행정 통계(23개 시군구)와의 집계 비교 시 창원시(통합) 단위 수치가 없어 직접 비교에 제한이 생깁니다. 또한 오타(함천군→합천군)로 인해 실제 고유 시군구 수가 프로그램상 23개로 잘못 카운팅될 수 있으므로, 전처리 시 문자열 정규화가 선행되어야 합니다.</p>
      <p style="margin-top:10px;">22개 지역 중 대부분이 데이터를 보유하고 있으나, 창원시 통합 단위 부재로 인해 경남 전체 시군구 비교 시 창원 관련 수치는 5개 구를 합산하는 별도 처리가 필요합니다. 이 점은 광역 수준의 관광 통계 보고서 작성 시 반드시 고려해야 하는 구조적 특성입니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>창원시 5개구의 CSI 지수를 개별 산출한 후, 필요 시 인구 가중 평균으로 창원시 통합 CSI를 별도 산출하는 이중 집계 체계를 설계합니다.</li>
        <li>'함천군' 오타를 포함한 문자열 정규화 전처리를 모든 분석 파이프라인의 첫 단계에 삽입합니다.</li>
        <li>커버리지 100% 달성을 위해 누락 시군구(존재 시)에 대한 데이터 수집 계획을 별도 수립하고, 공백 지역은 결측 처리 방침을 사전 명시합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 7 — 데이터 품질 이슈
══════════════════════════════════════════ -->
<section class="section" id="cell07">
  <div class="section-header sh-amber">
    <span class="section-icon">⚠️</span>
    <h2>셀 7 — 데이터 품질 이슈 진단</h2>
    <span class="cell-badge">chart_03</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      실제 분석에 영향을 미치는 4가지 데이터 품질 문제—오타, 소비액 0값, 중복 OD쌍, 유입유출비율 이상값—를 체계적으로 진단하였습니다.
      각 이슈의 규모와 원인을 파악하여 후속 전처리 전략을 수립합니다.
    </p>

    <div class="chart-container">
      {img(3, '데이터 품질 이슈 차트')}
      <div class="chart-caption">▲ 그림 3. 데이터 품질 이슈 유형별 현황 (오타·0값·중복·이상값)</div>
    </div>

    <div class="stats-title">📊 주요 수치</div>
    <table class="data-table">
      <thead>
        <tr><th>품질 이슈</th><th>규모</th><th>주요 해당 지역</th><th>권장 처리</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><span class="badge badge-amber">오타</span> 함천군 → 합천군</td>
          <td class="num">16행</td>
          <td>합천군 전체</td>
          <td>문자열 replace 수정</td>
        </tr>
        <tr>
          <td><span class="badge badge-red">소비액 0값</span></td>
          <td class="num">140행</td>
          <td>양산시·진주시·창녕군·창원 각구</td>
          <td>NaN 대체 또는 제외</td>
        </tr>
        <tr>
          <td><span class="badge badge-purple">중복 OD쌍</span></td>
          <td class="num">156개 조합</td>
          <td>성별·연령대 세분화 추정</td>
          <td>집계 전 그룹화 필요</td>
        </tr>
        <tr>
          <td><span class="badge badge-blue">유입비율 이상값</span></td>
          <td class="num">47행</td>
          <td>창원의창구·사천시 등</td>
          <td>Q3+3IQR(=15.50) 기준</td>
        </tr>
      </tbody>
    </table>

    <div class="highlight-row">
      <div class="hl-chip"><span class="hl-val">15.50</span><span class="hl-lbl">이상값 임계선 (Q3+3IQR)</span></div>
      <div class="hl-chip"><span class="hl-val">47행</span><span class="hl-lbl">이상값 해당 레코드</span></div>
      <div class="hl-chip"><span class="hl-val">40.15</span><span class="hl-lbl">최대 유입비율 (의창구)</span></div>
      <div class="hl-chip"><span class="hl-val">39.5</span><span class="hl-lbl">2위 (사천시→진주시)</span></div>
    </div>

    <div class="analysis-box">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>'함천군' 오타는 16행에 걸쳐 일관되게 발생하고 있어 데이터 입력 단계에서 시스템적 오류가 발생했음을 시사합니다. 단순 str.replace()로 수정 가능하나, 전처리 시 반드시 검증 로그를 남겨야 합니다.</p>
      <p style="margin-top:10px;">소비액 0값 140행은 실제 소비 없음(방문만)과 측정 실패를 구분할 수 없어 해석에 주의가 필요합니다. 양산시·진주시 등 도심 지역에 집중된 점을 고려하면, 대형 이벤트·무료 시설 방문 등 소비 없는 유입 패턴이 반영된 것일 수 있습니다.</p>
      <p style="margin-top:10px;">중복 OD쌍 156개 조합은 동일 출발지-도착지 쌍이 성별·연령대별로 세분화되어 복수 행으로 수록된 결과로 추정됩니다. 시군구 단위 집계 시 이를 반드시 그룹화(groupby + 가중 평균)하지 않으면 수치가 중복 산정됩니다. 이상값(47행)은 Q3+3IQR=15.50 기준을 초과하는 행으로, 통계 분석에서는 처리가 필요하지만, 관광 특화 지역의 실제 특성을 반영하는 의미 있는 데이터일 수 있어 무조건 제거보다는 별도 분석 대상으로 분류하는 것이 적절합니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>전처리 파이프라인 Step 1: 오타 수정 → Step 2: 소비액 0 처리 → Step 3: OD쌍 중복 집계 → Step 4: 이상값 플래깅 순서를 표준화합니다.</li>
        <li>이상값 47행은 별도 "고관광특화" 세그먼트로 분류하여 CSI 분석에서 가중치를 달리 적용하거나, 별도 모니터링 대시보드에서 관리합니다.</li>
        <li>소비액 0행은 결측 처리 전에 해당 지역의 관광 유형(무료 시설 위주 여부)을 확인하여 의미 있는 0과 측정 오류를 구분합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 9 — 유입유출비율
══════════════════════════════════════════ -->
<section class="section" id="cell09">
  <div class="section-header sh-green">
    <span class="section-icon">📈</span>
    <h2>셀 9 — 시군구별 유입유출비율 분석</h2>
    <span class="cell-badge">chart_04</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      유입유출비율(유입 관광객 수 ÷ 해당 지역 거주 유출 인구)은 지역의 관광 흡인력을 나타내는 핵심 지표입니다.
      시군구별 평균을 산출하고 4단계 등급(관광특화·고관광형·관광형·일반형)으로 분류하여 경남 관광 경쟁력 지도를 작성합니다.
    </p>

    <div class="chart-container">
      {img(4, '시군구별 유입유출비율 차트')}
      <div class="chart-caption">▲ 그림 4. 경남 시군구별 유입유출비율 평균 및 등급 분류</div>
    </div>

    <div class="stats-title">📊 주요 수치 — 유입유출비율 상위 시군구</div>
    <table class="data-table">
      <thead>
        <tr><th>순위</th><th>시군구</th><th class="num">유입유출비율</th><th>등급</th><th>특성</th></tr>
      </thead>
      <tbody>
        <tr><td>1</td><td>창원시 의창구</td><td class="num">40.15</td><td><span class="badge badge-red">관광특화(30+)</span></td><td>창원 관광중심 거점</td></tr>
        <tr><td>2</td><td>사천시</td><td class="num">39.30</td><td><span class="badge badge-red">관광특화(30+)</span></td><td>항공·해양 관광</td></tr>
        <tr><td>3</td><td>창원시 성산구</td><td class="num">34.50</td><td><span class="badge badge-red">관광특화(30+)</span></td><td>MICE·컨벤션 집중</td></tr>
        <tr><td>4</td><td>산청군</td><td class="num">32.40</td><td><span class="badge badge-red">관광특화(30+)</span></td><td>한방·생태관광</td></tr>
        <tr><td>5</td><td>창원시 마산합포구</td><td class="num">31.20</td><td><span class="badge badge-red">관광특화(30+)</span></td><td>항구·문화관광</td></tr>
        <tr><td>—</td><td>합천군 (최하위)</td><td class="num">~7~9</td><td><span class="badge badge-gray">일반형(~10)</span></td><td>내부 이동 중심</td></tr>
      </tbody>
    </table>

    <div class="highlight-row">
      <div class="hl-chip"><span class="hl-val">5개</span><span class="hl-lbl">관광특화(30+) 등급</span></div>
      <div class="hl-chip"><span class="hl-val">9개</span><span class="hl-lbl">고관광형(20~30)</span></div>
      <div class="hl-chip"><span class="hl-val">7개</span><span class="hl-lbl">관광형(10~20)</span></div>
      <div class="hl-chip"><span class="hl-val">1개</span><span class="hl-lbl">일반형(~10)</span></div>
    </div>

    <div class="analysis-box">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>경남 시군구의 유입유출비율은 매우 넓은 스펙트럼을 보입니다. 창원시 의창구(40.15)는 경남 최고 수치로, 유입 관광객이 지역 유출 인구의 40배가 넘는 극도로 강한 흡인력을 나타냅니다. 이는 창원시 내 행정구들이 기능적으로 분화되어 있으며, 의창구가 관광·상업 거점으로 강하게 집중되어 있음을 시사합니다.</p>
      <p style="margin-top:10px;">사천시(39.30)의 높은 비율은 항공우주박물관·삼천포항 등 전국 단위 관광 자원에 기인하며, 산청군(32.40)은 동의보감촌·지리산 접근성을 바탕으로 한 생태·힐링 관광 수요가 반영된 결과입니다. 전체 22개 시군구 중 5개(23%)가 관광특화, 9개(41%)가 고관광형으로, 경남의 3분의 2 이상 지역이 높은 관광 흡인력을 보유하고 있습니다.</p>
      <p style="margin-top:10px;">유일한 일반형(~10) 지역인 합천군은 관광 자원보다 생활 인구 유출이 상대적으로 많은 지역으로, 관광 활성화를 위한 집중 지원이 필요함을 시사합니다. 이 등급 분류 체계는 CSI 지수 가중치 설계의 기초 레이어로 활용될 수 있습니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>유입유출비율 4등급 분류를 CSI 지수의 <strong>관광 흡인력 하위지표</strong>로 직접 활용하며, 등급별 차등 가중치(관광특화 1.0 → 일반형 0.25)를 적용합니다.</li>
        <li>창원시 5개 구의 기능 분화를 분석하여 의창구·성산구 등 고비율 구의 성공 요인을 도출하고, 마산회원구·진해구 등 상대적 저비율 구에 대한 개선 전략을 제안합니다.</li>
        <li>합천군 일반형 지정을 계기로 해당 지역의 관광 잠재력(합천댐·황강 등) 대비 인프라 부족 원인을 별도 심층 분석합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 10 — 주요 유입 출발지
══════════════════════════════════════════ -->
<section class="section" id="cell10">
  <div class="section-header sh-crimson">
    <span class="section-icon">🚗</span>
    <h2>셀 10 — 주요 유입 출발지 분석</h2>
    <span class="cell-badge">chart_05 · chart_06</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      경남 각 시군구로 유입되는 관광객의 출발지(Origin)를 분석하여, 경남 내부 유입 대 도외 유입 비중을 파악하고
      주요 송출 지역을 식별합니다. 이를 통해 타겟 마케팅 권역과 교통·접근성 개선 우선순위를 도출합니다.
    </p>

    <div class="chart-container">
      {img(5, '주요 유입 출발지 분포 차트')}
      <div class="chart-caption">▲ 그림 5-1. 경남 시군구별 주요 유입 출발지 (상위 출발지 분포)</div>
    </div>

    <div class="chart-container">
      {img(6, '도외 유입 출발지 분포 차트')}
      <div class="chart-caption">▲ 그림 5-2. 도외 주요 유입 출발지 상세 분석</div>
    </div>

    <div class="stats-title">📊 주요 수치</div>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">경남 내 최고 유입지</div>
        <div class="stat-value" style="font-size:1.1rem;">진주시</div>
        <div class="stat-sub">평균 유입유출비율 8.98</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">창원 성산구</div>
        <div class="stat-value">7.42</div>
        <div class="stat-sub">2위 경남 내 유입</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">창원 의창구</div>
        <div class="stat-value">6.95</div>
        <div class="stat-sub">3위 경남 내 유입</div>
      </div>
      <div class="stat-card green-card">
        <div class="stat-label">거창군</div>
        <div class="stat-value">6.86</div>
        <div class="stat-sub">4위 경남 내 유입</div>
      </div>
      <div class="stat-card amber-card">
        <div class="stat-label">도외 최고 유입</div>
        <div class="stat-value" style="font-size:1.1rem;">부산 강서구</div>
        <div class="stat-sub">도외 비율 4.14</div>
      </div>
    </div>

    <div class="analysis-box">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>경남 시군구로의 유입은 <strong>경상남도 내부 이동이 압도적 비중</strong>을 차지합니다. 진주시(8.98)·창원 성산구(7.42)·의창구(6.95)·거창군(6.86) 등 상위 유입 출발지가 모두 경남 내 지역으로, 경남 관광은 도내 근거리 이동 중심의 단거리 관광 패턴이 지배적임을 보여줍니다.</p>
      <p style="margin-top:10px;">도외 유입에서는 부산광역시 강서구(4.14)가 최고를 기록했습니다. 부산 강서구는 경남과 인접한 지리적 특성상 경남 서남부 지역(진주·사천·고성 등)으로의 접근이 용이하며, 부산 도시민의 당일·1박 관광 수요가 경남으로 흘러드는 핵심 채널임을 시사합니다. 수도권 및 기타 광역 도시에서의 유입은 상대적으로 낮아, 경남 관광의 인지도 및 장거리 접근성 개선이 과제로 남습니다.</p>
      <p style="margin-top:10px;">거창군(6.86)이 경남 내 4위 유입지로 부상한 것은 덕유산·가조온천 등 자연 자원 기반의 도내 관광 이동이 활발함을 반영합니다. 이처럼 경남 내 관광 이동 네트워크가 촘촘하게 형성되어 있다는 점은 광역 연계 관광 패키지 개발에 유리한 조건입니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>진주시·창원시·거창군을 경남 관광 허브 지역으로 지정하고, 이들 지역 중심의 <strong>관광 클러스터 CSI</strong>를 별도 산출합니다.</li>
        <li>부산 강서구 등 도외 주요 송출 지역을 타겟으로 한 마케팅 캠페인 우선순위를 CSI 지수 기반으로 설정합니다.</li>
        <li>OD 네트워크 데이터를 활용해 <strong>경남 관광 이동 흐름도(관광 OD 히트맵)</strong>를 작성하고, CSI 개선 전략의 지리적 근거 자료로 활용합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 11 — 체류·숙박
══════════════════════════════════════════ -->
<section class="section" id="cell11">
  <div class="section-header sh-navy">
    <span class="section-icon">🏨</span>
    <h2>셀 11 — 체류시간 및 숙박일수 분석</h2>
    <span class="cell-badge">chart_07</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      경남 22개 시군구의 평균 체류시간과 숙박일수를 분석하여 관광객의 체류 패턴을 파악합니다.
      지역 간 편차가 크면 차별화된 체류 전략이 가능하지만, 편차가 작다면 균질한 베이스라인을 개선하는 공통 전략이 필요합니다.
    </p>

    <div class="chart-container">
      {img(7, '체류시간 및 숙박일수 분포 차트')}
      <div class="chart-caption">▲ 그림 6. 경남 시군구별 평균 체류시간(분) 및 평균 숙박일수</div>
    </div>

    <div class="stats-title">📊 주요 수치</div>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">전체 평균 숙박일수</div>
        <div class="stat-value">2.7<span class="stat-unit">일</span></div>
        <div class="stat-sub">모든 시군구 동일 범주</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">체류시간 범위</div>
        <div class="stat-value">20.7<span class="stat-unit">~</span></div>
        <div class="stat-sub">21.3시간 (매우 좁음)</div>
      </div>
      <div class="stat-card green-card">
        <div class="stat-label">체류 등급</div>
        <div class="stat-value" style="font-size:1rem;">일반체류</div>
        <div class="stat-sub">2.6~2.9일 (전 지역)</div>
      </div>
      <div class="stat-card amber-card">
        <div class="stat-label">지역 간 분산</div>
        <div class="stat-value" style="font-size:1rem;">매우 낮음</div>
        <div class="stat-sub">차별화 불가 수준</div>
      </div>
    </div>

    <div class="analysis-box amber">
      <div class="analysis-heading">🔍 분석 해석 — 균질성의 역설</div>
      <p>전 시군구가 2.6~2.9일 숙박, 20.7~21.3시간 체류라는 매우 좁은 범위에 집중되어 있는 것은 얼핏 긍정적으로 보일 수 있습니다. 그러나 이는 <strong>지역 간 관광 콘텐츠의 차별화가 이루어지지 않았음</strong>을 의미하는 "균질성의 역설"로 해석해야 합니다. 방문객들이 어느 지역을 가든 비슷한 시간을 체류하고 비슷한 일수를 숙박한다면, 특정 지역의 콘텐츠가 체류를 연장시키는 유인력을 갖지 못하고 있다는 신호입니다.</p>
      <p style="margin-top:10px;">평균 숙박 2.7일은 1박 2일 혹은 2박 3일 패턴이 혼재하는 것으로, 관광 목적지로서의 체류 연장 가능성을 탐색하려면 더 세분화된 숙박 유형 데이터(펜션·호텔·캠핑 등)가 필요합니다. 현 데이터만으로는 "왜 모든 지역이 비슷한 체류 시간을 기록하는가"라는 근본 질문에 답하기 어려우며, 추가 인터뷰·설문 데이터와의 결합이 필요합니다.</p>
      <p style="margin-top:10px;">이 균질성은 또한 관광 CSI 지수에서 체류·숙박 지표의 <strong>변별력이 낮음</strong>을 의미합니다. 지수 설계 시 이 지표의 가중치를 낮추거나, 체류 연장률(전년 대비 증감)과 같은 변화 기반 지표로 대체하는 것을 고려해야 합니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>체류·숙박 지표는 CSI 지수에서 <strong>가중치를 낮게 설정</strong>(예: 전체 지수의 10% 미만)하고, 대신 변화율(전년 대비 체류 증감)이나 고급숙박 비중 등 보완 지표를 추가합니다.</li>
        <li>"체류 연장형 콘텐츠" 개발 과제를 CSI 개선 과제의 공통 우선순위로 설정하고, 특히 3박 이상 체류를 유도하는 프로그램(체험·공예·교육 등) 개발을 권고합니다.</li>
        <li>향후 데이터 수집 시 숙박 유형별·요일별·계절별 세분화를 요청하여 지역 간 미세 차이를 포착할 수 있는 데이터 체계를 구축합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 12 — 업종별 소비액
══════════════════════════════════════════ -->
<section class="section" id="cell12">
  <div class="section-header sh-indigo">
    <span class="section-icon">💳</span>
    <h2>셀 12 — 업종별 소비액 분석</h2>
    <span class="cell-badge">chart_08</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      경남 관광 소비의 업종별 구성을 분석하여 소비 구조의 집중도와 다양성을 진단합니다.
      어느 업종에 소비가 몰려 있는지, 중분류 수준에서는 어떤 세부 업종이 주도하는지를 파악합니다.
    </p>

    <div class="chart-container">
      {img(8, '업종별 소비액 비중 차트')}
      <div class="chart-caption">▲ 그림 7. 경남 관광 소비액 업종별 구성 (대분류 및 중분류)</div>
    </div>

    <div class="stats-title">📊 주요 수치 — 업종 대분류별 소비 비중</div>
    <table class="data-table">
      <thead>
        <tr><th>업종 대분류</th><th class="num">소비 비중</th><th class="num">소비액 추정</th><th>특성</th></tr>
      </thead>
      <tbody>
        <tr><td><span class="badge badge-blue">쇼핑업</span></td><td class="num"><strong>37.3%</strong></td><td class="num">₩18.7B</td><td>최대 소비 업종</td></tr>
        <tr><td><span class="badge badge-green">식음료업</span></td><td class="num"><strong>29.6%</strong></td><td class="num">₩14.8B</td><td>필수 소비</td></tr>
        <tr><td><span class="badge badge-purple">숙박업</span></td><td class="num"><strong>18.7%</strong></td><td class="num">₩9.4B</td><td>체류형 소비</td></tr>
        <tr><td><span class="badge badge-amber">여가서비스업</span></td><td class="num">4.7%</td><td class="num">—</td><td>체험·레저</td></tr>
        <tr><td><span class="badge badge-teal">의료웰니스업</span></td><td class="num">4.4%</td><td class="num">—</td><td>힐링·의료</td></tr>
        <tr><td><span class="badge badge-gray">운송업</span></td><td class="num">4.3%</td><td class="num">—</td><td>이동 비용</td></tr>
        <tr><td><span class="badge badge-gray">여행업</span></td><td class="num">0.0%</td><td class="num">—</td><td>거의 미발생</td></tr>
      </tbody>
    </table>

    <div class="stats-title" style="margin-top:20px;">📊 중분류 상위 항목</div>
    <div class="highlight-row">
      <div class="hl-chip"><span class="hl-val">26.2%</span><span class="hl-lbl">일반외식업</span></div>
      <div class="hl-chip"><span class="hl-val">22.0%</span><span class="hl-lbl">대형쇼핑몰</span></div>
      <div class="hl-chip"><span class="hl-val">14.3%</span><span class="hl-lbl">기타관광쇼핑</span></div>
    </div>

    <div class="analysis-box">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>경남 관광 소비는 쇼핑업(37.3%)과 식음료업(29.6%)이 전체의 66.9%를 점유하는 <strong>2강 구조</strong>를 보입니다. 이는 관광객들이 경남을 방문할 때 체험·문화·자연 활동보다 쇼핑과 식사를 주된 소비 활동으로 인식하고 있음을 의미합니다. 이는 전국 관광지의 일반적 소비 패턴과 유사하지만, 경남 특유의 콘텐츠 경쟁력을 높이기 위해서는 하위 업종의 성장이 필요합니다.</p>
      <p style="margin-top:10px;">숙박업(18.7%)이 3위를 차지한 것은 경남 관광이 당일 관광보다 숙박 동반 관광의 비중이 높음을 반영합니다. 여행업 소비가 사실상 0%라는 점은 여행사 패키지보다 개인·자유 여행 중심의 방문 패턴이 지배적임을 시사하며, FIT(Free Individual Travel) 타겟 마케팅의 중요성을 강조합니다.</p>
      <p style="margin-top:10px;">중분류 수준에서 일반외식업(26.2%)과 대형쇼핑몰(22.0%)이 1~2위를 차지한 것은 경남 관광 소비의 '일상화' 현상을 나타냅니다. 즉, 관광객들이 특별한 관광 목적보다 일상적 소비 활동(식사·쇼핑)을 위해 방문하는 패턴이 강함을 의미합니다. 이를 넘어서는 체험형·문화형 콘텐츠 발굴이 관광 소비 고도화의 관건입니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>쇼핑·식음료 편중 구조를 탈피하기 위해 CSI 지수에 <strong>소비 다양성 하위지표</strong>(업종 엔트로피 지수)를 포함하고, 여가서비스·의료웰니스 업종 소비 비중 증가를 목표 KPI로 설정합니다.</li>
        <li>대형쇼핑몰·일반외식업 중심 소비가 높은 지역(김해시·창원시 등)에 대해서는 체험·문화 관광 상품 연계를 통한 소비 다변화 전략을 우선 적용합니다.</li>
        <li>여행업 소비 0%는 패키지 관광 상품 부재를 의미하므로, 지역 소상공인과 연계한 경남 특화 패키지 개발을 CSI 개선 과제에 포함합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 13 — HHI 업종 집중도
══════════════════════════════════════════ -->
<section class="section" id="cell13">
  <div class="section-header sh-brown">
    <span class="section-icon">🎯</span>
    <h2>셀 13 — HHI 업종 집중도 분석</h2>
    <span class="cell-badge">chart_09</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      Herfindahl-Hirschman Index(HHI)를 활용하여 각 시군구의 관광 소비 업종 집중도를 측정합니다.
      HHI가 높을수록 소수 업종에 소비가 집중되어 있어 취약성이 크고, 낮을수록 다양한 업종에 걸쳐 소비가 분산되어 있습니다.
    </p>

    <div class="chart-container">
      {img(9, 'HHI 업종 집중도 차트')}
      <div class="chart-caption">▲ 그림 8. 경남 시군구별 HHI(허핀달-허시만 지수) 업종 집중도</div>
    </div>

    <div class="stats-title">📊 주요 수치</div>
    <table class="data-table">
      <thead>
        <tr><th>시군구</th><th class="num">HHI 값</th><th>주도 업종</th><th>등급</th></tr>
      </thead>
      <tbody>
        <tr><td>합천군</td><td class="num"><strong>0.46</strong></td><td>쇼핑업 62%</td><td><span class="badge badge-red">고집중 (0.40+)</span></td></tr>
        <tr><td>김해시</td><td class="num"><strong>0.40</strong></td><td>쇼핑업 59%</td><td><span class="badge badge-red">고집중 (0.40+)</span></td></tr>
        <tr><td>— (중간집중 9개) —</td><td class="num">0.25~0.40</td><td>다양</td><td><span class="badge badge-amber">중간집중</span></td></tr>
        <tr><td>고성군</td><td class="num"><strong>0.22</strong></td><td>분산형</td><td><span class="badge badge-green">분산형 (&lt;0.25)</span></td></tr>
        <tr><td>함안군</td><td class="num"><strong>0.23</strong></td><td>분산형</td><td><span class="badge badge-green">분산형 (&lt;0.25)</span></td></tr>
        <tr><td>창원시 의창구</td><td class="num"><strong>0.24</strong></td><td>분산형</td><td><span class="badge badge-green">분산형 (&lt;0.25)</span></td></tr>
      </tbody>
    </table>

    <div class="highlight-row">
      <div class="hl-chip"><span class="hl-val">2개</span><span class="hl-lbl">고집중 (0.40+)</span></div>
      <div class="hl-chip"><span class="hl-val">9개</span><span class="hl-lbl">중간집중 (0.25~0.40)</span></div>
      <div class="hl-chip"><span class="hl-val">4개</span><span class="hl-lbl">분산형 (&lt;0.25)</span></div>
    </div>

    <div class="analysis-box">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>합천군(HHI=0.46)의 고집중은 관광 소비의 62%가 쇼핑업 단일 업종에 집중되어 있음을 의미합니다. 이는 외부 경제 충격(예: 특정 쇼핑 시설 폐업, 경기 침체로 인한 쇼핑 소비 감소)에 대한 취약성이 높음을 나타냅니다. 김해시 역시 쇼핑업 59%로 유사한 취약 구조를 보이며, 두 지역 모두 소비 다각화가 시급한 과제입니다.</p>
      <p style="margin-top:10px;">흥미로운 점은 유입유출비율 최고 지역인 창원시 의창구가 HHI 최저(0.24, 분산형)를 기록했다는 것입니다. 이는 의창구가 관광 흡인력도 높고 소비 다양성도 높은 <strong>이상적 관광 구조</strong>를 갖추고 있음을 시사합니다. 고성군(0.22)과 함안군(0.23)의 분산형도 주목할 만한데, 이 지역들은 유입 규모는 크지 않지만 방문한 관광객들이 다양한 업종에 걸쳐 소비를 분산시키는 질적으로 균형 잡힌 관광 패턴을 보입니다.</p>
      <p style="margin-top:10px;">전체 22개 지역 중 4개만이 분산형(HHI &lt; 0.25)에 해당하고, 2개 지역이 고집중 상태라는 사실은 경남 전체적으로 소비 다각화가 진행 중이나 아직 불충분한 수준임을 보여줍니다. 여가서비스·문화·의료웰니스 업종 육성을 통해 중간집중 지역들을 분산형으로 전환하는 전략이 필요합니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>HHI를 CSI 지수의 <strong>소비 다양성 하위지표</strong>로 역수(1/HHI) 형태로 통합하여, 분산형 지역이 높은 점수를 받도록 설계합니다.</li>
        <li>합천군·김해시 등 고집중 지역에 대해서는 쇼핑 의존도 감소를 목표로 하는 <strong>관광 다각화 집중 지원 대상</strong>으로 지정하고, 식음료·여가서비스 업종 창업 지원을 연계합니다.</li>
        <li>창원 의창구의 고유입·저HHI 조합을 경남 관광 발전 모델 사례로 활용하고, 유사 구조 달성을 다른 시군구의 벤치마크 목표로 설정합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     셀 14 — 관광취약도 점수
══════════════════════════════════════════ -->
<section class="section" id="cell14">
  <div class="section-header sh-crimson">
    <span class="section-icon">🏆</span>
    <h2>셀 14 — 관광취약도 점수 분석</h2>
    <span class="cell-badge">chart_10</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      유입유출비율, 소비 다양성(HHI 역수), 체류·숙박 등 다중 지표를 복합 산출한 관광취약도 점수(0~100점)를 분석합니다.
      점수가 높을수록 관광 취약성이 높아 정책적 지원이 시급한 지역을 의미합니다.
    </p>

    <div class="chart-container">
      {img(10, '관광취약도 점수 분포 차트')}
      <div class="chart-caption">▲ 그림 9. 경남 시군구별 관광취약도 점수 (0=최강, 100=최취약)</div>
    </div>

    <div class="stats-title">📊 주요 수치 — 관광취약도 점수 상·하위 순위</div>
    <table class="data-table">
      <thead>
        <tr>
          <th>구분</th>
          <th>시군구</th>
          <th class="num">취약도 점수</th>
          <th>주요 취약 요인</th>
        </tr>
      </thead>
      <tbody>
        <tr><td rowspan="5" style="vertical-align:middle;font-weight:700;color:#c62828;">★ 취약 상위<br>(지원 시급)</td>
            <td>사천시</td><td class="num"><strong>59.7</strong></td><td>고유입 but 소비 다양성 부족</td></tr>
        <tr><td>창원시 의창구</td><td class="num"><strong>59.2</strong></td><td>극단적 유입 편중 구조</td></tr>
        <tr><td>창원시 성산구</td><td class="num"><strong>54.9</strong></td><td>MICE 의존, 계절 변동성</td></tr>
        <tr><td>통영시</td><td class="num"><strong>51.1</strong></td><td>관광 시설 노후화 우려</td></tr>
        <tr><td>산청군</td><td class="num"><strong>50.9</strong></td><td>접근성·인프라 부족</td></tr>
        <tr><td rowspan="3" style="vertical-align:middle;font-weight:700;color:#2e7d32;">★ 취약 하위<br>(비교적 안정)</td>
            <td>양산시</td><td class="num"><strong>25.9</strong></td><td>다양한 관광 포트폴리오</td></tr>
        <tr><td>창녕군</td><td class="num"><strong>26.7</strong></td><td>자연·생태 기반 안정형</td></tr>
        <tr><td>고성군</td><td class="num"><strong>27.1</strong></td><td>공룡화석·자연 관광 균형</td></tr>
      </tbody>
    </table>

    <div class="highlight-row">
      <div class="hl-chip"><span class="hl-val">59.7</span><span class="hl-lbl">최고 취약 (사천시)</span></div>
      <div class="hl-chip"><span class="hl-val">25.9</span><span class="hl-lbl">최저 취약 (양산시)</span></div>
      <div class="hl-chip"><span class="hl-val">33.8p</span><span class="hl-lbl">지역 간 격차</span></div>
    </div>

    <div class="analysis-box red">
      <div class="analysis-heading">🔍 분석 해석</div>
      <p>관광취약도 최고 지역인 사천시(59.7점)와 창원시 의창구(59.2점)는 유입유출비율 상위 지역과 상당히 겹칩니다. 이는 역설적으로 <strong>높은 유입 흡인력이 곧 취약성의 원인</strong>이 될 수 있음을 보여줍니다. 즉, 관광에 지나치게 의존하는 지역 경제 구조, 단일 업종 소비 집중, 계절 편중 등이 복합적으로 작용하여 취약도를 높이는 것입니다.</p>
      <p style="margin-top:10px;">통영시(51.1점)의 높은 취약도는 전국적 관광지임에도 불구하고 관광 시설 노후화·체류 콘텐츠 부족 등 구조적 문제가 반영된 결과로 추정됩니다. 반면 양산시(25.9점)·창녕군(26.7점) 등이 비교적 낮은 취약도를 보이는 것은 종합적인 관광 포트폴리오(자연·생태·문화·쇼핑의 균형)와 접근성 덕분으로 분석됩니다.</p>
      <p style="margin-top:10px;">지역 간 점수 범위가 25.9~59.7점(약 34점 차이)이라는 사실은 경남 내에서도 관광 경쟁력의 불균형이 상당하다는 것을 보여줍니다. 정책 수립 시 상위 취약 지역(50점 이상)에 집중 지원을 배분하는 동시에, 하위 안정 지역의 성공 요인을 전파하는 이중 전략이 효과적입니다.</p>
    </div>

    <div class="csi-box">
      <div class="csi-heading">🎯 CSI 프로젝트 활용</div>
      <ul>
        <li>관광취약도 점수를 CSI 지수의 <strong>최종 우선순위 결정 레이어</strong>로 활용하여, 취약도 상위 5개 지역(사천시·창원의창구·성산구·통영시·산청군)을 1순위 정책 지원 대상으로 지정합니다.</li>
        <li>사천시·통영시 등 고유입·고취약 지역에 대해서는 <strong>관광 회복탄력성 전략</strong>(소비 다변화, 비수기 콘텐츠 강화, 다년간 방문 인센티브)을 CSI 개선 계획에 포함합니다.</li>
        <li>양산시·고성군 등 저취약 안정 지역의 성공 요인(업종 다양성, 접근성, 자연 자원 보전)을 분석하여 경남 관광 표준 모델로 정립하고, 유사 자연 자원 보유 지역(남해군·하동군 등)에 적용할 수 있는 <strong>관광 자원 개발 가이드라인</strong>을 작성합니다.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════
     종합 결론
══════════════════════════════════════════ -->
<section class="section" id="conclusion">
  <div class="section-header sh-conclusion">
    <span class="section-icon">📝</span>
    <h2>종합 결론 및 CSI 설계 제언</h2>
    <span class="cell-badge">Overall Insights</span>
  </div>
  <div class="section-body">
    <p class="section-desc">
      Static_Dimension EDA 전체 결과를 종합하여 경남 CSI 지수 설계에 활용할 핵심 인사이트와 구체적 권고 사항을 제시합니다.
    </p>

    <div class="conclusion-grid">
      <div class="conclusion-card">
        <h4>🏅 유입 흡인력 — 강점이자 취약점</h4>
        <p>경남은 전국 평균을 크게 상회하는 유입유출비율을 보유한 강력한 관광 목적지입니다. 그러나 일부 지역의 과도한 관광 의존 구조는 취약도를 높이므로, 관광 주도 성장과 경제 다각화의 균형이 필요합니다.</p>
      </div>
      <div class="conclusion-card green">
        <h4>🌿 소비 다각화 — 가장 시급한 과제</h4>
        <p>쇼핑·식음료 67% 집중 구조와 HHI 고집중 지역 존재는 관광 소비의 질적 다각화가 경남 관광 정책의 최우선 과제임을 시사합니다. 여가서비스·의료웰니스·문화 업종 육성이 핵심 전략입니다.</p>
      </div>
      <div class="conclusion-card amber">
        <h4>🕐 체류 연장 — 미개발 잠재력</h4>
        <p>전 지역 2.7일 숙박의 균질성은 체류 연장 콘텐츠 개발의 여지가 크다는 것을 의미합니다. 3박 이상 유도 상품, 지역 연계 투어, 체험형 프로그램 개발이 관광 소비 총량 증대의 핵심 레버입니다.</p>
      </div>
      <div class="conclusion-card purple">
        <h4>📊 CSI 지수 설계 방향</h4>
        <p>유입유출비율(35%)·소비다양성(25%)·취약도점수(25%)·체류지표(15%)의 복합 가중 구조를 권고합니다. 단, 체류 지표는 절대값보다 전년 대비 변화율을 활용해 변별력을 높여야 합니다.</p>
      </div>
    </div>

    <div class="divider"></div>

    <div class="analysis-box">
      <div class="analysis-heading">📌 우선 조치 사항 (Action Items)</div>
      <ul>
        <li><strong>[즉시]</strong> 데이터 전처리: '함천군' 오타 수정, 소비액 0값 정책 결정, OD 중복 집계 로직 구현</li>
        <li><strong>[단기]</strong> 이상값 47행 별도 분석: 창원의창구·사천시 등 극고값의 실제 의미 검증 및 CSI 가중치 처리 방안 결정</li>
        <li><strong>[단기]</strong> 창원시 통합 CSI 산출 로직: 5개구 데이터를 인구 가중 합산하는 집계 방법론 표준화</li>
        <li><strong>[중기]</strong> 체류 보완 데이터 수집: 숙박 유형별·계절별·요일별 세분화 데이터 확보 계획 수립</li>
        <li><strong>[중기]</strong> 여행업 소비 활성화 방안: 경남 특화 FIT 패키지 개발 및 지역 소상공인 연계 프로그램 기획</li>
        <li><strong>[장기]</strong> 관광취약도 모니터링 체계: 분기별 CSI 지수 업데이트 및 취약 지역 개선도 추적 대시보드 구축</li>
      </ul>
    </div>

    <div class="analysis-box green">
      <div class="analysis-heading">🌟 최종 요약 — 경남 관광의 현재와 미래</div>
      <p>경남은 <strong>강력한 관광 흡인력</strong>(평균 유입유출비율 4.28, 관광특화 지역 5개)을 보유한 동시에, <strong>소비 집중·체류 균질·취약도 편차</strong>라는 구조적 과제를 안고 있습니다. Static_Dimension EDA는 이 모순을 정량적으로 포착하여 경남 CSI 지수 설계의 탄탄한 데이터 기반을 제공합니다. 유입 흡인력을 지렛대로 삼아 소비 다각화와 체류 연장을 동시에 달성하는 <strong>"고유입·고분산·장체류"</strong> 전략이 경남 관광 경쟁력의 미래 방향입니다.</p>
    </div>
  </div>
</section>

</div><!-- .page-wrap -->

<footer class="report-footer">
  <p>경남 CSI 인턴십 2026 · Static_Dimension EDA 분석 리포트 · 생성일: 2026년 5월 28일</p>
  <p style="margin-top:4px;">본 리포트는 EDA 결과를 기반으로 작성된 내부 분석 문서입니다. 공식 발행 전 담당자 검토가 필요합니다.</p>
</footer>

</body>
</html>"""

with open('/home/user/fintech-internship-2026/경남_CSI_Static_Dimension_분석리포트.html', 'w', encoding='utf-8') as f:
    f.write(html)

size_bytes = len(html.encode('utf-8'))
print(f'Report written successfully.')
print(f'HTML size: {len(html):,} characters')
print(f'File size: {size_bytes:,} bytes ({size_bytes/1024/1024:.2f} MB)')
