"""Next owner generation in the existing sole original-key signing job."""
import argparse
import base64
import copy
import os
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from prepare_release import command, remote_head, patch_bundle, REPO, ISOLATION, load, require, check
from continuation.stage import generate, sha, save, CC, PREFIX
from inventory import file_sha


def prepare(baseline,bundles,out):
    baseline,bundles,out=baseline.resolve(),bundles.resolve(),out.resolve()
    permission=load(HERE/'RELEASE-AUTHORIZATION.json')
    scope=load(HERE/'SCOPE.json')
    expected=os.environ['GITHUB_SHA']
    require(os.environ.get('GITHUB_WORKFLOW')=='Infinity combined release | owner gate before original signing','SOLE_SIGNER_WORKFLOW')
    require(os.environ.get('GITHUB_REF')=='refs/heads/'+scope['branch'],'AUTHORIZED_BRANCH')
    remote_head(expected)
    require(load(ISOLATION/'release-authority.json')['candidate_versionCode']==2103426,'EXACT_PREVIOUS_AUTHORITY')
    import json
    previous=json.loads(command(['git','show',scope['input_apk_source']+':repairs/dual-experience-isolation-2103420/release-authority.json']))
    require(load(ISOLATION/'release-authority.json')==previous,'EXACT_SIGNED2103426_AUTHORITY')
    for line in (HERE/'SOURCE-SHA256SUMS').read_text().splitlines():
        pin,name=line.split('  ',1)
        path=HERE/name
        require(file_sha(path)==pin,'REVIEWED_SOURCE:'+name)
        tested=command(['git','show',permission['tested_source']+':'+str(path.relative_to(REPO))]).encode()
        # git show is text here; all bound inputs are UTF8 source/JSON.
        require(tested==path.read_bytes(),'TESTED_SOURCE_CHANGED:'+name)
    run=load_run(permission['tested_run'])
    require(run['head_sha']==permission['tested_source'] and run['conclusion']=='success','TESTED_RUN_BINDING')
    require(not out.exists(),'FRESH_OUTPUT');out.mkdir()
    generate(baseline,out/'source')
    candidate=out/'source/candidate-addons'
    manifest=candidate/CC/'INFINITY-MODULES.v1'
    require(file_sha(manifest)==permission['module_manifest_sha256'],'EXACT_REVIEWED_MANIFEST')
    firstparty=REPO/'repairs/infinity-final-closure-2103407'
    verifier=out/'verify-module-bundle'
    command(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',firstparty/'verify_module_bundle.cpp',
             firstparty/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier])
    routes=check(load(ISOLATION/'signer-policy.json'))
    with tempfile.TemporaryDirectory(prefix='infinity-original-module-') as temporary:
        temp=Path(temporary);classes=temp/'classes';classes.mkdir()
        command(['java','-m','jdk.compiler/com.sun.tools.javac.Main','--release','8','-g:none',
                 '-Xlint:all,-options','-Werror','-d',classes,firstparty/'SignInfinityModules.java'])
        remote_head(expected)
        require(check(load(ISOLATION/'signer-policy.json'))==routes,'SIGNER_POLICY_RACE')
        key=temp/'original.jks';key.touch(mode=0o600)
        key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True))
        env={n:os.environ[n] for n in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
        proof=command(['java','-cp',classes,'SignInfinityModules',key,manifest],env)
    proof+=command([verifier,candidate,firstparty/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'])
    require('NATIVE_VERIFIED package=0.3.5.51 protocol=1 files=75' in proof,'NATIVE_AUTHENTICATION')
    (out/'MODULE-AUTHENTICATION.txt').write_text(proof)
    authority=load(ISOLATION/'release-authority.json');catalog=copy.deepcopy(authority['bundle_catalog']);catalog['source']=expected
    changes={str(p.relative_to(out/'source/members')):p.read_bytes() for p in (out/'source/members').rglob('*') if p.is_file()}
    changes[PREFIX+CC+'/INFINITY-MODULES.v1.sig']=(candidate/CC/'INFINITY-MODULES.v1.sig').read_bytes()
    destination=out/'components';destination.mkdir();metas={}
    for owner,old in catalog['bundles'].items():
        source,target=bundles/old['file'],destination/old['file']
        if owner=='INFINITY':
            row,meta=patch_bundle(source,old,owner,changes,scope['Infinity_component'],expected,target)
        elif owner=='CHOOSER_SHELL':
            row,meta=patch_bundle(source,old,owner,{permission['metadata_member']:permission['metadata_after'].encode()},
                                 old['version']+'.infinity2103427',expected,target)
        else:
            shutil.copyfile(source,target);row,meta=old,load_bundle(target,old)
        catalog['bundles'][owner]=row;metas[owner]=meta
    save(destination/'catalog.json',catalog)
    actual={key:value for meta in metas.values() for key,value in meta['payload'].items()}
    changed={key for key in actual if actual[key]!=authority['payload'][key]}
    require(changed=={'member:'+n for n in changes}|{'member:'+permission['metadata_member']},'EXACT_OWNER_DIFF')
    remote_head(expected)
    save(out/'PREPARED-OWNERS.json',dict(source=expected,run_id=int(os.environ['GITHUB_RUN_ID']),
        tested_source=permission['tested_source'],tested_run=permission['tested_run'],
        changed_payload=sorted(changed),manifest_sha256=file_sha(manifest),catalog=catalog,
        original_module_signature='NATIVE_AND_JCA_VERIFIED',APK_produced=False,shutdown='NOT_RUN',physical_Fold='PENDING'))


def load_run(run):
    import json
    return json.loads(command(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(run)]))


def load_bundle(path,row):
    from component_bundles import read_bundle
    return read_bundle(path,row)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('baseline','bundles','out'):p.add_argument('--'+name,type=Path,required=True)
    prepare(**vars(p.parse_args()))
