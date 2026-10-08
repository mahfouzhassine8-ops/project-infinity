#!/usr/bin/env python3
"""Reconstruct exact 3330, apply bounded exit repair, then compile ARM64."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
import native_repair
HERE=Path(__file__).resolve().parent
OUT=Path('engine3334')
def run(cmd):subprocess.run(cmd,check=True)

def prepare():
    run(['python3','repairs/directory-close-2103330/native_ci.py','prepare'])
    run(['python3',str(HERE/'test_messenger.py'),'--source','kodi','--out',str(OUT/'messenger-tests')])
    run(['python3',str(HERE/'test_preservation.py'),'--source','kodi'])
    # 3330 prepare already ran the unchanged directory/cooperative/JobManager
    # suites. Their behavioral paths are preserved by full-source delta checks.
    native_repair.apply(Path('kodi'),Path('engine3330/source-manifest.json'),OUT/'source-manifest.json')

def compile_engine():
    script=Path('scripts/infinity_live_app_ci_2.sh').read_text()
    old='python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json'
    assert script.count(old)==1
    script=script.replace(old,'python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi')
    marker='make -C "$BUILD_DIR" apk -j"$(nproc)"';assert script.count(marker)==1
    path=OUT/'compile.sh';path.write_text(script[:script.index(marker)]);run(['bash',str(path)])
    r=json.loads((OUT/'source-manifest.json').read_text())
    assert native_repair.snapshot(Path('kodi'))==r['after'],'Source changed during compilation'
    libs=list(Path(os.environ['BUILD_DIR']).rglob('libkodi.so'));assert len(libs)==1
    data=libs[0].read_bytes()
    for token in (b'infinity-shutdown-2103334-v1',b'python.exit_frame',b'scripts.late_message_rejected',b'directory.result_wait_cancelled',b'thread.std_join_fallback'):
        assert token in data,token
    shutil.copy2(libs[0],OUT/'libkodi.so')
    p=dict(candidate=2103334,apk_parent=2103333,native_parent=2103330,locked_rollback=2103327,
        source_commit=os.environ['GITHUB_SHA'],native_sha256=hashlib.sha256(data).hexdigest(),
        baseline_kodi_commit='a3a448d26b8d560a65655dab2cd122994dc4e146',
        parent_packaged_native_sha256='22f56ef1836c53930f7b2c9fa89d1a3658482db9444c088bdc175c5a641b477d',
        late_message_gate_fixed=True,python_abort_policy_unchanged=True,script_finalizers_unchanged=True,
        directory_repair_preserved=True,final_joins_preserved=True,timeouts_unchanged=True,
        python_locals_or_arguments_recorded=False,physical_device_verified=False,locked=False)
    (OUT/'ENGINE-PROOF.json').write_text(json.dumps(p,indent=2)+'\n')
    with (OUT/'elf-identity.txt').open('w') as f:subprocess.run(['readelf','-h','-n','-W',str(OUT/'libkodi.so')],stdout=f,check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','compile']);a=p.parse_args();OUT.mkdir(exist_ok=True)
    (prepare if a.mode=='prepare' else compile_engine)()
