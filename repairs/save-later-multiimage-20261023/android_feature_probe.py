"""Execute exactly one selected feature on a fresh API37 emulator.

No Normal Close, Essential-First, durability assertions, service retirement or reopen.
The app is left running; runner teardown is infrastructure, not a shutdown test.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import traceback
from zipfile import ZipFile

import android_feature_device as device
import android_probe as staging

CASES=('saved-navigation','provider-pov','provider-umbrella','provider-seren','provider-future','multiimage','tracking-recovery','tracking-actions','tracking-continue','final-participant','final-continue','final-actions','final-pov')
COMPONENTS=('script.infinity.commandcenter','script.infinity.uirepair','script.infinity.watchedbridge')

def execute(args):
    if args.case not in CASES or not args.authorization.strip():
        raise ValueError('An explicit feature and user-authorized correction are required')
    args.out.mkdir(parents=True,exist_ok=True)
    report=dict(schema=1,scope='one selected feature; fresh Android17 emulator',
        selected_case=args.case,authorization=args.authorization,passed=False,
        candidate_build=os.environ.get('CANDIDATE_BUILD'),
        candidate_source_commit=os.environ.get('CANDIDATE_SOURCE_COMMIT'),
        test_source_commit=os.environ.get('TEST_SOURCE_COMMIT'),
        workflow_run=os.environ.get('GITHUB_RUN_ID'),
        shutdown={'status':'NOT_RUN','required_for_feature_result':False},
        physical_fold_verified=False,release_accepted=False,final_lock=False,
        app_termination_requested_by_harness=False)
    try:
        digest=hashlib.sha256(args.apk.read_bytes()).hexdigest()
        if digest!=args.expected_sha:raise RuntimeError('Signed candidate digest mismatch')
        report['apk_sha256']=digest
        device.adb('wait-for-device');device.adb('root');device.adb('wait-for-device')
        platform={k:device.shell('getprop',v).strip() for k,v in
            [('qemu','ro.kernel.qemu'),('sdk','ro.build.version.sdk'),
             ('release','ro.build.version.release'),('abis','ro.product.cpu.abilist')]}
        report['platform']=platform
        if platform['qemu']!='1' or platform['sdk']!='37' or platform['release'].split('.')[0]!='17':
            raise RuntimeError('Fresh Android17 emulator required; physical devices refused')
        if 'arm64-v8a' not in platform['abis']:raise RuntimeError('ARM64 execution unavailable')
        if device.PACKAGE in device.shell('pm','list','packages',device.PACKAGE):
            raise RuntimeError('Existing installation refused; no user data may be replaced')
        if 'Success' not in device.adb('install','--no-incremental',args.apk):
            raise RuntimeError('Candidate installation failed')
        device.shell('input','keyevent','82')
        for permission in ('android.permission.READ_EXTERNAL_STORAGE','android.permission.WRITE_EXTERNAL_STORAGE'):
            device.shell('pm','grant',device.PACKAGE,permission,check=False)
        device.shell('appops','set',device.PACKAGE,'MANAGE_EXTERNAL_STORAGE','allow',check=False)
        uid=device.shell('stat','-c','%u',device.PRIVATE).strip()
        if not uid.isdigit():raise RuntimeError('Installed UID unavailable')
        device.shell('mkdir','-p',device.PROFILE+'/../addons',device.PRIVATE+'/shared_prefs')
        preference=args.out/'infinity_experience.xml'
        preference.write_text('<map><string name="default">infinity</string></map>')
        device.adb('push',preference,device.PRIVATE+'/shared_prefs/infinity_experience.xml')
        settings=args.out/'guisettings.xml'
        settings.write_text('<settings version="2"><resolutions /><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting></settings>')
        device.adb('push',settings,device.PROFILE+'/guisettings.xml')
        stage=args.out/'fixture';stage.mkdir()
        with ZipFile(args.apk) as archive:
            for member in archive.namelist():
                if member.startswith('assets/addons/') and not member.endswith('/'):
                    relative=member[len('assets/addons/'):]
                    if relative.split('/')[0] in COMPONENTS:
                        target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.read(member))
        future=stage/staging.FUTURE;(future/'resources').mkdir(parents=True)
        (future/'addon.xml').write_text('<addon id="'+staging.FUTURE+'" name="Selected feature fixture" version="1.0.0" provider-name="Disposable CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.service" library="service.py" start="startup"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Feature-only observation</summary><description lang="en_GB">No Close or persistence controls</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        (future/'resources/settings.xml').write_text('<settings><category label="Fixture"><setting id="test_mode" type="text" default="safe"/></category></settings>')
        args.mode='safe' if args.case=='saved-navigation' else 'feature-multiimage' if args.case=='multiimage' else args.case
        args.feature_only=True
        staging.runtime={'probe':device}
        if args.case.startswith('final-'):
            path=Path(__file__).resolve().parent/'tracking/final-eight/android_selected.py'
            spec=importlib.util.spec_from_file_location('final_selected_host',path)
            selected=importlib.util.module_from_spec(spec);spec.loader.exec_module(selected)
            selected.stage(stage,args,report,device,staging.FUTURE)
        else:
            staging.extra(stage,args,report)
        report['fixture_manifest']={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file()}
        for addon in stage.iterdir():device.adb('push',addon,device.PROFILE+'/../addons/'+addon.name)
        backing='/data/media/0/Android/data/'+device.PACKAGE
        device.shell('chown','-R',uid+':'+uid,backing,device.PRIVATE+'/shared_prefs')
        device.shell('restorecon','-RF',backing,device.PRIVATE+'/shared_prefs')
        if device.shell('getenforce').strip()!='Enforcing':raise RuntimeError('SELinux must remain enforcing')
        device.adb('logcat','-c')
        report['launch']=device.shell('am','start','-W','-n',device.PACKAGE+'/.Splash')
        receipt=json.loads((args.apk.parent/'CANDIDATE.json').read_text())
        device.enable_features(args.out,receipt['matching_component_versions'])
        details=device.rpc('Addons.GetAddonDetails',{'addonid':staging.FUTURE,'properties':['enabled']})['addon']
        if not details['enabled']:
            if device.rpc('Addons.SetAddonEnabled',{'addonid':staging.FUTURE,'enabled':True})!='OK':
                raise RuntimeError('Selected feature fixture not enabled')
        owner=device.until(device.running_engine,180);report['engine']=owner
        staging.admit_runtime(device,owner,args.out)
        path=device.PROFILE+'/addon_data/'+staging.FUTURE+'/navigation-ready-'+str(owner['pid'])+'.json'
        result=device.until(lambda:device.read_json(path),1800)
        report['feature_result']=result
        expected=[args.case] if args.case.startswith(('tracking-','final-')) else ['multiimage'] if args.case=='multiimage' else ['navigation']
        if result.get('selected_features')!=expected or result.get('selected_mode')!=args.mode:raise RuntimeError('Unexpected test family executed')
        if result.get('pid')!=owner['pid'] or result.get('passed') is not True:
            raise RuntimeError('Selected feature failed: '+str(result.get('failure')))
        report['passed']=True
    except Exception as error:
        report['failure']=type(error).__name__+': '+str(error)
        report['traceback']=traceback.format_exc()
    finally:
        (args.out/'FEATURE-RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
        if report.get('platform',{}).get('qemu')=='1':
            try:device.adb('pull',device.PROFILE+'/../temp/kodi.log',args.out/'kodi.log',check=False)
            except Exception:pass
            try:(args.out/'logcat.txt').write_text(device.adb('logcat','-d','-v','threadtime',check=False))
            except Exception:pass
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk',type=Path,required=True)
    parser.add_argument('--expected-sha',required=True)
    parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--authorization',required=True)
    parser.add_argument('--out',type=Path,required=True)
    result=execute(parser.parse_args())
    print(json.dumps({k:result[k] for k in ('selected_case','passed','shutdown')}))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
