"""Source-bound proposals for the unchanged original owner release authority."""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import subprocess
import prepare_modules as prep

AUTHORITY='repairs/dual-experience-isolation-2103420/release-authority.json'
WORKFLOW='.github/workflows/infinity-combined-release.yml'
CANONICAL='bd46fa73c713ed869f75822fab1b0821a7d2d11b'
TARGETS=['INFINITY','CHOOSER_SHELL']

def load(path):return json.loads(path.read_bytes())
def git(*args):return subprocess.check_output(['git',*map(str,args)],cwd=prep.ROOT)
def original_intake():
    p=prep.ROOT/'repairs/infinity-tracking-integration-2103469-20261108/tracking_module_fixture.py'
    assert prep.sha(p.read_bytes())=='af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb'
    spec=importlib.util.spec_from_file_location('retained_official_intake',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def sources():
    request=load(prep.HERE/'SIGN-REQUEST.json');result=dict(request['source_bindings'])
    for name,wanted in result.items():
        p=Path(name);assert not p.is_absolute() and '..' not in p.parts and prep.sha((prep.ROOT/p).read_bytes())==wanted,name
    result[(prep.HERE/'SIGN-REQUEST.json').relative_to(prep.ROOT).as_posix()]=prep.sha((prep.HERE/'SIGN-REQUEST.json').read_bytes())
    return result

def intake(prepared,version):
    assert version in (2103480,2103481)
    t=prep.tools();import release_authority as authority
    pin=load(prep.HERE/'PREPARED-PAIR-PIN.json');row=pin['artifacts'][str(version)]
    assert pin['run']==42829229209 and pin['source']=='82c6144c9357182e237f536f280b57ba4b59c5de'
    recipe=prep.HERE/'prepare_apk.py';assert recipe.read_bytes()==git('show',pin['source']+':'+recipe.relative_to(prep.ROOT).as_posix())
    assert prep.sha((prepared.parent/'artifact.zip').read_bytes())==row['digest'].removeprefix('sha256:')
    proof=load(prepared/'PREPARATION.json');assert proof['source_commit']==pin['source']
    assert proof['versionCode']==version and proof['recovery'] is (version==2103481)
    assert proof['baseline_versionCode']==2103477 and proof['baseline_sha256']==prep.BASE_APK and proof['networking_inputs'] is False
    assert proof['native_sha256']=='ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
    label='recovery' if proof['recovery'] else 'candidate'
    expected=load(prep.HERE/'MODULE-PREPARE-REQUEST.json')['expected_outputs'][label]
    assert proof['module_manifest_sha256']==expected['manifest_sha256'] and proof['module_count']==80 and proof['CC']==expected['CC']
    catalog=load(prepared/'components/catalog.json');metas={owner:t.read_bundle(prepared/'components'/data['file'],data) for owner,data in catalog['bundles'].items()}
    base=json.loads(git('show',CANONICAL+':'+AUTHORITY))
    for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):assert catalog['bundles'][owner]==base['bundle_catalog']['bundles'][owner]
    audit=prepared/'MODULE-UPGRADE-RECOVERY.json';assert prep.sha(audit.read_bytes())==proof['original_module_audit_sha256'] and load(audit)['original_installer_changed'] is False
    report=load(prepared/'APK-PRESERVATION.json');assert report['status']=='PASS_EXACT77_TWO_FILE_PERFORMANCE_OR_FORWARD_RECOVERY'
    assert report['changed_members']==proof['changed_members'] and report['all_layout_provider_Cobra_members_unchanged'] is True
    return t,authority,pin,row,proof,catalog,metas

def download(version,out):
    pin=load(prep.HERE/'PREPARED-PAIR-PIN.json');m=original_intake()
    root=m.download(dict(pin['artifacts'][str(version)],run=pin['run'],source=pin['source']),out);intake(root,version);return root

def baseline(out):
    m=original_intake();row=load(prep.HERE/'INPUT-ARTIFACTS.json')['signed77'];root=m.download(row,out)
    p=root/'Infinity-2103477-Combined-Original-Signer.apk';assert prep.sha(p.read_bytes())==prep.BASE_APK;return p

def issued_candidate(path):
    pin=load(prep.HERE/'SIGNED-CANDIDATE-PIN.json');assert pin['version']==2103480
    m=original_intake();row=dict(pin['artifact'],run=pin['run'],source=pin['source'])
    run=m.api('actions/runs/'+str(pin['run']));assert run['workflow_id']==397702717 and run['head_sha']==pin['source'] and run['conclusion']=='success'
    meta=m.api('actions/artifacts/'+str(row['id']))
    assert not meta['expired'] and meta['workflow_run']['id']==pin['run'] and all(meta[k]==row[k] for k in ('id','name','digest','size_in_bytes'))
    archive=path.parent/'artifact.zip';assert archive.stat().st_size==row['size_in_bytes'] and prep.sha(archive.read_bytes())==row['digest'].removeprefix('sha256:')
    from zipfile import ZipFile
    with ZipFile(archive) as z:
        for name in ('BUILD-RECEIPT.json','SIGNATURE.txt','SIGNED-77-PRESERVATION.json','Infinity-2103480-Combined-Original-Signer.apk'):assert z.read(name)==(path/name).read_bytes(),name
    receipt=load(path/'BUILD-RECEIPT.json');assert receipt['versionCode']==2103480 and receipt['source']==pin['source']
    assert receipt['signed_apk_sha256']==pin['APK_sha256']==prep.sha((path/'Infinity-2103480-Combined-Original-Signer.apk').read_bytes())
    assert receipt['certificate_sha256']=='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
    signature=(path/'SIGNATURE.txt').read_text()
    for scheme in ('v1','v2','v3'):assert any(line.startswith('Verified using '+scheme+' scheme') and line.endswith(': true') for line in signature.splitlines())
    return pin

def propose(prepared,version,previous,out,predecessor=None):
    t,a,pin,row,proof,catalog,metas=intake(prepared,version);before=load(previous)
    if version==2103480:
        assert before==json.loads(git('show',CANONICAL+':'+AUTHORITY)) and before['generation']==62
        last=2103479
    else:
        signed=issued_candidate(predecessor);assert before==json.loads(git('show',signed['source']+':'+AUTHORITY))
        assert before['generation']==63 and before['candidate_versionCode']==2103480;last=2103480
    result=copy.deepcopy(before)
    result.update(generation=before['generation']+1,last_issued_versionCode=last,candidate_versionCode=version,previous_authority_sha256=prep.sha(t.canonical(before)),target_owners=TARGETS,update_kind='owner_update',payload={k:v for meta in metas.values() for k,v in meta['payload'].items()},bundle_catalog=catalog,experience_version_labels={'INFINITY':version,'COBRA':2103445},workflow_sha256=prep.sha((prep.ROOT/WORKFLOW).read_bytes()))
    for owner in TARGETS:
        result['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')};result['components'][owner]['revision']=before['components'][owner]['revision']+1
        result['bundle_sources'][owner]=dict(run_id=pin['run'],build_source=pin['source'],artifact=row['name'],path='components/'+owner+'.zip')
    result['owner_update_evidence']=dict(owner='INFINITY_PERFORMANCE_FORWARD_RECOVERY_TO77' if proof['recovery'] else 'INFINITY_PERFORMANCE_ENGINEERING_CANDIDATE',producer_run=pin['run'],producer_source=pin['source'],artifact=row,source_files=sources(),preparation_sha256=prep.sha((prepared/'PREPARATION.json').read_bytes()),immutable_functional_base=2103477,baseline_APK_sha256=prep.BASE_APK,native_sha256=proof['native_sha256'],CC=proof['CC'],skin=proof['skin'],module_manifest_sha256=proof['module_manifest_sha256'],module_source_count=80,module_upgrade_recovery_sha256=proof['original_module_audit_sha256'],frozen_network_versions_preserved=[2103478,2103479],networking_inputs=False,Cobra_changes=False,experimental=True,engineering_QA_only=True,publication=False,public_release=False,owner_delivery_cleared=False,accepted_pointer_updated=False,Android='WORKER_PASS42827490004_SIGNED_APK_INSTALL_RECOVERY_PENDING',physical_Fold='PENDING_OWNER',verification_toolchain=before['owner_update_evidence']['verification_toolchain'])
    a.transition(before,result,TARGETS);a.verify_evidence(result,lambda name:(prep.ROOT/name).read_bytes());prep.save(out,result)
    print('PASS exact owner authority proposal; no ref mutation or signing')

def check(prepared,version,out):
    t,a,pin,row,proof,catalog,metas=intake(prepared,version);registered=load(prep.ROOT/AUTHORITY)
    assert registered['candidate_versionCode']==version and registered['generation']==(63 if version==2103480 else 64)
    assert registered['owner_update_evidence']['producer_source']==pin['source'] and registered['bundle_catalog']==catalog
    assert registered['owner_update_evidence']['source_files']==sources()
    verified=a.verify(registered,{k:v['sha256'] for meta in metas.values() for k,v in meta['payload'].items()},version,registered['generation'])
    a.verify_evidence(registered,lambda name:(prep.ROOT/name).read_bytes());prep.save(out,dict(status='PASS_EXACT_REGISTERED_PERFORMANCE_OWNER_PAYLOAD',version=version,generation=registered['generation'],official_artifact=row,verification=verified,Android='SIGNED_APK_PENDING',owner_delivery_cleared=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('download','baseline','propose','check'));p.add_argument('--version',type=int);p.add_argument('--out',type=Path,required=True);p.add_argument('--prepared',type=Path);p.add_argument('--previous',type=Path);p.add_argument('--predecessor',type=Path);a=p.parse_args()
    if a.operation=='download':download(a.version,a.out)
    elif a.operation=='baseline':baseline(a.out)
    elif a.operation=='propose':propose(a.prepared,a.version,a.previous,a.out,a.predecessor)
    else:check(a.prepared,a.version,a.out)
