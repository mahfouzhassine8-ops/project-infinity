"""Native-only Essential repair / exact83 forward recovery; ORIGINAL397 signs.

This is an owner input/preservation gate, not a signer. Original assembly,
certificate, DEX, owner transition and protected-contract tools are unchanged.
"""
import copy,hashlib,importlib.util,json,os,re,shutil,stat,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OLD=ROOT/'repairs/infinity-core-outcomes-qa-2103483-20261112/releaseprep'
sys.path.insert(0,str(OLD));import original_gate as q
require=q.require;sha=q.sha;load=q.load;api=q.api;git=q.git
KINDS={'repair':(2103486,71),'recovery':(2103487,72)}
BASE83=q.APK83;BASE_NATIVE=q.ENGINE83;LIB=q.LIB;LABEL=q.LABEL
OWNERS=['INFINITY','CHOOSER_SHELL']
def context(kind):
 require(kind in KINDS,'EXACT_RELEASE_KIND')
 require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ['GITHUB_REPOSITORY']==q.REPO and os.environ['GITHUB_REF']=='refs/heads/'+q.CANONICAL and git('rev-parse','HEAD').decode().strip()==os.environ['GITHUB_SHA'],'EXACT_CANONICAL_CONTEXT')
 require(not git('status','--porcelain','--untracked-files=no').strip(),'CLEAN_CANONICAL_SOURCE')
 r=api('actions/runs/'+os.environ['GITHUB_RUN_ID']);require(r['workflow_id']==397702717 and r['head_sha']==os.environ['GITHUB_SHA'],'ORIGINAL397_ONLY')
 req=HERE/(kind.upper()+'-REQUEST.json');r=load(req);version,generation=KINDS[kind]
 require(r['enabled'] is True and r['kind']==kind and r['versionCode']==version and r['generation']==generation and r['baseline_APK_sha256']==BASE83,'FROZEN_SCOPE_AND_VERSION')
 require(r['Core_path_or_source_changed'] is False and r['Cobra_changed'] is False and r['publication'] is False and r['accepted_pointer_updated'] is False,'PRESERVATION_BOUNDARY')
 require(req.read_bytes()==git('show',os.environ['GITHUB_SHA']+':'+req.relative_to(ROOT).as_posix()),'COMMITTED_REQUEST')
 require(sha(ROOT/q.WORKFLOW)==r['workflow_sha256'],'REVIEWED_ORIGINAL_WORKFLOW')
 for n,h in r['source_bindings'].items():require(sha(ROOT/n)==h,'REVIEWED_RELEASE_SOURCE:'+n)
 return r
def tools():
 prior=load(OLD/'ORIGINAL-QA-REQUEST.json');t=q.toolkit(prior)
 refpath=ROOT/'repairs/infinity-functional-startup-2103482-20261111/package_internal_qa.py'
 require(sha(refpath)=='b4d03488be53396f0aa471da911f425ccfdf8d21869587151fe7f3485b435e89','ORIGINAL83_OWNER_REWRAPPER')
 spec=importlib.util.spec_from_file_location('retained83_rewrapper',refpath);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
 return t,ref
def obtain(row,role):
 q.producer(row);root=ROOT/('essential-release-input-'+role);archive=root/'artifact.zip';dest=root/'files'
 if not root.exists():
  root.mkdir()
  with archive.open('xb') as stream:subprocess.run(['gh','api','repos/'+q.REPO+'/actions/artifacts/'+str(row['id'])+'/zip'],stdout=stream,check=True,timeout=600)
 require('sha256:'+sha(archive)==row['digest'] and archive.stat().st_size==row['size_in_bytes'],'AUTHENTICATED_ARCHIVE:'+role)
 with ZipFile(archive) as z:
  t,_=tools();names=t.inventory.validate_names(z)
  require(len(names)<100000 and sum(i.file_size for i in z.infolist())<8*1024**3 and all(not stat.S_ISLNK(i.external_attr>>16) for i in z.infolist()),'REGULAR_BOUNDED_ARCHIVE')
  if not dest.exists():dest.mkdir();z.extractall(dest)
  # The same input is used by pre-sign and post-sign steps in ONE job. Reuse
  # only after comparing every extracted regular file with the authenticated
  # archive; never overwrite an existing cache or trust its mere existence.
  actual={p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}
  regular={i.filename for i in z.infolist() if not i.is_dir()}
  require(actual==regular and all(not p.is_symlink() for p in dest.rglob('*')),'CACHED_ARCHIVE_MEMBER_VECTOR')
  for n in regular:
   with z.open(n) as stream:require(hashlib.file_digest(stream,'sha256').hexdigest()==sha(dest/n),'CACHED_ARCHIVE_BYTES:'+n)
 return dest
def baseline():
 row=load(OLD/'BASELINE83.json')['signed_apk'];folder=obtain(row,'signed83');p=folder/'Infinity-2103483-Combined-Original-Signer.apk';require(sha(p)==BASE83,'EXACT_SIGNED83')
 verify_signature(p);return p
def verify_signature(p):
 text=subprocess.check_output([str(Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0/apksigner'),'verify','--verbose','--print-certs',str(p)],text=True)
 require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',text)==[q.CERT],'PERMANENT_CERTIFICATE')
 for v in ('v1','v2','v3'):require(any(x.startswith('Verified using '+v+' scheme') and x.endswith(': true') for x in text.splitlines()),'ACTUAL_SIGNATURE_'+v)
 return text
def engine(r):
 if r['kind']=='recovery':return BASE_NATIVE,None
 q.producer(r['native_producer'],expected_id=415461484)
 folder=obtain(r['native_producer'],'native');p=folder/'libkodi.so';proof=load(folder/'ESSENTIAL-ONLY-ARM64.json');source=load(folder/'ESSENTIAL-ONLY-SOURCE-PRESERVATION.json')
 require(proof['status']=='PASS_FULL_ARM64_ESSENTIAL_ONLY_LINK_AND_BASELINE_ABI' and proof['source_commit']==r['native_producer']['source'] and proof['native_sha256']==sha(p)==r['native_sha256'] and proof['Core_path_correction_activated'] is False and proof['signed'] is False,'ACTUAL_FROZEN_FULL_ARM64')
 require(source['baseline83_native_sha256']==BASE_NATIVE and source['unchanged83_native_sources']==9409 and len(source['changed'])==3 and source['Cobra_changed'] is False and source['essential_admission_or_durability_waivers'] is False,'EXACT83_THREE_HEADER_SOURCE_BOUNDARY')
 for n,change in source['changed'].items():
  require(sha(HERE.parent/'native/overlay'/n)==change['after'],'LOCAL_REVIEWED_NATIVE_SOURCE:'+n)
 return sha(p),p
def compare(base,candidate,r,t):
 expected,_=engine(r);members={'AndroidManifest.xml',LABEL}|({LIB} if r['kind']=='repair' else set())
 with ZipFile(base) as old,ZipFile(candidate) as new:
  names=set(t.inventory.validate_names(old))-set(t.inventory.SIGNATURE);require(set(t.inventory.validate_names(new))-set(t.inventory.SIGNATURE)==names,'EXACT_APK_MEMBER_VECTOR')
  changes={n for n in names if q.member_sha(old,n)!=q.member_sha(new,n)};require(changes==members,'ONLY_AUTHORIZED_NATIVE_AND_VERSION_MEMBERS')
  require(q.member_sha(old,LIB)==BASE_NATIVE and q.member_sha(new,LIB)==expected,'EXACT_ENGINE')
  a,av=t.cb.normalize_manifest(old.read('AndroidManifest.xml'));b,bv=t.cb.normalize_manifest(new.read('AndroidManifest.xml'));require(a==b and av==2103483 and bv==r['versionCode'],'VERSION_ONLY_MANIFEST')
  require(new.read(LABEL)==('infinity.last_updated_in='+str(r['versionCode'])+'\ncobra.last_updated_in=2103445\n').encode(),'INFINITY_ONLY_VERSION_LABEL')
 return len(names)-len(members)
def prepare(kind):
 r=context(kind);t,ref=tools();a=load(ROOT/q.AUTHORITY)
 require(a['generation']==r['generation']-1 and a['candidate_versionCode']==r['versionCode']-1,'RECONCILED_UNUSED_FORWARD_VERSION')
 base=baseline();native_sha,native=engine(r);components=obtain(load(OLD/'BASELINE83.json')['prepared_owners'],'owners83')/'components'
 if native is None:
  native=ROOT/'essential-original83-libkodi.so'
  if not native.exists():
   with ZipFile(base) as z,z.open(LIB) as src,native.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
  require(sha(native)==BASE_NATIVE,'EXACT_RECOVERY_ENGINE')
 catalog=load(components/'catalog.json');require(catalog==load(OLD/'BASELINE83.json')['bundle_catalog'],'ORIGINAL83_OWNER_CATALOG')
 out=ROOT/('essential-'+kind+'-prepared');out.mkdir(exist_ok=False);owners=out/'components';owners.mkdir()
 catalog=copy.deepcopy(catalog);catalog.update(source=os.environ['GITHUB_SHA'],release_approved=False)
 for owner in t.cb.OWNED:
  row=catalog['bundles'][owner];src=components/row['file'];dst=owners/row['file']
  if owner in OWNERS:
   changes={'payload/'+LABEL:('infinity.last_updated_in='+str(r['versionCode'])+'\ncobra.last_updated_in=2103445\n').encode()} if owner=='CHOOSER_SHELL' else {'payload/'+LIB:native}
   # Recovery still advances its Infinity owner metadata; payload is exact83.
   meta=ref.rebuild_owner(src,dst,owner,os.environ['GITHUB_SHA'],r['versionCode'],changes);row.update(sha256=sha(dst),**{k:meta[k] for k in ('version','digest','approved_source')})
  else:shutil.copyfile(src,dst);require(sha(src)==sha(dst),'PROTECTED_OWNER_ZIP_IDENTICAL')
  t.cb.read_bundle(dst,row)
 (owners/'catalog.json').write_bytes(t.inventory.canonical(catalog));apk=out/('Infinity-'+str(r['versionCode'])+'-UNSIGNED-NOT-INSTALLABLE.apk');t.cb.combine(owners,catalog,apk,r['versionCode'])
 count=compare(base,apk,r,t);proof=dict(status='PASS_EXACT83_OWNER_PRESERVATION',kind=kind,versionCode=r['versionCode'],source=os.environ['GITHUB_SHA'],baseline_APK_sha256=BASE83,native_sha256=native_sha,unsigned_sha256=sha(apk),unchanged_payload_members=count,Cobra_changed=False,Core_path_or_source_changed=False,original_key_used=False,signed=False)
 (out/'PRESERVATION.json').write_bytes(t.inventory.canonical(proof))
def prepared(r,t):
 q.producer(r['prepared_producer'],expected_id=397702717)
 folder=obtain(r['prepared_producer'],'prepared-'+r['kind']);p=folder/('Infinity-'+str(r['versionCode'])+'-UNSIGNED-NOT-INSTALLABLE.apk');proof=load(folder/'PRESERVATION.json')
 require(proof['status']=='PASS_EXACT83_OWNER_PRESERVATION' and proof['source']==r['prepared_producer']['source'] and proof['unsigned_sha256']==sha(p)==r['unsigned_sha256'],'EXACT_PREPARED_APK')
 return folder,p,proof
def propose(kind):
 r=context(kind);t,_=tools();data,p,proof=prepared(r,t);compare(baseline(),p,r,t);before=load(ROOT/q.AUTHORITY)
 require(sha(ROOT/q.AUTHORITY)==r['parent_authority_sha256'] and before['generation']==r['generation']-1 and before['candidate_versionCode']==r['versionCode']-1,'EXACT_REGISTRY_PARENT')
 catalog=load(data/'components/catalog.json');meta={o:t.cb.read_bundle(data/'components'/catalog['bundles'][o]['file'],catalog['bundles'][o]) for o in t.cb.OWNED};payload={k:v for m in meta.values() for k,v in m['payload'].items()}
 require(set(payload)==set(before['payload']) and all(payload[k]==v for k,v in before['payload'].items() if k not in ('member:'+LIB,'member:'+LABEL)),'NO_UNDECLARED_PAYLOAD_CHANGE')
 for o in ('COBRA','MINIMAL_ANDROID_CONTRACT'):require(catalog['bundles'][o]==before['bundle_catalog']['bundles'][o],'PROTECTED_OWNER_RETAINED')
 result=copy.deepcopy(before);result.update(generation=r['generation'],candidate_versionCode=r['versionCode'],last_issued_versionCode=max(before['last_issued_versionCode'],before['candidate_versionCode']),previous_authority_sha256=t.inventory.digest(t.inventory.canonical(before)),target_owners=OWNERS,update_kind='owner_update',payload=payload,bundle_catalog=catalog,experience_version_labels={'INFINITY':r['versionCode'],'COBRA':2103445},workflow_sha256=sha(ROOT/q.WORKFLOW))
 for o in OWNERS:
  result['components'][o]={k:meta[o][k] for k in ('version','digest','approved_source','settings_schema')};result['components'][o]['revision']=before['components'][o]['revision']+1
  result['bundle_sources'][o]=dict(run_id=r['prepared_producer']['run'],build_source=r['prepared_producer']['source'],artifact=r['prepared_producer']['name'],path='components/'+o+'.zip')
 files=dict(r['source_bindings']);req=HERE/(kind.upper()+'-REQUEST.json');files[req.relative_to(ROOT).as_posix()]=sha(req)
 result['owner_update_evidence']=dict(owner='INFINITY_ESSENTIAL_ONLY_SHUTDOWN_'+kind.upper(),producer_run=r['prepared_producer']['run'],producer_source=r['prepared_producer']['source'],artifact={k:r['prepared_producer'][k] for k in ('id','name','digest','size_in_bytes')},source_files=files,native_sha256=engine(r)[0],baseline_APK_sha256=BASE83,preparation_sha256=sha(data/'PRESERVATION.json'),Core_path_or_source_changed=False,Android=r.get('independent_Android_evidence','NOT_RUN'),Fold='NOT_RUN',publication=False,public_release=False,owner_delivery_cleared=False,accepted_pointer_updated=False,verification_toolchain=before['owner_update_evidence']['verification_toolchain'])
 t.ra.transition(before,result,OWNERS);t.ra.verify_evidence(result,lambda n:(ROOT/n).read_bytes());t.ra.verify(result,{k:v['sha256'] for k,v in payload.items()},r['versionCode'],r['generation'])
 out=ROOT/('essential-'+kind+'-authority');out.mkdir(exist_ok=False);(out/'AUTHORITY-PROPOSAL.json').write_bytes(t.inventory.canonical(result))
def admit(kind):
 r=context(kind);t,_=tools();a=load(ROOT/q.AUTHORITY)
 require(a['generation']==r['generation'] and a['candidate_versionCode']==r['versionCode'] and a['owner_update_evidence']['owner']=='INFINITY_ESSENTIAL_ONLY_SHUTDOWN_'+kind.upper(),'EXACT_REGISTERED_OWNER_RELEASE')
 require(a['payload']['member:'+LIB]=={'owner':'INFINITY','sha256':engine(r)[0]},'REGISTERED_ENGINE');t.ra.validate(a);t.ra.verify_evidence(a,lambda n:(ROOT/n).read_bytes());return r,t
def inputs(kind):
 r,t=admit(kind);_,p,_=prepared(r,t);compare(baseline(),p,r,t)
 with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:f.write('apk='+str(p.relative_to(ROOT))+'\n')
def post(kind):
 r,t=admit(kind);folder=ROOT/('essential-'+kind+'-original-signed');p=folder/('Infinity-'+str(r['versionCode'])+'-Combined-Original-Signer.apk');receipt=load(folder/'BUILD-RECEIPT.json')
 require(receipt['signed_apk_sha256']==sha(p) and receipt['certificate_sha256']==q.CERT,'SIGNED_IDENTITY');text=verify_signature(p);count=compare(baseline(),p,r,t)
 (folder/'SIGNATURE.txt').write_text(text);(folder/'SHA256SUMS').write_text(sha(p)+'  '+p.name+'\n')
 (folder/'PRESERVATION.json').write_bytes(t.inventory.canonical(dict(status='PASS_ORIGINAL_SIGNED_EXACT83_PRESERVATION',versionCode=r['versionCode'],kind=kind,APK_sha256=sha(p),certificate_sha256=q.CERT,native_sha256=engine(r)[0],unchanged_payload_members=count,Cobra_changed=False,Core_path_or_source_changed=False,Fold='NOT_RUN',accepted=False)))
if __name__=='__main__':
 require(len(sys.argv)==3,'EXACT_OPERATION_AND_KIND');op,kind=sys.argv[1:];{'prepare':prepare,'propose':propose,'admit':admit,'inputs':inputs,'post':post}[op](kind)
