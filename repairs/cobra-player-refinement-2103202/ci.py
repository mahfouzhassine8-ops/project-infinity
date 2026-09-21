from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,xml.etree.ElementTree as ET,zipfile
ROOT=Path(__file__).resolve().parent
OLD='1.0.9-Cobra-Player-Polish-RC1';NEW='1.0.9-Cobra-Player-Refinement-RC1';VERSION=2103202
PARENT='57a7b93abc073154ff36d717e2638b778dc378ba'
PARENT_APK='67850d37584d8caaada4ae5cc770acd7b61945a9ff7a74dba7921839d97e18d6'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
GRADLE='tools/android/packaging/xbmc/build.gradle.in';ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
def require(ok,message):
    if not ok:raise RuntimeError(message)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def replace(path,old,new):
    p=Path(path);s=p.read_text();require(s.count(old)==1,'Identity drift: '+old);p.write_text(s.replace(old,new))
def upgrade():
    receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    require(sha('baseline201/Infinity-'+OLD+'.apk')==PARENT_APK,'Wrong locked rollback APK')
    subprocess.run(['python3',str(ROOT/'apply.py'),'--source','kodi','--receipt',str(receipt),'--out','audit202/patch'],check=True)
    patch=json.loads(Path('audit202/patch/patch.json').read_text())
    for n,r in patch['files'].items():data['files'][n]['after']=r['after']
    replace(Path('kodi')/GRADLE,'versionCode 2103201','versionCode 2103202');replace(Path('kodi')/GRADLE,'versionName "'+OLD+'"','versionName "'+NEW+'"')
    replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103201','VERSION_CODE = 2103202');replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    pack=Path('scripts/package_background_resume.py');s=pack.read_text();require(s.count('Infinity-'+OLD)>=2,'Packager drift');pack.write_text(s.replace('Infinity-'+OLD,'Infinity-'+NEW))
    data['files'][GRADLE]['after']=sha(Path('kodi')/GRADLE)
    data.update(version_code=VERSION,version_name=NEW,source_parent=2103201,source_parent_commit=PARENT,source_parent_locked=True,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,native_engine_recompiled=False,new_controls=True,user_requested_controls=True,complete_product_acceptance=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    for n,r in data['files'].items():require(sha(Path('kodi')/n)==r['after'],'Final input drift: '+n)
    with Path('audit202/native-after.patch').open('wb') as output:subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=output,check=True)
    require(Path('audit202/native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
    Path('audit202/source-preservation.json').write_text(json.dumps({'passed':True,'parent_commit':PARENT,'changed_runtime_files':[ACTIVITY],'protected_runtime_members':patch['protected_runtime_members'],'native_source_unchanged':True,'physical_device_verified':False},indent=2)+'\n')
def verify():
    base=Path('baseline201/Infinity-'+OLD+'.apk');final=Path('signed202/Infinity-'+NEW+'.apk');require(sha(base)==PARENT_APK,'Wrong baseline')
    audit=json.loads(Path('signed202/background-resume-apk-audit.json').read_text())
    require(audit['version_code']==VERSION and audit['version_name']==NEW,'Wrong release identity');require(audit['apk_sha256']==sha(final) and audit['signer_certificate_sha256']==CERT,'Signer/hash mismatch');require(audit['native_recompiled'] is False,'Native rebuilt')
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:
        require(b.testzip() is None and len(b.namelist())==len(set(b.namelist())),'APK corrupt/duplicate members');require(set(a.namelist())==set(b.namelist()),'APK member inventory changed')
        keep={n for n in a.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
        for n in keep:require(a.read(n)==b.read(n),'Protected payload changed: '+n)
        dex=b''.join(b.read(n) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n));require(b'Cobra2103202' not in dex and b'Cobra2103201' not in dex,'Test code packaged')
    badging=Path('signed202/badging.txt').read_text();require("package: name='com.projectinfinity.kodi' versionCode='2103202'" in badging,'Package identity changed');require('application-debuggable' not in badging,'Debuggable release')
    Path('audit202/final-verification.json').write_text(json.dumps({'build':VERSION,'parent_commit':PARENT,'parent_apk_sha256':PARENT_APK,'apk_sha256':sha(final),'signer':CERT,'protected_payload_entries':len(keep),'native_engine_recompiled':False,'native_assets_resources_byte_identical':True,'physical_device_verified':False,'installed_update_tested':False},indent=2)+'\n')
def deliver():
    inherited=json.loads((ROOT/'inherited-android-cases.json').read_text());new=json.loads((ROOT/'new-android-cases.json').read_text());expected=inherited|new;suites={}
    for folder in ['audit159/android/cobra-regression/test-results','audit159/android/experience/test-results','audit198/android/runtime/test-results','audit198/targeted/test-results']:
        require(Path(folder).is_dir(),'Missing evidence: '+folder)
        for p in Path(folder).glob('TEST-*.xml'):
            r=ET.parse(p).getroot();name=r.get('name');cases=r.findall('testcase')
            require(len(cases)==int(r.get('tests','-1')),'Invalid testcase count');require(all(int(r.get(k,'0'))==0 for k in ['failures','errors','skipped']),'Nonpassing suite: '+name)
            require(all(all(c.find(k) is None for k in ['failure','error','skipped']) for c in cases),'Nonpassing case')
            row={'suite':name,'tests':len(cases),'evidence':str(p),'cases':sorted([c.get('classname'),c.get('name')] for c in cases)}
            if name in suites:require(suites[name]['cases']==row['cases'],'Conflicting suite')
            suites[name]=row
    require(set(suites)==set(expected),'Suite inventory mismatch: '+str(set(suites)^set(expected)))
    for name,cases in expected.items():require(suites[name]['cases']==cases,'Test identity mismatch: '+name)
    final=json.loads(Path('audit202/final-verification.json').read_text());require(final['apk_sha256']==sha('signed202/Infinity-'+NEW+'.apk'),'APK drift')
    result={'build':VERSION,'immediate_parent':2103201,'parent_commit':PARENT,'inherited_android_tests':sum(map(len,inherited.values())),'new_android_tests':sum(map(len,new.values())),'android_test_suites':list(suites.values()),'apk_sha256':final['apk_sha256'],'native_engine_recompiled':False,'user_requested_controls':True,'physical_device_verified':False,'installed_update_tested':False,'candidate_locked':False,'complete_product_acceptance':False,'status':'TEST CANDIDATE: physical Android/Fold acceptance required'}
    Path('signed202/ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    for name in ['final-verification.json','source-preservation.json']:shutil.copy2(Path('audit202')/name,Path('signed202')/('2103202-'+name))
    shutil.copy2(ROOT/'AUDIT.md','signed202/AUDIT-2103202.md');shutil.copy2(ROOT/'DEVICE-TEST.md','signed202/DEVICE-TEST.md');print('PASS: exact inherited/new case inventory; physical acceptance not claimed')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);args=p.parse_args();globals()[args.phase]()
