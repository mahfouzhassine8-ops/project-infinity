"""Compile changed Cast component only. Reuse every non-Cast DEX and Kodi engine.

Use the established pinned private SDK/linker recipe; no dependency upgrade.
The output is a component, never an owner installer or a signing operation.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,os,re,subprocess,sys,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];CAST=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast';WORK=ROOT/'cast506-component-work'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity' and os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103506-receiver-compatibility-20261117'
 r=json.loads((HERE/'CI-COMPONENT.json').read_bytes())
 assert not r['engine_build'] and not r['owner_APK'] and not r['shutdown']
 for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
 assert subprocess.check_output(['git','diff','--name-only',r['source_commit'],os.environ['GITHUB_SHA']],text=True).splitlines()==[str((HERE/'CI-COMPONENT.json').relative_to(ROOT))]
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py';raw=subprocess.check_output(['git','show','21616dfa94bf7ca9ec52e40119edf95df5e64073:'+helper]);scope={'__file__':str(ROOT/helper),'__name__':'_retained_reader'};exec(compile(raw,str(ROOT/helper),'exec'),scope);c=types.SimpleNamespace(**scope)
 apk=c.unique(c.obtain(r['baseline'],'component506-authenticated-baseline'),'Infinity-2103506-Combined-Original-Signer.apk');assert sha(apk)==r['baseline']['APK_sha256']
 WORK.mkdir();tools=WORK/'tools';tools.mkdir();sdk=Path(os.environ['ANDROID_HOME']);bt=sdk/'build-tools/35.0.0'
 for n,target in {'android.jar':sdk/'platforms/android-34/android.jar','core-lambda-stubs.jar':bt/'core-lambda-stubs.jar','d8.jar':bt/'lib/d8.jar','aapt2':bt/'aapt2'}.items():(tools/n).symlink_to(target)
 pins={'android.jar':'6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad','aapt2':'d1096e11aba9c974644369ee3c50d239acac3f3428ffa928e5b9c14dfb7a57de','d8.jar':'305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5','core-lambda-stubs.jar':'c8a21e0e653227d1fce74bd547c9e7278e17c016c405aa8e1f6c313b192ade31'}
 for name,wanted in pins.items():assert sha(tools/name)==wanted,('Original Cast resource/compiler tool identity',name)
 subprocess.run(['python',str(CAST/'resolve_sdk.py'),str(WORK/'maven')],check=True)
 sys.path.insert(0,str(CAST));import audit_sdk_component
 audit_sdk_component.BASE=r['baseline']['APK_sha256'];recipe=CAST/'build_sdk_component.py';code=recipe.read_text();pin='fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c';assert pin in code;code=code.replace(pin,r['baseline']['APK_sha256']);sys.argv=[str(recipe),str(WORK),str(apk)];exec(compile(code,str(recipe),'exec'),{'__file__':str(recipe),'__name__':'__main__'})
 output=WORK/'component-reuse86';receipt=json.loads((output/'COMPONENT-RESULT.json').read_bytes());assert receipt['status']=='PASS_COMPONENT_COMPILE_AND_EXISTING_API_LINK_CONTRACT'
 from dex_contract import Dex
 new={}
 for p in (output/'dex').glob('*.dex'):new.update(Dex(p.read_bytes()).classes)
 original={};external=[];original_members={}
 with ZipFile(apk) as z:
  identity=json.loads(z.read('assets/infinity/cast/RESOURCE-IDENTITY.json'));assert identity['sha256']==sha(output/'resources.apk'),'Unchanged Cast resources required'
  for n in z.namelist():
   if re.fullmatch(r'classes\d*\.dex',n):
    data=z.read(n);original_members[n]=hashlib.sha256(data).hexdigest();d=Dex(data)
    if n=='classes6.dex':original=d.classes
    else:external.append(d)
 assert original and len(receipt['dex'])==1,'One changed Cast DEX only'
 missing=[];definitions={**new}
 for d in external:definitions.update(d.classes)
 def resolves(owner,name,signature,kind,seen=None):
  seen=set() if seen is None else seen
  if owner in seen:return False
  seen.add(owner);definition=definitions.get(owner)
  if not definition:return False
  if (name,signature) in [tuple(v) for v in definition[kind]]:return True
  if name in ('<init>','<clinit>'):return False
  return any(resolves(parent,name,signature,kind,seen) for parent in [definition['parent']]+definition['interfaces'] if parent)
 for d in external:
  for kind,refs in [('methods',d.methods),('fields',d.fields)]:
   for owner,name,signature in refs:
    if owner in original and not resolves(owner,name,signature,kind):missing.append([kind,owner,name,signature])
 assert not missing,('External APK API contract changed',missing)
 (output/'CAST506-COMPONENT.json').write_text(json.dumps({'status':'PASS_CHANGED_CAST_COMPONENT_AND_EXTERNAL_API_CONTRACT','foundation':r['baseline'],'source':os.environ['GITHUB_SHA'],'source_hashes':r['inputs'],'non_Cast_DEX_inputs_reused':original_members,'SDK_dependencies':'original pinned versions; private Cast component link only','Cobra_type_references':receipt['Cobra_owned_type_references'],'external_APIs_missing':missing,'original_class_count':len(original),'candidate_class_count':len(new),'classes_added':sorted(set(new)-set(original)),'classes_removed':sorted(set(original)-set(new)),'engine_rebuilt':False,'owner_installer':False},indent=2)+'\n')
if __name__=='__main__':main()
