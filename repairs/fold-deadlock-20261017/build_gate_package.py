#!/usr/bin/env python3
"""Bind the first native gate to its actual signed artifacts and all five streams."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO = "https://github.com/mahfouzhassine8-ops/project-infinity"
NATIVE_SOURCE = "0c9b933c7916cce7d5e0f47a195751827fc41c28"
PACKAGE_SOURCE = "b0f9ded4f469f80576344751a1c3b559fec6f370"
RECOVERY_SOURCE = "2d5df339c0a32b678df80852b94e878b1752a8e7"
HELPER_SHA = "39c30258e8d8e737a1d484c3de91ac7e329f5283afbff6b3b1f422c859f88e53"
RECOVERY_SHA = "dba95ad2a74bc220aeb2d6b045ef303ec2b83ec819ae72a09f3d470c9acf4ae8"
DEBUG_SHA = "e653e8ae037a9dd88809b94780a1cdb7c818ce325c362974307e4bc3422e047c"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            result.update(block)
    return result.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def build(output, evidence):
    proof = json.loads((output / "FOLD-DEADLOCK-APK-PRESERVATION.json").read_text())
    assert proof["native_source_commit"] == NATIVE_SOURCE
    assert proof["packaging_source_commit"] == PACKAGE_SOURCE
    assert proof["all_dex_resources_assets_other_libraries_byte_identical"]
    assert not proof["physical_fold_verified"] and not proof["final_lock_authorized"]
    payloads = {}
    for item in proof["artifacts"]:
        path = output / item["file"]
        assert digest(path) == item["sha256"] and path.stat().st_size == item["bytes"]
        payloads[path.name] = path
    for name, expected in (("script.infinity.foldcapture-1.0.1-2103380-TEST1.zip", HELPER_SHA),
                           ("script.infinity.addonrecovery-1.0.0-TEST.zip", RECOVERY_SHA)):
        path = output / name
        assert digest(path) == expected
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
        payloads[name] = path
    runtime = json.loads((evidence / "addon-recovery/recovery-smoke-result.json").read_text())
    assert runtime["passed"] and runtime["real_kodi_api"]
    assert runtime["retained_settings_byte_identical"] and runtime["video_sources_reappearance_verified"]
    assert not runtime["actual_otaku_tested"] and not runtime["physical_fold_verified"]
    assert digest(evidence / "Infinity-2103380-Native-Debug-Evidence-TEST1.zip") == DEBUG_SHA

    android = {
        "run_id": 38997255083, "run_url": REPO + "/actions/runs/38997255083",
        "overall": "FAIL", "tests_modified": False, "skips_added": False,
        "cases": {"fresh": "PASS", "loaded": "PASS", "cold": "PASS", "core-initialized": "FAIL"},
        "failure": "AssertionError: native_admission: checkpoint_deadline_exceeded; owner proof incomplete",
        "fixture": "API 30 x86_64 emulator with ARM64 native translation, controlled services and Estuary",
        "physical_fold_verified": False,
        "interpretation": "Core-initialized failure class also existed on accepted TEST4; no causal regression or improvement claim from a single run. No save-admission or owner-proof waiver.",
        "java_note": "DEX is byte-identical to TEST4. The historical 308 Java tests were not newly rerun at this gate. Four actual Android process scenarios ran unchanged.",
    }
    save(output / "ANDROID-REGRESSION-RESULTS.json", android)
    states = [
        {"id": 1, "name": "Native Android stability", "code": "Targeted OnJobComplete item-retirement correction built and signed as 2103380 TEST1", "verification": "Full ARM64 compile; extracted production callback with real OS mutexes; fresh/loaded/cold Android pass; core-initialized fails", "remaining": "Physical return/screensaver/session/playback/PiP/safe-Close matrix; full lifecycle acceptance", "complete": False},
        {"id": 2, "name": "Watched / Resume Hub / Watchlist / Collection", "code": "Existing .20 controller source audited and preserved; no replacement installed or delivered", "verification": "Typed identity and current persistence/action paths reviewed; approved blue mockup retained", "remaining": "Universal provider-row presentation; compatible metadata adapters and manual/cross-provider/anime/negative tests; current device code preimages", "complete": False},
        {"id": 3, "name": "Add-on touch and recovery", "code": "Manual recovery helper 1.0.0 implemented; existing Home rail correction retained", "verification": "10 host checks and real Kodi 20.5 Linux enable/reappearance/settings-retention tests on two disposable video fixtures pass; first-right-click selection guard verified in actual TEST4 binary", "remaining": "Actual Otaku/Fold recovery; discoverable skin route; actual 1193/50 touch dispatch and repeated edge/scroll/rail tests", "complete": False},
        {"id": 4, "name": "Infinity skin refinement", "code": "Exact 1.0.5.223 retained; no new skin ZIP or animation changes", "verification": "3055 baseline files byte-identical; 2135 XML parse; 14 source profile trees inventoried", "remaining": "Runtime screen/theme/responsive audit, targeted polish, visual comparisons and forward-versioned full skin candidate; broad animation work after native stability", "complete": False},
        {"id": 5, "name": "Integrated verification", "code": "Coordinated native-gate bundle, signing/payload receipts, rollback and physical matrix prepared", "verification": "APK/permanent signer and native symbols matched; Android overall red; recovery helper isolated real-runtime pass", "remaining": "Full feature combination; physical 5/20/45/90-minute matrix, providers/data/regressions and explicit final approval", "complete": False},
    ]
    status = {"schema": 1, "date_utc": "2026-10-17", "authorization": "FULL_FIVE_WORKSTREAM_IMPLEMENTATION_REMAINS_ACTIVE",
              "delivery": "FIRST_NATIVE_VERIFICATION_GATE; NOT_COMPLETED_FIVE_WORKSTREAM_RELEASE",
              "workstreams": states, "original_locked_apk_modified": False, "original_locked_skin_modified": False,
              "rails_026_modified": False, "command_center_modified": False, "user_device_or_data_modified_by_agent": False,
              "merged": False, "promoted": False, "locked": False,
              "fresh_device_inventory": "Latest capture reports skin .223/Rails .026; Command Center unavailable. Earlier principal-file hashes match .20, not a fresh complete device audit."}
    save(output / "FIVE-WORKSTREAM-STATUS.json", status)
    matrix = {"schema": 1, "status": "NOT_EXECUTED_ON_PHYSICAL_FOLD", "candidate_apk_sha256": proof["artifacts"][0]["sha256"],
              "base_cases": [{"background_minutes": minutes, "display": display, "playback": playback,
                              "screensaver": saver, "observed_result": None, "live_process_or_reclaimed": None,
                              "arm_pid": None, "capture_file": None, "notes": None}
                             for minutes in (5, 20, 45, 90) for display in ("cover", "unfolded")
                             for playback in ("no-video", "playing") for saver in ("off", "on")],
              "additional_checks": {name: None for name in ("rotation", "split-pop-up", "Home-Recents", "screen-off",
                  "network-change", "immediate-navigation", "PiP", "background-playback", "session-without-autoplay",
                  "Essential-First-Close-reopen", "persistence", "provider-regressions", "themes-and-touch")}}
    save(output / "PHYSICAL-FOLD-TEST-MATRIX.json", matrix)

    reports = {
        "LOCK-RETIREMENT-HOST.json": evidence / "corrected-native/fold-lock-host/LOCK-RETIREMENT-HOST.json",
        "FOLD-DEADLOCK-SOURCE-DELTA.json": evidence / "corrected-native/FOLD-DEADLOCK-SOURCE-DELTA.json",
        "ENGINE-PROOF.json": evidence / "corrected-native/ENGINE-PROOF.json",
        "ADDON-RECOVERY-REAL-KODI-RESULT.json": evidence / "addon-recovery/recovery-smoke-result.json",
        "SKIN223-SOURCE-INVENTORY.json": evidence / "skin223-inventory-summary.json",
    }
    for name, source in reports.items():
        shutil.copyfile(source, output / name)
    text = """# Infinity — consolidated five-workstream project, TEST1 native gate

**Experimental phase-gate delivery. All five workstreams remain active and unfinished. No final lock or promotion.**

This gate delivers the evidence-based native correction first. It includes the signed APK, matching manual capture helper, same-code TEST4 compatibility rollback and a separately verified manual add-on recovery helper. It contains no new skin/controller/Rails replacement. Keep the installed skin **1.0.5.223** and existing Rails **0.2.6** and Command Center in place.

| Workstream | Delivered or verified here | Still open |
|---|---|---|
| 1. Native stability | OnJobComplete correction; complete ARM64 compile; permanent signing; causal host regression | Physical Fold background return, screensaver, session, playback, PiP and safe shutdown; core Close failure |
| 2. Watched / Resume Hub / Watchlist / Collection | Existing controller and identity/persistence paths audited; approved mockup retained | Universal provider badges, complete controls/identity integration and compatible-provider verification |
| 3. Touch and recovery | Manual recovery helper; ten host tests and two-fixture real Kodi enable/reappearance/data-retention pass | Actual Otaku, discoverable skin entry, custom-grid longpress and Fold rail/edge/scroll verification |
| 4. Full skin refinement | Exact .223 retained; 3,055 files matched; 2,135 XML parsed; 14 profile trees inventoried | Runtime defect matrix, themes/responsive comparisons, targeted polish and full forward skin ZIP |
| 5. Integrated verification | Current native-gate identities, receipts, rollback and physical matrix | Full feature combination, 5/20/45/90-minute physical tests and explicit final approval |

## Install and collect the native gate

1. Install **Infinity-2103380-Fold-Deadlock-Repair-TEST1.apk** as an update over the existing app. Do not uninstall or clear app data. It uses the permanent signing certificate and a new versionCode, 2103380.
2. Keep the current .223 skin, Rails and Command Center. Install **script.infinity.foldcapture-1.0.1-2103380-TEST1.zip** through Kodi Install from ZIP. This manual helper has no service or scheduled work; it only arms the exact TEST1 engine.
3. Open **Infinity Fold Freeze Capture** in Program Add-ons and choose **Arm capture for two hours** before each background-return scenario. Rearm before a new long scenario; the complete matrix lasts longer than a single two-hour arm.
4. Test return after **5, 20, 45 and 90 minutes**, dismissing the screensaver and immediately navigating Home/provider rows. Repeat cover/unfolded and no-video/playing variants, screensaver on/off. Also check rotation, split/pop-up, Home/Recents, screen off, network changes, PiP, background playback and session restoration without unwanted autoplay.
5. Export after a return or, if Android stops Infinity, reopen it once and export current/previous evidence. Keep any ordinary Android diagnostic ZIP from that same attempt. Record whether the process survived or Android reclaimed it. An empty stall export is **not a pass certificate**. The export includes the arm PID/hash and whitelisted installed add-on versions/code identities; it does not collect provider settings or databases.
6. Check a normal Essential-First Close/reopen and saved progress/settings. Record the result in **PHYSICAL-FOLD-TEST-MATRIX.json**, or provide equivalent notes with the exports. Every template result is initially null; none represents an executed test.

Physical exports are needed both to validate the correction and to resolve the current installed Command Center preimage before its next update. The latest earlier capture reported Rails .026 and skin .223 but could not query Command Center. Older installed hashes matched .20; they do not authorize overwriting unknown/newer current code. General implementation authorization for all five streams remains active.

## What changed in the native candidate

The physical recorder showed five repeated reciprocal waits: the GUI held graphics while waiting for the directory mutex; the OnJobComplete worker held the directory mutex while waiting for graphics. Exact symbolization identifies GUIWindowManager::Process and DirectoryProvider::OnJobComplete. The recorder does not contain the worker's complete stack. Source tracing and an extracted-production-callback test demonstrate the old-item destruction route into texture cleanup and graphics locking.

The callback now copies incoming references and swaps the retired list into a local declared before its directory lock guard. Reverse C++ destruction releases that guard before the retired GUI items are destroyed, including exception paths. Stale rail/job rejection, state transitions and failed-job behavior remain intact. The test compiles both actual callback versions and reproduces the baseline dependency using real OS mutexes; the candidate allows the GUI to proceed while old-item graphics cleanup waits.

Exactly **one of 4,499 xbmc source files** differs from reconstructed TEST4: DirectoryProvider.cpp. APK payload differences are limited to AndroidManifest.xml and lib/arm64-v8a/libkodi.so. Both DEX files, resources, assets, other libraries and existing native shutdown/write protections are retained. The APK does not replace external add-ons, profiles or data.

## Actual results and limits

| Check | Observed result |
|---|---|
| Full ARM64 native compilation | PASS |
| Production-callback causal/semantic host regression | PASS; baseline dependency reproduced, candidate releases directory before old-item graphics cleanup |
| Permanent certificate, APK signing v1/v2/v3, alignment, payload preservation | PASS |
| Android fresh / loaded / cold | PASS / PASS / PASS |
| Android core-initialized Close | **FAIL**: `native_admission: checkpoint_deadline_exceeded; owner proof incomplete` |
| Android overall | **FAIL**; original probes unchanged, no skips or weakened save gates |
| Recovery helper | Ten host checks PASS; real Kodi API re-enable/reappearance/settings-retention PASS on two disposable video fixtures |
| Physical Fold / actual Otaku | **NOT EXECUTED HERE** |

The core-initialized failure has the same recorded class as accepted TEST4. That does not prove every detail has the same cause. Cold passed this run; a single run does not establish a causal improvement. The emulator uses API 30 and ARM64 translation with a controlled fixture, not the customized Diggz/Fold environment. Historical Java tests were not newly rerun; DEX preservation is exact, and the four listed Android scenarios actually ran. Recovery integration used Linux Kodi 20.5, not the customized Android Kodi 21.3 build.

## Add-on recovery gate

**script.infinity.addonrecovery-1.0.0-TEST.zip** is a separate manual Program Add-on in this same project. It offers Restore Otaku, Disabled add-ons, native Add-on Manager and existing Infinity Add-on Rails. It lists installed-but-disabled installations and enables one selected add-on through Kodi's native API, then verifies the enabled state. It distinguishes missing, already enabled and unknown/refused states. Already enabled can still mean custom-hidden or filtered; no repository condition is invented.

It has no background service, bulk enable, Disable, uninstall, reinstall, reset, database edits or provider settings writes. Its real-runtime pass used two harmless disposable fixtures; **actual Otaku was not tested**. Complete the native capture gate before using this optional helper to change the installed add-on state. Later physical recovery acceptance must verify Otaku and a second add-on reappear while retaining their data. In-skin discoverability and Disable confirmation remain unfinished.

## Rollback without deleting data

Install **Infinity-2103380-TEST4-Compatibility-Rollback.apk** over TEST1 as an update. It uses the same versionCode 2103380 and permanent certificate, restoring TEST4's functional payload without an Android downgrade or uninstall. Only the versionCode differs from original TEST4's functional packaging; this is not a new locked baseline or a user-data rollback. The original **2103377 TEST4** remains byte-for-byte immutable.

Capture helper 1.0.1 deliberately refuses to arm the rollback engine. The existing original capture 1.0.0 matches the TEST4 engine if another baseline capture is needed. Neither helper clears data. The optional recovery helper only changes the explicitly selected Kodi enable flag; there is no automatic provider reconfiguration.

## Identities, source and evidence

See **FOLD-DEADLOCK-APK-PRESERVATION.json**, **NATIVE-SYMBOL-IDENTITY.json**, **ANDROID-REGRESSION-RESULTS.json**, **FIVE-WORKSTREAM-STATUS.json** and **GATE-SHA256SUMS**. The approved blue watched mockup is a reference image, not a screenshot of implemented new badges.

The matching **Infinity-2103380-Native-Debug-Evidence-TEST1.zip** is retained separately for future symbolization. Its SHA-256 is `e653e8ae037a9dd88809b94780a1cdb7c818ce325c362974307e4bc3422e047c`. The packaged and unstripped engine .text sections match. New recorder `elf_pc` values are already ELF RVAs; do not apply the historical ANR file-offset adjustment or use TEST4 symbols on TEST1.
"""
    text += "\n- [Native correction source](" + REPO + "/tree/" + NATIVE_SOURCE + "/repairs/fold-deadlock-20261017)"
    text += "\n- [Signed packaging source](" + REPO + "/tree/" + PACKAGE_SOURCE + "/repairs/fold-deadlock-20261017)"
    text += "\n- [Recovery source](" + REPO + "/tree/" + RECOVERY_SOURCE + "/repairs/addon-recovery-20261017)"
    text += "\n- [Full five-workstream continuation ledger](" + REPO + "/blob/work/infinity-consolidated-anr-first-20261017/repairs/fold-deadlock-20261017/PROGRAM.md)\n"
    for title, run in (("Native build", 38995006086), ("Signing and packaging", 38997149880),
                       ("Unchanged Android scenarios (overall red)", 38997255083), ("Real Kodi recovery verification", 38998654474)):
        text += "- [" + title + "](" + REPO + "/actions/runs/" + str(run) + ")\n"
    text += "\nNo source lock was moved, no merge/promotion was performed, and no physical device was changed by this development environment. Final approval and locking require the user's physical Galaxy Fold validation. Completing this gate does not complete watched, touch, skin or integrated acceptance.\n"
    (output / "Infinity-Five-Workstream-Status-TEST1.md").write_text(text)

    members = dict(payloads)
    for name in ("FOLD-DEADLOCK-APK-PRESERVATION.json", "NATIVE-SYMBOL-IDENTITY.json", "ANDROID-REGRESSION-RESULTS.json",
                 "FIVE-WORKSTREAM-STATUS.json", "PHYSICAL-FOLD-TEST-MATRIX.json", "Infinity-Five-Workstream-Status-TEST1.md", *reports):
        members[name] = output / name
    members["references/APPROVED-Infinity-Blue-Watched-Checkmark.png"] = evidence / "consolidated/references/APPROVED-Infinity-Blue-Watched-Checkmark.png"
    sums = "".join(digest(path) + "  " + name + "\n" for name, path in sorted(members.items()))
    (output / "GATE-SHA256SUMS").write_text(sums)
    members["GATE-SHA256SUMS"] = output / "GATE-SHA256SUMS"
    target = output / "Infinity-Consolidated-TEST1-Native-Gate.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(members.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            # Signed APKs and add-on ZIPs are already compressed.
            info.compress_type = zipfile.ZIP_STORED if path.suffix in (".apk", ".zip", ".png") else zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(members)
    result = {"file": target.name, "bytes": target.stat().st_size, "sha256": digest(target), "members": len(members),
              "delivery": status["delivery"], "physical_fold_verified": False, "locked": False}
    save(output / "GATE-PACKAGE-IDENTITY.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output.resolve(), args.evidence.resolve()), indent=2))
