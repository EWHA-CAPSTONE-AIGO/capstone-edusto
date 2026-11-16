"""EduSTO 공개 데이터 수집 스크립트 (데이터 구축 단계 ⓪)

외부 라이브러리 없이 표준 라이브러리만 사용합니다. Python 3.9+.

사용법
  # 1) 저장소 루트의 .env 에 키를 넣습니다 (.env.example 참고, 모두 무료 발급)
  #    python-dotenv가 있으면 그것을, 없으면 표준 라이브러리 파서로 .env를 읽습니다.
  #    이미 설정된 환경변수(export ...)가 .env 값보다 우선합니다.
  DART_API_KEY=...    # https://opendart.fss.or.kr  (인증키 신청)
  NEIS_API_KEY=...    # https://open.neis.go.kr     (인증키 신청)
  ECOS_API_KEY=...    # https://ecos.bok.or.kr/api/  (인증키 신청)
  KOSIS_API_KEY=...   # https://kosis.kr/openapi    (활용신청)

  # 2) 필요한 것만 실행합니다
  python collect_public_data.py dart --years 2023 2024 2025 2026
  python collect_public_data.py neis --region B10 --kind 고등학교 --schools 20 --from 20250301 --to 20260228
  python collect_public_data.py ecos --from 20200101 --to 20261115
  python collect_public_data.py kosis --org 101 --tbl <통계표ID> --prd Y --start 2015 --end 2025
  python collect_public_data.py summarize            # data/raw 아래 CSV의 행 수·기간 요약 → manifest.csv
  python collect_public_data.py manual               # 로그인/약관 동의가 필요한 데이터 안내 출력

어느 폴더에서 실행해도 결과는 <저장소 루트>/data/raw/<출처>/ 에 저장되고, summarize 결과(data/manifest.csv)를
중간발표 슬라이드 8의 "확보 현황" 표로 그대로 쓸 수 있습니다.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# 실행 위치와 상관없이 저장소 루트(scripts/의 상위 폴더)를 기준으로 경로를 잡습니다.
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.csv"


def load_env(path: Path = ROOT / ".env") -> None:
    """.env 파일을 읽어 환경변수로 넣습니다. 이미 있는 환경변수는 덮어쓰지 않습니다."""
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(path, override=False)
        return
    except ImportError:
        pass
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if v[:1] in ("'", '"') and v[-1:] == v[:1] and len(v) >= 2:
            v = v[1:-1]
        elif " #" in v or "\t#" in v:  # 따옴표 없는 값 뒤의 주석 제거
            v = v.split("#", 1)[0].strip()
        elif v.startswith("#"):
            v = ""
        if k and v and k not in os.environ:
            os.environ[k] = v

# 상장 교육사 (종목코드) — 유형별 계절성 실측 비교용
EDU_COMPANIES = {
    "메가스터디교육": "215200",   # B 입시형 비중 큼
    "디지털대성": "068930",       # B 입시형
    "아이스크림에듀": "289010",   # A 학년진급형(초등 구독)
    "웅진씽크빅": "095720",       # A 학년진급형
    "대교": "019680",             # A 학년진급형
    "비상교육": "100220",         # A·B 혼합
    "YBM넷": "057030",            # C 어학·자격
}
# 보고서 코드: 1분기, 반기, 3분기, 사업보고서
REPRT = {"11013": "Q1", "11012": "H1", "11014": "Q3", "11011": "FY"}


def http_get(url: str, params: dict | None = None, retries: int = 3) -> bytes:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"요청 실패: {url[:120]}... ({last})")


def need_key(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"[중단] {name} 가 없습니다. 저장소 루트의 .env 에 키를 넣으세요 (.env.example 참고).")
    return v


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        print(f"  (빈 결과) {path}")
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"  저장: {path} ({len(rows)}행)")


def to_int(s: str | None) -> int | None:
    if s in (None, "", "-"):
        return None
    try:
        return int(str(s).replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------- OpenDART
def dart_corp_codes(key: str) -> dict[str, str]:
    """종목코드 → 고유번호(corp_code) 매핑."""
    blob = http_get("https://opendart.fss.or.kr/api/corpCode.xml", {"crtfc_key": key})
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        xml_bytes = z.read(z.namelist()[0])
    out = {}
    for el in ET.fromstring(xml_bytes).iter("list"):
        stock = (el.findtext("stock_code") or "").strip()
        if stock:
            out[stock] = el.findtext("corp_code")
    return out


REVENUE_NAMES = ("매출액", "수익(매출액)", "영업수익", "매출")
# 013 = 조회된 데이터 없음(아직 공시 전 등). 그 밖의 코드는 키·한도 문제이므로 중단합니다.
DART_FATAL = {"010": "등록되지 않은 키", "011": "사용할 수 없는 키", "012": "접근할 수 없는 IP",
              "020": "요청 제한 초과", "800": "시스템 점검", "900": "정의되지 않은 오류",
              "901": "개인정보 보유기간 만료 키"}


def dart_revenue(key: str, corp_code: str, year: int, reprt: str) -> dict | None:
    """연결(CFS) 손익계산서 매출을 찾고, 연결재무제표가 없으면 별도(OFS)로 다시 찾습니다."""
    for fs_div in ("CFS", "OFS"):
        data = json.loads(http_get(
            "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
            {"crtfc_key": key, "corp_code": corp_code, "bsns_year": year,
             "reprt_code": reprt, "fs_div": fs_div},
        ))
        st = data.get("status")
        if st in DART_FATAL:
            sys.exit(f"[OpenDART 오류 {st}] {DART_FATAL[st]}: {data.get('message')}")
        if st != "000":
            continue
        for it in data.get("list", []):
            if it.get("sj_div") not in ("IS", "CIS"):
                continue
            if (it.get("account_id") == "ifrs-full_Revenue"
                    or it.get("account_nm", "").replace(" ", "") in REVENUE_NAMES):
                return {"amount": to_int(it.get("thstrm_amount")),
                        "cum": to_int(it.get("thstrm_add_amount")), "fs_div": fs_div}
    return None


def cmd_dart(a):
    key = need_key("DART_API_KEY")
    codes = dart_corp_codes(key)
    rows = []
    for name, stock in EDU_COMPANIES.items():
        cc = codes.get(stock)
        if not cc:
            print(f"  [건너뜀] {name}({stock}) 고유번호 없음")
            continue
        for y in a.years:
            got = {}
            for rc, label in REPRT.items():
                got[label] = dart_revenue(key, cc, y, rc)
                time.sleep(0.3)
            q1 = got["Q1"] and got["Q1"]["amount"]
            q2 = got["H1"] and got["H1"]["amount"]   # 반기보고서 당기 3개월
            q3 = got["Q3"] and got["Q3"]["amount"]
            cum9 = got["Q3"] and got["Q3"]["cum"]
            fy = got["FY"] and got["FY"]["amount"]
            q4 = fy - cum9 if (fy and cum9) else None
            fs = next((g["fs_div"] for g in got.values() if g), None)
            for q, v in (("Q1", q1), ("Q2", q2), ("Q3", q3), ("Q4", q4)):
                rows.append({"company": name, "stock_code": stock, "year": y,
                             "quarter": q, "revenue_krw": v, "fs_div": fs})
            print(f"  {name} {y}: {[q1, q2, q3, q4]}")
    write_csv(RAW / "opendart" / "edu_quarterly_revenue.csv", rows)


# ---------------------------------------------------------------- NEIS 학사일정
def neis_rows(res: dict, svc: str) -> list[dict]:
    """NEIS 응답에서 row 목록을 꺼냅니다. INFO-200(데이터 없음)은 빈 목록, 그 밖의 오류는 중단."""
    if svc not in res:
        r = res.get("RESULT", {})
        if r.get("CODE") == "INFO-200":
            return []
        sys.exit(f"[NEIS 오류] {r.get('CODE')}: {r.get('MESSAGE')}")
    return res[svc][1].get("row", [])


def cmd_neis(a):
    key = need_key("NEIS_API_KEY")
    base = "https://open.neis.go.kr/hub/"
    info = json.loads(http_get(base + "schoolInfo", {
        "KEY": key, "Type": "json", "pIndex": 1, "pSize": a.schools,
        "ATPT_OFCDC_SC_CODE": a.region, "SCHUL_KND_SC_NM": a.kind}))
    schools = neis_rows(info, "schoolInfo")
    rows = []
    for s in schools:
        res = json.loads(http_get(base + "SchoolSchedule", {
            "KEY": key, "Type": "json", "pIndex": 1, "pSize": 1000,
            "ATPT_OFCDC_SC_CODE": a.region, "SD_SCHUL_CODE": s["SD_SCHUL_CODE"],
            "AA_FROM_YMD": a.from_, "AA_TO_YMD": a.to}))
        for r in neis_rows(res, "SchoolSchedule"):
            rows.append({"school": s["SCHUL_NM"], "kind": a.kind, "date": r.get("AA_YMD"),
                         "event": r.get("EVENT_NM"), "grade_flags": "".join(
                             r.get(f"{g}_GRADE_EVENT_YN", "") or "" for g in
                             ("ONE", "TW", "THREE", "FR", "FIV", "SIX"))})
        time.sleep(0.2)
    write_csv(RAW / "neis" / f"school_schedule_{a.region}_{a.kind}.csv", rows)
    print("  다음 단계: event 이름에 '방학', '개학', '고사', '시험'이 들어간 날짜를 월별로 세면 계절성 변수가 됩니다.")


# ---------------------------------------------------------------- ECOS 금리
def cmd_ecos(a):
    key = need_key("ECOS_API_KEY")
    # 시장금리(일별) 통계표 817Y002, 국고채 3년 010200000 (5년 010200001). 2026-11-16 StatisticItemList로 확인.
    url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/1/100000/"
           f"{a.stat}/D/{a.from_}/{a.to}/{a.item}")
    data = json.loads(http_get(url))
    rows = [{"date": r["TIME"], "item": r.get("ITEM_NAME1"), "rate_pct": r["DATA_VALUE"]}
            for r in data.get("StatisticSearch", {}).get("row", [])]
    write_csv(RAW / "ecos" / f"rate_{a.stat}_{a.item}.csv", rows)


# ---------------------------------------------------------------- KOSIS
def cmd_kosis(a):
    key = need_key("KOSIS_API_KEY")
    # 통계표 ID(tblId)는 KOSIS 통계표 검색 API(statisticsSearch.do)나 통계표 화면 URL에서 확인합니다.
    # 표마다 분류 단계 수가 달라(사교육비 1단계, 추계인구 3단계) 메타 정보로 단계 수를 먼저 셉니다.
    # 없는 단계를 넘기면 err 21, 있는 단계를 빠뜨리면 err 20이 납니다.
    meta = json.loads(http_get(
        "https://kosis.kr/openapi/statisticsData.do",
        {"method": "getMeta", "type": "ITM", "apiKey": key, "format": "json", "jsonVD": "Y",
         "orgId": a.org, "tblId": a.tbl}))
    if isinstance(meta, dict) and meta.get("err"):
        sys.exit(f"[KOSIS 메타 오류] {meta}")
    levels = len({r["OBJ_ID"] for r in meta if r.get("OBJ_ID") != "ITEM"})
    params = {"method": "getList", "apiKey": key, "format": "json", "jsonVD": "Y",
              "orgId": a.org, "tblId": a.tbl, "prdSe": a.prd,
              "startPrdDe": a.start, "endPrdDe": a.end, "itmId": "ALL"}
    params.update({f"objL{i}": "ALL" for i in range(1, levels + 1)})
    data = json.loads(http_get("https://kosis.kr/openapi/Param/statisticsParameterData.do", params))
    if isinstance(data, dict) and data.get("err"):
        sys.exit(f"[KOSIS 오류] {data}")
    write_csv(RAW / "kosis" / f"{a.org}_{a.tbl}.csv", data)


# ---------------------------------------------------------------- 요약 (manifest)
DATE_HINTS = ("date", "time", "ymd", "transaction_date", "membership_expire_date", "year",
              "prd_de")  # prd_de: KOSIS 수록 시점


def _num(v: str) -> float | None:
    try:
        return float(v)
    except ValueError:
        return None


def cmd_summarize(_a):
    rows = []
    for p in sorted(RAW.rglob("*.csv")):
        n, lo, hi, col = 0, None, None, None
        with p.open(encoding="utf-8-sig", errors="ignore") as f:
            rd = csv.reader(f)
            header = next(rd, [])
            idx = next((i for i, h in enumerate(header)
                        if any(k in h.lower() for k in DATE_HINTS)), None)
            col = header[idx] if idx is not None else None
            for r in rd:
                n += 1
                if idx is not None and idx < len(r) and r[idx] not in ("", "?", "NA"):
                    v = r[idx]
                    # 숫자 열(OULAD 상대 일수 등)은 숫자로, 그 밖에는 문자열로 비교합니다.
                    key = _num(v)
                    key = (0, key, v) if key is not None else (1, 0.0, v)
                    lo = key if lo is None or key < lo else lo
                    hi = key if hi is None or key > hi else hi
        lo_v, hi_v = (lo[2] if lo else None), (hi[2] if hi else None)
        rows.append({"file": p.relative_to(ROOT).as_posix(), "rows": n, "period_column": col,
                     "from": lo_v, "to": hi_v,
                     "summarized_at": datetime.now().strftime("%Y-%m-%d %H:%M")})
        print(f"  {p.relative_to(ROOT)}: {n:,}행 {col or ''} {lo_v or ''} ~ {hi_v or ''}")
    write_csv(MANIFEST, rows)


def cmd_manual(_a):
    print("""로그인·약관 동의가 필요해 스크립트로 받지 않는 데이터
- KKBox: kaggle 계정에서 대회 규칙 동의 후
    kaggle competitions download -c kkbox-churn-prediction-challenge -p data/raw/kkbox
  (대안) Mendeley Data 사본 transactions_v2: https://data.mendeley.com/datasets/mv3f8bdrvy/1
         CC BY 4.0. 단 1,048,575행에서 잘린 사본이라 임시 표본으로만 씁니다 (docs/data_plan.md 참고)
- EdNet KT4: https://github.com/riiid/ednet 의 KT4 링크 (CC BY-NC 4.0, 연구용) → data/raw/ednet
- OULAD: https://archive.ics.uci.edu/dataset/349 (CC BY 4.0) → data/raw/oulad 에 압축 해제
- KDD Cup 2015: https://data-mining.philippe-fournier-viger.com/?p=1074 → data/raw/kddcup2015
- Q-Net: 공공데이터포털에서 '한국산업인력공단' 검색 → 활용신청(시험일정·종목 목록)
- 교육기본통계·수능 지원 현황·9급 통계: 각 기관 누리집의 엑셀/PDF 첨부 → data/raw/stats
받은 뒤 `python collect_public_data.py summarize` 를 실행하면 행 수·기간이 manifest.csv에 정리됩니다.""")


def main():
    ap = argparse.ArgumentParser(description="EduSTO 공개 데이터 수집")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dart"); d.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    n = sub.add_parser("neis")
    n.add_argument("--region", default="B10", help="시도교육청 코드 (B10=서울)")
    n.add_argument("--kind", default="고등학교", choices=["초등학교", "중학교", "고등학교"])
    n.add_argument("--schools", type=int, default=20)
    n.add_argument("--from", dest="from_", default="20250301")
    n.add_argument("--to", default="20260228")
    e = sub.add_parser("ecos")
    e.add_argument("--stat", default="817Y002"); e.add_argument("--item", default="010200000")
    e.add_argument("--from", dest="from_", default="20200101"); e.add_argument("--to", default="20261115")
    k = sub.add_parser("kosis")
    k.add_argument("--org", required=True); k.add_argument("--tbl", required=True)
    k.add_argument("--prd", default="Y"); k.add_argument("--start", default="2015"); k.add_argument("--end", default="2025")
    sub.add_parser("summarize"); sub.add_parser("manual")
    a = ap.parse_args()
    load_env()
    {"dart": cmd_dart, "neis": cmd_neis, "ecos": cmd_ecos, "kosis": cmd_kosis,
     "summarize": cmd_summarize, "manual": cmd_manual}[a.cmd](a)


if __name__ == "__main__":
    main()
