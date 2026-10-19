#!/usr/bin/env python3
"""Group #3 first-party UI Repair-only script entry for native Option B hold.

Only one new action branch in the pre-existing on-demand script dispatcher.
Never registers a service, timer or global context menu. All other entry
commands (addon/open/resume/restore) remain byte-identical.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

ENTRY = "assets/addons/script.infinity.uirepair/runtime.py"
ANCHOR = "        elif action == 'resume': resume_menu(token)\n        elif action == 'restore': restore_hidden()"
REPLACEMENT = """        elif action == 'resume': resume_menu(token)
        elif action == 'option-b':
            # Only a signed C++ Home-8101/8102 touch dispatch has the
            # matching pending native item proof. Invalid/stale holds do nothing.
            from home_option_b import show_for_focused_top_poster
            if len(args) == 4:
                show_for_focused_top_poster(args[1:])
        elif action == 'restore': restore_hidden()"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_runtime(data: bytes) -> bytes:
    source = data.decode("utf-8")
    if "elif action == 'option-b':" in source:
        raise ValueError("Option B action already registered")
    if source.count(ANCHOR) != 1:
        raise ValueError("Expected original on-demand UI Repair entry missing")
    before = source[:source.index(ANCHOR)]
    after = source[source.index(ANCHOR)+len(ANCHOR):]
    # Everything outside this single branch is exactly the original code.
    return (before + REPLACEMENT + after).encode("utf-8")


def apply_to_tree(tree: Path, *, expected_sha256: str | None = None) -> dict:
    path = Path(tree) / ENTRY
    before = path.read_bytes()
    if expected_sha256 and sha(before) != expected_sha256:
        raise ValueError("Unexpected original first-party UI Repair runtime")
    after = patch_runtime(before)
    path.write_bytes(after)
    return {'changed': [ENTRY], 'before_sha256': sha(before),
            'after_sha256': sha(after), 'other_actions_byte_identical': True,
            'original_addon_manifest_changed': False,
            'native_compiled': False, 'fold_verified': False}

if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("apk_expanded_tree", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    print(json.dumps(apply_to_tree(args.apk_expanded_tree,
                                   expected_sha256=args.expected_sha256), indent=2))
