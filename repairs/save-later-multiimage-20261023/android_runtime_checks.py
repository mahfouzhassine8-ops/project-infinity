"""Actual Kodi GUI/provider checks on a disposable API37 profile only.

No provider response, selection, native result or receipt is mocked. Network
failures fail the corresponding check. Authenticated playback is not claimed.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit,parse_qs
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

FUTURE='plugin.video.future.navigation.7fa29'
PROVIDERS={'pov':'plugin.video.pov','umbrella':'plugin.video.umbrella',
           'seren':'plugin.video.seren','future':FUTURE}

def require(value,message):
    if not value:raise AssertionError(message)

def rpc(method,params=None):
    raw={'jsonrpc':'2.0','id':731,'method':method}
    if params is not None:raw['params']=params
    response=json.loads(xbmc.executeJSONRPC(json.dumps(raw)))
    if 'error' in response:raise RuntimeError(method+': '+json.dumps(response['error']))
    return response.get('result')

def until(fn,message,seconds=90):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if xbmc.Monitor().abortRequested():raise RuntimeError('Shutdown during '+message)
        value=fn()
        if value:return value
        xbmc.sleep(100)
    raise RuntimeError('Timed out: '+message)

def folder():return xbmc.getInfoLabel('Container.FolderPath')
def digest(value):return hashlib.sha256(value.encode()).hexdigest()

def gui_snapshot():
    modal=xbmc.getCondVisibility('System.HasActiveModalDialog')
    dialog=xbmcgui.getCurrentWindowDialogId()
    # Kodi returns a sentinel ID when no dialog exists; do not create a Window
    # wrapper for that sentinel. No native control wrappers are used here.
    window=xbmcgui.Window(dialog) if modal and dialog not in (0,-1,9999) else None
    prop=lambda key:window.getProperty(key) if window is not None else ''
    return dict(window=xbmcgui.getCurrentWindowId(),dialog=dialog,folder=folder(),
        modal=modal,
        ok=xbmc.getCondVisibility('Window.IsActive(okdialog)'),
        yesno=xbmc.getCondVisibility('Window.IsActive(yesnodialog)'),
        xml=prop('xmlfile'),heading=xbmc.getInfoLabel('Control.GetLabel(1)'),
        body=[xbmc.getInfoLabel('Control.GetLabel(%d)'%i) for i in (9,2,3,4)],
        umbrella_heading=prop('umbrella.heading'),umbrella_text=prop('umbrella.text'))

def first_use_action(state,notice,seren):
    # Only the actual pinned provider's informational first-use notices.
    # Never dismiss a generic error, resolver chooser, account or data prompt.
    if (state['modal'] and Path(state['xml']).name=='textviewer.xml' and
        state['umbrella_heading']==notice['heading'] and state['umbrella_text']==notice['text']):
        return 'acknowledge-umbrella-first-use-information'
    if (state['modal'] and Path(state['xml']).name=='textviewer.xml' and
        notice.get('changelog_heading') and notice.get('changelog_text') and
        state['umbrella_heading']==notice['changelog_heading'] and
        state['umbrella_text']==notice['changelog_text']):
        return 'acknowledge-umbrella-first-home-changelog'
    bodies=[' '.join(s.split()) for s in state['body']]
    if (state['ok'] and state['heading']=='Seren' and
        ' '.join(seren['cache_complete'].split()) in bodies):
        return 'acknowledge-seren-own-first-use-completion'
    if (state['yesno'] and state['heading']==seren['timezone_heading'] and
        ' '.join(seren['timezone_body'].split()) in bodies):
        return 'decline-optional-seren-timezone-selection'
    return None

def first_use_status(log,home):
    # Only the source-backed first-use UI boundary, never service retirement or
    # durability. POV's final CheckUndesirablesDatabase is optional background
    # DB work: its caller swallows errors and may never log "Finished". Waiting
    # for that line blocked both Run39948674614 cases before navigation began.
    # "Starting" follows all first-use UI in the installed SettingsMonitor.
    # Any remaining DB obligations still face the unchanged native checkpoint.
    statuses={}
    for aid in ('plugin.video.pov',FUTURE):
        starts=list(re.finditer(r'T:(\d+).*Settings Monitor Service Starting \('+re.escape(aid)+r'-[^)]*\)',log))
        statuses[aid]=bool(starts and re.search(r'T:'+starts[-1].group(1)+r'\s.*CheckUndesirablesDatabase Service Starting',log[starts[-1].end():]))
    statuses['plugin.video.umbrella']='[ plugin.video.umbrella ]  Settings Monitor Service Starting...' in log
    statuses['plugin.video.seren']=(home.getProperty('seren.service.ready')==xbmcaddon.Addon('plugin.video.seren').getAddonInfo('version')
        and '?action=torrentCacheCleanup' in log)  # Scheduled after the optional timezone prompt.
    return statuses

def first_use_specifications():
    umbrella=xbmcaddon.Addon('plugin.video.umbrella')
    path=Path(xbmcvfs.translatePath(umbrella.getAddonInfo('path')))
    notice=dict(heading='[B]Umbrella -  v%s - externalProviders[/B]'%umbrella.getAddonInfo('version'),
        text=(path/'resources/help/externalProviders.txt').read_text(),
        changelog_heading='[B]Umbrella -  v%s - ChangeLog[/B]'%umbrella.getAddonInfo('version'),
        changelog_text=(path/'changelog.txt').read_text(encoding='utf-8',errors='ignore'))
    seren_addon=xbmcaddon.Addon('plugin.video.seren')
    seren=dict(cache_complete=seren_addon.getLocalizedString(30480),
        timezone_heading=seren_addon.getLocalizedString(30549),timezone_body=seren_addon.getLocalizedString(30550))
    require(all(seren.values()),'Pinned Seren first-use strings missing')
    return notice,seren

SEREN_INITIAL_TASKS=('torrentCacheCleanup','undesirablesStartup','updateAnimeMappings',
    'runMaintenance','syncTraktActivities','cleanOrphanedMetadata','updateLocalTimezone')

def first_use_task_results(log):
    # Actual Run39964672812 reached the UI boundary while Seren's one-time
    # anime mappings still held interpreter initialization for several minutes.
    # Observe completion of each finite startup invocation before normal-route
    # tests. This is not service retirement, a write receipt, or Close admission.
    results={}
    for action in SEREN_INITIAL_TASKS:
        starts=list(re.finditer(r'CPythonInvoker\((\d+)\):\s+\?action='+re.escape(action)+r'\s*$',log,re.M))
        if not starts:
            results[action]=dict(invocation=None,body_completed=False)
            continue
        start=starts[-1];ident=start.group(1)
        completed=bool(re.search(r'CPythonInvoker\('+ident+r', [^\n]*/plugin\.video\.seren/seren\.py\): script successfully run',log[start.end():]))
        results[action]=dict(invocation=int(ident),body_completed=completed)
    return results

def acknowledge_first_use(state,notice,seren,result,record):
    action=first_use_action(state,notice,seren)
    if not action:return False
    require(len(result['first_use_actions'])<8,'Provider first-use notice repeated unexpectedly')
    result['first_use_actions'].append(dict(action=action,observed=state,epoch_ms=int(time.time()*1000)))
    record('provider-first-use-interaction')
    # Back acknowledges only source-verified information, or declines optional
    # timezone selection. It never accepts a destructive or account prompt.
    require(rpc('Input.Back')=='OK','First-use information could not be dismissed')
    xbmc.sleep(500)
    return True

def complete_first_use(home,result,record):
    # Run39944949734: finish real setup interactions before navigation.
    # No provider settings/DB are seeded and no unknown dialog is dismissed.
    notice,seren=first_use_specifications()
    logpath=Path(xbmcvfs.translatePath('special://logpath/kodi.log'))
    # All actions are read from the unchanged installed service, not invented
    # setup receipts. Its longLifeServiceManager intentionally remains active.
    service=Path(xbmcvfs.translatePath(xbmcaddon.Addon('plugin.video.seren').getAddonInfo('path')))/'service.py'
    service_source=service.read_text()
    require(all('?action='+action in service_source for action in SEREN_INITIAL_TASKS),
        'Installed Seren startup scheduling changed')
    # The measured fresh API37/ARM-translation initialization took >12 minutes.
    # This setup allowance does not alter any product or checkpoint deadline.
    end=time.monotonic()+900;stable=None;last=None
    result['first_use_actions']=[]
    while time.monotonic()<end:
        require(not xbmc.Monitor().abortRequested(),'Shutdown during provider initialization')
        state=gui_snapshot();log=logpath.read_text(errors='replace')
        status=first_use_status(log,home);tasks=first_use_task_results(log)
        if acknowledge_first_use(state,notice,seren,result,record):continue
        observation=dict(first_use_ui_boundaries=status,finite_startup_task_bodies=tasks,gui=state,
            service_retirement_verified=False,persistence_verified=False)
        if observation!=last:
            result['first_use_observation']=observation;record('provider-first-use');last=observation
        if (all(status.values()) and all(t['body_completed'] for t in tasks.values()) and not state['modal']):
            if stable is None:stable=time.monotonic()
            if time.monotonic()-stable>=3:return
        else:stable=None
        xbmc.sleep(500)
    raise RuntimeError('Provider first-use did not complete: '+json.dumps(result['first_use_observation']))

def first_provider_home(aid,result,record):
    # Run39955714826 safe waited inside Umbrella's first-home changelog.
    # Its pinned router displays that modal before returning its real directory.
    # Keep observing only verified setup notices while the actual RPC runs.
    # This helper is never used for saved clicks, recovery, or provider results.
    import threading
    notice,seren=first_use_specifications();answers=[]
    def request():
        try:answers.append((True,rpc('Files.GetDirectory',dict(directory='plugin://'+aid+'/',media='video'))['files']))
        except Exception as error:answers.append((False,error))
    worker=threading.Thread(target=request,name='InfinityProviderFirstHome');worker.start()
    end=time.monotonic()+180
    while worker.is_alive():
        require(not xbmc.Monitor().abortRequested(),'Shutdown during provider first home')
        state=gui_snapshot();result['first_home_gui']=state
        if acknowledge_first_use(state,notice,seren,result,record):continue
        require(time.monotonic()<end,'Provider first home did not return: '+aid+'; '+json.dumps(state))
        worker.join(.1)
    require(bool(answers),'Provider first home returned no result')
    if not answers[0][0]:raise answers[0][1]
    return answers[0][1]

def select_native_item(control,predicate,message):
    # Run39938059169 crashed in the Python ControlList.size wrapper for a
    # native skin container. Use the GUI's own labels and focus messages;
    # never retain a Python control wrapper across native window changes.
    count=int(xbmc.getInfoLabel('Container(%d).NumItems'%control) or '0')
    require(0<count<=1000,'Native container has no bounded item list: '+message)
    for index in range(count):
        xbmc.executebuiltin('SetFocus(%d,%d,absolute)'%(control,index),True)
        until(lambda:xbmc.getCondVisibility('Control.HasFocus(%d)'%control),message+' focus')
        if predicate():
            require(rpc('Input.Select')=='OK',message+' selection failed')
            return
    raise AssertionError('Native item not found: '+message)

def open_saved(entry,home):
    path='plugin://script.infinity.commandcenter/?action=library&media='+entry['media']+'&bucket=later'
    # GUIMediaWindow WINDOW_INIT with "return" and the same start directory
    # intentionally restores its current child. Run39959879847 therefore
    # reopened Breaking Bad instead of returning to the saved list. Update the
    # active container explicitly; keep ActivateWindow for entry from Home.
    if xbmcgui.getCurrentWindowId()==10025:
        xbmc.executebuiltin('Container.Update("'+path+'",replace)')
    else:
        xbmc.executebuiltin('ActivateWindow(Videos,"'+path+'",return)')
    until(lambda:folder().rstrip('/')==path.rstrip('/'),'actual Save for Later listing')
    xbmc.executebuiltin('Container.SetViewMode(50)',True)
    until(lambda:int(xbmc.getInfoLabel('Container(50).NumItems') or '0')>0,'saved native items')
    def selected():
        if xbmc.getInfoLabel('ListItem.Property(Infinity.ResumeHub.Key)')==entry['key']:
            require(xbmc.getInfoLabel('ListItem.FileNameAndPath')==entry['source'],
                    'Original saved route was intercepted')
            require(xbmc.getInfoLabel('ListItem.Property(Infinity.ResumeHub.Bucket)')=='later',
                    'Saved bucket missing')
            return True
        return False
    require(not home.getProperty('Infinity.SavedNavigation.Failure'),'Stale failed ticket before new click')
    select_native_item(50,selected,'saved control item')

def verify_open_folder(path,home):
    def opened():
        require(not home.getProperty('Infinity.SavedNavigation.Failure'),'Original provider route failed')
        return folder().rstrip('/')==path.rstrip('/') and int(xbmc.getInfoLabel('Container.NumItems') or '0')>0
    until(opened,'provider seasons/episodes opened',180)
    require(not xbmc.getCondVisibility('Window.IsActive(selectdialog)'),
            'Successful navigation added a selection dialog')
    return dict(destination_sha256=digest(path),count=int(xbmc.getInfoLabel('Container.NumItems')))

def select_alternative(name):
    until(lambda:xbmc.getCondVisibility('Window.IsActive(selectdialog)'), 'actual recovery chooser')
    label=xbmc.getInfoLabel('Control.GetLabel(1)')
    require('saved destination failed' in label.lower(),'Unrelated selection dialog: '+label)
    select_native_item(3,lambda:xbmc.getInfoLabel('Container(3).ListItem.Label')==name,
                       'explicit provider alternative')

def verify_favorites_reference(nav,home,result,affected,umbrella):
    reference=json.loads(Path(__file__).with_name('ANDROID-FAVORITES-REFERENCE.json').read_text())
    path=reference['favorite_path'];ids=reference['identity']['ids']
    require(digest(path)==reference['favorite_path_sha256'],'Physical Favorites reference drift')
    params={k:v[0] for k,v in parse_qs(urlsplit(path).query).items()}
    require(all(params[k]==ids[k] for k in ids),'Favorites route identity differs')
    require(all(json.loads(params['meta'])[k]==ids[k] for k in ids),'Favorites metadata identity differs')
    require(affected['identity']['ids']['tmdb']==ids['tmdb'],'Different affected show')
    row=dict(type='tvshow',uniqueid=ids,file=path,filetype='directory')
    require(nav.destination(umbrella,row)==path,'Installed contract rejected actual Favorites route')
    # Exact native ActivateWindow command from the read-only physical capture.
    # No favorite, provider preference or saved record is created or replaced.
    xbmc.executebuiltin(reference['favorite_action'])
    opened=verify_open_folder(path,home)
    rows=rpc('Files.GetDirectory',dict(directory=path,media='video',
        properties=['title','uniqueid','season','episode']))['files']
    episodes=[r for r in rows if r.get('type')=='episode']
    require(bool(episodes),'Favorites reference returned no real episodes')
    for episode in episodes:
        destination=nav.destination(umbrella,episode)
        actual={k:v[0] for k,v in parse_qs(urlsplit(destination).query).items()}
        require(actual.get('tmdb')==ids['tmdb'],'Episode belongs to another show')
        require(all(actual.get(k) in (None,'',v) for k,v in ids.items()),'Conflicting episode identity')
        require(int(episode['season'])>=0 and int(episode['episode'])>=1,'Episode coordinates missing')
    result['cases'].append(dict(case='exact-physical-umbrella-favorite',passed=True,
        archive_sha256=reference['archive_sha256'],episodes=len(episodes),identity=ids,**opened))

def provider_stack_snapshot(aid):
    # Python3.11 exposes registered interpreter thread frames read-only. Keep
    # locations only: no locals, source text, credentials, URL values or writes.
    # This diagnostic cannot acknowledge work or authorize shutdown.
    import gc
    captured=[];frames={};frame=None
    try:
        # The APK embeds 3.11.7. Apply the later CPython _current_frames GC
        # protection only around this diagnostic call in its own interpreter;
        # restore the original GC state on every path (upstream gh-106883).
        enabled=gc.isenabled();gc.disable()
        try:frames=sys._current_frames()
        finally:
            if enabled:gc.enable()
        for ident,frame in list(frames.items())[:128]:
            locations=[];owned=False
            while frame is not None and len(locations)<96:
                name=frame.f_code.co_filename.replace('\\','/')
                owned=owned or ('/addons/'+aid+'/') in name
                if '/addons/' in name:name='addons/'+name.split('/addons/',1)[1]
                elif name.startswith('/'):name=Path(name).name
                locations.append(dict(file=name,function=frame.f_code.co_name,line=frame.f_lineno))
                frame=frame.f_back
            if owned:captured.append(dict(thread_ident=ident,locations=locations))
    except Exception as error:
        return dict(provider=aid,available=False,error_type=type(error).__name__)
    finally:
        frame=None;frames.clear()
    return dict(epoch_ms=int(time.time()*1000),provider=aid,threads=captured,
        python_version=sys.version.split()[0],
        scope='read-only locations; not a persistence or retirement receipt')

def observe_normal_directory(nav,search,entry,provider,result,record):
    # Run39955714826: the bounded consumer expired at 20 seconds, while POV's
    # invocation retired about eight seconds later without a provider traceback.
    # Compare Kodi's ordinary directory path as a separate diagnostic. This is
    # never a retry-to-pass and does not alter any production deadline or route.
    import threading
    query=str(entry.get('showtitle') or entry.get('title') or '').strip()
    path=search.route(provider,query)
    observation=dict(purpose='diagnostic only; original timeout remains failed',
        destination_sha256=digest(path),completed=False,request_started_epoch_ms=int(time.time()*1000))
    result['normal_directory_comparison']=observation
    answers=[]
    def request():
        began=time.monotonic()
        try:
            rows=rpc('Files.GetDirectory',dict(directory=path,media='video',
                properties=search.PROPERTIES,limits=dict(start=0,end=search.MAX_RESULTS)))['files']
            wanted=nav.hub.entry_identity(entry)
            matches=[r for r in rows if r.get('type')==wanted['kind'] and
                nav._same_ids(wanted['ids'],r.get('uniqueid'))]
            valid=[];rejected=[]
            for row in matches:
                try:valid.append(digest(nav.destination(provider,row)))
                except nav.Unavailable as error:rejected.append(str(error))
            answers.append(dict(completed=True,items=len(rows),identity_matches=len(matches),
                verified_destination_sha256=valid,rejected_destinations=rejected,
                elapsed_seconds=round(time.monotonic()-began,3)))
        except Exception as error:
            answers.append(dict(completed=True,error_type=type(error).__name__,
                elapsed_seconds=round(time.monotonic()-began,3)))
    worker=threading.Thread(target=request,name='InfinityNavigationDiagnostic')
    record('failed-normal-directory-comparison');worker.start()
    end=time.monotonic()+180
    while worker.is_alive() and time.monotonic()<end and not xbmc.Monitor().abortRequested():
        worker.join(.1)
    observation.update(answers[0] if answers else dict(still_pending=True))
    observation['provider_stacks']=provider_stack_snapshot(provider['id'])
    # Do not kill or mark a still-running provider/interpreter retired.
    record('failed-normal-directory-observed')

def run(root,cycle,mode):
    cc=xbmcaddon.Addon('script.infinity.commandcenter')
    sys.path.insert(0,xbmcvfs.translatePath(cc.getAddonInfo('path')))
    import saved_navigation as nav
    import resume_hub as hub
    import infinity_search as search
    result=dict(passed=False,pid=os.getpid(),provider_source_modified=False,
        third_party_cache_cleared_by_test=False,disposable_profile=True,physical_fold_verified=False,
        authenticated_provider_playback_verified=False,cases=[])
    out=Path(root)/('navigation-ready-'+cycle+'.json')
    def record(stage):
        result['stage']=stage
        (Path(root)/('navigation-progress-'+cycle+'.json')).write_text(json.dumps(result))
    try:
        # The host opens this test-only gate after real first-party startup
        # receipts and dismissal of Android's observed first-use overlay.
        # This marker is never a native persistence or termination receipt.
        until(lambda:(Path(root)/('navigation-start-'+cycle+'.json')).exists(),
              'host test admission',300)
        require(cc.getAddonInfo('version')=='0.3.5.31','Actual controller31 was not selected')
        result['active_skin']=xbmc.getSkinDir()
        require(result['active_skin']=='skin.infinity.diggz',
                'Infinity skin must be active; actual='+result['active_skin'])
        require(rpc('Settings.GetSettingValue',dict(setting='general.addonupdates'))['value']==2,
                'Disposable profile input-update policy was not loaded')
        for aid in PROVIDERS.values():
            details=rpc('Addons.GetAddonDetails',dict(addonid=aid,properties=['enabled','version']))['addon']
            if not details['enabled']:
                require(rpc('Addons.SetAddonEnabled',dict(addonid=aid,enabled=True))=='OK','Provider enable failed')
        record('providers-enabled')
        home=xbmcgui.Window(10000)
        if mode=='safe' or mode.startswith('provider-'):
            complete_first_use(home,result,record)
        profile=Path(xbmcvfs.translatePath(cc.getAddonInfo('profile')))
        saved=profile/'continue-watching.json'
        before=saved.read_bytes();data=hub.load_view(profile)
        entries={e['key']:e for e in hub.entries(data,'all','later')}
        require(set(k*64 for k in 'abcd')<=set(entries),'Disposable saved controls missing')
        # First visit the unmodified provider's real home on the fresh profile.
        # Existing user installations have already performed this initialization.
        # Record its actual duration/result; never change the bounded resolver's
        # deadline, retry its failures, or replace a provider directory response.
        initialize=(['plugin.video.pov','plugin.video.umbrella'] if mode=='safe' else
                    [PROVIDERS[mode.split('-',1)[1]]] if mode.startswith('provider-') else [])
        for aid in initialize:
            record('provider-home:'+aid)
            began=time.monotonic()
            rows=first_provider_home(aid,result,record)
            require(bool(rows),'Actual provider home returned no items: '+aid)
            result['cases'].append(dict(case='real-first-provider-home',provider=aid,
                elapsed_seconds=round(time.monotonic()-began,3),count=len(rows),passed=True))
        record('navigation')
        if mode=='safe':
            control=entries['a'*64]
            open_saved(control,home)
            result['cases'].append(dict(case='original-working-show',
                **verify_open_folder(control['source'],home),passed=True))
            affected=entries['c'*64]
            ready,_=nav.available('tv');pov=next(p for p in ready if p['id']=='plugin.video.pov')
            metadata_path=nav.direct_destination(affected,pov)
            # Execute the real provider through Kodi's directory API to warm
            # metadata without caching a successful GUI open of the failing
            # saved route. No provider or Kodi cache is deleted or disabled.
            metadata=rpc('Files.GetDirectory',dict(directory=metadata_path,media='video',
                properties=['title','uniqueid','season']))['files']
            require(bool(metadata),'Actual affected-show metadata destination returned no items')
            result['cases'].append(dict(case='actual-affected-provider-metadata',
                destination_sha256=digest(metadata_path),count=len(metadata),passed=True))
            # Only disposable emulator memory is fault-injected. Source and
            # SQLite are unmodified, and the malformed cache stays unchanged.
            prop='pov_meta_tvshow_tmdb_id_330430'
            actual=home.getProperty(prop)
            require(bool(actual),'Actual POV did not publish show metadata')
            expiry,meta=json.loads(actual)
            require(type(expiry) is int,'Clean provider expiry was already malformed')
            malformed=json.dumps([str(expiry),meta]);home.setProperty(prop,malformed)
            open_saved(affected,home)
            failure=until(lambda:home.getProperty('Infinity.SavedNavigation.Failure'),
                          'actual failed native directory result',180)
            ticket=json.loads(failure)
            require(ticket['key']==affected['key'] and ticket['reason']=='provider_directory_failed',
                    'Native failure did not identify clicked entry')
            require(ticket['original_sha256']==digest(affected['source']),'Failed destination mismatch')
            ready,_=nav.available('tv');umbrella=next(p for p in ready if p['id']=='plugin.video.umbrella')
            alternative=nav.direct_destination(affected,umbrella)
            require(bool(alternative),'Verified ID-addressed alternative unavailable')
            select_alternative(umbrella['name'])
            until(lambda:folder().rstrip('/')==alternative.rstrip('/'),'explicit alternative handoff',180)
            result['cases'].append(dict(case='actual-failure-explicit-alternative',
                **verify_open_folder(alternative,home),passed=True))
            require(home.getProperty(prop)==malformed,'Malformed cache changed or cleared')
            result['poisoned_cache_failure_and_explicit_alternative']=True
            result['poisoned_cache_preserved']=True
            record('physical-favorites-reference')
            verify_favorites_reference(nav,home,result,affected,umbrella)
        elif mode.startswith('provider-'):
            aid=PROVIDERS[mode.split('-',1)[1]]
            if home.getProperty('Infinity.Search.Protocol')!='1':
                search._leased_directory('plugin://script.infinity.commandcenter/?action=search-probe',home)
            require(home.getProperty('Infinity.Search.Protocol')=='1','Actual bounded directory protocol absent')
            class Progress:
                def iscanceled(self):return False
            for media,key in [('movie','b'*64),('tv','a'*64)]:
                record('provider-resolve:'+aid+':'+media)
                ready,_=nav.available(media);provider=next(p for p in ready if p['id']==aid)
                target=nav.resolve(entries[key],provider,home,Progress())
                require(urlsplit(target).netloc==aid,'Destination provider changed')
                case=dict(media=media,provider=aid,destination_sha256=digest(target),
                          real_provider_metadata_executed=True,passed=True)
                if media=='tv':
                    xbmc.executebuiltin('ActivateWindow(Videos,"'+target.replace('"','%22')+'",return)')
                    case.update(verify_open_folder(target,home))
                else:case['playback_verified']=False
                result['cases'].append(case)
        for media,bucket,key in [('movie','later','b'*64),('tv','continue','f'*64)]:
            rows=rpc('Files.GetDirectory',dict(directory='plugin://script.infinity.commandcenter/?action=library&media='+media+'&bucket='+bucket,
                media='video',properties=['title']))['files']
            expected=(entries[key] if bucket=='later' else data['items'][key])['source']
            result['listing_observation']=dict(media=media,bucket=bucket,expected_sha256=digest(expected),
                returned_sha256=[digest(r.get('file','')) for r in rows])
            require(any(r.get('file')==expected for r in rows),'Original '+bucket+' route missing')
            result['cases'].append(dict(case=media+'-'+bucket+'-original-route',passed=True))
        require(saved.read_bytes()==before,'Navigation mutated saved controls')
        require(data['items'] and data['watched'] and data['watchlist'],'Preservation controls missing')
        result['saved_state_sha256']=hashlib.sha256(before).hexdigest()
        result['saved_watchlist_resume_watched_unchanged']=True
        xbmc.executebuiltin('ActivateWindow(Home)')
        dialog=xbmcgui.WindowXMLDialog('multiimage-probe.xml',xbmcaddon.Addon().getAddonInfo('path'),'Default','1080i')
        dialog.show();xbmc.sleep(2500);dialog.close()
        result['multiimage_control_exercised']=True
        result['passed']=True
    except BaseException as error:
        result['failure']=type(error).__name__+': '+str(error)
        result['traceback']=__import__('traceback').format_exc()
        result['failure_gui']=gui_snapshot()
        if mode.startswith('provider-'):
            result['provider_stacks_at_failure']=provider_stack_snapshot(PROVIDERS[mode.split('-',1)[1]])
        record('failed-observing-late-provider-completion')
        # Preserve failure. Observe once, without retrying or extending the
        # production resolver deadline, so timeout logs include late completion.
        xbmc.Monitor().waitForAbort(30)
        result['failure_gui_after_observation']=gui_snapshot()
        if mode.startswith('provider-') and isinstance(error,nav.Unavailable) and '(timeout)' in str(error):
            try:observe_normal_directory(nav,search,entries[key],provider,result,record)
            except Exception as diagnostic_error:
                result['normal_directory_comparison_error']=type(diagnostic_error).__name__
    finally:
        with out.open('w') as stream:json.dump(result,stream)
    require(result['passed'],result.get('failure','Runtime check failed'))
