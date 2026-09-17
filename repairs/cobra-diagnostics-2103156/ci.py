#!/usr/bin/env python3
"""Reconstruct the locked 2103155 recipe verbatim, then apply diagnostics-only 2103156."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,zipfile
BASE='4d1ed032df7e13fd27cc2170fc5e028f5059ec32'
APK='ee26af80797e0d881219314e16b06f86cbb6fd0a9667b0f661120c1844311834'
UI='88ada1fded508fede9368bf9dc4259c60220a4f067b9ba5ae2b45ffdb6b2a81a'
JAVA='42b36566929293ea8a3848e1ef099b736dfdbd09842d5cd98d73d6b30a5ba1e3'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
OLD='1.0.9-Cobra-Adaptive-Views-EPG-Repair-RC1'
NEW='1.0.9-Cobra-Diagnostics-Audit-RC1'
ROOT=Path('audit-delta/repairs/cobra-diagnostics-2103156')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(*args):subprocess.run(list(args),check=True)
def require(ok,message):
 if not ok:raise RuntimeError(message)
def reconstruct():
 import yaml
 require(subprocess.check_output(['git','-C','refinement-delta','rev-parse','HEAD']).decode().strip()==BASE,'Immutable delta checkout drift')
 baseline=Path('baseline155/signed-candidate/Infinity-'+OLD+'.apk')
 ui=Path('baseline155/ui-package/Infinity-Cobra-UI-1.3.9.zip')
 require(sha(baseline)==APK,'Wrong locked APK');require(sha(ui)==UI,'Wrong locked UI ZIP')
 # A rollback package exists BEFORE source changes; neither locked branch nor installed userdata is edited.
 rollback=Path('rollback156');rollback.mkdir(exist_ok=False)
 shutil.copy2(baseline,rollback/'Infinity-Cobra-2103155.apk');shutil.copy2(ui,rollback/ui.name)
 with (rollback/'2103155-exact-repository.zip').open('wb') as out:subprocess.run(['git','archive','--format=zip',BASE],stdout=out,check=True)
 (rollback/'README.txt').write_text('Locked 2103155 APK, UI, repository source and generated Android source. Device userdata NOT included. Do not uninstall/clear data to downgrade without a separate backup.\n')
 workflow=yaml.safe_load(Path('refinement-delta/.github/workflows/cobra-epg-repair-rc1-package.yml').read_text())
 for key,value in workflow['jobs']['package']['env'].items():require(os.environ.get(key)==str(value),'Missing/drifted original environment: '+key)
 names=['Validate reconstruction inputs and preserve pre-change source','Verify all exact APK and matching UI inputs before reconstruction','Reconstruct exact audited 2103154 source and presentation','Apply audited EPG repair and promote only Android shell to 2103155','Package and verify exact matching UI 1.3.9']
 steps={s.get('name'):s for s in workflow['jobs']['package']['steps']}
 for name in names:
  print('::group::'+name,flush=True);run('bash','-e','-u','-o','pipefail','-c',steps[name]['run']);print('::endgroup::',flush=True)
 require(sha(Path('kodi')/REL)==JAVA,'2103155 generated Activity does not match locked artifact')
 receipt=json.loads(Path('engine/background-resume-source.json').read_text())
 original=json.loads(Path('baseline155/signed-candidate/background-resume-source.json').read_text())
 require(receipt['version_code']==2103155,'Wrong reconstructed version')
 for name,row in original['files'].items():require(sha(Path('kodi')/name)==row['after'],'Locked source mismatch: '+name)
 shutil.copy2(Path('kodi')/REL,rollback/'2103155-activity.java.in')
 shutil.copy2('engine/background-resume-source.json',rollback/'2103155-source-receipt.json')
 with zipfile.ZipFile(rollback/'2103155-generated-android-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for p in sorted(Path('kodi/tools/android/packaging').rglob('*')):
   if p.is_file():archive.write(p,str(p.relative_to('kodi')))
  archive.write('kodi/cmake/scripts/android/Install.cmake','cmake/scripts/android/Install.cmake')
 shutil.copy2('engine/native-before.patch',rollback/'protected-native-source.patch')
 (rollback/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(rollback.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
 print('PASS: full locked 2103155 source/receipt reproduced; exact rollback preserved')
def promote():
 require(sha(Path('kodi')/REL)!=JAVA,'Diagnostics patch missing')
 for name,old,new,count in [('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103155','versionCode 2103156',1),('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"',1),('scripts/infinity_background_resume.py','VERSION_CODE = 2103155','VERSION_CODE = 2103156',1),('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'",1)]:
  p=Path(name);text=p.read_text();require(text.count(old)==count,'Version promotion preimage mismatch: '+name);p.write_text(text.replace(old,new,count))
 p=Path('scripts/package_background_resume.py');text=p.read_text();require('Infinity-'+OLD in text,'Packager identity mismatch');p.write_text(text.replace('Infinity-'+OLD,'Infinity-'+NEW))
 p=Path('engine/background-resume-source.json');data=json.loads(p.read_text())
 data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
 data.update(version_code=2103156,version_name=NEW,locked_parent=2103155,source_parent=2103155,source_parent_locked=True,candidate_locked=False,diagnostic_export=True,device_playback_verified=False)
 p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 with Path('engine/native-after-2103156.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
 require(Path('engine/native-before.patch').read_bytes()==Path('engine/native-after-2103156.patch').read_bytes(),'Native source delta changed')
 print('PASS: version 2103156, source receipts updated, protected native delta unchanged')
def verify():
 apk=Path('signed156/Infinity-'+NEW+'.apk');baseline=Path('baseline155/signed-candidate/Infinity-'+OLD+'.apk')
 with zipfile.ZipFile(apk) as new,zipfile.ZipFile(baseline) as old:
  names={n for n in old.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')}
  require(names=={n for n in new.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')},'Native/asset inventory drift')
  for name in names:require(new.read(name)==old.read(name),'Protected bytes changed: '+name)
  dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
  for token in (b'CobraDiagnosticArchive',b'InfinityCobraDiagnostics',b'EXPORT CRASH & DIAGNOSTICS ZIP',b'android.intent.action.CREATE_DOCUMENT',b'CobraModeLayout',b'CobraBroadcastRow',b'cobraEpgSnapshotFile'):
   require(token in dex,'Runtime contract absent: '+repr(token))
  for token in (b'RuntimeTest',b'ArchiveTest',b'CobraModesUiTest'):require(token not in dex,'Test code entered APK: '+repr(token))
 report=json.loads(Path('signed156/background-resume-apk-audit.json').read_text())
 require(report['version_code']==2103156 and report['native_recompiled'] is False,'APK audit identity mismatch')
 require(report['signer_certificate_sha256']=='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7','Production signer mismatch')
 require(report['apk_sha256']==sha(apk),'APK hash receipt mismatch')
 # Deliver exactly the already locked matching UI, not a stale reconstruction theme or a new skin.
 shutil.copy2('baseline155/ui-package/Infinity-Cobra-UI-1.3.9.zip','signed156/Infinity-Cobra-UI-1.3.9.zip')
 shutil.copy2(ROOT/'AUDIT.md','signed156/AUDIT-AND-DEVICE-CHECKS.md')
 acceptance={'build':2103156,'source_parent':2103155,'parent_commit':BASE,'parent_apk_sha256':APK,'apk_sha256':sha(apk),'native_recompiled':False,'native_and_asset_entries_identical_to_locked_2103155':len(names),'matching_ui_version':'1.3.9','matching_ui_sha256':UI,'candidate_locked':False,'real_provider_playback_verified':False,'physical_saf_destination_verified':False,'android_visual_rendering':'not rerun; independent branch validation is not silently adopted'}
 Path('signed156/ACCEPTANCE.json').write_text(json.dumps(acceptance,indent=2)+'\n')
 Path('signed156/SHA256SUMS').write_text(sha(apk)+'  '+apk.name+'\n'+UI+'  Infinity-Cobra-UI-1.3.9.zip\n')
 print('PASS: signed 2103156 diagnostics candidate; exact 2103155 native and asset bytes preserved')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['reconstruct','promote','verify']);a=p.parse_args();globals()[a.phase]()
