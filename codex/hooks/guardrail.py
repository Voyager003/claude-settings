#!/usr/bin/env python3
"""
PreToolUse hook for Codex CLI (experimental).

Ported from ~/.claude/hooks/guardrail.py. Since Codex PreToolUse currently only
intercepts Bash commands (not Read/Edit/Write), this version strips the
file-path tool handling and keeps only:
  1) Bash command string scanning against PROTECTED_FILES
  2) Bash command string scanning against the DENY list

Exit 0 = allow, Exit 2 = block.
Codex also accepts JSON on stdout with
  { "hookSpecificOutput": { "hookEventName": "PreToolUse",
                             "permissionDecision": "deny",
                             "permissionDecisionReason": "..." } }
but the simpler exit-2 + stderr form is used here to match the Claude Code
version's behavior.
"""
import sys
import json
import re

# ─── Protected files ────────────────────────────────────────
# Any Bash command string referencing these paths is blocked.
PROTECTED_FILES = [
    # Claude Code self-protection (still honored for cross-tool safety)
    r"\.claude/settings\.json",
    r"\.claude/settings\.local\.json",
    r"\.claude/hooks/guardrail\.py",
    # Codex self-protection
    r"\.codex/config\.toml",
    r"\.codex/config\.local\.toml",
    r"\.codex/hooks\.json",
    r"\.codex/hooks/guardrail\.py",
    r"\.codex/auth\.json",
    # Shell rc files
    r"\.zshrc",
    r"\.zprofile",
    r"\.bash_profile",
    r"\.bashrc",
    # Secrets
    r"\.env\b",
    r"\.key\b",
    r"\.pem\b",
    # Sensitive directories
    r"\.ssh\b",
    r"\.aws\b",
    r"\.gnupg\b",
    r"\.kube\b",
    r"\.gcloud\b",
    # Sensitive config files
    r"\.npmrc\b",
    r"\.netrc\b",
    r"\.docker/config\.json",
    r"\.vault-token\b",
    r"\.git-credentials\b",
]
# ────────────────────────────────────────────────────────────

# ─── Deny list ──────────────────────────────────────────────
DENY: dict[str, str] = {
    # Destructive file operations
    "rm -rf":           r"\brm\s+-[a-z]*r[a-z]*f\b",
    "rm -fr":           r"\brm\s+-[a-z]*f[a-z]*r\b",
    "rm -r":            r"\brm\s+(-r\b|--recursive\b)",
    "mkfs":             r"\bmkfs\b",
    "dd":               r"\bdd\s+.*of=",
    "truncate":         r"\btruncate\b",
    "chmod 777":        r"\bchmod\s+777\b",
    "chown":            r"\bchown\b",

    # Git
    "git push --force": r"\bgit\s+push\b.*?(--force\b|-f\b)",
    "git push":         r"\bgit\s+push\b",
    "git reset --hard": r"\bgit\s+reset\s+--hard\b",
    "git clean":        r"\bgit\s+clean\b",

    # Infra / K8s
    "kubectl delete":   r"\bkubectl\s+delete\b",
    "kubectl drain":    r"\bkubectl\s+drain\b",
    "kubectl scale 0":  r"\bkubectl\s+scale\b.*--replicas[= ]*0\b",
    "kubectl exec":     r"\bkubectl\s+exec\b",
    "kubectl apply":    r"\bkubectl\s+apply\b",
    "helm uninstall":   r"\bhelm\s+(uninstall|delete)\b",
    "docker sys prune": r"\bdocker\s+system\s+prune\b",
    "docker rm":        r"\bdocker\s+rm\b",
    "docker rmi":       r"\bdocker\s+rmi\b",
    "docker exec":      r"\bdocker\s+exec\b",

    # Remote code execution
    "curl|wget pipe":   r"\b(curl|wget)\b.*\|\s*(ba)?sh\b",
    "sh < redirect":    r"^\s*(ba)?sh\s+<",

    # Publish (irreversible release)
    "npm publish":      r"\bnpm\s+publish\b",
    "gradle publish":   r"\bgradle\w*\s+publish\b",

    # Env/secret leak
    "printenv":         r"\bprintenv\b",
    "env dump":         r"^\s*env\s*$",
    "echo secret var":  r"\becho\b.*\$\{?\w*(TOKEN|SECRET|PASSWORD|KEY|CREDENTIAL)\w*\b",
    "show-token":       r"\bgh\s+auth\s+.*--show-token\b",

    # Encoding bypass (protected files evasion)
    "base64 decode":    r"\bbase64\s+(-d\b|--decode\b)",
    "printf hex":       r"\bprintf\s+.*\\x[0-9a-fA-F]",
    "xxd reverse":      r"\bxxd\s+.*-r\b",

    # GitHub CLI (read-only by default)
    "gh pr create":     r"\bgh\s+pr\s+create\b",
    "gh pr comment":    r"\bgh\s+pr\s+comment\b",
    "gh pr merge":      r"\bgh\s+pr\s+merge\b",
    "gh pr close":      r"\bgh\s+pr\s+close\b",
    "gh pr review":     r"\bgh\s+pr\s+review\b",
    "gh issue create":  r"\bgh\s+issue\s+create\b",
    "gh issue close":   r"\bgh\s+issue\s+close\b",
    "gh issue comment": r"\bgh\s+issue\s+comment\b",
    "gh repo delete":   r"\bgh\s+repo\s+delete\b",
    "gh release create": r"\bgh\s+release\s+create\b",
    "gh release delete": r"\bgh\s+release\s+delete\b",
    "gh api DELETE":    r"\bgh\s+api\b.*-X\s+DELETE\b",

    # Package install (supply chain risk)
    "npm install":       r"\bnpm\s+install\b",
    "npm i":             r"\bnpm\s+i\b",
    "yarn add":          r"\byarn\s+add\b",
    "pnpm add":          r"\bpnpm\s+add\b",
    "pip install":       r"\bpip3?\s+install\b",
    "brew install":      r"\bbrew\s+install\b",
    "brew uninstall":    r"\bbrew\s+uninstall\b",
    "cargo install":     r"\bcargo\s+install\b",

    # Infra / IaC
    "terraform destroy": r"\bterraform\s+destroy\b",
    "terraform apply":   r"\bterraform\s+apply\b",

    # Privilege escalation
    "sudo":              r"\bsudo\s",

    # Process kill
    "kill":              r"\bkill\s",
    "killall":           r"\bkillall\s",

    # macOS system
    "diskutil erase":    r"\bdiskutil\s+(eraseDisk|partitionDisk)\b",
    "crontab remove":    r"\bcrontab\s+-r\b",
    "launchctl unload":  r"\blaunchctl\s+unload\b",
    "osascript":         r"\bosascript\b",
    "defaults write":    r"\bdefaults\s+write\b",
    "security":          r"\bsecurity\s",

    # DB CLI direct access
    "mongo shell":       r"\bmongo\s",
    "mongosh":           r"\bmongosh\b",
    "psql":              r"\bpsql\s",
    "mysql":             r"\bmysql\s",

    # Remote access
    "ssh":               r"\bssh\s",
    "scp":               r"\bscp\s",
    "rsync":             r"\brsync\s",
}
# ────────────────────────────────────────────────────────────


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        # Fail-open on parse error (match Claude Code version's behavior).
        sys.exit(0)

    # Codex PreToolUse always emits tool_name == "Bash" today.
    tool = data.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input", {}) or {}
    cmd = tool_input.get("command", "")
    if not cmd:
        sys.exit(0)

    # Check protected file references in the command string.
    for pattern in PROTECTED_FILES:
        if re.search(pattern, cmd, re.IGNORECASE):
            print(
                f"BLOCKED: command references protected file ({pattern})",
                file=sys.stderr,
            )
            sys.exit(2)

    # Check deny list.
    for name, pattern in DENY.items():
        if re.search(pattern, cmd, re.IGNORECASE | re.MULTILINE):
            print(f"BLOCKED: {name} is not allowed", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
