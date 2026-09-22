#!/usr/bin/env python3
"""Apply the scoped 2103210 Movies/Shows + chooser Health Center Android-shell delta.

Live TV contracts are hash-gated before and after application. This script never
rebuilds or mutates the native engine.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = 2103210
OLD_VERSION = 2103209
OLD_NAME = '1.0.9-Cobra-Python311-GIL-Stability-RC1'
NEW_NAME = '1.0.9-Cobra-Media-Library-Health-RC1'
SOURCE = 'tools/android/packaging/xbmc/src/'
FILES = {
    SOURCE+'InfinityLiveActivity.java.in': ('8e930cf0a018950ea2e86923684bcfc7076298b09c6c5c8d8d72c90808508dc5','0d5172b619c8901994eb332050ae2330b0b6b607dae5e58e84a5b332581a8f5b'),
    SOURCE+'Splash.java.in': ('89d10b3eab529cb3faa3a810acf66cb2f30d3e6b1a03757deb40473b1131b121','e440ed7cfff5021c4e620ef825669c3e63126ce18e0fbeaa58a39cba3e216e93'),
    SOURCE+'Main.java.in': ('ddf18d30c4040369b30e861ded588a53846ff3de319a89a219344771f8db9318','240d08c21cbdbdfbff8f06f4af3f7a633516d499e49a24481c304990a705173f'),
}
PATCH_SHA = '9e579dce98126a3ea0118d6b6fbc99c30cb57984883934298444127d47fc770c'
NATIVE_SHA = 'db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PROTECTED = {
 'private void cobraOpenLiveTv()':'ca2104682cc43724a138310dac87361973d57a40a00a5db0e6557a3fa8f6a602',
 'private void showGuide()':'f57772610779aea49fc43c6d94db2df804e911e9c82cf224d9e5f6f96f9a93a4',
 'private void startSinglePlayer(String url)':'1c1a40c28072b5876e61ecedc5c64cfb6483b8d1c464041a16ee2b0128213708',
 'private void cobraShowQuickPeek(Channel channel,View anchor)':'bea049b1f6941709e13545eefd647915c64c2500e6b6716da2e246ab3718f869',
 'private void cobraStartLocalTimeshift':'758df5bc2d2c32df5836b13c23b33a44c35a90ef910cf3513516e4f8a3a6800a',
 'private void playChannel(Channel channel)':'48729254f6a27441b487fe8425b899ede48a804819c3d6bb466695d654087de3',
 'private void startCobraPreview(Channel channel)':'db8403d7256e8d353c9b7cef8397076ef7874646782d3972e7b3db2afa0a227c',
 'private void releaseSinglePlayer()':'1cd0ff7182a28e632f6601202c57050c87de10a923080ee64c062ced76f5b385',
 'private void releaseMulti()':'cc1a975f97fbb11dc9faa12f07e76045980e89911ed1f6cc7f0d8899886a1cad',
 'private LoadResult loadXtream(LiveSource source)':'6e9c2300e1c65095f2f8340f8764783e6852cbd8ccbc23ad238d14172e3ac2cb',
 'private LoadResult loadM3u(LiveSource source)':'ba2a26616379cd59e6b0514258e2734a19925f48627065ca33095793977d11b0',
}

def sha_bytes(data: bytes)->str:return hashlib.sha256(data).hexdigest()
def sha(path: Path)->str:return sha_bytes(path.read_bytes())
def require(v: bool,msg: str)->None:
    if not v: raise RuntimeError(msg)

def method(text: str, signature: str)->str:
    i=text.find(signature);require(i>=0,'Missing protected Live TV method: '+signature)
    b=text.find('{',i);require(b>=0,'Malformed protected method: '+signature)
    depth=0
    for j in range(b,len(text)):
        if text[j]=='{':depth+=1
        elif text[j]=='}':
            depth-=1
            if depth==0:return text[i:j+1]
    raise RuntimeError('Unbalanced protected method: '+signature)

def live_contract(text: str)->dict:
    result={}
    for sig,expected in PROTECTED.items():
        digest=sha_bytes(method(text,sig).encode())
        result[sig]=digest
        require(digest==expected,'Live TV contract drift before patch: '+sig)
    return result

def patch_identity_scripts():
    runtime=Path('scripts/infinity_background_resume.py')
    text=runtime.read_text()
    require(f'VERSION_CODE = {OLD_VERSION}' in text,'2103209 runtime version anchor missing')
    require("RELEASE = '"+OLD_NAME+"'" in text,'2103209 runtime release anchor missing')
    runtime.write_text(text.replace(f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}',1)
                           .replace("RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",1))
    packager=Path('scripts/package_background_resume.py')
    p=packager.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
    require(p.count(old)>=2,'2103209 packager identity anchor missing')
    p=p.replace(old,new)
    obsolete="for token in (b'InfinityExtendedBackgroundService',b'EXTENDED BACKGROUND MODE',b'InfinityCoreBridge',b'InfinityCobraDeviceBridge',b'getPlayWhenReady',b'Turn off'):"
    current="for token in (b'InfinityExtendedBackgroundService',b'InfinityBackgroundControlActivity',b'BACKGROUND_MODE_NORMAL',b'BACKGROUND_MODE_EXTENDED',b'InfinityCoreBridge',b'InfinityCobraDeviceBridge',b'getPlayWhenReady',b'Turn off'):"
    require(p.count(obsolete)==1,'Obsolete 2103209 runtime-token verifier anchor missing')
    p=p.replace(obsolete,current,1)
    packager.write_text(p)

def apply(shell: Path):
    require(sha(ROOT/'ui.patch')==PATCH_SHA,'Reviewed UI patch drift')
    before={name:sha(shell/name) for name in FILES}
    for name,(expected,_) in FILES.items():require(before[name]==expected,'Wrong exact 2103208 Android parent source: '+name)
    activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
    before_live=live_contract(activity.read_text())
    subprocess.run(['git','apply','--check',str(ROOT/'ui.patch')],cwd=shell,check=True)
    subprocess.run(['git','apply',str(ROOT/'ui.patch')],cwd=shell,check=True)
    for name,(_,expected) in FILES.items():require(sha(shell/name)==expected,'Unexpected scoped patch result: '+name)
    after_live=live_contract(activity.read_text())
    require(before_live==after_live,'Live TV method bytes changed')

    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
    require(g.count(f'versionCode {OLD_VERSION}')==1,'2103209 Gradle version anchor missing')
    require(g.count('versionName "'+OLD_NAME+'"')==1,'2103209 Gradle name anchor missing')
    gradle.write_text(g.replace(f'versionCode {OLD_VERSION}',f'versionCode {VERSION}',1)
                       .replace('versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"',1))
    patch_identity_scripts()

    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    require(receipt.get('version_code')==OLD_VERSION,'Wrong prepared 2103209 source receipt')
    for name in FILES:
        require(name in receipt.get('files',{}),'Patched source absent from receipt: '+name)
        receipt['files'][name]['after']=sha(shell/name)
    gradle_rel='tools/android/packaging/xbmc/build.gradle.in'
    receipt['files'][gradle_rel]['after']=sha(gradle)
    receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
                   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
                   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,
                   native_engine_sha256=NATIVE_SHA,live_tv_source_untouched=True,
                   movies_shows_cinematic_browse=True,kodi_health_center_chooser_shortcut=True)
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final successor shell receipt drift: '+name)
    Path('audit210').mkdir(exist_ok=True)
    (Path('audit210')/'scope.json').write_text(json.dumps({
      'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,
      'changed_java_files':sorted(FILES),'live_tv_protected_methods':before_live,
      'live_tv_source_untouched':True,'native_engine_rebuilt':False,
      'health_center_addon':'script.kodihealthcenter'
    },indent=2)+'\n')
    print('PASS: scoped Movies/Shows + Kodi Health Center shell applied; protected Live TV methods unchanged')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
