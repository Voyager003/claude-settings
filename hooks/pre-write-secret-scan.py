#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code (Write / Edit).
Scans the content being written for hardcoded secret patterns.
Exit 0 = allow, Exit 2 = block.

Complements guardrail.py which blocks by file PATH. This hook blocks by file CONTENT.
Never echoes the detected value to stderr — only pattern name and line number.
"""
import sys
import json
import re

# Core, high-confidence patterns. Tuned to minimize false positives.
SECRET_PATTERNS: dict[str, str] = {
    "AWS access key":      r"AKIA[0-9A-Z]{16}",
    "GitHub PAT":          r"ghp_[A-Za-z0-9]{36}",
    "GitHub fine-grained": r"github_pat_[A-Za-z0-9_]{82}",
    "OpenAI API key":      r"sk-[A-Za-z0-9]{20,}",
    "Slack token":         r"xox[baprs]-[A-Za-z0-9-]{10,}",
    "Private key header":  r"-----BEGIN (?:(?:RSA|EC|DSA|OPENSSH|ENCRYPTED|PGP) )?PRIVATE KEY-----",
    "JWT":                 r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
}

COMPILED = {name: re.compile(pat) for name, pat in SECRET_PATTERNS.items()}


def extract_content(tool_input: dict) -> str:
    """Extract the text payload from Write / Edit tool_input."""
    # Write: {file_path, content}
    content = tool_input.get("content")
    if isinstance(content, str):
        return content
    # Edit: {file_path, old_string, new_string}
    new_string = tool_input.get("new_string")
    if isinstance(new_string, str):
        return new_string
    return ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = data.get("tool_input", {}) or {}
    content = extract_content(tool_input)
    if not content:
        sys.exit(0)

    for name, rx in COMPILED.items():
        m = rx.search(content)
        if m:
            line_no = content[: m.start()].count("\n") + 1
            # Never print the matched value — only name and location.
            print(
                f"BLOCKED: potential secret '{name}' detected at line {line_no}. "
                "Move to env var or .env (git-ignored).",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # On unexpected error, fail-open (do not block) to avoid disrupting legitimate writes.
        sys.exit(0)
