"""Exact500 fast QA adapter. Original authority, owner gate and signer are unchanged."""
from pathlib import Path
from zipfile import ZipFile
import copy,hashlib,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'))
import common_release as c
import prepare_release as old
TASK=Path(__file__).resolve().parent
# Preserve the original tool pins. The sole permitted policy-data evolution is
# the exact audit catalog for three already reviewed unsigned500 CI workflows.
def reviewed_tools():
 for name in ('assemble.py','component_bundles.py','release_gate.py','inventory.py','review_ownership.py','signer_policy.py'):
  path='repairs/dual-experience-isolation-2103420/'+name
  c.require((ROOT/path).read_bytes()==c.git('show','e1ef672a6f24aed6c19a14ab96d2df6fe3380460:'+path),'UNCHANGED_ORIGINAL_TOOL:'+name)
 path='repairs/dual-experience-isolation-2103420/signer-policy.json'
 old=json.loads(c.git('show','5cdb593a:'+path));current=c.load(ROOT/path);review=c.load(TASK/'WORKFLOW-CATALOG-REVIEW.json');expected=copy.deepcopy(old)
 c.require({r['id'] for r in review['rows']}=={419489686,419528653,419521920},'EXACT_UNSIGNED_WORKFLOW_CATALOG')
 for row in review['rows']:
  c.require(row['original_key_access'] is False,'NO_ADDITIONAL_KEY_ROUTE')
  raw=c.git('show',row['source']+':'+row['path']);c.require(datahash(raw)==row['workflow_sha256'] and b'secrets.INFINITY_' not in raw and b'assemble.py sign' not in raw,'AUDITED_UNSIGNED_DEFINITION')
  expected['additional_unsigned_owner_workflows'].append(row)
 expected['reviewed_workflow_ids']=sorted(set(old['reviewed_workflow_ids'])|{r['id'] for r in review['rows']})
 c.require(current==expected and current['sole_original_key_workflow_id']==397702717,'POLICY_ONLY_EXACT_CATALOG_DELTA')
 for path in ('repairs/infinity-final-closure-2103407/p0/manifest.py','repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem','repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json'):
  c.require((ROOT/path).read_bytes()==c.git('show','e1ef672a6f24aed6c19a14ab96d2df6fe3380460:'+path),'ORIGINAL_TOOL_INPUT')
 sys.path.insert(0,str(c.CORE))
 import inventory,component_bundles,release_authority,release_gate,review_ownership
 return inventory,component_bundles,release_authority,release_gate,review_ownership
c.tools=reviewed_tools
BASE='224d5f808587ce4004a96a003331abe7c71cbe7bd08ec6b1d3ec288c6c75cf40'
ENGINE='ed2d955d1825bf838ea50a712782e54b69926d40605270a2f241efd913202ee7'
DEX='4360efcdf3af08a8388f18846c79353517ab3d7ee6a3c026838b7748c0914c98'
LABEL='assets/experience-component-updates.properties';LIB='lib/arm64-v8a/libkodi.so'
VERSIONS={'candidate':2103502,'recovery':2103503}
BASESOURCE='ccc30a77e07c2cf0abc3800ea60f4a68dc6bd9a3'
def datahash(b):return hashlib.sha256(b).hexdigest()
def request():
 c.context(True);r=c.load(TASK/'REQUEST.json');c.tools()
 c.require(r['baseline']==BASE and r['version_codes']==VERSIONS and r['accepted_pointer_updated'] is False,'EXACT_OWNER_FAST_QA')
 for n,h in r['source_bindings'].items():c.require(c.sha(ROOT/n)==h,'FROZEN_ADAPTER:'+n)
 c.require(c.sha(ROOT/c.WORKFLOW)==r['workflow_sha256'],'REVIEWED_EXISTING_SIGNER_WORKFLOW')
 return r

def preservation(base,apk,kind):
 inventory,cb,_,_,_=c.tools();changed={};same=0
 with ZipFile(base) as a,ZipFile(apk) as b:
  names=set(inventory.validate_names(a))-inventory.SIGNATURE
  c.require(set(inventory.validate_names(b))-inventory.SIGNATURE==names,'NO_ADDED_OR_REMOVED_PAYLOAD')
  expected={'AndroidManifest.xml':cb.set_version(a.read('AndroidManifest.xml'),VERSIONS[kind]),LABEL:('infinity.last_updated_in='+str(VERSIONS[kind])+'\ncobra.last_updated_in=2103445\n').encode()}
  for n in names:
   before=old.member_sha(a,n);after=old.member_sha(b,n)
   wanted=ENGINE if kind=='candidate' and n==LIB else DEX if kind=='candidate' and n=='classes6.dex' else datahash(expected[n]) if n in expected else before
   c.require(after==wanted,'OUT_OF_QA_MEMBER_SCOPE:'+n)
   if before!=after:changed[n]={'before':before,'after':after}
   else:same+=1
  c.require(set(changed)==({'AndroidManifest.xml',LABEL,LIB,'classes6.dex'} if kind=='candidate' else {'AndroidManifest.xml',LABEL}),'EXACT_QA_CHANGE_VECTOR')
 return dict(status='PASS_EXACT_SIGNED500_QA_MEMBER_PRESERVATION',kind=kind,versionCode=VERSIONS[kind],baseline_sha256=BASE,APK_sha256=c.sha(apk),changed_members=changed,unchanged_members=same,Cobra='UNCHANGED',providers_Search_tracking_profiles='UNCHANGED',deferred=['Continue Playing','Otaku Watchlist','Empty Shell'],physical_acceptance='PENDING_OWNER')

def inputs(r):
 base=c.unique(c.obtain(r['base'],'qa500-baseline'),'Infinity-2103500-Combined-Original-Signer.apk');c.require(c.sha(base)==BASE,'SIGNED500_IDENTITY');c.signature(base)
 stage=c.obtain(r['stage'],'qa500-stage');apk=c.unique(stage,'Infinity-2103502-Fast-QA-UNSIGNED-NOT-INSTALLABLE.apk');receipt=c.load(c.unique(stage,'QA-STAGING.json'))
 c.require(receipt['status']=='PASS_UNSIGNED_QA_STAGING_NOT_INSTALLABLE' and receipt['source']==r['stage']['source'] and receipt['native_sha256']==ENGINE and receipt['cast_dex_sha256']==DEX,'PASSED_COMPLETED_ASSEMBLY')
 preservation(base,apk,'candidate');return base,apk

def bundle(src,dst,owner,version,actual,kind,base,apk,source):
 inventory,cb,_,_,_=c.tools()
 with ZipFile(src) as z,ZipFile(apk) as a:
  meta=json.loads(z.read('component.json'));replacements={}
  for n in (LIB,LABEL):
   if 'payload/'+n in z.namelist():
    raw=a.read(n);replacements['payload/'+n]=raw;meta['members'][n]['sha256']=datahash(raw)
  if owner=='INFINITY':
   raw=a.read('classes6.dex');replacements['dex/cast-private.dex']=raw;meta['dex']['dex/cast-private.dex']=datahash(raw)
  meta['payload']={n:v for n,v in actual.items() if v['owner']==owner}
  if owner in ('INFINITY','CHOOSER_SHELL'):meta.update(version=str(version)+'.'+owner.lower()+'.fastqa500.1',approved_source=source)
  meta['digest']=cb.component_digest(meta['payload'],owner)
  with ZipFile(dst,'w',allowZip64=True) as out:
   for n in z.namelist():old.copy_entry(z,out,n,inventory.canonical(meta) if n=='component.json' else replacements.get(n))
 return meta

def prepare():
 r=request();current=c.load(ROOT/c.AUTHORITY)
 c.require(c.sha(ROOT/c.AUTHORITY)==r['parent_authority_sha256'] and current['candidate_versionCode']==2103501 and current['generation']==86,'LIVE_REGISTRY_RESERVATION_RACE')
 base,stage=inputs(r);inventory,cb,ra,rg,_=c.tools();out=ROOT/'fastqa-prepared';out.mkdir(exist_ok=False)
 baseline=json.loads(c.git('show',BASESOURCE+':'+c.AUTHORITY));c.require(baseline['candidate_versionCode']==2103500,'MATCHING500_AUTHORITY')
 actual,version=rg.inspect_candidate(stage,c.jars(),out/'qa-inspection');c.require(version==2103502,'STAGED_VERSION')
 diffs={n for n in set(actual)|set(baseline['payload']) if actual.get(n)!=baseline['payload'].get(n,{}).get('sha256')}
 c.require(all(n in {'member:'+LIB,'member:'+LABEL} or n in {'class:Lcom/projectinfinity/kodi/InfinityCastDialog;','class:Lcom/projectinfinity/kodi/InfinityCastSession;'} for n in diffs),'EXACT_OWNER_CLASS_NATIVE_VECTOR')
 c.require(len(diffs)==4,'EXACT_FOUR_PAYLOAD_IDENTITIES')
 ownerroot=c.obtain(r['owners'],'qa500-owner-bundles')/'candidate/components'
 original_catalog=c.load(ownerroot/'catalog.json');c.require(original_catalog==baseline['bundle_catalog'],'AUTHENTIC500_BUNDLES')
 prior=current
 for kind,ver in VERSIONS.items():
  dest=out/kind;dest.mkdir();apk=dest/('Infinity-'+str(ver)+'-UNSIGNED.apk')
  if kind=='candidate':shutil.copyfile(stage,apk)
  else:
   with ZipFile(base) as z,ZipFile(apk,'w',allowZip64=True) as target:
    changes={'AndroidManifest.xml':cb.set_version(z.read('AndroidManifest.xml'),ver),LABEL:('infinity.last_updated_in='+str(ver)+'\ncobra.last_updated_in=2103445\n').encode()}
    for n in z.namelist():
     if n not in inventory.SIGNATURE:old.copy_entry(z,target,n,changes.get(n))
  proof=preservation(base,apk,kind);c.save(dest/'PRESERVATION.json',proof)
  payload=copy.deepcopy(baseline['payload'])
  if kind=='candidate':
   payload={n:dict(owner=baseline['payload'][n]['owner'],sha256=h) for n,h in actual.items()}
  payload['member:'+LABEL]['sha256']=datahash(('infinity.last_updated_in='+str(ver)+'\ncobra.last_updated_in=2103445\n').encode())
  components=dest/'components';components.mkdir();catalog=copy.deepcopy(original_catalog);catalog.update(source=os.environ['GITHUB_SHA'],release_approved=False);metas={}
  for owner,row in catalog['bundles'].items():
   src=ownerroot/row['file'];dst=components/row['file'];cb.read_bundle(src,row)
   if owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):shutil.copyfile(src,dst);meta=cb.read_bundle(dst,row)
   else:
    meta=bundle(src,dst,owner,ver,payload,kind,base,apk,os.environ['GITHUB_SHA']);row.update(sha256=c.sha(dst),**{k:meta[k] for k in ('version','digest','approved_source')});cb.read_bundle(dst,row)
   metas[owner]=meta
  (components/'catalog.json').write_bytes(inventory.canonical(catalog))
  proposed=copy.deepcopy(prior);proposed.update(generation=prior['generation']+1,candidate_versionCode=ver,last_issued_versionCode=prior['candidate_versionCode'],previous_authority_sha256=inventory.digest(inventory.canonical(prior)),target_owners=['INFINITY','CHOOSER_SHELL'],update_kind='owner_update',payload=payload,bundle_catalog=catalog,experience_version_labels=dict(INFINITY=ver,COBRA=2103445),workflow_sha256=c.sha(ROOT/c.WORKFLOW))
  policy_path='repairs/dual-experience-isolation-2103420/signer-policy.json';proposed['source_files'][policy_path]=c.sha(ROOT/policy_path)
  for owner in proposed['target_owners']:
   proposed['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')};proposed['components'][owner]['revision']=prior['components'][owner]['revision']+1
   proposed['bundle_sources'][owner]=dict(run_id=int(os.environ['GITHUB_RUN_ID']),build_source=os.environ['GITHUB_SHA'],artifact='Infinity500-FastQA-Registered-Preparation-'+os.environ['GITHUB_RUN_ID'],path=kind+'/components/'+owner+'.zip')
  proposed['owner_update_evidence']=dict(owner='INFINITY_FAST_QA500_'+kind.upper(),producer_run=int(os.environ['GITHUB_RUN_ID']),producer_source=os.environ['GITHUB_SHA'],baseline_APK_sha256=BASE,unsigned_sha256=c.sha(apk),source_files=dict(r['source_bindings'],**{str((TASK/'REQUEST.json').relative_to(ROOT)):c.sha(TASK/'REQUEST.json')}),deferred=['Continue Playing','Otaku Watchlist','Empty Shell'],Fold='PENDING_OWNER',accepted_pointer_updated=False,public_release=False,verification_toolchain=current['owner_update_evidence']['verification_toolchain'])
  ra.transition(prior,proposed,proposed['target_owners']);ra.verify_evidence(proposed,lambda n:(ROOT/n).read_bytes());ra.verify(proposed,{n:v['sha256'] for n,v in payload.items()},ver,proposed['generation'])
  (dest/'AUTHORITY-PROPOSAL.json').write_bytes(inventory.canonical(proposed));prior=proposed
 c.save(out/'PREPARATION.json',dict(status='PASS_EXACT500_FAST_QA_AND_RECOVERY',source=os.environ['GITHUB_SHA'],base_sha256=BASE,registry_written=False,signed=False))
 shutil.rmtree(out/'qa-inspection')

def selected():
 r=request();a=c.load(ROOT/c.AUTHORITY);kind=r['active_kind'];c.require(a['candidate_versionCode']==VERSIONS[kind] and a['owner_update_evidence']['owner']=='INFINITY_FAST_QA500_'+kind.upper(),'EXACT_REGISTERED_FAST_QA');c.require(a['generation']==(87 if kind=='candidate' else 88),'EXACT_GENERATION')
 root=c.obtain(r['prepared'],'qa500-prepared');d=root/kind;apk=c.unique(d,'Infinity-'+str(VERSIONS[kind])+'-UNSIGNED.apk');base,_=inputs(r)
 c.require((d/'AUTHORITY-PROPOSAL.json').read_bytes()==(ROOT/c.AUTHORITY).read_bytes(),'EXACT_PREPARED_REGISTERED_AUTHORITY');preservation(base,apk,kind)
 c.require(c.sha(apk)==a['owner_update_evidence']['unsigned_sha256'],'EXACT_UNSIGNED_HASH')
 with Path(os.environ['GITHUB_OUTPUT']).open('a') as out:out.write('apk='+str(apk)+'\ngeneration='+str(a['generation'])+'\n')
 c.jars()
def post():
 r=request();kind=r['active_kind'];base,_=inputs(r);folder=ROOT/'signed-fastqa';apk=c.unique(folder,'Infinity-'+str(VERSIONS[kind])+'-Combined-Original-Signer.apk');c.signature(apk);c.save(folder/'PRESERVATION.json',preservation(base,apk,kind));shutil.copyfile(ROOT/c.AUTHORITY,folder/'release-authority.json')
if __name__=='__main__':{'prepare':prepare,'selected':selected,'post':post}[sys.argv[1]]()
