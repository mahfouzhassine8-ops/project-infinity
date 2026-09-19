#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, re, zipfile

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'visual-theme.json'
ZIP_ROOT = 'script.infinity.cobra.theme/resources/visual-theme.json'
COLOR = re.compile(r'^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$')
STYLE_FIELDS = {
    'fill','fill_end','stroke','stroke_width_dp','radius_dp','image','image_fit',
    'text','text_size_sp','font_family','font_asset','font_style','letter_spacing',
    'padding_dp','min_height_dp','elevation_dp','focus','pressed','selected',
    'width_dp','height_dp','margin_dp','margin_left_dp','margin_top_dp','margin_right_dp',
    'margin_bottom_dp','padding_left_dp','padding_top_dp','padding_right_dp','padding_bottom_dp',
    'weight','orientation','gravity','max_lines','alpha'
}
TOP = {'schema','scope','minimum_runtime','minimum_build','id','name','assets','base','variants'}
LAYER = {'colors','dimensions','numbers','copy','styles','images','scenes','guide_layouts'}
PALETTES = {'light','dark','oled','cover','portrait','landscape','tablet','tv'}
STYLE_PREFIXES = ('all.','widget.','drawer.','sheet.','settings','rail','screen','guide.','player.','multiview.','chooser','dialog.','tag.','font.','art.')
COPY_KEYS = {
    'chooser.label.brand','chooser.label.brand_tagline','chooser.label.title','chooser.label.personalization',
    'chooser.label.infinity_title','chooser.label.infinity_subtitle','chooser.label.cobra_title',
    'chooser.label.cobra_subtitle','chooser.label.footer_brand','chooser.label.footer_tagline','chooser.label.initials'
}

def fail(message: str) -> None:
    raise SystemExit('FAIL: ' + message)

def load() -> dict:
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    unknown = set(data) - TOP
    if unknown: fail('unsupported top-level fields: ' + ', '.join(sorted(unknown)))
    if data.get('schema') != 2 or data.get('scope') != 'cobra-presentation': fail('wrong Cobra visual schema/scope')
    if data.get('minimum_runtime') != 2: fail('minimum_runtime must remain 2')
    if int(data.get('minimum_build', 9999999)) > 2103160: fail('runtime build gate would reject this theme')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,63}', data.get('id','')): fail('invalid theme id')
    if not data.get('name') or len(data['name']) > 100: fail('invalid theme name')
    if data.get('assets') != {}: fail('v1 intentionally contains no binary/executable assets')
    validate_layer(data.get('base'), 'base')
    variants = data.get('variants', {})
    if not isinstance(variants, dict) or set(variants) - PALETTES: fail('unsupported variant')
    for name, layer in variants.items(): validate_layer(layer, 'variant:' + name)
    for required in ('light','dark','oled'):
        if required not in variants: fail('missing appearance variant: ' + required)
    return data

def validate_layer(layer, where: str) -> None:
    if not isinstance(layer, dict): fail(where + ' must be an object')
    unknown = set(layer) - LAYER
    if unknown: fail(where + ' has unsupported groups: ' + ', '.join(sorted(unknown)))
    colors = layer.get('colors', {})
    if not isinstance(colors, dict): fail(where + '/colors must be an object')
    for key, value in colors.items():
        if not isinstance(value, str) or not COLOR.fullmatch(value): fail(where + '/colors/' + key + ' invalid')
    copy = layer.get('copy', {})
    if not isinstance(copy, dict): fail(where + '/copy must be an object')
    for key, value in copy.items():
        if key not in COPY_KEYS: fail(where + '/copy/' + key + ' is not a wired chooser slot')
        if not isinstance(value, str) or not value.strip() or len(value) > 240 or '\x00' in value: fail(where + '/copy/' + key + ' invalid')
        low = value.lower()
        if key.endswith('_subtitle') and ('live tv' in low or '2-in-1' in low or '2 in 1' in low): fail('legacy chooser wording is forbidden')
    if 'chooser.label.initials' in copy and not re.fullmatch(r'[A-Za-z]{1,3}', copy['chooser.label.initials']): fail('initials must be 1-3 letters')
    styles = layer.get('styles', {})
    if not isinstance(styles, dict): fail(where + '/styles must be an object')
    for key, style in styles.items():
        if not key.startswith(STYLE_PREFIXES): fail(where + '/styles/' + key + ' is outside Cobra visual families')
        if not isinstance(style, dict): fail(where + '/styles/' + key + ' must be an object')
        unknown_style = set(style) - STYLE_FIELDS
        if unknown_style: fail(where + '/styles/' + key + ' unsupported fields: ' + ', '.join(sorted(unknown_style)))
        for c in ('fill','fill_end','stroke','text','focus','pressed','selected'):
            if c in style and (not isinstance(style[c], str) or not COLOR.fullmatch(style[c])): fail(where + '/styles/' + key + '/' + c + ' invalid')
        if 'radius_dp' in style and not 0 <= float(style['radius_dp']) <= 128: fail(where + '/styles/' + key + '/radius_dp out of range')
        if 'stroke_width_dp' in style and not 0 <= float(style['stroke_width_dp']) <= 24: fail(where + '/styles/' + key + '/stroke_width_dp out of range')
        if 'elevation_dp' in style and not 0 <= float(style['elevation_dp']) <= 24: fail(where + '/styles/' + key + '/elevation_dp out of range')
        if 'min_height_dp' in style and not 48 <= float(style['min_height_dp']) <= 200: fail(where + '/styles/' + key + '/min_height_dp out of range')
    numbers = layer.get('numbers', {})
    if not isinstance(numbers, dict): fail(where + '/numbers must be an object')
    for key, value in numbers.items():
        if key != 'chooser.layout.motion_ms': fail(where + '/numbers/' + key + ' is not a stable public slot')
        if not isinstance(value, (int,float)) or not 0 <= value <= 600: fail(where + '/numbers/' + key + ' invalid')
    for group in ('images','scenes','guide_layouts'):
        if layer.get(group): fail(where + '/' + group + ' intentionally unused in v1 to protect geometry/player ownership')

def build(out: Path) -> None:
    data = load()
    out.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    package = out / 'Cobra-Liquid-Glass-HM-v1.0.0.zip'
    info = zipfile.ZipInfo(ZIP_ROOT, date_time=(2026, 9, 19, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(package, 'w') as zf: zf.writestr(info, raw)
    with zipfile.ZipFile(package, 'r') as zf:
        names = zf.namelist()
        if names != [ZIP_ROOT]: fail('ZIP contains anything beyond the data-only manifest')
        if json.loads(zf.read(ZIP_ROOT).decode('utf-8')) != data: fail('ZIP manifest round-trip mismatch')
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    report = {
        'theme': data['id'], 'name': data['name'], 'sha256': digest,
        'zip': package.name, 'runtime': 2, 'minimum_build': 2103160,
        'base_commit': '0560b18c497e9861864126d96f9b784e488ebe32',
        'protected_playback_branch': 'infinity-cobra-2103179-buffer-resilience-rc1',
        'data_only': True, 'native_engine_changed': False, 'player_ownership_changed': False,
        'timeshift_rewind_changed': False, 'pip_changed': False, 'guide_geometry_changed': False,
        'assets': 0, 'appearance_variants': ['light','dark','oled'],
        'effect': 'Liquid Glass-inspired translucency, gradients, edge highlights, rounded depth; no fake claim of runtime blur.'
    }
    (out / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (out / 'SHA256SUMS').write_text(digest + '  ' + package.name + '\n', encoding='utf-8')
    print('PASS:', package)
    print('SHA-256:', digest)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=ROOT / 'dist')
    args = p.parse_args()
    build(args.out)
