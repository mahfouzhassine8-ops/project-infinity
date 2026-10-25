#!/usr/bin/env python3
"""Infinity 2103405 — registered Kodi context item for WatchNixtoons2.

Changes only Command Center's Kodi addon.xml registration and reciprocal version
contracts. The existing context.py, provider sources, playback and Cobra remain
byte-for-byte unchanged. No title matching and no new media writes.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import re
import sys
import xml.etree.ElementTree as ET

PARENT_CC_XML_SHA = 'bb0ef93153402f1cfe62cfb7045689f78f4f623c8d420622fe1de110c5411dd7'
PARENT_CP_SHA = 'e9c1a4e767005cbb2fb273fc2149ef180489e53915fdcb5a59fdd6576873745e'
PARENT_TRAKT_SHA = '2416e4c010325c285acb4376372b0c03cac72ff1ec1800e7e44f2c53436d1d64'

NEW_ITEM = '''      <item library="context.py" args="infinity-item-menu-v1">
        <label>Infinity Tracked</label>
        <visible>String.StartsWith(ListItem.FileNameAndPath,plugin://plugin.video.watchnixtoons2/) | String.StartsWith(ListItem.Path,plugin://plugin.video.watchnixtoons2/)</visible>
      </item>
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def only_once(s: str, orig: str, replacement: str) -> str:
    if s.count(orig) != 1:
        raise AssertionError(f'Expected one source anchor ({orig[:100]}): found {s.count(orig)}')
    return s.replace(orig, replacement, 1)


def patch(directory: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    for fname, expected in [('addon.xml', PARENT_CC_XML_SHA),
                            ('checkpoint_runtime.py', PARENT_CP_SHA),
                            ('infinity_trakt.py', PARENT_TRAKT_SHA)]:
        actual = sha((directory/fname).read_bytes())
        if actual != expected:
            raise AssertionError(f'Wrong signed baseline: {fname}: {actual}')

    old = (directory/'addon.xml').read_text(encoding='utf8')
    anchor = '    <menu id="kodi.core.main">\n'
    new = only_once(old, anchor, anchor + NEW_ITEM)
    new = only_once(new, 'version="0.3.5.37"', 'version="0.3.5.38"')
    addon = ET.fromstring(new)
    assert addon.attrib['id'] == 'script.infinity.commandcenter'
    assert addon.attrib['version'] == '0.3.5.38'
    matches=[]
    for extension in addon.findall('extension'):
        if extension.get('point') == 'kodi.context.item':
            menu = extension.find('menu')
            assert menu is not None and menu.get('id') == 'kodi.core.main'
            matches = list(menu.findall('item'))
    assert len(matches)==2, 'Existing general Trakt context entry must remain'
    assert matches[0].get('library') == 'context.py'
    assert matches[0].get('args') == 'infinity-item-menu-v1'
    assert matches[0].findtext('label') == 'Infinity Tracked'
    assert matches[1].get('args') == 'manage'
    assert matches[1].findtext('label') == 'Infinity Trakt'
    expr = matches[0].findtext('visible')
    assert 'plugin://plugin.video.watchnixtoons2/' in expr
    assert 'ListItem.FileNameAndPath' in expr and 'ListItem.Path' in expr
    assert not any(x in expr for x in ('UniqueID', 'ListItem.DBID', 'ListItem.DBTYPE'))
    assert new.replace(NEW_ITEM,'').replace('0.3.5.38','0.3.5.37') == old

    previous=(directory/'checkpoint_runtime.py').read_text(encoding='utf8')
    checkpoint=only_once(previous,'ADDON_VERSION = "0.3.5.37"','ADDON_VERSION = "0.3.5.38"')
    existing=(directory/'infinity_trakt.py').read_text(encoding='utf8')
    trakt=only_once(existing,"'script.infinity.commandcenter','0.3.5.37'", "'script.infinity.commandcenter','0.3.5.38'")
    trakt=only_once(trakt,"'script.infinity.watchedbridge','1.0.18'", "'script.infinity.watchedbridge','1.0.19'")
    for name, contents in [('addon.xml',new),('checkpoint_runtime.py',checkpoint),('infinity_trakt.py',trakt)]:
        if name.endswith('.py'):compile(contents, name, 'exec')
        (output/name).write_text(contents,encoding='utf-8')
    return {name:sha((output/name).read_bytes()) for name in ('addon.xml','checkpoint_runtime.py','infinity_trakt.py')}


if __name__=='__main__':
    result=patch(Path(sys.argv[1]),Path(sys.argv[2]))
    for name,h in result.items():print(name,h)
