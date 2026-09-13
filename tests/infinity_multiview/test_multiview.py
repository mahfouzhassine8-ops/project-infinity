import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "addons/script.infinity.live"))

from resources.lib.multiview import build_request, channel_payload, launch_command, write_request


class Channel:
    def __init__(self, name, url, group="News", logo="", properties=None):
        self.name = name
        self.url = url
        self.group = group
        self.logo = logo
        self.properties = properties or {}


class InfinityMultiViewTests(unittest.TestCase):
    def test_two_channel_request_and_headers(self):
        left = Channel(
            "News One",
            "https://tv.example/live/1.m3u8|User-Agent=Infinity%20Test&Referer=https%3A%2F%2Fguide.example%2F",
        )
        right = Channel(
            "Sports Two",
            "https://tv.example/live/2.ts",
            group="Sports",
            properties={"vlc.http-user-agent": "Provider Agent", "http-origin": "https://tv.example"},
        )
        request = build_request(left, right)
        self.assertEqual(request["schema"], 1)
        self.assertEqual(request["mode"], "split2")
        self.assertEqual(len(request["channels"]), 2)
        self.assertEqual(request["channels"][0]["url"], "https://tv.example/live/1.m3u8")
        self.assertEqual(request["channels"][0]["headers"]["User-Agent"], "Infinity Test")
        self.assertEqual(request["channels"][0]["headers"]["Referer"], "https://guide.example/")
        self.assertEqual(request["channels"][1]["headers"]["User-Agent"], "Provider Agent")
        self.assertEqual(request["channels"][1]["headers"]["Origin"], "https://tv.example")

    def test_duplicate_feed_rejected(self):
        one = Channel("One", "https://example.test/live")
        two = Channel("Two", "https://example.test/live")
        with self.assertRaises(ValueError):
            build_request(one, two)

    def test_launcher_contains_only_request_path(self):
        command = launch_command("/storage/emulated/0/Android/data/com.projectinfinity.kodi/files/request.json")
        self.assertIn("StartAndroidActivity(com.projectinfinity.kodi", command)
        self.assertIn("infinity-multiview://open?path=", command)
        self.assertIn("com.projectinfinity.kodi.Main", command)
        self.assertNotIn("username", command.lower())
        self.assertNotIn("password", command.lower())
        self.assertNotIn("m3u8", command.lower())

    def test_request_is_atomic_and_private_where_supported(self):
        request = build_request(
            Channel("One", "https://example.test/1.m3u8"),
            Channel("Two", "https://example.test/2.m3u8"),
        )
        with tempfile.TemporaryDirectory() as td:
            path = write_request(td, request)
            self.assertTrue(os.path.isfile(path))
            with open(path, "r", encoding="utf-8") as handle:
                stored = json.load(handle)
            self.assertEqual(stored["channels"][0]["name"], "One")
            mode = stat.S_IMODE(os.stat(path).st_mode)
            self.assertEqual(mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
