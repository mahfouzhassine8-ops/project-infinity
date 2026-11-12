"""Verify existing component output; never rebuild or change the baseline APK."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re,sys,subprocess
from dex_contract import Dex,class_contract

BASE='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def verify(apk,sdk,out):
 apk,sdk,out=map(Path,(apk,sdk,out));assert sha(apk)==BASE
 baseline={};original_members={}
 with ZipFile(apk) as z:
  for n in z.namelist():
   if re.fullmatch(r'classes\d*\.dex',n):
    data=z.read(n);baseline.update(Dex(data).classes);original_members[n]=hashlib.sha256(data).hexdigest()
 platform={}
 with ZipFile(sdk/'android.jar') as z:
  for n in z.namelist():
   if n.endswith('.class'):
    name,value=class_contract(z.read(n));platform[name]=value
 assert all(p.read_bytes()[:8]==b'dex\n035\0' for p in (out/'dex').glob('*.dex')), 'Original APK uses DEX035; do not raise its runtime requirement'
 outputs=[Dex(p.read_bytes()) for p in (out/'dex').glob('*.dex')]
 new=set().union(*(d.classes.keys() for d in outputs))
 overlap=sorted(new & baseline.keys())
 def resolves(owner,member,kind,seen=None):
  seen=set() if seen is None else seen
  if owner in seen:return False
  seen.add(owner);definition=baseline.get(owner) or platform.get(owner)
  if not definition:return False
  if tuple(member) in [tuple(x) for x in definition[kind]]:return True
  if member[0] in ('<init>','<clinit>'):return False
  return any(resolves(p,member,kind,seen) for p in [definition['parent']]+definition['interfaces'] if p)
 missing=[]
 old_policy=json.loads(subprocess.check_output(['git','show','e1ef672a6f24aed6c19a14ab96d2df6fe3380460:repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'],cwd=Path(__file__).resolve().parents[3]))
 def cobra_type(name):
  name=name.lstrip('[')
  if name.startswith('Lcom/projectinfinity/kodi/'):
   root=name[len('Lcom/projectinfinity/kodi/'):].split('$')[0].rstrip(';')
   return old_policy['project_roots'].get(root)=='COBRA'
  return any(name.startswith(prefix) and owner=='COBRA' for prefix,owner in old_policy['library_families'].items())
 cobra_refs=set();old_runtime_names=set()
 for d in outputs:
  for descriptor in d.types:
   if cobra_type(descriptor):cobra_refs.add(descriptor)
  old_runtime_names.update(s for s in d.strings if re.fullmatch(r'(?:okhttp3|okio|kotlin|com\.google\.common)\.[A-Za-z_$0-9.]+',s))
  for kind,refs in [('methods',d.methods),('fields',d.fields)]:
   for owner,name,signature in refs:
    if owner in baseline and not resolves(owner,(name,signature),kind):missing.append([kind,owner,name,signature])
 with ZipFile(out/'baseline-api-compile-only.jar') as z:
  reused=sorted({'L'+n[:-6]+';' for n in z.namelist() if n.endswith('.class')} & baseline.keys())
 identity=dict(schema=1,resource_package_id=128,sha256=sha(out/'resources.apk'))
 result=dict(schema=1,status='BLOCKED_PRESERVATION' if overlap or missing or cobra_refs or old_runtime_names else 'PASS_COMPONENT_COMPILE_AND_EXISTING_API_LINK_CONTRACT',
  baseline_APK_sha256=BASE,original_Dex_members=original_members,baseline_classes=len(baseline),new_classes=len(new),
  duplicate_classes=overlap,missing_baseline_APIs=missing,reused_existing_classes=reused,
  original_APK_modified=False,Android='NOT_RUN',receiver='NOT_RUN',installer=False,
  resources=identity,dex={p.name:sha(p) for p in (out/'dex').glob('*.dex')})
 result['provided_HTTP']='Private relocated HTTP/Kotlin/futures only; no Cobra-owned runtime imports or existing class replacements'
 result['Cobra_owned_type_references']=sorted(cobra_refs)
 result['old_HTTP_Kotlin_future_runtime_class_names']=sorted(old_runtime_names)
 result['private_resources']={p.relative_to(out/'private-resources').as_posix():sha(p) for p in (out/'private-resources').rglob('*') if p.is_file()}
 root=Path(__file__).resolve().parent
 inputs=json.loads((out/'BUILD-SOURCES.json').read_text())
 assert all(sha(root.parent/name)==wanted for name,wanted in inputs.items()), 'Build input changed after immutable input binding'
 result['build_inputs']=inputs
 compiled_sources=json.loads((out/'SOURCE-JAVA.json').read_text())
 current_sources={p.relative_to(root).as_posix():sha(p) for p in (root/'java').rglob('*.java')}
 assert compiled_sources==current_sources, 'Java source changed after immutable compilation snapshot; stale component cannot pass'
 result['feature_Java_sha256']=compiled_sources
 result['DEX_format']='035; baseline minimum Android API21 unchanged; Cast resources require API30 only when invoked'
 (out/'COMPONENT-RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 assert not overlap,('Cast would replace existing classes',overlap)
 assert not missing,('Existing APK lacks SDK-required API',missing)
 assert not cobra_refs,('Forbidden Cobra runtime import',sorted(cobra_refs))
 assert not old_runtime_names,('Reflective lookup could import Cobra runtime',sorted(old_runtime_names))
 (out/'RESOURCE-IDENTITY.json').write_text(json.dumps(identity,indent=2)+'\n')
 print(result['status'],'existing classes',len(baseline),'new classes',len(new),'reused',len(reused))
 return result
if __name__=='__main__':verify(*sys.argv[1:])
