"""Summarize one saved movie from a private local copy. No Kodi or network access."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
from urllib.parse import parse_qs, urlsplit
from zipfile import BadZipFile, ZipFile, is_zipfile

LIMIT = 8 * 1024 * 1024
MEMBER = "addon_data/script.infinity.commandcenter/continue-watching.json"
MEMBERS = {MEMBER, "profile/" + MEMBER}
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
PROVIDER = re.compile(r"plugin\.(?:video|audio|image|program)\.[a-zA-Z0-9._-]{1,96}\Z")
VERSION = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,6}){1,4}\Z")
ID_PATTERNS = {
    "tmdb": r"[1-9][0-9]{0,19}",
    "imdb": r"tt[0-9]{5,12}",
    "tvdb": r"[1-9][0-9]{0,19}",
}


def obj(value):
    return value if isinstance(value, dict) else {}


def safe_text(value, pattern):
    return value if isinstance(value, str) and pattern.fullmatch(value) else None


def number(value):
    return value if type(value) in (int, float) and 0 <= value <= 10**13 else None


def read_snapshot(path):
    if not path.is_file():
        raise ValueError("Expected an existing regular file.")
    if is_zipfile(path):
        with ZipFile(path) as archive:
            members = [m for m in archive.infolist() if m.filename in MEMBERS]
            if len(members) != 1:
                raise ValueError("Expected exactly one Command Center store in the existing ZIP.")
            member = members[0]
            if member.file_size > LIMIT or stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError("The store member is oversized or a symlink.")
            with archive.open(member) as stream:
                raw = stream.read(LIMIT + 1)
    else:
        with path.open("rb") as stream:
            raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("The store exceeds the supported size.")
    data = json.loads(raw)
    if type(obj(data).get("schema")) is not int or data["schema"] not in (1, 2):
        raise ValueError("Expected a schema 1 or 2 Continue Watching snapshot.")
    return data


def movie_ids(value):
    # Same typed-movie identity fields as signed resume_hub.entry_identity().
    value = obj(value)
    if (type(value.get("schema")) is not int or value["schema"] != 1
            or value.get("kind") != "movie" or value.get("scope") != "movie"):
        return {}
    ids = obj(value.get("ids"))
    return {
        name: text
        for name, pattern in ID_PATTERNS.items()
        if re.fullmatch(pattern, text := str(ids.get(name) or "").strip())
    }


def remembered(records, ids):
    if not ids:
        return {}, "identity_not_evaluated"

    def agrees(record):
        other = movie_ids(obj(record).get("identity"))
        common = ids.keys() & other.keys()
        return bool(common) and all(ids[key] == other[key] for key in common)

    name = next(iter(ids))
    canonical = hashlib.sha256(f"movie|{name}:{ids[name]}".encode("ascii")).hexdigest()
    exact = records.get(canonical)
    if agrees(exact):
        return exact, "canonical_identity"
    matches = [record for record in records.values() if agrees(record)]
    if len(matches) == 1:
        return matches[0], "unique_matching_alias"
    return {}, "ambiguous" if matches else "absent"


def route_fingerprint(value):
    if not isinstance(value, str) or not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def route_summary(value, fingerprint, failure_sha, ids):
    result = {
        "kind": "missing" if not fingerprint else "other",
        "provider": None,
        "matches_failed_route": fingerprint in failure_sha,
    }
    if not fingerprint:
        return result
    try:
        parsed = urlsplit(value)
    except ValueError:
        return result
    if parsed.scheme == "plugin":
        result.update(kind="plugin", provider=safe_text(parsed.netloc, PROVIDER))
        if parsed.netloc in ("plugin.video.umbrella", "plugin.video.pov"):
            # Report input shape only. Installed source and enablement are separate checks.
            query = parse_qs(parsed.query, keep_blank_values=True)
            single = all(len(values) == 1 for values in query.values())
            pov = parsed.netloc == "plugin.video.pov"
            mode = query.get("mode") == ["play_media"] and query.get("mediatype") == ["movie"]
            action = query.get("action") in (["play"], ["play_Item"])
            field_names = {name: name + "_id" if pov else name for name in ID_PATTERNS}
            route_ids = {
                name: query[field][0]
                for name, field in field_names.items()
                if field in query and re.fullmatch(ID_PATTERNS[name], query[field][0])
            }
            common = ids.keys() & route_ids.keys()
            result["movie_dispatch_shape_matches"] = (
                single and parsed.path in ("", "/")
                and (mode if pov else action) and not {"season", "episode"} & query.keys()
            )
            result["movie_ids_match"] = bool(common) and all(ids[name] == route_ids[name] for name in common)
    elif parsed.scheme in ("http", "https"):
        result["kind"] = "network"
    elif parsed.scheme in ("file", "special", "smb", "nfs") or value.startswith("/"):
        result["kind"] = "file"
    return result


def summarize(data, key):
    if not DIGEST.fullmatch(key):
        raise ValueError("An exact lowercase 64-digit key from the cancellation event is required.")
    entry = obj(obj(data.get("items")).get(key))
    if entry.get("media") != "movie":
        raise ValueError("The selected movie is absent from this snapshot.")
    ids = movie_ids(entry.get("identity"))
    source = obj(obj(data.get("sources")).get(key))
    recovery, lookup = remembered(obj(data.get("navigation_recovery")), ids)
    failures = recovery.get("failed_routes")
    failures = failures if isinstance(failures, list) else []
    failure_sha = {
        h for row in failures if (h := safe_text(obj(row).get("sha256"), DIGEST))
    }
    provider = obj(recovery.get("provider"))
    contract = obj(provider.get("contract"))
    values = {
        "source": entry.get("source"),
        "stable_source": entry.get("stable_source"),
        "legacy_preference": source.get("route"),
        "remembered_recovery": recovery.get("route"),
    }
    tmdb = str(entry.get("tmdb") or "").strip()
    values["tmdb_fallback_if_enabled"] = (
        "plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=movie&tmdb_id=" + tmdb
        if tmdb.isdigit() else None
    )
    fingerprints = {name: route_fingerprint(value) for name, value in values.items()}
    routes = {
        name: route_summary(value, fingerprints[name], failure_sha, ids)
        for name, value in values.items()
    }
    for name, route in routes.items():
        route["same_as"] = [
            other for other in routes
            if other != name and fingerprints[name] and fingerprints[name] == fingerprints[other]
        ]
    recorded = safe_text(recovery.get("route_sha256"), DIGEST)
    return {
        "selected_key": key,
        "store_schema": data["schema"],
        "store_revision": number(data.get("revision")),
        "checkpoint": {
            "position": number(entry.get("position")),
            "duration": number(entry.get("duration")),
            "updated": number(entry.get("updated")),
            "identity_namespaces": list(ids),
        },
        "legacy_source_failure_count": number(source.get("failures")),
        "routes": routes,
        "recovery": {
            "identity_lookup": lookup,
            "provider": safe_text(provider.get("id"), PROVIDER),
            "recorded_version": (safe_text(provider.get("version"), VERSION)
                                 or safe_text(contract.get("version"), VERSION)),
            "addon_manifest_sha256": safe_text(obj(contract.get("pins")).get("addon.xml"), DIGEST),
            "success_verified": recovery.get("success_verified") is True,
            "failed": recovery.get("failed") is True,
            "stored_route_fingerprint_matches": (
                recorded == fingerprints["remembered_recovery"] if recorded else None
            ),
            "failed_route_count": len(failure_sha),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="Existing, authorized JSON or ZIP on this computer")
    parser.add_argument("key", help="Full saved_key from the existing cancellation log")
    args = parser.parse_args()
    try:
        report = summarize(read_snapshot(args.snapshot), args.key)
    except (OSError, ValueError, BadZipFile, RuntimeError, RecursionError):
        # Input may contain private URLs, account paths and credentials.
        raise SystemExit("Unable to read exactly the selected movie from this snapshot.") from None
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
