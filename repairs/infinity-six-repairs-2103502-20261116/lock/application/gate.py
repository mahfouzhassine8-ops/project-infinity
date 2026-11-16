"""Exact reviewed-input gate for the selected disposable application journey."""
from pathlib import Path
import hashlib,json,os,subprocess

HERE=Path(__file__).resolve().parent
REPAIR=HERE.parent.parent
ROOT=REPAIR.parents[1]
CASE='actual_502_lock_stop_and_watched_actions'
REQUEST=HERE/'CI-APPLICATION.json'
REVIEW=HERE/'ASTRA-APPLICATION-REVIEW.json'

def digest(raw):return hashlib.sha256(raw).hexdigest()
def input_paths():
 fixed=[
  'BASELINE.json','PRESERVATION.json','SIGNED502-APK-MEMBER-HASHES.json',
  'lock/application/gate.py','lock/application/stage.py','lock/application/verify.py','lock/application/qa.py',
  'lock/application/SCOPE.json','lock/application/NATIVE.json',
  'crashes/watched_case.py','crashes/watched_probe.py','crashes/WATCHED-PUBLIC-FIXTURE.json',
  'crashes/WATCHED-SOURCE-REVIEW.json','crashes/OBSERVER-SOURCE.json',
  'crashes/ASTRA-NATIVE-RESULT-REVIEW.json',
  'lock/build_dex.py','lock/patch_main.py','lock/DEX-BUILD-SELECTION.json',
  'lock/DEX-BUILD-DIALOG-RETIREMENT.json','lock/NATIVE-BUILD-SCOPE.json',
  'lock/verified-classes3.zip','lock/DEX-CLASSES3-PRESERVATION.json',
  'lock/verified-classes7.zip','lock/DEX-BUILD-DIALOG-RETIREMENT.json',
  'lock/CI-NATIVE.json','lock/ASTRA-DEX-REVIEW.json','lock/android/ASTRA-ATTEMPT9-REVIEW.json',
 ]
 paths={REPAIR/name for name in fixed}
 # Entire reviewed overlay sets, including additive classes and native sources.
 for directory in ('overlay','lock/native','crashes/native','lock/java','lock/smali'):
  paths.update(path for path in (REPAIR/directory).rglob('*') if path.is_file())
 paths.update(ROOT/name for name in (
  '.github/workflows/infinity-502-lock-application.yml',
  'repairs/infinity-movies-continue-cast-2103486-20261112/cast/dex_contract.py',
  'repairs/infinity-consolidated-2103500-20261115/stage_fast_qa.py',
  'repairs/dual-experience-isolation-2103420/inventory.py',
  'repairs/infinity-final-closure-2103407/p0/manifest.py',
  'repairs/save-later-multiimage-20261023/android_feature_device.py',
 ))
 return {str(path.relative_to(ROOT)) for path in paths}

def validate(request):
 assert request['selected_case']==CASE and request['baseline']==2103502
 assert request['shutdown']=='NOT_SELECTED'
 assert request['original_signing'] is False and request['owner_installer'] is False
 assert set(request['inputs'])==input_paths(),'EXACT_REVIEWED_INPUT_SET_REQUIRED'
 for name,expected in request['inputs'].items():
  assert digest((ROOT/name).read_bytes())==expected,name
 pins=digest(json.dumps(request['inputs'],sort_keys=True,separators=(',',':')).encode())
 review=json.loads(REVIEW.read_bytes())
 assert digest(REVIEW.read_bytes())==request['independent_review_sha256']
 assert review['reviewer']=='Astra' and review['status']=='PASS_SELECTED_APPLICATION_SOURCE_REVIEW'
 assert review['reviewed_inputs_sha256']==pins and review['selected_case']==CASE
 native=json.loads((HERE/'NATIVE.json').read_bytes())
 assert native['status']=='VERIFIED_FULL_ARM64_SOURCE_AND_ABI'
 assert request['native']==native
 scope=json.loads((HERE/'SCOPE.json').read_bytes())
 assert scope['selected_case']==CASE and scope['shutdown']=='NOT_SELECTED'
 assert scope['original_signing'] is False and scope['owner_installer'] is False
 assert scope['native_build']==native['run']
 changed=subprocess.check_output(['git','diff','--name-only',request['source_commit'],os.environ['GITHUB_SHA']],cwd=ROOT,text=True).splitlines()
 assert changed==[str(REQUEST.relative_to(ROOT))],changed
 print('PASS_EXACT_SELECTED_APPLICATION_INPUTS_AND_SOURCE_REVIEW')

if __name__=='__main__':
 assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103502-six-repairs-20261116'
 validate(json.loads(REQUEST.read_bytes()))
