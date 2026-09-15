from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import cobra_provider_contract as c


class CobraProviderContractTests(unittest.TestCase):
    def test_server_normalization_preserves_port_and_provider_path(self):
        self.assertEqual(
            c.normalize_server("tv.example.test:8080/provider/"),
            "http://tv.example.test:8080/provider",
        )
        self.assertEqual(
            c.normalize_server("https://tv.example.test/player_api.php"),
            "https://tv.example.test",
        )

    def test_server_rejects_non_http(self):
        with self.assertRaises(ValueError):
            c.normalize_server("ftp://tv.example.test")

    def test_xtream_auth_url_encodes_credentials(self):
        url = c.xtream_api_url(
            "http://tv.example.test:8080",
            "user+name@example.test",
            "p&ss word",
            "get_live_streams",
        )
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/player_api.php")
        self.assertEqual(query["username"], ["user+name@example.test"])
        self.assertEqual(query["password"], ["p&ss word"])
        self.assertEqual(query["action"], ["get_live_streams"])

    def test_xtream_stream_path_and_extension(self):
        self.assertEqual(
            c.xtream_stream_url(
                "http://tv.example.test:8080",
                "user/name",
                "p@ss word",
                "9282",
                "m3u8",
            ),
            "http://tv.example.test:8080/live/user%2Fname/p%40ss%20word/9282.m3u8",
        )
        self.assertTrue(
            c.xtream_epg_url(
                "http://tv.example.test:8080", "user", "pass"
            ).startswith("http://tv.example.test:8080/xmltv.php?")
        )

    def test_invalid_container_extension_falls_back_to_ts(self):
        self.assertEqual(c.sanitize_extension("../../bad"), "ts")
        self.assertEqual(c.sanitize_extension("M3U8"), "m3u8")

    def test_m3u_parses_metadata_relative_urls_and_headers(self):
        playlist = """#EXTM3U
#EXTINF:-1 tvg-id="news.us" tvg-name="News" group-title="News",News HD
#EXTVLCOPT:http-user-agent=ProviderBox/7
#EXTVLCOPT:http-referrer=https://portal.example/
streams/news.m3u8
#EXTINF:-1 tvg-id="sport.one" group-title="Sports",Sports One
http://cdn.example/live.ts|User-Agent=Box%2F1&Referer=https%3A%2F%2Fportal.example%2F
"""
        channels = c.parse_m3u("https://lists.example/provider/list.m3u", playlist)
        self.assertEqual(len(channels), 2)
        self.assertEqual(channels[0].name, "News HD")
        self.assertEqual(channels[0].group, "News")
        self.assertEqual(channels[0].epg_id, "news.us")
        self.assertEqual(
            channels[0].url, "https://lists.example/provider/streams/news.m3u8"
        )
        self.assertEqual(channels[0].headers["User-Agent"], "ProviderBox/7")
        self.assertEqual(channels[0].headers["Referer"], "https://portal.example/")
        self.assertEqual(channels[1].headers["User-Agent"], "Box/1")
        self.assertEqual(channels[1].headers["Referer"], "https://portal.example/")

    def test_m3u_drops_non_playable_urls(self):
        playlist = """#EXTM3U
#EXTINF:-1 group-title="Other",Bad
javascript:alert(1)
#EXTINF:-1 group-title="Other",Good
https://cdn.example/live.m3u8
"""
        channels = c.parse_m3u("https://lists.example/list.m3u", playlist)
        self.assertEqual([x.name for x in channels], ["Good"])

    def test_provider_urls_are_redacted_for_diagnostics(self):
        value = c.redact_provider_url(
            "http://tv.example/live/alice/secret/17.ts?username=alice&password=secret"
        )
        self.assertNotIn("alice", value)
        self.assertNotIn("secret", value)
        self.assertIn("%2A%2A%2A", value)


class CobraSourceTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.java = (
            ROOT / "patches/infinity-cobra/InfinityLiveActivity.java.in"
        ).read_text(encoding="utf-8")
        cls.patcher = (
            ROOT / "scripts/infinity_1_0_9_cobra_legit.py"
        ).read_text(encoding="utf-8")
        cls.theme = json.loads(
            (
                ROOT
                / "addons/script.infinity.cobra.theme/resources/cobra-theme.json"
            ).read_text(encoding="utf-8")
        )

    def test_live_runtime_owns_real_provider_paths(self):
        for needle in (
            "player_api.php?username=",
            "get_live_categories",
            "get_live_streams",
            "/xmltv.php?username=",
            "direct_source",
            "#EXTVLCOPT:",
            "#EXTHTTP:",
            "parseM3u",
        ):
            self.assertIn(needle, self.java)

    def test_playback_is_media3_exoplayer(self):
        for needle in (
            "new ExoPlayer.Builder",
            "DefaultHttpDataSource.Factory",
            "setEnableDecoderFallback(true)",
            "setVideoTextureView",
            "openMultiView",
            "setMultiAudio",
        ):
            self.assertIn(needle, self.java)
        for forbidden in (
            "android.media.MediaPlayer",
            "new MediaPlayer(",
            "libmpv",
            "com.cobratv",
        ):
            self.assertNotIn(forbidden, self.java)

    def test_errors_are_actionable(self):
        self.assertIn(
            "Server not found. Check the address, Wi-Fi, VPN, or DNS.",
            self.java,
        )
        self.assertIn("Stream could not play", self.java)
        self.assertIn("provider returned no Live TV channels", self.java)

    def test_cobra_surface_and_fast_theme_contract_are_present(self):
        for needle in (
            "COBRA • LIVE TV",
            "GUIDE",
            "FAVORITES",
            "RECENTS",
            "MULTI-VIEW",
            "SOURCES",
            "SETTINGS",
            ".kodi/addons/script.infinity.cobra.theme/resources/cobra-theme.json",
        ):
            self.assertIn(needle, self.java)
        self.assertIn(
            'addons/script.infinity.cobra.theme/resources/cobra-theme.json',
            self.patcher,
        )
        self.assertEqual(self.theme["schema"], 1)
        self.assertRegex(self.theme["accent"], r"^#[0-9A-Fa-f]{6}$")
        self.assertGreaterEqual(self.theme["row_height"], 48)

    def test_build_corrects_xmltv_current_next_accumulator(self):
        self.assertIn(
            '"ProgramPair pair = mGuide.get(channel);",',
            self.patcher,
        )
        self.assertIn(
            '"ProgramPair pair = guide.get(channel);",',
            self.patcher,
        )


if __name__ == "__main__":
    unittest.main()
