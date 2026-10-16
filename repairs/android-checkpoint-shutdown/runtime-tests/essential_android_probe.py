#!/usr/bin/env python3
"""Observe the real signed APK on a disposable Android emulator.

No production hooks, synthetic save receipts, forced shutdown, or user device.
Only fresh emulator test data is seeded. Failure evidence never authorizes APK
delivery. Engine death and whole-package death are reported independently.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import socket
import sqlite3
import subprocess
import time
import xml.etree.ElementTree as ET

PACKAGE = 'com.projectinfinity.kodi'
PRIVATE = '/data/user/0/'+PACKAGE
PROFILE = '/sdcard/Android/data/'+PACKAGE+'/files/.kodi/userdata'
CONTROL = PROFILE+'/addon_data/script.infinity.commandcenter/.android-checkpoint'
FAVOURITE = 'Infinity essential shutdown probe'
FIRST_PARTY = {'script.infinity.commandcenter':'0.3.5.20', 'service.infinity.compat':'0.8.2'}
READONLY_FIXTURE = 'script.infinity.readonlymaps.test'
READONLY_RESULT = PROFILE+'/addon_data/'+READONLY_FIXTURE+'/observed-readonly-maps.json'
APP_UID = None

def rpc(method, params=None):
    request={'jsonrpc':'2.0','id':1,'method':method}
    if params is not None: request['params']=params
    with socket.create_connection(('127.0.0.1',19090),timeout=10) as connection:
        connection.sendall(json.dumps(request).encode())
        pending='';decoder=json.JSONDecoder()
        while True:
            data=connection.recv(65536)
            if not data: raise RuntimeError('Kodi JSON-RPC closed without response: '+method)
            pending+=data.decode()
            while pending.strip():
                try: response,end=decoder.raw_decode(pending.lstrip())
                except ValueError: break
                pending=pending.lstrip()[end:]
                if response.get('id')==1:
                    if 'error' in response: raise RuntimeError('Kodi JSON-RPC '+method+': '+json.dumps(response['error']))
                    return response['result']

def enable_first_party(out):
    adb('forward','tcp:19090','tcp:9090')
    deadline=time.monotonic()+180;last_error=None
    while time.monotonic()<deadline:
        try:
            assert rpc('JSONRPC.Ping')=='pong'
            break
        except (OSError,RuntimeError,AssertionError) as error:
            last_error=str(error);time.sleep(1)
    else: raise RuntimeError('Actual Kodi JSON-RPC not ready: '+str(last_error))
    inventory=rpc('Addons.GetAddons',{'properties':['version','enabled']})
    (out/'actual-addon-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    installed={row['addonid']:row for row in inventory.get('addons',[])}
    results={}
    for name,version in FIRST_PARTY.items():
        assert name in installed,'Actual Kodi did not discover approved fixture: '+name
        details=rpc('Addons.GetAddonDetails',{'addonid':name,'properties':['version','enabled']})['addon']
        assert details['version']==version,(name,details)
        if not details['enabled']:
            assert rpc('Addons.SetAddonEnabled',{'addonid':name,'enabled':True})=='OK'
        results[name]=rpc('Addons.GetAddonDetails',{'addonid':name,'properties':['version','enabled']})['addon']
        assert results[name]['enabled'],name
    return results

def adb(*args, check=True, binary=False):
    result = subprocess.run(['adb',*map(str,args)],capture_output=True,text=not binary,timeout=90)
    if check and result.returncode:
        raise RuntimeError('adb operation failed: '+str(args[:3])+': '+str(result.stderr)[-1000:])
    return result.stdout

def shell(*args, check=True):
    return adb('shell',shlex.join(map(str,args)),check=check)

def read_json(path):
    text = shell('cat',path,check=False)
    try: return json.loads(text)
    except (ValueError,TypeError): return {}

def processes():
    found=[]
    assert APP_UID is not None, 'Installed package UID must be known'
    for line in shell('ps','-A','-o','PID,UID,NAME').splitlines()[1:]:
        fields=line.split()
        # Child executables can change NAME. Include every process with the
        # app's actual Linux UID, not only names containing the package.
        if len(fields)==3 and fields[1]==APP_UID:
            found.append({'pid':int(fields[0]),'uid':int(fields[1]),'name':fields[2]})
    return found

def wait_ready(previous_owner=None):
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        owner=read_json(PRIVATE+'/files/infinity-kodi-process.json')
        native=read_json(CONTROL+'/engine.json')
        compat=read_json(CONTROL+'/compat-active.json')
        participant=read_json(CONTROL+'/participant.json')
        active=read_json(CONTROL+'/active.json')
        if (owner.get('phase')=='RUNNING' and owner.get('owner')!=previous_owner and
            native.get('owner')==owner.get('owner') and native.get('pid')==owner.get('pid') and
            compat.get('owner')==active.get('owner')==owner.get('owner') and
            compat.get('pid')==active.get('pid')==owner.get('pid') and participant and
            any(p['pid']==owner.get('pid') and p['name']==PACKAGE+':kodi' for p in processes())):
            return owner
        time.sleep(1)
    raise RuntimeError('Actual Kodi engine and first-party startup handshakes did not become ready')

def system_executable_evidence(owner, out):
    """Read-only context for native executable-proof failures, never a waiver.

    Shell permissions differ from the app's SELinux domain. Record that scope
    explicitly and retain the actual engine mount table without interpreting
    root's access as proof that an app-side operation was safe.
    """
    commands = [('shell_identity', ('id',)),
                ('engine_mounts', ('cat', '/proc/'+str(owner['pid'])+'/mountinfo'))]
    for path in ('/vendor/bin/uname', '/vendor/bin', '/vendor',
                 '/system/bin/uname', '/system/bin', '/system', '/'):
        commands += [('stat:'+path, ('ls', '-ldZ', path)),
                     ('canonical:'+path, ('readlink', '-f', path))]
    results = {}
    for name, command in commands:
        result = subprocess.run(['adb', 'shell', shlex.join(command)],
                                capture_output=True, text=True, timeout=90)
        results[name] = {'exit_code':result.returncode,
                         'stdout':result.stdout, 'stderr':result.stderr}
    (out/'readonly-system-paths.json').write_text(json.dumps({
        'scope':'read-only shell observations and actual engine mount table; not authorization evidence',
        'engine_pid':owner['pid'], 'results':results}, indent=2)+'\n')

def main():
    global APP_UID
    p=argparse.ArgumentParser();p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--installed-addons',type=Path,required=True)
    p.add_argument('--require-java-save-proof',action='store_true')
    p.add_argument('--out',type=Path,required=True);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    report={'scope':'real signed ARM64 APK on disposable Android emulator; not physical Fold acceptance',
            'passed':False,'android_engine_death_verified':False,'whole_package_death_verified':False,
            'reopen_verified':False,'favourites_preserved':False,'kodi_databases_checked':[],
            'physical_fold_accepted':False,'apk_delivery_authorized':False}
    def save(): (args.out/'ANDROID-PROCESS-PROBE.json').write_text(json.dumps(report,indent=2)+'\n')
    try:
        report['apk_sha256']=hashlib.sha256(args.apk.read_bytes()).hexdigest()
        adb('root');adb('wait-for-device')
        # Refuse to touch an existing installation or any physical device.
        assert shell('getprop','ro.kernel.qemu').strip()=='1','Disposable emulator required'
        assert PACKAGE not in shell('pm','list','packages',PACKAGE),'Fresh emulator required; no user data may be replaced'
        report['abis']=shell('getprop','ro.product.cpu.abilist').strip()
        assert 'arm64-v8a' in report['abis'],'Emulator cannot execute this ARM64 APK'
        report['install']=adb('install','--no-incremental',args.apk).strip()
        assert 'Success' in report['install']
        shell('input','keyevent','82')
        for permission in ('android.permission.READ_EXTERNAL_STORAGE','android.permission.WRITE_EXTERNAL_STORAGE'):
            shell('pm','grant',PACKAGE,permission,check=False)
        shell('appops','set',PACKAGE,'MANAGE_EXTERNAL_STORAGE','allow',check=False)
        shell('mkdir','-p',PRIVATE+'/shared_prefs',PROFILE)
        uid=shell('stat','-c','%u',PRIVATE).strip();assert uid.isdigit()
        APP_UID=uid;report['package_uid']=int(uid)
        preference=args.out/'test-preference.xml'
        preference.write_text('<map><string name="default">infinity</string></map>\n')
        adb('push',preference,PRIVATE+'/shared_prefs/infinity_experience.xml')
        shell('chown','-R',uid+':'+uid,PRIVATE+'/shared_prefs')
        favourite=args.out/'test-favourites.xml'
        favourite.write_text('<favourites><favourite name="'+FAVOURITE+'">ActivateWindow(Home)</favourite></favourites>\n')
        adb('push',favourite,PROFILE+'/favourites.xml')
        # A fresh APK has no installed Command Center. Use the exact approved
        # installed add-ons from the locked native evidence, not substitute
        # handlers. The combined hash is checked independently against RC1.
        fixture=args.out/'first-party-fixture';fixture.mkdir()
        manifest={}
        for name in FIRST_PARTY:
            source=args.installed_addons/name
            assert source.is_dir(),source
            shutil.copytree(source,fixture/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            for path in sorted((fixture/name).rglob('*')):
                if path.is_file(): manifest[path.relative_to(fixture).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert digest=='eb61ddf66a01f434978c9ea070131311360ad76c536dd704355738db9179c1a5',digest
        report['unchanged_locked_first_party_manifest']=manifest
        shell('mkdir','-p',PROFILE+'/../addons')
        for name in FIRST_PARTY: adb('push',fixture/name,PROFILE+'/../addons/'+name)
        # Exercise TEST2's physical failure inside the real protected Python
        # interpreter. This extra script exists only in this disposable data
        # tree; the signed APK and approved first-party sources are unchanged.
        readonly=fixture/READONLY_FIXTURE;readonly.mkdir()
        (readonly/'addon.xml').write_text('<addon id="'+READONLY_FIXTURE+'" name="Readonly maps regression" version="1.0.0" provider-name="Infinity internal test"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable read-only input regression</summary><description lang="en_GB">Internal emulator test fixture</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        script=Path(__file__).with_name('readonly_maps_fixture.py')
        shutil.copyfile(script,readonly/'default.py')
        report['readonly_maps_fixture_sha256']=hashlib.sha256(script.read_bytes()).hexdigest()
        adb('push',readonly,PROFILE+'/../addons/'+READONLY_FIXTURE)
        shutil.rmtree(fixture)
        # Root adbd labels /sdcard pushes as storage_file, which a normal app
        # cannot read through Android's direct app-data mount. Restore platform
        # labels using the actual backing path, without changing SELinux policy
        # or enforcement. This is restricted to the new disposable fixture.
        backing='/data/media/0/Android/data/'+PACKAGE
        shell('test','-d',backing)
        shell('chown','-R',uid+':'+uid,backing)
        shell('restorecon','-RF',backing)
        shell('restorecon','-RF',PRIVATE+'/shared_prefs')
        report['selinux_enforcement']=shell('getenforce').strip()
        assert report['selinux_enforcement']=='Enforcing'
        (args.out/'fixture-labels.txt').write_text(shell('ls','-lZR',backing,PRIVATE+'/shared_prefs'))
        adb('logcat','-c')
        # Use the unchanged launcher route and an ordinary saved preference.
        report['launch']=shell('am','start','-W','-n',PACKAGE+'/.Splash')
        report['actual_first_party_enabled']=enable_first_party(args.out);save()
        owner=wait_ready();report['old_owner']=owner;report['before_close_processes']=processes();save()
        details=rpc('Addons.GetAddonDetails',{'addonid':READONLY_FIXTURE,'properties':['enabled']})['addon']
        if not details['enabled']:
            assert rpc('Addons.SetAddonEnabled',{'addonid':READONLY_FIXTURE,'enabled':True})=='OK'
        assert rpc('Addons.ExecuteAddon',{'addonid':READONLY_FIXTURE,'wait':True})=='OK'
        # The RPC acknowledgement does not prove interpreter completion.
        deadline=time.monotonic()+30;observation={}
        while time.monotonic()<deadline:
            observation=read_json(READONLY_RESULT)
            if observation.get('pid')==owner['pid'] and observation.get('read_flush_close_completed') is True:break
            time.sleep(.25)
        report['readonly_virtual_file_observation']=observation;save()
        assert observation.get('pid')==owner['pid'] and observation.get('addon')==READONLY_FIXTURE
        assert observation.get('flags',-1)&3==0 and observation.get('writable') is False
        assert observation.get('descriptor_target')=='/proc/'+str(owner['pid'])+'/maps'
        assert observation.get('regular_file') is True and observation.get('inode',0)>0
        assert observation.get('proc_mount_types')==['proc']
        assert observation.get('read_succeeded') is True and observation.get('read_flush_close_completed') is True
        report['readonly_virtual_file_read_close_verified']=True;save()
        system_executable_evidence(owner, args.out)
        baseline=ET.fromstring(shell('cat',PROFILE+'/favourites.xml'))
        assert any(item.get('name')==FAVOURITE for item in baseline),'Startup did not retain seeded test favourite; close not attempted'
        # Same private bridge and action used by Power -> Close. Root exists
        # only for test access; native PID/UUID/generation/receipt checks run.
        # This bridge finishes immediately and may hand off without drawing a
        # frame. am -W waits for activity presentation, not a shutdown receipt.
        report['close_request']=shell('am','start','-n',PACKAGE+'/.InfinityPowerControlActivity',
                                      '-a',PACKAGE+'.action.CLOSE_KODI')
        receipt={};deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            receipt=read_json(PRIVATE+'/files/infinity-checkpoint-close.json')
            if receipt.get('owner')==owner['owner'] and receipt.get('phase') in ('COMPLETE','CHECKPOINT_FAILED'):
                break
            time.sleep(.25)
        report['close_receipt']=receipt;report['after_close_processes']=processes();save()
        assert receipt.get('phase')=='COMPLETE', 'Actual native/Android close failed: '+str(receipt.get('error','no terminal receipt'))
        assert receipt.get('pid')==owner['pid'] and receipt.get('owner')==owner['owner']
        assert all(receipt.get(k) is True for k in ('checkpoint_saved','authorization_consumed','process_death_confirmed'))
        assert receipt.get('exit_policy')=='essential_first_process_exit_v1'
        native=receipt['native_receipt']
        assert native['essential_writes_sealed'] and native['essential_writes_durable'] and not native['essential_write_blockers']
        assert len(native['owners'])==17 and len(native['essential_owners'])==16
        report['android_engine_death_verified']=not any(p['pid']==owner['pid'] for p in report['after_close_processes'])
        assert report['android_engine_death_verified'],'Original engine PID remains after death receipt'
        # Observe Android after the completion callback returns; never kill a
        # remaining process or turn a service-stop request into death evidence.
        for _ in range(10):
            if not processes(): break
            time.sleep(.2)
        report['remaining_package_processes']=processes()
        report['whole_package_death_verified']=not report['remaining_package_processes']
        if args.require_java_save_proof:
            final_receipt=read_json(PRIVATE+'/files/infinity-checkpoint-close.json')
            assert final_receipt.get('session')==receipt.get('session') and final_receipt.get('phase')=='COMPLETE'
            assert final_receipt.get('coordinator_termination_authorized') is True
            assert all(re.fullmatch(r'[0-9a-f-]{36}',final_receipt.get(key,'')) for key in ('engine_java_save_seal','coordinator_java_save_seal'))
            assert not final_receipt.get('engine_java_pending') and not final_receipt.get('coordinator_java_pending')
            report['close_receipt']=final_receipt;report['both_java_process_save_proofs_verified']=True
        (args.out/'services-after-close.txt').write_text(shell('dumpsys','activity','services',PACKAGE))
        adb('pull',PROFILE+'/Database',args.out/'Database')
        databases=list((args.out/'Database').glob('*.db'))
        assert databases,'No real Kodi databases available for integrity verification'
        for path in databases:
            with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as conn:
                assert conn.execute('PRAGMA integrity_check').fetchone()==('ok',),path.name
            report['kodi_databases_checked'].append(path.name)
        saved=shell('cat',PROFILE+'/favourites.xml')
        assert any(item.get('name')==FAVOURITE for item in ET.fromstring(saved))
        report['reopen_launch']=shell('am','start','-W','-n',PACKAGE+'/.Splash')
        reopened=wait_ready(owner['owner']);report['new_owner']=reopened;report['reopen_verified']=True
        restored=shell('cat',PROFILE+'/favourites.xml')
        report['favourites_preserved']=any(item.get('name')==FAVOURITE for item in ET.fromstring(restored))
        assert report['favourites_preserved'],'Essential favourite was lost on reopening'
        assert report['whole_package_death_verified'],'Engine exited, but another Infinity package process remained'
        report['passed']=True
    except Exception as error:
        report['failure']=type(error).__name__+': '+str(error)
    finally:
        save()
        for name,command in [('logcat.txt',('logcat','-d','-v','threadtime')),('services.txt',('shell','dumpsys','activity','services',PACKAGE)),
                             ('activities.txt',('shell','dumpsys','activity','activities')),('processes.txt',('shell','ps','-A'))]:
            try: (args.out/name).write_text(adb(*command,check=False))
            except Exception as error: (args.out/(name+'.error')).write_text(str(error))
        for source,name in [(PRIVATE+'/files/infinity-checkpoint-close.json','coordinator-receipt.json'),
                            (READONLY_RESULT,'observed-readonly-maps.json'),
                            (PRIVATE+'/shared_prefs/infinity_power_routes.xml','power-route-audit.xml'),
                            (PROFILE+'/addon_data/service.infinity.refresh/runtime.properties','refresh-runtime.properties'),
                            (PROFILE+'/addon_data/service.infinity.refresh/policy.properties','refresh-policy.properties'),
                            (PRIVATE+'/files/infinity-android-checkpoint.jsonl','android-checkpoint.jsonl'),
                            (PRIVATE+'/files/infinity-kodi-process.json','owner.json'),
                            (CONTROL+'/engine.json','engine.json'),
                            (CONTROL+'/compat-active.json','compat-active.json'),
                            (CONTROL+'/active.json','command-center-active.json'),
                            (CONTROL+'/participant.json','participant.json'),
                            (PROFILE+'/../temp/kodi.log','kodi.log')]:
            adb('pull',source,args.out/name,check=False)
        try: (args.out/'screen.png').write_bytes(adb('exec-out','screencap','-p',binary=True))
        except Exception: pass
    print(json.dumps({k:report[k] for k in ('passed','android_engine_death_verified','whole_package_death_verified','reopen_verified','favourites_preserved')},indent=2))
    if not report['passed']: raise SystemExit(report.get('failure','Android process probe failed'))

if __name__=='__main__': main()
