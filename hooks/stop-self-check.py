#!/usr/bin/env python3
"""
Stop hook for Claude Code.
Injects the CLAUDE.md FINAL SELF-CHECK reminder as additional context just before
the assistant stops. Never blocks and hides output from the transcript.
"""
import sys
import json

REMINDER = (
    "FINAL SELF-CHECK:\n"
    "- CORE 위반 없는가? (시크릿/승인/prod/contract/가드레일/테스트 우회)\n"
    "- 범위 외 리팩토링·포매팅 섞이지 않았는가?\n"
    "- 검증 수행했거나, 미수행 사유/영향 명시했는가?\n"
    "- 로그·스니펫에 민감정보 *** 마스킹했는가?"
)


def main() -> None:
    # Drain stdin per hook protocol.
    try:
        sys.stdin.read()
    except Exception:
        pass

    out = {
        "continue": True,
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": REMINDER,
        },
    }
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print('{"continue": true}')
        sys.exit(0)
