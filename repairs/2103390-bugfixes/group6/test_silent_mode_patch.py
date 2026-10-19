"""Group #6 only: one System Hub Silent Mode + guarded passive toast tests."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import hashlib
import os
import tempfile
import unittest
import silent_mode_patch as s

APK=Path(os.environ.get("INFINITY_2103390_APK","/mnt/data/Infinity-2103390-Nine-Item-Integration-EXPERIMENTAL.apk"))
ORIGINAL_TOAST=Path(__file__).parent/"GUIDialogKaiToast.Omega.cpp"

@unittest.skipUnless(APK.is_file(),"Protected signed original 2103390 required")
class Group6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=ZipFile(APK)
        cls.diff=s.skin_inventory(APK)

    @classmethod
    def tearDownClass(cls):cls.original.close()

    def original_file(self,p):
        return ET.fromstring(self.original.read(p))

    def new_file(self,p):
        return ET.fromstring(self.diff[p])

    def test_01_exact_original_sha_and_13_system_hub_only(self):
        self.assertEqual(s.sha(APK.read_bytes()),s.BASE_APK_SHA)
        self.assertEqual(len(self.original.namelist()),7430)
        self.assertEqual(len(self.diff),13)
        self.assertEqual(set(self.diff),{s.P+x+'/'+s.HUB for x in s.HUB_LAYOUTS})
        self.assertEqual(s.inventory(APK)['unchanged_original_members'],7417)
        for p in self.diff:
            self.assertTrue(p.startswith(s.P))
            self.assertNotIn('cobra',p.casefold())
            self.assertFalse(p.startswith(('lib/','assets/addons/plugin.','assets/system/')))

    def test_02_exactly_one_new_named_switch_on_all_13(self):
        for layout in sorted(s.HUB_LAYOUTS):
            with self.subTest(layout=layout):
                path=s.P+layout+'/'+s.HUB
                old=self.original_file(path)
                new=self.new_file(path)
                self.assertIsNone(old.find(".//control[@id='1191108']"))
                ctrl=new.find(".//control[@id='1191108']")
                self.assertIsNotNone(ctrl)
                self.assertEqual(len(new.findall(".//control[@id='1191108']")),1)
                self.assertEqual(ctrl.get('type'),'radiobutton')
                self.assertEqual(ctrl.findtext('label'),'Silent Mode')
                self.assertEqual(ctrl.findtext('selected'),'Skin.HasSetting(Infinity.SilentMode)')
                self.assertEqual(ctrl.findtext('onclick'),'Skin.ToggleSetting(Infinity.SilentMode)')

    def test_03_all_original_buttons_actions_and_geometry_identical(self):
        for layout in sorted(s.HUB_LAYOUTS):
            path=s.P+layout+'/'+s.HUB
            old=self.original_file(path)
            new=self.new_file(path)
            self.assertEqual(s.original_actions(old),s.original_actions(new))
            old_buttons={c.get('id'):c for c in old.findall('.//control[@type="button"]')}
            new_buttons={c.get('id'):c for c in new.findall('.//control[@type="button"]')}
            self.assertEqual(set(old_buttons),set(new_buttons))
            for id,c in old_buttons.items():
                self.assertEqual(ET.tostring(c),ET.tostring(new_buttons[id]),
                                 f"{layout} original control {id} must remain byte-for-byte XML equivalent")

    def test_04_unified_fold_keeps_original_scroll_and_original_six(self):
        p=s.P+'unified/'+s.HUB
        old=self.original_file(p)
        new=self.new_file(p)
        container=old.find(".//control[@id='1191888']")
        current=new.find(".//control[@id='1191888']")
        self.assertIsNotNone(container)
        self.assertEqual(len(current.findall('./control')),len(container.findall('./control'))+1)
        self.assertIsNone(new.find(".//control[@id='1191105']"))
        self.assertEqual(ET.tostring(old.find(".//control[@id='1198888']"))
                         .split(b'<control type="grouplist"')[0],
                         ET.tostring(new.find(".//control[@id='1198888']"))
                         .split(b'<control type="grouplist"')[0])

    def test_05_other_12_static_variants_original_row_untouched(self):
        for layout in s.HUB_LAYOUTS-{'unified'}:
            path=s.P+layout+'/'+s.HUB
            old=self.original_file(path)
            new=self.new_file(path)
            for id in s.BUTTON_IDS:
                self.assertEqual(ET.tostring(old.find(".//control[@id='"+id+"']")),
                                 ET.tostring(new.find(".//control[@id='"+id+"']")),layout)
            old_footer=[x for x in old.find('controls') if x.get('type')=='label' and
                        (x.findtext('label') or '').startswith('Infinity system tools')]
            new_footer=[x for x in new.find('controls') if x.get('type')=='label' and
                        (x.findtext('label') or '').startswith('Infinity system tools')]
            self.assertEqual(len(old_footer),len(new_footer))
            self.assertEqual(old_footer[0].findtext('label'),new_footer[0].findtext('label'))
            first=old.find(".//control[@id='1191101']")
            second=old.find(".//control[@id='1191102']")
            last=old.find(".//control[@id='1191105']")
            change=s.dec(second.findtext('top'))-s.dec(first.findtext('top'))
            new_switch=new.find(".//control[@id='1191108']")
            self.assertAlmostEqual(float(s.dec(new_switch.findtext('top'))),
                                   float(s.dec(last.findtext('top'))+change),places=2)
            self.assertAlmostEqual(float(s.dec(new_footer[0].findtext('top'))),
                                   float(s.dec(old_footer[0].findtext('top'))+change),places=2)

    def test_06_reapplication_or_different_signed_parent_fails_closed(self):
        path=s.P+'unified/'+s.HUB
        with self.assertRaises(ValueError):s.patch_hub(self.diff[path],'unified')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'changed.apk';p.write_bytes(APK.read_bytes()[:80])
            with self.assertRaises(ValueError):s.skin_inventory(p)

    def test_07_toast_native_patch_targets_only_do_work(self):
        data=ORIGINAL_TOAST.read_bytes()
        updated=s.patch_toast_cpp(data)
        self.assertIn(b'GROUP6_SILENT_MODE_V1',updated)
        self.assertEqual(data.count(b'SetSound(toast.withSound);'),
                         updated.count(b'SetSound(toast.withSound);'))
        self.assertEqual(data.count(b'CServiceBroker::GetPeripherals().OnUserNotification();'),
                         updated.count(b'CServiceBroker::GetPeripherals().OnUserNotification();'))
        self.assertIn(b'GetString(CSettings::SETTING_LOOKANDFEEL_SKIN)',updated)
        self.assertIn(b'Skin.HasSetting(Infinity.SilentMode)',updated)
        with self.assertRaises(ValueError):s.patch_toast_cpp(updated)

    def test_08_no_interactive_dialog_source_or_audio_changes(self):
        data=s.patch_toast_cpp(ORIGINAL_TOAST.read_bytes())
        gate=data.index(b'GROUP6_SILENT_MODE_V1')
        button=data.index(b'SetSound(toast.withSound);')
        self.assertLess(gate,button)
        self.assertNotIn(b'WINDOW_DIALOG_YES_NO',data)
        self.assertNotIn(b'WINDOW_DIALOG_SELECT',data)
        self.assertNotIn(b'WINDOW_DIALOG_ADDON_INFO',data)
        self.assertNotIn(b'setVolume',data)
        self.assertNotIn(b'DisableAddon',data)
        self.assertNotIn(b'AddonInstaller',data)
        self.assertIn(b'while (!m_notifications.empty())',data)

    def test_09_signed_parent_immutable_with_separate_stage(self):
        before=s.sha(APK.read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            result=s.stage(APK,Path(tmp)/'stage')
            self.assertEqual(result['changed_skin_members'],13)
            self.assertFalse(result['native_toast_compiled'])
            self.assertTrue((Path(tmp)/'stage'/s.P/'unified'/s.HUB).exists())
        self.assertEqual(before,s.sha(APK.read_bytes()))

    def test_10_silent_toggle_is_default_off_and_natively_guarded(self):
        inventory=s.inventory(APK)
        self.assertEqual(inventory['silent_mode_default'],'OFF')
        self.assertEqual(inventory['new_system_hub_controls'],1)
        self.assertEqual(inventory['new_services'],inventory['new_databases'])
        self.assertEqual(inventory['new_databases'],0)
        for p in self.diff:
            data=self.diff[p]
            self.assertEqual(data.count(b'Skin.ToggleSetting(Infinity.SilentMode)'),1)

if __name__=='__main__':unittest.main(verbosity=2)
