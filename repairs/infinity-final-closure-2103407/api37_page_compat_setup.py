"""Explicit OS-only backcompat configuration, before any app exists on disposable CI."""
import argparse
import json
from pathlib import Path
import subprocess

PROPERTIES={'bionic.linker.16kb.app_compat.enabled':'true','pm.16kb.app_compat.disabled':'false'}
PACKAGE='com.projectinfinity.kodi'


def validate(request):
    if (request.get('candidate_apk_sha256')!='0b202e3af93ce25be8cd5ecb2853043411ba5fbbf88dac0df94ef4b2ce55605a' or
        request.get('emulator_api')!='37.1' or request.get('emulator_target')!='google_apis_ps16k' or
        request.get('os_page_compat') is not True):
        raise ValueError('Exact signed419 explicit OS-backcompat environment required')


def configure(shell,adb,request):
    validate(request)
    def platform_guard():
        if (shell('getprop','ro.kernel.qemu')!='1' or shell('getprop','ro.build.version.sdk')!='37' or
            shell('getprop','ro.build.version.release')!='17' or shell('getconf','PAGE_SIZE')!='16384' or
            'arm64-v8a' not in shell('getprop','ro.product.cpu.abilist').split(',') or
            shell('pm','list','packages',PACKAGE) or shell('pidof',PACKAGE)):
            raise ValueError('Only fresh no-app native-compatible API37/Android17/16KiB emulator permitted')
    platform_guard()
    root=adb('root',allow_closed=True);adb('wait-for-device')
    platform_guard()
    if shell('id','-u')!='0' or shell('getenforce')!='Enforcing':raise ValueError('Root/enforcing transport required')
    before={key:shell('getprop',key) for key in PROPERTIES}
    for key,value in PROPERTIES.items():shell('setprop',key,value)
    after={key:shell('getprop',key) for key in PROPERTIES}
    if after!=PROPERTIES:raise RuntimeError('Actual OS compatibility property readback differs')
    return dict(mode='EXPLICIT_OS_BACKCOMPAT_ONLY_NOT_STRICT16K',before=before,after=after,
        root_transport=root,application_APK_installed=False,application_test_passed=False,
        APK_or_native_or_manifest_changed=False,physical_device_modified=False,
        strict16KiB_compliance=False,physical_Fold='NOT RUN')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    def adb(*values,allow_closed=False):
        result=subprocess.run(['adb',*values],capture_output=True,text=True,timeout=30)
        if result.returncode and not (allow_closed and 'unable to connect for root: closed' in result.stderr):
            raise RuntimeError('ADB failed: '+result.stderr[-1000:])
        return (result.stdout+result.stderr).strip()
    def shell(*values):
        result=subprocess.run(['adb','shell',*values],capture_output=True,text=True,timeout=30)
        if result.returncode and values[0]!='pidof':raise RuntimeError('ADB shell failed: '+result.stderr[-1000:])
        return result.stdout.strip()
    report=configure(shell,adb,json.loads(args.request.read_text()));args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
