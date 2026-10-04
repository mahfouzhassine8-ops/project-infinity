#!/usr/bin/env python3
"""Add conditional-route regressions while retaining the entire inherited suite."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--build", type=Path, required=True)
args = parser.parse_args()
tests = args.build / "xbmc/src/test/java/com/projectinfinity/kodi"
shutil.copy2(HERE / "ConditionalPowerRouteTest.java", tests / "ConditionalPowerRouteTest.java")
with tempfile.TemporaryDirectory(prefix="infinity-195-power-fixture-") as directory:
    root = Path(directory)
    fixture = root / "addons/skin.infinity.diggz/unified/DialogButtonMenu.xml"
    fixture.parent.mkdir(parents=True)
    shutil.copy2(HERE.parent / "e2e-mobile-2103303/fixtures/unified-DialogButtonMenu.xml", fixture)
    subprocess.run(["git", "apply", "--include=addons/skin.infinity.diggz/unified/DialogButtonMenu.xml",
                    str((HERE.parent / "mobile-regressions-2103304/skin-194-repair.patch").resolve())],
                   cwd=root, check=True)
    target = args.build / "xbmc/src/test/resources/power-profiles/conditional195/DialogButtonMenu.xml"
    target.parent.mkdir(parents=True)
    shutil.copy2(fixture, target)
