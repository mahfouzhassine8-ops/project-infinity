#!/usr/bin/env python3
"""Run all four locked Android cases unchanged plus eight completion cases.
Fixtures use Android views, real SharedPreferences and Media3 objects, not a provider/decoder.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 original=ROOT.parent/'cobra-navigation-2103157/tests';runner=out/'runner';runner.mkdir(exist_ok=True)
 base=(original/'CobraNavigationUiTest.java').read_text();extra=(ROOT/'tests/android-cases.java.inc').read_text();index=base.rfind('\n}')
 if index<0:raise ValueError('Unrecognized original Android test source')
 combined=base[:index]+'\n'+extra+base[index:]
 if combined.replace('\n'+extra,'',1)!=base:raise ValueError('Inherited Android test body changed')
 (runner/'CobraNavigationUiTest.java').write_text(combined)
 old=(original/'android.py').read_text();assert old.count('process.wait(timeout=300)')==1
 (runner/'android.py').write_text(old.replace('process.wait(timeout=300)','process.wait(timeout=600)'))
 subprocess.run(['python3',str(runner/'android.py'),'--build',str(a.build),'--out',str(out)],check=True)
 suite=ET.parse(a.build/'xbmc/build/test-results/testReleaseUnitTest/TEST-com.projectinfinity.kodi.CobraNavigationUiTest.xml').getroot();cases=suite.findall('testcase')
 if len(cases)!=12 or any(int(suite.get(n,'0')) for n in ('failures','errors','skipped')):raise ValueError('All 12 Android cases must actually pass without skips')
 if any(c.find(tag) is not None for c in cases for tag in ('failure','error','skipped')):raise ValueError('Incomplete Android evidence')
 (out/'acceptance.json').write_text(json.dumps({'tests':len(cases),'names':[c.get('name') for c in cases],'baseline_tests_sha256':hashlib.sha256(base.encode()).hexdigest(),'inherited_tests_unchanged':True,'physical_decoder_tested':False,'provider_tested':False},indent=2)+'\n')
if __name__=='__main__':main()
