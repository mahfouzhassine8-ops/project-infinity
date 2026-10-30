"""File entry point: emulator action executes each script line separately."""
import argparse,hashlib,json,os,shutil,zipfile
from pathlib import Path
from android_probe import probe

def reuse_icon_evidence(out,receipt):
 """Reuse reviewed native icon frames only for these exact signed bytes.

 This records their original run and launcher limitation, never a fresh PASS.
 """
 base=Path(__file__).parent/'results/runtime/candidate31-first-actions'
 metadata=json.loads((base/'EVIDENCE.json').read_text())
 review=json.loads((base/'VISUAL-REVIEW.json').read_text())
 assert receipt['versionCode']==metadata['signed_versionCode']==2103431
 assert receipt['source']==metadata['signed_source'],'Retained icon source mismatch'
 assert receipt['signed_apk_sha256']==metadata['signed_APK_sha256']==review['APK_sha256'],'Retained icon APK mismatch'
 assert metadata['run']==review['run']==40973858059
 assert review['AppInfo_light']=='ORIGINAL_EMBLEM_BLACK_ON_WHITE'
 assert review['AppInfo_dark']=='ORIGINAL_NAVY_CYAN'
 assert review['PixelLauncher_AllApps_after_dark_switch']=='RETAINED_LIGHT_BITMAP_DESPITE_DARK_FRAMEWORK_AND_APPINFO'
 files=['icon-surfaces/OUTCOME.json','icon-surfaces/light/Settings-AppInfo-1.png',
  'icon-surfaces/light/Settings-AppInfo-2.png','icon-surfaces/light/AllApps-key-1.png',
  'icon-surfaces/dark/Settings-AppInfo-1.png','icon-surfaces/dark/AllApps-key-1.png']
 raw=json.loads((base/'icon-surfaces/OUTCOME.json').read_text())
 assert raw['receipt_apk_sha256']==receipt['signed_apk_sha256'] and raw['versionCode']==2103431
 hashes={}
 for name in files:
  content=(base/name).read_bytes();digest=hashlib.sha256(content).hexdigest()
  assert digest==metadata['files'][name]['sha256'],name
  if name.endswith('.png'):assert digest==review['reviewed_file_SHA256'][name],name
  hashes[name]=digest
 # Every byte is checked before copying any evidence. Output cannot mask new UI results.
 out.mkdir(parents=True,exist_ok=False)
 for name in files+['EVIDENCE.json','VISUAL-REVIEW.json']:
  target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,target)
 result={'status':'REUSED_PREVIOUS_EXACT_SIGNED_APK_ICON_EVIDENCE; NOT_RERUN',
  'run':metadata['run'],'APK_sha256':receipt['signed_apk_sha256'],
  'source':receipt['source'],'verified_file_SHA256':hashes,
  'AppInfo_light':review['AppInfo_light'],'AppInfo_dark':review['AppInfo_dark'],
  'PixelLauncher_after_dark_switch':review['PixelLauncher_AllApps_after_dark_switch'],
  'Samsung_Finder_suggestions':'NOT_VERIFIED','physical_Fold':'NOT_RUN'}
 (out/'REUSE.json').write_text(json.dumps(result,indent=2)+'\n')
 return result

def main(signed,out,signature):
 files=list(signed.glob('Infinity-*-Combined-Original-Signer.apk'));assert len(files)==1
 receipt=json.loads((signed/'BUILD-RECEIPT.json').read_text());assert receipt['versionCode'] in (2103427,2103428,2103429,2103430,2103431)
 assert 'Signer #1 certificate SHA-256 digest: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7' in signature.read_text()
 retained_icons=None
 if receipt['versionCode']==2103431:
  retained_icons=reuse_icon_evidence(out.parent/'retained-icon-evidence',receipt)
 probe(files[0],out,receipt['signed_apk_sha256'])
 if receipt['versionCode']==2103431:
  # The exact signed431 icon frames were already independently reviewed.
  # Keep their original failed-run binding and observed launcher-cache limit.
  with zipfile.ZipFile(files[0]) as apk:
   native_paths={name for name in apk.namelist() if name.startswith('lib/arm64-v8a/') and name.endswith('.so')}
  from build_native_button_probe import build
  build_dir=out.parent.parent/'runtime-native-button'
  build(build_dir,Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0/lib/d8.jar')
  native_evidence=out.parent/'native-agent';native_evidence.mkdir(exist_ok=False)
  for name in ('BUILD-RECEIPT.json','CobraNativeButtonProbe.jar'):
   shutil.copyfile(build_dir/name,native_evidence/name)
  from android_button_journey import journey
  try:
   journey(out.parent/'functional',native_evidence/'CobraNativeButtonProbe.jar',native_paths=native_paths)
  finally:
   combined={'signed_source':receipt['source'],'APK_sha256':receipt['signed_apk_sha256'],
             'versionCode':receipt['versionCode'],'retained_icon_evidence':retained_icons,
             'physical_Fold':'NOT_RUN','shutdown':'NOT_RUN'}
   for label,folder in (('button_actions','functional'),):
    path=out.parent/folder/'OUTCOME.json'
    combined[label]=json.loads(path.read_text()) if path.is_file() else 'NOT_COMPLETED'
   (out.parent/'P0-OBSERVATIONS.json').write_text(json.dumps(combined,indent=2)+'\n')
 elif receipt['versionCode']>=2103428:
  from android_candidate_journey import journey
  journey(out.parent/'functional')
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('signed','out','signature'):p.add_argument('--'+n,type=Path,required=True)
 main(**vars(p.parse_args()))
