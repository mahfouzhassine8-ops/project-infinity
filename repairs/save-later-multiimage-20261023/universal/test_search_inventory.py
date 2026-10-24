"""Selected host inventory/dispatch checks; no Android, provider execution or Close."""
from copy import deepcopy
from contextlib import nullcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

HERE=Path(__file__).resolve().parent
REPAIR=HERE.parent
OVERLAY=HERE/'overlay/script.infinity.commandcenter'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value


class Inventory(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.cc=self.root/'cc';self.cc.mkdir()
        self.rows=[];self.paths={};self.props={};self.rpc_calls=0;self.added=[]
        self.home=types.SimpleNamespace(getProperty=lambda k:self.props.get(k,''),setProperty=self.props.__setitem__,clearProperty=lambda k:self.props.pop(k,None))
        modules={name:types.ModuleType(name) for name in ('xbmc','xbmcaddon','xbmcgui','xbmcplugin','xbmcvfs','resume_hub','common')}
        class Monitor:
            def abortRequested(self):return False
        modules['xbmc'].Monitor=Monitor
        modules['xbmc'].getSkinDir=lambda:'skin.infinity.diggz'
        modules['xbmc'].getCondVisibility=lambda c:any(row['addonid'] in c and row['enabled'] for row in self.rows)
        def rpc(raw):
            self.rpc_calls+=1;data=json.loads(raw)
            assert data['method']=='Addons.GetAddons',data
            return json.dumps({'result':{'addons':deepcopy(self.rows)}})
        modules['xbmc'].executeJSONRPC=rpc
        modules['xbmcaddon'].Addon=lambda aid:types.SimpleNamespace(getAddonInfo=lambda key: str(self.cc if aid=='script.infinity.commandcenter' else self.paths[aid]) if key=='path' else '')
        modules['xbmcvfs'].translatePath=lambda p:p
        modules['xbmcgui'].Window=lambda *a:self.home
        self.progress=types.SimpleNamespace(iscanceled=lambda:False,update=lambda *a:None,create=lambda *a:None,close=lambda:None)
        modules['xbmcgui'].DialogProgress=lambda:self.progress
        modules['xbmcgui'].Dialog=lambda:types.SimpleNamespace(ok=lambda *a:None)
        modules['xbmcplugin'].setContent=lambda *a:None
        modules['xbmcplugin'].setPluginCategory=lambda *a:None
        modules['common'].persistence_scope=lambda:nullcontext()
        modules['common'].addon_profile=lambda:self.root
        modules['common'].read_json=lambda p,d:json.loads(p.read_text()) if p.exists() else d
        modules['common'].atomic_json=lambda p,d:p.write_text(json.dumps(d))
        old={name:sys.modules.get(name) for name in ('infinity_search','saved_navigation','provider_inventory')}
        def restore():
            for name,value in old.items():
                if value is None:sys.modules.pop(name,None)
                else:sys.modules[name]=value
        self.addCleanup(restore)
        self.module_patch=patch.dict(sys.modules,modules);self.module_patch.start();self.addCleanup(self.module_patch.stop)
        self.search=load('infinity_search',OVERLAY/'infinity_search.py')
        self.nav=load('saved_navigation',OVERLAY/'saved_navigation.py')
        self.inv=load('provider_inventory',OVERLAY/'provider_inventory.py')
        self.code=b'def verified_search(query):\n    return query\n'
        self.spec=dict(family='action-list-v1',entrypoint='main.py',sources={'main.py':self.nav.fingerprint(self.code,'plugin.video.fixture')},search={
            'movie':{'params':{'action':'movieSearchterm'},'query_key':'name'},
            'tv':{'params':{'action':'tvSearchterm'},'query_key':'name'}})
        self.write_contracts([self.spec])

    def write_contracts(self,specs):
        (self.cc/'NAVIGATION-CONTRACTS.json').write_text(json.dumps({'schema':1,'contracts':specs}))

    def provider(self,index=0,enabled=True):
        aid='plugin.video.fixture'+str(index);root=self.root/aid;root.mkdir()
        (root/'addon.xml').write_text('<addon id="'+aid+'"><extension point="xbmc.python.pluginsource" library="main.py"/></addon>')
        (root/'main.py').write_bytes(self.code);self.paths[aid]=root
        self.rows.append(dict(addonid=aid,name='Fixture '+str(index),path=str(root),version='1',enabled=enabled))
        return aid,root

    def test_all_reviewed_family_members_beyond_first_eight(self):
        for i in range(17):self.provider(i)
        ready,unavailable=self.inv.eligible('movie',force=True)
        self.assertEqual(len(ready),17);self.assertEqual(unavailable,[])
        self.assertEqual({r['id'] for r in ready},{r['addonid'] for r in self.rows})

    def test_category_and_navigation_capabilities_independent(self):
        self.provider();special=deepcopy(self.spec);special['family']='reviewed-specialty-search-v1'
        special['search']={'anime':{'params':{'action':'anime'},'query_key':'q'}}
        self.write_contracts([special])
        self.assertEqual(len(self.inv.eligible('anime')[0]),1)
        self.assertEqual(self.inv.eligible('movie')[0],[])
        self.assertEqual(self.inv.eligible('anime','title_navigation')[0],[])
        self.assertEqual(self.inv.eligible('anime','identity_lookup')[0],[])

    def test_disabled_removed_newly_installed_and_updated(self):
        aid,root=self.provider();self.assertEqual(len(self.inv.eligible('movie')[0]),1)
        self.rows[0]['enabled']=False
        self.assertEqual(self.inv.eligible('movie',force=True)[0],[])
        self.assertEqual(self.inv.eligible('movie')[1][0]['reason'],'disabled')
        self.rows[0]['enabled']=True;self.rows[0]['version']='2'
        (root/'main.py').write_text('def different(q):\n    return None\n')
        self.assertEqual(self.inv.eligible('movie',force=True)[0],[])
        self.rows=[];self.assertEqual(self.inv.snapshot(force=True)['entries'],[])
        self.assertEqual(self.inv._verified,{})
        self.provider(1);self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)

    def test_source_change_without_version_change_reverified(self):
        aid,root=self.provider();self.assertEqual(len(self.inv.eligible('tv')[0]),1)
        (root/'main.py').write_text('def verified_search(query):\n    return "different"\n')
        self.assertEqual(self.inv.eligible('tv',force=True)[0],[])

    def test_unchanged_forced_enumeration_reuses_verified_sources(self):
        for i in range(9):self.provider(i)
        with patch.object(self.nav,'capability',wraps=self.nav.capability) as verify:
            self.inv.eligible('movie',force=True);first=verify.call_count
            self.inv.eligible('tv',force=True);self.inv.eligible('movie',force=True)
            self.assertEqual(first,9);self.assertEqual(verify.call_count,first)
        self.assertEqual(self.rpc_calls,3)

    def test_restart_reconstructs_without_persisting_or_reading_user_progress(self):
        self.provider();before={p.name:p.read_bytes() for p in self.cc.iterdir()}
        first=self.inv.eligible('movie')[0]
        self.inv=load('provider_inventory',OVERLAY/'provider_inventory.py')
        second=self.inv.eligible('movie')[0]
        self.assertEqual(first,second);self.assertEqual(before,{p.name:p.read_bytes() for p in self.cc.iterdir()})
        self.assertFalse((self.root/'continue-watching.json').exists())

    def test_lifecycle_notification_invalidates_no_unrelated_notification_scan(self):
        self.provider();self.inv.snapshot();self.rows[0]['enabled']=False
        self.inv.on_notification('xbmc','Player.OnStop','{}')
        self.assertTrue(self.inv.has_enabled(self.rows[0]['addonid']))
        self.inv.on_notification('xbmc','Addons.OnDisabled','{}')
        self.assertFalse(self.inv.has_enabled(self.rows[0]['addonid']))
        self.assertIn('Infinity.ProviderInventory.Revision',self.props)

    def test_dispatch_rehash_rejects_same_size_tamper_and_disabled(self):
        aid,root=self.provider();provider=self.inv.eligible('movie')[0][0]
        self.assertEqual(parse_qs(urlsplit(self.search.route(provider,'100% "exact"')).query)['name'],['100% "exact"'])
        raw=(root/'main.py').read_bytes();(root/'main.py').write_bytes(raw.replace(b'return query',b'return False'))
        with self.assertRaises(RuntimeError):self.search.route(provider,'query')
        (root/'main.py').write_bytes(raw);self.rows[0]['enabled']=False
        with self.assertRaises(RuntimeError):self.search.route(provider,'query')

    def test_unknown_and_symlink_source_never_admitted(self):
        aid,root=self.provider();(root/'main.py').unlink();(root/'main.py').symlink_to(self.cc/'NAVIGATION-CONTRACTS.json')
        self.assertEqual(self.inv.eligible('movie')[0],[])
        self.assertEqual(self.inv.eligible('movie')[1][0]['reason'],'unverified_operation')

    def test_raw_exact_contract_falls_back_only_to_reviewed_shape(self):
        aid,root=self.provider();spec=deepcopy(self.spec)
        spec['exact_sources']={'main.py':hashlib.sha256(self.code).hexdigest()}
        self.write_contracts([spec])
        self.assertEqual(len(self.inv.eligible('movie')[0]),1)
        (root/'main.py').write_bytes(self.code+b'# harmless comment\n')
        self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)
        (root/'main.py').write_bytes(self.code.replace(b'return query',b'return False'))
        self.assertEqual(self.inv.eligible('movie',force=True)[0],[])

    def test_invalidation_during_source_scan_is_nonblocking_and_retries(self):
        self.provider();original=self.inv._scan;calls=0
        def changing(*args):
            nonlocal calls
            calls+=1
            if calls==1:
                self.rows[0]['enabled']=False
                worker=threading.Thread(target=self.inv.invalidate);worker.start();worker.join(.3)
                self.assertFalse(worker.is_alive(),'source scan blocked lifecycle invalidation')
            return original(*args)
        with patch.object(self.inv,'_scan',side_effect=changing):
            self.assertEqual(self.inv.eligible('movie')[0],[])
        self.assertEqual(calls,2)

    def test_repeated_lifecycle_race_fails_closed_after_two_scans(self):
        self.provider();original=self.inv._scan;calls=0
        def changing(*args):
            nonlocal calls
            calls+=1;self.inv.invalidate();return original(*args)
        with patch.object(self.inv,'_scan',side_effect=changing),self.assertRaises(RuntimeError):
            self.inv.snapshot()
        self.assertEqual(calls,2)

    def test_path_component_query_preserves_reserved_characters(self):
        self.provider();spec=deepcopy(self.spec);spec['family']='otaku-path-search-v1'
        spec['search']={'anime':dict(params={},query_key='query',query_codec='path_component',path_prefix='search_anime/')}
        self.write_contracts([spec]);provider=self.inv.eligible('anime')[0][0]
        query='A/B % "日本"'
        from urllib.parse import unquote
        target=self.search.route(provider,query)
        self.assertEqual(unquote(urlsplit(target).path[len('/search_anime/'):]),query)
        self.assertEqual(urlsplit(target).query,'')

    def test_narrow_shared_navigation_delegation_preserves_other_functions(self):
        import ast
        original=(REPAIR/'saved_navigation.py').read_text();current=(OVERLAY/'saved_navigation.py').read_text()
        def functions(s):
            lines=s.splitlines(keepends=True)
            return {n.name:''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        old,new=functions(original),functions(current)
        self.assertEqual(set(old),set(new))
        for name in old:
            if name!='available':self.assertEqual(old[name],new[name],name)
        self.provider();ready,_=self.nav.available('movie');self.assertEqual(len(ready),1)

    def test_all_scheduler_bound_cancellation_and_cleanup(self):
        ready=[{'id':str(i),'name':str(i)} for i in range(11)];lock=threading.Lock();running=0;peak=0;visited=[]
        def request(provider,*args):
            nonlocal running,peak
            with lock:running+=1;peak=max(peak,running);visited.append(provider['id'])
            time.sleep(.005)
            with lock:running-=1
            return provider,'completed',{},'original'
        with patch.object(self.search,'_provider_result',side_effect=request):
            cancel=self.search._Cancellation()
            rows=list(self.search._bounded_results(ready,'q',self.home,cancel,self.progress))
            self.assertEqual(len(rows),11);self.assertEqual(set(visited),{str(i) for i in range(11)});self.assertLessEqual(peak,self.search.MAX_ACTIVE_CONSUMERS)
            visited.clear();cancel=self.search._Cancellation()
            iterator=self.search._bounded_results(ready,'q',self.home,cancel,self.progress)
            next(iterator);cancel.cancel();iterator.close()
            self.assertLessEqual(len(visited),self.search.MAX_ACTIVE_CONSUMERS);self.assertEqual(running,0)

    def test_single_provider_dispatch_never_calls_other_provider(self):
        self.props['Infinity.Search.Protocol']='1';self.provider(1);self.provider(2)
        visited=[]
        def request(provider,*args):visited.append(provider['id']);return provider,'completed',{},'original'
        with patch.object(self.search,'_provider_result',side_effect=request),patch.object(self.search,'_publish_result'):
            self.search.search_provider(1,'movie','Title','plugin.video.fixture2')
        self.assertEqual(visited,['plugin.video.fixture2'])

    def test_history_preserves_records_preferences_and_unrelated_state(self):
        path=self.root/'continue-watching.json'
        old=dict(schema=2,items={'keep':{'position':5}},navigation_recovery={'memory':{'route':'keep'}},unknown={'x':2})
        path.write_text(json.dumps(old));self.search.shared_history(query='Exact title',media='movie',provider='all',name='Search All')
        value=json.loads(path.read_text())
        for k,v in old.items():self.assertEqual(value[k],v)
        self.assertEqual(self.search.shared_history()[0]['query'],'Exact title')

    def test_open_search_restores_last_provider_without_dispatch_on_focus(self):
        aid,root=self.provider();self.search.shared_history(query='Last query',media='movie',provider=aid,name='Fixture')
        headings=[]
        def keyboard(query,heading,hidden):
            headings.append(json.loads(heading.split(':',1)[1]))
            return types.SimpleNamespace(doModal=lambda:None,isConfirmed=lambda:False)
        sys.modules['xbmc'].Keyboard=keyboard;sys.modules['xbmc'].getInfoLabel=lambda *a:''
        sys.modules['xbmc'].executebuiltin=lambda *a:self.fail('focus dispatched a provider')
        self.search.open_search('movie')
        self.assertEqual(headings[0]['selected'],aid)

    def test_actual_specialty_contracts_and_source_tamper(self):
        artifact=HERE/'SPECIALTY-CONTRACTS.json'
        if not artifact.exists():self.fail('Actual reviewed specialty source contracts required')
        value=json.loads(artifact.read_text());self.write_contracts(value['contracts'])
        for index,proof in enumerate(value['provenance']):
            source=Path(os.environ.get('INFINITY_PROVIDER_FIXTURES',str(HERE.parents[3]/'provider-references')))/proof['fixture_directory'];aid=proof['addon'];self.paths[aid]=source
            self.rows.append(dict(addonid=aid,name=aid,path=str(source),version=proof['version'],enabled=True))
        movie,unavailable=self.inv.eligible('movie',force=True)
        self.assertEqual(len(movie),3,unavailable)
        self.assertEqual(len(self.inv.eligible('tv')[0]),3)
        self.assertEqual([p['id'] for p in self.inv.eligible('anime')[0]],['plugin.video.otaku'])
        self.assertEqual(self.inv.eligible('cartoon')[0],[])
        self.assertEqual(self.inv.eligible('movie','title_navigation')[0],[])
        for provider in movie:self.assertTrue(self.search.route(provider,'Exact / 100%').startswith('plugin://'+provider['id']+'/'))


if __name__=='__main__':unittest.main(verbosity=2)
