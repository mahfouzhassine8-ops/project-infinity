"""One selected tracking feature, real Kodi GUI/provider actions, no app termination."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import android_runtime_checks as ui

CASES=('tracking-recovery','tracking-actions','tracking-continue')

def listing(entry,bucket,expected):
    path='plugin://script.infinity.commandcenter/?action=library&media='+entry['media']+'&bucket='+bucket
    xbmc.executebuiltin('Container.Update("'+path+'",replace)' if xbmcgui.getCurrentWindowId()==10025 else 'ActivateWindow(Videos,"'+path+'",return)')
    ui.until(lambda:ui.folder().rstrip('/')==path.rstrip('/'),'selected saved list')
    xbmc.executebuiltin('Container.SetViewMode(50)',True)
    ui.until(lambda:int(xbmc.getInfoLabel('Container(50).NumItems') or '0')>0,'saved items populated')
    def chosen():
        if xbmc.getInfoLabel('ListItem.Property(Infinity.ResumeHub.Key)')!=entry['key']:return False
        ui.require(xbmc.getInfoLabel('ListItem.FileNameAndPath')==expected,'Unexpected saved destination')
        return True
    ui.select_native_item(50,chosen,'exact saved media')

def provider_choice(name):
    def ready():
        s=ui.gui_snapshot()
        return s['modal'] and s['dialog']==12000 and Path(s['xml']).name=='DialogSelect.xml' and s['heading'] in (
            'The saved destination failed — open with','Saved destination unavailable — open with')
    ui.until(ready,'explicit recovery dialog',180)
    ui.select_native_item(3,lambda:xbmc.getInfoLabel('Container(3).ListItem.Label')==name,'user-selected provider')

def context_action(label):
    ui.require(ui.rpc('Input.ContextMenu')=='OK','Context menu input failed')
    ui.until(lambda:xbmc.getCondVisibility('Window.IsActive(contextmenu)'),'native context menu')
    def find():
        for ident in range(1000,1064):
            text=re.sub(r'\[[^]]*\]','',xbmc.getInfoLabel('Control.GetLabel(%d)'%ident))
            if text=='Infinity Trakt':return ident
        return False
    ident=ui.until(find,'Infinity Trakt context entry')
    xbmc.executebuiltin('SetFocus(%d)'%ident,True);ui.rpc('Input.Select')
    def menu():
        ident=xbmcgui.getCurrentWindowDialogId()
        return ident>0 and xbmc.getInfoLabel('Window(%d).Property(Infinity.UI.Title)'%ident)=='Infinity Trakt'
    ui.until(menu,'actual Infinity Trakt chooser')
    ui.select_native_item(50,lambda:xbmc.getInfoLabel('Container(50).ListItem.Label')==label,'explicit tracking action')

def run(root,cycle,mode):
    result=dict(passed=False,pid=os.getpid(),selected_features=[mode],selected_mode=mode,
        cases=[],disposable_profile=True,provider_source_modified=False,physical_fold_verified=False,
        shutdown='NOT RUN',external_trakt='NOT RUN; local-only actions',final_lock=False)
    output=Path(root)/('navigation-ready-'+cycle+'.json')
    def record(stage):
        result['stage']=stage;(Path(root)/('navigation-progress-'+cycle+'.json')).write_text(json.dumps(result))
    def passed(name,**details):result['cases'].append(dict(case=name,passed=True,**details));record(name)
    try:
        ui.require(mode in CASES,'Exactly one authorized tracking case required')
        ui.until(lambda:(Path(root)/('navigation-start-'+cycle+'.json')).exists(),'test-only host admission',300)
        cc=xbmcaddon.Addon('script.infinity.commandcenter');ccroot=Path(xbmcvfs.translatePath(cc.getAddonInfo('path')))
        ui.require(cc.getAddonInfo('version')=='0.3.5.32','Matching CC32 required')
        ui.require(xbmc.getSkinDir()=='skin.infinity.diggz','Infinity skin required')
        sys.path.insert(0,str(ccroot));import resume_hub as hub;import saved_navigation as nav;import infinity_search as search
        profile=Path(xbmcvfs.translatePath(cc.getAddonInfo('profile')));file=profile/hub.CONTINUE_FILE
        snapshot=hub.load_view(profile);home=xbmcgui.Window(10000)
        if mode=='tracking-continue':
            before=file.read_bytes();expected=hub.entries(snapshot,'tv','items')
            ui.require(len(snapshot['items'])==2 and len(expected)==1,'Two episode controls and one projected series required')
            ui.require(expected[0]['key']=='8'*64,'Newest episode was not chosen')
            # Execute the actual skin directory, then verify its actual Home panel.
            rows=ui.rpc('Files.GetDirectory',dict(directory='plugin://script.infinity.uirepair/?action=continue&media=tv',media='video',properties=['season','episode','resume']))['files']
            ui.require(len(rows)==1 and rows[0]['episode']==2,'Actual Home route did not return selected episode')
            start=time.monotonic();xbmc.executebuiltin('ActivateWindow(Home)')
            ui.until(lambda:xbmcgui.getCurrentWindowId()==10000,'Home')
            count=ui.until(lambda:int(xbmc.getInfoLabel('Container(9000).NumItems') or '0'),'Home tabs')
            for index in range(count):
                xbmc.executebuiltin('SetFocus(9000,%d,absolute)'%index,True)
                if xbmc.getInfoLabel('Container(9000).ListItem.Property(section)')=='tvshows':break
            else:raise AssertionError('Actual TV tab not found')
            ui.until(lambda:xbmc.getCondVisibility('Control.IsVisible(8831)') and int(xbmc.getInfoLabel('Container(8831).NumItems') or '0')==1,'one visible actual Continue Watching card',180)
            xbmc.executebuiltin('SetFocus(8831,0,absolute)',True)
            ui.require(xbmc.getInfoLabel('Container(8831).ListItem.Property(Infinity.ResumeHub.Key)')=='8'*64,'Home card offered wrong episode')
            passed('actual-home-one-series-card',elapsed_seconds=time.monotonic()-start,episode=2)
            ui.require(file.read_bytes()==before,'Read-only Home projection changed progress/history')
            passed('all-episode-records-retained')
        else:
            providers=['plugin.video.pov','plugin.video.umbrella',ui.FUTURE] if mode=='tracking-recovery' else ['plugin.video.umbrella']
            for aid in providers:
                detail=ui.rpc('Addons.GetAddonDetails',dict(addonid=aid,properties=['enabled']))['addon']
                if not detail['enabled']:ui.require(ui.rpc('Addons.SetAddonEnabled',dict(addonid=aid,enabled=True))=='OK','Fixture provider unavailable')
            ui.complete_first_use(home,result,record,providers=providers)
            for aid in providers:
                if aid==ui.FUTURE:continue
                ui.require(ui.first_provider_home(aid,result,record,providers=providers),'Provider first home incomplete')
            if mode=='tracking-actions':
                ready,_=nav.available('movie');provider=next(p for p in ready if p['id']=='plugin.video.umbrella')
                path=search.route(provider,query='The Matrix')
                xbmc.executebuiltin('ActivateWindow(Videos,"'+path.replace('"','%22')+'",return)')
                ui.until(lambda:ui.folder().rstrip('/')==path.rstrip('/'),'actual provider search results',180)
                xbmc.executebuiltin('Container.SetViewMode(50)',True)
                count=ui.until(lambda:int(xbmc.getInfoLabel('Container(50).NumItems') or '0'),'search results')
                for index in range(count):
                    xbmc.executebuiltin('SetFocus(50,%d,absolute)'%index,True)
                    if xbmc.getInfoLabel('ListItem.UniqueID(tmdb)')=='603':break
                else:raise AssertionError('Exact movie TMDb603 absent from actual search results')
                identity=hub.media_identity('movie',{'tmdb':'603'});before=hub.load_view(profile)
                actions=[('Add to Watchlist','watchlist',True),('Save for Later','later',True),('Mark as Watched','watched',True),('Mark as Unwatched','watched',False),('Remove from Watchlist','watchlist',False),('Remove from Save for Later','later',False)]
                for label,bucket,present in actions:
                    prior=hub.load_view(profile).get(bucket,{})
                    ui.require(any(hub.same_identity(hub.entry_identity(v),identity) for v in prior.values())!=present,'Action precondition already satisfied: '+label)
                    began=time.monotonic();context_action(label)
                    def applied():
                        rows=hub.load_view(profile).get(bucket,{})
                        return any(hub.same_identity(hub.entry_identity(v),identity) for v in rows.values())==present
                    ui.until(applied,'local '+label,90);passed(label,elapsed_seconds=time.monotonic()-began)
                after=hub.load_view(profile);ui.require(after['items']==before['items'],'Tracking actions damaged episode progress')
                passed('search-context-local-tracking-roundtrip')
            else:
                entries=snapshot['later'];control=entries['a'*64];affected=entries['c'*64]
                listing(control,'watchlist',control['source']);ui.verify_open_folder(control['source'],home);passed('working-watchlist-original-show')
                ready,_=nav.available('tv');pov=next(p for p in ready if p['id']=='plugin.video.pov');umbrella=next(p for p in ready if p['id']=='plugin.video.umbrella')
                meta=nav.direct_destination(affected,pov)
                ui.require(ui.rpc('Files.GetDirectory',dict(directory=meta,media='video',properties=['title','uniqueid','season']))['files'],'Actual POV metadata unavailable')
                prop='pov_meta_tvshow_tmdb_id_330430';original=home.getProperty(prop)
                expiry,metadata=json.loads(original);ui.require(type(expiry) is int,'Clean metadata control invalid')
                # Reuse the verified failure injection in this disposable emulator
                # only; never clear the cache or modify installed provider code.
                poisoned=json.dumps([str(expiry),metadata]);home.setProperty(prop,poisoned)
                listing(affected,'watchlist',affected['source'])
                failure=json.loads(ui.until(lambda:home.getProperty('Infinity.SavedNavigation.Failure'),'real failed original Watchlist route',180))
                ui.require(failure['bucket']=='watchlist' and failure['key']==affected['key'],'Failure was not the selected Watchlist media')
                provider_choice(umbrella['name']);target=nav.direct_destination(affected,umbrella)
                ui.verify_open_folder(target,home)
                choice=ui.until(lambda:nav.remembered(hub.load_view(profile),affected['identity']),'native-verified saved provider choice',90)
                ui.require(choice.get('success_verified') is True and choice['route']==target,'Unverified or wrong recovery was remembered')
                passed('watchlist-failure-explicit-umbrella-success-remembered')
                for bucket in ('watchlist','later'):
                    began=time.monotonic();listing(affected,bucket,target);ui.verify_open_folder(target,home)
                    passed('remembered-direct-'+bucket,elapsed_seconds=time.monotonic()-began)
                ui.require(home.getProperty(prop)==poisoned,'Failed POV cache was overwritten')
                after=hub.load_view(profile)
                for bucket in ('later','watchlist','items','watched','sources','collection','ratings','lists'):
                    ui.require(after[bucket]==snapshot[bucket],'Recovery changed existing '+bucket)
                passed('saved-records-and-continue-preserved')
                ui.verify_favorites_reference(nav,home,result,affected,umbrella)
                # Existing compatible future controls remain explicitly selected
                # in their independent provider-* workflow modes; no full suite.
                result['across_application_sessions']='NOT RUN; no Close/reopen in this cycle'
        result['passed']=True
    except BaseException as error:
        result['failure']=type(error).__name__+': '+str(error);result['traceback']=__import__('traceback').format_exc();result['failure_gui']=ui.gui_snapshot()
    finally:output.write_text(json.dumps(result,indent=2))
    ui.require(result['passed'],result.get('failure','Selected tracking case incomplete'))
