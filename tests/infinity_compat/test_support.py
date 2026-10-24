from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'addons/script.infinity.support'))
import support


class SupportExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.skin = self.root / 'skin.xenon2'
        (self.skin / '16x9').mkdir(parents=True)
        (self.skin / 'addon.xml').write_text('<addon id="skin.xenon2" version="fixture"/>')
        (self.skin / '16x9/Home.xml').write_text('<window><controls/></window>')
        self.output = self.root / 'report.zip'

    def tearDown(self):
        self.temp.cleanup()

    def test_real_nonempty_zip_and_correct_skin_id(self):
        result = support.make_report(self.output, self.skin, 'skin.xenon2')
        self.assertEqual(result['active_skin_id'], 'skin.xenon2')
        with zipfile.ZipFile(self.output) as z:
            self.assertIsNone(z.testzip())
            self.assertIn('active-skin/16x9/Home.xml', z.namelist())
            self.assertIn('report.json', z.namelist())
        self.assertGreater(self.output.stat().st_size, 0)

    def test_excludes_settings_database_media_and_fonts(self):
        (self.skin / 'userdata').mkdir()
        (self.skin / 'userdata/guisettings.xml').write_text('PRIVATE_PASSWORD')
        for name in ('Noto.ttf', 'Textures.xbt', 'cache.db', 'background.png', 'account.json'):
            (self.skin / name).write_text('EXCLUDED')
        support.make_report(self.output, self.skin, 'skin.xenon2')
        with zipfile.ZipFile(self.output) as z:
            raw = b''.join(z.read(n) for n in z.namelist())
            self.assertNotIn(b'PRIVATE_PASSWORD', raw)
            self.assertNotIn(b'EXCLUDED', raw)

    def test_source_bytes_remain_unchanged(self):
        before = {p: p.read_bytes() for p in self.skin.rglob('*') if p.is_file()}
        support.make_report(self.output, self.skin, 'skin.xenon2')
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_symlink_file_and_folder_are_not_followed(self):
        secret = self.root / 'secret.xml'
        secret.write_text('PRIVATE')
        (self.skin / 'outside.xml').symlink_to(secret)
        (self.skin / 'outside-dir').symlink_to(self.root, target_is_directory=True)
        support.make_report(self.output, self.skin, 'skin.xenon2')
        with zipfile.ZipFile(self.output) as z:
            self.assertNotIn('active-skin/outside.xml', z.namelist())
            self.assertFalse(any('outside-dir' in n for n in z.namelist()))

    def test_native_traces_require_opt_in(self):
        native = self.root / 'native'
        native.mkdir()
        (native / 'android-exit-info.json').write_text('{"schema":1}')
        (native / 'exit-123-45-5.trace').write_bytes(b'PRIVATE_NATIVE_TRACE')
        support.make_report(self.output, self.skin, 'skin.xenon2', native_roots=[native])
        with zipfile.ZipFile(self.output) as z:
            self.assertIn('native/android-exit-info.json', z.namelist())
            self.assertFalse(any(n.endswith('.trace') for n in z.namelist()))
        second = self.root / 'traces.zip'
        support.make_report(second, self.skin, 'skin.xenon2', native_roots=[native], include_native_traces=True)
        with zipfile.ZipFile(second) as z:
            self.assertIn('native/exit-123-45-5.trace', z.namelist())

    def test_size_limit_is_reported_not_silently_hidden(self):
        (self.skin / '16x9/TooLarge.xml').write_bytes(b'x' * 200)
        with patch.object(support, 'MAX_FILE', 100):
            result = support.make_report(self.output, self.skin, 'skin.xenon2')
        self.assertFalse(result['complete_within_limits'])
        self.assertEqual(result['omitted'][0]['file'], 'active-skin/16x9/TooLarge.xml')

    def test_refuses_overwrite(self):
        self.output.write_text('KEEP')
        with self.assertRaises(ValueError):
            support.make_report(self.output, self.skin, 'skin.xenon2')
        self.assertEqual(self.output.read_text(), 'KEEP')

    def test_report_cannot_be_written_into_skin(self):
        with self.assertRaises(ValueError):
            support.make_report(self.skin / 'report.zip', self.skin, 'skin.xenon2')

    def test_health_center_source_excludes_user_addon_data(self):
        health = self.root / 'health'
        (health / 'resources').mkdir(parents=True)
        (health / 'default.py').write_text('print("fixture")')
        (health / 'resources/settings.xml').write_text('<settings/>')
        (health / 'addon_data').mkdir()
        (health / 'addon_data/settings.xml').write_text('PRIVATE')
        support.make_report(self.output, self.skin, 'skin.xenon2', health_root=health)
        with zipfile.ZipFile(self.output) as z:
            self.assertIn('health-center-source/default.py', z.namelist())
            self.assertNotIn('health-center-source/addon_data/settings.xml', z.namelist())

    def test_no_native_files_is_explicit_not_claimed_success(self):
        result = support.make_report(self.output, self.skin, 'skin.xenon2')
        self.assertFalse(result['native_evidence_present'])
        self.assertFalse(result['crash_cause_confirmed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
