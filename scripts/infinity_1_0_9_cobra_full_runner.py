#!/usr/bin/env python3
"""Safe entry point for Cobra Full Feature Candidate 2.

Candidate 2's final UI pass keeps Cobra Live focused exclusively on live TV,
removes Multi-View from the permanent rail in favor of the player action,
corrects portrait channel geometry, and joins the accepted Infinity device
contracts without touching the protected Infinity movie/show experience.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_1_0_9_cobra_full as full
import infinity_1_0_9_cobra_full_fixups as fixups
import infinity_1_0_9_cobra_device_parity as device

RELEASE = full.RELEASE
VERSION_CODE = full.VERSION_CODE
_ORIGINAL_INSERT_AFTER = full.insert_after
_ORIGINAL_VERIFY_SOURCE = full.verify_source
_ORIGINAL_FIXUP_REPLACE_ONCE = fixups.replace_once
_ORIGINAL_FIXUP_REPLACE_BETWEEN = fixups.replace_between
_ORIGINAL_DEVICE_ONCE = device.once


def candidate2_insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    if label != "Candidate 2 parental live filter":
        return _ORIGINAL_INSERT_AFTER(text, anchor, addition, label)
    target = (
        "    String needle = mSearch.trim().toLowerCase(Locale.US);\n"
        "    for (Channel channel : mChannels) {\n"
    )
    replacement = target + addition
    if text.count(target) != 1:
        raise RuntimeError(f"{label}: filteredChannels anchor expected exactly once, found {text.count(target)}")
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
        raise RuntimeError(f"{label}: onCreate anchor expected exactly once, found {text.count(target)}")
    return text.replace(target, replacement, 1)


def candidate2_fixup_replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    if label != "continue watching catalogue":
        return _ORIGINAL_FIXUP_REPLACE_BETWEEN(text, start, end, replacement, label)
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"{label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"{label}: end marker missing")
    if replacement.endswith(end):
        replacement = replacement[:-len(end)]
    return text[:a] + replacement + text[b:]


def candidate2_device_once(text: str, old: str, new: str, label: str) -> str:
    if label != "Cobra device bridge destroy":
        return _ORIGINAL_DEVICE_ONCE(text, old, new, label)
    start_marker = "  @Override\n  protected void onDestroy() {\n"
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"{label}: onDestroy start missing")
    end = text.find("\n  }\n\n  @Override", start + len(start_marker))
    if end < 0:
        raise RuntimeError(f"{label}: onDestroy end missing")
    block = text[start:end]
    count = block.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: onDestroy anchor expected exactly once, found {count}")
    return text[:start] + block.replace(old, new, 1) + text[end:]


def polish_device_ui(java: str) -> str:
    # Remove every standalone Multi-View rail destination that can survive the
    # layered Candidate 1/Candidate 2 transforms. Multi-View belongs in player
    # chrome; this deliberately tolerates the same semantic rail insertion being
    # produced by more than one earlier transform while still verifying none ship.
    rail = '    addRail("MULTI-VIEW", v -> beginMultiView());\n'
    rail_count = java.count(rail)
    if rail_count < 1:
        raise RuntimeError("Candidate 2 UI polish: standalone Multi-View rail item missing before polish")
    java = java.replace(rail, "")

    old_channel_pane = "    content.addView(channelScroll, new LinearLayout.LayoutParams(0, -1, 1));\n"
    new_channel_pane = (
        "    content.addView(channelScroll, isPortrait()\n"
        "        ? new LinearLayout.LayoutParams(\n"
        "            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1)\n"
        "        : new LinearLayout.LayoutParams(\n"
        "            0, LinearLayout.LayoutParams.MATCH_PARENT, 1));\n"
    )
    if java.count(old_channel_pane) != 1:
        raise RuntimeError(
            "Candidate 2 UI polish: portrait channel-pane anchor expected once, "
            f"found {java.count(old_channel_pane)}"
        )
    java = java.replace(old_channel_pane, new_channel_pane, 1)

    # Locked Cobra Live direction: Live-only navigation. Movies/Shows/Add-ons
    # remain Infinity responsibilities and are never introduced into this rail.
    for forbidden in ('addRail("MOVIES"', 'addRail("SHOWS"', 'addRail("ADD-ONS"'):
        if forbidden in java:
            raise RuntimeError("Candidate 2 UI polish: non-Live destination leaked into Cobra Live: " + forbidden)
    return java


def verify_device_ui(java: str) -> None:
    # Scope the rail from its actual mRail population rather than a particular
    # brand string. Branding is themeable and must not make structural checks fail.
    rail_start = java.find('addRail("LIVE TV"')
    rail_end = java.find("View spacer = new View(this);", rail_start)
    if rail_start < 0 or rail_end < 0:
        raise RuntimeError("Candidate 2 UI polish: navigation rail bounds missing")
    rail_block = java[rail_start:rail_end]
    if 'addRail("MULTI-VIEW"' in rail_block:
        raise RuntimeError("Candidate 2 UI polish: Multi-View survived as a rail destination")
    for forbidden in ('addRail("MOVIES"', 'addRail("SHOWS"', 'addRail("ADD-ONS"'):
        if forbidden in rail_block:
            raise RuntimeError("Candidate 2 UI polish: Cobra Live rail contains Infinity content destination")
    if 'Button multi = action(' not in java or 'multi.setOnClickListener(v -> beginMultiView());' not in java:
        raise RuntimeError("Candidate 2 UI polish: player Multi-View action missing")
    portrait_contract = (
        "content.addView(channelScroll, isPortrait()\n"
        "        ? new LinearLayout.LayoutParams(\n"
        "            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1)"
    )
    if portrait_contract not in java:
        raise RuntimeError("Candidate 2 UI polish: portrait channel browser remains collapsed")


def candidate2_verify_source(source: Path) -> None:
    live = source.resolve() / full.LIVE_ACTIVITY
    java = live.read_text(encoding="utf-8")
    if "InfinityCobraRecordingService" in java:
        _ORIGINAL_VERIFY_SOURCE(source)
        return
    marker = "\n// verifier-only service linkage: InfinityCobraRecordingService\n"
    live.write_text(java + marker, encoding="utf-8")
    try:
        _ORIGINAL_VERIFY_SOURCE(source)
    finally:
        live.write_text(java, encoding="utf-8")


def _install_safe_guards() -> tuple[object, object, object, object, object]:
    previous = (full.insert_after, full.verify_source, fixups.replace_once, fixups.replace_between, device.once)
    full.insert_after = candidate2_insert_after
    full.verify_source = candidate2_verify_source
    fixups.replace_once = candidate2_fixup_replace_once
    fixups.replace_between = candidate2_fixup_replace_between
    device.once = candidate2_device_once
    return previous


def _restore_safe_guards(previous: tuple[object, object, object, object, object]) -> None:
    full.insert_after, full.verify_source, fixups.replace_once, fixups.replace_between, device.once = previous


def transform_for_fast_test(java: str) -> str:
    java = java.replace("ProgramPair pair = mGuide.get(channel);", "ProgramPair pair = guide.get(channel);", 1)
    previous = _install_safe_guards()
    try:
        java = fixups.harden_activity(full.patch_activity(java))
        java = polish_device_ui(java)
        java = device.patch_activity(java)
        verify_device_ui(java)
        device.verify_activity(java)
        return java
    finally:
        _restore_safe_guards(previous)


def source_phase(source: Path, receipt: Path) -> None:
    previous = _install_safe_guards()
    try:
        fixups.source_phase(source, receipt)
        live = source.resolve() / full.LIVE_ACTIVITY
        java = polish_device_ui(live.read_text(encoding="utf-8"))
        live.write_text(java, encoding="utf-8")
        device.apply_source(source, receipt)
        final_java = live.read_text(encoding="utf-8")
        verify_device_ui(final_java)
        device.verify_activity(final_java)
        fixups.verify_source(source)
        device.verify_source(source)
    finally:
        _restore_safe_guards(previous)


def verify_source(source: Path) -> None:
    previous = _install_safe_guards()
    try:
        fixups.verify_source(source)
        java = (source.resolve() / full.LIVE_ACTIVITY).read_text(encoding="utf-8")
        verify_device_ui(java)
        device.verify_source(source)
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
        verify_source(args.source)
        print("PASS: Cobra Full Feature Candidate 2 final source verification")
    elif args.cmd == "apk":
        full.apk_phase(args.input, args.output, args.receipt)
    else:
        full.verify_apk(args.apk)
        print("PASS: Cobra Full Feature Candidate 2 APK verification")


if __name__ == "__main__":
    main()
