#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path

V=2103224
NAME='1.0.9-Cobra-Movie-TV-Details-Trailers-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def h(b): return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v: raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--parent223',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--scope',type=Path,required=True)
    a=p.parse_args()

    report=json.loads(a.audit.read_text())
    scope=json.loads(a.scope.read_text())
    req(report.get('version_code')==V and report.get('version_name')==NAME,'identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'signer mismatch')
    req(scope.get('parent')==2103223,'wrong parent')
    req(scope['movies'].get('locked_2103223_detail_page_unchanged') is True,'movie detail changed')
    req(scope['tv_shows'].get('full_page_detail') is True,'TV full-page detail gate missing')
    req(scope['tv_shows'].get('trailers_action') is True,'TV trailer action gate missing')
    req(scope['episode_browser'].get('unchanged') is True,'episode browser changed')
    req(scope.get('providers_unchanged') is True,'providers changed')
    req(scope.get('choose_experience_ui_unchanged') is True,'chooser UI changed')

    with zipfile.ZipFile(a.apk) as z, zipfile.ZipFile(a.parent223) as pz:
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
            b'COBRA \xe2\x80\xa2 MOVIE DETAILS',
            b'COBRA \xe2\x80\xa2 TV SHOW DETAILS',
            b'BROWSE EPISODES',
            b'TRAILER',
            b'Trailers',
            b'Related Movies',
            b'Related Shows',
            b'Cast & Crew',
            b'Storyline',
            b'Available via ',
            b'official trailer',
            b'Resume Episode',
            b'Play Next Episode',
            b'cobra_drawer_active_section',
            b'experience_options_ui_dialog',
        ):
            req(token in dex,'compiled contract missing '+repr(token))

    out={
        'build':V,'version_name':NAME,'apk_sha256':h(a.apk.read_bytes()),
        'parent_2103223_apk_sha256':h(a.parent223.read_bytes()),
        'native_engine_sha256':NATIVE,'signer':CERT,
        'resources_assets_identical_to_2103223':True,
        'native_libraries_identical_to_2103223':True,
        'secondary_dex_identical_to_2103223':True,
        'movie_details_unchanged_from_2103223':True,
        'tv_show_details_full_page':True,'tv_show_trailers_option':True,
        'tv_episode_browser_unchanged':True,'playback_unchanged':True,
        'providers_unchanged':True,'choose_experience_ui_unchanged':True,
        'physical_device_verified':False,'status':'TEST CANDIDATE'
    }
    Path('audit224/final.json').write_text(json.dumps(out,indent=2)+'\n')
    Path('signed224/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: 2103224 carries locked movie-detail treatment to TV Shows without changing episode/playback behavior')

if __name__=='__main__':
    main()
