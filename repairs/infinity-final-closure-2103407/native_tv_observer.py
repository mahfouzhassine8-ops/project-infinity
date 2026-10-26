"""Actual native TV playback and next-episode checks in the admitted observer."""
from copy import deepcopy
import time

FOLDER='/storage/emulated/0/Android/data/com.projectinfinity.kodi/files/.kodi/userdata/infinity-cw-qa/'
DIRECTORY='plugin://script.infinity.commandcenter/?action=library&media=tv&bucket=next'


def tracking_ready(value,previous):
    """Original title navigation survives; actual played file belongs to sources."""
    row=value.get('items',{}).get('d'*64,{})
    source=value.get('sources',{}).get('d'*64,{})
    occurrence=row.get('playback_occurrence')
    return (isinstance(occurrence,str) and len(occurrence)==32 and
            all(ch in '0123456789abcdef' for ch in occurrence) and occurrence!=previous and
            row.get('identity')==dict(schema=1,kind='episode',scope='show_episode',
                ids={'tmdb':'1396'},season=1,episode=2) and row.get('show_ids_verified') is True and
            source.get('route')==FOLDER+'QA.S01E02.mp4' and source.get('failures')==0)


def source_memory_preserved(before,after,played_key,actual_source):
    """Only the genuinely played title may acquire its new successful source."""
    if not isinstance(before,dict) or not isinstance(after,dict):return False
    if set(after)-set(before)-{played_key}:return False
    if any(after.get(key)!=value for key,value in before.items() if key!=played_key):return False
    selected=after.get(played_key)
    return (isinstance(selected,dict) and selected.get('route')==actual_source and
            selected.get('failures')==0 and type(selected.get('updated')) is int and selected['updated']>0)


def run(ui,hub,profile,result,observe=None,phase='all'):
    import xbmc
    if phase not in ('all','progress','completion'):raise ValueError('Explicit TV scene phase required')
    def stage(name):
        if observe is not None:observe(name)
    def passed(name,**fields):
        result['cases'].append(dict(case=name,status='PASS',**fields))
        stage(name)
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
        old_occurrence=state().get('items',{}).get('d'*64,{}).get('playback_occurrence')
        began=time.monotonic()
        ui.rpc('Player.Open',{'item':{'episodeid':dbid},'options':{'resume':False}})
        def started():
            if not player.isPlayingVideo():return None
            value=ui.rpc('Player.GetItem',{'playerid':1,'properties':['season','episode','file','uniqueid','showtitle']})['item']
            if not(value.get('type')=='episode' and value.get('id')==dbid and value.get('season')==season and value.get('episode')==episode):return None
            # A typed selected item may precede decoder/AV clock readiness.
            # Keep the same20sec start deadline; never seek during initial
            # codec opening merely because isPlayingVideo already became true.
            clock=ui.rpc('Player.GetProperties',{'playerid':1,'properties':['time','speed']})
            stamp=clock.get('time',{})
            armed=tracking_ready(state(),old_occurrence)
            return value if armed and clock.get('speed')==1 and (stamp.get('seconds',0)>=1 or stamp.get('minutes',0)>0) else None
        value=ui.until(started,'actual typed native TV playback',max(0,20-(time.monotonic()-began)))
        result.setdefault('native_tv_tracking_ready',[]).append(dict(episodeid=dbid,
            elapsed_ms=(time.monotonic()-began)*1000,actual_occurrence=state()['items']['d'*64]['playback_occurrence']))
        return value
    if phase in ('all','progress'):
        stage('before-first-native-playback')
        result['native_tv_first_playback']=start(1,1,2)
        stage('before-first-test-seek')
        player.seekTime(70)
        stage('awaiting-exact-saved-TV-progress')
        def saved():
            value=state();row=value.get('items',{}).get('d'*64,{})
            return value if row.get('position',0)>=70 and row.get('show_ids_verified') is True and row.get('show_tmdb')=='1396' else None
        progress=ui.until(saved,'actual exact TV position saved',45)
        row=progress['items']['d'*64]
        ui.require(row['identity']=={'schema':1,'kind':'episode','scope':'show_episode','ids':{'tmdb':'1396'},'season':1,'episode':2},'TV canonical identity')
        ui.require(progress['items']['c'*64]==before['items']['c'*64],'Different episode progress preserved')
        stage('before-native-Stop-request')
        ui.rpc('Player.Stop',{'playerid':1})
        stage('native-Stop-acknowledged')
        ui.until(lambda:not active(),'native TV stop',20)
        restored=state()['items']['d'*64]
        ui.require(restored['position']>=70 and restored.get('verified_next',{}).get('after')==[1,2],
                   'Stopped TV retains exact progress and catalogue successor')
        rows=ui.rpc('Files.GetDirectory',{'directory':DIRECTORY,'media':'video','properties':['season','episode','resume']})['files']
        result['native_tv_in_progress_rows']=rows
        ui.require(len(rows)==1 and rows[0].get('season')==1 and rows[0].get('episode')==2,
                   'Next shows most recently played episode, not an older higher number')
        passed('actual-native-TV-stop-progress-restoration',position=restored['position'])
        if phase=='progress':return
    start(1,1,2);player.seekTime(175)
    def completed():
        value=state();row=value.get('watched',{}).get('d'*64,{})
        return value if row.get('watched') is True and row.get('percentage')==100 else None
    complete=ui.until(completed,'actual TV completion and watched state',45)
    if player.isPlayingVideo():ui.rpc('Player.Stop',{'playerid':1})
    ui.until(lambda:not active(),'native completed TV stopped',20)
    complete=state();result['native_tv_completed_record']=complete['watched']['d'*64]
    for key in ('c'*64,'d'*64):ui.require(key in complete['items'],'Completed history must remain stored')
    ui.require(not hub.entries(complete,'tv'),'Completed episode is removed from Continue Playing')
    for key in ('a'*64,'b'*64):ui.require(complete['items'][key]==before['items'][key],'Movie progress preserved by TV playback')
    for bucket in ('watchlist','collection','lists','navigation_recovery','later'):
        ui.require(complete.get(bucket)==before.get(bucket),'TV playback preserves '+bucket)
    ui.require(source_memory_preserved(before.get('sources',{}),complete.get('sources',{}),
               'd'*64,FOLDER+'QA.S01E02.mp4'),'TV preserves unrelated source memory and remembers actual played source')
    result['native_tv_source_memory']=dict(before=before.get('sources',{}),after=complete.get('sources',{}))
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
    ui.rpc('Player.Stop',{'playerid':1});ui.until(lambda:not active(),'selected Next stopped',20)
    passed('actual-native-Next-selection-plays-correct-episode',observed=observed)
