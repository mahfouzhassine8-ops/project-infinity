"""Build an isolated Infinity engine from the exact signed 2103401 source archive.

No historical source reconstruction, shared workflow edits or Cobra packaging.
Every original source input and original build link is checked before and after.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'checkpoint-build'
ARCHIVE='Infinity-2103401-Source-and-Build-Receipts.zip'

def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def hashes(root):return {p.relative_to(root).as_posix():patch.sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def checked_sources(root,expected,allow_generated=False):
    actual=hashes(root)
    assert all(actual.get(p)==h for p,h in expected.items()),'Reviewed native input changed'
    if not allow_generated:assert actual==expected,'Unexpected source inputs'
    return {p:h for p,h in actual.items() if p not in expected}

def prepare(parent):
    archive=parent/ARCHIVE
    assert patch.sha(archive.read_bytes())==patch.BASELINE['source_archive_sha256']
    native=ROOT/'kodi';assert not native.exists(),'Isolated source output already exists'
    OUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        expected=json.loads(z.read('NATIVE-SOURCE-MAP.json'))
        assert len(expected)==9404
        assert patch.sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())==patch.BASELINE['source_map_sha256']
        for name,pin in expected.items():
            path=Path(name);assert not path.is_absolute() and '..' not in path.parts
            info=z.getinfo('native/'+name);data=z.read(info);assert patch.sha(data)==pin
            target=native/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            target.chmod((info.external_attr>>16)&0o777)
        links=json.loads(z.read('receipts/FOLD101-NATIVE-BINDING.json'))['unchanged_build_links']
    # Restore precisely the two original source links; neither points to Cobra.
    assert set(links)=={'system/settings/freebsd.xml','xbmc/platform/darwin/tvos/Assets.xcassets/LaunchImage.launchimage/applaunch_screen.png'}
    for name,record in links.items():
        target=native/name;target.unlink();target.symlink_to(record['target'])
        assert target.resolve().is_relative_to(native.resolve())
        assert patch.sha(target.read_bytes())==expected[name]
    source_map=OUT/'BASE-NATIVE-SOURCE-MAP.json';save(source_map,expected)
    # Keep an untouched source mirror for the negative control and host harness.
    baseline=ROOT/'baseline-native';shutil.copytree(native,baseline,symlinks=True)
    save(ROOT/'NATIVE-SOURCE-MAP.json',expected)
    overlay=ROOT/'universal-overlay'
    delta=patch.apply(native,source_map,overlay)
    for name in patch.BASELINE['before']:shutil.copyfile(overlay/name,native/name)
    final=dict(expected,**delta['after']);checked_sources(native,final)
    delta.update(source_commit=os.environ['GITHUB_SHA'],original_links=links)
    save(OUT/'SOURCE-DELTA.json',delta);save(OUT/'NATIVE-SOURCE-MAP.json',final)
    return delta

def compile_engine():
    native=ROOT/'kodi';expected=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
    checked_sources(native,expected)
    # The unchanged dependency verifier checks the exact completed toolchain.
    subprocess.run(['python3','repairs/android-checkpoint-shutdown/native_ci.py','verify-dependencies'],cwd=ROOT,check=True)
    original=(ROOT/'scripts/infinity_live_app_ci_2.sh').read_text()
    apply='python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json'
    assert original.count(apply)==1
    stage=original.replace(apply,'python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi')
    start=stage.index('rm -f "$TARBALLS/fontconfig-2.14.0.tar.xz"')
    end=stage.index('make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"',start)
    stage=stage[:start]+stage[end:]
    marker='make -C "$BUILD_DIR" apk -j"$(nproc)"';assert stage.count(marker)==1
    stage=stage[:stage.index(marker)]
    script=OUT/'compile-native.sh';script.write_text(stage)
    subprocess.run(['bash',str(script)],cwd=ROOT,check=True)
    generated=checked_sources(native,expected,allow_generated=True)
    libraries=list(Path(os.environ['BUILD_DIR']).rglob('libkodi.so'));assert len(libraries)==1
    engine=OUT/'libkodi.so';shutil.copyfile(libraries[0],engine)
    binary=engine.read_bytes()
    for marker in (b'argument_rejected_before_native_write',b'removed_namespace_inventory_exhausted',
                   b'native_clean_io_inventory_exhausted',b'unverified_dirty_buffer_namespace',
                   b'pending_protected_',b'sqlite_write_transaction',b'SAFE_TO_TERMINATE',b'CHECKPOINT_FAILED'):
        assert marker in binary,marker
    proof=dict(source_commit=os.environ['GITHUB_SHA'],complete_native_engine_compiled=True,
        reviewed_file_count=len(expected),changed_or_missing_reviewed=[],build_generated_additions=generated,
        native_sha256=patch.sha(binary),shutdown_policy='essential_first_process_exit_v1',
        compile_recipe_sha256=patch.sha(stage.encode()),physical_fold_verified=False,final_lock=False)
    save(OUT/'ENGINE-PROOF.json',proof)
    return proof

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','compile'])
    p.add_argument('--parent',type=Path);a=p.parse_args()
    print(json.dumps(prepare(a.parent) if a.mode=='prepare' else compile_engine(),indent=2))
