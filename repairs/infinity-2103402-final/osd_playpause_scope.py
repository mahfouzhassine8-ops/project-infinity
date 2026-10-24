"""Stage only the approved Play/Pause appearance restoration for Infinity 2103402.

This is an isolated source overlay builder, NOT a signed APK or installable skin.
Requires the exact user-approved 1.0.5.242 skin ZIP and writes only 14 XML
staging files (plus one JSON receipt) under the output directory.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

SKIN_SHA256 = "a3c0998afc7367910968c7cd5ccb6dff4728403a4099543f875717b7b888e20b"
VARIANTS = (
    "16x9", "20x9", "5x6", "6x5", "fallback", "portrait",
    "responsive/base", "responsive/landscape", "responsive/portrait",
    "responsive/square", "responsive/tall", "responsive/ultrawide",
    "responsive/wide", "unified",
)
PREFIX = "skin.infinity.diggz/"
MEMBERS = tuple(PREFIX + mode + "/VideoOSD.xml" for mode in VARIANTS)
PATTERN = re.compile(rb'(<control\s+type="button"\s+id="202">)(.*?)(</control>)', re.S)
OLD = (
    b'<texturefocus>infinity_reference/button_dark.png</texturefocus>',
    b'<texturenofocus>infinity_reference/button_dark.png</texturenofocus>',
)
# Minimum-risk restoration: retain exact original art and icon/button semantics;
# fade the unwanted nearly opaque circular matte to a minimal unobtrusive state.
# Playback and focus actions, video pixels and all other OSD controls are unchanged.
NEW = (
    b'<texturefocus colordiffuse="44FFFFFF">infinity_reference/button_dark.png</texturefocus>',
    b'<texturenofocus colordiffuse="18FFFFFF">infinity_reference/button_dark.png</texturenofocus>',
)


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def patch_one(data: bytes) -> bytes:
    """Byte-preserving transform confined to exact OSD Play/Pause control 202."""
    matches = list(PATTERN.finditer(data))
    if len(matches) != 1:
        raise ValueError("OSD must have exactly one owned Play/Pause control 202")
    m = matches[0]
    original = m.group(2)
    if any(original.count(a) != 1 for a in OLD):
        raise ValueError("Play/Pause texture preimage changed; refuse patch")
    if b'PlayerControl(Play)' not in original:
        raise ValueError("Play/Pause behavior changed; refuse patch")
    revised = original
    for old, new in zip(OLD, NEW):
        revised = revised.replace(old, new, 1)
    out = data[:m.start(2)] + revised + data[m.end(2):]
    ET.fromstring(out)  # XML remains valid; no serializer or global formatting churn.
    if out == data or out.replace(NEW[0], OLD[0]).replace(NEW[1], OLD[1]) != data:
        raise ValueError("Non-target mutation detected")
    return out


def stage(archive: Path, destination: Path, expected_member_hashes: dict[str, str]) -> dict:
    if digest(archive.read_bytes()) != SKIN_SHA256:
        raise ValueError("Skin baseline ZIP hash mismatch. No staging authorized.")
    output = []
    with ZipFile(archive) as zin:
        names = {n for n in zin.namelist() if n.endswith('/VideoOSD.xml')}
        if names != set(MEMBERS):
            raise ValueError("The 14 expected VideoOSD variants were not found exactly")
        if set(expected_member_hashes) != set(MEMBERS):
            raise ValueError("Missing/extra original OSD SHA-256 entries")
        # Complete preflight before writing any staged file.
        staged = []
        for path in MEMBERS:
            b = zin.read(path)
            if digest(b) != expected_member_hashes[path]:
                raise ValueError("Member hash mismatch: " + path)
            candidate = patch_one(b)
            staged.append((path, b, candidate))
        for path, original, candidate in staged:
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(candidate)
            output.append({"path":path,"baseline_sha256":digest(original),
                           "candidate_sha256":digest(candidate),"changed":True})
    receipt = {"scope":"VideoOSD control 202 only; source overlay only",
               "accepted_baseline_sha256":SKIN_SHA256,
               "member_count":len(output),"signed_or_installable":False,
               "fold_acceptance":"NOT RUN","members":output}
    (destination / "OSD-SOURCE-RECEIPT.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return receipt


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit("usage: osd_playpause_scope.py SKIN_ZIP PREIMAGES_JSON OUTPUT_DIRECTORY")
    input_zip, hashes, target = map(Path, argv[1:])
    obj = json.loads(hashes.read_text(encoding='utf-8'))
    receipt = stage(input_zip,target,obj['members'])
    print("Staged",receipt['member_count'],"exact, unsigned OSD source variants only")


if __name__ == '__main__':
    main(sys.argv)
