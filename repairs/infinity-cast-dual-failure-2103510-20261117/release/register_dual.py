"""Exact signed508 Cast-only owner preparation; original signer remains sole key holder."""
from pathlib import Path
from zipfile import ZipFile
import copy,hashlib,json,os,re,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent;TASK=HERE.parent;ROOT=HERE.parents[2]
PARENT='0a568903a95afac2c7085caee658aff7a490a6e6'
BASE_AUTH='cd682193dc78da29cfcfef83c5b0d43dec5b89a2'
BASE='8fd4d06d4a93b29764d4820bd6000795562411802fb52a402e1b3b2ddaa93ab0'
LIB='lib/arm64-v8a/libinfinitycastremux.so';DEX='classes6.dex';LABEL='assets/experience-component-updates.properties'
HELPERS=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'
for name in ('common_release.py','prepare_release.py','patch_cast_manifest.py'):
 p=HELPERS/name
 assert p.read_bytes()==subprocess.check_output(['git','show',PARENT+':'+str(p.relative_to(ROOT))]),'ORIGINAL_HELPER_CHANGED'
sys.path.insert(0,str(HELPERS));import common_release as c
import prepare_release as prior
from owner_bundle import rewrite,classes

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def request():
 c.context(True);r=c.load(HERE/'OWNER-REQUEST.json')
 assert r['baseline_APK_sha256']==BASE and r['accepted_pointer_updated'] is False and r['versions']=={'candidate':2103512,'recovery':2103513}
 assert r['generations']=={'candidate':97,'recovery':98} and r['parent_generation']==96
 assert c.sha(ROOT/c.WORKFLOW)==r['workflow_sha256']
 required={str((HERE/name).relative_to(ROOT)) for name in ('register_dual.py','owner_bundle.py','ORCHESTRATION-REVIEW.json','WORKFLOW-REVIEW.json','ROOTS-REVIEW.json')}
 required|={str((TASK/name).relative_to(ROOT)) for name in ('CAST-CLASS-DELTA.json','component_contract.py')}
 unsigned=('infinity-506-cast-component.yml','infinity-506-cast-hardware-pipeline.yml','infinity-506-cast-hardware-stage.yml')
 required|={'.github/workflows/'+n for n in unsigned}
 assert set(r['source_bindings'])==required,'EXACT_RELEASE_SOURCE_SET'
 for name,h in r['source_bindings'].items():assert c.sha(ROOT/name)==h,name
 policy='repairs/dual-experience-isolation-2103420/signer-policy.json'
 assert (ROOT/policy).read_bytes()==c.git('show',PARENT+':'+policy),'ORIGINAL_SIGNER_POLICY_UNCHANGED'
 assert c.load(ROOT/policy)['sole_original_key_workflow_id']==397702717
 orchestration=c.load(HERE/'ORCHESTRATION-REVIEW.json');assert orchestration['reviewer']=='Astra'
 for row in orchestration['workflows']:
  assert row['id'] in (421031076,421009620,421117469)
  raw=(ROOT/row['path']).read_bytes();assert c.digest(raw)==row['after_sha256']
  assert b'secrets.INFINITY_' not in raw and b'assemble.py sign' not in raw
 roots='repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'
 assert (ROOT/roots).read_bytes()==c.git('show',PARENT+':'+roots),'EXISTING_OWNERSHIP_ROOTS_UNCHANGED'
 rr=c.load(HERE/'ROOTS-REVIEW.json');assert rr['reviewer']=='Astra' and rr['before_sha256']==rr['after_sha256']==c.sha(ROOT/roots)
 old_workflow=c.git('show',PARENT+':'+c.WORKFLOW).decode();marker='sign-cast508-reader]';assert old_workflow.count(marker)==1
 prefix=old_workflow.replace(marker,'sign-cast508-reader, prepare-cast510-dual, sign-cast510-dual]')
 assert (ROOT/c.WORKFLOW).read_text().startswith(prefix),'ORIGINAL_SIGNER_JOBS_CHANGED'
 wf=c.load(HERE/'WORKFLOW-REVIEW.json');assert wf['reviewer']=='Astra' and wf['after_sha256']==r['workflow_sha256'] and wf['before_sha256']==c.digest(old_workflow.encode())
 review_raw=(HERE/'OWNER-REVIEW.json').read_bytes();assert c.digest(review_raw)==r['review_sha256'];review=json.loads(review_raw)
 assert review['reviewer']=='Astra' and review['status']=='PASS_CAST510_DUAL_RELEASE_GATE'
 keys=('baseline_APK_sha256','versions','generations','parent_authority_sha256','workflow_sha256','source_bindings','base','stage','owners','expected_changes','accepted_pointer_updated','known_limitations')
 assert c.digest(canonical({k:r[k] for k in keys}))==review['request_sha256']
 c.tools();return r

def preservation(base,apk,kind,r):
 inventory,cb,_,_,_=c.tools();version=r['versions'][kind]
 allowed={LIB,DEX,'AndroidManifest.xml',LABEL} if kind=='candidate' else {'AndroidManifest.xml',LABEL}
 assert set(r['expected_changes'][kind])==allowed
 with ZipFile(base) as before,ZipFile(apk) as after:
  names=set(inventory.validate_names(before))-set(inventory.SIGNATURE);assert set(inventory.validate_names(after))-set(inventory.SIGNATURE)==names
  changes={}
  for name in names:
   def digest(z):
    with z.open(name) as f:return hashlib.file_digest(f,'sha256').hexdigest()
   a,b=digest(before),digest(after)
   if a!=b:changes[name]={'before':a,'after':b}
  assert changes==r['expected_changes'][kind],'EXACT_SIGNED510_MEMBER_VECTOR'
  assert after.read('AndroidManifest.xml')==cb.set_version(before.read('AndroidManifest.xml'),version)
  assert after.read(LABEL)==('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
 return {'status':'PASS_EXACT_CAST510_DUAL_PRESERVATION','kind':kind,'baseline':2103510,'APK_sha256':c.sha(apk),'changes':changes,'unchanged_members':len(names)-len(changes),'Cobra':'BYTE_UNCHANGED','Kodi_other_DEX_modules_resources':'BYTE_UNCHANGED','owner_data':'NOT_ACCESSED','physical_hardware_TV':'PENDING_OWNER'}

def verify_class_delta(actual,baseline,delta,kind):
 before={k:v['sha256'] for k,v in baseline['payload'].items()};changed={k for k in before.keys()&actual.keys() if before[k]!=actual[k]};added=actual.keys()-before.keys();removed=before.keys()-actual.keys()
 allowed={'member:'+LIB,'member:'+LABEL} if kind=='candidate' else {'member:'+LABEL}
 expected_changed=allowed|({'class:'+n for n in delta['changed']} if kind=='candidate' else set())
 assert changed==expected_changed and set(added)==({'class:'+n for n in delta['added']} if kind=='candidate' else set()) and set(removed)==({'class:'+n for n in delta['removed']} if kind=='candidate' else set()),'EXACT_SYMBOLIC_AND_MEMBER_DELTA'
 payload=copy.deepcopy(baseline['payload'])
 if kind=='candidate':
  for n,row in delta['changed'].items():assert payload['class:'+n]=={'owner':'INFINITY','sha256':row['before']} and actual['class:'+n]==row['after']
  for n,h in delta['added'].items():assert actual['class:'+n]==h;payload['class:'+n]={'owner':'INFINITY','sha256':h}
  for n in delta['removed']:assert payload.pop('class:'+n)['owner']=='INFINITY'
 for n in changed:assert payload[n]['owner'] in ('INFINITY','CHOOSER_SHELL');payload[n]['sha256']=actual[n]
 assert {n:v['sha256'] for n,v in payload.items()}==actual
 return payload

def prepare():
 r=request();inventory,cb,ra,gate,_=c.tools();current=c.load(ROOT/c.AUTHORITY)
 assert current['generation']==96 and c.sha(ROOT/c.AUTHORITY)==r['parent_authority_sha256'],'REGISTRY_RACE'
 baseline=json.loads(c.git('show',BASE_AUTH+':'+c.AUTHORITY));assert baseline['generation']==95 and baseline['candidate_versionCode']==2103510
 base=c.unique(c.obtain(r['base'],'cast510-dual-release-base'),'Infinity-2103510-Combined-Original-Signer.apk');assert c.sha(base)==BASE;c.signature(base)
 staged=c.obtain(r['stage'],'cast510-dual-release-stage');proof=c.load(c.unique(staged,'STAGING.json'));assert proof['status']=='PASS_UNSIGNED_CAST510_DUAL_STAGE' and proof['baseline_APK_sha256']==BASE and proof['versions']==r['versions']
 original=c.obtain(r['owners'],'cast510-dual-release-owner-bundles')/'candidate/components';catalog_base=c.load(original/'catalog.json');assert catalog_base==baseline['bundle_catalog'],'SIGNED510_OWNER_BUNDLES_REQUIRED'
 out=ROOT/'cast510-dual-prepared';out.mkdir();previous=current;jars=c.jars();delta=c.load(TASK/'CAST-CLASS-DELTA.json')
 for kind,number in r['versions'].items():
  source=c.unique(staged,'Infinity-'+str(number)+'-UNSIGNED-NOT-INSTALLABLE.apk');assert c.sha(source)==proof['payloads'][kind]['APK_sha256'] and proof['payloads'][kind]['changes']==r['expected_changes'][kind]
  dest=out/kind;dest.mkdir();apk=dest/('Infinity-'+str(number)+'-UNSIGNED.apk');shutil.copyfile(source,apk);c.save(dest/'PRESERVATION.json',preservation(base,apk,kind,r))
  work=ROOT/('cast510-dual-inspect-'+kind);actual,version=gate.inspect_candidate(apk,jars,work);assert version==number;payload=verify_class_delta(actual,baseline,delta,kind)
  smali=classes(work);assert {n:h for n,(_,h) in smali.items()}=={n[6:]:h for n,h in actual.items() if n.startswith('class:')}
  components=dest/'components';components.mkdir();catalog=copy.deepcopy(catalog_base);catalog.update(source=os.environ['GITHUB_SHA'],release_approved=False);metas={}
  for owner,row in catalog['bundles'].items():
   src=original/row['file'];target=components/row['file'];cb.read_bundle(src,row)
   if owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):shutil.copyfile(src,target);meta=cb.read_bundle(target,row)
   else:
    owner_delta=delta if kind=='candidate' else {'changed':{},'added':{},'removed':{}}
    meta=rewrite(src,target,apk,owner,payload,baseline['payload'],smali,owner_delta,jars,ROOT/('cast510-dual-owner-'+kind+'-'+owner),number,os.environ['GITHUB_SHA'],inventory,cb,prior.copy_entry)
    row.update(sha256=c.sha(target),**{k:meta[k] for k in ('version','digest','approved_source')});cb.read_bundle(target,row)
   metas[owner]=meta
  (components/'catalog.json').write_bytes(inventory.canonical(catalog))
  proposed=copy.deepcopy(previous);proposed.update(generation=previous['generation']+1,candidate_versionCode=number,last_issued_versionCode=previous['candidate_versionCode'],previous_authority_sha256=inventory.digest(inventory.canonical(previous)),target_owners=['INFINITY','CHOOSER_SHELL'],update_kind='owner_update',payload=payload,bundle_catalog=catalog,experience_version_labels={'INFINITY':number,'COBRA':2103445},workflow_sha256=c.sha(ROOT/c.WORKFLOW));assert proposed['generation']==r['generations'][kind]
  for policy in ('repairs/dual-experience-isolation-2103420/signer-policy.json','repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'):proposed['source_files'][policy]=c.sha(ROOT/policy)
  for owner in proposed['target_owners']:
   proposed['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')};proposed['components'][owner]['revision']=previous['components'][owner]['revision']+1
   proposed['bundle_sources'][owner]={'run_id':int(os.environ['GITHUB_RUN_ID']),'build_source':os.environ['GITHUB_SHA'],'artifact':'Infinity510-Cast-Dual-Failure-Prepared-'+os.environ['GITHUB_RUN_ID'],'path':kind+'/components/'+owner+'.zip'}
  proposed['owner_update_evidence']={'owner':'INFINITY_CAST510_DUAL_'+kind.upper(),'producer_run':int(os.environ['GITHUB_RUN_ID']),'producer_source':os.environ['GITHUB_SHA'],'baseline_APK_sha256':BASE,'unsigned_sha256':c.sha(apk),'source_files':dict(r['source_bindings'],**{str((HERE/'OWNER-REQUEST.json').relative_to(ROOT)):c.sha(HERE/'OWNER-REQUEST.json')}),'known_limitations':r['known_limitations'],'Fold':'PENDING_OWNER','accepted_pointer_updated':False,'public_release':False,'verification_toolchain':dict(current['owner_update_evidence']['verification_toolchain'],unchanged_original_DEX=(kind=='recovery'),unchanged_non_Cast_DEX=True,content_baseline_APK_sha256=BASE)}
  ra.transition(previous,proposed,proposed['target_owners']);ra.verify_evidence(proposed,lambda p:(ROOT/p).read_bytes());ra.verify(proposed,actual,number,proposed['generation']);gate.validate_runtime_ownership(proposed,work)
  (dest/'AUTHORITY-PROPOSAL.json').write_bytes(inventory.canonical(proposed));previous=proposed
 c.save(out/'PREPARATION.json',{'status':'PASS_CAST510_DUAL_OWNER_PREPARATION','source':os.environ['GITHUB_SHA'],'baseline':BASE,'registry_written':False,'signed':False,'Kodi_or_APK_DEX_rebuilt':False,'actual_class_delta':{'changed':len(delta['changed']),'added':len(delta['added']),'removed':len(delta['removed'])}})

def selected():
 r=request();kind=r['active_kind'];assert kind in ('candidate','recovery');a=c.load(ROOT/c.AUTHORITY)
 assert a['generation']==r['generations'][kind] and a['candidate_versionCode']==r['versions'][kind]
 prepared_root=c.obtain(r['prepared'],'cast510-dual-registered-preparation');prepared=prepared_root/kind
 assert (prepared/'AUTHORITY-PROPOSAL.json').read_bytes()==(ROOT/c.AUTHORITY).read_bytes(),'EXACT_PREPARED_AUTHORITY_REQUIRED'
 apk=c.unique(prepared,'Infinity-'+str(r['versions'][kind])+'-UNSIGNED.apk');assert c.sha(apk)==a['owner_update_evidence']['unsigned_sha256']
 base=c.unique(c.obtain(r['base'],'cast510-dual-sign-baseline'),'Infinity-2103510-Combined-Original-Signer.apk');assert c.sha(base)==BASE;preservation(base,apk,kind,r);c.jars()
 with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:f.write('apk='+str(apk)+'\ngeneration='+str(a['generation'])+'\n')
def post():
 r=request();kind=r['active_kind'];out=ROOT/'cast510-dual-original-signed';apk=c.unique(out,'Infinity-'+str(r['versions'][kind])+'-Combined-Original-Signer.apk');c.signature(apk)
 base=c.unique(c.obtain(r['base'],'cast510-dual-sign-baseline'),'Infinity-2103510-Combined-Original-Signer.apk');assert c.sha(base)==BASE;c.save(out/'PRESERVATION.json',preservation(base,apk,kind,r));shutil.copyfile(ROOT/c.AUTHORITY,out/'release-authority.json')
if __name__=='__main__':{'prepare':prepare,'selected':selected,'post':post}[sys.argv[1]]()
