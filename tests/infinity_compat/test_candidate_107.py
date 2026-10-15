from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'addons/service.infinity.compat'))
import compat_runtime
import infinity_1_0_7_compat_source as source_patch
import infinity_1_0_7_compat_package as package


class Candidate107Tests(unittest.TestCase):
    def test_protected_xml_is_self_contained_and_parseable(self):
        root = ROOT / 'addons/service.infinity.compat/resources/xml'
        for name in compat_runtime.PROTECTED:
            data = (root / name).read_bytes()
            tree = ET.fromstring(data)
            self.assertEqual(tree.tag, 'window')
            text = data.decode()
            self.assertNotIn('<include>', text)
            self.assertNotIn('$VAR[', text)
            self.assertNotIn('<include', text)
        osd = (root / 'VideoOSD.xml').read_text()
        self.assertIn('id="7999"', osd)
        self.assertIn('PlayerControl(Stop)', osd)
        self.assertIn('osdsubtitlesettings', osd)
        self.assertIn('osdaudiosettings', osd)

    def test_guard_does_not_touch_home_or_shortcuts(self):
        with tempfile.TemporaryDirectory() as td:
            skin = Path(td) / 'skin'; addon = ROOT / 'addons/service.infinity.compat'; backup = Path(td) / 'backup'
            (skin / '16x9').mkdir(parents=True); (skin / 'colors').mkdir(); (skin / 'shortcuts').mkdir()
            home = skin / '16x9/Home.xml'; home.write_text('<window><controls/></window>')
            shortcuts = skin / 'shortcuts/mainmenu.DATA.xml'; shortcuts.write_text('<shortcut/>')
            home_before = home.read_bytes(); shortcuts_before = shortcuts.read_bytes()
            for n in ('VideoOSD.xml','DialogSeekBar.xml'):
                (skin / '16x9' / n).write_text('<window><controls/></window>')
            compat_runtime.ensure_player_files(skin, addon, backup)
            compat_runtime.ensure_theme_files(skin, addon)
            self.assertEqual(home.read_bytes(), home_before)
            self.assertEqual(shortcuts.read_bytes(), shortcuts_before)
            self.assertTrue((backup / 'VideoOSD.xml').exists())
            self.assertTrue((skin / '16x9/Custom_1199_InfinityVideoLock.xml').exists())

    def test_theme_policy(self):
        self.assertEqual(compat_runtime.resolve_theme('light','dark'),'InfinityLight.xml')
        self.assertEqual(compat_runtime.resolve_theme('oled','light'),'InfinityDark.xml')
        self.assertEqual(compat_runtime.resolve_theme('system','light'),'InfinityLight.xml')
        self.assertEqual(compat_runtime.resolve_theme('', 'dark'),'InfinityDark.xml')

    def test_source_patch_ownership_model(self):
        self.assertIn('Py_DECREF(p);', source_patch.NEW_DELETER)
        self.assertNotIn('Py_REFCNT', source_patch.NEW_DELETER)
        self.assertIn('PyObjectPtr(PyLong_FromLong(GetId()))', source_patch.NEW_INIT)
        self.assertIn('PyDict_SetItemString(moduleDictionary, key, value.get()) != 0', source_patch.NEW_INIT)

    def test_package_injection_preserves_existing_members(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); src=td/'in.apk'; out=td/'out.apk'; receipt=td/'receipt.json'
            with zipfile.ZipFile(src,'w') as z:
                z.writestr('assets/example.txt', b'unchanged')
                z.writestr('META-INF/OLD.SF', b'old signature')
            package.build(src,out,receipt)
            with zipfile.ZipFile(out) as z:
                self.assertEqual(z.read('assets/example.txt'), b'unchanged')
                self.assertNotIn('META-INF/OLD.SF', z.namelist())
                self.assertIn('assets/addons/service.infinity.compat/addon.xml', z.namelist())
                self.assertNotIn('assets/addons/service.infinity.compat/16x9/Home.xml', z.namelist())


if __name__ == '__main__':
    unittest.main(verbosity=2)
