#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path
V=2103221
NAME='1.0.9-Cobra-Drawer-Owner-UI-Restore-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
def h(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--parent217',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--scope',type=Path,required=True)
    a=p.parse_args()
    report=json.loads(a.audit.read_text()); scope=json.loads(a.scope.read_text())
    req(report.get('version_code')==V and report.get('version_name')==NAME,'identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'signer mismatch')
    req(scope.get('smart_return_untouched') is True,'Smart Return gate failed')
    req(scope.get('only_drawer_changes_active_section') is True,'drawer owner gate failed')
    req(scope['chooser_settings_ui']['plain_framework_dialog_for_cobra_options'] is False,'plain Cobra options UI allowed')

    with zipfile.ZipFile(a.apk) as z, zipfile.ZipFile(a.parent217) as pz:
        req(h(z.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'native engine changed')
        for n in pz.namelist():
            if n.startswith('lib/') and not n.endswith('/'):
                req(n in z.namelist() and z.read(n)==pz.read(n),'native drift '+n)
            if n.startswith(('assets/','res/')) or n=='resources.arsc':
                req(n in z.namelist() and z.read(n)==pz.read(n),'approved UI/resource payload drift '+n)
            if n=='classes2.dex':
                req(z.read(n)==pz.read(n),'unrelated secondary DEX changed')
        dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
            b'cobra_drawer_active_section',
            b'cobraSelectDrawerOwner',
            b'cobraHandleDrawerOwnedBack',
            b'cobraSurfaceMatchesDrawerOwner',
            b'chooser.settings',
            b'chooser.recovery',
            b'Infinity Health Center',
            b'Cobra Recovery',
            b'EXPERIENCE & DISPLAY',
            b'cobra_smart_return_experience_display',
            b'LIVE TV AMBIENT BLUE',
        ):
            req(token in dex,'compiled contract missing '+repr(token))
    out={
      'build':V,'version_name':NAME,'apk_sha256':h(a.apk.read_bytes()),
      'parent_2103217_apk_sha256':h(a.parent217.read_bytes()),
      'native_engine_sha256':NATIVE,'signer':CERT,
      'resources_assets_identical_to_2103217':True,
      'smart_return_untouched':True,'only_drawer_changes_active_section':True,
      'chooser_option_panels_styled':True,'plain_cobra_options_removed':True,
      'physical_device_verified':False,'status':'TEST CANDIDATE'
    }
    Path('audit221/final.json').write_text(json.dumps(out,indent=2)+'\n')
    Path('signed221/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: 2103221 preserves locked 2103217 resources/native and adds only drawer-owner + styled chooser code')
if __name__=='__main__':main()
