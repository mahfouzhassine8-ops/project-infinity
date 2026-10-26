"""Explicit same-API environment comparison; never changes application bytes/data."""
import argparse
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEGACY=ROOT/'four-repair-20261018/android37_gate.py'
API='37.1'
TARGET='google_apis_ps16k'
IMAGE='system-images;android-'+API+';'+TARGET+';x86_64'


def legacy():
    spec=importlib.util.spec_from_file_location('unchanged_api37_sdk_gate',LEGACY)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.IMAGE=IMAGE
    return module


def check_avd(avd_home,out):
    ini=Path(avd_home)/'infinity-four-repair-api37.ini';text=ini.read_text()
    values=dict(line.split('=',1) for line in text.splitlines() if '=' in line)
    if values.get('target')!='android-'+API:
        raise RuntimeError('Exact explicitly selected API37.1 AVD target required')
    config=Path(values['path'])/'config.ini';raw=config.read_text()
    properties=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
    required='system-images/android-'+API+'/'+TARGET+'/x86_64/'
    if properties.get('image.sysdir.1','').replace('\\','/')!=required or properties.get('abi.type')!='x86_64':
        raise RuntimeError('Exact explicitly selected API37.1 Google APIs ps16k source/ABI required')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'api37-avd.ini.txt').write_text(text);(out/'api37-avd-config.ini.txt').write_text(raw)
    (out/'API37-ENVIRONMENT-COMPARISON.json').write_text(json.dumps(dict(
        exact_selected_image=IMAGE,previous_image='system-images;android-37.0;google_apis;x86_64',
        reason='Retained actual pre-Python talloc/AT_RANDOM native startup crashes in two419 runs',
        application_changed=False,application_restarted=False,application_test_passed=False,
        lower_API_fallback=False,samsung_one_ui_emulated=False),indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sdk-root',required=True)
    parser.add_argument('--out',required=True);parser.add_argument('--pin-tools',action='store_true')
    parser.add_argument('--check-avd',action='store_true');args=parser.parse_args()
    if os.environ.get('INFINITY_EMULATOR_API')!=API or os.environ.get('INFINITY_EMULATOR_TARGET')!=TARGET:
        raise ValueError('Exact explicitly selected37.1/ps16k environment required')
    if args.check_avd:check_avd(os.environ['ANDROID_AVD_HOME'],args.out)
    else:
        gate=legacy()
        if args.pin_tools:gate.pin_tools(args.sdk_root,args.out)
        print(json.dumps(gate.check(args.sdk_root,args.out),sort_keys=True))


if __name__=='__main__':main()
