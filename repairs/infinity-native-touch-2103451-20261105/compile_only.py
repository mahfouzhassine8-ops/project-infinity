"""Exact451 touch objects only; no native link, app run, APK or key access."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'touch-compile-evidence'
BRANCH='work/infinity-native-touch-from-2103451-20261105'
PARENT='55c993e31709f317bf1f31acf460f5641bc31420'
PRODUCER='89300fa6690015f17378657f96230040bb4766ea'
MAP_SHA='20f901cf5780aebff6eff45e4f21248904f8a8ff72d4acdcd5ea72e783c829c3'
PATCH_SHA='d6b61065f4158520e045985f6834327e80c163fed805cebd0c5b27c3179c1563'
ARCHIVE_SHA='b147411ef39a5a76250bc17ca41907866f5df684faa9397c84a3ce99c50ac213'
WORKFLOW='.github/workflows/infinity-native-touch-451-objects.yml'
ASSETS={
  'source':(13274901825,41726452356,'Infinity-Kodi451-P0-Verified-Input-Evidence-41726452356',51385496,'89646188945e35032c8eb5977882923b3293de4111421fbb32adfb0b77595bfc'),
  'dependencies':(11698374892,38132105717,'Infinity-2103367-Verified-Compiler-Dependencies',1199235695,'c26ea3ea6f21fe42e5ff9ff1d3f0adc5bf7adaa775348d812c14a0a377227b69')}

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def save(name,data):
    OUT.mkdir(exist_ok=True)
    (OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

def hashes(root):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}

def metadata():
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
    request=json.loads((HERE/'COMPILE-REQUEST.json').read_text())
    assert request['operation']=='compile-only-two-reviewed-touch-translation-units' and request['frozen_source_reference']==2103451
    assert request['branch']==BRANCH and request['base_checkpoint']==PARENT and request['patch_sha256']==PATCH_SHA
    assert request['native_object_compilation_allowed'] is True
    assert all(request[k] is False for k in ('native_engine_linking_allowed','apk_packaging_allowed','signing_allowed','installation_allowed','application_execution_allowed','shutdown_testing_allowed'))
    changed=subprocess.check_output(['git','diff','--name-only',PARENT,'HEAD'],text=True).splitlines()
    assert changed and all(p.startswith('repairs/infinity-native-touch-2103451-20261105/') or p==WORKFLOW for p in changed),changed
    assert subprocess.check_output(['git','rev-parse','origin/lock/infinity-preview-2103451-user-frozen-20261103'],text=True).strip()=='0b3450433adc3349056167a6697dae92dad63d86'
    for name in ('scripts/infinity_live_app_ci_2.sh','repairs/android-checkpoint-shutdown/native_ci.py','repairs/android-checkpoint-shutdown/install_ndk.sh'):
        assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',PRODUCER+':'+name]),name
    proof={}
    for label,(aid,run,name,size,digest) in ASSETS.items():
        row=json.loads(subprocess.check_output(['gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{aid}'],text=True))
        assert row['id']==aid and row['workflow_run']['id']==run and row['name']==name
        assert row['size_in_bytes']==size and row['digest']=='sha256:'+digest and row['expired'] is False
        proof[label]=dict(id=aid,run=run,name=name,bytes=size,archive_sha256=digest)
    save('AUTHENTICATED-INPUTS.json',proof)

def restore():
    proof=ROOT/'verified-inputs';native=ROOT/'kodi'
    assert not native.exists()
    assert sha(proof/'BASELINE-NATIVE-SOURCE-MAP.json')==MAP_SHA
    expected=json.loads((proof/'BASELINE-NATIVE-SOURCE-MAP.json').read_text())
    staged=json.loads((proof/'CANDIDATE-NATIVE-SOURCE-MAP.json').read_text())
    receipt=json.loads((proof/'SIGNED451-INPUTS-VERIFIED.json').read_text())
    assert receipt['native_producer_commit']==PRODUCER and receipt['native_member_sha256']=='151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e'
    assert receipt['signed451_apk_sha256']=='d77c31c458c4571212022bea7cea1e76c1d415cd5792b780b3c655fba97c6399'
    assert receipt['certificate_sha256']=='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
    assert sha(proof/'verified-p0-native-source.tar.gz')==ARCHIVE_SHA
    native.mkdir()
    with tarfile.open(proof/'verified-p0-native-source.tar.gz','r:gz') as z:z.extractall(native,filter='data')
    assert hashes(native)==staged
    applied=json.loads((HERE/'APPLIED-SOURCE-DELTA.json').read_text())
    assert sha(HERE/'BASELINE451-RESTORATION.patch')==applied['baseline_restoration_patch_sha256']
    subprocess.run(['git','apply','--unidiff-zero',str(HERE/'BASELINE451-RESTORATION.patch')],cwd=native,check=True)
    assert hashes(native)==expected and len(expected)==9411
    patch=ROOT/'repairs/infinity-master-corrective-20261105/TOUCH-NATIVE-PROPOSAL.patch'
    assert sha(patch)==PATCH_SHA
    subprocess.run(['git','apply','--unidiff-zero',str(patch)],cwd=native,check=True)
    actual=hashes(native)
    delta={n for n in actual if actual[n]!=expected[n]}
    assert set(actual)==set(expected) and delta==set(applied['changed_files'])
    for n in delta:assert sha(HERE/'native'/n)==actual[n]==applied['changed_files'][n]['after_sha256']
    save('NATIVE-SOURCE-MAP.json',actual)
    save('SOURCE-BINDING.json',dict(reference=2103451,full_baseline_match_before_patch=True,reviewed_source_count=len(actual),changed_files=sorted(delta),protected_native_source_count=len(actual)-len(delta),patch_sha256=PATCH_SHA,baseline_source_map_sha256=MAP_SHA,source_commit=os.environ.get('GITHUB_SHA'),APK_built=False,signing=False))

def compile_objects():
    expected=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text());native=ROOT/'kodi'
    assert hashes(native)==expected
    subprocess.run(['python3','repairs/android-checkpoint-shutdown/native_ci.py','verify-dependencies'],cwd=ROOT,check=True)
    original=(ROOT/'scripts/infinity_live_app_ci_2.sh').read_text()
    old='python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json'
    assert original.count(old)==1
    stage=original.replace(old,'python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi')
    start=stage.index('rm -f "$TARBALLS/fontconfig-2.14.0.tar.xz"')
    end=stage.index('make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"',start)
    stage=stage[:start]+stage[end:]
    stop='make -C "$BUILD_DIR" -j"$(nproc)"'
    assert stage.count(stop)==1
    stage=stage[:stage.index(stop)]
    assert ' apk ' not in stage and 'apksigner' not in stage
    script=OUT/'configure-only.sh';script.write_text(stage)
    subprocess.run(['bash',str(script)],cwd=ROOT,check=True)
    build=Path(os.environ['BUILD_DIR'])
    commands=json.loads((build/'compile_commands.json').read_text())
    wanted={'xbmc/guilib/GUIBaseContainer.cpp','xbmc/input/InputManager.cpp'}
    selected=[]
    for row in commands:
        file=Path(row['file']).resolve()
        if file.is_relative_to(native) and file.relative_to(native).as_posix() in wanted:selected.append(row)
    assert len(selected)==2 and {Path(r['file']).relative_to(native).as_posix() for r in selected}==wanted
    readelf=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    objects={}
    for row in selected:
        args=row.get('arguments') or shlex.split(row['command'])
        assert '-c' in args and '-o' in args and '-DTARGET_ANDROID' in args
        subprocess.run(args,cwd=row['directory'],check=True)
        output=Path(args[args.index('-o')+1]);output=output if output.is_absolute() else Path(row['directory'])/output
        header=subprocess.check_output([str(readelf),'-h',str(output)],text=True)
        assert 'AArch64' in header and 'REL (Relocatable file)' in header
        name=Path(row['file']).relative_to(native).as_posix()
        objects[name]=dict(sha256=sha(output),bytes=output.stat().st_size,source_sha256=sha(row['file']),ELF_class='ELF64',machine='AArch64',type='REL')
    actual=hashes(native)
    assert all(actual.get(n)==h for n,h in expected.items())
    assert not list(build.rglob('libkodi.so')) and not list(ROOT.glob('*.apk'))
    save('SELECTED-COMPILE-COMMANDS.json',selected)
    save('COMPILE-RESULT.json',dict(actual_ARM64_translation_units_compiled=objects,reviewed_native_inputs_unchanged=True,source_commit=os.environ.get('GITHUB_SHA'),configure_recipe_sha256=sha(script),generated_native_paths=sorted(set(actual)-set(expected)),native_engine_linked=False,APK_built=False,signing=False,Android_runtime='NOT_RUN',physical_fold='NOT_RUN'))
    print('Two real ARM64 Android translation units compiled; no engine link, APK, signing or Android execution.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['metadata','restore','compile']);args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    {'metadata':metadata,'restore':restore,'compile':compile_objects}[args.mode]()
