"""Run new actions through the actual unchanged CC participant and controller."""
import argparse
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--runtime", required=True)
args = parser.parse_args()
sys.path.insert(0, str(HERE / "addon"))
import controller
from bridge_state import OVERRIDES, records, identity, lookup
import provider_contracts as contracts
sys.argv = [sys.argv[0], "--runtime", args.runtime]
fixtures = runpy.run_path(str(HERE.parent / "android-checkpoint-shutdown/runtime-tests/test_runtime_checkpoint.py"), run_name="fixtures")
hub, common = fixtures["hub"], fixtures["common"]
cc_context = importlib.import_module("context")
spec = importlib.util.spec_from_file_location("bridge_context", HERE / "addon/context.py")
bridge_context = importlib.util.module_from_spec(spec); spec.loader.exec_module(bridge_context)
modules = dict(common=common, resume_hub=hub, context=cc_context)


class Selected:
    def __init__(self, folder=False, path="plugin://plugin.video.umbrella/?action=play&id=123", kind="movie"):
        self.folder, self.path, self.kind = folder, path, kind
    def isFolder(self): return self.folder
    def getPath(self): return self.path
    def getVideoInfoTag(self): return self
    def getMediaType(self): return self.kind
    def getUniqueID(self, name): return "123" if name == "tmdb" else ""
    def getSeason(self): return 1
    def getEpisode(self): return 2
    def getTitle(self): return "Unplayed fixture"
    def getTVShowTitle(self): return "Fixture show"
    def getLabel(self): return "Unplayed fixture"
    def getDbId(self): return -1
    def getArt(self, name): return ""


class ActionTests(fixtures["RuntimeTests"]):
    def test_episode_scope_attestation_preserves_old_key_and_data(self):
        selected = Selected(kind="episode")
        proof = contracts.CATALOG["plugin.video.umbrella"]["proof"]
        entry = bridge_context.selected(modules, selected, verify_provider=lambda name: proof)
        self.assertIsNotNone(entry)
        key = entry["key"]
        common.atomic_json(self.profile / hub.CONTINUE_FILE, dict(schema=2, foreign="retained", items={key: dict(entry, position=30, duration=100)}))
        self.assertTrue(controller.apply(modules, self.profile, entry, "mark-watched"))
        data = hub.load(self.profile)
        self.assertEqual(data["foreign"], "retained"); self.assertIn(key, data["watched"])
        self.assertEqual(data["watched"][key]["identity"]["scope"], "episode")
        query = dict(identity(entry), scope="show_episode")
        self.assertEqual(lookup(records(data), query), "true")
        self.assertEqual(lookup(records(data), identity(entry)), "")
        self.assertTrue(controller.apply(modules, self.profile, entry, "mark-unwatched"))
        self.assertEqual(lookup(records(hub.load(self.profile)), query), "false")

    def test_unknown_episode_producer_cannot_write_or_rebind_existing_route(self):
        self.assertIsNone(bridge_context.selected(modules, Selected(kind="episode"), verify_provider=lambda name: None))
        raw = cc_context.selected_entry(Selected(kind="episode"))
        self.assertFalse(controller.apply(modules, self.profile, raw, "mark-watched"))
        proof = contracts.CATALOG["plugin.video.umbrella"]["proof"]
        entry = bridge_context.selected(modules, Selected(kind="episode"), verify_provider=lambda name: proof)
        old = dict(entry, source="plugin://plugin.video.umbrella/?different=unverified-history")
        common.atomic_json(self.profile / hub.CONTINUE_FILE, dict(schema=2, watched={entry["key"]: old}))
        original = (self.profile / hub.CONTINUE_FILE).read_bytes()
        self.assertFalse(controller.apply(modules, self.profile, entry, "mark-unwatched"))
        self.assertEqual((self.profile / hub.CONTINUE_FILE).read_bytes(), original)

    def test_verified_episode_actions_share_state_across_providers_without_route_rewrite(self):
        first = bridge_context.selected(modules, Selected(kind="episode"), verify_provider=lambda name: contracts.CATALOG[name]["proof"])
        second = bridge_context.selected(modules, Selected(kind="episode", path="plugin://plugin.video.pov/?mode=play_media&item=123"), verify_provider=lambda name: contracts.CATALOG[name]["proof"])
        self.assertTrue(controller.apply(modules, self.profile, first, "mark-watched"))
        original = hub.load(self.profile)
        proof = copy.deepcopy(original[contracts.PROOFS])
        self.assertTrue(controller.apply(modules, self.profile, second, "mark-unwatched"))
        data = hub.load(self.profile)
        self.assertEqual(data[contracts.PROOFS], proof)
        self.assertEqual(data[OVERRIDES][first["key"]]["source"], first["source"])
        query = dict(identity(second), scope="show_episode")
        self.assertEqual(lookup(records(data), query), "false")
        self.assertTrue(controller.apply(modules, self.profile, second, "mark-watched"))
        self.assertEqual(lookup(records(hub.load(self.profile)), query), "true")

    def selected(self):
        return cc_context.selected_entry(Selected())

    def test_guard_accepts_complete_reviewed_source_and_refuses_unknown_edit(self):
        self.assertEqual(controller.verify(args.runtime), Path(args.runtime).resolve())
        import shutil
        root = self.profile / "code-copy"; shutil.copytree(args.runtime, root)
        (root / "common.py").write_text("# unreviewed newer code\n")
        with self.assertRaises(controller.UnsupportedController): controller.verify(root)

    def test_never_played_collection_and_watchlist_without_progress_or_badge(self):
        entry = self.selected()
        for action in ("toggle-collection", "toggle-watchlist"):
            self.assertTrue(controller.apply(modules, self.profile, entry, action))
        data = hub.load(self.profile)
        self.assertIn(entry["key"], data["collection"]); self.assertIn(entry["key"], data["watchlist"])
        self.assertEqual(data["items"], {}); self.assertEqual(data["watched"], {})
        self.assertEqual(records(data), [])

    def test_manual_completion_retains_lists_foreign_keys_and_removes_continue(self):
        entry = self.selected()
        data = dict(schema=1, foreign={"keep": [1, 2, 3]}, items={entry["key"]: dict(entry, position=50, duration=100)},
                    watchlist={entry["key"]: entry}, collection={entry["key"]: entry})
        common.atomic_json(self.profile / hub.CONTINUE_FILE, data)
        self.assertTrue(controller.apply(modules, self.profile, entry, "mark-watched"))
        data = hub.load(self.profile)
        self.assertEqual(data["foreign"], {"keep": [1, 2, 3]})
        self.assertEqual(data["items"], {})
        self.assertIn(entry["key"], data["watched"]); self.assertIn(entry["key"], data["watchlist"])
        self.assertIn(entry["key"], data["collection"])

    def test_unwatched_never_creates_continue_and_overrides_native_presentation(self):
        entry = self.selected()
        self.assertTrue(controller.apply(modules, self.profile, entry, "mark-unwatched"))
        data = hub.load(self.profile)
        self.assertEqual(data["items"], {}); self.assertEqual(data["watched"], {})
        self.assertEqual(lookup(records(data), identity(entry)), "false")
        self.assertTrue(controller.apply(modules, self.profile, entry, "mark-watched"))
        self.assertEqual(lookup(records(hub.load(self.profile)), identity(entry)), "true")

    def test_real_existing_progress_survives_unwatched_action(self):
        entry = self.selected()
        common.atomic_json(self.profile / hub.CONTINUE_FILE, dict(schema=2, items={entry["key"]: dict(entry, position=20, duration=100)}))
        controller.apply(modules, self.profile, entry, "mark-unwatched")
        self.assertEqual(hub.load(self.profile)["items"][entry["key"]]["position"], 20)

    def test_folder_ingress_is_scoped_and_navigation_rows_refused(self):
        self.assertIsNotNone(bridge_context.selected(modules, Selected(folder=True)))
        self.assertIsNone(bridge_context.selected(modules, Selected(folder=True, path="plugin://unreviewed.provider/")))
        self.assertIsNone(bridge_context.selected(modules, Selected(folder=True, kind="tvshow")))

    def test_checkpoint_fence_refuses_new_compatibility_writer(self):
        entry = self.selected(); self.prepare()
        with self.assertRaises(fixtures["runtime"].AdmissionClosed):
            controller.apply(modules, self.profile, entry, "toggle-collection")
        self.assertNotIn(entry["key"], hub.load(self.profile)["collection"])

    def test_invalid_or_newer_progress_file_is_not_replaced(self):
        file = self.profile / hub.CONTINUE_FILE
        for raw in ("{broken-json", '{"schema":3,"future":{"keep":true}}'):
            file.write_text(raw)
            with self.assertRaises(controller.UnsupportedController):
                controller.apply(modules, self.profile, self.selected(), "mark-watched")
            self.assertEqual(file.read_text(), raw)


if __name__ == "__main__":
    unittest.main(verbosity=2, argv=[sys.argv[0]])
