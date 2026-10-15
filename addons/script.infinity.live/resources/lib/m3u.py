import re
from urllib.parse import urljoin, urlsplit

from .models import Channel, Playlist

_ATTR_RE = re.compile(r"([A-Za-z0-9_.:-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s,]+))")


def _attrs(text: str):
    out = {}
    for match in _ATTR_RE.finditer(text or ""):
        out[match.group(1).lower()] = next((v for v in match.groups()[1:] if v is not None), "")
    return out


def _guide_from_header(line: str) -> str:
    attrs = _attrs(line)
    for key in ("x-tvg-url", "url-tvg", "tvg-url"):
        if attrs.get(key):
            return attrs[key].split(",")[0].strip()
    return ""



def _resolve_location(base_url: str, value: str) -> str:
    value = (value or "").strip()
    if not value or not base_url:
        return value
    try:
        if urlsplit(value).scheme:
            return value
    except Exception:
        pass
    if value.startswith("/"):
        return value
    if base_url.startswith("special://"):
        return base_url.rstrip("/") + "/" + value.lstrip("/")
    return urljoin(base_url, value)

def parse_m3u(data, base_url: str = "") -> Playlist:
    if isinstance(data, bytes):
        text = data.decode("utf-8-sig", "replace")
    else:
        text = str(data or "")
    lines = [line.strip() for line in text.splitlines()]
    channels = []
    guide_url = ""
    pending = None
    pending_props = {}
    pending_group = ""

    for line in lines:
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("#EXTM3U"):
            guide_url = guide_url or _resolve_location(base_url, _guide_from_header(line))
            continue
        if upper.startswith("#EXTINF"):
            after = line.split(":", 1)[1] if ":" in line else ""
            meta, comma, display = after.partition(",")
            attrs = _attrs(meta)
            pending = {
                "name": (display.strip() if comma else "") or attrs.get("tvg-name", "") or "Channel",
                "group": attrs.get("group-title", "") or pending_group or "Other",
                "tvg_id": attrs.get("tvg-id", ""),
                "tvg_name": attrs.get("tvg-name", ""),
                "logo": attrs.get("tvg-logo", ""),
                "number": attrs.get("tvg-chno", "") or attrs.get("channel-number", ""),
            }
            pending_props = {}
            pending_group = ""
            continue
        if upper.startswith("#EXTGRP:"):
            pending_group = line.split(":", 1)[1].strip() or "Other"
            if pending is not None:
                pending["group"] = pending_group
            continue
        if upper.startswith("#KODIPROP:"):
            payload = line.split(":", 1)[1]
            key, sep, value = payload.partition("=")
            if sep and key.strip():
                pending_props[key.strip()] = value.strip()
            continue
        if upper.startswith("#EXTVLCOPT:"):
            payload = line.split(":", 1)[1]
            key, sep, value = payload.partition("=")
            if sep and key.strip():
                pending_props["vlc." + key.strip().lower()] = value.strip()
            continue
        if line.startswith("#"):
            continue
        if pending is None:
            continue

        url = _resolve_location(base_url, line)
        if not url:
            pending = None
            pending_props = {}
            continue
        channels.append(Channel(url=url, properties=dict(pending_props), **pending))
        pending = None
        pending_props = {}

    return Playlist(channels=channels, guide_url=guide_url)
