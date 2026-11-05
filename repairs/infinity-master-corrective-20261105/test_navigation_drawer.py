"""Scoped source/API checks; no device, installed provider or shutdown test."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from zipfile import ZipFile
import xml.etree.ElementTree as E

HERE=Path(__file__).resolve().parent
UI=HERE.parent/'infinity-kodi-2103453-ui-navigation'
SKIN=UI/'overlay/assets/addons/skin.infinity.diggz'
spec=importlib.util.spec_from_file_location('candidate_navigation',UI/'navigation.py')
nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)


class API:
    def __init__(self): self.calls=[];self.errors=[];self.accept=True
    def executeJSONRPC(self, raw):
        request=json.loads(raw);self.calls.append(request)
        if request['method']!='GUI.ActivateWindow': raise AssertionError('Unexpected API')
        return json.dumps({'result':'OK'} if self.accept else {'error':{'code':-1}})
    def Dialog(self): return self
    def ok(self,*args): self.errors.append(args)
    def browseSingle(self,*args): raise AssertionError('ZIP-skinned picker must not be opened')


class NavigationAndDrawer(unittest.TestCase):
    def test_browse_uses_native_video_files_once(self):
        a=API();self.assertTrue(nav.run('browse',a,a))
        self.assertEqual(len(a.calls),1)
        self.assertEqual(a.calls[0]['params'],{'window':'videos','parameters':['files','return']})

    def test_failed_navigation_reports_failure_without_retry(self):
        a=API();a.accept=False
        self.assertFalse(nav.run('browse',a,a))
        self.assertEqual(len(a.calls),1);self.assertEqual(len(a.errors),1)

    def test_helper_matches_staged_source(self):
        self.assertEqual((UI/'navigation.py').read_bytes(),(SKIN/'resources/lib/infinity_library_navigation.py').read_bytes())

    def test_drawer_contains_only_reviewed_height_and_direct_route_changes(self):
        path='repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml'
        before=subprocess.check_output(['git','show','1b655a9e:'+path],cwd=HERE)
        candidate=(SKIN/'unified/Custom_1198_InfinityNav.xml').read_bytes()
        expected=before.replace(b'<height max="1050">88%</height>',b'<height max="1572">96%</height>',1)
        for action in ('movies','tv'):
            expected=expected.replace(('ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action='+action+',return)').encode(),('RunScript(special://skin/resources/lib/infinity_library_navigation.py,'+action+')').encode(),1)
        self.assertEqual(candidate,expected)

    def test_power_is_single_original_scroll_child_and_action(self):
        root=E.parse(SKIN/'unified/Custom_1198_InfinityNav.xml').getroot()
        matches=root.findall(".//control[@id='1198304']")
        self.assertEqual(len(matches),1)
        group=root.find(".//control[@id='1198899']")
        # Original rows are nested groups in the scrolling grouplist.
        self.assertIn(matches[0],list(group.iter('control')))
        self.assertIn('ActivateWindow(shutdownmenu)',[e.text for e in matches[0].findall('onclick')])

    def test_native_favourites_route_and_library_targets_remain(self):
        root=E.parse(SKIN/'unified/Custom_1198_InfinityNav.xml').getroot()
        actions=[e.text for e in root.iter('onclick')]
        self.assertIn('ActivateWindow(favouritesbrowser)',actions)
        self.assertTrue(any('videodb://movies/' in (v or '') for v in actions))
        self.assertTrue(any('videodb://tvshows/' in (v or '') for v in actions))

    def test_native_files_mapping_and_zip_label_are_confirmed_source_evidence(self):
        native=Path('/tmp/kodi452-pause-stop-integrated-native/xbmc/video/windows/GUIWindowVideoNav.cpp').read_text()
        self.assertIn('{"files", "sources://video/"}',native)
        with ZipFile('/tmp/kodi451-signed-baseline/Infinity-2103451-Combined-Original-Signer.apk') as apk:
            root=E.fromstring(apk.read('assets/addons/skin.infinity.diggz/unified/FileBrowser.xml'))
            self.assertIn('SELECT ZIP',[n.text for n in root.iter('label')])


if __name__=='__main__': unittest.main(verbosity=2)
