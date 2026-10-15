#!/usr/bin/env python3
"""Observe the real signed APK on a disposable Android emulator.

No production hooks, synthetic save receipts, forced shutdown, or user device.
Only fresh emulator test data is seeded. Failure evidence never authorizes APK
delivery. Engine death and whole-package death are reported independently.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess
import time
import xml.etree.ElementTree as ET

PACKAGE = 'com.projectinfinity.kodi'
PRIVATE = '/data/user/0/'+PACKAGE
PROFILE = '/sdcard/Android/data/'+PACKAGE+'/files/.kodi/userdata'
CONTROL = PROFILE+'/addon_data/script.infinity.commandcenter/.android-checkpoint'
FAVOURITE = 'Infinity essential shutdown probe'

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
    for line in shell('ps','-A','-o','PID,NAME').splitlines()[1:]:
        fields=line.split()
        if len(fields)==2 and (fields[1]==PACKAGE or fields[1].startswith(PACKAGE+':')):
            found.append({'pid':int(fields[0]),'name':fields[1]})
    return found

def wait_ready(previous_owner=None):
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        owner=read_json(PRIVATE+'/files/infinity-kodi-process.json')
        native=read_json(CONTROL+'/engine.json')
        compat=read_json(CONTROL+'/compat-active.json')
        participant=read_json(CONTROL+'/participant.json')
        if (owner.get('phase')=='RUNNING' and owner.get('owner')!=previous_owner and
            native.get('owner')==owner.get('owner') and native.get('pid')==owner.get('pid') and
            compat.get('owner')==owner.get('owner') and participant and
            any(p['pid']==owner.get('pid') and p['name']==PACKAGE+':kodi' for p in processes())):
            return owner
        time.sleep(1)
    raise RuntimeError('Actual Kodi engine and first-party startup handshakes did not become ready')

def main():
    p=argparse.ArgumentParser();p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    report={'scope':'real signed ARM64 APK on disposable Android emulator; not physical Fold acceptance',
            'passed':False,'android_engine_death_verified':False,'whole_package_death_verified':False,
            'reopen_verified':False,'favourites_preserved':False,'kodi_databases_checked':[],
            'physical_fold_accepted':False,'apk_delivery_authorized':False}
    def save(): (args.out/'ANDROID-PROCESS-PROBE.json').write_text(json.dumps(report,indent=2)+'\n')
    try:
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
        preference=args.out/'test-preference.xml'
        preference.write_text('<map><string name="default">infinity</string></map>\n')
        adb('push',preference,PRIVATE+'/shared_prefs/infinity_experience.xml')
        shell('chown','-R',uid+':'+uid,PRIVATE+'/shared_prefs')
        favourite=args.out/'test-favourites.xml'
        favourite.write_text('<favourites><favourite name="'+FAVOURITE+'">ActivateWindow(Home)</favourite></favourites>\n')
        adb('push',favourite,PROFILE+'/favourites.xml')
        adb('logcat','-c')
        # Use the unchanged launcher route and an ordinary saved preference.
        report['launch']=shell('am','start','-W','-n',PACKAGE+'/.Splash')
        owner=wait_ready();report['old_owner']=owner;report['before_close_processes']=processes();save()
        baseline=ET.fromstring(shell('cat',PROFILE+'/favourites.xml'))
        assert any(item.get('name')==FAVOURITE for item in baseline),'Startup did not retain seeded test favourite; close not attempted'
        # Same private bridge and action used by Power -> Close. Root exists
        # only for test access; native PID/UUID/generation/receipt checks run.
        report['close_request']=shell('am','start','-W','-n',PACKAGE+'/.InfinityPowerControlActivity',
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
                            (PRIVATE+'/files/infinity-android-checkpoint.jsonl','android-checkpoint.jsonl'),
                            (PROFILE+'/../temp/kodi.log','kodi.log')]:
            adb('pull',source,args.out/name,check=False)
        try: (args.out/'screen.png').write_bytes(adb('exec-out','screencap','-p',binary=True))
        except Exception: pass
    print(json.dumps({k:report[k] for k in ('passed','android_engine_death_verified','whole_package_death_verified','reopen_verified','favourites_preserved')},indent=2))
    if not report['passed']: raise SystemExit(report.get('failure','Android process probe failed'))

if __name__=='__main__': main()
