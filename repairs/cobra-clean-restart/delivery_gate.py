#!/usr/bin/env python3
"""Supplement the saved 185-case gate; no package is produced by this module."""
import argparse
import difflib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import stage

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
EXTRA={'CobraDeliveryVerificationTest':8}
VERSION=2103372
RELEASE='1.0.9-Cobra-Six-Verified-RC1'
SAVED={'CobraProUi.java.in':'a096e19cb594752274ded0ea18a40a48f9e5ee55ad5e7f6caf474236d56372cb','InfinityLiveActivity.java.in':'77482b135aff60a4c0c6953bb92b1949c32e447528434df659aa869892ab4c1c'}

def prepare(args):
 stage.stage(args)
 source=args.out/'source'
 for n,h in SAVED.items():stage.require(stage.sha(source/stage.RUNTIME/n)==h,'Not saved passing source: '+n)
 fix=HERE/'delivery_fixes.py'
 if fix.exists():
  spec=importlib.util.spec_from_file_location('delivery_fixes',fix);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.apply(source,args.out)
 # Reconfigure only the two reviewed runtime files after optional, preimage-guarded follow-up fixes.
 sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
 from packaging_checks import configured
 values={'APP_PACKAGE':'com.projectinfinity.kodi','APP_NAME':'Kodi','APP_NAME_LC':'kodi','APP_VERSION':RELEASE,'APP_VERSION_CODE_ANDROID':str(VERSION),'TARGET_MINSDK':'21','TARGET_SDK':'35'}
 for n in SAVED:
  (args.build/'xbmc/java/com/projectinfinity/kodi'/n.removesuffix('.in')).write_text(configured(source/stage.RUNTIME/n,values))
 for p in (args.build/'xbmc/build.gradle',args.build/'xbmc/AndroidManifest.xml'):
  text=p.read_text()
  stage.require('2103369' in text and '1.0.9-Cancelled-Script-Receipt-RC1' in text,'Unexpected compile identity')
  p.write_text(text.replace('2103369',str(VERSION)).replace('1.0.9-Cancelled-Script-Receipt-RC1',RELEASE))
 tests=args.build/'xbmc/src/test/java/com/projectinfinity/kodi'
 for n in EXTRA:shutil.copy2(HERE/(n+'.java'),tests/(n+'.java'))
 with (args.build/'xbmc/build.gradle').open('a') as out:
  for n in EXTRA:out.write("\ntasks.withType(Test).configureEach { filter { includeTestsMatching 'com.projectinfinity.kodi."+n+"' } }\n")
 proof=json.loads((args.out/'SOURCE-PRESERVATION.json').read_text());proof['after']=stage.snapshot(source)
 stage.require(set(proof['before'])==set(proof['after']),'Runtime membership changed')
 changed=sorted(n for n in proof['before'] if proof['before'][n]!=proof['after'][n]);stage.require(changed==proof['changed'],'Unauthorized runtime file change')
 stage.write(args.out/'SOURCE-PRESERVATION.json',proof)
 original=args.out/'extracted/shell-kodi'
 (args.out/'changes.patch').write_text(''.join(''.join(difflib.unified_diff((original/n).read_text().splitlines(True),(source/n).read_text().splitlines(True),'a/'+n,'b/'+n)) for n in changed))
 scope=json.loads((args.out/'TEST-SCOPE.json').read_text());scope['supplemental_suites']=EXTRA;scope['supplemental_source_hashes']={n:stage.sha(tests/(n+'.java')) for n in EXTRA};stage.write(args.out/'TEST-SCOPE.json',scope)

def results(directory):
 found={};names=set()
 for p in directory.glob('TEST-*.xml'):
  root=ET.parse(p).getroot();name=root.attrib['name'].rsplit('.',1)[-1]
  stage.require(name not in found,'Duplicate JUnit suite')
  found[name]={k:int(root.attrib.get(k,0)) for k in ('tests','failures','errors','skipped')}
  for case in root.findall('testcase'):
   key=(case.attrib['classname'],case.attrib['name']);stage.require(key not in names,'Duplicate JUnit case');names.add(key)
 return found,names

def gates(args):
 expected={n:c for n,(_,c) in stage.INHERITED.items()};expected.update(json.loads((HERE/'test-spec.json').read_text()));expected.update(EXTRA)
 found,names=results(args.build/'xbmc/build/test-results/testReleaseUnitTest')
 totals={k:sum(v[k] for v in found.values()) for k in ('tests','failures','errors','skipped')}
 stage.write(args.out/'RUNTIME-RESULTS.json',{'source_commit':os.environ.get('GITHUB_SHA',''),'suites':found,'totals':totals,'original_cases_required':185,'supplemental_cases_required':sum(EXTRA.values()),'physical_device_verified':False})
 stage.require(set(found)==set(expected),'Suite membership mismatch: '+repr(set(found)^set(expected)))
 for n,c in expected.items():stage.require(found[n]['tests']>=c,'Missing required cases: '+n)
 previous=list(args.reference.rglob('TEST-com.projectinfinity.kodi.CobraCleanRuntimeTest.xml'))
 stage.require(len(previous)==1,'Saved XML reference missing or ambiguous')
 old,oldnames=results(previous[0].parent)
 stage.require(len(oldnames)==185 and oldnames <= names,'A saved required test was removed or renamed')
 oldprovenance=json.loads(next(args.reference.rglob('TEST-SCOPE.json')).read_text())['inherited']
 now=json.loads((args.out/'TEST-SCOPE.json').read_text())['inherited'];stage.require(oldprovenance==now,'Inherited test sources changed')
 source=json.loads((args.out/'SOURCE-PRESERVATION.json').read_text());stage.require(stage.snapshot(args.out/'source')==source['after'],'Source changed after compilation')
 stage.write(args.out/'SAVED-TEST-PRESERVATION.json',{'original_test_names_preserved':185,'inherited_sources_unchanged':True,'supplemental_tests':len(names)-185,'no_failed_cases_waived':True})
 stage.require(all(totals[k]==0 for k in ('failures','errors','skipped')),'Required verification failure; package prohibited')
 print(json.dumps(totals))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','gates']);p.add_argument('--kind',default='candidate',choices=['candidate'])
 for n in ('evidence','base','build','out','reference'):p.add_argument('--'+n,type=Path,required=True)
 args=p.parse_args();(prepare if args.mode=='prepare' else gates)(args)
