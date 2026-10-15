#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path

V = 2103222
NAME = '1.0.9-Experience-Options-UI-RC1'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE = 'db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def h(b): return hashlib.sha256(b).hexdigest()
def req(v, m):
    if not v:
        raise RuntimeError(m)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--apk', type=Path, required=True)
    p.add_argument('--parent221', type=Path, required=True)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--scope', type=Path, required=True)
    a = p.parse_args()

    report = json.loads(a.audit.read_text())
    scope = json.loads(a.scope.read_text())
    req(report.get('version_code') == V and report.get('version_name') == NAME,
        'identity mismatch')
    req(report.get('signer_certificate_sha256') == CERT, 'signer mismatch')
    req(scope.get('parent') == 2103221, 'wrong parent')
    req(scope.get('both_gears_fixed') is True, 'both gear menus not gated')
    req(scope.get('option_actions_unchanged') is True, 'option actions changed')
    req(scope.get('option_labels_unchanged') is True, 'option labels changed')
    req(scope.get('smart_return_untouched') is True, 'Smart Return changed')
    req(scope.get('drawer_owner_untouched') is True, 'drawer owner changed')

    with zipfile.ZipFile(a.apk) as z, zipfile.ZipFile(a.parent221) as pz:
        req(h(z.read('lib/arm64-v8a/libkodi.so')) == NATIVE, 'native engine changed')

        for n in pz.namelist():
            if n.startswith('lib/') and not n.endswith('/'):
                req(n in z.namelist() and z.read(n) == pz.read(n), 'native drift ' + n)
            elif n.startswith(('assets/', 'res/')) or n == 'resources.arsc':
                req(n in z.namelist() and z.read(n) == pz.read(n),
                    'unrelated resource drift ' + n)
            elif re.fullmatch(r'classes\d+\.dex', n):
                req(n in z.namelist() and z.read(n) == pz.read(n),
                    'secondary DEX drift ' + n)

        dex = b''.join(z.read(n) for n in z.namelist()
                       if re.fullmatch(r'classes\d*\.dex', n))
        for token in (
            b'experience_options_ui_row',
            b'experience_options_ui_dialog',
            b'Cobra options',
            b'Infinity options',
            b'Remember & launch ',
            b'Launch ',
            b'Ask every time',
            b'Infinity Health Center',
            b'Cobra Recovery',
            b'cobra_drawer_active_section',
            b'cobraHandleDrawerOwnedBack',
            b'cobra_smart_return_experience_display',
        ):
            req(token in dex, 'compiled contract missing ' + repr(token))

    out = {
        'build': V,
        'version_name': NAME,
        'apk_sha256': h(a.apk.read_bytes()),
        'parent_2103221_apk_sha256': h(a.parent221.read_bytes()),
        'native_engine_sha256': NATIVE,
        'signer': CERT,
        'parent_branch': 'locked-infinity-cobra-2103221-drawer-owner-ui-restore-passed',
        'resources_assets_identical_to_2103221': True,
        'native_libraries_identical_to_2103221': True,
        'secondary_dex_identical_to_2103221': True,
        'infinity_options_ui_fixed': True,
        'cobra_options_ui_fixed': True,
        'option_actions_unchanged': True,
        'smart_return_untouched': True,
        'drawer_owner_untouched': True,
        'physical_device_verified': False,
        'status': 'TEST CANDIDATE',
    }
    Path('audit222/final.json').write_text(json.dumps(out, indent=2) + '\n')
    Path('signed222/ACCEPTANCE.json').write_text(json.dumps(out, indent=2) + '\n')
    print('PASS: 2103222 is a presentation-only Choose Your Experience settings UI delta over locked 2103221')

if __name__ == '__main__':
    main()
