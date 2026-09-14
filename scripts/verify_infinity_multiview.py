#!/usr/bin/env python3
"""Static repository gate for Infinity Live 2-up ExoPlayer Multi-View."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "addons/script.infinity.live"
REQUIRED = (
    ADDON / "resources/lib/multiview.py",
    ADDON / "resources/lib/focus.py",
    ADDON / "resources/lib/__init__.py",
    ROOT / "patches/infinity-multiview/InfinityMultiViewController.java.in",
    ROOT / "scripts/infinity_1_0_9_multiview_release.py",
    ROOT / "scripts/validate_infinity_multiview_java.py",
)


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
    if missing:
        raise SystemExit("missing Multi-View files: " + ", ".join(missing))

    parsed = 0
    for path in ADDON.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parsed += 1

    py = (ADDON / "resources/lib/multiview.py").read_text(encoding="utf-8")
    for needle in (
        '"mode": "split2"',
        '"audio_tile": 0',
        '"MULTI-VIEW"',
        'StartAndroidActivity(',
        'MAIN_CLASS = PACKAGE + ".Main"',
        'os.chmod(path, 0o600)',
    ):
        if needle not in py:
            raise SystemExit("missing Python Multi-View contract: " + needle)
    if "CobraTV" in py or "cobratv" in py or "libmpv" in py:
        raise SystemExit("third-party player/reference leaked into Infinity Multi-View Python")

    init = (ADDON / "resources/lib/__init__.py").read_text(encoding="utf-8")
    if "install_multiview_hooks()" not in init or init.index("install_multiview_hooks()") > init.index("install_focus_contracts()"):
        raise SystemExit("Multi-View hook must install before focus graph")

    focus = (ADDON / "resources/lib/focus.py").read_text(encoding="utf-8")
    if focus.count('"MULTI-VIEW"') != 1:
        raise SystemExit("D-pad Multi-View focus owner missing or duplicated")

    java = (ROOT / "patches/infinity-multiview/InfinityMultiViewController.java.in").read_text(encoding="utf-8")
    for needle in (
        "class InfinityMultiViewController",
        "new ExoPlayer.Builder",
        "DefaultHttpDataSource.Factory",
        "DefaultMediaSourceFactory",
        "setVideoTextureView(texture)",
        "clearVideoTextureView(texture)",
        'TAG_SCHEME = "infinity-multiview"',
        "setAudible(i == mAudioTile)",
        "mTileContainer.setOrientation",
        "file.delete()",
    ):
        if needle not in java:
            raise SystemExit("missing Java Multi-View contract: " + needle)
    for forbidden in ("android.media.MediaPlayer", "new MediaPlayer(", "libmpv", "Flutter", "CobraTV", "cobratv"):
        if forbidden in java:
            raise SystemExit("forbidden third-party dependency/reference in Multi-View Java: " + forbidden)

    release = (ROOT / "scripts/infinity_1_0_9_multiview_release.py").read_text(encoding="utf-8")
    for needle in ('VERSION_CODE = 2103130', 'RELEASE = "1.0.9-Live-ExoPlayer-MultiView-Candidate-1"', '"kodi_application_player_changed": False'):
        if needle not in release:
            raise SystemExit("missing Multi-View release contract: " + needle)

    print("Infinity ExoPlayer Multi-View static verification: PASS")
    print(f"Infinity Live Python files parsed: {parsed}")
    print("2-up overlay, single-audio owner, responsive split/stack and one-shot request contract present.")


if __name__ == "__main__":
    main()
