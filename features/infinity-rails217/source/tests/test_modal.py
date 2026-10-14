"""Exercise the real menu callback class through a simulated Kodi modal API."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import types
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'addons/script.infinity.rails/resources'))
from lib import menu


class ModalTests(unittest.TestCase):
    def setUp(self):
        self.properties={'Infinity.NativeReady':'true','Infinity.NativeDisplayRevision':'1',
                         'Infinity.NativeWidthDp':'384','Infinity.NativeHeightDp':'832'}
        self.aborting=False
        self.actions=[]
        self.logs=[]
        self.instances=[]
        self.scenario=lambda dialog:dialog.onClick(9)
        test=self
        class Control:
            def __init__(obj):obj.visible=True;obj.enabled=True;obj.label='';obj.animations=[];obj.nav=None
            def setAnimations(obj,a):obj.animations=a
            def setHeight(obj,h):obj.height=h
            def setImage(obj,p):obj.image=p
            def setVisible(obj,v):obj.visible=v
            def setEnabled(obj,v):obj.enabled=v
            def setLabel(obj,v):obj.label=v
            def setPosition(obj,x,y):obj.position=x,y
            def setNavigation(obj,*controls):obj.nav=controls
        class Window:
            def getProperty(obj,k):return test.properties.get(k,'')
        class XMLDialog:
            def __new__(cls,*a,**kw):
                obj=object.__new__(cls);obj.controls={};obj.properties={};obj.closed=threading.Event();obj.focus=200
                test.instances.append(obj);return obj
            def getWidth(obj):return 1080
            def getHeight(obj):return 2400
            def getControl(obj,c):return obj.controls.setdefault(c,Control())
            def setProperty(obj,k,v):obj.properties[k]=v
            def setFocusId(obj,c):obj.focus=c
            def getFocusId(obj):return obj.focus
            def close(obj):obj.closed.set()
            def doModal(obj):
                obj.onInit()
                test.scenario(obj)
                if not obj.closed.wait(1):
                    raise AssertionError('Modal did not close promptly.')
        self.gui=types.SimpleNamespace(WindowXMLDialog=XMLDialog,Window=lambda i:Window())
        self.xbmc=types.SimpleNamespace(Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:self.aborting),
                                      log=lambda *a:self.logs.append(a),LOGDEBUG=0)

    def choose(self, choices=None):
        return menu.select(self.gui,self.xbmc,Path('/fixture'),'INFINITY — RAIL OPTIONS','Empflix',
                           choices or [('open','Open Add-on'),('move','Move / Reorder'),('remove','Remove from TV Show Add-ons'),('settings','Add-on Settings'),(None,'Cancel')])

    def test_open_dispatches_selected_action(self):
        self.scenario=lambda d:d.onClick(200)
        self.assertEqual(self.choose(),'open')

    def test_remove_dispatches_selected_action(self):
        self.scenario=lambda d:d.onClick(202)
        self.assertEqual(self.choose(),'remove')

    def test_cancel_dispatches_no_action(self):
        self.scenario=lambda d:d.onClick(204)
        self.assertIsNone(self.choose())

    def test_x_dispatches_no_action(self):
        self.assertIsNone(self.choose())

    def test_back_dispatches_no_action(self):
        self.scenario=lambda d:d.onAction(types.SimpleNamespace(getId=lambda:92))
        self.assertIsNone(self.choose())

    def test_foreground_resize_dismisses_without_action(self):
        self.scenario=lambda d:self.properties.update({'Infinity.NativeDisplayRevision':'2','Infinity.NativeWidthDp':'832','Infinity.NativeHeightDp':'384'})
        self.assertIsNone(self.choose())
        self.assertTrue(self.instances[-1].done.is_set())
        self.assertFalse(self.instances[-1].observer.is_alive())

    def test_shutdown_dismisses_without_action(self):
        def abort(d):self.aborting=True
        self.scenario=abort
        self.assertIsNone(self.choose())
        self.assertFalse(self.instances[-1].observer.is_alive())

    def test_metrics_changing_during_init_never_opens(self):
        self.properties['Infinity.NativeReady']='false'
        self.assertIsNone(self.choose())
        self.assertIsNone(self.instances[-1].observer)

    def test_resize_racing_click_cannot_commit_old_geometry(self):
        def race(d):
            self.properties['Infinity.NativeDisplayRevision']='2'
            d.onClick(202)
        self.scenario=race
        self.assertIsNone(self.choose())

    def test_long_reorder_list_is_paged_and_navigable(self):
        choices=[(i,'Before add-on '+str(i)) for i in range(256)]+[(None,'Cancel')]
        def pick(d):
            d.onClick(211)
            self.assertEqual(d.getControl(200).label,'Before add-on 5')
            self.assertTrue(d.getControl(210).enabled)
            d.onClick(202)
        self.scenario=pick
        self.assertEqual(self.choose(choices),7)

    def test_last_partial_page_hides_empty_rows(self):
        def last(d):
            d.onClick(211)
            self.assertTrue(d.getControl(200).visible)
            self.assertFalse(d.getControl(201).visible)
            self.assertFalse(d.getControl(211).enabled)
            self.assertIs(d.getControl(200).nav[1],d.getControl(210))
            d.onClick(200)
        self.scenario=last
        self.assertEqual(self.choose([(i,str(i)) for i in range(6)]),5)

    def test_short_landscape_pages_and_keeps_cancel(self):
        self.properties.update({'Infinity.NativeWidthDp':'832','Infinity.NativeHeightDp':'250'})
        def cancel(d):
            self.assertLess(d.capacity,5)
            while d.getControl(211).enabled:
                d.onClick(211)
            d.onClick(200 + len(d.mapping)-1)
        self.scenario=cancel
        self.assertIsNone(self.choose())

    def test_repeated_open_close_leaves_no_observers(self):
        baseline={t.ident for t in threading.enumerate()}
        for _ in range(100):
            self.assertIsNone(self.choose())
        self.assertFalse([t for t in threading.enumerate() if t.ident not in baseline and t.name=='InfinityRailsModalBounds'])

    def test_reinitialization_keeps_one_foreground_observer(self):
        def reinit(d):
            original=d.observer
            d.onInit()
            self.assertIs(d.observer,original)
            d.onClick(9)
        self.scenario=reinit
        self.assertIsNone(self.choose())

    def test_two_interpreters_cannot_open_simultaneous_modal(self):
        with tempfile.TemporaryDirectory() as p:
            with menu.menu_lock(p) as first:
                self.assertTrue(first)
                with menu.menu_lock(p) as second:
                    self.assertFalse(second)
            with menu.menu_lock(p) as third:
                self.assertTrue(third)

    def test_unexpected_key_does_not_dispatch_action(self):
        def unknown(d):
            d.onClick(999)
            self.assertIsNone(d.result)
            d.onClick(9)
        self.scenario=unknown
        self.assertIsNone(self.choose())


if __name__=='__main__':
    unittest.main()
