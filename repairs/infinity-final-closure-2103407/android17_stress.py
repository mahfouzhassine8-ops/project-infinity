"""Explicit post-feature API37 stress. Real input/playback; no shutdown transport.

Only a fresh emulator already admitted by the exact signed candidate feature
runner can enter here. Generated test video is described as such. Missing frame
or poster-paint evidence stays unavailable instead of becoming a timing pass.
"""
from pathlib import Path
import json
import math
import re
import subprocess
import time
from urllib.parse import parse_qs,urlsplit
import xml.etree.ElementTree as ET
import android_frame_samples
import android_stress_script

COUNTS={'search':50,'playback_home':30,'rotation':20}
HOME_COUNTS={'search':0,'playback_home':30,'rotation':20}
SEARCH_COUNTS={'search':50,'playback_home':0,'rotation':0}


def require(value,message):
    if not value:raise RuntimeError(message)


def admit(device,setup,expected):
    require(expected.get('post_feature') in (COUNTS,HOME_COUNTS,SEARCH_COUNTS),'Exact stress selection required')
    require(setup.get('passed') is True,'Selected real feature did not pass')
    require(setup.get('apk_sha256')==expected['candidate_apk_sha256'],'Stress APK binding differs')
    require(device.PACKAGE=='com.projectinfinity.kodi','Wrong application')
    require(device.shell('getprop','ro.kernel.qemu').strip()=='1','Stress refuses physical devices')
    require(device.shell('getprop','ro.build.version.sdk').strip()=='37','Stress requires API37')
    owner=setup.get('engine',{})
    require(type(owner.get('pid')) is int and owner.get('owner'),'Missing admitted process identity')
    current=device.running_engine()
    require(current and current.get('pid')==owner['pid'] and current.get('owner')==owner['owner'],'Admitted engine changed')
    return owner


def quantiles(values):
    ordered=sorted(values)
    return dict(count=len(ordered),median_ms=ordered[(len(ordered)-1)//2] if ordered else None,
                p95_ms=ordered[max(0,math.ceil(.95*len(ordered))-1)] if ordered else None,
                max_ms=max(ordered) if ordered else None)


def _run(device,setup,expected,out):
    owner=admit(device,setup,expected);out=Path(out);out.mkdir(exist_ok=False)
    wanted=dict(expected['post_feature'])
    report=dict(passed=False,apk_sha256=expected['candidate_apk_sha256'],owner=owner,
        requested=wanted,selected_scopes={k:('SELECTED' if v else 'NOT SELECTED') for k,v in wanted.items()},search=[],playback_home=[],rotation=[],snapshots=[],scroll_samples=[],
        physical_Fold='NOT RUN',shutdown='NOT SELECTED',poster_first_paint='NOT MEASURED',
        native_frame_pacing='RAW SAMPLES ONLY; no native FPS claim',
        playback_content='Generated gray640x360 H264 clip, no real movie playback claim')
    save=lambda:(out/'STRESS-RESULT.json').write_text(json.dumps(report,indent=2)+'\n')

    def alive():
        value=device.running_engine()
        require(value and value.get('pid')==owner['pid'] and value.get('owner')==owner['owner'],'Engine died or restarted during stress')

    def memory(stage):
        alive();pid=str(owner['pid'])
        native_stat=device.shell('cat','/proc/'+pid+'/stat',check=False);sampled_at=time.monotonic()
        raw=device.shell('dumpsys','meminfo',pid,check=False)
        (out/(stage+'-meminfo.txt')).write_text(raw)
        match=re.search(r'TOTAL PSS:\s*(\d+).*?TOTAL RSS:\s*(\d+)',raw,re.S)
        status=device.shell('cat','/proc/'+pid+'/status',check=False)
        threads=re.search(r'^Threads:\s*(\d+)',status,re.M)
        descriptors=device.shell('ls','/proc/'+pid+'/fd',check=False).split()
        descriptor_count=len(descriptors) if descriptors and all(v.isdigit() for v in descriptors) else None
        report['snapshots'].append(dict(stage=stage,monotonic=sampled_at,
            pss_kib=int(match[1]) if match else None,rss_kib=int(match[2]) if match else None,
            proc_status=status,thread_count=int(threads[1]) if threads else None,descriptor_count=descriptor_count,
            proc_stat=native_stat))
        save()

    def nodes():
        device.shell('uiautomator','dump','/sdcard/infinity-search-stress.xml')
        raw=device.shell('cat','/sdcard/infinity-search-stress.xml')
        (out/'latest-ui.xml').write_text(raw)
        return list(ET.fromstring(raw).iter('node'))

    def control(values,description):
        matches=[n for n in values if n.get('content-desc')==description and n.get('clickable')=='true' and n.get('enabled')=='true']
        require(len(matches)==1,'Actual control unavailable: '+description)
        return matches[0]

    def tap(node):
        bounds=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
        require(bounds,'Actual control bounds unavailable')
        left,top,right,bottom=map(int,bounds.groups())
        device.shell('input','tap',str((left+right)//2),str((top+bottom)//2))

    def gui():return device.rpc('GUI.GetProperties',{'properties':['currentwindow']})['currentwindow']
    def home():
        device.rpc('GUI.ActivateWindow',{'window':'home'})
        device.until(lambda:gui().get('id')==10000,20)
        alive();require(device.rpc('JSONRPC.Ping')=='pong','Home RPC did not respond')

    def scroll_sample(index):
        folder=out/('scroll-'+str(index));folder.mkdir()
        current_layers=[s for s in device.shell('dumpsys','SurfaceFlinger','--list',check=False).splitlines()
                        if device.PACKAGE in s and 'SurfaceView' in s]
        before={layer:device.shell('dumpsys','SurfaceFlinger','--latency',layer,check=False) for layer in current_layers}
        entry=dict(search_cycle=index,scope='actual Search results list,25Down/25Up',native_layers=current_layers,selection=[],frames=[])
        began=time.monotonic()
        for step in range(50):
            device.rpc('Input.Down' if step<25 else 'Input.Up')
            if step%5==0:entry['selection'].append(device.rpc('XBMC.GetInfoLabels',{'labels':['Container.CurrentItem','Container.FolderPath']}))
            time.sleep(.05)
        entry['seconds']=time.monotonic()-began
        for number,layer in enumerate(current_layers):
            after=device.shell('dumpsys','SurfaceFlinger','--latency',layer,check=False)
            (folder/(str(number)+'-before.txt')).write_text(before[layer]);(folder/(str(number)+'-after.txt')).write_text(after)
            entry['frames'].append(dict(layer=layer,**android_frame_samples.summarize(before[layer],after)))
        alive();report['scroll_samples'].append(entry);save()

    frame_before=device.shell('dumpsys','gfxinfo',device.PACKAGE,'framestats',check=False)
    (out/'before-hwui.txt').write_text(frame_before)
    layers=[s for s in device.shell('dumpsys','SurfaceFlinger','--list',check=False).splitlines()
            if device.PACKAGE in s and 'SurfaceView' in s]
    report['native_layers']=layers
    for index,layer in enumerate(layers):
        (out/('before-layer-'+str(index)+'.txt')).write_text(device.shell('dumpsys','SurfaceFlinger','--latency',layer,check=False))
    ticks=device.shell('getconf','CLK_TCK',check=False).strip()
    report['clock_ticks']=int(ticks) if ticks.isdigit() and int(ticks)>0 else None
    memory('before');home()
    if expected.get('expected_skin_version'):
        actual_skin=device.rpc('Addons.GetAddonDetails',{'addonid':'skin.infinity.diggz','properties':['version','enabled']})['addon']
        require(actual_skin.get('version')==expected['expected_skin_version'],'Actual active skin component version differs')
        report['actual_skin']=actual_skin
        report['helper_lifecycle_before']=device.rpc('XBMC.GetInfoLabels',{'labels':[
            'Window(Home).Property(Infinity.Continuity.Observer)',
            'Window(Home).Property(Infinity.NativeAmbient.WriterLifecycle)']})
    android_stress_script.initialize(device,out,owner)
    state_path=device.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json'
    protected=device.read_json(state_path)
    require(setup.get('prelaunch_stress_fixture',{}).get('declared_resume_clip_exists') is True,
            'Declared saved-card clip must actually exist before a usability measurement')
    protected_keys=('items','watched','watchlist','collection','lists','sources','navigation_recovery')
    require(protected.get('items'),'Actual tracking fixture unavailable')
    if expected.get('measure_cached_poster') is True:
        import stress_resume_card
        report['initial_cached_Home_card']=stress_resume_card.observe(device,protected,'movie',out/'initial-cached-poster')
        report['poster_first_paint']='Actual cached QA bitmap observed on native Android surface; not cold app launch or remote artwork'
        save();home()
    for index in range(wanted['search']):
        query='Just Friends' if index%2==0 else 'The Matrix'
        provider='all' if index%2==0 else 'plugin.video.umbrella'
        began=time.monotonic()
        android_stress_script.launch(device)
        def keyboard():
            values=nodes()
            edits=[n for n in values if n.get('class')=='android.widget.EditText' and n.get('enabled')=='true']
            return (values,edits[0]) if len(edits)==1 else None
        def typing_keyboard():
            import android_input_readiness
            # Do not launch repeated UIAutomator VMs while the actual native
            # keyboard is still opening. Require the same strict IME proof,
            # then read the current real EditText under the original deadline.
            return keyboard() if android_input_readiness.ready(device,out) else None
        values,edit=device.until(typing_keyboard,45) # Retain the actual original keyboard deadline.
        android_stress_script.verify_dispatch(device)
        wanted='Search All' if provider=='all' else 'Umbrella'
        choices=[n for n in values if n.get('clickable')=='true' and
            any(n.get('content-desc','').startswith(wanted+p) for p in (', ','. '))]
        require(len(choices)==1,'Actual provider selector unavailable: '+wanted);tap(choices[0])
        history_used=False
        if (index+1)%10==0:
            tap(control(values,'Search History'))
            history_nodes=nodes()
            require(any(n.get('text')=='Search History' for n in history_nodes),'History dialog unavailable')
            matches=[n for n in history_nodes if n.get('text')==query and n.get('class')=='android.widget.TextView']
            require(matches,'Actual persisted query unavailable in History');tap(matches[0])
            values,edit=device.until(keyboard,45);history_used=True
        tap(edit)
        if not history_used:
            if edit.get('text'):
                device.shell('input','keycombination','113','29')
                device.shell('input','keyevent','67')
            device.shell('input','text',query.replace(' ','%s'))
        require(any(n.get('class')=='android.widget.EditText' and n.get('text')==query for n in nodes()),'Actual Search text differs')
        device.shell('input','keyevent','66')
        duplicate=(index+1)%10==0
        if duplicate:device.shell('input','keyevent','66')
        def results():
            if gui().get('id')!=10025:return None
            keys=['Container.FolderPath','Container.NumItems']
            value=device.rpc('XBMC.GetInfoLabels',{'labels':keys})
            path=value.get(keys[0],'');parsed=urlsplit(path)
            params=parse_qs(parsed.query)
            if parsed.netloc!='script.infinity.commandcenter' or params.get('query')!=[query]:return None
            action='search-all' if provider=='all' else 'search-provider'
            if params.get('action')!=[action]:raise RuntimeError('Search provider selection changed unexpectedly')
            if provider!='all' and params.get('provider')!=[provider]:raise RuntimeError('Provider identity changed')
            if not value.get(keys[1],'').isdigit() or int(value[keys[1]])<1:return None
            count=int(value[keys[1]]);require(count<=200,'Unexpected unbounded fixture results')
            labels=[key for i in range(count+1) for key in (
                'Container.ListItemAbsolute('+str(i)+').Property(Infinity.Search.Provider)',
                'Container.ListItemAbsolute('+str(i)+').Label')]
            sources=device.rpc('XBMC.GetInfoLabels',{'labels':labels})
            required={'plugin.video.pov','plugin.video.umbrella','plugin.video.seren'} if provider=='all' else {provider}
            from search_terminal_observer import classify
            terminal=classify([dict(provider=sources.get(labels[2*i],''),label=sources.get(labels[2*i+1],''))
                for i in range(count+1)],required)
            if terminal is None:return None
            value['actual_providers']=sorted(terminal['providers'])
            value['actual_provider_terminal']=terminal
            return value
        visible=device.until(results,90)
        report['search'].append(dict(cycle=index,query=query,elapsed_ms=(time.monotonic()-began)*1000,
                                     visible=visible,pid=owner['pid'],actual_android_input=True,
                                     selected_provider=provider,history_row_used=history_used,duplicate_enter_sent=duplicate))
        if index in (9,49):scroll_sample(index+1)
        home();save()
        if (index+1)%10==0:
            android_stress_script.launch(device)
            values,_=device.until(keyboard,45)
            android_stress_script.verify_dispatch(device)
            tap(control(values,'Close Infinity Search'))
            device.until(lambda:not any(n.get('class')=='android.widget.EditText' for n in nodes()),20)
            home();report['search'][-1]['additional_search_cancelled']=True;save()
        if (index+1)%5==0:memory('search-'+str(index+1))

    if wanted['playback_home']:
        clip=out/'generated-native-cycle.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=gray:s=640x360:r=24',
                        '-t','8','-an','-c:v','libx264','-pix_fmt','yuv420p',str(clip)],check=True)
        remote=device.PROFILE+'/infinity-stress-native.mp4';device.adb('push',clip,remote)
        require(not device.rpc('Player.GetActivePlayers'),'Unexpected playback before test clip')
    for index in range(wanted['playback_home']):
        device.rpc('Player.Open',{'item':{'file':remote},'options':{'resume':False}})
        players=device.until(lambda:[p for p in device.rpc('Player.GetActivePlayers') if p.get('type')=='video'],20)
        player=players[0]['playerid']
        def progressed():
            value=device.rpc('Player.GetProperties',{'playerid':player,'properties':['time','speed']})
            stamp=value.get('time',{})
            return value if value.get('speed')==1 and (stamp.get('seconds',0)>=1 or stamp.get('minutes',0)>0) else None
        evidence=device.until(progressed,20)
        started=time.monotonic();device.rpc('Player.Stop',{'playerid':player});home()
        rpc_ready_ms=(time.monotonic()-started)*1000
        require(not device.rpc('Player.GetActivePlayers'),'Playback did not stop')
        import stress_resume_card
        card=stress_resume_card.observe(device,protected,'movie' if index%2==0 else 'tv',out/('poster-playback-'+str(index)))
        report['playback_home'].append(dict(cycle=index,home_window_rpc_ready_ms=rpc_ready_ms,
            stop_to_correct_usable_card_ms=(card['observation_began_monotonic']-started)*1000+card['tab_select_to_usable_card_ms'],
            exact_native_proof_finished_after_stop_ms=(time.monotonic()-started)*1000,
            actual_resume_card=card,playback=evidence,poster_paint_verified=card['poster_paint_verified']))
        save()
        if (index+1)%10==0:memory('playback-'+str(index+1))

    if wanted['rotation']:
        previous={k:device.shell('settings','get','system',k).strip() for k in ('accelerometer_rotation','user_rotation')}
        report['original_rotation_settings']=previous
        try:
            device.shell('settings','put','system','accelerometer_rotation','0')
            for index in range(wanted['rotation']):
                value=1 if index%2==0 else 0;began=time.monotonic()
                device.shell('settings','put','system','user_rotation',str(value))
                def rotated():
                    raw=device.shell('dumpsys','input',check=False)
                    match=re.search(r'(?:orientation|SurfaceOrientation)\s*[=:]\s*([0-3])',raw)
                    return raw if match and int(match[1])==value else None
                evidence=device.until(rotated,20)
                (out/('rotation-'+str(index)+'-input.txt')).write_text(evidence)
                home()
                import stress_resume_card
                card=stress_resume_card.observe(device,protected,'movie' if index%2==0 else 'tv',out/('poster-rotation-'+str(index)))
                report['rotation'].append(dict(cycle=index,requested=value,actual=value,
                        elapsed_ms=(time.monotonic()-began)*1000,physical_fold=False,actual_resume_card=card));save()
        finally:
            for name,value in previous.items():
                if value!='null':device.shell('settings','put','system',name,value)
    memory('after')
    after=device.read_json(state_path)
    require(all(protected.get(k)==after.get(k) for k in protected_keys),'Stress changed protected tracking records')
    report['protected_records_unchanged']=True
    (out/'after-hwui.txt').write_text(device.shell('dumpsys','gfxinfo',device.PACKAGE,'framestats',check=False))
    for index,layer in enumerate(layers):
        (out/('after-layer-'+str(index)+'.txt')).write_text(device.shell('dumpsys','SurfaceFlinger','--latency',layer,check=False))
    (out/'display-state.txt').write_text(device.shell('dumpsys','display',check=False))
    report['search_duration']=quantiles([x['elapsed_ms'] for x in report['search']])
    report['search_interaction_stability_scope']='Exact actual terminal UI; attributed provider failures remain separate content failures' if wanted['search'] else 'NOT SELECTED; prior Search50failure remains independent'
    report['successful_content_searches']=sum(x['visible']['actual_provider_terminal']['content_success'] for x in report['search'])
    report['provider_content_failures']=[dict(cycle=x['cycle'],failures=x['visible']['actual_provider_terminal']['graceful_provider_failures'])
        for x in report['search'] if not x['visible']['actual_provider_terminal']['content_success']]
    report['all_searches_returned_successful_content']=report['successful_content_searches']==wanted['search'] if wanted['search'] else None
    report['home_window_rpc_duration']=quantiles([x['home_window_rpc_ready_ms'] for x in report['playback_home']])
    report['stop_to_correct_usable_card_duration']=quantiles([x['stop_to_correct_usable_card_ms'] for x in report['playback_home']])
    report['cpu_intervals']=[dict(before=a['stage'],after=b['stage'],**android_frame_samples.cpu_interval(a,b,report['clock_ticks']))
                             for a,b in zip(report['snapshots'],report['snapshots'][1:])]
    report['passed']=all(len(report[k])==v for k,v in wanted.items());save()
    return report


def run(device,setup,expected,out):
    try:return _run(device,setup,expected,out)
    except BaseException as error:
        path=Path(out)/'STRESS-RESULT.json'
        if path.is_file():
            report=json.loads(path.read_text());report['passed']=False
            report['failure']=type(error).__name__+': '+str(error)
            report['traceback']=__import__('traceback').format_exc()
            path.write_text(json.dumps(report,indent=2)+'\n')
        raise
