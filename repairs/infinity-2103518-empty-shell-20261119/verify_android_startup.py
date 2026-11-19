"""Run only the selected startup probe on a disposable Android 17 emulator."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = ROOT / "repairs/infinity-2103514-targeted-20261118"
sys.path.insert(0, str(PREVIOUS))
from typed_movie_playback_android import rpc, until
from verify_android import PACKAGE, PROFILE, adb, observe, launch_and_verify, package_record
import common_release as release

DRIVER = "script.infinityqastartup.driver"
WAVES = 6
WIDTH = 8
WORKERS = [[f"script.infinityqastartup.w{wave}.s{slot}" for slot in range(WIDTH)] for wave in range(WAVES)]
MANIFEST = "script.infinity.commandcenter/INFINITY-MODULES.v1"
TRACE = re.compile(r"InfinityStartupTrace stage=([a-z._]+) request=(\d+) invoker=(-?\d+) "
                   r"tid=(\d+) us=(\d+) value=(-?\d+) flags=\d+ tracked=\d+(?: addon=([\w.-]+))?$")
MARKER = re.compile(r"INFINITY_SELECTED_STARTUP_(BEGIN|END) (script\.infinityqastartup\.w\d\.s\d) "
                    r"(\d+) (\d+)$")


def stage_addon(addons, addon, body):
    root = addons / addon
    root.mkdir()
    (root / "addon.xml").write_text(
        f'<addon id="{addon}" name="{addon}" version="1.0.0" provider-name="Infinity QA">'
        '<requires><import addon="xbmc.python" version="3.0.1"/></requires>'
        '<extension point="xbmc.python.script" library="main.py"/>'
        '<extension point="xbmc.addon.metadata"><summary lang="en_GB">Selected startup fixture</summary>'
        '</extension></addon>')
    (root / "main.py").write_text(body)


def build_fixture(out, apk):
    profile = out / "fixture"
    addons = profile / "addons"
    addons.mkdir(parents=True)
    with ZipFile(apk) as archive:
        raw_manifest = archive.read("assets/addons/" + MANIFEST)
        rows = raw_manifest.decode("ascii").splitlines()
        release.require(rows[:3] == ["INFINITY-MODULES/1", "package\t0.3.5.87", "protocol\t1"],
                        "Exact signed 2103518 module generation required")
        for _, digest, member in (line.split("\t") for line in rows if line.startswith("file\t")):
            name = Path(member)
            release.require(not name.is_absolute() and ".." not in name.parts and len(name.parts) >= 2,
                            "Invalid signed fixture path")
            raw = archive.read("assets/addons/" + member)
            release.require(release.digest(raw) == digest, "Signed module source hash differs")
            target = addons / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        for member in (MANIFEST, MANIFEST + ".sig"):
            (addons / member).write_bytes(archive.read("assets/addons/" + member))
    for wave in WORKERS:
        for addon in wave:
            stage_addon(addons, addon, f"""import sys, time, threading, xbmc
assert sys.version_info[:3] == (3, 11, 7)
addon = {addon!r}
def event(phase):
    xbmc.log('INFINITY_SELECTED_STARTUP_' + phase + ' ' + addon + ' ' +
             str(threading.get_native_id()) + ' ' + str(time.monotonic_ns()), xbmc.LOGINFO)
event('BEGIN')
# Release the shared GIL normally while adjacent invokers initialize.
xbmc.Monitor().waitForAbort(0.8)
event('END')
""")
    stage_addon(addons, DRIVER, f"""import xbmc
monitor = xbmc.Monitor()
for wave in {WORKERS!r}:
    for addon in wave:
        xbmc.executebuiltin('RunScript(' + addon + ')')
    if monitor.waitForAbort(0.30):
        break
""")
    user = profile / "userdata"
    user.mkdir()
    (user / "guisettings.xml").write_text(
        '<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting>'
        '<setting id="general.addonupdates">2</setting><setting id="services.esenabled">true</setting>'
        '<setting id="services.esallinterfaces">false</setting></settings>')
    return profile, release.digest(raw_manifest)


def records(pid):
    log = adb("logcat", "-d", "-v", "raw", "--pid=" + pid, "-s", "Kodi:I")
    trace = []
    markers = {}
    for line in log.splitlines():
        found = TRACE.search(line)
        if found:
            stage, request, invoker, tid, us, value, addon = found.groups()
            trace.append(dict(stage=stage, request=int(request), invoker=int(invoker),
                              tid=int(tid), monotonic_us=int(us), value=int(value), addon=addon))
        found = MARKER.search(line)
        if found:
            event, addon, tid, ns = found.groups()
            markers.setdefault(addon, {})[event.lower()] = dict(tid=int(tid), monotonic_ns=int(ns))
    return trace, markers


def analyze(trace, markers):
    creates = {row["addon"]: row for row in trace if row["stage"] == "interpreter.create" and row["addon"]}
    by_worker = {}
    for row in trace:
        by_worker.setdefault((row["invoker"], row["tid"]), []).append(row)
    summary = {}
    for addon in (aid for group in WORKERS for aid in group):
        create = creates.get(addon)
        row = dict(timing=markers.get(addon, {}), create=create, lifecycle=[])
        if create:
            events = by_worker[create["invoker"], create["tid"]]
            row["lifecycle"] = [event for event in events
                                if event["monotonic_us"] >= create["monotonic_us"]]
            row["complete"] = all(any(e["stage"] == stage and
                                     (stage != "interpreter.returned" or e["value"] == 1)
                                     for e in row["lifecycle"])
                                  for stage in ("interpreter.returned", "interpreter.created",
                                                "bytecode.enter", "bytecode.returned"))
        summary[addon] = row
    return summary


def run(out):
    request_path = HERE / "ANDROID-STARTUP.json"
    request = release.load(request_path)
    release.require(os.environ.get("GITHUB_ACTIONS") == "true" and
                    os.environ.get("GITHUB_REPOSITORY") == release.REPO and
                    os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and
                    os.environ.get("GITHUB_REF", "").endswith(
                        "/work/infinity-2103518-empty-shell-investigation-20261119") and
                    os.environ.get("SELECTED_AUTHORIZATION") == release.sha(request_path) and
                    request["driver_sha256"] == release.sha(Path(__file__)) and
                    request["application_shutdown_selected"] is False and
                    request["production_mutations_selected"] is False,
                    "Wrong selected release and test")
    release.require(adb("shell", "getprop", "ro.kernel.qemu").strip() == "1" and
                    adb("shell", "getprop", "ro.build.version.sdk").strip() == "37" and
                    "arm64-v8a" in adb("shell", "getprop", "ro.product.cpu.abilist") and
                    "versionCode=" not in observe("shell", "dumpsys", "package", PACKAGE),
                    "Fresh Android 17 emulator with ARM64 execution required")
    out.mkdir()
    receipt = dict(status="STARTED", owner_profile_used=False, APK_modified=False, shutdown="NOT_SELECTED")
    report = out / "STARTUP-PROBE.json"

    def save():
        release.save(report, receipt)

    save()
    row = request["qa_input"]
    apk = release.unique(release.obtain(row, "exact-signed-518-startup"),
                         "Infinity-2103518-Combined-Original-Signer.apk")
    release.require(release.sha(apk) == row["APK_sha256"], "Exact signed 2103518 APK required")
    release.signature(apk)
    with ZipFile(apk) as archive, archive.open("lib/arm64-v8a/libkodi.so") as stream:
        engine = hashlib.file_digest(stream, "sha256").hexdigest()
    release.require(engine == request["engine_sha256"], "Original 2103518 engine differs")
    receipt.update(apk_sha256=row["APK_sha256"], engine_sha256=engine)
    fixture, manifest = build_fixture(out, apk)
    release.require("Success" in adb("install", apk), "Signed QA install failed")
    identity = package_record()
    release.require(identity["versionCode"] == "2103518", "Wrong engine package version")
    adb("shell", "input", "keyevent", "82")
    adb("shell", "appops", "set", PACKAGE, "MANAGE_EXTERNAL_STORAGE", "allow")
    observe("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS")
    adb("root")
    adb("wait-for-device")
    release.require(adb("shell", "id", "-u").strip() == "0" and
                    adb("shell", "getenforce").strip() == "Enforcing" and
                    identity["uid"].isdigit() and int(identity["uid"]) >= 10000,
                    "Verified disposable emulator owner required")
    adb("shell", "mkdir", "-p", PROFILE)
    adb("push", str(fixture) + "/.", PROFILE + "/")
    backing = f"/data/media/0/Android/data/{PACKAGE}/files/.kodi"
    uid = identity["uid"]
    adb("shell", "chown", "-R", f"{uid}:{uid}", backing)
    adb("shell", "restorecon", "-RF", backing)
    boot = launch_and_verify(manifest)
    receipt["startup"] = boot
    save()
    release.require(boot["complete"], "Stock QA launch did not reach the signed module")
    pid = str(boot["engine_pid"])
    try:
        adb("forward", "tcp:19090", "tcp:9090")
        until(lambda: rpc("JSONRPC.Ping") == "pong", "original Kodi process readiness", 80)
        for addon in [DRIVER, *(aid for wave in WORKERS for aid in wave)]:
            detail = rpc("Addons.GetAddonDetails", {"addonid": addon, "properties": ["enabled"]})["addon"]
            if not detail["enabled"]:
                release.require(rpc("Addons.SetAddonEnabled", {"addonid": addon, "enabled": True}) == "OK",
                                "Fixture add-on unavailable")
        release.require(rpc("Addons.ExecuteAddon", {"addonid": DRIVER, "wait": False}) == "OK",
                        "Fixture dispatch refused")
        deadline = time.monotonic() + 65
        trace, markers = [], {}
        while time.monotonic() < deadline:
            release.require(observe("shell", "pidof", PACKAGE + ":kodi") == pid, "Engine process exited")
            trace, markers = records(pid)
            if sum("end" in events for events in markers.values()) == WAVES * WIDTH and all(
                    row.get("complete") for row in analyze(trace, markers).values()):
                break
            time.sleep(2)
        overflow = any(row["stage"] == "trace.overflow" for row in trace)
        summary = analyze(trace, markers)
        receipt.update(invocations=summary, total_fixture_entries=len(markers), overflow=overflow,
                       status="STARTUP_PROBE_INCOMPLETE")
        # Verify actual overlap using worker timestamps, without assuming
        # that nominal dispatch spacing is the same as observed scheduling.
        overlaps = []
        for previous, current in zip(WORKERS, WORKERS[1:]):
            finishes = [markers.get(aid, {}).get("end", {}).get("monotonic_ns", 0) for aid in previous]
            starts = [markers[aid]["begin"]["monotonic_ns"] for aid in current
                      if "begin" in markers.get(aid, {})]
            overlaps.append(bool(starts and max(finishes) > min(starts)))
        receipt["overlapping_adjacent_bursts"] = overlaps
        warning = observe("logcat", "-d", "-v", "raw", "-s", "InfinityResumeHub:W")
        receipt["resume_hub_legacy_087_guard_seen"] = (
            "Unexpected Command Center parent 0.3.5.87; Resume Hub overlay skipped" in warning)
        save()
        complete = sum(bool(v.get("complete") and "end" in v["timing"]) for v in summary.values())
        print(f"Selected lifecycles complete: {complete}/{WAVES * WIDTH}; actual adjacent overlap: {overlaps}", flush=True)
        release.require(complete == WAVES * WIDTH and not overflow and any(overlaps),
                        "Incomplete startup or insufficient concurrency on the selected Android run")
        receipt["status"] = "PASS_SELECTED_CONCURRENT_STARTS"
        save()
    except Exception:
        if observe("shell", "pidof", PACKAGE + ":kodi") == pid:
            result = subprocess.run(["adb", "shell", "debuggerd", "-b", pid], capture_output=True,
                                    text=True, timeout=35)
            (out / "emulator-native-stacks.txt").write_text(result.stdout + result.stderr)
        else:
            (out / "emulator-crash.txt").write_text(observe("logcat", "-d", "-b", "crash", "-t", "100"))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
