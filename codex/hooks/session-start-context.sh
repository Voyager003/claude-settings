#!/bin/bash
# SessionStart hook for Codex CLI (experimental).
# Matcher in hooks.json: "startup|resume"
#
# Injects git context (branch, dirty files, recent commits) as additional
# developer context. No external dependencies beyond python3 and git.
#
# Codex SessionStart accepts either:
#   - Plain text on stdout (appended as developer context)
#   - JSON with { hookSpecificOutput: { hookEventName: "SessionStart",
#                                       additionalContext: "..." } }
# This script emits JSON so the payload is unambiguous.
set -u

# Drain stdin (hook protocol).
cat > /dev/null 2>&1 || true

CWD="$(pwd)"

# Git repo check — skip silently if not a repo.
if ! git -C "$CWD" rev-parse --git-dir > /dev/null 2>&1; then
  python3 -c 'import json; print(json.dumps({"continue": True}))'
  exit 0
fi

BRANCH="$(git -C "$CWD" branch --show-current 2>/dev/null || echo "detached")"
[ -z "$BRANCH" ] && BRANCH="detached"
DIRTY="$(git -C "$CWD" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
RECENT="$(git -C "$CWD" log --oneline -3 2>/dev/null || echo "")"

# Build JSON via python3 heredoc (jq-free, handles escaping safely).
CWD="$CWD" BRANCH="$BRANCH" DIRTY="$DIRTY" RECENT="$RECENT" \
python3 - <<'PY'
import json, os

cwd = os.environ.get("CWD", "")
branch = os.environ.get("BRANCH", "")
dirty = os.environ.get("DIRTY", "0")
recent = os.environ.get("RECENT", "").strip()

recent_lines = "\n".join(f"  {line}" for line in recent.splitlines()) if recent else "  (no commits)"

ctx = (
    "## Session Context (git)\n"
    f"- CWD: {cwd}\n"
    f"- Branch: {branch}\n"
    f"- Dirty files: {dirty}\n"
    f"- Recent commits:\n{recent_lines}"
)

out = {
    "continue": True,
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": ctx,
    },
}
print(json.dumps(out))
PY

exit 0
