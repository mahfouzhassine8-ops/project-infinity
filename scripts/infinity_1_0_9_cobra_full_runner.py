#!/usr/bin/env python3
"""Safe entry point for Cobra Full Feature Candidate 2.

The Candidate 2 transforms use strict exact-match guards. Candidate 1 contains
a few intentionally repeated structural snippets, so this runner narrows only
the known ambiguous insertions to their semantic methods while leaving every
other source guard strict.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_1_0_9_cobra_full as full
import infinity_1_0_9_cobra_full_fixups as fixups

RELEASE = full.RELEASE
VERSION_CODE = full.VERSION_CODE
_ORIGINAL_INSERT_AFTER = full.insert_after
_ORIGINAL_FIXUP_REPLACE_ONCE = fixups.replace_once
_ORIGINAL_FIXUP_REPLACE_BETWEEN = fixups.replace_between


def candidate2_insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    if label != "Candidate 2 parental live filter":
        return _ORIGINAL_INSERT_AFTER(text, anchor, addition, label)
    target = (
        "    String needle = mSearch.trim().toLowerCase(Locale.US);\n"
        "    for (Channel channel : mChannels) {\n"
    )
    replacement = target + addition
    if text.count(target) != 1:
        raise RuntimeError(
            f"{label}: filteredChannels anchor expected exactly once, found {text.count(target)}"
        )
    return text.replace(target, replacement, 1)


def candidate2_fixup_replace_once(text: str, old: str, new: str, label: str) -> str:
    if label != "Candidate 2 auto refresh start":
        return _ORIGINAL_FIXUP_REPLACE_ONCE(text, old, new, label)
    target = (
        "    mTheme = Theme.load(this);\n"
        "    loadPersistedState();\n"
        "    buildShell();\n"
        "    if (mSources.isEmpty()) {\n"
        "      showWelcome();\n"
    )
    replacement = (
        "    mTheme = Theme.load(this);\n"
        "    loadPersistedState();\n"
        "    buildShell();\n"
        "    mMain.removeCallbacks(mAutoRefresh);\n"
        "    mMain.postDelayed(mAutoRefresh, 30L * 60L * 1000L);\n"
        "    if (mSources.isEmpty()) {\n"
        "      showWelcome();\n"
    )
    if text.count(target) != 1:
        raise RuntimeError(
            f"{label}: onCreate anchor expected exactly once, found {text.count(target)}"
        )
    return text.replace(target, replacement, 1)


def candidate2_fixup_replace_between(
    text: str, start: str, end: str, replacement: str, label: str
) -> str:
    if label != "continue watching catalogue":
        return _ORIGINAL_FIXUP_REPLACE_BETWEEN(text, start, end, replacement, label)
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"{label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"{label}: end marker missing")
    # The original fixup supplied the end marker in replacement and the generic
    # helper also preserves it from text[b:], which would duplicate the method
    # declaration. Keep exactly one declaration.
    if replacement.endswith(end):
        replacement = replacement[:-len(end)]
    return text[:a] + replacement + text[b:]


def _install_safe_guards() -> tuple[object, object, object]:
    previous_insert = full.insert_after
    previous_replace = fixups.replace_once
    previous_between = fixups.replace_between
    full.insert_after = candidate2_insert_after
    fixups.replace_once = candidate2_fixup_replace_once
    fixups.replace_between = candidate2_fixup_replace_between
    return previous_insert, previous_replace, previous_between


def _restore_safe_guards(previous: tuple[object, object, object]) -> None:
    full.insert_after, fixups.replace_once, fixups.replace_between = previous


def transform_for_fast_test(java: str) -> str:
    # Candidate 1's source phase corrects this XMLTV accumulator before the
    # Candidate 2 transform runs. Mirror that accepted baseline in the fast test.
    java = java.replace(
        "ProgramPair pair = mGuide.get(channel);",
        "ProgramPair pair = guide.get(channel);",
        1,
    )
    previous = _install_safe_guards()
    try:
        return fixups.harden_activity(full.patch_activity(java))
    finally:
        _restore_safe_guards(previous)


def source_phase(source: Path, receipt: Path) -> None:
    previous = _install_safe_guards()
    try:
        fixups.source_phase(source, receipt)
    finally:
        _restore_safe_guards(previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("source")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-source")
    p.add_argument("--source", type=Path, required=True)
    p = sub.add_parser("apk")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-apk")
    p.add_argument("--apk", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "source":
        source_phase(args.source, args.receipt)
    elif args.cmd == "verify-source":
        fixups.verify_source(args.source)
        print("PASS: Cobra Candidate 2 safe source verification")
    elif args.cmd == "apk":
        fixups.configure_deep()
        import infinity_1_0_8_deep_rebrand as deep
        deep.apk_phase(args.input, args.output, args.receipt)
    else:
        fixups.configure_deep()
        import infinity_1_0_8_deep_rebrand as deep
        deep.verify_apk(args.apk)
        print("PASS: Cobra Candidate 2 safe APK branding verification")


if __name__ == "__main__":
    main()
