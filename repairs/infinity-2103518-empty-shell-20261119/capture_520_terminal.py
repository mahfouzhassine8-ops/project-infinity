"""Capture the existing Infinity 2103520 diagnostics from one USB-connected device."""
from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from filter_fold_trace import filtered_lines

PACKAGE = "com.projectinfinity.kodi"
VERSION = "2103520"


def run():
    adb = shutil.which("adb")
    if adb is None:
        print("ADB is missing from this Terminal's PATH.", file=sys.stderr)
        return 1
    usb = [adb, "-d"]
    try:
        state = subprocess.run([*usb, "get-state"], capture_output=True, text=True, timeout=15)
        if state.returncode or state.stdout.strip() != "device":
            print("Connect and unlock the Fold. Allow USB debugging if prompted.", file=sys.stderr)
            return 1
        package = subprocess.run([*usb, "shell", "dumpsys", "package", PACKAGE],
                                 capture_output=True, text=True, timeout=15, check=True)
    except (subprocess.SubprocessError, OSError):
        print("ADB could not read the installed Infinity version from the Fold.", file=sys.stderr)
        return 1

    version = re.search(r"^\s*versionCode=(\d+)\b", package.stdout, re.MULTILINE)
    if version is None or version.group(1) != VERSION:
        print("Infinity 2103520 must be installed for this capture.", file=sys.stderr)
        return 1

    folder = Path.home() / "Downloads"
    if not folder.is_dir():
        folder = Path.cwd()
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    count = 0
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=folder,
                                     prefix=f"Infinity-520-Fold-{stamp}-", suffix=".txt",
                                     delete=False) as result:
        with subprocess.Popen(
            [*usb, "logcat", "-v", "threadtime", "-T", "1",
             "Kodi:I", "InfinityPersistenceMutex:I", "*:S"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            encoding="utf-8", errors="replace",
        ) as stream:
            print(f"Capture running. Open Infinity normally. Press Control-C when finished.\n"
                  f"Filtered file {result.name}", flush=True)
            try:
                for line in filtered_lines(stream.stdout):
                    result.write(line + "\n")
                    result.flush()
                    count += 1
            except KeyboardInterrupt:
                pass
            finally:
                # Stop the local log reader. The Android app stays in its current state.
                if stream.poll() is None:
                    stream.terminate()
                    try:
                        stream.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        stream.kill()
            if not count:
                print("The capture received no matching diagnostic events.", file=sys.stderr)
                return 1
    print(f"Saved {count} filtered events to {result.name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run())
