from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

SKIN_ID = 'skin.xenon2'
PROTECTED = ('VideoOSD.xml', 'DialogSeekBar.xml', 'Custom_1199_InfinityVideoLock.xml')
THEMES = ('InfinityDark.xml', 'InfinityLight.xml', 'InfinityOLED.xml')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return False
    tmp = path.with_name(path.name + '.infinity.tmp')
    tmp.write_bytes(data)
    tmp.replace(path)
    return True


def backup_once(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    target = backup_root / path.name
    if not target.exists():
        backup_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def ensure_player_files(skin_root: Path, addon_root: Path, backup_root: Path) -> dict:
    xml_root = skin_root / '16x9'
    source_root = addon_root / 'resources/xml'
    changed = []
    for name in PROTECTED:
        source = source_root / name
        if not source.is_file():
            raise FileNotFoundError(source)
        ET.fromstring(source.read_bytes())
        target = xml_root / name
        if name in ('VideoOSD.xml', 'DialogSeekBar.xml'):
            backup_once(target, backup_root)
        if atomic_write(target, source.read_bytes()):
            changed.append(name)
    return {'changed': changed, 'protected': list(PROTECTED)}


def ensure_theme_files(skin_root: Path, addon_root: Path) -> list[str]:
    colors = skin_root / 'colors'
    source = addon_root / 'resources/colors'
    changed = []
    for name in THEMES:
        data = (source / name).read_bytes()
        ET.fromstring(data)
        if atomic_write(colors / name, data):
            changed.append(name)
    return changed


def ensure_system_fontset(skin_root: Path, backup_root: Path) -> bool:
    path = skin_root / '16x9/Font.xml'
    if not path.is_file():
        return False
    root = ET.fromstring(path.read_bytes())
    if any(fs.get('id') == 'Infinity System' for fs in root.findall('fontset')):
        return False
    base = next((fs for fs in root.findall('fontset') if fs.get('id') == 'Default'), None)
    if base is None:
        return False
    import copy
    system = copy.deepcopy(base)
    system.set('id', 'Infinity System')
    for font in system.findall('font'):
        filename = font.find('filename')
        if filename is None:
            continue
        current = (filename.text or '').lower()
        filename.text = 'InfinitySystem-Mono.ttf' if 'mono' in current else 'InfinitySystem.ttf'
    root.append(system)
    backup_once(path, backup_root)
    return atomic_write(path, ET.tostring(root, encoding='utf-8', xml_declaration=True))


def parse_estuary_policy(settings_path: Path) -> str:
    if not settings_path.is_file():
        return ''
    try:
        root = ET.fromstring(settings_path.read_bytes())
    except ET.ParseError:
        return ''
    for setting in root.iter('setting'):
        sid = setting.get('id', '')
        if sid in ('Infinity.ThemePolicy', 'infinity.themepolicy'):
            value = (setting.text or setting.get('value') or '').strip().lower()
            if value in ('light', 'dark', 'oled', 'system'):
                return value
    return ''


def resolve_theme(policy: str, system_theme: str) -> str:
    policy = (policy or '').lower()
    system_theme = (system_theme or '').lower()
    if policy == 'light':
        return 'InfinityLight.xml'
    if policy == 'dark':
        return 'InfinityDark.xml'
    if policy == 'oled':
        return 'InfinityOLED.xml'
    if system_theme == 'light':
        return 'InfinityLight.xml'
    if system_theme == 'oled':
        return 'InfinityOLED.xml'
    if system_theme == 'dark':
        return 'InfinityDark.xml'
    return ''


def setting_rpc(method, setting, value=None):
    params = {'setting': setting}
    if method == 'Settings.SetSettingValue':
        params['value'] = value
    return json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
