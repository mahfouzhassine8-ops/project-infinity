"""Recover one emulator ADB daemon setup closure before any app is installed."""
import json
from pathlib import Path
import subprocess


def root(device,adb,out):
    try:return adb('root')
    except RuntimeError as error:
        if 'unable to connect for root: closed' not in str(error):raise
        prior=str(error)
    # The retained adb wrapper has a fixed90sec timeout and accepts only
    # check/binary keywords. This fixed, non-mutating host wait has its own
    # 30sec budget; all actual root commands still use the retained wrapper.
    result=subprocess.run(['adb','wait-for-device'],capture_output=True,text=True,timeout=30)
    if result.returncode:
        raise RuntimeError('Emulator daemon wait failed: '+result.stderr[-1000:])
    if (device.PACKAGE!='com.projectinfinity.kodi' or
        device.shell('getprop','ro.kernel.qemu').strip()!='1' or
        device.shell('getprop','ro.build.version.sdk').strip()!='37' or
        device.shell('pm','list','packages',device.PACKAGE).strip() or device.running_engine()):
        raise ValueError('Root transport recovery requires fresh no-app API37 emulator')
    value=adb('root')
    (Path(out)/'ADB-ROOT-TRANSPORT-RECOVERY.json').write_text(json.dumps(dict(
        first_transport_error=prior,second_root_result=value,application_installed=False,
        application_test_retried=False,root_attempts=2),indent=2)+'\n')
    return value
