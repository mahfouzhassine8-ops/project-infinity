"""Selected lock application integration; disposable signing only, never an owner APK."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib, importlib.util, json, os, shutil, subprocess, sys, urllib.request

HERE=Path(__file__).resolve().parent
LOCK=HERE.parent
REPAIR=LOCK.parent
ROOT=REPAIR.parents[1]
REPO='mahfouzhassine8-ops/project-infinity'
BASE='f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28'
NATIVE=json.loads((HERE/'NATIVE.json').read_text())
ENGINE=NATIVE['engine_sha256']
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
INPUTS={
 'baseline':(14189813969,43785765772,'92bef1bcf056abf58d6754354173565e56f907ac','936e9b52a1880d3412bc86ad4a594145f9927a7dba7b2243a88eb3cea26fb9b2'),
 'native':(NATIVE['artifact'],NATIVE['run'],NATIVE['source'],NATIVE['archive_sha256'])}

def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def zhash(z,n):
 with z.open(n) as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(args):
 result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=900)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 return result.stdout+result.stderr
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path); value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def verify_native_proofs(z):
 def read(leaf):
  names=[name for name in z.namelist() if Path(name).name==leaf];assert len(names)==1,leaf
  raw=z.read(names[0]);assert hashlib.sha256(raw).hexdigest()==NATIVE['proof_sha256'][leaf],leaf
  (ROOT/'lock-app-work/evidence'/leaf).write_bytes(raw)
  return json.loads(raw)
 arm=read('ARM64.json');source=read('SOURCE-PRESERVATION.json');abi=read('ABI-COMPARISON.json')
 baseline=json.loads((REPAIR/'BASELINE.json').read_text())
 assert arm['status']=='PASS_FULL_ARM64_LINK_AND_EXACT502_ABI' and arm['native_sha256']==ENGINE
 assert arm['source']==source['source']==NATIVE['source']
 assert arm['selected_test']=='lock_and_observer_lifetime_full_arm64_compile_link_exact502_abi'
 assert arm['reviewed_file_count']==source['candidate_source_count']==9418
 assert arm['unchanged_original_native_sources']==source['unchanged_native_files']==9408
 assert source['exact_baseline_source_count']==9414
 assert arm['baseline_native_sha256']==source['baseline_native_sha256']==abi['baseline_native_sha256']==baseline['native_sha256']
 assert source['status']=='PASS_EXACT502_PREIMAGE_AND_TEN_REVIEWED_LOCK_OBSERVER_FILES'
 ledger=json.loads((REPAIR/'PRESERVATION.json').read_text())
 entries=[entry for entry in ledger['authorized_source_overlays'] if 'native_path' in entry]
 assert len(entries)==len(source['changed'])==10
 assert {entry['native_path'] for entry in entries}==set(source['changed'])
 for entry in entries:
  assert source['changed'][entry['native_path']]=={'before':entry['before_sha256'],'after':entry['candidate_source_sha256']}
  assert digest(REPAIR/entry['path'])==entry['candidate_source_sha256']
 assert abi['added']==abi['removed']==[] and abi['dependencies_before']==abi['dependencies_after']
 assert abi['version_definitions_before']==abi['version_definitions_after']
 assert arm['exported_interfaces_preserved']==136120 and arm['version_definitions_preserved'] is True
 assert arm['lock_bridge_linked'] is True and len(arm['dependencies'])==11

class SafeRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  result=super().redirect_request(req,fp,code,msg,headers,newurl)
  if result is not None:result.remove_header('Authorization')
  return result

def artifact(work,label):
 aid,rid,source,expected=INPUTS[label]
 api=lambda path:json.loads(run(['gh','api','repos/'+REPO+'/'+path]))
 row=api('actions/artifacts/'+str(aid)); parent=api('actions/runs/'+str(rid))
 assert not row['expired'] and row['workflow_run']['id']==rid and row['digest']=='sha256:'+expected
 assert parent['conclusion']=='success' and parent['head_sha']==source
 archive=work/(label+'.zip')
 req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(aid)+'/zip',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'})
 with urllib.request.build_opener(SafeRedirect()).open(req,timeout=90) as response,archive.open('wb') as dest:shutil.copyfileobj(response,dest,2*1024*1024)
 assert digest(archive)==expected,'ARTIFACT_DIGEST_'+label
 wanted=BASE if label=='baseline' else ENGINE
 suffix='.apk' if label=='baseline' else 'libkodi.so'
 with ZipFile(archive) as z:
  if label=='native':verify_native_proofs(z)
  candidates=[n for n in z.namelist() if n.endswith(suffix) and zhash(z,n)==wanted]
  assert len(candidates)==1,'EXACT_MEMBER_'+label
  target=work/('baseline.apk' if label=='baseline' else 'libkodi.so')
  with z.open(candidates[0]) as src,target.open('wb') as dest:shutil.copyfileobj(src,dest,2*1024*1024)
 archive.unlink()
 return target,{'artifact':aid,'run':rid,'source':source,'archive_sha256':expected,'member':candidates[0],'member_sha256':wanted}

def toolchain(work,sdk):
 builder=module('lock_dex_builder',LOCK/'build_dex.py');tools=work/'tools';tools.mkdir()
 coords=[('org.antlr','ST4','4.0.8'),('org.codehaus.mojo','animal-sniffer-annotations','1.17'),('antlr','antlr','2.7.7'),('org.antlr','antlr','3.5.2'),('org.antlr','antlr-runtime','3.5.2'),('org.smali','baksmali','2.5.2'),('org.checkerframework','checker-compat-qual','2.5.2'),('org.smali','dexlib2','2.5.2'),('com.google.errorprone','error_prone_annotations','2.2.0'),('com.google.guava','failureaccess','1.0.1'),('com.google.guava','guava','27.1-android'),('com.google.j2objc','j2objc-annotations','1.1'),('com.beust','jcommander','1.64'),('com.google.code.findbugs','jsr305','3.0.2'),('com.google.guava','listenablefuture','9999.0-empty-to-avoid-conflict-with-guava'),('org.smali','smali','2.5.2'),('org.antlr','stringtemplate','3.2.1'),('org.smali','util','2.5.2')]
 for group,name,version in coords:
  leaf=name+'-'+version+'.jar';data=urllib.request.urlopen('https://repo.maven.apache.org/maven2/'+group.replace('.','/')+'/'+name+'/'+version+'/'+leaf,timeout=60).read()
  assert hashlib.sha256(data).hexdigest()==builder.TOOLS[leaf],leaf
  (tools/leaf).write_bytes(data)
 ecj=work/'ecj.jar';data=urllib.request.urlopen('https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.37.0/ecj-3.37.0.jar',timeout=60).read();assert hashlib.sha256(data).hexdigest()==builder.ECJ_SHA;ecj.write_bytes(data)
 return tools,ecj

def retained_classes3():
 receipt=LOCK/'DEX-CLASSES3-PRESERVATION.json'
 assert digest(receipt)=='827550a5f3b305a403d2ec511552d1156f30fb48e8a09cb35635984e79881d2a'
 previous=json.loads(receipt.read_bytes());target=Path(previous['output'])
 assert str(target)=='/dev/shm/infinity502-lock-dex/build-main-preserved' and not target.exists()
 expected={'classes3.dex':previous['outputs_sha256']['classes3.dex'],
           'ORIGINAL-CLASS-PRESERVATION.json':previous['classes3_preservation']['canonical_class_inventory_sha256']}
 with ZipFile(LOCK/'verified-classes3.zip') as z:
  assert len(z.infolist())==2 and set(z.namelist())==set(expected)
  target.mkdir(parents=True)
  for name,wanted in expected.items():
   entry=z.getinfo(name)
   assert entry.external_attr>>16==0o100600 and 0<entry.file_size<1024*1024
   raw=z.read(name);assert hashlib.sha256(raw).hexdigest()==wanted,name
   (target/name).write_bytes(raw)
 return receipt

def main():
 assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REPOSITORY')==REPO
 assert os.environ.get('GITHUB_REF')=='refs/heads/work/infinity-2103502-six-repairs-20261116'
 work=ROOT/'lock-app-work';work.mkdir();evidence=work/'evidence';evidence.mkdir()
 sdk=Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0'
 base,binding=artifact(work,'baseline');engine,engine_binding=artifact(work,'native')
 engine_binding.update(build_id=NATIVE['build_id'],build_id_status=NATIVE['build_id_status'])
 sig=run([sdk/'apksigner','verify','--verbose','--print-certs',base]);assert 'certificate SHA-256 digest: '+CERT in sig
 assert all(any(line.startswith('Verified using v'+str(v)+' scheme') and line.endswith(': true') for line in sig.splitlines()) for v in (1,2,3))
 # Reuse both exact reviewed DEX artifacts. No Java/D8/native recompilation.
 prior=LOCK/'DEX-BUILD-DIALOG-RETIREMENT.json'
 assert digest(prior)=='bdc5f558ef1790c1f64481be98aeb49453c9e124b4e9009e402ed290415b6958'
 verified=json.loads(prior.read_bytes());assert verified['baseline_apk_sha256']==BASE
 for name,expected_source in verified['input_sha256'].items():assert digest(LOCK/name)==expected_source,name
 receipt=retained_classes3();assert digest(receipt)==verified['classes3_reused_receipt_sha256']
 dex=Path(json.loads(receipt.read_bytes())['output'])
 archive=LOCK/'verified-classes7.zip';assert digest(archive)=='04124f0ecc0cf029d2e8a5798b36fee97dda0c162391da5799f3c8810ca73a9e'
 with ZipFile(archive) as z:
  assert z.namelist()==['classes7.dex']
  info=z.getinfo('classes7.dex');assert info.file_size<1024*1024 and info.external_attr>>16==0o100600
  target=dex/'classes7.dex';assert not target.exists();target.write_bytes(z.read(info))
 expected=verified['outputs_sha256']
 assert digest(dex/'classes3.dex')==expected['classes3.dex'] and digest(dex/'classes7.dex')==expected['classes7.dex']
 (evidence/'DEX.json').write_text(json.dumps({'status':'PASS_REUSED_EXACT_VERIFIED_DEX_NO_COMPILATION','original_receipt_sha256':digest(prior),'original_receipt':verified,'actual_outputs_sha256':{name:digest(dex/name) for name in ('classes3.dex','classes7.dex')}},indent=2)+'\n')
 stream=module('retained_streaming_stage',ROOT/'repairs/infinity-consolidated-2103500-20261115/stage_fast_qa.py')
 inventory=module('retained_inventory',ROOT/'repairs/dual-experience-isolation-2103420/inventory.py')
 updates={'lib/arm64-v8a/libkodi.so':engine,'classes3.dex':dex/'classes3.dex','classes7.dex':dex/'classes7.dex'}
 ledger=json.loads((REPAIR/'PRESERVATION.json').read_text())
 for entry in ledger['authorized_source_overlays']:
  if entry['path'].startswith('overlay/'):
   source=REPAIR/entry['path'];assert digest(source)==entry['candidate_source_sha256'];updates[entry['APK_member']]=source
 unsigned=work/'INTERNAL-LOCK-UNSIGNED.apk'
 with ZipFile(base) as old:
  old_names=set(inventory.validate_names(old))-inventory.SIGNATURE
  for entry in ledger['authorized_source_overlays']:
   if entry['path'].startswith('overlay/'):assert zhash(old,entry['APK_member'])==entry['before_sha256']
  assert 'classes7.dex' not in old_names
  with ZipFile(unsigned,'w',allowZip64=True) as out:
   for info in old.infolist():
    if info.filename not in inventory.SIGNATURE:stream.write_zip_member(out,info,old,updates.get(info.filename))
   info=ZipInfo('classes7.dex');info.compress_type=ZIP_DEFLATED
   stream.write_zip_member(out,info,old,updates['classes7.dex'])
  with ZipFile(unsigned) as new:
   assert set(inventory.validate_names(new))==old_names|{'classes7.dex'}
   changes={}
   for name in sorted(old_names|{'classes7.dex'}):
    before=zhash(old,name) if name in old_names else None; after=zhash(new,name)
    assert after==(digest(updates[name]) if name in updates else before),name
    if before!=after:changes[name]={'before':before,'after':after}
   assert set(changes)==set(updates)
 key=work/'DISPOSABLE-ONLY.jks'
 run(['keytool','-genkeypair','-keystore',key,'-storepass','lock-qa-only','-keypass','lock-qa-only','-alias','qa','-keyalg','RSA','-keysize','2048','-validity','2','-dname','CN=Disposable Infinity Lock Test, O=Not for owner installation'])
 aligned=work/'INTERNAL-LOCK-ALIGNED.apk';apk=work/'INTERNAL-LOCK-QA-NOT-FOR-OWNER.apk'
 run([sdk/'zipalign','-p','4',unsigned,aligned]);run([sdk/'apksigner','sign','--ks',key,'--ks-pass','pass:lock-qa-only','--out',apk,aligned]);run([sdk/'zipalign','-c','4',apk])
 qa_sig=run([sdk/'apksigner','verify','--verbose','--print-certs',apk]);assert CERT not in qa_sig
 assert all(any(line.startswith('Verified using v'+str(v)+' scheme') and line.endswith(': true') for line in qa_sig.splitlines()) for v in (2,3))
 qa_signature_members={'META-INF/QA.SF','META-INF/QA.RSA','META-INF/MANIFEST.MF'}
 with ZipFile(unsigned) as old,ZipFile(apk) as new:
  assert set(inventory.validate_names(new))-qa_signature_members==set(inventory.validate_names(old))
  for name in old.namelist():assert zhash(old,name)==zhash(new,name),name
 unsigned.unlink();aligned.unlink()
 report={'status':'PASS_DISPOSABLE_APPLICATION_ASSEMBLY_ONLY','source':os.environ['GITHUB_SHA'],'baseline':binding,'native':engine_binding,'apk_sha256':digest(apk),'changed_members':changes,'unchanged_members':len(old_names)-len(updates)+1,'Cobra':'UNCHANGED_PAYLOAD','module_trust':'Original detached signatures and trust keys unchanged','package':'com.projectinfinity.kodi','versionCode':2103502,'original_key':False,'owner_installer':False,'new_release_version':False,'actual_Android':'NOT_RUN','signature':qa_sig}
 (evidence/'ASSEMBLY.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['status'])

if __name__=='__main__':main()
