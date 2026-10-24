"""Explicit final-eight feature staging and observation; no termination controls."""
import hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
from zipfile import ZipFile

SEARCH_CASES=('final-search-pov-enter','final-search-pov-button','final-search-all-enter')
CASES=('final-participant','final-continue','final-actions','final-pov')+SEARCH_CASES
HERE=Path(__file__).resolve().parent


def search_results_match(case, folder, records):
    """Selected fixture contract: exact requested CC route and source identity."""
    from urllib.parse import urlsplit, parse_qs
    if case not in SEARCH_CASES:return False
    try:
        parts=urlsplit(folder);query=parse_qs(parts.query,keep_blank_values=True,strict_parsing=True)
    except ValueError:return False
    if parts.scheme!='plugin' or parts.netloc!='script.infinity.commandcenter' or parts.path not in ('','/') or parts.fragment:return False
    expected={'action':['search-all' if case=='final-search-all-enter' else 'search-provider'],
              'media':['movie'],'query':['The Matrix']}
    providers={'plugin.video.pov','plugin.video.umbrella','plugin.video.seren'} if case=='final-search-all-enter' else {'plugin.video.pov'}
    if case!='final-search-all-enter':expected['provider']=['plugin.video.pov']
    if query!=expected:return False
    published={row['provider'] for row in records if row.get('provider')}
    if published!=providers:return False
    return any(row.get('tmdb')=='603' and row.get('provider') in providers for row in records)

def inputs(out, case):
    if case not in CASES:raise ValueError('Select one final-eight feature')
    out.mkdir(parents=True,exist_ok=False)
    if case!='final-pov' and case not in SEARCH_CASES:
        (out/'INPUTS.json').write_text(json.dumps({'archives':[],'case':case}));return
    sys.path.insert(0,str(HERE.parents[1]));import android_inputs
    pins=json.loads((HERE.parents[1]/'ANDROID-INPUT-PINS.json').read_text())
    pinned={r['addon']:r for r in pins['archives']}
    pending=[dict(addon='plugin.video.pov',version='6.10.22',
        url='https://raw.githubusercontent.com/kodifitzwell/repo/master/plugin.video.pov/plugin.video.pov-6.10.22.zip',
        sha256='126b9fbe690dded613d0c2bab177babd6ce2235bc9d67fb25e1c79aefc9dc0d3')]
    if case=='final-search-all-enter':
        pending.extend(pinned[aid] for aid in ('plugin.video.umbrella','plugin.video.seren'))
    rows=[];seen=set()
    while pending:
        row=pending.pop(0);aid=row['addon']
        if aid in seen:continue
        raw=android_inputs.fetch(row['url'])
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise RuntimeError('Pinned input changed: '+aid)
        manifest=android_inputs.manifest(raw,aid)
        if manifest.get('version')!=row['version']:raise RuntimeError('Wrong provider/dependency version')
        import io
        with ZipFile(io.BytesIO(raw)) as archive:
            for name in archive.namelist():
                p=Path(name)
                if p.is_absolute() or '..' in p.parts or p.parts[0]!=aid:raise RuntimeError('Unsafe fixture member')
                if (archive.getinfo(name).external_attr>>16)&0o170000==0o120000:raise RuntimeError('Fixture symlink')
            archive.extractall(out)
        seen.add(aid);rows.append(row)
        for dep in manifest.findall('requires/import'):
            name=dep.get('addon')
            if name.startswith('xbmc.') or dep.get('optional')=='true' or name in seen:continue
            if name not in pinned:raise RuntimeError('Dependency needs separately pinned input: '+name)
            pending.append(pinned[name])
    (out/'INPUTS.json').write_text(json.dumps({'archives':rows,'case':case},indent=2))

def stage(stage, args, report, device, fixture_id):
    if args.case not in CASES:raise ValueError('Select one final-eight feature')
    fixture=stage/fixture_id
    for name in ('android_selected.py',):shutil.copyfile(HERE/name,fixture/name)
    shutil.copyfile(HERE.parents[1]/'android_runtime_checks.py',fixture/'android_runtime_checks.py')
    (fixture/'service.py').write_text("import os,xbmcaddon,xbmcvfs\nfrom pathlib import Path\nimport android_selected\nroot=xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))\nPath(root).mkdir(parents=True,exist_ok=True)\nandroid_selected.run(root,str(os.getpid()),"+repr(args.case)+")\n")
    source=HERE.parents[3]/'android-provider-inputs'
    pins=json.loads((source/'INPUTS.json').read_text())
    for row in pins['archives']:shutil.copytree(source/row['addon'],stage/row['addon'])
    with ZipFile(args.apk) as apk:
        import xml.etree.ElementTree as ET
        expected={aid:ET.fromstring(apk.read('assets/addons/'+aid+'/addon.xml')).get('version') for aid in
                  ('script.infinity.commandcenter','script.infinity.uirepair','script.infinity.watchedbridge')}
    (fixture/'EXPECTED-COMPONENTS.json').write_text(json.dumps(expected))
    if args.case in SEARCH_CASES:
        report['test_provider_inputs']=pins
        return
    profile=args.out/'final-profile';profile.mkdir()
    clip='special://profile/infinity-final-qa.mp4'
    if args.case in ('final-continue','final-actions'):
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=gray:s=64x64:r=1','-t','180',
                        '-an','-c:v','libx264','-pix_fmt','yuv420p',str(profile/'infinity-final-qa.mp4')],check=True)
    def row(key,kind,ids,updated,episode=-1):
        identity=dict(schema=1,kind=kind,scope='movie' if kind=='movie' else 'show_episode',ids=ids)
        if kind=='episode':identity.update(season=1,episode=episode)
        return dict(key=key*64,media='movie' if kind=='movie' else 'tv',title='The Matrix' if kind=='movie' else 'Breaking Bad',
            label='The Matrix' if kind=='movie' else 'Breaking Bad S01E%02d'%episode,showtitle='' if kind=='movie' else 'Breaking Bad',
            season=-1 if kind=='movie' else 1,episode=episode,identity=identity,tmdb=ids.get('tmdb',''),
            source=clip,stable_source=clip,position=60,duration=180,updated=updated,playback_occurrence='1'*32)
    values=[row('a','movie',{'tmdb':'603','imdb':'tt0133093'},10),row('b','movie',{'imdb':'tt0133093'},20),
            row('c','episode',{'tmdb':'1396'},3,3),row('d','episode',{'tmdb':'1396'},4,2)]
    data=dict(schema=2,items={v['key']:v for v in values},watched={},watchlist={},collection={},lists={},sources={},later={},
              navigation_recovery={'unrelated':{'retained_sentinel':True}})
    target=profile/'addon_data/script.infinity.commandcenter/continue-watching.json';target.parent.mkdir(parents=True);target.write_text(json.dumps(data))
    # This path exists only after the enclosing runner refuses physical devices
    # and any pre-existing installation. No user profile can reach this setup.
    device.adb('push',str(profile)+'/.',device.PROFILE)
    report['test_provider_inputs']=pins
    report['disposable_media']='generated gray clip, synthetic metadata; no real movie playback claim'

def run(root,cycle,mode):
    import xbmc,xbmcaddon,xbmcgui,xbmcvfs
    import android_runtime_checks as ui
    result=dict(passed=False,pid=os.getpid(),selected_mode=mode,selected_features=[mode],cases=[],
                shutdown='NOT RUN',physical_fold_verified=False,final_lock=False)
    path=Path(root);output=path/('navigation-ready-'+cycle+'.json')
    def passed(name,**extra):
        result['cases'].append(dict(case=name,status='PASS',**extra));(path/('navigation-progress-'+cycle+'.json')).write_text(json.dumps(result))
    try:
        ui.require(mode in CASES,'Explicit final-eight selection required')
        ui.until(lambda:(path/('navigation-start-'+cycle+'.json')).exists(),'host admission',300)
        expected=json.loads((Path(__file__).parent/'EXPECTED-COMPONENTS.json').read_text())
        for aid,version in expected.items():ui.require(xbmcaddon.Addon(aid).getAddonInfo('version')==version,'Installed release mismatch: '+aid)
        ccroot=Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('path')))
        uiroot=Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.uirepair').getAddonInfo('path')))
        sys.path.insert(0,str(uiroot));from controller_access import load
        plugin=load();hub=plugin.hub;profile=plugin.PROFILE;home=xbmcgui.Window(10000)
        if mode in SEARCH_CASES:
            providers=['plugin.video.pov'] if mode!='final-search-all-enter' else ['plugin.video.pov','plugin.video.umbrella','plugin.video.seren']
            for aid in providers:
                details=ui.rpc('Addons.GetAddonDetails',{'addonid':aid,'properties':['enabled']})['addon']
                if not details['enabled']:ui.require(ui.rpc('Addons.SetAddonEnabled',{'addonid':aid,'enabled':True})=='OK','Provider not enabled: '+aid)
            ui.complete_first_use(home,result,lambda stage:None,providers=providers)
            for aid in providers:ui.require(ui.first_provider_home(aid,result,lambda stage:None,providers=[aid]),'Provider first-home incomplete: '+aid)
            ui.rpc('GUI.ActivateWindow',{'window':'home'})
            ui.until(lambda:xbmcgui.getCurrentWindowId()==10000,'Home before Search')
            before=hub.load_view(profile)
            (path/('search-ui-ready-'+cycle+'.json')).write_text(json.dumps({'pid':os.getpid(),'mode':mode}))
            # This is the exact Home Search action, not a replacement keyboard
            # or direct search-results RPC. Host sends actual Android input.
            xbmc.executebuiltin('RunScript(script.infinity.commandcenter,universal-search,movie)')
            ui.until(lambda:(path/('search-submitted-'+cycle+'.json')).exists(),'physical Android Search submission',180)
            def results():
                if xbmcgui.getCurrentWindowId()!=10025:return None
                folder=xbmc.getInfoLabel('Container.FolderPath')
                count=int(xbmc.getInfoLabel('Container.NumItems') or 0)
                # This isolated fixture has exactly three providers x40 titles
                # plus group rows. Refuse an unexpected/unbounded UI listing.
                if not 0<count<=200:return None
                records=[dict(tmdb=xbmc.getInfoLabel('Container.ListItemAbsolute(%d).UniqueID(tmdb)'%i),
                              provider=xbmc.getInfoLabel('Container.ListItemAbsolute(%d).Property(Infinity.Search.Provider)'%i))
                         for i in range(count+1)]
                return dict(folder=folder,tmdb_ids=[row['tmdb'] for row in records],
                            provider_attribution=[row['provider'] for row in records]) if search_results_match(mode,folder,records) else None
            visible=ui.until(results,'actual Search results window with verified Matrix TMDb603',180)
            after=hub.load_view(profile)
            for bucket in ('items','watched','watchlist','collection','lists','sources','navigation_recovery'):
                ui.require(after.get(bucket)==before.get(bucket),'Search damaged '+bucket)
            sys.path.insert(0,str(ccroot));from infinity_search import shared_history
            history=shared_history()
            selected='all' if mode=='final-search-all-enter' else 'plugin.video.pov'
            ui.require(any(row['query']=='The Matrix' and row['provider']==selected and row['media']=='movie' for row in history),'Search History submission not persisted')
            passed('actual-search-submission-results-and-history',**visible)
            ui.rpc('Input.Back')
            ui.until(lambda:xbmcgui.getCurrentWindowId()==10000,'Search results back to Home')
            home=xbmcgui.Window(10000)
            def focus():
                ident=home.getFocusId()
                return ident,xbmc.getInfoLabel('Container(%d).CurrentItem'%ident)
            old=focus()
            ui.rpc('Input.Down')
            ui.until(lambda:focus()!=old,'Home accepts navigation after Search',10)
            passed('Home-responsive-after-Search',before_focus=old,after_focus=focus())
        elif mode=='final-participant':
            def receipt():
                try:return json.loads(Path('/data/user/0/com.projectinfinity.kodi/files/checkpoint/installed-participants.json').read_text())
                except (OSError,ValueError):return None
            applied=ui.until(receipt,'actual installed participant receipt')
            ui.require(applied.get('pid')==os.getpid() and applied.get('command_center_version')==expected['script.infinity.commandcenter'] and applied.get('command_center_applied') is True,'CC applied result was not confirmed')
            active=ui.until(lambda:json.loads((profile/'.android-checkpoint/active.json').read_text()) if (profile/'.android-checkpoint/active.json').exists() else None,'resident registration')
            engine=json.loads((profile/'.android-checkpoint/engine.json').read_text())
            ui.require(active.get('pid')==engine.get('pid')==os.getpid() and active.get('owner')==engine.get('owner') and active.get('status')=='ACTIVE' and active.get('addon_version')==expected['script.infinity.commandcenter'],'Resident owner/version mismatch')
            passed('actual-startup-applied-and-resident-registration',installed=applied,active=active)
        elif mode=='final-pov':
            aid='plugin.video.pov';ui.require(xbmcaddon.Addon(aid).getAddonInfo('version')=='6.10.22','POV22 fixture required')
            details=ui.rpc('Addons.GetAddonDetails',{'addonid':aid,'properties':['enabled']})['addon']
            if not details['enabled']:ui.require(ui.rpc('Addons.SetAddonEnabled',{'addonid':aid,'enabled':True})=='OK','POV not enabled')
            ui.complete_first_use(home,result,lambda stage:None,providers=[aid])
            ui.require(ui.first_provider_home(aid,result,lambda stage:None,providers=[aid]),'Provider first-home incomplete')
            sys.path.insert(0,str(ccroot));import saved_navigation as nav
            ready,_=nav.available('tv');provider=next(p for p in ready if p['id']==aid)
            entry=dict(media='tv',season=-1,episode=-1,title='Breaking Bad',identity=hub.show_identity('tvshow',{'tmdb':'1396'}))
            target=nav.direct_destination(entry,provider)
            rows=ui.rpc('Files.GetDirectory',dict(directory=target,media='video',properties=['uniqueid','season','episode','title']))['files']
            valid=[r for r in rows if r.get('type')=='season' and str(r.get('uniqueid',{}).get('tmdb'))=='1396']
            ui.require(valid,'POV22 did not return actual ID-bound seasons')
            for row in valid:nav.destination(provider,row)
            xbmc.executebuiltin('ActivateWindow(Videos,"'+target+'",return)')
            ui.verify_open_folder(target,home);passed('actual-pov22-show-seasons',count=len(valid))
        else:
            before=hub.load_view(profile)
            def list_view(media):
                target='plugin://script.infinity.commandcenter/?action=library&media='+media+'&bucket=continue'
                xbmc.executebuiltin('ActivateWindow(Videos,"'+target+'",return)')
                ui.until(lambda:ui.folder()==target,'actual CC list');xbmc.executebuiltin('Container.SetViewMode(50)',True)
                ui.until(lambda:int(xbmc.getInfoLabel('Container(50).NumItems') or 0)>0,'actual list populated')
                return target
            def popup(key,label):
                began=time.monotonic();xbmc.executebuiltin('RunPlugin(plugin://script.infinity.commandcenter/?action=item-menu&bucket=continue&key='+key+')')
                ui.until(lambda:xbmc.getCondVisibility('System.HasActiveModalDialog') and
                    xbmc.getInfoLabel('Window(%d).Property(Infinity.UI.Popup)'%xbmcgui.getCurrentWindowDialogId())=='1','actual selected item popup')
                elapsed=time.monotonic()-began
                ui.select_native_item(50,lambda:xbmc.getInfoLabel('Container(50).ListItem.Label')==label,label)
                return elapsed
            if mode=='final-continue':
                for media,key,rail,section in [('movie','b'*64,8830,'movies'),('tv','d'*64,8831,'tvshows')]:
                    rows=ui.rpc('Files.GetDirectory',dict(directory='plugin://script.infinity.uirepair/?action=continue&media='+media,media='video',properties=['episode','resume']))['files']
                    ui.require(len(rows)==1,'Home route duplicates '+media)
                    xbmc.executebuiltin('ActivateWindow(Home)');ui.until(lambda:xbmcgui.getCurrentWindowId()==10000,'Home')
                    count=ui.until(lambda:int(xbmc.getInfoLabel('Container(9000).NumItems') or 0),'Home tabs')
                    for index in range(count):
                        xbmc.executebuiltin('SetFocus(9000,%d,absolute)'%index,True)
                        if xbmc.getInfoLabel('Container(9000).ListItem.Property(section)')==section:break
                    else:raise AssertionError('Home tab missing: '+section)
                    ui.until(lambda:xbmc.getCondVisibility('Control.IsVisible(%d)'%rail) and int(xbmc.getInfoLabel('Container(%d).NumItems'%rail) or 0)==1,'actual one-card Home rail')
                    xbmc.executebuiltin('SetFocus(%d,0,absolute)'%rail,True)
                    ui.require(xbmc.getInfoLabel('Container(%d).ListItem.Property(Infinity.ResumeHub.Key)'%rail)==key,'Wrong current resume card')
                    passed('actual-home-one-card-'+media)
                list_view('movie');popup('b'*64,'Remove from Continue Watching')
                ui.until(lambda:not hub.entries(hub.load_view(profile),'movie'),'all movie aliases hidden')
                after=hub.load_view(profile)
                for bucket in ('items','watched','watchlist','collection','lists','sources','navigation_recovery'):ui.require(after[bucket]==before[bucket],'Removal changed '+bucket)
                passed('remove-visible-card-retains-all-records')
                item=xbmcgui.ListItem(label='The Matrix');item.setInfo('video',{'title':'The Matrix','mediatype':'movie'});item.setUniqueIDs({'tmdb':'603','imdb':'tt0133093'})
                xbmc.Player().play(xbmcvfs.translatePath('special://profile/infinity-final-qa.mp4'),item)
                ui.until(lambda:xbmc.Player().isPlayingVideo(),'actual generated-video playback');xbmc.Player().seekTime(70)
                def saved():
                    data=hub.load_view(profile);rows=hub.entries(data,'movie')
                    return data if len(rows)==1 and data['items']['a'*64].get('position',0)>=70 and data['items']['a'*64].get('updated',0)>20 else None
                after=ui.until(saved,'actual playback updates original movie and restores card',45)
                ui.require(after['items']['a'*64]['position']==after['items']['b'*64]['position'],'Alias progress differs')
                for key in ('c'*64,'d'*64):ui.require(after['items'][key]==before['items'][key],'Episode progress changed')
                xbmc.Player().seekTime(3)
                ui.until(lambda:0<=hub.load_view(profile)['items']['a'*64].get('position',-1)<15,'actual deliberate short rewind replaces older progress',15)
                xbmc.Player().stop();passed('actual-new-playback-and-short-rewind-update-original-progress-key')
            else:
                list_view('movie')
                for label,bucket,present in [('Add to Watchlist','watchlist',True),('Remove from Watchlist','watchlist',False),
                    ('Add to Collection','collection',True),('Remove from Collection','collection',False),
                    ('Mark Watched','watched',True),('Mark Unwatched','watched',False)]:
                    elapsed=popup('b'*64,label)
                    ui.until(lambda:bool(hub.load_view(profile)[bucket])==present,'actual '+label)
                    passed(label,popup_seconds=elapsed)
                elapsed=popup('b'*64,'Add to Favorites')
                favourites=ui.rpc('Favourites.GetFavourites',{'properties':['path']})['favourites']
                ui.require(any(r.get('path')=='special://profile/infinity-final-qa.mp4' for r in favourites),'Favourite not added')
                popup('b'*64,'Remove from Favorites')
                ui.require(not any(r.get('path')=='special://profile/infinity-final-qa.mp4' for r in ui.rpc('Favourites.GetFavourites',{'properties':['path']})['favourites']),'Favourite not removed')
                passed('actual-favourites-toggle')
                after=hub.load_view(profile)
                for bucket in ('sources','navigation_recovery','lists'):ui.require(after[bucket]==before[bucket],'Action changed unrelated '+bucket)
                result['physical_gestures']='NOT RUN: first/second tap, hold, selection/scroll require separate Fold acceptance'
        result['passed']=True
    except BaseException as error:
        result['failure']=type(error).__name__+': '+str(error);result['traceback']=__import__('traceback').format_exc()
    finally:output.write_text(json.dumps(result,indent=2))

if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='inputs':inputs(Path(sys.argv[2]),sys.argv[3])
    else:raise SystemExit('Use inputs OUTPUT SELECTED_CASE; runtime is staged by the feature-only runner')
