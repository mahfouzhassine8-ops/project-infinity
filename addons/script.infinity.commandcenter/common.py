# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import time
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
    tmp = path.with_name('.' + path.name + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    tmp.replace(path)


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
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


def jsonrpc(method: str, params=None):
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        payload['params'] = params
    try:
        return json.loads(xbmc.executeJSONRPC(json.dumps(payload)))
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
            if 'restore-points' in rel.parts:
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
    for path in list_restore_points()[keep:]:
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
        create_restore_point('before-restore')
    except Exception as error:
        return False, 'Could not create pre-restore safety point: ' + type(error).__name__

    root = profile_root()
    temp = addon_profile() / 'restore-stage'
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    temp.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(path, 'r') as zf:
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
