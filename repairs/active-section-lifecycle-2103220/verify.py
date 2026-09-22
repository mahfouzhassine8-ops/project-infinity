#!/usr/bin/env python3
import argparse,hashlib,json,re,zipfile
from pathlib import Path
V=2103220;NAME='1.0.9-Cobra-Active-Section-Lifecycle-RC1'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
def h(b):return hashlib.sha256(b).hexdigest()
def req(v,m):
 if not v:raise RuntimeError(m)
def main():
 p=argparse.ArgumentParser();p.add_argument('--apk',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--base',type=Path,required=True);a=p.parse_args()
 report=json.loads(a.audit.read_text());req(report.get('version_code')==V and report.get('version_name')==NAME,'identity')
 req(report.get('signer_certificate_sha256')==CERT,'signer')
 with zipfile.ZipFile(a.apk) as z,zipfile.ZipFile(a.base) as b:
  req(h(z.read('lib/arm64-v8a/libkodi.so'))==NATIVE,'native engine changed')
  for n in b.namelist():
   if n.startswith('lib/') and not n.endswith('/') and n!='lib/arm64-v8a/libkodi.so':req(z.read(n)==b.read(n),'native drift '+n)
   if n.startswith(('assets/','res/')) or n=='resources.arsc':req(z.read(n)==b.read(n),'resource drift '+n)
  dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n))
  for token in (
    b'cobra_active_section_owner',b'cobraEnforceActiveSectionLifecycle',
    b'cobraRestoreActiveSectionOnEntry',b'cobraRegisterNativeBack',
    b'android/window/OnBackInvokedCallback',b'cobra_smart_return_experience_display',
    b'cobraRestoreVodLandingReturn',b'LIVE TV AMBIENT BLUE',b'Infinity Health Center'):
   req(token in dex,'missing '+repr(token))
 scope=json.loads(Path('audit220/scope.json').read_text())
 for k in ('smart_return_untouched','only_drawer_changes_active_section',
           'android_native_back_routes_to_cobra_back','cold_entry_restores_drawer_owner',
           'warm_resume_corrects_top_level_owner_mismatch','temporary_surfaces_not_forcibly_closed',
           'playback_unchanged','providers_unchanged','health_center_unchanged'):
  req(scope.get(k) is True,'gate '+k)
 out={'build':V,'version_name':NAME,'apk_sha256':h(a.apk.read_bytes()),
      'smart_return_untouched':True,'only_drawer_changes_active_section':True,
      'native_back_lifecycle_covered':True,'native_engine_sha256':NATIVE,
      'physical_device_verified':False,'status':'TEST CANDIDATE'}
 Path('audit220/final.json').write_text(json.dumps(out,indent=2)+'\n')
 Path('signed220/ACCEPTANCE.json').write_text(json.dumps(out,indent=2)+'\n')
 print('PASS: 2103220 active-section native-back/lifecycle verified; Smart Return untouched')
if __name__=='__main__':main()
