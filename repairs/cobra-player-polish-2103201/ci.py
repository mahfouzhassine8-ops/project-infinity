#!/usr/bin/env python3
"""Player interaction/polish repair over the exact verified Cobra 2103200."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess, xml.etree.ElementTree as ET, zipfile

ROOT=Path(__file__).resolve().parent
VERSION=2103201
OLD='1.0.9-Cobra-Provider-Boundary-RC1'
NEW='1.0.9-Cobra-Player-Polish-RC1'
PARENT='3a74876701abfd9e1382e466c07a5f3388abaef4'
PARENT_APK='0a5632068ed242245d17fc60753d22e5aee7e6d80680b81e82510de67343c243'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
REVIEWED_ACTIVITY='018f2875b5f922932db9a45a4e40aff73baa247b63d954a6082ac93d53e4f014'

def require(value,message):
    if not value: raise RuntimeError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def replace(path,old,new):
    p=Path(path);s=p.read_text();require(s.count(old)==1,'Identity anchor mismatch: '+old);p.write_text(s.replace(old,new,1))

def upgrade():
    receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    expected=json.loads((ROOT/'parent-source-hashes.json').read_text())
    require(data['version_code']==2103200 and data['version_name']==OLD,'Wrong reconstructed parent')
    require({p:r['after'] for p,r in data['files'].items()}==expected,'Parent receipt is not the verified final 2103200')
    for name,digest in expected.items():require(sha(Path('kodi')/name)==digest,'Parent input drift: '+name)
    require(sha('baseline200/Infinity-'+OLD+'.apk')==PARENT_APK,'Wrong signed 2103200 rollback')
    subprocess.run(['python3',str(ROOT/'apply.py'),'--source','kodi','--receipt',str(receipt),'--out','audit201/patch'],check=True)
    patch=json.loads(Path('audit201/patch/patch.json').read_text())
    allowed={ACTIVITY}
    require(set(patch['files'])==allowed,'Player repair scope changed')
    require(sha(Path('kodi')/ACTIVITY)==REVIEWED_ACTIVITY,'Player source differs from the reviewed composed repair')
    for name,row in patch['files'].items():data['files'].setdefault(name,{'before':row['before']})['after']=row['after']
    replace(Path('kodi')/GRADLE,'versionCode 2103200','versionCode 2103201')
    replace(Path('kodi')/GRADLE,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103200','VERSION_CODE = 2103201')
    replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    pack=Path('scripts/package_background_resume.py');s=pack.read_text()
    require(s.count('Infinity-'+OLD)>=2,'Parent packager filename drift')
    pack.write_text(s.replace('Infinity-'+OLD,'Infinity-'+NEW))
    data['files'][GRADLE]['after']=sha(Path('kodi')/GRADLE)
    data.update(version_code=VERSION,version_name=NEW,source_parent=2103200,source_parent_commit=PARENT,
        source_parent_locked=False,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
        player_interaction_polish=True,protected_timeshift_transport_unchanged=True,
        native_engine_recompiled=False,new_controls=False,complete_product_acceptance=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    for name,row in data['files'].items():require(sha(Path('kodi')/name)==row['after'],'Final source drift: '+name)
    for name,digest in expected.items():
        if name not in allowed|{GRADLE}:require(sha(Path('kodi')/name)==digest,'Unrelated tracked input changed: '+name)
    with Path('audit201/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit201/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source drift')
    Path('audit201/source-preservation.json').write_text(json.dumps({'passed':True,'parent':2103200,'parent_commit':PARENT,'changed_runtime_files':sorted(allowed),'source_receipt_files':len(data['files']),'all_other_tracked_inputs_preserved':True,'native_source_unchanged':True,'physical_device_verified':False},indent=2)+'\n')

def verify():
    base=Path('baseline200/Infinity-'+OLD+'.apk');final=Path('signed201/Infinity-'+NEW+'.apk')
    require(sha(base)==PARENT_APK,'Wrong parent APK')
    audit=json.loads(Path('signed201/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Wrong candidate identity')
    require(audit['apk_sha256']==sha(final) and audit['signer_certificate_sha256']==CERT,'Signer/hash mismatch')
    require(audit['native_recompiled'] is False,'Native engine was rebuilt')
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:
        require(len(b.namelist())==len(set(b.namelist())) and b.testzip() is None,'Corrupt/duplicate APK members')
        require(set(a.namelist())==set(b.namelist()),'APK member inventory changed')
        keep={n for n in a.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
        for name in keep:require(a.read(name)==b.read(name),'Protected payload changed: '+name)
        dex=b''.join(b.read(n) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        require(b'Cobra2103201' not in dex and b'Cobra2103200' not in dex and b'Cobra2103199' not in dex,'Test class packaged in release')
    badging=Path('signed201/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi' versionCode='2103201'" in badging,'Update identity mismatch')
    require('application-debuggable' not in badging,'Debuggable release')
    result={'build':VERSION,'parent':2103200,'parent_commit':PARENT,'parent_apk_sha256':PARENT_APK,
        'apk_sha256':sha(final),'signer':CERT,'protected_payload_entries':len(keep),
        'native_engine_recompiled':False,'native_assets_resources_byte_identical':True,
        'physical_device_verified':False,'installed_update_tested':False}
    Path('audit201/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')

def deliver():
    suites={}
    for folder in ['audit159/android/cobra-regression/test-results','audit159/android/experience/test-results','audit198/android/runtime/test-results','audit198/targeted/test-results']:
        require(Path(folder).is_dir(),'Missing test evidence: '+folder)
        for p in Path(folder).glob('TEST-*.xml'):
            root=ET.parse(p).getroot();name=root.get('name');cases=root.findall('testcase')
            require(name and len(cases)==int(root.get('tests','-1')),'Invalid test inventory: '+str(p))
            require(all(int(root.get(k,'0'))==0 for k in ['failures','errors','skipped']),'Nonpassing suite: '+str(p))
            require(all(all(c.find(k) is None for k in ['failure','error','skipped']) for c in cases),'Nonpassing case: '+str(p))
            row={'suite':name,'tests':len(cases),'evidence':str(p),'cases':sorted([c.get('classname'),c.get('name')] for c in cases)}
            if name in suites:require(suites[name]['cases']==row['cases'],'Conflicting duplicate suite: '+name)
            suites[name]=row
    expected=json.loads((ROOT/'inherited-android-tests.json').read_text())
    require(sum(expected.values())==316,'Inherited test receipt drift')
    expected_cases=json.loads((ROOT/'inherited-android-cases.json').read_text())
    require(set(expected_cases)==set(expected),'Inherited suite identity drift')
    for name,cases in expected_cases.items():
        require(name in suites and suites[name]['cases']==cases,'Inherited testcase identity changed: '+name)
    new_expected=json.loads((ROOT/'player-android-tests.json').read_text())
    new_cases=json.loads((ROOT/'player-android-cases.json').read_text())
    require(set(new_cases)==set(new_expected) and not set(expected)&set(new_expected),'New test manifest overlap/drift')
    for name,cases in new_cases.items():
        require(name in suites and suites[name]['cases']==cases,'New testcase identity changed: '+name)
    require({k:v['tests'] for k,v in suites.items()}==expected|new_expected,'Android suite inventory changed')
    final=json.loads(Path('audit201/final-verification.json').read_text())
    require(final['apk_sha256']==sha('signed201/Infinity-'+NEW+'.apk'),'APK changed after verification')
    result={'build':VERSION,'protected_baseline':2103197,'immediate_parent':2103200,
        'inherited_android_tests':316,'new_android_tests':sum(new_expected.values()),
        'android_test_suites':list(suites.values()),'apk_sha256':final['apk_sha256'],
        'native_engine_recompiled':False,'new_controls':False,'redesign':False,
        'physical_device_verified':False,'installed_update_tested':False,'candidate_locked':False,
        'complete_product_acceptance':False,'status':'TEST CANDIDATE: physical Android/Fold acceptance blocked by device access'}
    Path('signed201/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    for name in ['final-verification.json','source-preservation.json']:
        shutil.copy2(Path('audit201')/name,Path('signed201')/('2103201-'+name))
    shutil.copy2(ROOT/'AUDIT.md','signed201/AUDIT-2103201.md')
    shutil.copy2(ROOT/'DEVICE-TEST.md','signed201/DEVICE-TEST.md')
    print('PASS: 316 inherited +',sum(new_expected.values()),'player Android/Robolectric cases; physical acceptance not claimed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);args=p.parse_args();globals()[args.phase]()
