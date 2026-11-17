# EduSTO

구독형 에듀테크 기업의 결제·정산 기록에서 실제 반복 매출을 가려내고, 교육 서비스 특유의 이탈 구조를 반영해, 매출 연동 수익권의 가치와 근거를 담은 **STO 발행 사전 심사 패키지**를 생성하는 웹 서비스입니다.



### 1. 브랜치 전략

```
main ← develop ← feature/#이슈번호-페이지-작업설명-타입
main ← hotfix/#이슈번호-페이지-작업설명  (병합 후 develop에도 반영)
```

| 브랜치 | 용도 |
| --- | --- |
| `main` | 배포용 (프로덕션). 배포할 때만 `develop` → `main` PR로 갱신 |
| `develop` | 개발 통합 브랜치, **저장소 기본(default) 브랜치** |
| `feature/*` | 기능 개발 브랜치 (`develop`에서 분기 → `develop`으로 PR) |
| `hotfix/*` | 배포본 긴급 수정 브랜치 (`main`에서 분기 → `main`으로 PR → `main`을 `develop`에 병합) |

- `main`과 `develop`에는 **직접 push 금지**, PR을 통해서만 병합합니다.
- 작업 시작 전에 `develop`을 최신으로 받은 뒤 분기합니다.

```
git switch develop
git pull origin develop
git switch -c feature/#이슈번호-페이지-작업설명-타입
```

### 2. 브랜치 네이밍

**구조**

```
feature/#이슈번호-페이지-작업설명-타입
```

**타입 종류**

| 타입 | 설명 |
| --- | --- |
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `refactor` | 코드 리팩토링 |
| `design` | UI / 퍼블리싱 작업 |
| `chore` | 설정, 환경, 잡일 |
| `hotfix` | 긴급 수정 |

**예시**

```
feature/#9-goal-detail-ui-design
feature/#12-login-api-feat
feature/#21-reservation-modal-fix
```

**규칙**

- 페이지명은 영어 소문자로 통일 (`login`, `mypage`, `main`, `common`)
- 작업설명은 영어로 통일
- 공통 작업은 페이지명에 `common` 사용

### 3. 커밋 메시지

**구조**

```
타입: 작업 내용 [#이슈번호]
```

**예시**

```
Feat: 로그인 페이지 구현 [#7]
Fix: 프로필 이미지 업로드 오류 수정 [#12]
Refactor: 예약 API 호출 구조 변경 [#21]
Design: 회원가입 폼 UI 퍼블리싱 [#33]
Chore: pnpm 마이그레이션 [#45]
```

**규칙**

- 제목은 50자 이내로 간결하게
- 본문이 필요하면 한 줄 띄고 작성
- 타입은 브랜치 타입과 동일하게 사용

### 4. PR (Pull Request)

**제목 구조**

```
타입: 작업 내용
```

**예시**

```
Feat: 카카오 소셜 로그인 추가
Fix: 프로필 이미지 업로드 오류 수정
```

**본문**

PR을 열면 [`.github/pull_request_template.md`](.github/pull_request_template.md) 템플릿이 자동으로 채워집니다.

```markdown
## 📌 관련 이슈
- #1
- Close #1

## 📝 작업 내용
- 카카오 소셜 로그인 기능 추가
- 로그인 후 리다이렉트 처리

## 📸 스크린샷 (선택)
<!-- UI 변경이 있을 경우 첨부 -->

## ✅ 체크리스트
- [ ] 코드 리뷰 요청
- [ ] 테스트 완료
- [ ] 불필요한 console.log / print 제거
```

**규칙**

- `feature/*` PR의 대상(base) 브랜치는 `develop`입니다. 기본 브랜치가 `develop`이라 PR을 열면 자동으로 선택됩니다
- 배포 PR은 `develop` → `main`, 제목은 `Release: 배포 내용`으로 씁니다
- PR 제목에 이슈 키를 포함하면 PR 상태 자동 추적
- 본문에 `Close #이슈번호`를 적으면 기본 브랜치(`develop`)에 병합될 때 이슈가 자동으로 닫힙니다

### 5. 이슈

작업은 이슈를 먼저 만들고 시작합니다. 이슈 번호는 브랜치 이름과 커밋 메시지에 그대로 씁니다.

GitHub에서 **New issue**를 누르면 아래 템플릿 중 하나를 고를 수 있습니다.

| 템플릿 | 파일 | 제목 구조 |
| --- | --- | --- |
| ✨ 기능 요청 | [`.github/ISSUE_TEMPLATE/feature.md`](.github/ISSUE_TEMPLATE/feature.md) | `Feat: 작업 내용` |
| 🐞 버그 제보 | [`.github/ISSUE_TEMPLATE/bug.md`](.github/ISSUE_TEMPLATE/bug.md) | `Fix: 작업 내용` |

**규칙**

- API 키나 실제 기업 매출·재무 자료는 이슈에 붙여 넣지 않습니다
