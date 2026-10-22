"""Actual signed ARM64 APK and future service on a fresh Android17 emulator."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import time
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
probe=load('probe',ROOT/'repairs/android-checkpoint-shutdown/runtime-tests/essential_android_probe.py')
installed=load('installed',ROOT/'repairs/android-checkpoint-shutdown/installed/build.py')
FUTURE='service.future.persistence.7fa29'

def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def sha(data):return hashlib.sha256(data).hexdigest()
def until(fn,seconds):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=fn()
        if value:return value
        time.sleep(.25)
    raise RuntimeError('Timed out waiting for independently observed device state')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apk',type=Path,required=True);p.add_argument('--expected-sha',required=True)
    p.add_argument('--mode',choices=['safe','pending','baseline','opaque','lost-file'],required=True)
    p.add_argument('--versioncheck-fixture',type=Path)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    report=dict(passed=False,scope='actual signed APK on disposable Android17 emulator',mode=a.mode,
        physical_fold_verified=False,real_provider_code_tested=False,final_lock=False,cycles=[])
    try:
        assert sha(a.apk.read_bytes())==a.expected_sha
        report['apk_sha256']=a.expected_sha
        # A root restart can race the emulator's initial ADB transport. Retry
        # only this infrastructure handshake, before installation or test work.
        for attempt in range(3):
            try:
                probe.adb('wait-for-device');probe.adb('root');probe.adb('wait-for-device')
                assert probe.shell('id','-u').strip()=='0'
                break
            except RuntimeError:
                if attempt==2:raise
                time.sleep(1)
        platform={k:probe.shell('getprop',v).strip() for k,v in [('qemu','ro.kernel.qemu'),('sdk','ro.build.version.sdk'),('release','ro.build.version.release'),('abis','ro.product.cpu.abilist')]}
        report['platform']=platform
        assert platform['qemu']=='1' and platform['sdk']=='37' and platform['release'].split('.')[0]=='17'
        assert 'arm64-v8a' in platform['abis']
        assert probe.PACKAGE not in probe.shell('pm','list','packages',probe.PACKAGE),'Fresh emulator only'
        assert 'Success' in probe.adb('install','--no-incremental',a.apk)
        probe.shell('input','keyevent','82')
        for permission in ('android.permission.READ_EXTERNAL_STORAGE','android.permission.WRITE_EXTERNAL_STORAGE'):
            probe.shell('pm','grant',probe.PACKAGE,permission,check=False)
        probe.shell('appops','set',probe.PACKAGE,'MANAGE_EXTERNAL_STORAGE','allow',check=False)
        uid=probe.shell('stat','-c','%u',probe.PRIVATE).strip();assert uid.isdigit();probe.APP_UID=uid
        probe.shell('mkdir','-p',probe.PROFILE+'/../addons',probe.PRIVATE+'/shared_prefs')
        prefs=a.out/'infinity_experience.xml';prefs.write_text('<map><string name="default">infinity</string></map>')
        probe.adb('push',prefs,probe.PRIVATE+'/shared_prefs/infinity_experience.xml')
        settings=a.out/'guisettings.xml';settings.write_text('<settings version="2"><setting id="general.addonupdates">2</setting></settings>')
        probe.adb('push',settings,probe.PROFILE+'/guisettings.xml')
        favourite=a.out/'favourites.xml';favourite.write_text('<favourites><favourite name="Universal persistence preserved">ActivateWindow(Home)</favourite></favourites>')
        probe.adb('push',favourite,probe.PROFILE+'/favourites.xml')
        stage=a.out/'fixture';stage.mkdir()
        # Current first-party code comes from the exact APK, except the already
        # approved installed compat0.8.2 contract needed by the existing coordinator.
        with ZipFile(a.apk) as z:
            name='script.infinity.commandcenter';prefix='assets/addons/'+name+'/'
            for member in z.namelist():
                if member.startswith(prefix) and not member.endswith('/'):
                    target=stage/name/member[len(prefix):];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(member))
        _,compat=installed.sources('service.infinity.compat')
        for name,data in compat.items():
            target=stage/'service.infinity.compat'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        if a.mode in ('safe','pending','lost-file'):
            assert a.versioncheck_fixture
            # Reuse the existing archived compatible package byte-for-byte,
            # never patch provider source, disable its service or edit the APK.
            original=load('original_versioncheck_stager',ROOT/'repairs/four-repair-20261018/versioncheck_android.py')
            report['preexisting_compatible_profile_fixture']=original.stage(a.versioncheck_fixture,stage)
        future=stage/FUTURE;future.mkdir()
        (future/'addon.xml').write_text('<addon id="'+FUTURE+'" name="Future persistence test" version="1.0.0" provider-name="Disposable CI fixture"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.service" library="service.py" start="startup"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Future provider regression</summary><description lang="en_GB">Disposable emulator only</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        shutil.copyfile(HERE/'android_future_service.py',future/'service.py')
        (future/'resources').mkdir()
        (future/'resources/settings.xml').write_text('<settings><category label="Tests"><setting id="test_mode" type="text" default="'+('pending' if a.mode=='pending' else 'safe')+'"/><setting id="preserved_setting" type="text" default=""/></category></settings>')
        report['fixture_manifest']={str(f.relative_to(stage)):sha(f.read_bytes()) for f in stage.rglob('*') if f.is_file()}
        for directory in stage.iterdir():probe.adb('push',directory,probe.PROFILE+'/../addons/'+directory.name)
        backing='/data/media/0/Android/data/'+probe.PACKAGE
        probe.shell('chown','-R',uid+':'+uid,backing,probe.PRIVATE+'/shared_prefs')
        probe.shell('restorecon','-RF',backing,probe.PRIVATE+'/shared_prefs')
        assert probe.shell('getenforce').strip()=='Enforcing'
        probe.adb('logcat','-c')
        probe.FIRST_PARTY={'script.infinity.commandcenter':'0.3.5.29','service.infinity.compat':'0.8.2'}
        old_owner=None
        for cycle in range(3 if a.mode=='safe' else 1):
            entry=dict(cycle=cycle);report['cycles'].append(entry)
            probe.shell('am','start','-W','-n',probe.PACKAGE+'/.Splash')
            cycleout=a.out/('cycle-'+str(cycle));cycleout.mkdir()
            entry['first_party']=probe.enable_first_party(cycleout)
            entry['versioncheck']=probe.rpc('Addons.GetAddonDetails',{'addonid':'service.xbmc.versioncheck','properties':['enabled','version']})['addon']
            assert entry['versioncheck']['enabled']
            details=probe.rpc('Addons.GetAddonDetails',{'addonid':FUTURE,'properties':['enabled','version']})['addon']
            if not details['enabled']:assert probe.rpc('Addons.SetAddonEnabled',{'addonid':FUTURE,'enabled':True})=='OK'
            owner=probe.wait_ready(old_owner);entry['owner']=owner
            ready_path=probe.PROFILE+'/addon_data/'+FUTURE+'/ready-'+str(owner['pid'])+'.json'
            ready=until(lambda:probe.read_json(ready_path),60)
            assert ready['pid']==owner['pid'] and ready['addon']==FUTURE and ready['worker_ready']
            assert ready['supported_child_returned']
            assert ready['failed_commit_rolled_back']
            assert ready['history_count']==ready['watched_count']==cycle+1
            if a.mode in ('safe','pending','lost-file'):
                assert ready['versioncheck_version']=='0.5.28+infinity.1'
                assert ready['versioncheck_service_sha256']=='6eb8ed9dd5d4712aacb44d55c3e006b1da5198c6bee076315579927c437bcfc1'
            else:
                assert ready['versioncheck_version']=='0.5.27+matrix.1'
                assert ready['versioncheck_service_sha256']=='166a1f5974fd2f7c297f801dd36040b4e7d6ccf6655e2edfa335803f3bbc58d5'
            assert [x['value_type'] for x in ready['errors']]==['NoneType','int','memoryview']
            assert all(x['exception']=='TypeError' for x in ready['errors'])
            entry['service_ready']=ready
            if a.mode=='lost-file':
                # Fault injection only into this fresh emulator's own fixture,
                # after its dirty file is admitted. Never a user profile file.
                lost=probe.PROFILE+'/addon_data/'+FUTURE+'/buffered-'+str(owner['pid'])
                assert probe.shell('getprop','ro.kernel.qemu').strip()=='1'
                probe.shell('rm','--',lost)
                entry['injected_external_namespace_loss']=lost
            probe.shell('am','start','-n',probe.PACKAGE+'/.InfinityPowerControlActivity','-a',probe.PACKAGE+'.action.CLOSE_KODI')
            def terminal():
                r=probe.read_json(probe.PRIVATE+'/files/infinity-checkpoint-close.json')
                return r if r.get('owner')==owner['owner'] and r.get('phase') in ('COMPLETE','CHECKPOINT_FAILED') else None
            receipt=until(terminal,60);entry['receipt']=receipt
            entry['processes_after']=probe.processes()
            save(a.out/'ANDROID17-RESULT.json',report)
            if a.mode!='safe':
                assert receipt['phase']=='CHECKPOINT_FAILED'
                assert not receipt.get('authorization_consumed')
                assert any(x['pid']==owner['pid'] for x in entry['processes_after'])
                evidence=json.dumps(receipt)
                if a.mode=='baseline':assert FUTURE in evidence and 'vfs_write_exception' in evidence
                elif a.mode=='pending':
                    assert FUTURE in evidence and ('pending_protected_sqlite_write_transaction' in evidence or 'sqlite_pending_transaction_at_retirement' in evidence)
                    assert not any('unflushed_protected_buffer' in x for x in receipt['last_native_status']['essential_write_blockers'])
                elif a.mode=='lost-file':
                    actual=receipt['last_native_status']['essential_write_blockers']
                    stamp='buffered-'+str(owner['pid'])
                    assert any('unflushed_protected_buffer' in x and FUTURE in x and stamp in x for x in actual),actual
                    assert all(FUTURE in x and (stamp in x or 'unverified_dirty_buffer_namespace' in x) for x in actual),actual
                else:
                    assert 'service.xbmc.versioncheck' in evidence and 'external_or_opaque_writer_requires_explicit_participant' in evidence
                    blockers=receipt['last_native_status']['script_persistence']['blockers']
                    rejected=[x for x in blockers if x.get('writer','').startswith(FUTURE) and x.get('reason')=='vfs_write_exception']
                    assert len(rejected)==3 and all(not x['blocking'] and 'argument_rejected_before_native_write' in x['detail'] for x in rejected)
                    assert all('service.xbmc.versioncheck' in x['writer'] for x in blockers if x['blocking'])
                    assert all('service.xbmc.versioncheck' in x for x in receipt['last_native_status']['essential_write_blockers'])
                entry['unverified_state_remained_blocked']=True
                break
            assert receipt['phase']=='COMPLETE',json.dumps(receipt)
            assert receipt['pid']==owner['pid']
            assert all(receipt.get(k) is True for k in ('checkpoint_saved','authorization_consumed','process_death_confirmed'))
            native=receipt['native_receipt']
            assert native['essential_writes_sealed'] and native['essential_writes_durable'] and not native['essential_write_blockers']
            mandatory=[x for x in native['owners'] if x['owner'] in native['essential_owners']]
            assert len(mandatory)==16 and all(x['required_writes_finished'] and not x['dirty_remaining'] and x['result'] in ('COMMITTED','ALREADY_DURABLE') for x in mandatory)
            assert not any(x['pid']==owner['pid'] for x in entry['processes_after'])
            data=cycleout/'future-data';probe.adb('pull',probe.PROFILE+'/addon_data/'+FUTURE,data)
            stamp=str(owner['pid'])
            assert probe.shell('cat',ready['essential_vfs'])=='textbytesarray'
            for leaf,expected in [('plain-','ordinary state'),('replaced-','replaced state'),('buffered-','buffered state'),('worker-','child buffered state')]:
                assert (data/(leaf+stamp)).read_text()==expected
            for name,table,field,value in [('history.db','history','position',37),('watched.db','watched','watched',1),('commit-controls.db','commits','value',1)]:
                with sqlite3.connect(data/name) as db:
                    assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
                    rows=db.execute('SELECT '+field+' FROM '+table).fetchall()
                    assert rows==[(value,)]*(cycle+1),rows
            assert 'future-provider-state' in (data/'settings.xml').read_text()
            saved=ET.fromstring(probe.shell('cat',probe.PROFILE+'/favourites.xml'))
            assert any(x.get('name')=='Universal persistence preserved' for x in saved)
            entry['independent_data_readback_passed']=True;old_owner=owner['owner']
            probe.adb('pull',probe.PROFILE+'/Database',cycleout/'Database')
            databases=list((cycleout/'Database').glob('*.db'));assert databases
            for database in databases:
                with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:assert db.execute('PRAGMA integrity_check').fetchone()==('ok',),database
            entry['kodi_database_integrity_passed']=True
        if a.mode=='safe':
            probe.shell('am','start','-W','-n',probe.PACKAGE+'/.Splash')
            final=a.out/'final-reopen';final.mkdir();probe.enable_first_party(final)
            owner=probe.wait_ready(old_owner)
            ready=until(lambda:probe.read_json(probe.PROFILE+'/addon_data/'+FUTURE+'/ready-'+str(owner['pid'])+'.json'),60)
            assert ready['pid']==owner['pid'] and ready['history_count']==ready['watched_count']==4
            report['final_reopen_verified']=dict(owner=owner,ready=ready)
        report['passed']=True
    except Exception as error:report['failure']=type(error).__name__+': '+str(error)
    finally:
        save(a.out/'ANDROID17-RESULT.json',report)
        for path,name in [(probe.PRIVATE+'/files/infinity-checkpoint-close.json','coordinator.json'),(probe.PROFILE+'/../temp/kodi.log','kodi.log'),(probe.PRIVATE+'/files/infinity-android-checkpoint.jsonl','android-checkpoint.jsonl')]:
            try:probe.adb('pull',path,a.out/name,check=False)
            except Exception:pass
        try:(a.out/'logcat.txt').write_text(probe.adb('logcat','-d','-v','threadtime',check=False))
        except Exception:pass
        try:(a.out/'screen.png').write_bytes(probe.adb('exec-out','screencap','-p',binary=True))
        except Exception:pass
    print(json.dumps(dict(passed=report['passed'],mode=a.mode,failure=report.get('failure')),indent=2))
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
