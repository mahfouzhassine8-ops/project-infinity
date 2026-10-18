#!/usr/bin/env python3
"""Run the exact signed UI candidate with its full experimental skin and helpers.

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
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / "full-system-20261017"))
import infinity_full_stack_close as real_close

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
    FULL_SKIN, "script.infinity.uirepair", "script.infinity.uitest",
    *["plugin.video.infinityuitest" + str(i) for i in range(12)]
)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_versioncheck_candidate(runtime, out, expected, stage):
    """Observe Kodi's selected source as its live UID; never enable the service."""
    import versioncheck_android as package
    import versioncheck_shutdown_probe as diagnostic
    require(expected['addon'] == package.ADDON and expected['version'] == package.VERSION and
            expected['archive_sha256'] == package.ARCHIVE_SHA and
            expected['service_sha256'] == package.CANDIDATE_SERVICE_SHA and
            expected['source_apk_sha256'] == package.APK_SHA,
            'Full UI Version Check input is not the pinned Android correction')
    details = runtime.rpc('Addons.GetAddonDetails',
                          {'addonid': package.ADDON, 'properties': ['version', 'enabled']})['addon']
    require(details['enabled'] is True and details['version'] == expected['version'],
            'Running Version Check is disabled or not the exact staged candidate')
    owner = runtime.read_json(runtime.PRIVATE + '/files/infinity-kodi-process.json')
    require(diagnostic._same_live_owner(runtime, owner),
            'Version Check identity observation needs the current live engine owner')
    helper = runtime.rpc('Addons.GetAddonDetails',
                         {'addonid': diagnostic.DIAGNOSTIC, 'properties': ['enabled']})['addon']
    if not helper['enabled']:
        require(runtime.rpc('Addons.SetAddonEnabled',
                            {'addonid': diagnostic.DIAGNOSTIC, 'enabled': True}) == 'OK',
                'Cannot enable disposable Version Check identity observer')
    require(runtime.rpc('Addons.ExecuteAddon',
                        {'addonid': diagnostic.DIAGNOSTIC, 'params': [owner['owner']],
                         'wait': False}) == 'OK', 'Cannot observe selected Version Check source')
    deadline = time.monotonic() + 60
    observation = {}
    while time.monotonic() < deadline:
        observation = runtime.read_json(runtime.PROFILE + '/infinity-versioncheck-paths.json')
        if observation.get('owner') == owner['owner'] and observation.get('pid') == owner['pid']:
            break
        time.sleep(.25)
    evidence = {'input_archive_sha256': expected['archive_sha256'], 'addon': details,
                'owner': owner, 'selected_source': observation}
    (Path(out) / ('VERSIONCHECK-RUNTIME-' + stage + '.json')).write_text(
        json.dumps(evidence, indent=2) + '\n')
    require(observation.get('owner') == owner['owner'] and observation.get('pid') == owner['pid'] and
            str(observation.get('uid')) == str(runtime.APP_UID) and
            observation.get('android') is True and diagnostic._same_live_owner(runtime, owner),
            'Selected Version Check source was not observed by the same live Android engine UID')
    require(observation.get('addon_version') == expected['version'] and
            observation.get('service_sha256') == expected['service_sha256'] and
            bool(observation.get('addon_path')),
            'Kodi-selected Version Check source differs from the pinned correction')
    evidence['verified'] = True
    (Path(out) / ('VERSIONCHECK-RUNTIME-' + stage + '.json')).write_text(
        json.dumps(evidence, indent=2) + '\n')
    return evidence


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
        "test_variant": args.test_variant,
        "test4_reference_only": args.test_variant == "test4-reference",
        "test3_current_candidate": args.test_variant == "test3-current",
        "apk_sha256": None, "skin_version": "1.0.5.227",
        "fixture_manifest_rewritten": False, "stock_kodi_apk_used": False,
        "physical_fold_accepted": False, "full_release_accepted": False,
        "resume_seek_certified": False, "fold_input_certified": False, "crash_fixed": False,
        "close_certified": False,
    }
    def publish(stage):
        report["stage"] = stage
        (out / "FULL-STACK-ANDROID.json").write_text(json.dumps(report, indent=2) + "\n")
        print("INFINITY FULL STACK:", stage, flush=True)
    try:
        if getattr(args, 'versioncheck_descriptor_diagnostic', False):
            require(getattr(args, 'versioncheck_shutdown_only', False) and args.expected_api == '37',
                    'Readonly descriptor diagnostics require the dedicated targeted API37 run')
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

        candidate = input_report['ui_candidate']
        require(candidate['skin_version'] == '1.0.5.227', 'Wrong UI candidate')
        for rel, digest in candidate['source_files'].items():
            require(sha(source / rel) == digest, 'Candidate source changed: ' + rel)
        report['ui_candidate'] = {k:v for k,v in candidate.items() if k != 'source_files'}
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
        report['android_platform'] = {
            'sdk': probe.shell('getprop', 'ro.build.version.sdk').strip(),
            'release': probe.shell('getprop', 'ro.build.version.release').strip(),
            'abis': probe.shell('getprop', 'ro.product.cpu.abilist').strip(),
            'native_bridge': probe.shell('getprop', 'ro.dalvik.vm.native.bridge').strip(),
            'fingerprint': probe.shell('getprop', 'ro.build.fingerprint').strip(),
            'manufacturer': probe.shell('getprop', 'ro.product.manufacturer').strip(),
            'model': probe.shell('getprop', 'ro.product.model').strip(),
        }
        report['target_firmware'] = {'manufacturer': 'Samsung', 'ui': 'One UI 9.0',
                                     'android': '17', 'api': '37',
                                     'physical_acceptance_required': True}
        report['samsung_one_ui_emulated'] = False
        if args.expected_api:
            require(report['android_platform']['sdk'] == args.expected_api,
                    'Booted emulator API does not match the requested test target')
        if args.expected_release:
            require(report['android_platform']['release'].split('.')[0] == args.expected_release,
                    'Booted Android release does not match the requested test target')
        if args.expected_api == '37':
            # Run39125100898: SurfaceFlinger/mapper.ranchu aborted before APK
            # install. Boot-completed alone must not certify a usable emulator.
            samples = report['emulator_surfaceflinger_preinstall'] = []
            for sample in range(16):
                samples.append(probe.shell('pidof', 'surfaceflinger', check=False).strip())
                (out / 'surfaceflinger-preinstall.json').write_text(json.dumps(samples))
                require(samples[-1].isdigit() and samples[-1] == samples[0],
                        'API37 emulator SurfaceFlinger exited/restarted before app installation')
                if sample < 15:
                    time.sleep(2)
            storage = probe.shell('df', '-k', '/data')
            (out / 'emulator-data-space-before-install.txt').write_text(storage)
            fields = storage.strip().splitlines()[-1].split()
            require(len(fields) >= 6 and fields[3].isdigit(),
                    'Cannot establish available API37 emulator data space')
            report['emulator_data_free_kib_before_install'] = int(fields[3])
            require(int(fields[3]) >= 2 * 1024 * 1024,
                    'API37 disposable emulator needs at least2GiB free before staging full Infinity')
        require("Success" in probe.adb("install", "--no-incremental", args.apk),
                "Actual signed Infinity APK did not install")
        # Match the original approved fresh-Android probe's first-launch setup.
        # The qemu/no-existing-install guards above must precede every grant.
        probe.shell("input", "keyevent", "82")
        for permission in ("android.permission.READ_EXTERNAL_STORAGE",
                           "android.permission.WRITE_EXTERNAL_STORAGE"):
            probe.shell("pm", "grant", PARENT, permission, check=False)
        probe.shell("appops", "set", PARENT, "MANAGE_EXTERNAL_STORAGE", "allow", check=False)

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
                               + FULL_SKIN + '</setting>'
                               '<setting id="general.addonupdates">2</setting></settings>')
        probe.adb("push", guisettings, probe.PROFILE + "/guisettings.xml")
        if getattr(args, 'versioncheck_shutdown_only', False):
            # All three isolated comparison arms need natural service startup
            # evidence. Healthy Python retirement need not emit a warning.
            advanced = out / 'advancedsettings.xml'
            advanced.write_text('<advancedsettings><loglevel hide="true">1</loglevel></advancedsettings>')
            probe.adb('push', advanced, probe.PROFILE + '/advancedsettings.xml')
            report['targeted_debug_file_logging'] = True

        extras = out / "confirmation-source"
        extras.mkdir()
        confirmation = stage_confirmation(extras)
        versioncheck_diagnostic = None
        descriptor_diagnostic = None
        if (getattr(args, 'versioncheck_shutdown_only', False) or
                input_report.get('versioncheck_candidate')):
            import versioncheck_shutdown_probe as versioncheck_probe
            versioncheck_diagnostic = versioncheck_probe.stage_diagnostic(extras)
        if getattr(args, 'versioncheck_descriptor_diagnostic', False):
            descriptor_diagnostic = versioncheck_probe.stage_descriptor_diagnostic(extras)
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
        if versioncheck_diagnostic is not None:
            probe.adb("push", versioncheck_diagnostic,
                      probe.PROFILE + "/../addons/" + versioncheck_probe.DIAGNOSTIC)
        if descriptor_diagnostic is not None:
            probe.adb('push', descriptor_diagnostic,
                      probe.PROFILE + '/../addons/' + versioncheck_probe.DESCRIPTOR_DIAGNOSTIC)
        backing = "/data/media/0/Android/data/" + PARENT
        probe.shell("chown", "-R", uid + ":" + uid, backing,
                    probe.PRIVATE + "/shared_prefs")
        probe.shell("restorecon", "-RF", backing, probe.PRIVATE + "/shared_prefs")
        publish("launch-infinity-native-engine")
        probe.adb("logcat", "-c")
        probe.shell("am", "start", "-W", "-n", PARENT + "/.Splash")
        report["first_party"] = probe.enable_first_party(out)
        report["native_owner"] = probe.wait_ready()
        # Seed disposable-only update policy before first startup. A synchronous
        # settings write while first-party services bootstrap can exceed the
        # original probe's ten-second RPC deadline; retain that failed run.
        require(probe.rpc("Settings.GetSettingValue",
                          {"setting": "general.addonupdates"}).get("value") == 2,
                "Automatic external updates were not disabled in disposable test")

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
        if getattr(args, 'versioncheck_shutdown_only', False):
            publish("targeted-versioncheck-shutdown-evidence")
            import versioncheck_shutdown_probe as versioncheck_probe
            versioncheck_probe.before_close(probe, out, report, args)
            if getattr(args, 'versioncheck_descriptor_diagnostic', False):
                publish('diagnostic-only-readonly-descriptor-before-unchanged-Close')
                versioncheck_probe.capture_readonly_descriptor(probe, out, report)
                require(report['readonly_descriptor_diagnostic'].get('terminal_confirmed'),
                        'Descriptor collector incomplete; refuse to race a held diagnostic stream into Close')
        else:
            publish("actual-ui-and-post-stop-input")
            from android_interactions import exercise
            exercise(probe, out, report)
            if input_report.get('versioncheck_candidate'):
                report['versioncheck_runtime'] = {'before_close': verify_versioncheck_candidate(
                    probe, out, input_report['versioncheck_candidate'], 'before-close')}
        publish("request-native-Infinity-Power-Close-after-actual-skin-loading")
        real_close.loaded_close(probe, report["native_owner"], out, report)
        require(report.get("close_certified") is True and
                report.get("reopen_succeeded") is True,
                "Native Infinity loaded Close and reopen proof incomplete")
        if getattr(args, 'versioncheck_shutdown_only', False):
            versioncheck_probe.after_close(probe, out, report, args)
            if getattr(args, 'versioncheck_descriptor_diagnostic', False):
                require(report['readonly_descriptor_diagnostic'].get('captured'),
                        'Descriptor diagnostic incomplete; a Close result cannot substitute missing evidence')
        else:
            saved=probe.read_json(probe.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json')
            require(len(report['ui_expected_watchlist'])==2 and
                    all(key in saved.get('watchlist',{}) for key in report['ui_expected_watchlist']),
                    'Movie/episode Watchlist state was lost on actual Close/reopen')
            favourites=probe.rpc('Favourites.GetFavourites',{'properties':['windowparameter']})
            require(any(f.get('windowparameter')==report['ui_expected_favourite']
                        for f in (favourites.get('favourites') or [])),
                    'Add-on favourite was lost on actual Close/reopen')
            report['ui_mutations_survived_actual_restart']=True
            if input_report.get('versioncheck_candidate'):
                report['versioncheck_runtime']['after_reopen'] = verify_versioncheck_candidate(
                    probe, out, input_report['versioncheck_candidate'], 'after-reopen')
        report["passed"] = True
        publish("complete-Infinity-full-stack-loaded-Close-and-reopen")
        return report
    except Exception:
        report["passed"] = False
        report["failure"] = traceback.format_exc()
        if getattr(args, 'versioncheck_shutdown_only', False):
            import versioncheck_shutdown_probe as versioncheck_probe
            versioncheck_probe.capture_failure(probe, out, report)
        publish("failed")
        raise
    finally:
        (out / "FULL-STACK-ANDROID.json").write_text(json.dumps(report, indent=2) + "\n")
        for name, run in (
            ("kodi.log", lambda: probe.shell("cat", probe.PROFILE + "/../temp/kodi.log", check=False)),
            ("logcat.txt", lambda: probe.adb("logcat", "-d")),
            ("activities.txt", lambda: probe.shell("dumpsys", "activity", "activities", check=False)),
            ("windows.txt", lambda: probe.shell("dumpsys", "window", "windows", check=False)),
            ("input.txt", lambda: probe.shell("dumpsys", "input", check=False)),
            ("processes.txt", lambda: probe.shell("ps", "-A", check=False)),
            ("exit-info.txt", lambda: probe.shell("dumpsys", "activity", "exit-info", PARENT, check=False)),
            ("native-crash-dropbox.txt", lambda: probe.shell("dumpsys", "dropbox", "--print", "data_app_native_crash", check=False)),
        ):
            try:
                (out / name).write_text(run())
            except Exception:
                pass
        try:
            (out / "final-screen.png").write_bytes(probe.adb("exec-out", "screencap", "-p", binary=True))
            probe.adb("pull", "/data/tombstones", out / "emulator-tombstones", check=False)
        except Exception:
            pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--apk", type=Path, required=True)
    p.add_argument("--expected-sha", required=True)
    p.add_argument("--addons", type=Path, required=True)
    p.add_argument("--input-proof", type=Path, required=True)
    p.add_argument("--test-variant", choices=("ui-restoration",), required=True)
    p.add_argument("--expected-api", help="Require the actual booted API; no fallback")
    p.add_argument("--expected-release", help="Require the actual Android major release")
    p.add_argument("--versioncheck-shutdown-only", action="store_true",
                   help="Targeted equivalent Version Check Close comparison; does not certify UI matrix")
    p.add_argument("--versioncheck-expected-version")
    p.add_argument("--versioncheck-expected-service-sha")
    p.add_argument('--versioncheck-descriptor-diagnostic', action='store_true',
                   help='Dedicated disposable API37 descriptor evidence only; unchanged Close gate')
    p.add_argument("--out", type=Path, required=True)
    run(p.parse_args())
