#!/usr/bin/env python3
"""Run actual signed Infinity with complete unmodified skin and supporting addons.

This is an Android emulator integration smoke, not a host Kodi renderer and
not a substitute for physical Fold or long-duration feature acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import time
import traceback
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
probe_path = HERE.parent / "android-checkpoint-shutdown/runtime-tests/essential_android_probe.py"
spec = importlib.util.spec_from_file_location("infinity_production_probe", probe_path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
FULL_SKIN = "skin.infinity.diggz"
PARENT = "com.projectinfinity.kodi"
CONFIRM = "script.infinity.fullstack.confirm"
REQUIRED = (
    "script.infinity.commandcenter", "service.infinity.compat",
    "script.infinity.rails", "script.skinshortcuts",
    "resource.images.studios.white", "resource.images.recordlabels.white",
    FULL_SKIN
)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stage_confirmation(staging):
    """Only the disposable emulator gets this helper; do not modify the skin."""
    directory = staging / CONFIRM
    directory.mkdir()
    (directory / "addon.xml").write_text(
        '<addon id="' + CONFIRM + '" name="Infinity test dialog verifier" '
        'version="1.0.0" provider-name="Infinity CI">'
        '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
        '<extension point="xbmc.python.script" library="default.py"/>'
        '<extension point="xbmc.addon.metadata"><summary lang="en_GB">'
        'Test-only native skin confirmation</summary>'
        '<description lang="en_GB">Emulator test helper, never installed for a user</description>'
        '<platform>all</platform><license>GPL-2.0-or-later</license>'
        '</extension></addon>')
    (directory / "default.py").write_text('''
import json, time
from pathlib import Path
import xbmc, xbmcgui, xbmcvfs
output = Path(xbmcvfs.translatePath("special://profile/infinity-full-stack-confirm.json"))
def record(stage):
    tmp = output.with_suffix(".tmp")
    tmp.write_text(json.dumps({"stage":stage,"time":time.monotonic()}))
    tmp.replace(output)
record("armed")
watch = xbmc.Monitor()
until = time.monotonic() + 90
while not watch.abortRequested() and time.monotonic() < until:
    dialog = xbmcgui.getCurrentWindowDialogId()
    if dialog == 10100 and xbmc.getSkinDir() == "skin.infinity.diggz":
        xbmc.executebuiltin("SetFocus(9000)", True)
        xbmc.executebuiltin("SetFocus(11)", True)
        xbmc.sleep(70)
        xbmc.executebuiltin("Action(Select)", True)
        record("submitted_native_ok")
        break
    xbmc.sleep(80)
else:
    record("native_dialog_not_seen")
''')
    return directory


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "passed": False, "product": "Infinity",
        "apk_sha256": None, "skin_version": "1.0.5.225",
        "fixture_manifest_rewritten": False, "stock_kodi_apk_used": False,
        "physical_fold_accepted": False, "full_release_accepted": False,
        "resume_seek_certified": False, "fold_input_certified": False,
        "close_certified": False,
    }
    def publish(stage):
        report["stage"] = stage
        (out / "FULL-STACK-ANDROID.json").write_text(json.dumps(report, indent=2) + "\n")
        print("INFINITY FULL STACK:", stage, flush=True)
    try:
        require(Path(args.apk).is_file(), "Signed Infinity APK missing")
        report["apk_sha256"] = sha(args.apk)
        require(report["apk_sha256"] == args.expected_sha,
                "Wrong APK. Stock Kodi or a different Infinity candidate cannot count")
        input_report = json.loads(Path(args.input_proof).read_text())
        require(input_report.get("full_production_skin_dependencies_satisfied") is True,
                "Real production skin dependencies not proven")
        require(input_report.get("skin_sha256") ==
                "8ca8fc72ce24ae88d558d06485345ec37a2cd491ebea5805e169d84acf8ed235",
                "Full production skin identity mismatch")
        source = Path(args.addons)
        require(all((source / addon / "addon.xml").is_file() for addon in REQUIRED),
                "Incomplete native Infinity component set; no fixture substitution")

        publish("bootstrap-real-infinity-apk")
        for _ in range(6):
            probe.adb("root", check=False)
            probe.adb("wait-for-device")
            if probe.shell("id", "-u").strip() == "0":
                break
            time.sleep(1)
        else:
            raise RuntimeError("Disposable emulator did not obtain root adbd")
        require(probe.shell("getprop", "ro.kernel.qemu").strip() == "1",
                "Refuse to operate on a physical user device")
        require(PARENT not in probe.shell("pm", "list", "packages", PARENT),
                "Refuse to modify a pre-existing installation")
        require("arm64-v8a" in probe.shell("getprop", "ro.product.cpu.abilist"),
                "Emulator cannot run actual ARM64 Infinity engine")
        require("Success" in probe.adb("install", "--no-incremental", args.apk),
                "Actual signed Infinity APK did not install")

        report["installed_package"] = PARENT
        uid = probe.shell("stat", "-c", "%u", probe.PRIVATE).strip()
        require(uid.isdigit(), "Unknown app UID")
        probe.APP_UID = uid
        probe.shell("mkdir", "-p", probe.PROFILE + "/../addons",
                    probe.PRIVATE + "/shared_prefs")
        prefs = out / "infinity_experience.xml"
        prefs.write_text('<map><string name="default">infinity</string></map>')
        probe.adb("push", prefs, probe.PRIVATE + "/shared_prefs/infinity_experience.xml")
        # Make the native application discover the real skin on the FIRST boot.
        guisettings = out / "guisettings.xml"
        guisettings.write_text('<settings version="2"><setting id="lookandfeel.skin">'
                               + FULL_SKIN + '</setting></settings>')
        probe.adb("push", guisettings, probe.PROFILE + "/guisettings.xml")

        extras = out / "confirmation-source"
        extras.mkdir()
        confirmation = stage_confirmation(extras)
        # No addon.xml modifications, substitutions, dependency deletion or
        # fabricated plugin sources. Every required addon comes from full-stack
        # input proof and is installed with its own unmodified ID.
        for addon in sorted(source.iterdir()):
            if not addon.is_dir():
                continue
            manifest = ET.parse(addon / "addon.xml").getroot()
            require(manifest.get("id") == addon.name, "Addon path ID mismatch")
            probe.adb("push", addon, probe.PROFILE + "/../addons/" + addon.name)
        probe.adb("push", confirmation, probe.PROFILE + "/../addons/" + CONFIRM)
        backing = "/data/media/0/Android/data/" + PARENT
        probe.shell("chown", "-R", uid + ":" + uid, backing,
                    probe.PRIVATE + "/shared_prefs")
        probe.shell("restorecon", "-RF", backing, probe.PRIVATE + "/shared_prefs")
        publish("launch-infinity-native-engine")
        probe.adb("logcat", "-c")
        probe.shell("am", "start", "-W", "-n", PARENT + "/.Splash")
        report["first_party"] = probe.enable_first_party(out)
        report["native_owner"] = probe.wait_ready()
        require(probe.rpc("Settings.SetSettingValue",
                          {"setting": "general.addonupdates", "value": 2}) is True,
                "Could not disable automatic external updates in disposable test")

        publish("discover-all-production-infinity-components")
        result = probe.rpc("Addons.GetAddons", {"properties": ["version", "enabled"]})
        listing = {x["addonid"]: x for x in result.get("addons", [])}
        version_proof = {}
        for addon in REQUIRED:
            require(addon in listing, "Actual Infinity did not discover " + addon)
            info = probe.rpc("Addons.GetAddonDetails",
                             {"addonid": addon, "properties": ["version", "enabled"]})["addon"]
            expected = ET.parse(source / addon / "addon.xml").getroot().get("version")
            require(info["version"] == expected, "Addon version wrong in running Infinity: " + addon)
            if not info["enabled"]:
                require(probe.rpc("Addons.SetAddonEnabled",
                                  {"addonid": addon, "enabled": True}) == "OK",
                        "Infinity refused production addon " + addon)
                info = probe.rpc("Addons.GetAddonDetails",
                                 {"addonid": addon, "properties": ["version", "enabled"]})["addon"]
            require(info["enabled"], "Add-on disabled in running app: " + addon)
            version_proof[addon] = info["version"]
        report["enabled_production_components"] = version_proof

        log_path = probe.PROFILE + "/../temp/kodi.log"
        def last_skin_log():
            log = probe.shell("cat", log_path, check=False)
            return [line for line in log.splitlines() if "load skin from: " in line]
        observed = last_skin_log()
        expected_path = "/addons/" + FULL_SKIN + "/"
        if not observed or expected_path not in observed[-1]:
            publish("native-skin-selection-with-real-dialog")
            require(probe.rpc("Addons.SetAddonEnabled",
                              {"addonid": CONFIRM, "enabled": True}) == "OK",
                    "Native confirmation helper not discoverable")
            require(probe.rpc("Settings.SetSettingValue",
                              {"setting": "lookandfeel.skin", "value": "skin.estuary"}) is True,
                    "Could not enter native skin selection")
            require(probe.rpc("Addons.ExecuteAddon",
                              {"addonid": CONFIRM, "params": ["arm"], "wait": False}) == "OK",
                    "Cannot arm native keep-skin dialog")
            armed = {}
            for _ in range(100):
                armed = probe.read_json(probe.PROFILE + "/infinity-full-stack-confirm.json")
                if armed.get("stage") == "armed":
                    break
                time.sleep(.2)
            require(armed.get("stage") == "armed", "Skin confirmation monitor not armed")
            require(probe.rpc("Settings.SetSettingValue",
                              {"setting": "lookandfeel.skin", "value": FULL_SKIN}) is True,
                    "Actual native engine rejected unmodified production Infinity skin")
            result = {}
            for _ in range(325):
                result = probe.read_json(probe.PROFILE + "/infinity-full-stack-confirm.json")
                if result.get("stage") in ("submitted_native_ok", "native_dialog_not_seen"):
                    break
                time.sleep(.2)
            report["native_keep_skin_confirmation"] = result
            require(result.get("stage") == "submitted_native_ok",
                    "Infinity never accepted real native keep-skin dialog")

        time.sleep(4)
        selected = probe.rpc("Settings.GetSettingValue",
                             {"setting": "lookandfeel.skin"}).get("value")
        lines = last_skin_log()
        require(selected == FULL_SKIN, "Application selected stock Estuary or wrong skin")
        require(lines and expected_path in lines[-1],
                "Actual Infinity engine did NOT load production skin")
        require("skin loaded..." in probe.shell("cat", log_path, check=False),
                "Real skin render bootstrap incomplete")
        report["skin_loaded"] = lines[-1].strip()
        report["selected_skin"] = selected
        report["production_dependency_manifest_untouched"] = True
        report["exact_full_stack_boot_passed"] = True
        # Screenshot collection is part of the evidence gate; never emit
        # "passed" before the original Android GUI capture finishes.
        screenshot = probe.adb("exec-out", "screencap", "-p", binary=True)
        require(screenshot.startswith(b"\x89PNG\r\n\x1a\n"),
                "Actual Infinity screenshot missing or not PNG")
        (out / "infinity-real-screen.png").write_bytes(screenshot)
        report["passed"] = True
        publish("complete-Infinity-APK-and-full-skin-in-engine")
        return report
    except Exception:
        report["passed"] = False
        report["exact_full_stack_boot_passed"] = False
        report["failure"] = traceback.format_exc()
        publish("failed")
        raise
    finally:
        (out / "FULL-STACK-ANDROID.json").write_text(json.dumps(report, indent=2) + "\n")
        for name, run in (
            ("kodi.log", lambda: probe.shell("cat", probe.PROFILE + "/../temp/kodi.log", check=False)),
            ("logcat.txt", lambda: probe.adb("logcat", "-d")),
        ):
            try:
                (out / name).write_text(run())
            except Exception:
                pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--apk", type=Path, required=True)
    p.add_argument("--expected-sha", required=True)
    p.add_argument("--addons", type=Path, required=True)
    p.add_argument("--input-proof", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    run(p.parse_args())
