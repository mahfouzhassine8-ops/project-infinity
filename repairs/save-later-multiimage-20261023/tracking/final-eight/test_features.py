"""Selected final-eight host checks. Android and Fold are explicitly NOT RUN."""
import argparse, ast, copy, hashlib, importlib.util, json, sys, tempfile, time, types, unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent;REPAIR=HERE.parents[1]
sys.path.insert(0,str(HERE.parent))
import test_recovery as fixture
BASE=NATIVE=None

class Features(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Recovery('test_unknown_or_conflicting_identity_never_reuses_memory')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.hub=fixture.load('resume_hub',BASE/'script.infinity.commandcenter/resume_hub.py')
        self.hub.publish_home=lambda data:None
        with patch.object(sys,'argv',['plugin.py','1','']):
            self.plugin=fixture.load('final_eight_plugin',BASE/'script.infinity.commandcenter/plugin.py')
        self.f.hub=self.hub;self.f.plugin=self.plugin
        self.data={'schema':2,'items':{},'watched':{},'watchlist':{},'collection':{},'lists':{},
            'sources':{'c'*64:{'route':'original'}},'navigation_recovery':{'memory':{'keep':True}},
            'unknown_extension':{'preserve':[1,2]}}
    def movie(self,key,ids,updated=10,**extra):
        value=dict(key=key*64,media='movie',title='Same title',position=100,duration=1000,updated=updated,
            source='plugin://plugin.video.'+key+'/?original',playback_occurrence='1'*32,
            identity=self.hub.media_identity('movie',ids),**extra)
        self.data['items'][value['key']]=value;return value
    def episode(self,key,ids,episode,updated=10):
        value=self.movie(key,{},updated);value.update(media='tv',season=1,episode=episode,
            identity=self.hub.media_identity('tv',{},1,episode,ids));return value
    def test_movie_aliases_update_original_key_and_keep_routes(self):
        a=self.movie('b',{'tmdb':'603','imdb':'tt0133093'},10)
        b=self.movie('a',{'imdb':'tt0133093'},20)
        original=copy.deepcopy(self.data)
        self.assertEqual(len(self.hub.entries(self.data)),1)
        entry=dict(b,key='d'*64,position=211,updated=30,playback_occurrence='2'*32,source='new-provider')
        for tick in (30,40,50):
            entry.update(updated=tick,position=tick+200)
            self.data,key=self.hub.record_progress(self.data,entry)
            self.assertEqual(key,a['key'])
        self.assertEqual(len(self.data['items']),2)
        for key,value in self.data['items'].items():
            self.assertEqual(value['source'],original['items'][key]['source'])
            self.assertEqual(value['position'],250);self.assertEqual(value['updated'],50)
        self.assertEqual(self.data['navigation_recovery'],original['navigation_recovery'])
    def test_unrelated_titles_conflicting_ids_and_namespaces_stay_separate(self):
        self.movie('a',{'tmdb':'603','imdb':'tt0133093'},30)
        self.movie('b',{'tmdb':'604','imdb':'tt0133093'},20)
        self.movie('c',{'imdb':'tt0133093'},10)
        self.movie('d',{'tvdb':'603'},5)
        self.movie('e',{},1)
        self.assertEqual(len(self.hub.entries(self.data)),5)
    def test_verified_cross_namespace_link_is_one_card_and_original_progress(self):
        a=self.movie('a',{'tmdb':'603'},10)
        b=self.movie('b',{'imdb':'tt0133093'},20)
        original=copy.deepcopy(self.data)
        incoming=dict(a,key='c'*64,identity=self.hub.media_identity('movie',{'tmdb':'603','imdb':'tt0133093'}),
                      position=211,updated=30,playback_occurrence='2'*32)
        self.data,key=self.hub.record_progress(self.data,incoming)
        self.assertEqual(key,a['key']);self.assertEqual(len(self.hub.entries(self.data)),1)
        self.assertEqual(len(self.data['items']),2)
        for key,old in original['items'].items():
            value=self.data['items'][key]
            self.assertEqual(value['position'],211)
            for field in ('identity','source'):self.assertEqual(value[field],old[field])
        self.assertEqual(self.data['navigation_recovery'],original['navigation_recovery'])
        self.assertEqual(self.hub.progress_key(self.data,b),a['key'])
        self.data,_=self.hub.remove_resume_data(self.data,b['key'])
        self.assertEqual(self.hub.entries(self.data),[])
    def test_existing_verified_bridge_and_later_conflict_are_order_independent(self):
        self.movie('a',{'tmdb':'603'},30)
        self.movie('b',{'imdb':'tt0133093'},20)
        self.movie('c',{'tmdb':'603','imdb':'tt0133093'},10)
        self.assertEqual([r['key'] for r in self.hub.entries(self.data)],['a'*64])
        self.movie('d',{'tmdb':'604','imdb':'tt0133093'},1)
        self.assertEqual(len(self.hub.entries(self.data)),4)
        self.data,_=self.hub.remove_resume_data(self.data,'a'*64)
        self.assertEqual(set(self.data['resume_hidden']),{'a'*64})
    def test_series_uses_latest_playback_even_earlier_episode_keeps_all_progress(self):
        self.episode('a',{'tmdb':'330430','tvdb':'123'},8,10)
        recent=self.episode('b',{'tvdb':'123'},2,20)
        self.episode('c',{'tmdb':'999'},2,30)
        before=copy.deepcopy(self.data)
        rows=self.hub.entries(self.data,'tv')
        self.assertEqual([r['key'] for r in rows],['c'*64,recent['key']])
        self.assertEqual(self.data,before)
    def test_remove_series_from_show_list_retains_records_and_replay_restores(self):
        a=self.episode('a',{'tmdb':'330430'},1,10);b=self.episode('b',{'tmdb':'330430'},2,20)
        show=dict(key='d'*64,media='tv',season=-1,episode=-1,identity=self.hub.show_identity('tvshow',{'tmdb':'330430'}))
        self.data['watchlist'][show['key']]=show
        self.data['watched']['e'*64]=dict(a,episode=0)
        self.data['collection'][show['key']]=copy.deepcopy(show)
        self.data['lists']['Favorites']={show['key']:copy.deepcopy(show)}
        before=copy.deepcopy(self.data)
        data,removed=self.hub.remove_resume_data(self.data,show['key'])
        self.assertIsNotNone(removed);self.assertEqual(self.hub.entries(data),[])
        for bucket in before:self.assertEqual(data[bucket],before[bucket])
        data,key=self.hub.record_progress(data,dict(a,position=120,updated=30))
        self.assertEqual(self.hub.entries(data),[]) # same playback cannot undo removal
        data,key=self.hub.record_progress(data,dict(b,position=130,updated=40,playback_occurrence='3'*32))
        self.assertEqual([r['key'] for r in self.hub.entries(data)],[b['key']])
        self.assertEqual(len(data['items']),2)
    def test_mark_watched_hides_movie_aliases_without_erasing_progress(self):
        a=self.movie('a',{'tmdb':'603'});self.movie('b',{'tmdb':'603'},20)
        before=copy.deepcopy(self.data['items'])
        data,entry=self.hub.mark_watched_data(self.data,a['key'],a)
        self.assertEqual(self.hub.entries(data),[]);self.assertEqual(data['items'],before)
        self.assertTrue(self.hub.is_watched(data,'b'*64))
        data,entry=self.hub.mark_unwatched_data(data,'b'*64)
        self.assertIsNotNone(entry);self.assertEqual(data['watched'],{})
    def test_menu_only_applicable_actions_and_no_provider_discovery_per_card(self):
        entry=self.movie('a',{'tmdb':'603'})
        self.data['watchlist'][entry['key']]=copy.deepcopy(entry)
        self.data['collection'][entry['key']]=copy.deepcopy(entry)
        rows=self.plugin._menu_rows(entry,self.data,True)
        self.assertEqual([r[0] for r in rows],['Resume','Mark Watched','Remove from Watchlist',
            'Remove from Favorites','Remove from Collection','Add to Custom List','Information','Remove from Continue Watching'])
        with patch.object(self.plugin,'_rpc',side_effect=AssertionError('per-card RPC')):
            self.assertEqual(len(self.plugin._context(entry,self.data)),1)
        self.assertNotIn('Save for Later',[r[0] for r in rows])
        self.data,_=self.hub.remove_resume_data(self.data,entry['key'])
        self.assertEqual(self.plugin._menu_rows(entry,self.data)[0][0],'Play')
    def test_saved_list_menu_keeps_its_exact_route_and_removal(self):
        entry=self.movie('a',{'tmdb':'603'})
        saved=dict(entry,source='original-watchlist-provider',stable_source='original-watchlist-provider')
        self.data['watchlist'][entry['key']]=saved
        self.data['later']={entry['key']:copy.deepcopy(saved)}
        self.assertEqual(self.plugin._selected_menu_entry(self.data,entry['key'],'watchlist'),saved)
        rows=self.plugin._menu_rows(saved,self.data,bucket='later')
        self.assertIn(('Remove from Save for Later','remove-later',''),rows)
        self.assertNotIn('Save for Later',[r[0] for r in rows])
        self.f.path.write_text(json.dumps(self.data));before=copy.deepcopy(self.data)
        with self.plugin.persistence_scope():changed,_=self.plugin._mutate_locked('remove-later',entry['key'],'')
        self.assertTrue(changed);after=json.loads(self.f.path.read_text());self.assertEqual(after['later'],{})
        for bucket in ('items','watchlist','watched','sources','navigation_recovery'):
            self.assertEqual(after[bucket],before[bucket])

    def test_menu_cancel_preserves_underlying_view_and_data(self):
        entry=self.movie('a',{'tmdb':'603'});self.f.path.write_text(json.dumps(self.data));before=self.f.path.read_bytes()
        with patch.object(self.plugin,'_favourite',return_value=(None,None)),patch.dict(sys.modules,{'infinity_settings':types.SimpleNamespace(choose=lambda *a:-1)}):
            self.assertFalse(self.plugin.show_item_menu(entry['key']))
        self.assertEqual(self.f.path.read_bytes(),before);self.assertEqual(self.f.calls,[])
    def test_stale_popup_does_not_remove_new_playback(self):
        entry=self.movie('a',{'tmdb':'603'});self.f.path.write_text(json.dumps(self.data))
        def choose(title,labels):
            self.data['items'][entry['key']]=dict(entry,playback_occurrence='4'*32,position=333)
            self.f.path.write_text(json.dumps(self.data));return labels.index('Remove from Continue Watching')
        with patch.object(self.plugin,'_favourite',return_value=(None,None)),patch.dict(sys.modules,{'infinity_settings':types.SimpleNamespace(choose=choose)}):
            self.assertFalse(self.plugin.show_item_menu(entry['key']))
        saved=json.loads(self.f.path.read_text());self.assertNotIn('resume_hidden',saved)
        self.assertEqual(saved['items'][entry['key']]['position'],333)
    def test_remove_mutation_keeps_history_and_all_records_beyond_old_limit(self):
        for n in range(120):
            key=hashlib.sha256(str(n).encode()).hexdigest();self.data['items'][key]=dict(key=key,media='movie',identity=self.hub.media_identity('movie',{'tmdb':str(n+1)}),position=100)
        key=next(iter(self.data['items']));self.f.path.write_text(json.dumps(self.data))
        with self.plugin.persistence_scope():changed,_=self.plugin._mutate_locked('remove-resume',key,'')
        self.assertTrue(changed);saved=json.loads(self.f.path.read_text())
        self.assertEqual(len(saved['items']),120);self.assertEqual(len(self.hub.entries(saved)),119)
        self.assertEqual(saved['navigation_recovery'],self.data['navigation_recovery'])
        self.hub.save(self.f.root, saved)
        self.assertEqual(len(json.loads(self.f.path.read_text())['items']),120)
    def test_actual_home_route_uses_same_projection(self):
        self.episode('a',{'tmdb':'330430'},4,10);recent=self.episode('b',{'tmdb':'330430'},2,20)
        self.movie('c',{'tmdb':'603'},10);self.movie('d',{'tmdb':'603'},20)
        self.hub.load_view=lambda p:self.data;before=copy.deepcopy(self.data)
        rows=[];api=sys.modules['xbmcplugin'];api.setContent=lambda *a:None;api.endOfDirectory=lambda *a,**kw:None
        api.addDirectoryItem=lambda h,t,item,**kw:rows.append((t,item))
        for media,key in [('tv',recent['key']),('movie','d'*64)]:
            rows.clear()
            with patch.dict(sys.modules,{'controller_access':types.SimpleNamespace(load=lambda:self.plugin),'runtime':types.SimpleNamespace(addons=lambda:[],hidden=lambda x:False,destination=lambda x:None)}):
                with patch.object(sys,'argv',['plugin://script.infinity.uirepair/','1','?action=continue&media='+media]):
                    route=fixture.load('actual_home_continue_plugin',BASE/'script.infinity.uirepair/plugin.py');route.main()
            self.assertEqual(len(rows),1);self.assertEqual(rows[0][1].properties['Infinity.ResumeHub.Key'],key)
        self.assertEqual(self.data,before)
    def test_locked_trackit_implementation_and_working_saved_routes(self):
        scope=json.loads((HERE/'SCOPE.json').read_text())
        for file,sha in scope['locked_trackit_files'].items():
            self.assertEqual(hashlib.sha256((REPAIR/file).read_bytes()).hexdigest(),sha)
        original=ast.parse((HERE.parent/'overlay/script.infinity.commandcenter/plugin.py').read_text())
        final=ast.parse((BASE/'script.infinity.commandcenter/plugin.py').read_text())
        for name in ('_target','navigation_target','recover_entry','play_saved'):
            before=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name==name)
            after=next(n for n in final.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(ast.dump(before),ast.dump(after),name)
        entry=self.movie('a',{'tmdb':'603'});self.data.pop('navigation_recovery')
        for bucket in ('later','watchlist','continue'):
            with patch.object(self.plugin,'_target',return_value=entry['source']):
                self.assertEqual(self.plugin.navigation_target(entry,self.data,bucket),entry['source'])
    def test_real_poll_skips_fifteen_unnecessary_writer_entries(self):
        original=ast.parse((HERE.parent/'overlay/script.infinity.commandcenter/service.py').read_text())
        final=ast.parse((BASE/'script.infinity.commandcenter/service.py').read_text())
        def player(tree):return next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='InfinityPlayer')
        counts=[]
        for tree in (original,final):
            method=next(n for n in player(tree).body if isinstance(n,ast.FunctionDef) and n.name=='poll')
            clock=[100.0];calls=[]
            env={'time':types.SimpleNamespace(monotonic=lambda:clock[0]),
                 'setting_bool':lambda name,*a:name=='continue_watching_enabled'}
            exec(compile(ast.Module(body=[method],type_ignores=[]),'actual-service-poll','exec'),env)
            item=types.SimpleNamespace(isPlayingVideo=lambda:True,cw_pending=False,cw_item={'key':'a'*64},cw_key='a'*64,cw_last_save=100.0)
            def persist(**kwargs):calls.append(clock[0]);item.cw_last_save=clock[0]
            item.persist_continue=persist
            for tick in range(1,17):clock[0]=100+tick*.5;env['poll'](item)
            counts.append(len(calls))
        self.assertEqual(counts,[16,1])
        for name in ('onPlayBackStopped','onPlayBackEnded','onPlayBackError','persist_continue'):
            before=next(n for n in player(original).body if isinstance(n,ast.FunctionDef) and n.name==name)
            after=next(n for n in player(final).body if isinstance(n,ast.FunctionDef) and n.name==name)
            if name!='persist_continue':self.assertEqual(ast.dump(before),ast.dump(after),name)
        print('actual poll writer entries per 8 seconds: before=16 after=1')

    def test_projection_has_no_quadratic_growth_for_large_series(self):
        for n in range(3000):
            key=hashlib.sha256(str(n).encode()).hexdigest();self.data['items'][key]=dict(key=key,media='tv',season=1,episode=n,updated=n,identity=self.hub.media_identity('tv',{},1,n,{'tmdb':'330430'}))
        start=time.monotonic();rows=self.hub.entries(self.data,'tv');elapsed=time.monotonic()-start
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['episode'],2999)
        self.assertLess(elapsed,1.0);print('3000-episode host projection seconds:',round(elapsed,4))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',type=Path,required=True);args=parser.parse_args()
    BASE=args.base.resolve();fixture.BASE=BASE
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Features))
    (HERE/'FEATURE-HOST.json').write_text(json.dumps(dict(host='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,
        scope='final-eight progress, actions, Home route, TrackIt preservation; mocked Kodi APIs',
        android='NOT RUN',physical_fold='NOT RUN',shutdown='NOT RUN'),indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
