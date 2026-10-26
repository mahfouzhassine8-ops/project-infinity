"""Explicit one-shot real TV scene before independently authorized Power Close.

This script fixture has no service extension. It never executes on reopening,
imports a first-party writer, or changes the shipped APK.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

import native_tv_fixture
import readonly_resume_observer

ADDON='script.future.resumedurability.7fa29'
SCRIPT='''import json,os,time,traceback
from pathlib import Path
from types import SimpleNamespace
import xbmc,xbmcaddon,xbmcvfs
from readonly_resume_view import entries
from native_tv_observer import run

own=Path(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
request=json.loads((own/'request.json').read_text())
profile=Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('profile')))
owner=json.loads((profile/'.android-checkpoint/active.json').read_text())
if (request.get('pid')!=os.getpid() or request.get('owner')!=owner.get('owner') or
    owner.get('pid')!=os.getpid() or owner.get('status')!='ACTIVE' or
    len(request.get('nonce',''))!=32):raise RuntimeError('Exact live host admission required')
output=own/('result-'+request['nonce']+'.json')
if output.exists():raise RuntimeError('One-shot admission already consumed')
result=dict(passed=False,pid=os.getpid(),owner=owner['owner'],nonce=request['nonce'],cases=[])
def require(value,message):
    if not value:raise AssertionError(message)
def rpc(method,params=None):
    call=dict(jsonrpc='2.0',id=731,method=method)
    if params is not None:call['params']=params
    response=json.loads(xbmc.executeJSONRPC(json.dumps(call)))
    if 'error' in response:raise RuntimeError(method+': '+json.dumps(response['error']))
    return response.get('result')
def until(fn,message,seconds):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if xbmc.Monitor().abortRequested():raise RuntimeError('Shutdown during '+message)
        value=fn()
        if value:return value
        xbmc.sleep(100)
    raise RuntimeError('Timed out: '+message)
def load_view(path):
    file=Path(path)/'continue-watching.json'
    if file.is_symlink() or file.stat().st_size>8*1024*1024:raise RuntimeError('Invalid observation')
    value=json.loads(file.read_text())
    if not isinstance(value,dict):raise RuntimeError('Invalid state')
    return value
try:
    run(SimpleNamespace(require=require,rpc=rpc,until=until),SimpleNamespace(load_view=load_view,entries=entries),profile,result)
    result['passed']=True
except BaseException as error:
    result['failure']=type(error).__name__+': '+str(error)
    result['traceback']=traceback.format_exc()
finally:output.write_text(json.dumps(result))
'''


def stage(folder,args,report,device,aid):
    from android17_candidate_probe import require_disposable
    require_disposable(device)
    if args.case!='final-participant' or aid!='service.future.persistence.7fa29' or Path(folder).resolve()!=args.out.resolve()/'fixture':
        raise ValueError('Exact independent participant fixture required')
    receipt=json.loads((args.out/'INSTALL-OVER-EVIDENCE.json').read_text())
    if receipt.get('baseline_launched') is not False or receipt.get('uninstall_or_data_clear') is not False or device.running_engine():
        raise ValueError('Existing live data refused')
    clip=args.out/'final-profile/infinity-final-qa.mp4'
    if clip.exists() or clip.is_symlink():raise ValueError('Existing clip refused')
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=gray:s=64x64:r=24','-t','180',
                    '-an','-c:v','libx264','-g','24','-keyint_min','24','-sc_threshold','0','-pix_fmt','yuv420p',str(clip)],check=True)
    report['generated_clip_format']=dict(fps=24,duration_seconds=180,keyframe_interval=24,
        sha256=hashlib.sha256(clip.read_bytes()).hexdigest(),actual_generated_test_media=True,APK_changed=False)
    from candidate_request import EXPECTED
    native_tv_fixture.stage(device,args,report,dict(EXPECTED,verify_tv_completion=True),allow_participant=True)
    target=device.PROFILE+'/infinity-final-qa.mp4'
    device.shell('test','!','-e',target);device.shell('test','!','-L',target)
    device.adb('push',clip,target)
    if hashlib.sha256(device.adb('exec-out','cat',target,binary=True)).hexdigest()!=report['generated_clip_format']['sha256']:
        raise ValueError('Actual movie clip readback differs')
    addon=Path(folder)/ADDON
    if addon.exists() or addon.is_symlink():raise ValueError('Existing scene refused')
    addon.mkdir()
    (addon/'addon.xml').write_text('<addon id="'+ADDON+'" name="Disposable real resume durability" version="1.0.0" provider-name="Disposable CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Explicit real TV scene before independent Close</summary><description lang="en_GB">Disposable API37 fixture only</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    (addon/'default.py').write_text(SCRIPT)
    shutil.copyfile(Path(__file__).with_name('native_tv_observer.py'),addon/'native_tv_observer.py')
    report['resume_durability_fixture']=dict(addon=ADDON,automatically_started=False,
        read_only_projection=readonly_resume_observer.stage(args.apk,EXPECTED['candidate_apk_sha256'],addon))


def enable(device,out):
    detail=device.rpc('Addons.GetAddonDetails',{'addonid':ADDON,'properties':['version','enabled']})['addon']
    if detail.get('version')!='1.0.0':raise ValueError('Unexpected one-shot scene')
    if not detail.get('enabled') and device.rpc('Addons.SetAddonEnabled',{'addonid':ADDON,'enabled':True})!='OK':
        raise ValueError('Cannot enable one-shot scene')


def run(transport,owner,out):
    out=Path(out);nonce=uuid.uuid4().hex
    profile=transport.PROFILE+'/addon_data/'+ADDON
    request=dict(pid=owner['pid'],owner=owner['owner'],nonce=nonce)
    local=out/'resume-scene-admission.json';local.write_text(json.dumps(request))
    transport.shell('mkdir','-p',profile)
    transport.adb('push',local,profile+'/request.json')
    transport.rpc('Addons.ExecuteAddon',{'addonid':ADDON,'wait':False})
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        value=transport.read_json(profile+'/result-'+nonce+'.json')
        if value.get('nonce')==nonce:
            (out/'REAL-TV-BEFORE-CLOSE.json').write_text(json.dumps(value,indent=2)+'\n')
            if not(value.get('passed') is True and value.get('pid')==owner['pid'] and value.get('owner')==owner['owner']):
                raise AssertionError('Actual native TV scene failed: '+str(value.get('failure')))
            # Observe the natural final stop callback settling before snapshot.
            prior=None;stable_since=time.monotonic();settle=time.monotonic()+15
            while time.monotonic()<settle:
                state=transport.read_json(transport.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json')
                if state!=prior:prior=state;stable_since=time.monotonic()
                if time.monotonic()-stable_since>=2:return value
                time.sleep(.25)
            raise AssertionError('Final stopped playback records did not settle')
        time.sleep(.25)
    raise AssertionError('Actual native TV scene did not complete')


def reopened(transport,before):
    if transport.rpc('Player.GetActivePlayers'):raise AssertionError('Reopened Home must not autoplay')
    rows=transport.rpc('Files.GetDirectory',{'directory':'plugin://script.infinity.commandcenter/?action=library&media=tv&bucket=next',
        'media':'video','properties':['season','episode','resume']})['files']
    if not(len(rows)==1 and rows[0].get('season')==2 and rows[0].get('episode')==1 and
           'action=play-local-next' in rows[0].get('file','')):
        raise AssertionError('Reopened local Next is not the verified S2E1')
    detail=transport.rpc('VideoLibrary.GetEpisodeDetails',{'episodeid':2,'properties':['season','episode','tvshowid','file']})['episodedetails']
    if (detail.get('tvshowid'),detail.get('season'),detail.get('episode'),detail.get('file'))!=(1,2,1,native_tv_fixture.FOLDER+'QA.S02E01.mp4'):
        raise AssertionError('Reopened native source identity differs')
    return dict(passed=True,autoplay=False,next_rows=rows,native_source=detail,
        completed_watched=before['watched']['d'*64],actual_playback_not_seed_only=True)
