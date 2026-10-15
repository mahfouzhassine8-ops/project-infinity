#!/usr/bin/env python3
"""Compile the repaired Android Java shell only; do not assemble/sign/release an APK.

Reconstruct the immutable 2103153 stack using its original steps, then verify
all registered receipt files against 2103154 before substituting the tested EPG
repair. No Kodi native compiler, production key or provider credential is used.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, shutil, subprocess, sys
BASE='06f7dffa4b23af03030042bc057cfe1a8b672189'
SOURCE153='00d8984b7979db9400fd2e0799ae3736b3cb579953c6a847fd3d193ab1fa6872'
SOURCE154='923a43943ecdf0ff096eb3206cd7ab70dcb22063d2f23f5856546b62469ff326'
RELEASE154='1.0.9-Cobra-Adaptive-View-Identities'
LIVE=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git_file(path):return subprocess.check_output(['git','show',BASE+':'+path])
def main():
    import yaml
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--host-results',type=Path,required=True);a=p.parse_args()
    delta=Path('refinement-delta'); evidence=a.evidence.resolve(); host=a.host_results.resolve()
    for base in ('patches/cobra-2103153','tests/cobra_2103153'):
        for f in (delta/base).rglob('*'):
            if f.is_file():assert f.read_bytes()==git_file(str(f.relative_to(delta))),f
    name='scripts/infinity_cobra_2103153_refinement.py';assert (delta/name).read_bytes()==git_file(name)
    for name in ('background-rollback','background-candidate','engine','preflight','ui-package','compile-evidence'):Path(name).mkdir(exist_ok=True)
    base=Path('run40/candidate/Infinity-1.0.9-Cobra-Full-Feature-Candidate-2.apk').resolve()
    assert sha(base)=='8ef45e9c54a79e2295e295ce1fcdd3430322a0049c7ff5227804c15aed6b4c57'
    workflow=yaml.safe_load(git_file('.github/workflows/infinity-cobra-2103153-audited-build.yml'))
    names=('Reconstruct exact protected RC3 and 2103152 presentation','Apply integrated refinement and execute final production algorithms');done=[]
    for step in workflow['jobs']['android-update']['steps']:
        if step.get('name') in names:
            print('::group::'+step['name'],flush=True)
            subprocess.run(['bash','-e','-o','pipefail','-c',step['run']],check=True)
            done.append(step['name']);print('::endgroup::',flush=True)
    assert tuple(done)==names
    source=Path('kodi').resolve();assert sha(source/LIVE)==SOURCE153
    assert sha(evidence/'preflight/2103154-final.java.in')==SOURCE154
    shutil.copy2(evidence/'preflight/2103154-final.java.in',source/LIVE)
    gradle=source/'tools/android/packaging/xbmc/build.gradle.in';text=gradle.read_text()
    assert text.count('versionCode 2103138')==1
    assert text.count('versionName "1.0.9-Infinity-Lifecycle-Repair-RC3"')==1
    gradle.write_text(text.replace('versionCode 2103138','versionCode 2103154',1).replace('versionName "1.0.9-Infinity-Lifecycle-Repair-RC3"','versionName "'+RELEASE154+'"',1))
    receipt=json.loads((evidence/'engine/background-resume-source.json').read_text())
    for path,row in receipt['files'].items():assert sha(source/path)==row['after'],path
    repair_receipt=json.loads((host/'repair-receipt.json').read_text())
    assert repair_receipt['before_sha256']==SOURCE154
    assert sha(host/'InfinityLiveActivity.java.in')==repair_receipt['after_sha256']
    shutil.copy2(host/'InfinityLiveActivity.java.in',source/LIVE)
    receipt['files'][str(LIVE)]['after']=sha(source/LIVE)
    Path('engine/background-resume-source.json').write_text(json.dumps(receipt,indent=2)+'\n')
    before=Path('engine/native-before.patch').read_bytes()
    after=subprocess.check_output(['git','-C',str(source),'diff','--binary','--','xbmc']);assert before==after
    sys.path.insert(0,str(Path('scripts').resolve()))
    import package_background_resume as pack
    pack.VERSION_CODE=2103154;pack.RELEASE=RELEASE154
    build=Path('epg-compile-build').resolve();out=Path('compile-evidence').resolve()
    pack.prepare(source,base,build,out)
    env=dict(os.environ);env.update(KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
    # compileReleaseJavaWithJavac does not assemble, package or sign an APK.
    subprocess.run(['./gradlew','--no-daemon','--console=plain',':xbmc:compileReleaseJavaWithJavac','--stacktrace'],cwd=build,env=env,check=True)
    classes=list(build.glob('xbmc/build/intermediates/javac/release/**/InfinityLiveActivity.class'));assert len(classes)==1
    data=classes[0].read_bytes()
    for token in (b'cobraEpgSnapshotFile',b'cobraProgrammeAt',b'cobraRefreshChannelMetadata',b'cobraGuidePresentationActive'):assert token in data,token
    assert not list(build.rglob('*.apk')),'Unexpected APK produced by compile-only gate'
    assert before==subprocess.check_output(['git','-C',str(source),'diff','--binary','--','xbmc'])
    result={'generated_source_sha256':sha(source/LIVE),'android_java_compilation':'PASS','native_recompiled':False,'native_source_delta_unchanged':True,'apk_created':False,'production_signing_used':False,'device_verified':False}
    (out/'compile-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
