#!/usr/bin/env python3
"""Cobra-only source compilation over exact retained 2103369; never rebuild native/Infinity."""
import argparse,difflib,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tarfile,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'mobile-regressions-2103304'))
from packaging_checks import DEX,SIGNATURE,require,resource_ids,run,sha,verify_manifest_pair,dex_contract
import package_candidate as factory
from source_scope import verify
from dex_encoding import canonical
IDENTITY=json.loads((HERE/'baseline-identity.json').read_text())
BASE=IDENTITY['retained_transport_sha256'];CERT=IDENTITY['signer_sha256']
VERSION=2103370;RELEASE='1.0.9-Cobra-Six-Changes-RC1'
ALLOWED=re.compile(r'com/projectinfinity/kodi/(?:InfinityLiveActivity|CobraProUi\$Hero|CobraProUi|BuildConfig)(?:\$[^/]*)?\.smali$')
# Specific unchanged CobraProUi nested families are also compared, not blanket-exempted.
CHANGED_FAMILY=re.compile(r'com/projectinfinity/kodi/(?:InfinityLiveActivity(?:\$[^/]*)?|CobraProUi\$Hero(?:\$[^/]*)?|CobraProUi|BuildConfig)\.smali$')
TESTS=[
 'repairs/cobra-navigation-2103157/tests/CobraNavigationUiTest.java',
 'repairs/sports-hub-2103270/SportsHubTest.java',
 'repairs/cobra-pro-preview-2103321/ProTeams312Test.java',
 'repairs/cobra-pro-season-2103317/CobraProSeason317Test.java',
 'repairs/cobra-six-2103370/CobraProHandoffTest.java',
 'repairs/cobra-power-audit-2103199/tests/Cobra2103199TimeshiftRegressionTest.java',
 'repairs/whole-ui-ambient-2103276/WholeUiAmbientTest.java',
 'repairs/multiview-stability-fill-2103229/tests/Cobra2103229MultiViewStabilityFillTest.java',
 'repairs/cobra-pro-refinement-2103322/CobraProRefinementTest.java',
 'repairs/cobra-six-2103370/CobraProControlsRefinementTest.java',
 'repairs/cobra-pro-refinement-2103322/CobraProPausedReturnTest.java',
 'repairs/cobra-sports-live-2103323/CobraSportsLiveFeedTest.java',
 'repairs/cobra-six-2103370/CobraSixContractsTest.java',
]
EXPECTED={'Cobra2103199TimeshiftRegressionTest':7,'Cobra2103229MultiViewStabilityFillTest':10,
 'CobraProHandoffTest':50,'CobraProSeason317Test':13,'ProTeams312Test':17,'WholeUiAmbientTest':23,
 'CobraProRefinementTest':12,'CobraProControlsRefinementTest':11,'CobraProPausedReturnTest':8,
 'CobraSportsLiveFeedTest':16,'CobraSixContractsTest':41}

def snapshot(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}

def prepare(base,build,out,source):
 require(sha(base.read_bytes())==BASE,'Wrong retained 2103369 APK')
 expected=json.loads((HERE/'baseline-source-sha256.json').read_text())
 require(snapshot(source)==expected and len(expected)==264,'Source differs from exact 2103369 CI export')
 for name,value in IDENTITY['cobra_source_hashes'].items():require(expected[name]==value,'Approved 2103324 Cobra source drift: '+name)
 require(os.environ.get('INFINITY_BASE_SOURCE_COMMIT')==IDENTITY['retained_transport_source_commit'],'Wrong baseline source association')
 target=out/'android-source';shutil.copytree(source,target)
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str((HERE/'changes.patch').resolve())],cwd=target,check=True)
 actual=snapshot(target)
 for name,value in json.loads((HERE/'runtime-source-sha256.json').read_text()).items():require(actual[name]==value,'Reviewed source delta mismatch: '+name)
 report=verify(source,target,out/'SOURCE-PRESERVATION.json')
 shutil.copy2(HERE/'baseline-identity.json',out/'BASELINE-IDENTITY.json')
 (out/'changes.patch').write_text(''.join(''.join(difflib.unified_diff((source/n).read_text().splitlines(True),(target/n).read_text().splitlines(True),fromfile='retained-2103369/'+n,tofile='candidate-2103370/'+n)) for n in report['changed']))
 factory.BASE_APK_SHA256=BASE;factory.VERSION_CODE=VERSION;factory.RELEASE=RELEASE
 factory.prepare(target.resolve(),base.resolve(),build.resolve(),out.resolve())
 tests=build/'xbmc/src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
 for name in TESTS:shutil.copy2(ROOT/name,tests/Path(name).name)
 # Preserve the inherited obsolete destination test exclusion exactly; no newly skipped tests.
 previous=tests/'ProTeams312Test.java';previous.write_text(previous.read_text().replace('@Test public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()',
 '/* Established 2103324 exclusion: obsolete drawer destination; Pro Sports tab has replacement checks. */ public void proDrawerSportsOpensSameHubAndSelectionSurvivesRerender()'))
 resources=build/'xbmc/src/test/resources';resources.mkdir(parents=True)
 shutil.copy2(HERE.parent/'cobra-pro-season-2103317/schedule-fixtures.json',resources/'schedule-fixtures.json')
 with (build/'xbmc/build.gradle').open('a') as f:f.write('''
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "3g"; systemProperty "cobra.evidence", rootProject.file("../evidence3370/screenshots").absolutePath; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
''')
 print('PASS exact source, 24 approved Cobra owners, 262 protected sources, six scoped changes; no native build')


def merge(base,donor,output):
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(donor) as new,zipfile.ZipFile(output,'w') as dest:
  for archive in (old,new):require(archive.testzip() is None and len(set(archive.namelist()))==len(archive.namelist()),'Corrupt/duplicate APK input')
  require(not any(n.startswith(('assets/','lib/')) for n in new.namelist()),'Donor unexpectedly contains native or assets')
  for entry in old.infolist():
   if SIGNATURE.fullmatch(entry.filename) or DEX.fullmatch(entry.filename) or entry.filename=='AndroidManifest.xml':continue
   dest.writestr(entry,old.read(entry.filename))
  for name in new.namelist():
   if DEX.fullmatch(name) or name=='AndroidManifest.xml':dest.writestr(new.getinfo(name),new.read(name))


def compare_dex(base,final,build,out):
 classpath=(build/'preservation-classpath.txt').read_text().strip();maps=[]
 for label,apk in [('base',base),('final',final)]:
  root=out/('dex-'+label);root.mkdir();target=out/('smali-'+label)
  with zipfile.ZipFile(apk) as z:
   for name in z.namelist():
    if DEX.fullmatch(name):
     dex=root/name;dex.write_bytes(z.read(name));subprocess.run(['java','-cp',classpath,'org.jf.baksmali.Main','disassemble',str(dex),'-o',str(target)],check=True)
  # Source line numbers are compiler metadata; every opcode/register remains compared.
  maps.append({p.relative_to(target).as_posix():re.sub(r'^\s*\.line \d+\n','',p.read_text(),flags=re.M) for p in target.rglob('*.smali')})
 spec=importlib.util.spec_from_file_location('bridge',HERE.parent/'chooser-close-owner-2103324/bridge_preservation.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
 bridge.OWNER=r'com/projectinfinity/kodi/(?:[^/]+\$\$ExternalSyntheticApiModelOutline\d+|InfinityExitDiagnostics\$\$ExternalSyntheticBackport2)'
 bridge.HELPER=re.compile(bridge.OWNER+r'\.smali$');bridge.CALL=re.compile(r'L'+bridge.OWNER+r';->m(?:\$\d+)?\([^\s]+')
 left,old_bodies,old_helpers=bridge.resolve(maps[0]);right,new_bodies,new_helpers=bridge.resolve(maps[1])
 encoding_changed=sorted(n for n in left.keys()|right.keys() if left.get(n)!=right.get(n) and not CHANGED_FAMILY.fullmatch(n))
 left={n:canonical(text) for n,text in left.items()};right={n:canonical(text) for n,text in right.items()}
 encoding_only=[n for n in encoding_changed if left.get(n)==right.get(n)]
 changed=sorted(n for n in left.keys()|right.keys() if left.get(n)!=right.get(n))
 unexpected=[n for n in changed if not CHANGED_FAMILY.fullmatch(n)]
 diagnostic=out/'compiler-diffs';diagnostic.mkdir(exist_ok=True)
 for name in unexpected:(diagnostic/(Path(name).name+'.diff')).write_text(''.join(difflib.unified_diff(left.get(name,'').splitlines(True),right.get(name,'').splitlines(True),fromfile='base/'+name,tofile='candidate/'+name)))
 require(not unexpected,'Protected compiled instructions changed: '+repr(unexpected))
 # JNI signatures must remain exactly unchanged, including untouched native activity owners.
 with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:require(dex_contract(a)[0]==dex_contract(b)[0],'JNI declaration changed')
 report={'changed_dex_classes':changed,'protected_compiled_classes_identical':len(set(left)|set(right))-len(changed),
 'protected_class_differences':unexpected,'encoding_only_protected_classes':encoding_only,'jni_declarations_identical':True,
 'helper_bodies_before':len(old_bodies),'helper_bodies_after':len(new_bodies),
 'helper_containers_before':sorted(old_helpers),'helper_containers_after':sorted(new_helpers),
 'method':'Exact opcodes/registers/signatures after recursively resolving stateless API helper relocation; source line metadata excluded. Source token gate independently preserves every unapproved method.'}
 (out/'DEX-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
 for label in ['dex-base','dex-final','smali-base','smali-final']:shutil.rmtree(out/label)
 return report


def package(base,build,out,source):
 require(sha(base.read_bytes())==BASE,'Wrong retained 2103369 APK at packaging')
 proof=json.loads((out/'SOURCE-PRESERVATION.json').read_text());require(snapshot(out/'android-source')==proof['after'],'Tested source drift')
 bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0';donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
 require(resource_ids(bt/'aapt2',base,out/'base-resources.txt')==resource_ids(bt/'aapt2',donor,out/'donor-resources.txt'),'Resource ID drift')
 unsigned=out/'candidate-unsigned.apk';merge(base,donor,unsigned)
 verify_manifest_pair(run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt'),run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'candidate-manifest.txt'))
 final=out/f'Infinity-{VERSION}-Cobra-Six-Changes-RC1.apk';run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
 signing=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt');require(CERT in signing.lower(),'Permanent signer drift')
 badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt');require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Candidate identity mismatch')
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(final) as new:
  require(new.testzip() is None and len(set(new.namelist()))==len(new.namelist()),'Candidate ZIP corrupt/duplicate')
  protected={n for n in old.namelist() if not SIGNATURE.fullmatch(n) and not DEX.fullmatch(n) and n!='AndroidManifest.xml'}
  require(protected=={n for n in new.namelist() if not SIGNATURE.fullmatch(n) and not DEX.fullmatch(n) and n!='AndroidManifest.xml'},'Protected payload inventory drift')
  for n in protected:require(old.read(n)==new.read(n),'Protected payload changed: '+n)
  require(sha(new.read('lib/arm64-v8a/libkodi.so'))==IDENTITY['retained_native_sha256'],'Native engine drift')
  hashes={n:sha(new.read(n)) for n in sorted(protected)}
 (out/'PROTECTED-PAYLOAD.json').write_text(json.dumps(hashes,indent=2)+'\n')
 dex=compare_dex(base,final,build,out)
 suites=[]
 for file in sorted((build/'xbmc/build/test-results/testReleaseUnitTest').glob('TEST-*.xml')):
  suite=ET.parse(file).getroot();suites.append({'suite':suite.attrib['name'],**{k:int(suite.attrib.get(k,0)) for k in ('tests','failures','errors','skipped')}})
 require({s['suite'].rsplit('.',1)[-1] for s in suites}==set(EXPECTED),'Missing/additional unreviewed test suite')
 require(all(s['tests']>=EXPECTED[s['suite'].rsplit('.',1)[-1]] and s['failures']==s['errors']==s['skipped']==0 for s in suites),'Reduced/failed/skipped tests')
 report={'candidate_version':VERSION,'version_name':RELEASE,'source_commit':os.environ['GITHUB_SHA'],'validation_run':os.environ['GITHUB_RUN_ID'],
 'baseline':IDENTITY,'apk_sha256':sha(final.read_bytes()),'apk_size':final.stat().st_size,'signer_certificate_sha256':CERT,
 'native_sha256':IDENTITY['retained_native_sha256'],'native_recompiled':False,'skin_changed':False,'Kodi_or_Dual_Infinity_modified':False,
 'protected_payload_entries_byte_identical':len(protected),'all_assets_and_resources_byte_identical':True,'manifest_unchanged_except_candidate_version':True,
 'source_changed_files':proof['changed'],'tests':suites,'tests_passed':sum(s['tests'] for s in suites),
 'locked':False,'physical_fold_verified':False,'production_promoted':False,'rollback_reference':'Retained exact 2103369 APK; approved Cobra 2103324 source identity separately recorded',**dex}
 (out/'APK-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');(out/'SHA256SUMS').write_text(report['apk_sha256']+'  '+final.name+'\n')
 with tarfile.open(out/'repaired-shell-source.tar.gz','w:gz') as tar:tar.add(out/'android-source',arcname='shell-kodi')
 unsigned.unlink();print('PASS signed Cobra-only candidate; native/Infinity/assets/settings install contracts preserved; physical Fold acceptance pending')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','package'])
 for n in ('base','build','out','source'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);(prepare if a.mode=='prepare' else package)(a.base,a.build,a.out,a.source)
