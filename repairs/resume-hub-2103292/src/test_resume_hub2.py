import json, sys, tempfile, types, unittest, zipfile, hashlib
from pathlib import Path

ROOT=Path('/mnt/data/resumehub/work/script.infinity.commandcenter')
PROFILE=Path(tempfile.mkdtemp(prefix='resume-hub2-tests-'))
sys.path.insert(0,str(ROOT))

class Window:
    props={}
    def __init__(self,id=10000): self.id=id
    def getProperty(self,k): return self.props.get((self.id,k),'')
    def setProperty(self,k,v): self.props[(self.id,k)]=str(v)
    def clearProperty(self,k): self.props.pop((self.id,k),None)
    def getFocusId(self): return 0
class Player:
    def __init__(self): self.playing=False; self.position=120.; self.duration=1200.; self.seeks=[]
    def isPlaying(self): return self.playing
    def isPlayingVideo(self): return self.playing
    def getTime(self): return self.position
    def getTotalTime(self): return self.duration
    def seekTime(self,n): self.seeks.append(n)
class Dialog:
    notifications=[]; selections=[]; inputs=[]; messages=[]
    def notification(self,*a,**k): self.notifications.append(a)
    def select(self,*a,**k): return self.selections.pop(0) if self.selections else -1
    def input(self,*a,**k): return self.inputs.pop(0) if self.inputs else ''
    def ok(self,*a,**k): self.messages.append(a)
class ListItem:
    def __init__(self,label='',label2='',path='',**kw): self.label=label;self.label2=label2;self.path=path;self.props={};self.art={};self.info={};self.context=[];self.ids={}
    def setProperty(self,k,v): self.props[k]=str(v)
    def setInfo(self,k,v): self.info=v
    def setArt(self,v): self.art=v
    def setUniqueIDs(self,v): self.ids=v
    def addContextMenuItems(self,v): self.context.extend(v)
class Addon:
    settings={}
    def __init__(self,*a): pass
    def getSetting(self,k): return self.settings.get(k,'')
    def setSetting(self,k,v): self.settings[k]=v
    def getAddonInfo(self,k): return {'profile':str(PROFILE),'icon':'','version':'0.3.5.19'}.get(k,'')

labels={};conditions={};builtins=[];rpc_calls=[];rpc_responses={};directory=[];resolved=[];categories=[]
xbmc=types.ModuleType('xbmc'); xbmc.Player=Player; xbmc.LOGINFO=1; xbmc.LOGWARNING=2; xbmc.LOGERROR=3
xbmc.log=lambda *a,**k: None
xbmc.getInfoLabel=lambda k: labels.get(k,'')
xbmc.getCondVisibility=lambda k: conditions.get(k,False)
xbmc.executebuiltin=lambda s,*a: builtins.append(s)
xbmc.getSkinDir=lambda:'skin.infinity.diggz'
def rpc(payload):
    p=json.loads(payload); rpc_calls.append(p); return json.dumps(rpc_responses.get(p['method'],{'result':'OK'}))
xbmc.executeJSONRPC=rpc
xbmcgui=types.ModuleType('xbmcgui'); xbmcgui.Window=Window; xbmcgui.Dialog=Dialog; xbmcgui.ListItem=ListItem; xbmcgui.NOTIFICATION_INFO='info'; xbmcgui.NOTIFICATION_WARNING='warning'; xbmcgui.getCurrentWindowId=lambda:10000; xbmcgui.getCurrentWindowDialogId=lambda:9999
xbmcaddon=types.ModuleType('xbmcaddon'); xbmcaddon.Addon=Addon
xbmcvfs=types.ModuleType('xbmcvfs'); xbmcvfs.translatePath=lambda p: str(PROFILE) if p.startswith('special://profile') else ('/tmp/skin' if p=='special://skin' else p)
xbmcplugin=types.ModuleType('xbmcplugin'); xbmcplugin.setContent=lambda *a,**k:None; xbmcplugin.setPluginCategory=lambda *a,**k:categories.append(a); xbmcplugin.addDirectoryItem=lambda h,url,li,**k:directory.append((url,li,k)); xbmcplugin.endOfDirectory=lambda *a,**k:None; xbmcplugin.setResolvedUrl=lambda *a,**k:resolved.append(a)
for n,m in [('xbmc',xbmc),('xbmcgui',xbmcgui),('xbmcaddon',xbmcaddon),('xbmcvfs',xbmcvfs),('xbmcplugin',xbmcplugin)]: sys.modules[n]=m

import common, resume_hub as hub, service, experience
saved=sys.argv; sys.argv=['plugin.py','9','?action=resume']; import plugin; sys.argv=saved

class ResumeHub2Tests(unittest.TestCase):
    def setUp(self):
        Window.props.clear(); Addon.settings.clear(); labels.clear(); conditions.clear(); builtins.clear(); rpc_calls.clear(); rpc_responses.clear(); directory.clear(); resolved.clear(); categories.clear(); Dialog.selections.clear(); Dialog.inputs.clear(); Dialog.notifications.clear()
        for p in PROFILE.glob('*.json'): p.unlink()
        self.movie={'type':'movie','id':42,'title':'Arrival','uniqueid':{'tmdb':'329865','imdb':'tt2543164'},'file':'plugin://plugin.video.example/?play=329865','art':{'poster':'https://image.tmdb.org/t/p/original/a.jpg','fanart':'https://image.tmdb.org/t/p/original/b.jpg'}}
        rpc_responses['Player.GetActivePlayers']={'result':[{'playerid':1,'type':'video'}]}
        rpc_responses['Player.GetItem']={'result':{'item':self.movie}}
        rpc_responses['Player.GetProperties']={'result':{'currentaudiostream':{},'currentsubtitle':{},'subtitleenabled':False,'audiostreams':[],'subtitles':[],'speed':1}}
        self.player=service.InfinityPlayer(PROFILE)

    def start(self): self.player.playing=True; self.player.onAVStarted(); self.player.poll()
    def data(self): return hub.load(PROFILE)

    def test_schema1_migrates_in_place(self):
        key='a'*64; (PROFILE/'continue-watching.json').write_text(json.dumps({'schema':1,'items':{key:{'key':key,'media':'movie','title':'Old'}},'sources':{}}))
        d=hub.load(PROFILE); self.assertEqual(d['schema'],2); self.assertIn(key,d['items']); self.assertIn('watched',d); self.assertIn('lists',d)

    def test_completion_moves_progress_to_watched(self):
        self.start(); key=next(iter(self.data()['items']))
        self.player.onPlayBackEnded(); d=self.data(); self.assertNotIn(key,d['items']); self.assertIn(key,d['watched']); self.assertEqual(d['watched'][key]['percentage'],100.0); self.assertEqual(d['watched'][key]['play_count'],1)

    def test_95_percent_stop_marks_watched(self):
        self.player.position=1145.; self.player.duration=1200.; self.start(); self.player.onPlayBackStopped(); d=self.data(); self.assertFalse(d['items']); self.assertEqual(len(d['watched']),1)

    def test_partial_rewatch_can_be_in_progress_and_still_watched(self):
        self.start(); self.player.onPlayBackEnded(); watched_key=next(iter(self.data()['watched']))
        self.player=service.InfinityPlayer(PROFILE); self.player.playing=True; self.player.position=240.; self.player.duration=1200.; self.player.onAVStarted(); self.player.poll(); d=self.data(); self.assertIn(watched_key,d['watched']); self.assertIn(watched_key,d['items'])

    def test_manual_watched_unwatched(self):
        self.start(); d=self.data(); key=next(iter(d['items'])); entry=d['items'][key]
        d,e=hub.mark_watched_data(d,key,entry); self.assertIsNotNone(e); hub.save(PROFILE,d); self.assertIn(key,self.data()['watched']); self.assertNotIn(key,self.data()['items'])
        d,e=hub.mark_unwatched_data(self.data(),key); hub.save(PROFILE,d); self.assertNotIn(key,self.data()['watched'])

    def test_watchlist_collection_rating_and_custom_list(self):
        self.start(); d=self.data(); key=next(iter(d['items']))
        d,added,e=hub.toggle_watchlist_data(d,key); self.assertTrue(added); d,added,e=hub.toggle_collection_data(d,key); self.assertTrue(added)
        d,r=hub.set_rating_data(d,key,9); self.assertEqual(r['rating'],9); d,e=hub.add_to_list_data(d,key,'Friday Night'); self.assertIsNotNone(e); hub.save(PROFILE,d); d=self.data()
        self.assertIn(key,d['watchlist']); self.assertIn(key,d['collection']); self.assertEqual(d['ratings'][key]['rating'],9); self.assertIn(key,d['lists']['Friday Night'])

    def test_next_episode_candidate_after_completed_episode(self):
        self.movie.update(type='episode',title='Pilot',showtitle='Example Show',season=1,episode=2,uniqueid={'tmdb':'999'})
        self.start(); self.player.onPlayBackEnded(); values=hub.next_episodes(self.data()); self.assertEqual(len(values),1); self.assertEqual(values[0]['season'],1); self.assertEqual(values[0]['episode'],3); self.assertTrue(values[0]['synthetic_next'])

    def test_progress_shows_prefers_in_progress(self):
        self.movie.update(type='episode',title='Episode 2',showtitle='Example Show',season=1,episode=2,uniqueid={'tmdb':'999'})
        self.start(); self.player.onPlayBackEnded()
        self.player=service.InfinityPlayer(PROFILE); self.movie['episode']=3; self.movie['title']='Episode 3'; self.player.playing=True; self.player.onAVStarted(); self.player.poll()
        values=hub.progress_shows(self.data()); self.assertEqual(len(values),1); self.assertEqual(values[0]['episode'],3)

    def test_watched_listitem_drives_kodi_overlay_and_starts_fresh(self):
        self.start(); self.player.onPlayBackEnded(); d=self.data(); entry=next(iter(d['watched'].values())); target,li=plugin._list_item(entry,d,'history','')
        self.assertEqual(li.info['playcount'],1); self.assertEqual(li.info['overlay'],6); self.assertEqual(li.props['ResumeTime'],'0'); self.assertEqual(li.props['Infinity.ResumeHub.Watched'],'true'); self.assertEqual(li.props['PlayCount'],'1'); self.assertEqual(li.props['Overlay'],'6'); self.assertEqual(li.props['Watched'],'true'); self.assertEqual(li.props['Infinity.ResumeHub.State'],'watched'); self.assertEqual(li.ids['tmdb'],'329865')

    def test_in_progress_watched_rewatch_keeps_resume(self):
        self.start(); self.player.onPlayBackEnded(); self.player=service.InfinityPlayer(PROFILE); self.player.playing=True; self.player.position=300.; self.player.duration=1200.; self.player.onAVStarted(); self.player.poll(); d=self.data(); entry=next(iter(d['items'].values())); target,li=plugin._list_item(entry,d,'continue',''); self.assertEqual(li.info['playcount'],1); self.assertEqual(li.props['ResumeTime'],'300.0')

    def test_navigators_are_local_and_trakt_optional(self):
        plugin.navigator('movie'); urls=[x[0] for x in directory]; self.assertTrue(any('bucket=watchlist' in u for u in urls)); self.assertTrue(all('plugin.video.umbrella' not in u for u in urls))
        directory.clear(); plugin.navigator('tv'); urls=[x[0] for x in directory]; self.assertTrue(any('bucket=next' in u for u in urls)); self.assertTrue(any('bucket=progress' in u for u in urls)); self.assertTrue(all('plugin.video.umbrella' not in u for u in urls))

    def test_context_has_required_manual_controls(self):
        self.start(); d=self.data(); e=next(iter(d['items'].values())); labels=[x[0] for x in plugin._context(e,d,'continue','')]
        for wanted in ('Mark Watched','Reset Progress','Add to Watchlist','Add to Collection','Rate','Add to Custom List','Remove from Continue Playing'): self.assertIn(wanted,labels)

    def test_kodi_library_playcount_bridge_when_dbid_exists(self):
        self.start(); self.player.onPlayBackEnded(); calls=[x for x in rpc_calls if x['method']=='VideoLibrary.SetMovieDetails']; self.assertEqual(len(calls),1); self.assertEqual(calls[0]['params']['movieid'],42); self.assertEqual(calls[0]['params']['playcount'],1)

    def test_home_counts_include_resume_hub_state(self):
        self.start(); self.player.onPlayBackEnded(); home=Window(10000); self.assertEqual(home.getProperty('Infinity.WatchedMovies'),'1'); self.assertTrue(home.getProperty('Infinity.ResumeHubRevision'))

class SkinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=Path('/mnt/data/resumehub/Infinity-1.0.5.181-Native-Responsive-Layout-RC1.zip')
        cls.candidate=Path('/mnt/data/resumehub/skin182-build/Infinity-1.0.5.182-Resume-Hub-2-RC1.zip')
        cls.profiles=('16x9','20x9','6x5','5x6','portrait','fallback','responsive/base','responsive/wide','responsive/ultrawide','responsive/landscape','responsive/square','responsive/portrait','responsive/tall')
    def test_all_home_profiles_have_both_new_and_old_sections(self):
        with zipfile.ZipFile(self.candidate) as z:
            for d in self.profiles:
                text=z.read('skin.infinity.diggz/'+d+'/Home.xml').decode()
                self.assertIn('<label>TRAKT MOVIES</label>',text); self.assertIn('<label>TRAKT TV</label>',text)
                self.assertIn('<label>INFINITY MOVIES</label>',text); self.assertIn('<label>INFINITY TV</label>',text)
                self.assertIn('<property name="hubsource">trakt</property>',text); self.assertIn('<property name="hubsource">infinity</property>',text)
    def test_all_responsive_universes_have_local_path_variables(self):
        with zipfile.ZipFile(self.candidate) as z:
            for d in ('responsive/base','responsive/wide','responsive/ultrawide','responsive/landscape','responsive/square','responsive/portrait','responsive/tall'):
                text=z.read('skin.infinity.diggz/'+d+'/Includes_InfinityHomeUnified.xml').decode()
                for token in ('InfinityMoviesPrimaryPath','InfinityMoviesSecondaryPath','InfinityTVPrimaryPath','InfinityTVSecondaryPath','InfinityResumeHubWatchedState','action=library&amp;media=movie','action=library&amp;media=tv'): self.assertIn(token,text)
    def test_player_and_non_scoped_files_byte_identical(self):
        with zipfile.ZipFile(self.parent) as a, zipfile.ZipFile(self.candidate) as b:
            changed=[]
            for n in a.namelist():
                if n.endswith('/') or n not in b.namelist(): continue
                if a.read(n)!=b.read(n): changed.append(n)
            allowed=lambda n: n.endswith('/Home.xml') or n.endswith('/Includes_InfinityHomeUnified.xml') or n in ('skin.infinity.diggz/addon.xml','skin.infinity.diggz/infinity-skin.json','skin.infinity.diggz/Infinity-Protected-Manifest.json')
            unexpected=[n for n in changed if not allowed(n)]
            self.assertEqual(unexpected,[])
            self.assertFalse(any('VideoOSD' in n or '/DialogVideo' in n or '/MyVideo' in n for n in changed))
    def test_candidate_crc_and_version(self):
        with zipfile.ZipFile(self.candidate) as z:
            self.assertIsNone(z.testzip()); addon=z.read('skin.infinity.diggz/addon.xml').decode(); self.assertIn('version="1.0.5.182"',addon); self.assertIn('script.infinity.commandcenter" version="0.3.5.19"',addon)

if __name__=='__main__': unittest.main(verbosity=2)
