#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CODEX_DIR="$HOME/.codex"

# ─── Target selection ────────────────────────────────────────
# Usage:
#   ./install.sh            # install both (default)
#   ./install.sh claude     # install only Claude Code
#   ./install.sh codex      # install only Codex CLI
TARGET="${1:-both}"

install_claude() {
  echo "Installing claude-settings → $CLAUDE_DIR"

  if [ -d "$CLAUDE_DIR" ]; then
    echo "Backing up existing ~/.claude → ~/.claude.bak"
    cp -r "$CLAUDE_DIR" "$CLAUDE_DIR.bak" 2>/dev/null || true
  fi

  mkdir -p "$CLAUDE_DIR"

  for item in CLAUDE.md settings.json; do
    cp "$REPO_DIR/$item" "$CLAUDE_DIR/"
  done

  for dir in rules hooks commands skills scheduled-tasks; do
    if [ -d "$REPO_DIR/$dir" ]; then
      cp -r "$REPO_DIR/$dir" "$CLAUDE_DIR/"
    fi
  done

  # .claude/agents/ — Claude Code subagents (ECC origin). The repo stores
  # these under .claude/agents/ to match the runtime location.
  if [ -d "$REPO_DIR/.claude/agents" ]; then
    mkdir -p "$CLAUDE_DIR/agents"
    cp -r "$REPO_DIR/.claude/agents/." "$CLAUDE_DIR/agents/"
  fi

  echo "  → CLAUDE.md, settings.json, rules/, hooks/, commands/, skills/, scheduled-tasks/, agents/"
}

install_codex() {
  if [ ! -d "$REPO_DIR/codex" ]; then
    echo "Skip Codex: $REPO_DIR/codex not found"
    return 0
  fi

  echo "Installing codex-settings → $CODEX_DIR"

  if [ -d "$CODEX_DIR" ]; then
    echo "Backing up existing ~/.codex → ~/.codex.bak"
    cp -r "$CODEX_DIR" "$CODEX_DIR.bak" 2>/dev/null || true
  fi

  mkdir -p "$CODEX_DIR"

  # Top-level Codex files
  for item in AGENTS.md config.toml hooks.json; do
    if [ -f "$REPO_DIR/codex/$item" ]; then
      cp "$REPO_DIR/codex/$item" "$CODEX_DIR/"
    fi
  done

  # Hooks directory
  if [ -d "$REPO_DIR/codex/hooks" ]; then
    cp -r "$REPO_DIR/codex/hooks" "$CODEX_DIR/"
  fi

  echo "  → AGENTS.md, config.toml, hooks.json, hooks/"
}

case "$TARGET" in
  both)
    install_claude
    echo ""
    install_codex
    ;;
  claude)
    install_claude
    ;;
  codex)
    install_codex
    ;;
  *)
    echo "Unknown target: $TARGET" >&2
    echo "Usage: $0 [both|claude|codex]" >&2
    exit 1
    ;;
esac

echo ""
echo "Done."
echo ""
echo "Notes:"
echo "  • Claude Code: create ~/.claude/settings.local.json for secrets (env) and plugins"
echo "    Example:"
echo '      {'
echo '        "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "..." },'
echo '        "enabledPlugins": {}'
echo '      }'
echo ""
echo "  • Codex CLI: create ~/.codex/config.local.toml for machine-specific overrides."
echo "    auth.json is managed by 'codex login' / OS keychain — do NOT edit by hand."
echo "    Hooks are experimental: confirm 'codex_hooks = true' is set in config.toml."
