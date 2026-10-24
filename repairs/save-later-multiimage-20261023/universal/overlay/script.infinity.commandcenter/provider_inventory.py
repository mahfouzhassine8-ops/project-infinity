"""Versioned, read-only Infinity provider capability inventory.

One verified inventory serves Search and failure-only saved-title recovery.
Installation is not compatibility. Only the bundled, reviewed source contracts
grant an operation, and every dispatched route rechecks the original raw pins.
No provider code is imported, executed, patched, or granted persistence rights.

The cache is deliberately process-local: mutable Home properties and provider
files are not trusted as persisted capability proofs. Rebuilding after restart
keeps discovery functional without a second database or progress owner. An
unchanged inventory reuses verified source shapes within the invocation; UI
focus/taps never request discovery. Add-on events invalidate the cheap inventory
snapshot, and submission always enumerates current enabled state.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

API_VERSION = 1
CC = 'script.infinity.commandcenter'
MEDIA = ('movie', 'tv', 'anime', 'cartoon')
NAVIGATION_FAMILIES = frozenset(('mode-list-v1', 'action-list-v1', 'json-args-list-v1'))
INVENTORY_TTL = 2.0
MAX_CONTRACT_BYTES = 256 * 1024
_lock = threading.RLock()
_scan_lock = threading.Lock()
_cached = None
_checked_at = -1.0
_verified = {}
_generation = 0
_monitor = None
_event_revision = ''


def _rpc(method, params):
    answer = json.loads(xbmc.executeJSONRPC(json.dumps(
        dict(jsonrpc='2.0', id=1, method=method, params=params))))
    if 'error' in answer:
        raise RuntimeError('Installed providers could not be read safely.')
    return answer.get('result', {})


def invalidate():
    """Invalidate inventory metadata only; never touch routes or saved data."""
    global _checked_at, _generation
    with _lock:
        _checked_at = -1.0
        _generation += 1


class InventoryMonitor(xbmc.Monitor):
    def onNotification(self, sender, method, data):
        on_notification(sender, method, data)


def on_notification(sender, method, data):
    """Advisory Addons namespace invalidation, never execute notification data.

    Forward from the existing resident monitor as well as foreground Search.
    Kodi versions that don't emit lifecycle notifications still refresh through
    metadata TTL, source stamps and mandatory submission enumeration.
    """
    if isinstance(method, str) and method.startswith('Addons.'):
        invalidate()
        xbmcgui.Window(10000).setProperty('Infinity.ProviderInventory.Revision', str(time.monotonic_ns()))


def _contracts():
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon(CC).getAddonInfo('path'))).resolve()
    path = root / 'NAVIGATION-CONTRACTS.json'
    if path.is_symlink() or not path.is_file():
        raise RuntimeError('The installed provider contracts are unavailable.')
    with path.open('rb') as stream:
        raw = stream.read(MAX_CONTRACT_BYTES + 1)
    if len(raw) > MAX_CONTRACT_BYTES:
        raise RuntimeError('The installed provider contracts exceed their size limit.')
    value = json.loads(raw.decode('utf-8'))
    specs = value.get('contracts')
    if value.get('schema') != 1 or not isinstance(specs, list):
        raise RuntimeError('The installed provider contract version is unsupported.')
    for spec in specs:
        if (not isinstance(spec, dict) or not isinstance(spec.get('sources'), dict)
                or not isinstance(spec.get('search'), dict)
                or not isinstance(spec.get('entrypoint'), str)
                or not isinstance(spec.get('family'), str)):
            raise RuntimeError('The installed provider contracts are invalid.')
        if any(media not in MEDIA for media in spec['search']):
            raise RuntimeError('The installed provider category is unsupported.')
        for media, contract in spec['search'].items():
            if (not isinstance(contract, dict) or not isinstance(contract.get('params'), dict)
                    or not isinstance(contract.get('query_key'), str)):
                raise RuntimeError('The installed search operation is invalid.')
    return specs, hashlib.sha256(raw).hexdigest()


def _stamp(root, names):
    """Cheap change detection; dispatch still hashes every admitted source."""
    rows = []
    for name in sorted(set(names) | {'addon.xml'}):
        path = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Invalid provider source path.')
        try:
            stat = path.lstat()
            rows.append((name, stat.st_dev, stat.st_ino, stat.st_size,
                         stat.st_mtime_ns, stat.st_ctime_ns, path.is_symlink()))
        except FileNotFoundError:
            rows.append((name, None))
    return tuple(rows)


def _verify(addon_id, root, specs):
    # Import lazily to avoid Search -> inventory -> navigation -> Search cycles.
    # Reuse the original canonical shape/source verifier, not a weaker parser.
    from saved_navigation import capability, _source
    operations = {}
    for spec in specs:
        categories = [media for media in MEDIA if media in spec['search']]
        if not categories:
            continue
        provider = None
        # Exact reviewed release bytes can be verified by their bundled raw
        # SHA256 pins without reparsing large ASTs. Name-independent/new-version
        # family compatibility still falls back to the original shape verifier.
        # These hashes come from the signed component contract, never a mutable
        # persisted cache or an installed add-on's own capability declaration.
        exact = spec.get('exact_sources')
        if isinstance(exact, dict) and set(exact) == set(spec['sources']):
            try:
                manifest_raw = _source(root, 'addon.xml')
                if b'<!DOCTYPE' in manifest_raw:
                    raise ValueError('Unsupported manifest.')
                manifest = ET.fromstring(manifest_raw)
                extension = manifest.find('extension[@point="xbmc.python.pluginsource"]')
                if manifest.get('id') != addon_id or extension is None or extension.get('library') != spec['entrypoint']:
                    continue
                pins = {'addon.xml': hashlib.sha256(manifest_raw).hexdigest()}
                for name, expected in exact.items():
                    actual = hashlib.sha256(_source(root, name)).hexdigest()
                    if actual != expected:
                        raise ValueError('Source differs from the reviewed release.')
                    pins[name] = actual
                provider = dict(id=addon_id, root=str(root), family=spec['family'],
                                contract=dict(deepcopy(spec['search'][categories[0]]), pins=pins))
            except (OSError, ValueError, SyntaxError, UnicodeError, ET.ParseError):
                pass
        if provider is None:
            provider = capability(addon_id, root, categories[0], [spec])
        if provider is None:
            continue
        for media in categories:
            search = deepcopy(provider)
            search['contract'] = dict(deepcopy(spec['search'][media]),
                                      pins=deepcopy(provider['contract']['pins']))
            search['category_scope'] = spec.get('category_scope', {}).get(media, '')
            operations[(media, 'search')] = search
            # Existing navigation decoders independently support these exact
            # reviewed families. A specialty search-only adapter grants no
            # saved-route/identity/playback capability by implication.
            if spec['family'] in NAVIGATION_FAMILIES and media in ('movie', 'tv'):
                operations[(media, 'title_navigation')] = deepcopy(search)
                operations[(media, 'identity_lookup')] = deepcopy(search)
        break
    return operations


def _scan(rows, specs, digest, prior_proofs):
    names = {name for spec in specs for name in spec['sources']}
    entries, retained = [], {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        aid = row.get('addonid', '')
        if not isinstance(aid, str) or not re.fullmatch(r'plugin\.video\.[A-Za-z0-9._-]{1,90}', aid):
            continue
        enabled = row.get('enabled') is True
        entry = dict(id=aid, name=str(row.get('name') or aid)[:100],
                     version=str(row.get('version') or ''), enabled=enabled,
                     icon=str(row.get('thumbnail') or ''), status='disabled' if not enabled else 'unsupported',
                     operations={})
        if enabled:
            try:
                addon = xbmcaddon.Addon(aid)
                root = Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))).resolve()
                entry['icon'] = xbmcvfs.translatePath(addon.getAddonInfo('icon'))
                signature = (str(root), entry['version'], digest, _stamp(root, names))
                prior = prior_proofs.get(aid)
                operations = prior[1] if prior and prior[0] == signature else _verify(aid, root, specs)
                retained[aid] = (signature, operations)
                entry['operations'] = deepcopy(operations)
                entry['status'] = 'verified' if operations else 'unsupported'
            except (OSError, RuntimeError, ValueError, KeyError, SyntaxError, UnicodeError, ET.ParseError):
                entry['status'] = 'unsupported'
        entries.append(entry)
    priority = {'plugin.video.umbrella': 0, 'plugin.video.pov': 1, 'plugin.video.seren': 2}
    entries.sort(key=lambda entry: (priority.get(entry['id'], 3), entry['name'].casefold(), entry['id']))
    return entries, retained


def snapshot(force=False):
    global _cached, _checked_at, _verified, _monitor, _event_revision
    # Invalidation never acquires the scan lock. Native JSONRPC, Home property
    # access, filesystem IO and large copies run outside the publication lock.
    if _monitor is None:
        monitor = InventoryMonitor()
        with _lock:
            if _monitor is None:
                _monitor = monitor
    with _scan_lock:
        for attempt in range(2):
            now = time.monotonic()
            revision = xbmcgui.Window(10000).getProperty('Infinity.ProviderInventory.Revision')
            with _lock:
                cached, checked, event, generation = _cached, _checked_at, _event_revision, _generation
                prior_proofs = dict(_verified)
            if cached is not None and not force and revision == event and 0 <= now - checked < INVENTORY_TTL:
                return deepcopy(cached)
            # Omit enabled filter to include disabled installed providers.
            rows = _rpc('Addons.GetAddons', dict(type='xbmc.addon.video',
                        properties=['name', 'path', 'version', 'enabled', 'thumbnail'])).get('addons', [])
            if not isinstance(rows, list):
                raise RuntimeError('Installed provider inventory is invalid.')
            specs, digest = _contracts()
            entries, retained = _scan(rows, specs, digest, prior_proofs)
            current_revision = xbmcgui.Window(10000).getProperty('Infinity.ProviderInventory.Revision')
            candidate = dict(schema=API_VERSION, generation=generation, entries=entries)
            with _lock:
                if _generation != generation or current_revision != revision:
                    continue
                # Removed/disabled rows lose proofs; no first-N truncation.
                _verified = retained
                _cached = candidate
                _checked_at = now
                _event_revision = revision
            return deepcopy(candidate)
    raise RuntimeError('Providers changed during discovery. Reopen Search to refresh the available providers.')


def eligible(media, operation='search', force=False):
    """Return exact verified providers for one operation, plus installed status.

    Caller must use infinity_search.route before dispatch. This function never
    picks/replaces a provider or writes the user's successful-route memory.
    """
    if media not in MEDIA or operation not in ('search', 'title_navigation', 'identity_lookup'):
        return [], []
    ready, unavailable = [], []
    for entry in snapshot(force=force)['entries']:
        provider = entry['operations'].get((media, operation))
        if entry['enabled'] and provider:
            ready.append(dict(deepcopy(provider), name=entry['name'], icon=entry['icon'],
                              inventory_api=API_VERSION, media=media, operation=operation))
        else:
            unavailable.append(dict(id=entry['id'], name=entry['name'], icon=entry['icon'],
                                    enabled=entry['enabled'], reason='disabled' if not entry['enabled'] else 'unverified_operation'))
    return ready, unavailable


def has_enabled(addon_id):
    """Installed state only; deliberately grants no route/capability authority."""
    return any(entry['id'] == addon_id and entry['enabled'] for entry in snapshot()['entries'])
