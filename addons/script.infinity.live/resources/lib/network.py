import gzip
import os
import shutil
import time
import urllib.request
from urllib.parse import unquote, urlsplit

_USER_AGENT = "InfinityLive/0.1 Kodi/21"


def _fresh(path: str, max_age: int) -> bool:
    return os.path.exists(path) and (time.time() - os.path.getmtime(path)) <= max_age and os.path.getsize(path) > 0


def _copy_local(location: str, destination: str, max_bytes: int):
    if location.startswith("file://"):
        location = unquote(urlsplit(location).path)
    if location.startswith("special://") or ("://" in location and not location.startswith("file://")):
        import xbmcvfs
        src = xbmcvfs.File(location)
        try:
            with open(destination, "wb") as out:
                total = 0
                while True:
                    chunk = src.readBytes(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError("Source exceeds Infinity Live size limit")
                    out.write(chunk)
        finally:
            src.close()
    else:
        if os.path.getsize(location) > max_bytes:
            raise ValueError("Source exceeds Infinity Live size limit")
        shutil.copyfile(location, destination)


def _download(location: str, destination: str, max_bytes: int):
    request = urllib.request.Request(location, headers={"User-Agent": _USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=20) as response:
        encoding = (response.headers.get("Content-Encoding") or "").lower()
        source = gzip.GzipFile(fileobj=response) if "gzip" in encoding else response
        total = 0
        with open(destination, "wb") as out:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("Source exceeds Infinity Live size limit")
                out.write(chunk)


def _maybe_unpack_gzip(path: str, max_bytes: int):
    with open(path, "rb") as handle:
        magic = handle.read(2)
    if magic != b"\x1f\x8b":
        return
    tmp = path + ".gunzip"
    total = 0
    try:
        with gzip.open(path, "rb") as src, open(tmp, "wb") as out:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("Expanded source exceeds Infinity Live size limit")
                out.write(chunk)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def cache_location(location: str, cache_path: str, max_age: int, force: bool, max_bytes: int) -> str:
    location = (location or "").strip()
    if not location:
        raise ValueError("Empty source address")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    if not force and _fresh(cache_path, max_age):
        return cache_path

    tmp = cache_path + ".tmp"
    try:
        if location.startswith(("http://", "https://")):
            _download(location, tmp, max_bytes)
        else:
            _copy_local(location, tmp, max_bytes)
        _maybe_unpack_gzip(tmp, max_bytes)
        if os.path.getsize(tmp) <= 0:
            raise ValueError("Source returned no data")
        os.replace(tmp, cache_path)
        return cache_path
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            return cache_path
        raise
