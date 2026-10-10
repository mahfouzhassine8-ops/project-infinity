#!/usr/bin/env python3
"""Verify the candidate against the exact installed 2103361 APK, beyond donor lineage."""
import argparse,hashlib,json,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'repairs/mobile-regressions-2103304'))
from packaging_checks import DEX,SIGNATURE,dex_contract,require
BASELINE_SHA='70440287e3ac908b1518611992362c2de666a0e6e58cc27083812ba6943fd4c3'
def compare(a,b):
 allowed={'AndroidManifest.xml','lib/arm64-v8a/libkodi.so'}
 left={n for n in a.namelist() if not SIGNATURE.fullmatch(n)};right={n for n in b.namelist() if not SIGNATURE.fullmatch(n)}
 require(left==right,'Candidate APK entry inventory drift from installed 2103361')
 protected=[n for n in sorted(left) if n not in allowed and not DEX.fullmatch(n)]
 for n in protected:require(a.read(n)==b.read(n),'Installed 2103361 protected payload changed: '+n)
 old_jni,old_classes=dex_contract(a);new_jni,new_classes=dex_contract(b)
 require(old_jni==new_jni and old_classes==new_classes,'Installed 2103361 Java/JNI coverage drift')
 return {'baseline_version':2103361,'baseline_sha256':BASELINE_SHA,'protected_entries_unchanged':len(protected),'java_class_and_jni_inventory_unchanged':True,'allowed_byte_changes':['manifest candidate identity','native engine','DEX generated candidate identity','APK signature blocks'],'physical_device_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 require(hashlib.sha256(a.baseline.read_bytes()).hexdigest()==BASELINE_SHA,'Wrong installed 2103361 baseline APK')
 with zipfile.ZipFile(a.baseline) as x,zipfile.ZipFile(a.candidate) as y:result=compare(x,y)
 a.report.write_text(json.dumps(result,indent=2)+'\n');print('PASS: exact installed 2103361 protected APK payload and Java/JNI inventories')
