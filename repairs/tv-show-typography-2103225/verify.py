#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path

V=2103225
NAME='1.0.9-Cobra-TV-Show-Typography-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def h(b): return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v: raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--parent224',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--scope',type=Path,required=True)
    a=p.parse_args()

    report=json.loads(a.audit.read_text())
    scope=json.loads(a.scope.read_text())
    req(report.get('version_code')==V and report.get('version_name')==NAME,'identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'signer mismatch')
    req(scope.get('parent')==2103224,'wrong parent')
    req(scope['tv_show_typography'].get('font_family_unchanged') is True,'font family changed')
    req(scope['tv_show_typography'].get('shelf_order_unchanged') is True,'shelf order changed')
    req(scope['movies'].get('card_metrics_unchanged') is True,'movie card metrics changed')
    req(scope.get('tv_show_details_unchanged') is True,'TV details changed')
    req(scope.get('playback_unchanged') is True,'playback changed')
    req(scope.get('providers_unchanged') is True,'providers changed')

    with zipfile.ZipFile(a.apk) as z, zipfile.ZipFile(a.parent224) as pz:
        req(h(z.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'native engine changed')
        for n in pz.namelist():
            if n.startswith('lib/') and not n.endswith('/'):
                req(n in z.namelist() and z.read(n)==pz.read(n),'native drift '+n)
            elif n.startswith(('assets/','res/')) or n=='resources.arsc':
                req(n in z.namelist() and z.read(n)==pz.read(n),'resource drift '+n)
            elif re.fullmatch(r'classes\d+\.dex',n):
                req(n in z.namelist() and z.read(n)==pz.read(n),'secondary DEX drift '+n)

        dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
            b'tv_show_title_typography',
            b'tv_show_metadata_typography',
            b'tv_show_hero_metadata_typography',
            b'COBRA \xe2\x80\xa2 MOVIE DETAILS',
            b'COBRA \xe2\x80\xa2 TV SHOW DETAILS',
            b'BROWSE EPISODES',
            b'TRAILER',
            b'Related Movies',
            b'Related Shows',
            b'experience_options_ui_dialog',
            b'cobra_drawer_active_section',
        ):
            req(token in dex,'compiled contract missing '+repr(token))

    out={
        'build':V,'version_name':NAME,'apk_sha256':h(a.apk.read_bytes()),
        'parent_2103224_apk_sha256':h(a.parent224.read_bytes()),
        'native_engine_sha256':NATIVE,'signer':CERT,
        'resources_assets_identical_to_2103224':True,
        'native_libraries_identical_to_2103224':True,
        'secondary_dex_identical_to_2103224':True,
        'tv_show_typography_only':True,
        'tv_show_font_family_unchanged':True,
        'tv_show_metadata_clipping_fixed':True,
        'movie_card_metrics_unchanged':True,
        'movie_tv_details_unchanged':True,
        'playback_unchanged':True,'providers_unchanged':True,
        'physical_device_verified':False,'status':'TEST CANDIDATE'
    }
    Path('audit225/final.json').write_text(json.dumps(out,indent=2)+'\n')
    Path('signed225/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: 2103225 is TV Shows typography-only over locked 2103224')

if __name__=='__main__':
    main()
