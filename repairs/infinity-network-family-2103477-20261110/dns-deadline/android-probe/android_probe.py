"""Isolated diagnostic packages only; never builds/signs/installs Infinity."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
DNS = HERE.parent
OUT = Path('dns-android-feasibility')
PACKAGES = {'x86_64': 'com.projectinfinity.dnsprobe.x86',
            'arm64-v8a': 'com.projectinfinity.dnsprobe.arm64'}


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def save(name, data):
    OUT.mkdir(exist_ok=True)
    (OUT/name).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')


def build():
    assert os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity'
    assert os.environ.get('GITHUB_REF') == 'refs/heads/work/infinity-network-family-from-2103477-20261109'
    assert os.environ.get('GITHUB_ACTIONS') == 'true'
    OUT.mkdir(exist_ok=True)
    sdk = Path(os.environ['ANDROID_HOME'])
    tools = sdk/'build-tools/35.0.0'
    ndk = sdk/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin'
    android = sdk/'platforms/android-35/android.jar'
    key = OUT/'DISPOSABLE-DIAGNOSTIC-ONLY.jks'
    run(['keytool','-genkeypair','-keystore',key,'-alias','diagnostic','-storepass','android',
         '-keypass','android','-keyalg','RSA','-keysize','2048','-validity','2',
         '-dname','CN=Disposable DNS Feasibility Test'], stdout=subprocess.DEVNULL,
         stderr=subprocess.DEVNULL)
    try:
        for abi, package in PACKAGES.items():
            assert package != 'com.projectinfinity.kodi'
            stage = OUT/abi; stage.mkdir()
            library = stage/'lib'/abi; library.mkdir(parents=True)
            prefix = 'aarch64' if abi == 'arm64-v8a' else 'x86_64'
            cc = ndk/(prefix+'-linux-android21-clang')
            cxx = ndk/(prefix+'-linux-android21-clang++')
            flags = ['-O2','-fPIE','-pie','-Wl,-z,max-page-size=16384',
                     '-Wl,--no-as-needed','-landroid','-ldl']
            for source, dest in [('helper.c','libinfinity_dns_helper.so'),
                                 ('stalled_helper.c','libinfinity_dns_stalled_fixture.so')]:
                run([cc, DNS/'prototype'/source, *flags, '-o', library/dest])
            run([cxx,'-std=c++17','-O2','-fPIC','-shared','-static-libstdc++',
                 HERE/'jni_probe.cpp',DNS/'prototype/owned_lookup.cpp',
                 '-Wl,-z,max-page-size=16384','-Wl,--no-as-needed','-landroid','-ldl',
                 '-o',library/'libdnsprobe.so'])
            manifest = ET.parse(HERE/'AndroidManifest.xml')
            manifest.getroot().set('package', package)
            activity = manifest.getroot().find('application/activity')
            activity.set('{http://schemas.android.com/apk/res/android}name',
                         'com.projectinfinity.dnsprobe.ProbeActivity')
            manifest.write(stage/'AndroidManifest.xml', encoding='utf-8', xml_declaration=True)
            assert ET.parse(stage/'AndroidManifest.xml').getroot().get('package') in PACKAGES.values()
            run([tools/'aapt2','link','-o',stage/'resources.apk','--manifest',
                 stage/'AndroidManifest.xml','-I',android])
            classes = stage/'classes'; classes.mkdir()
            run(['javac','-source','8','-target','8','-classpath',android,
                 '-d',classes,HERE/'ProbeActivity.java'])
            dex = stage/'dex'; dex.mkdir()
            run([tools/'d8','--lib',android,'--output',dex,
                 *sorted(classes.rglob('*.class'))])
            with ZipFile(stage/'resources.apk') as original, ZipFile(stage/'unsigned.apk','w') as target:
                for info in original.infolist(): target.writestr(info, original.read(info))
                target.write(dex/'classes.dex','classes.dex')
                for p in library.iterdir(): target.write(p, 'lib/'+abi+'/'+p.name)
            run([tools/'zipalign','-P','16','-f','4',stage/'unsigned.apk',stage/'aligned.apk'])
            run([tools/'apksigner','sign','--ks',key,'--ks-key-alias','diagnostic',
                 '--ks-pass','pass:android','--key-pass','pass:android',
                 '--out',stage/'DIAGNOSTIC-ONLY.apk',stage/'aligned.apk'])
            run([tools/'apksigner','verify',stage/'DIAGNOSTIC-ONLY.apk'])
    finally:
        key.unlink(missing_ok=True)
    save('BUILD.json', {'status':'DIAGNOSTIC_PACKAGES_ONLY','packages':PACKAGES,
         'original_key_access':False,'Infinity_APK':False,'Cobra_changes':False,
         'native_sources':{str(p.relative_to(DNS)):hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (DNS/'prototype').glob('*') if p.suffix in ('.c','.cpp','.h')}})


def execute():
    assert os.environ.get('GITHUB_ACTIONS') == 'true'
    serial = subprocess.check_output(['adb','get-serialno'],text=True).strip()
    assert serial.startswith('emulator-'), 'Only disposable CI emulator is authorized'
    save('RESULT.json', {'status':'RUNNING_NOT_ACCEPTED','Infinity_installed':False})
    results = {}
    for abi, package in PACKAGES.items():
        assert package != 'com.projectinfinity.kodi'
        run(['adb','install','-t',OUT/abi/'DIAGNOSTIC-ONLY.apk'])
        run(['adb','shell','am','start','-W','-n',
             package+'/com.projectinfinity.dnsprobe.ProbeActivity'])
        report = None
        for _ in range(80):
            result = subprocess.run(['adb','shell','run-as',package,'cat','files/report.json'],
                                    capture_output=True,text=True)
            if result.returncode == 0:
                try: report = json.loads(result.stdout); break
                except json.JSONDecodeError: pass
            time.sleep(.5)
        log = subprocess.check_output(['adb','logcat','-d','-v','threadtime'],text=True)
        (OUT/(abi+'-logcat.txt')).write_text(log)
        if report is None:
            report = {'status':'NO_REPORT_NATIVE_EXECUTION_NOT_PROVEN'}
        save(abi+'-REPORT.json', report)
        failures = []
        if report.get('status') != 'EXECUTED_REQUIRES_HOST_ASSERTIONS':
            failures.append('APP_OR_HELPER_STARTUP_FAILED')
        else:
            def require(value, label):
                if not value: failures.append(label)
            require(report.get('helper_executable'), 'NATIVE_MEMBER_NOT_EXECUTABLE')
            require(not report.get('helper_writable'), 'NATIVE_MEMBER_APP_WRITABLE')
            for label, expected, limit in [('normal',0,2.25),('explicit_binding',0,2.25),
                    ('deadline',1,2.25),('cancel',2,.5),('repeated_cancel',2,.5),
                    ('missing_helper',5,2.25)]:
                rows = report.get(label,[])
                require(bool(rows), label+':NOT_RUN')
                for row in rows:
                    require(row['outcome']==expected, label+':OUTCOME')
                    require(row['caller_seconds']<=limit,label+':DEADLINE')
                    require(row['binding_read'],label+':BINDING_CAPTURE')
                    require(row['wait_error']==0,label+':CHILD_NOT_REAPED')
                    if label in ('normal','explicit_binding'):
                        require(row['gai_error']==0 and row['addresses']>0,label+':NO_ADDRESS')
                        require(row['inherited_extra_fds']==0,label+':FD_INHERITANCE')
                    if label=='explicit_binding': require(row['explicit_binding'],label+':NOT_BOUND')
            # Process-wide FD counts are observations; independent ART activity
            # can change them. Retain every delta for resource review.
        results[abi] = {'status':'PASS_ISOLATED_ANDROID_FEASIBILITY' if not failures else 'FAIL',
                        'failures':failures, 'package':package}
        save('RESULT.json', {'status':'PASS' if len(results)==2 and
             all(r['status'].startswith('PASS') for r in results.values()) else 'INCOMPLETE_OR_FAIL',
             'variants':results,'production_curl_integration':'NOT_IMPLEMENTED',
             'Infinity_or_Cobra_app_tests':'NOT_RUN','Fold_acceptance':'NOT_RUN'})
    if any(not r['status'].startswith('PASS') for r in results.values()):
        raise RuntimeError('ANDROID_FEASIBILITY_GATE_FAILED; exact reports retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation',choices=['build','execute'])
    {'build':build,'execute':execute}[parser.parse_args().operation]()
