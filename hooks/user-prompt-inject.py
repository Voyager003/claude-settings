#!/usr/bin/env python3
"""
UserPromptSubmit hook for Claude Code.
Injects current date, CWD, and git branch into each user prompt as additional context.
Never blocks. Fails silently to avoid disrupting the user's prompt.
"""
import sys
import json
import os
import subprocess
from datetime import datetime, timezone


def get_branch() -> str:
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode == 0:
            return r.stdout.strip() or "detached"
    except Exception:
        pass
    return "n/a"


def main() -> None:
    # Drain stdin per hook protocol (content unused).
    try:
        sys.stdin.read()
    except Exception:
        pass

    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d (%A)")
    cwd = os.getcwd()
    branch = get_branch()

    ctx = f"[현재 시점] {today} | CWD: {cwd} | Branch: {branch}"

    out = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ctx,
        },
    }
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never disrupt the prompt flow.
        print('{"continue": true}')
        sys.exit(0)
