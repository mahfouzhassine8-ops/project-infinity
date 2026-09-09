#!/usr/bin/env python3
# Infinity 1.0.4 responsive-branding trigger revision 2
from __future__ import annotations
import argparse, copy
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import infinity_1_0_3_reference_ui as base

_orig_patch_home = base.patch_home
_orig_patch_fonts = base.patch_fonts


def _set_text(parent, tag, value):
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    node.text = value
    return node


def _set_visible(control, cond):
    for v in list(control.findall('visible')):
        control.remove(v)
    ET.SubElement(control, 'visible').text = cond


def make_sidebar_logo(src_icon, light=False):
    out = Image.new('RGBA', (360, 210), (0, 0, 0, 0))
    sym = base._fit_symbol(src_icon, 292)
    out.alpha_composite(sym, ((360 - sym.width) // 2, 0))
    d = ImageDraw.Draw(out)
    color = (15, 22, 30, 255) if light else (246, 249, 252, 255)
    base._draw_centered_text(d, 148, 'I N F I N I T Y', base._font(29), color, 360)
    return out


def make_splash(src_icon, light=False, size=(1920, 1080)):
    bg = (248, 251, 255) if light else (0, 0, 0)
    out = Image.new('RGB', size, bg)
    sym = base._fit_symbol(src_icon, 640)
    x = (size[0] - sym.width) // 2
    y = 205
    out.paste(sym, (x, y), sym)
    d = ImageDraw.Draw(out)
    color = (15, 22, 30) if light else (248, 250, 252)
    base._draw_centered_text(d, 600, 'I N F I N I T Y', base._font(84), color, size[0])
    accent = (0, 119, 222) if light else (77, 202, 255)
    base._draw_centered_text(d, 728, 'Y O U R   M E D I A .   Y O U R   W A Y .', base._font(26), accent, size[0])
    return out


def patch_fonts(data):
    patched = _orig_patch_fonts(data)
    root = ET.fromstring(patched)
    wanted = {
        'InfinityMenuPortrait': '40',
        'InfinityBodyHeroPortrait': '30',
    }
    for fs in root.findall('fontset'):
        for f in fs.findall('font'):
            name = f.findtext('name')
            if name in wanted:
                _set_text(f, 'size', wanted[name])
                if name == 'InfinityBodyHeroPortrait':
                    _set_text(f, 'linespacing', '1.18')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def patch_home(data):
    patched = _orig_patch_home(data)
    root = ET.fromstring(patched)
    for parent in root.iter('control'):
        if parent.attrib.get('type') != 'group':
            continue
        children = list(parent)
        brand_controls = []
        for c in children:
            if c.attrib.get('type') != 'image':
                continue
            t = c.find('texture')
            if t is None:
                continue
            tex = (t.text or '').strip()
            if tex in ('infinity/sidebar-dark.png', 'infinity/sidebar-light.png'):
                brand_controls.append((c, tex))
        if not brand_controls:
            continue
        insert_at = min(parent.index(c) for c, _ in brand_controls)
        for c, _ in brand_controls:
            parent.remove(c)
        new_controls = []
        for _, tex in brand_controls:
            theme = base.DARK if tex.endswith('dark.png') else base.LIGHT
            specs = [
                (base.PORTRAIT, '0', '-8', '360', '200'),
                (base.MOBILE_LANDSCAPE, '8', '-4', '330', '170'),
                (base.NON_MOBILE, '12', '-4', '330', '170'),
            ]
            for layout_cond, left, top, width, height in specs:
                c = ET.Element('control', {'type': 'image'})
                _set_text(c, 'left', left)
                _set_text(c, 'top', top)
                _set_text(c, 'width', width)
                _set_text(c, 'height', height)
                _set_text(c, 'aspectratio', 'keep')
                ET.SubElement(c, 'texture').text = tex
                _set_visible(c, f'{theme} + {layout_cond}')
                new_controls.append(c)
        for offset, c in enumerate(new_controls):
            parent.insert(insert_at + offset, c)
        break
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


base.make_sidebar_logo = make_sidebar_logo
base.make_splash = make_splash
base.patch_fonts = patch_fonts
base.patch_home = patch_home


def main():
    p = argparse.ArgumentParser()
    p.add_argument('src', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('receipt', type=Path)
    a = p.parse_args()
    base.build(a.src, a.out, a.receipt)


if __name__ == '__main__':
    main()
