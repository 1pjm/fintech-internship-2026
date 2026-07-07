"""
raw_transactions.csv (fetch_realprice.py 결과) -> (시도, 주택구분, 연월) 단위로
갱신계약비율 / 갱신요구권행사비율 / 평균보증금인상률 을 집계한다.

정의 (대화 정리본 9-4절 그대로, 단 실제 API 응답값에 맞게 보정):
  갱신계약비율        = contractType == '갱신' 비율   (contractType이 공백(정보없음)인 행은 분모에서 제외)
  갱신요구권행사비율   = useRRRight == '사용' 비율      (전체 계약 대비. API 실제값은 'Y'가 아니라 '사용'/공백)
  평균보증금인상률     = mean((deposit - preDeposit) / preDeposit)  (갱신계약만, preDeposit>0)

주의: 실거래가 API의 contractType/useRRRight는 정보가 없을 때 빈 문자열이 아니라
공백문자(" ")로 채워져 있다 (기존 전세보증대위변제 데이터의 "임대보증금액" 컬럼과 동일한 패턴).
그대로 '갱신'/'사용' 문자열과만 비교하면 되지만, 공백을 신규/미사용으로 잘못 세지 않도록
strip() 하고 contractType이 유효값('신규'/'갱신')인 행만 갱신계약비율 분모로 쓴다.

사용법:
    python build_renewal_features.py --in raw_transactions.csv --out renewal_features.csv
"""
import argparse

import pandas as pd

from house_type_map import HOUSE_TYPE_TO_API

HOUSE_TYPE_RAW_NORM = {
    "다세대": "다세대주택", "다세대주택": "다세대주택",
    "연립": "연립주택", "연립주택": "연립주택",
    "단독": "단독주택", "단독주택": "단독주택",
    "다가구": "다가구주택", "다가구주택": "다가구주택",
}

ALL_HOUSE_TYPES = list(HOUSE_TYPE_TO_API.keys())


def normalize_house_type(row):
    """rh/sh API는 house_type_raw로 세부 유형을 알 수 있고, apt/offi는 유형이 고정이다."""
    if row["api_type"] == "apt":
        return "아파트"
    if row["api_type"] == "offi":
        return "오피스텔"
    return HOUSE_TYPE_RAW_NORM.get(str(row["house_type_raw"]).strip(), None)


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def aggregate(df, group_cols):
    valid_ct = df[df["contract_type"].isin(["신규", "갱신"])]
    grp = valid_ct.groupby(group_cols, dropna=False)
    out = grp.agg(
        n_contracts=("contract_type", "size"),
        갱신계약비율=("contract_type", lambda s: (s == "갱신").mean()),
    ).reset_index()

    rr = (
        df.groupby(group_cols, dropna=False)["use_rr_right"]
        .apply(lambda s: (s == "사용").mean())
        .reset_index(name="갱신요구권행사비율")
    )
    out = out.merge(rr, on=group_cols, how="left")

    renewal = valid_ct[valid_ct["contract_type"] == "갱신"].copy()
    renewal = renewal[renewal["pre_deposit"] > 0]
    renewal["인상률"] = (renewal["deposit"] - renewal["pre_deposit"]) / renewal["pre_deposit"]
    rate = renewal.groupby(group_cols, dropna=False)["인상률"].mean().reset_index()
    rate = rate.rename(columns={"인상률": "평균보증금인상률"})

    return out.merge(rate, on=group_cols, how="left")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="infile", default="raw_transactions.csv")
    parser.add_argument("--out", default="renewal_features.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.infile, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    before = len(df)
    df = df.drop_duplicates()
    if len(df) < before:
        print(f"완전 중복행 {before - len(df)}건 제거 ({before}행 -> {len(df)}행)")

    df["contract_type"] = df["contract_type"].str.strip()
    df["use_rr_right"] = df["use_rr_right"].str.strip()

    df["deposit"] = to_num(df["deposit"])
    df["pre_deposit"] = to_num(df["pre_deposit"])
    df["deal_year"] = to_num(df["deal_year"])
    df["deal_month"] = to_num(df["deal_month"])
    df["연월"] = df["deal_year"].astype("Int64").astype(str) + "-" + df["deal_month"].astype("Int64").astype(str).str.zfill(2)

    df["주택구분"] = df.apply(normalize_house_type, axis=1)
    df["api_group"] = df["api_type"]

    # 세부 유형까지 정확히 복원되는 경우 (아파트/오피스텔/다세대/연립/단독/다가구)
    detailed = df[df["주택구분"].notna()].copy()
    fine = aggregate(detailed, ["sido", "주택구분", "연월"])
    fine.to_csv("renewal_features_fine.csv", index=False, encoding="utf-8-sig")

    # api 그룹 단위 (다중주택/주상복합처럼 세부유형이 없는 케이스의 대체값용)
    coarse = aggregate(df, ["sido", "api_group", "연월"])
    coarse.to_csv("renewal_features_coarse.csv", index=False, encoding="utf-8-sig")

    # 시도 무시, 주택구분(api_group) + 연월 단위 전국 평균 (시도 매칭 실패시 최종 대체값)
    national = aggregate(df, ["api_group", "연월"])
    national.to_csv("renewal_features_national.csv", index=False, encoding="utf-8-sig")

    print(f"fine: {len(fine)}행, coarse: {len(coarse)}행, national: {len(national)}행 -> renewal_features_*.csv 저장")
    print("merge_renewal_features.py 에서 이 3개 파일을 fine -> coarse -> national 순서로 대체하며 merge 한다.")


if __name__ == "__main__":
    main()
