"""Exact signed83 payload as forward85, through original397 and unchanged tools."""
import argparse,copy,hashlib,importlib.util,json,os,re,shutil,stat,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
import original_gate as q
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
VERSION=2103485;GENERATION=70
AUTH=ROOT/q.AUTHORITY;REQ=HERE/'FORWARD-RECOVERY-REQUEST.json'
BASE83=q.APK83;ENGINE=q.ENGINE83;LIB=q.LIB;LABEL=q.LABEL
MEMBERS={'AndroidManifest.xml',LABEL};OWNERS=['INFINITY','CHOOSER_SHELL']
OWNER='INFINITY_EXACT_SIGNED83_FORWARD_RECOVERY_85'
PARENT='4131a4ef58bd861891b039f023c6b290bbe7e0e0'
OUT=ROOT/'forward85-prepared';APK=OUT/'Infinity-2103485-Forward83-UNSIGNED-NOT-INSTALLABLE.apk'
require=q.require;sha=q.sha;load=q.load;api=q.api;git=q.git

def tools():
    prior=load(HERE/'ORIGINAL-QA-REQUEST.json')
    for n,h in prior['source_bindings'].items():require(sha(ROOT/n)==h,'ORIGINAL_QA_TOOL_CHANGED:'+n)
    t=q.toolkit(prior)
    reference=ROOT/'repairs/infinity-functional-startup-2103482-20261111/package_internal_qa.py'
    require(sha(reference)=='b4d03488be53396f0aa471da911f425ccfdf8d21869587151fe7f3485b435e89','IMMUTABLE83_REWRAPPER')
    spec=importlib.util.spec_from_file_location('exact83_rewrap',reference);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    return t,ref

def context():
    require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ['GITHUB_REPOSITORY']==q.REPO and
        os.environ['GITHUB_REF']=='refs/heads/'+q.CANONICAL and git('rev-parse','HEAD').decode().strip()==os.environ['GITHUB_SHA'], 'EXACT_CANONICAL_CI')
    require(not git('status','--porcelain','--untracked-files=no').strip(),'CLEAN_OWNER_HEAD')
    r=api('actions/runs/'+os.environ['GITHUB_RUN_ID']);require(r['workflow_id']==397702717 and r['head_sha']==os.environ['GITHUB_SHA'],'ONLY_ORIGINAL397')
    a=load(HERE/'OWNER-QA-AUTHORIZATION.json');require(a['forward_recovery_if_feasible']==VERSION and a['protected_baseline']==2103483,'OWNER_FORWARD_RECOVERY_AUTHORIZATION')

def obtain(row,role):
    q.producer(row)
    root=ROOT/('forward85-input-'+role);root.mkdir(exist_ok=False);archive=root/'artifact.zip'
    with archive.open('xb') as f:subprocess.run(['gh','api','repos/'+q.REPO+'/actions/artifacts/'+str(row['id'])+'/zip'],stdout=f,check=True,timeout=600)
    require('sha256:'+sha(archive)==row['digest'] and archive.stat().st_size==row['size_in_bytes'],'EXACT_ARCHIVE:'+role)
    dest=root/'files';dest.mkdir()
    with ZipFile(archive) as z:
        names=q.toolkit(load(HERE/'ORIGINAL-QA-REQUEST.json')).inventory.validate_names(z)
        require(len(names)<100000 and sum(i.file_size for i in z.infolist())<8*1024**3 and all(not stat.S_ISLNK(i.external_attr>>16) for i in z.infolist()),'BOUNDED_REGULAR_ZIP')
        z.extractall(dest)
    return dest

def baseline():
    row=load(HERE/'BASELINE83.json')['signed_apk'];folder=obtain(row,'signed83');p=folder/'Infinity-2103483-Combined-Original-Signer.apk';require(sha(p)==BASE83,'EXACT_SIGNED83')
    sdk=Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0';text=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(p)],text=True)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',text)==[q.CERT],'ORIGINAL83_CERTIFICATE')
    for v in ('v1','v2','v3'):require(any(x.startswith('Verified using '+v+' scheme') and x.endswith(': true') for x in text.splitlines()),'BASE_SIGNATURE:'+v)
    return p

def compare(base,candidate,t):
    require(sha(base)==BASE83,'BASELINE_HASH')
    with ZipFile(base) as old,ZipFile(candidate) as new:
        names=set(t.inventory.validate_names(old))-set(t.inventory.SIGNATURE);require(set(t.inventory.validate_names(new))-set(t.inventory.SIGNATURE)==names,'EXACT_MEMBER_VECTOR')
        delta={n for n in names if q.member_sha(old,n)!=q.member_sha(new,n)};require(delta==MEMBERS,'ONLY_TWO_VERSION_MEMBERS_CHANGE')
        require(q.member_sha(old,LIB)==q.member_sha(new,LIB)==ENGINE,'ORIGINAL83_NATIVE_RESTORED')
        a,av=t.cb.normalize_manifest(old.read('AndroidManifest.xml'));b,bv=t.cb.normalize_manifest(new.read('AndroidManifest.xml'));require(a==b and av==2103483 and bv==VERSION,'MANIFEST_VERSION_ONLY')
        require(new.read(LABEL)==b'infinity.last_updated_in=2103485\ncobra.last_updated_in=2103445\n','ONLY_INFINITY_LABEL_ADVANCES')
        return len(names)-2

def prepare():
    context();t,ref=tools();a=load(AUTH);require(a['generation']==69 and a['candidate_versionCode']==2103484,'CURRENT_REGISTERED84_PARENT')
    r=api('actions/runs/43169914369');require(r['conclusion']=='success' and r['head_sha']==PARENT and r['workflow_id']==397702717,'ACTUAL_ORIGINAL_SIGNED84_ISSUANCE')
    base=baseline();components=obtain(load(HERE/'BASELINE83.json')['prepared_owners'],'owners83')/'components';catalog=load(components/'catalog.json');require(catalog==load(HERE/'BASELINE83.json')['bundle_catalog'],'EXACT83_OWNER_CATALOG')
    OUT.mkdir(exist_ok=False);owners=OUT/'components';owners.mkdir();native=ROOT/'forward85-original83-libkodi.so'
    with ZipFile(base) as z,z.open(LIB) as src,native.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
    require(sha(native)==ENGINE,'EXACT_ORIGINAL_ENGINE_BYTES')
    catalog=copy.deepcopy(catalog);catalog.update(source=os.environ['GITHUB_SHA'],release_approved=False)
    for owner in t.cb.OWNED:
        row=catalog['bundles'][owner];old=components/row['file'];target=owners/row['file']
        if owner in OWNERS:
            changes={'payload/'+LIB:native} if owner=='INFINITY' else {'payload/'+LABEL:b'infinity.last_updated_in=2103485\ncobra.last_updated_in=2103445\n'}
            meta=ref.rebuild_owner(old,target,owner,os.environ['GITHUB_SHA'],VERSION,changes);row.update(sha256=sha(target),**{k:meta[k] for k in ('version','digest','approved_source')})
        else:shutil.copyfile(old,target);require(sha(old)==sha(target),'PROTECTED_OWNER_ZIP_IDENTICAL')
        t.cb.read_bundle(target,row)
    (owners/'catalog.json').write_bytes(t.inventory.canonical(catalog));t.cb.combine(owners,catalog,APK,VERSION)
    count=compare(base,APK,t);proof=dict(status='PASS_EXACT83_FORWARD85_UNSIGNED_TWO_MEMBER_PRESERVATION',source=os.environ['GITHUB_SHA'],versionCode=VERSION,baseline_APK_sha256=BASE83,native_sha256=ENGINE,unsigned_sha256=sha(APK),unchanged_payload_members=count,Core_path_or_source_patch=False,Cobra_changed=False,original_key_used=False,signed=False)
    (OUT/'FORWARD-PRESERVATION.json').write_bytes(t.inventory.canonical(proof))

def request():
    context();r=load(REQ);require(r['enabled'] is True and r['versionCode']==VERSION and r['generation']==GENERATION and r['operation']=='EXACT83_FORWARD85_RECOVERY','EXACT_RECOVERY_REQUEST')
    require(r['baseline_APK_sha256']==BASE83 and r['native_sha256']==ENGINE and r['publication'] is False and r['accepted_pointer_updated'] is False,'RECOVERY_SCOPE')
    require(sha(ROOT/q.WORKFLOW)==r['workflow_sha256'],'FROZEN_ORIGINAL_WORKFLOW')
    for n,h in r['source_bindings'].items():require(sha(ROOT/n)==h,'FROZEN_RECOVERY_SOURCE:'+n)
    q.producer(r['prepared_producer'],expected_id=397702717);return r

def prepared(r,t):
    data=obtain(r['prepared_producer'],'prepared');proof=load(data/'FORWARD-PRESERVATION.json')
    require(proof['status']=='PASS_EXACT83_FORWARD85_UNSIGNED_TWO_MEMBER_PRESERVATION' and proof['source']==r['prepared_producer']['source'] and proof['unsigned_sha256']==r['unsigned_sha256'] and proof['native_sha256']==ENGINE,'EXACT_PREPARED_RECOVERY')
    p=data/'Infinity-2103485-Forward83-UNSIGNED-NOT-INSTALLABLE.apk';require(sha(p)==r['unsigned_sha256'],'EXACT_RECOVERY_APK');return data,p,proof

def propose():
    r=request();t,_=tools();data,p,proof=prepared(r,t);base=baseline();compare(base,p,t)
    before=load(AUTH);require(before==json.loads(git('show',PARENT+':'+q.AUTHORITY)),'EXACT_REGISTERED84_PARENT_UNCHANGED')
    catalog=load(data/'components/catalog.json');meta={o:t.cb.read_bundle(data/'components'/catalog['bundles'][o]['file'],catalog['bundles'][o]) for o in t.cb.OWNED};payload={k:v for m in meta.values() for k,v in m['payload'].items()}
    require(set(payload)==set(before['payload']) and all(payload[k]==v for k,v in before['payload'].items() if k not in ('member:'+LIB,'member:'+LABEL)),'ALL_UNDECLARED_PAYLOAD_IDENTICAL')
    for o in ('COBRA','MINIMAL_ANDROID_CONTRACT'):require(catalog['bundles'][o]==before['bundle_catalog']['bundles'][o],'PROTECTED_OWNER_RETAINED')
    result=copy.deepcopy(before);result.update(generation=GENERATION,candidate_versionCode=VERSION,last_issued_versionCode=2103484,previous_authority_sha256=t.inventory.digest(t.inventory.canonical(before)),target_owners=OWNERS,update_kind='owner_update',payload=payload,bundle_catalog=catalog,experience_version_labels={'INFINITY':VERSION,'COBRA':2103445},workflow_sha256=sha(ROOT/q.WORKFLOW))
    for o in OWNERS:
        result['components'][o]={k:meta[o][k] for k in ('version','digest','approved_source','settings_schema')};result['components'][o]['revision']=before['components'][o]['revision']+1
        result['bundle_sources'][o]=dict(run_id=r['prepared_producer']['run'],build_source=r['prepared_producer']['source'],artifact=r['prepared_producer']['name'],path='components/'+o+'.zip')
    files=dict(r['source_bindings']);files[str(REQ.relative_to(ROOT))]=sha(REQ)
    result['owner_update_evidence']=dict(owner=OWNER,producer_run=r['prepared_producer']['run'],producer_source=r['prepared_producer']['source'],artifact={k:r['prepared_producer'][k] for k in ('id','name','digest','size_in_bytes')},source_files=files,native_sha256=ENGINE,baseline_APK_sha256=BASE83,preparation_sha256=sha(data/'FORWARD-PRESERVATION.json'),restores_exact83=True,Core_path_or_source_patch=False,Android='RECOVERY_INSTALL_OVER_NOT_YET_TESTED',Fold='NOT_RUN',publication=False,public_release=False,owner_delivery_cleared=False,accepted_pointer_updated=False,verification_toolchain=before['owner_update_evidence']['verification_toolchain'])
    t.ra.transition(before,result,OWNERS);t.ra.verify_evidence(result,lambda n:(ROOT/n).read_bytes());t.ra.verify(result,{k:v['sha256'] for k,v in payload.items()},VERSION,GENERATION)
    out=ROOT/'forward85-authority';out.mkdir(exist_ok=False);(out/'AUTHORITY-PROPOSAL.json').write_bytes(t.inventory.canonical(result))

def admit():
    r=request();t,_=tools();a=load(AUTH);require(a['generation']==GENERATION and a['candidate_versionCode']==VERSION and a['last_issued_versionCode']==2103484 and a['owner_update_evidence']['owner']==OWNER,'REGISTERED_RECOVERY_ONLY')
    require(a['payload']['member:'+LIB]=={'owner':'INFINITY','sha256':ENGINE} and a['protected_contract']==json.loads(git('show',PARENT+':'+q.AUTHORITY))['protected_contract'],'EXACT83_NATIVE_AND_PROTECTIONS')
    t.ra.validate(a);t.ra.verify_evidence(a,lambda n:(ROOT/n).read_bytes());return r,t

def inputs():
    r,t=admit();data,p,proof=prepared(r,t);base=baseline();compare(base,p,t)
    Path(os.environ['GITHUB_OUTPUT']).open('a').write('apk='+str(p.relative_to(ROOT))+'\n')

def post():
    r,t=admit();base=baseline();folder=ROOT/'forward85-original-signed';p=folder/'Infinity-2103485-Combined-Original-Signer.apk';receipt=load(folder/'BUILD-RECEIPT.json');require(receipt['signed_apk_sha256']==sha(p) and receipt['certificate_sha256']==q.CERT,'SIGNED_RECOVERY_IDENTITY')
    text=subprocess.check_output([str(Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0/apksigner'),'verify','--verbose','--print-certs',str(p)],text=True)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',text)==[q.CERT],'PERMANENT_CERTIFICATE')
    for v in ('v1','v2','v3'):require(any(x.startswith('Verified using '+v+' scheme') and x.endswith(': true') for x in text.splitlines()),'ACTUAL_SCHEME:'+v)
    count=compare(base,p,t);(folder/'FORWARD-RECOVERY.json').write_bytes(t.inventory.canonical(dict(status='PASS_ORIGINAL_SIGNED85_RESTORES_EXACT83_TWO_MEMBER_PRESERVATION',versionCode=VERSION,source=os.environ['GITHUB_SHA'],APK_sha256=sha(p),baseline_APK_sha256=BASE83,native_sha256=ENGINE,certificate_sha256=q.CERT,unchanged_payload_members=count,Cobra_changed=False,Core_path_or_source_patch=False,userdata_removed=False,physical_Fold='NOT_RUN')));(folder/'RECOVERY-SIGNATURE.txt').write_text(text)

if __name__=='__main__':
    mode=sys.argv[1];{'prepare':prepare,'propose':propose,'admit':admit,'inputs':inputs,'post':post}[mode]()
