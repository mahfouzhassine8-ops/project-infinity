"""One finite original435->436 install-over and selected drawer UI journey.

Uses existing informational-notice handling and size-bounded transfer. Never
clears, uninstalls, stops or closes the application or runs shutdown checks.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'release-stage')]
import android_probe435 as probe
from prepare import APK_SHA,CERT_SHA,VERSION,file_sha,save
from verify import check

def driver(phase,prepared,out,reference='none'):
    out.mkdir(parents=True,exist_ok=False);jar=prepared/'CobraDrawerDriver.jar';built=json.loads((prepared/'BUILD.json').read_text())
    assert file_sha(jar)==built['jar_sha256'] and file_sha(HERE/'CobraDrawerDriver.java')==built['source_sha256']
    probe.adb('push',str(jar),'/data/local/tmp/CobraDrawerDriver.jar');assert probe.adb('shell','sha256sum','/data/local/tmp/CobraDrawerDriver.jar').split()[0]==built['jar_sha256']
    remote='/sdcard/cobra-drawer-'+phase+'-'+str(time.monotonic_ns())
    command=['adb','shell','CLASSPATH=/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:/data/local/tmp/CobraDrawerDriver.jar','ANDROID_DATA=/data/local/tmp','/system/bin/app_process','/system/bin','qa.CobraDrawerDriver',phase,remote,built['jar_sha256'],reference]
    result=subprocess.run(command,capture_output=True,text=True,timeout=360)
    (out/'stdout.txt').write_text(result.stdout);(out/'stderr.txt').write_text(result.stderr)
    probe.adb('pull',remote,str(out/'native'),check=False,timeout=60)
    assert result.returncode==0,'Selected native driver failed; inspect preserved public UI/dump evidence before any new run'
    report=json.loads((out/'native/OUTCOME.json').read_text());assert report['phase']==phase and report['status'].startswith('NATIVE_EVENTS_CAPTURED')
    return report,remote

def run(baseline,candidate,driver_dir,sdk,out):
    assert not out.exists();out.mkdir(parents=True)
    old=baseline/'Infinity-2103435-Combined-Original-Signer.apk';apk=candidate/'Infinity-2103436-Combined-Original-Signer.apk'
    receipt=json.loads((candidate/'BUILD-RECEIPT.json').read_text());assert receipt['versionCode']==VERSION and file_sha(apk)==receipt['signed_apk_sha256']
    assert file_sha(old)==APK_SHA
    for name,path in [('435',old),('436',apk)]:
        signature=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(path)],text=True);(out/(name+'-SIGNATURE.txt')).write_text(signature)
        assert 'Signer #1 certificate SHA-256 digest: '+CERT_SHA in signature
        for scheme in [1,2,3]:assert __import__('re').search('Verified using v'+str(scheme)+r' scheme.*: true',signature)
    scope=json.loads((HERE/'SCOPE.json').read_text());assert scope['selected_before_execution']
    report=dict(scope='ONE_SIGNED436_CARDS_DRAWER_CANDIDATE_OVER_EXACT435',candidate_SHA256=receipt['signed_apk_sha256'],signed_source=receipt['source'],physical_Fold='NOT_RUN',shutdown='NOT_CHANGED_NOT_RUN',Infinity='NOT_LAUNCHED',media_contact_sheets='NOT_ACCESSED')
    try:
        probe.probe(old,out/'baseline435-first-screen',APK_SHA)
        _,reference=driver('setup',driver_dir,out/'baseline435-data-setup')
        original_uid=probe.adb('shell','pm','list','packages','-U',probe.PACKAGE).strip();assert __import__('re').fullmatch(r'package:com\.projectinfinity\.kodi uid:[0-9]+',original_uid)
        report['original_package_uid']=original_uid
        # Normal PackageManager update with the same original certificate.
        # Timeout is infrastructure I/O, unchanged from established QA; any
        # uncertain client completion requires exact installed-byte proof.
        budget=min(120,max(30,math.ceil(apk.stat().st_size/(10*1024*1024))+45));started=time.monotonic()
        try:report['install_client']=probe.adb('install','--no-incremental','-r',str(apk),timeout=budget)
        except subprocess.TimeoutExpired:report['install_client']='CLIENT_TIMEOUT; VERIFY_INSTALLED_BYTES_BEFORE_CONTINUING'
        report['installed_bytes']=probe.confirm_installed_apk(receipt['signed_apk_sha256'],budget);report['update_and_hash_seconds']=round(time.monotonic()-started,3)
        report['updated_package_uid']=probe.adb('shell','pm','list','packages','-U',probe.PACKAGE).strip();assert report['updated_package_uid']==original_uid,'Normal install-over must retain the original application UID'
        launched=probe.adb('shell','am','start','-W','-n',probe.PACKAGE+'/.InfinityLiveActivity');(out/'launch436.txt').write_text(launched)
        with ZipFile(apk) as z:native={n for n in z.namelist() if n.startswith('lib/arm64-v8a/') and n.endswith('.so')}
        report['launch_notice']=probe.acknowledge_known_notice_after_launch(launched,out/'launch436-notice',native)
        driver('verify',driver_dir,out/'candidate436-journey',reference)
        verified=check(out/'candidate436-journey/native',out/'baseline435-data-setup/native');report['verification']=verified['status']
        report['status']='PASS_EXACT_ORIGINAL_KEY_INSTALL_OVER_AND_TARGETED_NATIVE_DRAWER_JOURNEY'
    except Exception as e:
        report['status']='BLOCKED_OR_FAILED; NOT_A_PASS';report['error']=str(e);raise
    finally:
        for name,args in [('logcat',('logcat','-d','-v','threadtime')),('activities',('shell','dumpsys','activity','activities')),('memory',('shell','dumpsys','meminfo',probe.PACKAGE))]:
            (out/(name+'.txt')).write_text(probe.adb(*args,check=False))
        save(out/'OUTCOME.json',report)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['baseline','candidate','driver-dir','sdk','out']:p.add_argument('--'+n,type=Path,required=True)
    run(**vars(p.parse_args()))
