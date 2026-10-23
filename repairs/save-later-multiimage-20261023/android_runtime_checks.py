"""Actual Kodi GUI/provider checks on a disposable API37 profile only.

No provider response, selection, native result or receipt is mocked. Network
failures fail the corresponding check. Authenticated playback is not claimed.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
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

def run(root,cycle,mode):
    cc=xbmcaddon.Addon('script.infinity.commandcenter')
    sys.path.insert(0,xbmcvfs.translatePath(cc.getAddonInfo('path')))
    import saved_navigation as nav
    import resume_hub as hub
    import infinity_search as search
    result=dict(passed=False,pid=os.getpid(),provider_source_modified=False,
        third_party_cache_cleared=False,physical_fold_verified=False,
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
            rows=rpc('Files.GetDirectory',dict(directory='plugin://'+aid+'/',media='video'))['files']
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
        elif mode.startswith('provider-'):
            aid=PROVIDERS[mode.split('-',1)[1]]
            if home.getProperty('Infinity.Search.Protocol')!='1':
                search._leased_directory('plugin://script.infinity.commandcenter/?action=search-probe',home)
            require(home.getProperty('Infinity.Search.Protocol')=='1','Actual bounded directory protocol absent')
            class Progress:
                def iscanceled(self):return False
            for media,key in [('movie','b'*64),('tv','a'*64)]:
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
    finally:
        with out.open('w') as stream:json.dump(result,stream)
    require(result['passed'],result.get('failure','Runtime check failed'))
