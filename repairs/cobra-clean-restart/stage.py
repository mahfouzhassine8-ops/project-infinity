#!/usr/bin/env python3
"""Compile exact archived Cobra sources; never rebuild native or package a release here."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TRANSPORT = '83128afbd2595dbf4053ded40ee1d22ae0d1c7b798f62dd9f077bd4d729261f4'
ARCHIVE = 'b3d70a863adbe350141729989bfe78279514f0870e55107d15bf15dc1e766597'
RUNTIME = 'tools/android/packaging/xbmc/src/'
COBRA = {'InfinityLiveActivity.java.in':'02111d4971307e5e0e0e9f22c319305e2924bc1942fa03f68b7b3a3a50f2f9ba', 'CobraProUi.java.in':'68b5eee8a3783594cbb8da86474279b34e9181b65530e30e6bede1bf809b4ec3'}
INHERITED = {
 'Cobra2103199TimeshiftRegressionTest': ('cobra-power-audit-2103199/tests',7),
 'Cobra2103229MultiViewStabilityFillTest': ('multiview-stability-fill-2103229/tests',10),
 'CobraProHandoffTest': ('cobra-pro-refinement-2103322',50),
 'CobraProSeason317Test': ('cobra-pro-season-2103317',13),
 'ProTeams312Test': ('cobra-pro-preview-2103321',17),
 'WholeUiAmbientTest': ('whole-ui-ambient-2103276',23),
 'CobraProRefinementTest': ('cobra-pro-refinement-2103322',12),
 'CobraProControlsRefinementTest': ('cobra-pro-refinement-2103322',11),
 'CobraProPausedReturnTest': ('cobra-pro-refinement-2103322',8),
 'CobraSportsLiveFeedTest': ('cobra-sports-live-2103323',16),
}

def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot(path):
 return {p.relative_to(path).as_posix():sha(p) for p in path.rglob('*') if p.is_file()}

def require(value, message):
 if not value: raise RuntimeError(message)

def write(path, value):
 path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def stage(args):
 archive = next(args.evidence.rglob('runtime-shell-source.tar.gz'))
 require(sha(archive)==ARCHIVE, 'Transport source archive mismatch')
 require(sha(args.base)==TRANSPORT, 'Transport signed APK mismatch')
 args.out.mkdir(parents=True,exist_ok=True)
 with tarfile.open(archive) as tar:
  # Python 3.10 runners may not expose extractall(filter=); reject every unsafe member explicitly.
  for m in tar.getmembers():
   p=Path(m.name)
   require(not p.is_absolute() and '..' not in p.parts and (m.isfile() or m.isdir()), 'Unsafe source archive member')
  tar.extractall(args.out/'extracted')
 original=args.out/'extracted/shell-kodi'
 before=snapshot(original)
 require(len(before)==264, 'Unexpected complete runtime source count')
 for name,h in COBRA.items(): require(before[RUNTIME+name]==h,'Approved Cobra identity mismatch: '+name)
 source=args.out/'source';shutil.copytree(original,source)
 if args.kind=='candidate':
  spec=importlib.util.spec_from_file_location('clean_changes',HERE/'apply.py')
  changes=importlib.util.module_from_spec(spec);spec.loader.exec_module(changes)
  changes.apply(source,args.out)
 after=snapshot(source)
 changed=sorted(n for n in before.keys()|after.keys() if before.get(n)!=after.get(n))
 require(before.keys()==after.keys(),'Source membership changed')
 require(changed==([] if args.kind=='baseline' else sorted(RUNTIME+n for n in COBRA)), 'Runtime source scope exceeded')
 write(args.out/'SOURCE-PRESERVATION.json',{'kind':args.kind,'before':before,'after':after,'changed':changed,'transport_sha256':TRANSPORT,'source_archive_sha256':ARCHIVE,'source_commit':os.environ.get('GITHUB_SHA','')})
 sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
 spec=importlib.util.spec_from_file_location('factory',ROOT/'repairs/mobile-regressions-2103304/package_candidate.py')
 factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
 factory.BASE_APK_SHA256=TRANSPORT
 # Compile-only identity. No candidate version or permanent-signing claim is made.
 factory.VERSION_CODE=2103369;factory.RELEASE='1.0.9-Cancelled-Script-Receipt-RC1'
 factory.prepare(source.resolve(),args.base.resolve(),args.build.resolve(),args.out.resolve())
 tests=args.build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True,exist_ok=True)
 for path in ('cobra-navigation-2103157/tests/CobraNavigationUiTest.java','sports-hub-2103270/SportsHubTest.java'):
  shutil.copy2(ROOT/'repairs'/path,tests/Path(path).name)
 provenance=[]
 for name,(folder,count) in INHERITED.items():
  original_test=ROOT/'repairs'/folder/(name+'.java');target=tests/(name+'.java')
  shutil.copy2(original_test,target)
  if name=='ProTeams312Test':
   old='@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'
   require(target.read_text().count(old)==1,'Established baseline exclusion no longer matches')
   target.write_text(target.read_text().replace(old,'/* Pre-existing locked 2103324 exclusion: Sports already uses the Pro tab. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
  provenance.append({'suite':name,'original_sha256':sha(original_test),'staged_sha256':sha(target),'minimum_cases':count})
 extra=['CobraCleanBaselineViewsTest'] if args.kind=='baseline' else json.loads((HERE/'test-spec.json').read_text())
 for name in extra: shutil.copy2(HERE/(name+'.java'),tests/(name+'.java'))
 resources=args.build/'xbmc/src/test/resources';resources.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/'repairs/cobra-pro-season-2103317/schedule-fixtures.json',resources)
 if (HERE/'fixtures').exists():shutil.copytree(HERE/'fixtures',resources,dirs_exist_ok=True)
 write(args.out/'TEST-SCOPE.json',{'inherited':provenance,'new_suites':extra,'no_new_skips':True,'device_acceptance':False})
 with (args.build/'xbmc/build.gradle').open('a') as f:
  f.write('''\nandroid { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../'''+args.out.name+'''/screenshots").absolutePath; systemProperty "cobra.clean.evidence", rootProject.file("../'''+args.out.name+'''/runtime").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')
 # Helper suites provide fixtures but are not additional inherited acceptance suites.
 with (args.build/'xbmc/build.gradle').open('a') as f:
  f.write('\ntasks.withType(Test).configureEach { filter {\n')
  for name in list(INHERITED)+list(extra):f.write(" includeTestsMatching 'com.projectinfinity.kodi."+name+"'\n")
  f.write('} }\n')

def gates(args):
 expected={n:c for n,(_,c) in INHERITED.items()}
 if args.kind=='baseline':expected['CobraCleanBaselineViewsTest']=1
 else:expected.update(json.loads((HERE/'test-spec.json').read_text()))
 found={};totals={'tests':0,'failures':0,'errors':0,'skipped':0}
 for p in (args.build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml'):
  root=ET.parse(p).getroot();name=root.attrib['name'].rsplit('.',1)[-1]
  counts={k:int(root.attrib.get(k,0)) for k in totals}
  require(name not in found,'Duplicate test report');found[name]=counts
  for k,v in counts.items():totals[k]+=v
 require(set(found)==set(expected),'Test suite membership mismatch: '+repr(set(found)^set(expected)))
 write(args.out/'RUNTIME-RESULTS.json',{'kind':args.kind,'suites':found,'totals':totals,'source_commit':os.environ.get('GITHUB_SHA',''),'physical_device_verified':False})
 for n,c in expected.items():require(found[n]['tests']>=c,'Missing tests: '+n)
 require(all(totals[k]==0 for k in ('failures','errors','skipped')),'Runtime gate failed; packaging prohibited')
 print(json.dumps(totals))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['stage','gates']);p.add_argument('--kind',choices=['baseline','candidate'],required=True)
 for name in ('evidence','base','build','out'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();(stage if a.mode=='stage' else gates)(a)
