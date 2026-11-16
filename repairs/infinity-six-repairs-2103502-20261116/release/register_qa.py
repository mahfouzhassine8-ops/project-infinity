"""502-derived QA/recovery adapter for the established owner/signing gates.

Execute only on the canonical release branch, after independent review and a
frozen request. Development and every payload byte still originate in 502.
"""
from pathlib import Path
from zipfile import ZipFile
import copy, hashlib, json, os, re, shutil, subprocess, sys

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
PARENT='4c6bc0b4a06828f43639761e481c1d42d2fcbc34'
for name in ('common_release.py','prepare_release.py','patch_cast_manifest.py'):
    path=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'/name
    assert path.read_bytes()==subprocess.check_output(['git','show',PARENT+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT),'UNCHANGED_IMPORTED_RELEASE_HELPER:'+name
sys.path.insert(0,str(ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'))
import common_release as c
import prepare_release as old
import owner_bundles as owned
import recovery_metadata

BASE='f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28'
BASE_AUTHORITY='92bef1bcf056abf58d6754354173565e56f907ac'
VERSIONS={'candidate':2103504,'recovery':2103505}
LABEL='assets/experience-component-updates.properties'
CC='assets/addons/script.infinity.commandcenter/'
ORIGINAL_TOOLS=c.tools

def canonical_hash(value):return c.digest(json.dumps(value,sort_keys=True,separators=(',',':')).encode())

def reviewed_tools():
    result=ORIGINAL_TOOLS()
    path='repairs/dual-experience-isolation-2103420/signer-policy.json'
    previous=json.loads(c.git('show',PARENT+':'+path));expected=copy.deepcopy(previous)
    rows=c.load(TASK/'ROWS.json');review=c.load(TASK/'WORKFLOW-CATALOG-REVIEW.json')
    assert len(rows)==8 and all(row['original_key_access'] is False for row in rows)
    for row in rows:
        raw=c.git('show',row['source']+':'+row['path'])
        assert c.digest(raw)==row['workflow_sha256']
        assert b'secrets.INFINITY_' not in raw and b'assemble.py sign' not in raw
    expected['additional_unsigned_owner_workflows'].extend(rows)
    expected['reviewed_workflow_ids']=sorted(set(previous['reviewed_workflow_ids'])|{row['id'] for row in rows})
    assert c.load(ROOT/path)==expected,'SIGNER_POLICY_ONLY_REVIEWED_UNSIGNED_CATALOG'
    assert expected['sole_original_key_workflow_id']==397702717
    return result
c.tools=reviewed_tools

def request():
    c.context(True);r=c.load(TASK/'OWNER-QA-REQUEST.json');c.tools()
    assert r['baseline']==BASE and r['version_codes']==VERSIONS
    assert r['ContinuePlaying']=='DEFERRED_NOT_FIXED_UNCHANGED' and r['accepted_pointer_updated'] is False
    assert c.sha(ROOT/c.WORKFLOW)==r['workflow_sha256']
    required={str((TASK/name).relative_to(ROOT)) for name in
              ('register_qa.py','owner_bundles.py','recovery_metadata.py','ROWS.json','WORKFLOW-CATALOG-REVIEW.json')}
    assert set(r['source_bindings'])==required,'EXACT_RELEASE_ADAPTER_SOURCES_REQUIRED'
    for name,digest in r['source_bindings'].items():assert c.sha(ROOT/name)==digest,name
    raw=(TASK/'OWNER-QA-REVIEW.json').read_bytes();assert c.digest(raw)==r['review_sha256']
    review=json.loads(raw);assert review['reviewer']=='Astra' and review['status']=='PASS_SELECTED502_REGISTRATION_ADAPTER'
    fixed={name:r[name] for name in ('baseline','version_codes','ContinuePlaying','accepted_pointer_updated',
        'workflow_sha256','source_bindings','parent_authority_sha256','base','stage','owners',
        'recovery_modules','recovery_module_hashes','expected_changes','new_lock_classes','known_limitations')}
    assert canonical_hash(fixed)==review['reviewed_request_sha256']
    return r

def inputs(r):
    base=c.unique(c.obtain(r['base'],'six502-base'),'Infinity-2103502-Combined-Original-Signer.apk')
    assert c.sha(base)==BASE;c.signature(base)
    stage=c.obtain(r['stage'],'six502-stage');apk=c.unique(stage,'Infinity-2103504-Combined-QA-UNSIGNED-NOT-INSTALLABLE.apk')
    receipt=c.load(c.unique(stage,'COMBINED-QA-STAGING.json'))
    assert receipt['status']=='PASS_UNSIGNED_COMBINED_QA_PRESERVATION_NOT_INSTALLABLE'
    assert receipt['source']==r['stage']['source'] and receipt['changes']==r['expected_changes']
    assert c.sha(apk)==receipt['APK_sha256']
    recovery=c.obtain(r['recovery_modules'],'six502-recovery-modules')
    proof=c.load(recovery/'ORIGINAL-SIGNATURE-VERIFICATION.json')
    assert proof['module_version']=='0.3.5.85' and proof['code_restores_exact502'] is True
    assert proof['modules']==r['recovery_module_hashes']
    public=ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'
    subprocess.run(['openssl','dgst','-sha256','-verify',str(public),'-signature',str(recovery/'modules/script.infinity.commandcenter/INFINITY-MODULES.v1.sig'),str(recovery/'modules/script.infinity.commandcenter/INFINITY-MODULES.v1')],check=True,capture_output=True)
    preservation(base,apk,'candidate',r)
    return base,apk,recovery/'modules'

def preservation(base,apk,kind,r):
    inventory,cb,_,_,_=c.tools();changes={}
    with ZipFile(base) as before,ZipFile(apk) as after:
        names=set(inventory.validate_names(before))-inventory.SIGNATURE
        actual=set(inventory.validate_names(after))-inventory.SIGNATURE
        assert actual==names|({'classes7.dex'} if kind=='candidate' else set())
        for name in sorted(actual):
            a=old.member_sha(before,name) if name in names else None;b=old.member_sha(after,name)
            if a!=b:changes[name]={'before':a,'after':b}
        if kind=='candidate':assert changes==r['expected_changes'],'EXACT_SEVENTEEN_MEMBER_VECTOR'
        else:
            expected={'AndroidManifest.xml':c.digest(cb.set_version(before.read('AndroidManifest.xml'),VERSIONS[kind])),
                      LABEL:c.digest(('infinity.last_updated_in='+str(VERSIONS[kind])+'\ncobra.last_updated_in=2103445\n').encode())}
            expected.update({'assets/addons/'+name:h for name,h in r['recovery_module_hashes'].items() if name in {
                'script.infinity.commandcenter/addon.xml','script.infinity.commandcenter/INFINITY-MODULES.v1','script.infinity.commandcenter/INFINITY-MODULES.v1.sig'}})
            expected.update({name:c.digest(raw) for name,raw in recovery_metadata.replacements(before).items()})
            assert set(changes)==set(expected)
            assert all(changes[name]['after']==h for name,h in expected.items())
    return dict(status='PASS_EXACT502_SCOPED_QA_PRESERVATION',baseline=2103502,kind=kind,
                APK_sha256=c.sha(apk),changes=changes,ContinuePlaying='DEFERRED_NOT_FIXED_UNCHANGED',
                Cobra='UNCHANGED',physical_acceptance='PENDING_OWNER')

def prepare():
    r=request();inventory,cb,ra,rg,_=c.tools();current=c.load(ROOT/c.AUTHORITY)
    assert current['generation']==88 and current['candidate_versionCode']==2103503
    assert c.sha(ROOT/c.AUTHORITY)==r['parent_authority_sha256'],'LIVE_REGISTRY_RACE'
    baseline=json.loads(c.git('show',BASE_AUTHORITY+':'+c.AUTHORITY))
    assert baseline['generation']==87 and baseline['candidate_versionCode']==2103502
    base,stage,recovery=inputs(r);out=ROOT/'six502-prepared';out.mkdir()
    actual,version=rg.inspect_candidate(stage,c.jars(),out/'inspection')
    assert version==2103504
    parsed=owned._class_files(out/'inspection')
    payload=owned.payload(baseline['payload'],actual,r['new_lock_classes'],set(r['expected_changes']))
    original_root=c.obtain(r['owners'],'six502-baseline-owner-bundles')/'candidate/components'
    original_catalog=c.load(original_root/'catalog.json')
    assert original_catalog==baseline['bundle_catalog'],'EXACT502_OWNER_BUNDLES_REQUIRED'
    prior=current
    for kind,number in VERSIONS.items():
        dest=out/kind;dest.mkdir();apk=dest/('Infinity-'+str(number)+'-UNSIGNED.apk')
        if kind=='candidate':shutil.copyfile(stage,apk);selected_payload=copy.deepcopy(payload)
        else:
            with ZipFile(base) as before,ZipFile(apk,'w',allowZip64=True) as after:
                changes={'AndroidManifest.xml':cb.set_version(before.read('AndroidManifest.xml'),number),
                         LABEL:('infinity.last_updated_in='+str(number)+'\ncobra.last_updated_in=2103445\n').encode()}
                changes.update(recovery_metadata.replacements(before))
                for name,h in r['recovery_module_hashes'].items():
                    full='assets/addons/'+name
                    if old.member_sha(before,full)!=h:
                        assert full in {CC+n for n in ('addon.xml','INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig')}
                        changes[full]=(recovery/name).read_bytes();assert c.digest(changes[full])==h
                for name in before.namelist():
                    if name not in inventory.SIGNATURE:old.copy_entry(before,after,name,changes.get(name))
            selected_payload=copy.deepcopy(baseline['payload'])
            for name,raw in changes.items():
                if name!='AndroidManifest.xml':selected_payload['member:'+name]['sha256']=c.digest(raw)
        proof=preservation(base,apk,kind,r);c.save(dest/'PRESERVATION.json',proof)
        components=dest/'components';components.mkdir();catalog=copy.deepcopy(original_catalog)
        catalog.update(source=os.environ['GITHUB_SHA'],release_approved=False);metas={}
        for owner,row in catalog['bundles'].items():
            src=original_root/row['file'];dst=components/row['file'];cb.read_bundle(src,row)
            if owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
                shutil.copyfile(src,dst);meta=cb.read_bundle(dst,row)
            else:
                meta=owned.rewrite(src,dst,apk,owner,selected_payload,parsed,
                    r['new_lock_classes'] if kind=='candidate' else [],c.jars(),out/('bundle-'+kind+'-'+owner),
                    number,os.environ['GITHUB_SHA'],inventory,cb,old.copy_entry)
                row.update(sha256=c.sha(dst),**{k:meta[k] for k in ('version','digest','approved_source')});cb.read_bundle(dst,row)
            metas[owner]=meta
        (components/'catalog.json').write_bytes(inventory.canonical(catalog))
        proposed=copy.deepcopy(prior)
        proposed.update(generation=prior['generation']+1,candidate_versionCode=number,
            last_issued_versionCode=prior['candidate_versionCode'],previous_authority_sha256=inventory.digest(inventory.canonical(prior)),
            target_owners=['INFINITY','CHOOSER_SHELL'],update_kind='owner_update',payload=selected_payload,
            bundle_catalog=catalog,experience_version_labels=dict(INFINITY=number,COBRA=2103445),workflow_sha256=c.sha(ROOT/c.WORKFLOW))
        policy='repairs/dual-experience-isolation-2103420/signer-policy.json';proposed['source_files'][policy]=c.sha(ROOT/policy)
        for owner in proposed['target_owners']:
            proposed['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')}
            proposed['components'][owner]['revision']=prior['components'][owner]['revision']+1
            proposed['bundle_sources'][owner]=dict(run_id=int(os.environ['GITHUB_RUN_ID']),build_source=os.environ['GITHUB_SHA'],
                artifact='Infinity502-Consolidated-Registered-Preparation-'+os.environ['GITHUB_RUN_ID'],path=kind+'/components/'+owner+'.zip')
        proposed['owner_update_evidence']=dict(owner='INFINITY_SIX502_QA_'+kind.upper(),producer_run=int(os.environ['GITHUB_RUN_ID']),
            producer_source=os.environ['GITHUB_SHA'],baseline_APK_sha256=BASE,unsigned_sha256=c.sha(apk),
            source_files=dict(r['source_bindings'],**{str((TASK/'OWNER-QA-REQUEST.json').relative_to(ROOT)):c.sha(TASK/'OWNER-QA-REQUEST.json')}),
            deferred=['Continue Playing'],known_limitations=r['known_limitations'],Fold='PENDING_OWNER',accepted_pointer_updated=False,
            public_release=False,verification_toolchain=current['owner_update_evidence']['verification_toolchain'])
        ra.transition(prior,proposed,proposed['target_owners']);ra.verify_evidence(proposed,lambda name:(ROOT/name).read_bytes())
        ra.verify(proposed,{name:row['sha256'] for name,row in selected_payload.items()},number,proposed['generation'])
        (dest/'AUTHORITY-PROPOSAL.json').write_bytes(inventory.canonical(proposed));prior=proposed
    c.save(out/'PREPARATION.json',dict(status='PASS_REVIEWED502_QA_AND_TRUE_FORWARD_RECOVERY',source=os.environ['GITHUB_SHA'],
        base_sha256=BASE,registry_written=False,signed=False,application_native_or_DEX_rebuilt=False))
    shutil.rmtree(out/'inspection')

def selected():
    r=request();authority=c.load(ROOT/c.AUTHORITY);kind=r['active_kind']
    assert authority['generation']==(89 if kind=='candidate' else 90)
    assert authority['candidate_versionCode']==VERSIONS[kind]
    assert authority['owner_update_evidence']['owner']=='INFINITY_SIX502_QA_'+kind.upper()
    root=c.obtain(r['prepared'],'six502-frozen-preparation')/kind
    assert (root/'AUTHORITY-PROPOSAL.json').read_bytes()==(ROOT/c.AUTHORITY).read_bytes()
    apk=c.unique(root,'Infinity-'+str(VERSIONS[kind])+'-UNSIGNED.apk');base,_,_=inputs(r)
    preservation(base,apk,kind,r);assert c.sha(apk)==authority['owner_update_evidence']['unsigned_sha256']
    with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:output.write('apk='+str(apk)+'\ngeneration='+str(authority['generation'])+'\n')
    c.jars()

def post():
    r=request();kind=r['active_kind'];base,_,_=inputs(r);out=ROOT/'signed-six502'
    apk=c.unique(out,'Infinity-'+str(VERSIONS[kind])+'-Combined-Original-Signer.apk');c.signature(apk)
    c.save(out/'PRESERVATION.json',preservation(base,apk,kind,r));shutil.copyfile(ROOT/c.AUTHORITY,out/'release-authority.json')

if __name__=='__main__':{'prepare':prepare,'selected':selected,'post':post}[sys.argv[1]]()
