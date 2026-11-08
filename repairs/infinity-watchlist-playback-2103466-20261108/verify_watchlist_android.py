"""Selected Watchlist journey only. Retained transport class; no old journey/main."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import traceback
from urllib.parse import urlsplit, parse_qs
from zipfile import ZipFile
from android_watchlist_common import HERE, CC, PACKAGE, HOME, PROFILE, device_class, sha
from watchlist_fixture_server import generate_clip, start


def require(value, message):
    if not value:raise AssertionError(message)


def seconds(value):
    return sum(value.get(k,0)*scale for k,scale in (('hours',3600),('minutes',60),('seconds',1),('milliseconds',.001)))


def manifest(apk):
    with ZipFile(apk) as z:
        source=z.read('assets/addons/'+CC+'/INFINITY-MODULES.v1').decode()
        return {f[2]:f[1] for line in source.splitlines() if (f:=line.split('\t'))[0]=='file'}


def run(baseline,candidate,recovery,fixture,out,port):
    require(not out.exists(),'Fresh evidence directory required');out.mkdir(parents=True)
    selected=json.loads((HERE/'ANDROID-REQUEST.json').read_text())
    require(selected['application_tests'] is True and selected['shutdown_tests'] is False,'Exact selected feature-only request required')
    (out/'ANDROID-REQUEST.json').write_text(json.dumps(selected,indent=2)+'\n')
    inputs=json.loads((fixture/'ANDROID-INPUTS.json').read_text())
    for version,path in ((2103466,baseline),(2103468,candidate),(2103469,recovery)):
        require(sha(path)==inputs['signed_pair'][str(version)]['sha256'],'Staged exact APK hash required')
    report=dict(status='RUNNING_SELECTED_WATCHLIST_ANDROID',cases=[],synthetic_fixture_media=True,
                real_provider_source_unmodified=True,provider_accounts=False,Fold='NOT_RUN',shutdown='NOT_SELECTED',release_acceptance=False)
    device=None;server=None
    def save(): (out/'ANDROID-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    def passed(name,**detail): report['cases'].append(dict(case=name,status='PASS',**detail));save()
    def fail_capture():
        if device is None:return
        for name,fn in (('failure-logcat.txt',lambda:device.adb('logcat','-d',timeout=45)),
                        ('failure-pids.txt',lambda:device.shell('pidof',PACKAGE+':kodi',check=False)),
                        ('failure-snapshot.json',lambda:json.dumps(device.command('snapshot',seconds=10),indent=2))):
            try:(out/name).write_text(fn())
            except BaseException as error:(out/(name+'.error')).write_text(repr(error))
        try:device.screenshot('failure')
        except BaseException:pass
    def check_identity(apk,count):
        actual=device.command('identity')
        require(actual['module_files']==manifest(apk) and actual['module_count']==count,'Complete actual authenticated module inventory mismatch')
        require(actual['skin']=='skin.infinity.diggz','Exact Infinity experience required')
        require(actual['Python_optimization']==1,'Real Kodi optimize1 observer expected')
        return actual
    def state():return device.command('state')
    def unchanged_watchlist(value):require(value['data']['watchlist']==inputs['seed']['watchlist'],'Saved Watchlist row/route/membership changed')
    def active():
        values=device.rpc('Player.GetActivePlayers')
        return next((v['playerid'] for v in values if v['type']=='video'),None)
    def properties(pid):return device.rpc('Player.GetProperties',dict(playerid=pid,properties=['time','totaltime','speed']))
    def playing(origin=True,kind='movie',tmdb='603',se=None):
        prompt_handled=False
        def observe():
            nonlocal prompt_handled
            device.alive();pid=active()
            if pid is None:
                current=device.command('snapshot',seconds=15)
                if current.get('provider_bookmark_prompt') is True and not prompt_handled:
                    device.command('provider-start-new',seconds=15);prompt_handled=True
                return None
            item=device.rpc('Player.GetItem',dict(playerid=pid,properties=['title','file','uniqueid','season','episode','showtitle']))['item']
            require(item.get('type')==kind and str(item.get('uniqueid',{}).get('tmdb'))==tmdb,'Actual typed provider identity mismatch')
            if se:require((item.get('season'),item.get('episode'))==se,'Actual exact S/E mismatch')
            receipt=item.get('infinity_watchlist_origin')
            require(bool(receipt)==origin,'Native actual-item origin mismatch')
            if origin:require(receipt['destination'].startswith('plugin://plugin.video.pov/') and receipt['selection']['bucket']=='watchlist','Actual invocation receipt missing')
            p=properties(pid)
            return (pid,item,p) if p['speed']==1 and seconds(p['totaltime'])>=200 else None
        pid,item,before=device.until(observe,'actual unmodified POV playback and native receipt',160)
        after=device.until(lambda:(p if seconds((p:=properties(pid))['time'])>seconds(before['time'])+.5 else None),'actual AV clock advances',10)
        def av_started():
            events=device.command('events')
            started=max((e['monotonic'] for e in events if e['event']=='Started'),default=0)
            return events if any(e['event']=='AVStarted' and e['monotonic']>=started for e in events) else None
        device.until(av_started,'genuine actual AVStarted callback',10)
        return pid,item,after
    def seek(pid,position):
        value=dict(hours=int(position)//3600,minutes=int(position)%3600//60,seconds=int(position)%60,milliseconds=0)
        device.rpc('Player.Seek',dict(playerid=pid,value={'time':value}))
    def wait_alive(duration):
        end=time.monotonic()+duration
        while time.monotonic()<end:device.alive();time.sleep(max(0,min(.5,end-time.monotonic())))
    def stop(pid):
        marker=max((e['monotonic'] for e in device.command('events')),default=0)
        device.rpc('Player.Stop',dict(playerid=pid));device.until(lambda:active() is None,'actual user Stop',20)
        def actual_stop():
            events=device.command('events')
            return events if any(e['event']=='Stopped' and e['monotonic']>marker for e in events) else None
        device.until(actual_stop,'genuine actual Stopped callback',10);wait_alive(2)
    def row_for(key):
        view=device.command('watchlist',seconds=120)
        return next(r for r in view['rows'] if r.get('Infinity.ResumeHub.Key')==key)
    def click(row):device.command('click',index=row['index'],file=row['file'],seconds=20)
    def menu_pick(choices):
        def find():
            view=device.command('snapshot',seconds=15)
            for button in view.get('context_buttons',[]):
                if button['label'] in choices:return dict(control=button['control'],index=0,label=button['label'],button=True)
            for control,labels in view.get('menus',{}).items():
                for index,label in enumerate(labels):
                    if label in choices:return dict(control=int(control),index=index,label=label,button=False)
            return None
        selected=device.until(find,'actual native menu '+str(choices),15)
        return device.command('menu-select',seconds=20,**selected)
    save()
    try:
        clip=out/'fixture.mp4';generate_clip(clip);server=start(clip,port,out/'AIO-HTTP.jsonl')
        report['fixture_clip_sha256']=sha(clip)
        Device=device_class();device=Device(out)
        require(not device.shell('pm','list','packages',PACKAGE).strip(),'FRESH_DISPOSABLE_EMULATOR_ONLY')
        device.install(baseline,'baseline466')
        for args in [('appops','set',PACKAGE,'MANAGE_EXTERNAL_STORAGE','allow'),('pm','grant',PACKAGE,'android.permission.RECORD_AUDIO'),('pm','grant',PACKAGE,'android.permission.POST_NOTIFICATIONS')]:device.shell(*args)
        device.shell('mkdir','-p',HOME);device.adb('push',str(fixture/'home')+'/.',HOME)
        device.adb('root');device.adb('wait-for-device')
        uid=device.shell('stat','-c','%u','/data/user/0/'+PACKAGE).strip();require(uid.isdigit() and int(uid)>=10000,'Fresh normal app UID required')
        device.shell('chown','-R',uid+':'+uid,'/data/media/0/Android/data/'+PACKAGE);device.shell('restorecon','-RF','/data/media/0/Android/data/'+PACKAGE)
        device.enter('baseline466')
        for aid in [r['addon'] for r in inputs['dependencies']]+['plugin.video.pov']:
            if not device.rpc('Addons.GetAddonDetails',dict(addonid=aid,properties=['enabled']))['addon']['enabled']:device.rpc('Addons.SetAddonEnabled',dict(addonid=aid,enabled=True))
        device.start_qa();before=check_identity(baseline,79)
        initial=state();unchanged_watchlist(initial);require(not initial['data']['items'] and not initial['data']['watched'],'Seed must never create progress/watched')
        sentinel=device.shell('cat',PROFILE+'/watchlist-profile-sentinel.txt')
        passed('original466_authenticated79_and_two_saved_rows_only',identity=before)
        device.install(candidate,'candidate468');device.enter('candidate468');device.start_qa()
        passed('signed_install_over_466_to468_authenticated80',identity=check_identity(candidate,80))
        require(device.shell('cat',PROFILE+'/watchlist-profile-sentinel.txt')==sentinel,'Existing sentinel changed')
        device.command('configure',port=port,base='http://10.0.2.2:'+str(port));device.command('initialize',seconds=960)
        movie=next(r for r in inputs['seed']['watchlist'].values() if r['media']=='movie');show=next(r for r in inputs['seed']['watchlist'].values() if r['media']=='tv')
        click(row_for(movie['key']));pid,item,clock=playing();seek(pid,60);wait_alive(8);stop(pid)
        partial=device.until(lambda:(s if (s:=state())['data']['items'].get(movie['key'],{}).get('position',0)>=55 else None),'real existing writer saves partial movie',30)
        unchanged_watchlist(partial);require(movie['key'] not in partial['data']['watched'],'Partial movie incorrectly completed')
        passed('native_Watchlist_movie_actual_POV_fresh_item_partial_and_saved_row_immutable',item=item,state=partial)
        offset=partial['data']['items'][movie['key']]['position']
        click(row_for(movie['key']));pid,item,clock=playing();current=seconds(properties(pid)['time'])
        require(offset-3<=current<=offset+15,'Fresh direct Watchlist resume offset was not applied');stop(pid)
        passed('fresh_direct_Watchlist_movie_resume',expected=offset,actual=current,item=item)
        selected=row_for(movie['key']);device.command('popup-open',index=selected['index'],file=selected['file'])
        menu_pick(('Title options',));menu_pick(('Resume','Play'));pid,item,clock=playing();stop(pid)
        passed('actual_native_saved_title_popup_Play',item=item)
        click(row_for(show['key']))
        def provider_rows():
            view=device.command('snapshot',seconds=20)
            return view if view['folder'].startswith('plugin://plugin.video.pov/') and view['rows'] else None
        seasons=device.until(provider_rows,'actual POV seasons after saved show selection',120)
        season=next(r for r in seasons['rows'] if parse_qs(urlsplit(r['file']).query).get('season')==['1'])
        click(season)
        episodes=device.until(lambda:(v if (v:=provider_rows()) and any(parse_qs(urlsplit(r['file']).query).get('episode')==['1'] for r in v['rows']) else None),'actual POV S1 episode rows',120)
        episode=next(r for r in episodes['rows'] if parse_qs(urlsplit(r['file']).query).get('season')==['1'] and parse_qs(urlsplit(r['file']).query).get('episode')==['1'])
        click(episode);pid,item,clock=playing(kind='episode',tmdb='1396',se=(1,1));seek(pid,60);wait_alive(8)
        tvpartial=device.until(lambda:(s if (s:=state())['progress_shows'] and s['next_episodes'] else None),'actual TV partial projections',30)
        require(tvpartial['progress_shows'][0]['episode']==1 and tvpartial['next_episodes'][0]['episode']==1,'Unfinished Next must retain exact S1E1')
        unchanged_watchlist(tvpartial);passed('native_cached_descendant_TV_identity_partial_ProgressShows_unfinishedNext',item=item,state=tvpartial)
        before_end=device.command('events')
        end_marker=max((event['monotonic'] for event in before_end),default=0)
        seek(pid,202);device.until(lambda:active() is None,'actual generated clip natural Ended',30)
        def natural_end_event():
            events=device.command('events')
            return events if any(e['event']=='Ended' and e['monotonic']>end_marker for e in events) else None
        ended_events=device.until(natural_end_event,'real SDK natural Ended callback',15)
        require(not any(e['event']=='Error' and e['monotonic']>end_marker for e in ended_events),'Actual player Error during natural completion')
        def watched_once():
            current=state()
            return current if any(r.get('media')=='tv' and r.get('play_count')==1 for r in current['data']['watched'].values()) else None
        completed=device.until(watched_once,'actual onEnded watched once',30)
        require(not any(r.get('synthetic_next') for r in completed['next_episodes']),'Unavailable catalogue invented successor')
        unchanged_watchlist(completed);passed('TV_actual_natural_Ended_watched_once_no_invented_successor',state=completed,actual_player_events=ended_events)
        # Normal same-title URL lacks exact selected item/Launch proof. Provider bookmark UI is real.
        device.rpc('Player.Open',dict(item={'file':movie['source']}))
        pid,item,clock=playing(origin=False);require(seconds(clock['time'])<20,'Ordinary launch inherited Watchlist resume seek');stop(pid)
        passed('ordinary_same_title_provider_launch_negative_origin_and_seek',item=item,time=clock)
        persisted=state();require(active() is None,'Explicit persistence restart requires saved Stop')
        device.shell('am','force-stop',PACKAGE);device.enter('selected-persistence-restart468');device.start_qa()
        restarted=state();require(restarted['data']==persisted['data'],'Saved state changed across explicit selected restart');unchanged_watchlist(restarted)
        passed('explicit_app_restart_persists_saved_offsets_and_membership',shutdown_acceptance=False)
        device.install(recovery,'forward-recovery469');device.enter('forward-recovery469');device.start_qa()
        recovered=check_identity(recovery,80);after=state();require(after['data']==persisted['data'],'Forward recovery changed saved data')
        require(device.shell('cat',PROFILE+'/watchlist-profile-sentinel.txt')==sentinel,'Recovery changed sentinel')
        passed('signed_forward_recovery469_restores_baseline_functional_modules_preserves_data',identity=recovered)
        report['status']='PASS_SELECTED_ANDROID_WATCHLIST_SYNTHETIC_MEDIA_GATES'
    except BaseException as error:
        report.update(status='FAIL_SELECTED_ANDROID_WATCHLIST_GATES',error=repr(error),traceback=traceback.format_exc());fail_capture();raise
    finally:
        save()
        if server:server.shutdown();server.server_close()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('baseline','candidate','recovery','fixture','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--port',type=int,default=18766);run(**vars(p.parse_args()))
