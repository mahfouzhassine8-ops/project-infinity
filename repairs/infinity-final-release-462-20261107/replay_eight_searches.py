"""Eight real Search All cycles on exact signed 2103464; QA-only A/B experiment.

Preserve all seven previous positive query paths, the eighth TV query and two
real provider heading activations. Difference from the failing run:
the disposable QA observer avoids reading Container(50).ListItem directly
during GUI transition. No changes to Infinity/Cobra, providers, or APK.
This is a focused diagnostic PASS, never full Fold or release acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import traceback

from verify_android_release import Device, PACKAGE, HOME, PROFILE, COMPAT, PROVIDERS

QUERIES = [
    ("movie", "The Matrix"),
    ("movie", "Just Friends"),
    ("movie", "Inception"),
    ("movie", "Toy Story"),
    ("movie", "Spirited Away"),
    ("movie", "Finding Nemo"),
    ("tv", "Re:zero"),
    ("tv", "SpongeBob"),
]
HEADING_ROUTE_CYCLES = (0, 7)
EXPECTED_TV_HEADING = "plugin://plugin.video.umbrella/?action=tvSearchterm&name=SpongeBob"


def run(parent: Path, candidate: Path, fixture: Path, out: Path) -> None:
    assert not out.exists(), "FRESH_DISPOSABLE_EIGHT_SEARCH_REPLAY_REQUIRED"
    out.mkdir(parents=True)
    report = dict(
        case="exact_eight_Search_All_cycles_with_targeted_QA_read_reduction",
        parent="signed2103462",
        candidate="signed2103464",
        prior_crash_run=42437719318,
        prior_single_heading_pass=42441430136,
        status="RUNNING",
        results=[],
        qaseq_changes="disposable_observer_action_only",
        signed_APK_modified=False,
        provider_addons_modified=False,
        real_Fold="NOT_RUN",
        full_release_pass=False,
    )
    def save():
        (out / "EIGHT-SEARCH-REPLAY.json").write_text(json.dumps(report, indent=2) + "\n")

    device = None
    try:
        device = Device(out)
        assert device.shell("getprop", "ro.build.version.sdk").strip() == "37"
        assert not device.shell("pm", "list", "packages", PACKAGE).strip(), "FRESH_EMULATOR_REQUIRED"
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
        assert uid.isdigit() and int(uid) >= 10000, "EXACT_FRESH_APP_UID_REQUIRED"
        backing = "/data/media/0/Android/data/" + PACKAGE
        device.shell("chown", "-R", uid + ":" + uid, backing)
        device.shell("restorecon", "-RF", backing)
        sentinel = device.shell("cat", PROFILE + "/release-data-sentinel.txt")
        assert sentinel == "preserve-disposable-preupdate-data-464465-v1"
        device.install(candidate, "signed464")
        report["normal_entry"] = device.enter("signed464")
        assert device.shell("stat", "-c", "%u", "/data/user/0/" + PACKAGE).strip() == uid
        assert device.shell("cat", PROFILE + "/release-data-sentinel.txt") == sentinel

        source = json.loads((fixture / "ANDROID-INPUTS.json").read_text())
        report["provider_fixture_versions"] = {}
        for row in source["original_provider_archives"]:
            addon = device.rpc("Addons.GetAddonDetails", dict(addonid=row["addon"], properties=["enabled", "version"]))["addon"]
            assert addon["version"] == row["version"], ("UNMODIFIED_PROVIDER_VERSION", row["addon"])
            if not addon["enabled"]:
                assert device.rpc("Addons.SetAddonEnabled", dict(addonid=row["addon"], enabled=True)) == "OK"
            report["provider_fixture_versions"][row["addon"]] = row["version"]
        compat = device.rpc("Addons.GetAddonDetails", dict(addonid=COMPAT, properties=["enabled", "version"]))["addon"]
        assert compat["version"] == "0.8.2", "EXACT_EXISTING_COMPAT_VERSION"
        if not compat["enabled"]:
            assert device.rpc("Addons.SetAddonEnabled", dict(addonid=COMPAT, enabled=True)) == "OK"

        device.start_qa()
        init = device.command("first-use", seconds=420)
        report["first_use"] = init["status"]
        assert init["status"] == "PASS_UNMODIFIED_TWO_PROVIDER_INITIALIZATION"
        report["pid"] = device.pid
        save()

        for cycle, (media, query) in enumerate(QUERIES):
            device.alive()
            device.command("home")
            device.command("search", media=media)
            device.submit_search_all(query, cycle)

            def real_grouped_results():
                snapshot = device.command("snapshot", seconds=55)
                if snapshot["window"] != 10025 or "action=search-all" not in snapshot["labels"]["Container.FolderPath"]:
                    return None
                headings = [row for row in snapshot.get("rows", [])
                            if row.get("provider") in PROVIDERS
                            and re.search(r" — \d+ results$", row.get("label", ""))]
                good = [row for row in snapshot.get("rows", [])
                        if row.get("provider") in PROVIDERS
                        and not re.search(r" — \d+ results$", row.get("label", ""))
                        and row.get("file", "").startswith("plugin://" + row["provider"] + "/")]
                if {row["provider"] for row in headings} == PROVIDERS and good:
                    return snapshot, headings, good
                return None

            snapshot, headings, good = device.until(real_grouped_results, "two actual native provider headings " + str(cycle+1), 160)
            assert not any("state changed" in row.get("label", "").lower() for row in snapshot["rows"])
            if query == "Re:zero":
                assert any(row["provider"] == "plugin.video.watchnixtoons2" for row in good), "ACTUAL_NIXTOONS_RESULT_REQUIRED"
            device.alive()
            # Identical two real native user swipe inputs from the failing run.
            device.shell("input", "swipe", "820", "1650", "820", "750", "500")
            device.shell("input", "swipe", "820", "750", "820", "1650", "500")
            entry = dict(cycle=cycle+1, media=media, query=query, results=len(good),
                         providers=sorted({row["provider"] for row in headings}),
                         search_folder=snapshot["labels"]["Container.FolderPath"],
                         pid=device.pid, heading_opened=False)
            if cycle in HEADING_ROUTE_CYCLES:
                umbrella = [row for row in headings if row["provider"] == "plugin.video.umbrella"]
                assert len(umbrella) == 1, "EXACT_ONE_UMBRELLA_HEADING_REQUIRED"
                heading = umbrella[0]
                assert heading["file"].startswith("plugin://plugin.video.umbrella/")
                if cycle == 7:
                    assert heading["file"] == EXPECTED_TV_HEADING, "EXACT_EIGHTH_TV_QUERY_ROUTE"
                if cycle == 7:
                    device.screenshot("before-eighth-heading")
                # Uses actual Kodi SetFocus and Input.Select; returns success
                # only if the provider folder really opens. Crucially no
                # volatile Container(50).ListItem label read in this action.
                opened = device.command("select-row-no-list-read", index=heading["index"],
                                        file=heading["file"], seconds=120)
                assert opened["status"] == "REAL_PROVIDER_FOLDER_MATCHED_NO_LIVE_LIST_ITEM_READ"
                assert opened["folder_path"].rstrip("/") == heading["file"].rstrip("/")
                assert opened["pid"] == device.pid
                entry.update(heading_opened=True, provider_folder=opened["folder_path"],
                             heading_file=heading["file"], verified_navigated=True)
            device.alive()
            report["results"].append(entry)
            save()
            print("PASS real search cycle", cycle+1, media, query, "results", len(good),
                  "heading", entry["heading_opened"], flush=True)
        assert len(report["results"]) == 8
        assert [entry["cycle"] for entry in report["results"] if entry["heading_opened"]] == [1, 8]
        assert device.shell("cat", PROFILE + "/release-data-sentinel.txt") == sentinel
        device.alive()
        report["status"] = "PASS_EIGHT_NATIVE_SEARCHES_AND_TWO_REAL_HEADING_ROUTES_QA_ONLY"
        report["limit"] = ("Controlled emulator observer reads only; does not prove no recurrence, "
                           "does not test physical Fold, remaining release gates or 465 recovery.")
        device.screenshot("after-eighth-heading")
    except BaseException as error:
        report.update(status="FAIL_EIGHT_NATIVE_SEARCH_DIAGNOSTIC",
                      error=type(error).__name__ + ": " + str(error),
                      traceback=traceback.format_exc())
        raise
    finally:
        if device is not None:
            try:
                (out/"KODI-LOG.txt").write_text(device.shell("cat", HOME + "/temp/kodi.log", check=False))
            except Exception as error:
                report["kodi_log_error"] = repr(error)
            try:
                (out/"LOGCAT.txt").write_text(device.adb("logcat", "-d", "-v", "threadtime", timeout=60, check=False))
            except Exception as error:
                report["logcat_error"] = repr(error)
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
