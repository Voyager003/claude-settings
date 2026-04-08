---
name: debug
description: 체계적 디버깅 워크플로 (로그 → 재현 → 가설 → 증거 → Next action). rules/02-workflow.md R2 "Investigation First, then STOP" 프로세스를 강제한다. 사용자가 "디버그", "버그 찾아줘", "왜 안 돼?", "에러 해결", "/debug" 등을 요청할 때 사용한다.
---

# Debug — Investigation-First Debugging Workflow

증상을 보고 바로 수정에 들어가지 않고 **Log → Repro → Hypothesis → Evidence → Next action** 순서로 원인을 규명한다. `rules/02-workflow.md` R2 프로세스를 그대로 따른다.

## Rules

1. **Read-only (기본)**: 조사 단계에서는 코드를 수정하지 않는다. Edit, Write 사용 금지.
2. **수정은 별도 단계**: 원인이 명확해진 후에만, 사용자 승인을 받아 별도로 수정한다.
3. **Evidence 없으면 STOP**: 가설을 뒷받침할 증거(로그·재현·코드 경로)가 없으면 STOP & Re-plan한다.
4. **Secrets masking**: 로그 인용 시 토큰·비밀·PII는 `***` 마스킹.
5. **근본 원인 우선**: 증상을 숨기는 band-aid 대신 root cause를 찾는다.

## Workflow

### 1. 증상 파악 (Symptom)
- 사용자가 본 현상을 한 문장으로 재진술
- 예상 동작 vs 실제 동작
- 재현 가능한지, 간헐적인지

### 2. Log Summary (Masked)
- 관련 로그·스택트레이스·에러 메시지 수집
- 민감정보 `***` 마스킹 후 핵심 부분만 발췌
- 타임스탬프·컴포넌트·레벨 포함

### 3. Minimal Reproduction
- 가장 작은 재현 시나리오 구성
- 가능하면 실패하는 테스트로 재현
- 환경 의존성(OS, 버전, 설정) 기록

### 4. Hypothesis + Evidence
- 가설을 명시적 문장으로 기술
- 뒷받침 증거: 코드 경로(`파일:라인`), 로그, 재현 결과
- 여러 가설이 있다면 우선순위 표시
- 반증 가능성도 고려

### 5. Next Action
둘 중 하나만 선택:
- **Fix proposal**: 구체적 변경안 + 영향 범위 + 테스트 계획 (수정은 별도 단계)
- **STOP & Ask**: 필요한 추가 정보(로그·권한·재현 환경)를 1~3개 질문으로 요청

## STOP 조건 (rules/02-workflow.md R2)

다음 중 하나라도 해당하면 진단을 멈추고 사용자에게 넘긴다:
- 원인 가설이 여러 개고 증거로 좁힐 수 없음
- 승인 필요 액션(DB 수정·prod 접근·파괴적 명령) 필요
- 필수 증거(로그·실패 테스트·재현 환경) 부재

## Output Format

```markdown
### Investigation: {증상 한 줄 요약}

**1. Symptom**
- Expected: {기대 동작}
- Actual: {실제 동작}
- Reproducible: {항상 / 간헐적 / 알 수 없음}

**2. Log summary (masked)**
```
{타임스탬프} {level} {component} — {메시지}
{스택트레이스 발췌, *** 마스킹}
```
- 출처: `{로그 파일 또는 명령}`

**3. Minimal reproduction**
```bash
{재현 명령 또는 테스트 코드}
```
- 환경: {OS/버전/설정}

**4. Hypothesis + evidence**
- **H1 (가장 가능성 높음)**: {가설 문장}
  - Evidence: `{파일:라인}` — {왜 이 코드가 근거인지}
  - Evidence: {로그 라인 또는 재현 결과}
- **H2 (대안)**: {가설} — {증거 부족 / 가능성 낮음 이유}

**5. Next action**
- [ ] **Fix proposal** (승인 후 별도 단계):
  - Change: `{파일:라인}` — {변경 내용}
  - Impact: {영향 범위}
  - Test: {검증 방법}
- [ ] 또는 **STOP & Ask**:
  1. {필요한 질문 1}
  2. {필요한 질문 2}
```

## Example

사용자: "어제부터 로그인이 간헐적으로 500 나는데 왜 그래?"

```markdown
### Investigation: 로그인 API 간헐적 500 발생

**1. Symptom**
- Expected: POST /api/auth/login → 200 (valid) 또는 401 (invalid)
- Actual: 약 10% 요청에서 500 반환
- Reproducible: 간헐적 (피크 시간대 집중)

**2. Log summary (masked)**
```
2026-04-08 14:32:11 ERROR AuthService — org.hibernate.exception.JDBCConnectionException:
  unable to acquire JDBC Connection
  at ...HikariPool.getConnection(...)
User: u***@example.com
```
- 출처: `logs/app.log`

**3. Minimal reproduction**
- 부하: 동시 30 request로 로그인 호출 → 3~4건 500 관찰
```bash
ab -n 100 -c 30 -p login.json http://localhost:8080/api/auth/login
```

**4. Hypothesis + evidence**
- **H1 (유력)**: HikariCP 커넥션 풀 고갈
  - Evidence: `application.yml:23` — `maximum-pool-size: 10` (낮음)
  - Evidence: `AuthService.kt:48` — 로그인마다 `userRepository.findByEmail()` + `sessionRepository.save()` + `auditRepository.log()` 총 3회 DB 호출
  - Evidence: 로그의 "unable to acquire JDBC Connection"
- **H2**: DB 자체 슬로우 쿼리 — 가능성 낮음 (DB 메트릭 상 p99 < 20ms)

**5. Next action**
- [ ] **Fix proposal** (승인 후 별도 단계):
  - Change: `application.yml:23` — `maximum-pool-size: 10 → 30`
  - Change: `AuthService.kt:48` — audit 로깅을 async로 분리
  - Impact: 로그인 latency 감소, 커넥션 경합 완화
  - Test: 동일 부하 재현 후 에러율 확인
```

## 주의

- `rules/02-workflow.md R2`를 그대로 구현한 워크플로이다. 임의로 생략하지 않는다.
- **"fix를 먼저 해볼게"**는 금지. 반드시 1→2→3→4→5 순서로 진행한다.
- 증거가 부족하면 지레짐작 말고 **STOP & Ask**.
