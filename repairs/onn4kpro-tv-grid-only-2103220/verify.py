#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path

VERSION=2103220
NAME='1.0.9-Cobra-Onn4KPro-TV-Grid-RC3'
PACKAGE='com.projectinfinity.kodi'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
FOLLOWUP='ddb60bd932b929724a9b0d2226043dc54d0d1912'
ABI='armeabi-v7a'
LIB='lib/armeabi-v7a/libkodi.so'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p): return sha_bytes(Path(p).read_bytes())
def require(v,m):
    if not v: raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--badging',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--signing',type=Path,required=True)
    p.add_argument('--python-proof',type=Path,required=True)
    p.add_argument('--grid-proof',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    for path in (a.apk,a.badging,a.manifest,a.signing,a.python_proof,a.grid_proof):
        require(path.is_file(),'Missing verification input: '+str(path))

    badging=a.badging.read_text(errors='replace')
    manifest=a.manifest.read_text(errors='replace')
    signing=a.signing.read_text(errors='replace').lower()
    require(f"package: name='{PACKAGE}' versionCode='{VERSION}' versionName='{NAME}'" in badging,
            'TV APK identity mismatch')
    require("application-label:'Infinity'" in badging,'Infinity label changed')
    require("native-code: 'armeabi-v7a'" in badging,'APK does not advertise armeabi-v7a native code')
    require('android.intent.category.LEANBACK_LAUNCHER' in manifest,'Leanback launcher missing')
    require('banner' in manifest,'Android TV banner missing')
    require('android.hardware.touchscreen' in manifest,'Touchscreen compatibility declaration missing')
    pip_lines=[line for line in manifest.splitlines() if 'supportsPictureInPicture' in line]
    require(pip_lines,'Compiled PiP manifest attribute missing')
    require(all('0xffffffff' not in line.lower() for line in pip_lines),'Compiled TV manifest still enables PiP')
    require(CERT in signing,'Permanent signer changed')

    with zipfile.ZipFile(a.apk) as z:
        names=z.namelist()
        native=[n for n in names if n.startswith('lib/') and not n.endswith('/')]
        require(native,'No native libraries in TV APK')
        require(LIB in native,'armeabi-v7a libkodi.so missing')
        require(all(n.startswith('lib/armeabi-v7a/') for n in native),
                'TV APK contains non-armeabi-v7a native libraries: '+repr([n for n in native if not n.startswith('lib/armeabi-v7a/')]))
        require(not any(n.startswith('lib/arm64-v8a/') for n in native),'arm64 payload leaked into TV APK')
        elf=z.read(LIB)
        require(elf[:4]==b'\x7fELF' and elf[4]==1 and elf[5]==1,'libkodi.so is not little-endian ELF32')
        require(struct.unpack_from('<H',elf,18)[0]==40,'libkodi.so is not ARM32')
        dex=b''.join(z.read(n) for n in names if re.fullmatch(r'classes\d*\.dex',n))
        for token in (
            b'InfinityLiveActivity',
            b'cobra_smart_return_experience_display',
            b'cobraRestoreVodLandingReturn',
            b'LIVE TV AMBIENT BLUE',
            b'Play Next Episode',
            b'Infinity Health Center',
            b'CobraQuickPeekSession',
            b'InfinityCobraRecordingService',
            b'cobra_tv_remote_optimized_2103219',
            b'cobra_tv_grid_only_2103220',
        ):
            require(token in dex,'Locked Infinity/Cobra/TV feature missing: '+repr(token))
        native_hashes={n:sha_bytes(z.read(n)) for n in native}

    proof=json.loads(a.python_proof.read_text())
    require(proof.get('upstream_followup')==FOLLOWUP,'Wrong Python 3.11 GIL follow-up')
    require(all(proof.get('checks',{}).values()),'Python 3.11 GIL source proof failed')

    grid=json.loads(a.grid_proof.read_text())
    require(grid.get('build')==VERSION,'Wrong TV Grid source proof')
    require(grid.get('mobile_fold_untouched') is True,'Mobile/Fold protection missing')
    require(grid.get('grid_only') is True,'TV Grid-only contract missing')
    require(grid.get('drawer_focus_owned') is True and grid.get('drawer_restores_focus') is True,
            'TV drawer focus ownership proof missing')
    require(grid.get('pip_enabled') is False,'TV PiP proof mismatch')
    require(grid.get('rotation_control') is False,'TV rotation control proof mismatch')
    require(grid.get('touch_first') is False,'TV remote-first proof mismatch')
    require(grid.get('refresh_policy')=='60hz','TV 60 Hz policy proof mismatch')
    for key in ('display_performance_setting','background_mode_setting','play_in_background_setting','file_picker_setting','media_during_calls_setting'):
        require(grid.get(key) is False,'TV setting still enabled in source proof: '+key)

    result={
        'build':VERSION,'version_name':NAME,'package':PACKAGE,
        'target':'onn. 4K Pro / Google TV','target_abi':ABI,
        'apk_sha256':sha(a.apk),'signer_certificate_sha256':CERT,
        'libkodi_sha256':native_hashes[LIB],'native_inventory':native_hashes,
        'elf_class':'ELF32','elf_machine':'ARM','leanback_launcher':True,
        'python311_gil_fix':FOLLOWUP,'tv_remote_optimized':True,'tv_grid_only':True,
        'drawer_focus_owned':True,'pip_enabled':False,'rotation_control':False,
        'refresh_policy':'60hz','mobile_fold_untouched':True,
        'physical_device_verified':False,
        'status':'TEST CANDIDATE - physical onn. 4K Pro remote/layout acceptance required',
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('PASS: 2103220 is ARMv7-only, permanently signed, TV Grid-only, PiP-off and remote-first')

if __name__=='__main__': main()
