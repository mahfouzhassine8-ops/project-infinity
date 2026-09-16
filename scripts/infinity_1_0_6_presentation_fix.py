#!/usr/bin/env python3
"""Recover Infinity 1.0.6 presentation from a fresh source-built engine.

The 1.0.3/1.0.4 presentation chain can resize an existing Infinity sidebar brand,
but a freshly source-built Kodi 21.3 Estuary Home.xml has no Infinity brand node.
This wrapper creates the approved responsive dark/light sidebar controls only when
none exist, then delegates every other presentation and release gate to 1.0.6.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import infinity_1_0_6_consolidated as release

_original_patch_home = release.base.patch_home


def _set_text(parent: ET.Element, tag: str, value: str) -> None:
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    node.text = value


def _image(texture: str, visible: str, left: str, top: str,
           width: str, height: str) -> ET.Element:
    control = ET.Element('control', {'type': 'image'})
    _set_text(control, 'left', left)
    _set_text(control, 'top', top)
    _set_text(control, 'width', width)
    _set_text(control, 'height', height)
    _set_text(control, 'aspectratio', 'keep')
    ET.SubElement(control, 'texture').text = texture
    ET.SubElement(control, 'visible').text = visible
    return control


def patch_home(data: bytes) -> bytes:
    patched = _original_patch_home(data)
    root = ET.fromstring(patched)

    existing = []
    for control in root.iter('control'):
        if control.attrib.get('type') != 'image':
            continue
        texture = (control.findtext('texture') or '').strip()
        if texture in ('infinity/sidebar-dark.png', 'infinity/sidebar-light.png'):
            existing.append(control)
    if existing:
        return patched

    controls = root.find('controls')
    if controls is None:
        raise RuntimeError('Home.xml top-level controls container missing')

    brand = ET.Element('control', {'type': 'group'})
    layouts = [
        (release.base.PORTRAIT, '0', '-8', '360', '200'),
        (release.base.MOBILE_LANDSCAPE, '8', '-4', '320', '170'),
        (release.base.NON_MOBILE, '12', '-4', '330', '170'),
    ]
    for texture, theme in (
        ('infinity/sidebar-dark.png', release.base.DARK),
        ('infinity/sidebar-light.png', release.base.LIGHT),
    ):
        for layout, left, top, width, height in layouts:
            brand.append(_image(texture, f'{theme} + {layout}', left, top, width, height))

    # Keep branding near the top of Home's draw order while leaving Kodi's hidden
    # focus objects/background and the menu/widget groups otherwise untouched.
    insert_at = min(3, len(list(controls)))
    controls.insert(insert_at, brand)

    out = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    check = out.decode('utf-8')
    if 'infinity/sidebar-dark.png' not in check or '<width>320</width>' not in check:
        raise RuntimeError('Fresh-engine sidebar insertion self-check failed')
    return out


# v105/v104/base all reference the same imported base module object.
release.base.patch_home = patch_home


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('src', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('receipt', type=Path)
    a = p.parse_args()
    release.build(a.src, a.out, a.receipt)


if __name__ == '__main__':
    main()
