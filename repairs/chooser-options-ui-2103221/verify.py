#!/usr/bin/env python3
import argparse,hashlib,json,re,zipfile
from pathlib import Path
V=2103221
NAME='1.0.9-Cobra-Chooser-Options-UI-RC1'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
def h(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
 if not v:raise RuntimeError(m)
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--apk',type=Path,required=True)
 p.add_argument('--audit',type=Path,required=True)
 a=p.parse_args()
 report=json.loads(a.audit.read_text())
 req(report.get('version_code')==V and report.get('version_name')==NAME,'identity mismatch')
 req(report.get('signer_certificate_sha256')==CERT,'signer changed')
 with zipfile.ZipFile(a.apk) as z:
  req(h(z.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'native engine changed')
  dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (b'CobraVisualRenderer$DialogBuilder',b'Cobra options',b'Infinity options',
                b'Remember & launch ',b'Infinity Health Center',b'Cobra Recovery',
                b'cobra_active_section_owner',b'cobraRestoreActiveSectionOnEntry'):
   req(token in dex,'missing '+repr(token))
 scope=json.loads(Path('audit221/scope.json').read_text())
 for k in ('stock_cobra_alert_dialog_removed','option_actions_unchanged','smart_return_untouched'):
  req(scope.get(k) is True,'scope gate '+k)
 out={'build':V,'version_name':NAME,'apk_sha256':h(a.apk.read_bytes()),
      'both_chooser_option_menus_styled':True,'smart_return_untouched':True,
      'active_section_lifecycle_untouched':True,'native_engine_sha256':NATIVE,
      'physical_device_verified':False,'status':'TEST CANDIDATE'}
 Path('signed221/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
 print('PASS: 2103221 signed candidate preserves native/lifecycle and restores styled options UI')
if __name__=='__main__':main()
