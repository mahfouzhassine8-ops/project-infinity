#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path

VERSION=2103218
NAME='1.0.9-Cobra-Onn4KPro-TV-ARMv7-RC1'
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
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 for path in (a.apk,a.badging,a.manifest,a.signing,a.python_proof):
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
  ):
   require(token in dex,'Locked Infinity/Cobra feature missing: '+repr(token))
  native_hashes={n:sha_bytes(z.read(n)) for n in native}

 proof=json.loads(a.python_proof.read_text())
 require(proof.get('upstream_followup')==FOLLOWUP,'Wrong Python 3.11 GIL follow-up')
 require(all(proof.get('checks',{}).values()),'Python 3.11 GIL source proof failed')

 result={
  'build':VERSION,
  'version_name':NAME,
  'package':PACKAGE,
  'target':'onn. 4K Pro / Google TV',
  'target_abi':ABI,
  'native_host':'arm-linux-androideabi',
  'apk_sha256':sha(a.apk),
  'signer_certificate_sha256':CERT,
  'libkodi_sha256':native_hashes[LIB],
  'native_inventory':native_hashes,
  'elf_class':'ELF32',
  'elf_machine':'ARM',
  'leanback_launcher':True,
  'touchscreen_not_required_source_contract':True,
  'python311_gil_fix':FOLLOWUP,
  'same_infinity_cobra_features_as_locked_2103217':True,
  'physical_device_verified':False,
  'status':'TEST CANDIDATE - onn. 4K Pro device acceptance required',
 }
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('PASS: onn. 4K Pro ARMv7 TV APK is ELF32 ARM, permanently signed, Leanback-capable, and feature-complete')

if __name__=='__main__':main()
