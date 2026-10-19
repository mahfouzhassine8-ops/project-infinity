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


# Final all-in-one must also preserve Group #1's separately source-approved
# Continue Watching chooser. That earlier scoped patch introduces a single
# home-choice branch BETWEEN resume and restore; both legitimate preimages
# must keep all existing actions and function bodies byte-identical.
GROUP1_ANCHOR = ("        elif action == 'resume': resume_menu(token)\n"
                 "        elif action == 'home-choice': home_continue_choice(token, args[2] if len(args) > 2 else '')\n"
                 "        elif action == 'restore': restore_hidden()")
GROUP1_REPLACEMENT = GROUP1_ANCHOR.replace(
    "        elif action == 'restore': restore_hidden()",
    """        elif action == 'option-b':
            # Only a signed C++ Home-8101/8102 touch dispatch has the
            # matching pending native item proof. Invalid/stale holds do nothing.
            from home_option_b import show_for_focused_top_poster
            if len(args) == 4:
                show_for_focused_top_poster(args[1:])
        elif action == 'restore': restore_hidden()""", 1)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_runtime(data: bytes) -> bytes:
    source = data.decode("utf-8")
    if "elif action == 'option-b':" in source:
        raise ValueError("Option B action already registered")
    # Accept precisely the untouched signed baseline OR the separately staged
    # Group1 home-choice-prepared runtime; never substitute speculative snippets.
    candidates = ((GROUP1_ANCHOR, GROUP1_REPLACEMENT),
                  (ANCHOR, REPLACEMENT))
    found = [(needle, replacement) for needle, replacement in candidates
             if source.count(needle) == 1]
    if len(found) != 1:
        raise ValueError("Expected exactly one authorized UI Repair runtime preimage")
    needle, replacement = found[0]
    before = source[:source.index(needle)]
    after = source[source.index(needle)+len(needle):]
    # Everything outside the one bounded dispatch remains byte-for-byte.
    result = (before + replacement + after).encode("utf-8")
    compile(result.decode("utf-8"), ENTRY, "exec")
    return result


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
