#!/usr/bin/env python3
"""Validate the Kodi 22 Piers builder contract without running Android builds."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope", choices=("all", "workflow", "docs"), default="all"
    )
    scope = parser.parse_args().scope

    workflow = read(".github/workflows/build-kodi.yml")
    readme = read("README.md")
    addons = read("kodi-config/addons.txt")
    sources = read("kodi-config/sources.xml")
    preflight = read("scripts/local-gha-preflight.ps1")

    checks: list[tuple[str, str, bool]] = []

    def check(group: str, label: str, condition: bool) -> None:
        checks.append((group, label, condition))

    check("workflow", "Piers is the workflow default", "default: 'Piers'" in workflow)
    for release in ("Piers", "Omega", "Nexus", "Matrix"):
        check(
            "workflow",
            f"{release} remains selectable",
            f"          - {release}\n" in workflow,
        )
    check(
        "workflow",
        "raw master is not exposed as a release choice",
        "          - master\n" not in workflow,
    )
    check(
        "workflow",
        "ABI default is an exact selectable value",
        "        default: 'arm64-v8a'" in workflow
        and "          - arm64-v8a\n" in workflow,
    )
    check(
        "workflow",
        "Piers resolves to rolling master and Android 37.0",
        bool(
            re.search(
                r"Piers\).*?SOURCE_REF=master.*?ADDON_CHANNEL=piers"
                r".*?ANDROID_PLATFORM=37\.0.*?ANDROID_BUILD_TOOLS=37\.0\.0"
                r".*?IS_PRERELEASE=true",
                workflow,
                re.DOTALL,
            )
        ),
    )
    check(
        "workflow",
        "legacy Android 34 and Piers Android 37.0 SDKs are installed",
        "platforms;android-34 build-tools;34.0.0" in workflow
        and "platforms;android-37.0 build-tools;37.0.0" in workflow,
    )
    check("workflow", "NDK r28c remains configured", "android-ndk-r28c" in workflow)
    check("workflow", "Java 17 remains configured", "java-version: '17'" in workflow)
    check(
        "workflow",
        "source checkout uses the resolved ref",
        workflow.count("steps.kodi.outputs.source_ref") >= 4,
    )
    check(
        "workflow",
        "depends cache uses the upstream depends fingerprint",
        "steps.source.outputs.depends_fingerprint" in workflow,
    )
    check(
        "workflow",
        "signing uses the selected build-tools directory",
        'BUILD_TOOLS="$ANDROID_HOME/build-tools/${{ steps.kodi.outputs.android_build_tools }}"'
        in workflow
        and "$ANDROID_HOME/build-tools/34.0.0/zipalign" not in workflow,
    )
    check(
        "workflow",
        "Piers releases are marked prerelease",
        "prerelease: ${{ steps.kodi.outputs.is_prerelease == 'true' }}" in workflow,
    )
    check(
        "workflow",
        "workflow runs the contract validator",
        "python3 scripts/validate-kodi22-builder.py" in workflow,
    )

    check(
        "docs",
        "README identifies Piers as Kodi 22 prerelease",
        "Piers" in readme and "Kodi 22" in readme and "prerelease" in readme.lower(),
    )
    check(
        "docs",
        "addon examples use the Piers channel",
        "https://mirrors.kodi.tv/addons/piers/" in addons,
    )
    check(
        "docs",
        "source example uses the Piers channel",
        "<name>Kodi Piers Repo</name>" in sources
        and "https://mirrors.kodi.tv/addons/piers/" in sources,
    )
    check(
        "docs",
        "local preflight dispatches Piers",
        preflight.count("--input branch=Piers") == 2
        and "--input branch=Omega" not in preflight,
    )

    selected = [item for item in checks if scope == "all" or item[0] == scope]
    failures = [label for _, label, passed in selected if not passed]
    for _, label, passed in selected:
        print(f"[{'PASS' if passed else 'FAIL'}] {label}")
    if failures:
        print(f"\n{len(failures)} validation check(s) failed.")
        return 1
    print(f"\nAll {len(selected)} validation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
