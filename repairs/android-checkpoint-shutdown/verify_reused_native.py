#!/usr/bin/env python3
"""Require the exact passed 2103345 native job and unchanged engine inputs."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT_SHA='04128777ae7e7e635ea54fc595534be6e518f663'
PARENT_RUN=37887463358

def verify_run(directory):
    run=json.loads((directory/'parent-run.json').read_text())
    jobs=json.loads((directory/'parent-jobs.json').read_text())['jobs']
    if run['id']!=PARENT_RUN or run['head_sha']!=PARENT_SHA or run['head_branch']!='work/android-checkpoint-shutdown-2103335':
        raise ValueError('Reused native run identity mismatch')
    native=[job for job in jobs if job['name']=='native-engine' and job['run_id']==PARENT_RUN]
    if len(native)!=1 or native[0]['status']!='completed' or native[0]['conclusion']!='success':
        raise ValueError('The exact parent native compilation has not passed')
    return native[0]['id']

def verify_engine(directory):
    job=verify_run(directory)
    proof=json.loads((directory/'ENGINE-PROOF.json').read_text())
    manifest=HERE/'runtime/native/manifest.json'
    digest=lambda data:hashlib.sha256(data).hexdigest()
    if proof['source_commit']!=PARENT_SHA or proof['all_reviewed_inputs_preserved'] is not True:
        raise ValueError('Reused engine source/preservation proof mismatch')
    if proof['source_manifest_sha256']!=digest(manifest.read_bytes()):
        raise ValueError('Native sources changed; exact engine reuse is unavailable')
    data=(directory/'libkodi.so').read_bytes()
    if proof['native_sha256']!=digest(data):raise ValueError('Reused engine bytes do not match proof')
    import native_ci
    native_ci.verify_engine_identity(HERE/'runtime/native/overlay',data)
    (directory/'REUSE-PROOF.json').write_text(json.dumps({
        'native_run':PARENT_RUN,'native_job':job,'native_source_commit':PARENT_SHA,
        'source_manifest_sha256':digest(manifest.read_bytes()),'native_sha256':digest(data),
        'native_recompiled':False,'device_accepted':False,'locked':False,
        'purpose':'Android lifecycle follow-up over exact 2103345 engine',
    },indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['run','engine']);parser.add_argument('--directory',type=Path,required=True)
    args=parser.parse_args();(verify_run if args.mode=='run' else verify_engine)(args.directory)
    print('PASS exact parent native '+args.mode+' reuse association')
if __name__=='__main__':main()
