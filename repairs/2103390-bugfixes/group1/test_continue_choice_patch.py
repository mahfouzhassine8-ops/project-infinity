"""Signed-base Infinity Continue Watching chooser tests; no runtime installation."""
import ast
import copy
import hashlib
import re
import sys
import types
import unittest
from pathlib import Path
from zipfile import ZipFile
import continue_choice_patch as fix

APK=Path('/mnt/data/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk')
SHA='778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'

class Item:
    def __init__(self): self.props={'IsPlayable':'true','Infinity.ResumeHub.Key':'a'*64}
    def setProperty(self,k,v): self.props[k]=v

class FakeHub:
    KEY_RE=re.compile(r'[a-f0-9]{64}')
    def __init__(self,state): self.state=state
    def load_view(self,profile): return copy.deepcopy(self.state)
    def entry_identity(self,e): return e.get('identity')

class FakeController:
    PROFILE='/example'
    def __init__(self,state):self.hub=FakeHub(state)
    def number(self,n):return float(n or 0)
    def _target(self,e,sources):return e.get('source') or ''
    def _list_item(self,e,data,bucket): return e['source'],Item()

@unittest.skipUnless(APK.is_file(),'Exact 2103390 signed parent required')
class TestChoice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apkbytes=APK.read_bytes()
        assert hashlib.sha256(cls.apkbytes).hexdigest()==SHA
        with ZipFile(APK) as z:
            cls.proposed=fix.proposed_members(APK)
            cls.runtime=z.read(fix.RUNTIME)
            cls.homes={n:z.read(n) for n in cls.proposed if fix.home_type(n)}

    def test_01_original_signed_and_14_homes(self):
        self.assertEqual(len(self.homes),14)
        self.assertEqual(len(self.proposed),15)
        self.assertEqual(fix.digest(self.runtime),fix.RUNTIME_SHA256)

    def test_02_exact_home_delta_two_scoped_lines_each(self):
        for path,original in self.homes.items():
            with self.subTest(path=path):
                changed=self.proposed[path]
                old=changed
                for act in fix.ACTIONS.values():
                    self.assertEqual(changed.count(act),1)
                    old=old.replace(act,b'')
                self.assertEqual(old,original)

    def test_03_runtime_only_handler_and_dispatch_inserted(self):
        changed=self.proposed[fix.RUNTIME]
        self.assertEqual(changed.count(fix.HELPER.encode()),1)
        stripped=changed.replace(fix.HELPER.encode(),b'',1).replace(fix.DISPATCH_AFTER,fix.DISPATCH_BEFORE,1)
        self.assertEqual(stripped,self.runtime)
        compile(changed.decode(),'runtime.py','exec')

    def test_04_fail_closed_on_unknown_or_second_patch(self):
        path=next(iter(self.homes))
        with self.assertRaises(ValueError):fix.patch_home(path,self.homes[path]+b' ')
        with self.assertRaises(ValueError):fix.patch_home(path,self.proposed[path])
        with self.assertRaises(ValueError):fix.patch_runtime(self.runtime+b'\n')
        with self.assertRaises(ValueError):fix.patch_runtime(self.proposed[fix.RUNTIME])

    def test_05_does_not_change_cobra_shutdown_3p_or_engine(self):
        self.assertEqual(set(self.proposed),set(self.homes)|{fix.RUNTIME})
        for path in self.proposed:
            self.assertNotIn('cobra',path.lower())
            self.assertNotIn('lib/',path)
            self.assertNotIn('shutdown',path)
            self.assertFalse(path.startswith('assets/addons/plugin.video.'))

    def _run(self,decision,media='movie',modify=None,item=None):
        calls=[]; dialog=[]; self.state={
            'items':{'a'*64:dict(key='a'*64,media=media,identity={'scope':'media','ids':{'tmdb':'100'}},
                 source='plugin://plugin.video.example/?id=100',position=120,duration=1200,updated=15,
                 label='Example',watched=False)},'sources':{}}
        controller=FakeController(self.state)
        gui=types.SimpleNamespace(Dialog=lambda:types.SimpleNamespace(ok=lambda *args:dialog.append(('ok',args)),notification=lambda *a,**kw:dialog.append(('notice',a))))
        xbmc=types.SimpleNamespace(Player=lambda:types.SimpleNamespace(play=lambda *a,**kw:calls.append((a,kw))))
        sys.modules['controller_access']=types.SimpleNamespace(load=lambda:controller)
        def fake_choose(title,options):
            self.assertIn('Continue Watching',title)
            self.assertEqual(options[0][1],'resume')
            self.assertEqual(options[-1][1],'begin')
            if modify:modify(self.state)
            return decision
        parsed=ast.parse(fix.HELPER)
        ns={'choose':fake_choose,'xbmc':xbmc,'xbmcgui':gui}
        exec(compile(parsed,'helper','exec'),ns)
        try:ns['home_continue_choice'](item if item is not None else 'a'*64,media)
        finally:sys.modules.pop('controller_access',None)
        return calls,dialog

    def test_06_resume_reuses_verified_listitem_and_offset(self):
        calls,dialog=self._run('resume')
        self.assertEqual(len(calls),1)
        args,_=calls[0];self.assertEqual(args[0],'plugin://plugin.video.example/?id=100')
        self.assertEqual(args[1].props['StartOffset'],'120.0')
        self.assertEqual(args[1].props['ResumeTime'],'120.0')
        self.assertEqual(dialog,[])

    def test_07_begin_zero_offset_and_preserves_original_live_url(self):
        calls,dialog=self._run('begin',media='tv')
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0][1].props['StartOffset'],'0')
        self.assertEqual(calls[0][0][1].props['ResumeTime'],'0')
        self.assertFalse(dialog)

    def test_08_back_cancels_without_playback_or_writes(self):
        calls,dialog=self._run(None)
        self.assertFalse(calls)
        self.assertFalse(dialog)

    def test_09_reject_changed_source_during_popup(self):
        calls,dialog=self._run('resume',modify=lambda d:d['items']['a'*64].update(source='plugin://plugin.video.other/'))
        self.assertFalse(calls);self.assertTrue(dialog)

    def test_10_reject_changed_progress_during_popup(self):
        calls,dialog=self._run('resume',modify=lambda d:d['items']['a'*64].update(position=800))
        self.assertFalse(calls);self.assertTrue(dialog)

    def test_11_reject_missing_key(self):
        calls,dialog=self._run('resume',item='not-a-key')
        self.assertFalse(calls)

    def test_12_unavailable_source_preserves_specific_error(self):
        original_target=FakeController._target
        FakeController._target=lambda self,e,sources:''
        try:
            calls,dialog=self._run('resume')
            self.assertEqual(calls,[])
            self.assertEqual(dialog[0][0], 'ok')
            self.assertIn('source is unavailable',str(dialog[0][1]))
        finally:
            FakeController._target=original_target

if __name__=='__main__':unittest.main(verbosity=2)
