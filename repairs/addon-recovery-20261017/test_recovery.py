import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("recovery", Path(__file__).parent / "addon/recovery.py")
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class Kodi:
    def __init__(self):
        self.addons = {recovery.OTAKU: dict(addonid=recovery.OTAKU, name="Otaku", version="fixture", enabled=False),
                       "plugin.video.second": dict(addonid="plugin.video.second", name="Second", version="1", enabled=False),
                       "script.infinity.rails": dict(addonid="script.infinity.rails", name="Rails", version="0.2.6", enabled=True)}
        self.calls = []
        self.refuse = self.ignore = False

    def execute(self, raw):
        request = json.loads(raw)
        self.calls.append(request)
        if request["method"] == "Addons.GetAddons":
            return json.dumps({"result": {"addons": list(self.addons.values())}})
        if request["method"] == "Addons.SetAddonEnabled":
            if self.refuse:
                return json.dumps({"error": {"code": -1}})
            if not self.ignore:
                self.addons[request["params"]["addonid"]]["enabled"] = True
            return json.dumps({"result": "OK"})
        raise AssertionError(request)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.kodi = Kodi()

    def test_otaku_enable_uses_native_api_and_readback(self):
        result = recovery.enable(self.kodi.execute, recovery.OTAKU)
        self.assertEqual(result["state"], "enabled")
        self.assertEqual(result["previous_version"], "fixture")
        self.assertEqual([x["method"] for x in self.kodi.calls], ["Addons.GetAddons", "Addons.SetAddonEnabled", "Addons.GetAddons"])
        self.assertEqual(self.kodi.calls[1]["params"], {"addonid": recovery.OTAKU, "enabled": True})
        self.assertFalse(self.kodi.addons["plugin.video.second"]["enabled"])

    def test_second_addon_is_independent(self):
        recovery.enable(self.kodi.execute, "plugin.video.second")
        self.assertFalse(self.kodi.addons[recovery.OTAKU]["enabled"])

    def test_already_enabled_is_not_modified(self):
        result = recovery.enable(self.kodi.execute, "script.infinity.rails")
        self.assertEqual(result["state"], "already-enabled")
        self.assertEqual(len(self.kodi.calls), 1)

    def test_missing_is_not_treated_as_disabled(self):
        result = recovery.enable(self.kodi.execute, "plugin.video.missing")
        self.assertEqual(result["state"], "not-installed")
        self.assertEqual(len(self.kodi.calls), 1)

    def test_unknown_state_never_enables(self):
        self.kodi.addons[recovery.OTAKU]["enabled"] = "false"
        with self.assertRaises(recovery.RecoveryError):
            recovery.enable(self.kodi.execute, recovery.OTAKU)
        self.assertEqual(len(self.kodi.calls), 1)

    def test_native_refusal_is_reported(self):
        self.kodi.refuse = True
        with self.assertRaises(recovery.RecoveryError):
            recovery.enable(self.kodi.execute, recovery.OTAKU)

    def test_acknowledgement_without_state_change_is_not_success(self):
        self.kodi.ignore = True
        with self.assertRaises(recovery.RecoveryError):
            recovery.enable(self.kodi.execute, recovery.OTAKU)

    def test_malformed_inventory_is_not_empty_success(self):
        for value in ({"error": {}}, {"result": {}}, {"result": None}):
            with self.assertRaises(recovery.RecoveryError):
                recovery.disabled(lambda raw: json.dumps(value))

    def test_invalid_identity_never_reaches_kodi(self):
        with self.assertRaises(recovery.RecoveryError):
            recovery.enable(self.kodi.execute, "bad),ClearData(")
        self.assertFalse(self.kodi.calls)

    def test_inventory_distinguishes_enabled_and_disabled(self):
        rows = recovery.disabled(self.kodi.execute)
        self.assertEqual({row["addonid"] for row in rows}, {recovery.OTAKU, "plugin.video.second"})


if __name__ == "__main__":
    unittest.main()
