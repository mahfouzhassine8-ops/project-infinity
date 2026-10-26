"""Exercise the actual signed inventory scan after bounded structural integration."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import types
import sys
import unittest
from unittest.mock import patch

import patch_provider_capabilities as capability_patch
import patch_mode_class_integration as mode_patch

ROOT=Path(__file__).parent
SOURCE=Path(__file__).resolve().parents[3]/'baseline-2103407/ownership-local/sources/script.infinity.commandcenter/provider_inventory.py'

class StructuralCache(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);self.cc=self.root/'cc';self.cc.mkdir()
  (self.cc/'provider_inventory.py').write_bytes(capability_patch.patch('provider_inventory.py',SOURCE.read_bytes()))
  self.report=mode_patch.finalize(self.cc)
  self.plugin=self.root/'plugin.video.fixture';self.plugin.mkdir()
  (self.plugin/'addon.xml').write_text('<addon id="plugin.video.fixture"><extension point="xbmc.python.pluginsource" library="main.py"/></addon>')
  (self.plugin/'main.py').write_text('query = "first"\n')
  self.dep=self.root/'script.module.fixture';self.dep.mkdir();(self.dep/'router.py').write_text('router = "first"\n')
  self.enabled=True;self.version='1.0';self.calls=0
  def read(root,name):return (root/name).read_bytes()
  mods={'saved_navigation':types.SimpleNamespace(_source=read,fingerprint=lambda raw,aid:None),
        'xbmc':types.SimpleNamespace(Monitor=type('Monitor',(),{})),
        'xbmcaddon':types.SimpleNamespace(Addon=lambda aid:types.SimpleNamespace(getAddonInfo=lambda key:str(self.plugin) if key=='path' else 'icon')),
        'xbmcgui':types.SimpleNamespace(),'xbmcvfs':types.SimpleNamespace(translatePath=lambda x:x)}
  p=patch.dict(sys.modules,mods);p.start();self.addCleanup(p.stop)
  spec=importlib.util.spec_from_file_location('actual_patched_inventory',self.cc/'provider_inventory.py')
  self.inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.inv)
  def resolve(aid):
   if not self.enabled:raise RuntimeError('disabled dependency')
   return self.dep,self.version
  self.inv._resolve_search_dependency=resolve
  def automatic(aid,root,manifest):
   self.calls+=1
   contract={'params':{'action':'verified'},'query_key':'q','pins':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ('addon.xml','main.py')},
             'dependencies':[{'id':'script.module.fixture','root':str(self.dep),'version':self.version,'pins':{'router.py':hashlib.sha256((self.dep/'router.py').read_bytes()).hexdigest()}}]}
   return {('movie','search'):{'id':aid,'root':str(root),'family':'test-reviewed-family','contract':contract}}
  self.inv._automatic_search=automatic
  self.rows=[dict(addonid='plugin.video.fixture',name='[B][COLOR cyan]Fixture[/COLOR][/B]',version='1.0',enabled=True)]
 def scan(self,prior):return self.inv._scan(self.rows,[],'unchanged-contract-policy',prior)
 def test_reuse_is_cheap_while_own_and_dependency_updates_reverify(self):
  rows,proof=self.scan({});self.assertEqual(self.calls,1)
  self.assertEqual(rows[0]['name'],'Fixture')
  for i in range(20):rows,proof=self.scan(proof)
  self.assertEqual(self.calls,1,'An unchanged dependency must not force repeated AST recognition')
  self.assertEqual(set(rows[0]['operations']),{('movie','search')})
  (self.plugin/'main.py').write_text('query = "changed own source"\n')
  rows,proof=self.scan(proof);self.assertEqual(self.calls,2)
  (self.dep/'router.py').write_text('router = "changed dependency source"\n')
  rows,proof=self.scan(proof);self.assertEqual(self.calls,3)
  self.version='1.1';rows,proof=self.scan(proof);self.assertEqual(self.calls,4)
  self.assertEqual(rows[0]['operations'][('movie','search')]['contract']['dependencies'][0]['version'],'1.1')
 def test_disabled_dependency_and_provider_never_reuse_positive_proofs(self):
  rows,proof=self.scan({});self.enabled=False
  rows,retained=self.scan(proof);self.assertEqual(rows[0]['status'],'unsupported');self.assertEqual(rows[0]['operations'],{});self.assertEqual(retained,{})
  self.enabled=True;self.rows[0]['enabled']=False
  rows,retained=self.scan(proof);self.assertEqual(rows[0]['status'],'disabled');self.assertEqual(rows[0]['operations'],{});self.assertEqual(retained,{})

if __name__=='__main__':unittest.main(verbosity=2)
