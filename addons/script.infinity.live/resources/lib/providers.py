from urllib.parse import urlencode, urlsplit, urlunsplit


def normalize_server(server: str) -> str:
    server = (server or "").strip()
    if not server:
        raise ValueError("Server address is required")
    if "://" not in server:
        server = "http://" + server
    parts = urlsplit(server)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError("Server must be an http:// or https:// address")
    path = parts.path.rstrip("/")
    for suffix in ("/get.php", "/player_api.php", "/xmltv.php"):
        if path.lower().endswith(suffix):
            path = path[: -len(suffix)]
            break
    return urlunsplit((parts.scheme, parts.netloc, path, "", "")).rstrip("/")


def build_xtream_urls(server: str, username: str, password: str, output: str = "ts"):
    base = normalize_server(server)
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        raise ValueError("Username and password are required")
    output = "m3u8" if str(output).lower() == "m3u8" else "ts"
    playlist_query = urlencode(
        {"username": username, "password": password, "type": "m3u_plus", "output": output}
    )
    epg_query = urlencode({"username": username, "password": password})
    return f"{base}/get.php?{playlist_query}", f"{base}/xmltv.php?{epg_query}"


def resolve_source(source: dict):
    kind = (source.get("type") or "m3u").lower()
    if kind == "xtream":
        return build_xtream_urls(
            source.get("server", ""),
            source.get("username", ""),
            source.get("password", ""),
            source.get("output", "ts"),
        )
    return (source.get("m3u", "").strip(), source.get("epg", "").strip())


def redacted_source(source: dict) -> dict:
    safe = dict(source)
    if "password" in safe:
        safe["password"] = "***" if safe["password"] else ""
    for key in ("m3u", "epg"):
        value = safe.get(key)
        if isinstance(value, str) and ("username=" in value.lower() or "password=" in value.lower()):
            safe[key] = "<redacted-url>"
    return safe
