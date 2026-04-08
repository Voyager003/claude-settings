# claude-settings

Claude Code 커스텀 설정 백업 및 관리

## 특징

- **보안 우선** — 원격 쓰기, PR 생성/머지 등 위험 작업은 guardrail hook으로 차단
- **묻지 않고 판단** — ask(확인 후 허용) 대신 allow/deny로 처리
- **가드레일 일원화** — 모든 차단은 `guardrail.py` 훅 하나에서 처리
- **시크릿 격리** — 토큰은 git-ignored인 `settings.local.json`에서 머신별 관리

## Setup

```bash
git clone https://github.com/<your-username>/claude-settings.git
cd claude-settings && ./install.sh
```

기존 `~/.claude`가 있으면 자동으로 `~/.claude.bak`에 백업합니다.

### 시크릿 설정

`~/.claude/settings.local.json`에 env 섹션을 만들어 머신별로 관리하세요.

```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "..."
  },
  "enabledPlugins": {}
}
```

## Structure

```
.
├── CLAUDE.md                  # 핵심 정책 요약 (entry router)
├── settings.json              # Permission allow, hooks 등록
├── rules/                     # 상세 룰셋
│   ├── 00-core.md             # 핵심 정책
│   ├── 01-safety.md           # 보안/승인 규칙
│   ├── 02-workflow.md         # 워크플로
│   ├── 10-stack-java-spring.md # Java/Spring 스타일
│   ├── 11-stack-kotlin.md     # Kotlin 스타일
│   └── 12-stack-nextjs-ts.md  # Next.js/TypeScript 스타일
├── hooks/
│   ├── guardrail.py              # 통합 가드레일 (PreToolUse: Bash/Read/Edit/Write)
│   ├── session-start-context.sh  # SessionStart: git 컨텍스트 주입
│   ├── user-prompt-inject.py     # UserPromptSubmit: 날짜·CWD·branch 주입
│   ├── stop-self-check.py        # Stop: FINAL SELF-CHECK 리마인더
│   └── pre-write-secret-scan.py  # PreToolUse(Write/Edit): 내용 기반 시크릿 차단
├── commands/                  # 슬래시 커맨드
├── skills/                    # 커스텀 스킬
└── scheduled-tasks/           # 예약 작업
```

## Hooks

| Hook | 이벤트 | 타입 | 기능 |
|------|--------|------|------|
| `guardrail.py` | PreToolUse (Bash·Read·Edit·Write) | command | 경로·명령 기반 통합 가드레일 (자기 보호, 직접 편집 필요) |
| `pre-write-secret-scan.py` | PreToolUse (Write·Edit) | command | Write/Edit **내용**에서 AWS/GitHub/OpenAI/Slack/Private key/JWT 탐지, 발견 시 차단. guardrail과 직교하는 내용 기반 방어층 |
| `session-start-context.sh` | SessionStart | command | 세션 시작 시 CWD·브랜치·dirty 파일·최근 커밋 3개를 `additionalContext`로 주입 (git repo 아니면 skip) |
| `user-prompt-inject.py` | UserPromptSubmit | command | 매 프롬프트마다 `[현재 시점] 날짜 \| CWD \| Branch` 주입 — 지식 컷오프로 인한 날짜 오류 방지 |
| `stop-self-check.py` | Stop | command | 응답 종료 시 `CLAUDE.md`의 FINAL SELF-CHECK 항목을 재주입 (사용자에게는 `suppressOutput: true`로 숨김) |

각 훅은 `settings.json`의 `hooks` 배열에 독립적으로 등록되어 있으므로 개별 비활성화 가능.

## Commands

| 커맨드 | 설명 |
|--------|------|
| `/backup-customs` | `~/.claude/` 설정을 이 레포에 동기화 |
| `/handoff` | 세션 인수인계 문서 생성 |

## Skills

| 스킬 | 설명 |
|------|------|
| `/ask` | 코드 수정 없이 코드베이스 질의응답 (read-only) |
| `/plan` | 구조화된 구현 계획 생성 (Goals/Scope/Steps/Verification/Risks) |
| `/review` | `rules/` 기반 자가 코드 리뷰 (CRITICAL/WARN/INFO 분류 + 컴플라이언스 매트릭스) |
| `/debug` | Investigation-First 디버깅 워크플로 (Log → Repro → Hypothesis → Evidence → Next) |

## 차단 명령어 추가

`guardrail.py`는 Claude를 통한 수정이 불가합니다 (자기 보호). 직접 편집하세요.

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
