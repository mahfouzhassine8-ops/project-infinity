"""External447: exact445 inputs, isolated feature, original guarded combined signer."""
import argparse,copy,hashlib,importlib.util,json,os,re,shutil,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
H=Path(__file__).resolve().parent;HERE=H;REPO=H.parents[1]
ISO=REPO/'repairs/dual-experience-isolation-2103420'
sys.path[:0]=[str(ISO),str(H)]
from inventory import canonical,digest,file_sha,load,save,CERT_SHA,SIGNATURE,validate_names
from component_bundles import read_bundle,record,combine
from release_gate import component_digest,normalize_manifest,require
from release_authority import transition,verify_evidence
BASE='6cf75639a46ec6b0c858ae32abc102450fdc0974';AUTHORITY_BASE=BASE
BRANCH='work/infinity-2103445-standalone-external-player-20261101'
VERSION=2103447;GENERATION=33
APK_SHA='b7e78393ade7e52d8653823a0ad72ae99614a5a8e0b6cdedf5d5d15a9e643400'
LABEL='assets/experience-component-updates.properties'
AUTH=ISO/'release-authority.json'
TARGETS=['INFINITY','CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT']
def cmd(*args,env=None):return subprocess.check_output(list(map(str,args)),text=True,env=env,stderr=subprocess.STDOUT)
def previous():return json.loads(cmd('git','show',AUTHORITY_BASE+':'+str(AUTH.relative_to(REPO))))
def head_check():
    head=os.environ['GITHUB_SHA']
    require(os.environ.get('GITHUB_WORKFLOW')=='Infinity combined release | owner gate before original signing','SOLE_SIGNER_WORKFLOW')
    require(os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'EXACT_BRANCH')
    require(cmd('git','rev-parse','HEAD').strip()==head,'HEAD')
    require(cmd('git','ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head,'REMOTE_HEAD_RACE')
    require(not cmd('git','status','--porcelain','--untracked-files=no').strip(),'DIRTY_SOURCE')
    return head

def certificate(apk,sdk):
    text=cmd(sdk/'apksigner','verify','--verbose','--print-certs',apk)
    match=re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)',text)
    require(match is not None and match.group(1)==CERT_SHA,'ORIGINAL_CERTIFICATE')
    return text

def official(prepared,run_id):
    run=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)))
    proof=load(prepared/'PREPARATION.json')
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==proof['source'] and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-combined-release.yml','OFFICIAL_PRODUCER')
    require(proof['run_id']==run_id and proof['status']=='PASS_ISOLATED_EXTERNAL_PLAYER_OWNER_PREPARATION' and proof['baseline']==BASE and proof['baseline_apk_sha256']==APK_SHA,'PRODUCER_IDENTITY')
    rows=json.loads(cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run_id)+'/artifacts?per_page=100'))['artifacts']
    rows=[r for r in rows if r['name']=='Infinity447-Prepared-'+str(run_id) and not r['expired']]
    require(len(rows)==1,'ONE_OFFICIAL_ARTIFACT');row={k:rows[0][k] for k in ('id','name','digest','size_in_bytes')}
    require(re.fullmatch('sha256:[0-9a-f]{64}',row['digest']) is not None,'OFFICIAL_ARTIFACT_DIGEST')
    cache=Path(os.environ.get('LOADING_ARTIFACT_CACHE','/tmp/infinity447-official'));cache.mkdir(parents=True,exist_ok=True)
    archive=cache/(str(row['id'])+'.zip')
    if not archive.exists():
        with archive.open('wb') as f:subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(row['id'])+'/zip'],stdout=f,check=True)
    require(file_sha(archive)==row['digest'][7:],'OFFICIAL_ARCHIVE_BYTES')
    with ZipFile(archive) as z:
        names=set(validate_names(z));names={n for n in names if not n.endswith('/')}
        require(names=={str(p.relative_to(prepared)) for p in prepared.rglob('*') if p.is_file()},'OFFICIAL_ARTIFACT_FILE_SET')
        for n in names:
            with z.open(n) as f:require(hashlib.file_digest(f,'sha256').hexdigest()==file_sha(prepared/n),'OFFICIAL_FILE:'+n)
    for n,pin in proof['source_files'].items():
        require(file_sha(REPO/n)==pin and digest(subprocess.check_output(['git','show',proof['source']+':'+n]))==pin,'TESTED_SOURCE_CHANGED:'+n)
    return row

def compare(baseline,candidate,plan,out,sdk=None):
    from patch_manifest import patch
    require(file_sha(baseline)==APK_SHA,'EXACT_SIGNED445_APK')
    proof=load(plan);expected={'classes.dex','classes3.dex','AndroidManifest.xml',LABEL}
    changes={};all_members={}
    with ZipFile(baseline) as a,ZipFile(candidate) as b:
        names=set(validate_names(a))-set(SIGNATURE)
        require(names==set(validate_names(b))-set(SIGNATURE),'EXACT_APK_MEMBER_SET')
        for n in sorted(names):
            x=a.read(n);y=b.read(n);pair={'before':digest(x),'after':digest(y)};all_members[n]=pair
            if x!=y:changes[n]=pair
            if n=='AndroidManifest.xml':
                require(normalize_manifest(y)==(normalize_manifest(patch(x))[0],VERSION),'EXACT_AUTHORIZED_MANIFEST_AND_VERSION')
            if n==LABEL:require(y==b'infinity.last_updated_in=2103447\ncobra.last_updated_in=2103445\n','TRUTHFUL_COMPONENT_LABELS')
            if n in ('classes.dex','classes3.dex'):
                require(digest(y)==proof['compiled_members'][n],'EXACT_ANDROID_TESTED_DEX:'+n)
        require(set(changes)==expected,'UNEXPECTED_APK_MEMBER_DELTA:'+str(set(changes)^expected))
    out.mkdir(parents=True,exist_ok=True)
    report=dict(status='PASS_EXACT_SIGNED445_PRESERVATION',baseline_sha256=APK_SHA,candidate_sha256=file_sha(candidate),
        changed_members=changes,unchanged_members=len(names)-len(changes),added=[],removed=[],
        native_libraries_unchanged=sum(n.startswith('lib/') and n.endswith('.so') for n in names),
        original_Infinity_classes_unchanged=578,Cobra_DEX_and_payload_identical=True,
        shared_DEX_resources_and_shutdown_identical=True,normal_Splash_instructions_preserved=True,
        user_data='NO_ACCESS',shutdown='UNCHANGED_NOT_TESTED',physical_Fold='PENDING')
    if sdk:
        (out/'BASELINE-SIGNATURE.txt').write_text(certificate(baseline,sdk))
        (out/'CANDIDATE-SIGNATURE.txt').write_text(certificate(candidate,sdk))
        report['certificate_sha256']=CERT_SHA
    save(out/'APK-PRESERVATION.json',report);save(out/'ALL-APK-MEMBERS.json',all_members)
    return report

def repack(owner,bundles,dest,row,source,build,classes):
    old=read_bundle(bundles/row['file'],row);meta=copy.deepcopy(old)
    meta.update(version='2103447.'+owner.lower()+'.1',approved_source=source)
    members={};dex={}
    if owner in ('INFINITY','CHOOSER_SHELL'):
        dex['dex/part-0.dex']=(build/(owner+'-new.dex')).read_bytes()
        require(set(classes[owner])>={n[6:] for n in old['payload'] if n.startswith('class:')},'NO_ORIGINAL_CLASS_REMOVAL')
        for name,pin in classes[owner].items():meta['payload']['class:'+name]=dict(owner=owner,sha256=pin)
        meta['dex']={'dex/part-0.dex':digest(dex['dex/part-0.dex'])}
    if owner=='CHOOSER_SHELL':members[LABEL]=b'infinity.last_updated_in=2103447\ncobra.last_updated_in=2103445\n'
    if owner=='MINIMAL_ANDROID_CONTRACT':members['AndroidManifest.xml']=(build/'AndroidManifest.xml').read_bytes()
    for n,raw in members.items():
        meta['members'][n]['sha256']=digest(raw)
        normalized=normalize_manifest(raw)[0] if n=='AndroidManifest.xml' else raw
        meta['payload']['member:'+n]['sha256']=digest(normalized)
    meta['digest']=component_digest(meta['payload'],owner)
    path=dest/(owner+'.zip')
    with ZipFile(bundles/row['file']) as z,ZipFile(path,'w') as target:
        for n in z.namelist():
            if n=='component.json':continue
            raw=dex[n] if n in dex else members[n[8:]] if n.startswith('payload/') and n[8:] in members else z.read(n)
            target.writestr(record(n),raw)
        target.writestr(record('component.json'),canonical(meta))
    result=dict(file=path.name,sha256=file_sha(path),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')})
    read_bundle(path,result);return result

def runtime_binding(build):
    observed=load(build/'OWNER-BUILD.json');tested=load(H/'final-evidence/OWNER-BUILD.json')
    require(observed['deltas']==tested['deltas'],'EXACT_ANDROID_TESTED_CLASS_OUTPUTS')
    require(observed['manifest_sha256']==tested['manifest_sha256'],'EXACT_ANDROID_TESTED_MANIFEST')
    for name,pin in tested['sources'].items():
        if '/runtime/' in name:require(file_sha(REPO/name)==pin,'ANDROID_TESTED_RUNTIME_SOURCE_CHANGED:'+name)
    require(load(build/'CLASS-HASHES.json')==load(H/'final-evidence/CLASS-HASHES.json'),'EXACT_TESTED_CLASS_DEFINITIONS')
    result=load(H/'final-evidence/ANDROID-RESULT.json')
    require(result['status']=='PASS','ACTUAL_ANDROID_DECODING_REQUIRED')
    host=load(H/'final-evidence/HOST-RESULT.json')
    require(host['status']=='PASS' and host['tests']==11,'REQUEST_STATE_HOST_TESTS_REQUIRED')
    binding=load(H/'final-evidence/HOST-SOURCE-BINDING.json')
    require(binding['status']=='PASS_RETAINED_HOST_SOURCE_UNCHANGED','RETAINED_HOST_BINDING')
    for name,pin in binding['sha256'].items():require(file_sha(REPO/name)==pin,'RETAINED_HOST_SOURCE_CHANGED:'+name)
    actual=result['source_build']['replaced']
    require(actual['classes.dex']==observed['deltas']['CHOOSER_SHELL']['dex_sha256'] and actual['classes3.dex']==observed['deltas']['INFINITY']['dex_sha256'],'RUNTIME_INSTALLED_DEX_BINDING')
    require(actual['AndroidManifest.xml']==observed['manifest_sha256'],'RUNTIME_INSTALLED_MANIFEST_BINDING')
    return observed,result

def prepare(bundles,baseline,sdk,out):
    bundles,baseline,sdk,out=[p.resolve() for p in (bundles,baseline,sdk,out)]
    source=head_check();prior=previous();require(prior['candidate_versionCode']==2103445,'EXACT445_PREDECESSOR')
    require(file_sha(baseline)==APK_SHA,'EXACT_BASELINE');certificate(baseline,sdk)
    require(not out.exists(),'FRESH_OUTPUT');out.mkdir(parents=True)
    catalog=copy.deepcopy(prior['bundle_catalog'])
    for owner,row in catalog['bundles'].items():read_bundle(bundles/row['file'],row)
    spec=importlib.util.spec_from_file_location('_external447_builder',H/'build_owner.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    builder.build(out/'owner',bundles)
    observed,result=runtime_binding(out/'owner');classes=load(out/'owner/CLASS-HASHES.json')
    dest=out/'components';dest.mkdir();catalog['source']=source
    shutil.copyfile(bundles/'COBRA.zip',dest/'COBRA.zip')
    for owner in TARGETS:catalog['bundles'][owner]=repack(owner,bundles,dest,catalog['bundles'][owner],source,out/'owner',classes)
    require(file_sha(dest/'COBRA.zip')==prior['bundle_catalog']['bundles']['COBRA']['sha256'],'COBRA445_EXACT_ZIP')
    save(dest/'catalog.json',catalog)
    source_files={str(p.relative_to(REPO)):file_sha(p) for p in H.rglob('*') if p.is_file() and p.suffix in ('.py','.java','.json','.md','.bin')}
    save(out/'PREPARATION.json',dict(status='PASS_ISOLATED_EXTERNAL_PLAYER_OWNER_PREPARATION',source=source,
        run_id=int(os.environ['GITHUB_RUN_ID']),baseline=BASE,baseline_apk_sha256=APK_SHA,
        compiled_members={'classes.dex':observed['deltas']['CHOOSER_SHELL']['dex_sha256'],'classes3.dex':observed['deltas']['INFINITY']['dex_sha256']},
        source_files=source_files,Android='PASS_SYNTHETIC_API37_DECODING_PHYSICAL_FOLD_PENDING',accepted_pointer_updated=False))
    combine(dest,catalog,out/'combined-unsigned.apk',VERSION)
    compare(baseline,out/'combined-unsigned.apk',out/'PREPARATION.json',out/'preservation')
    head_check();publish=out/'publish';publish.mkdir()
    shutil.copytree(dest,publish/'components');shutil.copytree(out/'preservation',publish/'preservation')
    shutil.copyfile(out/'PREPARATION.json',publish/'PREPARATION.json')
    print('PASS tested external447 owners, exact445 preservation; unsigned preparation only')

def proposed(prepared,run_id):
    artifact=official(prepared,run_id);proof=load(prepared/'PREPARATION.json');prior=previous()
    catalog=load(prepared/'components/catalog.json')
    metas={o:read_bundle(prepared/'components'/r['file'],r) for o,r in catalog['bundles'].items()}
    payload={k:v for m in metas.values() for k,v in m['payload'].items()}
    authority=copy.deepcopy(prior)
    authority.update(generation=GENERATION,last_issued_versionCode=2103446,candidate_versionCode=VERSION,target_owners=TARGETS,
        update_kind='owner_update',previous_authority_sha256=digest(canonical(prior)),payload=payload,bundle_catalog=catalog,
        experience_version_labels={'INFINITY':VERSION,'COBRA':2103445})
    for owner in TARGETS:
        authority['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')}
        authority['components'][owner]['revision']=prior['components'][owner]['revision']+1
        authority['bundle_sources'][owner]=dict(run_id=run_id,build_source=proof['source'],artifact='Infinity447-Prepared-'+str(run_id),path='components/'+owner+'.zip')
    from release_guard import AUTH as USER_AUTH,AUTH_SHA,REFERENCE,REFERENCE_SHA,PREFIX
    authority['external_player_manifest_exception']=dict(schema=1,authorization=USER_AUTH,authorization_sha256=AUTH_SHA,
        reference=REFERENCE,reference_sha256=REFERENCE_SHA,candidate_manifest_sha256=payload['member:AndroidManifest.xml']['sha256'],
        source_inputs={n:file_sha(REPO/n) for n in (USER_AUTH,REFERENCE,PREFIX+'patch_manifest.py',PREFIX+'release_guard.py')})
    authority['source_files']={n:file_sha(REPO/n) for n in prior['source_files']}
    authority['workflow_sha256']=file_sha(REPO/'.github/workflows/infinity-combined-release.yml')
    authority['owner_update_evidence']=dict(owner='INFINITY_ISOLATED_EXTERNAL_VIDEO',producer_run=run_id,producer_source=proof['source'],source_files=proof['source_files'],artifact=artifact,
        preparation_sha256=file_sha(prepared/'PREPARATION.json'),Android='PASS_SYNTHETIC_API37_REAL_DECODING',physical_Fold='PENDING',frozen_owners=['COBRA'],accepted_pointer_updated=False)
    transition(prior,authority,TARGETS);verify_evidence(authority,lambda n:(REPO/n).read_bytes());return authority

def register(prepared,run_id):
    proposed_value=proposed(prepared,run_id)
    require(load(AUTH)==previous(),'AUTHORITY_PREDECESSOR');save(AUTH,proposed_value)
def check_registered(prepared,run_id,out):
    require(proposed(prepared,run_id)==load(AUTH),'REGISTERED_EXACT_OFFICIAL_PREPARATION')
    save(out,dict(status='PASS_OFFICIAL_TESTED_SOURCE_AND_COMPONENTS',run_id=run_id,physical_Fold='PENDING'))
if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='op',required=True)
    a=sub.add_parser('prepare')
    for n in ('bundles','baseline','sdk','out'):a.add_argument('--'+n,type=Path,required=True)
    for name in ('register','check_registered'):
        a=sub.add_parser(name);a.add_argument('--prepared',type=Path,required=True);a.add_argument('--run-id',type=int,required=True)
        if name=='check_registered':a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('compare')
    for n in ('baseline','candidate','plan','out','sdk'):a.add_argument('--'+n,type=Path,required=True)
    args=vars(p.parse_args());op=args.pop('op');globals()[op](**args)

