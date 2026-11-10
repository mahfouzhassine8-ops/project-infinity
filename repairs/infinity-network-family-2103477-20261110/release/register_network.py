"""Propose/check the original owner authority; never signs or mutates a Git ref."""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import prepare_modules as prep

AUTHORITY = 'repairs/dual-experience-isolation-2103420/release-authority.json'
WORKFLOW = '.github/workflows/infinity-combined-release.yml'
SOURCE = '5e19f2ba861b51f23918594c68ee1edaaacb65f3'
CANONICAL = 'dfee7205dd88abe81db5e263c368f67ece43df02'
TARGETS = ['INFINITY', 'CHOOSER_SHELL']


def load(path):
    return json.loads(path.read_bytes())


def git(*args):
    return subprocess.check_output(['git', *map(str,args)], cwd=prep.ROOT)


def tools():
    t = prep.tools()
    import release_authority
    assert Path(release_authority.__file__).resolve() == prep.ROOT/'repairs/dual-experience-isolation-2103420/release_authority.py'
    path = prep.HERE/'prepare_apk.py'
    assert path.read_bytes() == git('show', SOURCE+':'+path.relative_to(prep.ROOT).as_posix())
    spec=importlib.util.spec_from_file_location('frozen_network_apk_preparation',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return t, release_authority, module


def intake(prepared, version):
    assert version in (2103478,2103479)
    t, authority, recipe = tools()
    pin = load(prep.HERE/'PREPARED-PAIR-PIN.json')
    assert pin['run'] == 42763160667 and pin['source'] == SOURCE
    row=pin['artifacts'][str(version)]
    assert prep.sha((prepared.parent/'artifact.zip').read_bytes()) == row['digest'].removeprefix('sha256:')
    proof=load(prepared/'PREPARATION.json')
    assert proof['source_commit']==SOURCE and proof['baseline_versionCode']==2103477 and proof['baseline_sha256']==prep.BASE_APK
    assert proof['versionCode']==version and proof['recovery'] is (version==2103479)
    assert proof['production_resolver']=='ORIGINAL_KODI' and proof['public_release'] is False
    approved=json.loads(git('show',SOURCE+':'+str((prep.HERE/'APK-PREPARE-REQUEST.json').relative_to(prep.ROOT))))
    label='recovery' if proof['recovery'] else 'candidate'
    assert proof['changed_members']==approved['expected_changes'][label]
    catalog=load(prepared/'components/catalog.json')
    metas={owner:t.read_bundle(prepared/'components'/data['file'],data) for owner,data in catalog['bundles'].items()}
    base=json.loads(git('show',CANONICAL+':'+AUTHORITY))
    for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
        assert catalog['bundles'][owner]==base['bundle_catalog']['bundles'][owner], owner
    assert prep.sha((prepared/'MODULE-UPGRADE-RECOVERY.json').read_bytes())==proof['original_module_audit_sha256']
    audit=load(prepared/'MODULE-UPGRADE-RECOVERY.json')
    assert audit['status']=='PASS_FOUR_AFFECTED_ORIGINAL_INSTALLER_CASES' and audit['original_installer_changed'] is False
    report=load(prepared/'APK-PRESERVATION.json')
    assert report['status']=='PASS_EXACT77_ONLY_DECLARED_NETWORK_OR_FORWARD_RECOVERY_MEMBERS'
    assert report['changed_members']==proof['changed_members'] and report['Cobra_members_unchanged'] is True
    return t, authority, recipe, pin, row, proof, catalog, metas


def download(version, out):
    pin=load(prep.HERE/'PREPARED-PAIR-PIN.json')
    assert version in (2103478,2103479) and pin['source']==SOURCE
    helper=prep.ROOT/'repairs/infinity-tracking-integration-2103469-20261108/tracking_module_fixture.py'
    assert prep.sha(helper.read_bytes())=='af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb'
    t=prep.tools()
    spec=importlib.util.spec_from_file_location('original_network_artifact_intake',helper)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    row=dict(pin['artifacts'][str(version)],run=pin['run'],source=pin['source'])
    root=m.download(row,out)
    intake(root,version)
    return root


def baseline(out):
    helper=prep.ROOT/'repairs/infinity-tracking-integration-2103469-20261108/tracking_module_fixture.py'
    assert prep.sha(helper.read_bytes())=='af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb'
    spec=importlib.util.spec_from_file_location('original_signed77_intake',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    row=load(prep.HERE/'INPUT-ARTIFACTS.json')['signed77']
    root=module.download(row,out)
    apk=root/'Infinity-2103477-Combined-Original-Signer.apk'
    assert prep.sha(apk.read_bytes())==prep.BASE_APK
    return apk


def sources():
    request=load(prep.HERE/'SIGN-REQUEST.json')
    bindings=request['source_bindings']
    for name,wanted in bindings.items():
        p=Path(name)
        assert not p.is_absolute() and '..' not in p.parts
        assert prep.sha((prep.ROOT/p).read_bytes())==wanted,name
    return dict(bindings, **{str((prep.HERE/'SIGN-REQUEST.json').relative_to(prep.ROOT)):
                              prep.sha((prep.HERE/'SIGN-REQUEST.json').read_bytes())})


def issued_candidate(prepared=None):
    """Authenticate the actual original-signed predecessor, not just a green run."""
    signed=load(prep.HERE/'SIGNED-CANDIDATE-PIN.json')
    assert signed['version']==2103478
    helper=prep.ROOT/'repairs/infinity-tracking-integration-2103469-20261108/tracking_module_fixture.py'
    assert prep.sha(helper.read_bytes())=='af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb'
    spec=importlib.util.spec_from_file_location('original_signed78_receipt_intake',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='network-original-signed78-') as tmp:
        if prepared is None:
            root=module.download(dict(signed['artifact'],run=signed['run'],source=signed['source']),Path(tmp)/'input')
        else:
            # Reuse a retained download, with the same live provenance and whole-ZIP checks.
            row=dict(signed['artifact'],run=signed['run'],source=signed['source'])
            run=module.api('actions/runs/'+str(row['run']))
            assert run['workflow_id']==397702717 and run['path']==module.WORKFLOW and run['head_sha']==row['source'] and run['status']=='completed' and run['conclusion']=='success'
            meta=module.api('actions/artifacts/'+str(row['id']))
            assert not meta['expired'] and meta['workflow_run']['id']==row['run'] and all(meta[k]==row[k] for k in ('id','name','digest','size_in_bytes'))
            archive=prepared.parent/'artifact.zip'
            assert archive.stat().st_size==row['size_in_bytes'] and 'sha256:'+prep.sha(archive.read_bytes())==row['digest']
            # Read the checked archive itself; a retained extraction alone is not authority.
            from zipfile import ZipFile
            with ZipFile(archive) as z:
                for name in ('BUILD-RECEIPT.json','SIGNATURE.txt','SIGNED-77-PRESERVATION.json','Infinity-2103478-Combined-Original-Signer.apk'):
                    assert z.read(name)==(prepared/name).read_bytes(),name
            root=prepared
        receipt=load(root/'BUILD-RECEIPT.json')
        assert receipt['versionCode']==2103478 and receipt['source']==signed['source']
        assert receipt['certificate_sha256']=='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
        assert receipt['signed_apk_sha256']==signed['APK_sha256']==prep.sha((root/'Infinity-2103478-Combined-Original-Signer.apk').read_bytes())
        assert prep.sha((root/'BUILD-RECEIPT.json').read_bytes())==signed['receipt_sha256']
        assert receipt['accepted_pointer_updated'] is False
        signature=(root/'SIGNATURE.txt').read_text()
        assert receipt['certificate_sha256'] in signature
        for scheme in ('v1','v2','v3'):
            assert any(line.startswith('Verified using '+scheme+' scheme') and line.endswith(': true') for line in signature.splitlines())
        assert load(root/'SIGNED-77-PRESERVATION.json')['status']=='PASS_EXACT77_ONLY_DECLARED_NETWORK_OR_FORWARD_RECOVERY_MEMBERS'
    return signed


def propose(prepared, version, previous, out, predecessor=None):
    t,a,recipe,pin,row,proof,catalog,metas=intake(prepared,version)
    before=load(previous)
    if version==2103478:
        assert before==json.loads(git('show',CANONICAL+':'+AUTHORITY)), 'EXACT_LAST_CANONICAL75_PREDECESSOR'
        last_issued=2103477
    else:
        signed=issued_candidate(predecessor)
        assert before==json.loads(git('show',signed['source']+':'+AUTHORITY))
        assert before['generation']==60 and before['candidate_versionCode']==2103478
        last_issued=2103478
    result=copy.deepcopy(before)
    result.update(generation=before['generation']+1,last_issued_versionCode=last_issued,
                  candidate_versionCode=version,previous_authority_sha256=prep.sha(t.canonical(before)),
                  target_owners=TARGETS,update_kind='owner_update',
                  payload={k:v for meta in metas.values() for k,v in meta['payload'].items()},
                  bundle_catalog=catalog,experience_version_labels={'INFINITY':version,'COBRA':2103445},
                  workflow_sha256=prep.sha((prep.ROOT/WORKFLOW).read_bytes()))
    for owner in TARGETS:
        result['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')}
        result['components'][owner]['revision']=before['components'][owner]['revision']+1
        result['bundle_sources'][owner]=dict(run_id=pin['run'],build_source=pin['source'],artifact=row['name'],path='components/'+owner+'.zip')
    result['owner_update_evidence']=dict(
        owner='INFINITY_NETWORK_FORWARD_RECOVERY_TO77' if proof['recovery'] else 'INFINITY_NETWORK_ENGINEERING_QA',
        producer_run=pin['run'],producer_source=pin['source'],artifact=row,
        source_files=sources(),preparation_sha256=prep.sha((prepared/'PREPARATION.json').read_bytes()),
        immutable_functional_base=2103477,baseline_APK_sha256=prep.BASE_APK,
        native_sha256=proof['native_sha256'],CC=proof['CC'],skin=proof['skin'],
        module_manifest_sha256=proof['module_manifest_sha256'],module_source_count=proof['module_count'],
        module_upgrade_recovery_sha256=proof['original_module_audit_sha256'],
        issuance_reconciliation=dict(previous_canonical=CANONICAL,previous_registered_candidate=2103475,
            actual_signed76_run=42719403128,actual_signed77_run=42724088145,
            actual_signed76_APK_sha256='6f5a90c548c41f0a38b8420010419f15939b6d2b731fc0e87588d2944560e6f7',
            actual_signed77_APK_sha256=prep.BASE_APK,no_claim_76_or77_were_historically_registered=True),
        DNS_contract='OWNER_APPROVED_BASELINE_COMPARISON;ORIGINAL_RESOLVER;HISTORICAL_HARD_DEADLINE_FAIL_RETAINED',
        resolver_helpers_or_replacement_included=False,Cobra_changes=False,
        experimental=True,engineering_QA_only=True,publication=False,public_release=False,
        owner_delivery_cleared=False,accepted_pointer_updated=False,
        remaining_unverified=['Actual Android UI/mode/connections/fallback/cancellation/playback',
                             'Signed in-place Android installation and forward recovery',
                             'One final physical Galaxy Fold owner acceptance'],
        Android='PENDING_INTERNAL_QA_NOT_OWNER_DELIVERY',physical_Fold='PENDING_OWNER',
        verification_toolchain=before['owner_update_evidence']['verification_toolchain'])
    a.transition(before,result,TARGETS)
    a.verify_evidence(result,lambda name:(prep.ROOT/name).read_bytes())
    prep.save(out,result)
    print('PASS original authority transition/evidence; exact77 owner-preserved internal QA proposal; no ref mutation or signing')


def check_registered(prepared, version, out):
    t,a,recipe,pin,row,proof,catalog,metas=intake(prepared,version)
    registered=load(prep.ROOT/AUTHORITY)
    assert registered['candidate_versionCode']==version and registered['generation']==(60 if version==2103478 else 61)
    assert registered['owner_update_evidence']['producer_source']==SOURCE
    assert registered['owner_update_evidence']['artifact']==row and registered['bundle_catalog']==catalog
    assert registered['owner_update_evidence']['source_files']==sources()
    actual={k:v['sha256'] for meta in metas.values() for k,v in meta['payload'].items()}
    verified=a.verify(registered,actual,version,registered['generation'])
    a.verify_evidence(registered,lambda name:(prep.ROOT/name).read_bytes())
    prep.save(out,dict(status='PASS_EXACT_REGISTERED_NETWORK_OWNER_PAYLOAD',version=version,
                      generation=registered['generation'],official_artifact=row,verification=verified,
                      owner_delivery_cleared=False,Android='PENDING_INTERNAL_QA'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['download','baseline','propose','check'])
    p.add_argument('--version',type=int);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--prepared',type=Path);p.add_argument('--previous',type=Path)
    p.add_argument('--predecessor',type=Path)
    args=p.parse_args()
    if args.operation=='baseline':baseline(args.out)
    elif args.operation=='download':download(args.version,args.out)
    elif args.operation=='propose':propose(args.prepared,args.version,args.previous,args.out,args.predecessor)
    else:check_registered(args.prepared,args.version,args.out)
