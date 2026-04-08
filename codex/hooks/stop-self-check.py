#!/usr/bin/env python3
"""
Stop hook for Codex CLI (experimental).

Codex Stop requires JSON on stdout (plain text is invalid). It also does NOT
support `additionalContext` on this event — the closest equivalent is
`systemMessage`, which is surfaced as a warning in the UI / event stream.

This differs from the Claude Code counterpart, which could silently inject a
reminder via `additionalContext` + `suppressOutput: true`. In Codex, the
reminder will be visible to the user as a system warning.

Also note: in Codex, `decision: "block"` on Stop does NOT reject the turn —
it tells Codex to continue the conversation with the reason as a new prompt.
We explicitly avoid that and use `continue: true` + `systemMessage` so the
turn simply ends with a visible reminder.
"""
import sys
import json

REMINDER = (
    "FINAL SELF-CHECK — "
    "CORE 위반(시크릿/승인/prod/contract/가드레일/테스트 우회)? / "
    "범위 외 변경 혼입? / "
    "검증 수행 혹은 미수행 사유 명시? / "
    "로그·스니펫 민감정보 *** 마스킹?"
)


def main() -> None:
    # Drain stdin per hook protocol.
    try:
        sys.stdin.read()
    except Exception:
        pass

    out = {
        "continue": True,
        "systemMessage": REMINDER,
    }
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Fallback: emit a minimal valid JSON so Codex doesn't break on the Stop.
        print('{"continue": true}')
        sys.exit(0)
