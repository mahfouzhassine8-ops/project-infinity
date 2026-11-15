#!/usr/bin/env python3
"""Execute actual ARM64 engines in isolated Android case processes, no owner data."""
from pathlib import Path
import argparse
import json
import subprocess
import time


def adb(*args, check=True, timeout=40):
    return subprocess.run(['adb',*args],text=True,capture_output=True,check=check,timeout=timeout)


def run(work,out):
    out.mkdir(parents=True,exist_ok=True)
    build=json.loads((work/'BUILD.json').read_text())
    environment={key:adb('shell','getprop',key).stdout.strip() for key in (
        'ro.build.version.sdk','ro.product.cpu.abilist','ro.dalvik.vm.native.bridge')}
    assert 'arm64-v8a' in environment['ro.product.cpu.abilist'], 'Android image cannot execute ARM64'
    environment['execution']='ARM64 engine through Android native-bridge translation on x86_64 emulator'
    assert environment['ro.dalvik.vm.native.bridge'] not in ('','0'), 'Expected translated ARM64 environment unavailable'
    rows=[]
    try:
        for variant in (build['variant'],):
            package='com.projectinfinity.observerqa.'+variant
            assert adb('shell','pm','path',package,check=False).stdout.strip()=='','Fresh fixture identity required'
            # This fixture contains the unchanged 611MiB native engine. Its
            # package transfer/extraction is not a Python admission deadline.
            installation_started=time.monotonic()
            installed=adb('install',str(work/(variant+'-CI-ONLY.apk')),timeout=180)
            (out/(variant+'-install.txt')).write_text(installed.stdout+installed.stderr)
            (out/(variant+'-install-time.json')).write_text(json.dumps({'seconds':time.monotonic()-installation_started,'bounded_limit_seconds':180})+'\n')
            assert 'Success' in installed.stdout
            # Baseline closed text is the causal control; other cases were
            # already host verified. Candidate checks cover native integration.
            selected=('closed_text',) if variant=='baseline' else tuple(build['cases'])
            for case in selected:
                component=package+'/com.projectinfinity.observerqa.ProbeActivity$'+build['cases'][case]
                launch=adb('shell','am','start','-W','-n',component,'--es','case',case)
                (out/(variant+'-'+case+'-launch.txt')).write_text(launch.stdout+launch.stderr)
                remote='/sdcard/Android/data/'+package+'/files/'+case+'.json'
                deadline=time.monotonic()+120;row=None
                while time.monotonic()<deadline:
                    content=adb('shell','cat',remote,check=False)
                    if content.returncode==0 and content.stdout.strip():
                        row=json.loads(content.stdout);break
                    time.sleep(2)
                if row is None:row={'status':'FAIL','stage':'fixture_result_timeout','case':case}
                row.update(variant=variant,engine_sha256=build['packages'][variant]['engine_sha256'])
                rows.append(row)
                (out/(variant+'-'+case+'.json')).write_text(json.dumps(row,indent=2)+'\n')
                print(variant,case,row['status'],flush=True)
                if row['status']!='PASS':raise AssertionError((variant,case,row))
    finally:
        log=adb('logcat','-d','-v','threadtime',check=False)
        (out/'component.logcat.txt').write_text(log.stdout)
        required=1 if build['variant']=='baseline' else len(build['cases'])
        result={'status':'PASS_ACTUAL_EMBEDDED_ARM64_BRIDGE' if len(rows)==required and all(r['status']=='PASS' for r in rows) else 'FAIL_OR_INCOMPLETE',
                'variant':build['variant'],'correction_tested':build['variant']=='candidate',
                'environment':environment,'cases':rows,'native_source':build['native_source'],
                'full_application_startup_shutdown':'NOT_TESTED','physical_Fold':False,'user_profile_accessed':False,
                'fixture_disposal':'Activities finish normally; each test has its own process. No Infinity installation or process is controlled.'}
        (out/'ANDROID-BRIDGE.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    assert result['status']=='PASS_ACTUAL_EMBEDDED_ARM64_BRIDGE'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('work',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.work.resolve(),a.out.resolve())
