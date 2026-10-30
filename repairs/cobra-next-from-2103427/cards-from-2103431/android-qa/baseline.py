"""Finite public-UI Cards baseline for the exact accepted signed 2103431 APK.

No app build, private-data injection, shutdown, package reset or Pro/button suite.
The caller prepares a fresh API37 emulator and the deterministic local HTTP media.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

OWNER = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(OWNER))
from android_probe import PACKAGE, adb, acknowledge_known_notice_after_launch, probe
from android_button_journey import Snapshot, bounds, center, intersect, positive

VERSION = 2103431
SOURCE = "9ccc4c362a65118eeba38a8e7e4b0de5723c69af"
APK_SHA256 = "3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471"
CERT_SHA256 = "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
CHANNEL_COUNT = 20226
COBRA = PACKAGE + "/.InfinityLiveActivity"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def activity_times(raw):
    """am start -W values only; no inferred first-frame or list-ready timing."""
    values = {key: int(value) for key, value in re.findall(
        r"^(TotalTime|WaitTime|ThisTime):\s*(\d+)\s*$", raw, re.M)}
    found = re.search(r"^LaunchState:\s*(\S+)", raw, re.M)
    if found:
        values["LaunchState"] = found.group(1)
    return values


def nearest_rank(values, percentile):
    return sorted(values)[max(0, math.ceil(len(values) * percentile) - 1)] if values else None


def frame_rows(raw):
    """Parse only complete, non-flagged HWUI records actually supplied by Android."""
    result = {}
    columns = None
    for line in raw.splitlines():
        fields = line.strip().rstrip(",").split(",")
        if "IntendedVsync" in fields and "FrameCompleted" in fields:
            columns = fields
            continue
        if not columns or len(fields) < len(columns):
            continue
        try:
            row = {key: int(value) for key, value in zip(columns, fields)}
            start, stop = row["IntendedVsync"], row["FrameCompleted"]
        except (ValueError, KeyError):
            continue
        if row.get("Flags", 0) or not (0 < start < stop < 9_223_372_036_854_775_807):
            continue
        result[(start, stop)] = row
    return result


def summarize_frames(before, samples):
    observed = {}
    for sample in samples:
        observed.update(frame_rows(sample))
    previous = frame_rows(before)
    rows = [row for key, row in observed.items() if key not in previous]
    durations = [(row["FrameCompleted"] - row["IntendedVsync"]) / 1_000_000 for row in rows]
    deadlines = [row for row in rows if row.get("FrameDeadline", 0) > row["IntendedVsync"]]
    return {
        "scope": "OBSERVED_NEW_COMPLETE_HWUI_RECORDS_ACROSS_BOUNDED_SCROLL_SNAPSHOTS",
        "sample_count": len(rows),
        "p50_frame_completion_ms": nearest_rank(durations, .50),
        "p95_frame_completion_ms": nearest_rank(durations, .95),
        "records_with_native_deadline": len(deadlines),
        "native_deadline_exceeded_records": sum(row["FrameCompleted"] > row["FrameDeadline"] for row in deadlines),
        "observed_frame_intervals_ns": sorted({row["FrameInterval"] for row in rows if row.get("FrameInterval", 0) > 0}),
        "limit": "Rolling HWUI buffers can omit frames. Not complete FPS, decoder frames, physical Fold jank or thermal acceptance. No fixed refresh-rate threshold assumed.",
    }


def validate_inputs(signed, signature, fixtures):
    apks = list(signed.glob("Infinity-*-Combined-Original-Signer.apk"))
    assert len(apks) == 1, "One existing signed APK required"
    receipt = json.loads((signed / "BUILD-RECEIPT.json").read_text())
    assert receipt["versionCode"] == VERSION and receipt["source"] == SOURCE, "Accepted 431 source/version required"
    assert receipt["signed_apk_sha256"] == APK_SHA256, "Accepted 431 APK receipt required"
    signature_text = signature.read_text()
    assert "Signer #1 certificate SHA-256 digest: " + CERT_SHA256 in signature_text, "Original certificate verification required"
    for scheme in (1, 2, 3):
        assert re.search(r"Verified using v" + str(scheme) + r" scheme[^\r\n]*:\s*true", signature_text), "Original APK signature scheme not verified"
    manifest = json.loads((fixtures / "FIXTURE.json").read_text())
    assert manifest["channel_count"] == manifest["unique_stream_url_count"] == CHANNEL_COUNT
    assert manifest["group_count"] == 12 and manifest["epg_channel_count"] == 32
    assert manifest["epg_programme_count"] == 64 and manifest["channels_without_epg"] == CHANNEL_COUNT - 32
    assert manifest["media_complete"], "Existing synthetic media must be generated and hashed first"
    for name in ("cards-20226.m3u", "cards-epg.xml"):
        assert sha256(fixtures / name) == manifest["files"][name]["sha256"], "Fixture bytes changed: " + name
    for name in ("qa1.mp4", "qa2.mp4", "qa3.mp4", "qa4.mp4"):
        assert sha256(fixtures / name) == manifest["media"][name]["sha256"], "Synthetic media changed: " + name
    start, stop = manifest["current_programme_window_epoch"]
    assert start <= time.time() < stop, "Frozen fixture current/next EPG window expired before execution"
    return apks[0], receipt, manifest


class MissingHierarchy(RuntimeError):
    """A completed dump produced no fresh nonempty hierarchy, never app PASS."""


class CardsObservation:
    def __init__(self, out):
        self.out = out
        self.sequence = 0
        self.events = []
        self.remote_prefix = "/sdcard/cobra-cards-baseline-%d-" % time.monotonic_ns()

    def screenshot(self, name):
        raw = subprocess.check_output(["adb", "exec-out", "screencap", "-p"], timeout=15)
        assert raw.startswith(b"\x89PNG\r\n\x1a\n"), "Native screenshot missing"
        (self.out / (name + ".png")).write_bytes(raw)

    def ui(self, name="ui"):
        self.sequence += 1
        stem = "%03d-%s" % (self.sequence, name)
        remote = self.remote_prefix + "%03d.xml" % self.sequence
        started = time.monotonic()
        command = ["adb", "shell", "uiautomator", "dump", "--compressed", remote]
        diagnostic = {"command": command, "remote_fresh_path": remote}
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            decode = lambda value: value.decode(errors="replace") if isinstance(value, bytes) else value or ""
            diagnostic.update(exit_code=None, timed_out=True, stdout=decode(error.stdout), stderr=decode(error.stderr))
            (self.out / (stem + "-dump.json")).write_text(json.dumps(diagnostic, indent=2) + "\n")
            raise
        diagnostic.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
        (self.out / (stem + "-dump.json")).write_text(json.dumps(diagnostic, indent=2) + "\n")
        if result.returncode:
            raise RuntimeError("Hierarchy dump command failed (%d): %s; see %s-dump.json" %
                               (result.returncode, result.stderr[-1500:], stem))
        present = subprocess.run(["adb", "shell", "test", "-s", remote],
                                 capture_output=True, text=True, timeout=30)
        diagnostic.update(nonempty_check_exit_code=present.returncode,
                          nonempty_check_stdout=present.stdout, nonempty_check_stderr=present.stderr)
        (self.out / (stem + "-dump.json")).write_text(json.dumps(diagnostic, indent=2) + "\n")
        if present.returncode == 1 and not present.stdout.strip() and not present.stderr.strip():
            self.events.append({"observation_miss": stem, "reason": "NO_FRESH_NONEMPTY_XML",
                                "dump_exit_code": result.returncode,
                                "native_hierarchy_seconds": round(time.monotonic() - started, 3)})
            raise MissingHierarchy("No fresh nonempty hierarchy: %s; dump stdout=%r stderr=%r; see %s-dump.json" %
                                   (remote, result.stdout, result.stderr, stem))
        if present.returncode:
            raise RuntimeError("Hierarchy file check failed (%d): %s" % (present.returncode, present.stderr[-1500:]))
        raw = adb("shell", "cat", remote)
        (self.out / (stem + ".xml")).write_text(raw)
        snap = Snapshot(raw)
        self.events.append({"observation": stem, "native_hierarchy_seconds": round(time.monotonic() - started, 3)})
        return snap

    def press(self, node, purpose, clip=None):
        hit = intersect(bounds(node), clip) if clip else bounds(node)
        assert positive(hit), "No visible target: " + purpose
        coordinate = center(hit)
        started = time.monotonic()
        adb("shell", "input", "tap", *(str(value) for value in coordinate))
        self.events.append({"coordinate_press": purpose, "bounds": list(hit), "coordinate": list(coordinate)})
        return started

    def tap(self, pattern, native_dialog=False, sheet_scroll=False, attempts=8):
        for attempt in range(attempts):
            snap = self.ui("target")
            node = snap.find(pattern, enabled=True, clickable=True)
            if node is not None:
                return self.press(node, pattern)
            item = snap.native_dialog_item(pattern) if native_dialog else None
            if item is not None:
                return self.press(item[0], "Native dialog item " + pattern, item[1])
            if sheet_scroll:
                for candidate in reversed(snap.nodes):
                    if candidate.get("class") == "android.widget.ScrollView" and candidate.get("scrollable") == "true":
                        box = bounds(candidate)
                        if positive(box):
                            inset = max(30, (box[3] - box[1]) // 8)
                            x = (box[0] + box[2]) // 2
                            adb("shell", "input", "swipe", str(x), str(box[3] - inset), str(x), str(box[1] + inset), "350")
                            self.events.append({"native_sheet_scroll": list(box)})
                            break
            if attempt + 1 != attempts:
                time.sleep(.5)
        raise RuntimeError("Visible action not observed: " + pattern + "; labels=" + repr(snap.labels()))

    @staticmethod
    def grid(snap):
        candidates = [node for node in snap.nodes if node.get("package") == PACKAGE
                      and node.get("class") == "android.widget.GridView" and positive(bounds(node))]
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def channel_count(snap):
        for label in snap.labels():
            found = re.search(r"COBRA LIVE\s*[·•]\s*(\d[\d,.\s\u00a0\u202f\u066c]*)\s+CHANNELS", label)
            if found:
                return int(re.sub(r"\D", "", found.group(1)))
        return None

    def cards_ready(self, snap):
        if snap.find(r"^Cards$") is None or snap.find(r"^Pro$|^Previous Pro source$|^Return to preview$") is not None:
            return False
        if snap.find(r"^All channels / Channel wall") is None or self.channel_count(snap) != CHANNEL_COUNT:
            return False
        grid = self.grid(snap)
        return grid is not None and any(re.match(r"^Cards QA \d{5},", node.get("content-desc", ""))
                                        for node in grid.iter("node"))

    def wait_cards(self, attempts=10):
        last_labels = []
        for attempt in range(attempts):
            try:
                snap = self.ui("cards-state")
            except MissingHierarchy:
                pass  # Consume this existing finite observation attempt.
            else:
                last_labels = snap.labels()
                if self.cards_ready(snap):
                    return snap
            if attempt + 1 != attempts:
                time.sleep(.5)
        raise RuntimeError("Exact Cards / 20,226 / All-channels grid was not observed; labels=" + repr(last_labels))

    def hints(self, snap):
        grid = self.grid(snap)
        assert grid is not None, "One visible native Cards grid required"
        visible = []
        for node in grid.iter("node"):
            found = re.match(r"^Cards QA (\d{5}),", node.get("content-desc", ""))
            hit = intersect(bounds(node), bounds(grid))
            if found and positive(hit):
                visible.append({"fixture_channel_number": int(found.group(1)), "bounds": list(bounds(node)),
                                "selected": node.get("selected") == "true", "focused": node.get("focused") == "true"})
        visible.sort(key=lambda row: (row["bounds"][1], row["bounds"][0]))
        return {"actual_header_channel_count": self.channel_count(snap), "grid_bounds": list(bounds(grid)),
                "visible_cards": visible, "selected_visible_fixture_numbers": [row["fixture_channel_number"] for row in visible if row["selected"]],
                "limit": "Public accessibility hints only; no private absolute scroll offset or offscreen selected-card assertion"}


def snapshot_resources(out, name):
    memory = adb("shell", "dumpsys", "meminfo", PACKAGE)
    cpu = adb("shell", "dumpsys", "cpuinfo")
    (out / (name + "-meminfo.txt")).write_text(memory)
    (out / (name + "-cpuinfo.txt")).write_text(cpu)
    def number(label):
        match = re.search(label + r":\s*(\d+)", memory)
        return int(match.group(1)) if match else None
    observed = re.search(r"^\s*([0-9.]+)%\s+\d+/" + re.escape(PACKAGE) + r":", cpu, re.M)
    return {"name": name, "PSS_KiB": number("TOTAL PSS"), "RSS_KiB": number("TOTAL RSS"),
            "cpu_snapshot_percent": float(observed.group(1)) if observed else None,
            "limit": "Finite process snapshots with Android's reported CPU averaging window; no leak, battery or thermal conclusion"}


def run(signed, signature, fixtures, out):
    apk, receipt, manifest = validate_inputs(signed, signature, fixtures)
    assert not out.exists(), "Fresh result directory required"
    out.mkdir(parents=True)
    shutil.copyfile(fixtures / "FIXTURE.json", out / "FIXTURE.json")
    shutil.copyfile(signed / "BUILD-RECEIPT.json", out / "BUILD-RECEIPT.json")
    shutil.copyfile(signature, out / "ORIGINAL-SIGNATURE.txt")
    (out / "fixture").mkdir()
    for name in ("cards-20226.m3u", "cards-epg.xml"):
        shutil.copyfile(fixtures / name, out / "fixture" / name)
    report = {"scope": "ACCEPTED_SIGNED431_FINITE_CARDS_ANDROID_BASELINE", "versionCode": VERSION,
              "signed_source": SOURCE, "APK_sha256": APK_SHA256, "fixture_manifest_sha256": sha256(fixtures / "FIXTURE.json"),
              "physical_Fold": "NOT_RUN", "Infinity": "NOT_LAUNCHED", "shutdown": "NOT_RUN",
              "warm_returns": [], "scroll_swipes": [], "resource_snapshots": [], "state_differences": []}
    observation = CardsObservation(out / "journey")
    observation.out.mkdir()
    try:
        probe(apk, out / "cold-probe", APK_SHA256)
        cold_raw = (out / "cold-probe/launch.txt").read_text()
        report["cold_welcome"] = {"sample_count": 1, "am_start_W": activity_times(cold_raw),
                                  "first_screen_observer": json.loads((out / "cold-probe/OUTCOME.json").read_text()),
                                  "limit": "Single fresh sample. Accessibility/notice observer includes overhead; no p50/p95 or clean first-frame claim."}
        for name, args in (("display.txt", ("shell", "dumpsys", "display")),
                           ("configuration.txt", ("shell", "am", "get-config")),
                           ("power-saving.txt", ("shell", "settings", "get", "global", "low_power"))):
            (out / name).write_text(adb(*args))
        with zipfile.ZipFile(apk) as source:
            native_paths = {name for name in source.namelist() if name.startswith("lib/arm64-v8a/") and name.endswith(".so")}
        observation.tap(r"ADD TV SOURCE")
        observation.tap(r"^M3U / M3U8 playlist$", native_dialog=True)
        values = ("CobraCardsQA", "http://10.0.2.2:8765/cards-20226.m3u", "http://10.0.2.2:8765/cards-epg.xml")
        for index, value in enumerate(values):
            fields = [node for node in observation.ui("source-form").nodes if node.get("class") == "android.widget.EditText"]
            assert len(fields) == 3, "Normal M3U source form must have three fields"
            observation.press(fields[index], "M3U source field " + str(index))
            focused = [node for node in observation.ui("focused-source-form").nodes if node.get("class") == "android.widget.EditText"]
            assert len(focused) == 3 and focused[index].get("focused") == "true", "IME moved the expected input field"
            adb("shell", "input", "text", value)
        saved_at = observation.tap(r"^TEST & SAVE$")
        for attempt in range(15):
            try:
                snap = observation.ui("source-save-return")
            except MissingHierarchy:
                pass  # Consume this existing finite observation attempt.
            else:
                if snap.find(r"^Return to preview$") is not None and snap.find(r"^Multi-View$") is not None:
                    adb("shell", "input", "keyevent", "KEYCODE_BACK")
                    observation.events.append({"navigation": "ONE_BACK_FROM_SOURCE_VALIDATION_AUTO_FULLSCREEN; NO_FULLSCREEN_BUTTON_TEST"})
                    break
                if snap.find(r"^Cards QA \d{5},") is not None:
                    break
            if attempt != 14:
                time.sleep(.5)
        else:
            raise RuntimeError("Imported fixture inventory was not observed after normal source save")
        observation.tap(r"^Choose one of five view modes$|^Choose view mode$|^Views$")
        observation.tap(r"^Cards,", sheet_scroll=True)
        snap = observation.wait_cards()
        report["source_save_to_first_cards_observed_upper_bound_seconds"] = round(time.monotonic() - saved_at, 3)
        report["first_cards_timing_limit"] = "Includes source validation/import, normal mode selection and all host accessibility-query overhead; not isolated first-card render latency."
        report["initial_cards"] = observation.hints(snap)
        observation.screenshot("first-cards")
        report["resource_snapshots"].append(snapshot_resources(out, "cards-initial"))
        for sample in range(1, 4):
            before = observation.hints(observation.wait_cards())
            adb("shell", "input", "keyevent", "KEYCODE_HOME")
            started = time.monotonic()
            launch = adb("shell", "am", "start", "-W", "-n", COBRA)
            (out / ("warm-%d-launch.txt" % sample)).write_text(launch)
            notice = acknowledge_known_notice_after_launch(launch, out / ("warm-%d-notice" % sample), native_paths)
            after = observation.hints(observation.wait_cards())
            elapsed = time.monotonic() - started
            same_visible = before["visible_cards"] == after["visible_cards"]
            entry = {"sample": sample, "am_start_W": activity_times(launch),
                     "return_to_confirmed_cards_upper_bound_seconds": round(elapsed, 3), "OS_notice": notice,
                     "before": before, "after": after, "same_visible_card_hints": same_visible}
            report["warm_returns"].append(entry)
            if not same_visible:
                report["state_differences"].append({"warm_sample": sample, "scope": "VISIBLE_CARD_BOUNDS_SELECTION_FOCUS_HINTS_CHANGED; NOT_PRIVATE_SCROLL_OFFSET"})
            observation.screenshot("warm-%d-cards" % sample)
            report["resource_snapshots"].append(snapshot_resources(out, "warm-%d" % sample))
        warm = [sample["return_to_confirmed_cards_upper_bound_seconds"] for sample in report["warm_returns"]]
        report["warm_observer_summary"] = {"sample_count": len(warm), "p50_seconds": nearest_rank(warm, .5),
                                           "p95_seconds": nearest_rank(warm, .95),
                                           "limit": "Three finite samples; p95 is the maximum nearest-rank sample, includes notice/hierarchy overhead and is not stable population p95."}
        before_frames = adb("shell", "dumpsys", "gfxinfo", PACKAGE, "framestats")
        (out / "scroll-before-gfxinfo.txt").write_text(before_frames)
        report["resource_snapshots"].append(snapshot_resources(out, "scroll-before"))
        frame_samples = []
        for step in range(1, 9):
            snap = observation.wait_cards()
            before = observation.hints(snap)
            box = bounds(observation.grid(snap))
            assert box[2] - box[0] >= 64 and box[3] - box[1] >= 96, "Usable native grid viewport required"
            inset = max(24, (box[3] - box[1]) // 6)
            x = (box[0] + box[2]) // 2
            started = time.monotonic()
            adb("shell", "input", "swipe", str(x), str(box[3] - inset), str(x), str(box[1] + inset), "350")
            after = observation.hints(observation.wait_cards())
            before_positions = [(row["fixture_channel_number"], *row["bounds"]) for row in before["visible_cards"]]
            after_positions = [(row["fixture_channel_number"], *row["bounds"]) for row in after["visible_cards"]]
            assert before_positions != after_positions, "Native grid swipe did not produce observable card movement"
            report["scroll_swipes"].append({"step": step, "grid_bounds": list(box), "coordinate_swipe": [x, box[3] - inset, x, box[1] + inset, 350],
                                            "before": before, "after": after,
                                            "swipe_to_observed_cards_upper_bound_seconds": round(time.monotonic() - started, 3)})
            observation.screenshot("scroll-%d" % step)
            frames = adb("shell", "dumpsys", "gfxinfo", PACKAGE, "framestats")
            (out / ("scroll-%d-gfxinfo.txt" % step)).write_text(frames)
            frame_samples.append(frames)
        report["scroll_HWUI"] = summarize_frames(before_frames, frame_samples)
        report["resource_snapshots"].append(snapshot_resources(out, "scroll-after"))
        report["final_cards"] = observation.hints(observation.wait_cards())
        report["status"] = "BASELINE_OBSERVED_WITH_STATE_DIFFERENCES" if report["state_differences"] else "FINITE_BASELINE_OBSERVED; NO_PERFORMANCE_GAIN_OR_PHYSICAL_ACCEPTANCE_CLAIM"
    except Exception as error:
        report["status"] = "FAILED_AT_RECORDED_BASELINE_OPERATION"
        report["error"] = str(error)
        (out / "ERROR.txt").write_text(traceback.format_exc())
        raise
    finally:
        report["UI_events"] = observation.events
        for name, args in (("terminal-activity.txt", ("shell", "dumpsys", "activity", "activities")),
                           ("terminal-logcat.txt", ("logcat", "-d", "-t", "4000", "-v", "threadtime"))):
            try:
                (out / name).write_text(adb(*args, check=False))
            except Exception as error:
                report.setdefault("diagnostic_errors", []).append(name + ": " + str(error))
        try:
            observation.ui("terminal")
        except Exception as error:
            report.setdefault("diagnostic_errors", []).append("terminal hierarchy: " + str(error))
        try:
            observation.screenshot("terminal")
        except Exception as error:
            report.setdefault("diagnostic_errors", []).append("terminal screenshot: " + str(error))
        report.setdefault("status", "FAILED_BEFORE_COMPLETION")
        (out / "OUTCOME.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("signed", "signature", "fixtures", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    run(**vars(parser.parse_args()))
