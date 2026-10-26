"""Inspect exact signed407 sources and compatibility owners without APK mutation."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile
import xml.etree.ElementTree as ET

BASELINE_SHA = "3616c4e69c976bd63b36170d4dbbd9b190a7ec2eace4bc0c34c3c72f7f9e8578"
SEARCH_SHA = "bb6e8791ca7644ca9d370b5871d69ded71790557069b56535e920baa6cf50531"
EXPECTED_COMPONENTS = {
    "script.infinity.commandcenter-0.3.5.39-2103407-QA.zip": "085626880963b4ae43870ff7fb57746d45dfa3ea7ce56ea2dd6be7fe53768fcf",
    "script.infinity.watchedbridge-1.0.20-2103407-QA.zip": "42a03a9c3c8452d8f1f8cffc651c2805902bf9376b18975e8828af023218f55a",
    "script.infinity.uirepair-0.1.22-2103407-QA.zip": "f37749294e5f3f0a6f431fbbe06c728e7ea3e08f7f455bcde5cf080739a222a7",
    "skin.infinity.diggz-1.0.5.243.zip": "0adfed89f1d5384a3fa3a023152c7c2a094ef2edb6dd60129f336fe3b7cb9ef9",
}
CC = "script.infinity.commandcenter"
OWNERS = (CC, "script.infinity.watchedbridge", "script.infinity.uirepair", "script.infinity.rails")
PREFIX = "assets/addons/"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(4*1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def inspect(root, output):
    apks = list(root.rglob("*.apk"))
    assert len(apks) == 1, "Exactly one signed baseline APK required"
    apk = apks[0]
    assert file_sha(apk) == BASELINE_SHA, "Signed407 baseline digest differs"
    for name, wanted in EXPECTED_COMPONENTS.items():
        found = list(root.rglob(name))
        assert len(found) == 1 and file_sha(found[0]) == wanted, "Matching component differs: "+name
    output.mkdir(parents=True, exist_ok=False)
    with ZipFile(apk) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), "Duplicate APK member"
        cc_search = archive.read(PREFIX+CC+"/infinity_search.py")
        assert digest(cc_search) == SEARCH_SHA, "Proven407 Search source changed"
        checkpoint = archive.read(PREFIX+CC+"/checkpoint_runtime.py")
        addon = archive.read(PREFIX+CC+"/addon.xml")
        version = ET.fromstring(addon).get("version")
        parsed = ast.parse(checkpoint.decode())
        declared = [ast.literal_eval(n.value) for n in parsed.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "ADDON_VERSION" for t in n.targets)]
        assert version == "0.3.5.39" and declared == ["0.3.5.38"], "Reported version skew not reproduced in signed407"
        ui_pins = json.loads(archive.read(PREFIX+"script.infinity.uirepair/CONTROLLER-PREIMAGES.json"))
        wb_pins = json.loads(archive.read(PREFIX+"script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json"))
        assert len(ui_pins) == 25 and ui_pins == wb_pins, "Expected exact25 source ownership inventory"
        for name, wanted in ui_pins.items():
            assert digest(archive.read(PREFIX+CC+"/"+name)) == wanted, "Installed helper inventory disagrees: "+name
        inventory = {}
        for name in names:
            if not name.startswith(PREFIX) or name.endswith("/"):
                continue
            relative = name[len(PREFIX):]
            if relative.split("/")[0] not in OWNERS:
                continue
            path = Path(relative)
            assert not path.is_absolute() and ".." not in path.parts
            assert not ((archive.getinfo(name).external_attr >> 16) & 0o170000 == 0o120000)
            data = archive.read(name)
            inventory[relative] = digest(data)
            dest = output/"sources"/relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        report = {
            "baseline_apk_sha256": BASELINE_SHA,
            "baseline_source_commit": "0e8739d2d0e1be0ab8f127519b526556426fb160",
            "components_byte_verified": EXPECTED_COMPONENTS,
            "controller_pins": ui_pins,
            "component_source_hashes": inventory,
            "command_center_version": version,
            "checkpoint_declared_version": declared[0],
            "reported_version_skew_reproduced": True,
            "search_original_admission_preserved": True,
            "runtime_source_modified": False,
            "android17": "NOT RUN",
            "physical_fold": "NOT RUN",
            "release_ready": False,
        }
        (output/"BASELINE-SOURCE-OWNERSHIP.json").write_text(json.dumps(report, indent=2)+"\n")
        snippets = []
        for name in (CC+"/infinity_search.py", CC+"/checkpoint_runtime.py",
                     "script.infinity.uirepair/controller_access.py"):
            data = archive.read(PREFIX+name).decode()
            if name.endswith("infinity_search.py"):
                tree = ast.parse(data)
                wanted = {"_native_search_admission", "_leased_directory", "_bounded_results",
                          "_Cancellation", "_VisibleCancellation", "_search_results", "_open_search"}
                chunks = [ast.get_source_segment(data, n) for n in tree.body
                          if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in wanted]
                data = "\n\n".join(chunks)
            snippets.append("\n=== "+name+" ===\n"+data)
        for owner in OWNERS:
            snippets.append("\n=== "+owner+"/addon.xml ===\n"+archive.read(PREFIX+owner+"/addon.xml").decode())
        text = "\n".join(snippets)
        (output/"SIGNED407-READING.txt").write_text(text)
        print(json.dumps({key: value for key, value in report.items()
                          if key not in ("component_source_hashes", "controller_pins")}, indent=2))
        print("SIGNED407_SOURCE_READING_BEGIN")
        print(text)
        print("SIGNED407_SOURCE_READING_END")
    return report

if __name__ == "__main__":
    inspect(Path(sys.argv[1]), Path(sys.argv[2]))
