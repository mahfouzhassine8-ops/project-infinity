#!/usr/bin/env python3
"""Exercise actual candidate callbacks, lifecycle, geometry and byte preservation."""
import ast
import importlib.util
import math
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import build

BASE = Path(__file__).resolve().parents[3]
SKIN_PATH = Path(os.environ.get('SKIN_BASE', str(BASE/'provider-repair/candidate197/skin.infinity.diggz-1.0.5.197-Browser-Focus-RC1.zip')))
SAVER_PATH = Path(os.environ.get('SAVER_BASE', str(BASE/'upload/screensaver.arctic.mirage-420-INSTALLED-20261004-203213-1.zip')))
SKIN_OLD = build.read_zip(SKIN_PATH, build.SKIN_ID)
SAVER_OLD = build.read_zip(SAVER_PATH, build.SAVER_ID)
SKIN, ADDITIONS = build.repair_skin(SKIN_OLD)
SAVER = build.repair_saver(SAVER_OLD)


class FakeItem:
    def getPath(self): return 'plugin://test/movie/11'
    def getLabel(self): return 'Selected Movie'
    def getLabel2(self): return ''
    def getArt(self, key): return 'image://'+key if key in ('fanart','poster') else ''


class Context:
    def __init__(self):
        self.clock = 0.0
        self.waits = 0
        self.events = {}
        self.callback = False
        self.conditions = {'System.ScreenSaverActive':True}
        self.labels = {'System.ScreenWidth':'1080','System.ScreenHeight':'2400','Player.FilenameAndPath':'movie://one'}
        self.monitors = []
        self.calls = []
        self.window = None
        self.abort = False

    def info(self, label):
        if label in self.labels: return self.labels[label]
        if label.endswith('FileNameAndPath'): return 'plugin://test/movie/11'
        if label.endswith('.Title'): return 'Selected Movie'
        return ''

    def event(self, tick, *callbacks): self.events[tick] = callbacks

    def modules(self):
        ctx = self
        xbmc = types.ModuleType('xbmc')
        xbmc.LOGINFO=1; xbmc.LOGWARNING=2; xbmc.LOGERROR=3
        xbmc.getInfoLabel = self.info
        xbmc.getCondVisibility = lambda key: self.conditions.get(key,False)
        xbmc.executebuiltin = lambda call, wait=False: self.calls.append(('builtin',call,wait,self.window.closed))

        class Monitor:
            def __init__(self): ctx.monitors.append(self)
            def abortRequested(self): return ctx.abort
            def waitForAbort(self, seconds):
                ctx.waits += 1; ctx.clock += seconds
                if ctx.waits > 150: raise RuntimeError('Unbounded window loop')
                for callback in ctx.events.get(ctx.waits,()):
                    ctx.callback=True
                    try: callback(ctx.window)
                    finally: ctx.callback=False
                return ctx.abort
        xbmc.Monitor = Monitor
        gui = types.ModuleType('xbmcgui')

        class Window:
            def __new__(cls,*args,**kwargs):
                obj=object.__new__(cls); obj.closed=False; obj.close_count=0;obj.properties={};obj.reads=0
                ctx.window=obj
                return obj
            def show(self): self.onInit()
            def close(self):
                if ctx.callback: raise AssertionError('Close invoked from event callback')
                self.closed=True;self.close_count+=1
            def setProperty(self,k,v): self.properties[k]=v
            def getWidth(self): return 1080
            def getHeight(self): return 2400
            def getControl(self,id):
                if ctx.callback: raise AssertionError('GUI control read from event callback')
                if self.closed: raise AssertionError('GUI control read after close')
                self.reads+=1
                return types.SimpleNamespace(getSelectedItem=lambda:FakeItem())
        gui.WindowXMLDialog = Window
        class ListItem:
            def __init__(self,label): self.label=label
            def setPath(self,v): self.path=v
            def setArt(self,v): self.art=v
            def setProperty(self,k,v): pass
            def setInfo(self,k,v): self.info=v
        gui.ListItem=ListItem
        gui.Dialog=lambda:types.SimpleNamespace(info=lambda item:ctx.calls.append(('info',item.label,ctx.window.closed)))
        utils=types.ModuleType('resources.lib.utils')
        utils.get_saved_widget_path=lambda:'plugin://test/widget'
        utils.get_saved_widget_name=lambda:'Widget'
        utils.get_bool_setting=lambda key,default=False: default
        utils.log=lambda *args:None
        utils.sync_skinstrings_from_addon_settings=lambda:None
        resources=types.ModuleType('resources');lib=types.ModuleType('resources.lib');lib.utils=utils
        return {'xbmc':xbmc,'xbmcgui':gui,'resources':resources,'resources.lib':lib,'resources.lib.utils':utils}

    def load(self):
        mods=self.modules()
        with patch.dict(sys.modules,mods):
            controller=types.ModuleType('candidate_saver')
            exec(compile(SAVER['resources/lib/screensaver.py'],'candidate_saver','exec'),controller.__dict__)
        controller.time=types.SimpleNamespace(monotonic=lambda:self.clock)
        return controller


def action(id): return types.SimpleNamespace(getId=lambda:id)
def deactivate(w): w.exit_monitor.onScreensaverDeactivated()


class Lifecycle(unittest.TestCase):
    def create(self,ctx=None):
        self.ctx=ctx or Context();self.module=self.ctx.load()
        self.saver=self.module.Screensaver('x','y','Default','1080i')
        return self.saver

    def assert_clean(self,w):
        self.assertEqual(w.close_count,1)
        self.assertIsNone(w.exit_monitor)
        self.assertIsNone(self.ctx.monitors[0].deactivated_callback)
        self.assertFalse(w._ready)
        w.close_screensaver();self.assertEqual(w.close_count,1)

    def test_generic_wake_closes_without_second_popup(self):
        w=self.create();self.ctx.event(2,deactivate);w.run()
        self.assertFalse(w.should_open_info_after_close());self.assert_clean(w)
        self.ctx.monitors[0].onScreensaverDeactivated();self.assertEqual(w.close_count,1)

    def test_back_wins_even_if_deactivation_was_delivered_first(self):
        for callbacks in [(deactivate,lambda w:w.onAction(action(92))), (lambda w:w.onAction(action(92)),deactivate)]:
            with self.subTest(order=callbacks):
                w=self.create();self.ctx.event(2,*callbacks);w.run()
                self.assertFalse(w.should_open_info_after_close());self.assertFalse(w.should_restore_paused_video_osd_after_close());self.assert_clean(w)

    def test_plain_touch_does_not_open_info(self):
        w=self.create();self.ctx.event(1,lambda w:w.onAction(action(100)),deactivate);w.run()
        self.assertFalse(w.should_open_info_after_close());self.assert_clean(w)

    def test_explicit_details_open_only_after_close(self):
        w=self.create();self.ctx.event(2,lambda w:w.onClick(1299));w.run()
        self.assertTrue(w.should_open_info_after_close());w.open_last_item_info()
        self.assertEqual(self.ctx.calls,[('info','Selected Movie',True)]);self.assert_clean(w)

    def test_info_setting_false_is_respected(self):
        w=self.create();w.open_info_on_wake=False
        self.ctx.event(2,lambda w:w.onAction(action(11)));w.run()
        self.assertFalse(w.should_open_info_after_close());self.assert_clean(w)

    def paused(self,fullscreen=True):
        ctx=Context();ctx.conditions.update({'Player.HasVideo':True,'Player.Paused':True,'Window.IsActive(fullscreenvideo)':fullscreen})
        return self.create(ctx)

    def test_same_paused_foreground_session_restores_one_osd_async(self):
        w=self.paused();self.ctx.event(2,deactivate);w.run()
        self.assertTrue(callable(w.restore_paused_video_osd))
        self.assertTrue(w.should_restore_paused_video_osd_after_close());w.restore_paused_video_osd()
        self.assertEqual(self.ctx.calls,[('builtin','ActivateWindow(videoosd)',False,True)])
        self.ctx.conditions['Window.IsActive(videoosd)']=True;w.restore_paused_video_osd()
        self.assertEqual(len(self.ctx.calls),1);self.assert_clean(w)

    def test_paused_background_video_does_not_leave_home(self):
        w=self.paused(False);self.ctx.event(2,deactivate);w.run()
        self.assertFalse(w.should_restore_paused_video_osd_after_close())
        self.assertFalse(w.restore_paused_video_osd());self.assertEqual(self.ctx.calls,[])

    def test_stopped_resumed_or_replaced_video_is_not_resurrected(self):
        for field,value in [('Player.Paused',False),('Player.HasVideo',False),('Player.FilenameAndPath','movie://other')]:
            with self.subTest(field=field):
                w=self.paused();self.ctx.event(2,deactivate);w.run()
                if field=='Player.FilenameAndPath': self.ctx.labels[field]=value
                else:self.ctx.conditions[field]=value
                self.assertFalse(w.restore_paused_video_osd());self.assertEqual(self.ctx.calls,[])

    def test_abort_cleans_up_and_suppresses_wake(self):
        w=self.paused();self.ctx.event(2,lambda w:setattr(self.ctx,'abort',True));w.run()
        self.assertFalse(w.should_restore_paused_video_osd_after_close());self.assert_clean(w)

    def test_show_exception_still_closes_and_detaches_monitor(self):
        w=self.create();w.show=lambda:(_ for _ in ()).throw(RuntimeError('show failed'))
        with self.assertRaises(RuntimeError):w.run()
        self.assert_clean(w)

    def test_unchanged_widget_is_not_fully_polled_every_second(self):
        w=self.create();self.ctx.event(70,deactivate);w.run()
        self.assertEqual(w.reads,1);self.assert_clean(w)

    def test_stable_resize_reopens_only_saver_while_active(self):
        w=self.create();self.ctx.event(2,lambda w:self.ctx.labels.update({'System.ScreenWidth':'2256','System.ScreenHeight':'2504'}));w.run()
        self.assertEqual(w._close_reason,'viewport-resize');self.assertGreaterEqual(self.ctx.clock,0.6)
        self.assertTrue(w.should_reopen_for_resize());self.ctx.conditions['System.ScreenSaverActive']=False
        self.assertFalse(w.should_reopen_for_resize());self.assert_clean(w)

    def test_transient_resize_does_not_recreate(self):
        w=self.create()
        self.ctx.event(2,lambda w:self.ctx.labels.update({'System.ScreenWidth':'1200'}))
        self.ctx.event(4,lambda w:self.ctx.labels.update({'System.ScreenWidth':'1080'}))
        self.ctx.event(12,deactivate);w.run()
        self.assertEqual(w._close_reason,'deactivated');self.assertFalse(w.should_reopen_for_resize())

    def test_entrypoint_calls_restore_and_handles_one_resize_without_module_clear(self):
        calls=[];instances=[]
        class Saver:
            def __init__(self,*args):self.index=len(instances);instances.append(self)
            def run(self):calls.append(('run',self.index))
            def should_reopen_for_resize(self):return self.index==0
            def should_restore_paused_video_osd_after_close(self):return True
            def restore_paused_video_osd(self):calls.append(('restore',self.index))
            def should_open_info_after_close(self):return False
            def close_screensaver(self):calls.append(('close',self.index))
        ctx=Context();mods=ctx.modules();mod=types.ModuleType('resources.lib.screensaver');mod.Screensaver=Saver;mods[mod.__name__]=mod
        addon=types.ModuleType('xbmcaddon');addon.Addon=lambda:types.SimpleNamespace(getAddonInfo=lambda k:'/addon');mods['xbmcaddon']=addon
        with patch.dict(sys.modules,mods):
            entry=types.ModuleType('candidate_entry')
            exec(compile(SAVER['default.py'],'candidate_entry','exec'),entry.__dict__);entry.main()
        self.assertEqual(calls,[('run',0),('close',0),('run',1),('restore',1),('close',1)])
        self.assertNotIn('sys.modules.clear()',SAVER['default.py'].decode())
        self.assertNotIn('threading.Thread',SAVER['resources/lib/screensaver.py'].decode())


class PreservationAndGeometry(unittest.TestCase):
    def test_exact_baselines(self):
        self.assertEqual(build.sha(SKIN_PATH.read_bytes()),build.SKIN_SHA)
        self.assertEqual(build.sha(SAVER_PATH.read_bytes()),build.SAVER_SHA)

    def test_existing_skin_files_and_profile_extension_preserved(self):
        self.assertEqual({n for n in SKIN_OLD if SKIN_OLD[n]!=SKIN[n]},build.SKIN_METADATA)
        self.assertEqual(set(SKIN)-set(SKIN_OLD),ADDITIONS)
        self.assertEqual(SKIN['unified/AddonBrowser.xml'],SKIN_OLD['unified/AddonBrowser.xml'])
        old=ET.fromstring(SKIN_OLD['addon.xml']);new=ET.fromstring(SKIN['addon.xml'])
        self.assertEqual(ET.tostring(old.find('requires')),ET.tostring(new.find('requires')))
        self.assertEqual(ET.tostring(old.find('extension[@point="xbmc.gui.skin"]')),ET.tostring(new.find('extension[@point="xbmc.gui.skin"]')))

    def test_saver_settings_sources_fonts_and_art_are_byte_identical(self):
        self.assertEqual({n for n in SAVER_OLD if SAVER_OLD[n]!=SAVER[n]},build.SAVER_CHANGED)
        self.assertEqual(set(SAVER_OLD),set(SAVER))
        for name in ['resources/settings.xml','resources/lib/utils.py','script.py']:
            self.assertEqual(SAVER[name],SAVER_OLD[name])

    def test_every_canonical_font_exists_without_font_injection(self):
        fonts={n.text for n in ET.fromstring(SKIN['unified/Font.xml']).findall('.//font/name')}
        xml=ET.fromstring(SKIN['unified/'+build.XML_NAME])
        for name in xml.findall('.//font'):self.assertIn(name.text,fonts)
        self.assertNotIn('install_mirage_fonts',SAVER['default.py'].decode())

    def test_identity_xml_and_python_parse(self):
        self.assertEqual(ET.fromstring(SAVER['addon.xml']).get('version'),'421')
        self.assertEqual(ET.fromstring(SKIN['addon.xml']).get('version'),'1.0.5.198')
        for files in (SAVER,SKIN):
            for name,data in files.items():
                if name.endswith('.xml'):ET.fromstring(data)
                if name.endswith('.py'):ast.parse(data.decode())

    def test_captions_and_details_stay_inside_canvas_and_do_not_overlap(self):
        root=ET.fromstring(SKIN['unified/'+build.XML_NAME])
        def number(text,parent):return float(text[:-1])*parent/100 if text.endswith('%') else float(text)
        def bounds(control,pw,ph):
            width=number(control.findtext('width','0'),pw)
            left=number(control.findtext('left','0'),pw)
            height=number(control.findtext('height','0'),ph)
            bottom=number(control.findtext('bottom','0'),ph)
            top=number(control.findtext('top','0'),ph)
            if control.find('top') is None:top=ph-bottom-height
            if control.find('height') is None:height=ph-top-bottom
            return left,top,width,height
        matrix=[(1080,2520),(2520,1080),(2256,2504),(2504,2256),(1128,2504),(640,360),(320,720),(1200,600),(1920,1080)]
        group=root.find('controls/control[@type="group"]')
        for pixels_w,pixels_h in matrix:
            ratio=pixels_w/pixels_h;area=1080*2400
            logical_w=math.sqrt(area*ratio);logical_h=math.sqrt(area/ratio)
            gx,gy,gw,gh=bounds(group,logical_w,logical_h)
            with self.subTest(viewport=(pixels_w,pixels_h)):
                self.assertLessEqual(gy+gh,logical_h+0.001)
                children=[]
                for c in group.findall('control'):
                    if c.get('type')=='textbox' and c.find('bottom') is not None and logical_h<1100:continue
                    x,y,w,h=bounds(c,gw,gh);children.append((c,x,y,w,h))
                    self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
                    self.assertGreater(w,0);self.assertGreater(h,0)
                    self.assertLessEqual(x+w,gw+0.001);self.assertLessEqual(y+h,gh+0.001)
                button=next(v for v in children if v[0].get('id')=='1299')
                caption=next((v for v in children if v[0].get('type')=='textbox' and v[0].find('bottom') is not None),None)
                title=next(v for v in children if v[0].get('type')=='textbox' and v[0].find('bottom') is None)
                self.assertLess(title[2]+title[4],button[2])
                if caption:
                    self.assertGreaterEqual(caption[4],68)
                    self.assertLess(caption[2]+caption[4],button[2])
        full=root.find('controls/control[@type="image"]')
        self.assertEqual(full.findtext('width'),'100%');self.assertEqual(full.findtext('height'),'100%')
        self.assertEqual(full.find('texture').get('colordiffuse'),'FF000000')


if __name__=='__main__':unittest.main(verbosity=2)
