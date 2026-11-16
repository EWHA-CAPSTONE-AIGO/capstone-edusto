# Claude Code 첫 요청 (복사해서 붙여 넣기)

## 준비 (한 번만)
1. 이 폴더의 파일을 팀 저장소 루트에 복사합니다: `CLAUDE.md`, `docs/`, `.env.example`, `.gitignore`, `scripts/collect_public_data.py`
2. `.env.example`을 `.env`로 복사하고, 발급받은 키를 넣습니다.
3. 저장소 폴더에서 Claude Code를 엽니다.

## 첫 요청
```
CLAUDE.md와 docs/data_plan.md를 먼저 읽어 줘.
이번 작업 목표는 중간발표용 "데이터 확보 현황"을 만드는 거야.

1. scripts/collect_public_data.py가 내 환경에서 돌아가는지 확인하고, .env의 키를 읽도록 고쳐 줘 (python-dotenv가 없으면 표준 라이브러리로 .env를 읽게).
2. data_plan.md의 우선순위 "높음" 데이터부터 받아 줘:
   - OpenDART 교육사 분기 매출 (2023~2026)
   - NEIS 학사일정 (서울 초·중·고 각 20개교, 2025.3~2026.2)
   - KKBox 거래 테이블 (Kaggle이 안 되면 Mendeley 사본)
   - OULAD
3. 오류가 나면 원인을 찾아 고치고 다시 실행해 줘. 확인이 안 되는 값(통계 코드, URL)은 추측하지 말고 나에게 물어봐.
4. 마지막에 summarize를 실행해서 data/manifest.csv를 만들고, 중간발표 슬라이드에 넣을 수 있게 "데이터 | 행 수 | 기간 | 용도" 표를 마크다운으로 정리해 줘.
5. OpenDART 분기 매출로 회사별 분기 매출 추이를 비교해서, 유형 A(아이스크림에듀·웅진씽크빅·대교)와 유형 B(메가스터디교육·디지털대성)의 계절성 차이를 한 문단으로 요약해 줘.

원본 데이터와 .env는 커밋하지 마.
```

## 다음 요청 (데이터 확보 후)
```
docs/data_plan.md의 3~4절대로 진행하자.
1. KKBox·OULAD를 F1 CSV 템플릿 v0으로 변환하는 스크립트를 scripts/에 만들어 줘.
2. 유형 A·B·D의 준실데이터 v0을 만들고, 검수 체크리스트 항목을 자동으로 확인하는 리포트를 출력해 줘.
3. 결과는 data/synthetic/v0/에 생성 조건과 함께 저장해 줘.
```
