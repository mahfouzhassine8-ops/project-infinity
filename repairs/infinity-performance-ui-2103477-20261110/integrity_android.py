"""Selected signed module update and real resident checks on original signed77."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time
import traceback
from zipfile import ZipFile,ZIP_DEFLATED
import baseline as b

HERE=b.HERE;ROOT=b.ROOT;base=b.base;gui=b.gui;QA=b.QA;QP=b.QP;REMOTE=b.REMOTE

def selected():
    scope=base.load(HERE/'CANDIDATE-ANDROID-SCOPE.json')
    base.require(scope['selected_feature']=='infinity77-integrity-worker-android' and not scope['shutdown_tests'] and not scope['APK_build'],'EXACT_CORRECTION_SCOPE')
    if os.environ.get('GITHUB_ACTIONS')=='true':base.require(os.environ.get('SELECTED_FEATURE')==scope['selected_feature'],'EXACT_SELECTED_FEATURE')
    for name,wanted in scope['source_bindings'].items():base.require(base.sha(ROOT/name)==wanted,'BOUND_SOURCE:'+name)
    return scope

def admit(sdk,out):
    scope=selected();base.require(not out.exists(),'FRESH_INTAKE')
    path=b.OLD/'tracking_module_fixture.py';base.require(base.sha(path)=='af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb','UNCHANGED_INTAKE')
    spec=importlib.util.spec_from_file_location('retained_intake_only',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    files=module.download(scope['baseline_artifact'],out/'baseline')
    modules=module.download(scope['module_artifact'],out/'signed-modules')
    apk=files/'Infinity-2103477-Combined-Original-Signer.apk';base.require(base.sha(apk)==b.APK_SHA,'EXACT_SIGNED77')
    sig=base.command([sdk/'build-tools/35.0.0/apksigner','verify','--verbose','--print-certs',apk],timeout=60)
    base.require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',sig)==[b.CERT],'ORIGINAL_CERTIFICATE');(out/'SIGNATURE.txt').write_text(sig)
    root=modules/'performance-module-prepared/candidate/modules';inputs=base.load(root.parent/'INPUTS.json')
    base.require(inputs['manifest_sha256']==scope['candidate_manifest_sha256'] and inputs['authenticated_source_count']==80,'EXACT_REVIEWED80')
    actual={p.relative_to(root).as_posix():base.sha(p) for p in root.rglob('*') if p.is_file()}
    base.require({k:v for k,v in actual.items() if not k.endswith('/INFINITY-MODULES.v1.sig')}==inputs['modules'],'EXACT_STAGED_SOURCES')
    cc=root/'script.infinity.commandcenter'
    subprocess.run(['openssl','dgst','-sha256','-verify',str(ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),'-signature',str(cc/'INFINITY-MODULES.v1.sig'),str(cc/'INFINITY-MODULES.v1')],check=True,capture_output=True)
    archive=out/'signed-performance-CC78.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED) as z:
        for p in sorted(cc.rglob('*')):
            if p.is_file():z.write(p,'script.infinity.commandcenter/'+p.relative_to(cc).as_posix())
    update=dict(addon='script.infinity.commandcenter',version='0.3.5.78',archive=archive.name,sha256=base.sha(archive),path=str(archive.resolve()))
    observer=out/'performance-observer.zip'
    with ZipFile(observer,'w',ZIP_DEFLATED) as z:
        z.writestr(QA+'/addon.xml','<addon id="'+QA+'" version="1.0.0" name="Disposable performance observer" provider-name="Infinity QA"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">CI-only measurement</summary><description lang="en_GB">Not shipped</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        z.write(HERE/'integrity_observer.py',QA+'/default.py')
        for name in ('integrity_probe.py','context_batch_prototype.py'):z.write(HERE/name,QA+'/'+name)
        z.writestr(QA+'/candidate_pin.py','MANIFEST='+repr(scope['candidate_manifest_sha256'])+'\n')
    base.save(out/'INTAKE.json',dict(apk=str(apk.resolve()),sha256=b.APK_SHA,scope_sha256=base.sha(HERE/'CANDIDATE-ANDROID-SCOPE.json'),update=update,observer=dict(addon=QA,version='1.0.0',archive=observer.name,sha256=base.sha(observer)),observer_path=str(observer.resolve())))

def run(sdk,inputs,out):
    scope=selected()
    base.require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REF')=='refs/heads/work/infinity-2103477-full-performance-ui-stability-20261110','EXACT_DISPOSABLE_BRANCH')
    base.require(not out.exists(),'FRESH_RESULTS');out.mkdir(parents=True)
    report=dict(status='RUNNING',APK=2103477,CC='0.3.5.78',shutdown='NOT_SELECTED',Fold='NOT_RUN',thermal_battery='NOT_RUN',provider_playback_preservation_smoke='NOT_RUN_BY_THIS_WORKER_CASE',no_APK_build=True)
    device=reader=None
    try:
        intake=base.load(inputs/'INTAKE.json');base.require(intake['scope_sha256']==base.sha(HERE/'CANDIDATE-ANDROID-SCOPE.json'),'EXACT_INTAKE')
        device=b.Device(out,sdk);report['environment']=base.environment(device,out)
        base.require(not device.shell('pm','list','packages',base.PACKAGE).strip(),'FRESH_VM_ONLY')
        base.root_reconnect(device,out);reader=base.start_lifecycle_log(device,out)
        base.require(device.adb('install','--no-streaming',intake['apk'],timeout=300).strip().endswith('Success'),'NORMAL_INSTALL77')
        paths=device.shell('pm','path',base.PACKAGE).splitlines();base.require(len(paths)==1,'ONE_APK')
        base.require(device.shell('sha256sum',paths[0][8:],timeout=30).split()[0]==b.APK_SHA,'ACTUAL_INSTALLED77_SHA')
        device.shell('mkdir','-p',base.PROFILE,REMOTE)
        settings=out/'FRESH-FIXTURE-guisettings.xml';settings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting><setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>')
        sources=out/'FRESH-FIXTURE-sources.xml';sources.write_text('<sources><files><source><name>Disposable performance observer</name><path pathversion="1">'+REMOTE+'</path><allowsharing>false</allowsharing></source></files></sources>')
        device.adb('push',settings,base.PROFILE+'/guisettings.xml');device.adb('push',sources,base.PROFILE+'/sources.xml')
        device.adb('push',intake['observer_path'],REMOTE+intake['observer']['archive']);device.adb('push',intake['update']['path'],REMOTE+intake['update']['archive'])
        uid=device.shell('stat','-c','%u','/data/user/0/'+base.PACKAGE).strip();base.require(uid.isdigit(),'FRESH_UID')
        device.shell('chown','-R',uid+':'+uid,'/data/media/0/Android/data/'+base.PACKAGE);device.shell('restorecon','-RF','/data/media/0/Android/data/'+base.PACKAGE)
        device.adb('forward','tcp:19090','tcp:9090');report['startup']=base.start_once(device,2103477,out)
        gui.install_zip(device,intake['update'],dict(remote_zip_directory=REMOTE),out,'signed-CC78')
        gui.install_zip(device,intake['observer'],dict(remote_zip_directory=REMOTE),out,'performance-observer')
        observer=b.Observer(device,out);report['native_authenticated_CC78']=observer.ready
        device.rpc('Input.Home');until=time.monotonic()+65;states=[]
        while time.monotonic()<until:
            current=observer.call('state');states.append(current)
            if current['resident_context'] and current['resident_current_window']=='10000' and current['integrity']['BaselineIntegrityStatus'] in ('checking','ok'):break
            time.sleep(.25)
        else:raise TimeoutError('Actual updated resident readiness')
        report['resident_ready']=states
        report['home_focus']=observer.call('home-focus')
        report['worker_contracts']=observer.call('worker-contracts',timeout=85)
        report['resident_cycle']=observer.call('resident-cycle',timeout=55)
        report['loading']=[observer.call('loading',outcome=outcome) for outcome in ('ready','failed')]
        base.require(all(r['local_owner_measurement']=='OBSERVED_MATCHING_TOKEN' for r in report['loading']),'REAL_RESIDENT_LOADING_PUBLICATION')
        report['home_focus_scene']=b.scene(device,out,'candidate-home-focus',['Input.Right']*8+['Input.Left']*8)
        report['hub']=observer.call('hub');report['hub_focus_scene']=b.scene(device,out,'candidate-hub-focus',['Input.Down']*5+['Input.Up']*5)
        device.rpc('Input.Back');device.rpc('Input.Home')
        before=device.pid;report['foreground_gate_before']=observer.call('gate');device.shell('input','keyevent','3');time.sleep(1)
        report['background_gate']=observer.call('gate',timeout=8)
        base.require(report['background_gate']['allowed'] is False,'EXISTING_NATIVE_GATE_FALSE_IN_BACKGROUND')
        begun=time.monotonic();device.shell('am','start','-W','-n',base.PACKAGE+'/.Main',timeout=30);device.alive()
        report['foreground_return']=dict(same_pid=device.pid==before,command_return_ms=1000*(time.monotonic()-begun),not_first_frame=True)
        report['foreground_gate_after']=observer.call('gate')
        base.require(report['foreground_gate_after']['allowed'] is True,'EXISTING_NATIVE_GATE_TRUE_AFTER_RETURN')
        report['final_state']=observer.call('state');report['observer_finished']=observer.call('finish')
        base.save(out/'memory-final.json',b.query(device,'dumpsys','meminfo',str(device.pid),timeout=12))
        device.screenshot('final-home');base.crash_free_alive(device)
        report['status']='PASS_SELECTED_AUTHENTICATED_ANDROID_WORKER_AND_RESIDENT_CASE_NOT_RELEASE_OR_FOLD_ACCEPTANCE'
    except Exception:
        report.update(status='FAILED_OR_BLOCKED_SELECTED_CANDIDATE',error=traceback.format_exc())
        if device:
            try:base.capture_failure(device,out)
            except Exception as e:report['capture_error']=type(e).__name__
        raise
    finally:
        if device:
            for source,target in [(base.HOME+'/temp/kodi.log',out/'kodi.log'),(QP,out/'observer-profile')]:
                try:device.adb('pull',source,target,timeout=15,check=False)
                except Exception as e:report.setdefault('collection_errors',[]).append(type(e).__name__)
        if reader:
            try:report['lifecycle_reader']=base.stop_lifecycle_log(reader,out)
            except Exception as e:report['reader_error']=type(e).__name__
        base.save(out/'CANDIDATE-ANDROID.json',report)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('admit','run'));p.add_argument('--sdk',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--inputs',type=Path);a=p.parse_args()
    admit(a.sdk,a.out) if a.operation=='admit' else run(a.sdk,a.inputs,a.out)
