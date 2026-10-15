from pathlib import Path
import sys
import tempfile
import types
import unittest
import zipfile
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'collector/script.infinity.railcapture'))
import capture_core as core

class CaptureTests(unittest.TestCase):
    def fixture(self,dialogs=(9999,13001)):
        state={'now':0.0,'queries':[]}
        class Window:
            def getProperty(self,key):return 'script-super-favourites-contextmenu.xml' if key=='xmlfile' else ''
            def getFocusId(self):return 9200
        def dialog():return dialogs[min(int(state['now']*10),len(dialogs)-1)]
        gui=types.SimpleNamespace(getCurrentWindowId=lambda:10000,getCurrentWindowDialogId=dialog,Window=lambda _:Window())
        def info(q):state['queries'].append(q);return 'movies' if 'section' in q else ''
        xbmc=types.SimpleNamespace(getInfoLabel=info,getCondVisibility=lambda q:'9200' in q)
        def wait(seconds):state['now']+=seconds;return False
        monitor=types.SimpleNamespace(abortRequested=lambda:False,waitForAbort=wait)
        return state,xbmc,gui,monitor
    def test_real_kodi_no_dialog_sentinel_samples_home(self):
        state,xbmc,gui,_=self.fixture()
        shot=core.snapshot(xbmc,gui)
        self.assertEqual(shot['dialog'],9999);self.assertEqual(shot['focus'],9200)
    def test_popup_snapshot_captures_identity_not_home_labels(self):
        state,xbmc,gui,_=self.fixture((13001,))
        shot=core.snapshot(xbmc,gui)
        self.assertEqual(shot['xml_property'],'script-super-favourites-contextmenu.xml')
        self.assertFalse(any('Container(' in q for q in state['queries']))
    def test_one_transition_stops_after_two_seconds(self):
        state,xbmc,gui,monitor=self.fixture()
        r=core.observe(xbmc,gui,monitor,clock=lambda:state['now'])
        self.assertTrue(r['saw_window_transition']);self.assertLess(r['duration_seconds'],3)
        self.assertEqual([e['dialog'] for e in r['events']],[9999,13001])
    def test_no_popup_has_hard_thirty_second_bound(self):
        state,xbmc,gui,monitor=self.fixture((9999,))
        r=core.observe(xbmc,gui,monitor,seconds=900,clock=lambda:state['now'])
        self.assertFalse(r['saw_window_transition']);self.assertLess(r['duration_seconds'],30.2)
        self.assertEqual(len(r['events']),1)
    def test_abort_ends_without_wait(self):
        state,xbmc,gui,monitor=self.fixture();monitor.abortRequested=lambda:True
        r=core.observe(xbmc,gui,monitor,clock=lambda:state['now'])
        self.assertEqual(r['events'],[]);self.assertEqual(state['now'],0)
    def test_zip_preserves_source_bytes_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'capture.zip';report={};data=b'<keymap>original</keymap>'
            core.write_capture(p,report,{'keymaps/profile/gen.xml':data})
            with zipfile.ZipFile(p) as z:
                self.assertIsNone(z.testzip());self.assertEqual(z.read('keymaps/profile/gen.xml'),data)
                self.assertEqual(json.loads(z.read('capture.json'))['files']['keymaps/profile/gen.xml']['bytes'],len(data))
    def test_inventory_does_not_modify_sources_or_copy_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'menus.py').write_text('original');(root/'addon.xml').write_text('<addon/>')
            (root/'settings.xml').write_text('private settings')
            class Addon:
                def __init__(self,aid):self.aid=aid
                def getAddonInfo(self,k):return {'id':self.aid,'version':'0.2.3','path':tmp,'profile':tmp}[k]
            files,identities,missing=core.collect_files(types.SimpleNamespace(Addon=Addon),types.SimpleNamespace(translatePath=lambda p:p if not str(p).startswith('special:') else str(root/'missing')))
            self.assertEqual((root/'menus.py').read_text(),'original')
            self.assertFalse(any('settings.xml' in n for n in files))
            self.assertEqual(identities['script.infinity.rails']['version'],'0.2.3')
    def test_addon_has_no_service(self):
        import xml.etree.ElementTree as ET
        addon=ET.parse(Path(core.__file__).parent/'addon.xml')
        self.assertEqual([e.get('point') for e in addon.findall('extension')],['xbmc.python.script','xbmc.addon.metadata'])

if __name__=='__main__':unittest.main()
