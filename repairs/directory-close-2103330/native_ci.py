#!/usr/bin/env python3
"""Reuse exact 3327 reconstruction and dependencies; build only the reviewed new native delta."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
import yaml

def run(command):subprocess.run(command,check=True)
p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','compile']);a=p.parse_args()
out=Path('engine3330');out.mkdir(exist_ok=True)
if a.mode=='prepare':
    recipe=yaml.safe_load(Path('.github/workflows/infinity-2103327-native-jobmanager.yml').read_text())
    blocks=[]
    for step in recipe['jobs']['native-engine']['steps']:
        if step.get('name','').startswith('Compile ARM64 engine'):break
        if 'run' in step:blocks.append(step['run'])
    assert len(blocks)==2
    stage=out/'reconstruct327.sh';stage.write_text('set -euo pipefail\n'+'\n'.join(blocks))
    run(['bash',str(stage)])
    run(['python3','repairs/directory-close-2103330/native_repair.py','--source','kodi','--proof','engine3327/source-manifest.json','--receipt',str(out/'source-manifest.json')])
    run(['python3','repairs/directory-close-2103330/test_native.py','--source','kodi'])
    run(['python3','repairs/cooperative-close-2103326/test_cooperative.py','--source','kodi'])
    shutil.copy2('engine3327/jobmanager-host-tests.log',out)
else:
    stage=Path('scripts/infinity_live_app_ci_2.sh').read_text()
    old='python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json'
    assert stage.count(old)==1
    stage=stage.replace(old,'python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi')
    marker='make -C "$BUILD_DIR" apk -j"$(nproc)"';assert stage.count(marker)==1
    script=out/'compile.sh';script.write_text(stage[:stage.index(marker)])
    run(['bash',str(script)])
    receipt=json.loads((out/'source-manifest.json').read_text())
    expected=json.loads(Path('repairs/directory-close-2103330/native-delta.json').read_text())
    assert {n:receipt['after'][n] for n in receipt['changed']}==expected['after']
    for name,digest in receipt['after'].items():
        assert hashlib.sha256((Path('kodi')/name).read_bytes()).hexdigest()==digest,name
    libs=list(Path(os.environ['BUILD_DIR']).rglob('libkodi.so'));assert len(libs)==1
    data=libs[0].read_bytes()
    for token in (b'infinity-shutdown-2103330-v1',b'directory.result_wait_cancelled',b'jobs.waiting_active',b'IsShutdownRequested'):
        assert token in data,token
    shutil.copy2(libs[0],out/'libkodi.so')
    proof={'candidate':2103330,'apk_parent':2103327,'locked_rollback':2103327,
           'source_commit':os.environ['GITHUB_SHA'],'native_sha256':hashlib.sha256(data).hexdigest(),
           'baseline_kodi_commit':'a3a448d26b8d560a65655dab2cd122994dc4e146',
           'parent_packaged_native_sha256':'a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c',
           'diagnostics_only':False,'shutdown_behavior_changed':True,
           'result_wait_cancellation':True,'script_owner_cleanup_preserved':True,
           'early_job_cancellation':True,'final_worker_join_preserved':True,
           'worker_force_stop_added':False,'physical_device_verified':False,'locked':False}
    (out/'ENGINE-PROOF.json').write_text(json.dumps(proof,indent=2)+'\n')
    with (out/'elf-identity.txt').open('w') as f:
        subprocess.run(['readelf','-h','-n','-W',str(out/'libkodi.so')],stdout=f,check=True)
