# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import tempfile
import zipfile

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

TAG = '[InfinityCommand] '
ADDON_ID = 'script.infinity.commandcenter'
PROFILE_FILES = (
    'guisettings.xml',
    'advancedsettings.xml',
    'sources.xml',
    'favourites.xml',
    'profiles.xml',
)
ADDON_DATA_DIRS = (
    'script.infinity.commandcenter',
    'skin.infinity.diggz',
    'script.skinshortcuts',
    'service.infinity.compat',
    'service.infinity.refresh',
)


def log(message, level=xbmc.LOGINFO):
    xbmc.log(TAG + message, level)


def addon():
    return xbmcaddon.Addon(ADDON_ID)


def profile_root() -> Path:
    return Path(xbmcvfs.translatePath('special://profile'))


def addon_profile() -> Path:
    return Path(xbmcvfs.translatePath(addon().getAddonInfo('profile')))


def restore_root() -> Path:
    path = addon_profile() / 'restore-points'
    path.mkdir(parents=True, exist_ok=True)
    return path


def atomic_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Separate invocations may save settings/restore metadata concurrently.
    # Unique temporary files prevent one invocation replacing another's temp.
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(json.dumps(data, indent=2, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, str(path))
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_json(path: Path, default):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(default, (dict, list)) and not isinstance(value, type(default)):
            return default
        return value
    except Exception:
        return default


def nonnegative_int(value, default=0):
    try:
        if isinstance(value, bool):
            return default
        result = int(value)
        return result if result >= 0 else default
    except (ValueError, TypeError, OverflowError):
        return default


def setting_bool(name: str, default=True) -> bool:
    try:
        raw = addon().getSetting(name)
        return default if raw == '' else raw.lower() == 'true'
    except Exception:
        return default


def setting_int(name: str, default: int) -> int:
    try:
        raw = addon().getSetting(name)
        return int(raw) if raw != '' else default
    except Exception:
        return default


def setting_str(name: str, default: str) -> str:
    try:
        raw = addon().getSetting(name)
        return raw if raw != '' else default
    except Exception:
        return default


def read_properties(path: Path) -> dict:
    """Read the small Java-style Infinity .properties files without external deps."""
    result = {}
    try:
        for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
            line = raw.strip()
            if not line or line.startswith(('#', '!')):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
            elif ':' in line:
                key, value = line.split(':', 1)
            else:
                continue
            key = key.strip()
            if key:
                result[key] = value.strip()
    except Exception:
        pass
    return result


def refresh_runtime_state() -> dict:
    root = Path(xbmcvfs.translatePath('special://profile/addon_data/service.infinity.refresh'))
    runtime = read_properties(root / 'runtime.properties')
    policy = read_properties(root / 'policy.properties')
    allowed_runtime = {
        'hook_active', 'mode', 'reason', 'requested_mode_id', 'requested_hz',
        'active_mode_id', 'active_hz', 'granted', 'status', 'battery_saver',
        'thermal_limited', 'updated_ms'
    }
    allowed_policy = {
        'mode', 'user_mode', 'max_hz', 'ui_policy', 'video_policy',
        'respect_battery_saver', 'thermal_protection', 'performance_override_battery'
    }
    return {
        'runtime': {k: runtime.get(k, '') for k in sorted(allowed_runtime) if k in runtime},
        'policy': {k: policy.get(k, '') for k in sorted(allowed_policy) if k in policy},
        'runtime_file_present': (root / 'runtime.properties').is_file(),
        'policy_file_present': (root / 'policy.properties').is_file(),
    }


def skin_baseline_integrity() -> dict:
    """Read-only exact hash check against the candidate-shipped protected manifest."""
    root = Path(xbmcvfs.translatePath('special://skin'))
    manifest_path = root / 'Infinity-Protected-Manifest.json'
    manifest = read_json(manifest_path, {})
    protected = manifest.get('protected_files') if isinstance(manifest, dict) else None
    if not isinstance(protected, dict) or not protected:
        return {'status': 'unavailable', 'checked': 0, 'mismatches': []}
    mismatches = []
    checked = 0
    for rel, wanted in sorted(protected.items()):
        path = root / rel
        checked += 1
        if not path.is_file():
            mismatches.append(rel + ':missing')
            continue
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception:
            mismatches.append(rel + ':unreadable')
            continue
        if actual != wanted:
            mismatches.append(rel + ':changed')
    return {
        'status': 'ok' if not mismatches else 'mismatch',
        'checked': checked,
        'mismatches': mismatches[:40],
        'candidate': manifest.get('candidate', ''),
        'skin_version': manifest.get('skin_version', ''),
    }

def jsonrpc(method: str, params=None):
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        payload['params'] = params
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(payload)))
        return response if isinstance(response, dict) else {'error': {'message': 'Invalid JSON-RPC response'}}
    except Exception:
        return {'error': {'message': 'JSON-RPC failure'}}


def addon_set_setting(addon_id: str, key: str, value: str) -> bool:
    try:
        xbmcaddon.Addon(addon_id).setSetting(key, value)
        return True
    except Exception as error:
        log('Cannot set ' + addon_id + ':' + key + ': ' + type(error).__name__, xbmc.LOGWARNING)
        return False


def disable_addon(addon_id: str) -> bool:
    result = jsonrpc('Addons.SetAddonEnabled', {'addonid': addon_id, 'enabled': False})
    return 'error' not in result


def _iter_snapshot_sources():
    root = profile_root()
    for name in PROFILE_FILES:
        path = root / name
        if path.is_file():
            yield path, Path(name)

    addon_data = root / 'addon_data'
    for dirname in ADDON_DATA_DIRS:
        source = addon_data / dirname
        if not source.is_dir():
            continue
        for path in source.rglob('*'):
            if not path.is_file():
                continue
            rel = Path('addon_data') / dirname / path.relative_to(source)
            if 'restore-points' in rel.parts or 'ui-backups' in rel.parts or path.name.startswith('.'):
                continue
            yield path, rel


def create_restore_point(reason='manual') -> Path:
    root = restore_root()
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    target = root / ('Infinity-Restore-' + timestamp + '-' + reason.replace(' ', '-') + '.zip')
    manifest = {
        'schema': 1,
        'created': int(time.time()),
        'reason': reason,
        'active_skin': xbmc.getSkinDir(),
        'infinity_theme': xbmcgui.Window(10000).getProperty('Infinity.Theme'),
        'infinity_device_mode': xbmcgui.Window(10000).getProperty('Infinity.DeviceMode'),
        'files': [],
    }
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zf:
        for source, rel in _iter_snapshot_sources():
            try:
                zf.write(str(source), str(rel).replace(os.sep, '/'))
                manifest['files'].append(str(rel).replace(os.sep, '/'))
            except OSError:
                continue
        zf.writestr('manifest.json', json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    prune_restore_points()
    log('Created restore point ' + target.name)
    return target


def list_restore_points():
    return sorted(restore_root().glob('Infinity-Restore-*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)


def prune_restore_points() -> None:
    keep = max(2, min(10, setting_int('max_restore_points', 5)))
    marker = read_json(addon_profile() / 'known-good.json', {})
    protected = marker.get('restore_point', '') if isinstance(marker, dict) else ''
    kept_regular = 0
    for path in list_restore_points():
        if path.name == protected:
            continue
        if kept_regular < keep:
            kept_regular += 1
            continue
        try:
            path.unlink()
        except OSError:
            pass


def _safe_member(name: str) -> bool:
    normalized = Path(name)
    return not normalized.is_absolute() and '..' not in normalized.parts and name != 'manifest.json'


def restore_point(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, 'Restore point does not exist.'
    try:
        # Creating the safety point also prunes old restore points. Keep the
        # selected archive available even when it is the oldest retained one.
        archive_bytes = path.read_bytes()
        create_restore_point('before-restore')
    except Exception as error:
        return False, 'Could not create pre-restore safety point: ' + type(error).__name__

    root = profile_root()
    temp = addon_profile() / 'restore-stage'
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    temp.mkdir(parents=True, exist_ok=True)

    try:
        import io
        with zipfile.ZipFile(io.BytesIO(archive_bytes), 'r') as zf:
            bad = [name for name in zf.namelist() if name != 'manifest.json' and not _safe_member(name)]
            if bad:
                return False, 'Restore point contains an unsafe path.'
            zf.extractall(temp)

        copied = 0
        for source in temp.rglob('*'):
            if not source.is_file() or source.name == 'manifest.json':
                continue
            rel = source.relative_to(temp)
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
        return True, 'Restored ' + str(copied) + ' configuration files.'
    except Exception as error:
        return False, 'Restore failed: ' + type(error).__name__
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def semantic_playback_key() -> tuple[str, str]:
    show = xbmc.getInfoLabel('VideoPlayer.TVShowTitle').strip()
    season = xbmc.getInfoLabel('VideoPlayer.Season').strip()
    episode = xbmc.getInfoLabel('VideoPlayer.Episode').strip()
    title = xbmc.getInfoLabel('VideoPlayer.Title').strip()
    year = xbmc.getInfoLabel('VideoPlayer.Year').strip()
    filename = xbmc.getInfoLabel('Player.Filenameandpath').strip()

    if show and season and episode:
        readable = 'tv:' + show + ':s' + season + 'e' + episode
    elif title:
        readable = 'movie:' + title + (':' + year if year else '')
    else:
        readable = 'file:' + filename
    digest = hashlib.sha256(readable.encode('utf-8', errors='replace')).hexdigest()
    return digest, readable


KNOWN_GOOD_FILE = 'known-good.json'
UI_BACKUP_DIR = 'ui-known-good'
DEFAULT_CRITICAL_UI = ('Home.xml','FileBrowser.xml','AddonBrowser.xml','VideoOSD.xml','DialogSeekBar.xml','DialogButtonMenu.xml')
DEFAULT_REQUIRED_IDS = {
    'Home.xml': {9000, 9100, 9081, 9082, 9083},
    'FileBrowser.xml': {412, 450, 451},
    'AddonBrowser.xml': {50},
    'VideoOSD.xml': {200, 201, 202, 204, 205, 250, 251, 252, 253, 254, 255, 256, 7999},
}


def _skin_root() -> Path | None:
    try:
        skin = xbmcaddon.Addon('skin.infinity.diggz')
        root = Path(xbmcvfs.translatePath(skin.getAddonInfo('path')))
        return root if root.is_dir() else None
    except Exception:
        return None


def _skin_resolution_dirs(root: Path):
    # The add-on declaration owns active layouts. Do not diagnose or restore
    # inactive historical folders instead of the actual unified mobile skin.
    import xml.etree.ElementTree as ET
    try:
        addon = ET.parse(root / 'addon.xml').getroot()
        wanted = [node.get('folder', '') for node in addon.findall("extension[@point='xbmc.gui.skin']/res")]
        return [root / name for name in dict.fromkeys(wanted)
                if name and not Path(name).is_absolute() and '..' not in Path(name).parts
                and (root / name).is_dir()]
    except (OSError, ET.ParseError):
        return []


def _skin_manifest(root: Path):
    data = read_json(root / 'infinity-skin.json', {})
    return data if isinstance(data, dict) else {}


def _skin_version(root: Path | None = None) -> str:
    if root is not None:
        manifest = _skin_manifest(root)
        value = str(manifest.get('skin_version', '') or '').strip()
        if value:
            return value
    try:
        return str(xbmcaddon.Addon('skin.infinity.diggz').getAddonInfo('version') or '').strip()
    except Exception:
        return ''


def _health_contract(root: Path):
    manifest = _skin_manifest(root)
    ui = manifest.get('ui_health', {}) if isinstance(manifest.get('ui_health', {}), dict) else {}
    critical_raw = ui.get('critical_files')
    if isinstance(critical_raw, list) and critical_raw:
        critical = tuple(x for x in critical_raw if isinstance(x, str) and
                         Path(x).name == x and x.endswith('.xml')) or DEFAULT_CRITICAL_UI
    else:
        critical = DEFAULT_CRITICAL_UI

    required = {name: set(values) for name, values in DEFAULT_REQUIRED_IDS.items()}
    declared = ui.get('required_ids', {}) if isinstance(ui.get('required_ids', {}), dict) else {}
    if declared:
        # A versioned skin manifest owns the current contract. Unlisted files have no ID requirement.
        required = {}
        for name, values in declared.items():
            ids = set()
            if isinstance(values, (list, tuple, set)):
                for value in values:
                    try: ids.add(int(value))
                    except Exception: pass
            required[str(name)] = ids
    try:
        schema = int(ui.get('schema', 0) or 0)
    except Exception:
        schema = 0
    return critical, required, schema, manifest


def _xml_ids(path: Path):
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(path.read_bytes())
    except Exception as error:
        return None, type(error).__name__
    ids = set()
    for node in root.iter():
        value = node.get('id')
        if value is None and node.tag == 'id':
            value = node.text
        try:
            if value is not None:
                ids.add(int(str(value).strip()))
        except Exception:
            pass
    return ids, ''


def ui_health():
    root = _skin_root()
    result = {
        'skin': 'skin.infinity.diggz', 'skin_version': '', 'healthy': True,
        'issues': [], 'issue_files': [], 'checked': [], 'contract_schema': 0,
    }
    if root is None:
        result['healthy'] = False
        result['issues'].append('Active skin path is unavailable.')
        return result
    result['skin_version'] = _skin_version(root)
    critical, required, schema, manifest = _health_contract(root)
    result['contract_schema'] = schema
    must_exist = {'Home.xml','VideoOSD.xml','DialogSeekBar.xml'}
    folders = _skin_resolution_dirs(root)
    if not folders:
        result['healthy'] = False
        result['issues'].append('No Infinity skin resolution folders are available.')
    for folder in folders:
        for name in critical:
            path = folder / name
            rel = folder.name + '/' + name
            if not path.is_file():
                # Auxiliary resolution folders may inherit non-core windows from the default resolution.
                if name in must_exist:
                    result['healthy'] = False
                    result['issues'].append(rel + ' is missing.')
                    result['issue_files'].append(rel)
                continue
            ids, error = _xml_ids(path)
            result['checked'].append(rel)
            if ids is None:
                result['healthy'] = False
                result['issues'].append(rel + ' parse error: ' + error)
                result['issue_files'].append(rel)
                continue
            needed = required.get(name, set())
            missing = sorted(needed - ids)
            if missing:
                result['healthy'] = False
                result['issues'].append(rel + ' missing control IDs ' + ','.join(str(x) for x in missing))
                result['issue_files'].append(rel)
    # Keep deterministic order and no duplicates.
    result['issue_files'] = list(dict.fromkeys(result['issue_files']))
    return result


def _file_sha256(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with path.open('rb') as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ''


def backup_ui_if_healthy(force=False):
    state = ui_health()
    if not state.get('healthy'):
        return False, state
    root = _skin_root()
    if root is None:
        return False, state
    target = addon_profile() / UI_BACKUP_DIR
    current_version = state.get('skin_version', '') or _skin_version(root)
    old_manifest = read_json(target / 'manifest.json', {}) if target.exists() else {}
    if target.exists() and (target / 'manifest.json').is_file() and not force:
        # A backup is reusable only for the exact installed skin version/contract.
        if (old_manifest.get('skin') == 'skin.infinity.diggz' and
                str(old_manifest.get('skin_version', '') or '') == current_version and
                nonnegative_int(old_manifest.get('schema', 0)) >= 2):
            return True, state
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    critical, _required, schema, _manifest = _health_contract(root)
    copied = []
    hashes = {}
    for folder in _skin_resolution_dirs(root):
        for name in critical:
            source = folder / name
            if source.is_file():
                rel = folder.name + '/' + name
                dest = target / folder.name / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                copied.append(rel)
                hashes[rel] = _file_sha256(source)
    atomic_json(target / 'manifest.json', {
        'schema': 2,
        'skin': 'skin.infinity.diggz',
        'skin_version': current_version,
        'health_contract_schema': schema,
        'created': int(time.time()),
        'checked': state.get('checked', []),
        'files': copied,
        'sha256': hashes,
    })
    log('UI known-good backup refreshed for skin version ' + (current_version or '?'))
    return True, state


def self_heal_ui():
    current = ui_health()
    if current.get('healthy'):
        backup_ui_if_healthy(force=False)
        return True, 'Critical Infinity UI files are healthy. Known-good UI backup matches the current skin version.'
    root = _skin_root()
    backup = addon_profile() / UI_BACKUP_DIR
    manifest = read_json(backup / 'manifest.json', {})
    if root is None or not manifest or manifest.get('skin') != 'skin.infinity.diggz':
        return False, 'UI problems were found, but no matching known-good UI backup is available.'

    current_version = current.get('skin_version', '') or _skin_version(root)
    backup_version = str(manifest.get('skin_version', '') or '')
    if not current_version or not backup_version or backup_version != current_version:
        return False, ('UI problems were found, but the known-good UI backup belongs to a different or unknown skin version. '
                       'Stale UI was not restored over the current skin.')

    issue_files = [str(x) for x in current.get('issue_files', []) if str(x).strip()]
    if not issue_files:
        return False, 'UI validation failed without a safely restorable file list; no automatic restore was performed.'
    copied = 0
    unavailable = []
    backup_hashes = manifest.get('sha256', {})
    if not isinstance(backup_hashes, dict):
        backup_hashes = {}
    for rel_text in issue_files:
        rel = Path(rel_text)
        if rel.is_absolute() or '..' in rel.parts:
            unavailable.append(rel_text)
            continue
        source = backup / rel
        target = root / rel
        expected = backup_hashes.get(rel_text)
        if not source.is_file() or not isinstance(expected, str) or not expected or _file_sha256(source) != expected:
            unavailable.append(rel_text)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1

    after = ui_health()
    if after.get('healthy'):
        return True, 'Restored only ' + str(copied) + ' unhealthy UI file(s) from the same-version known-good backup.'
    detail = '; '.join(after.get('issues', [])[:4])
    if unavailable:
        detail += '; backup missing or fails integrity: ' + ', '.join(unavailable[:4])
    return False, 'Selective restore completed, but critical UI validation still reports: ' + detail

def mark_known_good() -> Path:
    point = create_restore_point('known-good')
    backup_ui_if_healthy(force=True)
    atomic_json(addon_profile() / KNOWN_GOOD_FILE, {'schema':1,'created':int(time.time()),'restore_point':point.name,'skin':xbmc.getSkinDir()})
    return point


def known_good_point() -> Path | None:
    data = read_json(addon_profile() / KNOWN_GOOD_FILE, {})
    name = data.get('restore_point','') if isinstance(data, dict) else ''
    if not name:
        return None
    path = restore_root() / Path(name).name
    return path if path.is_file() else None


def restore_known_good():
    point = known_good_point()
    if point is None:
        return False, 'No Last Known Good Infinity snapshot exists yet.'
    return restore_point(point)
