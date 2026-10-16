#!/usr/bin/env python3
"""Preinstall the runner's stable emulator, retrying only its observed bad ZIP.

The pinned runner installs ``emulator`` before any ``emulator-build`` override:
https://github.com/ReactiveCircus/android-emulator-runner/blob/a421e43855164a8197daf9d8d40fe71c6996bb0d/src/sdk-installer.ts
SDK package/channel/SDK-root options: https://developer.android.com/tools/sdkmanager

This prepares disposable CI infrastructure. It never retries an application test,
changes app data, deletes SDK directories, or treats a failed install as success.
"""
import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path


BAD_ARCHIVE = "An error occurred while preparing SDK package Android Emulator: Archive is not a ZIP archive."
MAX_ATTEMPTS = 3


def run_command(command, log_path):
    with log_path.open("w") as log:
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=180, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            log.write("\nEmulator preparation command exceeded 180 seconds.\n")
            code = 124
    return code, log_path.read_text(errors="replace")


def prepare(sdk_root, out, *, run=run_command, pause=time.sleep):
    sdk_root, out = Path(sdk_root).resolve(), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"passed": False, "scope": "disposable emulator setup only",
              "application_test_retried": False, "attempts": []}
    try:
        command = [str(sdk_root / "cmdline-tools/latest/bin/sdkmanager"),
                   "--sdk_root=" + str(sdk_root), "--install", "emulator", "--channel=0"]
        for attempt in range(1, MAX_ATTEMPTS + 1):
            log = out / ("sdkmanager-attempt-%d.log" % attempt)
            code, output = run(command, log)
            bad_archive = BAD_ARCHIVE in output
            report["attempts"].append({"attempt": attempt, "exit_code": code,
                                       "observed_invalid_emulator_zip": bad_archive,
                                       "log": log.name})
            if code == 0 and not bad_archive:
                break
            if code == 124 or not bad_archive or attempt == MAX_ATTEMPTS:
                raise RuntimeError("Emulator SDK installation failed; see " + str(log))
            print("Retrying only the observed invalid Android Emulator ZIP (attempt %d/%d)." %
                  (attempt + 1, MAX_ATTEMPTS), flush=True)
            pause(2 * attempt)

        properties = (sdk_root / "emulator/source.properties").read_text()
        revision = re.search(r"(?m)^Pkg\.Revision\s*=\s*(\S+)\s*$", properties)
        if revision is None:
            raise RuntimeError("Installed emulator has no package revision")
        executable = sdk_root / "emulator/emulator"
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise RuntimeError("Installed emulator executable is missing or not executable")
        code, version = run([str(executable), "-version"], out / "emulator-version.log")
        reported = re.search(r"Android emulator version ([0-9]+(?:\.[0-9]+)+)", version)

        def version_parts(value):
            parts = [int(part) for part in value.split(".")]
            while parts and parts[-1] == 0:
                parts.pop()
            return parts

        if (code != 0 or reported is None or
                version_parts(revision.group(1)) != version_parts(reported.group(1))):
            raise RuntimeError("Installed emulator did not report its recorded package revision")
        report.update(passed=True, emulator_revision=revision.group(1),
                      executable_revision=reported.group(1))
        return report
    except Exception as error:
        report["failure"] = str(error)
        raise
    finally:
        (out / "EMULATOR-PREPARATION.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", default=os.environ.get("ANDROID_HOME"), required=False)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.sdk_root:
        parser.error("--sdk-root or ANDROID_HOME is required")
    print(json.dumps(prepare(args.sdk_root, args.out), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
