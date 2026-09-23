#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path

VERSION=2103221
NAME='1.0.9-Cobra-Onn4KPro-TV-Remote-UI-RC4'
PACKAGE='com.projectinfinity.kodi'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
FOLLOWUP='ddb60bd932b929724a9b0d2226043dc54d0d1912'
ABI='armeabi-v7a'
LIB='lib/armeabi-v7a/libkodi.so'

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def require(v,m):
    if not v:raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--badging',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--signing',type=Path,required=True)
    p.add_argument('--python-proof',type=Path,required=True)
    p.add_argument('--grid-proof',type=Path,required=True)
    p.add_argument('--remote-ui-proof',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    for path in (a.apk,a.badging,a.manifest,a.signing,a.python_proof,a.grid_proof,a.remote_ui_proof):
        require(path.is_file(),'Missing verification input: '+str(path))

    badging=a.badging.read_text(errors='replace');manifest=a.manifest.read_text(errors='replace');signing=a.signing.read_text(errors='replace').lower()
    require(f"package: name='{PACKAGE}' versionCode='{VERSION}' versionName='{NAME}'" in badging,'TV APK identity mismatch')
    require("application-label:'Infinity'" in badging,'Infinity label changed')
    require("native-code: 'armeabi-v7a'" in badging,'APK does not advertise armeabi-v7a native code')
    require('android.intent.category.LEANBACK_LAUNCHER' in manifest,'Leanback launcher missing')
    require('banner' in manifest,'Android TV banner missing')
    pip_lines=[line for line in manifest.splitlines() if 'supportsPictureInPicture' in line]
    require(pip_lines and all('0xffffffff' not in line.lower() for line in pip_lines),'Compiled TV manifest enables PiP')
    require(CERT in signing,'Permanent signer changed')

    with zipfile.ZipFile(a.apk) as z:
        names=z.namelist();native=[n for n in names if n.startswith('lib/') and not n.endswith('/')]
        require(native and LIB in native,'armeabi-v7a libkodi.so missing')
        require(all(n.startswith('lib/armeabi-v7a/') for n in native),'Non-ARMv7 native library leaked into TV APK')
        require(not any(n.startswith('lib/arm64-v8a/') for n in native),'arm64 payload leaked into TV APK')
        elf=z.read(LIB);require(elf[:4]==b'\x7fELF' and elf[4]==1 and elf[5]==1,'libkodi.so is not little-endian ELF32')
        require(struct.unpack_from('<H',elf,18)[0]==40,'libkodi.so is not ARM32')
        dex=b''.join(z.read(n) for n in names if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
            b'InfinityLiveActivity',b'cobra_smart_return_experience_display',b'cobraRestoreVodLandingReturn',
            b'LIVE TV AMBIENT BLUE',b'Play Next Episode',b'Infinity Health Center',
            b'CobraQuickPeekSession',b'InfinityCobraRecordingService',
            b'cobra_tv_remote_optimized_2103219',b'cobra_tv_grid_only_2103220',
            b'cobra_tv_remote_ui_2103221',
        ):require(token in dex,'Locked Infinity/Cobra/TV feature missing: '+repr(token))
        native_hashes={n:sha_bytes(z.read(n)) for n in native}

    proof=json.loads(a.python_proof.read_text())
    require(proof.get('upstream_followup')==FOLLOWUP and all(proof.get('checks',{}).values()),'Python 3.11 GIL proof failed')

    grid=json.loads(a.grid_proof.read_text())
    require(grid.get('build')==2103220 and grid.get('grid_only') is True,'2103220 Grid parent proof mismatch')
    require(grid.get('mobile_fold_untouched') is True and grid.get('pip_enabled') is False,'2103220 protected TV contract mismatch')

    remote=json.loads(a.remote_ui_proof.read_text())
    require(remote.get('build')==VERSION,'Wrong TV Remote UI proof')
    for key in (
        'mobile_fold_untouched','group_overlay_always','group_current_focus','guide_initial_focus',
        'player_primary_focus','player_back_layers','timeline_dpad','player_drawer_current_focus',
        'player_drawer_one_press_tune','playback_engine_unchanged',
    ):require(remote.get(key) is True,'Remote UI proof missing '+key)
    require(remote.get('preview_focusable') is False and remote.get('preview_phone_controls') is False,'Preview is still phone-focusable')
    require(remote.get('quick_peek_video_focusable') is False,'Quick Peek video still owns remote focus')

    result={
        'build':VERSION,'version_name':NAME,'package':PACKAGE,'target':'onn. 4K Pro / Google TV','target_abi':ABI,
        'apk_sha256':sha(a.apk),'signer_certificate_sha256':CERT,'libkodi_sha256':native_hashes[LIB],
        'native_inventory':native_hashes,'elf_class':'ELF32','elf_machine':'ARM','leanback_launcher':True,
        'python311_gil_fix':FOLLOWUP,'tv_grid_only':True,'tv_remote_ui':True,'group_overlay_always':True,
        'group_current_focus':True,'guide_initial_focus':True,'preview_focusable':False,
        'player_primary_focus':True,'player_back_layers':True,'timeline_dpad':True,
        'player_drawer_current_focus':True,'player_drawer_one_press_tune':True,
        'pip_enabled':False,'refresh_policy':'60hz','mobile_fold_untouched':True,
        'physical_device_verified':False,
        'status':'TEST CANDIDATE - physical onn. 4K Pro group/player/preview acceptance required',
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('PASS: 2103221 ARMv7 TV Remote UI candidate is signed, Grid-only and remote-first')

if __name__=='__main__':main()
