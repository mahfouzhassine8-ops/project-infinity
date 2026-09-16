import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .m3u import parse_m3u
from .models import Catalog, ChannelGuide
from .network import cache_location
from .providers import resolve_source
from .xmltv import parse_xmltv


def _norm(value: str):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _base_url(location: str):
    location = (location or "").strip()
    if not location:
        return ""
    if location.startswith("special://"):
        return location.rsplit("/", 1)[0] + "/"
    try:
        parts = urlsplit(location)
        if parts.scheme:
            base_path = parts.path.rsplit("/", 1)[0] + "/"
            return parts._replace(path=base_path, query="", fragment="").geturl()
    except Exception:
        pass
    if os.path.isabs(location):
        return os.path.dirname(location) + os.sep
    return ""


def _guide_name_index(guide):
    index = {}
    if not guide:
        return index
    for guide_id, names in guide.display_names.items():
        for name in names:
            key = _norm(name)
            if key and key not in index:
                index[key] = guide_id
    return index


def _match_guide(channel, guide, guide_names, now):
    candidates = []
    if channel.tvg_id and channel.tvg_id in guide.programmes:
        candidates = guide.programmes[channel.tvg_id]
    if not candidates:
        for wanted in (_norm(channel.tvg_name), _norm(channel.name)):
            guide_id = guide_names.get(wanted) if wanted else None
            if guide_id:
                candidates = guide.programmes.get(guide_id, [])
                if candidates:
                    break
    current = None
    nxt = None
    for program in candidates:
        if program.start <= now < program.stop:
            current = program
            continue
        if program.start > now:
            nxt = program
            break
    return ChannelGuide(current=current, next=nxt, schedule=list(candidates))


def load_catalog(source: dict, profile_dir: str, force: bool = False) -> Catalog:
    source_id = source.get("id") or "source"
    m3u_location, epg_location = resolve_source(source)
    if not m3u_location:
        raise ValueError("This source has no playlist address")

    source_cache = os.path.join(profile_dir, "cache", source_id)
    os.makedirs(source_cache, exist_ok=True)
    playlist_path = cache_location(m3u_location, os.path.join(source_cache, "playlist.m3u"), 300, force, 32 * 1024 * 1024)
    with open(playlist_path, "rb") as handle:
        playlist_data = handle.read()
    playlist = parse_m3u(playlist_data, _base_url(m3u_location))
    if not playlist.channels:
        raise ValueError("The playlist did not contain any playable channels")

    if not epg_location:
        epg_location = playlist.guide_url

    guide = None
    warning = ""
    if epg_location:
        try:
            guide_path = cache_location(epg_location, os.path.join(source_cache, "guide.xml"), 1800, force, 256 * 1024 * 1024)
            guide = parse_xmltv(guide_path, horizon_hours=36)
        except Exception as exc:
            warning = "Guide unavailable: " + str(exc)

    now = datetime.now(timezone.utc)
    guide_names = _guide_name_index(guide)
    guides = {}
    groups = []
    seen = set()
    for channel in playlist.channels:
        group = channel.group or "Other"
        if group not in seen:
            seen.add(group)
            groups.append(group)
        guides[channel.stable_key()] = _match_guide(channel, guide, guide_names, now) if guide else ChannelGuide()

    return Catalog(
        channels=playlist.channels,
        guides=guides,
        source_id=source_id,
        source_name=source.get("name") or "Live TV",
        groups=groups,
        warning=warning,
    )
