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
│   └── guardrail.py           # 통합 가드레일 (Bash + Read/Edit/Write)
├── commands/                  # 슬래시 커맨드
├── skills/                    # 커스텀 스킬
└── scheduled-tasks/           # 예약 작업
```

## Commands

| 커맨드 | 설명 |
|--------|------|
| `/backup-customs` | `~/.claude/` 설정을 이 레포에 동기화 |
| `/handoff` | 세션 인수인계 문서 생성 |

## Skills

| 스킬 | 설명 |
|------|------|
| `/ask` | 코드 수정 없이 코드베이스 질의응답 |

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
