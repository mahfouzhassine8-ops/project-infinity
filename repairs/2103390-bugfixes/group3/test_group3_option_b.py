"""Executable host-only Option B source, routing and no-Cobra preservation tests."""
import copy
from pathlib import Path
import json
import os
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import home_option_b as m
import stage_option_b as stage

ROOT=Path(__file__).resolve().parent
APK=Path(os.environ.get('INFINITY_2103390_APK','/mnt/data/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk'))

class Control:
    def __init__(self, index=2):self.index=index
    def getSelectedPosition(self):return self.index

class Home:
    def __init__(self,focus=8101,index=2): self.focus=focus;self.control=Control(index)
    def getFocusId(self):return self.focus
    def getControl(self,i):return self.control

class Kodi:
    def __init__(self):
        self.labels={
            'Container(9000).ListItem.Property(section)':'movies',
            'Container(8101).NumItems':'12',
            'Container(8101).ListItem.Title':'Movie One',
            'Container(8101).ListItem.FileNameAndPath':'plugin://plugin.video.umbrella/?action=play&media=movie1',
            'Container(8101).ListItem.Thumb':'poster.jpg',
            'Container(8101).ListItem.Year':'2024',
            'Container(8101).ListItem.Plot':'A verified provider plot',
            'Container(8101).ListItem.Rating':'7.8',
            'Container(8101).ListItem.Duration':'2:01:00',
            'Container(8101).ListItem.Trailer':'plugin://plugin.video.youtube/?id=trailer1',
            'Container(8101).ListItem.DBTYPE':'movie',
        }
        self.calls=[];self.rpc=[];self.favorites=[];self.folder=False
    def getInfoLabel(self,k):return self.labels.get(k,'')
    def getCondVisibility(self,k):return self.folder if k.endswith('IsFolder') else False
    def executebuiltin(self,v):self.calls.append(('builtin',v))
    def executeJSONRPC(self,s):
        q=json.loads(s);self.rpc.append(q)
        if q['method']=='Favourites.GetFavourites':return json.dumps({'jsonrpc':'2.0','id':1,'result':{'favourites':self.favorites}})
        if q['method']=='Favourites.AddFavourite':self.favorites.append(dict(q['params']));return json.dumps({'jsonrpc':'2.0','id':1,'result':'OK'})
        raise AssertionError(q)
    def Player(self):
        k=self
        class P:
            def play(self,url):k.calls.append(('play',url))
        return P()

class UI:
    def __init__(self,k,focus=8101,index=2):self.k=k;self.home=Home(focus,index);self.current_window=10000;self.current_dialog=9999
    def getCurrentWindowId(self):return self.current_window
    def getCurrentWindowDialogId(self):return self.current_dialog
    def Window(self,id):return self.home

@unittest.skipUnless(APK.is_file(),'Exact original signed 2103390 required')
class GroupThreeOptionB(unittest.TestCase):
    def test_01_exact_signed_base_scope_two_new_files_only(self):
        result=stage.audit(APK,ROOT)
        self.assertEqual(result['original_members'],7430)
        self.assertEqual(result['original_members_unchanged'],7430)
        self.assertEqual(result['modified_members'],0)
        self.assertEqual(result['proposed_added_members'],2)
        self.assertFalse(result['ready_for_signed_apk'])
        self.assertEqual(result['input_dispatch'],'UNRESOLVED_NOT_CONNECTED')
        self.assertTrue(all(row['path'].startswith(stage.ADDON_PREFIX) for row in result['proposed_additions']))

    def test_02_design_xml_single_compact_glass_modal_exact_controls(self):
        xml=ET.parse(ROOT/'InfinityHomeOptionB.xml').getroot()
        self.assertEqual(xml.get('type'),'dialog')
        self.assertEqual(len(xml.findall(".//control[@type='group'][@id='100']")),1)
        self.assertEqual(xml.find(".//control[@id='112']").get('type'),'image')
        self.assertEqual([xml.find(f".//control[@id='{i}']/label").text for i in (101,102,103,104)],list(m.APPROVED_ORDER))
        self.assertEqual(xml.find(".//control[@id='9']").get('type'),'button')
        self.assertEqual(xml.find(".//control[@id='2']").get('type'),'button')
        self.assertEqual([i for i in m.ACTIONS], [101,102,103,104])
        self.assertEqual(len(xml.findall(".//control[@type='button']")),6)
        s=(ROOT/'InfinityHomeOptionB.xml').read_text()
        for token in ('InfinityLegacySurface','InfinityLegacyBorder','InfinityLegacyAccent','Window(Home).Property(Infinity.OptionalMotionAllowed)'):
            self.assertIn(token,s)
        self.assertNotIn('ActivateWindow(Videos,',s)

    def test_03_layout_safely_centers_and_reflows_without_extra_actions(self):
        for w,h in [(1080,1920),(1920,1080),(720,1280),(480,960),(320,680)]:
            with self.subTest(view=(w,h)):
                g=m.geometry(w,h)
                self.assertGreaterEqual(g['x'],0);self.assertGreaterEqual(g['y'],0)
                self.assertLessEqual(g['x']+g['width'],w)
                self.assertLessEqual(g['y']+g['height'],h)
                self.assertEqual(len(g['buttons']),4)
                for x,y,bw,bh in g['buttons']:
                    self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
                    self.assertLessEqual(x+bw,g['width']);self.assertLessEqual(y+bh,g['height'])
                for x,y,bw,bh in g['details'].values():
                    self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
                    self.assertLessEqual(x+bw,g['width']);self.assertLessEqual(y+bh,g['height'])
                for i,a in enumerate(g['buttons']):
                    for b in g['buttons'][i+1:]:
                        overlap=max(0,min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0])) * max(0,min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]))
                        self.assertEqual(overlap,0)

    def test_04_movie_selected_correct_panel_and_no_guessing(self):
        k=Kodi();ui=UI(k)
        snap=m.capture(k,ui)
        self.assertIsNotNone(snap)
        self.assertEqual((snap.control,snap.index,snap.section),(8101,2,'movies'))
        self.assertEqual(snap.title,'Movie One')
        self.assertEqual(snap.path,k.labels['Container(8101).ListItem.FileNameAndPath'])
        self.assertNotIn('S2 E3',snap.properties()['YearAndEpisode'])
        self.assertEqual(snap.properties()['PlayAvailable'],'true')
        self.assertEqual(snap.properties()['TrailerAvailable'],'true')
        self.assertEqual(k.calls,[]);self.assertEqual(k.rpc,[])

    def test_05_tv_episode_only_uses_actual_typed_episode_tags(self):
        s=m.Selection(8102,3,'tvshows','plugin://plugin.video.umbrella/?id=ep','Episode',year='2024',media_type='episode',season='2',episode='3',episode_title='Episode Name')
        self.assertEqual(s.properties()['YearAndEpisode'],'2024   •   S2 E3  •  Episode Name')
        s2=m.Selection(8102,3,'tvshows',s.path,'Series',media_type='tvshow',season='2',episode='3')
        self.assertNotIn('S2 E3',s2.properties()['YearAndEpisode'])
        s3=m.Selection(8102,3,'tvshows',s.path,'Episode',media_type='episode',season='',episode='3')
        self.assertNotIn('S E',s3.properties()['YearAndEpisode'])

    def test_06_wrong_home_control_or_missing_selection_fails_closed(self):
        k=Kodi();ui=UI(k,focus=8830)
        self.assertIsNone(m.capture(k,ui))
        ui.home.focus=8101;ui.home.control.index=99
        self.assertIsNone(m.capture(k,ui))
        ui.home.control.index=2;ui.current_window=12005
        self.assertIsNone(m.capture(k,ui))
        ui.current_window=10000;ui.current_dialog=10100
        self.assertIsNone(m.capture(k,ui))
        ui.current_dialog=9999;k.labels['Container(9000).ListItem.Property(section)']='tvshows'
        self.assertIsNone(m.capture(k,ui))

    def test_07_play_does_only_original_kodi_select_after_identity_recheck(self):
        k=Kodi();ui=UI(k);s=m.capture(k,ui)
        self.assertTrue(m._perform(k,ui,s,'play'))
        self.assertEqual(k.calls,[('builtin','Action(Select)')]);self.assertEqual(k.rpc,[])
        k.calls.clear();k.labels['Container(8101).ListItem.FileNameAndPath']='plugin://plugin.video.umbrella/?id=different'
        self.assertFalse(m._perform(k,ui,s,'play'))
        self.assertFalse(k.calls)

    def test_08_more_info_original_kodi_info_not_new_details_route(self):
        k=Kodi();ui=UI(k);s=m.capture(k,ui)
        self.assertTrue(m._perform(k,ui,s,'more-info'))
        self.assertEqual(k.calls,[('builtin','Action(Info)')]);self.assertFalse(k.rpc)

    def test_09_original_kodi_favourites_only_when_explicitly_selected(self):
        k=Kodi();ui=UI(k);s=m.capture(k,ui)
        self.assertFalse(k.favorites)
        self.assertTrue(m._perform(k,ui,s,'favorite'))
        self.assertEqual([call['method'] for call in k.rpc],['Favourites.GetFavourites','Favourites.AddFavourite'])
        self.assertEqual(k.favorites[0]['path'],s.path)
        self.assertEqual(k.favorites[0]['type'],'media')
        self.assertTrue(m._perform(k,ui,s,'favorite'))
        self.assertEqual([c['method'] for c in k.rpc].count('Favourites.AddFavourite'),1)

    def test_10_folder_favorite_uses_original_kodi_videos_window(self):
        k=Kodi();k.folder=True;ui=UI(k);s=m.capture(k,ui)
        self.assertTrue(s.is_folder)
        self.assertTrue(m._perform(k,ui,s,'favorite'))
        self.assertEqual(k.favorites[0]['type'],'window')
        self.assertEqual(k.favorites[0]['window'],'Videos')
        self.assertEqual(k.favorites[0]['windowparameter'],s.path)

    def test_11_trailer_only_from_saved_supported_provider_link(self):
        k=Kodi();ui=UI(k);s=m.capture(k,ui)
        self.assertTrue(m._perform(k,ui,s,'trailer'))
        self.assertEqual(k.calls,[('play',s.trailer)])
        self.assertFalse(m._trailer_path('javascript:alert(1)'))
        self.assertFalse(m._trailer_path('plugin://untrusted;cmd/'))
        k.calls.clear();k.labels['Container(8101).ListItem.Trailer']=''
        self.assertFalse(m._perform(k,ui,s,'trailer'))
        self.assertFalse(k.calls)

    def test_12_source_integrity_fail_closed_against_modified_signed_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            corrupted=Path(tmp)/'different.apk'
            corrupted.write_bytes(APK.read_bytes()[:50])
            with self.assertRaises(ValueError):stage.audit(corrupted,ROOT)
            with self.assertRaises(ValueError):stage.stage(APK,ROOT,ROOT)
        self.assertEqual(stage.digest(APK.read_bytes()),stage.PARENT_SHA256)

    def test_13_scope_no_changes_to_home_cobra_native_shutdown(self):
        with ZipFile(APK) as z:
            names=z.namelist()
            for n in stage.NEW_FILES:
                self.assertNotIn(n,names)
                self.assertNotIn('cobra',n.lower())
                self.assertFalse(n.startswith(('lib/','assets/system/keymaps/')))
            for n in names:
                if n.endswith('/Home.xml') and n.startswith('assets/addons/skin.infinity.diggz/'):
                    b=z.read(n)
                    self.assertNotIn(b'<oncontextmenu>',b)
                    self.assertNotIn(b'<onlongclick>',b)

    def test_15_modal_cancel_is_inert_and_does_not_steal_home_focus(self):
        import sys, types
        k=Kodi();ui=UI(k)
        class GUIControl:
            def __init__(self,w=1080,h=1920):self.w=w;self.h=h
            def getWidth(self):return self.w
            def getHeight(self):return self.h
            def setPosition(self,x,y):self.x,self.y=x,y
            def setWidth(self,w):self.w=w
            def setHeight(self,h):self.h=h
        class Dialog:
            def __init__(self,*args): self.props={};self.controls={i:GUIControl() for i in (2,9,100,112,120,121,122,123,124,125,126,101,102,103,104)};self.closed=False
            def getControl(self,i):return self.controls[i]
            def setProperty(self,k,v):self.props[k]=v
            def setFocusId(self,i):self.focus=i
            def doModal(self):self.onInit();self.onAction(types.SimpleNamespace(getId=lambda:10))
            def close(self):self.closed=True
        ui.WindowXMLDialog=Dialog
        backup={n:sys.modules.get(n) for n in ('xbmc','xbmcgui','xbmcaddon','xbmcvfs')}
        sys.modules.update({'xbmc':k,'xbmcgui':ui,
                            'xbmcaddon':types.SimpleNamespace(Addon=lambda ident:types.SimpleNamespace(getAddonInfo=lambda name:'/fake/ui')),
                            'xbmcvfs':types.SimpleNamespace(translatePath=lambda path:path)})
        try:self.assertFalse(m.show_for_focused_top_poster())
        finally:
            for name,module in backup.items():
                if module is None:sys.modules.pop(name,None)
                else:sys.modules[name]=module
        self.assertEqual(k.calls,[]);self.assertEqual(k.rpc,[])
        self.assertEqual(ui.home.focus,8101)

    def test_16_modal_one_click_dispatches_once_without_fake_provider(self):
        import sys,types
        k=Kodi();ui=UI(k)
        class GUIControl:
            def __init__(self):self.w=1080;self.h=1920
            def getWidth(self):return self.w
            def getHeight(self):return self.h
            def setPosition(self,x,y):self.x,self.y=x,y
            def setWidth(self,w):self.w=w
            def setHeight(self,h):self.h=h
        class Dialog:
            def __init__(self,*args):self.props={};self.controls={i:GUIControl() for i in (2,9,100,112,120,121,122,123,124,125,126,101,102,103,104)}
            def getControl(self,i):return self.controls[i]
            def setProperty(self,k,v):self.props[k]=v
            def setFocusId(self,i):self.focus=i
            def doModal(self):self.onInit();self.onClick(101)
            def close(self):pass
        ui.WindowXMLDialog=Dialog
        backup={n:sys.modules.get(n) for n in ('xbmc','xbmcgui','xbmcaddon','xbmcvfs')}
        sys.modules.update({'xbmc':k,'xbmcgui':ui,
                            'xbmcaddon':types.SimpleNamespace(Addon=lambda ident:types.SimpleNamespace(getAddonInfo=lambda name:'/fake/ui')),
                            'xbmcvfs':types.SimpleNamespace(translatePath=lambda path:path)})
        try:self.assertTrue(m.show_for_focused_top_poster())
        finally:
            for name,module in backup.items():
                if module is None:sys.modules.pop(name,None)
                else:sys.modules[name]=module
        self.assertEqual(k.calls,[('builtin','Action(Select)')])
        self.assertEqual(ui.home.focus,8101)
        self.assertFalse(k.rpc)

    def test_14_staging_separate_keeps_exact_signed_parent_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'candidate_source_only'
            before=stage.digest(APK.read_bytes())
            output=stage.stage(APK,ROOT,target)
            self.assertEqual(output['proposed_added_members'],2)
            self.assertTrue((target/stage.ADDON_PREFIX/'home_option_b.py').is_file())
            self.assertEqual(before,stage.digest(APK.read_bytes()))
            self.assertEqual((target/stage.ADDON_PREFIX/'home_option_b.py').read_bytes(),(ROOT/'home_option_b.py').read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
