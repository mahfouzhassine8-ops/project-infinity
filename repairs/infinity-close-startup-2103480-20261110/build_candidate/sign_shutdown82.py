#!/usr/bin/env python3
"""Fail-closed exact 2103482 QA signing admission and post-sign integrity audit.

Never signs independently. The sole existing original-key signer performs
release_gate pre_sign and assemble.py sign after these inputs pass.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
import release_authority as ra
import release_gate as gate
from inventory import CERT_SHA,SIGNATURE,digest,canonical

VERSION=2103482
GEN=66
SHA_BASE='9cbb4c5f89a214924b6890463aa5842f85b18ff445d04d855e441fa61f4578c2'
SHA_ENGINE='503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437'
REQ=ROOT/'repairs/infinity-close-startup-2103480-20261110/build_candidate/SHUTDOWN-ORIGINAL-SIGN-REQUEST.json'
MEMBERS={'AndroidManifest.xml','lib/arm64-v8a/libkodi.so','assets/experience-component-updates.properties'}

def fail(cond,why):
    if not cond:raise RuntimeError(why)

def sha(file):
    with Path(file).open('rb') as f:
        return hash_file(f)

def hash_file(stream):
    h=hashlib.sha256()
    for chunk in iter(lambda:stream.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def hash_member(z,name):
    with z.open(name) as f:return hash_file(f)

def admission():
    fail(os.environ.get('GITHUB_REPOSITORY')=='mahfouzhassine8-ops/project-infinity','WRONG_REPO')
    fail(os.environ.get('GITHUB_REF')=='refs/heads/work/infinity-2103460-nine-corrections-20261106','WRONG_SIGNING_BRANCH')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    fail(actual==os.environ.get('GITHUB_SHA'),'SOURCE_HEAD_RACE')
    fail(not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT),'DIRTY_PROTECTED_SOURCE')
    req=json.loads(REQ.read_text())
    fail(req=={
      'operation':'sign-exact-registered-shutdown82-internal-QA',
      'versionCode':2103482,'generation':66,
      'original_signer_workflow_id':397702717,
      'prepared_artifact_id':13833695178,
      'prepared_run':42970204230,
      'baseline':2103480,
      'signed_QA_only':True,'user_acceptance':False,'Android_shutdown':'NOT_RUN',
      'preserve_Cobra':True,'unknown_writer_still_fail_closed':True,
      'recovery':'ORIGINAL_SIGNED80_PRESERVED',
    },'INVALID_SIGN_REQUEST')
    a=json.loads((ROOT/ra.AUTHORITY_PATH).read_text())
    fail(a['generation']==GEN and a['candidate_versionCode']==VERSION,'UNREGISTERED_CANDIDATE')
    fail(a['status']=='ENGINEERING_REVIEWED_FOLD_PENDING','RELEASE_ALREADY_ACCEPTED')
    fail(a['target_owners']==['INFINITY','CHOOSER_SHELL'],'WRONG_OWNER_VECTOR')
    fail(a['experience_version_labels']=={'INFINITY':VERSION,'COBRA':2103445},'LABELS_CHANGED')
    fail(a['components']['COBRA']['version']=='2103445.cobra.1','COBRA_CHANGED')
    fail(a['accepted_pointer_updated'] is False,'ACCEPTED_BASELINE_UPDATED')
    e=a['owner_update_evidence']
    fail(e['owner']=='INFINITY_SHUTDOWN82_INTERNAL_QA_NOT_ACCEPTED','WRONG_QA_OWNER')
    fail(e['producer_run']==42970204230 and e['artifact']['id']==13833695178,'WRONG_QA_SOURCE')
    fail(e['baseline_APK_sha256']==SHA_BASE and e['native_sha256']==SHA_ENGINE,'WRONG_QA_HASHES')
    fail(e['Android']=='NOT_RUN' and e['native_writer_unknown_effect']=='UNPROVEN_FAIL_CLOSED','SAFETY_WAIVED')
    fail(e['publication'] is False and e['accepted_pointer_updated'] is False,'UNAUTHORIZED_ACCEPTANCE')
    for path,required in e['source_files'].items():
        fail(sha(ROOT/path)==required,'UNREVIEWED_SIGNING_SOURCE:'+path)
    fail(a['payload']['member:lib/arm64-v8a/libkodi.so']==
         {'owner':'INFINITY','sha256':SHA_ENGINE},'NATIVE_PAYLOAD_CHANGED')
    ra.validate(a)
    ra.verify_evidence(a,lambda p:(ROOT/p).read_bytes())
    print('PASS 2103482/66 exact QA admission; signer key not yet accessed',flush=True)

def inputs():
    admission()
    base=ROOT/'signed80/Infinity-2103480-Combined-Original-Signer.apk'
    candidate=ROOT/'shutdown82-prepared/Infinity-2103482-Shutdown-UNSIGNED-NOT-INSTALLABLE.apk'
    proof=json.loads((ROOT/'shutdown82-prepared/UNSIGNED-QA-PRESERVATION.json').read_text())
    fail(base.is_file() and sha(base)==SHA_BASE,'SIGNED80_BASELINE_NOT_AUTHENTIC')
    fail(candidate.is_file() and sha(candidate)==proof['unsigned_sha256'],'UNSIGNED_CANDIDATE_NOT_AUTHENTIC')
    fail(proof['status']=='PASS_UNSIGNED_OWNER_BUNDLE_AND_APK_MEMBER_PRESERVATION','UNSIGNED_PRESERVATION_INVALID')
    fail(proof['native_engine_sha256']==SHA_ENGINE and proof['baseline_apk_sha256']==SHA_BASE,'SHA_MISMATCH')
    fail(proof['Android_shutdown']=='NOT_RUN' and proof['release_authority_registered'] is False,'FAKE_QA_ACCEPTANCE')
    fail(proof['original_key_used'] is False and proof['signed_apk_sha256'] is None,'ALREADY_SIGNED_UNEXPECTED')
    fail(set(proof['changed_member_sha256'])==MEMBERS,'UNRELATED_MEMBER_IN_UNSIGN_STAGE')
    with ZipFile(base) as old, ZipFile(candidate) as new:
        old_names=set(old.namelist())-SIGNATURE
        new_names=set(new.namelist())-SIGNATURE
        fail(old_names==new_names,'APK_MEMBER_INVENTORY_CHANGED')
        change={name for name in old_names if hash_member(old,name)!=hash_member(new,name)}
        fail(change==MEMBERS,'UNEXPECTED_UNSIGN_DELTA:'+repr(change))
        fail(hash_member(new,'lib/arm64-v8a/libkodi.so')==SHA_ENGINE,'ENGINE_CHANGED_AFTER_SOURCE_REVIEW')
        fail(new.read('assets/experience-component-updates.properties')==
             b'infinity.last_updated_in=2103482\ncobra.last_updated_in=2103445\n','SHELL_LABEL_CHANGED')
        a,av=gate.normalize_manifest(old.read('AndroidManifest.xml'))
        b,bv=gate.normalize_manifest(new.read('AndroidManifest.xml'))
        fail(av==2103480 and bv==VERSION and a==b,'MANIFEST_CHANGED_BEYOND_VERSION')
    print('PASS exact signed80 baseline, exact native and 3-member unsigned QA delta',flush=True)

def post():
    admission()
    baseline=ROOT/'signed80/Infinity-2103480-Combined-Original-Signer.apk'
    signed=ROOT/'shutdown82-original-signed/Infinity-2103482-Combined-Original-Signer.apk'
    d=json.loads((ROOT/'shutdown82-original-signed/BUILD-RECEIPT.json').read_text())
    fail(signed.is_file() and sha(signed)==d['signed_apk_sha256'],'SIGNED_APK_CHANGED')
    fail(d['versionCode']==VERSION and d['certificate_sha256']==CERT_SHA,'ORIGINAL_KEY_OR_VERSION_MISMATCH')
    text=(ROOT/'shutdown82-original-signed/SIGNATURE.txt').read_text()
    for scheme in ('v1','v2','v3'):
        fail(any(line.startswith('Verified using '+scheme+' scheme') and line.endswith(': true')
                 for line in text.splitlines()),'MISSING_SIGNING_SCHEME:'+scheme)
    with ZipFile(baseline) as original, ZipFile(signed) as apk:
        before=set(original.namelist())-SIGNATURE
        after=set(apk.namelist())-SIGNATURE
        fail(before==after,'SIGNED_APK_MEMBER_INVENTORY_CHANGED')
        changed={name for name in before if hash_member(original,name)!=hash_member(apk,name)}
        fail(changed==MEMBERS,'SIGNED_APK_UNRELATED_CHANGE:'+repr(changed))
        fail(hash_member(apk,'lib/arm64-v8a/libkodi.so')==SHA_ENGINE,'SIGNED_NATIVE_MISMATCH')
        fail(apk.read('assets/experience-component-updates.properties')==
             b'infinity.last_updated_in=2103482\ncobra.last_updated_in=2103445\n','SIGNED_SHELL_LABEL_CHANGED')
        a,av=gate.normalize_manifest(original.read('AndroidManifest.xml'))
        b,bv=gate.normalize_manifest(apk.read('AndroidManifest.xml'))
        fail(av==2103480 and bv==VERSION and a==b,'SIGNED_MANIFEST_CHANGED')
    report={
      'status':'PASS_ORIGINAL_SIGNED_2103482_THREE_MEMBER_PRESERVATION',
      'signed_apk_sha256':sha(signed),'certificate_sha256':CERT_SHA,
      'versionCode':VERSION,'original_native_sha256':SHA_ENGINE,
      'changed_members':sorted(MEMBERS),'Cobra_changed':False,
      'Android_shutdown':'NOT_RUN','physical_Fold':'PENDING_OWNER',
      'user_acceptance':False,'published_release':False,
      'opaque_native_retirement':'UNPROVEN_STILL_FAIL_CLOSED',
      'signed80_baseline_preserved':True,'forward_recovery_higher_version':'NOT_ISSUED',
    }
    (signed.parent/'QA-PRESERVATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS original permanently signed 2103482 QA package with exact scope',flush=True)

if __name__=='__main__':
    fail(len(sys.argv)==2 and sys.argv[1] in ('admit','inputs','post'),'MODE')
    {'admit':admission,'inputs':inputs,'post':post}[sys.argv[1]]()
