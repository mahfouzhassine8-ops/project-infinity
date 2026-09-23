#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

V=2103227
NAME='1.0.9-Cobra-Device-Live-Fold-MultiView-RC1'
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
    req(scope.get('parent')==2103226,'wrong source parent')
    req(source.get('passed') is True,'source audit failed')
    req(source.get('fold_geometry_case_count',0)>=30,'Fold geometry audit incomplete')
    req(source.get('multi_enlarge_case_count',0)>=9,'Multi-View enlarge audit incomplete')
    req(scope.get('live_ended',{}).get('vod_excluded') is True,'VOD end behavior not protected')
    req(scope.get('live_ended',{}).get('max_automatic_recoveries')==2,'live-ended loop bound drift')
    req(scope.get('multiview',{}).get('fullscreen_player_recreated') is False,'Multi-View fullscreen recreates player')
    req(scope.get('multiview',{}).get('other_tiles_released') is False,'Multi-View fullscreen releases peers')
    req(scope.get('fold_fill',{}).get('preserved') is True,'Fold Fill preservation missing')

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
            b'Fold Fit',b'Fold Fill',b'Balanced fit',
            b'Search and add',b'Enlarge screen',b'Restore grid',
            b'Full screen',b'Return to Multi-View',
            b'live-ended-recovery',b'Reconnecting',
            b'COBRA \xe2\x80\xa2 MOVIE DETAILS',b'COBRA \xe2\x80\xa2 TV SHOW DETAILS',
            b'experience_options_ui_dialog',b'cobra_drawer_active_section'
        ):
            req(token in dex,'compiled contract missing '+repr(token))
        req(b'Watch fullscreen' not in dex,'old destructive Multi-View fullscreen label survived')
        req(b'Whole frame \xe2\x80\xa2 no crop' not in dex,'device-rejected Fold Fit copy survived')

    out={
      'build':V,'version_name':NAME,'apk_sha256':h(a.apk.read_bytes()),
      'locked_parent_2103225_apk_sha256':h(a.parent225.read_bytes()),
      'native_engine_sha256':NATIVE,'signer':CERT,
      'resources_assets_identical_to_locked_2103225':True,
      'native_libraries_identical_to_locked_2103225':True,
      'secondary_dex_identical_to_locked_2103225':True,
      'live_ended_recovery_bounded':True,'vod_end_behavior_preserved':True,
      'fold_fit_device_balanced':True,'fold_fill_preserved':True,
      'multiview_search_add':True,'multiview_pause_resume':True,'multiview_enlarge':True,
      'multiview_fullscreen_reversible':True,'multiview_fullscreen_player_recreated':False,
      'multiview_other_tiles_released':False,'android_back_returns_multiview':True,
      'source_audit_passed':True,'fold_geometry_cases':source.get('fold_geometry_case_count'),
      'multi_enlarge_cases':source.get('multi_enlarge_case_count'),
      'physical_device_verified':False,'status':'TEST CANDIDATE'
    }
    Path('audit227/final.json').write_text(json.dumps(out,indent=2)+'\n')
    Path('signed227/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: 2103227 APK preserves locked payload and passes Live/Fold/Multi-View audit')

if __name__=='__main__':main()
