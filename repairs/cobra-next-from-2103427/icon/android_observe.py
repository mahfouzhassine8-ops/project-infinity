#!/usr/bin/env python3
"""Finite final-APK Android37 theme/launcher observation, before any video plays.

No install, component toggle, package reset, private data access, icon launch,
Infinity launch, root, force-stop or application shutdown. The parent has already
verified/installed the exact signed APK and observed Cobra's empty welcome.

`cmd overlay lookup` establishes framework resource selection, not Drawable
inflation or universal launcher parity. Actual launcher frames are separate
evidence, with explicit partial/cache outcomes.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

# Preserve the existing direct-script CLI as well as run_android_probe imports.
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_probe import acknowledge_known_notice_after_launch

PACKAGE = "com.projectinfinity.kodi"
COBRA = PACKAGE + "/.InfinityLiveActivity"
VERSION = 2103431


def observe(out: Path, apk_sha256: str, version_code: int, native_paths=None):
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "scope": "EXACT_FINAL_COMBINED_APK_ANDROID37_THEME_AND_LAUNCHER_OBSERVATION_ONLY",
        "versionCode": version_code, "receipt_apk_sha256": apk_sha256,
        "APK_binding": "Parent verified signed APK/signature/hash and installed it before this observer",
        "physical_Samsung": "NOT_RUN", "shutdown": "NOT_RUN", "Infinity": "NOT_LAUNCHED",
        "lookup_limit": "Framework Res_value selection only; not a direct Drawable.inflate test",
        "launcher_limit": "Only this disposable emulator launcher and refresh/re-entry sequence; Samsung/Finder/suggestions and monochrome palettes remain OS-managed",
        "operations": [], "modes": {},
    }

    def command(*args, check=True):
        try:
            p = subprocess.run(["adb", *args], capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            report["operations"].append({"adb": list(args), "returncode":124,"error":"ADB30s operation timeout"})
            if check: raise RuntimeError("adb operation timed out: " + repr(args[:3]))
            return {"stdout":"","stderr":"ADB30s operation timeout","returncode":124}
        report["operations"].append({"adb": list(args), "returncode": p.returncode})
        if check and p.returncode:
            raise RuntimeError("adb operation failed: " + repr(args[:3]) + "; " + p.stderr[-500:])
        return {"stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode}

    def text(*args, check=True): return command(*args, check=check)["stdout"]

    def ui(folder, tag):
        dump = command("shell", "uiautomator", "dump", "/sdcard/infinity-icon-qa.xml", check=False)
        data = text("shell", "cat", "/sdcard/infinity-icon-qa.xml", check=False)
        (folder/(tag+".xml")).write_text(data)
        p = subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True, timeout=20)
        report["operations"].append({"adb": ["exec-out", "screencap", "-p"], "returncode": p.returncode})
        (folder/(tag+".png")).write_bytes(p.stdout)
        try: nodes = list(ET.fromstring(data).iter("node"))
        except ET.ParseError: nodes = []
        return nodes, p.stdout, dump

    def read_bounds(n):
        b = [int(v) for v in re.findall(r"-?\d+", n.get("bounds", ""))]
        return b if len(b) == 4 and b[2] > b[0] and b[3] > b[1] else None

    def classify_icon(nodes, screenshot, folder):
        # Launcher labels belong to native BubbleTextViews and identify their
        # actual item bounds; never substitute a guessed screen coordinate.
        matches = []
        for n in nodes:
            label = n.get("text", "").strip() or n.get("content-desc", "").strip()
            if label == "Infinity" and n.get("package") == report.get("launcher_package"):
                b = read_bounds(n)
                if b: matches.append((n, b))
        result = {"exact_Infinity_labels": len(matches), "classification": "UNOBSERVABLE"}
        if len(matches) != 1:
            result["reason"] = "A single visible native Infinity launcher item was not observed"
            return result
        _, b = matches[0]; result["native_item_bounds"] = b
        try:
            # Use the same audited stdlib decoder as resource host checks.
            try: from .resources import png_rgba, png_encode
            except ImportError: from resources import png_rgba, png_encode
            w, h, rgba = png_rgba(screenshot)
            left, top, right, bottom = b
            left, right = max(0,left), min(w,right); top, bottom = max(0,top), min(h,bottom)
            # Native bubble includes its text label below the icon. Analyze
            # its top square region and retain exact crop coordinates.
            bottom = min(bottom, top + right-left)
            if right-left < 24 or bottom-top < 24:
                raise ValueError("Native item bounds do not include a usable icon region")
            pixels = bytearray(); cyan = white = black = 0
            for y in range(top, bottom):
                line = rgba[(y*w+left)*4:(y*w+right)*4]; pixels += line
                for i in range(0,len(line),4):
                    r,g,b,a = line[i:i+4]
                    cyan += int(g > 80 and b > 80 and g > r*1.7 and b > r*1.7)
                    white += int(min(r,g,b) >= 235)
                    black += int(max(r,g,b) <= 48)
            total = (right-left)*(bottom-top)
            result.update(crop_bounds=[left,top,right,bottom], pixels=total,
                          cyan_pixels=cyan, white_pixels=white, dark_pixels=black)
            if cyan >= max(8,total*.002): result["classification"] = "DARK_CYAN_EMBLEM_OBSERVED"
            elif white >= total*.3 and black >= max(5,total*.002): result["classification"] = "LIGHT_BLACK_ON_WHITE_OBSERVED"
            else: result["classification"] = "UNCLASSIFIED_NATIVE_ITEM_COLORS"
            (folder/"Infinity-item-crop.png").write_bytes(png_encode(right-left,bottom-top,pixels))
        except Exception as e:
            result["reason"] = "Read-only screenshot classification unavailable: " + str(e)
        return result

    failure = None; original_mode = None; safe_Cobra_return = False
    try:
        if version_code != VERSION or not re.fullmatch(r"[0-9a-f]{64}", apk_sha256):
            raise RuntimeError("Observer requires the exact final2103431 receipt")
        serial = text("get-serialno").strip()
        sdk = text("shell", "getprop", "ro.build.version.sdk").strip()
        qemu = text("shell", "getprop", "ro.kernel.qemu").strip()
        if not (serial.startswith("emulator-") and sdk == "37" and qemu == "1"):
            raise RuntimeError("Disposable Android37 emulator required")
        package = text("shell", "dumpsys", "package", PACKAGE)
        (out/"installed-package.txt").write_text(package)
        if not re.search(r"\bversionCode="+str(VERSION)+r"\b", package):
            raise RuntimeError("Installed package version does not match final receipt")
        # It is safe to leave this Cobra welcome temporarily: no active streams
        # or user source settings exist yet. Enforce this stage via native UI.
        nodes, _, _ = ui(out, "before-Cobra-welcome")
        if not any(n.get("package") == PACKAGE and re.search(r"ADD TV SOURCE|Add a TV source", n.get("text", "") + n.get("content-desc", ""), re.I) for n in nodes):
            raise RuntimeError("Icon observation must run at empty Cobra welcome before playback/source import")
        safe_Cobra_return = True
        original = text("shell", "cmd", "uimode", "night", check=False)
        (out/"initial-night-mode.txt").write_text(original)
        found = re.search(r"Night mode:\s*(no|yes|auto|custom)\b", original, re.I)
        if found and found.group(1).lower() in ("no","yes"): original_mode = found.group(1).lower()
        home = text("shell", "cmd", "package", "resolve-activity", "--brief", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME", check=False)
        (out/"launcher-component.txt").write_text(home)
        components = re.findall(r"([A-Za-z0-9_.]+)/(\S+)", home)
        if not components: raise RuntimeError("Actual HOME launcher could not be resolved")
        report.update(serial=serial,sdk=sdk,launcher_package=components[-1][0],launcher_component="/".join(components[-1]))
        wm = text("shell", "wm", "size")
        size = re.findall(r"(\d+)x(\d+)", wm)
        if not size: raise RuntimeError("Actual emulator display size unavailable")
        width,height = map(int,size[-1]); report["display"] = [width,height]
        for mode, expected in (("no", {"ic_launcher":"res/infinity_launcher_light_v33.xml", "ic_launcher_round":"res/infinity_launcher_light_v33.xml"}),
                               ("yes", {"ic_launcher":"res/IG.xml", "ic_launcher_round":"res/6H.xml"})):
            folder = out/("light" if mode == "no" else "dark"); folder.mkdir()
            state = {"requested_night_mode":mode,"resource_lookups":{},"launcher_frames":[]}
            report["modes"][mode] = state
            state["set_night_mode"] = command("shell", "cmd", "uimode", "night", mode, check=False)
            for name,path in expected.items():
                samples = []
                for attempt in range(3):
                    value = command("shell","cmd","overlay","lookup","--verbose",PACKAGE,PACKAGE+":mipmap/"+name,check=False)
                    samples.append(value)
                    if path in value["stdout"] and value["returncode"] == 0: break
                    time.sleep(.5)
                state["resource_lookups"][name] = {"expected_path":path,"samples":samples,
                    "status":"PASS" if path in samples[-1]["stdout"] and samples[-1]["returncode"]==0 else "FAIL"}
            (folder/"lookup.json").write_text(json.dumps(state["resource_lookups"],indent=2)+"\n")
            state["actual_uimode"] = text("shell","cmd","uimode","night",check=False)
            state["configuration"] = text("shell","am","get-config",check=False)
            # Supported launcher re-entry and opening its app drawer only.
            # No icon tap, app-data operation or launcher reset is performed.
            for attempt in range(2):
                text("shell","input","keyevent","KEYCODE_HOME")
                text("shell","input","swipe",str(width//2),str(height*9//10),str(width//2),str(height//5),"450")
                nodes, screenshot, dump = ui(folder,"app-drawer-"+str(attempt+1))
                classification = classify_icon(nodes,screenshot,folder)
                state["launcher_frames"].append(classification)
                if classification["classification"] not in ("UNOBSERVABLE","UNCLASSIFIED_NATIVE_ITEM_COLORS"): break
            state["launcher_observation"] = state["launcher_frames"][-1]
        lookups = [v["status"] for state in report["modes"].values() for v in state["resource_lookups"].values()]
        report["framework_resource_selection"] = "PASS" if len(lookups)==4 and all(x=="PASS" for x in lookups) else "FAIL"
        light = report["modes"]["no"]["launcher_observation"]["classification"]
        dark = report["modes"]["yes"]["launcher_observation"]["classification"]
        if light == "LIGHT_BLACK_ON_WHITE_OBSERVED" and dark == "DARK_CYAN_EMBLEM_OBSERVED":
            report["launcher_observation"] = "PASS_DISTINCT_LIGHT_DARK_NATIVE_ITEMS_ON_THIS_EMULATOR_LAUNCHER"
        elif light == dark and light in ("LIGHT_BLACK_ON_WHITE_OBSERVED","DARK_CYAN_EMBLEM_OBSERVED"):
            report["launcher_observation"] = "PARTIAL_LAUNCHER_RETAINS_SAME_ICON_ACROSS_MODE_CHANGE_AND_REENTRY"
        else:
            report["launcher_observation"] = "PARTIAL_NATIVE_ICON_NOT_CONCLUSIVELY_CLASSIFIED; INSPECT_ACTUAL_FRAMES"
        if report["framework_resource_selection"] != "PASS":
            raise RuntimeError("Actual framework launcher resource path did not follow both requested system modes")
        report["status"] = "PASS_FRAMEWORK_AND_EMULATOR_LAUNCHER" if report["launcher_observation"].startswith("PASS_") else "PASS_FRAMEWORK_SELECTION_LAUNCHER_PARTIAL"
    except Exception as e:
        failure = e; report["status"] = "FAIL_AT_RECORDED_ICON_OPERATION"; report["error"] = str(e)
    finally:
        # Restore only an explicitly observed no/yes system setting; never guess
        # how to rewrite auto/custom schedules. Then return through the existing
        # exported Cobra Activity, with no force-stop/restart/data operation.
        if original_mode:
            report["restore_initial_mode"] = command("shell","cmd","uimode","night",original_mode,check=False)
        if safe_Cobra_return:
            report["return_Cobra"] = command("shell","am","start","-W","-n",COBRA,check=False)
            try:
                report["return_Cobra_OS_notice"] = acknowledge_known_notice_after_launch(
                    report["return_Cobra"]["stdout"], out/"return-Cobra-OS-notice", native_paths)
            except Exception as e:
                report["return_Cobra_OS_notice_error"] = str(e)
                if failure is None:
                    failure = e
                    report["status"] = "FAIL_AT_COBRA_RETURN_OS_NOTICE"
        else:
            report["return_Cobra"] = "NOT_RUN; receipt/environment/welcome guard did not pass"
        (out/"OUTCOME.json").write_text(json.dumps(report,indent=2)+"\n")
    if failure: raise failure
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--out",type=Path,required=True)
    p.add_argument("--apk-sha256",required=True); p.add_argument("--version-code",type=int,required=True)
    a=p.parse_args(); observe(a.out,a.apk_sha256,a.version_code)
