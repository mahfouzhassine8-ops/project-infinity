#!/usr/bin/env python3
"""Locked 2103165 -> isolated 2103166 end-to-end Android-shell audit and delivery gates."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
LOCKED_BASE='6148e34be3024c5939c736a7b4316572d7bd50c0'
CANDIDATE14='1465eabb045badad56142642c48292df94caaa12'
OLD='1.0.9-Cobra-Insets-PiP-Return-Player-Consistency-RC1'
NEW='1.0.9-Cobra-End-to-End-UI-Lifecycle-Audit-RC1'
VERSION=2103166
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,msg):
    if not v:raise RuntimeError(msg)
def run(*args):subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new,count=1):
    p=Path(path);s=p.read_text();require(s.count(old)==count,'Identity anchor drift: '+str(p)+' '+old)
    p.write_text(s.replace(old,new))

def baseline_identity():
    apk=Path('baseline165/Infinity-'+OLD+'.apk')
    proof=Path('baseline165/2103165-verification.json')
    require(apk.is_file() and proof.is_file(),'Locked 2103165 artifact incomplete')
    data=json.loads(proof.read_text())
    require(data.get('version_code')==2103165,'Locked 2103165 version mismatch')
    require(data.get('apk_sha256')==sha(apk),'Locked 2103165 APK identity mismatch')
    return apk,data

def upgrade():
    base,baseproof=baseline_identity()
    out=Path('audit166');out.mkdir(exist_ok=True)
    shutil.copy2('engine/background-resume-source.json',out/'source-receipt-before.json')
    run('python3',ROOT/'apply.py','--source','kodi','--receipt','engine/background-resume-source.json','--out',out/'patch')
    run('python3',ROOT/'source_audit.py','--source','kodi','--patch',out/'patch/patch.json','--out',out/'source-audit')

    replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103165','versionCode 2103166')
    replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"')
    replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103165','VERSION_CODE = 2103166')
    replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    replace('scripts/package_background_resume.py','Infinity-'+OLD,'Infinity-'+NEW,2)

    receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    require(data.get('version_code')==2103165,'Expected exact locked 2103165 source parent')
    patch=json.loads((out/'patch/patch.json').read_text())
    for rel,row in patch['files'].items():
        require(data['files'][rel]['after']==row['before'],'Source receipt mismatch '+rel)
        data['files'][rel]['after']=row['after']
    data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
    data.update(
        version_code=VERSION,version_name=NEW,
        source_parent=2103165,source_parent_commit=LOCKED_BASE,source_parent_locked=True,
        protected_candidate14=CANDIDATE14,candidate14_preserved=True,
        locked_2103164_playback_stability_preserved=True,
        locked_2103165_pip_player_contract_preserved=True,
        shared_browse_safe_area=True,display_cutout_safe=True,
        status_bar_contrast_policy=True,navigation_bar_hidden=False,
        native_engine_unchanged=True,physical_device_verified=False,candidate_locked=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

    with (out/'native-after.patch').open('wb') as f:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=f,check=True)
    require((out/'native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')

    dest=out/'source-after';dest.mkdir(exist_ok=True)
    shutil.copy2(Path('kodi')/REL,dest/'InfinityLiveActivity.java.in')
    shutil.copy2(receipt,out/'source-receipt-after.json')
    (out/'baseline165.json').write_text(json.dumps({'apk_sha256':sha(base),'verification':baseproof},indent=2)+'\n')
    print('PASS: exact locked 2103165 -> isolated 2103166 end-to-end audit delta')

def verify():
    baseline_identity()
    apk=Path('signed166/Infinity-'+NEW+'.apk')
    audit=json.loads(Path('signed166/background-resume-apk-audit.json').read_text())
    require(audit['apk_sha256']==sha(apk) and audit['version_code']==VERSION,'APK identity mismatch')
    require(audit['signer_certificate_sha256']==CERT and not audit['native_recompiled'],'Signer/native mismatch')
    proof={}
    with zipfile.ZipFile(apk) as new:
        for folder,name in [
            ('baseline165',OLD),
            ('baseline162','1.0.9-Cobra-Theme-Switch-Player-Rotation-RC1')]:
            oldapk=Path(folder)/('Infinity-'+name+'.apk')
            require(oldapk.is_file(),'Missing protected baseline '+str(oldapk))
            with zipfile.ZipFile(oldapk) as old:
                protected={n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
                current={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
                require(protected==current,'Protected inventory mismatch vs '+folder)
                for n in protected:require(old.read(n)==new.read(n),'Protected APK entry changed: '+n)
                proof[folder]={'apk_sha256':sha(oldapk),'protected_entries':len(protected)}
        dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
        for token in (
            b'cobraInstallBrowseSafeArea',b'cobraDarkIconsFor',b'cobraApplySystemBarsForSurface',
            b'cobraConsumeLauncherPipReturn',b'CobraPlaybackPolicy',
            b'cobra_player_refined_chrome',b'Previous channel',b'Next channel',b'Lock controls',
            b'Channels',b'Display',b'Multi-View',b'More',b'PLAY IN BACKGROUND',b'MiXplorer'):
            require(token in dex,'Missing compiled contract '+repr(token))
    proof.update(apk_sha256=sha(apk),version_code=VERSION,signer=CERT,native_recompiled=False,locked_base_commit=LOCKED_BASE)
    Path('audit166/apk-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('PASS: signer/native/resources preserved against locked 2103165 and Candidate 14')

def suite(path,count):
    p=Path(path);require(p.is_file(),'Missing Android evidence '+str(p))
    root=ET.parse(p).getroot();cases=root.findall('testcase')
    require(len(cases)==count,'Unexpected test count '+str(p)+' '+str(len(cases)))
    require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Incomplete Android suite '+str(p))
    return count

def deliver():
    inherited=0
    for name,count,folder in [
        ('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),
        ('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
        inherited+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    for name,count in [('CobraVisualRuntimeTest',17),('CobraVisualLayoutTest',10)]:
        inherited+=suite(Path('audit166/android/runtime/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)

    candidate14=suite('audit166/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml',16)
    locked164=suite('audit166/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103164PlaybackStabilityTest.xml',26)
    locked165=suite('audit166/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103165InsetsPipPlayerTest.xml',6)
    new=suite('audit166/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103166EndToEndUiAuditTest.xml',8)

    source=json.loads(Path('audit166/source-audit/source-audit.json').read_text())
    require(source.get('passed') and source.get('protected_methods',0)>=25,'End-to-end source audit failed')
    patch=json.loads(Path('audit166/patch/patch.json').read_text())
    require(patch.get('changed_methods')==['buildShell','cobraApplySystemBarsForSurface'],'Scope drift in 2103166')
    require(patch.get('navigation_bar_hidden') is False,'Navigation bar ownership drift')
    apkproof=json.loads(Path('audit166/apk-verification.json').read_text())
    require(apkproof['apk_sha256']==sha('signed166/Infinity-'+NEW+'.apk'),'APK changed after verification')

    total=inherited+candidate14+locked164+locked165+new
    require(total==102,'Expected 102 Android tests, got '+str(total))
    report={
        'build':VERSION,'locked_base_commit':LOCKED_BASE,'protected_candidate14':CANDIDATE14,
        'candidate_locked':False,'inherited_android_tests':inherited,'candidate14_tests':candidate14,
        'locked_2103164_tests':locked164,'locked_2103165_tests':locked165,'new_2103166_tests':new,
        'total_android_tests':total,'source_checks':len(source['checks']),
        'protected_methods':source['protected_methods'],'native_recompiled':False,
        'physical_device_verified':False,'status':'TEST CANDIDATE - physical Fold acceptance required'
    }
    Path('signed166/ACCEPTANCE.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copy2('audit166/apk-verification.json','signed166/2103166-verification.json')
    shutil.copy2('audit166/source-audit/source-audit.json','signed166/2103166-source-audit.json')
    shutil.copy2('audit166/patch/patch.json','signed166/2103166-source-proof.json')
    shutil.copy2(ROOT/'AUDIT.md','signed166/AUDIT-2103166.md')
    print('PASS:',total,'Android tests +',len(source['checks']),'source checks; locked 2103165 preserved')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args()
    globals()[a.phase]()
