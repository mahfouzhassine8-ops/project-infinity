from pathlib import Path
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import infinity_compat_palette as palette
import infinity_player_resource_audit as player_audit


class PaletteTests(unittest.TestCase):
    def test_fresh_empty_palette_gets_all_defined_colors(self):
        root = ET.fromstring(palette.materialize_variables(b'<includes/>'))
        definitions = {v.get('name'): v for v in root.findall('variable')}
        self.assertEqual(set(definitions), {'InfinityColor_' + key for key in palette.LIGHT_VALUES})
        for key, color in palette.LIGHT_VALUES.items():
            values = definitions['InfinityColor_' + key].findall('value')
            self.assertEqual(values[0].text, color)
            self.assertEqual(values[1].text, palette.DARK_VALUES[key])
            self.assertEqual(values[2].text, palette.DARK_VALUES[key])

    def test_existing_menu_variable_is_preserved(self):
        src = b'<includes><variable name="InfinityColor_menu_text"><value>KEEP</value></variable></includes>'
        root = ET.fromstring(palette.materialize_variables(src))
        self.assertEqual(root.find("variable[@name='InfinityColor_menu_text']/value").text, 'KEEP')

    def test_idempotent(self):
        once = palette.materialize_variables(b'<includes/>')
        self.assertEqual(once, palette.materialize_variables(once))

    def test_duplicate_variable_fails_closed(self):
        with self.assertRaises(ValueError):
            palette.materialize_variables(b'<includes><variable name="InfinityColor_blue"/><variable name="InfinityColor_blue"/></includes>')

    def test_malformed_xml_is_rejected(self):
        with self.assertRaises(ET.ParseError):
            palette.materialize_variables(b'<includes>')

    def test_apk_byte_preservation_except_palette_and_signatures(self):
        with tempfile.TemporaryDirectory() as temp:
            src, dst = Path(temp) / 'input.apk', Path(temp) / 'output.apk'
            with zipfile.ZipFile(src, 'w') as z:
                z.writestr(palette.VARIABLES, b'<includes/>')
                for name in ('classes.dex', 'lib/arm64-v8a/libkodi.so', 'AndroidManifest.xml', 'Home.xml'):
                    z.writestr(name, name.encode())
                z.writestr('META-INF/INFINITY.SF', 'stale-signature')
            receipt = palette.build(src, dst)
            with zipfile.ZipFile(dst) as z:
                self.assertEqual(z.read('classes.dex'), b'classes.dex')
                self.assertNotIn('META-INF/INFINITY.SF', z.namelist())
            self.assertFalse(receipt['signed'])
            self.assertFalse(receipt['runtime_player_protection'])

    def test_actual_1_0_6_missing_player_colors_are_fixed(self):
        # Required in candidate CI; do not confuse fixture tests with real APK coverage.
        apk = os.environ.get('INFINITY_BASELINE_APK')
        if not apk:
            self.skipTest('Set INFINITY_BASELINE_APK for real signed 1.0.6 coverage')
        before = player_audit.audit(Path(apk))
        self.assertIn('variable:InfinityColor_blue', before['unresolved_definitions'])
        self.assertIn('variable:InfinityColor_white', before['unresolved_definitions'])
        with tempfile.TemporaryDirectory() as temp:
            dst = Path(temp) / 'palette-test-unsigned.apk'
            palette.build(Path(apk), dst)
            after = player_audit.audit(dst)
        self.assertFalse(after['unresolved_definitions'])
        self.assertEqual(before['engine_and_dex_sha256'], after['engine_and_dex_sha256'])
        self.assertFalse(after['home_window_redirected'])
        self.assertFalse(after['runtime_protection_implemented'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
