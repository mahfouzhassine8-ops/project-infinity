"""Selected signed install-over and normal startup checks on a disposable ARM64 emulator."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import time
from zipfile import ZipFile
from xml.etree import ElementTree

from stage_qa import HERE, ROOT, file_sha, load, require

sys.path.insert(0, str(ROOT / "repairs/infinity-movies-continue-cast-2103486-20261112/release"))
from common_release import signature, tools

PACKAGE = "com.projectinfinity.kodi"
PROCESS = PACKAGE + ":kodi"
PROFILE = f"/sdcard/Android/data/{PACKAGE}/files/.kodi"
MANIFEST = "addons/script.infinity.commandcenter/INFINITY-MODULES.v1"
SENTINEL = PROFILE + "/userdata/addon_data/script.infinity.commandcenter/infinity-514-qa-profile-sentinel"
EVENT = re.compile(r"InfinityStartupTrace stage=(\S+) request=\d+ invoker=(\d+) "
                   r"tid=(\d+) us=(\d+) value=(-?\d+) flags=\d+ tracked=\d+(?: addon=([\w.-]+))?$")


def adb(*args):
    return subprocess.check_output(["adb", *map(str, args)], text=True, stderr=subprocess.STDOUT, timeout=240)


def observe(*args):
    value = subprocess.run(["adb", *map(str, args)], capture_output=True, text=True, timeout=25)
    return value.stdout.strip() if value.returncode == 0 else ""


def seed_existing_modules(baseline, out, app_uid):
    # Reproduce an existing 2103514 profile on the disposable Android runner.
    # Authenticate every staged member from the exact original-signed APK.
    fixture = out / "baseline-modules"
    with ZipFile(baseline) as archive:
        lines = archive.read("assets/" + MANIFEST).decode("ascii").splitlines()
        require(lines[:3] == ["INFINITY-MODULES/1", "package\t0.3.5.84", "protocol\t1"],
                "Incorrect signed module generation for the Android fixture")
        for _, digest, name in (line.split("\t") for line in lines if line.startswith("file\t")):
            path = Path(name)
            require(not path.is_absolute() and ".." not in path.parts, "Invalid fixture member path")
            data = archive.read("assets/addons/" + name)
            require(hashlib.sha256(data).hexdigest() == digest, "Baseline fixture member does not match signed manifest")
            target = fixture / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for name in (MANIFEST, MANIFEST + ".sig"):
            (fixture / name.removeprefix("addons/")).write_bytes(archive.read("assets/" + name))
    require(adb("shell", "getprop", "ro.kernel.qemu").strip() == "1" and
            app_uid.isdigit() and int(app_uid) >= 10000, "Disposable emulator app UID required")
    adb("root")
    adb("wait-for-device")
    require(adb("shell", "id", "-u").strip() == "0" and adb("shell", "getenforce").strip() == "Enforcing",
            "Expected debug-emulator transport with SELinux enforcing")
    adb("shell", "mkdir", "-p", PROFILE + "/addons")
    adb("push", str(fixture) + "/.", PROFILE + "/addons/")
    backing = f"/data/media/0/Android/data/{PACKAGE}/files/.kodi"
    adb("shell", "chown", "-R", f"{app_uid}:{app_uid}", backing)
    adb("shell", "restorecon", "-RF", backing)


def package_record():
    text = adb("shell", "dumpsys", "package", PACKAGE)
    patterns = dict(versionCode=r"\bversionCode=(\d+)", uid=r"\b(?:userId|appId)=(\d+)",
                    dataDir=r"\bdataDir=(\S+)", firstInstallTime=r"\bfirstInstallTime=([^\r\n]+)")
    result = {}
    for name, pattern in patterns.items():
        value = re.search(pattern, text)
        require(value is not None, "Installed package omitted " + name)
        result[name] = value.group(1).strip()
    return result


def startup_markers(log):
    invokers = {}
    for line in log.splitlines():
        match = EVENT.search(line)
        if not match:
            continue
        stage, ident, tid, stamp, value, addon = match.groups()
        key = (ident, tid)
        if stage == "interpreter.create" and addon == "script.infinity.commandcenter":
            invokers[key] = [int(stamp)]
        elif stage == "interpreter.returned" and value == "1" and len(invokers.get(key, [])) == 1:
            invokers[key].append(int(stamp))
        elif stage == "interpreter.created" and len(invokers.get(key, [])) == 2:
            stamps = invokers[key]
            if stamps[0] <= stamps[1] <= int(stamp):
                return dict(addon="script.infinity.commandcenter", invoker=int(ident), tid=int(tid),
                            create_us=stamps[0], returned_us=stamps[1], bookkeeping_done_us=int(stamp))
    return None


def choose_infinity():
    # UI actions apply only to an exact label in this package's fresh chooser.
    path = "/sdcard/infinity514-emulator-chooser.xml"
    if not observe("shell", "uiautomator", "dump", path):
        return False
    try:
        tree = ElementTree.fromstring(observe("shell", "cat", path))
    except ElementTree.ParseError:
        return False
    for node in tree.iter("node"):
        if node.get("package") != PACKAGE or not any(
                (node.get(name) or "").strip().casefold() == "infinity" for name in ("text", "content-desc")):
            continue
        bounds = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
        if bounds:
            left, top, right, bottom = map(int, bounds.groups())
            if left < right and top < bottom:
                adb("shell", "input", "tap", (left + right) // 2, (top + bottom) // 2)
                return True
    return False


def launch_and_verify(manifest_sha, with_trace=False):
    launch = adb("shell", "am", "start", "-W", "-n", PACKAGE + "/.Splash")
    report = dict(launch_ok="Status: ok" in launch and "Error" not in launch,
                  process_observed=False, manifest_readable=False, manifest_matched=False,
                  startup_trace=None, trace_seen=False, observed_module_sha256=None, complete=False)
    if not report["launch_ok"]:
        return report
    deadline = time.monotonic() + 145
    last_choose = 0
    while time.monotonic() < deadline:
        pid = observe("shell", "pidof", PROCESS)
        manifest = observe("shell", "cat", PROFILE + "/" + MANIFEST)
        installed = hashlib.sha256((manifest + "\n").encode()).hexdigest() if manifest else ""
        report["process_observed"] |= pid.isdigit()
        report["manifest_readable"] |= bool(manifest)
        report["manifest_matched"] |= installed == manifest_sha
        if installed:
            report["observed_module_sha256"] = installed
        marker = None
        if pid.isdigit() and with_trace:
            log = adb("logcat", "-d", "-v", "raw", "--pid=" + pid, "-s", "Kodi:I")
            report["trace_seen"] |= "InfinityStartupTrace stage=" in log
            marker = startup_markers(log)
            if marker is not None:
                report["startup_trace"] = marker
        if not pid.isdigit() and time.monotonic() - last_choose > 15:
            choose_infinity()
            last_choose = time.monotonic()
        if pid.isdigit() and installed == manifest_sha:
            if not with_trace or marker is not None:
                report.update(complete=True, engine_pid=int(pid), installed_module_sha256=installed,
                              startup_trace=marker)
                break
        time.sleep(3)
    return report


def run(args):
    require(adb("shell", "getprop", "ro.kernel.qemu").strip() == "1" and
            "arm64-v8a" in adb("shell", "getprop", "ro.product.cpu.abilist"),
            "Disposable Android emulator with ARM64 execution required")
    platform = dict(sdk=adb("shell", "getprop", "ro.build.version.sdk").strip(),
                    kernel_arch=adb("shell", "uname", "-m").strip(),
                    native_bridge=adb("shell", "getprop", "ro.dalvik.vm.native.bridge").strip())
    require("versionCode=" not in observe("shell", "dumpsys", "package", PACKAGE),
            "A fresh emulator is required; package or profile will not be cleared")
    inventory, bundles, *_ = tools()
    apk = dict(baseline=args.baseline, candidate=args.candidate, recovery=args.recovery)
    baseline = load(HERE / "SCOPE.json")["baseline"]
    proof = load(HERE / "MODULE-PRESERVATION.json")
    receipts = dict(candidate=load(args.candidate_receipt), recovery=load(args.recovery_receipt))
    require(file_sha(apk["baseline"]) == baseline["apk_sha256"], "Wrong protected 2103514 APK")
    versions = {}
    records = {}
    source_signatures = {}
    for kind, file in apk.items():
        sha = file_sha(file)
        signature(file)
        with ZipFile(file) as archive:
            manifest = archive.read("AndroidManifest.xml")
            require(inventory.manifest_tree(manifest)["attributes"]["package"]["value"] == PACKAGE,
                    "Package identity changed")
            versions[kind] = bundles.normalize_manifest(manifest)[1]
            manifest_sha = hashlib.sha256(archive.read("assets/" + MANIFEST)).hexdigest()
        if kind in receipts:
            expected = proof["candidate" if kind == "candidate" else "forward-recovery"]
            require(receipts[kind]["signed_apk_sha256"] == sha and
                    receipts[kind]["versionCode"] == versions[kind] and manifest_sha == expected["manifest_sha256"],
                    "Signed APK, release receipt, or module generation differs")
        source_signatures[kind] = manifest_sha
    require(versions["baseline"] == 2103514 < versions["candidate"] < versions["recovery"],
            "Monotonic versions required without downgrading")

    args.out.mkdir()
    sentinel = args.out / "profile-sentinel"
    sentinel.write_text("infinity514-qa-synthetic-profile\n")
    for kind, file in apk.items():
        install = ["install"] if kind == "baseline" else ["install", "-r"]
        require("Success" in adb(*install, file), "Android PackageManager install failed: " + kind)
        identity = package_record()
        require(int(identity["versionCode"]) == versions[kind], "Wrong installed version")
        if kind == "baseline":
            adb("shell", "input", "keyevent", "82")
            # Equivalent to allowing Android's onboarding permission on this
            # disposable device. The signed APK and its app UID are untouched.
            adb("shell", "appops", "set", PACKAGE, "MANAGE_EXTERNAL_STORAGE", "allow")
            observe("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS")
            adb("shell", "mkdir", "-p", str(Path(SENTINEL).parent))
            adb("push", sentinel, SENTINEL)
            seed_existing_modules(file, args.out, identity["uid"])
        else:
            require(all(identity[field] == records["baseline"]["package"][field]
                        for field in ("uid", "dataDir", "firstInstallTime")), "Installation changed profile owner")
        require(observe("shell", "cat", SENTINEL) == sentinel.read_text().strip(), "Profile sentinel changed")
        records[kind] = dict(package=identity, installs=True, profile_sentinel=True)
        print(f"{kind}: Android PackageManager installed {versions[kind]} over the selected profile", flush=True)
        records[kind].update(launch_and_verify(source_signatures[kind], kind == "candidate"))
        require(observe("shell", "cat", SENTINEL) == sentinel.read_text().strip(), "Launch changed profile sentinel")
        shown = {field: records[kind][field] for field in (
            "launch_ok", "process_observed", "manifest_readable", "manifest_matched", "observed_module_sha256", "trace_seen", "complete")}
        print(f"{kind}: selected startup {json.dumps(shown, sort_keys=True)}", flush=True)
        inventory.save(args.out / "ANDROID-VERIFICATION.json", dict(
            steps=records, completes_pair=kind == "recovery", platform=platform,
            all_startup_verified=kind == "recovery" and all(record["complete"] for record in records.values()),
            fixture="Authenticated 2103514 installed-module bytes on the disposable emulator",
            Fold="NOT_RUN", shutdown="NOT_SELECTED", data_reset=False, uninstall=False))
    require(all(record["complete"] for record in records.values()), "Normal startup observation incomplete")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for path in ("baseline", "candidate", "recovery", "candidate-receipt", "recovery-receipt", "out"):
        parser.add_argument("--" + path, type=Path, required=True)
    run(parser.parse_args())
