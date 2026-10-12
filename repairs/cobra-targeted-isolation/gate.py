#!/usr/bin/env python3
"""Preserve all 193 delivered cases; add 12 regression cases and bounded source review."""
import argparse, difflib, hashlib, importlib.util, json, os, shutil, subprocess, sys, tarfile, zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/cobra-clean-restart'))
import stage, delivery_gate, package_test
spec=importlib.util.spec_from_file_location('targeted_changes',HERE/'apply.py')
changes=importlib.util.module_from_spec(spec);spec.loader.exec_module(changes)
VERSION=2103373
RELEASE='1.0.9-Cobra-Targeted-Isolation-RC1'
NAME='Cobra-2103373-Targeted-Isolation-RC1.apk'
EXTRA='CobraTargetedIsolationTest'
delivery_gate.EXTRA[EXTRA]=12
delivery_gate.VERSION=VERSION;delivery_gate.RELEASE=RELEASE

def require(ok,message):
 if not ok:raise RuntimeError(message)
def write(p,data):p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare(args):
 # The old preparer stages this supplemental class from its own directory.
 shutil.copy2(HERE/(EXTRA+'.java'),ROOT/'repairs/cobra-clean-restart'/(EXTRA+'.java'))
 delivery_gate.prepare(args)
 source=args.out/'source';parent=args.out/'parent-2103372';shutil.copytree(source,parent)
 approval=json.loads((HERE/'APPROVAL.json').read_text())
 require(sha(parent/stage.RUNTIME/'InfinityLiveActivity.java.in')==changes.PREIMAGE,'Wrong delivered source parent')
 # Match the entire runtime to the saved successful 2103372 build, not reconstructed filenames alone.
 archive=next(args.current_reference.rglob('runtime-source.tar.gz'))
 with tarfile.open(archive) as t:
  entries={m.name.removeprefix('source/'):hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t.getmembers() if m.isfile()}
 require(entries==stage.snapshot(parent),'Saved 2103372 source does not match reconstructed parent')
 changes.apply(source,args.out)
 require(sha(source/stage.RUNTIME/'InfinityLiveActivity.java.in')==approval['source_sha256'],'Correction source differs from review')
 sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
 from packaging_checks import configured
 values={'APP_PACKAGE':'com.projectinfinity.kodi','APP_NAME':'Kodi','APP_NAME_LC':'kodi','APP_VERSION':RELEASE,'APP_VERSION_CODE_ANDROID':str(VERSION),'TARGET_MINSDK':'21','TARGET_SDK':'35'}
 name='InfinityLiveActivity.java.in';(args.build/'xbmc/java/com/projectinfinity/kodi'/name.removesuffix('.in')).write_text(configured(source/stage.RUNTIME/name,values))
 proof=json.loads((args.out/'SOURCE-PRESERVATION.json').read_text());proof['after']=stage.snapshot(source)
 require(proof['before'].keys()==proof['after'].keys(),'Unexpected runtime file removal')
 require(sorted(k for k in proof['before'] if proof['before'][k]!=proof['after'][k])==proof['changed'],'Unrelated runtime changed')
 write(args.out/'SOURCE-PRESERVATION.json',proof)
 delta=[n for n,h in stage.snapshot(parent).items() if stage.snapshot(source)[n]!=h]
 require(delta==[stage.RUNTIME+name],'Corrections exceed the single permitted runtime file')
 (args.out/'targeted.patch').write_text(''.join(difflib.unified_diff((parent/stage.RUNTIME/name).read_text().splitlines(True),(source/stage.RUNTIME/name).read_text().splitlines(True),'2103372/'+name,'2103373/'+name)))
 tests=args.build/'xbmc/src/test/java/com/projectinfinity/kodi'
 # Preserve exact tests and fixtures delivered in 2103372.
 archive=next(args.current_reference.rglob('test-source.tar.gz'))
 with tarfile.open(archive) as t:
  for m in t.getmembers():
   if not m.isfile():continue
   rel=Path(m.name).relative_to('test')
   target=args.build/'xbmc/src/test'/rel
   require(target.is_file() and target.read_bytes()==t.extractfile(m).read(),'Delivered test or fixture altered: '+str(rel))
 write(args.out/'TARGETED-TEST-PROVENANCE.json',{'preserved_2103372_test_tree':True,'new_tests':12,'new_test_sha256':sha(tests/(EXTRA+'.java')),'negative_control_pending':True,'physical_fold_acceptance':False})

def review(args):
 require(sha(args.base)==stage.TRANSPORT,'Retained native transport changed')
 approved=json.loads((HERE/'APPROVAL.json').read_text())
 require(approved['purpose']=='TEST_CANDIDATE_ONLY' and not approved['production_promotion'],'Production promotion prohibited')
 before=args.out/'parent-2103372';after=args.out/'source';a=stage.snapshot(before);b=stage.snapshot(after)
 require(a.keys()==b.keys() and [k for k in a if a[k]!=b[k]]==[stage.RUNTIME+'InfinityLiveActivity.java.in'],'Unrelated runtime change')
 require(a[stage.RUNTIME+'InfinityLiveActivity.java.in']==approved['parent_source_sha256'] and b[stage.RUNTIME+'InfinityLiveActivity.java.in']==approved['source_sha256'],'Unreviewed correction')
 tool=ROOT/'repairs/cobra-clean-restart/MemberInventory.java';maps=[]
 for label,root in [('parent',before),('candidate',after)]:
  dest=args.out/('TARGETED-MEMBERS-'+label+'.json')
  subprocess.run(['java',str(tool),str(root/stage.RUNTIME/'InfinityLiveActivity.java.in'),str(dest)],check=True)
  maps.append(json.loads(dest.read_text()))
 old,new=maps;delta={k:{'before':old.get(k),'after':new.get(k)} for k in sorted(old.keys()|new.keys()) if old.get(k)!=new.get(k)}
 require(delta==approved['members'],'Correction touched an unreviewed named member')
 result=json.loads((args.out/'RUNTIME-RESULTS.json').read_text());counts=result['totals']
 require(result['source_commit']==os.environ['GITHUB_SHA'] and counts['tests']>=205,'Missing current tests')
 require(all(counts[k]==0 for k in ('failures','errors','skipped')),'Required verification failure')
 preserved=json.loads((args.out/'SAVED-TEST-PRESERVATION.json').read_text())
 require(preserved['original_test_names_preserved']==185 and preserved['inherited_sources_unchanged'],'Inherited verification changed')
 proof=json.loads((args.out/'SOURCE-PRESERVATION.json').read_text());require(proof['after']==b,'Source changed after compile')
 report={'changes':delta,'all_changes_mapped':True,'corrective_runtime_files':1,'other_2103372_runtime_files_byte_identical':len(a)-1,'source_commit':os.environ['GITHUB_SHA'],'retired_methods_removed':approved['removed_dashboard_methods'],'physical_acceptance':False}
 write(args.out/'CHANGED-MEMBERS.json',report)
 return report,counts

def absent(apk,classpath,out):
 import tempfile,re
 forbidden=changes.RETIRED+['COBRA • SPORTS','cobra_sports_drawer_header','cobra_sports_soccer_section','cobra_sports_soccer_leagues','cobra_sports_soccer_rail','cobra-sports-game:','cobra-sports-league-game:']
 with tempfile.TemporaryDirectory(prefix='cobra-retired-apk-') as d:
  root=Path(d)
  with zipfile.ZipFile(apk) as z:
   for name in z.namelist():
    if re.fullmatch(r'classes\d*\.dex',name):
     dex=root/name;dex.write_bytes(z.read(name));subprocess.run(['java','-cp',classpath,'org.jf.baksmali.Main','disassemble',str(dex),'-o',str(root/'smali')],check=True)
   dedicated=[n for n in z.namelist() if any(token in n for token in ('cobra_sports_soccer','cobra_sports_drawer_header','cobra-sports-game'))]
  found=[]
  for p in (root/'smali').rglob('*.smali'):
   text=p.read_text()
   for token in forbidden:
    if re.search(r'(?<![A-Za-z0-9_])'+re.escape(token)+r'(?![A-Za-z0-9_])',text):found.append([p.name,token])
  require(not found and not dedicated,'Retired dashboard survived in final APK: '+repr(found+dedicated))
  write(out/'RETIRED-DASHBOARD-APK.json',{'apk_sha256':sha(apk),'forbidden_methods_and_dedicated_strings':forbidden,'surviving_matches':found,'dedicated_resource_entries':dedicated,'compiled_dex_scanned':True,'physical_acceptance':False})

def package(args):
 package_test.review=review
 package_test.package(args)
 old=args.out/'Cobra-2103372-Six-Verified-RC1.apk';final=args.out/NAME;old.rename(final)
 absent(final,(args.build/'preservation-classpath.txt').read_text().strip(),args.out)
 receipt=json.loads((args.out/'DELIVERY.json').read_text());receipt.update({'file':NAME,'parent_candidate':2103372,'new_regression_cases':12,'preserved_2103372_cases':193,'retired_dashboard_compiled_absence_verified':True,'locked':False,'production_promoted':False})
 write(args.out/'DELIVERY.json',receipt)
 print('PASS signed candidate, retained engine, 205 tests and compiled dashboard absence:',NAME)

def negative_source(args):
 sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
 from packaging_checks import configured
 values={'APP_PACKAGE':'com.projectinfinity.kodi','APP_NAME':'Kodi','APP_NAME_LC':'kodi','APP_VERSION':RELEASE,'APP_VERSION_CODE_ANDROID':str(VERSION),'TARGET_MINSDK':'21','TARGET_SDK':'35'}
 parent=args.out/'parent-2103372';target=args.build/'xbmc/java/com/projectinfinity/kodi/InfinityLiveActivity.java'
 target.write_text(configured(parent/stage.RUNTIME/'InfinityLiveActivity.java.in',values))

def negative_result(args):
 import xml.etree.ElementTree as ET
 required={'savedProCannotExposeFullscreenSportsTabInAnyOtherExperience',
  'retiredDashboardMethodsAndCallbacksAreAbsentFromCompiledActivity',
  'savedProCannotCreatePlayerTickerOrClockInOtherExperiences',
  'sportsMultiScoresCannotRenderOutsideProAndOrdinaryTilesStayAlive'}
 path=args.build/'xbmc/build/test-results/testReleaseUnitTest'/('TEST-com.projectinfinity.kodi.'+EXTRA+'.xml')
 root=ET.parse(path).getroot();cases=root.findall('testcase')
 failures={c.attrib['name'].removesuffix('()') for c in cases if c.find('failure') is not None}
 require(len(cases)==4 and failures==required,'New tests did not independently reproduce all four parent failures')
 for c in cases:
  failure=c.find('failure');require(failure is not None and 'AssertionError' in failure.attrib.get('type',''),'Negative control failed at a fixture boundary rather than reproducing the regression')
  message=failure.attrib.get('message','')
  if c.attrib['name'].startswith('retiredDashboard'):require(any(n in message for n in changes.RETIRED),'Dashboard absence assertion was not reached')
  else:require('expected null' in message.lower(),'Actual forbidden UI presence was not observed: '+message)
 shutil.copy2(path,args.out/'NEGATIVE-CONTROL.xml')
 write(args.out/'NEGATIVE-CONTROL.json',{'source':2103372,'four_identified_failures_reproduced':sorted(failures),'failure_count':4,'tests_modified':False})
 sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
 from packaging_checks import configured
 values={'APP_PACKAGE':'com.projectinfinity.kodi','APP_NAME':'Kodi','APP_NAME_LC':'kodi','APP_VERSION':RELEASE,'APP_VERSION_CODE_ANDROID':str(VERSION),'TARGET_MINSDK':'21','TARGET_SDK':'35'}
 (args.build/'xbmc/java/com/projectinfinity/kodi/InfinityLiveActivity.java').write_text(configured(args.out/'source'/stage.RUNTIME/'InfinityLiveActivity.java.in',values))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','gates','review','package','negative-source','negative-result'])
 p.add_argument('--kind',default='candidate')
 for n in ('evidence','base','build','out','reference','current-reference'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();{'prepare':prepare,'gates':delivery_gate.gates,'review':review,'package':package,'negative-source':negative_source,'negative-result':negative_result}[a.mode](a)
