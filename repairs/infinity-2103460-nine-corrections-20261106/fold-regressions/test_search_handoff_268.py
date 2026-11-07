"""Host-only checks of actual signed266-derived Search handoff, not Android proof."""
import ast
import json
import subprocess
import sys
import types
import unittest
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

ROOT=Path(__file__).resolve().parents[3]
CC=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter'
SEARCH=CC/'infinity_search.py'
PLUGIN=CC/'plugin.py'
BASE='b535cfb2fec27bb1ad9185b57e69f61dffe4e230'
PROVIDER={'id':'plugin.video.watchnixtoons2','name':'Nixtoons','root':'fixture','contract':{}}

def selected(path,names):
    tree=ast.parse(path.read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    return compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec')

def funcs(raw):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body
            if isinstance(n,ast.FunctionDef)}

class Item:
    def __init__(self,*a,**kw):
        self.label=kw.get('label') or (a[0] if a else '')
        self.props={};self.context=[]
    def setProperty(self,k,v):self.props[k]=v
    def addContextMenuItems(self,items):self.context.extend(items)
    def setInfo(self,k,details):pass
    def setUniqueIDs(self,ids):pass
    def setArt(self,art):pass

class XBMC:
    LOGINFO=1
    def __init__(self,events):self.events=events;self.aborted=False
    def Monitor(self):return self
    def abortRequested(self):return self.aborted
    def log(self,s,level):self.events.append(('log',s))
    def executebuiltin(self,s):self.events.append(('execute',s))

class GUI:
    NOTIFICATION_WARNING=2
    ListItem=Item
    def __init__(self,events):self.events=events
    def Dialog(self):
        events=self.events
        class Dialog:
            def notification(self,*args):events.append(('notice',args))
        return Dialog()

class XBMCPlugin:
    def __init__(self,events):self.events=events;self.items=[]
    def addDirectoryItem(self,handle,target,item,isFolder=False):
        self.items.append((target,item,isFolder))
        return True
    def endOfDirectory(self,handle,**kwargs):self.events.append(('end',kwargs))

class VFS:
    def __init__(self):self.n=0;self.switch=False
    def translatePath(self,name):
        self.n+=1
        return '/tmp/scoped-profile' if not self.switch or self.n==1 else '/tmp/new-profile'

class Host(unittest.TestCase):
    def setUp(self):
        self.events=[];self.xbmc=XBMC(self.events);self.gui=GUI(self.events)
        self.plugin=XBMCPlugin(self.events);self.vfs=VFS()
        self.providers=[dict(PROVIDER)];self.routes=[];self.route_changed=False
        def eligible(media,force=False,provider_id=None):
            return self.providers,[]
        def route(provider,query,history=False):
            self.routes.append(query)
            result='plugin://'+provider['id']+'/?'+urlencode({'action':'search','query':query})
            return result+('&changed=1' if self.route_changed and len(self.routes)>1 else '')
        self.env=dict(Path=Path,xbmc=self.xbmc,xbmcgui=self.gui,xbmcplugin=self.plugin,
                      xbmcvfs=self.vfs,providers=eligible,route=route,
                      json=json,urlencode=urlencode,MAX_RESULTS=40,CC='script.infinity.commandcenter')
        exec(selected(SEARCH,('_search_nav_trace','verified_provider_target',
                              '_verified_heading_target','_publish_result')),self.env)

    def test_invalidated_results_never_published_stale(self):
        provider=PROVIDER
        raw='plugin://'+provider['id']+'/?query=test'
        self.env['_publish_result'](1,provider,'state_changed',
            {'result':{'files':[{'file':raw}]*31}},raw,'anime','Re:zero')
        self.assertEqual(len(self.plugin.items),1)
        path,item,folder=self.plugin.items[0]
        self.assertTrue(folder)
        self.assertEqual(parse_qs(urlparse(path).query)['action'],['search-open-verified'])
        self.assertEqual(parse_qs(urlparse(path).query)['provider'],[provider['id']])
        self.assertEqual(parse_qs(urlparse(path).query)['query'],['Re:zero'])
        self.assertIn('fresh provider search',item.label)
        self.assertEqual(len(item.context),1)
        self.assertNotIn('31 results',item.label)

    def test_non_state_heading_and_provider_path_unchanged(self):
        raw='plugin://'+PROVIDER['id']+'/?query=test'
        self.env['_publish_result'](1,PROVIDER,'unavailable',{},raw,'anime','test')
        self.assertEqual(self.plugin.items[0][0],raw)
        self.assertEqual(self.plugin.items[0][1].context,[])
        self.assertEqual(len(self.plugin.items),1)

    def test_reverified_route_no_query_in_log(self):
        target=self.env['verified_provider_target']('anime',PROVIDER['id'],'private title')
        self.assertTrue(target.startswith('plugin://'+PROVIDER['id']+'/'))
        self.assertEqual(len(self.routes),2)
        self.assertTrue(self.events)
        self.assertTrue(all('private title' not in str(e) and 'plugin://' not in str(e) for e in self.events))

    def test_disabled_changed_or_aborted_refuses(self):
        self.providers=[]
        self.assertEqual(self.env['verified_provider_target']('anime',PROVIDER['id'],'test'),'')
        self.providers=[dict(PROVIDER)]
        self.route_changed=True
        self.assertEqual(self.env['verified_provider_target']('anime',PROVIDER['id'],'test'),'')
        self.routes.clear();self.route_changed=False;self.xbmc.aborted=True
        self.assertEqual(self.env['verified_provider_target']('anime',PROVIDER['id'],'test'),'')

    def test_profile_change_refuses(self):
        self.vfs.switch=True
        self.assertEqual(self.env['verified_provider_target']('anime',PROVIDER['id'],'test'),'')

    def test_malformed_input_refuses_without_provider_call(self):
        f=self.env['verified_provider_target']
        for media,identity,query in [('bad',PROVIDER['id'],'q'),('anime','script.infinity.commandcenter','q'),
                                     ('anime','plugin.video.bad"','q'),('anime',PROVIDER['id'],'')]:
            self.assertEqual(f(media,identity,query),'')
        self.assertEqual(self.routes,[])

    def test_plugin_dispatch_after_own_directory_end(self):
        self.env['PARAMS']={'action':'search-open-verified','provider':PROVIDER['id'],
                            'media':'anime','query':'Re:zero'}
        self.env['HANDLE']=1
        mock=types.ModuleType('infinity_search')
        mock.verified_provider_target=self.env['verified_provider_target']
        mock._search_nav_trace=self.env['_search_nav_trace']
        original=sys.modules.get('infinity_search')
        sys.modules['infinity_search']=mock
        try:
            exec(selected(PLUGIN,('main',)),self.env)
            self.env['main']()
            self.assertEqual([e[0] for e in self.events if e[0] in ('end','execute')],['end','execute'])
            self.events.clear();self.providers=[]
            self.env['main']()
            self.assertEqual([e[0] for e in self.events if e[0] in ('end','execute','notice')],['end','notice'])
        finally:
            if original is None:sys.modules.pop('infinity_search',None)
            else:sys.modules['infinity_search']=original

    def test_existing_state_aba_and_native_lease_guards_byte_untouched(self):
        old=subprocess.check_output(['git','show',BASE+':'+str(SEARCH.relative_to(ROOT))],
                                    cwd=ROOT,text=True)
        before,after=funcs(old),funcs(SEARCH.read_text())
        for name in ('route','_leased_directory','_query_file_stamp','_query_signature',
                     '_state_rejection_trace','_provider_result','_bounded_results'):
            self.assertEqual(before[name],after[name],name)
        self.assertIn("return provider,'state_changed',{},path",SEARCH.read_text())
        self.assertNotIn('new permission',SEARCH.read_text())

    def test_four_passes_native_and_signer_sources_untouched(self):
        delta=subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines()
        protected=('xbmc/','kodi/','Custom_1198_InfinityNav.xml',
                   'library_navigation.py','signer_policy.py','signer-policy.json',
                   'release-authority.json','.github/workflows/infinity-combined-release.yml')
        for item in delta:
            self.assertFalse(any(item.startswith(p) or item.endswith(p) for p in protected),item)
        self.assertTrue(any(p.endswith('infinity_search.py') for p in delta))
        self.assertTrue(any(p.endswith('plugin.py') for p in delta))

if __name__=='__main__':unittest.main(verbosity=2)
