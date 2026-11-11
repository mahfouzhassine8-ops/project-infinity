#!/usr/bin/env python3
"""Selected disposable API36 startup/local-Python/Health Center execution only."""
import argparse
import ast
import codecs
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time
import traceback
import uuid
from zipfile import ZipFile, ZIP_DEFLATED

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/infinity-tracking-integration-2103469-20261108'))
import qualify_android_baseline as base
import verify_tracking_android as gui
QA='script.infinity.startupqaprobe'
QP=base.PROFILE+'/addon_data/'+QA
REMOTE='/sdcard/Download/infinity-startup-qa/'
APK82='78b2a5dd878ea847f425f8bbf5b9c71e810d19e134fe4480588db55a7ea52a32'
HC_HASH='fc2cb4ce6251cd363094b43462f4d919db27268d2701e30d705fc93fbefc2f26'
SELECTION=HERE/'ANDROID-STARTUP-SELECTION.json'

def selected():
    row=base.load(SELECTION)
    assert row['feature']=='signed82-local-python-and-health-center' and row['shutdown_tests'] is False
    for name,wanted in row['helper_sha256'].items():
        assert base.sha(ROOT/name)==wanted,'RETAINED_HELPER_DRIFT:'+name
    if os.environ.get('GITHUB_ACTIONS')=='true':
        assert os.environ.get('SELECTED_FEATURE')==row['feature']
    return row

# Reuse the existing bounded feature transport, without importing/running its
# performance suite. This class authorizes only this disposable observer.
device_source=(ROOT/'repairs/infinity-performance-ui-2103477-20261110/baseline.py').read_text()
node=next(n for n in ast.parse(device_source).body if isinstance(n,ast.ClassDef) and n.name=='Device')
exec(compile(ast.Module(body=[node],type_ignores=[]),'retained-feature-transport','exec'),globals())

OBSERVER=r'''
import hashlib, json, os, time
import xbmc, xbmcaddon, xbmcgui, xbmcvfs
ROOT=xbmcvfs.translatePath('special://profile/addon_data/script.infinity.startupqaprobe/')
with open(ROOT+'request.json') as f: request=json.load(f)
with open('/proc/self/stat') as f: started=f.read().rsplit(') ',1)[1].split()[19]
assert request['pid']==os.getpid() and request['process_start']==started
result=dict(nonce=request['nonce'],sequence=request['sequence'],pid=os.getpid(),process_start=started,
            action=request['action'],python_body_entered=True,passed=False)
def save():
    with open(ROOT+'reply.pending','w') as f: json.dump(result,f)
    os.replace(ROOT+'reply.pending',ROOT+'reply.json')
if request['action']=='controlled-body-error':
    marker='startup_qa_body_error_'+request['nonce']
    result['controlled_error']=marker;save()
    raise RuntimeError(marker)
elif request['action']=='health-center':
    path=xbmcvfs.translatePath(xbmcaddon.Addon('script.kodihealthcenter').getAddonInfo('path'))
    with open(os.path.join(path,'default.py'),'rb') as f: actual=hashlib.sha256(f.read()).hexdigest()
    assert actual=='fc2cb4ce6251cd363094b43462f4d919db27268d2701e30d705fc93fbefc2f26'
    assert not xbmc.getCondVisibility('Window.IsVisible(1188)')
    result.update(health_window_initially_absent=True,health_source_sha256=actual)
    xbmc.executebuiltin('RunScript(script.kodihealthcenter)')
    deadline=time.monotonic()+40
    monitor=xbmc.Monitor()
    while time.monotonic()<deadline and not monitor.abortRequested():
        visible=xbmc.getCondVisibility('Window.IsVisible(1188)')
        version=xbmcgui.Window(10000).getProperty('KHC.Version')
        dialog=xbmcgui.getCurrentWindowDialogId()
        if visible and version=='2.5.27' and dialog==11188:
            label=xbmcgui.Window(11188).getControl(1188101).getLabel()
            assert label=='Scan Kodi'
            result.update(health_window_visible=True,health_version=version,
                          actual_dialog_id=dialog,health_control_label=label,passed=True)
            break
        monitor.waitForAbort(.1)
else:
    assert request['action']=='local-python'
    result.update(passed=True,arithmetic=sum([1,2,3]),cc_version=xbmc.getInfoLabel('System.AddonVersion(script.infinity.commandcenter)'))
save()
'''


def prepare(apk,out):
    selection=selected()
    out.mkdir(parents=True,exist_ok=False)
    assert base.sha(apk)==APK82,'UNVERIFIED_BASELINE82'
    with ZipFile(apk) as z:assert hashlib.sha256(z.read('assets/addons/script.kodihealthcenter/default.py')).hexdigest()==HC_HASH
    archive=out/'startup-observer.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED) as z:
        z.writestr(QA+'/addon.xml','<addon id="'+QA+'" version="1.0.0" name="Internal Startup QA" provider-name="Infinity QA"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable engineering probe</summary><description lang="en_GB">Not shipped</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        z.writestr(QA+'/default.py',OBSERVER)
    base.save(out/'INTAKE.json',dict(apk=str(apk.resolve()),sha256=APK82,versionCode=2103482,
        selection_sha256=base.sha(SELECTION),helper_sha256=selection['helper_sha256'],
        health_source_sha256=HC_HASH,observer=dict(addon=QA,version='1.0.0',archive=archive.name,sha256=base.sha(archive))))


def run(sdk,inputs,out):
    selection=selected()
    assert os.environ.get('GITHUB_ACTIONS')=='true'
    assert os.environ.get('GITHUB_REF')=='refs/heads/work/infinity-2103482-functional-startup-20261111'
    out.mkdir(parents=True,exist_ok=False);proof=base.load(inputs/'INTAKE.json')
    assert base.sha(Path(proof['apk']))==proof['sha256']==APK82
    assert proof['selection_sha256']==base.sha(SELECTION) and proof['helper_sha256']==selection['helper_sha256']
    assert base.sha(inputs/proof['observer']['archive'])==proof['observer']['sha256']
    report=dict(status='RUNNING',owner_device=False,Cobra_executed=False,shutdown='NOT_RUN',
                profile='NEW_DISPOSABLE_EMULATOR_ONLY',baseline_apk=proof['sha256'],cases=[],
                startup_repair_accepted=False,fold_failure_reproduced=False)
    device=None;reader=None
    def checkpoint():base.save(out/'FUNCTIONAL-STARTUP-ANDROID.json',report)
    try:
        device=Device(out,sdk);report['environment']=base.environment(device,out)
        base.require(not device.shell('pm','list','packages',base.PACKAGE).strip(),'FRESH_VM_REQUIRED')
        base.root_reconnect(device,out);reader=base.start_lifecycle_log(device,out)
        base.require(device.adb('install','--no-streaming',proof['apk'],timeout=300).strip().endswith('Success'),'ORIGINAL_SIGNED_INSTALL')
        device.shell('mkdir','-p',base.PROFILE,REMOTE,QP)
        settings=out/'NEW-FIXTURE-guisettings.xml';settings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting><setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>')
        sources=out/'NEW-FIXTURE-sources.xml';sources.write_text('<sources><files><source><name>Internal Startup QA</name><path pathversion="1">'+REMOTE+'</path><allowsharing>false</allowsharing></source></files></sources>')
        device.adb('push',settings,base.PROFILE+'/guisettings.xml');device.adb('push',sources,base.PROFILE+'/sources.xml')
        device.adb('push',inputs/proof['observer']['archive'],REMOTE+proof['observer']['archive'])
        uid=device.shell('stat','-c','%u','/data/user/0/'+base.PACKAGE).strip();base.require(uid.isdigit(),'FRESH_VM_UID')
        device.shell('chown','-R',uid+':'+uid,'/data/media/0/Android/data/'+base.PACKAGE)
        device.shell('restorecon','-RF','/data/media/0/Android/data/'+base.PACKAGE)
        device.adb('forward','tcp:19090','tcp:9090')
        report['startup']=base.start_once(device,1,out);checkpoint()
        installed=device.shell('pm','path',base.PACKAGE).strip().removeprefix('package:')
        base.require(device.shell('sha256sum',installed).split()[0]==APK82,'ACTUAL_INSTALLED_APK_HASH')
        gui.install_zip(device,proof['observer'],dict(remote_zip_directory=REMOTE),out,'startup-observer')
        nonce=uuid.uuid4().hex
        for sequence,action in enumerate(['local-python','controlled-body-error','local-python','health-center','local-python'],1):
            request=dict(pid=device.pid,process_start=device.start_time,nonce=nonce,sequence=sequence,action=action)
            local=out/'request.json';base.save(local,request);device.adb('push',local,QP+'/request.pending');device.shell('mv',QP+'/request.pending',QP+'/request.json')
            device.rpc('Addons.ExecuteAddon',dict(addonid=QA));deadline=time.monotonic()+55;reply=None
            while time.monotonic()<deadline:
                device.alive()
                raw=device.shell('head','-c','65536',QP+'/reply.json',check=False)
                try:r=json.loads(raw)
                except ValueError:r={}
                if all(r.get(k)==request[k] for k in ('pid','process_start','nonce','sequence','action')):reply=r;break
                time.sleep(.2)
            base.require(reply is not None,'ACTUAL_PYTHON_REPLY_'+action)
            report['cases'].append(reply);checkpoint()
            if action=='controlled-body-error':
                marker='startup_qa_body_error_'+nonce
                base.require(reply.get('controlled_error')==marker and not reply['passed'],'CONTROLLED_ERROR_BODY_ENTERED')
                deadline=time.monotonic()+15
                while time.monotonic()<deadline:
                    device.alive()
                    raw=device.shell('tail','-c','1048576',base.HOME+'/temp/kodi.log',check=False)
                    if 'RuntimeError: '+marker in raw:
                        reply['actual_traceback_observed']=True;checkpoint();break
                    time.sleep(.2)
                else:raise TimeoutError('CONTROLLED_EXCEPTION_NOT_REPORTED')
            else:base.require(reply['passed'],'PYTHON_FUNCTIONAL_'+action)
            if action=='health-center':
                device.screenshot('actual-python-health-center');device.rpc('Input.Back');device.rpc('Input.Home')
        base.crash_free_alive(device)
        report['status']='PASS_SELECTED_BASELINE_LOCAL_PYTHON_AND_HEALTH_CENTER_NOT_FOLD_REPRODUCTION'
    except Exception:
        report.update(status='BLOCKED_OR_FAILED_SELECTED_CASE',error=traceback.format_exc())
        if device:
            try:base.capture_failure(device,out)
            except Exception as e:report['capture_error']=type(e).__name__
        raise
    finally:
        if device:
            try:device.adb('pull',base.HOME+'/temp/kodi.log',out/'kodi.log',timeout=15,check=False)
            except Exception as e:report['log_collection_error']=type(e).__name__
        if reader:
            try:report['lifecycle_reader']=base.stop_lifecycle_log(reader,out)
            except Exception as e:report['lifecycle_collection_error']=type(e).__name__
        checkpoint()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','run']);p.add_argument('--apk',type=Path);p.add_argument('--sdk',type=Path);p.add_argument('--inputs',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    prepare(a.apk,a.out) if a.operation=='prepare' else run(a.sdk,a.inputs,a.out)
