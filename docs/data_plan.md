# 데이터 계획: 수집 → 매핑 → 준실데이터 → 동결

목표: 2026년 12월 2주까지 **데이터셋 v1 동결**, 12월 3주 F1 데모.
중간발표 슬라이드 8에는 `data/manifest.csv`(파일별 행 수·기간)를 그대로 씁니다.

## 1. 수집 대상과 접근 조건

| # | 데이터 | 받는 방법 | 필요한 것 | 쓰는 곳 | 유형 | 우선순위 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | KKBox Churn Prediction | `kaggle competitions download -c kkbox-churn-prediction-challenge` | Kaggle 계정, 대회 규칙 동의 | F1 분류 규칙, F3 백테스트 뼈대 | A·B·D | 높음 |
| 2 | KKBox transactions_v2 사본 | https://data.mendeley.com/datasets/mv3f8bdrvy/1 | 없음 (CC BY 4.0, 2026-11-16 확인). **1,048,575행에서 잘림**(아래 주의) | 1번 대안 | A·B·D | 높음 |
| 3 | OULAD | https://archive.ics.uci.edu/dataset/349 (원래 주소 analyse.kmi.open.ac.uk/open-dataset는 2026-11 현재 OU Analyse 첫 화면으로 이동) | 없음 (CC BY 4.0) | 과정 종료형 이탈, F4 검증 | B·C | 높음 |
| 4 | OpenDART 교육사 분기 매출 | `scripts/collect_public_data.py dart` | `DART_API_KEY` | 유형별 계절성 실측 대조 | A·B·C | 높음 |
| 5 | NEIS 학사일정 | `scripts/collect_public_data.py neis` | `NEIS_API_KEY` | F3 계절성 변수 | A·B | 높음 |
| 6 | EdNet KT4 | https://github.com/riiid/ednet 의 KT4 링크 | Google Drive 다운로드, CC BY-NC 4.0 | 유형 C 구매·이용 패턴 | C | 중간 |
| 7 | KOSIS 사교육비조사·장래인구추계 | `scripts/collect_public_data.py kosis --org --tbl` | `KOSIS_API_KEY`, 통계표 ID TODO(확인) | F2 기준, 모의데이터 분포 | A·B | 중간 |
| 8 | 교육기본통계 학년별 학생 수 | 교육통계서비스 엑셀 | 없음 | F2 모수, 코호트 크기 | A·B | 중간 |
| 9 | 수능·모의평가 지원 현황 | 평가원 보도자료 | 없음 | B 모수 | B | 중간 |
| 10 | KDD Cup 2015 (XuetangX) | https://data-mining.philippe-fournier-viger.com/?p=1074 | 이용 조건 TODO(확인) | 보조 검증 | B·C | 낮음 |
| 11 | ECOS 국고채 금리 | `scripts/collect_public_data.py ecos` | `ECOS_API_KEY`, 통계 코드 817Y002 TODO(확인) | F5 할인율 참고선 | 공통 | 낮음 |
| 12 | Q-Net 시험일정·종목 목록 | 공공데이터포털 활용신청 | `DATA_GO_KR_KEY` | C 종료 시점 | C | 낮음 |
| 13 | 9급 공채 통계 | 사이버국가고시센터 시험 통계 | 없음 | C 모수 | C | 낮음 |
| 14 | 평생학습 참여율 | e-나라지표 / KOSIS | 없음 | D 모수 | D | 낮음 |
| 15 | 앱마켓 지표 | `google-play-scraper` | 스토어 약관 준수 | F2·S2 보조 | 공통 | 낮음 |
| 16 | 듀오링고 분기 공시 | SEC 8-K 주주서한 | 없음 | D 비교 기준 | D | 낮음 |
| 17 | 투자계약증권 증권신고서 사례 | DART 공시 검색 | 없음 | F6 항목 구성 | 공통 | 낮음 |

**KKBox Mendeley 사본 주의 (2026-11-16 확인)**
- 행 수가 정확히 1,048,575(엑셀 최대 행 − 헤더)이고, msno 정렬 순서로 `ZB…`에서 끊깁니다. 소문자로 시작하는 msno 사용자가 빠져 있어 사용자 약 90.7만 명(원본 대비 일부)만 남습니다. 남은 사용자는 거래가 온전하므로 "사용자 무작위 표본"처럼 쓸 수는 있습니다.
- transactions_v2는 원래 2017년 3월 갱신분이 중심인 파일입니다(2017-03 거래 78.4만 행). 24개월 코호트 유지율·백테스트 뼈대에는 Kaggle 원본 `transactions.csv`(2015-01~2017-02 TODO(확인))가 필요합니다.
- SHA-256 `926b9b15…e2ce` (Mendeley 공개 해시와 일치).

## 2. F1 입력 CSV 템플릿 (초안 v0)
결제사 내보내기 형식에 가깝게 잡았습니다. 이름은 팀에서 확정하세요.

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| record_id | str | 원천 행 ID (추적용) |
| user_id | str | 가명 처리된 사용자 ID |
| event_date | date | 결제·해지·환불 발생일 |
| event_type | enum | new / renew / cancel / refund (F1이 판별, 입력은 비어 있어도 됨) |
| plan_id | str | 요금제 |
| plan_period_days | int | 이용 기간(일) |
| list_price | int | 정가(원) |
| paid_amount | int | 실결제액(원), 환불은 음수 |
| is_auto_renew | bool | 자동 갱신 여부 |
| expire_date | date | 이용 만료일 |
| payment_method | str | 결제 수단 |
| settlement_date | date | 정산일 |
| settlement_amount | int | 정산액(원) |
| source_grade | enum | self / witnessed_or_pg / direct_api |
| segment | enum | A / B / C / D |
| grade_or_course | str | 학년·과정 (A: 학년, B: 수능 연도, C: 시험 회차) |
| stage_end_date | date | 학습 단계 종료 예정일 (D는 비움) |

## 3. 원본 → 템플릿 매핑

**KKBox `transactions`**
| KKBox | 템플릿 | 비고 |
| --- | --- | --- |
| msno | user_id | |
| transaction_date | event_date | `%Y%m%d` |
| payment_plan_days | plan_period_days | |
| plan_list_price | list_price | 통화·규모는 M1 사례(월 매출 약 6,000만 원)에 맞춰 환산 |
| actual_amount_paid | paid_amount | |
| is_auto_renew | is_auto_renew | |
| membership_expire_date | expire_date | |
| is_cancel | event_type = cancel | |
| payment_method_id | payment_method | |
| (없음) | settlement_*, source_grade, segment, grade_or_course, stage_end_date | 교육 보정 단계에서 생성 |

**OULAD `studentRegistration`**
| OULAD | 템플릿 | 비고 |
| --- | --- | --- |
| id_student | user_id | |
| code_module + code_presentation | grade_or_course | presentation B=2월 개강, J=10월 개강 |
| date_registration | event_date (new) | 개강일 기준 상대 일수 → 실제 날짜로 변환 |
| date_unregistration | event_date (cancel) | NA = 과정 완료 → stage_end_date로 처리 |

**EdNet KT4**: 사용자별 행동 로그 중 구매 관련 행동을 결제 이벤트로 추출. 타임스탬프는 고정값만큼 이동되어 있으므로 상대 시점만 사용.

## 4. 준실데이터 → 모의데이터 → 검수 → 동결
1. **준실데이터 v0**: KKBox 거래 패턴(갱신 간격, 해지·자동갱신 비율)을 뼈대로, 교육기본통계·사교육비조사로 학년 분포와 학교급 전환 지속률을, NEIS 학사일정으로 계절성을 덧씌웁니다. D는 보정 없이 원본 패턴만 씁니다.
2. **AI 모의데이터**: 유형마다 시나리오 기업 3개(기준·고성장·고이탈)를 생성합니다. 생성 프롬프트와 파라미터를 `data/synthetic/v1/README.md`에 남깁니다.
3. **팀 검수 체크리스트**
   - 학년 분포·학교급 전환율이 공개 통계 범위 안인가
   - 월별 매출 증감이 학사 일정·유형별 계절성과 맞는가 (OpenDART 분기 패턴과 비교)
   - 환불·중복·결제↔정산 차이 케이스가 일정 비율 섞여 있는가 (F1 테스트용)
   - 매출 이력 24개월 이상 / 12~23개월 사례가 모두 있는가
4. **v1 동결**: 파일 해시, seed, 파라미터, 사용한 원본 버전을 기록하고 이후 변경은 v2로만.

## 5. 이미 확인한 공개 통계 (시드 값)
| 지표 | 값 | 기준 |
| --- | --- | --- |
| 유·초·중등 학생 수 | 5,362,281명 (전년 대비 −3.4%) | 2026.4.1 교육기본통계 |
| 초등학생 수 | 2,219,370명 (−5.4%) | 2026.4.1 |
| 초1 / 초6 | 295,507명 / 417,504명 | 2026.4.1 |
| 초·중등 학생 수 전망 | 2030년 331.7만 명 (2025년 대비 −21.4%) | 교육부 |
| 사교육 참여율 | 75.7% (2024년 80.0%) | 2025 사교육비조사 |
| 1인당 월평균 사교육비 | 전체 45.8만 원 / 참여학생 60.4만 원 | 2025 |
| 학교급별 사교육비 총액 | 초 12.2조 / 중 7.6조 / 고 7.8조 원 | 2025 |
| 2027학년도 수능 지원자 | 551,864명, 고3 355,391명, 졸업생 등 20만 명 안팎 | 2026.9 |
| 2026 국가직 9급 | 선발 3,802명 / 출원 108,718명 | 2026.2 |
| 메가스터디교육 분기 매출(억 원) | 1Q25 2,377 · 2Q25 2,010 · 3Q25 2,497 · 4Q25 1,966 · 1Q26 2,365 · 2Q26 2,047 | 잠정실적 공시 |
| 듀오링고 유료 구독자 | 1,150만 명, MAU 대비 9.0% | 2025 3분기 |
