"""
구버전 fetch_realprice.py(진행기록 없음)로 이미 완료한 raw_transactions.csv에서
진행기록 파일(<out>.progress.csv)을 역산해서 만든다.

(시도, api_type, 연월) 조합이 raw_transactions.csv에 행으로 실제 존재할 때만 'ok'로 표시한다.
행이 없는 조합은 재실행 시 다시 시도하도록 기록을 남기지 않는다.

주의: 이전 버전은 아파트/연립다세대/단독다가구를 무조건 'ok'로 간주했었는데,
실제로는 인천/광주/전남처럼 이 3개 API도 전부 실패한 시도가 있어서 그 가정은 틀렸다.
데이터가 큰 도시인데 특정 (시도,api_type,월) 조합에 행이 0건이면 거의 항상 수집 실패이지,
진짜 거래 0건인 경우는 아주 드물다고 보고 전부 재시도 대상으로 남긴다.

사용법:
    python bootstrap_progress.py --raw raw_transactions.csv --start 202201 --end 202412 --out raw_transactions.csv
    (이후 python fetch_realprice.py --start 202201 --end 202412 --out raw_transactions.csv 를
     그대로 재실행하면 비어있는 조합만 재수집된다)
"""
import argparse
import csv
import os

import pandas as pd

from fetch_realprice import month_range
from house_type_map import API_TYPES
from lawd_codes import LAWD_CODES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="raw_transactions.csv")
    parser.add_argument("--start", default="202201")
    parser.add_argument("--end", default="202412")
    parser.add_argument("--out", default="raw_transactions.csv", help="fetch_realprice.py 의 --out 과 동일한 값")
    args = parser.parse_args()

    df = pd.read_csv(args.raw, encoding="utf-8-sig", dtype=str)
    df["deal_ymd"] = df["deal_year"].astype(str).str.zfill(4) + df["deal_month"].astype(str).str.zfill(2)
    have_rows = set(zip(df["sido"], df["api_type"], df["deal_ymd"]))

    months = list(month_range(args.start, args.end))
    progress_path = args.out + ".progress.csv"

    n_ok, n_pending = 0, 0
    with open(progress_path, "w", newline="", encoding="utf-8-sig") as pf:
        writer = csv.DictWriter(pf, fieldnames=["sido", "api_type", "deal_ymd", "status"])
        writer.writeheader()
        for sido in LAWD_CODES:
            for deal_ymd in months:
                for api_type in API_TYPES:
                    if (sido, api_type, deal_ymd) in have_rows:
                        writer.writerow({"sido": sido, "api_type": api_type, "deal_ymd": deal_ymd, "status": "ok"})
                        n_ok += 1
                    else:
                        n_pending += 1

    print(f"{progress_path} 생성 완료: ok {n_ok}건, 재수집 대상(미기록) {n_pending}건")
    print("이제 fetch_realprice.py를 동일한 --out으로 다시 실행하면 위 미기록 조합만 재시도합니다.")


if __name__ == "__main__":
    main()
