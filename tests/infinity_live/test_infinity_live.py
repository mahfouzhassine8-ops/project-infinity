import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "addons", "script.infinity.live"))

from resources.lib.m3u import parse_m3u
from resources.lib.providers import build_xtream_urls, redacted_source
from resources.lib.xmltv import parse_xmltv, parse_xmltv_time


class InfinityLiveTests(unittest.TestCase):
    def test_m3u_groups_epg_and_properties(self):
        data = b'''#EXTM3U x-tvg-url="https://example.test/guide.xml"\n#EXTINF:-1 tvg-id="news.1" tvg-name="News One" tvg-logo="https://img/logo.png" group-title="News" tvg-chno="101",News One HD\n#KODIPROP:inputstream=inputstream.ffmpegdirect\n#EXTVLCOPT:http-user-agent=Infinity Test\nhttps://example.test/live/101.ts\n#EXTINF:-1 group-title="Sports",Sports Live\nhttps://example.test/live/201.m3u8\n'''
        playlist = parse_m3u(data)
        self.assertEqual(playlist.guide_url, "https://example.test/guide.xml")
        self.assertEqual(len(playlist.channels), 2)
        first = playlist.channels[0]
        self.assertEqual(first.group, "News")
        self.assertEqual(first.tvg_id, "news.1")
        self.assertEqual(first.number, "101")
        self.assertEqual(first.properties["inputstream"], "inputstream.ffmpegdirect")
        self.assertEqual(first.properties["vlc.http-user-agent"], "Infinity Test")

    def test_relative_playlist_and_guide_resolution(self):
        data = b'''#EXTM3U x-tvg-url="guide.xml"\n#EXTINF:-1 group-title="Local",Local\nstreams/local.m3u8\n'''
        playlist = parse_m3u(data, "https://example.test/root/")
        self.assertEqual(playlist.guide_url, "https://example.test/root/guide.xml")
        self.assertEqual(playlist.channels[0].url, "https://example.test/root/streams/local.m3u8")
        special = parse_m3u(data, "special://profile/iptv/")
        self.assertEqual(special.guide_url, "special://profile/iptv/guide.xml")
        self.assertEqual(special.channels[0].url, "special://profile/iptv/streams/local.m3u8")

    def test_xmltv_timezone_and_current_window(self):
        xml = b'''<?xml version="1.0"?><tv>
<channel id="news.1"><display-name>News One HD</display-name></channel>
<programme channel="news.1" start="20260913150000 -0400" stop="20260913160000 -0400"><title>Live News</title></programme>
<programme channel="news.1" start="20260913160000 -0400" stop="20260913170000 -0400"><title>Next News</title></programme>
</tv>'''
        now = datetime(2026, 9, 13, 19, 30, tzinfo=timezone.utc)
        guide = parse_xmltv(xml, now=now, horizon_hours=4)
        self.assertEqual(guide.display_names["news.1"], ["News One HD"])
        self.assertEqual([p.title for p in guide.programmes["news.1"]], ["Live News", "Next News"])
        self.assertEqual(parse_xmltv_time("20260913150000 -0400"), datetime(2026, 9, 13, 19, 0, tzinfo=timezone.utc))

    def test_xtream_url_encoding_and_redaction(self):
        m3u, epg = build_xtream_urls("https://tv.example.test/", "user+name", "p&a ss", "m3u8")
        self.assertIn("type=m3u_plus", m3u)
        self.assertIn("output=m3u8", m3u)
        self.assertIn("user%2Bname", m3u)
        self.assertIn("p%26a+ss", m3u)
        self.assertIn("xmltv.php", epg)
        safe = redacted_source({"type": "xtream", "username": "u", "password": "secret"})
        self.assertEqual(safe["password"], "***")
        self.assertNotIn("secret", repr(safe))


if __name__ == "__main__":
    unittest.main()
