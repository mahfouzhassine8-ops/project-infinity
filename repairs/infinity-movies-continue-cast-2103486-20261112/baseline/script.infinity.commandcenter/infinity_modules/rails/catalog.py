"""Extract approved shortcuts; discover custom cards from installed Kodi metadata only."""
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
from .store import RailError, SECTIONS, valid_id, ordered_tokens

LAUNCH = re.compile(r'^ActivateWindow\(Videos,"([^"\r\n]+)",return\)$', re.I)
SECTION = re.compile(r'String\.IsEqual\(Container\(9000\)\.ListItem\.Property\(submenuVisibility\),(movies|tvshows)\)')


def default_catalog(xml_bytes):
    if len(xml_bytes) > 2 * 1024 * 1024 or b'<!DOCTYPE' in xml_bytes or b'<!ENTITY' in xml_bytes:
        raise RailError('Unexpected shortcut source. No existing shortcuts were changed.')
    root = ET.fromstring(xml_bytes)
    inc = root.find("./include[@name='skinshortcuts-submenu-2']")
    if inc is None:
        raise RailError('The approved add-on rail include was not found.')
    rails = {sec: [] for sec in SECTIONS}
    for item in inc.findall('item'):
        visible = item.findtext('visible', '')
        section = SECTION.search(visible)
        if section is None:
            continue
        actions = item.findall('onclick')
        if len(actions) != 1 or actions[0].attrib:
            raise RailError('An existing add-on launcher has changed. Its action was not replaced.')
        match = LAUNCH.fullmatch(actions[0].text or '')
        if match is None or urlsplit(match[1]).scheme != 'plugin':
            raise RailError('Unsupported existing launcher. The approved source was retained.')
        uri = match[1]
        addon_id = urlsplit(uri).netloc
        if not valid_id(addon_id):
            raise RailError('Invalid existing add-on identity.')
        label = item.findtext('label', addon_id)
        key = 'b:' + hashlib.sha256((label + '\0' + uri).encode()).hexdigest()[:16]
        props = {p.get('name'): p.text or '' for p in item.findall('property')}
        rails[section[1]].append(dict(key=key, addon_id=addon_id, label=label,
            label2=item.findtext('label2',''), uri=uri, action=actions[0].text,
            icon=item.findtext('icon','DefaultAddonVideo.png'),
            thumb=item.findtext('thumb',item.findtext('icon','DefaultAddonVideo.png')),
            visible=visible, properties=props, custom=False, is_folder=True))
    if not all(rails.values()):
        raise RailError('One of the approved add-on rails is missing.')
    return rails


def resolve_selected(item):
    """Only accept an add-on root/metadata item, never infer a movie as an add-on."""
    value = item.getProperty('Addon.ID')
    if valid_id(value):
        return value
    uri = item.getPath() or ''
    parsed = urlsplit(uri)
    if parsed.scheme in ('plugin','script') and parsed.path in ('','/') and valid_id(parsed.netloc):
        return parsed.netloc
    if parsed.scheme == 'addons' and parsed.netloc in ('user','enabled'):
        value = unquote(parsed.path).strip('/')
        if valid_id(value):
            return value
    raise RailError('Select an installed video add-on, not a movie, episode or repository.')


def installed_card(addon_id, xbmc, xbmcaddon, xbmcvfs):
    if not valid_id(addon_id) or addon_id == 'script.infinity.rails':
        return None
    if not xbmc.getCondVisibility('System.AddonIsEnabled(%s)' % addon_id):
        return None
    try:
        addon = xbmcaddon.Addon(addon_id)
        directory = xbmcvfs.translatePath(addon.getAddonInfo('path'))
        with open(Path(directory) / 'addon.xml', 'rb') as src:
            raw = src.read(131073)
        if len(raw) > 131072 or b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:
            return None
        root = ET.fromstring(raw)
        if root.get('id') != addon_id:
            return None
        launch_type = None
        provides_several = False
        for extension in root.findall('extension'):
            provided = (extension.findtext('provides') or '').split()
            if 'video' not in provided:
                continue
            if extension.get('point') == 'xbmc.python.pluginsource':
                launch_type = 'plugin'
                provides_several = len(provided) > 1
                break
            if extension.get('point') == 'xbmc.python.script':
                launch_type = 'script'
        if launch_type is None:
            return None
        uri = launch_type + '://' + addon_id
        if provides_several:
            uri += '/?content_type=video'
        art = addon.getAddonInfo('icon') or 'DefaultAddonVideo.png'
        return dict(key='c:'+addon_id, addon_id=addon_id,
            label=addon.getAddonInfo('name') or addon_id, label2='', uri=uri,
            icon=art, thumb=art, visible='System.AddonIsEnabled(%s)' % addon_id,
            properties={}, custom=True, is_folder=(launch_type == 'plugin'))
    except (OSError, RuntimeError, ET.ParseError, ValueError):
        return None


def merge(standard, state, section, discover):
    defaults = standard[section]
    rows = {row['key']: dict(row) for row in defaults}
    builtin_ids = {row['addon_id'] for row in defaults}
    for addon_id in state['rails'][section]['custom']:
        if addon_id not in builtin_ids:
            row = discover(addon_id)
            if row is not None:
                rows[row['key']] = row
    return [rows[key] for key in ordered_tokens([r['key'] for r in defaults], state['rails'][section]) if key in rows]
