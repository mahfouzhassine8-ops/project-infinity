"""Native-only504 owner preparation and original signing gate on canonical metadata.
Content comes exclusively from signed504 and the verified Cast artifact.
"""
from pathlib import Path
from zipfile import ZipFile
import copy,hashlib,json,os,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PARENT='7755b1ecb959492599c2ffab25e230fe2aebe7a2'
BASE_AUTH='80506277145dcd4bbd66da3eaa02d9c085c1b437'
BASE='ab9104471c729751d6127cc4dfc6e98d8bb4c916212c356ce9c0295b2a0c5234'
LIB='lib/arm64-v8a/libinfinitycastremux.so';LABEL='assets/experience-component-updates.properties'
HELPERS=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'
for name in ('common_release.py','prepare_release.py','patch_cast_manifest.py'):
 p=HELPERS/name
 assert p.read_bytes()==subprocess.check_output(['git','show',PARENT+':'+str(p.relative_to(ROOT))]),'ORIGINAL_HELPER_CHANGED'
sys.path.insert(0,str(HELPERS))
import common_release as c
import prepare_release as prior
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def request():
 c.context(True);r=c.load(HERE/'OWNER-REQUEST.json')
 assert r['baseline_APK_sha256']==BASE and r['accepted_pointer_updated'] is False
 assert set(r['versions'])=={'candidate','recovery'} and r['versions']['recovery']>r['versions']['candidate']>2103505
 assert c.sha(ROOT/c.WORKFLOW)==r['workflow_sha256']
 required={str((HERE/name).relative_to(ROOT)) for name in ('register_audio.py','stage.py','CATALOG-ROWS.json','CATALOG-REVIEW.json','WORKFLOW-REVIEW.json')}
 assert set(r['source_bindings'])==required,'EXACT_RELEASE_SOURCE_SET'
 for name,h in r['source_bindings'].items():assert c.sha(ROOT/name)==h,name
 policy='repairs/dual-experience-isolation-2103420/signer-policy.json'
 expected=json.loads(c.git('show',PARENT+':'+policy));rows=c.load(HERE/'CATALOG-ROWS.json')
 assert len(rows)==3 and all(v['original_key_access'] is False for v in rows)
 for row in rows:
  raw=c.git('show',row['source']+':'+row['path']);assert c.digest(raw)==row['workflow_sha256']
  assert b'secrets.INFINITY_' not in raw and b'assemble.py sign' not in raw,'UNSIGNED_WORKFLOW_ONLY'
 expected['additional_unsigned_owner_workflows'].extend(rows)
 expected['reviewed_workflow_ids']=sorted(set(expected['reviewed_workflow_ids'])|{v['id'] for v in rows})
 assert c.load(ROOT/policy)==expected and expected['sole_original_key_workflow_id']==397702717,'EXACT_UNSIGNED_CATALOG_EXTENSION'
 roots='repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'
 assert (ROOT/roots).read_bytes()==c.git('show',PARENT+':'+roots),'OWNER_ROOTS_UNCHANGED'
 old_workflow=c.git('show',PARENT+':'+c.WORKFLOW).decode()
 marker='sign-six502-qa]';assert old_workflow.count(marker)==1
 prefix=old_workflow.replace(marker,'sign-six502-qa, prepare-cast504-audio, sign-cast504-audio]')
 assert (ROOT/c.WORKFLOW).read_text().startswith(prefix),'ORIGINAL_SIGNER_JOBS_CHANGED'
 wf_review=c.load(HERE/'WORKFLOW-REVIEW.json')
 assert wf_review['reviewer']=='Astra' and wf_review['after_sha256']==r['workflow_sha256'] and wf_review['before_sha256']==c.digest(old_workflow.encode())
 review_raw=(HERE/'OWNER-REVIEW.json').read_bytes();assert c.digest(review_raw)==r['review_sha256']
 review=json.loads(review_raw);assert review['reviewer']=='Astra' and review['status']=='PASS_NATIVE_ONLY_CAST504_RELEASE_GATE'
 fixed={k:r[k] for k in ('baseline_APK_sha256','versions','generations','parent_authority_sha256','workflow_sha256','source_bindings','base','stage','owners','expected_changes','accepted_pointer_updated','known_limitations')}
 assert c.digest(canonical(fixed))==review['request_sha256']
 c.tools();return r
def preservation(base,apk,kind,r):
 inventory,cb,_,_,_=c.tools();version=r['versions'][kind]
 with ZipFile(base) as before,ZipFile(apk) as after:
  names=set(before.namelist())-set(inventory.SIGNATURE);assert set(after.namelist())-set(inventory.SIGNATURE)==names
  changes={}
  for name in names:
   def digest(z):
    with z.open(name) as f:return hashlib.file_digest(f,'sha256').hexdigest()
   a,b=digest(before),digest(after)
   if a!=b:changes[name]={'before':a,'after':b}
  assert changes==r['expected_changes'][kind],'EXACT_SIGNED504_MEMBER_VECTOR'
  assert after.read('AndroidManifest.xml')==cb.set_version(before.read('AndroidManifest.xml'),version)
  assert after.read(LABEL)==('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
 return {'status':'PASS_EXACT_NATIVE_ONLY504_PRESERVATION','kind':kind,'baseline':2103504,'APK_sha256':c.sha(apk),'changes':changes,'unchanged_members':len(names)-len(changes),'Cobra':'UNCHANGED','Kodi_and_DEX':'UNCHANGED','CC_Health_skin_modules':'UNCHANGED','owner_data':'NOT_ACCESSED','physical_TV':'PENDING_OWNER'}
def rewrite_bundle(source,dest,apk,owner,payload,version,inventory,cb):
 with ZipFile(source) as old,ZipFile(apk) as app:
  meta=json.loads(old.read('component.json'));assert meta['owner']==owner
  patches={}
  for name,row in meta['members'].items():
   raw=app.read(name)
   if c.digest(raw)!=row['sha256']:patches['payload/'+name]=raw;row['sha256']=c.digest(raw)
  # Every owner DEX stream is copied verbatim, including the accepted lock classes.
  meta['payload']={n:v for n,v in payload.items() if v['owner']==owner}
  meta.update(version=str(version)+'.'+owner.lower()+'.cast504audio.1',approved_source=os.environ['GITHUB_SHA'])
  meta['digest']=cb.component_digest(meta['payload'],owner)
  with ZipFile(dest,'w',allowZip64=True) as out:
   for name in old.namelist():prior.copy_entry(old,out,name,inventory.canonical(meta) if name=='component.json' else patches.get(name))
 return meta
def prepare():
 r=request();inventory,cb,ra,_,_=c.tools();current=c.load(ROOT/c.AUTHORITY)
 assert current['generation']==r['parent_generation'] and c.sha(ROOT/c.AUTHORITY)==r['parent_authority_sha256'],'REGISTRY_RACE'
 baseline=json.loads(c.git('show',BASE_AUTH+':'+c.AUTHORITY));assert baseline['generation']==89 and baseline['candidate_versionCode']==2103504
 base=c.unique(c.obtain(r['base'],'cast504-release-base'),'Infinity-2103504-Combined-Original-Signer.apk');assert c.sha(base)==BASE;c.signature(base)
 staged=c.obtain(r['stage'],'cast504-release-stage');proof=c.load(c.unique(staged,'STAGING.json'))
 assert proof['status']=='PASS_UNSIGNED_NATIVE_ONLY504_STAGE' and proof['baseline_APK_sha256']==BASE and proof['versions']==r['versions']
 original=c.obtain(r['owners'],'cast504-release-owner-bundles')/'candidate/components'
 catalog_base=c.load(original/'catalog.json');assert catalog_base==baseline['bundle_catalog'],'SIGNED504_OWNER_BUNDLES_REQUIRED'
 out=ROOT/'cast504-prepared';out.mkdir();previous=current
 for kind,number in r['versions'].items():
  source=c.unique(staged,'Infinity-'+str(number)+'-UNSIGNED-NOT-INSTALLABLE.apk');assert c.sha(source)==proof['payloads'][kind]['APK_sha256']
  assert proof['payloads'][kind]['changes']==r['expected_changes'][kind]
  dest=out/kind;dest.mkdir();apk=dest/('Infinity-'+str(number)+'-UNSIGNED.apk');shutil.copyfile(source,apk)
  c.save(dest/'PRESERVATION.json',preservation(base,apk,kind,r))
  payload=copy.deepcopy(baseline['payload'])
  for name,row in r['expected_changes'][kind].items():
   if name=='AndroidManifest.xml':continue
   key='member:'+name;assert payload[key]['sha256']==row['before'] and payload[key]['owner'] in ('INFINITY','CHOOSER_SHELL');payload[key]['sha256']=row['after']
  components=dest/'components';components.mkdir();catalog=copy.deepcopy(catalog_base);catalog.update(source=os.environ['GITHUB_SHA'],release_approved=False);metas={}
  for owner,row in catalog['bundles'].items():
   src=original/row['file'];target=components/row['file'];cb.read_bundle(src,row)
   if owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):shutil.copyfile(src,target);meta=cb.read_bundle(target,row)
   else:
    meta=rewrite_bundle(src,target,apk,owner,payload,number,inventory,cb)
    row.update(sha256=c.sha(target),**{k:meta[k] for k in ('version','digest','approved_source')});cb.read_bundle(target,row)
   metas[owner]=meta
  (components/'catalog.json').write_bytes(inventory.canonical(catalog))
  proposed=copy.deepcopy(previous);proposed.update(generation=previous['generation']+1,candidate_versionCode=number,last_issued_versionCode=previous['candidate_versionCode'],previous_authority_sha256=inventory.digest(inventory.canonical(previous)),target_owners=['INFINITY','CHOOSER_SHELL'],update_kind='owner_update',payload=payload,bundle_catalog=catalog,experience_version_labels={'INFINITY':number,'COBRA':2103445},workflow_sha256=c.sha(ROOT/c.WORKFLOW))
  assert proposed['generation']==r['generations'][kind]
  for policy in ('repairs/dual-experience-isolation-2103420/signer-policy.json','repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'):proposed['source_files'][policy]=c.sha(ROOT/policy)
  for owner in proposed['target_owners']:
   proposed['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')};proposed['components'][owner]['revision']=previous['components'][owner]['revision']+1
   proposed['bundle_sources'][owner]={'run_id':int(os.environ['GITHUB_RUN_ID']),'build_source':os.environ['GITHUB_SHA'],'artifact':'Infinity504-Cast-Audio-Prepared-'+os.environ['GITHUB_RUN_ID'],'path':kind+'/components/'+owner+'.zip'}
  proposed['owner_update_evidence']={'owner':'INFINITY_CAST504_AUDIO_'+kind.upper(),'producer_run':int(os.environ['GITHUB_RUN_ID']),'producer_source':os.environ['GITHUB_SHA'],'baseline_APK_sha256':BASE,'unsigned_sha256':c.sha(apk),'source_files':dict(r['source_bindings'],**{str((HERE/'OWNER-REQUEST.json').relative_to(ROOT)):c.sha(HERE/'OWNER-REQUEST.json')}),'known_limitations':r['known_limitations'],'Fold':'PENDING_OWNER','accepted_pointer_updated':False,'public_release':False,'verification_toolchain':current['owner_update_evidence']['verification_toolchain']}
  ra.transition(previous,proposed,proposed['target_owners']);ra.verify_evidence(proposed,lambda p:(ROOT/p).read_bytes());ra.verify(proposed,{n:v['sha256'] for n,v in payload.items()},number,proposed['generation'])
  (dest/'AUTHORITY-PROPOSAL.json').write_bytes(inventory.canonical(proposed));previous=proposed
 c.save(out/'PREPARATION.json',{'status':'PASS_NATIVE_ONLY504_OWNER_PREPARATION','source':os.environ['GITHUB_SHA'],'baseline':BASE,'registry_written':False,'signed':False,'Kodi_DEX_modules_rebuilt':False})
def selected():
 r=request();kind=r['active_kind'];assert kind in ('candidate','recovery')
 a=c.load(ROOT/c.AUTHORITY);assert a['generation']==r['generations'][kind] and a['candidate_versionCode']==r['versions'][kind]
 prepared=c.obtain(r['prepared'],'cast504-registered-preparation')/kind
 assert (prepared/'AUTHORITY-PROPOSAL.json').read_bytes()==(ROOT/c.AUTHORITY).read_bytes(),'EXACT_REVIEWED_REGISTERED_AUTHORITY'
 apk=c.unique(prepared,'Infinity-'+str(r['versions'][kind])+'-UNSIGNED.apk');assert c.sha(apk)==a['owner_update_evidence']['unsigned_sha256']
 base=c.unique(c.obtain(r['base'],'cast504-sign-baseline'),'Infinity-2103504-Combined-Original-Signer.apk');assert c.sha(base)==BASE;preservation(base,apk,kind,r)
 c.jars()
 with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:f.write('apk='+str(apk)+'\ngeneration='+str(a['generation'])+'\n')
def post():
 r=request();kind=r['active_kind'];out=ROOT/'cast504-original-signed';apk=c.unique(out,'Infinity-'+str(r['versions'][kind])+'-Combined-Original-Signer.apk');c.signature(apk)
 base=c.unique(c.obtain(r['base'],'cast504-sign-baseline'),'Infinity-2103504-Combined-Original-Signer.apk');assert c.sha(base)==BASE
 c.save(out/'PRESERVATION.json',preservation(base,apk,kind,r));shutil.copyfile(ROOT/c.AUTHORITY,out/'release-authority.json')
if __name__=='__main__':{'prepare':prepare,'selected':selected,'post':post}[sys.argv[1]]()
