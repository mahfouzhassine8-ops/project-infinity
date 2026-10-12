#!/usr/bin/env python3
"""Create a permanently signed test APK only after saved tests and source review pass."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
import stage
import delivery_gate
import bytecode_guard
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
from packaging_checks import DEX,SIGNATURE,dex_contract,manifest_tree,resource_ids,run
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE='5d42d0d8ef6a90a5678fd7a24cc4e3b01e2375c213c590a92c178d7a34cc1113'
ENGINE='lib/arm64-v8a/libkodi.so'

def require(value,message):
 if not value:raise RuntimeError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def review(args):
 require(sha(args.base.read_bytes())==stage.TRANSPORT,'Wrong retained 2103369 signed APK')
 approved=json.loads((HERE/'DELIVERY-APPROVAL.json').read_text())
 require(approved['purpose']=='TEST_CANDIDATE_ONLY' and not approved['production_promotion'],'No production promotion is allowed')
 proof=json.loads((args.out/'SOURCE-PRESERVATION.json').read_text())
 require(proof['source_commit']==os.environ['GITHUB_SHA'],'Different source/test commit')
 require(stage.snapshot(args.out/'source')==proof['after'],'Source changed after staging')
 require(stage.snapshot(args.out/'extracted/shell-kodi')==proof['before'],'Reference source changed')
 changed=sorted(n for n in proof['before'].keys()|proof['after'].keys() if proof['before'].get(n)!=proof['after'].get(n))
 require(changed==sorted(stage.RUNTIME+n for n in delivery_gate.SAVED),'Runtime source scope exceeds the two allowed files')
 for n,h in approved['source_hashes'].items():require(proof['after'][stage.RUNTIME+n]==h,'Source differs from reviewed candidate: '+n)
 require(set(approved['source_hashes'])==set(delivery_gate.SAVED),'Incomplete source review')
 results=json.loads((args.out/'RUNTIME-RESULTS.json').read_text());counts=results['totals']
 require(results['source_commit']==os.environ['GITHUB_SHA'] and counts['tests']>=193,'Missing current verification')
 require(all(counts[k]==0 for k in ('failures','errors','skipped')),'A required test failed or was skipped')
 preserved=json.loads((args.out/'SAVED-TEST-PRESERVATION.json').read_text())
 require(preserved['original_test_names_preserved']==185 and preserved['inherited_sources_unchanged'],'Saved tests were altered')
 tool=args.out/'member-tool';tool.mkdir(exist_ok=True)
 subprocess.run(['javac','-d',str(tool),str(HERE/'MemberInventory.java')],check=True)
 inventory=[];total=0
 for n in delivery_gate.SAVED:
  maps=[]
  for label,root in [('approved',args.out/'extracted/shell-kodi'),('candidate',args.out/'source')]:
   result=args.out/(n+'.'+label+'.members.json')
   subprocess.run(['java','-cp',str(tool),'MemberInventory',str(root/stage.RUNTIME/n),str(result)],check=True)
   maps.append(json.loads(result.read_text()))
  before,after=maps;total+=len(before)
  for key in sorted(before.keys()|after.keys()):
   if before.get(key)==after.get(key):continue
   require(key in after,'Original source member removed: '+key)
   requirements=approved['members'].get(key)
   require(requirements and all(i in range(1,7) for i in requirements),'Unmapped source member: '+key)
   inventory.append({'file':stage.RUNTIME+n,'member':key,'requirements':requirements,'before':before.get(key),'after':after[key],'change':'added' if key not in before else 'changed'})
 require({r['member'] for r in inventory}==set(approved['members']),'Reviewed member set differs from current source')
 report={'approved_named_members_checked':total,'changes':inventory,'all_changes_mapped':True,'other_runtime_files_byte_identical':len(proof['before'])-2,'source_hashes':approved['source_hashes'],'review_reference_run':approved['reviewed_run'],'source_commit':os.environ['GITHUB_SHA'],'parser':'JDK canonical named-member trees; method hashes include complete anonymous class bodies'}
 write(args.out/'CHANGED-MEMBERS.json',report)
 print('PASS source and saved-test gates:',len(inventory),'mapped members;',counts['tests'],'passing tests')
 return report,counts

def payload(base,donor,out):
 with zipfile.ZipFile(base) as a,zipfile.ZipFile(donor) as b:
  for z in (a,b):require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'Corrupt or duplicate APK input')
  require(sha(a.read(ENGINE))==NATIVE,'Retained native engine mismatch')
  require(not any(n.startswith(('lib/','assets/')) and not n.endswith('/') for n in b.namelist()),'Unexpected native/assets in Android donor')
  require(dex_contract(a)[0]==dex_contract(b)[0],'JNI/native method contracts changed')
  kept={n for n in a.namelist() if n!='AndroidManifest.xml' and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
  with zipfile.ZipFile(out,'w') as z:
   for info in a.infolist():
    if info.filename in kept:z.writestr(copy.copy(info),a.read(info.filename))
   for info in b.infolist():
    if info.filename=='AndroidManifest.xml' or DEX.fullmatch(info.filename):z.writestr(copy.copy(info),b.read(info.filename))
  return kept

def package(args):
 source,counts=review(args)
 bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
 donor=args.build/'xbmc/build/outputs/apk/release/xbmc-release.apk';require(donor.is_file(),'Android donor was not assembled')
 require(resource_ids(bt/'aapt2',args.base,args.out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,args.out/'donor-resources.txt'),'Android resource IDs changed')
 trees=[]
 for label,apk in [('base',args.base),('donor',donor)]:
  tree=manifest_tree(run(bt/'aapt','dump','xmltree',apk,'AndroidManifest.xml',output=args.out/(label+'-manifest.txt')))
  for field in ('android:versionCode','android:versionName'):tree['attrs'].pop(field,None)
  trees.append(tree)
 require(trees[0]==trees[1],'Manifest changed outside test-candidate version')
 dex=bytecode_guard.compare(args.base,donor,(args.build/'preservation-classpath.txt').read_text().strip(),args.out)
 unsigned=args.out/'cobra-unsigned.apk';kept=payload(args.base,donor,unsigned)
 # All four existing permanent-signing settings are mandatory. There is no test-key fallback.
 for key in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
  require(bool(os.environ.get(key)),'Missing permanent signing setting: '+key)
 final=args.out/'Cobra-2103372-Six-Verified-RC1.apk'
 run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
 for label,apk in [('base',args.base),('final',final)]:
  certificate=run(bt/'apksigner','verify','--verbose','--print-certs',apk,output=args.out/(label+'-signature.txt'))
  require(CERT in certificate.lower(),'Permanent signer differs from original: '+label)
 badging=run(bt/'aapt','dump','badging',final,output=args.out/'badging.txt')
 require(f"package: name='com.projectinfinity.kodi' versionCode='{delivery_gate.VERSION}' versionName='{delivery_gate.RELEASE}'" in badging,'Wrong test candidate identity')
 require('application-debuggable' not in badging,'Test candidate must not be debuggable')
 run(bt/'zipalign','-c','-p','4',final,output=args.out/'alignment.txt')
 with zipfile.ZipFile(args.base) as a,zipfile.ZipFile(donor) as d,zipfile.ZipFile(final) as b:
  require(b.testzip() is None and len(b.namelist())==len(set(b.namelist())),'Final APK integrity failure')
  expected=kept|{'AndroidManifest.xml'}|{n for n in b.namelist() if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
  require(set(b.namelist())==expected,'Unexpected packaged payload')
  for n in kept:require(a.read(n)==b.read(n),'Protected APK entry changed: '+n)
  for n in d.namelist():
   if DEX.fullmatch(n) or n=='AndroidManifest.xml':require(d.read(n)==b.read(n),'Compiled donor changed during signing: '+n)
  native_hashes={n:sha(b.read(n)) for n in kept if n.startswith('lib/') and not n.endswith('/')}
 receipt={'file':final.name,'bytes':final.stat().st_size,'sha256':sha(final.read_bytes()),'package':'com.projectinfinity.kodi','version_code':delivery_gate.VERSION,'version_name':delivery_gate.RELEASE,'source_commit':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'tests':counts,'original_185_preserved':True,'permanent_signer_sha256':CERT,'native_rebuilt':False,'native_libraries_preserved':native_hashes,'protected_payload_entries':len(kept),'protected_decoded_classes':dex['protected_classes_checked'],'manifest_preserved_except_version':True,'resources_and_assets_byte_identical':True,'approved_cobra_source':'9f621f34e3ded845e1c3e9c2a49d98158b6e31b3','transport_source':'9abf7c84fbd8224958bc8465c983429bc5976074','transport_apk_sha256':stage.TRANSPORT,'device_test_pending':True,'locked':False,'production_promoted':False}
 write(args.out/'DELIVERY.json',receipt);unsigned.unlink();print('PASS permanently signed TEST candidate:',final.name,receipt['sha256'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['review','package'])
 for n in ('base','build','out'):p.add_argument('--'+n,type=Path,required=True)
 args=p.parse_args();(review if args.mode=='review' else package)(args)
