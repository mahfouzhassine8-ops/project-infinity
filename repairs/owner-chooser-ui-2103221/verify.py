#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

VERSION=2103221
NAME='1.0.9-Cobra-Drawer-Owner-Chooser-UI-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
LIB='lib/arm64-v8a/libkodi.so'
def hb(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--scope',type=Path,required=True)
    a=p.parse_args()
    for path in (a.apk,a.audit,a.base,a.scope):req(path.is_file(),'Missing '+str(path))
    report=json.loads(a.audit.read_text())
    scope=json.loads(a.scope.read_text())
    req(report.get('version_code')==VERSION and report.get('version_name')==NAME,'APK identity mismatch')
    req(report.get('signer_certificate_sha256')==CERT,'Permanent signer changed')
    for key in ('smart_return_untouched','only_drawer_changes_active_section',
                'primary_fallback_routes_to_drawer_owner','back_from_owned_landing_backgrounds_task',
                'cobra_options_styled','infinity_options_styled',
                'stock_alert_dialog_removed_from_both_chooser_option_surfaces',
                'chooser_option_actions_unchanged','health_center_unchanged',
                'playback_unchanged','providers_unchanged','live_tv_blue_ambient_unchanged'):
        req(scope.get(key) is True,'scope gate failed '+key)

    with zipfile.ZipFile(a.apk) as z,zipfile.ZipFile(a.base) as b:
        req(hb(z.read(LIB))==NATIVE,'Native engine changed')
        native=[n for n in z.namelist() if n.startswith('lib/') and not n.endswith('/')]
        base_native=[n for n in b.namelist() if n.startswith('lib/') and not n.endswith('/')]
        req(set(native)==set(base_native),'Native inventory changed')
        for n in native:
            if n!=LIB:req(z.read(n)==b.read(n),'Non-target native drift '+n)
        for n in b.namelist():
            if n.startswith(('assets/','res/')) or n=='resources.arsc':
                req(z.read(n)==b.read(n),'Protected resource drift '+n)
        dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
            b'cobra_active_section_owner',
            b'cobraBackOutOfOwnedLanding',
            b'cobraShowLivePrimaryView',
            b'cobraSelectActiveSection',
            b'chooser.settings',
            b'CobraVisualRenderer$DialogBuilder',
            b'Infinity Health Center',
            b'Cobra Recovery',
            b'cobra_smart_return_experience_display',
            b'LIVE TV AMBIENT BLUE'
        ):
            req(token in dex,'Required runtime token missing '+repr(token))

    result={
      'build':VERSION,'version_name':NAME,'apk_sha256':hb(a.apk.read_bytes()),
      'native_engine_sha256':NATIVE,'signer_certificate_sha256':CERT,
      'smart_return_untouched':True,'only_drawer_changes_active_section':True,
      'chooser_options_styled_for_both':True,'physical_device_verified':False,
      'status':'TEST CANDIDATE - device acceptance required'
    }
    Path('audit221/final.json').write_text(json.dumps(result,indent=2)+'\n')
    Path('signed221/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: 2103221 signed candidate preserves native/resources and contains drawer-owner + styled chooser contracts')
if __name__=='__main__':main()
