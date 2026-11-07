"""Pending focused checks for removing failed268 navigation; no full-repair claim.
Run only after execution is recovered. These fixtures do not prove Android
directory transitions, benign-settings acceptance or a native crash repair.
"""
import ast
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
CC=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter'
BASE='0a0ab8573d41c807d71814220a567ed93318bc19'
PRE='10c261ac06cd3337a755db984a379edd7d849fd7'

def source(leaf,ref=None):
    path=CC/leaf
    if ref:return subprocess.check_output(['git','show',ref+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True)
    return path.read_text()

def functions(raw):
    return {n.name:ast.get_source_segment(raw,n) for n in ast.parse(raw).body
            if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

def load(leaf,name,env):
    node=next(n for n in ast.parse(source(leaf)).body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(CC/leaf),'exec'),env)
    return env[name]

class Item:
    def __init__(self,label,*args,**kwargs):self.label=label;self.properties={};self.context=[]
    def setProperty(self,key,value):self.properties[key]=value
    def addContextMenuItems(self,value):self.context.extend(value)
    def setInfo(self,*args):pass
    def setUniqueIDs(self,*args):pass
    def setArt(self,*args):pass

class Removal(unittest.TestCase):
    def publisher(self):
        rows=[]
        env=dict(xbmcgui=types.SimpleNamespace(ListItem=Item),MAX_RESULTS=40,
                 xbmcplugin=types.SimpleNamespace(addDirectoryItem=lambda h,p,i,isFolder:rows.append((p,i,isFolder))))
        return load('infinity_search.py','_publish_result',env),rows

    def test_original_common_publisher_and_result_collection_restored(self):
        before=functions(source('infinity_search.py',PRE));now=functions(source('infinity_search.py'))
        for name in ('_publish_result','_search_results'):
            self.assertEqual(before[name],now[name],name)
        self.assertNotIn('Open fresh provider search',source('infinity_search.py'))
        self.assertNotIn('search-open-verified',source('infinity_search.py'))
        self.assertNotIn('verified_provider_target',now)
        self.assertNotIn('_verified_heading_target',now)

    def test_every_provider_uses_its_own_original_result_targets(self):
        run,published=self.publisher()
        metadata=types.ModuleType('title_metadata');metadata.trailer_route=lambda value:None
        with patch.dict(sys.modules,title_metadata=metadata):
            for aid,count in [('plugin.video.thecrew',2),('plugin.video.watchnixtoons2',31),
                              ('plugin.video.seren',1),('plugin.video.otaku',5),
                              ('plugin.video.umbrella',0)]:
                with self.subTest(provider=aid):
                    published.clear()
                    route='plugin://'+aid+'/?action=search&query=fixture'
                    actual=[dict(file='plugin://'+aid+'/?action=title&id='+str(i),
                                 label='Fixture',type='tvshow',filetype='directory') for i in range(count)]
                    run(1,dict(id=aid,name=aid),'completed',{'result':{'files':actual}},route)
                    self.assertEqual(len(published),count+1)
                    self.assertEqual(published[0][0],route)
                    self.assertIn(str(count)+' results',published[0][1].label)
                    self.assertEqual([p for p,_,_ in published[1:]],[r['file'] for r in actual])
                    self.assertFalse(any('script.infinity.commandcenter' in p for p,_,_ in published))

    def test_invalidated_rows_stay_rejected_without_another_directory_hop(self):
        run,published=self.publisher()
        aid='plugin.video.watchnixtoons2';route='plugin://'+aid+'/?action=search'
        run(1,dict(id=aid,name=aid),'state_changed',
            {'result':{'files':[dict(file=route)]*31}},route)
        self.assertEqual(len(published),1)
        self.assertEqual(published[0][0],route)
        self.assertIn('State changed',published[0][1].label)
        self.assertEqual(published[0][1].context,[])
        # This confirms safe rejection, NOT the required benign-write repair.

    def test_retired_cached_action_is_refused_without_navigation_or_resume_fallthrough(self):
        events=[]
        env=dict(PARAMS={'action':'search-open-verified'},HANDLE=1,
                 xbmcplugin=types.SimpleNamespace(endOfDirectory=lambda *a,**k:events.append(k)),
                 xbmc=types.SimpleNamespace(executebuiltin=lambda value:self.fail('unexpected navigation')))
        load('plugin.py','main',env)()
        self.assertEqual(events,[dict(succeeded=False,cacheToDisc=False)])

    def test_source_dependency_settings_aba_and_native_request_ownership_are_unchanged(self):
        before=functions(source('infinity_search.py',BASE));now=functions(source('infinity_search.py'))
        for name in ('route','_leased_directory','_native_search_admission','_query_file_stamp',
                     '_query_signature','_state_rejection_trace','_provider_result',
                     '_bounded_results','_open_search','shared_history'):
            self.assertEqual(before[name],now[name],name)

    def test_watch_writers_and_other_plugin_actions_unchanged(self):
        before=functions(source('plugin.py',BASE));now=functions(source('plugin.py'))
        self.assertEqual(set(before),set(now))
        for name in before:
            if name!='main':self.assertEqual(before[name],now[name],name)
        old=before['main'];new=now['main']
        start=old.index("    if action == 'search-open-verified':")
        end=old.index("    if action == 'search-all':",start)
        replacement=new[start:new.index("    if action == 'search-all':",start)]
        self.assertEqual(old[:start]+replacement+old[end:],new)

    def test_protected_runtime_and_original_signer_sources_unchanged(self):
        allowed={str((CC/n).relative_to(ROOT)) for n in ('plugin.py','infinity_search.py')}
        prefix='repairs/infinity-2103460-nine-corrections-20261106/'
        names=subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines()
        self.assertTrue(all(n in allowed or n==prefix+'SOURCE-INVENTORY.json'
                            or n.startswith(prefix+'fold-regressions/') for n in names),names)

if __name__=='__main__':unittest.main(verbosity=2)
