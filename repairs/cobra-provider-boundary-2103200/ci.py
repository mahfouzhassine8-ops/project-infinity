#!/usr/bin/env python3
"""Forward-only Java provider repair over the exact verified Cobra 2103199."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess, xml.etree.ElementTree as ET, zipfile

ROOT=Path(__file__).resolve().parent
VERSION=2103200
OLD='1.0.9-Cobra-Power-Audit-Repairs-RC1'
NEW='1.0.9-Cobra-Provider-Boundary-RC1'
PARENT='abb3bcdbbf40290985413a5df30294820d1189ba'
PARENT_APK='c162a097870e0da4f472a16aec32269118ca22d38cd843cd1941d4c243a0346c'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'

def require(value,message):
    if not value: raise RuntimeError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def replace(path,old,new):
    p=Path(path);s=p.read_text();require(s.count(old)==1,'Identity anchor mismatch: '+old);p.write_text(s.replace(old,new,1))

def upgrade():
    receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    expected=json.loads((ROOT/'parent-source-hashes.json').read_text())
    require(data['version_code']==2103199 and data['version_name']==OLD,'Wrong reconstructed parent')
    require({p:r['after'] for p,r in data['files'].items()}==expected,'Parent receipt is not the verified final 2103199')
    for name,digest in expected.items():require(sha(Path('kodi')/name)==digest,'Parent input drift: '+name)
    require(sha('baseline199/Infinity-'+OLD+'.apk')==PARENT_APK,'Wrong signed 2103199 rollback')
    subprocess.run(['python3',str(ROOT/'apply.py'),'--source','kodi','--receipt',str(receipt),'--out','audit200/patch'],check=True)
    patch=json.loads(Path('audit200/patch/patch.json').read_text())
    allowed={'tools/android/packaging/xbmc/src/content/XBMCFileContentProvider.java.in','tools/android/packaging/xbmc/src/XBMCJsonRPC.java.in'}
    require(set(patch['files'])==allowed,'Provider repair scope changed')
    for name,row in patch['files'].items():data['files'].setdefault(name,{'before':row['before']})['after']=row['after']
    replace(Path('kodi')/GRADLE,'versionCode 2103199','versionCode 2103200')
    replace(Path('kodi')/GRADLE,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103199','VERSION_CODE = 2103200')
    replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    pack=Path('scripts/package_background_resume.py');s=pack.read_text()
    require(s.count('Infinity-'+OLD)>=2,'Parent packager filename drift')
    pack.write_text(s.replace('Infinity-'+OLD,'Infinity-'+NEW))
    data['files'][GRADLE]['after']=sha(Path('kodi')/GRADLE)
    data.update(version_code=VERSION,version_name=NEW,source_parent=2103199,source_parent_commit=PARENT,
        source_parent_locked=False,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
        file_provider_authorization_repaired=True,search_query_json_escaped=True,
        native_engine_recompiled=False,new_controls=False,complete_product_acceptance=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    for name,row in data['files'].items():require(sha(Path('kodi')/name)==row['after'],'Final source drift: '+name)
    for name,digest in expected.items():
        if name not in allowed|{GRADLE}:require(sha(Path('kodi')/name)==digest,'Unrelated tracked input changed: '+name)
    with Path('audit200/native-after.patch').open('wb') as out:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=out,check=True)
    require(Path('audit200/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source drift')
    Path('audit200/source-preservation.json').write_text(json.dumps({'passed':True,'parent':2103199,'parent_commit':PARENT,'changed_runtime_files':sorted(allowed),'source_receipt_files':len(data['files']),'all_other_tracked_inputs_preserved':True,'native_source_unchanged':True,'physical_device_verified':False},indent=2)+'\n')

def verify():
    base=Path('baseline199/Infinity-'+OLD+'.apk');final=Path('signed200/Infinity-'+NEW+'.apk')
    require(sha(base)==PARENT_APK,'Wrong parent APK')
    audit=json.loads(Path('signed200/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Wrong candidate identity')
    require(audit['apk_sha256']==sha(final) and audit['signer_certificate_sha256']==CERT,'Signer/hash mismatch')
    require(audit['native_recompiled'] is False,'Native engine was rebuilt')
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:
        require(len(b.namelist())==len(set(b.namelist())) and b.testzip() is None,'Corrupt/duplicate APK members')
        require(set(a.namelist())==set(b.namelist()),'APK member inventory changed')
        keep={n for n in a.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
        for name in keep:require(a.read(name)==b.read(name),'Protected payload changed: '+name)
        dex=b''.join(b.read(n) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n))
        require(b'Cobra2103200' not in dex and b'Cobra2103199' not in dex,'Test class packaged in release')
    badging=Path('signed200/badging.txt').read_text()
    require("package: name='com.projectinfinity.kodi' versionCode='2103200'" in badging,'Update identity mismatch')
    require('application-debuggable' not in badging,'Debuggable release')
    result={'build':VERSION,'parent':2103199,'parent_commit':PARENT,'parent_apk_sha256':PARENT_APK,
        'apk_sha256':sha(final),'signer':CERT,'protected_payload_entries':len(keep),
        'native_engine_recompiled':False,'native_assets_resources_byte_identical':True,
        'physical_device_verified':False,'installed_update_tested':False}
    Path('audit200/final-verification.json').write_text(json.dumps(result,indent=2)+'\n')

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
    require(sum(expected.values())==293,'Inherited test receipt drift')
    expected_cases=json.loads((ROOT/'inherited-android-cases.json').read_text())
    require(set(expected_cases)==set(expected),'Inherited suite identity drift')
    for name,cases in expected_cases.items():
        require(name in suites and suites[name]['cases']==cases,'Inherited testcase identity changed: '+name)
    new_expected=json.loads((ROOT/'provider-android-tests.json').read_text())
    require({k:v['tests'] for k,v in suites.items()}==expected|new_expected,'Android suite inventory changed')
    final=json.loads(Path('audit200/final-verification.json').read_text())
    require(final['apk_sha256']==sha('signed200/Infinity-'+NEW+'.apk'),'APK changed after verification')
    result={'build':VERSION,'protected_baseline':2103197,'immediate_parent':2103199,
        'inherited_android_tests':293,'new_android_tests':sum(new_expected.values()),
        'android_test_suites':list(suites.values()),'apk_sha256':final['apk_sha256'],
        'native_engine_recompiled':False,'new_controls':False,'redesign':False,
        'physical_device_verified':False,'installed_update_tested':False,'candidate_locked':False,
        'complete_product_acceptance':False,'status':'TEST CANDIDATE: physical Android/Fold acceptance blocked by device access'}
    Path('signed200/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    for name in ['final-verification.json','source-preservation.json']:
        shutil.copy2(Path('audit200')/name,Path('signed200')/('2103200-'+name))
    shutil.copy2(ROOT/'AUDIT.md','signed200/AUDIT-2103200.md')
    shutil.copy2(ROOT/'DEVICE-TEST.md','signed200/DEVICE-TEST.md')
    print('PASS: 293 inherited +',sum(new_expected.values()),'provider Android/Robolectric cases; physical acceptance not claimed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);args=p.parse_args();globals()[args.phase]()
