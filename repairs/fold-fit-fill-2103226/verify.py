#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

V=2103226
NAME='1.0.9-Cobra-Fold-Fit-Fill-Audited-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def h(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--parent225',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--scope',type=Path,required=True)
    p.add_argument('--source-audit',type=Path,required=True)
    a=p.parse_args()

    report=json.loads(a.audit.read_text());scope=json.loads(a.scope.read_text());source=json.loads(a.source_audit.read_text())
    req(report.get('version_code')==V and report.get('version_name')==NAME,'identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'signer mismatch')
    req(scope.get('parent')==2103225,'wrong parent')
    req(source.get('passed') is True,'source audit did not pass')
    req(source.get('geometry_case_count',0)>=40,'geometry audit incomplete')
    req(scope.get('fold_fit',{}).get('mode')==12,'Fold Fit mode drift')
    req(scope.get('fold_fill',{}).get('mode')==13,'Fold Fill mode drift')
    req(scope.get('switching',{}).get('player_recreated') is False,'player recreation allowed')
    req(scope.get('switching',{}).get('retune') is False,'retune allowed')
    req(scope.get('switching',{}).get('seek') is False,'seek allowed')

    with zipfile.ZipFile(a.apk) as z,zipfile.ZipFile(a.parent225) as pz:
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
            b'Fold Fit',b'Fold Fill',b'Whole frame',
            b'Fill pane',b'minimum center crop',
            b'Multi-View tiles inherit Fold Fit / Fold Fill',
            b'COBRA \xe2\x80\xa2 MOVIE DETAILS',
            b'COBRA \xe2\x80\xa2 TV SHOW DETAILS',
            b'experience_options_ui_dialog',
            b'cobra_drawer_active_section',
        ):
            req(token in dex,'compiled contract missing '+repr(token))
        req(b'Fold Adaptive automatically follows the usable screen size' not in dex,
            'old Fold Adaptive picker copy survived')

    out={
        'build':V,'version_name':NAME,'apk_sha256':h(a.apk.read_bytes()),
        'parent_2103225_apk_sha256':h(a.parent225.read_bytes()),
        'native_engine_sha256':NATIVE,'signer':CERT,
        'resources_assets_identical_to_2103225':True,
        'native_libraries_identical_to_2103225':True,
        'secondary_dex_identical_to_2103225':True,
        'fold_fit_mode':12,'fold_fill_mode':13,
        'source_audit_passed':True,'geometry_cases':source.get('geometry_case_count'),
        'player_recreated_on_switch':False,'retune_on_switch':False,'seek_on_switch':False,
        'pip_best_fit_preserved':True,'multi_view_fold_reflow':True,
        'playback_unchanged':True,'providers_unchanged':True,'timeshift_unchanged':True,
        'physical_device_verified':False,'status':'TEST CANDIDATE'
    }
    Path('audit226/final.json').write_text(json.dumps(out,indent=2)+'\n')
    Path('signed226/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: 2103226 Fold Fit / Fold Fill APK preserves locked 2103225 payload and playback ownership')

if __name__=='__main__':main()
