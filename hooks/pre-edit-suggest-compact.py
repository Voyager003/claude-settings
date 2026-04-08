#!/usr/bin/env python3
"""
PreToolUse hook (Edit/Write) — strategic compact suggester.

Ported from ECC `pre:edit-write:suggest-compact`
(affaan-m/everything-claude-code, MIT). Tracks an Edit/Write call counter per
session and prints a `/compact` suggestion at threshold intervals.

Why manual over auto-compact:
  - Auto-compact happens at arbitrary points, often mid-task
  - Strategic compacting preserves context through logical phases
  - Compact after exploration, before execution
  - Compact after completing a milestone, before starting the next

Never blocks. Pass-through.

Environment:
  COMPACT_THRESHOLD     (default 50) — first suggestion threshold
  CLAUDE_SESSION_ID     used for per-session counter file
"""
import sys
import json
import os
import re
import tempfile

DEFAULT_THRESHOLD = 50
INTERVAL_AFTER = 25  # suggest again every N calls past the threshold


def get_session_id() -> str:
    sid = os.environ.get("CLAUDE_SESSION_ID", "default")
    return re.sub(r"[^A-Za-z0-9_-]", "", sid) or "default"


def get_threshold() -> int:
    raw = os.environ.get("COMPACT_THRESHOLD", "")
    try:
        v = int(raw)
        if 0 < v <= 10000:
            return v
    except (TypeError, ValueError):
        pass
    return DEFAULT_THRESHOLD


def main() -> None:
    # Drain stdin per hook protocol.
    try:
        sys.stdin.read()
    except Exception:
        pass

    counter_path = os.path.join(
        tempfile.gettempdir(), f"claude-tool-count-{get_session_id()}"
    )

    count = 1
    try:
        if os.path.exists(counter_path):
            with open(counter_path) as fp:
                raw = fp.read().strip()
            try:
                parsed = int(raw)
                if 0 < parsed <= 1_000_000:
                    count = parsed + 1
            except ValueError:
                count = 1
        with open(counter_path, "w") as fp:
            fp.write(str(count))
    except Exception:
        # Counter unavailable — silently bail out.
        sys.exit(0)

    threshold = get_threshold()

    if count == threshold:
        print(
            f"[strategic-compact] {threshold} tool calls reached — "
            "consider running /compact if you are transitioning between phases.",
            file=sys.stderr,
        )
    elif count > threshold and (count - threshold) % INTERVAL_AFTER == 0:
        print(
            f"[strategic-compact] {count} tool calls — checkpoint for /compact "
            "if context feels stale.",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
