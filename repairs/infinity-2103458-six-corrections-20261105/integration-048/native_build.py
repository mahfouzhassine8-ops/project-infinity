"""Exact signed458 native inputs plus the approved VideoNav delta. No APK/key access."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'controlled-native'
BRANCH = 'work/infinity-2103458-six-corrections-20261105'
APPROVAL = '04806da44330e5db4a795bf291625e72abded128'
NAV = 'xbmc/video/windows/GUIWindowVideoNav.cpp'
WORKFLOW = '.github/workflows/infinity-six-navigation-arm64.yml'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


touch = load(ROOT / 'repairs/infinity-native-touch-2103451-20261105/compile_only.py', 'unchanged_touch_restore')
touch.OUT = OUT


def bindings():
    approved = json.loads(subprocess.check_output(['git', 'show', APPROVAL + ':repairs/infinity-2103458-six-corrections-20261105/navigation-6a/MANIFEST.json']))
    applied = json.loads((HERE / 'APPLIED-APPROVED-PATCH.json').read_text())
    assert applied['approved_commit'] == APPROVAL and applied['approved_patch_sha256'] == approved['patch_sha256']
    for name, row in applied['files'].items():
        assert row['before_sha256'] == approved['files'][name]['before_sha256']
        assert touch.sha(ROOT / row['applied_source']) == row['proposed_sha256'] == approved['files'][name]['proposed_sha256']
    return applied


def metadata():
    assert os.environ['GITHUB_REPOSITORY'] == 'mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF'] == 'refs/heads/' + BRANCH
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip() == os.environ['GITHUB_SHA']
    subprocess.run(['git','merge-base','--is-ancestor',APPROVAL,'HEAD'],check=True)
    request=json.loads((HERE/'NATIVE-BUILD-REQUEST.json').read_text())
    assert request['approval_checkpoint']==APPROVAL and request['signed_base']==2103458 and request['full_ARM64_link'] is True
    assert all(request[n] is False for n in ('APK_build','signing','application_execution','shutdown_testing','installation','promotion','lock'))
    applied=bindings()
    allowed={WORKFLOW}|{r['applied_source'] for r in applied['files'].values()}
    changed=subprocess.check_output(['git','diff','--name-only',APPROVAL,'HEAD'],text=True).splitlines()
    assert changed and all(n.startswith(str(HERE.relative_to(ROOT))+'/') or n in allowed for n in changed),changed
    for name in ('scripts/infinity_live_app_ci_2.sh','repairs/android-checkpoint-shutdown/native_ci.py','repairs/android-checkpoint-shutdown/install_ndk.sh','repairs/universal-persistence-2103401/build.py'):
        assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',touch.PRODUCER+':'+name]),name
    engine=json.loads((ROOT/'repairs/infinity-browser-visual-20261105/packaging/ENGINE-INPUT.json').read_text())
    assets=dict(touch.ASSETS, signed458_native=tuple(engine['artifact_identity']))
    report={}
    for label,(aid,run,title,size,digest) in assets.items():
        row=json.loads(subprocess.check_output(['gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{aid}'],text=True))
        assert row['id']==aid and row['workflow_run']['id']==run and row['name']==title
        assert row['size_in_bytes']==size and row['digest']=='sha256:'+digest and row['expired'] is False
        report[label]=dict(id=aid,run=run,name=title,size=size,archive_sha256=digest)
    touch.save('AUTHENTICATED-INPUTS.json',report)


def restore():
    applied=bindings()
    touch.restore()  # Existing byte-verified reconstruction of the signed458 input map.
    pins=json.loads((ROOT/'repairs/infinity-browser-visual-20261105/packaging/ENGINE-INPUT.json').read_text())
    mapping=OUT/'NATIVE-SOURCE-MAP.json'
    assert touch.sha(mapping)==pins['source_map_sha256']
    before=json.loads(mapping.read_text())
    assert len(before)==9411 and before[NAV]==applied['files'][NAV]['before_sha256']
    shutil.copyfile(mapping,OUT/'SIGNED458-NATIVE-SOURCE-MAP.json')
    candidate=ROOT/applied['files'][NAV]['applied_source']
    shutil.copyfile(candidate,ROOT/'kodi'/NAV)
    after=touch.hashes(ROOT/'kodi')
    assert set(after)==set(before) and {n for n in after if after[n]!=before[n]}=={NAV}
    assert after[NAV]==applied['files'][NAV]['proposed_sha256']
    touch.save('NATIVE-SOURCE-MAP.json',after)
    touch.save('SOURCE-BINDING.json',dict(base=2103458,base_engine_sha256=pins['native_sha256'],base_source_map_sha256=pins['source_map_sha256'],source_commit=os.environ['GITHUB_SHA'],approval=APPROVAL,changed_files={NAV:applied['files'][NAV]},reviewed_count=len(after),protected_native_source_count=len(after)-1))


def compile_engine():
    bindings()
    sys.path.insert(0,str(ROOT/'repairs/universal-persistence-2103401'))
    producer=load(ROOT/'repairs/universal-persistence-2103401/build.py','unchanged_full_engine_producer')
    producer.OUT=OUT
    proof=producer.compile_engine()
    assert proof['complete_native_engine_compiled'] is True and proof['reviewed_file_count']==9411
    library=OUT/'libkodi.so'
    tool=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    header=subprocess.check_output([str(tool),'-h',str(library)],text=True)
    assert 'ELF64' in header and 'AArch64' in header
    symbols=subprocess.check_output([str(tool),'--dyn-syms','--wide',str(library)],text=True)
    identity=[line for line in symbols.splitlines() if 'InfinityCommandCenterIdentityV1' in line]
    assert any('GLOBAL' in line and 'DEFAULT' in line for line in identity)
    assert b'infinity-library-direct' in library.read_bytes()
    (OUT/'ELF-ABI.txt').write_text(header+'\n'+'\n'.join(identity)+'\n')
    baseline=json.loads((OUT/'SIGNED458-NATIVE-SOURCE-MAP.json').read_text())
    after=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
    assert set(after)==set(baseline) and {n for n in after if after[n]!=baseline[n]}=={NAV}
    touch.save('CONTROLLED-ENGINE-VERIFIED.json',dict(status='PASS_FULL_ARM64_SIGNED458_PLUS_APPROVED_LIBRARY_ENTRY',source_commit=os.environ['GITHUB_SHA'],approval=APPROVAL,native_sha256=touch.sha(library),native_bytes=library.stat().st_size,source_reference=2103458,reviewed_count=9411,protected_native_source_count=9410,changed_native_sources={NAV:after[NAV]},apk_packaged=False,signing=False,Android_runtime='NOT_RUN',physical_Fold='NOT_RUN',shutdown_behavior='NOT_RUN_UNSELECTED',Search_acceptance='TWO_EXISTING_FAILURES_RETAINED'))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['metadata','restore','compile'])
    args=parser.parse_args();OUT.mkdir(exist_ok=True)
    {'metadata':metadata,'restore':restore,'compile':compile_engine}[args.mode]()
