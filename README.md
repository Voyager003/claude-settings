# claude-settings

Claude Code **및 Codex CLI** 커스텀 설정 백업 및 관리.

> 같은 "보안 우선 / 가드레일 일원화" 철학을 두 개의 에이전트 런타임에 동시 적용합니다.

## 특징

- **보안 우선** — 원격 쓰기, PR 생성/머지 등 위험 작업은 guardrail hook으로 차단
- **묻지 않고 판단** — ask(확인 후 허용) 대신 allow/deny로 처리
- **가드레일 일원화** — 모든 차단은 `guardrail.py` 훅 하나에서 처리
- **시크릿 격리** — 토큰은 git-ignored인 `settings.local.json` / `config.local.toml` 에서 머신별 관리
- **이중 타깃 지원** — 동일 정책을 Claude Code(`~/.claude/`)와 Codex CLI(`~/.codex/`) 양쪽에 설치

## Setup

```bash
git clone https://github.com/<your-username>/claude-settings.git
cd claude-settings

# 둘 다 설치 (기본)
./install.sh

# 또는 한 쪽만
./install.sh claude   # Claude Code만
./install.sh codex    # Codex CLI만
```

기존 `~/.claude` / `~/.codex`가 있으면 자동으로 `.bak`에 백업합니다.

### 시크릿 설정

**Claude Code** — `~/.claude/settings.local.json`:

```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "..."
  },
  "enabledPlugins": {}
}
```

**Codex CLI** — 시크릿은 **절대 `config.toml`에 두지 마세요**. 대신:
- `codex login`이 OS 키체인 또는 `~/.codex/auth.json`에 저장
- API 키는 환경변수 (`OPENAI_API_KEY` 등)
- 머신별 오버라이드는 `~/.codex/config.local.toml` (git-ignored)

## Structure

```
.
├── CLAUDE.md                  # Claude Code entry router
├── settings.json              # Claude Code permissions + hooks
├── rules/                     # 공통 룰셋 (두 에이전트가 참조)
│   ├── 00-core.md             # 핵심 정책
│   ├── 01-safety.md           # 보안/승인 규칙
│   ├── 02-workflow.md         # 워크플로
│   ├── 10-stack-java-spring.md # Java/Spring 스타일
│   ├── 11-stack-kotlin.md     # Kotlin 스타일
│   └── 12-stack-nextjs-ts.md  # Next.js/TypeScript 스타일
├── hooks/                     # Claude Code hooks
│   ├── guardrail.py              # 통합 가드레일 (PreToolUse: Bash/Read/Edit/Write)
│   ├── session-start-context.sh  # SessionStart: git 컨텍스트 주입
│   ├── user-prompt-inject.py     # UserPromptSubmit: 날짜·CWD·branch 주입
│   ├── stop-self-check.py        # Stop: FINAL SELF-CHECK 리마인더
│   └── pre-write-secret-scan.py  # PreToolUse(Write/Edit): 내용 기반 시크릿 차단
├── commands/                  # Claude Code 슬래시 커맨드
├── skills/                    # Claude Code 커스텀 스킬
├── scheduled-tasks/           # Claude Code 예약 작업
├── codex/                     # Codex CLI (experimental hooks)
│   ├── AGENTS.md              # Codex entry router (CLAUDE.md 포팅)
│   ├── config.toml            # Codex 설정 (codex_hooks=true, 보안 기본값)
│   ├── hooks.json             # Codex 훅 등록
│   └── hooks/
│       ├── guardrail.py              # Bash-only 가드레일 (Codex 제약)
│       ├── session-start-context.sh  # SessionStart (matcher: startup|resume)
│       ├── user-prompt-inject.py     # UserPromptSubmit
│       └── stop-self-check.py        # Stop (systemMessage 경로)
└── install.sh                 # 양쪽 설치 (./install.sh [both|claude|codex])
```

## Hooks

### Original (in-house)
| Hook | 이벤트 | 타입 | 기능 |
|------|--------|------|------|
| `guardrail.py` | PreToolUse (Bash·Read·Edit·Write) | command | 경로·명령 기반 통합 가드레일 (자기 보호, 직접 편집 필요) |
| `pre-write-secret-scan.py` | PreToolUse (Write·Edit) | command | Write/Edit **내용**에서 AWS/GitHub/OpenAI/Slack/Private key/JWT 탐지, 발견 시 차단 |
| `session-start-context.sh` | SessionStart | command | 세션 시작 시 CWD·브랜치·dirty 파일·최근 커밋 3개를 `additionalContext`로 주입 |
| `user-prompt-inject.py` | UserPromptSubmit | command | 매 프롬프트마다 `[현재 시점] 날짜 \| CWD \| Branch` 주입 |
| `stop-self-check.py` | Stop | command | 응답 종료 시 `CLAUDE.md`의 FINAL SELF-CHECK 항목을 재주입 (`suppressOutput: true`) |

### ECC origin (affaan-m/everything-claude-code, MIT)
Node.js 원본을 Python으로 재작성하여 기존 훅 스타일과 일관성 유지.

| Hook | 이벤트 | 기능 |
|------|--------|------|
| `pre-bash-block-no-verify.py` | PreToolUse (Bash) | `git --no-verify` / `git push -n` 등 hook bypass 플래그 차단 (exit 2) |
| `pre-bash-commit-quality.py` | PreToolUse (Bash) | `git commit` 직전 staged 파일에서 console.log·debugger·secret 검사, conventional commit 메시지 검증 |
| `post-bash-pr-created.py` | PostToolUse (Bash) | `gh pr create` 성공 시 PR URL·리뷰 명령 stderr 출력 |
| `pre-edit-suggest-compact.py` | PreToolUse (Edit·Write) | Edit/Write 호출 카운터 (세션별), 임계값(`COMPACT_THRESHOLD`, 기본 50)에서 `/compact` 제안 |

각 훅은 `settings.json`의 `hooks` 배열에 독립적으로 등록되어 있으므로 개별 비활성화 가능.

## Commands

| 커맨드 | 설명 |
|--------|------|
| `/backup-customs` | `~/.claude/` 설정을 이 레포에 동기화 |
| `/handoff` | 세션 인수인계 문서 생성 |

## Skills

### Original (in-house, read-only)
| 스킬 | 설명 |
|------|------|
| `/ask` | 코드 수정 없이 코드베이스 질의응답 |
| `/plan` | 구조화된 구현 계획 생성 (Goals/Scope/Steps/Verification/Risks) |
| `/review` | `rules/` 기반 자가 코드 리뷰 (CRITICAL/WARN/INFO + 컴플라이언스 매트릭스) |
| `/debug` | Investigation-First 디버깅 워크플로 (Log → Repro → Hypothesis → Evidence → Next) |

### ECC origin (affaan-m/everything-claude-code, MIT)
| 스킬 | 설명 |
|------|------|
| `hexagonal-architecture` | Ports & Adapters 시스템 설계·리팩토링 (TS/Java/Kotlin/Go) |
| `api-design` | REST·GraphQL API 설계 패턴 (버저닝·에러 처리·페이지네이션) |
| `deep-research` | firecrawl·exa MCP 기반 다중 소스 리서치 (MCP 서버 설정 필요) |
| `kotlin-patterns` | Kotlin 2.0+ idiomatic 패턴·null safety·coroutine |
| `springboot-patterns` | **Spring Boot 4.0+** 아키텍처·REST·JPA·async (Spring Framework 7.x baseline) |
| `frontend-patterns` | React·Next.js·상태관리·성능 최적화 |

## Agents (Claude Code 전용)

ECC에서 채택한 12개 subagent. `.claude/agents/`에 보관되며 `~/.claude/agents/`로 설치된다.

> **Codex CLI는 미지원**: Codex의 `[agents]` 설정은 role config 성격이며, Claude Code의 frontmatter 기반 subagent 시스템과 호환되지 않는다. Agents는 Claude Code 세션에서만 자동 발동된다.

### Core agents
| Agent | 역할 |
|---|---|
| `planner` | Proactive 구현 계획 (`/plan` skill과 공존; agent는 자동 발동) |
| `code-reviewer` | 범용 코드 리뷰 (git diff 자동 분석, confidence-based filtering) |
| `security-reviewer` | 보안 취약점 전문 리뷰 (SQL injection, XSS, secrets, auth bypass) |
| `refactor-cleaner` | dead code, 중복 제거, knip / depcheck / ts-prune 실행 |

### Support agents
| Agent | 역할 |
|---|---|
| `doc-updater` | README·codemap·문서 업데이트 |
| `tdd-guide` | Red-Green-Refactor 워크플로 강제 |
| `database-reviewer` | PostgreSQL·Supabase 쿼리·스키마 리뷰 |

### Language-specific
| Agent | 역할 |
|---|---|
| `typescript-reviewer` | TS strict mode, `any` 회피, 타입 안정성 |
| `kotlin-reviewer` | Kotlin idiom, null safety, coroutine 패턴 |
| `java-reviewer` | Java/Spring 레이어링, DI, 트랜잭션 경계 |
| `java-build-resolver` | Java/Maven/Gradle 빌드 오류 자동 해결 |
| `kotlin-build-resolver` | Kotlin/Gradle 빌드 오류 자동 해결 |

## ECC 채택 정책

이 레포는 보안·가드레일 중심 철학을 유지하면서 [`affaan-m/everything-claude-code`](https://github.com/affaan-m/everything-claude-code) (MIT) 의 검증된 컴포넌트를 큐레이션 채택한다.

**채택된 항목 (총 22개)**: 4 hooks + 12 agents + 6 skills.

**채택 원칙**:
- 우리 기존 항목과 **중복되지 않는 것** 우선
- 각 파일 frontmatter에 `origin: ECC (affaan-m/everything-claude-code, MIT)` 명시
- ECC의 Node.js 훅은 **Python으로 재작성**하여 우리 훅 스타일과 일관성 유지
- ECC의 `run-with-flags.js` 프로파일 시스템은 미적용 (오버엔지니어링 회피)
- Spring Boot 관련은 **4.0+ 기준으로 업데이트**

전체 ECC 크기는 47 agents / 181 skills / 79 commands / 34 hooks이며, 본 레포는 그중 **약 12%** 만 큐레이션 채택했다. 추가가 필요하면 `/tmp/everything-claude-code/`를 직접 참조하거나 후속 작업으로 별도 채택.

## 차단 명령어 추가

`guardrail.py`는 Claude를 통한 수정이 불가합니다 (자기 보호). 직접 편집하세요.
Codex 포트(`codex/hooks/guardrail.py`)도 동일한 자기 보호 대상이며, DENY·PROTECTED_FILES 변경 시 **두 파일을 같이 맞춰야** 합니다.

```python
# Bash 명령 차단
DENY = {
    "my new rule":  r"\bsome-dangerous-command\b",
}

# 파일 접근 차단
PROTECTED_FILES = [
    r"\.my-secret-file\b",
]
```

---

## Codex CLI 포팅

OpenAI **Codex CLI** (experimental hooks)에도 동일한 철학을 적용했습니다. 본 레포의 `codex/` 디렉토리가 `~/.codex/`에 설치되는 구조입니다.

### Codex 훅 이식 매트릭스

| Claude Code 훅 | Codex 이식 | 비고 |
|---|---|---|
| `guardrail.py` (Bash) | ✅ `codex/hooks/guardrail.py` | 동일 DENY·PROTECTED_FILES |
| `guardrail.py` (Read/Edit/Write) | ❌ 지원 불가 | Codex PreToolUse는 **Bash만** 인터셉트 |
| `pre-write-secret-scan.py` | ❌ 지원 불가 | 같은 이유. 대안: git pre-commit hook (후속 과제) |
| `session-start-context.sh` | ✅ | matcher `"startup\|resume"` 사용 |
| `user-prompt-inject.py` | ✅ | Codex는 plain text stdout도 context로 수용 |
| `stop-self-check.py` | ⚠️ 부분 | Codex Stop은 `additionalContext` 미지원. `systemMessage`로 대체 → 사용자에게 warning으로 보임 |
| Skills (`/ask`, `/plan`, `/review`, `/debug`) | ⏳ TODO | Codex Skills 시스템은 별도 스펙. 후속 작업으로 포팅 예정 |
| `CLAUDE.md` | ✅ `codex/AGENTS.md` | 핵심 정책 이식 + Codex 제약 섹션 추가 |

### Codex hooks.json 구조

`~/.codex/hooks.json`에 등록되는 훅은 4개 이벤트입니다:

| Event | Matcher | Hook | 역할 |
|---|---|---|---|
| `SessionStart` | `startup\|resume` | `session-start-context.sh` | git 컨텍스트 주입 |
| `PreToolUse` | `Bash` | `guardrail.py` | Bash 명령 차단 |
| `UserPromptSubmit` | (all) | `user-prompt-inject.py` | 날짜·CWD·branch 주입 |
| `Stop` | (all) | `stop-self-check.py` | FINAL SELF-CHECK 리마인더 (systemMessage) |

`config.toml`에서 `[features] codex_hooks = true`가 설정되어 있어야 활성화됩니다.

### Codex-specific 주의사항

1. **PreToolUse는 Bash 전용**: Write/Edit/Read에 대한 가드레일은 작동하지 않습니다. 파일 내용 기반 시크릿 차단은 git pre-commit hook이나 CI 단계에서 처리하세요.
2. **Stop 이벤트 프로토콜 차이**: Claude Code는 `additionalContext` + `suppressOutput: true`로 숨겨진 리마인더를 주입할 수 있지만, Codex는 `systemMessage`만 지원하여 사용자에게 warning으로 보입니다. 노이즈가 싫다면 `codex/hooks/stop-self-check.py`를 no-op으로 바꾸세요.
3. **샌드박스 기본값**: `approval_policy = "on-request"`, `sandbox_mode = "workspace-write"`, `network_access = false`. 네트워크 필요 시 명시적으로 opt-in하세요.
4. **Telemetry off**: `[analytics] enabled = false`. OpenAI 익명 사용 메트릭 수집 opt-out.
5. **Windows 미지원**: Codex 훅은 현재 Windows에서 비활성화입니다. WSL 사용 시 문제 없음.
6. **Experimental 상태**: Codex hooks는 실험적 기능이므로 상위 스펙 변경 가능성이 있습니다. 업데이트 후에는 훅 동작을 재확인하세요.

### Codex 설치 확인

```bash
./install.sh codex
codex --version                     # Codex CLI 설치 확인
cat ~/.codex/config.toml             # codex_hooks=true 확인
cat ~/.codex/hooks.json              # 4개 이벤트 등록 확인
ls -la ~/.codex/hooks/               # 4개 훅 파일 + 실행 권한 확인
```
