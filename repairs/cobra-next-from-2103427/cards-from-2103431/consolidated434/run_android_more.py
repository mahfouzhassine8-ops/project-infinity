"""One finite More observation on unchanged signed433, no product APK build."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
OWNER=HERE.parents[1]
sys.path.insert(0,str(OWNER))
sys.path.insert(0,str(HERE.parent/'android-qa'))
from android_probe import adb,probe
from immediate_observer import ImmediateObserver

APK_SHA='874db7007b9fc79478844e5b37d4795d43c4c58de770c553d943734e1014b986'
SOURCE='6f6abe78fae65046e1ef475c558957eae873130f'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def run(signed,signature,driver,observer,out):
    assert not out.exists();out.mkdir(parents=True)
    apk=signed/'Infinity-2103433-Combined-Original-Signer.apk'
    receipt=json.loads((signed/'BUILD-RECEIPT.json').read_text())
    assert receipt['versionCode']==2103433 and receipt['source']==SOURCE
    assert receipt['signed_apk_sha256']==sha(apk)==APK_SHA
    verified=signature.read_text();assert 'Signer #1 certificate SHA-256 digest: '+CERT in verified
    for scheme in (1,2,3):assert re.search(r'Verified using v'+str(scheme)+r' scheme[^\r\n]*:\s*true',verified)
    scope=json.loads((HERE/'SCOPE.json').read_text());assert scope['android_more_selection']['signed_APK']==APK_SHA
    report={'scope':'UNCHANGED_SIGNED433_CARDS_FULLSCREEN_MORE_ONLY','APK_sha256':APK_SHA,
            'source':SOURCE,'physical_Fold':'NOT_RUN','Infinity':'NOT_LAUNCHED','shutdown':'NOT_RUN'}
    remote='/sdcard/cobra-fold-more-'+str(time.monotonic_ns())
    try:
        probe(apk,out/'cold-probe',APK_SHA)
        preflight=ImmediateObserver(observer/'CobraImmediateHierarchy.jar',observer/'BUILD-RECEIPT.json',out/'OS-platform-preflight')
        preflight.prepare()  # Actual OS/JAR surface only; no2s hierarchy capture.
        jar=driver/'CobraFoldMoreDriver.jar';binding=json.loads((driver/'BUILD-RECEIPT.json').read_text())
        assert sha(jar)==binding['jar_sha256']
        adb('push',str(jar),'/data/local/tmp/CobraFoldMoreDriver.jar')
        assert adb('shell','sha256sum','/data/local/tmp/CobraFoldMoreDriver.jar').split()[0]==binding['jar_sha256']
        shutil.copyfile(driver/'BUILD-RECEIPT.json',out/'DRIVER-BUILD.json')
        command=['adb','shell','CLASSPATH=/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:/data/local/tmp/CobraFoldMoreDriver.jar',
                 'ANDROID_DATA=/data/local/tmp','/system/bin/app_process','/system/bin','qa.CobraFoldMoreDriver',remote,binding['jar_sha256']]
        executed=subprocess.run(command,capture_output=True,text=True,timeout=360)
        (out/'native-driver.stdout.txt').write_text(executed.stdout)
        (out/'native-driver.stderr.txt').write_text(executed.stderr)
        report['driver_returncode']=executed.returncode
        # Public synthetic QA output only, never application private storage.
        adb('pull',remote,str(out/'native'))
        native=json.loads((out/'native/OUTCOME.json').read_text())
        report['native']=native
        assert executed.returncode==0 and native['status'].startswith('SIGNED433_BASELINE_MORE_REPRODUCED_AS_WORKING'),native
        report['status']='BASELINE_MORE_WORKS_IN_ANDROID_EMULATOR; PHYSICAL_FAILURE_NOT_REPRODUCED'
    except Exception as error:
        report['status']='BLOCKED_OR_FAILED_FOCUSED_OBSERVATION'
        report['error']=str(error)
        raise
    finally:
        for name,args in [('logcat',('logcat','-d','-v','threadtime')),
                          ('activity',('shell','dumpsys','activity','activities'))]:
            (out/(name+'.txt')).write_text(adb(*args,check=False))
        (out/'OUTCOME.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('signed','signature','driver','observer','out'):p.add_argument('--'+name,type=Path,required=True)
    run(**vars(p.parse_args()))
