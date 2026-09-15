from pathlib import Path
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'addons/service.infinity.compat'))

# Minimal Kodi stubs so the clean-core contract module can be imported in host CI.
sys.modules.setdefault('xbmc', types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz'))
sys.modules.setdefault('xbmcaddon', types.SimpleNamespace(Addon=lambda *a, **k: None))
sys.modules.setdefault('xbmcgui', types.SimpleNamespace(Window=lambda *a, **k: None))

import compat_runtime
import infinity_1_0_7_compat_source as source_patch
import infinity_1_0_7_compat_package as package


class Candidate107Tests(unittest.TestCase):
    def test_clean_core_dual_skin_contract(self):
        self.assertEqual(compat_runtime.API_VERSION, '0.8.1')
        self.assertEqual(compat_runtime.PRIMARY_SKIN_ID, 'skin.infinity.diggz')
        self.assertEqual(
            compat_runtime.SUPPORTED_SKINS,
            ('skin.infinity.diggz', 'skin.infinity'),
        )

    def test_single_runtime_service(self):
        manifest = ET.parse(ROOT / 'addons/service.infinity.compat/addon.xml').getroot()
        services = [
            node for node in manifest.findall('extension')
            if node.attrib.get('point') == 'xbmc.service'
        ]
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0].attrib.get('library'), 'runtime_service.py')

    def test_guard_has_no_legacy_file_reassertion(self):
        root = ROOT / 'addons/service.infinity.compat'
        text = '\n'.join(
            path.read_text(encoding='utf-8', errors='ignore')
            for path in root.rglob('*.py')
        )
        self.assertNotIn('ensure_player_files(', text)
        self.assertNotIn('ensure_theme_files(', text)
        self.assertNotIn('skin.xenon2', text)
        self.assertFalse((root / 'service.py').exists())

    def test_source_patch_ownership_model(self):
        self.assertIn('Py_DECREF(p);', source_patch.NEW_DELETER)
        self.assertNotIn('Py_REFCNT', source_patch.NEW_DELETER)
        self.assertIn('PyObjectPtr(PyLong_FromLong(GetId()))', source_patch.NEW_INIT)
        self.assertIn('PyDict_SetItemString(moduleDictionary, key, value.get()) != 0', source_patch.NEW_INIT)

    def test_package_injection_preserves_existing_members(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / 'in.apk'
            out = td / 'out.apk'
            receipt = td / 'receipt.json'
            with zipfile.ZipFile(src, 'w') as archive:
                archive.writestr('assets/example.txt', b'unchanged')
                archive.writestr('META-INF/OLD.SF', b'old signature')
            package.build(src, out, receipt)
            with zipfile.ZipFile(out) as archive:
                self.assertEqual(archive.read('assets/example.txt'), b'unchanged')
                self.assertNotIn('META-INF/OLD.SF', archive.namelist())
                self.assertIn('assets/addons/service.infinity.compat/addon.xml', archive.namelist())
                self.assertNotIn('assets/addons/service.infinity.compat/16x9/Home.xml', archive.namelist())


if __name__ == '__main__':
    unittest.main(verbosity=2)
