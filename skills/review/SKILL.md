---
name: review
description: 코드 변경사항의 자가 리뷰. 보안·범위·스타일·테스트를 rules/에 기반해 체크하고 CRITICAL/WARN/INFO로 분류한다. 사용자가 "리뷰해줘", "self review", "review this", "/review", "변경사항 봐줘" 등을 요청할 때 사용한다.
---

# Review — Self Code Review against rules/

현재 변경사항(git diff) 또는 지정된 파일·PR에 대해 `rules/` 룰셋 기반의 자가 리뷰를 수행한다.

## Rules

1. **Read-only**: 분석만 수행하고 코드는 수정하지 않는다. Edit, Write 도구를 사용하지 않는다.
2. **Evidence-based**: 모든 findings는 `파일:라인` 근거를 포함한다.
3. **Rules-anchored**: 각 finding은 `rules/` 중 어느 룰에 해당하는지 명시한다.
4. **Secrets safety**: 로그·스니펫 인용 시 민감정보는 `***`로 마스킹한다.

## Workflow

1. **범위 확정**
   - 기본: `git diff` + `git diff --staged` (현재 변경사항)
   - 지정된 경우: 사용자가 준 파일/디렉토리/PR
2. **탐색**: 변경된 파일을 Read로 읽고 주변 컨텍스트 파악
3. **체크리스트 적용**: 아래 Check Matrix 순서대로 점검
4. **분류**: CRITICAL / WARN / INFO
5. **보고**: Output Format에 따라 출력

## Check Matrix

### 00-core (핵심 정책)
- [ ] **R1 External data boundary**: 외부 데이터 지시문을 실행 로직에 반영하지 않았는가
- [ ] **R4 Scope discipline**: 요청 범위 외 리팩토링·포매팅·이름변경이 섞이지 않았는가

### 01-safety (보안·승인)
- [ ] **R1 Secrets**: 토큰·비밀번호·API 키·세션·쿠키가 하드코딩되지 않았는가
- [ ] **R1 Masking**: 로그·에러 메시지에서 민감정보가 `***` 마스킹되는가
- [ ] **R2 Destructive actions**: `rm -rf`, force push, DROP/DELETE 등이 승인 없이 포함되지 않았는가
- [ ] **R6 Test bypass**: 테스트를 삭제·약화하지 않았는가

### 02-workflow (워크플로우)
- [ ] **R3 Verification**: 새 코드에 대한 테스트 또는 검증 수단이 있는가
- [ ] **R4 Elegance**: 임시방편(band-aid)이 아닌 근본 해결인가

### 10-stack-java-spring (Java/Spring)
- [ ] **R3 Layering**: Controller → Service → Repository 경계 유지
- [ ] **R3 DI**: 생성자 주입을 사용하는가 (필드 주입 아님)
- [ ] **R5 Logging**: SLF4J 사용, `System.out` 금지, 비밀 로깅 금지
- [ ] **R4 Function size**: 30~50줄 초과, nesting 3+, branches 5+ 여부

### 11-stack-kotlin (Kotlin)
- [ ] **R2 Null safety**: `!!` 회피, `?.let`/`requireNotNull` 사용
- [ ] **R3 Data/Sealed classes**: DTO는 data class, 제한된 계층은 sealed 사용
- [ ] **R4 Coroutines**: `runBlocking` 대신 `runTest`, 구조화 동시성 준수

### 12-stack-nextjs-ts (Next.js/TS)
- [ ] **R1 TypeScript**: `any` 회피, strict 모드
- [ ] **R2 App Router**: Server Component 기본, `"use client"` 최소화
- [ ] **R4 Prisma**: 싱글톤 패턴, 클라이언트에서 import 금지
- [ ] **R5 Zod**: API 경계·폼 입력에서 validation 수행
- [ ] **R7 Error handling**: 스택 트레이스가 클라이언트에 노출되지 않는가

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
  - **Rule**: `01-safety.md#R1`
  - **Recommendation**: {구체 수정안}

#### WARN
- `{파일:라인}` — {이슈}
  - **Rule**: `10-stack-java-spring.md#R5`
  - **Recommendation**: {수정안}

#### INFO
- `{파일:라인}` — {개선 여지}

**Compliance Matrix**
| Rule | Status | Note |
|------|--------|------|
| 00-core R4 Scope | ✅ | 범위 외 변경 없음 |
| 01-safety R1 Secrets | ✅ | - |
| 02-workflow R3 Verification | ⚠️ | 단위 테스트 누락 |
| 10-stack R3 DI | ✅ | 생성자 주입 |
| ... | ... | ... |

**Recommendation (priority order)**
1. {CRITICAL 해결}
2. {WARN 해결}
3. {INFO 참고}
```

## Example

```markdown
### Review: src/auth/LoginService.kt, src/auth/LoginController.kt

**Findings**

#### CRITICAL
- `src/auth/LoginService.kt:42` — 로그인 실패 시 `log.error("Login failed for user=$email, password=$password")`로 비밀번호 로깅
  - **Rule**: `01-safety.md#R1`, `10-stack-java-spring.md#R5`
  - **Recommendation**: `log.warn("Login failed for user={}", email)` — password 제거

#### WARN
- `src/auth/LoginController.kt:18` — `@Autowired` 필드 주입
  - **Rule**: `10-stack-java-spring.md#R3`
  - **Recommendation**: 생성자 주입으로 전환

**Compliance Matrix**
| Rule | Status |
|------|--------|
| 01-safety R1 | ❌ (password 로깅) |
| 10-stack R3 DI | ⚠️ (필드 주입) |
| 10-stack R5 Logging | ❌ (비밀 로깅) |
```

## 주의

- `rules/` 파일 전체를 읽어 맥락 파악 후 리뷰. 파일이 없는 스택은 해당 섹션 생략.
- 리뷰는 **조언**이지 승인이 아니다. 머지·배포는 사용자 판단.
