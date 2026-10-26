"""Remove a measured exception path without changing installed refresh settings."""
import ast
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import compose_firstparty as composition


class RefreshLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.output=Path(cls.temp.name)/'addons'
        cls.sources=Path(os.environ['INFINITY_SIGNED407_SOURCES'])
        composition.compose(cls.sources,cls.output)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def function(self,source,scope):
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_refresh_setting')
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'actual-refresh-function','exec'),scope)
        return scope['_refresh_setting']

    def test_only_existence_guard_changes_original_refresh_function(self):
        before=(self.sources/composition.CC/'service.py').read_text()
        after=(self.output/composition.CC/'service.py').read_text()
        guard="        if not xbmc.getCondVisibility('System.HasAddon(service.infinity.refresh)'):\n            return default\n"
        self.assertEqual(after.count(guard),1)
        old=next(n for n in ast.parse(before).body if isinstance(n,ast.FunctionDef) and n.name=='_refresh_setting')
        same=next(n for n in ast.parse(after.replace(guard,'',1)).body if isinstance(n,ast.FunctionDef) and n.name=='_refresh_setting')
        self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(same,include_attributes=False))

    def test_absent_lookup_avoids_2000_exceptions_but_dynamic_and_disabled_settings_remain_live(self):
        installed=[False];calls=[];values={'mode':'balanced','max_hz':'90'}
        def addon(name):
            calls.append(name)
            if not installed[0]:raise RuntimeError('Unknown addon id service.infinity.refresh')
            return SimpleNamespace(getSetting=lambda key:values.get(key,''))
        probes=[]
        def has_addon(query):probes.append(query);return installed[0]
        scope=dict(xbmc=SimpleNamespace(getCondVisibility=has_addon),xbmcaddon=SimpleNamespace(Addon=addon))
        before=self.function((self.sources/composition.CC/'service.py').read_text(),dict(scope))
        after=self.function((self.output/composition.CC/'service.py').read_text(),dict(scope))
        for _ in range(1000):self.assertEqual((before('mode','auto'),before('max_hz','auto')),('auto','auto'))
        self.assertEqual(len(calls),2000);calls.clear()
        for _ in range(1000):self.assertEqual((after('mode','auto'),after('max_hz','auto')),('auto','auto'))
        self.assertEqual(calls,[])
        self.assertEqual(set(probes),{'System.HasAddon(service.infinity.refresh)'})
        # HasAddon remains true for installed-but-disabled settings, matching
        # the original Addon constructor semantics. Never use IsEnabled here.
        installed[0]=True
        self.assertEqual((after('mode','auto'),after('max_hz','auto')),('balanced','90'))
        values['max_hz']='120';self.assertEqual(after('max_hz','auto'),'120')
        installed[0]=False;self.assertEqual(after('mode','auto'),'auto')
        self.assertEqual(len(calls),3)


if __name__=='__main__':unittest.main(verbosity=2)
