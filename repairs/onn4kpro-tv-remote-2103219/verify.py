#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path

VERSION=2103219
NAME='1.0.9-Cobra-Onn4KPro-TV-Remote-RC2'
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
    p.add_argument('--remote-proof',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()

    for path in (a.apk,a.badging,a.manifest,a.signing,a.python_proof,a.remote_proof):
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
    require('android.hardware.touchscreen' in manifest,'Touchscreen feature declaration missing')
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
        require(elf[:4]==b'\x7fELF','libkodi.so is not ELF')
        require(elf[4]==1,'libkodi.so is not ELF32')
        require(elf[5]==1,'libkodi.so is not little-endian ELF')
        machine=struct.unpack_from('<H',elf,18)[0]
        require(machine==40,'libkodi.so is not ARM32 (e_machine=%d)'%machine)
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
        ):
            require(token in dex,'Locked Infinity/Cobra/TV feature missing: '+repr(token))
        native_hashes={n:sha_bytes(z.read(n)) for n in native}

    proof=json.loads(a.python_proof.read_text())
    require(proof.get('upstream_followup')==FOLLOWUP,'Wrong Python 3.11 GIL follow-up')
    require(all(proof.get('checks',{}).values()),'Python 3.11 GIL source proof failed')

    remote=json.loads(a.remote_proof.read_text())
    require(remote.get('build')==VERSION,'Wrong TV remote source proof')
    require(remote.get('mobile_fold_untouched') is True,'Mobile/Fold protection missing')
    require(remote.get('focus_animation_on_dpad') is False,'D-pad focus fast path missing')
    require(remote.get('guide_focus_debounce_ms')==45,'Guide focus debounce mismatch')
    require(remote.get('drawer_remote_focusable') is True,'Drawer remote focus proof missing')

    result={
        'build':VERSION,
        'version_name':NAME,
        'package':PACKAGE,
        'target':'onn. 4K Pro / Google TV',
        'target_abi':ABI,
        'apk_sha256':sha(a.apk),
        'signer_certificate_sha256':CERT,
        'libkodi_sha256':native_hashes[LIB],
        'native_inventory':native_hashes,
        'elf_class':'ELF32',
        'elf_machine':'ARM',
        'leanback_launcher':True,
        'python311_gil_fix':FOLLOWUP,
        'tv_remote_optimized':True,
        'focus_animation_on_dpad':False,
        'guide_focus_debounce_ms':45,
        'mobile_fold_untouched':True,
        'physical_device_verified':False,
        'status':'TEST CANDIDATE - physical onn. remote acceptance required',
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('PASS: 2103219 is ARMv7-only, permanently signed, feature-complete, and TV-remote optimized')

if __name__=='__main__':
    main()
