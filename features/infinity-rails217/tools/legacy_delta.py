#!/usr/bin/env python3
"""Recovered RC1/RC2 XML transforms retained for additive full-skin RC3 packaging."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

BASE_SHA = '486aa86c8f8dcda31d80c6d058f4b96154dcb2b3f1a18cfa464c65e280ec7e70'
ROOT = 'skin.infinity.diggz/'
PROFILES = ['16x9','20x9','5x6','6x5','fallback','portrait','unified'] + ['responsive/'+x for x in ['base','landscape','portrait','square','tall','ultrawide','wide']]
HERE = Path(__file__).resolve().parents[1]
ADDON = HERE / 'addons' / 'script.infinity.rails'
sys.path.insert(0, str(ADDON / 'resources'))
from lib.catalog import default_catalog


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rails_include(source):
    parsed = ET.fromstring(source)
    original = parsed.find("./include[@name='skinshortcuts-submenu-2']")
    section_re = re.compile(r'String\.IsEqual\(Container\(9000\)\.ListItem\.Property\(submenuVisibility\),(movies|tvshows)\)')
    original = copy.deepcopy(original)
    original.set('name','InfinityRailsFallback')
    count = 0
    for item in original.findall('item'):
        visible = item.find('visible')
        m = section_re.search(visible.text or '') if visible is not None else None
        if m:
            count += 1
            visible.text = '['+visible.text+'] + [!System.AddonIsEnabled(script.infinity.rails) | !String.IsEqual(Window(Home).Property(Infinity.Rails.'+m[1]+'.Ready),true)]'
    if count != 21:
        raise ValueError('Unexpected original rail count; will not overwrite a different source.')
    root = ET.Element('includes')
    var = ET.SubElement(root, 'variable', {'name':'InfinityRailsContent'})
    for section in ['movies','tvshows']:
        value = ET.SubElement(var,'value',{'condition':'System.AddonIsEnabled(script.infinity.rails) + String.IsEqual(Container(9000).ListItem.Property(section),'+section+')'})
        value.text = 'plugin://script.infinity.rails/?section='+section+'&revision=$INFO[Window(Home).Property(Infinity.Rails.Revision)]'
    ET.SubElement(var,'value')
    root.append(original)
    ET.indent(root,space='  ')
    return b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='utf-8')+b'\n'


def patch_home(raw):
    """Only replace the three rail content blocks; append to the Cinema submenu.

    Everything outside these exact content nodes remains byte-identical,
    including .212 continuity retirement and .213/.214 launch/Back fixes.
    """
    text = raw.decode('utf-8')
    patt = re.compile(r'(?P<block><content>\s*<include>skinshortcuts-submenu-2</include>\s*</content>)')
    if len(patt.findall(text)) != 3:
        raise ValueError('Unexpected rail structure.')
    dynamic = '<content target="videos" sortby="none" limit="0" browse="never">$VAR[InfinityRailsContent]</content>'
    text = patt.sub(lambda m:m['block'].replace('skinshortcuts-submenu-2','InfinityRailsFallback')+'\n        '+dynamic,text)
    marker = '<control type="fixedlist" id="19600">'
    start = text.index(marker)
    pos = text.index('<content>',start)
    end = text.index('</content>',pos)+len('</content>')
    if 'skinshortcuts-submenu</include>' not in text[pos:end]:
        raise ValueError('Unexpected Cinema menu structure.')
    text = text[:end]+'\n              '+dynamic+text[end:]
    ET.fromstring(text)
    return text.encode('utf-8')

