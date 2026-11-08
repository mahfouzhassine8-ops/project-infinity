"""Actual signed69 projection functions; controlled Kodi, no app/provider calls."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from contextlib import nullcontext
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
BASE = HERE / 'reference/script.infinity.commandcenter'
OVERLAY = HERE / 'overlay/script.infinity.commandcenter'


def hub_module():
    common = types.ModuleType('common')
    common.persistence_scope = nullcontext
    common.read_json = lambda path, default: json.loads(path.read_text()) if path.exists() else default
    common.atomic_json = lambda path, data: path.write_text(json.dumps(data))
    sys.modules['common'] = common
    sys.modules['xbmc'] = types.SimpleNamespace(log=lambda *args: None)
    spec = importlib.util.spec_from_file_location('common_projection_hub', OVERLAY / 'resume_hub.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class Item:
    def __init__(self, **kwargs): self.properties = {}; self.path = kwargs.get('path')
    def setProperty(self, name, value): self.properties[name] = value
    def setInfo(self, *args): pass
    def setUniqueIDs(self, *args): pass
    def setArt(self, *args): pass
    def addContextMenuItems(self, *args): pass


class CommonProjection(unittest.TestCase):
    def setUp(self):
        self.hub = hub_module()
        self.data = {'schema': 2, 'revision': 10, 'items': {}, 'watched': {}, 'watchlist': {},
                     'collection': {}, 'later': {}, 'ratings': {}, 'lists': {}, 'resume_hidden': {},
                     'sources': {'f' * 64: {'route': 'preserve'}}, 'unknown_extension': {'preserve': [1, 2]}}
        sys.modules['title_metadata'] = types.SimpleNamespace(from_entry=lambda entry: {})
        sys.modules['selection_contract'] = types.SimpleNamespace(publish=lambda *args: None)
        names = ('_values_for', '_apply_identity', '_list_item', '_menu_resume')
        nodes = [n for n in ast.parse((OVERLAY / 'plugin.py').read_text()).body
                 if isinstance(n, ast.FunctionDef) and n.name in names]
        self.env = {'hub': self.hub, 'number': lambda value: float(value or 0),
                    'navigation_target': lambda entry, *args: entry['source'], '_url': lambda **params: 'unavailable',
                    '_context': lambda *args: [], 'artwork': lambda value, *args: value,
                    'xbmcgui': types.SimpleNamespace(ListItem=Item)}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'actual69-projection', 'exec'), self.env)

    def row(self, name, ids, *, tv=False, season=1, episode=1, updated=100, revision=11, position=120):
        identity = (self.hub.media_identity('tv', {}, season, episode, ids) if tv else
                    self.hub.media_identity('movie', ids))
        value = dict(key=hashlib.sha256(name.encode()).hexdigest(), media='tv' if tv else 'movie',
                     identity=identity, title='Same title', showtitle='Re:Zero' if tv else '',
                     season=season if tv else -1, episode=episode if tv else -1,
                     source='plugin://plugin.video.any-source/?original=' + name,
                     position=position, duration=1200, percentage=position / 12,
                     updated=updated, resume_revision=revision, playback_occurrence='1' * 32)
        return value

    def add(self, value, bucket='items'):
        self.data[bucket][value['key']] = value
        return value

    def test_rezero_alias_bridge_is_one_show_in_continue_progress_and_next(self):
        self.add(self.row('tmdb-tvdb', {'tmdb': '65942', 'tvdb': '305089'}, tv=True, episode=1))
        latest = self.add(self.row('tvdb', {'tvdb': '305089'}, tv=True, episode=2, updated=200))
        before = copy.deepcopy(self.data)
        for values in (self.hub.entries(self.data, 'tv'), self.hub.progress_shows(self.data), self.hub.next_episodes(self.data)):
            self.assertEqual([value['key'] for value in values], [latest['key']])
        self.assertEqual(self.data, before)

    def test_conflicting_alias_bridge_is_quarantined_in_all_three_projections(self):
        self.add(self.row('a', {'tmdb': '65942', 'tvdb': '305089'}, tv=True))
        self.add(self.row('b', {'tmdb': '999', 'tvdb': '305089'}, tv=True, episode=2))
        self.add(self.row('c', {'tvdb': '305089'}, tv=True, episode=3))
        for values in (self.hub.entries(self.data, 'tv'), self.hub.progress_shows(self.data), self.hub.next_episodes(self.data)):
            self.assertEqual(len(values), 3)

    def test_watched_alias_bridge_is_shared_by_all_continue_progress_next_inputs(self):
        self.add(self.row('tmdb',{'tmdb':'65942'},tv=True,episode=1))
        recent=self.add(self.row('tvdb',{'tvdb':'305089'},tv=True,episode=2,updated=200))
        self.add(self.row('bridge',{'tmdb':'65942','tvdb':'305089'},tv=True,episode=3,updated=50),'watched')
        for values in (self.hub.entries(self.data,'tv'),self.hub.progress_shows(self.data),self.hub.next_episodes(self.data)):
            self.assertEqual([row['key'] for row in values],[recent['key']])

    def test_watched_conflict_quarantines_continue_as_well_as_progress_and_next(self):
        a=self.add(self.row('a',{'tmdb':'65942','tvdb':'305089'},tv=True))
        b=self.add(self.row('b',{'tvdb':'305089'},tv=True,episode=2))
        self.add(self.row('conflict',{'tmdb':'999','tvdb':'305089'},tv=True,episode=3),'watched')
        self.assertEqual({row['key'] for row in self.hub.entries(self.data,'tv')},{a['key'],b['key']})
        self.assertEqual({row['key'] for row in self.hub.next_episodes(self.data)},{a['key'],b['key']})
        self.assertEqual(len(self.hub.progress_shows(self.data)),3)

    def test_watched_movie_bridge_also_deduplicates_continue(self):
        self.add(self.row('tmdb',{'tmdb':'603'}))
        recent=self.add(self.row('imdb',{'imdb':'tt0133093'},updated=200))
        self.add(self.row('bridge',{'tmdb':'603','imdb':'tt0133093'},updated=50),'watched')
        self.assertEqual([row['key'] for row in self.hub.entries(self.data,'movie')],[recent['key']])

    def test_remove_continue_uses_watched_series_bridge_and_preserves_records(self):
        self.add(self.row('bridge',{'tmdb':'65942','tvdb':'305089'},tv=True,episode=3,updated=50),'watched')
        self.add(self.row('tmdb',{'tmdb':'65942'},tv=True,episode=4))
        selected=self.add(self.row('tvdb',{'tvdb':'305089'},tv=True,episode=5,updated=200))
        self.assertEqual([row['key'] for row in self.hub.entries(self.data,'tv')],[selected['key']])
        before=copy.deepcopy(self.data)
        result,removed=self.hub.remove_resume_data(self.data,selected['key'])
        self.assertIsNotNone(removed)
        self.assertEqual(self.hub.entries(result,'tv'),[])
        self.assertEqual(result['items'],before['items'])
        self.assertEqual(result['watched'],before['watched'])
        self.assertEqual(set(result['resume_hidden']),set(before['items']))

    def test_remove_continue_conflicting_watched_bridge_does_not_overremove(self):
        self.add(self.row('a',{'tmdb':'65942','tvdb':'305089'},tv=True,episode=4))
        selected=self.add(self.row('b',{'tvdb':'305089'},tv=True,episode=5,updated=200))
        self.add(self.row('conflict',{'tmdb':'999','tvdb':'305089'},tv=True,episode=3),'watched')
        before=copy.deepcopy(self.data)
        result,removed=self.hub.remove_resume_data(self.data,selected['key'])
        self.assertIsNotNone(removed)
        self.assertEqual(set(result['resume_hidden']),{selected['key']})
        self.assertEqual(result['items'],before['items'])
        self.assertEqual(result['watched'],before['watched'])
        self.assertEqual(len(self.hub.entries(result,'tv')),1)

    def test_same_titles_different_ids_and_namespaces_stay_separate(self):
        self.add(self.row('a', {'tmdb': '1'}, tv=True))
        self.add(self.row('b', {'tmdb': '2'}, tv=True))
        self.add(self.row('c', {'tvdb': '1'}, tv=True))
        self.assertEqual(len(self.hub.progress_shows(self.data)), 3)
        self.assertEqual(len(self.hub.next_episodes(self.data)), 3)

    def test_unproven_parent_replay_same_exact_key_is_one_record(self):
        row=self.row('item-scoped',{'tmdb':'101'},tv=True)
        row['identity']=self.hub.media_identity('tv',{'tmdb':'101'},1,1)
        self.add(dict(row,updated=10,playback_occurrence='1'*32),'watched')
        current=self.add(dict(row,updated=20,playback_occurrence='2'*32))
        self.assertEqual([v['key'] for v in self.hub.progress_shows(self.data)],[current['key']])
        self.assertEqual([v['key'] for v in self.hub.next_episodes(self.data)],[current['key']])
        # Same title and raw item IDs cannot prove a parent for another key.
        self.add(dict(current,key='e'*64))
        self.assertEqual(len(self.hub.progress_shows(self.data)),2)

    def test_movie_aliases_use_current_revision_without_rewriting_saved_rows(self):
        a = self.add(self.row('a', {'tmdb': '603', 'imdb': 'tt0133093'}, revision=11))
        recent = self.add(self.row('b', {'imdb': 'tt0133093'}, revision=12, position=222))
        saved = dict(a, key='e' * 64, position=0)
        self.add(copy.deepcopy(saved), 'watchlist'); before = copy.deepcopy(self.data)
        self.assertEqual(self.hub.exact_progress(self.data, saved)['key'], recent['key'])
        self.assertEqual(self.data, before)

    def test_exact_movie_selector_quarantines_transitive_secondary_id_conflict(self):
        self.add(self.row('a',{'tmdb':'603','imdb':'tt0133093'}))
        self.add(self.row('b',{'tmdb':'604','imdb':'tt0133093'}))
        query=self.row('query',{'tmdb':'603'})
        self.assertIsNone(self.hub.exact_progress(self.data,query))

    def test_exact_episode_uses_raw_items_even_when_series_display_collapses(self):
        exact = self.add(self.row('s1e1', {'tmdb': '65942'}, tv=True, episode=1, position=123))
        self.add(self.row('s1e5', {'tmdb': '65942'}, tv=True, episode=5, updated=200, position=456))
        self.add(self.row('s2e1', {'tmdb': '65942'}, tv=True, season=2, episode=1, updated=300))
        self.assertEqual(len(self.hub.entries(self.data, 'tv')), 1)
        self.assertEqual(self.hub.exact_progress(self.data, dict(exact, position=0))['position'], 123)
        self.assertEqual(self.env['_menu_resume'](dict(exact, position=0), self.data)['episode'], 1)

    def test_all_saved_families_render_exact_current_offset_without_membership_mutation(self):
        for tv in (False, True):
            self.data['items'].clear(); self.data['watched'].clear()
            played = self.add(self.row('played-tv' if tv else 'played-movie', {'tmdb': '100'}, tv=tv, position=333))
            saved = dict(played, position=0, key='e' * 64)
            for bucket in ('watchlist', 'collection', 'later'):
                self.data[bucket] = {saved['key']: copy.deepcopy(saved)}
            self.data['lists'] = {'Weekend': {saved['key']: copy.deepcopy(saved)}}
            self.data['ratings'] = {saved['key']: {'rating': 8}}
            self.data['watched'] = {saved['key']: dict(saved, updated=1, resume_revision=1)}
            before = copy.deepcopy(self.data)
            for bucket in ('watchlist', 'collection', 'later', 'list', 'ratings', 'history', 'continue'):
                values = self.env['_values_for'](self.data, played['media'], bucket, 'Weekend')
                self.assertTrue(values, bucket)
                for row in values:
                    target, item = self.env['_list_item'](row, self.data, bucket, 'Weekend', render={'tier': 'standard'})
                    self.assertEqual(item.properties['StartOffset'], '333.0', bucket)
                    self.assertEqual(target, row['source'])
                    self.assertEqual(item.properties['Infinity.ResumeHub.Key'], row['key'])
            self.assertEqual(self.data, before)

    def test_newest_hidden_completed_and_manual_state_block_old_alias_then_replay(self):
        selected = self.row('selected', {'tmdb': '603'})
        self.add(self.row('older', {'tmdb': '603'}, updated=10))
        current = self.add(self.row('current', {'tmdb': '603'}, updated=20))
        self.data['resume_hidden'][current['key']] = {'occurrence': current['playback_occurrence']}
        self.assertIsNone(self.hub.exact_progress(self.data, selected))
        self.data['resume_hidden'].clear()
        watched = self.add(dict(current, updated=21, watched_at=21, completed_occurrence='1' * 32), 'watched')
        self.assertIsNone(self.hub.exact_progress(self.data, selected))
        current.update(updated=22, resume_revision=12, playback_occurrence='2' * 32)
        self.assertIsNotNone(self.hub.exact_progress(self.data, selected))
        watched.pop('completed_occurrence'); watched.update(updated=23, watched_at=23)
        self.assertIsNone(self.hub.exact_progress(self.data, selected))

    def test_legacy_exact_key_retains_own_offset_but_never_title_or_other_route_match(self):
        old = self.row('legacy', {'tmdb': '603'}); old.pop('identity')
        self.add(old)
        self.assertEqual(self.hub.exact_progress(self.data, dict(old, position=0))['position'], 120)
        self.assertIsNone(self.hub.exact_progress(self.data, dict(old, key='e' * 64)))
        self.assertIsNone(self.hub.exact_progress(self.data, dict(old, source='different')))

    def test_local_source_identity_keeps_its_existing_namespace(self):
        route='plugin://plugin.video.watchnixtoons2/?action=actionResolve&url=%2Fanime%2Fepisode-one'
        identity=self.hub.watchnixtoons_source_identity(route,'episode',-1,-1)
        old=dict(self.row('local',{}),media='tv',season=-1,episode=-1,identity=identity,source=route,stable_source=route)
        old['key']=self.hub.identity_key(identity);self.add(old)
        self.assertEqual(self.hub.exact_progress(self.data,old)['key'],old['key'])
        self.assertEqual(self.hub.entry_identity(old)['ids'],identity['ids'])

    def local_episode(self,name,parent='/anime/re-zero',episode=4,**extra):
        route='plugin://plugin.video.watchnixtoons2/?'+urlencode({'action':'actionResolve','url':'/anime/'+name})
        identity=self.hub.watchnixtoons_source_identity(route,'episode',-1,episode)
        value=dict(self.row(name,{}),key=self.hub.identity_key(identity),identity=identity,media='tv',
                   source=route,stable_source=route,season=-1,episode=episode,**extra)
        if parent is not None:
            value['source_parent']='plugin://plugin.video.watchnixtoons2/?'+urlencode({'action':'actionEpisodesMenu','url':parent})
        return value

    def test_wnt_validated_parent_groups_unknown_season_and_persists_existing_identity(self):
        a=self.local_episode('episode4',episode=4)
        b=self.local_episode('episode5',episode=5);b['updated']=200
        self.data,_=self.hub.record_progress(self.data,a)
        self.data,_=self.hub.record_progress(self.data,b)
        stored=self.data['items'][a['key']]
        self.assertEqual(stored['source_parent'],a['source_parent'])
        self.assertEqual(stored['identity'],a['identity'])
        self.assertEqual(stored['season'],-1)
        for values in (self.hub.entries(self.data,'tv'),self.hub.progress_shows(self.data),self.hub.next_episodes(self.data)):
            self.assertEqual([row['key'] for row in values],[b['key']])
        self.assertEqual(self.hub.exact_progress(self.data,a)['episode'],4)
        self.assertNotIn('show_tmdb',stored)

    def test_wnt_different_missing_and_malformed_parents_never_join(self):
        self.add(self.local_episode('a','/anime/a'))
        self.add(self.local_episode('b','/anime/b'))
        self.add(self.local_episode('c',None))
        malformed=self.local_episode('d');malformed['source_parent']='plugin://other/?action=actionEpisodesMenu&url=/anime/a'
        self.add(malformed)
        self.assertEqual(len(self.hub.progress_shows(self.data)),4)
        self.assertEqual(len(self.hub.entries(self.data,'tv')),4)
        self.assertEqual(len(self.hub.next_episodes(self.data)),4)

    def test_wnt_canonical_series_bridge_requires_explicit_verified_parent_fields(self):
        local=self.add(self.local_episode('a'));local['show_tmdb']='65942'
        canonical=self.add(self.row('canonical',{'tmdb':'65942'},tv=True,updated=200))
        self.assertEqual(len(self.hub.progress_shows(self.data)),2)
        local['show_ids_verified']=True
        self.assertEqual([row['key'] for row in self.hub.progress_shows(self.data)],[canonical['key']])
        self.assertEqual(local['season'],-1)
        self.assertEqual(self.hub.exact_progress(self.data,local)['key'],local['key'])
        conflict=self.local_episode('b',episode=5);conflict.update(show_ids_verified=True,show_tmdb='999')
        self.add(conflict)
        self.assertEqual(len(self.hub.progress_shows(self.data)),3)

    def test_wnt_invalid_parent_is_not_persisted_as_new_progress_evidence(self):
        local=self.local_episode('bad');local['source_parent']='not-a-provider-parent'
        self.data,_=self.hub.record_progress(self.data,local)
        self.assertNotIn('source_parent',self.data['items'][local['key']])
        self.assertEqual(self.hub.continue_series_ids(self.data['items'][local['key']]),{})

    def test_multiple_wnt_parent_locators_can_share_one_verified_canonical_show(self):
        a=self.local_episode('a','/anime/first');a.update(show_ids_verified=True,show_tmdb='65942')
        b=self.local_episode('b','/anime/alternate');b.update(show_ids_verified=True,show_tmdb='65942',updated=200)
        c=self.local_episode('c','/anime/alternate');c.update(updated=300)
        for row in (a,b,c):self.add(row)
        for values in (self.hub.entries(self.data,'tv'),self.hub.progress_shows(self.data),self.hub.next_episodes(self.data)):
            self.assertEqual([row['key'] for row in values],[c['key']])
        self.assertEqual(self.hub.exact_progress(self.data,a)['key'],a['key'])
        conflict=self.local_episode('conflict','/anime/alternate');conflict.update(show_ids_verified=True,show_tmdb='999')
        self.add(conflict)
        self.assertEqual(len(self.hub.progress_shows(self.data)),4)

    def test_same_key_fallback_does_not_bypass_contradictory_parent_quarantine(self):
        row=self.row('canonical',{'tmdb':'1'},tv=True)
        broken=dict(row,show_ids_verified=True,show_tmdb='2',updated=10,verified_next={
            'verified':True,'after':[1,1],'show_tmdb':'2','season':1,'episode':2})
        self.add(broken,'watched')
        valid=self.add(dict(row,show_ids_verified=True,show_tmdb='1',updated=20))
        self.assertEqual(len(self.hub.progress_shows(self.data)),2)
        self.assertEqual([v['key'] for v in self.hub.next_episodes(self.data)],[valid['key']])

    def test_unfinished_alias_suppresses_completed_successor_and_verified_season_edge_survives(self):
        watched=self.row('watched',{'tmdb':'65942','tvdb':'305089'},tv=True,episode=12)
        watched.update(show_ids_verified=True,show_tmdb='65942',watched_at=100,verified_next={
            'verified':True,'after':[1,12],'show_tmdb':'65942','season':2,'episode':1})
        self.add(watched,'watched')
        current=self.add(self.row('partial',{'tvdb':'305089'},tv=True,episode=5,updated=200))
        self.assertEqual([r['key'] for r in self.hub.next_episodes(self.data)],[current['key']])
        self.data['items'].clear()
        successor=self.hub.next_episodes(self.data)
        self.assertEqual([(r['season'],r['episode']) for r in successor],[(2,1)])
        watched.pop('verified_next')
        self.assertEqual(self.hub.next_episodes(self.data),[])

    def test_saving_and_rendering_alone_creates_no_progress(self):
        saved=self.row('saved',{'tmdb':'603'},position=0)
        self.data,_,_=self.hub.toggle_watchlist_data(self.data,saved['key'],saved)
        before=copy.deepcopy(self.data)
        values=self.env['_values_for'](self.data,'movie','watchlist')
        _,item=self.env['_list_item'](values[0],self.data,'watchlist',render={'tier':'standard'})
        self.assertEqual(item.properties['StartOffset'],'0')
        self.assertEqual(self.data['items'],{})
        self.assertEqual(self.data['watched'],{})
        self.assertEqual(self.data,before)

    def test_existing_store_reload_preserves_canonical_outcome_and_unknown_fields(self):
        self.add(self.row('a',{'tmdb':'65942','tvdb':'305089'},tv=True))
        latest=self.add(self.row('b',{'tvdb':'305089'},tv=True,episode=2,updated=200))
        with tempfile.TemporaryDirectory() as folder:
            self.hub.save(Path(folder),self.data)
            restored=hub_module().load(Path(folder))
            self.assertEqual(self.hub.progress_shows(restored)[0]['key'],latest['key'])
            self.assertEqual(restored['unknown_extension'],self.data['unknown_extension'])
            self.assertEqual(restored['sources'],self.data['sources'])

    def test_original_writer_identity_and_source_functions_are_unchanged(self):
        for file,names in [('resume_hub.py',('identity_key','same_identity','_resume_identity','progress_key','save','mark_watched_data')),
                           ('plugin.py',('_target','navigation_target','play_saved'))]:
            def methods(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
            before,after=methods(BASE/file),methods(OVERLAY/file)
            for name in names:self.assertEqual(before[name],after[name],name)
        spec=importlib.util.spec_from_file_location('original69_hub',BASE/'resume_hub.py')
        original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        for row in (self.row('ordinary-movie',{'tmdb':'603'}),self.row('ordinary-tv',{'tmdb':'65942'},tv=True)):
            before=original.record_progress(copy.deepcopy(self.data),copy.deepcopy(row))
            after=self.hub.record_progress(copy.deepcopy(self.data),copy.deepcopy(row))
            self.assertEqual(before,after)

    def test_home_continue_explicit_begin_still_overrides_common_item_offset(self):
        path=BASE/'infinity_modules/uirepair/runtime.py'
        node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='home_continue_choice')
        row=self.add(self.row('home',{'tmdb':'603'},position=333))
        plays=[]
        controller=types.SimpleNamespace(hub=self.hub,PROFILE=Path('/unused'),number=self.env['number'],
            navigation_target=lambda entry,*args:entry['source'],_list_item=self.env['_list_item'])
        self.hub.load_view=lambda profile:copy.deepcopy(self.data)
        self.env['xbmcgui'].Window=lambda ident:types.SimpleNamespace(getProperty=lambda name:'standard')
        package=types.ModuleType('infinity_modules.uirepair');package.__path__=[]
        sys.modules['infinity_modules']=types.ModuleType('infinity_modules')
        sys.modules['infinity_modules.uirepair']=package
        sys.modules['infinity_modules.uirepair.controller_access']=types.SimpleNamespace(load=lambda:controller)
        env={'__package__':'infinity_modules.uirepair','choose':lambda *args:'begin',
             '_continue_choice_clock':lambda pos:str(pos),
             'xbmc':types.SimpleNamespace(Player=lambda:types.SimpleNamespace(play=lambda target,item:plays.append((target,item)))),
             'xbmcgui':self.env['xbmcgui']}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'actual69-home-continue','exec'),env)
        env['home_continue_choice'](row['key'],'movie')
        self.assertEqual(len(plays),1)
        self.assertEqual(plays[0][1].properties['StartOffset'],'0')
        self.assertEqual(self.data['items'][row['key']]['position'],333)


if __name__=='__main__':unittest.main(verbosity=2)
