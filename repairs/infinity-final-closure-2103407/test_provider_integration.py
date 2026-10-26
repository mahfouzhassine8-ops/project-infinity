"""Actual composed inventory -> version/source pinned route, without provider execution."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from urllib.parse import parse_qs,urlsplit
from unittest.mock import patch
import xml.etree.ElementTree as ET

import compose_firstparty

ROOT=Path(__file__).parent
CREW=Path(os.environ.get('CREW_SOURCE_ROOT','/workspace/scratch/ea870406277a/upstream-sources'))
RED=Path(os.environ.get('REDLIGHT_SOURCE_ROOT','/workspace/scratch/9491f79db5c3/provider-official-readonly/sources/plugin.video.redlight'))
SIGNED=Path(os.environ.get('INFINITY_SIGNED407_SOURCES','/workspace/scratch/9491f79db5c3/baseline-2103407/ownership-local/sources'))


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value


class ProviderIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        compose_firstparty.compose(SIGNED,self.root/'composed')
        self.cc=self.root/'composed/script.infinity.commandcenter'
        self.paths={};self.rows=[]
        profile=json.loads((ROOT/'SEARCH-STRUCTURES.json').read_text())['profiles'][0]
        inventories={
            'plugin.video.thecrew':(CREW/'plugin.video.thecrew',{'addon.xml','thecrew.py'}),
            'script.module.thecrew':(CREW/'script.module.thecrew',{'addon.xml',profile['router']}|{r['path'] for r in profile['receivers'].values()}),
            'plugin.video.redlight':(RED,{'addon.xml'}|set(json.loads((ROOT/'MODE-CLASS-SEARCH-POLICY.json').read_text())['shapes']))}
        for aid,(source,names) in inventories.items():
            target=self.root/aid;self.paths[aid]=target
            for name in names:
                p=target/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
            if aid.startswith('plugin.video.'):
                version=ET.parse(target/'addon.xml').getroot().get('version')
                self.rows.append(dict(addonid=aid,name='[COLOR red]'+aid+'[/COLOR]',enabled=True,version=version))
        self.props={};home=types.SimpleNamespace(getProperty=lambda k:self.props.get(k,''),setProperty=self.props.__setitem__)
        def addon(aid):
            p=self.cc if aid=='script.infinity.commandcenter' else self.paths[aid]
            version=ET.parse(p/'addon.xml').getroot().get('version')
            return types.SimpleNamespace(getAddonInfo=lambda key:str(p) if key=='path' else version if key=='version' else '')
        def visibility(query):
            for row in self.rows:
                if row['addonid'] in query:return row['enabled']
            return any(aid in query for aid in self.paths)
        def source(root,name):
            p=root/name
            if Path(name).is_absolute() or '..' in Path(name).parts or not p.resolve().is_relative_to(root) or p.is_symlink():raise ValueError('unsafe source')
            raw=p.read_bytes()
            if len(raw)>512*1024:raise ValueError('source too large')
            return raw
        class Monitor:pass
        modules={
            'xbmc':types.SimpleNamespace(Monitor=Monitor,getCondVisibility=visibility),
            'xbmcgui':types.SimpleNamespace(Window=lambda *args:home),
            'xbmcaddon':types.SimpleNamespace(Addon=addon),
            'xbmcvfs':types.SimpleNamespace(translatePath=lambda p:p),
            'xbmcplugin':types.SimpleNamespace(),
            'saved_navigation':types.SimpleNamespace(_source=source,fingerprint=lambda *args:(_ for _ in ()).throw(AssertionError('Unexpected legacy family'))),
        }
        old={k:sys.modules.get(k) for k in ('provider_inventory','provider_capabilities','structural_search','infinity_search')}
        def restore():
            for k,v in old.items():
                if v is None:sys.modules.pop(k,None)
                else:sys.modules[k]=v
        self.addCleanup(restore)
        self.patch=patch.dict(sys.modules,modules);self.patch.start();self.addCleanup(self.patch.stop)
        load('provider_capabilities',self.cc/'provider_capabilities.py')
        load('structural_search',self.cc/'structural_search.py')
        self.inv=load('provider_inventory',self.cc/'provider_inventory.py')
        self.inv._rpc=lambda *args,**kwargs:dict(addons=self.rows)
        original=self.inv._verify;self.verifications=0
        def verify(*args,**kwargs):
            self.verifications+=1;return original(*args,**kwargs)
        self.inv._verify=verify
        self.search=load('infinity_search',self.cc/'infinity_search.py')

    def test_actual_four_media_operations_inventory_labels_and_dispatch(self):
        for media in ('movie','tv'):
            ready,unavailable=self.inv.eligible(media,force=True)
            self.assertEqual(len(ready),2);self.assertEqual(unavailable,[])
            self.assertTrue(all('[COLOR' not in p['name'] for p in ready))
            for provider in ready:
                uri=self.search.route(provider,'Literal % & query')
                self.assertEqual(urlsplit(uri).netloc,provider['id'])
                self.assertEqual(parse_qs(urlsplit(uri).query)[provider['contract']['query_key']],['Literal % & query'])
        self.assertEqual(self.inv.eligible('tv',operation='title_navigation',force=True)[0],[])
        self.assertEqual(self.verifications,2)  # unchanged own/dependency stamps avoid repeated AST work

    def test_update_disable_reenable_and_dependency_mutation_revalidate(self):
        ready,_=self.inv.eligible('movie',force=True)
        crew=next(p for p in ready if p['id']=='plugin.video.thecrew')
        red=next(p for p in ready if p['id']=='plugin.video.redlight')
        # Change code bytes without changing compatible semantics or package
        # versions. Every old proof must fail; rediscovery must regenerate it.
        dep=self.paths['script.module.thecrew']/'lib/resources/lib/modules/crew.py'
        dep.write_bytes(dep.read_bytes()+b'\n# compatible source update\n')
        with self.assertRaises(RuntimeError):self.search.route(crew,'query')
        current=next(p for p in self.inv.eligible('movie',force=True)[0] if p['id']==crew['id'])
        self.search.route(current,'query')
        rp=self.paths['plugin.video.redlight']/'resources/lib/modules/router.py'
        rp.write_bytes(rp.read_bytes()+b'\n# compatible source update\n')
        with self.assertRaises(RuntimeError):self.search.route(red,'query')
        current=next(p for p in self.inv.eligible('movie',force=True)[0] if p['id']==red['id'])
        self.search.route(current,'query')
        row=next(r for r in self.rows if r['addonid']==red['id']);row['enabled']=False
        with self.assertRaises(RuntimeError):self.search.route(current,'query')
        self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)
        row['enabled']=True;self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),2)
        self.rows.append(dict(addonid='script.module.thecrew',name='module',version='3.2.26',enabled=False))
        with self.assertRaises(RuntimeError):self.search.route(crew,'query')
        self.assertEqual(len(self.inv.eligible('movie',force=True)[0]),1)


if __name__=='__main__':unittest.main(verbosity=2)
