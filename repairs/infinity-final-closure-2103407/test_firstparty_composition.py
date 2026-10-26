"""Direct dependency checks for exact-source module moves, not an Android PASS."""
import ast
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
import xml.etree.ElementTree as ET

import compose_firstparty as composition

ROOT=Path(__file__).parent
CC=composition.CC


def sources_root():
    return Path(os.environ.get('INFINITY_SIGNED407_SOURCES',ROOT.parents[2]/'baseline-2103407/ownership-local/sources'))


def normalize_imports(tree):
    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom):n.level=0
    return ast.dump(tree,include_attributes=False)


class FirstPartyCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=sources_root();cls.workspace=tempfile.TemporaryDirectory()
        cls.stage=Path(cls.workspace.name)/'addons'
        cls.receipt=composition.compose(cls.sources,cls.stage)
        cls.cc=cls.stage/CC

    @classmethod
    def tearDownClass(cls):cls.workspace.cleanup()

    def setUp(self):
        old_path=list(sys.path);old_modules=dict(sys.modules)
        sys.path.insert(0,str(self.cc))
        def restore():
            sys.path[:]=old_path
            for name in set(sys.modules)-set(old_modules):
                if name.startswith('infinity_modules') or name in ('xbmc','xbmcgui','xbmcaddon','xbmcvfs','module_contract'):
                    sys.modules.pop(name,None)
            for name in ('xbmc','xbmcgui','xbmcaddon','xbmcvfs','module_contract'):
                if name in old_modules:sys.modules[name]=old_modules[name]
        self.addCleanup(restore)

    def test_exact_source_preimages_and_unchanged_user_data_paths(self):
        plan=json.loads((ROOT/'FIRSTPARTY-COMPOSITION-PLAN.json').read_text())['plan']
        for aid,item in plan.items():
            actual={p.relative_to(self.sources/aid).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (self.sources/aid).rglob('*') if p.is_file()}
            self.assertEqual(actual,item['signed407_all_file_preimages'])
        original=self.sources/'script.infinity.rails/resources/lib/store.py'
        self.assertEqual(original.read_bytes(),(self.cc/'infinity_modules/rails/store.py').read_bytes())
        for name in ('common.py','resume_hub.py','saved_navigation.py','selection_contract.py','experience.py'):
            self.assertEqual((self.sources/CC/name).read_bytes(),(self.cc/name).read_bytes())
        self.assertFalse(self.receipt['user_data_mutation']);self.assertFalse(self.receipt['apk_produced'])

    def test_native_watchnixtoons_registration_and_stable_ids_are_preserved(self):
        for aid in (CC,*composition.PACKAGES):
            before=ET.parse(self.sources/aid/'addon.xml').getroot();after=ET.parse(self.stage/aid/'addon.xml').getroot()
            self.assertEqual(before.get('id'),after.get('id'))
            for point in ('kodi.context.item','xbmc.python.script','xbmc.python.pluginsource'):
                self.assertEqual([ET.tostring(n) for n in before.findall('extension') if n.get('point')==point],
                                 [ET.tostring(n) for n in after.findall('extension') if n.get('point')==point])
            self.assertEqual(after.find("extension[@point='xbmc.addon.metadata']/reuselanguageinvoker").text,'false')
        wb=ET.parse(self.stage/'script.infinity.watchedbridge/addon.xml').getroot()
        self.assertIsNone(wb.find("extension[@point='xbmc.service']"))
        cc=ET.parse(self.cc/'addon.xml').getroot()
        self.assertEqual(len(cc.findall("extension[@point='xbmc.service']")),1)

    def test_moved_actions_identity_and_provider_contracts_keep_original_implementation(self):
        for package,aid in ((v,k) for k,v in composition.PACKAGES.items()):
            oldroot=self.sources/aid/('resources/lib' if package=='rails' else '')
            for old in oldroot.glob('*.py'):
                if old.name=='__init__.py':continue
                before=ast.parse(old.read_bytes());after=ast.parse((self.cc/'infinity_modules'/package/old.name).read_bytes())
                changed={'controller_access.py':{'load'},'controller.py':{'verify'},'service.py':{'run'}}.get(old.name,set())
                if package=='uirepair' and old.name=='runtime.py':changed={'rails_supported'}
                originals={n.name:n for n in before.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name not in changed}
                current={n.name:n for n in after.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
                for name,node in originals.items():
                    # "import controller" becomes "from . import controller";
                    # all actual action/identity/mutation code is preserved.
                    self.assertEqual(normalize_imports(node),normalize_imports(current[name]),(package,old.name,name))
        self.assertEqual((self.sources/'script.infinity.watchedbridge/PROVIDER-CONTRACTS.json').read_bytes(),
                         (self.cc/'infinity_modules/watchedbridge/PROVIDER-CONTRACTS.json').read_bytes())

    def test_relocated_provider_identity_still_rejects_ambiguous_or_unverified_titles(self):
        state=importlib.import_module('infinity_modules.watchedbridge.bridge_state')
        movie={'media':'movie','source':'plugin://plugin.video.watchnixtoons2/?id=603',
               'identity':{'schema':1,'kind':'movie','scope':'movie','ids':{'tmdb':'603','imdb':'tt0133093'}}}
        verified=state.identity(movie)
        data={'schema':2,'watched':{'a'*64:movie}}
        rows=state.records(data)
        self.assertEqual(state.lookup(rows,verified),'true')
        other={**verified,'ids':{'tmdb':'604','imdb':'tt0133093'}}
        self.assertEqual(state.lookup(rows,other),'')
        self.assertIsNone(state.identity({'media':'movie','title':'The Matrix'}))
        episode={'media':'tv','source':'plugin://plugin.video.unknown/?title=Same', 'season':1,'episode':1,
                 'identity':{'schema':1,'kind':'episode','scope':'episode','ids':{'tmdb':'123'},'season':1,'episode':1}}
        self.assertEqual(state.records({'schema':2,'watched':{'b'*64:episode}}),[])

    def test_publisher_reuses_cc_scheduler_without_new_worker_or_writer(self):
        tree=ast.parse((self.cc/'service.py').read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        loop=next(n for n in main.body if isinstance(n,ast.While))
        self.assertIn('checkpoint.poll()',ast.unparse(loop.body[0]))
        self.assertIsInstance(loop.body[0].body[-1],ast.Continue)
        body=ast.unparse(main)
        self.assertEqual(body.count('watched_publisher.tick('),1)
        publisher=ast.parse((self.cc/'infinity_modules/watchedbridge/service.py').read_bytes())
        self.assertFalse(any(isinstance(n,(ast.While,ast.AsyncFunctionDef)) for n in ast.walk(publisher)))
        text=ast.unparse(publisher)
        for forbidden in ('Thread(','.write_text(','.write_bytes(','.save(','Monitor('):self.assertNotIn(forbidden,text)
        self.assertIn('self.next_tick = now + 1.0',text)

    def test_publisher_state_survives_ticks_and_updates_without_changing_source_data(self):
        class Home:
            def __init__(self):self.values={'Infinity.ResumeHub.BridgeVersion':'1'}
            def getProperty(self,key):return self.values.get(key,'')
            def setProperty(self,key,value):self.values[key]=value
        home=Home();commands=[]
        xbmc=ModuleType('xbmc');xbmc.getInfoLabel=lambda name:'1';xbmc.executebuiltin=commands.append
        gui=ModuleType('xbmcgui');gui.Window=lambda ident:home
        xa=ModuleType('xbmcaddon')
        profile=Path(self.workspace.name)/'profile';profile.mkdir(exist_ok=True)
        data=profile/'continue-watching.json';raw=b'{"schema":2,"watched":{}}';data.write_bytes(raw)
        class Addon:
            def __init__(self,aid):self.aid=aid
            def getAddonInfo(self,key):
                if self.aid!=CC:raise RuntimeError('Fixture provider unavailable')
                return str(profile)
        xa.Addon=Addon;vfs=ModuleType('xbmcvfs');vfs.translatePath=lambda path:str(profile) if path=='special://profile/' else path
        sys.modules.update(xbmc=xbmc,xbmcgui=gui,xbmcaddon=xa,xbmcvfs=vfs)
        service=importlib.import_module('infinity_modules.watchedbridge.service')
        publisher=service.Publisher();publisher.tick(1.0)
        value=home.getProperty(service.PROPERTY);self.assertTrue(value)
        initial=list(commands);publisher.tick(1.1);publisher.tick(2.0)
        self.assertEqual(commands,initial)
        self.assertEqual(home.getProperty(service.PROPERTY),value)
        self.assertEqual(data.read_bytes(),raw)

    def test_new_rails_package_uses_signed_capability_and_honors_disabled_state(self):
        xbmc=ModuleType('xbmc');xbmc.getCondVisibility=lambda name:True
        gui=ModuleType('xbmcgui');xa=ModuleType('xbmcaddon');vfs=ModuleType('xbmcvfs')
        xa.Addon=lambda aid:SimpleNamespace(getAddonInfo=lambda key:str(self.cc) if key=='path' else composition.VERSION)
        vfs.translatePath=lambda path:path
        contract=ModuleType('module_contract');calls=[]
        def active(root,version):
            calls.append((root,version))
            return SimpleNamespace(entries={'script.infinity.rails/context_add.py':'command_center_client'})
        contract.active_contract=active
        sys.modules.update(xbmc=xbmc,xbmcgui=gui,xbmcaddon=xa,xbmcvfs=vfs,module_contract=contract)
        runtime=importlib.import_module('infinity_modules.uirepair.runtime')
        self.assertTrue(runtime.rails_supported())
        self.assertEqual(calls,[(self.cc,composition.VERSION)])
        xbmc.getCondVisibility=lambda name:False
        self.assertFalse(runtime.rails_supported());self.assertEqual(len(calls),1)
        xbmc.getCondVisibility=lambda name:True
        contract.active_contract=lambda *args:SimpleNamespace(entries={})
        self.assertFalse(runtime.rails_supported())

    def test_current_generation_is_required_before_original_writer_scope(self):
        source=(self.cc/'checkpoint_runtime.py').read_text()
        tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='write_scope')
        self.assertLess(ast.unparse(node).index('require_current()'),ast.unparse(node).index('store_for(profile)'))
        # Original writer scopes, profile lock, PREPARE/FINALIZE and receipts are
        # preserved by exact AST comparison outside the two admitted methods.
        old=ast.parse((self.sources/CC/'checkpoint_runtime.py').read_bytes())
        for before in old.body:
            if isinstance(before,ast.FunctionDef) and before.name!='write_scope':
                after=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==before.name)
                self.assertEqual(ast.dump(before,include_attributes=False),ast.dump(after,include_attributes=False))
        resident_old=next(n for n in old.body if isinstance(n,ast.ClassDef) and n.name=='ResidentCheckpoint')
        resident_new=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ResidentCheckpoint')
        for before in resident_old.body:
            if isinstance(before,ast.FunctionDef) and before.name!='register':
                after=next(n for n in resident_new.body if isinstance(n,ast.FunctionDef) and n.name==before.name)
                self.assertEqual(ast.dump(before,include_attributes=False),ast.dump(after,include_attributes=False))


if __name__=='__main__':unittest.main(verbosity=2)
