"""Actual signed413 getters with Kodi's compiled enabled-only constructor."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from zipfile import ZipFile
import patch_refresh_enabled as correction


class EnabledRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(Path(os.environ['INFINITY_REFRESH_PARENT_APK'])) as z:
            cls.raw={n:z.read('assets/addons/'+correction.CC+'/'+n) for n in ('service.py','default.py','addon.xml')}

    def load(self,name,raw,scope):
        fn='_refresh_setting' if name=='service.py' else '_read_refresh_state'
        node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name==fn)
        exec(compile(ast.Module(body=[node],type_ignores=[]),name,'exec'),scope)
        return scope[fn]

    def test_only_constructor_guard_or_declared_version_changes(self):
        for n,raw in self.raw.items():
            updated=correction.patch(n,raw)
            old,new=(('version="0.3.5.43"','version="0.3.5.44"') if n=='addon.xml' else
                     ('System.HasAddon(service.infinity.refresh)','System.AddonIsEnabled(service.infinity.refresh)'))
            self.assertEqual(updated.replace(new.encode(),old.encode(),1),raw)
            with self.assertRaises(ValueError):correction.patch(n,raw+b'\n')

    def test_real_disabled_constructor_defaults_match_without_exception_loop(self):
        state=dict(installed=True,enabled=False);calls=[];values=dict(mode='balanced',max_hz='90')
        def addon(aid):
            calls.append(aid)
            if not state['enabled']:raise RuntimeError('Actual Kodi OnlyEnabled::CHOICE_YES rejection')
            return SimpleNamespace(getSetting=lambda key:values.get(key,''))
        def visible(query):
            if query=='System.HasAddon(service.infinity.refresh)':return state['installed']
            if query=='System.AddonIsEnabled(service.infinity.refresh)':return state['enabled']
            raise AssertionError(query)
        scope=dict(xbmc=SimpleNamespace(getCondVisibility=visible),xbmcaddon=SimpleNamespace(Addon=addon))
        for name in ('service.py','default.py'):
            before=self.load(name,self.raw[name],dict(scope));after=self.load(name,correction.patch(name,self.raw[name]),dict(scope))
            invoke=lambda f:f('mode','auto') if name=='service.py' else f()
            expected='auto' if name=='service.py' else ('auto','auto')
            calls.clear()
            for _ in range(100):self.assertEqual(invoke(before),expected)
            self.assertEqual(len(calls),100);calls.clear()
            for _ in range(100):self.assertEqual(invoke(after),expected)
            self.assertEqual(calls,[])
            state['installed']=False;self.assertEqual(invoke(after),expected);self.assertEqual(calls,[])
            state.update(installed=True,enabled=True)
            self.assertEqual(invoke(after),'balanced' if name=='service.py' else ('balanced','90'))
            values['mode']='auto';values['max_hz']='120'
            self.assertEqual(invoke(after),'auto' if name=='service.py' else ('auto','120'))
            state['enabled']=False;calls.clear();self.assertEqual(invoke(after),expected);self.assertEqual(calls,[])
            values.update(mode='balanced',max_hz='90')


if __name__=='__main__':unittest.main(verbosity=2)
