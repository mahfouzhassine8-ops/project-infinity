"""Behavior equivalence of the exact Normal command and resident refresh."""
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import patch_home_entry as correction

PARENT=Path(os.environ.get('INFINITY_HOME_PARENT_APK','/workspace/scratch/7aaf34f5a62d/candidate412/resume-candidate/Infinity-2103412-Resume-Render-Corrective-VERIFICATION.apk'))


class HomeEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(PARENT) as z:
            prefix='assets/addons/script.infinity.commandcenter/'
            cls.default=z.read(prefix+'default.py');cls.service=z.read(prefix+'service.py')
            prefix='assets/addons/skin.infinity.diggz/'
            cls.skin={n[len(prefix):]:z.read(n) for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}

    def test_all_profiles_equivalent_normal_state_and_no_layout_or_other_action_change(self):
        actions=correction.normal_actions(self.default)
        result,proof=correction.skin_sources(self.skin,self.default)
        self.assertEqual(len(proof['changed_members']),17)
        for name in [n for n in self.skin if n.endswith('/Home.xml')]:
            old=self.skin[name].decode();new=result[name].decode()
            generated='\n  '.join(correction.VIEW_OPEN+a+'</onload>' for a in actions)
            self.assertEqual(new.replace(generated,correction.VIEW_OPEN+correction.VIEW+'</onload>',1)
                .replace(correction.SYNC_OPEN+correction.REQUEST+'</onload>',correction.SYNC_OPEN+correction.SYNC+'</onload>',1),old)
            self.assertEqual([ET.tostring(n) for n in ET.fromstring(old).findall('controls')],
                             [ET.tostring(n) for n in ET.fromstring(new).findall('controls')])
        # Independently replay every generated native builtin against arbitrary
        # old latches and compare all final fields to the actual Python branch.
        initial={a[14:-6]:'old latch' for a in actions if a.startswith('ClearProperty(')}
        states=[]
        for native in (False,True):
            props=deepcopy(initial);settings={}
            def builtin(value):
                op,args=value.split('(',1);args=args[:-1].split(',')
                if op=='Skin.SetString':settings[args[0]]=args[1]
                elif op=='ClearProperty':props.pop(args[0],None)
                elif op=='SetProperty':props[args[0]]=args[1]
                else:raise AssertionError(op)
            if native:
                for a in actions:builtin(a)
            else:
                node=next(n for n in ast.parse(self.default).body if isinstance(n,ast.FunctionDef) and n.name=='direct_command')
                scope=dict(xbmc=SimpleNamespace(executebuiltin=builtin),
                    xbmcgui=SimpleNamespace(Window=lambda _:SimpleNamespace(clearProperty=lambda key:props.pop(key,None),
                        setProperty=lambda key,value:props.__setitem__(key,value))))
                exec(compile(ast.Module(body=[node],type_ignores=[]),'original-normal','exec'),scope)
                self.assertTrue(scope['direct_command'](['default.py','view-mode','normal']))
            states.append((props,settings))
        self.assertEqual(*states)
        self.assertEqual(states[1][1],{'Infinity.VisualMode':'normal','Infinity.HomeView':'auto'})

    def consumer(self):
        home={};calls=[];environment={'skin':'skin.infinity.diggz','window':10000,'fail':False}
        class Window:
            def getProperty(self,key):return home.get(key,'')
            def clearProperty(self,key):home.pop(key,None)
            def setProperty(self,key,value):home[key]=value
        contract=object()
        def require_current():
            calls.append('require-current')
            if environment['fail']:raise RuntimeError('generation changed')
        def source_module(owner,name,path):
            self.assertIs(owner,contract);self.assertEqual(path,'script.infinity.commandcenter/default.py')
            calls.append('load-signed-default')
            return SimpleNamespace(runtime_sync=lambda **kw:calls.append(('runtime-sync',kw)))
        scope=dict(HOME=Window(),xbmc=SimpleNamespace(getSkinDir=lambda:environment['skin']),
                   xbmcgui=SimpleNamespace(getCurrentWindowId=lambda:environment['window']),
                   log=lambda *a:None,_infinity_contract=contract)
        module=SimpleNamespace(require_current=require_current,source_module=source_module)
        return home,calls,environment,scope,module

    def test_runtime_requests_coalesce_signed_module_reused_and_other_skin_untouched(self):
        home,calls,env,scope,module=self.consumer()
        with patch.dict(sys.modules,{'module_contract':module}):
            exec(correction.CONSUMER,scope);consume=scope['_consume_home_runtime_sync']
            for _ in range(10):home['Infinity.Home.RuntimeSync.Pending']='true'
            self.assertTrue(consume(10));self.assertFalse(consume(10.5));self.assertFalse(consume(12))
            home['Infinity.Home.RuntimeSync.Pending']='true';self.assertTrue(consume(13))
            self.assertEqual(calls.count('load-signed-default'),1)
            self.assertEqual(calls.count(('runtime-sync',{'quiet':True})),2)
            home['Infinity.Home.RuntimeSync.Pending']='true';before=list(calls)
            env['skin']='skin.cobra';self.assertFalse(consume(20));self.assertEqual(calls,before)
            self.assertEqual(home['Infinity.Home.RuntimeSync.Pending'],'true')
            env['skin']='skin.infinity.diggz';env['window']=10025
            self.assertFalse(consume(21));self.assertEqual(calls,before)

    def test_changed_generation_is_not_called_or_marked_complete_and_checkpoint_stays_first(self):
        home,calls,env,scope,module=self.consumer();home['Infinity.Home.RuntimeSync.Pending']='true';env['fail']=True
        with patch.dict(sys.modules,{'module_contract':module}):
            exec(correction.CONSUMER,scope)
            self.assertFalse(scope['_consume_home_runtime_sync'](10))
            self.assertEqual(home['Infinity.Home.RuntimeSync.Pending'],'true')
            self.assertNotIn('load-signed-default',calls)
        revised=correction.patch('service.py',self.service).decode()
        main=revised[revised.index('def main():'):]
        self.assertLess(main.index('if checkpoint.poll():'),main.index('_consume_home_runtime_sync(now)'))
        for name,raw in [('service.py',self.service),('default.py',self.default)]:
            text=correction.patch(name,raw).decode()
            for old,new in reversed(correction.python_edits(name)):text=text.replace(new,old,1)
            self.assertEqual(text.encode(),raw)
        function=lambda raw,name:ast.dump(next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name==name))
        self.assertEqual(function(self.default,'runtime_sync'),
                         function(correction.patch('default.py',self.default),'runtime_sync'))

    def test_missing_optional_refresh_does_not_construct_addon_installed_settings_preserved(self):
        fn=next(n for n in ast.parse(correction.patch('default.py',self.default)).body
                if isinstance(n,ast.FunctionDef) and n.name=='_read_refresh_state')
        calls=[];installed=[False]
        scope=dict(xbmc=SimpleNamespace(getCondVisibility=lambda expression:installed[0]),
            xbmcaddon=SimpleNamespace(Addon=lambda aid:(calls.append(aid) or SimpleNamespace(getSetting=lambda key:{'mode':'system','max_hz':'90'}[key]))))
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-refresh-read','exec'),scope)
        for _ in range(100):self.assertEqual(scope['_read_refresh_state'](),('auto','auto'))
        self.assertEqual(calls,[])
        installed[0]=True;self.assertEqual(scope['_read_refresh_state'](),('system','90'))
        self.assertEqual(calls,['service.infinity.refresh'])


if __name__=='__main__':unittest.main(verbosity=2)
