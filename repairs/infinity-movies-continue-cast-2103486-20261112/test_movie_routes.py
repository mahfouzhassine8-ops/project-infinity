"""Selected movie-route checks against signed86 and supplied source exports.

No add-on execution, network, profile reads, player or persistence mutation.
Run: python test_movie_routes.py /path/to/extracted-reviewed-producer-code
"""
import ast
import copy
from contextlib import nullcontext
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import time
import types
import unittest
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
BASE = HERE / 'baseline/script.infinity.commandcenter'
FIXTURES = Path(sys.argv.pop(1)).resolve()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class MovieRoutes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('plugin.video.umbrella', 'plugin.video.pov'):
            shutil.copytree(FIXTURES / name, self.root / name)
        bridge = self.root / 'script.infinity.watchedbridge'
        bridge.mkdir()
        shutil.copyfile(HERE / 'baseline/script.infinity.watchedbridge/PROVIDER-CONTRACTS.json',
                        bridge / 'PROVIDER-CONTRACTS.json')
        def addon(name):
            root = self.root / name
            def info(key):
                if key == 'path': return str(root)
                if key == 'id': return name
                if key == 'version': return ET.parse(root / 'addon.xml').getroot().get('version')
                raise AssertionError(key)
            return types.SimpleNamespace(getAddonInfo=info)
        self.writes = []
        def forbidden(*args, **kwargs):
            self.writes.append((args, kwargs))
            raise AssertionError('Unexpected profile mutation/read')
        common = types.ModuleType('common')
        common.persistence_scope = nullcontext
        common.atomic_json = common.read_json = forbidden
        sys.modules['common'] = common
        sys.modules['xbmc'] = types.SimpleNamespace(log=lambda *args: None)
        sys.modules['xbmcaddon'] = types.SimpleNamespace(Addon=addon)
        sys.modules['xbmcvfs'] = types.SimpleNamespace(translatePath=lambda x: x)
        self.hub = module('resume_hub', BASE / 'resume_hub.py')
        sys.modules['resume_hub'] = self.hub
        self.before = module('signed86_experience', BASE / 'experience.py')
        self.after = module('movie_candidate_experience', HERE / 'overlay/script.infinity.commandcenter/experience.py')
        sys.modules['experience'] = self.after
        sys.modules['xbmcgui'] = types.SimpleNamespace()
        sys.modules['saved_playback'] = module('saved_playback', BASE / 'saved_playback.py')
        sys.modules['title_metadata'] = module('title_metadata', BASE / 'title_metadata.py')

    def movie(self, provider='plugin.video.umbrella', ids=None):
        ids = ids or {'tmdb': '268'}  # synthetic route-identity fixture, not owner data
        query = dict(action='play_Item', tmdb=ids['tmdb']) if provider.endswith('umbrella') else dict(mode='play_media', mediatype='movie', tmdb_id=ids['tmdb'])
        route = 'plugin://' + provider + '/?' + urlencode(query)
        identity = self.hub.media_identity('movie', ids)
        entry = dict(key=self.hub.identity_key(identity), identity=identity, media='movie',
                     title='Verified movie fixture', source=route, stable_source=route, **ids)
        return entry, route

    def target(self, policy, entry, sources=None):
        tree = ast.parse((BASE / 'plugin.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_target')
        env = dict(hub=self.hub, setting_bool=lambda *a: True, number=policy.number,
                   _render_verified_source=lambda entry, route, render: policy.verified_source(entry, route),
                   _has_addon=lambda *a: True, _has_tmdb_helper=lambda *a: True,
                   _local_next_proof=lambda entry: None, stable_route=policy.stable_route)
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual-signed86-target', 'exec'), env)
        return env['_target'](entry, sources or {})

    def test_original86_wrongly_falls_back_but_candidate_retains_both_actual_routes(self):
        for provider in ('plugin.video.umbrella', 'plugin.video.pov'):
            entry, route = self.movie(provider)
            self.assertIn('plugin.video.themoviedb.helper/', self.target(self.before, entry))
            self.assertEqual(route, self.target(self.after, entry))

    def test_movie_interface_file_tampering_is_not_accepted(self):
        entry, route = self.movie()
        self.assertEqual(route, self.target(self.after, entry))
        path = self.root / 'plugin.video.umbrella/resources/lib/menus/movies.py'
        path.write_bytes(path.read_bytes() + b'\n# changed producer\n')
        self.assertIn('plugin.video.themoviedb.helper/', self.target(self.after, entry))

    def test_unknown_newer_version_does_not_inherit_trust(self):
        entry, route = self.movie()
        path = self.root / 'plugin.video.umbrella/addon.xml'
        path.write_bytes(path.read_bytes().replace(b'6.8.00', b'6.8.01'))
        self.assertEqual('', self.after.verified_source(entry, route))

    def test_conflicting_identity_and_episode_route_stay_rejected(self):
        entry, route = self.movie()
        self.assertEqual('', self.after.verified_source(entry, route.replace('268', '269')))
        self.assertEqual('', self.after.verified_source(entry, route + '&season=1&episode=4'))
        self.assertEqual('', self.after.verified_source(entry, route + '&tmdb=269'))

    def test_no_writes_or_progress_from_rendering_a_saved_title(self):
        entry, route = self.movie()
        data = dict(watchlist={entry['key']: entry}, items={}, watched={})
        before = copy.deepcopy(data)
        self.assertEqual(route, self.target(self.after, data['watchlist'][entry['key']]))
        self.assertEqual(data, before)
        self.assertEqual([], self.writes)

    def test_tv_episode_contracts_have_identical_results(self):
        route = 'plugin://plugin.video.pov/?mode=play_media&mediatype=episode&tmdb_id=268&season=1&episode=4'
        for verify in (lambda provider: None, lambda provider: {'scope': 'show_episode'}):
            self.assertEqual(self.before.source_identity(route, 'tv', {'tmdb': '268'}, 1, 4, verify),
                             self.after.source_identity(route, 'tv', {'tmdb': '268'}, 1, 4, verify))
        self.assertIsNone(self.after._source_contract('plugin.video.pov', media='tv'))
        self.assertIsNone(self.after._source_contract('plugin.video.umbrella', media='tv'))

    def test_unrelated_provider_and_local_routes_are_unchanged(self):
        entry, _ = self.movie()
        for route in ('plugin://plugin.video.thecrew/?action=play&tmdb=268', '/storage/test.mp4'):
            self.assertEqual(self.before.verified_source(entry, route), self.after.verified_source(entry, route))

    def actual_movie(self, item=None, race=False, playing=True, native_route=None):
        _, route = self.movie()
        raw = dict(type='movie', title='Fixture', uniqueid={}, file='https://media.invalid/public.mp4',
                   infinity_original_route=route)
        raw.update(item or {})
        calls = []
        tag = types.SimpleNamespace(getMediaType=lambda: 'movie', getTitle=lambda: 'Fixture',
                                   getUniqueID=lambda name: '')
        native = types.SimpleNamespace(getVideoInfoTag=lambda: tag, getPath=lambda: raw['file'],
                                      getProperty=lambda name: raw['infinity_original_route'] if native_route is None else native_route)
        def filename():
            calls.append(1)
            return 'https://media.invalid/changed.mp4' if race and len(calls) > 1 else raw['file']
        player = types.SimpleNamespace(isPlayingVideo=lambda: playing, getPlayingItem=lambda: native,
                                       getPlayingFile=filename)
        xbmc = types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz', Player=lambda: player,
                                     getInfoLabel=lambda name: '')
        env = dict(xbmc=xbmc, hub=self.hub, source_identity=self.after.source_identity,
                   setting_bool=lambda *a: True)
        source = HERE / 'overlay/script.infinity.commandcenter/service.py'
        tree = ast.parse(source.read_text())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and
                 n.name in ('_continue_identity', '_continue_movie_route_item')]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), env)
        return env['_continue_movie_route_item'](raw), calls

    def test_actual_movie_route_supplies_exact_ids_without_guessing_a_library_id(self):
        result, calls = self.actual_movie()
        self.assertEqual({'tmdb': '268'}, result['identity']['ids'])
        self.assertEqual(-1, result['dbid'])
        self.assertTrue(result['stable_source'].startswith('plugin://plugin.video.umbrella/'))
        self.assertEqual(2, len(calls))
        self.assertEqual([], self.writes)

    def test_movie_ingress_rejects_races_conflicts_and_unstarted_playback(self):
        self.assertIsNone(self.actual_movie(race=True)[0])
        self.assertIsNone(self.actual_movie(playing=False)[0])
        self.assertIsNone(self.actual_movie(item={'uniqueid': {'tmdb': '269'}})[0])
        self.assertIsNone(self.actual_movie(item={'infinity_original_route': ''})[0])
        self.assertIsNone(self.actual_movie(native_route='plugin://plugin.video.umbrella/?action=play_Item&tmdb=269')[0])

    def test_typed_tv_row_never_enters_movie_probe(self):
        result, calls = self.actual_movie(item={'type': 'episode'})
        self.assertIsNone(result)
        self.assertEqual([], calls)

    def test_existing_progress_function_and_eligibility_are_not_modified(self):
        def function(path):
            tree = ast.parse(path.read_text())
            return next(n for c in tree.body if isinstance(c, ast.ClassDef) and c.name == 'InfinityPlayer'
                        for n in c.body if isinstance(n, ast.FunctionDef) and n.name == 'persist_continue')
        old = function(BASE / 'service.py')
        new = function(HERE / 'overlay/script.infinity.commandcenter/service.py')
        self.assertEqual(ast.dump(old), ast.dump(new))
        new.decorator_list = []
        movie, _ = self.actual_movie()
        for position, expected in ((29, 0), (258, 1)):
            saved = []
            data = dict(schema=2, items={}, watched={}, watchlist={}, collection={}, later={}, lists={})
            env = dict(hub=self.hub, time=time, setting_bool=lambda *a: True,
                       xbmc=types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz'),
                       _load_continue=lambda profile: copy.deepcopy(data),
                       _save_continue=lambda profile, value: saved.append(copy.deepcopy(value)))
            exec(compile(ast.Module(body=[new], type_ignores=[]), 'actual-unchanged-progress-function', 'exec'), env)
            instance = types.SimpleNamespace(cw_item=dict(movie, playback_occurrence='fixture-occurrence'),
                cw_key=movie['key'], cw_occurrence='fixture-occurrence', profile=Path('/unused-profile'),
                cw_last_save=0, getTime=lambda: position, getTotalTime=lambda: 7200,
                isPlayingVideo=lambda: True)
            env['persist_continue'](instance, immediate=True)
            self.assertEqual(expected, len(saved))
            if expected:
                self.assertEqual(1, len(self.hub.entries(saved[0], 'movie', 'items')))
                self.assertEqual(258, saved[0]['items'][movie['key']]['position'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
