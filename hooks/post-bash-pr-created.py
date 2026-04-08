#!/usr/bin/env python3
"""
PostToolUse hook (Bash) — log GitHub PR URL after creation.

Ported from ECC `post:bash:pr-created` (affaan-m/everything-claude-code, MIT).
After a successful `gh pr create`, parses the tool output for the PR URL and
prints it to stderr along with a suggested review command.

Never blocks. Pass-through.
"""
import sys
import json
import re

PR_URL_RE = re.compile(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)")
GH_PR_CREATE_RE = re.compile(r"\bgh\s+pr\s+create\b")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name", "") != "Bash":
        sys.exit(0)

    cmd = (data.get("tool_input", {}) or {}).get("command", "")
    if not GH_PR_CREATE_RE.search(cmd):
        sys.exit(0)

    # Tool response shape varies (Claude vs Codex). Try common fields.
    response = data.get("tool_response") or data.get("tool_output") or {}
    if isinstance(response, str):
        output_text = response
    elif isinstance(response, dict):
        output_text = (
            response.get("output")
            or response.get("stdout")
            or response.get("content")
            or ""
        )
    else:
        output_text = ""

    if not output_text:
        sys.exit(0)

    m = PR_URL_RE.search(output_text)
    if not m:
        sys.exit(0)

    pr_url = m.group(0)
    repo = m.group(1)
    pr_num = m.group(2)

    print(f"[pr-created] PR created: {pr_url}", file=sys.stderr)
    print(
        f"[pr-created] To review: gh pr view {pr_num} --repo {repo} --comments",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
