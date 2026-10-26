"""Actual signed416 functions: exact identity, real resolver guards, helper epochs."""
import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import sys
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit,urlencode
from zipfile import ZipFile

import patch_continue_fast_home as correction
from test_continue_completion import pure


def functions(raw,names,scope):
    nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual417.py','exec'),scope)
    return scope


class ContinueFastHomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(os.environ['INFINITY_FAST_HOME_PARENT_APK']) as z:
            cls.raw={n:z.read('assets/addons/'+correction.CC+'/'+n) for n in
                     ('service.py','resume_hub.py','plugin.py','addon.xml','experience.py')}
            prefix='assets/addons/'+correction.SKIN+'/'
            cls.skin={n[len(prefix):]:z.read(n) for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
        cls.updated={n:correction.patch(n,cls.raw[n]) for n in ('service.py','resume_hub.py','plugin.py','addon.xml')}
        cls.before=pure(cls.raw['resume_hub.py']);cls.after=pure(cls.updated['resume_hub.py'])
        cls.experience=ModuleType('experience');scope=dict(re=re,urlsplit=urlsplit)
        functions(cls.raw['experience.py'],['stable_route'],scope);cls.experience.stable_route=scope['stable_route']

    def row(self,season=1,episode=2,updated=4,flags=True,**fields):
        identity=self.after.media_identity('tv',{},season,episode,{'tmdb':'1396'})
        row=dict(key=self.after.identity_key(identity),media='tv',identity=identity,season=season,episode=episode,
                 title='Breaking Bad',showtitle='Breaking Bad',tmdb='1396',updated=updated,position=60,duration=180,
                 source='/actual/episode.mp4',playback_occurrence='1'*32)
        if flags:row.update(show_ids_verified=True,show_tmdb='1396')
        row.update(fields);return row

    def candidate(self):
        proof=dict(verified=True,after=[1,2],show_tmdb='1396',season=2,episode=1,
                   library=dict(episodeid=2,tvshowid=1,file='/actual/next.mp4',show_tmdb='1396',season=2,episode=1))
        row=self.row(verified_next=proof);data,_=self.after.mark_watched_data(
            dict(schema=2,items={row['key']:row}),row['key'],row,completed=True)
        return self.after.next_episodes(data)[0],data

    def test_original_fixture_parent_groups_and_recent_earlier_episode_next_agree(self):
        for flags in (False,True):
            rows=[self.row(episode=3,updated=3,flags=flags),self.row(episode=2,updated=4,flags=flags)]
            data=dict(schema=2,items={r['key']:r for r in rows});before=deepcopy(data)
            self.assertEqual(self.after.entries(data,'tv')[0]['episode'],2)
            self.assertEqual([x['episode'] for x in self.after.next_episodes(data)],[2])
            self.assertEqual([x['episode'] for x in self.after.progress_shows(data)],[2])
            self.assertEqual(data,before)
            original=[x['episode'] for x in self.before.next_episodes(data)]
            self.assertEqual(original,[3] if flags else [2,3])

    def test_revision_orders_same_second_replay_and_current_watched_completion(self):
        rows=[self.row(episode=8,updated=100,resume_revision=5),self.row(episode=2,updated=100,resume_revision=6)]
        data=dict(schema=2,items={r['key']:r for r in rows})
        self.assertEqual(self.after.next_episodes(data)[0]['episode'],2)
        early=self.row(updated=200,watched_at=200,verified_next=dict(verified=True,after=[1,2],show_tmdb='1396',season=1,episode=3))
        later=self.row(season=3,episode=9,updated=100,watched_at=100,verified_next=dict(verified=True,after=[3,9],show_tmdb='1396',season=4,episode=1))
        data=dict(schema=2,watched={r['key']:r for r in (early,later)})
        nxt=self.after.next_episodes(data);self.assertEqual([(v['season'],v['episode']) for v in nxt],[(1,3)])

    def test_namespace_and_conflicting_parent_metadata_are_not_title_merged(self):
        a=self.row();b=self.row();b['identity']=self.after.media_identity('tv',{},1,2,{'tvdb':'1396'})
        b.update(key=self.after.identity_key(b['identity']),show_tmdb='',show_tvdb='1396')
        data=dict(schema=2,items={r['key']:r for r in (a,b)})
        self.assertEqual(len(self.after.next_episodes(data)),2)
        bad=self.row(show_tmdb='999');self.assertFalse(self.after.continue_series_ids(bad))

    def native_catalogue(self,catalogue=None):
        if catalogue is None:catalogue=[dict(episodeid=1,season=1,episode=2,file='/actual/episode.mp4'),
                                        dict(episodeid=2,season=2,episode=1,file='/actual/next.mp4')]
        calls=[]
        def rpc(method,params):
            calls.append((method,params))
            if method=='VideoLibrary.GetEpisodeDetails':return dict(result=dict(episodedetails=dict(episodeid=1,season=1,episode=2,showtitle='Breaking Bad',tvshowid=1)))
            if method=='VideoLibrary.GetTVShowDetails':return dict(result=dict(tvshowdetails=dict(tvshowid=1,title='Breaking Bad',uniqueid={'tmdb':'1396'})))
            if method=='VideoLibrary.GetEpisodes':return dict(result=dict(episodes=catalogue,limits={'total':len(catalogue)}))
            raise AssertionError('Unexpected native request '+method)
        scope=dict(xbmc=SimpleNamespace(getCondVisibility=lambda _:True),jsonrpc=rpc,hub=self.after)
        functions(self.updated['service.py'],['_continue_show_identity'],scope)
        with patch.dict(sys.modules,{'experience':self.experience}):value=scope['_continue_show_identity']('episode',1,1,2,'Breaking Bad')
        return value,calls

    def test_only_single_exact_native_catalogue_row_grants_local_successor(self):
        result,calls=self.native_catalogue();proof=result['verified_next']['library']
        self.assertEqual(proof,dict(episodeid=2,tvshowid=1,file='/actual/next.mp4',show_tmdb='1396',season=2,episode=1))
        self.assertEqual(calls[-1][1]['properties'],['season','episode','file'])
        bads=[dict(episodeid=True,season=2,episode=1,file='/actual/next.mp4'),
              dict(episodeid=2,season=2,episode=1,file='https://stale/stream'),
              dict(episodeid=2,season=2,episode=1,file='plugin://unverified/provider')]
        for bad in bads:
            result,_=self.native_catalogue([dict(episodeid=1,season=1,episode=2,file='/actual/episode.mp4'),bad])
            self.assertNotIn('library',result['verified_next'])
        row=dict(episodeid=2,season=2,episode=1,file='/actual/next.mp4')
        result,_=self.native_catalogue([dict(episodeid=1,season=1,episode=2),row,dict(row,episodeid=3)])
        self.assertNotIn('library',result['verified_next'])

    def resolver(self,entry,data,episode_change=None,show_change=None,exists=True,skin='skin.infinity.diggz'):
        calls=[];resolved=[];built=[]
        episode=dict(episodeid=2,tvshowid=1,season=2,episode=1,file='/actual/next.mp4',title='Correct next episode',
                     showtitle='Breaking Bad',uniqueid={'tmdb':'900000020001'},plot='Full original plot',runtime=180,art={'thumb':'local.jpg'})
        episode.update(episode_change or {});show=dict(tvshowid=1,uniqueid={'tmdb':'1396'});show.update(show_change or {})
        def rpc(method,params):
            calls.append((method,params))
            if method=='VideoLibrary.GetEpisodeDetails':return dict(episodedetails=episode)
            if method=='VideoLibrary.GetTVShowDetails':return dict(tvshowdetails=show)
            raise AssertionError('Unexpected RPC '+method)
        class Item:
            def __init__(self,**kwargs):self.args=kwargs;self.info={};self.ids={};built.append(self)
            def setInfo(self,kind,value):self.info=value
            def setUniqueIDs(self,value):self.ids=value
            def setArt(self,value):self.art=value
        scope=dict(xbmc=SimpleNamespace(getSkinDir=lambda:skin),hub=self.after,PROFILE='/test/profile',_rpc=rpc,
                   stable_route=self.experience.stable_route,number=lambda v:float(v or 0),HANDLE=123,
                   xbmcgui=SimpleNamespace(ListItem=Item),xbmcplugin=SimpleNamespace(setResolvedUrl=lambda *v:resolved.append(v)))
        hub=SimpleNamespace(**vars(self.after));hub.load_view=lambda _:deepcopy(data);scope['hub']=hub
        functions(self.updated['plugin.py'],['_local_next_proof','play_local_next'],scope)
        with patch.dict(sys.modules,{'xbmcvfs':SimpleNamespace(exists=lambda _:exists)}):answer=scope['play_local_next'](entry['key'])
        return answer,calls,resolved,built

    def test_user_selected_local_successor_is_freshly_native_verified_and_resolved(self):
        entry,data=self.candidate();answer,calls,resolved,built=self.resolver(entry,data)
        self.assertTrue(answer);self.assertEqual(len(calls),2);self.assertEqual(resolved,[(123,True,built[0])])
        self.assertEqual(built[0].args['path'],'/actual/next.mp4');self.assertEqual(built[0].info['dbid'],2)
        self.assertEqual((built[0].info['season'],built[0].info['episode']),(2,1))
        self.assertEqual(built[0].ids,{'tmdb':'900000020001'})

    def test_stale_reused_source_ids_series_coords_missing_file_and_cobra_fail_closed(self):
        entry,data=self.candidate()
        bads=[dict(episode_change={name:value}) for name,value in [('episodeid',3),('episodeid',True),
              ('tvshowid',2),('season',1),('episode',2),('file','/stale/replaced.mp4')]]
        bads += [dict(show_change={'uniqueid':{'tmdb':'999'}}),dict(exists=False),dict(skin='skin.cobra')]
        for values in bads:
            answer,calls,resolved,built=self.resolver(entry,data,**values)
            self.assertFalse(answer);self.assertEqual(resolved,[]);self.assertEqual(built,[])
        answer,calls,resolved,_=self.resolver(entry,dict(schema=2,items={},watched={}))
        self.assertFalse(answer);self.assertEqual(calls,[]);self.assertEqual(resolved,[])

    def test_rendering_only_selects_route_no_playback_or_remote_request(self):
        entry,_=self.candidate();scope=dict(hub=self.after,stable_route=self.experience.stable_route,
            _url=lambda **v:'plugin://script.infinity.commandcenter/?'+urlencode(v),
            _has_tmdb_helper=lambda _:False,number=lambda v:float(v or 0))
        functions(self.updated['plugin.py'],['_local_next_proof','_target'],scope)
        render=dict(source_memory=False)
        target=scope['_target'](entry,render=render)
        self.assertIn('action=play-local-next&key=',target)
        entry.pop('library_next');self.assertEqual(scope['_target'](entry,render=render),'')
        scope['_has_tmdb_helper']=lambda _:True
        self.assertEqual(scope['_target'](entry,render=render),
            'plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=tv&tmdb_id=1396&season=2&episode=1')

    def epoch(self,continuity=False,ambient=False,skin='skin.infinity.diggz',window=10000,reject=False):
        state={};events=[];tokens=iter(('a'*32,'b'*32))
        if continuity:state['Infinity.Home.Continuity.Pending']='true'
        if ambient:state['Infinity.Home.Ambient.Pending']='true'
        def current():
            events.append(('authenticated',))
            if reject:raise RuntimeError('obsolete generation')
        home=SimpleNamespace(getProperty=lambda k:state.get(k,''),
            setProperty=lambda k,v:(state.__setitem__(k,v),events.append((k,v))),clearProperty=lambda k:state.pop(k,None))
        scope=dict(xbmc=SimpleNamespace(getSkinDir=lambda:skin),xbmcgui=SimpleNamespace(getCurrentWindowId=lambda:window),
                   HOME=home,uuid=SimpleNamespace(uuid4=lambda:SimpleNamespace(hex=next(tokens))),log=lambda _:None)
        functions(self.updated['service.py'],['_consume_home_observer_epoch'],scope)
        with patch.dict(sys.modules,{'module_contract':SimpleNamespace(require_current=current)}):
            answer=scope['_consume_home_observer_epoch']();again=scope['_consume_home_observer_epoch']()
        return answer,again,state,events

    def test_exact_original_home_tokens_are_coalesced_in_existing_authenticated_resident(self):
        for c,a in ((True,True),(True,False),(False,True)):
            answer,again,state,events=self.epoch(c,a);self.assertTrue(answer);self.assertFalse(again)
            self.assertEqual(events[0],('authenticated',));self.assertEqual(len(events),1+int(c)+int(a))
            self.assertEqual('Infinity.Continuity.HomeLoad' in state,c)
            self.assertEqual('Infinity.NativeAmbient.LayoutEpoch' in state,a)
        for values in (dict(),dict(continuity=True,skin='skin.cobra'),dict(ambient=True,window=10025)):
            self.assertFalse(self.epoch(**values)[0]);self.assertEqual(self.epoch(**values)[3],[])
        answer,_,state,events=self.epoch(True,True,reject=True)
        self.assertFalse(answer);self.assertIn('Infinity.Home.Ambient.Pending',state)
        self.assertNotIn('Infinity.NativeAmbient.LayoutEpoch',state)

    def test_resident_token_fields_match_actual_helper_pre_lock_side_effects(self):
        for leaf,flag,expected in [('infinity_continuity.py','Continuity','Infinity.Continuity.HomeLoad'),
                                    ('infinity_native_ambient.py','Ambient','Infinity.NativeAmbient.LayoutEpoch')]:
            tree=ast.parse(self.skin['resources/lib/'+leaf]);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
            prefix=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                        and any(isinstance(t,ast.Name) and t.id=='PREFIX' for t in n.targets))
            observed={};home=SimpleNamespace(setProperty=lambda k,v:observed.__setitem__(k,v))
            scope=dict(HOME=10000,PREFIX=prefix,xbmcgui=SimpleNamespace(Window=lambda _:home),
                       uuid=SimpleNamespace(uuid4=lambda:SimpleNamespace(hex='a'*32)))
            exec(compile(ast.Module(body=main.body[:2],type_ignores=[]),'actual-helper-pre-lock','exec'),scope)
            self.assertEqual(observed,{expected:'a'*32})
            state=self.epoch(continuity=flag=='Continuity',ambient=flag=='Ambient')[2]
            self.assertEqual(state[expected],observed[expected])

    def test_all14_home_xml_full_inverse_and_exact942pins_helpers_and_geometry(self):
        revised,proof=correction.skin_sources(self.skin)
        self.assertTrue(proof['all942parent_pins_verified']);self.assertEqual(len(proof['changed_members']),17)
        for name,old in self.skin.items():
            if not name.endswith('/Home.xml'):continue
            text=revised[name].decode()
            for before,after in reversed(correction.home_edits()):text=text.replace(after,before,1)
            self.assertEqual(text.encode(),old)
            original_cont=b'infinity_continuity.py' in old
            self.assertEqual(b'Infinity.Home.Continuity.Pending' in revised[name],original_cont)
            self.assertIn(b'Infinity.Home.Ambient.Pending',revised[name])
        protected=json.loads(revised['Infinity-Protected-Manifest.json'])['protected_files']
        self.assertEqual(len(protected),942)
        for name,pin in protected.items():self.assertEqual(correction.digest(revised[name]),pin)
        for leaf in ('infinity_native_ambient.py','infinity_continuity.py','infinity_playlist_routes.py'):
            self.assertEqual(revised['resources/lib/'+leaf],self.skin['resources/lib/'+leaf])

    def test_every_owned_python_edit_inverse_and_no_new_thread_writer_or_checkpoint_bypass(self):
        for n,updated in self.updated.items():
            text=updated.decode()
            for before,after in reversed(correction.edits(n)):text=text.replace(after,before,1)
            self.assertEqual(text.encode(),self.raw[n])
        service=self.updated['service.py'].decode()
        main=service[service.index('def main():'):]
        self.assertLess(main.index('if checkpoint.poll()'),main.index('_consume_home_observer_epoch()'))
        epoch=(correction.ROOT/'home_observer_epoch.py').read_text()
        for bad in ('Thread(','.write_', 'persistence_scope','RunScript','Player.Open'):self.assertNotIn(bad,epoch)


if __name__=='__main__':unittest.main(verbosity=2)
