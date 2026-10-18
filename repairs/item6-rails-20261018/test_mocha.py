#!/usr/bin/env python3
"""#6 host proof: old Mocha XML path negative, real approved XML positive.

This mocks Kodi's script-specific WindowXMLDialog lookup; no emulator/Fold
acceptance is claimed. The exact helper/source hashes are checked by build.py.
"""
import argparse
import importlib.util
from pathlib import Path
import sys
import types
from unittest import mock
import unittest
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rails_item6_builder',HERE/'build.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class FakeWindow:
    def __init__(self,xml,path,skin,resolution):
        self.path=Path(path)/'resources'/'skins'/skin/resolution/xml
        if not self.path.is_file():
            raise RuntimeError('Kodi cannot find XML in the SCRIPT addon path')
        self.props={}
        self.ready=False
        self.result='cancel'
        self.closed=False
        self.focus=None
        self.clicked=None
    def setProperty(self,key,value):self.props[key]=value
    def getControl(self,id):
        if id not in (91001,91002,91003,91004,91005,91006):
            raise RuntimeError('Unknown approved Mocha control')
        return id
    def setFocusId(self,id):self.focus=id
    def doModal(self):
        self.onInit()
        if self.clicked is not None:self.onClick(self.clicked)
    def close(self):self.closed=True

class MochaSourceTests(unittest.TestCase):
    RAILS=None
    SKIN=None
    SOURCE=None

    def setUp(self):
        self.row=dict(label='Movie Add-on',custom=True,thumb='thumbnail.png')
        self.windows=[]
        self.fallbacks=[]
        self.fallback_index=None
        self.logs=[]

    def invoke(self,source,rail_dir,section='movies',settings=False,click=None):
        test=self
        class Capture(FakeWindow):
            def __init__(self,*args):
                super().__init__(*args)
                self.clicked=click
                test.windows.append(self)
        class KodiSelector:
            def select(self,title,labels):
                test.fallbacks.append((title,list(labels)))
                return test.fallback_index
        xbmc=types.SimpleNamespace(log=lambda message,level:test.logs.append(message),LOGWARNING=2)
        xa=types.SimpleNamespace(Addon=lambda addon:types.SimpleNamespace(
            getAddonInfo=lambda what:'1.0.5.228' if what=='version' else str(test.SKIN)))
        gui=types.SimpleNamespace(WindowXMLDialog=Capture,Dialog=lambda:KodiSelector())
        vfs=types.SimpleNamespace(translatePath=str)
        scope={}
        with mock.patch.dict(sys.modules,{'xbmc':xbmc,'xbmcaddon':xa,'xbmcgui':gui,'xbmcvfs':vfs}):
            exec(compile(source,'RailsMocha.py','exec'),scope)
            return scope['rail_options'](self.row,section,settings,rail_dir)

    def corrected_dir(self):
        out=self.RAILS.parent/'item6-only-sandbox'/'script.infinity.rails'
        xml=out/'resources/skins/Default/720p/InfinityRailsOptions.xml'
        xml.parent.mkdir(parents=True,exist_ok=True)
        xml.write_bytes((self.SKIN/'unified/InfinityRailsOptions.xml').read_bytes())
        return out

    def test_original_script_misses_xml_and_forces_generic_fallback(self):
        self.assertFalse((self.RAILS/'resources/skins/Default/720p/InfinityRailsOptions.xml').exists())
        self.fallback_index=0
        self.assertEqual(self.invoke(self.SOURCE,self.RAILS),'open')
        self.assertEqual(self.windows,[])
        self.assertEqual(len(self.fallbacks),1)
        self.assertIn('custom dialog unavailable',self.logs[0])

    def test_corrected_xml_opens_mocha_without_action_on_focus(self):
        out=self.corrected_dir()
        candidate=builder.correct_mocha(self.SOURCE)
        self.assertEqual(self.invoke(candidate,out,settings=True),'cancel')
        self.assertEqual(len(self.fallbacks),0)
        window=self.windows[-1]
        self.assertTrue(window.ready and window.closed)
        self.assertEqual(window.focus,91002)
        self.assertEqual(window.props['Infinity.Rails.Menu.Settings'],'true')
        self.assertEqual(window.props['Infinity.Rails.Menu.Remove'],'true')
        self.assertEqual(self.invoke(candidate,out,'tvshows',False,click=91001),'open')
        self.assertEqual(self.windows[-1].props['Infinity.Rails.Menu.Subtitle'],'TV Show Add-ons')
        self.assertEqual(self.invoke(candidate,out,'tvshows',True,click=91003),'remove')
        self.assertEqual(self.invoke(candidate,out,'tvshows',False,click=91004),'cancel')
        self.row['custom']=False
        self.assertEqual(self.invoke(candidate,out,'movies',False,click=91003),'cancel')

    def test_missing_or_wrong_layout_uses_original_safe_chooser(self):
        out=self.corrected_dir()
        layout=out/'resources/skins/Default/720p/InfinityRailsOptions.xml'
        candidate=builder.correct_mocha(self.SOURCE)
        layout.unlink()
        self.fallback_index=-1
        self.assertEqual(self.invoke(candidate,out),'cancel')
        self.assertEqual(self.windows,[])
        layout.write_text('<window/>')
        self.fallback_index=1
        self.assertEqual(self.invoke(candidate,out),'move')
        self.assertEqual(self.windows,[])
        self.assertEqual(len(self.fallbacks),2)

    def test_only_approved_mocha_block_changed_and_all_controls_present(self):
        fixed=builder.correct_mocha(self.SOURCE)
        self.assertEqual(fixed.replace(builder.NEW.encode(),builder.OLD.encode(),1),self.SOURCE)
        self.assertEqual(builder.digest(self.SOURCE),builder.MOCHA_SHA)
        layout=(self.SKIN/'unified/InfinityRailsOptions.xml').read_bytes()
        self.assertEqual(builder.digest(layout),builder.XML_SHA)
        root=ET.fromstring(layout)
        controls={c.get('id') for c in root.iter('control') if c.get('id')}
        self.assertTrue({'91001','91002','91003','91004','91005','91006'}<=controls)

def run_tests(rail_dir,skin_dir):
    MochaSourceTests.RAILS=Path(rail_dir)
    MochaSourceTests.SKIN=Path(skin_dir)
    MochaSourceTests.SOURCE=(MochaSourceTests.RAILS/'resources/lib/mocha.py').read_bytes()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(MochaSourceTests)
    report=unittest.TextTestRunner(verbosity=2).run(suite)
    if not report.wasSuccessful():raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--extracted-original-helper',type=Path,required=True)
    p.add_argument('--extracted-skin',type=Path,required=True)
    a=p.parse_args()
    run_tests(a.extracted_original_helper,a.extracted_skin)
