#!/usr/bin/env python3
"""Build the Infinity 1.0.6 presentation on a freshly source-built engine APK.

Order matters:
1. Reapply the approved 1.0.5 visual presentation/portrait sizing.
2. Apply the audited hook-driven theme/layout contract (menu contrast + hero flow).
3. Add an optional System fontset to Kodi's native Interface -> Skin -> Fonts chooser.
4. Replace the native bundled splash art with a square, bounded composition designed
   for the source-level AR_KEEP renderer correction.

This script does not sign and must not modify DEX/native libraries.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageDraw

import infinity_1_0_5_branding_fit as v105
import infinity_1_0_3_reference_ui as base
import infinity_theme_contract as audited

SKIN = 'assets/addons/skin.estuary/'
FONT_XML = SKIN + 'xml/Font.xml'
NATIVE_SPLASH = 'assets/media/splash.jpg'
AUDITED_XML = audited.XML_FILES
SYSTEM_FONT = 'InfinitySystem.ttf'
SYSTEM_MONO = 'InfinitySystem-Mono.ttf'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def image_bytes(image: Image.Image, fmt='PNG', **kwargs) -> bytes:
    out = io.BytesIO()
    image.save(out, fmt, **kwargs)
    return out.getvalue()


def make_square_splash(src_icon: bytes, light: bool = False, size=(1080, 1080)) -> Image.Image:
    # One square master works on tall cover screens and wide/inner screens when the
    # native renderer uses AR_KEEP. Black/ice bars blend into the background instead
    # of cropping the brand.
    bg = (248, 251, 255) if light else (0, 0, 0)
    out = Image.new('RGB', size, bg)
    symbol = base._fit_symbol(src_icon, 470)
    x = (size[0] - symbol.width) // 2
    y = 280
    out.paste(symbol, (x, y), symbol)
    draw = ImageDraw.Draw(out)
    word = (15, 22, 30) if light else (248, 250, 252)
    accent = (0, 119, 222) if light else (77, 202, 255)
    base._draw_centered_text(draw, 570, 'I N F I N I T Y', base._font(66), word, size[0])
    base._draw_centered_text(draw, 680, 'Y O U R   M E D I A .   Y O U R   W A Y .',
                             base._font(20), accent, size[0])
    return out


def system_fontset(data: bytes) -> bytes:
    root = ET.fromstring(data)
    existing = [fs for fs in root.findall('fontset') if fs.get('id') == 'System']
    for fs in existing:
        root.remove(fs)
    default = next((fs for fs in root.findall('fontset') if fs.get('id') == 'Default'), None)
    if default is None:
        raise RuntimeError('Default fontset missing')
    system = copy.deepcopy(default)
    system.set('id', 'System')
    # No idloc: Kodi displays the fontset identifier itself, i.e. "System".
    system.attrib.pop('idloc', None)
    for font in system.findall('font'):
        filename = font.find('filename')
        if filename is None:
            continue
        filename.text = SYSTEM_MONO if font.findtext('name') == 'Mono26' else SYSTEM_FONT
    root.append(system)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def rewrite_apk(src: Path, dst: Path, replacements: dict[str, bytes]) -> None:
    if src.resolve() == dst.resolve():
        raise RuntimeError('Input and output APK must differ')
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, 'w', allowZip64=True) as zout:
        names = zin.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError('Duplicate APK entries')
        seen = set()
        for item in zin.infolist():
            data = replacements.get(item.filename, zin.read(item.filename))
            if item.filename in replacements:
                seen.add(item.filename)
            zout.writestr(item, data)
        for name, data in replacements.items():
            if name not in seen:
                zout.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)


def native_and_dex_hashes(apk: Path) -> dict[str, str]:
    with zipfile.ZipFile(apk) as z:
        return {n: sha(z.read(n)) for n in z.namelist()
                if n.startswith('lib/') or (n.startswith('classes') and n.endswith('.dex'))}


def build(src: Path, out: Path, receipt: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        intermediate = Path(tmpdir) / 'presented.apk'
        old_receipt = Path(tmpdir) / 'old-presentation.json'

        # Override only the bundled startup art; leave the approved hero/launcher/sidebar
        # branding and portrait text treatment from 1.0.5 intact.
        v105.base.make_splash = make_square_splash
        v105.v104.base.make_splash = make_square_splash
        v105.v104.base.build(src, intermediate, old_receipt)

        protected_before = native_and_dex_hashes(intermediate)
        with zipfile.ZipFile(intermediate) as z:
            audit_in = {name: z.read(name) for name in AUDITED_XML}
            audited_out = audited.transform(audit_in)
            font_out = system_fontset(z.read(FONT_XML))
            # The 1.0.5 presentation already wrote our overridden splash function.
            splash = Image.open(io.BytesIO(z.read(NATIVE_SPLASH)))
            if splash.size[0] != splash.size[1]:
                raise RuntimeError('Native splash is not square after presentation override')

        replacements = dict(audited_out)
        replacements[FONT_XML] = font_out
        rewrite_apk(intermediate, out, replacements)
        protected_after = native_and_dex_hashes(out)
        if protected_before != protected_after:
            raise RuntimeError('Presentation changed DEX/native libraries')

    with zipfile.ZipFile(out) as z:
        home = z.read(SKIN + 'xml/Home.xml').decode('utf-8')
        ih = z.read(SKIN + 'xml/Includes_Home.xml').decode('utf-8')
        inc = z.read(SKIN + 'xml/Includes.xml').decode('utf-8')
        fonts = ET.fromstring(z.read(FONT_XML))
        system_sets = [fs for fs in fonts.findall('fontset') if fs.get('id') == 'System']
        checks = {
            'hook_named_theme_expression': 'Infinity.ThemeLight' in inc and 'Infinity.ThemeDark' in inc,
            'paired_menu_palettes': 'Infinity palette light' in home and 'Infinity palette dark' in home,
            'hero_centered_flow': '<centerleft>50%</centerleft>' in ih and 'max="550"' in ih,
            'center_brand_preserved': 'infinity/hero-dark.png' in ih and 'infinity/hero-light.png' in ih,
            'system_fontset_once': len(system_sets) == 1,
            'system_font_sentinel': len(system_sets) == 1 and SYSTEM_FONT in ET.tostring(system_sets[0], encoding='unicode'),
            'system_mono_sentinel': len(system_sets) == 1 and SYSTEM_MONO in ET.tostring(system_sets[0], encoding='unicode'),
            'native_splash_square': Image.open(io.BytesIO(z.read(NATIVE_SPLASH))).size == (1080, 1080),
            'lock_present': SKIN + 'xml/Custom_1199_InfinityVideoLock.xml' in z.namelist(),
        }
        if not all(checks.values()):
            raise RuntimeError('Consolidated presentation self-audit failed: ' + repr(checks))

    receipt.write_text(json.dumps({
        'release': 'Infinity 1.0.6 consolidated candidate',
        'input_apk': src.name,
        'output_apk': out.name,
        'presentation_native_or_dex_changed': False,
        'theme_layout_source': 'existing Infinity bridge v4 Home properties via audited named expressions',
        'light_selected_row': 'pale blue background + dark-blue foreground',
        'dark_selected_row': 'deep blue background + white foreground',
        'hero_paragraph': 'centered coordinate-aware autoheight; portrait font sizes preserved',
        'hero_branding': '1.0.5 approved center artwork preserved',
        'splash_art': '1080x1080 bounded Infinity composition; requires native AR_KEEP source correction',
        'font_option': 'System fontset appears in Kodi Interface -> Skin -> Fonts; Default remains available',
        'system_font_runtime': 'Android generic font matcher when available; bundled Noto fallback',
        'device_tested': False,
        'checks': checks,
    }, indent=2) + '\n')
    print('Infinity 1.0.6 consolidated presentation built; device verification still required.')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('src', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('receipt', type=Path)
    a = p.parse_args()
    build(a.src, a.out, a.receipt)


if __name__ == '__main__':
    main()
