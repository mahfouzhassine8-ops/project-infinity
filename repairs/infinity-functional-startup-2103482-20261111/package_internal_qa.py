#!/usr/bin/env python3
"""Stage original82 plus the verified native QA engine through retained owners.

No signer, credentials, registry update, installation or acceptance. Execution
requires a separately frozen request with actual successful producer identities.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile, ZipInfo

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
import component_bundles as cb
from inventory import SIGNATURE, canonical, digest, file_sha, validate_names

BASE_APK='78b2a5dd878ea847f425f8bbf5b9c71e810d19e134fe4480588db55a7ea52a32'
BASE_ENGINE='503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437'
BRANCH='work/infinity-2103482-functional-startup-20261111'
LIB='lib/arm64-v8a/libkodi.so'
LABEL='assets/experience-component-updates.properties'
CHANGES={LIB,LABEL,'AndroidManifest.xml'}
OWNERS={'INFINITY':{'payload/'+LIB},'CHOOSER_SHELL':{'payload/'+LABEL}}

def require(value,label):
    if not value:raise RuntimeError(label)

def read(path):return json.loads(Path(path).read_text())

def member_sha(archive,name):
    with archive.open(name) as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def api(path):
    return json.loads(subprocess.check_output(['gh','api','repos/mahfouzhassine8-ops/project-infinity/'+path],text=True,timeout=45))

def producer(row):
    run=api('actions/runs/'+str(row['run']))
    require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==row['source'],'SUCCESSFUL_EXACT_PRODUCER_REQUIRED')
    artifact=api('actions/artifacts/'+str(row['artifact_id']))
    require(not artifact['expired'] and artifact['workflow_run']['id']==row['run'] and artifact['digest']==row['artifact_digest'],'EXACT_LIVE_AUTHENTICATED_ARTIFACT_REQUIRED')

def copy_entry(source,target,name,replacement=None):
    info=source.getinfo(name);entry=ZipInfo(name,info.date_time)
    entry.compress_type=info.compress_type;entry.external_attr=info.external_attr
    entry.create_system=info.create_system;entry.comment=info.comment
    with target.open(entry,'w',force_zip64=info.file_size>=(1<<31)) as output:
        if replacement is None:
            with source.open(name) as stream:shutil.copyfileobj(stream,output,4*1024*1024)
        elif isinstance(replacement,bytes):output.write(replacement)
        else:
            with Path(replacement).open('rb') as stream:shutil.copyfileobj(stream,output,4*1024*1024)

def rebuild_owner(source,target,owner,commit,version,changes):
    require(set(changes)==OWNERS[owner],'EXACT_OWNER_MEMBER_SCOPE')
    with ZipFile(source) as z:
        validate_names(z);meta=read_bytes(z.read('component.json'))
        require(meta['owner']==owner,'WRONG_OWNER')
        meta['approved_source']=commit;meta['version']=str(version)+'.'+owner.lower()+'.startupqa.1'
        for entry,value in changes.items():
            name=entry.removeprefix('payload/');require(name in meta['members'],'UNOWNED_MEMBER')
            sha=digest(value) if isinstance(value,bytes) else file_sha(value)
            meta['members'][name]['sha256']=sha;meta['payload']['member:'+name]['sha256']=sha
        meta['digest']=cb.component_digest(meta['payload'],owner)
        with ZipFile(target,'w',allowZip64=True) as out:
            for name in z.namelist():copy_entry(z,out,name,canonical(meta) if name=='component.json' else changes.get(name))
        return meta

def read_bytes(value):return json.loads(value)

def main():
    p=argparse.ArgumentParser()
    for name in ('request','baseline','components','native','native-archive','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=read(a.request)
    require(os.environ.get('GITHUB_REPOSITORY')=='mahfouzhassine8-ops/project-infinity' and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'EXACT_QA_PREPARATION_BRANCH')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    require(commit==os.environ['GITHUB_SHA'],'HEAD_RACE')
    require(r['operation']=='stage-functional-startup-internal-QA' and r['signed'] is False and r['owner_delivery'] is False,'EXPLICIT_INTERNAL_UNSIGNED_SCOPE')
    require(not a.out.exists(),'NO_OVERWRITE_OF_PRIOR_ARTIFACT')
    require(file_sha(a.baseline)==BASE_APK,'EXACT_ORIGINAL_SIGNED82_BYTES')
    for name in ('component_bundles.py','inventory.py','release_gate.py','assemble_modules.py'):
        path='repairs/dual-experience-isolation-2103420/'+name
        require((ROOT/path).read_bytes()==subprocess.check_output(['git','show','4ed6e8a8:'+path],cwd=ROOT),'ORIGINAL_OWNER_TOOL_CHANGED:'+name)
    for key in ('native_producer','base_owner_producer'):producer(r[key])
    require('sha256:'+file_sha(a.native_archive)==r['native_producer']['artifact_digest'],'DOWNLOADED_NATIVE_ARCHIVE_DIGEST')
    with ZipFile(a.native_archive) as archive:
        names=set(validate_names(archive))
        for name in ('libkodi.so','ARM64-DIAGNOSTIC-BUILD.json','DIAGNOSTIC-SOURCE-PRESERVATION.json'):
            require(name in names and member_sha(archive,name)==file_sha(a.native/name),'LOCAL_NATIVE_INPUT_NOT_FROM_AUTHENTICATED_ARCHIVE:'+name)
    require(r['base_owner_producer']['run']==42970204230 and r['base_owner_producer']['artifact_id']==13833695178,'EXACT_REGISTERED82_OWNER_INPUT')
    # No version reservation here: staging uses a frozen provisional version.
    # Original signer independently reconciles live authority again before issue.
    authority=read_bytes(subprocess.check_output(['git','show',r['registry_source']+':repairs/dual-experience-isolation-2103420/release-authority.json'],cwd=ROOT))
    require(r['registry_source']=='4ed6e8a8bdc19f7bca50429e5bbb286f70eaf143' and authority['generation']==67 and authority['candidate_versionCode']==2103482,'FROZEN_REGISTRY_INPUT')
    issued=api('actions/runs/42979187229')
    require(issued['conclusion']=='success' and issued['head_sha']==r['registry_source'] and issued['workflow_id']==397702717,'ORIGINAL82_ISSUANCE_NOT_CONFIRMED')
    version=r['provisional_version'];require(type(version) is int and version==2103483,'UNEXPECTED_PROVISIONAL_VERSION')
    live=api('git/ref/heads/work/infinity-2103460-nine-corrections-20261106')['object']['sha']
    require(live==r['registry_source'],'LIVE_AUTHORITY_ADVANCED_RECONCILE_BEFORE_STAGING')
    engine=read(a.native/'ARM64-DIAGNOSTIC-BUILD.json');source=read(a.native/'DIAGNOSTIC-SOURCE-PRESERVATION.json')
    require(engine['status']=='PASS_FULL_ARM64_LINK_AND_BASELINE_ABI' and engine['source_commit']==r['native_producer']['source'],'ACTUAL_ARM64_LINK_REQUIRED')
    require(source['status']=='PASS_EXACT82_PLUS_FOUR_DIAGNOSTIC_CALLSITE_FILES_AND_ONE_QA_HEADER','NATIVE_SOURCE_PRESERVATION_NOT_PASS')
    require(engine['native_sha256']==r['native_sha256']==file_sha(a.native/'libkodi.so'),'ACTUAL_ENGINE_HASH_REQUIRED')
    require(source['source_commit']==engine['source_commit'] and source['baseline82_engine']==BASE_ENGINE,'WRONG_NATIVE_BASE')
    require(source['changed']==read(HERE/'native/SOURCE-BINDINGS.json') and source['unchanged82_native_sources']==9407,'UNREVIEWED_NATIVE_DELTA')
    header='xbmc/interfaces/generic/InfinityStartupTrace.h'
    prefix=b'#define INFINITY_STARTUP_TRACE_QA 1 // This native artifact is internal diagnostic QA only.\n'
    require(source['new_header']=={header:digest(prefix+(HERE/'native/overlay'/header).read_bytes())},'UNREVIEWED_DIAGNOSTIC_HEADER')
    catalog=read(a.components/'catalog.json');require(set(catalog['bundles'])==set(cb.OWNED),'COMPLETE_OWNER_SET_REQUIRED')
    require(catalog==authority['bundle_catalog'],'REGISTERED82_OWNER_CATALOG_REQUIRED')
    before={o:cb.read_bundle(a.components/catalog['bundles'][o]['file'],catalog['bundles'][o]) for o in cb.OWNED}
    require(catalog['bundles']['COBRA']['version']=='2103445.cobra.1','COBRA_CHANGED')
    a.out.mkdir();owners=a.out/'components';owners.mkdir();updated=copy.deepcopy(catalog)
    updated.update(source=commit,release_approved=False)
    label=('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
    for owner in cb.OWNED:
        row=updated['bundles'][owner];src=a.components/row['file'];dest=owners/row['file']
        if owner in OWNERS:
            meta=rebuild_owner(src,dest,owner,commit,version,{'payload/'+LIB:a.native/'libkodi.so'} if owner=='INFINITY' else {'payload/'+LABEL:label})
        else:
            shutil.copyfile(src,dest);meta=before[owner];require(file_sha(dest)==file_sha(src),'PROTECTED_OWNER_BUNDLE_CHANGED')
        row.update(sha256=file_sha(dest),version=meta['version'],digest=meta['digest'],approved_source=meta['approved_source'])
        require(cb.read_bundle(dest,row)==meta,'OWNER_REASSEMBLY_MISMATCH')
    (owners/'catalog.json').write_bytes(canonical(updated))
    apk=a.out/('Infinity-'+str(version)+'-Startup-UNSIGNED-NOT-INSTALLABLE.apk')
    cb.combine(owners,updated,apk,version)
    changed={}
    with ZipFile(a.baseline) as old, ZipFile(apk) as new:
        names=set(validate_names(old))-set(SIGNATURE);require(set(validate_names(new))==names,'APK_MEMBER_SET_CHANGED')
        require(member_sha(old,LIB)==BASE_ENGINE and old.read(LABEL)==b'infinity.last_updated_in=2103482\ncobra.last_updated_in=2103445\n','WRONG_BASELINE_ENGINE_OR_LABEL')
        for name in names:
            before_sha=member_sha(old,name);after_sha=member_sha(new,name)
            if before_sha!=after_sha:changed[name]={'before':before_sha,'after':after_sha}
        require(set(changed)==CHANGES,'UNRELATED_APK_PAYLOAD_CHANGE')
        old_manifest,old_version=cb.normalize_manifest(old.read('AndroidManifest.xml'))
        new_manifest,new_version=cb.normalize_manifest(new.read('AndroidManifest.xml'))
        require(old_version==2103482 and new_version==version and old_manifest==new_manifest,'MANIFEST_CHANGED_BEYOND_VERSION')
    proof=dict(status='PASS_UNSIGNED_STARTUP_QA_THREE_MEMBER_PRESERVATION',source=commit,baseline_version=2103482,baseline_sha256=BASE_APK,
        versionCode=version,version_reserved=False,native_sha256=engine['native_sha256'],native_source=engine['source_commit'],native_producer=r['native_producer'],
        unsigned_sha256=file_sha(apk),changed_members=changed,unchanged_payload_members=len(names)-len(changed),
        preserved_owner_bundles={o:file_sha(owners/catalog['bundles'][o]['file']) for o in ('COBRA','MINIMAL_ANDROID_CONTRACT')},
        original_key_used=False,signed=False,installable=False,Android_candidate='NOT_RUN',Fold='NOT_RUN',owner_delivery=False,
        root_cause_of_Fold='UNPROVEN',purpose='Internal diagnostic instrumentation and host-proven CPython cleanup correction; not accepted production repair')
    (a.out/'UNSIGNED-QA-PRESERVATION.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
