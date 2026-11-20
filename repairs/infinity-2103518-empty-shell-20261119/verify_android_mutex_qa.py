"""Selected original-signed Android 17 install-over and root-free log check."""
import json
import os
from pathlib import Path
import sys
import time
from zipfile import ZipFile

import verify_android_startup as startup
from verify_android import PACKAGE, PROCESS, PROFILE, adb, observe, launch_and_verify, package_record
import common_release as release

HERE = Path(__file__).resolve().parent
START = "phase=observer_start"


def fetch(row, role):
    version = row["versionCode"]
    apk = release.unique(release.obtain(row, role), f"Infinity-{version}-Combined-Original-Signer.apk")
    release.signature(apk)
    release.require(release.sha(apk) == row["APK_sha256"], "Wrong original-signed installation input")
    return apk


def run():
    request_path = HERE / "MUTEX-ANDROID-REQUEST.json"
    request = release.load(request_path)
    release.require(os.environ.get("GITHUB_ACTIONS") == "true" and
                    os.environ.get("GITHUB_REPOSITORY") == release.REPO and
                    os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and
                    os.environ.get("GITHUB_REF") ==
                    "refs/heads/work/infinity-2103518-empty-shell-investigation-20261119" and
                    os.environ.get("SELECTED_AUTHORIZATION") == release.sha(request_path) and
                    request["driver_sha256"] == release.sha(Path(__file__)),
                    "Wrong selected Android diagnostic verification")
    release.require(adb("shell", "getprop", "ro.kernel.qemu").strip() == "1" and
                    adb("shell", "getprop", "ro.build.version.sdk").strip() == "37" and
                    "arm64-v8a" in adb("shell", "getprop", "ro.product.cpu.abilist") and
                    "versionCode=" not in observe("shell", "dumpsys", "package", PACKAGE),
                    "Fresh ARM64-capable Android 17 emulator required")
    out = Path("infinity518-mutex-android")
    out.mkdir()
    row = request["diagnostic"]
    baseline = fetch(request["baseline"], "mutex-install-baseline")
    diagnostic = fetch(row, "mutex-install-diagnostic")
    with ZipFile(baseline) as a, ZipFile(diagnostic) as b:
        for member in (startup.MANIFEST, startup.MANIFEST + ".sig"):
            name = "assets/addons/" + member
            release.require(a.read(name) == b.read(name), "Command Center owner data binding changed")
    # Reuse the authenticated synthetic .87 runtime from the successful 518
    # probe. This release selects package upgrade plus one small startup run.
    startup.WORKERS = [["script.infinityqastartup.w0.s0", "script.infinityqastartup.w0.s1"]]
    fixture, manifest = startup.build_fixture(out, baseline)
    sentinel = fixture / "userdata/infinity-mutex-qa-sentinel"
    sentinel.write_text("retained diagnostic installation fixture\n")
    release.require("Success" in adb("install", baseline), "Signed 2103518 baseline failed to install")
    before = package_record()
    release.require(before["versionCode"] == "2103518" and int(before["uid"]) >= 10000,
                    "Wrong baseline package identity")
    adb("shell", "input", "keyevent", "82")
    adb("shell", "appops", "set", PACKAGE, "MANAGE_EXTERNAL_STORAGE", "allow")
    observe("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS")
    adb("root")
    adb("wait-for-device")
    release.require(adb("shell", "id", "-u").strip() == "0" and
                    adb("shell", "getenforce").strip() == "Enforcing", "Disposable fixture setup failed")
    adb("shell", "mkdir", "-p", PROFILE)
    adb("push", str(fixture) + "/.", PROFILE + "/")
    backing = f"/data/media/0/Android/data/{PACKAGE}/files/.kodi"
    uid = before["uid"]
    adb("shell", "chown", "-R", f"{uid}:{uid}", backing)
    adb("shell", "restorecon", "-RF", backing)
    profile_file = PROFILE + "/userdata/" + sentinel.name
    release.require("Success" in adb("install", "-r", diagnostic), "Original-key install-over failed")
    after = package_record()
    release.require(after["versionCode"] == str(row["versionCode"]) and
                    all(after[key] == before[key] for key in ("uid", "dataDir", "firstInstallTime")) and
                    adb("shell", "cat", profile_file) == sentinel.read_text(),
                    "Package identity or synthetic profile sentinel changed")
    boot = launch_and_verify(manifest, with_trace=True)
    report = dict(status="INCOMPLETE", baseline=before, diagnostic=after, startup=boot,
                  profiles_preserved=True, shutdown="NOT_SELECTED", owner_profile_used=False,
                  physical_acceptance=False)
    output = out / "MUTEX-ANDROID.json"
    release.save(output, report)
    release.require(boot["complete"], "Diagnostic startup did not execute Command Center")
    pid = str(boot["engine_pid"])

    adb("unroot")
    adb("wait-for-device")
    release.require(adb("shell", "id", "-u").strip() == "2000" and
                    observe("shell", "pidof", PROCESS) == pid, "Root-free log transport failed")
    adb("forward", "tcp:19090", "tcp:9090")
    startup.until(lambda: startup.rpc("JSONRPC.Ping") == "pong", "same Kodi process readiness", 80)
    for addon in [startup.DRIVER, *startup.WORKERS[0]]:
        detail = startup.rpc("Addons.GetAddonDetails", {"addonid": addon, "properties": ["enabled"]})["addon"]
        if not detail["enabled"]:
            release.require(startup.rpc("Addons.SetAddonEnabled", {"addonid": addon, "enabled": True}) == "OK",
                            "Selected fixture failed to start")
    release.require(startup.rpc("Addons.ExecuteAddon", {"addonid": startup.DRIVER, "wait": False}) == "OK",
                    "Selected script dispatch failed")
    limit = time.monotonic() + 45
    completed = False
    while time.monotonic() < limit:
        release.require(observe("shell", "pidof", PROCESS) == pid, "Instrumented Kodi process exited")
        events, markers = startup.records(pid)
        workers = startup.analyze(events, markers)
        completed = all(value.get("complete") and "end" in value["timing"] for value in workers.values())
        if completed:
            break
        time.sleep(2)
    observed = adb("logcat", "-d", "-v", "raw", "--pid=" + pid, "-s", "InfinityPersistenceMutex:I")
    phases = observed.splitlines()
    overflow = any(row["stage"] == "trace.overflow" for row in events)
    loss = [line for line in phases if line.startswith("phase=loss ")]
    report.update(root_free_log_capture=True, native_observer_started=START in phases,
                  completed_workers=workers, startup_trace_overflow=overflow, diagnostic_loss=loss,
                  naturally_slow_wait_samples=sum(line.startswith("phase=waiting ") for line in phases))
    release.save(output, report)
    release.require(completed and START in phases and not any(
        line.startswith("phase=observer_start_failed ") for line in phases) and not overflow and not loss,
        "Signed Android observer startup or bounded delivery check failed")
    report["status"] = "PASS_SIGNED_INSTALL_OVER_AND_ROOT_FREE_DIAGNOSTIC_STARTUP"
    release.save(output, report)


if __name__ == "__main__":
    run()
