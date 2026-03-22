#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing claude-settings → $CLAUDE_DIR"

# Backup existing settings
if [ -d "$CLAUDE_DIR" ]; then
  echo "Backing up existing ~/.claude → ~/.claude.bak"
  cp -r "$CLAUDE_DIR" "$CLAUDE_DIR.bak" 2>/dev/null || true
fi

mkdir -p "$CLAUDE_DIR"

# Copy files
for item in CLAUDE.md settings.json; do
  cp "$REPO_DIR/$item" "$CLAUDE_DIR/"
done

for dir in rules hooks commands skills scheduled-tasks; do
  if [ -d "$REPO_DIR/$dir" ]; then
    cp -r "$REPO_DIR/$dir" "$CLAUDE_DIR/"
  fi
done

echo ""
echo "Done! Installed:"
echo "  CLAUDE.md, settings.json, rules/, hooks/, commands/, skills/, scheduled-tasks/"
echo ""
echo "Note: settings.local.json에 시크릿(토큰 등)과 플러그인 설정을 직접 추가하세요."
echo "Example:"
echo '  {'
echo '    "env": {'
echo '      "GITHUB_PERSONAL_ACCESS_TOKEN": "..."'
echo '    },'
echo '    "enabledPlugins": { ... }'
echo '  }'
