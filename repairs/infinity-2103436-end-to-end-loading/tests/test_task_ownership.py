"""Focused lifetime regressions, not Android/physical timing evidence."""
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
source=Path(os.environ.get('LOADING_SOURCE',str(ROOT/'overlay/script.infinity.commandcenter/action_loading.py')))
spec=importlib.util.spec_from_file_location('loading',source);loading=importlib.util.module_from_spec(spec);spec.loader.exec_module(loading)

def context(**changes):
    value={key:'' for key in loading.IDENTITY}
    value.update(window=10000,control=8801,item='1',profile='profile-a',geometry='1600|1680',dialog=0,playback='',busy=False,framed=True,allowed=True)
    value.update(changes);return value

def begin(token,owner,born=1):
    return dict(token=token*32,state='preparing',born=born,target='a'*64,foreground=False,owner={k:owner[k] for k in loading.IDENTITY})

class OwnershipTests(unittest.TestCase):
    def test_other_task_completion_does_not_discard_delayed_start(self):
        state=loading.LoadingState();ctx=context()
        state.event(begin('b',ctx),1,ctx)
        state.event(dict(token='b'*32,state='ready',sent=2),2,ctx)
        state.event(begin('a',ctx,1.5),2.1,ctx)
        self.assertEqual(state.tick(2.2,ctx)['Global'],'true')
        state.event(dict(token='a'*32,state='ready',sent=2.3),2.3,ctx)
        self.assertEqual(state.tick(2.4,ctx)['Global'],'false')
        state.event(begin('b',ctx),2.5,ctx)
        self.assertFalse(state.jobs)

    def test_background_resize_keeps_pending_work(self):
        state=loading.LoadingState();ctx=context();state.event(begin('a',ctx),1,ctx)
        self.assertEqual(state.tick(2,context(geometry='1080|2520'))['Global'],'true')
        self.assertEqual(state.tick(3,context(profile='profile-b'))['Global'],'false')

    def test_background_old_profile_is_rejected(self):
        state=loading.LoadingState();state.event(begin('a',context()),1,context(profile='profile-b'))
        self.assertEqual(state.tick(2,context(profile='profile-b'))['Global'],'false')

    def test_monitor_window_change_preserves_background_until_terminal(self):
        class Home:
            def __init__(self):self.values={}
            def setProperty(self,k,v):self.values[k]=v
            def clearProperty(self,k):self.values.pop(k,None)
        class Gui:
            def __init__(self):self.home=Home()
            def Window(self,n):return self.home
        class Xbmc:
            class Monitor:pass
        gui=Gui();monitor=loading.make_monitor(Xbmc(),gui)
        ctx=context()
        with patch.object(loading,'_context',return_value=ctx),patch.object(loading.time,'monotonic',return_value=1):
            monitor.tick();monitor.onNotification(loading.SENDER,loading.EVENT,json.dumps(begin('a',ctx)))
        with patch.object(loading,'_context',return_value=ctx),patch.object(loading.time,'monotonic',return_value=2):monitor.tick()
        with patch.object(loading,'_context',return_value=context(window=10025)),patch.object(loading.time,'monotonic',return_value=3):monitor.tick()
        self.assertEqual(gui.home.values['Infinity.Loading.Global'],'true')
        with patch.object(loading,'_context',return_value=context(window=10025)),patch.object(loading.time,'monotonic',return_value=4):
            monitor.onNotification(loading.SENDER,loading.EVENT,json.dumps(dict(token='a'*32,state='ready',sent=4)));monitor.tick()
        self.assertEqual(gui.home.values['Infinity.Loading.Global'],'false')

if __name__=='__main__':
    scope=json.loads((ROOT/'SCOPE.json').read_text());assert scope['selected_before_execution']
    selected=scope['selected_tests'];assert sorted(selected)==unittest.defaultTestLoader.getTestCaseNames(OwnershipTests)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(OwnershipTests(n) for n in selected))
    raise SystemExit(not result.wasSuccessful())
