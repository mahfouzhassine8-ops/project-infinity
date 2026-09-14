#!/usr/bin/env python3
"""Validate actual packaged identity/version/debug flag with Android's resource tool.
This is not a signature or device-install test. Reports never certify device behavior.
"""
import argparse,json,os,re,subprocess
from pathlib import Path

def check(apk: Path, report: Path) -> None:
    tool=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0/aapt2'
    result=subprocess.run([str(tool),'dump','badging',str(apk)],check=True,text=True,capture_output=True)
    text=result.stdout
    if not re.search(r"^package: name='com\.projectinfinity\.kodi' versionCode='2103100' versionName='21\.3-Infinity-Android-First'",text,re.M):
        raise ValueError('Wrong Android package/version; refusing stale or mismatched base')
    if re.search(r'^application-debuggable(?:\s|$)',text,re.M):
        raise ValueError('Refusing a debuggable application package')
    if "application-label:'Infinity'" not in text and not re.search(r"^application: label='Infinity'",text,re.M):
        raise ValueError('Infinity application label missing')
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps({'package':'com.projectinfinity.kodi','version_code':2103100,
        'version_name':'21.3-Infinity-Android-First','debuggable':False,'label':'Infinity',
        'device_accepted':False,'signature_checked_by_this_tool':False},indent=2)+'\n')
    print('PASS: actual Android package, Infinity label, version and non-debuggable flag')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apk',required=True,type=Path);p.add_argument('--report',required=True,type=Path)
    a=p.parse_args();check(a.apk,a.report)
