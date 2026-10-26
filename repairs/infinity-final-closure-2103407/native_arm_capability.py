"""Platform capability only: no APK, application input, writer or Close operation."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import time

IMAGE='system-images;android-37.0;default;arm64-v8a'
AVD='infinity-native-arm-capability'


def validate(request):
    exact=dict(schema=1,kind='native-arm-platform-capability-only',runner='macos-26',
        image=IMAGE,acceleration='off',application_APK_installed=False,application_tests_selected=False)
    if (set(request)!=set(exact)|{'authorization'} or not request.get('authorization') or
            any(type(request.get(k)) is not type(v) or request[k]!=v for k,v in exact.items())):
        raise ValueError('Exact platform-only ARM64 capability request required')
    return request


def run(sdk,out):
    sdk=Path(sdk);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    report=dict(platform_capability_ready=False,application_tests_selected=False,
        application_APK_installed=False,application_test_passed=False,physical_Fold='NOT RUN',
        image=IMAGE,host_machine=platform.machine(),host_os=platform.system(),
        acceleration='off',software_emulation='Explicit experimental TCG, unsupported/slow; no physical performance claim')
    process=None;log=None
    def command(args,timeout=20):
        result=subprocess.run([str(a) for a in args],capture_output=True,text=True,timeout=timeout)
        if result.returncode:raise RuntimeError(str(args[0])+': '+result.stderr[-2000:]+result.stdout[-1000:])
        return result.stdout.strip()
    adb=sdk/'platform-tools/adb';emulator=sdk/'emulator/emulator'
    try:
        if platform.system()!='Darwin' or platform.machine() not in ('arm64','aarch64'):
            raise RuntimeError('Native ARM64 macOS host required')
        report['emulator_version']=command([emulator,'-version'])
        home=Path(os.environ.get('ANDROID_AVD_HOME',str(Path.home()/'.android/avd')))
        meta=dict(line.split('=',1) for line in (home/(AVD+'.ini')).read_text().splitlines() if '=' in line)
        if meta.get('target')!='android-37.0':raise RuntimeError('Exact API37.0 AVD required')
        config=(Path(meta['path'])/'config.ini').read_text()
        (out/'avd-config.txt').write_text(config)
        if 'image.sysdir.1=system-images/android-37.0/default/arm64-v8a/' not in config:
            raise RuntimeError('Exact native ARM64 AOSP image required')
        command([adb,'start-server'])
        log=(out/'emulator.log').open('w')
        process=subprocess.Popen([str(emulator),'@'+AVD,'-accel','off','-no-window','-no-snapshot',
            '-gpu','swiftshader','-noaudio','-no-boot-anim','-camera-back','none',
            '-memory','2048','-cores','2'],stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,ANDROID_I_WANT_MY_TCG='yes'))
        began=time.monotonic();deadline=began+240
        booted=False
        while time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('Emulator exited before boot; inspect emulator.log')
            result=subprocess.run([str(adb),'-s','emulator-5554','shell','getprop','sys.boot_completed'],
                capture_output=True,text=True,timeout=10)
            if result.returncode==0 and result.stdout.strip()=='1':booted=True;break
            time.sleep(2)
        if not booted:raise RuntimeError('Platform boot not observed in240sec; no application test attempted')
        report['emulator_boot_seconds']=time.monotonic()-began
        def shell(*args):return command([adb,'-s','emulator-5554','shell',*args])
        props=shell('getprop');(out/'runtime-properties.txt').write_text(props)
        values=dict((line[1:].split(']: [',1)[0],line.split(']: [',1)[1][:-1])
                    for line in props.splitlines() if line.startswith('[') and ']: [' in line)
        report['sdk']=values.get('ro.build.version.sdk');report['release']=values.get('ro.build.version.release')
        report['ABI']=values.get('ro.product.cpu.abilist','').split(',')
        report['page_size']=int(shell('getconf','PAGE_SIZE'))
        if report['sdk']!='37' or report['release']!='17' or values.get('ro.kernel.qemu')!='1' or 'arm64-v8a' not in report['ABI']:
            raise RuntimeError('Actual platform does not match native ARM64 Android17/API37 emulator')
        if report['page_size']!=4096:raise RuntimeError('This unchanged native payload is not qualified on strict16KiB')
        if shell('pm','list','packages','com.projectinfinity.kodi'):
            raise RuntimeError('Platform probe refuses an existing application')
        report['adb_root']=command([adb,'-s','emulator-5554','root'])
        command([adb,'-s','emulator-5554','wait-for-device'],timeout=30)
        if shell('id','-u')!='0' or shell('getenforce')!='Enforcing':raise RuntimeError('Root/enforcing test transport unavailable')
        report['platform_capability_ready']=True
    except Exception as error:
        report['failure']=type(error).__name__+': '+str(error)
        raise
    finally:
        (out/'NATIVE-ARM-PLATFORM-CAPABILITY.json').write_text(json.dumps(report,indent=2)+'\n')
        if process is not None and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
        if log is not None:log.close()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--sdk',type=Path);parser.add_argument('--out',type=Path)
    args=parser.parse_args();validate(json.loads(args.request.read_text()))
    if args.sdk is not None:
        if args.out is None:parser.error('--out required with--sdk')
        print(json.dumps(run(args.sdk,args.out)))
