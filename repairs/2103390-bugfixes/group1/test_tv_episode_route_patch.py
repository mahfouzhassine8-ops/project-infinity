"""Group #1 TV source fix: prove exact preimage, safe fallback, no guessed IDs."""
import ast
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from tv_episode_route_patch import patch_bytes,ORIGINAL_ROUTE,SAFE_ROUTE,ORIGINAL_TMDB,SAFE_TMDB

BASE=Path(os.environ.get('INFINITY_GROUP1_CC_ROOT','/mnt/data/infinity_group1_review/base/assets/addons/script.infinity.commandcenter'))

def load_hub():
    import importlib.util
    xbmc=types.ModuleType('xbmc');xbmc.LOGINFO=1;xbmc.log=lambda *args:None
    common=types.ModuleType('common');common.atomic_json=lambda *args: (_ for _ in ()).throw(AssertionError('writes forbidden'));common.read_json=lambda *args:{}
    common.persistence_scope=lambda *args,**kw:(_ for _ in ()).throw(AssertionError('writes forbidden'))
    sys.modules['xbmc']=xbmc;sys.modules['common']=common
    spec=importlib.util.spec_from_file_location('group1_real_resume_hub',BASE/'resume_hub.py');hub=importlib.util.module_from_spec(spec);spec.loader.exec_module(hub)
    return hub

def target_from(source,addons):
    root=ast.parse(source)
    functions=[n for n in root.body if isinstance(n,ast.FunctionDef) and n.name=='_target']
    assert len(functions)==1
    code=compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),'group1 target','exec')
    hub=load_hub()
    def stable(route):
        if not isinstance(route,str) or '\n' in route or '\r' in route or '\0' in route:return ''
        if route.startswith('plugin://'):
            host=route[9:].split('/')[0];return route if host and host.replace('.','').replace('-','').replace('_','').isalnum() else ''
        return route if route.startswith(('file://','smb://','nfs://','special://','/')) else ''
    scope=dict(stable_route=stable,number=lambda x:float(x or 0),_has_addon=lambda name,render=None: name in addons,
               _has_tmdb_helper=lambda render=None:'plugin.video.themoviedb.helper' in addons,
               setting_bool=lambda *_:True,hub=hub,time=__import__('time'))
    exec(code,scope)
    return scope['_target'],hub

class TVEpisodeRouteTests(unittest.TestCase):
    def setUp(self):
        if not (BASE/'plugin.py').is_file(): self.skipTest('signed 2103390 Command Center source not mounted')
        self.source=(BASE/'plugin.py').read_bytes()
        self.patched=patch_bytes(self.source)
        self.movie={'key':'a'*64,'media':'movie','tmdb':'42','updated':1,'source':'https://expired.example/film.m3u8'}
        self.tv={'key':'b'*64,'media':'tv','season':2,'episode':3,'updated':1,'source':'https://expired.example/episode.m3u8'}

    def test_exact_two_function_local_changes_and_compile(self):
        self.assertEqual(self.patched,self.source.replace(ORIGINAL_ROUTE.encode(),SAFE_ROUTE.encode(),1).replace(ORIGINAL_TMDB.encode(),SAFE_TMDB.encode(),1))
        compile(self.patched,'plugin.py','exec')
        with self.assertRaises(ValueError):patch_bytes(self.patched)

    def test_invalid_stored_preference_no_longer_masks_installed_entry_route(self):
        entry=dict(self.tv,stable_source='plugin://plugin.video.fixture/?episode=7')
        sources={entry['key']:{'route':'https://expired.example/temp.m3u8','failures':0}}
        before,_=target_from(self.source,{'plugin.video.fixture'})
        after,_=target_from(self.patched,{'plugin.video.fixture'})
        self.assertEqual(before(entry,sources),'')
        self.assertEqual(after(entry,sources),entry['stable_source'])

    def test_uninstalled_preferred_addon_can_fallback_to_installed_saved_route(self):
        entry=dict(self.tv,stable_source='plugin://plugin.video.fixture/?episode=7')
        sources={entry['key']:{'route':'plugin://plugin.video.absent/?episode=7','failures':0}}
        after,_=target_from(self.patched,{'plugin.video.fixture'})
        self.assertEqual(after(entry,sources),entry['stable_source'])

    def test_two_recorded_failures_remain_blocked(self):
        entry=dict(self.tv,stable_source='plugin://plugin.video.fixture/?episode=7')
        sources={entry['key']:{'route':'plugin://plugin.video.fixture/?episode=7','failures':2}}
        after,_=target_from(self.patched,{'plugin.video.fixture'})
        self.assertEqual(after(entry,sources),'')

    def test_typed_verified_series_identity_can_restore_original_tv_resolver(self):
        after,hub=target_from(self.patched,{'plugin.video.themoviedb.helper'})
        identity=hub.media_identity('tv',{'tmdb':'7000'},2,3,{'tmdb':'1234'})
        entry=dict(self.tv,identity=identity,tmdb='7000',show_ids_verified=False,show_tmdb='')
        self.assertEqual(after(entry), 'plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=tv&tmdb_id=1234&season=2&episode=3')

    def test_episode_id_without_series_identity_can_never_be_used_as_show_id(self):
        after,hub=target_from(self.patched,{'plugin.video.themoviedb.helper'})
        identity=hub.media_identity('tv',{'tmdb':'7000'},2,3)
        entry=dict(self.tv,identity=identity,tmdb='7000')
        self.assertEqual(after(entry),'')

    def test_synthetic_next_stays_identity_guarded(self):
        after,hub=target_from(self.patched,{'plugin.video.themoviedb.helper'})
        identity=hub.media_identity('tv',{'tmdb':'7000'},2,4,{'tmdb':'1234'})
        entry=dict(self.tv,identity=identity,season=2,episode=4,synthetic_next=True,next_verified=True,show_ids_verified=False,tmdb='7000')
        self.assertEqual(after(entry),'')

    def test_movie_resolver_unchanged_and_no_expired_http(self):
        old,_=target_from(self.source,{'plugin.video.themoviedb.helper'})
        new,_=target_from(self.patched,{'plugin.video.themoviedb.helper'})
        self.assertEqual(new(self.movie),old(self.movie))
        self.assertIn('tmdb_type=movie',new(self.movie))
        empty,_=target_from(self.patched,{'plugin.video.fixture'})
        self.assertEqual(empty(self.tv),'')

    def test_missing_series_no_sources_preserves_unavailable(self):
        x,_=target_from(self.patched,set())
        self.assertEqual(x(self.tv),'')

if __name__=='__main__':unittest.main()
