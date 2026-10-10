#!/usr/bin/env python3
"""Compare Resume speed candidate with exact green 2103362; only two script assets may change."""
import argparse,hashlib,io,json,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'repairs/mobile-regressions-2103304'))
from packaging_checks import DEX,SIGNATURE,dex_contract,require
BASELINE_SHA='3c6f171895b3ac04ec11722611450854602ea623097e4859a08614d19c542db5'
ASSETS={'assets/infinity/checkpoint-controller.zip','assets/infinity/checkpoint-controller-20.zip'}
def compare(a,b):
 allowed={'AndroidManifest.xml','lib/arm64-v8a/libkodi.so'}|ASSETS
 left={n for n in a.namelist() if not SIGNATURE.fullmatch(n)};right={n for n in b.namelist() if not SIGNATURE.fullmatch(n)}
 require(left==right,'Candidate APK inventory drift from green 2103362')
 protected=[n for n in sorted(left) if n not in allowed and not DEX.fullmatch(n)]
 for n in protected:require(a.read(n)==b.read(n),'Green 2103362 protected payload changed: '+n)
 old_jni,old_classes=dex_contract(a);new_jni,new_classes=dex_contract(b)
 require(old_jni==new_jni and old_classes==new_classes,'Green 2103362 Java/JNI inventory drift')
 for name in ASSETS:
  with zipfile.ZipFile(io.BytesIO(a.read(name))) as old,zipfile.ZipFile(io.BytesIO(b.read(name))) as new:
   require(set(old.namelist())==set(new.namelist()),'Script asset inventory changed: '+name)
   prior=json.loads(old.read('manifest.json'));current=json.loads(new.read('manifest.json'))
   for key in ('schema','addon_id','addon_version','addon_xml_sha256'):require(prior[key]==current[key],'Script asset identity changed: '+key)
   pins={x['path']:x for x in prior['files']}
   require(set(pins)=={x['path'] for x in current['files']},'Script manifest inventory changed')
   for row in current['files']:
    p=row['path'];require(row['before']==pins[p]['before'] and row['previous']==pins[p]['after'],'Unreviewed script upgrade preimage: '+p)
    raw=new.read('payload/'+p);require(hashlib.sha256(raw).hexdigest()==row['after'],'Bad script payload hash: '+p)
    if p not in ('service.py','plugin.py','resume_hub.py'):require(raw==old.read('payload/'+p),'Unrelated script changed: '+p)
 return dict(baseline_version=2103362,baseline_sha256=BASELINE_SHA,protected_entries_unchanged=len(protected),java_class_and_jni_inventory_unchanged=True,changed_script_files=['service.py','plugin.py','resume_hub.py'],physical_device_verified=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 require(hashlib.sha256(a.baseline.read_bytes()).hexdigest()==BASELINE_SHA,'Wrong green 2103362 baseline APK')
 with zipfile.ZipFile(a.baseline) as x,zipfile.ZipFile(a.candidate) as y:result=compare(x,y)
 a.report.write_text(json.dumps(result,indent=2)+'\n');print('PASS exact green 2103362 payload, reviewed script upgrade and Java/JNI inventories')
