"""Actual native TV playback and next-episode checks in the admitted observer."""
from copy import deepcopy
import time

FOLDER='/storage/emulated/0/Android/data/com.projectinfinity.kodi/files/.kodi/userdata/infinity-cw-qa/'
DIRECTORY='plugin://script.infinity.commandcenter/?action=library&media=tv&bucket=next'


def run(ui,hub,profile,result):
    import xbmc
    def passed(name,**fields):
        result['cases'].append(dict(case=name,status='PASS',**fields))
    def state():return hub.load_view(profile)
    def active():return ui.rpc('Player.GetActivePlayers')
    ui.until(lambda:not active(),'original clip stopped before native TV',20)
    before=deepcopy(state())
    show=ui.rpc('VideoLibrary.GetTVShowDetails',{'tvshowid':1,'properties':['title','uniqueid']})['tvshowdetails']
    ui.require(show['tvshowid']==1 and show['uniqueid'].get('tmdb')=='1396','Native exact parent series identity')
    for dbid,season,episode,file in [(1,1,2,'QA.S01E02.mp4'),(2,2,1,'QA.S02E01.mp4')]:
        row=ui.rpc('VideoLibrary.GetEpisodeDetails',{'episodeid':dbid,
            'properties':['season','episode','tvshowid','file','uniqueid']})['episodedetails']
        ui.require((row['episodeid'],row['tvshowid'],row['season'],row['episode'],row['file'])==
                   (dbid,1,season,episode,FOLDER+file),'Actual native catalogue coordinates/source')
    player=xbmc.Player()
    def start(dbid,season,episode):
        ui.rpc('Player.Open',{'item':{'episodeid':dbid},'options':{'resume':False}})
        def started():
            if not player.isPlayingVideo():return None
            value=ui.rpc('Player.GetItem',{'playerid':1,'properties':['season','episode','file','uniqueid','showtitle']})['item']
            return value if value.get('type')=='episode' and value.get('id')==dbid and value.get('season')==season and value.get('episode')==episode else None
        return ui.until(started,'actual typed native TV playback',20)
    result['native_tv_first_playback']=start(1,1,2)
    player.seekTime(70)
    def saved():
        value=state();row=value.get('items',{}).get('d'*64,{})
        return value if row.get('position',0)>=70 and row.get('show_ids_verified') is True and row.get('show_tmdb')=='1396' else None
    progress=ui.until(saved,'actual exact TV position saved',45)
    row=progress['items']['d'*64]
    ui.require(row['identity']=={'schema':1,'kind':'episode','scope':'show_episode','ids':{'tmdb':'1396'},'season':1,'episode':2},'TV canonical identity')
    ui.require(progress['items']['c'*64]==before['items']['c'*64],'Different episode progress preserved')
    player.stop();ui.until(lambda:not active(),'native TV stop',20)
    restored=state()['items']['d'*64]
    ui.require(restored['position']>=70 and restored.get('verified_next',{}).get('after')==[1,2],
               'Stopped TV retains exact progress and catalogue successor')
    rows=ui.rpc('Files.GetDirectory',{'directory':DIRECTORY,'media':'video','properties':['season','episode','resume']})['files']
    result['native_tv_in_progress_rows']=rows
    ui.require(len(rows)==1 and rows[0].get('season')==1 and rows[0].get('episode')==2,
               'Next shows most recently played episode, not an older higher number')
    passed('actual-native-TV-stop-progress-restoration',position=restored['position'])
    start(1,1,2);player.seekTime(175)
    def completed():
        value=state();row=value.get('watched',{}).get('d'*64,{})
        return value if row.get('watched') is True and row.get('percentage')==100 else None
    complete=ui.until(completed,'actual TV completion and watched state',45)
    if player.isPlayingVideo():player.stop()
    ui.until(lambda:not active(),'native completed TV stopped',20)
    complete=state();result['native_tv_completed_record']=complete['watched']['d'*64]
    for key in ('c'*64,'d'*64):ui.require(key in complete['items'],'Completed history must remain stored')
    ui.require(not hub.entries(complete,'tv'),'Completed episode is removed from Continue Playing')
    for key in ('a'*64,'b'*64):ui.require(complete['items'][key]==before['items'][key],'Movie progress preserved by TV playback')
    for bucket in ('watchlist','collection','lists','sources','navigation_recovery','later'):
        ui.require(complete.get(bucket)==before.get(bucket),'TV playback preserves '+bucket)
    began=time.monotonic()
    rows=ui.rpc('Files.GetDirectory',{'directory':DIRECTORY,'media':'video',
        'properties':['season','episode','resume','uniqueid','showtitle']})['files']
    result['native_tv_successor_rows']=rows
    ui.require(len(rows)==1 and rows[0].get('season')==2 and rows[0].get('episode')==1,
               'Correct actual catalogue successor across season boundary; no guessed E+1')
    target=rows[0].get('file','')
    ui.require(target and 'action=unavailable' not in target,'Next episode must have a genuinely usable source')
    ui.require(not active(),'Next restoration must not autoplay')
    passed('actual-native-TV-completion-next-restoration',elapsed_ms=(time.monotonic()-began)*1000,
           source=target,synthetic_metadata_and_generated_clip=True)
    ui.rpc('Player.Open',{'item':{'file':target},'options':{'resume':False}})
    def correct_next_playback():
        if not player.isPlayingVideo():return None
        value=ui.rpc('Player.GetItem',{'playerid':1,'properties':['season','episode','file','uniqueid','showtitle']})['item']
        return value if (value.get('type')=='episode' and value.get('id')==2 and value.get('season')==2 and
                         value.get('episode')==1 and value.get('file')==FOLDER+'QA.S02E01.mp4') else None
    observed=ui.until(correct_next_playback,'actual selected Next starts exact native episode/source',20)
    player.stop();ui.until(lambda:not active(),'selected Next stopped',20)
    passed('actual-native-Next-selection-plays-correct-episode',observed=observed)
