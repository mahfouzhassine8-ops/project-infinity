#!/usr/bin/env python3
"""19 inherited Android cases unchanged, then actual package/bitmap/style safety tests."""
from pathlib import Path
import argparse,importlib.util,os,shutil,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 # Execute exact existing regression harness and retain its existing physical-test boundaries.
 subprocess.run(['python3','experience-delta/repairs/infinity-experience-2103159/tests/android.py','--build',str(build),'--out','audit159/android'],check=True)
 path=Path('experience-delta/repairs/infinity-experience-2103159/tests/android.py');spec=importlib.util.spec_from_file_location('runner159',path);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
 test=build/'xbmc/src/test/java/com/projectinfinity/kodi';shutil.copy2(ROOT/'tests/CobraVisualRuntimeTest.java',test);shutil.copy2(ROOT/'tests/CobraVisualLayoutTest.java',test)
 runtime=out/'runtime';env=runner.test_environment(runtime,Path('experience-delta/repairs/infinity-experience-2103159/experience-theme.json'))
 runner.run_ui_gate(['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest','--tests','com.projectinfinity.kodi.CobraVisualRuntimeTest','--tests','com.projectinfinity.kodi.CobraVisualLayoutTest','--stacktrace'],build,env,runtime)
 suite=ET.parse(runtime/'test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml').getroot()
 if len(suite.findall('testcase'))!=17 or any(int(suite.get(k,'0')) for k in ('failures','errors','skipped')):raise RuntimeError('All 17 actual Android tests must execute and pass')
 data=ET.parse(runtime/'test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml').getroot()
 if len(data.findall('testcase'))!=10 or any(int(data.get(k,'0')) for k in ('failures','errors','skipped')):raise RuntimeError('All 10 layout/scene Android cases must execute and pass')
 print('PASS: 19 inherited + 27 runtime/scene Android tests; provider/physical GPU tests NOT performed')
if __name__=='__main__':main()
