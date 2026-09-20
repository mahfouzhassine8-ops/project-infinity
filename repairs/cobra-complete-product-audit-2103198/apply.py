#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re,xml.etree.ElementTree as ET

MANIFEST=Path('tools/android/packaging/xbmc/AndroidManifest.xml.in')
ACTIVITY=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103197
BASE_COMMIT='b5fa21731a1662cc7206ac6dc45cb6d6682612cd'
BOOT='android.permission.RECEIVE_BOOT_COMPLETED'

def sha(v):
    if isinstance(v,Path): return hashlib.sha256(v.read_bytes()).hexdigest()
    if isinstance(v,str): v=v.encode()
    return hashlib.sha256(v).hexdigest()

def require(v,msg):
    if not v: raise RuntimeError(msg)

def apply(source:Path,receipt:Path,out:Path):
    data=json.loads(receipt.read_text())
    require(data.get('version_code')==BASE_BUILD,'2103198 requires exact 2103197 source receipt')
    require(data.get('version_name')=='1.0.9-Cobra-Original-Player-Menu-RC1','Unexpected 2103197 version name')
    manifest=source/MANIFEST
    activity=source/ACTIVITY
    before=manifest.read_text()
    activity_before=sha(activity)
    pat=re.compile(r'^[ \t]*<uses-permission\s+android:name="' + re.escape(BOOT) + r'"\s*/>\s*\n',re.M)
    matches=list(pat.finditer(before))
    require(len(matches)==2,f'Expected inherited duplicate {BOOT} permission, found {len(matches)}')
    first=matches[0]
    after=before[:first.start()]+before[first.end():]
    ET.fromstring(after)
    require(len(list(pat.finditer(after)))==1,'Boot permission cleanup did not leave exactly one declaration')
    manifest.write_text(after)
    require(sha(activity)==activity_before,'2103198 must not modify Cobra Activity runtime')
    out.mkdir(parents=True,exist_ok=True)
    report={
      'base_build':BASE_BUILD,
      'base_commit':BASE_COMMIT,
      'files':{str(MANIFEST):{'before':sha(before),'after':sha(after)}},
      'duplicate_receive_boot_completed_before':2,
      'duplicate_receive_boot_completed_after':1,
      'activity_runtime_changed':False,
      'playback_behavior_changed':False,
      'network_selection_changed':False,
      'timeshift_ownership_changed':False,
      'buffer_policy_changed':False,
      'parser_flags_changed':False,
      'native_changed':False,
      'theme_zip_changed':False,
      'physical_device_verified':False
    }
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103198 removes one inherited duplicate RECEIVE_BOOT_COMPLETED declaration only; Cobra runtime untouched')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    apply(a.source,a.receipt,a.out)
