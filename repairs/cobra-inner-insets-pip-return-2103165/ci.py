#!/usr/bin/env python3
"""Locked 2103164 -> isolated 2103165 Android-shell packaging and acceptance gates."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, zipfile, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
LOCKED_BASE='d9819b9823ff281f874daaa2bf91fdac1613aeb1'
CANDIDATE14='1465eabb045badad56142642c48292df94caaa12'
OLD='1.0.9-Cobra-Playback-Stability-RC1'
NEW='1.0.9-Cobra-Insets-PiP-Return-Player-Consistency-RC1'
VERSION=2103165
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,message):
    if not v: raise RuntimeError(message)
def run(*args):subprocess.run(list(map(str,args)),check=True)
def replace(path,old,new,count=1):
    p=Path(path);s=p.read_text();require(s.count(old)==count,'Identity anchor drift: '+str(p)+' '+old);p.write_text(s.replace(old,new))

def baseline_identity():
    base=Path('baseline164/Infinity-'+OLD+'.apk')
    proof=Path('baseline164/2103164-verification.json')
    require(base.is_file() and proof.is_file(),'Locked 2103164 artifact incomplete')
    data=json.loads(proof.read_text())
    require(data.get('version_code')==2103164,'Locked baseline version mismatch')
    require(data.get('apk_sha256')==sha(base),'Locked 2103164 APK identity mismatch')
    return base,data

def upgrade():
    base,base_proof=baseline_identity()
    out=Path('audit165');out.mkdir(exist_ok=True)
    shutil.copy2('engine/background-resume-source.json',out/'source-receipt-before.json')
    run('python3',ROOT/'apply.py','--source','kodi','--receipt','engine/background-resume-source.json','--out',out/'patch')

    replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionCode 2103164','versionCode 2103165')
    replace('kodi/tools/android/packaging/xbmc/build.gradle.in','versionName "'+OLD+'"','versionName "'+NEW+'"')
    replace('scripts/infinity_background_resume.py','VERSION_CODE = 2103164','VERSION_CODE = 2103165')
    replace('scripts/infinity_background_resume.py',"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")
    replace('scripts/package_background_resume.py','Infinity-'+OLD,'Infinity-'+NEW,2)

    receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    require(data.get('version_code')==2103164,'Expected locked 2103164 source parent')
    patch=json.loads((out/'patch/patch.json').read_text())
    for rel,row in patch['files'].items():
        require(data['files'][rel]['after']==row['before'],'Source receipt mismatch '+rel)
        data['files'][rel]['after']=row['after']
    data['files']['tools/android/packaging/xbmc/build.gradle.in']['after']=sha('kodi/tools/android/packaging/xbmc/build.gradle.in')
    data.update(
        version_code=VERSION,version_name=NEW,
        source_parent=2103164,source_parent_commit=LOCKED_BASE,source_parent_locked=True,
        protected_candidate14=CANDIDATE14,candidate14_preserved=True,
        locked_playback_stability_preserved=True,player_chrome_contract_preserved=True,
        status_bar_surface_scoped=True,pip_launcher_reentry_browse=True,native_pip_expand_preserved=True,
        native_engine_unchanged=True,physical_device_verified=False,candidate_locked=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

    with (out/'native-after.patch').open('wb') as f:
        subprocess.run(['git','-C','kodi','diff','--binary','--','xbmc'],stdout=f,check=True)
    require((out/'native-after.patch').read_bytes()==Path('engine/native-before.patch').read_bytes(),'Native source changed')
    dest=out/'source-after';dest.mkdir(exist_ok=True)
    shutil.copy2(Path('kodi')/REL,dest/'InfinityLiveActivity.java.in')
    shutil.copy2(receipt,out/'source-receipt-after.json')
    (out/'baseline164.json').write_text(json.dumps({'apk_sha256':sha(base),'verification':base_proof},indent=2)+'\n')
    print('PASS: exact locked 2103164 -> isolated 2103165 Android-shell delta')

def verify():
    base,_=baseline_identity()
    apk=Path('signed165/Infinity-'+NEW+'.apk')
    audit=json.loads(Path('signed165/background-resume-apk-audit.json').read_text())
    require(audit['apk_sha256']==sha(apk) and audit['version_code']==VERSION,'APK identity mismatch')
    require(audit['signer_certificate_sha256']==CERT and not audit['native_recompiled'],'Signer/native mismatch')
    proof={}
    with zipfile.ZipFile(apk) as new:
        for folder,name in [('baseline164',OLD),('baseline162','1.0.9-Cobra-Theme-Switch-Player-Rotation-RC1')]:
            oldapk=Path(folder)/('Infinity-'+name+'.apk')
            require(oldapk.is_file(),'Missing protected baseline '+str(oldapk))
            with zipfile.ZipFile(oldapk) as old:
                protected={n for n in old.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
                current={n for n in new.namelist() if n.startswith(('lib/','assets/','res/')) or n=='resources.arsc'}
                require(protected==current,'Protected inventory mismatch vs '+folder)
                for n in protected:require(old.read(n)==new.read(n),'Protected bytes changed: '+n)
                proof[folder]={'apk_sha256':sha(oldapk),'protected_entries':len(protected)}
        dex=b''.join(new.read(n) for n in new.namelist() if n.startswith('classes') and n.endswith('.dex'))
        for token in (
            b'CobraPlaybackPolicy',b'cobraApplySystemBarsForSurface',b'cobraConsumeLauncherPipReturn',
            b'cobra_player_refined_chrome',b'Previous channel',b'Next channel',b'Lock controls',
            b'Channels',b'Display',b'Multi-View',b'More'):
            require(token in dex,'Missing compiled contract '+repr(token))
    proof.update(apk_sha256=sha(apk),version_code=VERSION,signer=CERT,native_recompiled=False,
                 locked_base_commit=LOCKED_BASE)
    Path('audit165/apk-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('PASS: signer/native/resources preserved against locked 2103164 and Candidate 14')

def suite(path,count):
    p=Path(path);require(p.is_file(),'Missing Android evidence '+str(p))
    root=ET.parse(p).getroot()
    require(len(root.findall('testcase'))==count,'Unexpected test count '+str(p))
    require(all(int(root.get(k,'0'))==0 for k in ('failures','errors','skipped')),'Incomplete Android suite '+str(p))
    return count

def deliver():
    inherited=0
    for name,count,folder in [
        ('CobraNavigationUiTest',4,'cobra-regression'),('CobraHealthUiTest',7,'cobra-regression'),
        ('Cobra2103159UiTest',2,'experience'),('ExperienceChooserUiTest',6,'experience')]:
        inherited+=suite(Path('audit159/android')/folder/'test-results'/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    for name,count in [('CobraVisualRuntimeTest',17),('CobraVisualLayoutTest',10)]:
        inherited+=suite(Path('audit165/android/runtime/test-results')/('TEST-com.projectinfinity.kodi.'+name+'.xml'),count)
    candidate14=suite('audit165/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml',16)
    locked164=suite('audit165/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103164PlaybackStabilityTest.xml',26)
    new=suite('audit165/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103165InsetsPipPlayerTest.xml',6)
    patch=json.loads(Path('audit165/patch/patch.json').read_text())
    require(len(patch.get('protected_player_methods',{}))==7,'Player contract proof incomplete')
    require(patch.get('status_bar_scope')=='browse-visible / fullscreen-video-hidden','Status-bar contract missing')
    require(patch.get('pip_launcher_return')=='browse' and patch.get('native_pip_expand')=='preserve fullscreen','PiP return contract missing')
    apkproof=json.loads(Path('audit165/apk-verification.json').read_text())
    require(apkproof['apk_sha256']==sha('signed165/Infinity-'+NEW+'.apk'),'APK changed after verification')
    report={
        'build':VERSION,'locked_base_commit':LOCKED_BASE,'protected_candidate14':CANDIDATE14,
        'candidate_locked':False,'inherited_android_tests':inherited,'candidate14_tests':candidate14,
        'locked_2103164_tests':locked164,'new_2103165_tests':new,'total_android_tests':inherited+candidate14+locked164+new,
        'player_contract_methods_protected':len(patch['protected_player_methods']),
        'native_recompiled':False,'physical_device_verified':False,
        'status':'TEST CANDIDATE - physical Fold/PiP acceptance required'
    }
    Path('signed165/ACCEPTANCE.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copy2('audit165/apk-verification.json','signed165/2103165-verification.json')
    shutil.copy2('audit165/patch/patch.json','signed165/2103165-source-proof.json')
    shutil.copy2(ROOT/'AUDIT.md','signed165/AUDIT-2103165.md')
    print('PASS:',report['total_android_tests'],'Android tests; locked 2103164/player contract preserved')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['upgrade','verify','deliver']);a=p.parse_args()
    globals()[a.phase]()
