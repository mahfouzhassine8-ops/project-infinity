#!/usr/bin/env python3
"""Reuse the verified local startup probe for one frozen original-key QA APK.

No request file is synthesized, and no caller-supplied hash/feature override is
accepted. Invocation requires the signed APK identity committed after issuance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile
import android_startup_probe as probe

HERE=Path(__file__).resolve().parent

def configure():
    probe.SELECTION=HERE/'ANDROID-INTERNAL-QA-SELECTION.json'
    r=json.loads(probe.SELECTION.read_text())
    assert r['feature']=='signed-startup-internal-qa' and r['APK_version']==2103483
    assert r['require_native_trace'] is True and r['shutdown_tests'] is False and r['Cobra_tests'] is False
    assert r['owner_device'] is False and r['Fold_cause_established'] is False
    assert r['execution_actions']==['local-python','controlled-body-error','local-python','health-center','local-python']
    assert r['original_signer_workflow_id']==397702717
    assert r['baseline_apk_sha256']=='78b2a5dd878ea847f425f8bbf5b9c71e810d19e134fe4480588db55a7ea52a32'
    probe.FEATURE=r['feature'];probe.APK_VERSION=r['APK_version'];probe.APK82=r['APK_sha256']
    probe.selected()
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['fetch','prepare','run'])
    for name in ('apk','baseline','sdk','inputs','out'):p.add_argument('--'+name,type=Path,required=name=='out')
    a=p.parse_args();r=configure()
    if a.operation=='fetch':
        sys.path.insert(0,str(probe.ROOT/'repairs/dual-experience-isolation-2103420'))
        from inventory import validate_names
        def api(path):return json.loads(subprocess.check_output(['gh','api','repos/mahfouzhassine8-ops/project-infinity/'+path],text=True,timeout=45))
        assert type(r['signed_run']) is int and type(r['signed_artifact_id']) is int
        run=api('actions/runs/'+str(r['signed_run']))
        assert run['status']=='completed' and run['conclusion']=='success' and run['workflow_id']==397702717
        assert run['head_sha']==r['signed_source'] and run['head_branch']=='work/infinity-2103460-nine-corrections-20261106'
        artifact=api('actions/artifacts/'+str(r['signed_artifact_id']))
        assert not artifact['expired'] and artifact['workflow_run']['id']==r['signed_run'] and artifact['digest']==r['signed_artifact_digest']
        a.out.mkdir(parents=True,exist_ok=False);archive=a.out/'source-artifact.zip'
        with archive.open('wb') as stream:
            subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(r['signed_artifact_id'])+'/zip'],stdout=stream,check=True,timeout=300)
        assert 'sha256:'+probe.base.sha(archive)==r['signed_artifact_digest']
        with ZipFile(archive) as z:
            names=set(validate_names(z));required={'Infinity-2103483-Combined-Original-Signer.apk','QA-PRESERVATION.json','SIGNATURE.txt','BUILD-RECEIPT.json'}
            assert required<=names
            for name in required:z.extract(name,a.out)
        proof=probe.base.load(a.out/'QA-PRESERVATION.json')
        assert proof['status']=='PASS_ORIGINAL_SIGNED_INTERNAL_QA_THREE_MEMBER_PRESERVATION'
        assert proof['signed_apk_sha256']==r['APK_sha256']==probe.base.sha(a.out/'Infinity-2103483-Combined-Original-Signer.apk')
        assert proof['native_sha256']==r['native_sha256'] and proof['Fold_cause_established'] is False
    elif a.operation=='prepare':
        assert a.apk and a.baseline
        assert probe.base.sha(a.baseline)==r['baseline_apk_sha256']
        with ZipFile(a.apk) as z:
            with z.open('lib/arm64-v8a/libkodi.so') as stream:
                assert hashlib.file_digest(stream,'sha256').hexdigest()==r['native_sha256']
        probe.prepare(a.apk,a.out)
        proof=probe.base.load(a.out/'INTAKE.json');proof['upgrade_baseline']=str(a.baseline.resolve())
        proof['native_sha256']=r['native_sha256'];probe.base.save(a.out/'INTAKE.json',proof)
    else:probe.run(a.sdk,a.inputs,a.out)

if __name__=='__main__':main()
