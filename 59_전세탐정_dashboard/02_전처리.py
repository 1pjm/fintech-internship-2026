"""02 전처리 — 원본 xlsx를 읽어 정제된 clean.parquet으로 저장한다.
04는 이 파일을 새로 계산하지 않고, 03이 채점한 결과만 읽는다.

실행:
    python 02_전처리.py
"""
import pandas as pd

import common as C

CAT_COLS = ["시도", "주택구분"]


def main():
    C.DATA_DIR.mkdir(exist_ok=True)

    df = pd.read_excel(C.RAW_XLSX)
    print(f"원본 {df.shape}")

    # 일련번호는 식별자일 뿐인데 엑셀 저장 과정에서 일부 행이 날짜형으로 잘못 들어와 있어
    # (예: 2022-10-01) parquet 저장 시 타입 충돌이 난다. 표시용 문자열로 통일한다.
    bad_id = ~df["일련번호"].map(lambda v: isinstance(v, (int, float)))
    if bad_id.any():
        print(f"일련번호가 날짜형으로 잘못 들어온 행 {int(bad_id.sum())}건 → 문자열로 정리")
    df["일련번호"] = df["일련번호"].astype(str)

    dup = df["일련번호"].duplicated().sum()
    print(f"업무 키(일련번호) 중복: {dup}건")

    # 깡통전세여부는 깡통지수와 중복인 파생 라벨이라 제외 (modeling/전세사기예측_AUC 비교.ipynb와 동일)
    df = df.drop(columns=["깡통전세여부"])

    na = df.isna().sum()
    if na.any():
        print("결측 발견:\n", na[na > 0])
    else:
        print("결측 0건")

    # 날짜 분리 (보증완료월은 엑셀에서부터 datetime으로 들어와 있어 파싱 이슈 없음)
    dt = pd.to_datetime(df["보증완료월"])
    df["보증완료연도"] = dt.dt.year
    df["보증완료월"] = dt.dt.month

    for c in CAT_COLS:
        df[c] = df[c].astype("category")

    # 파생 비율 (분모 0 방어)
    df["선순위채권비율"] = (df["선순위채권금액"] / df["주택가액"].replace(0, pd.NA)).fillna(0.0)

    # 이상치: 지우거나 윈저화하지 않고 그대로 둔다. dashboard/train_model.py로 이미 학습해 둔
    # 모델도 원본 값 그대로 학습했고(트리 기반이라 극단값에 강건 — modeling 리포트에서 검증됨),
    # 여기서 값을 바꾸면 03에서 그 모델에 넣을 입력이 학습 때와 달라져 버린다.
    # 다만 거래량(03의 Gate 기준)만큼은 극단적으로 낮은 값 자체가 "표본 부족"이라는 신호이므로
    # 절대 건드리지 않는다.

    df.to_parquet(C.CLEAN_PARQUET, index=False)
    print(f"저장: {C.CLEAN_PARQUET} {df.shape}")
    print(f"기간: {dt.min():%Y-%m} ~ {dt.max():%Y-%m}")


if __name__ == "__main__":
    main()
