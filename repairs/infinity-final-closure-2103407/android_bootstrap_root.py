"""Recover one emulator ADB daemon setup closure before any app is installed."""
import json
from pathlib import Path


def root(device,adb,out):
    try:return adb('root')
    except RuntimeError as error:
        if 'unable to connect for root: closed' not in str(error):raise
        prior=str(error)
    adb('wait-for-device',timeout=30)
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
