#!/usr/bin/env python3
"""Harden Kodi Android touch startup against GUI-service races.

The Android event loop can receive a touch-down before Kodi has registered the
GUI component. Kodi 21.3's CGenericTouchActionHandler::QuerySupportedGestures()
currently dereferences CServiceBroker::GetGUI() without a null check. On fast
startup/touch this can SIGSEGV at address 0x8 inside libkodi.so.

This patch is intentionally narrow: when the GUI is not registered yet, report
no supported gestures and drop only that premature gesture query. Normal touch
behavior is unchanged once the GUI exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TARGET = Path("xbmc/input/touch/generic/GenericTouchActionHandler.cpp")

OLD = '''int CGenericTouchActionHandler::QuerySupportedGestures(float x, float y)\n{\n  CGUIMessage msg(GUI_MSG_GESTURE_NOTIFY, 0, 0, static_cast<int>(std::round(x)),\n                  static_cast<int>(std::round(y)));\n  if (!CServiceBroker::GetGUI()->GetWindowManager().SendMessage(msg))\n    return 0;\n'''

NEW = '''int CGenericTouchActionHandler::QuerySupportedGestures(float x, float y)\n{\n  CGUIComponent* gui = CServiceBroker::GetGUI();\n  if (gui == nullptr)\n    return 0;\n\n  CGUIMessage msg(GUI_MSG_GESTURE_NOTIFY, 0, 0, static_cast<int>(std::round(x)),\n                  static_cast<int>(std::round(y)));\n  if (!gui->GetWindowManager().SendMessage(msg))\n    return 0;\n'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(source: Path) -> dict:
    path = source / TARGET
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    required = (
        "CGUIComponent* gui = CServiceBroker::GetGUI();",
        "if (gui == nullptr)",
        "if (!gui->GetWindowManager().SendMessage(msg))",
    )
    for needle in required:
        if needle not in text:
            raise RuntimeError("missing touch-startup guard contract: " + needle)
    if "CServiceBroker::GetGUI()->GetWindowManager().SendMessage(msg)" in text:
        raise RuntimeError("unguarded touch GUI dereference remains")
    return {
        "schema": 1,
        "target": str(TARGET),
        "failure_class": "android_touch_startup_gui_null_sigsegv",
        "guard": "CServiceBroker::GetGUI() != nullptr",
        "fallback": "return 0 supported gestures",
        "normal_touch_behavior_changed_after_gui_ready": False,
        "sha256": sha(path),
    }


def apply(source: Path, receipt: Path) -> None:
    source = source.resolve()
    path = source / TARGET
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    count = text.count(OLD)
    if count != 1:
        raise RuntimeError(f"touch-startup source anchor expected exactly once, found {count}")
    before = sha(path)
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    result = verify(source)
    result["before_sha256"] = before
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Kodi Android touch startup GUI-null guard applied")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify")
    p.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "apply":
        apply(args.source, args.receipt)
    else:
        print(json.dumps(verify(args.source.resolve()), indent=2, sort_keys=True))
        print("PASS: Kodi Android touch startup GUI-null guard verified")


if __name__ == "__main__":
    main()
