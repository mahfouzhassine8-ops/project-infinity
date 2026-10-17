"""Typed, bounded presentation snapshot; no Kodi imports, writes or title matching."""
import hashlib
import json
import re
from provider_contracts import PROOFS, presentation, CATALOG

OVERRIDES = "infinity_watched_overrides"
MAX_RECORDS = 1200
MAX_BYTES = 262144
KEY = re.compile(r"[a-f0-9]{64}\Z")


def ids(values):
    if not isinstance(values, dict):
        return {}
    result = {}
    for name, value in values.items():
        value = str(value or "").strip()
        if name in ("tmdb", "tvdb") and re.fullmatch(r"[1-9][0-9]{0,19}", value):
            result[name] = value
        elif name == "imdb" and re.fullmatch(r"tt[0-9]{5,12}", value):
            result[name] = value
    return result


def number(value):
    return value if type(value) is int and 0 <= value <= 100000 else -1


def identity(entry):
    if not isinstance(entry, dict):
        return None
    value = entry.get("identity")
    if not isinstance(value, dict) or type(value.get("schema")) is not int or value["schema"] != 1:
        return None
    names = ids(value.get("ids"))
    if not names:
        return None
    kind, scope = value.get("kind"), value.get("scope")
    if entry.get("media") == "movie" and kind == "movie" and scope == "movie":
        return dict(kind=kind, scope=scope, ids=names)
    if entry.get("media") != "tv" or kind != "episode" or scope not in ("episode", "show_episode"):
        return None
    season, episode = number(value.get("season")), number(value.get("episode"))
    if season < 0 or episode < 0 or (season, episode) != (number(entry.get("season")), number(entry.get("episode"))):
        return None
    return dict(kind=kind, scope=scope, ids=names, season=season, episode=episode)


def aliases(value):
    suffix = "" if value["kind"] == "movie" else ":%d:%d" % (value["season"], value["episode"])
    return [value["scope"] + ":" + name + ":" + uid + suffix for name, uid in sorted(value["ids"].items())]


def same(left, right):
    if not left or not right or (left["kind"], left["scope"]) != (right["kind"], right["scope"]):
        return False
    if left["kind"] == "episode" and (left["season"], left["episode"]) != (right["season"], right["episode"]):
        return False
    common = set(left["ids"]) & set(right["ids"])
    return bool(common) and all(left["ids"][name] == right["ids"][name] for name in common)


def records(data):
    if not isinstance(data, dict) or type(data.get("schema")) is not int or data["schema"] not in (1, 2):
        raise ValueError("Progress schema is unavailable or unsupported")
    watched, overrides = data.get("watched", {}), data.get(OVERRIDES, {})
    if not isinstance(watched, dict) or not isinstance(overrides, dict):
        raise ValueError("Watched state has an unsupported shape")
    if len(watched) > 600 or len(overrides) > 600:
        raise ValueError("Watched state exceeds the reviewed presentation limit")
    proofs = data.get(PROOFS, {})
    if not isinstance(proofs, dict) or len(proofs) > 1200:
        raise ValueError("Episode identity proof field is unsupported")
    positive = []
    by_alias = {}
    for key, entry in sorted(watched.items()):
        value = presentation(entry, identity(entry), proofs.get(key)) if KEY.fullmatch(str(key)) else None
        if value:
            index = len(positive)
            positive.append(dict(identity=value, watched=True))
            for alias in aliases(value):
                by_alias.setdefault(alias, set()).add(index)
    result = list(positive)
    for key, entry in sorted(overrides.items()):
        value = presentation(entry, identity(entry), proofs.get(key)) if KEY.fullmatch(str(key)) else None
        if not value:
            continue
        candidates = set().union(*(by_alias.get(alias, set()) for alias in aliases(value)))
        # Completion through the unchanged controller supersedes a former local
        # Unwatched override. No modification of that controller is required.
        if not any(same(value, positive[index]["identity"]) for index in candidates):
            result.append(dict(identity=value, watched=False))
    return result


def snapshot(data, profile, providers=None):
    rows = records(data)
    contracts = {name: CATALOG[name]["scope"] for name, proof in (providers or {}).items()
                 if name in CATALOG and CATALOG[name]["proof"] == proof}
    canonical = json.dumps(dict(records=rows, providers=contracts), separators=(",", ":"), sort_keys=True)
    payload = dict(schema=1, profile=str(profile).rstrip("/\\"),
                   revision=hashlib.sha256(canonical.encode()).hexdigest(), records=rows, providers=contracts)
    result = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    if len(result.encode("utf-8")) > MAX_BYTES or len(rows) > MAX_RECORDS:
        raise ValueError("Watched snapshot exceeds its native limit")
    return result


def lookup(rows, query):
    """Reference oracle for the same fail-closed native alias-index contract."""
    if not query:
        return ""
    candidates = [row for row in rows if set(aliases(row["identity"])) & set(aliases(query))]
    if not candidates or any(not same(row["identity"], query) for row in candidates):
        return ""
    # Two records sharing one alias but contradicting another are ambiguous,
    # even if a reduced query lacks that other namespace.
    if any(not same(left["identity"], right["identity"]) for left in candidates for right in candidates):
        return ""
    states = {row["watched"] for row in candidates}
    return ("true" if states.pop() else "false") if len(states) == 1 else ""
