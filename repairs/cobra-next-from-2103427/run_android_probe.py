"""File entry point: emulator action executes each script line separately."""
import argparse,json,os,shutil
from pathlib import Path
from android_probe import probe

def main(signed,out,signature):
 files=list(signed.glob('Infinity-*-Combined-Original-Signer.apk'));assert len(files)==1
 receipt=json.loads((signed/'BUILD-RECEIPT.json').read_text());assert receipt['versionCode'] in (2103427,2103428,2103429,2103430,2103431)
 assert 'Signer #1 certificate SHA-256 digest: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7' in signature.read_text()
 probe(files[0],out,receipt['signed_apk_sha256'])
 if receipt['versionCode']==2103431:
  from icon.android_observe import observe
  observe(out.parent/'icon',receipt['signed_apk_sha256'],receipt['versionCode'])
  from android_icon_surface_probe import observe as observe_surfaces
  surface_error=None
  try:
   observe_surfaces(out.parent/'icon-surfaces',receipt['signed_apk_sha256'],receipt['versionCode'])
  except Exception as exc:
   # Preserve an OS-surface error, but allow independent button presses only
   # after the observer verified return to the original empty Cobra screen.
   surface_outcome=out.parent/'icon-surfaces'/'OUTCOME.json'
   if not surface_outcome.is_file() or not json.loads(surface_outcome.read_text()).get('safe_empty_Cobra_for_independent_buttons'):
    raise
   surface_error=str(exc)
  from build_native_button_probe import build
  build_dir=out.parent.parent/'runtime-native-button'
  build(build_dir,Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0/lib/d8.jar')
  native_evidence=out.parent/'native-agent';native_evidence.mkdir(exist_ok=False)
  for name in ('BUILD-RECEIPT.json','CobraNativeButtonProbe.jar'):
   shutil.copyfile(build_dir/name,native_evidence/name)
  from android_button_journey import journey
  try:
   journey(out.parent/'functional',native_evidence/'CobraNativeButtonProbe.jar')
  finally:
   combined={'signed_source':receipt['source'],'APK_sha256':receipt['signed_apk_sha256'],
             'versionCode':receipt['versionCode'],'icon_surface_error':surface_error,
             'physical_Fold':'NOT_RUN','shutdown':'NOT_RUN'}
   for label,folder in (('framework_and_first_launcher','icon'),('native_icon_surfaces','icon-surfaces'),('button_actions','functional')):
    path=out.parent/folder/'OUTCOME.json'
    combined[label]=json.loads(path.read_text()) if path.is_file() else 'NOT_COMPLETED'
   (out.parent/'P0-OBSERVATIONS.json').write_text(json.dumps(combined,indent=2)+'\n')
  if surface_error:raise RuntimeError('Icon surface operation failed; independent button outcome retained: '+surface_error)
 elif receipt['versionCode']>=2103428:
  from android_candidate_journey import journey
  journey(out.parent/'functional')
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('signed','out','signature'):p.add_argument('--'+n,type=Path,required=True)
 main(**vars(p.parse_args()))
