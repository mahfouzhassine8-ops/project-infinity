#!/usr/bin/env python3
"""Group #1/task 03: restore numeric hit/scroll widths for only two Home panels.

The EXACT signed 2103390 Infinity skin declares 'unified' as its default
9:20 Home folder. That folder's horizontal Continue Watching item/focused
layouts say width='auto', height='97.619048%' and aspectratio='0.561219512'.
Kodi CGUIListItemLayout::LoadLayout consumes width/height as plain floating
point attributes; an unparsable width falls back to the full parent width,
making the effective focus/touch/scroll cell as wide as the panel.

The other THIRTEEN signed Home.xml variants already use the approved numeric
width='230.1', height='410' for both corresponding Continue Watching panels.
Change ONLY these four layout open tags in the default unified Home.xml.
All item art/params/appearance, routes, actions, providers and other panels
are byte-for-byte unchanged. The signed parent is never overwritten.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
from xml.etree import ElementTree as ET

TARGET = 'assets/addons/skin.infinity.diggz/unified/Home.xml'
PREIMAGE_SHA256 = '61fe23defed0536ce24f7c6d2d9b6beed5c0f3b8d04a33809a929a6b1f2532be'
FIXED_LAYOUT = b'width="230.1" height="410" aspectratio="0.561219512"'
ORIGINAL_LAYOUT = b'width="auto" height="97.619048%" aspectratio="0.561219512"'
CONTROL_IDS = ('8830', '8831')

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _block_pattern(ident: str) -> bytes:
    return (rb'(<control type="panel" id="' + ident.encode('ascii') +
            rb'">)(.*?)(\n      </control>)')


def patch_bytes(original: bytes) -> bytes:
    if digest(original) != PREIMAGE_SHA256:
        raise ValueError('Not signed 2103390 default unified/Home.xml preimage')
    text = original
    for ident in CONTROL_IDS:
        matches = list(re.finditer(_block_pattern(ident), text, re.DOTALL))
        if len(matches) != 1:
            raise ValueError('Cannot uniquely isolate Continue Watching panel ' + ident)
        found = matches[0]
        body = found.group(2)
        if body.count(ORIGINAL_LAYOUT) != 2:
            raise ValueError('Unexpected original item/focused layout ' + ident)
        # Test both item and focused layouts have identical intended size;
        # preserve every include param, animation, content, visibility, action.
        for tag in (b'itemlayout', b'focusedlayout'):
            if body.count(b'<' + tag + b' ' + ORIGINAL_LAYOUT + b'>') != 1:
                raise ValueError('Unexpected nested card layout ' + ident)
        repaired = body.replace(ORIGINAL_LAYOUT, FIXED_LAYOUT)
        text = text[:found.start(2)] + repaired + text[found.end(2):]
    root = ET.fromstring(text)
    for ident in CONTROL_IDS:
        panel = root.find('.//control[@id="' + ident + '"]')
        if panel is None or panel.attrib.get('type') != 'panel':
            raise ValueError('Continue Watching panel missing')
        if panel.findtext('orientation') != 'horizontal':
            raise ValueError('Continue Watching horizontal contract lost')
        for tag in ('itemlayout', 'focusedlayout'):
            item = panel.find(tag)
            if item is None or item.get('width') != '230.1' or item.get('height') != '410':
                raise ValueError('Numerical touch geometry not fixed')
    if text.count(FIXED_LAYOUT) != 4:
        raise ValueError('Changed more or fewer than exactly four layout tags')
    return text


def stage(source: Path, output: Path) -> tuple[str, str]:
    source, output = source.resolve(), output.resolve()
    if source == output:
        raise ValueError('Do not overwrite protected input')
    repaired = patch_bytes(source.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(repaired)
    return PREIMAGE_SHA256, digest(repaired)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('original', type=Path)
    parser.add_argument('staged', type=Path)
    options = parser.parse_args()
    old, new = stage(options.original, options.staged)
    print('Signed-parent safe Group #1/#03 staging only:', old, '=>', new)
