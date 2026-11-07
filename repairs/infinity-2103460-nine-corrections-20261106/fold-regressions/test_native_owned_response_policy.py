"""Native-provider-owned response policy regression tests (host only).

A fresh completed native response is authoritative for its owning provider;
settings.xml metadata is for caching, not post hoc reinterpreting a result.
This does not prove semantic consistency if a provider changes a filter while
its request executes. Full Fold/device acceptance remains mandatory.
"""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import types
import unittest
import os
import time

ROOT=Path(__file__).resolve().parents[3]
CC=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter'
SOURCE=CC/'infinity_search.py'

def functions(env):
    tree=ast.parse(SOURCE.read_text())
    wanted={'_query_file_stamp','_query_signature','_provider_result'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
    assert {n.name for n in nodes}==wanted
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),env)

class Home:
    def __init__(self): self.props={};self.before_get=None
    def getProperty(self,key):
        if key.startswith('Infinity.Search.Cache.') and self.before_get:
            self.before_get()
        return self.props.get(key,'')
    def setProperty(self,key,value): self.props[key]=value

class Cancel:
    def __init__(self): self.value=False
    def iscanceled(self): return self.value

class Fixture:
    def __init__(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.profile=root/'profile';self.profile.mkdir()
        self.progress=root/'cc';self.progress.mkdir()
        self.root=root/'provider';self.root.mkdir()
        self.settings=self.profile/'addon_data/plugin.video.watchnixtoons2/settings.xml'
        self.settings.parent.mkdir(parents=True)
        self.initial=b'<settings><setting id="filter">on</setting></settings>'
        self.settings.write_bytes(self.initial)
        (self.root/'addon.xml').write_text('<addon id="plugin.video.watchnixtoons2"/>')
        self.provider=dict(id='plugin.video.watchnixtoons2',root=str(self.root),
                           contract=dict(pins={},dependencies=[]),name='Nixtoons')
        self.home=Home();self.cancel=Cancel()
        self.answer={'result':{'files':[dict(file='plugin://plugin.video.watchnixtoons2/?id='+str(i))
                                        for i in range(31)]}}
        self.calls=0;self.change=lambda:None
        self.directory='plugin://plugin.video.watchnixtoons2/?action=actionSearchMenu&searchType=series&query=fixture'
        def native(*_):
            self.calls+=1
            self.change()
            return 'completed',self.answer
        self.env={
            'Path':Path,'hashlib':hashlib,'json':json,'time':time,
            'CC':'script.infinity.commandcenter',
            'xbmcaddon':types.SimpleNamespace(Addon=lambda _:types.SimpleNamespace(getAddonInfo=lambda k:{
                'version':'0.3.5.61','profile':str(self.progress)}[k])),
            'xbmcvfs':types.SimpleNamespace(translatePath=lambda name:
                str(self.profile) if name=='special://profile' else name),
            '_leased_directory':native,
            '_VisibleCancellation':lambda c,p:c,
            '_query_cache_entries':lambda raw,now:[],
            '_remember_query_answer':lambda *args:None,
            '_state_rejection_trace':lambda *args:None,
            'route':lambda p,q:self.directory,
        }
        functions(self.env)
    def close(self): self.tmp.cleanup()
    def query(self):return self.env['_provider_result'](self.provider,'fixture',self.home,self.cancel)
    def write(self,value):self.settings.write_bytes(value)
    def touch(self,p):
        old=p.stat();os.utime(p,ns=(old.st_atime_ns,old.st_mtime_ns+1000000))

class Policy(unittest.TestCase):
    def setUp(self):
        self.f=Fixture();self.addCleanup(self.f.close)

    def test_no_change_remains_valid(self):
        self.assertEqual(self.f.query()[1],'completed')
        self.assertEqual(self.f.calls,1)

    def test_nixtoons_history_only_write_retains_31_fresh_rows(self):
        self.f.change=lambda:self.f.write(
            b'<settings><setting id="filter">on</setting><setting id="searchHistory">fixture</setting></settings>')
        status=self.f.query()
        self.assertEqual(status[1],'completed')
        self.assertEqual(len(status[2]['result']['files']),31)
        self.assertEqual(self.f.calls,1)

    def test_crew_style_native_settings_write_keeps_2_results(self):
        self.f.provider['id']='plugin.video.thecrew'
        crew=self.f.profile/'addon_data/plugin.video.thecrew/settings.xml'
        crew.parent.mkdir(parents=True);crew.write_bytes(self.f.initial)
        self.f.answer={'result':{'files':[dict(file='plugin://plugin.video.thecrew/?id='+str(i))
                                        for i in range(2)]}}
        self.f.change=lambda:crew.write_bytes(
            b'<settings><setting id="filter">on</setting><setting id="orion.installed">true</setting></settings>')
        status=self.f.query()
        self.assertEqual(status[1],'completed')
        self.assertEqual(len(status[2]['result']['files']),2)

    def test_source_manifest_update_is_still_rejected(self):
        self.f.change=lambda:self.f.touch(self.f.root/'addon.xml')
        self.assertEqual(self.f.query()[1],'state_changed')

    def test_dependency_bookkeeping_write_keeps_fresh_native_result(self):
        dep=self.f.profile/'addon_data/script.module.fixture/settings.xml'
        dep.parent.mkdir(parents=True);dep.write_bytes(b'<settings/>')
        dep_root=Path(self.f.tmp.name)/'dependency';dep_root.mkdir()
        (dep_root/'addon.xml').write_text('<addon/>')
        self.f.provider['contract']['dependencies']=[dict(id='script.module.fixture',root=str(dep_root))]
        self.f.change=lambda:dep.write_bytes(b'<settings><setting id="auth">changed</setting></settings>')
        self.assertEqual(self.f.query()[1],'completed')

    def test_profile_switch_is_still_rejected(self):
        other=Path(self.f.tmp.name)/'profile2';other.mkdir()
        def change():
            self.f.env['xbmcvfs'].translatePath=lambda k: str(other) if k=='special://profile' else k
        self.f.change=change
        self.assertEqual(self.f.query()[1],'state_changed')

    def test_provider_disabled_or_changed_route_refuses(self):
        def change():
            self.f.env['route']=lambda *_: (_ for _ in ()).throw(RuntimeError('disabled'))
        self.f.change=change
        self.assertEqual(self.f.query()[1],'unavailable')

    def test_cancelled_result_stays_cancelled(self):
        self.f.change=lambda:setattr(self.f.cancel,'value',True)
        self.assertEqual(self.f.query()[1],'cancelled')

    def test_guard_no_fresh_response_cached_after_settings_write(self):
        events=[]
        self.f.env['_remember_query_answer']=lambda *args:events.append('cache')
        self.f.change=lambda:self.f.write(
            b'<settings><setting id="searchHistory">history</setting></settings>')
        self.assertEqual(self.f.query()[1],'completed')
        self.assertEqual(events,[])

    def test_cache_hit_must_reject_intervening_settings_write(self):
        # A cached response is NOT a newly completed response from the provider.
        signature=self.f.env['_query_signature'](self.f.provider,self.f.directory,self.f.home)
        old=dict(signature=signature,at=time.monotonic(),answer=self.f.answer)
        self.f.env['_query_cache_entries']=lambda *args:[old]
        get=self.f.home.getProperty
        def after_lookup(key):
            if key.startswith('Infinity.Search.Cache.'):
                self.f.write(b'<settings><setting id="filter">changed</setting></settings>')
            return get(key)
        self.f.home.getProperty=after_lookup
        self.assertEqual(self.f.query()[1],'state_changed')
        self.assertEqual(self.f.calls,0)

    def test_unreadable_or_linked_settings_fail_closed(self):
        self.f.change=lambda:(self.f.settings.unlink(),
                              self.f.settings.symlink_to(self.f.root/'addon.xml'))
        self.assertEqual(self.f.query()[1],'state_changed')

    def test_native_failure_is_not_reinterpreted_as_state_change(self):
        self.f.env['_leased_directory']=lambda *args:('timeout',{'error':{'message':'provider_timeout'}})
        self.assertEqual(self.f.query()[1],'timeout')

    def test_multiple_settings_metadata_changes_do_not_block_fresh_reply(self):
        dep=self.f.profile/'addon_data/script.module.fixture/settings.xml'
        dep.parent.mkdir(parents=True);dep.write_bytes(b'<settings/>')
        dep_root=Path(self.f.tmp.name)/'dependency';dep_root.mkdir()
        (dep_root/'addon.xml').write_text('<addon/>')
        self.f.provider['contract']['dependencies']=[dict(id='script.module.fixture',root=str(dep_root))]
        def both():
            self.f.write(b'<settings><setting id="searchHistory">history</setting></settings>')
            dep.write_bytes(b'<settings><setting id="requestTimes">4</setting></settings>')
        self.f.change=both
        self.assertEqual(self.f.query()[1],'completed')
        self.assertEqual(self.f.calls,1)

    def test_native_provider_owns_intermediate_meaningful_config_changes(self):
        # Deliberate contract: only the provider can interpret how it used its
        # settings. We must NOT claim that setting changes are semantically safe.
        self.f.change=lambda:self.f.write(
            b'<settings><setting id="filter">disabled</setting></settings>')
        self.assertEqual(self.f.query()[1],'completed')

    def test_native_completed_response_is_not_falsely_rejected_for_aba(self):
        # A -> B -> A cannot be classified by Infinity; trust fresh native result,
        # never a stale cached response, and preserve source/enable checks.
        def mutate():
            self.f.write(b'<settings><setting id="filter">disabled</setting></settings>')
            self.f.write(self.f.initial)
            self.f.touch(self.f.settings)
        self.f.change=mutate
        self.assertEqual(self.f.query()[1],'completed')

if __name__=='__main__': unittest.main(verbosity=2)
