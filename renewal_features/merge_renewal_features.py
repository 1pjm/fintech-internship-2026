"""
build_renewal_features.py 가 만든 renewal_features_fine/coarse/national.csv 를
data/전세보증대위변제현황_피처추가.xlsx 에 merge해서 3개 컬럼을 추가한다.

대체(fallback) 순서 (샘플링한 대표 시군구라 특정 시도x주택구분x월 조합이 비어있을 수 있어서):
  1순위: (시도, 주택구분, 연월) 정확히 일치 - fine
  2순위: (시도, api_group, 연월) - coarse  (다중주택/주상복합처럼 세부유형 구분이 안 되는 경우 포함)
  3순위: (api_group, 연월) 전국 평균 - national
  4순위: 그래도 없으면 전체 평균

어느 단계에서 값을 채웠는지 '갱신피처_출처' 컬럼에 남겨서 투명성 확보
(7장에서 이미 쓰던 '주택가액_이상치여부' 플래그 방식과 동일한 접근).

사용법:
    python merge_renewal_features.py \
        --base ../data/전세보증대위변제현황_피처추가.xlsx \
        --out ../data/전세보증대위변제현황_피처추가_갱신피처.xlsx
"""
import argparse

import pandas as pd

from house_type_map import HOUSE_TYPE_TO_API

FEATURE_COLS = ["평균보증금인상률", "갱신계약비율", "갱신요구권행사비율"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="../data/전세보증대위변제현황_피처추가.xlsx")
    parser.add_argument("--fine", default="renewal_features_fine.csv")
    parser.add_argument("--coarse", default="renewal_features_coarse.csv")
    parser.add_argument("--national", default="renewal_features_national.csv")
    parser.add_argument("--out", default="../data/전세보증대위변제현황_피처추가_갱신피처.xlsx")
    args = parser.parse_args()

    df = pd.read_excel(args.base)
    df["연월"] = pd.to_datetime(df["보증완료월"]).dt.strftime("%Y-%m")
    df["api_group"] = df["주택구분"].map(HOUSE_TYPE_TO_API)

    fine = pd.read_csv(args.fine, encoding="utf-8-sig")
    coarse = pd.read_csv(args.coarse, encoding="utf-8-sig")
    national = pd.read_csv(args.national, encoding="utf-8-sig")

    overall = {c: national[c].mean() for c in FEATURE_COLS}

    df = df.merge(
        fine[["sido", "주택구분", "연월"] + FEATURE_COLS],
        left_on=["시도", "주택구분", "연월"], right_on=["sido", "주택구분", "연월"],
        how="left",
    ).drop(columns=["sido"])

    df["갱신피처_출처"] = df[FEATURE_COLS[0]].notna().map({True: "fine", False: None})

    coarse_ren = coarse.rename(columns={c: f"{c}_coarse" for c in FEATURE_COLS})
    df = df.merge(
        coarse_ren[["sido", "api_group", "연월"] + [f"{c}_coarse" for c in FEATURE_COLS]],
        left_on=["시도", "api_group", "연월"], right_on=["sido", "api_group", "연월"],
        how="left",
    ).drop(columns=["sido"])

    national_ren = national.rename(columns={c: f"{c}_national" for c in FEATURE_COLS})
    df = df.merge(
        national_ren[["api_group", "연월"] + [f"{c}_national" for c in FEATURE_COLS]],
        on=["api_group", "연월"], how="left",
    )

    for c in FEATURE_COLS:
        need_coarse = df[c].isna() & df[f"{c}_coarse"].notna()
        df.loc[need_coarse & df["갱신피처_출처"].isna(), "갱신피처_출처"] = "coarse"
        df[c] = df[c].fillna(df[f"{c}_coarse"])

        need_national = df[c].isna() & df[f"{c}_national"].notna()
        df.loc[need_national & df["갱신피처_출처"].isna(), "갱신피처_출처"] = "national"
        df[c] = df[c].fillna(df[f"{c}_national"])

        still_na = df[c].isna()
        df.loc[still_na & df["갱신피처_출처"].isna(), "갱신피처_출처"] = "overall_mean"
        df[c] = df[c].fillna(overall[c])

    df = df.drop(columns=["연월", "api_group"] + [f"{c}_coarse" for c in FEATURE_COLS] + [f"{c}_national" for c in FEATURE_COLS])

    df.to_excel(args.out, index=False)
    print(f"저장 완료: {args.out} ({df.shape[0]}행 x {df.shape[1]}컬럼)")
    print(df["갱신피처_출처"].value_counts(dropna=False))


if __name__ == "__main__":
    main()
