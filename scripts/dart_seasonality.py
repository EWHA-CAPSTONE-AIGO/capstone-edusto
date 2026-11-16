"""OpenDART 교육사 분기 매출로 유형별 계절성을 비교합니다.

입력: data/raw/opendart/edu_quarterly_revenue.csv  (collect_public_data.py dart 결과)
출력: data/interim/opendart_seasonality.csv + 화면에 마크다운 표

계산 (규칙 기반, 같은 입력이면 같은 결과)
- 분기 비중 = 분기 매출 / 그 해 4개 분기 합. 4개 분기가 모두 있는 해만 씁니다.
- 회사별로 연도 평균 분기 비중, 최고·최저 분기, 진폭(최고 − 최저 비중, %p)을 냅니다.
- 유형 평균은 회사별 평균 비중의 단순 평균입니다(매출 규모 가중 아님).

사용법: python scripts/dart_seasonality.py
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "raw" / "opendart" / "edu_quarterly_revenue.csv"
OUT = ROOT / "data" / "interim" / "opendart_seasonality.csv"

TYPE_OF = {
    "아이스크림에듀": "A", "웅진씽크빅": "A", "대교": "A",
    "메가스터디교육": "B", "디지털대성": "B",
}
QS = ("Q1", "Q2", "Q3", "Q4")


def main() -> None:
    if not SRC.exists():
        sys.exit(f"[중단] {SRC.relative_to(ROOT)} 가 없습니다. 먼저 collect_public_data.py dart 를 실행하세요.")
    rev: dict[str, dict[int, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    with SRC.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["company"] in TYPE_OF and r["revenue_krw"]:
                rev[r["company"]][int(r["year"])][r["quarter"]] = int(float(r["revenue_krw"]))

    rows, by_type = [], defaultdict(list)
    for co in TYPE_OF:
        years = sorted(y for y, q in rev[co].items() if all(k in q for k in QS))
        if not years:
            print(f"  [건너뜀] {co}: 4개 분기가 모두 있는 해가 없습니다.")
            continue
        share = {q: sum(rev[co][y][q] / sum(rev[co][y].values()) for y in years) / len(years)
                 for q in QS}
        peak, low = max(share, key=share.get), min(share, key=share.get)
        row = {"type": TYPE_OF[co], "company": co, "years": f"{years[0]}-{years[-1]}",
               **{f"{q}_share_pct": round(share[q] * 100, 1) for q in QS},
               "peak": peak, "low": low,
               "amplitude_pp": round((share[peak] - share[low]) * 100, 1)}
        rows.append(row)
        by_type[TYPE_OF[co]].append(share)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print("| 유형 | 회사 | 연도 | Q1 | Q2 | Q3 | Q4 | 최고 | 최저 | 진폭(%p) |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['type']} | {r['company']} | {r['years']} | "
              + " | ".join(f"{r[f'{q}_share_pct']}%" for q in QS)
              + f" | {r['peak']} | {r['low']} | {r['amplitude_pp']} |")
    for t, shares in sorted(by_type.items()):
        avg = {q: sum(s[q] for s in shares) / len(shares) for q in QS}
        print(f"| {t} 평균 | ({len(shares)}개사) | | "
              + " | ".join(f"{avg[q] * 100:.1f}%" for q in QS)
              + f" | {max(avg, key=avg.get)} | {min(avg, key=avg.get)} | "
              f"{(max(avg.values()) - min(avg.values())) * 100:.1f} |")

    # 연도별 원 매출(억 원)도 함께 보여 줍니다 (불완전 연도 포함).
    print("\n분기 매출(억 원)")
    for co in TYPE_OF:
        for y in sorted(rev[co]):
            vals = [rev[co][y].get(q) for q in QS]
            print(f"  {co} {y}: " + " · ".join(
                f"{q} {v / 1e8:,.0f}" if v else f"{q} -" for q, v in zip(QS, vals)))
    print(f"\n저장: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
