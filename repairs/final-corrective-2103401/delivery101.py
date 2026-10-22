"""Full scoped native compilation, exact DEX/ZIP binding and permanent signature."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import argparse,copy,json,os,re,shutil,subprocess,tempfile
import components101 as c,native101 as n,dex101
import delivery98 as prior
CODE=2103401
NAME='1.0.9-Final-Corrections-TEST0011'
FILENAME='Infinity-2103401-Fold-Corrective-EXPERIMENTAL.apk'
ENGINE,RECORDER,CERT=prior.ENGINE,prior.RECORDER,prior.CERT
save=prior.save

def assemble(a):
 d,r,_=n.old_adapters();_,_,signer=d.adapters()
 c.require(all(os.environ.get(k) for k in d.KEYS),'all permanent signing secrets mandatory')
 producer=a.producer.resolve();checkpoint=producer/'checkpoint-build'
 parent=a.parent_dir/'Infinity-2103400-Fold-Corrective-EXPERIMENTAL.apk'
 original=c.read_parent(parent);final=c.components(original);ledger=c.ledger(original,final)
 c.require(not d.command(['git','-C',producer,'diff','--name-only']).strip(),'immutable producer changed')
 binding=json.loads((checkpoint/'FOLD101-NATIVE-BINDING.json').read_text());expected=json.loads((checkpoint/'FOLD101-NATIVE-SOURCE-MAP.json').read_text())
 c.require(binding['source_commit']==a.source_commit and set(binding['after'])==n.PATHS and binding['all_other_sources_byte_identical'],'native scope/provenance missing')
 c.require(len(expected)==9404 and all(c.digest(producer/'kodi'/p)==h for p,h in expected.items()),'compiler source changed')
 post=json.loads((checkpoint/'POST-BUILD-SOURCE-INVENTORY.json').read_text());c.require(post['reviewed_file_count']==9404 and not post['changed_or_missing_reviewed'],'postcompile inventory failed')
 proof=json.loads((checkpoint/'ENGINE-PROOF.json').read_text());engine=checkpoint/'libkodi.so';native=engine.read_bytes();engine_hash=c.sha(native)
 c.require(proof['source_commit']==a.source_commit and proof['complete_native_engine_compiled'] and proof['native_sha256']==engine_hash and proof['shutdown_policy']=='essential_first_process_exit_v1','full native provenance missing')
 for symbol in (b'Infinity.Resume.OriginalProvider',b'infinity_original_route',b'0.3.5.29'):
  c.require(symbol in native,'compiled correction absent '+repr(symbol))
 pins=json.loads(final[c.UI+'/CONTROLLER-PREIMAGES.json'])
 for pin in pins.values():c.require(pin.encode() in native,'controller source pin absent from native')
 dex=a.component/'component/classes.dex';dexproof=json.loads((a.component/'STARTUP-DEX-INTEGRATION.json').read_text());art=json.loads((a.component/'ART-COMPONENT-VERIFICATION.json').read_text())
 c.require(dexproof['source_commit']==a.source_commit and dexproof['source_apk_sha256']==c.PARENT and c.digest(dex)==dexproof['component_dex_sha256'],'wrong production DEX')
 c.require(dexproof['decoded_protected_instructions_identical'] and dexproof['fields']['encoded_values_and_presence_preserved'],'Cobra/DEX preservation failed')
 c.require(art['source_commit']==a.source_commit and art['passed'] and art['candidate_cases_passed']==45 and art['baseline_control_cases_passed']==1 and art['platform']['api']==37 and art['integrated_search_android']['passed'],'Android17 execution missing')
 for p,b in final.items():c.require((a.stage/p).read_bytes()==b,'component stage drift '+p)
 tools=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0';parent_signature=d.verify_signature(parent,tools)
 manifest=d.module('scoped100_manifest',c.ROOT/'repairs/critical-preview-2103376/manifest_patch.py')
 manifest.PARENT_CODE=2103400;manifest.CODE=CODE;manifest.PARENT_NAME='1.0.9-Three-Corrections-TEST0010';manifest.NAME=NAME
 out=a.out.resolve();c.require(not out.exists(),'output exists');out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.infinity-100-',dir=out.parent) as tmp:
  temp=Path(tmp);unsigned=temp/'unsigned.apk';signed=temp/FILENAME
  with ZipFile(parent) as z:
   old_engine=z.read(ENGINE);abi=signer.native_export_compatibility(old_engine,native)
   recorder=d.replace_recorder_field(z.read(RECORDER),c.sha(old_engine),engine_hash,signer.nativeidentity.elf_sections(z.read(RECORDER)))
   patched,edits=manifest.patch(z.read('AndroidManifest.xml'));c.require(len(edits)==2,'manifest scope changed')
   targets={'assets/addons/'+p:final[p] for p in ledger['changed']}
   targets.update({ENGINE:native,RECORDER:recorder,'classes.dex':dex.read_bytes(),'AndroidManifest.xml':patched})
   for code in range(2103395,2103402):targets['assets/infinity-'+str(code)+'-components.json']=c.evidence_manifest(final)
   with ZipFile(unsigned,'w',allowZip64=True) as result:
    for info in z.infolist():
     if not prior.SIGNATURE.fullmatch(info.filename):result.writestr(copy.copy(info),targets.get(info.filename,z.read(info)))
    for name in sorted(set(targets)-set(z.namelist())):result.writestr(name,targets[name],compress_type=ZIP_DEFLATED,compresslevel=9)
  prior.verify_delta(parent,unsigned,targets)
  subprocess.run(['bash',str(c.ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(signed)],check=True)
  signature=d.verify_signature(signed,tools);changed=prior.verify_delta(parent,signed,targets)
  badging=d.command([tools/'aapt','dump','badging',signed]);c.require("package: name='com.projectinfinity.kodi' versionCode='2103401'" in badging and 'application-debuggable' not in badging,'install-over manifest verification failed')
  with ZipFile(signed) as z:
   for addon,version in c.VERSIONS.items():
    filename=addon+'-'+version+'.zip';entries=sorted(n for n in z.namelist() if n.startswith('assets/addons/'+addon+'/') and not n.endswith('/'))
    with ZipFile(temp/filename,'w',compression=ZIP_DEFLATED,compresslevel=9) as component:
     for name in entries:component.writestr(name[14:],z.read(name))
    with ZipFile(temp/filename) as component:
     c.require(component.testzip() is None and set(component.namelist())=={n[14:] for n in entries} and all(component.read(n)==z.read('assets/addons/'+n) for n in component.namelist()),'ZIP/APK incompatibility '+addon)
  for entry in ledger['changed'].values():entry['regression_result']='CI VERIFIED: targeted source/identity/state tests; physical Fold NEEDS EVIDENCE'
  for p in n.PATHS:
   ledger.setdefault('native_changed',{})[p]=dict(original_sha256=binding['before'][p],new_sha256=binding['after'][p],corrective_reason='Add only exact CC29 controller fingerprints and version admission; all shutdown ownership checks and lifecycle guards retained',affected_runtime_behavior='Allow the corrected CC29 participant to use the existing verified persistence contract',regression_result='CI VERIFIED: full ARM64 compilation, targeted regression checks; physical Fold NEEDS EVIDENCE')
  receipt=dict(version_code=CODE,version_name=NAME,source_commit=a.source_commit,protected_commit=c.COMMIT,protected_apk_sha256=c.PARENT,apk_sha256=c.digest(signed),build_run=int(os.environ['GITHUB_RUN_ID']),build_url='https://github.com/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['GITHUB_RUN_ID'],native_sha256=engine_hash,native_source_count=9404,native_changed=sorted(n.PATHS),native_abi=abi,complete_native_engine_compiled=True,permanent_certificate_sha256=CERT,signed_permanently=True,matching_component_versions=c.VERSIONS,matching_zips_identical_to_apk=True,cobra_members_and_protected_class_definitions_identical=True,rails_unchanged=True,shutdown_policy='essential_first_process_exit_v1',essential_first_guards_weakened=False,apk_changed_members=changed,physical_fold_verified=False,actual_install_over_tested=False,final_lock=False)
  save(temp/'INFINITY-2103401-DELIVERY.json',receipt);save(temp/'CHANGED-FILE-MANIFEST.json',ledger)
  with ZipFile(parent) as oldzip,ZipFile(signed) as newzip:
   oldnames=set(oldzip.namelist());newnames=set(newzip.namelist());delta=[];identical=[]
   for name in sorted(oldnames|newnames):
    before=oldzip.read(name) if name in oldnames else None;after=newzip.read(name) if name in newnames else None
    if before==after:identical.append(dict(path=name,sha256=c.sha(after)));continue
    if name.startswith('assets/addons/'):workstream,why=c.reason(name[14:]);evidence='TARGETED-RESULTS.json; member/component integrity comparison'
    elif name=='classes.dex':workstream,why,evidence='3/binding','Only Search decorate and additive CC29 verifier; all other definitions retained','STARTUP-DEX-INTEGRATION.json; ART-COMPONENT-VERIFICATION.json'
    elif name==ENGINE:workstream,why,evidence='binding','Compile only the two additive exact CC29 owner admission inputs','FOLD101-NATIVE-BINDING.json; ENGINE-PROOF.json'
    elif name==RECORDER:workstream,why,evidence='packaging','Rebind the existing crash recorder to the exact compiled engine hash','Exact recorder field replacement and native export compatibility'
    elif name=='AndroidManifest.xml':workstream,why,evidence='packaging','Only install-over versionCode and versionName attributes','APK-BADGING.txt; exact two-field binary-manifest delta'
    elif prior.SIGNATURE.fullmatch(name):workstream,why,evidence='signing','Regenerated permanent signature for changed APK payload','FINAL-SIGNATURE.txt; original certificate equality'
    elif name.startswith('assets/infinity-') and name.endswith('-components.json'):workstream,why,evidence='binding','Exact installed component diagnostic fingerprints','COMPONENTS.json; member inventory'
    else:raise ValueError('Unattributed APK difference: '+name)
    delta.append(dict(path=name,original_sha256=c.sha(before) if before is not None else None,final_sha256=c.sha(after) if after is not None else None,workstream=workstream,reason=why,test_evidence=evidence))
   save(temp/'APK-DELTA-REPORT.json',dict(protected_apk_sha256=c.PARENT,final_apk_sha256=c.digest(signed),changed=delta,byte_identical_members=identical,removed_members=sorted(oldnames-newnames),signing_block='APK signing block is outside ZIP members; permanent certificate verified independently'))
   import csv
   with (temp/'APK-DELTA.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=['path','original_sha256','final_sha256','workstream','reason','test_evidence']);writer.writeheader();writer.writerows(delta)
  if (a.component/'visuals').is_dir():shutil.copytree(a.component/'visuals',temp/'visuals')
  for leaf in ('PERFORMANCE-HOST.json','PERSISTENCE-REGRESSIONS.log','PERSISTENCE-RESULTS.json'):
   if (a.component/leaf).is_file():shutil.copyfile(a.component/leaf,temp/leaf)
  historical=temp/'protected-2103400-evidence';historical.mkdir()
  for leaf in ('PASS-FAIL-REPORT.json','ART-COMPONENT-VERIFICATION.json','TARGETED-RESULTS.json','TARGETED-REGRESSIONS.log','INFINITY-2103400-DELIVERY.json','FINAL-SIGNATURE.txt'):
   shutil.copyfile(a.parent_dir/leaf,historical/leaf)

  tests=json.loads((a.component/'TARGETED-RESULTS.json').read_text());c.require(tests['passed'],'targeted tests failed');c.require(json.loads((a.component/'PERSISTENCE-RESULTS.json').read_text())['passed'],'persistence tests failed')
  report=dict(source_commit=a.source_commit,workstreams={str(i):dict(implementation='IMPLEMENTED',ci='CI VERIFIED',physical_fold='NEEDS EVIDENCE') for i in (1,2,3,4)},source_tests=tests,persistence_tests=json.loads((a.component/'PERSISTENCE-RESULTS.json').read_text()),android17=art,complete_arm64_compilation=True,protected_writer_guards_unchanged=True,whole_engine_close_and_reopen='NEEDS EVIDENCE',whole_package_termination='NEEDS EVIDENCE: separately classified',ambient_close_modes={m:'NEEDS EVIDENCE' for m in ('Off','Subtle','Immersive')},refinement=dict(status='AUDITED; corrections resolve demonstrated UI failures; no speculative runtime rewrites',performance='Host timings and call counts only; device frame-time measurements pending'),final_lock=False)
  save(temp/'PASS-FAIL-REPORT.json',report)
  (temp/'FINAL-SIGNATURE.txt').write_text(signature);(temp/'PARENT-SIGNATURE.txt').write_text(parent_signature);(temp/'APK-BADGING.txt').write_text(badging)
  for leaf in ('ENGINE-PROOF.json','FOLD101-NATIVE-BINDING.json'):shutil.copyfile(checkpoint/leaf,temp/leaf)
  for leaf in ('STARTUP-DEX-INTEGRATION.json','ART-COMPONENT-VERIFICATION.json','TARGETED-RESULTS.json','TARGETED-REGRESSIONS.log'):shutil.copyfile(a.component/leaf,temp/leaf)
  for leaf in ('INSTALLATION.txt','CORRECTIVE-ACCEPTANCE.md','FIVE-WORKSTREAMS.md','PHYSICAL-FOLD-CHECKLIST.md','STABILITY-PERFORMANCE.md','VISUAL-VERIFICATION.md','BASELINE.json','VISUAL-REFERENCES.json','SEREN-QUERY-CONTRACT.json'):shutil.copyfile(c.HERE/leaf,temp/leaf)
  with ZipFile(temp/'Infinity-2103401-Source-and-Build-Receipts.zip','w',compression=ZIP_DEFLATED,compresslevel=9) as archive:
   archive.writestr('SOURCE-COMMIT.txt',a.source_commit+'\n');archive.writestr('NATIVE-SOURCE-MAP.json',json.dumps(expected,indent=2,sort_keys=True)+'\n')
   for p in sorted(expected):archive.write(producer/'kodi'/p,'native/'+p)
   for p in sorted(c.HERE.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:archive.write(p,'corrective/'+p.relative_to(c.HERE).as_posix())
   for p,b in final.items():
    if p in ledger['changed']:archive.writestr('components/'+p,b)
   for p in temp.iterdir():
    if p.is_file() and p.suffix in ('.json','.txt','.log','.md'):archive.write(p,'receipts/'+p.name)
  save(temp/'COMPONENTS.json',{a:dict(version=v,file=a+'-'+v+'.zip',sha256=c.digest(temp/(a+'-'+v+'.zip'))) for a,v in c.VERSIONS.items()})
  unsigned.unlink();(temp/'SHA256SUMS').write_text(''.join(c.digest(p)+'  '+p.relative_to(temp).as_posix()+'\n' for p in sorted(temp.rglob('*')) if p.is_file()))
  os.rename(temp,out)
 print(json.dumps(receipt,indent=2,sort_keys=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['bind','assemble'])
 for k in ('producer','parent-dir','stage','component','out'):p.add_argument('--'+k,type=Path)
 p.add_argument('--source-commit',required=True);a=p.parse_args()
 if a.mode=='bind':print(json.dumps(n.bind(a.producer,a.parent_dir/'Infinity-2103400-Fold-Corrective-EXPERIMENTAL.apk',a.stage,a.source_commit),indent=2))
 else:assemble(a)
