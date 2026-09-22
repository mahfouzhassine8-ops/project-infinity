#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path
VERSION=2103221
NAME='1.0.9-Cobra-Drawer-Owner-Surgical-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
DEX=re.compile(r'classes\\d*\\.dex$')
SIGN=re.compile(r'META-INF/(?:MANIFEST\\.MF|[^/]+\\.(?:SF|RSA|DSA|EC))$',re.I)
def hb(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
 if not v:raise RuntimeError(m)
def main():
 p=argparse.ArgumentParser();p.add_argument('--final',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);a=p.parse_args()
 report=json.loads(a.audit.read_text())
 req(report.get('version_code')==VERSION and report.get('version_name')==NAME,'identity mismatch')
 req(report.get('signer_certificate_sha256')==CERT,'signer changed')
 req(report.get('native_engine_sha256')==NATIVE,'native receipt changed')
 scope=json.loads(Path('audit221/scope.json').read_text())
 for k in ('only_drawer_changes_active_section','cold_and_warm_entry_restore_owner','smart_return_untouched','chooser_and_chooser_settings_untouched','cobra_settings_untouched','main_untouched'):
  req(scope.get(k) is True,'scope gate failed '+k)
 with zipfile.ZipFile(a.parent) as old,zipfile.ZipFile(a.final) as new:
  on=set(old.namelist());nn=set(new.namelist())
  req(on==nn,'APK member inventory changed')
  protected=[n for n in on if (n.startswith(('assets/','res/','lib/')) or n=='resources.arsc') and not n.endswith('/')]
  for n in protected:req(old.read(n)==new.read(n),'protected APK payload changed: '+n)
  req(hb(new.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'libkodi changed')
  joined=b''.join(new.read(n) for n in nn if DEX.fullmatch(n))
  for token in (b'cobra_active_section_owner',b'cobraSelectActiveSectionFromDrawer',b'cobraIsActiveSectionLanding',b'cobraReturnToActiveSection',b'cobraReconcileActiveSectionAfterEntry',b'cobra_smart_return_experience_display',b'Infinity Health Center',b'EXPERIENCE & DISPLAY'):
   req(token in joined,'missing runtime token '+repr(token))
  req(b'OnBackInvokedCallback' not in joined,'2103220 native-back experiment leaked into surgical build')
  changed=[n for n in on if old.read(n)!=new.read(n)]
  allowed=[n for n in changed if DEX.fullmatch(n) or n=='AndroidManifest.xml' or SIGN.fullmatch(n)]
  req(set(changed)==set(allowed),'unexpected parent APK change: '+repr(sorted(set(changed)-set(allowed))))
 result={'build':VERSION,'version_name':NAME,'apk_sha256':hb(a.final.read_bytes()),'parent_build':2103217,'parent_apk_sha256':hb(a.parent.read_bytes()),'native_engine_sha256':NATIVE,'smart_return_untouched':True,'chooser_settings_ui_untouched':True,'cobra_settings_ui_untouched':True,'only_drawer_changes_active_section':True,'physical_device_verified':False,'status':'TEST CANDIDATE'}
 Path('audit221/final.json').write_text(json.dumps(result,indent=2)+'\n')
 Path('signed221/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: 2103221 differs from 2103217 only in compiled Android code/version/signature; UI resources/native protected')
if __name__=='__main__':main()
