"""Existing feature-only probe with exact install-over/participant fixture adapters.

No APK modification, production helper replacement, writer approval, shutdown
operation, provider modification or asserted success is introduced.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
from zipfile import ZipFile

from android17_reference_observation import (OLD,PROBE_SHA,FIXTURE_SHA,DRIVER_SHA,CHECKS_SHA,
    instrument_fixture,restore_fixture,owned_fixture_profile,setup_logging,preparation_seconds)
from prepare_signed407_fixture import digest
from candidate_request import EXPECTED

HOOK_BEFORE='            selected.stage(stage,args,report,device,staging.FUTURE)'
HOOK_AFTER=HOOK_BEFORE+'\n            _candidate_fixture(stage,args,report,device,staging.FUTURE)'
PROFILE_BEFORE='''        sys.path.insert(0,str(uiroot));from controller_access import load
        plugin=load();hub=plugin.hub;profile=plugin.PROFILE;home=xbmcgui.Window(10000)'''
PROFILE_AFTER='''        if mode=='final-participant' or mode in SEARCH_CASES:
            # This case reads actual native participant receipts only. No
            # first-party controller imports or writes in the test invoker.
            profile=Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('profile')))
            home=xbmcgui.Window(10000)
            if mode in SEARCH_CASES:
                # Independent read-only observation of persisted records. Do
                # not acquire the production writer lease from a test invoker.
                from types import SimpleNamespace
                def observed_state(actual_profile):
                    actual=Path(actual_profile)/'continue-watching.json'
                    if actual.is_symlink():raise RuntimeError('Linked observation refused')
                    if not actual.exists():return {'schema':2,'items':{}}
                    if actual.stat().st_size>8*1024*1024:raise RuntimeError('Oversized observation refused')
                    value=json.loads(actual.read_text(encoding='utf-8'))
                    if not isinstance(value,dict):raise RuntimeError('Invalid actual persisted state')
                    return value
                hub=SimpleNamespace(load_view=observed_state)
        else:
            sys.path.insert(0,str(uiroot));from controller_access import load
            plugin=load();hub=plugin.hub;profile=plugin.PROFILE;home=xbmcgui.Window(10000)'''
BASELINE_SHA='fc1d726fee8002da7cdccec6dd79a029f6536f0f1c3857791bec94c45d620e50'
IDS={'script.infinity.commandcenter','script.infinity.uirepair','script.infinity.watchedbridge','script.infinity.rails'}
RECEIPT_BEFORE='/data/user/0/com.projectinfinity.kodi/files/checkpoint/installed-participants.json'
RECEIPT_AFTER='/data/user/0/com.projectinfinity.kodi/files/infinity-checkpoint-install.json'
HISTORY_BEFORE='''            sys.path.insert(0,str(ccroot));from infinity_search import shared_history
            history=shared_history()'''
HISTORY_AFTER='''            history=observed_state(profile).get('infinity_search_history_v1',[])'''


def fixture(raw):
    observed=instrument_fixture(raw).decode()
    if observed.count(PROFILE_BEFORE)!=1:raise ValueError('Retained participant setup changed')
    if observed.count(RECEIPT_BEFORE)!=1:raise ValueError('Retained receipt read changed')
    if observed.count(HISTORY_BEFORE)!=1:raise ValueError('Retained history observation changed')
    updated=observed.replace(PROFILE_BEFORE,PROFILE_AFTER,1).replace(RECEIPT_BEFORE,RECEIPT_AFTER,1).replace(HISTORY_BEFORE,HISTORY_AFTER,1)
    restored=restore_candidate_fixture(updated)
    if restore_fixture(restored).encode()!=raw:
        raise ValueError('An original feature assertion changed')
    compile(updated,'android_selected.py','exec')
    return updated.encode()


def restore_candidate_fixture(text):
    return text.replace(PROFILE_AFTER,PROFILE_BEFORE,1).replace(RECEIPT_AFTER,RECEIPT_BEFORE,1).replace(HISTORY_AFTER,HISTORY_BEFORE,1)


def original_sources(apk,out):
    if digest(apk)!=BASELINE_SHA:raise ValueError('Exact signed408 reference source required')
    with ZipFile(apk) as archive:
        for name in archive.namelist():
            if not name.startswith('assets/addons/') or name.endswith('/'):continue
            relative=name[len('assets/addons/'):];path=Path(relative)
            if path.parts[0] not in IDS:continue
            if path.is_absolute() or '..' in path.parts or ((archive.getinfo(name).external_attr>>16)&0o170000)==0o120000:
                raise ValueError('Unsafe original source member')
            target=out/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(name))


def require_disposable(device):
    if (device.PACKAGE!='com.projectinfinity.kodi' or
        device.shell('getprop','ro.kernel.qemu').strip()!='1' or
        device.shell('getprop','ro.build.version.sdk').strip()!='37'):
        raise ValueError('Only the already-authorized fresh API37 emulator may install over')


def install_over(device,adb,baseline,candidate,out,fixture_id):
    require_disposable(device)
    if digest(baseline)!=BASELINE_SHA:raise ValueError('Protected baseline differs')
    if digest(candidate)!=EXPECTED['candidate_apk_sha256']:raise ValueError('Exact signed409candidate required')
    if device.PACKAGE in device.shell('pm','list','packages',device.PACKAGE):
        raise ValueError('Existing device installation refused')
    if 'Success' not in adb('install','--no-incremental',baseline):raise RuntimeError('Protected baseline installation failed')
    uid=device.shell('stat','-c','%u',device.PRIVATE).strip()
    if not uid.isdigit() or int(uid)<10000:raise RuntimeError('Baseline UID unavailable')
    owned_fixture_profile(device,fixture_id)
    sentinel=out/'preupdate-test-sentinel.txt';sentinel.write_text('Infinity private fixture data before install-over\n')
    target=device.PROFILE+'/addon_data/'+fixture_id+'/preupdate-test-sentinel.txt'
    adb('push',sentinel,target)
    result=adb('install','-r','--no-incremental',candidate)
    after=device.shell('stat','-c','%u',device.PRIVATE).strip()
    retained=device.shell('cat',target)
    if 'Success' not in result or uid!=after or retained!=sentinel.read_text():
        raise RuntimeError('Install-over UID or test-data preservation failed')
    record=dict(baseline_sha256=BASELINE_SHA,candidate_sha256=digest(candidate),
        baseline_uid=uid,candidate_uid=after,install_method='adb install -r',
        baseline_launched=False,test_sentinel_preserved=True,
        actual_user_database_acceptance=False,uninstall_or_data_clear=False)
    (out/'INSTALL-OVER-EVIDENCE.json').write_text(json.dumps(record,indent=2)+'\n')
    return result


def main(selected_case=None):
    # Independent shutdown may reuse only the already-passing participant
    # setup. This module and its feature transport never request termination.
    if selected_case not in (None,'final-participant'):
        raise ValueError('Only retained participant setup may be reused')
    selected_case=selected_case or EXPECTED['selected_case']
    original=OLD/'android_feature_probe.py';raw=original.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PROBE_SHA or raw.decode().count(HOOK_BEFORE)!=1:
        raise ValueError('Retained feature-only transport changed')
    text=raw.decode().replace(HOOK_BEFORE,HOOK_AFTER,1)
    if text.replace(HOOK_AFTER,HOOK_BEFORE,1)!=raw.decode():raise ValueError('Original transport assertions changed')
    baseline=Path(os.environ['TEST_BASELINE_APK']).resolve()
    sys.path.insert(0,str(OLD))
    probe=types.ModuleType('exact_integrated_feature_probe');probe.__file__=str(original)
    exec(compile(text,str(original),'exec'),probe.__dict__)
    original_adb=probe.device.adb
    with tempfile.TemporaryDirectory(prefix='infinity-test407-source-') as temp:
        sources=Path(temp);original_sources(baseline,sources)
        def adapt(stage,args,report,device,aid):
            if args.case!=selected_case or aid!='service.future.persistence.7fa29':
                raise ValueError('Only the explicitly selected candidate case is adapted')
            if stage.resolve()!=(args.out.resolve()/'fixture'):raise ValueError('Unexpected fixture root')
            path=stage/aid/'android_selected.py';before=path.read_bytes()
            if hashlib.sha256(before).hexdigest()!=FIXTURE_SHA:raise ValueError('Original selected feature differs')
            path.write_bytes(fixture(before))
            # Seed the actual previous code, not new code installed by a test.
            # Java409 must migrate all four original IDs before Python starts.
            for addon in IDS:
                target=stage/addon
                if target.is_symlink():raise ValueError('Linked fixture refused')
                if target.exists():shutil.rmtree(target)
                shutil.copytree(sources/addon,target)
            report['candidate_test_adapter']=dict(case=args.case,original_fixture_sha256=FIXTURE_SHA,
                actual_fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                actual_old_code_staged=True,code_baseline_sha256=BASELINE_SHA,
                APK_changed=False,assertions_changed=False,providers_changed=False,shutdown='NOT RUN')
        probe._candidate_fixture=adapt
        def adb(*args,**kwargs):
            if args and args[0]=='install':
                # The original probe already refuses physical/non37/existing
                # installs. Recheck that boundary before either APK install.
                candidate=Path(args[-1]);out=Path(sys.argv[sys.argv.index('--out')+1])
                return install_over(probe.device,original_adb,baseline,candidate,out,probe.staging.FUTURE)
            if len(args)>=2 and args[0]=='push':
                folder=Path(args[1])
                if folder.is_dir() and folder.name==probe.staging.FUTURE:
                    owned_fixture_profile(probe.device,probe.staging.FUTURE)
                    setup_logging(probe.device,folder.parent.parent)
            return original_adb(*args,**kwargs)
        probe.device.adb=adb
        for source,wanted in ((OLD/'universal/android_search_input.py',DRIVER_SHA),
                              (OLD/'android_runtime_checks.py',CHECKS_SHA)):
            if hashlib.sha256(source.read_bytes()).hexdigest()!=wanted:
                raise ValueError('Retained real Android input/assertions changed')
        original_until=probe.device.until
        probe.device.until=lambda function,seconds:original_until(function,preparation_seconds(function,seconds))
        original_admit=probe.staging.admit_runtime
        def admit(device,owner,out):
            owned_fixture_profile(device,probe.staging.FUTURE)
            original_admit(device,owner,out)
            target=device.PROFILE+'/addon_data/'+probe.staging.FUTURE+'/preupdate-test-sentinel.txt'
            if device.shell('cat',target)!='Infinity private fixture data before install-over\n':
                raise RuntimeError('Startup changed the preserved test-data sentinel')
            observations={}
            for name in ('infinity-checkpoint-install.json','checkpoint/installed-participants.json','infinity-kodi-process.json'):
                observations[name]=device.read_json(device.PRIVATE+'/files/'+name)
            (out/'NATIVE-PARTICIPANT-OBSERVATIONS.json').write_text(json.dumps(observations,indent=2)+'\n')
        probe.staging.admit_runtime=admit
        original_execute=probe.execute
        def execute(args):
            report=original_execute(args)
            if report.get('platform',{}).get('qemu')=='1' and isinstance(report.get('engine',{}).get('pid'),int):
                snapshot={}
                for name in ('active.json','engine.json'):
                    target=probe.device.PROFILE+'/addon_data/script.infinity.commandcenter/.android-checkpoint/'+name
                    try:
                        value=probe.device.read_json(target)
                        snapshot[name]=dict(status='AVAILABLE' if value else 'UNAVAILABLE',value=value)
                    except Exception as error:snapshot[name]=dict(status='UNAVAILABLE',reason=type(error).__name__)
                (args.out/'POST-FEATURE-NATIVE-PARTICIPANT.json').write_text(json.dumps(snapshot,indent=2)+'\n')
                if report.get('passed') is not True:
                    try:
                        stack=probe.device.shell('debuggerd','-b',str(report['engine']['pid']),check=False)
                        (args.out/'participant-live-native-backtrace.txt').write_text(stack or 'UNAVAILABLE: debuggerd returned no context\n')
                    except Exception as error:
                        (args.out/'participant-live-native-backtrace.txt').write_text('UNAVAILABLE: '+type(error).__name__+'\n')
            return report
        probe.execute=execute
        probe.main()


if __name__=='__main__':main()
