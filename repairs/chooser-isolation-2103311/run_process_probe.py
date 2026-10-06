#!/usr/bin/env python3
"""Run the actual Android JUnit probe directly, retaining its instrumentation output."""
from pathlib import Path
import argparse, re, subprocess, time

def validate(text):
    assert re.search(r'OK\s*\(1 test\)',text),'Android JUnit did not report its one test passing'
    assert re.search(r'^INSTRUMENTATION_CODE: -1\s*$',text,re.M),'Instrumentation did not finish normally'
    assert len(re.findall(r'^INSTRUMENTATION_STATUS_CODE: 0\s*$',text,re.M))==1,'Missing completed test status'
    assert not re.search(r'^INSTRUMENTATION_STATUS_CODE: -[123]\s*$',text,re.M),'Android test reported a failure'
    assert 'chooserSurvivesRealSeparateProcessExitAndSeesConfirmedCompletion' in text,'Wrong Android test'

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    def adb(*args):
        return subprocess.run(['adb',*args],text=True,capture_output=True,timeout=90,check=True).stdout
    adb('wait-for-device');adb('shell','input','keyevent','82')
    for name in ['debug/processprobe-debug.apk','androidTest/debug/processprobe-debug-androidTest.apk']:
        result=adb('install','-t','-r',str(a.build/'processprobe/build/outputs/apk'/name));assert 'Success' in result,result
    adb('logcat','-c')
    try:
        run=subprocess.run(['adb','shell','am','instrument','-w','-r','-e','class',
            'com.projectinfinity.kodi.ProcessExitInstrumentedTest',
            'com.projectinfinity.kodi.processprobe.test/androidx.test.runner.AndroidJUnitRunner'],
            text=True,capture_output=True,timeout=60)
        result=run.stdout+'\n'+run.stderr
        (a.out/'process-exit-instrumentation.txt').write_text(result)
        print(result);assert run.returncode==0,'adb instrumentation command failed';validate(result)
    finally:
        try:(a.out/'process-exit-logcat.txt').write_text(adb('logcat','-d','-v','threadtime','-t','1200'))
        except Exception as e:print('Logcat collection unavailable:',type(e).__name__)
    print('PASS: real separate Android process exited; the chooser stayed alive and observed the completion receipt.')

if __name__=='__main__':main()
