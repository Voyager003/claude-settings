#!/usr/bin/env python3
"""
PreToolUse hook (Bash) — pre-commit quality check.

Ported from ECC `pre:bash:commit-quality` (affaan-m/everything-claude-code, MIT).
Simplified: dropped the optional ESLint/Pylint/golint runners (those are project-
specific and slow). Kept the core static checks:

  - console.log / debugger statements in JS/TS files
  - Hardcoded secrets (overlaps with our pre-write-secret-scan; defense in depth)
  - Conventional commit message format

Behavior
--------
- Only triggers when the Bash command contains `git commit`.
- Skips on `--amend`.
- Reads staged file contents via `git show :PATH` (no FS access).
- Errors → exit 2 (block). Warnings → exit 0 with stderr message.
"""
import sys
import json
import re
import subprocess

CHECKABLE_EXT = (".js", ".jsx", ".ts", ".tsx", ".py", ".go", ".rs", ".java", ".kt")

SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"),                           "AWS Access Key"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"),                        "GitHub PAT"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"),                        "OpenAI API key"),
    (re.compile(r"(?i)api[_-]?key\s*[=:]\s*['\"][^'\"]{8,}['\"]"), "API key literal"),
]

CONVENTIONAL_COMMIT = re.compile(
    r"^(feat|fix|docs|style|refactor|test|chore|build|ci|perf|revert)(\(.+\))?:\s*.+"
)


def get_staged_files() -> list[str]:
    try:
        r = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return []
        return [line for line in r.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def get_staged_content(path: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", "show", f":{path}"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def find_file_issues(path: str) -> list[tuple[str, int, str]]:
    """Returns list of (severity, line_no, message)."""
    content = get_staged_content(path)
    if content is None:
        return []

    issues: list[tuple[str, int, str]] = []
    for i, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("#"):
            continue

        # console.log (JS/TS)
        if "console.log" in line and path.endswith((".js", ".jsx", ".ts", ".tsx")):
            issues.append(("warning", i, "console.log found"))

        # debugger statement
        if re.search(r"\bdebugger\b", line):
            issues.append(("error", i, "debugger statement"))

        # Hardcoded secrets
        for rx, name in SECRET_PATTERNS:
            if rx.search(line):
                issues.append(("error", i, f"potential {name}"))
                break  # one secret per line is enough

    return issues


def validate_commit_message(cmd: str) -> list[tuple[str, str]]:
    """Returns list of (severity, message). Empty if no -m / no issues."""
    m = re.search(r"(?:-m|--message)[=\s]+[\"']([^\"']+)[\"']", cmd)
    if not m:
        return []

    msg = m.group(1)
    issues: list[tuple[str, str]] = []

    if not CONVENTIONAL_COMMIT.match(msg):
        issues.append((
            "warning",
            "Commit message does not match conventional format "
            "(type(scope): subject)",
        ))

    if len(msg) > 72:
        issues.append((
            "warning",
            f"Commit subject too long ({len(msg)} chars, max 72)",
        ))

    if msg.endswith("."):
        issues.append((
            "warning",
            "Commit subject should not end with a period",
        ))

    return issues


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name", "") != "Bash":
        sys.exit(0)

    cmd = (data.get("tool_input", {}) or {}).get("command", "")
    if "git commit" not in cmd:
        sys.exit(0)

    # Skip --amend (we don't want to block amend cycles)
    if "--amend" in cmd:
        sys.exit(0)

    staged = get_staged_files()
    if not staged:
        # Nothing to check.
        sys.exit(0)

    error_count = 0
    warning_count = 0
    findings: list[str] = []

    for path in staged:
        if not path.endswith(CHECKABLE_EXT):
            continue
        for severity, line_no, message in find_file_issues(path):
            findings.append(f"  [{severity.upper()}] {path}:{line_no} — {message}")
            if severity == "error":
                error_count += 1
            else:
                warning_count += 1

    for severity, message in validate_commit_message(cmd):
        findings.append(f"  [{severity.upper()}] commit message — {message}")
        if severity == "error":
            error_count += 1
        else:
            warning_count += 1

    if findings:
        print("[commit-quality] findings:", file=sys.stderr)
        for f in findings:
            print(f, file=sys.stderr)
        print(
            f"[commit-quality] {error_count} error(s), {warning_count} warning(s)",
            file=sys.stderr,
        )
        if error_count > 0:
            print(
                "[commit-quality] BLOCKED: fix errors before committing.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[commit-quality] hook error: {e}", file=sys.stderr)
        sys.exit(0)
