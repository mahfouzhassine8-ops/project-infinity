"""Selected original-signed install/recovery and Infinity preservation smoke only."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time
import traceback
from urllib.parse import urlsplit,parse_qs
from zipfile import ZipFile,ZIP_DEFLATED
import baseline as b

HERE=b.HERE;ROOT=b.ROOT;base=b.base;gui=b.gui;QA=b.QA;QP=b.QP;REMOTE=b.REMOTE

def selected():
    scope=base.load(HERE/'RELEASE-ANDROID-SCOPE.json')
    base.require(scope['selected_feature']=='infinity77-performance-signed-pair' and not scope['shutdown_tests'] and not scope['Cobra_tests'],'EXACT_SIGNED_PAIR_SCOPE')
    if os.environ.get('GITHUB_ACTIONS')=='true':base.require(os.environ.get('SELECTED_FEATURE')==scope['selected_feature'],'EXACT_FEATURE')
    for name,wanted in scope['source_bindings'].items():base.require(base.sha(ROOT/name)==wanted,'SOURCE_BINDING:'+name)
    return scope

def admit(sdk,out):
    scope=selected();base.require(not out.exists(),'FRESH_INPUTS')
    p=b.OLD/'tracking_module_fixture.py';base.require(base.sha(p)=='af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb','UNCHANGED_INTAKE')
    spec=importlib.util.spec_from_file_location('original_intake_only',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    rows=dict(baseline=scope['baseline_artifact'],**scope['signed_pair']);inputs={}
    for label,row in rows.items():
        path=m.download(row,out/label);version=2103477 if label=='baseline' else (2103480 if label=='candidate' else 2103481)
        apk=path/('Infinity-'+str(version)+'-Combined-Original-Signer.apk');wanted=b.APK_SHA if label=='baseline' else scope['APK_sha256'][label]
        base.require(base.sha(apk)==wanted,'EXACT_ORIGINAL_SIGNED_APK')
        sig=base.command([sdk/'build-tools/35.0.0/apksigner','verify','--verbose','--print-certs',apk],timeout=60)
        base.require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',sig)==[b.CERT],'ORIGINAL_PERMANENT_CERTIFICATE')
        for scheme in ('v1','v2','v3'):base.require(any(line.startswith('Verified using '+scheme+' scheme') and line.endswith(': true') for line in sig.splitlines()),'SIGNATURE_SCHEME:'+scheme)
        (out/(label+'-SIGNATURE.txt')).write_text(sig);inputs[label]=dict(apk=str(apk.resolve()),version=version,sha256=wanted)
        if label=='baseline':continue
        pin=scope['components'][label];archive=out/('observer-'+label+'.zip');qa_version='1.0.80' if label=='candidate' else '1.0.81'
        with ZipFile(archive,'w',ZIP_DEFLATED) as z:
            z.writestr(QA+'/addon.xml','<addon id="'+QA+'" version="'+qa_version+'" name="Disposable performance observer" provider-name="Infinity QA"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">CI-only measurement</summary><description lang="en_GB">Not shipped</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
            z.write(HERE/'release_observer.py',QA+'/default.py')
            for name in ('integrity_probe.py','context_batch_prototype.py'):z.write(HERE/name,QA+'/'+name)
            z.writestr(QA+'/candidate_pin.py','MANIFEST='+repr(pin['manifest'])+'\nVERSION='+repr(pin['CC'])+'\nSKIN='+repr(pin['skin'])+'\n')
        inputs[label]['observer']=dict(addon=QA,version=qa_version,archive=archive.name,sha256=base.sha(archive),path=str(archive.resolve()))
    base.save(out/'INTAKE.json',dict(inputs=inputs,scope_sha256=base.sha(HERE/'RELEASE-ANDROID-SCOPE.json')))

def wait_identity(observer,pin):
    rows=[];until=time.monotonic()+70
    while time.monotonic()<until:
        current=observer.call('state');rows.append(current)
        if current['resident_context'] and current['integrity']['BaselineIntegrityStatus']=='ok' and current['integrity']['BaselineCheckedFiles']=='948':return rows
        time.sleep(.25)
    raise TimeoutError('Signed APK resident full948 integrity readiness')

def navigation(device,out,label,params):
    url='plugin://script.infinity.commandcenter/?'+params
    device.rpc('GUI.ActivateWindow',dict(window='videos',parameters=[url,'return']))
    until=time.monotonic()+35;rows=[]
    expected=parse_qs(params)
    expected_category={'movies':'Infinity Movies','tv':'Infinity TV Shows'}.get(expected['action'][0])
    if expected['action']==['library']:
        expected_category=('TV Shows' if expected.get('media')==['tv'] else 'Movies')+' — '+{'progress':'Progress Shows','next':'Next Episodes','continue':'Continue Playing'}[expected['bucket'][0]]
    while time.monotonic()<until:
        names=['Container.FolderPath','Container.PluginCategory','Container.NumItems','System.CurrentWindowId']
        value=device.rpc('XBMC.GetInfoLabels',dict(labels=names));rows.append(dict(at=time.monotonic(),labels=value))
        found=parse_qs(urlsplit(value['Container.FolderPath']).query)
        current_window=device.rpc('GUI.GetProperties',dict(properties=['currentwindow']))['currentwindow']['id']
        rows[-1]['native_current_window']=current_window
        if current_window==10025 and all(found.get(k)==v for k,v in expected.items()) and value['Container.PluginCategory']==expected_category:
            if expected['action']==['library'] or int(value['Container.NumItems'] or 0)>=7:break
        time.sleep(.1)
    else:raise TimeoutError('Existing Infinity navigation: '+params)
    base.save(out/('navigation-'+label+'.json'),dict(requested=url,rows=rows,fixture_profile_not_owner_tracking_card_evidence=True))
    return rows[-1]

def run(sdk,inputs,out):
    scope=selected();base.require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REF')=='refs/heads/work/infinity-2103477-full-performance-ui-stability-20261110','DISPOSABLE_SELECTED_BRANCH')
    base.require(not out.exists(),'FRESH_RESULTS');out.mkdir(parents=True)
    report=dict(status='RUNNING',shutdown='NOT_SELECTED',Cobra_tests=False,Fold='NOT_RUN',provider_online_playback='NOT_RUN_THIS_CASE_IS_LOCAL_MEDIA_SMOKE',physical_Hz_thermal_battery='NOT_RUN',uninstall_reset_or_data_clear=False)
    device=reader=None
    try:
        admitted=base.load(inputs/'INTAKE.json');base.require(admitted['scope_sha256']==base.sha(HERE/'RELEASE-ANDROID-SCOPE.json'),'EXACT_INTAKE')
        device=b.Device(out,sdk);report['environment']=base.environment(device,out);base.require(not device.shell('pm','list','packages',base.PACKAGE).strip(),'FRESH_VM_ONLY')
        base.root_reconnect(device,out);reader=base.start_lifecycle_log(device,out)
        row=admitted['inputs']['baseline'];base.require(device.adb('install','--no-streaming',row['apk'],timeout=300).strip().endswith('Success'),'NORMAL_BASELINE_INSTALL')
        device.shell('mkdir','-p',base.PROFILE,REMOTE,QP)
        settings=out/'FRESH-FIXTURE-guisettings.xml';settings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting><setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>')
        sources=out/'FRESH-FIXTURE-sources.xml';sources.write_text('<sources><files><source><name>Disposable performance observer</name><path pathversion="1">'+REMOTE+'</path><allowsharing>false</allowsharing></source></files></sources>')
        sentinel=out/'preservation-sentinel.txt';sentinel.write_text('Performance QA retained-data sentinel. Not account or database data.\n');sentinel_sha=base.sha(sentinel)
        device.adb('push',settings,base.PROFILE+'/guisettings.xml');device.adb('push',sources,base.PROFILE+'/sources.xml');device.adb('push',sentinel,QP+'/preservation-sentinel.txt')
        device.adb('push',HERE/'qa-fixtures/synthetic24.mp4',REMOTE+'synthetic24.mp4')
        for label in ('candidate','recovery'):
            q=admitted['inputs'][label]['observer'];device.adb('push',q['path'],REMOTE+q['archive'])
        uid=device.shell('stat','-c','%u','/data/user/0/'+base.PACKAGE).strip();base.require(uid.isdigit(),'FRESH_UID')
        device.shell('chown','-R',uid+':'+uid,'/data/media/0/Android/data/'+base.PACKAGE);device.shell('restorecon','-RF','/data/media/0/Android/data/'+base.PACKAGE)
        device.adb('forward','tcp:19090','tcp:9090');report['baseline_setup_not_repeated_acceptance']=base.start_once(device,2103477,out)
        report['stages']={}
        for label in ('candidate','recovery'):
            row=admitted['inputs'][label];stage={}
            stage_out=out/label;stage_out.mkdir()
            stage['install']=device.adb('install','-r','--no-streaming',row['apk'],timeout=300)
            base.require(stage['install'].strip().endswith('Success'),'ORIGINAL_SIGNED_IN_PLACE_'+label.upper())
            path=device.shell('pm','path',base.PACKAGE).splitlines();base.require(len(path)==1,'ONE_PACKAGE_APK')
            stage['installed_sha256']=device.shell('sha256sum',path[0][8:],timeout=30).split()[0];base.require(stage['installed_sha256']==row['sha256'],'ACTUAL_INSTALLED_SIGNED_BYTES')
            stage['retained_sentinel_sha256']=device.shell('sha256sum',QP+'/preservation-sentinel.txt').split()[0];base.require(stage['retained_sentinel_sha256']==sentinel_sha,'USERDATA_SENTINEL_RETAINED')
            stage['startup']=base.start_once(device,row['version'],out)
            gui.install_zip(device,row['observer'],dict(remote_zip_directory=REMOTE),out,label+'-observer')
            # Reset only this disposable observer's protocol slots, retaining its data sentinel.
            for protocol,value in [('request.json',dict(pid=device.pid,sequence=0,action='state')),('ready.json',dict(pid=0,qa=QA))]:
                temporary=stage_out/protocol;base.save(temporary,value);device.adb('push',temporary,QP+'/'+protocol+'.pending');device.shell('mv',QP+'/'+protocol+'.pending',QP+'/'+protocol)
            observer=b.Observer(device,stage_out);stage['authenticated_native_module_identity']=observer.ready
            base.require(observer.ready['manifest']==scope['components'][label]['manifest'] and observer.ready['files']==80,'COMPLETE80_NATIVE_AUTHENTICATION')
            device.rpc('Input.Home');stage['resident_ready']=wait_identity(observer,scope['components'][label]);stage['hub']=observer.call('hub');device.rpc('Input.Back');device.rpc('Input.Home')
            if label=='candidate':
                stage['provider_availability']=observer.call('provider-availability')
                stage['playback_smoke']=observer.call('playback-smoke',timeout=75)
                base.require(stage['playback_smoke']['complete_integrity_cycle_during_video'],'ACTUAL_VIDEO_WITH_COMPLETE_PERIODIC_CHECK')
                device.rpc('Input.Home');stage['search_interface']=observer.call('search-open',timeout=40);device.rpc('Input.Back');device.rpc('Input.Home')
                stage['navigation']={}
                for name,query in [('movies','action=movies'),('tv','action=tv'),('progress','action=library&media=tv&bucket=progress'),('next','action=library&media=tv&bucket=next'),('continue','action=library&media=movie&bucket=continue')]:stage['navigation'][name]=navigation(device,out,name,query)
                device.rpc('Input.Home')
            stage['finished']=observer.call('finish');base.crash_free_alive(device)
            report['stages'][label]=stage
        report['status']='PASS_SELECTED_ORIGINAL_SIGNED_UPGRADE_FORWARD_RECOVERY_AND_INFINITY_SMOKE_NOT_FOLD_ACCEPTANCE'
    except Exception:
        report.update(status='FAILED_OR_BLOCKED_SIGNED_PAIR_CASE',error=traceback.format_exc())
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
        base.save(out/'SIGNED-PAIR-ANDROID.json',report)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('admit','run'));p.add_argument('--sdk',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--inputs',type=Path);a=p.parse_args()
    admit(a.sdk,a.out) if a.operation=='admit' else run(a.sdk,a.inputs,a.out)
