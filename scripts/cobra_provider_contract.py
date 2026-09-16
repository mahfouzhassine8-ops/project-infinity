#!/usr/bin/env python3
"""Pure reference contract for Infinity Cobra provider parsing.

The Android runtime implements the same URL/parsing rules. Keeping these rules
in a tiny dependency-free module lets CI validate provider edge cases before a
40-minute native APK build is allowed to start.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import quote, urlencode, urljoin, urlparse, parse_qsl


@dataclass(frozen=True)
class Channel:
    name: str
    group: str
    epg_id: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)


_M3U_ATTR = re.compile(r'([A-Za-z0-9_-]+)="([^"]*)"')


def normalize_server(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        raise ValueError("empty server")
    if "://" not in value:
        value = "http://" + value
    parsed = urlparse(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("invalid server")
    path = parsed.path.rstrip("/")
    if path.endswith("/player_api.php"):
        path = path[: -len("/player_api.php")]
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme.lower()}://{parsed.hostname}{port}{path}"


def xtream_api_url(server: str, username: str, password: str, action: str = "") -> str:
    base = normalize_server(server)
    params = {"username": username or "", "password": password or ""}
    if action:
        params["action"] = action
    return f"{base}/player_api.php?{urlencode(params)}"


def xtream_epg_url(server: str, username: str, password: str) -> str:
    base = normalize_server(server)
    return f"{base}/xmltv.php?{urlencode({'username': username or '', 'password': password or ''})}"


def xtream_stream_url(
    server: str, username: str, password: str, stream_id: str, extension: str = "ts"
) -> str:
    base = normalize_server(server)
    ext = sanitize_extension(extension)
    return (
        f"{base}/live/{quote(username or '', safe='')}/"
        f"{quote(password or '', safe='')}/{quote(str(stream_id), safe='')}.{ext}"
    )


def sanitize_extension(value: str) -> str:
    lower = (value or "ts").strip().lower()
    return lower if re.fullmatch(r"[a-z0-9]{1,8}", lower) else "ts"


def _pipe_headers(stream: str) -> tuple[str, dict[str, str]]:
    if "|" not in stream:
        return stream, {}
    url, options = stream.split("|", 1)
    headers: dict[str, str] = {}
    for key, value in parse_qsl(options, keep_blank_values=False):
        if key.lower() == "user-agent":
            headers["User-Agent"] = value
        elif key.lower() in {"referer", "referrer"}:
            headers["Referer"] = value
        elif key.lower() == "cookie":
            headers["Cookie"] = value
    return url, headers


def parse_m3u(base_url: str, text: str, limit: int = 12000) -> list[Channel]:
    channels: list[Channel] = []
    pending_info: str | None = None
    headers: dict[str, str] = {}
    for raw in (text or "").replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            pending_info = line
            headers = {}
            continue
        if line.startswith("#EXTVLCOPT:"):
            option = line[len("#EXTVLCOPT:") :]
            if "=" in option:
                key, value = option.split("=", 1)
                key = key.strip().lower()
                value = value.strip()
                if key == "http-user-agent":
                    headers["User-Agent"] = value
                elif key in {"http-referrer", "http-referer"}:
                    headers["Referer"] = value
            continue
        if line.startswith("#"):
            continue
        if pending_info is None:
            continue

        attrs = {m.group(1).lower(): m.group(2) for m in _M3U_ATTR.finditer(pending_info)}
        name = pending_info.rsplit(",", 1)[-1].strip() if "," in pending_info else ""
        name = name or attrs.get("tvg-name") or "Live channel"
        group = attrs.get("group-title") or "Other"
        epg_id = attrs.get("tvg-id") or ""

        stream, extra = _pipe_headers(line)
        merged = dict(headers)
        merged.update(extra)
        resolved = urljoin(base_url, stream.strip())
        if resolved.lower().startswith(("http://", "https://", "rtsp://")):
            channels.append(Channel(name, group, epg_id, resolved, merged))
        pending_info = None
        headers = {}
        if len(channels) >= limit:
            break
    return channels


def redact_provider_url(url: str) -> str:
    """Remove provider credentials from an URL before surfacing it in diagnostics."""
    if not url:
        return ""
    parsed = urlparse(url)
    path = parsed.path
    parts = path.split("/")
    # Common /live/user/password/id.ext shape.
    if len(parts) >= 5 and "live" in parts:
        live_index = parts.index("live")
        if live_index + 2 < len(parts):
            parts[live_index + 1] = "***"
            parts[live_index + 2] = "***"
            path = "/".join(parts)
    query_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in {"username", "password", "user", "pass"}:
            value = "***"
        query_pairs.append((key, value))
    query = urlencode(query_pairs)
    return parsed._replace(path=path, query=query).geturl()
