#!/usr/bin/env python3
"""Deliver exact Infinity 2103391 embedded add-ons as separately installable ZIPs.

Only distribution artifacts are written; do not edit signed APK, native engine,
Cobra, shutdown, Rails code, provider/addon user data or feature scope.

User-installed add-ons may supersede identically-ID'd APK embedded assets.
For four changed add-ons, bump the standalone addon.xml version attribute only
to make normal Kodi install-over upgrades unambiguous; every OTHER addon
member must be byte-identical to the permanently signed 2103391 APK.

Rails 0.2.7 is unchanged from the signed 2103391 package; include a matching
reinstallable ZIP for older manually installed Rails. No invented Rails changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

SIGNED_BASE_2103390 = "778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb"
EXPECTED_CERT = "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
EXPECTED_VERSION_CODE = 2103391
PREFIX = "assets/addons/"

# ID / embedded 2103391 version / standalone install-over version / install order
PACKAGES = (
    ("script.infinity.commandcenter", "0.3.5.20", "0.3.5.21", 1),
    ("script.infinity.watchedbridge", "1.0.1", "1.0.2", 2),
    ("script.infinity.uirepair", "0.1.2", "0.1.3", 3),
    ("script.infinity.rails", "0.2.7", "0.2.7", 4),
    ("skin.infinity.diggz", "1.0.5.228", "1.0.5.229", 5),
)
EXPECTED_CHANGED_ADDONS = {
    "skin.infinity.diggz",
    "script.infinity.commandcenter",
    "script.infinity.watchedbridge",
    "script.infinity.uirepair",
}
REQUIRED_PATHS = {
    "skin.infinity.diggz": (
        "unified/Home.xml",
        "unified/VideoOSD.xml",
        "unified/AddonBrowser.xml",
        "unified/Custom_1191_InfinitySystemHub.xml",
        "unified/DialogSettings.xml",
    ),
    "script.infinity.commandcenter": ("plugin.py", "resume_hub.py"),
    "script.infinity.watchedbridge": ("CONTROLLER-PREIMAGES.json",),
    "script.infinity.uirepair": (
        "runtime.py",
        "home_option_b.py",
        "resources/skins/Default/1080i/InfinityHomeOptionB.xml",
        "CONTROLLER-PREIMAGES.json",
    ),
    "script.infinity.rails": ("addon.xml",),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(reason: str):
    raise ValueError("Infinity 2103391 matching add-on export REFUSED: " + reason)


def safe_member(name: str) -> bool:
    pp = PurePosixPath(name)
    return (bool(name) and not name.startswith("/") and "\\" not in name
            and not name.endswith("/") and "//" not in name
            and all(part not in ("", ".", "..") for part in pp.parts)
            and len(pp.parts) > 3)


def new_manifest(data: bytes, addon_id: str, old_version: str, new_version: str) -> bytes:
    root = ET.fromstring(data)
    if root.tag != "addon" or root.get("id") != addon_id or root.get("version") != old_version:
        fail("unexpected signed add-on manifest: " + addon_id)
    # Preserve comments, imports, dependency constraints, XML formatting
    # and all metadata. Only the original root version attribute may change.
    m = re.search(rb"<addon\b[^>]*>", data, flags=re.DOTALL)
    if not m:
        fail("root addon tag absent: " + addon_id)
    start, stop = m.span()
    opening = data[start:stop]
    attr = list(re.finditer(rb'\bversion\s*=\s*(["\'])([^"\']+)\1', opening))
    if len(attr) != 1 or attr[0].group(2) != old_version.encode():
        fail("ambiguous original manifest version: " + addon_id)
    change = opening[:attr[0].start(2)] + new_version.encode() + opening[attr[0].end(2):]
    result = data[:start] + change + data[stop:]
    current = ET.fromstring(result)
    if current.get("id") != addon_id or current.get("version") != new_version:
        fail("standalone version upgrade failed: " + addon_id)
    if result.replace(change, opening, 1) != data:
        fail("unexpected manifest structure change: " + addon_id)
    return result


def verify_signed_receipt(apk: Path, receipt_path: Path) -> dict:
    info = json.loads(receipt_path.read_text())
    allowed = {
        "experimental_only": True, "signed_permanently": True,
        "changed_existing_apk_members": 128, "new_first_party_apk_members": 2,
        "original_apk_members": 7430,
        "actual_SIGSEGV_139_root_cause_fixed": False,
        "physical_fold_accepted": False,
        "user_final_LOCK": False,
    }
    for name, expected in allowed.items():
        if info.get(name) != expected:
            fail("signed all-in-one receipt failed " + name)
    if info.get("original_apk_sha256") != SIGNED_BASE_2103390:
        fail("original source is not protected 2103390")
    if info.get("signer_sha256") != EXPECTED_CERT:
        fail("wrong permanent Infinity signing identity")
    if info.get("apk_sha256") != sha(apk.read_bytes()):
        fail("APK contents do not match signed release receipt")
    if info.get("feature_freeze_after_this_apk") != "NO_NEW_FEATURES_BUG_FIXES_ONLY":
        fail("feature-freeze contract missing")
    return info


def export(apk: Path, signed_receipt: Path, out: Path) -> dict:
    apk, signed_receipt, out = (Path(x).resolve() for x in (apk, signed_receipt, out))
    if out == apk.parent or apk.is_relative_to(out):
        fail("refusing to modify or stage alongside signed APK")
    report = verify_signed_receipt(apk, signed_receipt)
    if not out.exists():
        out.mkdir(parents=True)
    if any(out.iterdir()):
        fail("delivery directory must be empty; refuse overwrite")

    with ZipFile(apk) as original:
        names = original.namelist()
        if original.testzip() is not None or len(names) != len(set(names)):
            fail("corrupt or duplicate original APK members")
        by_id = {addon: [] for addon, *_ in PACKAGES}
        for name in names:
            if not name.startswith(PREFIX):
                continue
            pieces = name[len(PREFIX):].split("/", 1)
            if len(pieces) != 2 or pieces[0] not in by_id or name.endswith("/"):
                continue
            if not safe_member(name):
                fail("unsafe bundled add-on path " + name)
            by_id[pieces[0]].append(name)
        ledger = []
        for addon_id, installed, standalone, order in PACKAGES:
            source_files = sorted(by_id[addon_id])
            base = PREFIX + addon_id + "/"
            for must in REQUIRED_PATHS[addon_id]:
                if base + must not in source_files:
                    fail("signed APK lacks approved " + addon_id + " member " + must)
            manifest = original.read(base + "addon.xml")
            adjusted = new_manifest(manifest, addon_id, installed, standalone)
            if len(source_files) < (300 if addon_id == "skin.infinity.diggz" else 2):
                fail("incomplete embedded add-on " + addon_id)
            # Installation order is deliberate: Command Center source first,
            # matching preimage consumers next, skin last after first-party scripts.
            filename = addon_id + "-" + standalone + "-Infinity-2103391-TEST.zip"
            destination = out / filename
            source_sha = {}
            with ZipFile(destination, "w", compression=ZIP_DEFLATED,
                         compresslevel=6, allowZip64=True) as target:
                for member in source_files:
                    rel = member[len(PREFIX):]
                    data = original.read(member)
                    if rel == addon_id + "/addon.xml":
                        data = adjusted
                    else:
                        source_sha[rel] = sha(data)
                    target.writestr(rel, data)
            with ZipFile(destination) as standalone_zip:
                written = standalone_zip.namelist()
                if len(written) != len(source_files) or len(set(written)) != len(written):
                    fail("ZIP has missing/duplicate components " + addon_id)
                if standalone_zip.testzip() is not None:
                    fail("ZIP integrity failure " + addon_id)
                for member in source_files:
                    rel = member[len(PREFIX):]
                    expected = adjusted if rel == addon_id + "/addon.xml" else original.read(member)
                    if standalone_zip.read(rel) != expected:
                        fail("standalone code not an exact APK match: " + member)
                if ET.fromstring(standalone_zip.read(addon_id+"/addon.xml")).get("version") != standalone:
                    fail("standalone manifest version mismatch: " + addon_id)
            deps = [(v.get("addon"), v.get("version")) for v in
                    ET.fromstring(adjusted).findall("./requires/import")]
            ledger.append(dict(
                install_order=order,
                addon_id=addon_id,
                contained_in_signed_apk=True,
                signed_apk_embedded_version=installed,
                separately_installable_version=standalone,
                version_attribute_only_changed=(installed != standalone),
                source_members=len(source_files),
                addon_code_byte_identical_to_signed_apk=True,
                member_hashes=source_sha,
                standalone_zip=filename,
                standalone_sha256=sha(destination.read_bytes()),
                standalone_zip_bytes=destination.stat().st_size,
                deps=deps
            ))
    if [i["addon_id"] for i in ledger] != [x[0] for x in PACKAGES]:
        fail("delivery package set missing expected first-party components")
    if {i["addon_id"] for i in ledger if i["version_attribute_only_changed"]} != EXPECTED_CHANGED_ADDONS:
        fail("unexpected external add-on version amendments")
    summary = {
        "source_apk": apk.name,
        "source_signed_apk_sha256": report["apk_sha256"],
        "source_version_code": 2103391,
        "original_signed_2103390_preserved": True,
        "standalone_addon_archives": len(ledger),
        "all_addon_code_identical_to_signed_apk_except_version_attributes": True,
        "rails_new_logic_in_2103391": False,
        "option_b_requires_native_2103391_and_uirepair": True,
        "group1_task19_reload_fixed": False,
        "group5_native_SIGSEGV_139_fixed": False,
        "feature_freeze": "NO_NEW_FEATURES_BUG_FIXES_ONLY",
        "physical_fold_tested": False,
        "user_final_lock": False,
        "no_uninstall_no_data_clear": True,
        "installation_order": [item["addon_id"] for item in ledger],
        "archives": ledger,
    }
    (out/"INFINITY-2103391-MATCHING-ZIPS.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True)+"\n")
    (out/"SHA256SUMS").write_text("".join(
        item["standalone_sha256"] + "  " + item["standalone_zip"] + "\n" for item in ledger))
    (out/"INSTALL-ORDER.txt").write_text(
        "Infinity 2103391 experimental: matching separately installable ZIPs\n"
        "Do not uninstall Infinity or clear addon/user data. Preserve 2103390 rollback.\n"
        "1. Install permanently signed 2103391 APK over current Infinity (not clean install).\n"
        "2. In Kodi: Add-ons > Install from ZIP file, in this exact order:\n"
        "   a. script.infinity.commandcenter (0.3.5.21)\n"
        "   b. script.infinity.watchedbridge (1.0.2)\n"
        "   c. script.infinity.uirepair (0.1.3)\n"
        "   d. script.infinity.rails (0.2.7; same source as 2103390)\n"
        "   e. skin.infinity.diggz (1.0.5.229; LAST)\n"
        "3. Choose/keep the skin ID skin.infinity.diggz. Do not install stock Diggz.\n"
        "4. Close/reopen Infinity normally; check installed addon versions first.\n"
        "5. Verify Home, Movie/TV Option B, Add-on Browser, Player menus, Silent Mode,\n"
        "   Cobra, saved/resume state and Essential-First Close on actual Fold.\n"
        "This set is experimental, not Fold-qualified or user-locked.\n"
        "Group1 task19 and native SIGSEGV/139 root cause remain open.\n")
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--signed-apk",type=Path,required=True)
    p.add_argument("--signed-receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    r=export(args.signed_apk,args.signed_receipt,args.out)
    print(json.dumps({k:r[k] for k in
        ("source_signed_apk_sha256","standalone_addon_archives","installation_order",
         "all_addon_code_identical_to_signed_apk_except_version_attributes",
         "rails_new_logic_in_2103391","physical_fold_tested")},indent=2))
