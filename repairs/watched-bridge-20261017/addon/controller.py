"""Use the installed .20 participant only after all reviewed code hashes match."""
import hashlib
import importlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from bridge_state import OVERRIDES
from bridge_state import identity as presentation_raw, same, records as presentation_records, lookup as presentation_lookup
from provider_contracts import PROOFS, ENTRY_PROOF, provider, canonical, presentation


class UnsupportedController(RuntimeError):
    pass


def verify(root):
    root = Path(root).resolve()
    expected = json.loads((Path(__file__).parent / "CONTROLLER-PREIMAGES.json").read_text())
    if ET.parse(root / "addon.xml").getroot().get("version") != "0.3.5.20":
        raise UnsupportedController("This installed Command Center version has not been verified for these menu actions. Its code and data were left unchanged.")
    for name, wanted in expected.items():
        path = root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != wanted:
            raise UnsupportedController("The installed Command Center code differs from the reviewed .20 source. No menu action was applied; keep this code for the next compatibility audit.")
    return root


def load(root):
    root = verify(root)
    sys.path.insert(0, str(root))
    modules = {name: importlib.import_module(name) for name in ("common", "resume_hub", "context")}
    for name, module in modules.items():
        if Path(module.__file__).resolve() != root / (name + ".py"):
            raise UnsupportedController("A conflicting controller module is already loaded; no changes were made.")
    return modules


def apply(modules, profile, entry, action, intent=None):
    hub, common = modules["resume_hub"], modules["common"]
    identity = hub.entry_identity(entry)
    if not identity or entry.get("key") != hub.identity_key(identity):
        return False
    raw = presentation_raw(entry)
    query = canonical(entry, raw, entry.get(ENTRY_PROOF))
    if not query:
        return False
    with common.persistence_scope():
        source = Path(profile) / hub.CONTINUE_FILE
        if source.exists():
            if source.stat().st_size > 8 * 1024 * 1024:
                raise UnsupportedController("The progress file exceeds the reviewed action limit; no changes were made.")
            try:
                original = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise UnsupportedController("The progress file cannot be read safely; its existing contents were left unchanged.")
            if not isinstance(original, dict) or type(original.get("schema")) is not int or original["schema"] not in (1, 2):
                raise UnsupportedController("The progress schema is not compatible; no migration or reset was performed.")
        data = hub.load(profile)
        if data.get("pending_kodi_sync"):
            # Do not make a new action drive an older operation whose selected
            # row/proof was not admitted by this bridge. Keep its durable queue
            # for the existing controller owner; never discard or acknowledge it.
            raise UnsupportedController("An earlier library update is still pending in Command Center. Its queue and saved data were left unchanged; let the existing controller finish or review that update before trying another menu action.")
        proofs = data.get(PROOFS, {})
        if not isinstance(proofs, dict):
            raise UnsupportedController("The episode identity proof field is not compatible; no state was changed.")
        overrides = data.get(OVERRIDES, {})
        if not isinstance(overrides, dict):
            raise UnsupportedController("The local watched override field is not compatible; its contents were left unchanged.")
        key = hub.compatible_key(data, entry)
        override_keys = [name for name, value in overrides.items()
                         if hub.KEY_RE.fullmatch(str(name)) and hub.same_identity(hub.entry_identity(value), identity)]
        if not hub.find_entry(data, key) and override_keys:
            if len(override_keys) != 1:
                raise UnsupportedController("This identity matches more than one saved override; no ambiguous row was changed.")
            key = override_keys[0]
        saved = hub.find_entry(data, key)
        if saved and not hub.same_identity(hub.entry_identity(saved), identity):
            return False
        if intent is not None:
            # An existing local movie/episode menu can remain open while another
            # writer marks the item or changes a list. Recheck ONLY the selected
            # operation under the same Command Center persistence scope.
            # Do not rewrite provider databases, queued sync, or unrelated items.
            if (not isinstance(intent, dict) or intent.get("key") != key or
                    type(intent.get("watchlist")) is not bool or
                    type(intent.get("collection")) is not bool or
                    type(intent.get("displayed_watched")) is not bool or
                    intent.get("local_watched") not in ("", "true", "false")):
                return False
            if action == "toggle-watchlist":
                if (key in data.get("watchlist", {})) != intent["watchlist"]:
                    return False  # stale Add cannot silently become Remove
            elif action == "toggle-collection":
                if (key in data.get("collection", {})) != intent["collection"]:
                    return False
            elif action in ("mark-watched", "mark-unwatched"):
                # A native-library PlayCount may not yet be mirrored to local
                # state, so compare the same typed LOCAL observation shown in
                # the dialog, not an unverified new provider read.
                current_local = presentation_lookup(presentation_records(data), query)
                if current_local != intent["local_watched"]:
                    return False
                if (action == "mark-watched") == intent["displayed_watched"]:
                    return False  # selected action never matched visible state
            else:
                return False
        saved_canonical = presentation(saved, presentation_raw(saved), proofs.get(key)) if saved else None
        if saved and identity["kind"] == "episode" and provider(entry):
            if saved_canonical and not same(saved_canonical, query):
                return False
            if (not saved_canonical and
                    saved.get("source") != entry.get("source")):
                return False  # Old scope cannot be rebound by ID coincidence alone.
        admitted = dict(saved or entry, key=key)
        provider_episode = identity["kind"] == "episode" and provider(entry)
        if provider_episode:
            admitted["dbid"] = -1
        changed = None
        if action == "mark-watched":
            data, changed = hub.mark_watched_data(data, key, admitted, completed=False)
            if changed:
                overrides.pop(key, None)
                hub.queue_kodi_sync(data, changed, True)
        elif action == "mark-unwatched":
            data, changed = hub.mark_unwatched_data(data, key)
            changed = changed or admitted
            if provider_episode:
                # Older saved selections may predate the producer-scope proof.
                changed = dict(changed, dbid=-1)
            # Derived presentation state lives in the existing checkpointed
            # file as an additive foreign key, not a new unregistered database.
            overrides[key] = dict(changed, watched=False, updated=hub._now())
            overrides = dict(sorted(overrides.items(), key=lambda pair: int(pair[1].get("updated") or 0), reverse=True)[:600])
            hub.queue_kodi_sync(data, changed, False)
        elif action == "toggle-watchlist":
            data, _, changed = hub.toggle_watchlist_data(data, key, admitted)
        elif action == "toggle-collection":
            data, _, changed = hub._toggle_bucket(data, key, "collection", admitted)
        if changed is None:
            return False
        if identity["kind"] == "episode" and provider(entry):
            # Keep the existing controller key, routes and identities intact.
            # This attests only a currently selected, code-verified producer row.
            if saved_canonical:
                pass  # Keep the verified original producer/route proof across add-ons.
            elif provider(admitted) != provider(entry):
                raise UnsupportedController("This saved episode uses a different producer; its identity was left unchanged.")
            else:
                proofs[key] = dict(provider=provider(entry), proof=entry[ENTRY_PROOF], identity=presentation_raw(admitted))
            active = set(overrides)
            for bucket in ("items", "watched", "watchlist", "collection"):
                active.update(data.get(bucket, {}))
            proofs = {name: value for name, value in proofs.items() if name in active}
            if len(proofs) > 1200:
                raise UnsupportedController("The episode identity proof limit was reached; no state was saved.")
            data[PROOFS] = proofs
        data[OVERRIDES] = overrides
        hub.save(profile, data, hub.publish_home)
        # The existing lease is reentrant. Keep the new write and its existing
        # checked library flush in one lease so another invocation cannot add
        # an older/unrelated operation between admission and synchronization.
        hub.flush_kodi_sync(profile)
    return True
