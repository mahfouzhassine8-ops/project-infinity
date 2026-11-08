"""One disposable Android Search All heading replay; QA only, no release gates waived.

Deliberately does not repeat signed package/hash checks, 7 prior search cycles,
UI variants, or 465 recovery. Those are separate retained evidence, not PASS
assertions of this single-target replay. Exact signed inputs are still pinned
and verified by stage_android_release.py before this script starts.
"""
from pathlib import Path
import argparse
import json
import re
import time
import traceback

from verify_android_release import Device, PACKAGE, HOME, PROFILE, QA, COMPAT, PROVIDERS


def run(parent, candidate, fixture, out):
    assert not out.exists(), "FRESH_DISPOSABLE_REPLAY_RESULTS_REQUIRED"
    out.mkdir(parents=True)
    report = dict(
        case="single_existing_Umbrella_TV_Search_All_heading",
        source="exact_signed_2103464_unchanged",
        search_query="SpongeBob",
        status="RUNNING",
        baseline_prior_seven_searches="REUSED_AS_EVIDENCE_NOT_RERUN",
        related_failed_android_run=42437719318,
        physical_Fold="NOT_RUN",
        APK_modified=False,
        third_party_addons_modified=False,
        full_release_pass=False,
    )
    def save():
        (out / "REPLAY-RESULT.json").write_text(json.dumps(report, indent=2) + "\n")
    device = None
    try:
        device = Device(out)
        assert not device.shell("pm", "list", "packages", PACKAGE).strip(), "FRESH_EMULATOR_ONLY"
        assert device.shell("getprop", "ro.build.version.sdk").strip() == "37", "PINNED_ANDROID_17"
        device.shell("wm", "size", "1080x2520")
        device.shell("wm", "density", "420")
        device.install(parent, "baseline462")
        for args in (
            ("appops", "set", PACKAGE, "MANAGE_EXTERNAL_STORAGE", "allow"),
            ("pm", "grant", PACKAGE, "android.permission.RECORD_AUDIO"),
            ("pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS"),
        ):
            device.shell(*args)
        device.shell("mkdir", "-p", HOME)
        device.adb("push", str(fixture / "home") + "/.", HOME)
        device.adb("root")
        device.adb("wait-for-device")
        uid = device.shell("stat", "-c", "%u", "/data/user/0/" + PACKAGE).strip()
        assert uid.isdigit() and int(uid) >= 10000, "DISPOSABLE_APP_UID_REQUIRED"
        backing = "/data/media/0/Android/data/" + PACKAGE
        device.shell("chown", "-R", uid + ":" + uid, backing)
        device.shell("restorecon", "-RF", backing)
        device.install(candidate, "candidate464")
        report["normal_entry"] = device.enter("candidate464")
        assert device.shell("stat", "-c", "%u", "/data/user/0/" + PACKAGE).strip() == uid
        inputs = json.loads((fixture / "ANDROID-INPUTS.json").read_text())
        for row in inputs["original_provider_archives"]:
            addon = device.rpc("Addons.GetAddonDetails", dict(addonid=row["addon"], properties=["enabled", "version"]))["addon"]
            assert addon["version"] == row["version"], row["addon"]
            if not addon["enabled"]:
                assert device.rpc("Addons.SetAddonEnabled", dict(addonid=row["addon"], enabled=True)) == "OK"
        compat = device.rpc("Addons.GetAddonDetails", dict(addonid=COMPAT, properties=["enabled", "version"]))["addon"]
        assert compat["version"] == "0.8.2"
        if not compat["enabled"]:
            assert device.rpc("Addons.SetAddonEnabled", dict(addonid=COMPAT, enabled=True)) == "OK"
        device.start_qa()
        report["first_use"] = device.command("first-use", seconds=360)["status"]
        device.command("home")
        device.command("search", media="tv")
        device.submit_search_all("SpongeBob", 0)

        def actual_results():
            snapshot = device.command("snapshot")
            if snapshot["window"] != 10025 or "action=search-all" not in snapshot["labels"]["Container.FolderPath"]:
                return None
            headings = [x for x in snapshot.get("rows", []) if x.get("provider") == "plugin.video.umbrella"
                        and re.search(r" — \d+ results$", x.get("label", ""))]
            if len(headings) != 1:
                return None
            return snapshot, headings[0]

        snapshot, heading = device.until(actual_results, "real Umbrella TV heading", 120)
        assert heading["index"] > 0
        assert heading["file"] == "plugin://plugin.video.umbrella/?action=tvSearchterm&name=SpongeBob"
        report["heading"] = {k: heading[k] for k in ("index", "provider", "label", "file")}
        report["pre_select_pid"] = device.pid
        device.screenshot("before-select")
        # Reproduce the original GUI selection, but do not wait 160 seconds
        # after a native crash: Device.command calls alive() on each reply poll.
        opened = device.command("select-row", index=heading["index"], file=heading["file"], seconds=90)
        assert opened["labels"]["Container.FolderPath"].rstrip("/") == heading["file"].rstrip("/")
        device.alive()
        report["status"] = "PASS_SINGLE_HEADING_REPLAY_ONLY"
        report["post_select_pid"] = device.pid
        report["remaining"] = "Seven-query accumulated-state crash and mandatory full release gates still unverified"
    except BaseException as error:
        report.update(status="FAIL_SINGLE_HEADING_REPLAY", error=type(error).__name__ + ": " + str(error), traceback=traceback.format_exc())
        raise
    finally:
        if device:
            for label, fn in [
                ("KODI-LOG.txt", lambda: device.shell("cat", HOME + "/temp/kodi.log", check=False)),
                ("LOGCAT.txt", lambda: device.adb("logcat", "-d", "-v", "threadtime", check=False)),
            ]:
                try:
                    (out / label).write_text(fn())
                except Exception as error:
                    report[label + "_error"] = str(error)
            try:
                device.screenshot("final-observation")
            except Exception:
                pass
        save()
        print(report["status"], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ("parent", "candidate", "fixture", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    run(**vars(p.parse_args()))
