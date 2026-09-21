"""207 refinement over the fully built/tested 206 parent; never rebuild native code."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, re, shutil, subprocess, xml.etree.ElementTree as ET, zipfile
ROOT=Path(__file__).resolve().parent
PARENT='6f18a77e83f961a870975e6686154bf7e5a3126f'
OLD='1.0.9-Cobra-Media-Calls-RC1'
NEW='1.0.9-Cobra-Feature-Refinement-RC1'
APK206='32bb55c82c4f7cd90a52d0aa488d643b6c26890d5a4b1844b4d28cae20911d78'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
    if not ok:raise RuntimeError(msg)
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def replace(p,old,new):
    p=Path(p);t=p.read_text();require(t.count(old)==1,'Identity drift: '+old);p.write_text(t.replace(old,new,1))
def review():
    r=json.loads((ROOT/'reviewed.json').read_text())
    require(r['parent_commit']==PARENT,'Wrong parent')
    for name,digest in r['recipe_hashes'].items():require(sha(ROOT/name)==digest,'Recipe drift '+name)
    return r
def upgrade():
    r=review();src=Path('kodi');receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    require(data['version_code']==2103206,'Not built parent 206')
    require(sha('baseline206/Infinity-'+OLD+'.apk')==APK206,'Wrong rollback APK')
    parent=module('parent206_apply',Path('audit206/repairs/cobra-media-calls-2103206/apply.py'))
    parent.verify_parent_inventory(src,r['parent_inventory'])
    for name,row in r['files'].items():require(sha(src/name)==row['before'],'Source drift '+name)
    subprocess.run(['git','apply','--check',str(ROOT/'features.patch')],cwd=src,check=True)
    subprocess.run(['git','apply',str(ROOT/'features.patch')],cwd=src,check=True)
    for name,row in r['files'].items():
        require(sha(src/name)==row['after'],'Unexpected patch result '+name)
        data['files'][name]['after']=row['after']
    replace(src/GRADLE,'versionCode 2103206','versionCode 2103207')
    replace(src/GRADLE,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103206','VERSION_CODE = 2103207')
    replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    p=Path('scripts/package_background_resume.py');t=p.read_text();require(t.count('Infinity-'+OLD)>=2,'Packager drift');p.write_text(t.replace('Infinity-'+OLD,'Infinity-'+NEW))
    data['files'][GRADLE]['after']=sha(src/GRADLE)
    data.update(version_code=2103207,version_name=NEW,source_parent=2103206,source_parent_commit=PARENT,
        candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,native_engine_recompiled=False,
        new_features=False,new_controls=False,complete_product_acceptance=False)
    receipt.write_text(json.dumps(data,indent=2)+'\n')
    for name,row in data['files'].items():require(sha(src/name)==row['after'],'Final source drift '+name)
    with Path('audit207/native-after.patch').open('wb') as out:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit207/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native diff changed')
    Path('audit207/source-preservation.json').write_text(json.dumps(dict(changed_runtime_files=sorted(r['files']),native_source_unchanged=True,physical_device_verified=False),indent=2)+'\n')
def verify():
    review();base=Path('baseline206/Infinity-'+OLD+'.apk');apk=Path('signed207/Infinity-'+NEW+'.apk')
    require(sha(base)==APK206,'Rollback drift')
    audit=json.loads(Path('signed207/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==2103207 and audit['version_name']==NEW,'Wrong version')
    require(audit['apk_sha256']==sha(apk) and audit['signer_certificate_sha256']==CERT,'Signer/hash mismatch')
    require(audit['native_recompiled'] is False,'Native rebuild forbidden')
    with zipfile.ZipFile(base) as old,zipfile.ZipFile(apk) as new:
        require(new.testzip() is None and len(new.namelist())==len(set(new.namelist())),'Bad APK')
        require(set(old.namelist())==set(new.namelist()),'APK inventory changed')
        keep=[n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc']
        for name in keep:require(old.read(name)==new.read(name),'Protected payload changed '+name)
        dex=b''.join(new.read(n) for n in new.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        require(all(('Cobra'+str(n)).encode() not in dex for n in range(2103201,2103208)),'Test code packaged')
    b=Path('signed207/badging.txt').read_text();require("package: name='com.projectinfinity.kodi' versionCode='2103207'" in b and 'application-debuggable' not in b,'Wrong manifest')
    Path('audit207/final-verification.json').write_text(json.dumps(dict(apk_sha256=sha(apk),parent_apk_sha256=APK206,signer=CERT,native_assets_resources_byte_identical=True,protected_payload_entries=len(keep),physical_device_verified=False),indent=2)+'\n')
def tests():
    review();build=Path('refinement207-build');app=build/'xbmc';prior=Path('repair202-build/xbmc');out=Path('audit207/android')
    # Reuse the fully configured, successfully executed baseline test project.
    # No production code or APK is copied from the parent's build directory.
    shutil.copytree(prior/'src/test',app/'src/test',dirs_exist_ok=True)
    t=(prior/'build.gradle').read_text();require('versionCode 2103206' in t,'Wrong baseline Gradle fixture')
    (app/'build.gradle').write_text(t.replace('versionCode 2103206','versionCode 2103207').replace(OLD,NEW))
    folder=app/'src/test/java/com/projectinfinity/kodi'
    module('adapt207',ROOT/'adapt_tests.py').adapt(folder,Path('audit207/test-expectation-supersessions.json'))
    for p in (ROOT/'tests').glob('*.java'):shutil.copy2(p,folder/p.name)
    baseline=json.loads(Path('signed206/ACCEPTANCE.json').read_text())
    expected={row['suite']:row['cases'] for row in baseline['android_test_suites']}
    expected.update(json.loads((ROOT/'new-cases.json').read_text()))
    Path('audit207/expected-cases.json').write_text(json.dumps(expected,indent=2)+'\n')
    runner=module('runner207',Path('experience-delta/repairs/infinity-experience-2103159/tests/android.py'))
    env=runner.test_environment(out,Path('experience-delta/repairs/infinity-experience-2103159/experience-theme.json'))
    command=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest','--rerun-tasks']
    for suite,cases in expected.items():
        for owner,name in cases:command+=['--tests',owner+'.'+name]
    command+=['--stacktrace']
    try:runner.run_process(command,build,env,out,timeout=900)
    finally:runner.copy_results(app,out)
    actual={}
    for p in (out/'test-results').glob('TEST-*.xml'):
        root=ET.parse(p).getroot();cases=root.findall('testcase')
        require(all(int(root.get(k,'0'))==0 for k in ['failures','errors','skipped']),'Failing suite '+str(p))
        require(all(c.find(k) is None for c in cases for k in ['failure','error','skipped']),'Nonpassing case')
        actual[root.get('name')]=sorted([[c.get('classname'),c.get('name')] for c in cases])
    require(actual==expected,'Test inventory mismatch')
    verify()
    result=dict(build=2103207,parent_commit=PARENT,parent_tests_passed=665,
        candidate_tests=sum(map(len,actual.values())),candidate_suites=len(actual),
        test_expectations_superseded='See test-expectation-supersessions.json; originals ran first on 206',
        physical_device_verified=False,installed_update_tested=False,live_dual_decoder_verified=False,
        audible_phone_call_playback_verified=False,complete_product_acceptance=False,candidate_locked=False,
        status='TEST CANDIDATE: physical phone/provider acceptance required')
    Path('signed207/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    for p in ['AUDIT.md','DEVICE-TEST.md']:shutil.copy2(ROOT/p,Path('signed207')/p)
    for p in ['final-verification.json','source-preservation.json','test-expectation-supersessions.json','expected-cases.json']:shutil.copy2(Path('audit207')/p,Path('signed207')/p)
    with zipfile.ZipFile('signed207/Cobra-2103207-Generated-Android-Source.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in json.loads((ROOT/'reviewed.json').read_text())['parent_inventory']:archive.write(Path('kodi')/name,name)
    print('PASS: exact candidate inventory; physical acceptance NOT claimed')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','tests']);globals()[p.parse_args().phase]()
