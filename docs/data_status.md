# 데이터 확보 현황 (중간발표 슬라이드 8)

기준일 2026-11-16. 행 수·기간은 `python scripts/collect_public_data.py summarize` 결과(`data/manifest.csv`)에서 옮겼습니다.

| 데이터 | 행 수 | 기간 | 용도 |
| --- | --- | --- | --- |
| KKBox 거래 (Mendeley 사본 transactions_v2) | 1,048,575 (사용자 906,706명) | 2015-01-01 ~ 2017-03-31 (2017-03이 78.4만 행) | F1 신규·갱신·해지 분류 규칙, 준실데이터 뼈대 (A·B·D). 잘린 사본이라 임시 표본 |
| OULAD studentRegistration | 32,593 | 2013B ~ 2014J 4개 학기 (개강일 기준 −322 ~ +167일) | 과정 종료형 이탈, F4 검증 (B·C) |
| OULAD studentInfo | 32,593 (학생 28,785명) | 2013B ~ 2014J | 최종 결과(합격·불합격·중도 포기 10,156건)로 종료 vs 해지 구분 |
| OULAD studentVle 외 5개 표 | 10,655,280 (studentVle) 등 | 2013B ~ 2014J | 이용 활동량 → 이탈 전조 보조 지표 |
| OpenDART 교육사 분기 매출 | 대기 (API 키 필요) | 2023 ~ 2026 | 유형별 계절성 실측 대조 (A·B·C) |
| NEIS 학사일정 (서울 초·중·고 각 20개교) | 대기 (API 키 필요) | 2025-03 ~ 2026-02 | F3 계절성 변수 (A·B) |
| KKBox 거래 (Kaggle 원본 transactions.csv) | 대기 (Kaggle 계정·대회 규칙 동의 필요) | 2015-01 ~ 2017-02 TODO(확인) | F3 24개월 코호트·백테스트 뼈대 |

라이선스: KKBox Mendeley 사본 CC BY 4.0, OULAD CC BY 4.0 (UCI dataset 349).
