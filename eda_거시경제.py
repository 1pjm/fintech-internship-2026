# ============================================================
# 경남 상권 생존지수(CSI) — 거시경제_1 EDA
# Google Colab 전용 노트북 코드
# ============================================================


# ┌─────────────────────────────────────────────────────────┐
# │  셀 1 │ 라이브러리 설치                                  │
# └─────────────────────────────────────────────────────────┘
# !pip install -q pandas matplotlib seaborn plotly kaleido


# ┌─────────────────────────────────────────────────────────┐
# │  셀 2 │ 임포트 & 시각화 스타일 설정                       │
# └─────────────────────────────────────────────────────────┘
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정 (Colab)
import subprocess
subprocess.run(['apt-get', 'install', '-y', 'fonts-nanum'], capture_output=True)
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120
plt.rcParams['figure.figsize'] = (12, 6)

print("✅ 라이브러리 로드 완료")


# ┌─────────────────────────────────────────────────────────┐
# │  셀 3 │ 파일 업로드 & 데이터 로드                         │
# └─────────────────────────────────────────────────────────┘
from google.colab import files

print("📂 파일을 업로드하세요 (거시경제_1 CSV 파일)")
uploaded = files.upload()
filename = list(uploaded.keys())[0]

df_raw = pd.read_csv(filename, low_memory=False)
df_raw['연월'] = pd.to_datetime(df_raw['연월'])

print(f"✅ 로드 완료 | {df_raw.shape[0]:,}행 × {df_raw.shape[1]}열")
df_raw.head(3)


# ┌─────────────────────────────────────────────────────────┐
# │  셀 4 │ 기본 구조 확인 (shape / dtypes / 결측 요약)       │
# └─────────────────────────────────────────────────────────┘
print("=" * 55)
print("▶ 기본 정보")
print("=" * 55)
print(f"  행 수       : {df_raw.shape[0]:,}")
print(f"  열 수       : {df_raw.shape[1]}")
print(f"  시군구명 수  : {df_raw['시군구명'].nunique()}개")
print(f"  연월 범위    : {df_raw['연월'].min().date()} ~ {df_raw['연월'].max().date()}")
print()

print("▶ 컬럼별 결측 현황")
null_df = pd.DataFrame({
    '결측 수': df_raw.isnull().sum(),
    '결측률(%)': (df_raw.isnull().sum() / len(df_raw) * 100).round(1)
})
print(null_df[null_df['결측 수'] > 0].to_string())
print()

print("▶ 수치 컬럼 기술통계")
display(df_raw.describe().T.round(2))


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 5 │ [데이터 품질-1] 지표별 측정 주기 불일치 시각화                │
# └─────────────────────────────────────────────────────────────────────┘
# ── 각 지표별 데이터가 존재하는 연월 집합 추출
metrics = {
    '인구수':       df_raw[df_raw['인구수'].notna()]['연월'],
    '고용률':       df_raw[df_raw['고용률'].notna()]['연월'],
    '실업률':       df_raw[df_raw['실업률'].notna()]['연월'],
    'GRDP':        df_raw[df_raw['GRDP'].notna()]['연월'],
    '순방문자수':   df_raw[df_raw['순방문자수'].notna()]['연월'],
    '숙박자비율':   df_raw[df_raw['숙박자비율'].notna()]['연월'],
    '방문자수증감률': df_raw[df_raw['방문자수증감률'].notna()]['연월'],
    '평균숙박일수': df_raw[df_raw['평균숙박일수'].notna()]['연월'],
}

# ── 타임라인 Gantt 형태로 시각화
fig, ax = plt.subplots(figsize=(14, 5))
colors = {'인구수': '#4C72B0', '고용률': '#DD8452', '실업률': '#55A868',
          'GRDP': '#C44E52', '순방문자수': '#8172B2', '숙박자비율': '#937860',
          '방문자수증감률': '#DA8BC3', '평균숙박일수': '#8C8C8C'}

y_positions = {}
for i, (metric, dates) in enumerate(metrics.items()):
    unique_dates = sorted(dates.unique())
    y_positions[metric] = i
    ax.scatter(unique_dates, [i] * len(unique_dates),
               color=colors[metric], s=80, zorder=5, label=metric)
    # 점선으로 연결
    ax.plot(unique_dates, [i] * len(unique_dates),
            color=colors[metric], alpha=0.3, linewidth=1.5)

ax.set_yticks(range(len(metrics)))
ax.set_yticklabels(metrics.keys(), fontsize=11)
ax.set_xlabel('연월', fontsize=11)
ax.set_title('지표별 측정 시점 분포 — 측정 주기가 각각 다름\n(인구수:분기 | 고용률·실업률:반기 | GRDP:연간 | 관광지표:월별)',
             fontsize=13, fontweight='bold', pad=12)
ax.grid(axis='x', alpha=0.3)
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y.%m'))
ax.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(bymonth=[1, 7]))
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# ── 측정 주기 요약 텍스트
print("\n📋 측정 주기 요약")
print("-" * 50)
freq_summary = {
    '인구수':       '분기 (3·6·9·12월) — 2024년만',
    '고용률·실업률': '반기 (1·7월) — 2023~2025',
    'GRDP':        '연간 (1월) — 2020~2022',
    '관광지표':    '월별 — 2023.01~2024.12',
}
for k, v in freq_summary.items():
    print(f"  {k:<12}: {v}")

print("\n⚠️  CSI 통합 시 유의사항")
print("  - 관측 시점이 다른 지표는 직접 결합 불가")
print("  - 고용률·GRDP는 가장 최근값(latest)으로 단면 조인 권장")
print("  - 인구수의 실제 단위 확인 필요 (생활인구·체류인구 가능성)")


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 6 │ [데이터 품질-2] 시군구별 × 지표별 커버리지 매트릭스           │
# └─────────────────────────────────────────────────────────────────────┘
# ── 시군구명 정규화 (prefix '경상남도 ' 제거)
df_raw['시군구_clean'] = df_raw['시군구명'].str.replace(r'^경상남도\s*', '', regex=True).str.strip()

# ── 지표별 데이터 보유 여부 집계
indicator_cols = ['인구수', '고용률', '실업률', 'GRDP', '순방문자수', '숙박자비율', '방문자수증감률', '평균숙박일수']
coverage = {}
for col in indicator_cols:
    sub = df_raw[df_raw[col].notna()].groupby('시군구_clean')[col].count()
    coverage[col] = sub

coverage_df = pd.DataFrame(coverage).fillna(0).astype(int)
coverage_df = coverage_df.sort_index()

# ── 히트맵 시각화
fig, ax = plt.subplots(figsize=(14, 10))

# 값이 0이면 회색, 있으면 파란 계열
cmap = sns.color_palette("Blues", as_cmap=True)
mask = coverage_df == 0  # 0인 셀은 따로 표시

sns.heatmap(coverage_df, ax=ax, cmap=cmap, mask=mask,
            linewidths=0.5, linecolor='#ddd',
            cbar_kws={'label': '데이터 보유 행 수', 'shrink': 0.6},
            annot=True, fmt='d', annot_kws={'size': 9})

# 0인 셀 → 회색 표시
for i in range(coverage_df.shape[0]):
    for j in range(coverage_df.shape[1]):
        if coverage_df.iloc[i, j] == 0:
            ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=True, color='#f0f0f0', lw=0))
            ax.text(j + 0.5, i + 0.5, '✗', ha='center', va='center',
                    color='#aaa', fontsize=10)

ax.set_title('시군구별 × 지표별 데이터 커버리지 매트릭스\n(숫자 = 보유 데이터 행 수, ✗ = 데이터 없음)',
             fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel('지표', fontsize=11)
ax.set_ylabel('시군구', fontsize=11)
ax.tick_params(axis='x', rotation=30)
ax.tick_params(axis='y', labelsize=9)
plt.tight_layout()
plt.show()

# ── 결측 시군구 경고 출력
all_cities = coverage_df.index.tolist()
for col in indicator_cols:
    missing = coverage_df[coverage_df[col] == 0].index.tolist()
    if missing:
        print(f"⚠️  [{col}] 데이터 없는 시군구 ({len(missing)}개): {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}")


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 7 │ 전처리 — 시군구명 패턴별 서브테이블 분리                      │
# └─────────────────────────────────────────────────────────────────────┘
# ── 패턴 1: prefix 없는 행 → 인구수 / 고용률 / 실업률
df_socio = df_raw[~df_raw['시군구명'].str.startswith('경상남도')].copy()
df_socio['시군구_clean'] = df_socio['시군구_clean'].str.strip()

# ── 패턴 2: '경상남도' prefix 있는 행 → GRDP / 관광지표
df_econ = df_raw[df_raw['시군구명'].str.startswith('경상남도')].copy()
df_econ['시군구_clean'] = df_econ['시군구_clean'].str.strip()

# ── 관광지표 전용 (순방문자수 있는 행)
df_tour = df_econ[df_econ['순방문자수'].notna()].copy()

# ── GRDP 전용 (GRDP 있는 행)
df_grdp = df_econ[df_econ['GRDP'].notna()].copy()

print("✅ 서브테이블 분리 완료")
print(f"  df_socio  (인구·고용·실업): {df_socio.shape[0]}행, {df_socio['시군구_clean'].nunique()}개 시군구")
print(f"  df_grdp   (GRDP 연간)    : {df_grdp.shape[0]}행, {df_grdp['시군구_clean'].nunique()}개 시군구")
print(f"  df_tour   (관광 월별)    : {df_tour.shape[0]}행, {df_tour['시군구_clean'].nunique()}개 시군구")


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 8 │ [인구 분석] 시군구별 인구 감소율 계산                         │
# └─────────────────────────────────────────────────────────────────────┘
# 인구수 데이터: 2024년 분기(3·6·9·12월)
df_pop = df_socio[df_socio['인구수'].notna()][['시군구_clean', '연월', '인구수']].copy()
df_pop = df_pop.sort_values(['시군구_clean', '연월'])

# ── 1분기 대비 4분기 변화율 (2024 내 변화)
pop_pivot = df_pop.pivot(index='시군구_clean', columns='연월', values='인구수')
pop_pivot.columns = [c.strftime('%Y.%m') for c in pop_pivot.columns]

# 첫 분기 vs 마지막 분기
first_col = pop_pivot.columns[0]
last_col  = pop_pivot.columns[-1]
pop_pivot['변화율(%)'] = ((pop_pivot[last_col] - pop_pivot[first_col]) / pop_pivot[first_col] * 100).round(2)
pop_pivot = pop_pivot.sort_values('변화율(%)')

print("📊 2024년 분기별 인구 변화율 (3월 → 12월 기준)")
print(pop_pivot[['변화율(%)']].to_string())

# ── 시각화 1: 시군구별 인구 변화율 수평 막대
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# 막대 색상: 감소(빨강) / 증가(파랑)
bar_colors = ['#e74c3c' if v < 0 else '#2980b9' for v in pop_pivot['변화율(%)']]
axes[0].barh(pop_pivot.index, pop_pivot['변화율(%)'], color=bar_colors, edgecolor='white')
axes[0].axvline(0, color='black', linewidth=0.8, linestyle='--')
axes[0].set_xlabel('변화율 (%)', fontsize=11)
axes[0].set_title('시군구별 생활인구 변화율\n(2024년 1분기→4분기)', fontsize=12, fontweight='bold')
axes[0].tick_params(axis='y', labelsize=9)
for i, (v, name) in enumerate(zip(pop_pivot['변화율(%)'], pop_pivot.index)):
    axes[0].text(v + (0.05 if v >= 0 else -0.05), i,
                 f'{v:+.1f}%', va='center', ha=('left' if v >= 0 else 'right'), fontsize=8)

# 시각화 2: 분기별 추이 (상위 5개 + 하위 5개 시군구)
top5    = pop_pivot.nlargest(5, '변화율(%)')
bottom5 = pop_pivot.nsmallest(5, '변화율(%)')
highlight = pd.concat([top5, bottom5])

for city in highlight.index:
    subset = df_pop[df_pop['시군구_clean'] == city]
    color  = '#e74c3c' if pop_pivot.loc[city, '변화율(%)'] < 0 else '#2980b9'
    axes[1].plot(subset['연월'], subset['인구수'] / 1e6,
                 marker='o', label=city, linewidth=2, color=color)

axes[1].set_title('분기별 생활인구 추이\n(변화율 상위5·하위5 시군구)', fontsize=12, fontweight='bold')
axes[1].set_xlabel('연월', fontsize=11)
axes[1].set_ylabel('생활인구 (백만 단위)', fontsize=11)
axes[1].legend(fontsize=8, ncol=2)
axes[1].xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y.%m'))
plt.xticks(rotation=30)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.show()

print("\n⚠️  주의: 인구수 컬럼은 실제 주민등록 인구가 아닌 통신 기반 생활인구(추정 월간 체류량)일 가능성")
print("     → 절대값보다 시군구별 상대 변화율·추세 비교에 활용 권장")


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 9 │ [경제 지표] 고용률·실업률 시군구별 비교                        │
# └─────────────────────────────────────────────────────────────────────┘
df_emp = df_socio[df_socio['고용률'].notna()][['시군구_clean', '연월', '고용률', '실업률']].copy()
df_emp = df_emp.sort_values(['시군구_clean', '연월'])

# ── 최신 시점(2025-07) 단면 데이터
latest_emp = df_emp[df_emp['연월'] == df_emp['연월'].max()].copy()
latest_emp = latest_emp.sort_values('고용률', ascending=False)

# ── 경남 평균 (가능한 경우)
emp_mean    = df_emp.groupby('연월')[['고용률', '실업률']].mean().reset_index()

# ── 시각화 1: 최신 시점 시군구별 고용률·실업률 버블 차트
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 버블 차트 (x=고용률, y=실업률, size=없음)
scatter = axes[0].scatter(latest_emp['고용률'], latest_emp['실업률'],
                          s=120, alpha=0.8, c=latest_emp['고용률'],
                          cmap='RdYlGn', edgecolors='gray', linewidth=0.5)
plt.colorbar(scatter, ax=axes[0], label='고용률(%)')
for _, row in latest_emp.iterrows():
    axes[0].annotate(row['시군구_clean'],
                     (row['고용률'], row['실업률']),
                     fontsize=7.5, xytext=(3, 3), textcoords='offset points')
axes[0].axvline(latest_emp['고용률'].mean(), color='gray', linestyle='--', alpha=0.5,
                label=f"평균 고용률 {latest_emp['고용률'].mean():.1f}%")
axes[0].axhline(latest_emp['실업률'].mean(), color='gray', linestyle=':', alpha=0.5,
                label=f"평균 실업률 {latest_emp['실업률'].mean():.1f}%")
axes[0].set_xlabel('고용률 (%)', fontsize=11)
axes[0].set_ylabel('실업률 (%)', fontsize=11)
axes[0].set_title(f'고용률 vs 실업률 (최신: {df_emp["연월"].max().strftime("%Y.%m")})',
                  fontsize=12, fontweight='bold')
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

# 시계열: 반기별 경남 평균 고용률 추이
ax2 = axes[1].twinx()
axes[1].bar(emp_mean['연월'], emp_mean['고용률'],
            color='#2980b9', alpha=0.6, label='평균 고용률', width=80)
ax2.plot(emp_mean['연월'], emp_mean['실업률'],
         color='#e74c3c', marker='o', linewidth=2, label='평균 실업률')
axes[1].set_xlabel('연월', fontsize=11)
axes[1].set_ylabel('고용률 (%)', fontsize=11, color='#2980b9')
ax2.set_ylabel('실업률 (%)', fontsize=11, color='#e74c3c')
axes[1].set_title('경남 평균 고용률·실업률 반기별 추이', fontsize=12, fontweight='bold')
axes[1].xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y.%m'))
lines1, labels1 = axes[1].get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
axes[1].legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc='upper left')
axes[1].grid(alpha=0.3)
plt.xticks(rotation=30)

plt.tight_layout()
plt.show()

# ── 시각화 2: 시군구별 고용률 반기 추이 히트맵
emp_pivot = df_emp.pivot_table(index='시군구_clean', columns='연월', values='고용률')
emp_pivot.columns = [c.strftime('%Y.%m') for c in emp_pivot.columns]

fig, ax = plt.subplots(figsize=(14, 9))
sns.heatmap(emp_pivot, ax=ax, cmap='RdYlGn', annot=True, fmt='.1f',
            annot_kws={'size': 9}, linewidths=0.3, linecolor='#eee',
            cbar_kws={'label': '고용률(%)', 'shrink': 0.6})
ax.set_title('시군구별 × 반기별 고용률 히트맵\n(녹색=높음, 빨강=낮음)',
             fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel('연월', fontsize=11)
ax.set_ylabel('')
ax.tick_params(axis='y', labelsize=9)
plt.tight_layout()
plt.show()

# ── 통계 요약
print("\n📊 최신 시점 고용률 순위 (상위 5 / 하위 5)")
print("상위 5:", latest_emp.nlargest(5, '고용률')[['시군구_clean', '고용률', '실업률']].to_string(index=False))
print()
print("하위 5:", latest_emp.nsmallest(5, '고용률')[['시군구_clean', '고용률', '실업률']].to_string(index=False))


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 10 │ [경제 지표] GRDP 성장률 추이 (2020 ~ 2022)                  │
# └─────────────────────────────────────────────────────────────────────┘
df_g = df_grdp[['시군구_clean', '연월', 'GRDP']].copy()
df_g['연도'] = df_g['연월'].dt.year
df_g = df_g.sort_values(['시군구_clean', '연도'])

# ── 연도별 성장률 계산
df_g['GRDP_전년'] = df_g.groupby('시군구_clean')['GRDP'].shift(1)
df_g['GRDP_성장률(%)'] = ((df_g['GRDP'] - df_g['GRDP_전년']) / df_g['GRDP_전년'] * 100).round(2)

# ── 시각화 1: GRDP 절대값 (억원 단위, 1억 = 100000000)
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 시군구별 GRDP 추이 (상위 6개)
top_cities = df_g.groupby('시군구_clean')['GRDP'].max().nlargest(6).index
for city in top_cities:
    sub = df_g[df_g['시군구_clean'] == city]
    axes[0].plot(sub['연도'], sub['GRDP'] / 1e8, marker='o', linewidth=2, label=city)

axes[0].set_title('주요 시군구 GRDP 추이 (상위 6개)\n(단위: 억원)', fontsize=12, fontweight='bold')
axes[0].set_xlabel('연도', fontsize=11)
axes[0].set_ylabel('GRDP (억원)', fontsize=11)
axes[0].legend(fontsize=9)
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
axes[0].grid(alpha=0.3)
axes[0].set_xticks([2020, 2021, 2022])

# 시각화 2: GRDP 성장률 히트맵
grdp_growth = df_g[df_g['GRDP_성장률(%)'].notna()].pivot_table(
    index='시군구_clean', columns='연도', values='GRDP_성장률(%)')
grdp_growth.columns = [str(c) for c in grdp_growth.columns]

sns.heatmap(grdp_growth, ax=axes[1], cmap='RdYlGn', center=0,
            annot=True, fmt='.1f', annot_kws={'size': 9},
            linewidths=0.3, linecolor='#eee',
            cbar_kws={'label': 'GRDP 성장률(%)', 'shrink': 0.6})
axes[1].set_title('시군구별 GRDP 성장률 히트맵\n(전년 대비 %, 녹색=성장, 빨강=역성장)',
                  fontsize=12, fontweight='bold')
axes[1].set_xlabel('연도', fontsize=11)
axes[1].tick_params(axis='y', labelsize=9)

plt.tight_layout()
plt.show()

# ── 요약 통계
print("\n📊 2020→2022 GRDP 성장 vs 역성장 시군구")
grdp_2yr = df_g.groupby('시군구_clean').apply(
    lambda x: (x.iloc[-1]['GRDP'] - x.iloc[0]['GRDP']) / x.iloc[0]['GRDP'] * 100
    if len(x) >= 2 else np.nan
).rename('2년_누적성장률(%)').reset_index().dropna()
grdp_2yr = grdp_2yr.sort_values('2년_누적성장률(%)', ascending=False)
print(grdp_2yr.to_string(index=False))


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 11 │ [통합] 인구·고용·GRDP 다지표 순위표 & 상관관계              │
# └─────────────────────────────────────────────────────────────────────┘
# ── 각 지표의 최신 단면값으로 통합 테이블 생성
# 1) 인구 변화율 (2024년 1분기→4분기)
pop_change = pop_pivot[['변화율(%)']].reset_index()
pop_change.columns = ['시군구_clean', '인구변화율(%)']

# 2) 최신 고용률·실업률
emp_latest = df_emp[df_emp['연월'] == df_emp['연월'].max()][['시군구_clean', '고용률', '실업률']]

# 3) 최신 GRDP 성장률 (2021→2022)
grdp_latest = df_g[df_g['연도'] == 2022][['시군구_clean', 'GRDP', 'GRDP_성장률(%)']]

# ── 통합
summary = emp_latest.merge(grdp_latest, on='시군구_clean', how='outer')
summary = summary.merge(pop_change, on='시군구_clean', how='outer')
summary = summary.sort_values('고용률', ascending=False).reset_index(drop=True)
summary.index += 1  # 1부터 시작

print("📊 시군구별 다지표 종합 현황")
display(summary.style
        .background_gradient(subset=['고용률'], cmap='RdYlGn')
        .background_gradient(subset=['실업률'], cmap='RdYlGn_r')
        .background_gradient(subset=['GRDP_성장률(%)'], cmap='RdYlGn', vmin=-5, vmax=10)
        .background_gradient(subset=['인구변화율(%)'], cmap='RdYlGn')
        .format({'고용률': '{:.1f}%', '실업률': '{:.1f}%',
                 'GRDP_성장률(%)': '{:+.1f}%', '인구변화율(%)': '{:+.2f}%',
                 'GRDP': '{:,.0f}'})
        .set_caption('경남 시군구별 거시경제 지표 통합 현황'))

# ── 상관관계 히트맵
numeric_cols = ['고용률', '실업률', 'GRDP_성장률(%)', '인구변화율(%)']
corr_df = summary[numeric_cols].dropna()

if len(corr_df) > 3:
    corr_matrix = corr_df.corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, ax=ax, mask=mask, cmap='coolwarm', center=0,
                annot=True, fmt='.2f', annot_kws={'size': 12},
                square=True, linewidths=0.5,
                cbar_kws={'label': '피어슨 상관계수'})
    ax.set_title('인구·고용·GRDP 지표 간 상관관계\n(하삼각 행렬)',
                 fontsize=13, fontweight='bold', pad=12)
    plt.tight_layout()
    plt.show()
else:
    print("⚠️  공통 시군구 데이터 부족으로 상관관계 계산 불가")


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 12 │ [관광 분석] 순방문자수 추이 & 계절성 패턴                    │
# └─────────────────────────────────────────────────────────────────────┘
df_v = df_tour[['시군구_clean', '연월', '순방문자수']].dropna().copy()
df_v = df_v.sort_values(['시군구_clean', '연월'])
df_v['월'] = df_v['연월'].dt.month
df_v['연도'] = df_v['연월'].dt.year

# ── 시각화 1: 시군구별 월별 순방문자수 추이 (상위 8)
top8 = df_v.groupby('시군구_clean')['순방문자수'].sum().nlargest(8).index

fig, axes = plt.subplots(2, 4, figsize=(18, 9), sharey=False)
axes = axes.flatten()

for i, city in enumerate(top8):
    sub = df_v[df_v['시군구_clean'] == city]
    for year, grp in sub.groupby('연도'):
        axes[i].plot(grp['월'], grp['순방문자수'] / 1e4,
                     marker='o', linewidth=2, label=str(year))
    axes[i].set_title(city, fontsize=11, fontweight='bold')
    axes[i].set_xlabel('월', fontsize=9)
    axes[i].set_ylabel('방문자(만명)', fontsize=9)
    axes[i].set_xticks(range(1, 13))
    axes[i].legend(fontsize=8)
    axes[i].grid(alpha=0.3)

plt.suptitle('시군구별 월별 순방문자수 추이 (상위 8개, 2023 vs 2024)',
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()

# ── 시각화 2: 계절성 분석 — 전체 경남 월별 평균 방문자수
monthly_avg = df_v.groupby(['연도', '월'])['순방문자수'].sum().reset_index()

fig, ax = plt.subplots(figsize=(13, 5))
for year, grp in monthly_avg.groupby('연도'):
    ax.plot(grp['월'], grp['순방문자수'] / 1e6,
            marker='o', linewidth=2.5, label=str(year))
ax.set_title('경남 전체 순방문자수 월별 계절성 패턴 (연도 비교)',
             fontsize=13, fontweight='bold')
ax.set_xlabel('월', fontsize=11)
ax.set_ylabel('순방문자수 합계 (백만명)', fontsize=11)
ax.set_xticks(range(1, 13))
ax.set_xticklabels(['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'])
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ── 성수기 지수: 각 시군구별 피크월 확인
peak_month = df_v.groupby('시군구_clean').apply(
    lambda x: x.groupby('월')['순방문자수'].mean().idxmax()
).rename('피크월').reset_index()
peak_month['피크월_이름'] = peak_month['피크월'].map(
    {1:'1월',2:'2월',3:'3월',4:'4월',5:'5월',6:'6월',
     7:'7월',8:'8월',9:'9월',10:'10월',11:'11월',12:'12월'})

print("\n📊 시군구별 관광 피크월")
print(peak_month[['시군구_clean', '피크월_이름']].to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 4))
peak_month['피크월'].value_counts().sort_index().plot.bar(ax=ax, color='#2980b9', alpha=0.8)
ax.set_title('피크월 분포 (몇 개 시군구가 같은 달에 피크를 맞는가)', fontsize=12, fontweight='bold')
ax.set_xlabel('월', fontsize=11)
ax.set_ylabel('시군구 수', fontsize=11)
ax.set_xticklabels([f'{m}월' for m in range(1, 13)], rotation=0)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 13 │ [관광 분석] 방문자수 증감률 분석                             │
# └─────────────────────────────────────────────────────────────────────┘
df_chg = df_tour[['시군구_clean', '연월', '방문자수증감률']].dropna().copy()
df_chg = df_chg.sort_values(['시군구_clean', '연월'])
df_chg['연도'] = df_chg['연월'].dt.year
df_chg['월'] = df_chg['연월'].dt.month

# ── 시각화 1: 시군구별 연평균 증감률 (2023 vs 2024)
annual_chg = df_chg.groupby(['시군구_clean', '연도'])['방문자수증감률'].mean().reset_index()
annual_pivot = annual_chg.pivot(index='시군구_clean', columns='연도', values='방문자수증감률')
annual_pivot.columns = [str(c) for c in annual_pivot.columns]
annual_pivot = annual_pivot.sort_values(annual_pivot.columns[-1], ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 그룹 막대 차트
x = np.arange(len(annual_pivot))
width = 0.4
cols = annual_pivot.columns.tolist()
bar_palette = ['#2980b9', '#e67e22']

for i, (col, color) in enumerate(zip(cols, bar_palette)):
    vals = annual_pivot[col].fillna(0)
    bars = axes[0].bar(x + i * width - width / 2, vals, width,
                       label=f'{col}년', color=color, alpha=0.8)

axes[0].axhline(0, color='black', linewidth=0.8, linestyle='--')
axes[0].set_xticks(x)
axes[0].set_xticklabels(annual_pivot.index, rotation=45, ha='right', fontsize=8.5)
axes[0].set_ylabel('평균 증감률 (%)', fontsize=11)
axes[0].set_title('시군구별 연평균 방문자수 증감률 비교\n(전년 동월 대비)',
                  fontsize=12, fontweight='bold')
axes[0].legend(fontsize=10)
axes[0].grid(axis='y', alpha=0.3)

# 회복 vs 둔화 분류 (2024년 기준)
if '2024' in annual_pivot.columns:
    categories = []
    for city in annual_pivot.index:
        val_2024 = annual_pivot.loc[city, '2024'] if '2024' in annual_pivot.columns else np.nan
        val_2023 = annual_pivot.loc[city, '2023'] if '2023' in annual_pivot.columns else np.nan
        if pd.isna(val_2024):
            categories.append('데이터없음')
        elif val_2024 > 5:
            categories.append('성장 (>5%)')
        elif val_2024 > 0:
            categories.append('소폭성장 (0~5%)')
        elif val_2024 > -5:
            categories.append('소폭감소 (-5~0%)')
        else:
            categories.append('감소 (<-5%)')

    cat_counts = pd.Series(categories).value_counts()
    cat_palette = {'성장 (>5%)': '#27ae60', '소폭성장 (0~5%)': '#82e0aa',
                   '소폭감소 (-5~0%)': '#f1948a', '감소 (<-5%)': '#e74c3c', '데이터없음': '#bdc3c7'}
    colors_list = [cat_palette.get(c, '#999') for c in cat_counts.index]
    axes[1].pie(cat_counts.values, labels=cat_counts.index,
                colors=colors_list, autopct='%1.0f%%', startangle=90,
                textprops={'fontsize': 10})
    axes[1].set_title('2024년 방문자수 증감률 구간 분포\n(시군구 비율)', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.show()

# ── 시각화 2: 월별 증감률 분포 (박스플롯)
fig, ax = plt.subplots(figsize=(13, 5))
monthly_data = [df_chg[df_chg['월'] == m]['방문자수증감률'].dropna().values
                for m in range(1, 13)]
bp = ax.boxplot(monthly_data, patch_artist=True,
                medianprops={'color': 'black', 'linewidth': 1.5})
colors_box = plt.cm.RdYlGn(np.linspace(0.2, 0.9, 12))
for patch, color in zip(bp['boxes'], colors_box):
    patch.set_facecolor(color)
ax.axhline(0, color='red', linestyle='--', alpha=0.6, linewidth=1)
ax.set_xticklabels([f'{m}월' for m in range(1, 13)], fontsize=10)
ax.set_ylabel('방문자수 증감률 (%)', fontsize=11)
ax.set_title('월별 방문자수 증감률 분포 (전 시군구 기준)\n박스=IQR, 수염=1.5*IQR',
             fontsize=12, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()

print("\n📊 2024년 방문자 증감률 기준 상위/하위 시군구")
if '2024' in annual_pivot.columns:
    print("↑ 증가 상위 5:", annual_pivot['2024'].nlargest(5).round(1).to_string())
    print()
    print("↓ 감소 하위 5:", annual_pivot['2024'].nsmallest(5).round(1).to_string())


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 14 │ [관광 분석] 숙박자비율로 관광 유형 분류                       │
# └─────────────────────────────────────────────────────────────────────┘
df_stay = df_tour[['시군구_clean', '연월', '숙박자비율', '평균숙박일수', '순방문자수']].dropna(
    subset=['숙박자비율']).copy()

# ── 시군구별 평균 숙박자비율
stay_avg = df_stay.groupby('시군구_clean').agg(
    평균_숙박자비율=('숙박자비율', 'mean'),
    평균_숙박일수=('평균숙박일수', 'mean'),
    평균_순방문자수=('순방문자수', 'mean')
).round(2).reset_index()

# ── 유형 분류 기준 (숙박자비율 기준)
stay_avg['관광유형'] = pd.cut(
    stay_avg['평균_숙박자비율'],
    bins=[0, 10, 20, 100],
    labels=['당일형 (0~10%)', '혼합형 (10~20%)', '체류형 (20%+)']
)

print("📊 시군구별 관광 유형 분류")
print(stay_avg.sort_values('평균_숙박자비율', ascending=False).to_string(index=False))

# ── 시각화 1: 숙박자비율 × 평균숙박일수 산점도
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

type_colors = {'당일형 (0~10%)': '#3498db', '혼합형 (10~20%)': '#f39c12', '체류형 (20%+)': '#e74c3c'}
for t, grp in stay_avg.groupby('관광유형', observed=True):
    axes[0].scatter(grp['평균_숙박자비율'], grp['평균_숙박일수'],
                    s=grp['평균_순방문자수'] / 2e4,   # 버블 크기 = 방문자수
                    color=type_colors[t], alpha=0.7, label=t, edgecolors='gray', linewidth=0.5)
    for _, row in grp.iterrows():
        axes[0].annotate(row['시군구_clean'],
                         (row['평균_숙박자비율'], row['평균_숙박일수']),
                         fontsize=8, xytext=(3, 3), textcoords='offset points')

axes[0].set_xlabel('평균 숙박자비율 (%)', fontsize=11)
axes[0].set_ylabel('평균 숙박일수 (일)', fontsize=11)
axes[0].set_title('관광 유형 분류\n(버블 크기 = 순방문자수)',
                  fontsize=12, fontweight='bold')
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

# 시각화 2: 시군구별 숙박자비율 시계열 변화 (2023 vs 2024 월별)
city_order = stay_avg.sort_values('평균_숙박자비율', ascending=False)['시군구_clean'].tolist()
stay_pivot = df_stay.pivot_table(index='시군구_clean', columns='연월', values='숙박자비율')
stay_pivot = stay_pivot.reindex(city_order)
stay_pivot.columns = [c.strftime('%y.%m') for c in stay_pivot.columns]

sns.heatmap(stay_pivot, ax=axes[1], cmap='YlOrRd',
            annot=False, linewidths=0.2, linecolor='#eee',
            cbar_kws={'label': '숙박자비율(%)', 'shrink': 0.6})
axes[1].set_title('시군구별 숙박자비율 월별 변화\n(짙을수록 체류형 관광객 비중 높음)',
                  fontsize=12, fontweight='bold')
axes[1].set_xlabel('연월', fontsize=11)
axes[1].tick_params(axis='y', labelsize=9)
axes[1].tick_params(axis='x', rotation=45, labelsize=8)

plt.tight_layout()
plt.show()

# ── 유형별 요약
type_summary = stay_avg.groupby('관광유형', observed=True).agg(
    시군구수=('시군구_clean', 'count'),
    평균숙박자비율=('평균_숙박자비율', 'mean'),
    평균방문자수=('평균_순방문자수', 'mean'),
    대표시군구=('시군구_clean', lambda x: ', '.join(x.head(3)))
).round(1)

print("\n📊 관광 유형별 요약")
display(type_summary)

print("\n🔑 CSI 활용 인사이트")
print("  체류형 관광지(숙박자비율 20%+) → 숙박/관광업 의존도 높아 외부 충격에 취약")
print("  당일형 관광지(숙박자비율 10% 미만) → 유동인구 의존, 소비 단가 낮음")
print("  → CSI '업종 집중도' 지표 산출 시 관광 유형별 가중치 차등 적용 고려")
