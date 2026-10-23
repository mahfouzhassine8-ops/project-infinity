"""Focused host contracts; real Android/provider/Fold acceptance is separate."""
import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

HERE=Path(__file__).resolve().parent
CONFIG=None


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


class Progress:
    def iscanceled(self):return False


class Navigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in ('xbmc','xbmcaddon','xbmcgui','xbmcplugin','xbmcvfs','common','persistence_participant'):
            sys.modules[name]=types.ModuleType(name)
        cls.xbmc=sys.modules['xbmc']
        cls.xbmc.getCondVisibility=lambda *a:True
        cls.xbmc.Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:False)
        cls.xbmc.log=lambda *a:None
        common=sys.modules['common']
        for n in ('atomic_json','read_json','persistence_scope','addon_profile','setting_bool'):
            setattr(common,n,lambda *a,**k:None)
        cls.hub=load('resume_hub',CONFIG.assets/'script.infinity.commandcenter/resume_hub.py')
        cls.search=load('infinity_search',CONFIG.assets/'script.infinity.commandcenter/infinity_search.py')
        cls.nav=load('saved_navigation',HERE/'saved_navigation.py')
        cls.contracts=load('provider_contracts',HERE/'provider_contracts.py').build(CONFIG.providers)['contracts']
        cls.proofs=load('provider_proofs',HERE/'provider_contracts.py').PROOFS
        cls.data=json.loads(CONFIG.profile.read_text()) if CONFIG.profile else None

    def provider(self,index=0,media='tv',root=None,aid=None):
        proof=self.proofs[index]
        root=root or CONFIG.providers/proof['archive'][:-4]/proof['addon']
        return self.nav.capability(aid or proof['addon'],root,media,self.contracts)

    def entry(self,kind='tvshow'):
        e=dict(key='a'*64,title='Exact Show',media='movie' if kind=='movie' else 'tv',season=-1,episode=-1)
        if kind=='movie':identity=self.hub.media_identity('movie',{'tmdb':'100'})
        elif kind in ('tvshow','season'):
            if kind=='season':e['season']=1
            identity=self.hub.show_identity(kind,{'tmdb':'100'},e['season'])
        else:
            e.update(season=1,episode=3)
            identity=self.hub.media_identity('tv',{},1,3,{'tmdb':'100'})
        return dict(e,identity=identity)

    def row(self,p,kind='tvshow',ids=None,season=1,episode=3):
        ids=ids or {'tmdb':'100','imdb':'tt1234567'}
        family=p['family']
        if family=='mode-list-v1':
            params=dict(mode={'tvshow':'build_episode_list','season':'build_episode_list',
                              'episode':'play_media','movie':'play_media'}[kind],tmdb_id=ids['tmdb'])
            if kind in ('episode','movie'):params['mediatype']=kind
            if kind in ('tvshow','season','episode'):params['season']='all' if kind=='tvshow' else season
            if kind=='episode':params['episode']=episode
        elif family=='action-list-v1':
            params=dict(action='episodes' if kind in ('tvshow','season') else 'play_Item',**ids)
            if kind in ('season','episode'):params['season']=season
            if kind=='episode':params['episode']=episode
        else:
            params=dict(action={'tvshow':'showSeasons','season':'seasonEpisodes','episode':'getSources','movie':'getSources'}[kind],
                        action_args=json.dumps(dict(mediatype=kind,trakt_id=123,trakt_show_id=1000)))
        return dict(type=kind,uniqueid=ids,season=season,episode=episode,
                    filetype='directory' if kind in ('tvshow','season') else 'file',
                    file='plugin://'+p['id']+'/?'+urlencode(params))

    def resolve(self,e,p,answers):
        calls=[]
        def directory(path,*a):
            calls.append(path)
            result=answers[len(calls)-1]
            return result
        with patch.object(self.nav,'_directory',directory):
            result=self.nav.resolve(e,p,None,Progress())
        return result,calls

    def test_01_real_current_provider_api_shapes(self):
        for i in range(3):
            for media in ('movie','tv'):
                with self.subTest(i=i,media=media):self.assertIsNotNone(self.provider(i,media))

    def test_02_all_provider_movie_tv_season_episode_identity(self):
        for i in range(3):
            for kind in ('movie','tvshow','season','episode'):
                with self.subTest(i=i,kind=kind):
                    p=self.provider(i,'movie' if kind=='movie' else 'tv')
                    e=self.entry(kind);before=deepcopy(e)
                    base=self.row(p,'movie' if kind=='movie' else 'tvshow')
                    season=self.row(p,'season');episode=self.row(p,'episode')
                    result,calls=self.resolve(e,p,[[base],[season],[episode]])
                    self.assertEqual(result,{'movie':base,'tvshow':base,'season':season,'episode':episode}[kind]['file'])
                    self.assertEqual(e,before)
                    self.assertNotIn('stable_source',e)

    def test_03_title_similarity_never_authorizes_another_show(self):
        p=self.provider();wrong=self.row(p,ids={'tmdb':'999'})
        wrong.update(title='Exact Show',label='Exact Show')
        with self.assertRaisesRegex(self.nav.Unavailable,'exact saved media identity'):
            self.resolve(self.entry(),p,[[wrong]])

    def test_04_conflicting_typed_namespace_blocks(self):
        p=self.provider();e=self.entry();e['identity']['ids']['imdb']='tt7654321'
        with self.assertRaises(self.nav.Unavailable):self.resolve(e,p,[[self.row(p)]])

    def test_05_stale_saved_url_is_never_dispatched(self):
        p=self.provider();e=self.entry();e.update(source='plugin://plugin.video.pov/?mode=unsupported',stable_source='stale')
        target,calls=self.resolve(e,p,[[self.row(p)],[self.row(p,'episode')]])
        self.assertNotIn(e['source'],calls);self.assertNotIn('stale',calls)
        self.assertEqual(target,self.row(p)['file'])

    def test_06_unknown_route_and_wrong_identity_destination_block(self):
        p=self.provider()
        for bad in ('plugin://'+p['id']+'/?mode=unknown&tmdb_id=100',
                    'plugin://'+p['id']+'/?mode=build_season_list&tmdb_id=999',
                    'plugin://other/?mode=build_season_list&tmdb_id=100',
                    'plugin://'+p['id']+'/?mode=build_season_list&tmdb_id=100&tmdb_id=999'):
            with self.subTest(path=bad),self.assertRaises(self.nav.Unavailable):
                self.nav.destination(p,dict(self.row(p),file=bad))

    def test_07_empty_and_failed_destinations_are_visible_errors(self):
        p=self.provider()
        with self.assertRaisesRegex(self.nav.Unavailable,'no result'):
            self.resolve(self.entry(),p,[[]])
        with patch.object(self.search,'_leased_directory',lambda *a:('failed',{'error':{}})):
            with self.assertRaisesRegex(self.nav.Unavailable,'did not complete'):
                self.nav._directory('route',p,'title',None,Progress())

    def test_08_disabled_and_mid_request_source_updates_block(self):
        p=self.provider()
        with patch.object(self.xbmc,'getCondVisibility',lambda *a:False):
            with self.assertRaisesRegex(RuntimeError,'disabled'):self.search.route(p,'Exact Show')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'provider';shutil.copytree(p['root'],root)
            p=self.provider(root=root)
            file=root/'resources/lib/modules/entry.py';file.write_bytes(file.read_bytes()+b'\n# provider update\n')
            with self.assertRaisesRegex(RuntimeError,'changed'):self.search.route(p,'Exact Show')
            self.assertIsNotNone(self.provider(root=root))  # Reopen revalidates the compatible API.

    def test_09_simulated_future_compatible_provider_needs_no_core_name_patch(self):
        original=self.provider();future='plugin.video.simulated.future'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/future;shutil.copytree(original['root'],root)
            for file in root.rglob('*'):
                if file.is_file() and file.suffix in ('.py','.xml'):
                    raw=file.read_bytes().replace(original['id'].encode(),future.encode())
                    file.write_bytes(raw)
            manifest=root/'addon.xml';manifest.write_bytes(manifest.read_bytes().replace(b'6.10.21',b'99.1.0'))
            for media,kind in (('movie','movie'),('tv','tvshow')):
                p=self.provider(root=root,aid=future,media=media)
                self.assertIsNotNone(p)
                result,_=self.resolve(self.entry(kind),p,[[self.row(p,kind)],[self.row(p,'episode')]])
                self.assertTrue(result.startswith('plugin://'+future+'/'))
            file=root/'resources/lib/modules/entry.py';file.write_bytes(file.read_bytes().replace(b"'build_episode_list'",b"'changed_api'"))
            self.assertIsNone(self.provider(root=root,aid=future))

    def test_10_episode_ids_never_become_show_ids(self):
        e=self.entry('episode');e['identity']=self.hub.media_identity('tv',{'tmdb':'100'},1,3)
        with self.assertRaisesRegex(self.nav.Unavailable,'episode-scoped'):
            self.resolve(e,self.provider(),[])

    def test_11_only_later_plugin_hook_changes(self):
        module=load('component_hook',HERE/'component_contract.py')
        before=(CONFIG.assets/'script.infinity.commandcenter/plugin.py').read_bytes()
        after=module.plugin(before)
        old,new=ast.parse(before),ast.parse(after)
        functions=lambda tree:{n.name:ast.dump(n) for n in tree.body if isinstance(n,ast.FunctionDef)}
        old,new=functions(old),functions(new)
        self.assertEqual({n for n in old if old[n]!=new[n]},{'main'})
        self.assertEqual(old['_target'],new['_target'])
        self.assertEqual(old['play_saved'],new['play_saved'])
        self.assertNotIn(b'open-later',after)
        self.assertIn(b"if action == 'saved-fallback':",after)
        self.assertEqual(old['_list_item'],new['_list_item'])

    def test_12_actual_profile_readonly_original_identity_and_control(self):
        if self.data is None:self.skipTest('No physical profile supplied')
        before=hashlib.sha256(CONFIG.profile.read_bytes()).hexdigest();snapshot=deepcopy(self.data)
        later=self.hub.entries(self.data,'tv','later')
        affected=next(e for e in later if e['identity']['ids'].get('tmdb')=='330430')
        self.assertEqual(affected['identity']['ids'],dict(tmdb='330430',tvdb='482439',imdb='tt48447471'))
        self.assertEqual(affected['identity']['scope'],'show')
        self.assertIn('mode=build_episode_list',affected['source']);self.assertIn('season=all',affected['source'])
        for e,i in ((affected,0),(next(e for e in later if e['identity']['ids'].get('tmdb')=='296756'),1)):
            p=self.provider(i);ids=e['identity']['ids']
            target,_=self.resolve(e,p,[[self.row(p,ids=ids)],[self.row(p,'episode',ids=ids)]])
            self.assertEqual(target,self.row(p,ids=ids)['file'])
        self.assertEqual(self.data,snapshot)
        self.assertEqual(hashlib.sha256(CONFIG.profile.read_bytes()).hexdigest(),before)
        self.assertEqual(self.data['items'],snapshot['items'])
        self.assertEqual(self.data['watchlist'],snapshot['watchlist'])

    def test_13_failed_provider_offers_explicit_verified_alternative(self):
        for kind in ('movie','tvshow'):
            e=self.entry(kind);before=deepcopy(e)
            providers=[dict(self.provider(i,'movie' if kind=='movie' else 'tv'),name=str(i)) for i in range(3)]
            choices=[];attempts=[]
            def choose(reason,remaining):
                choices.append([p['id'] for p in remaining]);return 0
            def attempt(saved,provider):
                attempts.append(provider['id'])
                if len(attempts)==1:raise self.nav.Unavailable('Provider directory request did not complete (failed).')
                base=self.row(provider,'movie' if kind=='movie' else 'tvshow')
                return self.resolve(saved,provider,[[base],[self.row(provider,'episode')]])[0]
            provider,target=self.nav.resolve_with_choices(e,providers,providers[0]['id'],choose,attempt)
            self.assertEqual(provider['id'],providers[1]['id'])
            self.assertEqual(choices,[[p['id'] for p in providers[1:]]])
            self.assertEqual(attempts,[p['id'] for p in providers[:2]])
            self.assertEqual(e,before);self.assertIn(providers[1]['id'],target)

    def test_14_alternative_is_not_opened_without_user_choice(self):
        providers=[dict(self.provider(i),name=str(i)) for i in (0,1)]
        attempts=[]
        def attempt(e,p):attempts.append(p['id']);raise self.nav.Unavailable('Failed')
        with self.assertRaises(self.nav.Cancelled):
            self.nav.resolve_with_choices(self.entry(),providers,providers[0]['id'],lambda *a:-1,attempt)
        self.assertEqual(attempts,[providers[0]['id']])

    def test_15_alternative_with_similar_title_wrong_ids_cannot_open(self):
        providers=[dict(self.provider(i),name=str(i)) for i in (0,1)]
        def attempt(e,p):
            if p is providers[0]:raise self.nav.Unavailable('Original provider failed')
            return self.resolve(e,p,[[self.row(p,ids={'tmdb':'999'})]])[0]
        with self.assertRaisesRegex(self.nav.Unavailable,'exact saved media identity'):
            self.nav.resolve_with_choices(self.entry(),providers,providers[0]['id'],lambda *a:0,attempt)

    def test_16_progress_cancellation_never_schedules_another_provider(self):
        providers=[dict(self.provider(i),name=str(i)) for i in (0,1)]
        def attempt(*a):raise self.nav.Cancelled('Cancelled')
        with self.assertRaises(self.nav.Cancelled):
            self.nav.resolve_with_choices(self.entry(),providers,providers[0]['id'],
                lambda *a:self.fail('Do not offer new work after cancellation'),attempt)


    def test_17_direct_identity_contracts_do_not_query_by_title(self):
        for i in (0,1):
            for tmdb,title in (('330430','Love After Lockup: Relationship Rehab'),('1396','Breaking Bad')):
                p=self.provider(i);e=self.entry();e['title']=title
                e['identity']=self.hub.show_identity('tvshow',{'tmdb':tmdb})
                with patch.object(self.nav,'_directory',side_effect=AssertionError('No preliminary invocation')):
                    target=self.nav.direct_destination(e,p)
                self.assertIn(tmdb,target)
                self.assertIn('mode=build_season_list' if i==0 else 'action=seasons',target)

    def test_18_recovery_requires_current_matching_failure(self):
        import time
        key='a'*64;token='1'*32;original='plugin://plugin.video.pov/?mode=build_episode_list&season=all&tmdb_id=330430'
        identity=self.hub.show_identity('tvshow',{'tmdb':'330430'})
        value=dict(schema=1,token=token,key=key,reason='provider_directory_failed',
            epoch_ms=int(time.time()*1000),original_sha256=hashlib.sha256(original.encode()).hexdigest(),
            folder=True,attempted=['plugin.video.pov'])
        home=types.SimpleNamespace(getProperty=lambda _:json.dumps(value))
        self.assertEqual(self.nav.failure_ticket(home,key,token,original,identity),value)
        for field,bad in [('key','b'*64),('token','2'*32),('reason','completed'),
                          ('epoch_ms',0),('original_sha256','0'*64),('folder',False),('attempted',[])]:
            prior=value[field];value[field]=bad
            with self.subTest(field=field),self.assertRaises(self.nav.Unavailable):
                self.nav.failure_ticket(home,key,token,original,identity)
            value[field]=prior


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--providers',type=Path,required=True);p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--profile',type=Path);p.add_argument('--out',type=Path,required=True)
    CONFIG=p.parse_args();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Navigation)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    CONFIG.out.write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        scope='Host provider source contracts and resolver, mocked directory responses; not actual provider runtime or Android/Fold acceptance',
        actual_profile_readonly=CONFIG.profile is not None,physical_fold_verified=False),indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
