"""Read-only original-workflow admission before module key access.

No signing implementation, registry mutation, application test or device access.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE='5ee1c7ae0bbe295c311aa34c02f6b62688ccb5a7'
AUTHORITY='2aa41804821264581fe69e0fb1d10703e6583baf'
WORKFLOW='.github/workflows/infinity-combined-release.yml'
FEATURE_WORKFLOW='.github/workflows/infinity-saved-navigation-android.yml'
REPO='repos/mahfouzhassine8-ops/project-infinity/'


def command(*args):return subprocess.check_output(list(map(str,args)))
def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def gh(path):return json.loads(command('gh','api',REPO+path))


def admit(native_artifact,out):
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-watchlist-phase-b-20261108'
    head=command('git','rev-parse','HEAD').decode().strip();assert head==os.environ['GITHUB_SHA']
    assert not command('git','status','--porcelain','--untracked-files=no').strip()
    this=gh('actions/runs/'+os.environ['GITHUB_RUN_ID'])
    assert this['head_sha']==head and this['workflow_id']==397702717 and this['path']==WORKFLOW
    previous=command('git','show',BASE+':'+WORKFLOW).decode()
    actual=(ROOT/WORKFLOW).read_text()
    additions=[n for n in ('watchlist-verify-native','prepare-watchlist','sign-watchlist','publish-watchlist') if n in actual.split('options: [',1)[1].split(']',1)[0]]
    expected=previous.replace('prepare-three, sign-three]', 'prepare-three, sign-three, '+', '.join(additions)+']')
    assert additions[:2]==['watchlist-verify-native','prepare-watchlist']
    assert actual.startswith(expected.rstrip()+'\n'),'EXISTING_ORIGINAL_WORKFLOW_JOBS_CHANGED'
    feature_before=command('git','show',BASE+':'+FEATURE_WORKFLOW).decode()
    feature_actual=(ROOT/FEATURE_WORKFLOW).read_text()
    if feature_actual!=feature_before:
        selector='preview-fullscreen451-android]'
        exclusion="&& inputs.feature != 'cobra-quality444-final'"
        assert feature_before.count(selector)==1 and feature_before.count(exclusion)==1,'EXACT_FEATURE_WORKFLOW_ANCHORS'
        feature_expected=feature_before.replace(selector,'preview-fullscreen451-android, watchlist-playback-android]',1)
        feature_expected=feature_expected.replace(exclusion,exclusion+" && inputs.feature != 'watchlist-playback-android'",1)
        assert feature_actual.startswith(feature_expected),'EXISTING_FEATURE_WORKFLOW_JOBS_CHANGED'
        appended=feature_actual[len(feature_expected):]
        assert appended.lstrip('\n').startswith('  selected_watchlist:\n') and re.findall(r'^  ([A-Za-z0-9_-]+):',appended,re.M)==['selected_watchlist'],'ONLY_SELECTED_WATCHLIST_FEATURE_JOB_MAY_BE_APPENDED'
    changed=command('git','diff','--name-only',BASE,'HEAD').decode().splitlines()
    prefix=HERE.relative_to(ROOT).as_posix()+'/'
    assert all(n.startswith(prefix) or n in (WORKFLOW,FEATURE_WORKFLOW) for n in changed),'PREPARATION_HAS_UNRELATED_SOURCE_CHANGES'
    for n in ('SignInfinityModules.java','ORIGINAL-INFINITY-PUBLIC-KEY.pem','module_bundle.py','module_dex.py','InfinityInstalledModules.java.in'):
        path='repairs/infinity-final-closure-2103407/'+n
        assert (ROOT/path).read_bytes()==command('git','show',BASE+':'+path),'ORIGINAL_MODULE_TOOLS_CHANGED:'+n
    # The permanent APK signer and its owner/source gate are immutable.
    for n in ('assemble.py','release_gate.py','release_authority.py','component_bundles.py','signer_policy.py'):
        path='repairs/dual-experience-isolation-2103420/'+n
        assert (ROOT/path).read_bytes()==command('git','show',BASE+':'+path),'ORIGINAL_RELEASE_IMPLEMENTATION_CHANGED:'+n
    pins=load(HERE/'RUNTIME-SOURCE-PINS.json')
    assert len(pins['native'])==6 and set(pins['python'])=={'plugin.py','service.py','resume_hub.py','saved_playback.py'}
    for n,d in pins['native'].items():assert sha(HERE/'native'/n)==d
    for n,d in pins['python'].items():assert sha(HERE/'overlay/script.infinity.commandcenter'/n)==d
    host=load(HERE/'HOST-INTEGRATION-RESULT.json')
    assert host['result']=='PASS' and host['unique_focused_host_cases']==28
    for n,d in host['source_binding'].items():assert sha(HERE/n)==d,'HOST_SOURCE_BINDING:'+n
    assert {Path(n).name:d for n,d in host['source_binding'].items() if n.startswith('overlay/')}==pins['python']
    native_host=load(HERE/'NATIVE-HOST-RESULT.json')
    assert native_host['status']=='PASS' and native_host['source_sha256']==pins['native']
    assert sha(HERE/'test_native_watchlist_state.cpp')==native_host['test_sha256']
    review=load(HERE/'NATIVE-REVIEW.json')
    assert review['source_sha256']==pins['native'] and not review['findings'],'NATIVE_TARGETED_REVIEW_OPEN'
    python_review=load(HERE/'PYTHON-TARGETED-REVIEW.json')
    assert python_review['source_sha256']==pins['python'] and python_review['producer_pins_match_reviewed_map']
    # The helper's reviewed producer closure is data, not an imported provider.
    tree=ast.parse((HERE/'overlay/script.infinity.commandcenter/saved_playback.py').read_text())
    producer=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRODUCERS' for t in n.targets))
    provider_pins=load(HERE/'CURRENT-EMITTER-PINS.json')['providers']
    assert producer=={aid:{'version':item['version'],'files':item['files']} for aid,item in provider_pins.items()},'EXACT_PRODUCER_VERSION_AND_FILES_PINS'
    request=load(HERE/'NATIVE-INPUT-REQUEST.json')
    run=gh('actions/runs/'+str(request['run_id']))
    assert run['status']=='completed' and run['conclusion']=='success' and run['workflow_id']==397702717
    assert run['head_sha']==request['source_commit'] and run['head_branch']=='work/infinity-watchlist-phase-b-20261108'
    row=gh('actions/artifacts/'+str(request['artifact']['id']))
    assert not row['expired'] and row['workflow_run']['id']==request['run_id']
    assert all(row[k]==v for k,v in request['artifact'].items()),'EXACT_NATIVE_ARTIFACT_METADATA'
    assert sha(native_artifact/'libkodi.so')==request['native_sha256']
    assert sha(native_artifact/'ARM64-LINK-VERIFIED.json')==request['proof_sha256']
    proof=load(native_artifact/'ARM64-LINK-VERIFIED.json')
    assert proof['status']=='PASS_REAL_FOUR_ARM64_OBJECTS_FULL_NATIVE_LINK_UNCHANGED_ABI'
    assert proof['source_commit']==request['source_commit'] and proof['native_sha256']==request['native_sha256']
    for n,d in pins['native'].items():
        assert hashlib.sha256(command('git','show',request['source_commit']+':'+prefix+'native/'+n)).hexdigest()==d
    # Preparation observes the live registry; it never reserves or issues versions.
    registry=gh('git/ref/heads/work/infinity-2103460-nine-corrections-20261106')
    assert registry['object']['sha']==AUTHORITY,'LIVE_AUTHORITY_ADVANCED_REVIEW_VERSIONS'
    admission=load(HERE/'VERSION-ADMISSION.json')
    assert admission['status']=='CONFIRMED_UNUSED_FORWARD_PAIR' and admission['authority_source']==AUTHORITY and admission['reserved'] is False
    assert (admission['candidate_versionCode'],admission['recovery_versionCode'])==(2103468,2103469)
    a=json.loads(command('git','show',AUTHORITY+':repairs/dual-experience-isolation-2103420/release-authority.json'))
    assert a['generation']==54 and a['candidate_versionCode']==2103467
    baseline=gh('git/ref/heads/locks/infinity-2103466-owner-approved-base-20261108')
    assert baseline['object']['sha']==BASE
    out.mkdir(parents=True,exist_ok=True)
    (out/'VERSION-ADMISSION.json').write_text(json.dumps(admission,indent=2)+'\n')
    (out/'ADMISSION.json').write_text(json.dumps(dict(status='PASS_REVIEWED_WATCHLIST_MODULE_PREPARATION_BEFORE_KEYS',
        source=head,original_workflow=397702717,native_run=request['run_id'],native_sha256=request['native_sha256'],
        Python_host_cases=28,native_source_count=6,module_signer_unchanged=True,APK_signer_unchanged=True,
        registry_unchanged=True,APK_signing=False,Android='PENDING_SELECTED_CASES',Fold='PENDING_OWNER'),indent=2)+'\n')
    print('PASS pinned runtime source/host/link/producer/original signer/unused versions; no credentials accessed')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native-artifact',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    admit(**vars(p.parse_args()))
