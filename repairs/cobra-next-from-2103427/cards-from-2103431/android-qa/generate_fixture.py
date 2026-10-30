"""Generate finite local-only Cards QA inventory and honest partial XMLTV data.

This script performs no network or Android operation and creates no video/image.
The existing synthetic-video generator supplies qa1.mp4 through qa4.mp4 before
--require-media is used. Explicit anchor epochs make all text bytes reproducible.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET

CHANNEL_COUNT = 20226
GROUP_COUNT = 12
EPG_CHANNEL_COUNT = 32
BASE_URL = "http://10.0.2.2:8765"
PLAYLIST_NAME = "cards-20226.m3u"
EPG_NAME = "cards-epg.xml"
VIDEO_NAMES = tuple("qa%d.mp4" % number for number in range(1, 5))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def xmltv_time(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y%m%d%H%M%S +0000")


def generate(out: Path, anchor_epoch: int | None = None,
             require_media: bool = False) -> dict:
    anchor = ((int(time.time()) // 60) * 60 - 300
              if anchor_epoch is None else anchor_epoch)
    if not isinstance(anchor, int) or anchor < 0:
        raise ValueError("A nonnegative integer anchor epoch is required")
    # Validate timestamp representability before writing output.
    xmltv_time(anchor + 7200)
    out.mkdir(parents=True, exist_ok=True)

    media = {}
    for name in VIDEO_NAMES:
        path = out / name
        present = path.is_file() and path.stat().st_size > 0
        if require_media and not present:
            raise ValueError("Existing nonempty synthetic media required: " + name)
        media[name] = ({"status": "PRESENT_HASHED", "bytes": path.stat().st_size,
                        "sha256": sha256_file(path)} if present else
                       {"status": "ABSENT_NOT_GENERATED_BY_THIS_SCRIPT",
                        "bytes": 0, "sha256": None})

    playlist = ['#EXTM3U x-tvg-url="' + BASE_URL + '/' + EPG_NAME + '"']
    for number in range(1, CHANNEL_COUNT + 1):
        channel_id = "cards-%05d" % number
        group = "Cards QA Group %02d" % ((number - 1) % GROUP_COUNT + 1)
        channel_name = "Cards QA %05d" % number
        playlist.append('#EXTINF:-1 tvg-id="%s" group-title="%s",%s' %
                        (channel_id, group, channel_name))
        # The distinct query preserves 20,226 stream URLs without producing
        # 20,226 video files. Python's normal HTTP server serves the base path.
        playlist.append(BASE_URL + "/qa%d.mp4?cards_channel=%05d" %
                        ((number - 1) % 4 + 1, number))
    playlist_bytes = ("\n".join(playlist) + "\n").encode("utf-8")

    television = ET.Element("tv", {"generator-info-name": "Cobra Cards local synthetic QA"})
    for number in range(1, EPG_CHANNEL_COUNT + 1):
        channel_id = "cards-%05d" % number
        channel = ET.SubElement(television, "channel", {"id": channel_id})
        ET.SubElement(channel, "display-name").text = "Cards QA %05d" % number
    # XMLTV orders all channel declarations before programme entries.
    for number in range(1, EPG_CHANNEL_COUNT + 1):
        channel_id = "cards-%05d" % number
        for slot, label in enumerate(("current", "next")):
            programme = ET.SubElement(television, "programme", {
                "channel": channel_id,
                "start": xmltv_time(anchor + slot * 3600),
                "stop": xmltv_time(anchor + (slot + 1) * 3600),
            })
            ET.SubElement(programme, "title", {"lang": "en"}).text = (
                "Synthetic %s %05d" % (label, number))
            ET.SubElement(programme, "desc", {"lang": "en"}).text = (
                "Local deterministic QA schedule; synthetic programme data, "
                "not a real broadcaster or live guide.")
            ET.SubElement(programme, "category", {"lang": "en"}).text = "Synthetic QA"
    ET.indent(television, space="  ")
    epg_bytes = ET.tostring(television, encoding="utf-8", xml_declaration=True) + b"\n"

    (out / PLAYLIST_NAME).write_bytes(playlist_bytes)
    (out / EPG_NAME).write_bytes(epg_bytes)
    manifest = {
        "schema": 1,
        "scope": "FINITE_LOCAL_CARDS_QA_FIXTURE_NO_PRODUCTION_ASSETS",
        "generator_source_sha256": sha256_file(Path(__file__)),
        "channel_count": CHANNEL_COUNT,
        "group_count": GROUP_COUNT,
        "unique_stream_url_count": CHANNEL_COUNT,
        "channel_name_pattern": "Cards QA %05d",
        "channel_id_pattern": "cards-%05d",
        "group_name_pattern": "Cards QA Group %02d",
        "playlist_url": BASE_URL + "/" + PLAYLIST_NAME,
        "epg_url": BASE_URL + "/" + EPG_NAME,
        "anchor_epoch": anchor,
        "anchor_utc": datetime.fromtimestamp(anchor, timezone.utc).isoformat(),
        "current_programme_window_epoch": [anchor, anchor + 3600],
        "next_programme_window_epoch": [anchor + 3600, anchor + 7200],
        "epg_channel_count": EPG_CHANNEL_COUNT,
        "epg_programme_count": EPG_CHANNEL_COUNT * 2,
        "channels_without_epg": CHANNEL_COUNT - EPG_CHANNEL_COUNT,
        "epg_limit": "Only first 32 channels have two synthetic programmes; all others have no schedule.",
        "clock_limit": "Current/next labels are valid only for the recorded anchor windows; do not claim current EPG after expiry.",
        "logos": "OMITTED; provider-logo latency and visual parity are not measured by this fixture.",
        "files": {
            PLAYLIST_NAME: {"bytes": len(playlist_bytes),
                            "sha256": hashlib.sha256(playlist_bytes).hexdigest()},
            EPG_NAME: {"bytes": len(epg_bytes),
                       "sha256": hashlib.sha256(epg_bytes).hexdigest()},
        },
        "media": media,
        "media_complete": all(row["status"] == "PRESENT_HASHED" for row in media.values()),
        "media_validation_limit": "Hashes identify supplied files; this generator does not validate playback or generate media.",
        "network_operations": "NONE",
        "Android_or_application_execution": "NONE",
        "shutdown": "NOT_RUN",
    }
    (out / "FIXTURE.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--anchor-epoch", type=int)
    parser.add_argument("--require-media", action="store_true")
    args = parser.parse_args()
    manifest = generate(args.out, args.anchor_epoch, args.require_media)
    print(json.dumps({"manifest": str(args.out / "FIXTURE.json"),
                      "channel_count": manifest["channel_count"],
                      "anchor_epoch": manifest["anchor_epoch"],
                      "media_complete": manifest["media_complete"]}, sort_keys=True))


if __name__ == "__main__":
    main()
