# ============================================================
# 경남 상권 생존지수(CSI) — Static_Dimension EDA
# Google Colab 전용 노트북 코드
# ============================================================


# ┌─────────────────────────────────────────────────────────┐
# │  셀 1 │ 라이브러리 설치                                  │
# └─────────────────────────────────────────────────────────┘
# !pip install -q pandas matplotlib seaborn plotly


# ┌─────────────────────────────────────────────────────────┐
# │  셀 2 │ 임포트 & 한글 폰트 설정                           │
# └─────────────────────────────────────────────────────────┘
import subprocess, matplotlib, os
subprocess.run(['apt-get', 'install', '-y', 'fonts-nanum'], capture_output=True)

cache_dir = matplotlib.get_cachedir()
for f in os.listdir(cache_dir):
    if f.startswith('fontlist'):
        os.remove(os.path.join(cache_dir, f))

from matplotlib import font_manager
font_manager._load_fontmanager(try_read_cache=False)

nanum_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
if os.path.exists(nanum_path):
    font_manager.fontManager.addfont(nanum_path)
    prop = font_manager.FontProperties(fname=nanum_path)
    font_name = prop.get_name()
    print(f"✅ 폰트 등록 성공: {font_name}")
else:
    font_name = 'DejaVu Sans'

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
plt.rcParams['font.family'] = font_name
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120
plt.rcParams['figure.figsize'] = (12, 6)

import pandas as pd
import numpy as np
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

print("✅ 라이브러리 & 폰트 설정 완료")


# ┌─────────────────────────────────────────────────────────┐
# │  셀 3 │ 파일 업로드 & 데이터 로드                         │
# └─────────────────────────────────────────────────────────┘
from google.colab import files

print("📂 파일을 업로드하세요 (Static_Dimension CSV)")
uploaded = files.upload()
filename = list(uploaded.keys())[0]

df_raw = pd.read_csv(filename, low_memory=False)

print(f"✅ 로드 완료 | {df_raw.shape[0]:,}행 × {df_raw.shape[1]}열")
df_raw.head(5)


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 4 │ 기본 구조 확인 (shape / dtypes / 결측 현황 / 기술통계)        │
# └─────────────────────────────────────────────────────────────────────┘
print("=" * 55)
print("▶ 기본 정보")
print("=" * 55)
print(f"  행 수       : {df_raw.shape[0]:,}")
print(f"  열 수       : {df_raw.shape[1]}")
print(f"  시군구명 수  : {df_raw['시군구명'].nunique()}개")
print(f"  시군구명 목록: {sorted(df_raw['시군구명'].unique())}")
print()

print("▶ 컬럼별 결측 현황")
null_df = pd.DataFrame({
    '비결측 수': df_raw.notnull().sum(),
    '결측 수'  : df_raw.isnull().sum(),
    '결측률(%)': (df_raw.isnull().sum() / len(df_raw) * 100).round(1)
})
display(null_df)
print()

print("▶ 수치 컬럼 기술통계")
display(df_raw[['유입유출비율', '평균체류시간', '평균숙박일수', '소비액']].describe().round(2))


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 5 │ [데이터 품질-1] 행 유형 식별 — 3종 서브테이블 구조 분석        │
# └─────────────────────────────────────────────────────────────────────┘
# ── 컬럼 채움 패턴으로 행 유형 분류
def classify_row(row):
    has_spend   = pd.notna(row['소비액'])
    has_cat     = pd.notna(row['업종대분류명'])
    has_inflow  = pd.notna(row['유입지역명'])
    has_ratio   = pd.notna(row['유입유출비율'])
    has_stay    = pd.notna(row['평균체류시간'])

    if has_cat and has_spend:
        return '① 업종소비액'
    elif has_inflow and has_ratio and has_stay:
        return '② 유입비율+체류숙박'
    elif has_inflow and has_ratio:
        return '③ 유입비율만'
    elif has_inflow and has_stay:
        return '④ 체류숙박만'
    else:
        return '⑤ 기타'

df_raw['행_유형'] = df_raw.apply(classify_row, axis=1)

print("▶ 행 유형 분포")
type_counts = df_raw['행_유형'].value_counts()
print(type_counts.to_string())
print()

# ── 유형별 채워지는 컬럼 패턴 시각화
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# 파이차트
type_counts.plot.pie(
    ax=axes[0], autopct='%1.0f%%', startangle=90,
    colors=['#2ecc71', '#3498db', '#e74c3c', '#f39c12', '#9b59b6'],
    textprops={'fontsize': 10}
)
axes[0].set_title('행 유형별 비율\n(Static_Dimension은 3가지 성격의 데이터가 혼재)',
                  fontsize=12, fontweight='bold')
axes[0].set_ylabel('')

# 컬럼별 채움 여부 히트맵 (유형별 평균)
cols_to_check = ['업종대분류명', '업종중분류명', '소비액', '유입지역명', '유입유출비율', '평균체류시간', '평균숙박일수']
pattern = df_raw.groupby('행_유형')[cols_to_check].apply(lambda x: x.notnull().mean())

sns.heatmap(pattern, ax=axes[1], cmap='Blues', annot=True, fmt='.0%',
            linewidths=0.5, linecolor='#ddd', annot_kws={'size': 10},
            cbar_kws={'label': '데이터 존재율'})
axes[1].set_title('행 유형별 × 컬럼별 데이터 존재율\n(파랑=있음, 흰색=없음)',
                  fontsize=12, fontweight='bold')
axes[1].set_xlabel('')
axes[1].tick_params(axis='x', rotation=30, labelsize=9)
axes[1].tick_params(axis='y', rotation=0, labelsize=9)

plt.tight_layout()
plt.show()

print("\n📋 행 유형 해석")
print("  ① 업종소비액      : 관광 목적지에서 업종별 외래 관광객 소비 규모")
print("  ② 유입비율+체류숙박: 출발지 → 목적지 유입 강도 + 체류 패턴이 동시 기록된 행")
print("  ③ 유입비율만      : 유입 강도만 기록 (주로 부산·대도시 출발지)")
print("  ④ 체류숙박만      : 체류시간·숙박일수만 기록 (유입비율 임계값 미달)")
print("  → CSI 활용 시 유형별로 분리하여 각각 다른 분석에 투입 필요")


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 6 │ [데이터 품질-2] 시군구 커버리지 비교 (23개 vs 카드매출 46개)   │
# └─────────────────────────────────────────────────────────────────────┘
# ── 경남 시군구 전체 목록 (카드매출_2 기준 18개 시군 + 창원시 5개구)
all_gyeongnam = [
    '거제시','거창군','고성군','김해시','남해군','밀양시','사천시','산청군',
    '양산시','의령군','진주시','창녕군','창원시','통영시','하동군','함안군',
    '함양군','합천군',
    '창원시 마산합포구','창원시 마산회원구','창원시 성산구','창원시 의창구','창원시 진해구'
]

# Static_Dimension 시군구명 정규화
df_raw['시군구_clean'] = df_raw['시군구명'].str.replace(r'^경상남도\s*', '', regex=True).str.strip()
static_cities = set(df_raw['시군구_clean'].unique())

present = sorted([c for c in all_gyeongnam if c in static_cities])
missing = sorted([c for c in all_gyeongnam if c not in static_cities])

print(f"▶ Static_Dimension 수록 시군구: {len(static_cities)}개")
print(f"  (함천군 오타 포함 시 22+1개)")
print()
print(f"▶ 경남 전체 대비 누락 시군구: {len(missing)}개")
for m in missing:
    print(f"  ✗ {m}")
print()
print(f"▶ 수록 확인된 시군구: {len(present)}개")
for p in present:
    print(f"  ✓ {p}")

# ── 시각화: 경남 지도 대신 카드형 커버리지 표시
fig, ax = plt.subplots(figsize=(14, 5))
all_sorted = sorted(all_gyeongnam)
colors_bar = ['#2ecc71' if c in static_cities else '#e74c3c' for c in all_sorted]
y_vals = [1] * len(all_sorted)

bars = ax.bar(all_sorted, y_vals, color=colors_bar, edgecolor='white', linewidth=1.5)
ax.set_yticks([])
ax.set_xticks(range(len(all_sorted)))
ax.set_xticklabels(all_sorted, rotation=45, ha='right', fontsize=9)
ax.set_title('경남 시군구별 Static_Dimension 수록 여부\n(녹색=수록, 빨강=누락)',
             fontsize=13, fontweight='bold', pad=12)

from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#2ecc71', label='수록됨'),
                   Patch(facecolor='#e74c3c', label='누락')]
ax.legend(handles=legend_elements, fontsize=10, loc='upper right')
plt.tight_layout()
plt.show()

print("\n⚠️  창원시(통합)는 누락, 5개 구(마산합포·마산회원·성산·의창·진해)는 별도 수록")
print("⚠️  카드매출 파일의 창원시 통합 데이터와 직접 조인 불가 → 구별 집계 필요")


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 7 │ [데이터 품질-3] 이상값·오타·중복 탐지                         │
# └─────────────────────────────────────────────────────────────────────┘
print("=" * 55)
print("▶ 이슈 1: 시군구명 오타 — '함천군' vs '합천군'")
print("=" * 55)
typo_check = df_raw[df_raw['시군구명'].str.contains('합천|함천', na=False)]['시군구명'].value_counts()
print(typo_check.to_string())
print("→ '함천군'은 '합천군'의 오타. 16개 행 수정 필요\n")

print("=" * 55)
print("▶ 이슈 2: 소비액이 0인 행")
print("=" * 55)
zero_spend = df_raw[df_raw['소비액'] == 0.0]
zero_by_city = zero_spend.groupby('시군구_clean').size()
print(f"소비액 0 행 수: {len(zero_spend)}개")
print(zero_by_city.sort_values(ascending=False).to_string())
print("→ 양산시·진주시·창녕군·창원시 각 구 등은 소비액이 전부 0 → 실질 데이터 없음\n")

print("=" * 55)
print("▶ 이슈 3: 같은 시군구-유입지역 조합에 중복 행")
print("=" * 55)
dup_check = df_raw[df_raw['유입지역명'].notna() & df_raw['유입유출비율'].notna()]
dup_count = dup_check.groupby(['시군구_clean', '유입지역명']).size()
multi_rows = dup_count[dup_count > 1]
print(f"중복 조합 수: {len(multi_rows)}개")
print("샘플 (거제시-사천시):")
sample = df_raw[(df_raw['시군구_clean']=='거제시') & (df_raw['유입지역명'].str.contains('사천', na=False))]
print(sample[['시군구_clean','유입지역명','유입유출비율','평균체류시간','평균숙박일수']].to_string(index=False))
print("→ 동일 OD쌍에 값이 다른 이유: 성별·연령대별 세분화 가능성. 집계 시 평균 처리 권장\n")

print("=" * 55)
print("▶ 이슈 4: 유입유출비율 이상값 탐지")
print("=" * 55)
ratio_stats = df_raw['유입유출비율'].describe()
q3 = ratio_stats['75%']
iqr = ratio_stats['75%'] - ratio_stats['25%']
upper_fence = q3 + 3 * iqr
outliers = df_raw[df_raw['유입유출비율'] > upper_fence][['시군구_clean','유입지역명','유입유출비율']]
print(f"IQR 기반 이상값 임계선(Q3+3IQR): {upper_fence:.2f}")
print(f"이상값 행 수: {len(outliers)}개")
print(outliers.sort_values('유입유출비율', ascending=False).head(10).to_string(index=False))

# ── 유입유출비율 분포 시각화
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

axes[0].hist(df_raw['유입유출비율'].dropna(), bins=50, color='#3498db', alpha=0.8, edgecolor='white')
axes[0].axvline(upper_fence, color='red', linestyle='--', label=f'이상값 임계선({upper_fence:.1f})')
axes[0].set_title('유입유출비율 전체 분포\n(오른쪽 꼬리 극단값 존재)', fontsize=12, fontweight='bold')
axes[0].set_xlabel('유입유출비율')
axes[0].set_ylabel('빈도')
axes[0].legend()
axes[0].grid(alpha=0.3)

# 로그 스케일
axes[1].hist(df_raw['유입유출비율'].dropna(), bins=50, color='#e67e22', alpha=0.8, edgecolor='white', log=True)
axes[1].axvline(upper_fence, color='red', linestyle='--', label=f'이상값 임계선({upper_fence:.1f})')
axes[1].set_title('유입유출비율 분포 (로그 스케일)\n극단값 구조 확인용', fontsize=12, fontweight='bold')
axes[1].set_xlabel('유입유출비율')
axes[1].set_ylabel('빈도 (log)')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.show()


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 8 │ 전처리 — 오타 수정 & 서브테이블 분리                          │
# └─────────────────────────────────────────────────────────────────────┘
df = df_raw.copy()

# ── 1) 오타 수정: 함천군 → 합천군
df['시군구명']    = df['시군구명'].str.replace('함천군', '합천군', regex=False)
df['시군구_clean'] = df['시군구_clean'].str.replace('함천군', '합천군', regex=False)
print(f"✅ '함천군' → '합천군' 수정 완료 | 수정 후 시군구 수: {df['시군구_clean'].nunique()}개")

# ── 2) 소비액 0인 행을 NaN으로 처리 (실질 데이터 없음)
df.loc[df['소비액'] == 0.0, '소비액'] = np.nan
print(f"✅ 소비액 0 → NaN 처리 완료 | 유효 소비액 행 수: {df['소비액'].notna().sum()}개")

# ── 3) 서브테이블 분리
# 소비액 테이블
df_spend = df[df['소비액'].notna()][
    ['시군구_clean', '업종대분류명', '업종중분류명', '소비액']
].copy()

# 유입 테이블 (비율 또는 체류 정보가 있는 행)
df_inflow = df[df['유입지역명'].notna()].copy()

# 유입지역명 공백 제거 & 광역 분류
df_inflow['유입지역명'] = df_inflow['유입지역명'].str.strip()
df_inflow['유입광역'] = df_inflow['유입지역명'].str[:3].map({
    '경상남': '경상남도',
    '부산광': '부산광역시',
    '대구광': '대구광역시',
    '울산광': '울산광역시',
    '경상북': '경상북도',
    '전라남': '전라남도',
    '전북특': '전북특별자치도',
    '서울특': '서울특별시',
    '인천광': '인천광역시',
    '경기도': '경기도',
    '강원특': '강원특별자치도',
})
df_inflow.loc[df_inflow['유입광역'].isna(), '유입광역'] = '경상남도'  # prefix 없는 경남 시군구

# 유입비율 집계용 (중복 조합 → 평균)
df_ratio = (
    df_inflow[df_inflow['유입유출비율'].notna()]
    .groupby(['시군구_clean', '유입지역명', '유입광역'], as_index=False)
    .agg(유입유출비율=('유입유출비율', 'mean'))
)

# 체류숙박 집계용 (중복 조합 → 평균)
df_stay2 = (
    df_inflow[df_inflow['평균체류시간'].notna()]
    .groupby(['시군구_clean', '유입지역명', '유입광역'], as_index=False)
    .agg(평균체류시간=('평균체류시간', 'mean'),
         평균숙박일수=('평균숙박일수', 'mean'))
)

print(f"\n✅ 서브테이블 분리 완료")
print(f"  df_spend  (업종별 소비액)   : {df_spend.shape[0]}행, {df_spend['시군구_clean'].nunique()}개 시군구")
print(f"  df_ratio  (유입비율 집계)   : {df_ratio.shape[0]}행")
print(f"  df_stay2  (체류숙박 집계)   : {df_stay2.shape[0]}행")


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 9 │ [유입 분석-1] 시군구별 유입유출비율 분포                        │
# └─────────────────────────────────────────────────────────────────────┘
# ── 시군구별 유입유출비율 요약 (최대·평균·중앙값)
ratio_summary = (
    df_ratio.groupby('시군구_clean')['유입유출비율']
    .agg(최대=('max'), 평균=('mean'), 중앙값=('median'), 유입지역수=('count'))
    .round(2)
    .sort_values('최대', ascending=False)
    .reset_index()
)

print("📊 시군구별 유입유출비율 요약 (최대값 기준 정렬)")
display(ratio_summary)

# ── 시각화 1: 시군구별 최대 유입유출비율 수평 막대
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

bar_colors = plt.cm.RdYlGn_r(
    (ratio_summary['최대'] - ratio_summary['최대'].min()) /
    (ratio_summary['최대'].max() - ratio_summary['최대'].min())
)
bars = axes[0].barh(ratio_summary['시군구_clean'][::-1],
                    ratio_summary['최대'][::-1],
                    color=bar_colors[::-1], edgecolor='white')
axes[0].axvline(ratio_summary['최대'].median(), color='navy', linestyle='--',
                alpha=0.6, label=f"중앙값 {ratio_summary['최대'].median():.1f}")
axes[0].set_xlabel('유입유출비율 (최대값)', fontsize=11)
axes[0].set_title('시군구별 유입유출비율 최대값\n(높을수록 외지인 방문 집중도 강함)',
                  fontsize=12, fontweight='bold')
axes[0].legend(fontsize=9)
axes[0].grid(axis='x', alpha=0.3)
for bar, val in zip(bars[::-1], ratio_summary['최대'][::-1]):
    axes[0].text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                 f'{val:.1f}', va='center', fontsize=8.5)

# 시각화 2: 박스플롯 (시군구별 유입비율 분포)
top10_cities = ratio_summary.head(10)['시군구_clean'].tolist()
box_data = [df_ratio[df_ratio['시군구_clean'] == c]['유입유출비율'].values
            for c in top10_cities]
bp = axes[1].boxplot(box_data, patch_artist=True, vert=True,
                     medianprops={'color': 'black', 'linewidth': 1.5})
palette = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(top10_cities)))
for patch, color in zip(bp['boxes'], palette):
    patch.set_facecolor(color)
axes[1].set_xticklabels(top10_cities, rotation=40, ha='right', fontsize=9)
axes[1].set_ylabel('유입유출비율', fontsize=11)
axes[1].set_title('유입유출비율 상위 10개 시군구 분포\n(박스=IQR, 수염=1.5*IQR)',
                  fontsize=12, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

# ── 관광 특화 등급 분류
ratio_summary['관광특화등급'] = pd.cut(
    ratio_summary['최대'],
    bins=[0, 10, 20, 30, 100],
    labels=['일반형 (~10)', '관광형 (10~20)', '고관광형 (20~30)', '관광특화 (30+)']
)
print("\n📊 관광 특화 등급 분류 (유입유출비율 최대값 기준)")
print(ratio_summary[['시군구_clean', '최대', '관광특화등급']].to_string(index=False))


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 10 │ [유입 분석-2] 주요 유입 지역 & 광역별 집계                    │
# └─────────────────────────────────────────────────────────────────────┘
# ── 전체 유입지역 Top 20 (유입비율 평균 기준)
top_inflow = (
    df_ratio.groupby('유입지역명')['유입유출비율']
    .agg(평균유입비율='mean', 나타난횟수='count')
    .sort_values('평균유입비율', ascending=False)
    .head(20)
    .reset_index()
)

print("📊 경남 전체 평균 유입유출비율 상위 20개 출발지")
print(top_inflow.to_string(index=False))

# ── 시각화 1: Top 20 유입지역 막대
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

colors_inflow = ['#e74c3c' if '부산' in r else '#2980b9' for r in top_inflow['유입지역명']]
axes[0].barh(top_inflow['유입지역명'][::-1], top_inflow['평균유입비율'][::-1],
             color=colors_inflow[::-1], alpha=0.85, edgecolor='white')
axes[0].set_xlabel('평균 유입유출비율', fontsize=11)
axes[0].set_title('경남 관광지로의 평균 유입유출비율 Top 20\n(빨강=부산, 파랑=기타)',
                  fontsize=12, fontweight='bold')
axes[0].grid(axis='x', alpha=0.3)
axes[0].tick_params(axis='y', labelsize=9)

# 시각화 2: 광역별 집계 파이차트
region_agg = (
    df_ratio.groupby('유입광역')['유입유출비율']
    .agg(총유입강도='sum', 평균유입비율='mean')
    .sort_values('총유입강도', ascending=False)
    .reset_index()
)

region_palette = {
    '경상남도':     '#2ecc71',
    '부산광역시':   '#e74c3c',
    '대구광역시':   '#e67e22',
    '경상북도':     '#3498db',
    '전라남도':     '#9b59b6',
    '전북특별자치도': '#1abc9c',
    '울산광역시':   '#f39c12',
}
region_colors = [region_palette.get(r, '#bdc3c7') for r in region_agg['유입광역']]

axes[1].pie(region_agg['총유입강도'], labels=region_agg['유입광역'],
            colors=region_colors, autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 9})
axes[1].set_title('광역별 경남 관광지 유입 강도 비중\n(유입유출비율 합산 기준)',
                  fontsize=12, fontweight='bold')

plt.tight_layout()
plt.show()

# ── 시각화 3: 시군구별 × 광역별 유입 히트맵
heatmap_data = (
    df_ratio.groupby(['시군구_clean', '유입광역'])['유입유출비율']
    .mean()
    .unstack(fill_value=0)
    .round(2)
)
heatmap_data = heatmap_data.loc[ratio_summary['시군구_clean'].tolist()]  # 관광특화 순 정렬

fig, ax = plt.subplots(figsize=(14, 10))
sns.heatmap(heatmap_data, ax=ax, cmap='YlOrRd',
            annot=True, fmt='.1f', annot_kws={'size': 9},
            linewidths=0.3, linecolor='#eee',
            cbar_kws={'label': '평균 유입유출비율', 'shrink': 0.6})
ax.set_title('시군구별 × 광역별 유입유출비율 히트맵\n(짙을수록 해당 광역에서의 방문 집중도 강함)',
             fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel('출발 광역', fontsize=11)
ax.set_ylabel('')
ax.tick_params(axis='y', labelsize=9)
ax.tick_params(axis='x', rotation=30)
plt.tight_layout()
plt.show()


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 11 │ [유입 분석-3] 평균 체류시간·숙박일수 시군구별 비교             │
# └─────────────────────────────────────────────────────────────────────┘
# ── 시군구별 체류시간·숙박일수 평균
stay_summary = (
    df_stay2.groupby('시군구_clean')
    .agg(평균체류시간_분=('평균체류시간', 'mean'),
         평균숙박일수=('평균숙박일수', 'mean'),
         유입지역수=('유입지역명', 'count'))
    .round(2)
    .reset_index()
)
stay_summary['평균체류시간_시간'] = (stay_summary['평균체류시간_분'] / 60).round(1)
stay_summary = stay_summary.sort_values('평균숙박일수', ascending=False)

print("📊 시군구별 평균 체류시간·숙박일수")
display(stay_summary[['시군구_clean','평균체류시간_시간','평균숙박일수','유입지역수']].to_string(index=False))

# ── 시각화 1: 체류시간 × 숙박일수 산점도
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

sc = axes[0].scatter(
    stay_summary['평균체류시간_시간'],
    stay_summary['평균숙박일수'],
    s=stay_summary['유입지역수'] * 5,
    c=stay_summary['평균숙박일수'],
    cmap='YlOrRd', alpha=0.85, edgecolors='gray', linewidth=0.5
)
plt.colorbar(sc, ax=axes[0], label='평균 숙박일수')
for _, row in stay_summary.iterrows():
    axes[0].annotate(row['시군구_clean'],
                     (row['평균체류시간_시간'], row['평균숙박일수']),
                     fontsize=8, xytext=(4, 2), textcoords='offset points')
axes[0].axhline(stay_summary['평균숙박일수'].mean(), color='navy',
                linestyle='--', alpha=0.5,
                label=f"평균 숙박일수 {stay_summary['평균숙박일수'].mean():.2f}일")
axes[0].axvline(stay_summary['평균체류시간_시간'].mean(), color='green',
                linestyle=':', alpha=0.5,
                label=f"평균 체류시간 {stay_summary['평균체류시간_시간'].mean():.1f}h")
axes[0].set_xlabel('평균 체류시간 (시간)', fontsize=11)
axes[0].set_ylabel('평균 숙박일수 (일)', fontsize=11)
axes[0].set_title('체류시간 vs 숙박일수 산점도\n(버블 크기 = 유입지역 다양성)',
                  fontsize=12, fontweight='bold')
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

# 시각화 2: 시군구별 숙박일수 수평 막대
bar_colors2 = plt.cm.YlOrRd(
    (stay_summary['평균숙박일수'] - stay_summary['평균숙박일수'].min()) /
    (stay_summary['평균숙박일수'].max() - stay_summary['평균숙박일수'].min())
)
axes[1].barh(stay_summary['시군구_clean'][::-1],
             stay_summary['평균숙박일수'][::-1],
             color=bar_colors2[::-1], edgecolor='white')
axes[1].axvline(stay_summary['평균숙박일수'].mean(), color='navy',
                linestyle='--', alpha=0.6,
                label=f"평균 {stay_summary['평균숙박일수'].mean():.2f}일")
axes[1].set_xlabel('평균 숙박일수 (일)', fontsize=11)
axes[1].set_title('시군구별 평균 숙박일수\n(길수록 체류형 관광 특성)',
                  fontsize=12, fontweight='bold')
axes[1].legend(fontsize=9)
axes[1].grid(axis='x', alpha=0.3)
axes[1].set_xlim(left=stay_summary['평균숙박일수'].min() * 0.97)
axes[1].tick_params(axis='y', labelsize=9)
for i, (val, row) in enumerate(zip(stay_summary['평균숙박일수'][::-1],
                                    stay_summary.iloc[::-1].itertuples())):
    axes[1].text(val + 0.003, i, f'{val:.2f}일', va='center', fontsize=8.5)

plt.tight_layout()
plt.show()

# ── 체류·숙박 유형 분류
stay_summary['체류유형'] = pd.cut(
    stay_summary['평균숙박일수'],
    bins=[0, 2.6, 2.9, 10],
    labels=['단기체류 (~2.6일)', '일반체류 (2.6~2.9일)', '장기체류 (2.9일+)']
)
print("\n📊 체류 유형 분류")
print(stay_summary[['시군구_clean', '평균체류시간_시간', '평균숙박일수', '체류유형']].to_string(index=False))


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 12 │ [소비 분석-1] 업종별 관광 소비액 비중                         │
# └─────────────────────────────────────────────────────────────────────┘
# 유효 소비액만 (0·NaN 제외)
df_sp = df_spend[df_spend['소비액'].notna() & (df_spend['소비액'] > 0)].copy()

# ── 업종 대분류별 소비액 합계
cat_total = (
    df_sp.groupby('업종대분류명')['소비액']
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
cat_total['비중(%)'] = (cat_total['소비액'] / cat_total['소비액'].sum() * 100).round(1)

print("📊 업종 대분류별 관광 소비액")
print(cat_total.to_string(index=False))

# ── 업종 중분류별 소비액
subcat_total = (
    df_sp.groupby(['업종대분류명', '업종중분류명'])['소비액']
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# 도넛 차트 (대분류)
cat_palette = {
    '쇼핑업':      '#e74c3c',
    '식음료업':    '#2980b9',
    '숙박업':      '#27ae60',
    '여가서비스업': '#f39c12',
    '의료웰니스업': '#9b59b6',
    '운송업':      '#1abc9c',
    '여행업':      '#95a5a6',
}
cat_colors = [cat_palette.get(c, '#bdc3c7') for c in cat_total['업종대분류명']]

wedges, texts, autotexts = axes[0].pie(
    cat_total['소비액'],
    labels=cat_total['업종대분류명'],
    colors=cat_colors,
    autopct=lambda p: f'{p:.1f}%\n({p/100*cat_total["소비액"].sum()/1e6:.1f}M)',
    startangle=90,
    pctdistance=0.75,
    wedgeprops={'width': 0.55},   # 도넛 구멍
    textprops={'fontsize': 9}
)
axes[0].set_title('관광 업종 대분류별 소비액 비중\n(단위: 백만원)',
                  fontsize=12, fontweight='bold')

# 중분류 수평 막대 (상위 12개)
top12_sub = subcat_total.head(12)
sub_colors = [cat_palette.get(r['업종대분류명'], '#bdc3c7') for _, r in top12_sub.iterrows()]
axes[1].barh(
    top12_sub['업종중분류명'][::-1],
    top12_sub['소비액'][::-1] / 1e6,
    color=sub_colors[::-1], alpha=0.85, edgecolor='white'
)
axes[1].set_xlabel('소비액 합계 (백만원)', fontsize=11)
axes[1].set_title('업종 중분류별 관광 소비액 Top 12\n(색상 = 대분류 구분)',
                  fontsize=12, fontweight='bold')
axes[1].grid(axis='x', alpha=0.3)
axes[1].tick_params(axis='y', labelsize=9)

from matplotlib.patches import Patch
legend_els = [Patch(facecolor=v, label=k) for k, v in cat_palette.items()]
axes[1].legend(handles=legend_els, fontsize=8, loc='lower right')

plt.tight_layout()
plt.show()

print("\n📊 업종 중분류 전체 소비액")
subcat_total['비중(%)'] = (subcat_total['소비액'] / subcat_total['소비액'].sum() * 100).round(1)
print(subcat_total.to_string(index=False))


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 13 │ [소비 분석-2] 시군구별 업종 포트폴리오 & 관광 의존도           │
# └─────────────────────────────────────────────────────────────────────┘
# ── 시군구 × 업종 대분류 소비액 피벗
city_cat = (
    df_sp.groupby(['시군구_clean', '업종대분류명'])['소비액']
    .sum()
    .unstack(fill_value=0)
)
city_cat_pct = city_cat.div(city_cat.sum(axis=1), axis=0) * 100  # 비중(%)

# 관광 의존도 지표 (HHI: 허핀달-허쉬만 지수)
city_cat_pct['HHI'] = ((city_cat_pct.drop(columns=['HHI'], errors='ignore') / 100) ** 2).sum(axis=1).round(4)
city_cat_pct_sorted = city_cat_pct.sort_values('HHI', ascending=False)

print("📊 시군구별 업종 포트폴리오 비중(%) + HHI")
display(city_cat_pct_sorted.round(1))

# ── 시각화 1: 스택 막대 (시군구별 업종 비중)
plot_cols = [c for c in city_cat_pct.columns if c != 'HHI']
city_cat_pct_plot = city_cat_pct_sorted[plot_cols].copy()

fig, axes = plt.subplots(2, 1, figsize=(16, 14))

city_cat_pct_plot.plot(
    kind='bar', stacked=True, ax=axes[0],
    color=[cat_palette.get(c, '#bdc3c7') for c in plot_cols],
    edgecolor='white', linewidth=0.4
)
axes[0].set_title('시군구별 관광 소비 업종 포트폴리오\n(HHI 높은 순 정렬: 특정 업종 집중도 높음)',
                  fontsize=13, fontweight='bold')
axes[0].set_xlabel('')
axes[0].set_ylabel('소비 비중 (%)', fontsize=11)
axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=40, ha='right', fontsize=9)
axes[0].legend(loc='upper right', fontsize=9, ncol=2)
axes[0].grid(axis='y', alpha=0.3)

# 시각화 2: HHI 막대 (업종 집중도)
hhi_sorted = city_cat_pct_sorted['HHI'].reset_index()
hhi_colors = plt.cm.RdYlGn_r(
    (hhi_sorted['HHI'] - hhi_sorted['HHI'].min()) /
    (hhi_sorted['HHI'].max() - hhi_sorted['HHI'].min())
)
axes[1].bar(hhi_sorted['시군구_clean'], hhi_sorted['HHI'],
            color=hhi_colors, edgecolor='white')
axes[1].axhline(hhi_sorted['HHI'].mean(), color='navy', linestyle='--',
                alpha=0.6, label=f"평균 HHI {hhi_sorted['HHI'].mean():.3f}")
axes[1].set_ylabel('HHI (업종 집중도)', fontsize=11)
axes[1].set_title('시군구별 관광 소비 업종 집중도 (HHI)\n(1.0 = 단일 업종 완전 집중, 0.14 = 7개 업종 균등분산)',
                  fontsize=12, fontweight='bold')
axes[1].set_xticklabels(hhi_sorted['시군구_clean'], rotation=40, ha='right', fontsize=9)
axes[1].legend(fontsize=9)
axes[1].grid(axis='y', alpha=0.3)
for i, (val, city) in enumerate(zip(hhi_sorted['HHI'], hhi_sorted['시군구_clean'])):
    axes[1].text(i, val + 0.003, f'{val:.3f}', ha='center', fontsize=7.5)

plt.tight_layout()
plt.show()

print("\n📊 HHI 기반 업종 집중도 등급")
hhi_sorted['집중도등급'] = pd.cut(
    hhi_sorted['HHI'],
    bins=[0, 0.25, 0.40, 1.0],
    labels=['분산형 (<0.25)', '중간집중 (0.25~0.40)', '고집중 (0.40+)']
)
print(hhi_sorted[['시군구_clean', 'HHI', '집중도등급']].to_string(index=False))


# ┌─────────────────────────────────────────────────────────────────────┐
# │  셀 14 │ [통합] 시군구별 관광 취약도 종합 프로파일 (CSI 보정 변수)      │
# └─────────────────────────────────────────────────────────────────────┘
# ── 각 분석 결과 통합
profile = ratio_summary[['시군구_clean', '최대', '관광특화등급']].copy()
profile = profile.rename(columns={'최대': '유입유출비율_최대'})

profile = profile.merge(
    stay_summary[['시군구_clean', '평균숙박일수', '체류유형']],
    on='시군구_clean', how='left'
)

hhi_merge = hhi_sorted[['시군구_clean', 'HHI', '집중도등급']]
profile = profile.merge(hhi_merge, on='시군구_clean', how='left')

# ── 병합 결과 진단 (빈 차트 원인 파악용)
print("▶ 병합 후 NaN 현황")
print(profile[['유입유출비율_최대', '평균숙박일수', 'HHI']].isna().sum().to_string())
print(f"  체류유형 고유값: {profile['체류유형'].dropna().unique()}")

# ── NaN-안전 Min-Max 정규화
# fallback: 해당 컬럼이 전부 NaN일 때 사용할 대체값 (도메인 지식 기반)
def minmax_safe(series, fallback=None):
    filled = series.copy()
    if filled.isna().all():
        filled = filled.fillna(fallback if fallback is not None else 0)
    else:
        filled = filled.fillna(filled.median())
    s_min, s_max = filled.min(), filled.max()
    if s_max == s_min:
        return pd.Series(0.5, index=series.index)
    return (filled - s_min) / (s_max - s_min)

# 관광 취약도 종합 점수 (0~100, 높을수록 외부 충격에 취약)
profile['취약도_유입집중'] = minmax_safe(profile['유입유출비율_최대']) * 40
# fallback=2.7 → 경남 평균 숙박일수 (체류숙박 행이 없는 시군구에 대한 대체값)
profile['취약도_장기체류']  = minmax_safe(profile['평균숙박일수'], fallback=2.7) * 35
profile['취약도_HHI']      = minmax_safe(profile['HHI'], fallback=0) * 25
profile['관광취약도_점수']  = (
    profile['취약도_유입집중'] + profile['취약도_장기체류'] + profile['취약도_HHI']
).round(1)
profile = profile.sort_values('관광취약도_점수', ascending=False).reset_index(drop=True)
profile.index += 1

print(f"\n관광취약도_점수 범위: {profile['관광취약도_점수'].min():.1f} ~ {profile['관광취약도_점수'].max():.1f}")
print(f"NaN 점수 개수: {profile['관광취약도_점수'].isna().sum()}")

print("\n📊 시군구별 관광 취약도 종합 프로파일")
display(
    profile[['시군구_clean', '유입유출비율_최대', '관광특화등급',
             '평균숙박일수', '체류유형', 'HHI', '집중도등급', '관광취약도_점수']]
    .style
    .background_gradient(subset=['관광취약도_점수'], cmap='RdYlGn_r')
    .background_gradient(subset=['유입유출비율_최대'], cmap='YlOrRd')
    .background_gradient(subset=['HHI'], cmap='YlOrRd')
    .format({'유입유출비율_최대': '{:.2f}', '평균숙박일수': '{:.2f}일',
             'HHI': '{:.3f}', '관광취약도_점수': '{:.1f}점'})
    .set_caption('관광 취약도 = 외지인 유입집중(40%) + 장기체류(35%) + 업종집중도(25%)')
)

# ── 시각화
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 막대 차트 (전체 순위) — np.nanmin/nanmax 로 NaN 안전 색상 계산
scores_arr  = profile['관광취약도_점수'].values.astype(float)
cities_arr  = profile['시군구_clean'].values

s_min = np.nanmin(scores_arr)
s_max = np.nanmax(scores_arr)
norm_scores = (scores_arr - s_min) / (s_max - s_min + 1e-9)
bar_c = plt.cm.RdYlGn_r(norm_scores)

axes[0].barh(cities_arr[::-1], scores_arr[::-1], color=bar_c[::-1], edgecolor='white')
axes[0].set_xlabel('관광 취약도 점수 (0~100)', fontsize=11)
axes[0].set_title('시군구별 관광 취약도 점수 순위\n(높을수록 외부 충격 시 상권 침체 위험 큼)',
                  fontsize=12, fontweight='bold')
axes[0].grid(axis='x', alpha=0.3)
axes[0].tick_params(axis='y', labelsize=9)

# 값 레이블 — enumerate 로 인덱스·패치 수 불일치 방지
patches = axes[0].patches
rev_scores = scores_arr[::-1]
for i, patch in enumerate(patches):
    val = rev_scores[i] if i < len(rev_scores) else None
    if val is not None and not np.isnan(val):
        axes[0].text(val + 0.3, patch.get_y() + patch.get_height() / 2,
                     f'{val:.1f}', va='center', fontsize=8.5)

# 3개 구성 요소 스택 막대 (상위 10개)
top10 = profile.head(10)
comp_cols   = ['취약도_유입집중', '취약도_장기체류', '취약도_HHI']
comp_labels = ['유입집중도(40%)', '장기체류(35%)', '업종집중도(25%)']
comp_colors = ['#e74c3c', '#3498db', '#f39c12']

bottom = np.zeros(len(top10))
for col, label, color in zip(comp_cols, comp_labels, comp_colors):
    vals = top10[col].fillna(0).values
    axes[1].bar(top10['시군구_clean'], vals,
                bottom=bottom, label=label, color=color, alpha=0.85, edgecolor='white')
    bottom += vals

axes[1].set_ylabel('취약도 점수 구성', fontsize=11)
axes[1].set_title('상위 10개 시군구 관광 취약도 구성 분해\n(각 지표별 기여 비중)',
                  fontsize=12, fontweight='bold')
axes[1].set_xticks(range(len(top10)))
axes[1].set_xticklabels(top10['시군구_clean'].tolist(), rotation=40, ha='right', fontsize=9)
axes[1].legend(fontsize=9)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

print("\n🔑 CSI 프로젝트 활용 포인트")
print("  ① 관광취약도 점수 → CSI '업종집중도(25%)' 지표의 보정 입력값으로 활용")
print("  ② 유입지역 다양성 → 특정 광역 의존 시 외부 충격 확산 위험 경고 지표")
print("  ③ 평균 숙박일수   → 거시경제_1 파일의 숙박자비율 교차 검증에 활용")
print("  ④ 소비액 0 시군구 → 카드매출_2에서 직접 관광 소비 측정으로 대체 필요")
