#!/usr/bin/env python3
"""Static manifest boundary regression; does not simulate Android ActivityManager."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--packager',type=Path);p.add_argument('--old-manifest',type=Path);p.add_argument('--new-manifest',type=Path);a=p.parse_args()
module_path=Path(__file__).resolve().parents[1]/'apply_packaging.py'
s=importlib.util.spec_from_file_location('packaging_repair',module_path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
text=a.manifest.read_text();ns=m.ANDROID
tree=ET.fromstring(text);target=tree.find("./application/activity[@%sname='%s']"%(ns,m.TARGET))
assert target is not None and target.get(ns+'exported')=='false'
assert {x.get(ns+'name') for x in target.findall('./intent-filter/action')}=={'com.projectinfinity.kodi.action.BACKGROUND_MODE_NORMAL','com.projectinfinity.kodi.action.BACKGROUND_MODE_EXTENDED'}
for name in ['.content.XBMCFileContentProvider','.content.XBMCMediaContentProvider','.content.XBMCYTDLContentProvider']:
 node=tree.find("./application/provider[@%sname='%s']"%(ns,name));assert node is not None and node.get(ns+'exported')=='true'
assert tree.find("./application/service[@%sname='.InfinityExtendedBackgroundService']"%ns).get(ns+'exported')=='false'
original=text.replace('android:name=".InfinityBackgroundControlActivity"\n            android:exported="false"','android:name=".InfinityBackgroundControlActivity"\n            android:exported="true"',1)
assert hashlib.sha256(original.encode()).hexdigest()==m.BASE_MANIFEST_SHA256
assert m.transform(original)==text
for malformed in [original+'\n',text,original.replace('BACKGROUND_MODE_NORMAL','BACKGROUND_MODE_OTHER')]:
 try:m.transform(malformed)
 except RuntimeError:pass
 else:raise AssertionError('Drift or repeated application must be rejected')
a.out.mkdir(parents=True,exist_ok=True)
report={'manifest_sha256':hashlib.sha256(text.encode()).hexdigest(),'background_bridge_exported':False,'action_contracts_preserved':True,'provider_exports_preserved':True,'only_expected_manifest_attribute_changed':True,'malformed_preimages_rejected':3,'verification_level':'source/static manifest and transformation checks','android_external_activity_denial_tested':False,'physical_device_verified':False}
if a.packager:
 assert a.old_manifest and a.new_manifest
 parsed=ast.parse(a.packager.read_text())
 names={'manifest_tree','verify_manifest_pair','require'}
 functions=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert {f.name for f in functions}==names
 executable=ast.Module(body=functions,type_ignores=[]);context={}
 exec(compile(executable,str(a.packager),'exec'),context)
 old=a.old_manifest.read_text();new=a.new_manifest.read_text()
 # A pre-repair 198 dump can be used as a fixture by changing the sole bridge
 # export flag. An actual repaired candidate dump is accepted unchanged.
 name='A: android:name(0x01010003)="com.projectinfinity.kodi.InfinityBackgroundControlActivity"'
 at=new.index(name);end=new.index('      E:',at)
 bridge=new[at:end]
 if '(0x01010010)=(type 0x12)0xffffffff' in bridge:
  bridge=bridge.replace('(0x01010010)=(type 0x12)0xffffffff','(0x01010010)=(type 0x12)0x0',1);new=new[:at]+bridge+new[end:]
 context['verify_manifest_pair'](old,new)
 bad=[new.replace('BACKGROUND_MODE_NORMAL','BACKGROUND_MODE_OTHER'),new.replace('InfinityBackgroundControlActivity','DifferentBackgroundControlActivity'),new.replace('XBMCFileContentProvider','UnexpectedFileProvider')]
 private='(0x01010010)=(type 0x12)0x0'
 bad.append(new[:at]+new[at:].replace(private,'(0x01010010)=(type 0x12)0xffffffff',1))
 live=new.index('A: android:name(0x01010003)="com.projectinfinity.kodi.InfinityLiveActivity"')
 bad.append(new[:live]+new[live:].replace('(0x01010010)=(type 0x12)0xffffffff',private,1))
 for drift in bad:
  try:context['verify_manifest_pair'](old,drift)
  except RuntimeError:pass
  else:raise AssertionError('Manifest gate accepted unrelated component/action/export drift')
 report['generated_packager_expected_manifest_pass']=True
 report['generated_packager_adversarial_drifts_rejected']=len(bad)
(a.out/'background-bridge-boundary.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: private same-UID background bridge; action/provider/service contracts preserved. Source/static only.')
