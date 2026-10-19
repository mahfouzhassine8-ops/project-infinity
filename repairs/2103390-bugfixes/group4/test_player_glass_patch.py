"""Group #4 signed original source and non-regression tests."""
from pathlib import Path
import hashlib
import os
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import player_glass_patch as g

APK=Path(os.environ.get("INFINITY_2103390_APK",
         "/mnt/data/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk"))


@unittest.skipUnless(APK.is_file(),"Original signed 2103390 required")
class Group4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modified=g.proposed(APK)
        cls.zip=ZipFile(APK)
        cls.layouts=sorted(g.LAYOUTS)

    @classmethod
    def tearDownClass(cls):
        cls.zip.close()

    def before(self,layout,name):
        return ET.fromstring(self.zip.read(g.P+layout+'/'+name))

    def after(self,layout,name):
        return ET.fromstring(self.modified[g.P+layout+'/'+name])

    def test_01_exact_signed_apk_and_41_xml_member_allowlist(self):
        self.assertEqual(g.sha(APK.read_bytes()),g.BASE_SHA)
        self.assertEqual(len(self.zip.namelist()),7430)
        self.assertEqual(len(self.modified),41)
        expect={g.P+layout+'/'+name for layout in g.LAYOUTS for name in g.FILES
                if name!="Custom_1195_InfinityAudioSubtitles.xml" or layout!="fallback"}
        self.assertEqual(set(self.modified),expect)
        self.assertTrue(all("cobra" not in s.lower() and "shutdown" not in s.lower()
                     and s.startswith(g.P) for s in self.modified))
        self.assertTrue(all(g.sha(self.zip.read(p))!=g.sha(body)
                     for p,body in self.modified.items()))

    def test_02_actual_original_display_button_reused_all_14(self):
        for layout in self.layouts:
            with self.subTest(layout=layout):
                orig=self.before(layout,'VideoOSD.xml')
                out=self.after(layout,'VideoOSD.xml')
                before=orig.find('.//control[@id="255"]')
                after=out.find('.//control[@id="255"]')
                self.assertEqual([x.text for x in before.findall('onclick')],['Action(AspectRatio)'])
                self.assertEqual([x.text for x in after.findall('onclick')],
                                 ['ActivateWindow(OSDVideoSettings)'])
                for field in ['left','right','top','width','height','onleft','onright','enable']:
                    self.assertEqual(before.findtext(field),after.findtext(field))

    def test_03_only_redundant_video_settings_row_removed(self):
        for layout in self.layouts:
            old=self.before(layout,'VideoOSD.xml');new=self.after(layout,'VideoOSD.xml')
            self.assertIsNone(new.find('.//control[@id="274"]'))
            prev=[(x.get('id'),x.findtext('label'),[s.text for s in x.findall('onclick')])
                 for x in old.findall('.//control[@type="button"]')
                 if x.get('id') not in ('255','274')]
            after=[(x.get('id'),x.findtext('label'),[s.text for s in x.findall('onclick')])
                   for x in new.findall('.//control[@type="button"]')
                   if x.get('id') not in ('255','274')]
            self.assertEqual(prev,after,layout)
            for cid in ['270','272','275','276','277','278','279','281','282']:
                self.assertIsNotNone(new.find(".//control[@id='"+cid+"']"))
            for cid in ['250','253','263','262','257']:
                self.assertEqual(ET.tostring(old.find(".//control[@id='"+cid+"']")),
                                 ET.tostring(new.find(".//control[@id='"+cid+"']")))

    def test_04_original_legacy_focus_without_dead_274(self):
        for layout in self.layouts:
            root=self.after(layout,'VideoOSD.xml')
            for node in root.findall('.//control'):
                for nav in ('onleft','onright','onup','ondown'):
                    self.assertNotEqual(node.findtext(nav),'274',layout)
            if layout!='unified':
                self.assertEqual(root.find('.//control[@id="272"]').findtext('ondown'),'275')
                self.assertEqual(root.find('.//control[@id="275"]').findtext('onup'),'272')

    def test_05_only_existing_glass_surface_changed_and_theme_variable(self):
        for layout in self.layouts:
            root=self.after(layout,'VideoOSD.xml')
            tex=[x for x in root.findall('.//control[@type="image"]/texture')
                 if x.get('colordiffuse')==g.GLASS]
            self.assertEqual(len(tex),1,layout)
            self.assertTrue(any('infinity_polish/surface.png'==v.text for v in tex))

    def test_06_audio_subtitle_native_action_identical_and_material(self):
        for layout in self.layouts:
            if layout=='fallback':continue
            old=self.before(layout,'Custom_1195_InfinityAudioSubtitles.xml')
            new=self.after(layout,'Custom_1195_InfinityAudioSubtitles.xml')
            def actions(r):return [(v.get('id'),v.findtext('label'),
                      tuple(w.text for w in v.findall('onclick')))
                      for v in r.findall('.//control[@type="button"]')]
            self.assertEqual(actions(old),actions(new))
            self.assertEqual(len(new.findall('.//control[@type="button"]')),4)
            self.assertIn(g.GLASS,ET.tostring(new,encoding='unicode'))
            self.assertIn('66000000',ET.tostring(new,encoding='unicode'))

    def test_07_native_dialog_non_osd_stays_original(self):
        for layout in self.layouts:
            old=self.before(layout,'DialogSettings.xml')
            new=self.after(layout,'DialogSettings.xml')
            old_actions=g.nav_snapshot(old)
            new_actions=g.nav_snapshot(new)
            self.assertEqual(old_actions,new_actions,layout)
            self.assertEqual(len(new.findall('.//control[@id="5"]')),
                             len(old.findall('.//control[@id="5"]')))
            conditions=[v.text for v in new.findall('.//visible')]
            self.assertTrue(any(g.NATIVE_OSD_ONLY==c for c in conditions))
            self.assertTrue(any('!['+g.NATIVE_OSD_ONLY+']'==c for c in conditions))
            self.assertEqual(len(new.findall('.//control[@type="grouplist"]')),
                             len(old.findall('.//control[@type="grouplist"]')))

    def test_08_no_generic_modal_cobra_video_core_or_third_party_delta(self):
        # All named targets are strict skin-only; no Kodi binaries, Cocoa/Cobra,
        # native dialog source, third-party provider, player DB or settings.
        forbidden=('lib/','assets/addons/plugin.','assets/addons/script.infinity.rails',
                   'assets/addons/script.infinity.commandcenter','assets/system/')
        self.assertFalse(any(any(x.startswith(v) for v in forbidden) for x in self.modified))

    def test_09_idempotence_refused(self):
        with self.assertRaises(ValueError):
            g.patch_osd(self.modified[g.P+'unified/VideoOSD.xml'],'unified')
        with self.assertRaises(ValueError):
            g.patch_audio(self.modified[g.P+'unified/Custom_1195_InfinityAudioSubtitles.xml'],'unified')

    def test_10_original_signed_file_immutable_after_separate_stage(self):
        before=g.sha(APK.read_bytes())
        with tempfile.TemporaryDirectory() as t:
            result=g.stage(APK,Path(t)/"stage")
            self.assertEqual(result['proposed_modified_members'],41)
            self.assertEqual(result['proposed_untouched_original_members'],7389)
            self.assertTrue((Path(t)/"stage"/g.P/'unified'/'VideoOSD.xml').is_file())
        self.assertEqual(before,g.sha(APK.read_bytes()))

if __name__=='__main__':unittest.main(verbosity=2)
