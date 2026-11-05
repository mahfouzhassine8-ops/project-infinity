"""Full native link of the exact verified touch source. Never package or sign."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'controlled-native'
BRANCH='work/infinity-master-testing-from-2103451-20261105'
PARENT='4c4094918845bd42649f50bcb094d2ba334a51bc'
TOUCH=ROOT/'repairs/infinity-native-touch-2103451-20261105'

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

touch=load(TOUCH/'compile_only.py','approved_touch_restoration')

def metadata():
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
    request=json.loads((HERE/'NATIVE-BUILD-REQUEST.json').read_text())
    assert request['checkpoint']==PARENT and request['full_native_link_allowed'] is True
    assert all(request[n] is False for n in ('apk_packaging_in_native_job','signing_in_native_job','application_execution','shutdown_testing','install_promote_lock'))
    for name in ('scripts/infinity_live_app_ci_2.sh','repairs/android-checkpoint-shutdown/native_ci.py','repairs/android-checkpoint-shutdown/install_ndk.sh','repairs/universal-persistence-2103401/build.py'):
        assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',touch.PRODUCER+':'+name])
    assert subprocess.check_output(['git','rev-parse','origin/lock/infinity-preview-2103451-user-frozen-20261103'],text=True).strip()=='0b3450433adc3349056167a6697dae92dad63d86'
    report={}
    for label,(aid,run,title,size,digest) in touch.ASSETS.items():
        row=json.loads(subprocess.check_output(['gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{aid}'],text=True))
        assert row['id']==aid and row['workflow_run']['id']==run and row['name']==title and row['size_in_bytes']==size and row['digest']=='sha256:'+digest and row['expired'] is False
        report[label]=dict(id=aid,run=run,name=title,size=size,archive_sha256=digest)
    touch.OUT=OUT;touch.save('AUTHENTICATED-INPUTS.json',report)

def restore():
    touch.OUT=OUT;touch.restore()

def compile_engine():
    sys.path.insert(0,str(ROOT/'repairs/universal-persistence-2103401'))
    producer=load(ROOT/'repairs/universal-persistence-2103401/build.py','frozen_original_engine_producer')
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
    (OUT/'ELF-ABI.txt').write_text(header+'\n'+'\n'.join(identity)+'\n')
    expected=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
    approved=json.loads((TOUCH/'APPLIED-SOURCE-DELTA.json').read_text())
    for n,row in approved['changed_files'].items():assert expected[n]==row['after_sha256']
    touch.OUT=OUT;touch.save('CONTROLLED-ENGINE-VERIFIED.json',dict(status='PASS_FULL_ARM64_FROZEN451_PLUS_TWO_APPROVED_TOUCH_FILES',source_commit=os.environ['GITHUB_SHA'],native_sha256=touch.sha(library),native_bytes=library.stat().st_size,source_reference=2103451,reviewed_count=9411,protected_native_source_count=9409,changed_native_sources=approved['changed_files'],apk_packaged=False,signing=False,Android_runtime='NOT_RUN',physical_Fold='NOT_RUN',shutdown_behavior='NOT_RUN_UNSELECTED',known_Search_failures=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['metadata','restore','compile']);a=p.parse_args();OUT.mkdir(exist_ok=True)
    {'metadata':metadata,'restore':restore,'compile':compile_engine}[a.mode]()
