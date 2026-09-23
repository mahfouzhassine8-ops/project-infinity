#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

V=2103229
NAME='1.0.9-Cobra-MultiView-Stability-Fill-RC1'
PARENT_NAME='Infinity-1.0.9-Cobra-Device-Live-Fold-MultiView-RC1.apk'
PARENT_SHA='136ed5b2682fd9c13d54458194a3ac67f3b23b416229cc01c08093ee0f355cb9'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def h(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser();p.add_argument('--apk',type=Path,required=True);p.add_argument('--parent227',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True);p.add_argument('--scope',type=Path,required=True);p.add_argument('--source-audit',type=Path,required=True);a=p.parse_args()
    report=json.loads(a.audit.read_text());scope=json.loads(a.scope.read_text());source=json.loads(a.source_audit.read_text())
    req(report.get('version_code')==V and report.get('version_name')==NAME,'identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'signer mismatch')
    req(h(a.parent227.read_bytes())==PARENT_SHA,'not exact locked 2103227 accepted APK')
    req(scope.get('parent')==2103227,'wrong source parent')
    req(source.get('passed') is True,'source audit failed')
    req(source.get('fill_geometry_case_count',0)>=80,'Fill Screen geometry audit incomplete')
    st=scope.get('stability',{});ly=scope.get('layout',{})
    req(st.get('automatic_same_player_only') is True and st.get('automatic_player_recreation') is False,'automatic recovery ownership drift')
    req(st.get('max_reprepares_per_tile')==2 and st.get('healthy_peers_untouched') is True,'recovery bound/peer preservation drift')
    req(st.get('surface_recovery_owner_preserved') is True and st.get('live_ended_owner_preserved') is True,'existing recovery ownership drift')
    req(st.get('timeshift_excluded') is True,'timeshift entered Multi-View auto recovery')
    req(ly.get('fit_preserved') is True and ly.get('fill_screen') is True and ly.get('persistent') is True,'layout contract missing')
    req(ly.get('player_recreated') is False and ly.get('retune') is False and ly.get('audio_interrupted') is False,'layout mutated playback')
    req(ly.get('proportional') is True and ly.get('minimum_center_crop') is True and ly.get('safe_insets') is True,'Fill Screen geometry contract drift')

    with zipfile.ZipFile(a.apk) as z,zipfile.ZipFile(a.parent227) as pz:
        req(h(z.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'native engine changed')
        for n in pz.namelist():
            if n.startswith('lib/') and not n.endswith('/'):
                req(n in z.namelist() and z.read(n)==pz.read(n),'native drift '+n)
            elif n.startswith(('assets/','res/')) or n=='resources.arsc':
                req(n in z.namelist() and z.read(n)==pz.read(n),'resource/asset drift '+n)
            elif re.fullmatch(r'classes\d+\.dex',n):
                req(n in z.namelist() and z.read(n)==pz.read(n),'secondary DEX drift '+n)
        dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
            b'Multi-View layout',b'Fill Screen',b'cobra_multiview_layout_fill_screen',
            b'Reconnecting this screen',b'multiview-auto-recovery',b'auto-recovery',
            b'recovery-budget-reset',b'Search and add',b'Enlarge screen',b'Return to Multi-View',
            b'live-ended-recovery',b'Fold Fit',b'Fold Fill'
        ):
            req(token in dex,'compiled contract missing '+repr(token))

    out={
      'build':V,'version_name':NAME,'apk_sha256':h(a.apk.read_bytes()),
      'locked_parent_2103227_apk_sha256':PARENT_SHA,'native_engine_sha256':NATIVE,'signer':CERT,
      'resources_assets_identical_to_locked_2103227':True,'native_libraries_identical_to_locked_2103227':True,
      'secondary_dex_identical_to_locked_2103227':True,
      'multiview_auto_recovery_same_player':True,'multiview_auto_recovery_bounded':2,'multiview_healthy_peers_untouched':True,
      'multiview_surface_recovery_preserved':True,'multiview_live_ended_recovery_preserved':True,'timeshift_ownership_preserved':True,
      'multiview_fit_preserved':True,'multiview_fill_screen':True,'multiview_fill_proportional':True,
      'multiview_fill_minimum_center_crop':True,'multiview_fill_safe_insets':True,'multiview_fill_persistent':True,
      'multiview_layout_player_recreated':False,'multiview_layout_retune':False,'multiview_layout_audio_interrupted':False,
      'source_audit_passed':True,'fill_geometry_cases':source.get('fill_geometry_case_count'),
      'physical_device_verified':False,'status':'TEST CANDIDATE'
    }
    Path('audit229/final.json').write_text(json.dumps(out,indent=2)+'\n')
    Path('signed229/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: 2103229 APK preserves locked 2103227 payload and passes Multi-View stability/Fill audit')
if __name__=='__main__':main()
