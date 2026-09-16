from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import infinity_1_0_9_cobra_full as full
import infinity_1_0_9_cobra_full_runner as runner


class CobraFullTransformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = (ROOT / "patches/infinity-cobra/InfinityLiveActivity.java.in").read_text(encoding="utf-8")
        cls.java = runner.transform_for_fast_test(base)
        cls.feature = (ROOT / "patches/infinity-cobra-v2/InfinityCobraFeatureRuntime.java.in").read_text(encoding="utf-8")
        cls.recording = (ROOT / "patches/infinity-cobra-v2/InfinityCobraRecordingService.java.in").read_text(encoding="utf-8")
        cls.theme = json.loads((ROOT / "addons/script.infinity.cobra.theme/resources/cobra-theme.json").read_text(encoding="utf-8"))

    def test_identity(self):
        self.assertEqual(full.VERSION_CODE, 2103134)
        self.assertEqual(full.RELEASE, "1.0.9-Cobra-Full-Feature-Candidate-2")

    def test_multiview_is_two_to_four_with_one_audio_owner(self):
        for token in ("2 screens", "3 screens", "4 screens", "openMultiView(List<Channel>", "setMultiAudio"):
            self.assertIn(token, self.java)
        self.assertIn("mMultiPlayers[i].setVolume(i == index ? 1f : 0f)", self.java)

    def test_dvr_and_guide_contract(self):
        for token in ("showRecordings()", "scheduleRecording", "addReminder", "playCatchup", "showGuideOverlay()", "cobra_custom_epg:"):
            self.assertIn(token, self.java)
        for token in ("startForegroundService", "recordHls", "recordDirect", "hasRecordingSpace"):
            self.assertIn(token, self.feature + self.recording)

    def test_vod_resume_and_auto_next(self):
        for token in ("get_vod_streams", "get_series_info", "continue_items", "playSavedVod", "playNextEpisode()"):
            self.assertIn(token, self.java)
        method = self.java.split("private void playVodUrl", 1)[1].split("private void saveVodProgress", 1)[0]
        self.assertLess(method.index("closePlayer();"), method.index("mPlayingVodKey ="))

    def test_all_enabled_provider_guide_callbacks_are_kept(self):
        guide = self.java.split("private void loadGuideAsync", 1)[1].split("private Map<String, ProgramPair> parseXmlTv", 1)[0]
        self.assertNotIn("if (source != mActiveSource) return;", guide)
        self.assertIn("if (!mFeatures.sourceEnabled(source.id)) return;", guide)

    def test_profiles_tracks_cast_local_files_and_discover(self):
        for token in (
            "showProfiles()", "profileKey(FAVORITES)", "TrackSelectionOverride",
            "ACTION_CAST_SETTINGS", "ACTION_OPEN_DOCUMENT", "showDiscover()",
            "CONTINUE WATCHING", "MY LIST", "MY FILES",
        ):
            self.assertIn(token, self.java)

    def test_health_snapshot_is_redacted(self):
        for token in ("cobra-health.json", "redact(", "/live/***/***/", "/movie/***/***/", "/series/***/***/"):
            self.assertIn(token, self.feature)
        self.assertIn("mFeatures.writeHealth", self.java)

    def test_theme_is_schema_two_and_touch_first(self):
        self.assertEqual(self.theme["schema"], 2)
        self.assertGreaterEqual(self.theme["touch_target"], 48)
        self.assertGreaterEqual(self.theme["rail_item_height"], 42)
        self.assertGreaterEqual(self.theme["motion_ms"], 80)

    def test_proprietary_cobra_and_legacy_players_are_absent(self):
        all_source = self.java + self.feature + self.recording
        for forbidden in ("CobraTV_", "com.cobratv", "libmpv", "android.media.MediaPlayer", "new MediaPlayer("):
            self.assertNotIn(forbidden, all_source)


if __name__ == "__main__":
    unittest.main()
