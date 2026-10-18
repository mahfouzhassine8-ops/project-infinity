"""Load, never replace, the exact installed Command Center persistence owner."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

def load():
    import xbmcaddon
    import xbmcvfs
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('path'))).resolve()
    expected = json.loads((Path(__file__).parent / 'CONTROLLER-PREIMAGES.json').read_text())
    for name, digest in expected.items():
        p = root / name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise RuntimeError('Command Center differs from the verified version. Your saved data was left unchanged.')
    sys.path.insert(0, str(root))
    for name in ('common', 'experience', 'resume_hub', 'checkpoint_runtime', 'persistence_participant'):
        mod = importlib.import_module(name)
        if Path(mod.__file__).resolve() != root / (name + '.py'):
            raise RuntimeError('A conflicting Command Center module is loaded. No changes were made.')
    # The original module only reads argv at import. Never invoke its main()
    # or replace plugin.py: its exact menu generator and mutation owner are reused.
    before = sys.argv[:]
    try:
        sys.argv = ['plugin://script.infinity.commandcenter/', '-1', '']
        spec = importlib.util.spec_from_file_location('infinity_verified_resume_plugin', root / 'plugin.py')
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
    finally:
        sys.argv = before
    return plugin

def _context_rows_data(plugin, key, data, entry):
    """Evaluate the original Command Center menu for a current Continue item.

    Never mutate an item that completed or disappeared during the popup.
    """
    from urllib.parse import parse_qs, urlparse
    items = data.get('items')
    if not isinstance(items, dict) or key not in items:
        return []
    if not entry or not plugin.hub.entry_identity(entry) or entry.get('synthetic_next'):
        return []
    rows = []
    for label, command in plugin._context(entry, data, 'continue'):
        if not command.startswith('RunPlugin(plugin://script.infinity.commandcenter/?') or not command.endswith(')'):
            raise RuntimeError('Unexpected Command Center context action.')
        params = parse_qs(urlparse(command[len('RunPlugin('):-1]).query)
        op = params.get('op', [''])[0]
        if params.get('key') != [key] or not op:
            raise RuntimeError('The menu item identity changed.')
        rows.append((label, op))
    return rows


def context_rows(plugin, key):
    hub = plugin.hub
    if not hub.KEY_RE.fullmatch(key):
        return None, []
    data = hub.load_view(plugin.PROFILE)
    entry = hub.find_entry(data, key)
    rows = _context_rows_data(plugin, key, data, entry)
    return (entry, rows) if rows else (None, [])

def mutate(plugin, key, original, op, choice=None, name='', expected_label=None):
    """Keep the original writer gate, mutation functions, queue and home publisher."""
    hub = plugin.hub
    with plugin.persistence_scope():
        data = hub.load(plugin.PROFILE)
        current = hub.find_entry(data, key)
        if not current or not hub.same_identity(hub.entry_identity(original), hub.entry_identity(current)):
            return False
        if expected_label is not None:
            # Check the actual action seen by the user, under the existing
            # protected CC writer scope. 'Add' must not become 'Remove' while
            # a background writer updates membership, rating, or playback.
            if not isinstance(expected_label, str) or (expected_label, op) not in \
                    _context_rows_data(plugin, key, data, current):
                return False
            if op in ('mark-watched', 'mark-unwatched', 'reset-progress', 'remove-resume'):
                for field in ('position', 'playback_occurrence'):
                    if original.get(field) != current.get(field):
                        return False
        overrides = data.get('infinity_watched_overrides', {})
        if not isinstance(overrides, dict):
            raise RuntimeError('The watched bridge state is unsupported; no changes were made.')
        changed, _ = plugin._mutate_locked(op, key, '', choice, name)
        if changed and op in ('mark-watched', 'mark-unwatched'):
            # Preserve the existing bridge's explicit negative watched override.
            # This is the SAME essential, checkpointed progress file and lease.
            data = hub.load(plugin.PROFILE)
            overrides = data.get('infinity_watched_overrides', {})
            if op == 'mark-watched':
                overrides.pop(key, None)
            else:
                overrides[key] = dict(current, watched=False, updated=hub._now())
                overrides = dict(sorted(overrides.items(), key=lambda pair: int(pair[1].get('updated') or 0), reverse=True)[:600])
            data['infinity_watched_overrides'] = overrides
            hub.save(plugin.PROFILE, data, hub.publish_home)
        if changed:
            hub.flush_kodi_sync(plugin.PROFILE)
        return changed
