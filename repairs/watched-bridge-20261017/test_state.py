import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / "addon"))
import bridge_state as state


def entry(kind="movie", names=None, scope=None, season=1, episode=2):
    value = dict(schema=1, kind=kind, scope=scope or kind, ids=names or {"tmdb": "123", "imdb": "tt00123"})
    result = dict(media="movie" if kind == "movie" else "tv", identity=value)
    if kind == "episode":
        value.update(season=season, episode=episode)
        result.update(season=season, episode=episode)
    return result


class SnapshotTests(unittest.TestCase):
    def test_cross_provider_movie_aliases_and_namespace_negatives(self):
        rows = state.records(dict(schema=2, watched={"a" * 64: entry()}))
        self.assertEqual(state.lookup(rows, state.identity(entry(names={"imdb": "tt00123"}))), "true")
        self.assertEqual(state.lookup(rows, state.identity(entry(names={"tvdb": "123"}))), "")
        self.assertEqual(state.lookup(rows, state.identity(entry(names={"tmdb": "123", "imdb": "tt00999"}))), "")

    def test_movie_episode_show_scope_and_absolute_numbers_stay_separate(self):
        rows = state.records(dict(schema=2, watched={"a" * 64: entry("episode")}))
        for value in (entry(), entry("episode", episode=102), entry("episode", scope="show_episode")):
            self.assertEqual(state.lookup(rows, state.identity(value)), "")
        self.assertEqual(state.lookup(rows, state.identity(entry("episode"))), "true")

    def test_special_zero_valid_missing_or_boolean_coordinate_invalid(self):
        self.assertIsNotNone(state.identity(entry("episode", season=0, episode=0)))
        for value in (-1, None, True, "2"):
            self.assertIsNone(state.identity(entry("episode", episode=value)))

    def test_title_only_unknown_anime_namespace_and_legacy_untyped_do_not_match(self):
        self.assertIsNone(state.identity({"media": "movie", "title": "Same title"}))
        self.assertIsNone(state.identity(entry(names={"anilist": "123"})))
        self.assertIsNone(state.identity({"media": "tv", "tmdb": "123", "season": 1, "episode": 2}))

    def test_partial_watchlist_collection_never_become_watched(self):
        data = dict(schema=2, items={"a" * 64: entry()}, watchlist={"b" * 64: entry()}, collection={"c" * 64: entry()})
        self.assertEqual(state.records(data), [])

    def test_explicit_unwatched_and_subsequent_controller_completion(self):
        data = dict(schema=2, infinity_watched_overrides={"a" * 64: entry()})
        self.assertEqual(state.lookup(state.records(data), state.identity(entry())), "false")
        data["watched"] = {"b" * 64: entry()}
        self.assertEqual(state.lookup(state.records(data), state.identity(entry())), "true")

    def test_contradictory_aliases_and_mixed_states_are_unknown(self):
        data = dict(schema=2, watched={"a" * 64: entry(), "b" * 64: entry(names={"tmdb": "123", "imdb": "tt00999"})})
        self.assertEqual(state.lookup(state.records(data), state.identity(entry(names={"tmdb": "123"}))), "")
        row = dict(identity=state.identity(entry()), watched=True)
        self.assertEqual(state.lookup([row, dict(row, watched=False)], row["identity"]), "")

    def test_snapshot_has_no_titles_paths_or_provider_credentials(self):
        value = entry(); value.update(title="Private title", source="plugin://provider/?token=private")
        raw = state.snapshot(dict(schema=2, watched={"a" * 64: value}), "/profile/")
        self.assertNotIn("Private", raw); self.assertNotIn("token", raw)
        self.assertEqual(json.loads(raw)["profile"], "/profile")

    def test_progress_only_revisions_do_not_republish_watched_index(self):
        data = dict(schema=2, revision=1, watched={"a" * 64: entry()})
        original = state.snapshot(data, "/profile")
        data.update(revision=999, items={"b" * 64: entry()}, foreign={"retained": True})
        self.assertEqual(state.snapshot(data, "/profile"), original)

    def test_schema_and_shape_errors_are_withheld_without_repair(self):
        for value in ({"schema": 3}, {"schema": True}, {"schema": 2, "watched": []},
                      {"schema": 2, "infinity_watched_overrides": "foreign-data"}):
            before = copy.deepcopy(value)
            with self.assertRaises(ValueError): state.snapshot(value, "/profile")
            self.assertEqual(value, before)

    def test_bounded_history_and_invalid_persistent_keys(self):
        self.assertEqual(state.records(dict(schema=1, watched={"invalid": entry()})), [])
        with self.assertRaises(ValueError):
            state.records(dict(schema=2, watched={str(i): entry() for i in range(601)}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
