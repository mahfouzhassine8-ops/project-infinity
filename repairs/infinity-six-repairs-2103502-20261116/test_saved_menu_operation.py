"""One exact502 host reproduction; no provider, profile or application access.

The snapshot fixture stands for an already verified capability, not a claim of
compatibility for an installed producer. It has no media IDs or provider URL.
The real eligibility function and its two real callers remain unmodified.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import zipfile

HERE = Path(__file__).resolve().parent
PREFIX = "assets/addons/script.infinity.commandcenter/"
SELECTED = json.loads((HERE / "test-selection-data.json").read_text())
OBSERVATIONS = {}


def function(raw, name, globals_):
    tree = ast.parse(raw.decode("utf-8"))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise AssertionError("Expected exactly one source function: " + name)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), name, "exec"), globals_)
    return globals_[name]


class SavedMenuOperation(unittest.TestCase):
    def test_verified_navigation_capability_remains_available_in_saved_popup(self):
        inventory = types.ModuleType("provider_inventory")
        inventory.__dict__.update(deepcopy=deepcopy)
        tree = ast.parse(SOURCES["provider_inventory.py"].decode("utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in ("MEDIA", "API_VERSION"):
                    inventory.__dict__[node.targets[0].id] = ast.literal_eval(node.value)
        snapshots = []

        def snapshot(**kwargs):
            snapshots.append(kwargs)
            # Opaque inventory fixture: no actual add-on or media identity.
            return {"entries": [{"enabled": True, "name": "Host capability control", "icon": "",
                "operations": {("movie", "title_navigation"): {"host_capability_control": True}}}]}

        inventory.snapshot = snapshot
        function(SOURCES["provider_inventory.py"], "eligible", inventory.__dict__)
        available = function(SOURCES["saved_navigation.py"], "available", {})
        popup_available = function(SOURCES["plugin.py"], "_menu_play_available", {})
        with patch.dict(sys.modules, {"provider_inventory": inventory}):
            ready, unavailable = available("movie")
            self.assertEqual(len(ready), 1, "Real recovery caller must recognize the host capability control")
            self.assertEqual(unavailable, [])
            self.assertEqual(len(snapshots), 1)
            result = popup_available({"media": "movie"}, {}, "continue",
                target="plugin://script.infinity.commandcenter/?action=saved-recovery&")
        OBSERVATIONS.update(recovery_available=len(ready), popup_available=result,
                            inventory_snapshot_calls=len(snapshots),
                            popup_requested_operation="navigation",
                            recovery_requested_operation="title_navigation")
        self.assertTrue(result, "Saved recovery has a verified title_navigation capability, but the popup rejects it")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    SOURCES = {}
    with zipfile.ZipFile(args.apk) as archive:
        for leaf, expected in SELECTED["baseline_member_sha256"].items():
            raw = archive.read(PREFIX + leaf)
            digest = hashlib.sha256(raw).hexdigest()
            if digest != expected:
                raise AssertionError("Unexpected baseline member: " + leaf)
            SOURCES[leaf] = raw
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "SavedMenuOperation.test_verified_navigation_capability_remains_available_in_saved_popup", sys.modules[__name__])
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    output = stream.getvalue()
    print(output, end="")
    expected_failure = (result.testsRun == 1 and len(result.failures) == 1 and not result.errors and
                        OBSERVATIONS.get("recovery_available") == 1 and
                        OBSERVATIONS.get("popup_available") is False and
                        OBSERVATIONS.get("inventory_snapshot_calls") == 1)
    receipt = dict(status="BASELINE_FAIL_EXPECTED" if expected_failure else "UNEXPECTED_RESULT",
                   selected_test=SELECTED["selected_test"], tests_run=result.testsRun,
                   failures=len(result.failures), errors=len(result.errors),
                   apk_member_binding="Exact source member SHA-256 verified directly from retained signed502 APK",
                   source_hashes=SELECTED["baseline_member_sha256"],
                   observations=OBSERVATIONS, output=output,
                   production_changed=False, owner_store_accessed=False, provider_executed=False,
                   candidate_tested=False, runtime_incident_attributed=False)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    raise SystemExit(1 if expected_failure else 2)
