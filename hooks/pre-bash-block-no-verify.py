#!/usr/bin/env python3
"""
PreToolUse hook (Bash) — block git hook bypass flags.

Ported from ECC `pre:bash:block-no-verify` (affaan-m/everything-claude-code, MIT).
The original was `npx block-no-verify@1.1.2`; this is a Python equivalent matching
our hook style and avoiding the npm dependency.

Blocks commands that contain `--no-verify` for git operations that would skip
pre-commit / commit-msg / pre-push hooks. Also catches `-n` for git push.

Exit 0 = allow, Exit 2 = block.
"""
import sys
import json
import re

# Patterns for git hook bypass flags.
DENY_PATTERNS = [
    # Long form: --no-verify on git commit/push/merge/rebase/cherry-pick
    (
        r"\bgit\s+(?:commit|push|merge|rebase|cherry-pick|am|tag)\b[^|;&]*\s--no-verify\b",
        "git --no-verify (skips pre-commit / commit-msg / pre-push hooks)",
    ),
    # Short form: -n on git push (push uses -n for --no-verify)
    (
        r"\bgit\s+push\b[^|;&]*\s-n(?:\s|$)",
        "git push -n (alias for --no-verify on push)",
    ),
]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        # Fail-open on parse error to avoid disrupting unrelated tool calls.
        sys.exit(0)

    if data.get("tool_name", "") != "Bash":
        sys.exit(0)

    cmd = (data.get("tool_input", {}) or {}).get("command", "")
    if not cmd:
        sys.exit(0)

    for pattern, label in DENY_PATTERNS:
        if re.search(pattern, cmd):
            print(
                f"BLOCKED: {label}. "
                "Hook bypass is not allowed — fix the underlying issue instead.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
