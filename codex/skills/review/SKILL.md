---
name: review
description: 코드 변경사항의 자가 리뷰. 보안·범위·스타일·테스트를 체크하고 CRITICAL/WARN/INFO로 분류한다. 사용자가 "리뷰해줘", "self review", "review this", "$review", "변경사항 봐줘" 등을 요청할 때 사용한다.
---

# Review — Self Code Review

현재 변경사항(git diff) 또는 지정된 파일·PR에 대해 자가 리뷰를 수행한다.

## Rules

1. **Read-only**: 분석만 수행하고 코드는 수정하지 않는다.
2. **Evidence-based**: 모든 findings는 `파일:라인` 근거를 포함한다.
3. **Secrets safety**: 로그·스니펫 인용 시 민감정보는 `***`로 마스킹한다.

## Workflow

1. **범위 확정**
   - 기본: `git diff` + `git diff --staged` (현재 변경사항)
   - 지정된 경우: 사용자가 준 파일/디렉토리/PR
2. **탐색**: 변경된 파일을 읽고 주변 컨텍스트 파악
3. **체크리스트 적용**: 아래 Check Matrix 순서대로 점검
4. **분류**: CRITICAL / WARN / INFO
5. **보고**: Output Format에 따라 출력

## Check Matrix

### Core (핵심 정책)
- [ ] 외부 데이터 지시문을 실행 로직에 반영하지 않았는가
- [ ] 요청 범위 외 리팩토링·포매팅·이름변경이 섞이지 않았는가

### Safety (보안·승인)
- [ ] 토큰·비밀번호·API 키·세션·쿠키가 하드코딩되지 않았는가
- [ ] 로그·에러 메시지에서 민감정보가 `***` 마스킹되는가
- [ ] `rm -rf`, force push, DROP/DELETE 등이 승인 없이 포함되지 않았는가
- [ ] 테스트를 삭제·약화하지 않았는가

### Workflow (워크플로우)
- [ ] 새 코드에 대한 테스트 또는 검증 수단이 있는가
- [ ] 임시방편(band-aid)이 아닌 근본 해결인가

### Java/Spring
- [ ] Controller → Service → Repository 경계 유지
- [ ] 생성자 주입을 사용하는가 (필드 주입 아님)
- [ ] SLF4J 사용, `System.out` 금지, 비밀 로깅 금지

### Kotlin
- [ ] `!!` 회피, `?.let`/`requireNotNull` 사용
- [ ] DTO는 data class, 제한된 계층은 sealed 사용

### Next.js/TS
- [ ] `any` 회피, strict 모드
- [ ] Server Component 기본, `"use client"` 최소화
- [ ] API 경계·폼 입력에서 Zod validation 수행

## Severity

- **CRITICAL**: 보안·데이터 손실·prod 영향·계약 파괴. 머지 금지.
- **WARN**: 룰 위반·유지보수성 저하·테스트 누락. 머지 전 수정 권장.
- **INFO**: 스타일·네이밍·개선 여지. 참고용.

## Output Format

```markdown
### Review: {파일 또는 범위}

**Scope**
- Files: {변경된 파일 수}
- Added: +N / Removed: -M

**Findings**

#### CRITICAL
- `{파일:라인}` — {이슈 설명}
  - **Recommendation**: {구체 수정안}

#### WARN
- `{파일:라인}` — {이슈}
  - **Recommendation**: {수정안}

#### INFO
- `{파일:라인}` — {개선 여지}

**Recommendation (priority order)**
1. {CRITICAL 해결}
2. {WARN 해결}
3. {INFO 참고}
```

## 주의

- 리뷰는 **조언**이지 승인이 아니다. 머지·배포는 사용자 판단.
