#!/usr/bin/env python3
"""Keep Cobra as the visible task when Android Back exits its root screen.

Android presentation-shell only. Internal Cobra Back behavior (dialogs, drawers,
player restore, context sheet) is preserved. Only the terminal Back fallback is
changed so it backgrounds the whole Infinity task instead of popping Cobra and
revealing the Infinity activity underneath. The explicit Infinity toggle remains
the only Cobra -> Infinity handoff.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
SIGNATURE = "  @Override\n  public void onBackPressed() {"


def method_end(text: str, start: int) -> int:
    """Return the index just after the matching method-closing brace."""
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError("Cobra task-exit guard: onBackPressed opening brace missing")

    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""

        if line_comment:
            if c == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if c == "*" and n == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote is not None:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote:
                quote = None
            i += 1
            continue

        if c == "/" and n == "/":
            line_comment = True
            i += 2
            continue
        if c == "/" and n == "*":
            block_comment = True
            i += 2
            continue
        if c in ('"', "'"):
            quote = c
            i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1

    raise RuntimeError("Cobra task-exit guard: onBackPressed closing brace missing")


def patch(java: str) -> str:
    start = java.find(SIGNATURE)
    if start < 0 or java.find(SIGNATURE, start + 1) >= 0:
        raise RuntimeError("Cobra task-exit guard: expected exactly one onBackPressed method")
    end = method_end(java, start)
    block = java[start:end]

    # Change only the method's terminal fallback. Earlier branches continue to
    # dismiss Cobra UI/player state exactly as before.
    close = block.rfind("}")
    body = block[:close]
    tail_patterns = (
        r"(?s)(.*\n\s*)returnToInfinity\(\);\s*$",
        r"(?s)(.*\n\s*)super\.onBackPressed\(\);\s*$",
        r"(?s)(.*\n\s*)finish\(\);\s*$",
        r"(?s)(.*\n\s*)finishAndRemoveTask\(\);\s*$",
    )
    replacement = None
    for pattern in tail_patterns:
        match = re.fullmatch(pattern, body)
        if match:
            replacement = match.group(1) + "moveTaskToBack(true);\n  "
            break
    if replacement is None:
        snippet = body[-500:].replace("\n", "\\n")
        raise RuntimeError("Cobra task-exit guard: unknown terminal Back fallback: " + snippet)

    patched_block = replacement + "}"
    java = java[:start] + patched_block + java[end:]
    return java


def verify(java: str) -> None:
    start = java.find(SIGNATURE)
    if start < 0:
        raise RuntimeError("Cobra task-exit verify: onBackPressed missing")
    end = method_end(java, start)
    block = java[start:end]
    if "moveTaskToBack(true);" not in block:
        raise RuntimeError("Cobra task-exit verify: terminal task-background action missing")
    if block.rstrip().endswith("returnToInfinity();\n  }"):
        raise RuntimeError("Cobra task-exit verify: Back still hands off to Infinity")
    if "returnToInfinity" not in java:
        raise RuntimeError("Cobra task-exit verify: explicit Infinity handoff was removed")
    if "closeFullscreenToCobraView()" not in block:
        raise RuntimeError("Cobra task-exit verify: fullscreen Back restore was disturbed")
    if "closeCobraChannelActions()" not in block:
        raise RuntimeError("Cobra task-exit verify: context-sheet Back dismissal was disturbed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra terminal Back backgrounds the task; Infinity remains explicit-toggle only")


if __name__ == "__main__":
    main()
