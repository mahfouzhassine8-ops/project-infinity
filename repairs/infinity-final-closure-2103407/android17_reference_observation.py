"""Reuse the feature-only runner; preserve failures hidden by fixture export errors.

No APK modification, shutdown operation, permission relaxation or passing-result
fallback. Only the disposable selected-test service gets an additional bounded
failure log before its original JSON export. File/UID observations are read-only.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'repairs/save-later-multiimage-20261023'
PROBE_SHA='72a79edb17640df3a9b7ebf1916047a982211029289486cba0d5d21e48849511'
FIXTURE_SHA='84f8bd92b186500f8a3d5a41a6492ac58bc7c895b423f3ddb0fa0ca6cdc4dd98'
BEFORE='    finally:output.write_text(json.dumps(result,indent=2))'
AFTER='''    finally:
        if not result.get('passed'):
            xbmc.log('INFINITY_FEATURE_FIXTURE_FAILURE '+json.dumps({
                'pid':os.getpid(),'selected_mode':mode,'passed':False,
                'failure':result.get('failure','unavailable'),
                'traceback':str(result.get('traceback',''))[-12000:]}),xbmc.LOGERROR)
        try:
            output.write_text(json.dumps(result,indent=2))
        except BaseException as export_error:
            xbmc.log('INFINITY_FEATURE_FIXTURE_EXPORT_FAILED '+type(export_error).__name__,xbmc.LOGERROR)
            raise'''


def instrument_fixture(raw):
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('Retained exact selected-test source required')
    text=raw.decode()
    if text.count(BEFORE)!=1:raise ValueError('Unexpected original fixture export')
    result=text.replace(BEFORE,AFTER,1)
    if result.replace(AFTER,BEFORE,1)!=text:raise ValueError('A selected-test assertion changed')
    compile(result,'android_selected.py','exec')
    return result.encode()


def failed_observation(log,pid):
    prefix='INFINITY_FEATURE_FIXTURE_FAILURE '
    for line in reversed(log.splitlines()):
        if prefix not in line:continue
        try:value=json.loads(line.split(prefix,1)[1])
        except (ValueError,TypeError):continue
        if (isinstance(value,dict) and value.get('pid')==pid and value.get('passed') is False and
                value.get('selected_mode')=='final-search-all-enter'):
            return value
    return None


def owned_fixture_profile(device,fixture_id):
    expected='/sdcard/Android/data/com.projectinfinity.kodi/files/.kodi/userdata'
    if (device.PROFILE!=expected or fixture_id!='service.future.persistence.7fa29' or
        device.PACKAGE!='com.projectinfinity.kodi' or
        device.shell('getprop','ro.kernel.qemu').strip()!='1' or
        device.shell('getprop','ro.build.version.sdk').strip()!='37'):
        raise ValueError('Only the original disposable API37 fixture may be prepared')
    uid=device.shell('stat','-c','%u',device.PRIVATE).strip()
    if not uid.isdigit() or int(uid)<10000:raise ValueError('Verified installed application UID required')
    relative='/Android/data/'+device.PACKAGE+'/files/.kodi/userdata/addon_data/'+fixture_id
    backing='/data/media/0'+relative
    profile=expected+'/addon_data/'+fixture_id
    device.shell('mkdir','-p',profile)
    before=device.shell('stat','-c','%u',profile).strip()
    if before not in ('0',uid):raise ValueError('Unexpected fixture owner; no ownership change permitted')
    if before=='0':
        device.shell('chown','-R',uid+':'+uid,backing)
        device.shell('restorecon','-RF',backing)
    after=device.shell('stat','-c','%u',profile).strip()
    if after!=uid or device.shell('getenforce').strip()!='Enforcing':
        raise ValueError('Fixture ownership or original SELinux boundary could not be established')
    return dict(fixture_profile=profile,backing_fixture_profile=backing,installed_uid=uid,
                before_uid=before,after_uid=after,permissions_relaxed=False,
                provider_or_other_profile_modified=False)


def main():
    path=OLD/'android_feature_probe.py'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=PROBE_SHA:raise ValueError('Existing feature-only runner changed')
    sys.path.insert(0,str(OLD))
    spec=importlib.util.spec_from_file_location('retained_feature_only_probe',path)
    probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    original_adb=probe.device.adb
    def push(*args,**kwargs):
        if len(args)>=2 and args[0]=='push':
            candidate=Path(args[1])
            if candidate.is_dir() and candidate.name==probe.staging.FUTURE:
                fixture=candidate/'android_selected.py'
                if fixture.exists():
                    raw=fixture.read_bytes();result=instrument_fixture(raw);fixture.write_bytes(result)
                    ownership=owned_fixture_profile(probe.device,probe.staging.FUTURE)
                    (candidate.parent.parent/'FIXTURE-OBSERVATION-SCOPE.json').write_text(json.dumps({
                        'original_fixture_sha256':hashlib.sha256(raw).hexdigest(),
                        'observed_fixture_sha256':hashlib.sha256(result).hexdigest(),
                        'test_assertions_changed':False,'APK_changed':False,'provider_code_changed':False,
                        'shutdown':'NOT RUN','false_or_missing_results_cannot_pass':True,
                        'fixture_ownership':ownership},indent=2)+'\n')
        return original_adb(*args,**kwargs)
    probe.device.adb=push
    original_admit=probe.staging.admit_runtime
    def admit(device,owner,out):
        ownership=owned_fixture_profile(device,probe.staging.FUTURE)
        original_admit(device,owner,out)
        profile=device.PROFILE+'/addon_data/'+probe.staging.FUTURE
        report={'pid':owner['pid'],'private_uid':device.shell('stat','-c','%u',device.PRIVATE,check=False).strip(),
                'process_uid_status':device.shell('cat','/proc/'+str(owner['pid'])+'/status',check=False),
                'fixture_permissions':{},'owned_fixture_preparation':ownership}
        for path in (device.PROFILE,device.PROFILE+'/addon_data',profile,
                     profile+'/navigation-start-'+str(owner['pid'])+'.json'):
            report['fixture_permissions'][path]=device.shell('stat','-c','%u:%g:%a:%F',path,check=False).strip()
        (out/'FIXTURE-PERMISSIONS.json').write_text(json.dumps(report,indent=2)+'\n')
    probe.staging.admit_runtime=admit
    original_read=probe.device.read_json;next_read=0.0
    def read(path):
        nonlocal next_read
        result=original_read(path)
        name=Path(path).name
        if not result and name.startswith('navigation-ready-') and name.endswith('.json'):
            token=name.removeprefix('navigation-ready-').removesuffix('.json')
            if token.isdigit() and time.monotonic()>=next_read:
                next_read=time.monotonic()+5.0
                log=probe.device.shell('tail','-n','220',probe.device.PROFILE+'/../temp/kodi.log',check=False)
                failure=failed_observation(log,int(token))
                if failure is not None:
                    # Early failure only. The original JSON result is still
                    # mandatory for PASS and any export exception remains FAIL.
                    raise RuntimeError('Selected fixture failed before JSON export: '+str(failure['failure']))
        return result
    probe.device.read_json=read
    original_execute=probe.execute
    def execute(args):
        report=original_execute(args)
        receipt=args.out/'FIXTURE-OBSERVATION-SCOPE.json'
        if receipt.exists():
            scope=json.loads(receipt.read_text())
            key=probe.staging.FUTURE+'/android_selected.py'
            if (scope['original_fixture_sha256']!=FIXTURE_SHA or
                    report.get('fixture_manifest',{}).get(key)!=FIXTURE_SHA):
                raise ValueError('Observation source binding differs from the actual staged fixture')
            report['fixture_manifest_before_observation']={key:FIXTURE_SHA}
            report['fixture_manifest'][key]=scope['observed_fixture_sha256']
            report['observation_fixture_scope']=scope
            (args.out/'FEATURE-RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    probe.execute=execute
    probe.main()


if __name__=='__main__':main()
