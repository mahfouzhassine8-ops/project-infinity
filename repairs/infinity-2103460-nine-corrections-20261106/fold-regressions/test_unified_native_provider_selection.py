"""Candidate-only host contracts for one Infinity UI + each provider's native search.

This is not a Kodi/Fold runtime PASS or a benign-settings/ABA acceptance fix.
"""
import ast
from contextlib import nullcontext
import json
from pathlib import Path
import re
import subprocess
import sys
import types
import unittest
import uuid
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit, urlencode

ROOT=Path(__file__).resolve().parents[3]
CC=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter'
SEARCH=CC/'infinity_search.py'
PLUGIN=CC/'plugin.py'
FROZEN='86d5b5e2b65acb878632d407c3a3a07dd1af3b6d'
PID='plugin.video.watchnixtoons2'

def functions(src):
    return {n.name:ast.get_source_segment(src,n) for n in ast.parse(src).body
            if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

def load(names,env):
    names=set(names)
    tree=ast.parse(SEARCH.read_text())
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert len(nodes)==len(names),(names,{n.name for n in nodes})
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SEARCH),'exec'),env)

class Candidate(unittest.TestCase):
    def form(self,which,history=False,change_after_history=False,abort_after_history=False):
        calls=[]
        routes=[]
        writes=[]
        notice=[]
        flags={'changed':False,'abort':False}
        provider=dict(id=PID,name='WatchNixtoons2',root='fixture',contract={})
        class Keyboard:
            def __init__(self,text,heading,hidden):
                self.token=json.loads(heading.split(':',1)[1])['token']
            def doModal(self): pass
            def isConfirmed(self):return True
            def getText(self):
                return json.dumps(dict(token=self.token,provider=which,
                    query='Re:zero',history=bool(history)))
        def route(p,q,history=False):
            routes.append((p['id'],q,history))
            return 'plugin://'+p['id']+'/?'+urlencode(dict(action='history' if history else 'actionSearchMenu',
                query=q,changed='1' if flags['changed'] else '0'))
        def shared_history(**kw):
            if not kw:return []
            writes.append(kw)
            if change_after_history:flags['changed']=True
            if abort_after_history:flags['abort']=True
            return []
        xbmc=types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz',
            getInfoLabel=lambda _: '',Keyboard=Keyboard,
            Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:flags['abort']),
            executebuiltin=calls.append)
        env=dict(xbmc=xbmc,
                 xbmcgui=types.SimpleNamespace(Window=lambda _:types.SimpleNamespace(getProperty=lambda _:'')),
                 xbmcaddon=types.SimpleNamespace(Addon=lambda _:types.SimpleNamespace(getAddonInfo=lambda _:'icon.png')),
                 xbmcvfs=types.SimpleNamespace(translatePath=lambda p:p),
                 providers=lambda media,force=False,provider_id=None:([provider],[]),
                 route=route,shared_history=shared_history,
                 _search_nav_trace=lambda *args:notice.append(args),
                 uuid=uuid,json=json,urlencode=urlencode,CC='script.infinity.commandcenter')
        prep=types.ModuleType('action_loading');prep.preparation=lambda key:nullcontext()
        load(('_open_search',),env)
        with patch.dict(sys.modules,action_loading=prep):
            env['_open_search']('anime')
        return calls,routes,writes,notice

    def test_single_provider_keeps_native_provider_search_but_uses_existing_infinity_results(self):
        commands,routes,writes,notice=self.form(PID)
        self.assertEqual(len(commands),1)
        self.assertIn('action=search-provider',commands[0])
        self.assertNotIn('action=actionSearchMenu',commands[0])
        self.assertEqual(len(routes),2)
        self.assertEqual(routes,[(PID,'Re:zero',False)]*2)
        self.assertEqual(writes[0]['provider'],PID)
        self.assertEqual(notice,[('provider_form',PID,'native_navigation_requested'),
                                 ('provider_form',PID,'builtin_returned')])
        target=re.search(r'ActivateWindow\(Videos,"([^"]+)",return\)',commands[0]).group(1)
        parsed=urlsplit(target)
        self.assertEqual(parsed.netloc,'script.infinity.commandcenter')
        self.assertEqual(parse_qs(parsed.query),
                         dict(action=['search-provider'],media=['anime'],query=['Re:zero'],provider=[PID]))
        self.assertIn("if action == 'search-provider':",PLUGIN.read_text())

    def test_search_all_retains_original_single_unified_aggregator(self):
        commands,routes,writes,notice=self.form('all')
        self.assertEqual(len(commands),1)
        self.assertIn('action=search-all',commands[0])
        self.assertNotIn('search-provider',commands[0])
        self.assertEqual(routes,[])
        self.assertEqual(writes[0]['provider'],'all')
        self.assertEqual(notice,[])

    def test_legacy_history_stays_native_and_is_verified_twice(self):
        commands,routes,writes,notice=self.form(PID,history=True)
        self.assertEqual(len(commands),1)
        self.assertIn('plugin.video.watchnixtoons2',commands[0])
        self.assertIn('action=history',commands[0])
        self.assertNotIn('search-provider',commands[0])
        self.assertEqual(routes,[(PID,'Re:zero',True)]*2)
        self.assertEqual(writes,[])
        self.assertEqual(len(notice),2)

    def test_provider_changed_after_history_write_cannot_launch_unverified_route(self):
        with self.assertRaisesRegex(RuntimeError,'Provider changed'):
            self.form(PID,change_after_history=True)

    def test_abort_after_history_writer_blocks_dispatch(self):
        commands,routes,writes,notice=self.form(PID,abort_after_history=True)
        self.assertEqual(commands,[])
        self.assertEqual(len(routes),1)

    def test_atomic_modal_guard_rejects_duplicate_and_releases_when_closed(self):
        env={}
        load(('_search_modal_admission',),env)
        first=env['_search_modal_admission']()
        self.assertIsNotNone(first)
        try:
            self.assertIsNone(env['_search_modal_admission']())
        finally:first.close()
        second=env['_search_modal_admission']()
        self.assertIsNotNone(second)
        second.close()

    def test_modal_owner_encloses_entry_and_blocks_concurrent_gui(self):
        calls=[]
        env={'xbmc':types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz'),
             'xbmcgui':types.SimpleNamespace(Dialog=lambda:types.SimpleNamespace(ok=lambda *x:self.fail(str(x))))}
        def action(media):
            calls.append(media)
            if len(calls)==1:
                self.assertIsNone(env['open_search']('tv'))
            return 'first'
        env['_open_search']=action
        load(('_search_modal_admission','open_search'),env)
        self.assertEqual(env['open_search']('movie'),'first')
        self.assertEqual(calls,['movie'])
        self.assertEqual(env['open_search']('anime'),'first')
        self.assertEqual(calls,['movie','anime'])

    def test_single_provider_collects_and_publishes_native_rows_in_existing_infinity_screen(self):
        """Host-level integration of existing search-provider -> shared publisher."""
        provider=dict(id=PID,name='WatchNixtoons2',root='fixture',contract={})
        native_calls=[]
        published=[]
        chosen=[]
        class Item:
            def __init__(self,label='',path='',offscreen=False):
                self.label,self.path=label,path
                self.props={}
            def setProperty(self,k,v):self.props[k]=v
            def setInfo(self,*a):pass
            def setUniqueIDs(self,*a):pass
            def setArt(self,*a):pass
            def addContextMenuItems(self,*a):pass
        class Home:
            def getProperty(self,name):return '1' if name=='Infinity.Search.Protocol' else ''
            def setProperty(self,*a):pass
        class Progress:
            def create(self,*a):pass
            def iscanceled(self):return False
            def update(self,*a):pass
            def close(self):pass
        def eligible(media,force=False,provider_id=None):
            chosen.append((media,force,provider_id))
            return ([provider],[])
        def native(path,home,progress):
            native_calls.append(path)
            return ('completed',{'result':{'files':[
                dict(file='plugin://'+PID+'/?action=title&id='+str(i),
                     label='Synthetic series '+str(i),type='tvshow',filetype='directory')
                for i in range(31)]}})
        class Cancel:
            def iscanceled(self):return False
            def cancel(self):pass
        env=dict(
            xbmc=types.SimpleNamespace(Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:False)),
            xbmcgui=types.SimpleNamespace(ListItem=Item,Window=lambda _:Home(),DialogProgress=Progress),
            xbmcplugin=types.SimpleNamespace(setPluginCategory=lambda *a:None,
                setContent=lambda *a:None,
                addDirectoryItem=lambda *args,**kw:published.append((args,kw))),
            providers=eligible,
            _Cancellation=Cancel,
            _leased_directory=native,
            _query_signature=lambda *args,**kw:'0'*64,
            _query_cache_entries=lambda *args:[],
            _remember_query_answer=lambda *args:None,
            _VisibleCancellation=lambda *args:None,
            route=lambda p,q:'plugin://'+PID+'/?action=actionSearchMenu&searchType=series&query=Re%3Azero',
            time=types.SimpleNamespace(monotonic=lambda:1.0),
            MAX_RESULTS=40,CC='script.infinity.commandcenter'
        )
        load(('_publish_result','_provider_result','_bounded_results','_search_results',
              'search_provider'),env)
        metadata=types.ModuleType('title_metadata')
        metadata.trailer_route=lambda *args:None
        with patch.dict(sys.modules,title_metadata=metadata):
            env['search_provider'](1,'anime','Re:zero',PID)
        self.assertEqual(chosen,[('anime',True,PID)])
        self.assertEqual(len(native_calls),1)
        self.assertTrue(native_calls[0].startswith('plugin://'+PID+'/'))
        self.assertEqual(len(published),32)
        heading_path=published[0][0][1]
        self.assertEqual(heading_path,native_calls[0])
        self.assertIn('31 results',published[0][0][2].label)
        self.assertEqual([args[1] for args,kw in published[1:]],
            ['plugin://'+PID+'/?action=title&id='+str(i) for i in range(31)])
        self.assertFalse(any('script.infinity.commandcenter' in args[1]
                             for args,kw in published[1:]))

    def test_protected_validator_native_lease_and_external_components_unchanged(self):
        before=subprocess.check_output(['git','show',FROZEN+':'+str(SEARCH.relative_to(ROOT))],
                                        cwd=ROOT,text=True)
        now=SEARCH.read_text()
        bs=functions(before);ns=functions(now)
        self.assertEqual(set(ns)-set(bs),{'_search_modal_admission'})
        self.assertEqual({name for name in bs if bs[name]!=ns[name]},
                         {'open_search','_open_search','_provider_result'})
        for guard in ('route','_query_file_stamp','_query_signature',
                      '_leased_directory','_native_search_admission','_bounded_results',
                      '_search_results','_publish_result','search_provider','search_all'):
            self.assertEqual(bs[guard],ns[guard],guard)
        old_plugin=subprocess.check_output(['git','show',FROZEN+':'+str(PLUGIN.relative_to(ROOT))],
                                            cwd=ROOT,text=True)
        self.assertEqual(old_plugin,PLUGIN.read_text())
        names=set(subprocess.check_output(['git','diff','--name-only',FROZEN,'HEAD'],
                                          cwd=ROOT,text=True).splitlines())
        allowed={str(SEARCH.relative_to(ROOT)),
                 str(Path(__file__).relative_to(ROOT)),
                 '.github/workflows/infinity-unified-native-search-candidate.yml',
                 'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/UNIFIED-NATIVE-SEARCH-CANDIDATE.md',
                 'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/test_native_owned_response_policy.py',
                 'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/NATIVE-OWNED-RESPONSE-POLICY.md',
                 'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/SEARCH-CONSISTENCY-NATIVE-CONTRACT-20261107.md',
                 '.github/workflows/infinity-native-owned-response-candidate-20261107.yml'}
        self.assertTrue(names <= allowed, names-allowed)

if __name__=='__main__':
    unittest.main(verbosity=2)
