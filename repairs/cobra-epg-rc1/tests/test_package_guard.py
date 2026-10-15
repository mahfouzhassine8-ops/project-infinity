#!/usr/bin/env python3
"""Packaging-only regressions. These are not Android/device acceptance tests."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_guard as guard


class PackagingGuardTests(unittest.TestCase):
    def valid_env(self):
        return {'RUNTIME_COMMIT': guard.RUNTIME, 'NDK_VER': guard.NDK, 'GITHUB_REPOSITORY': guard.REPOSITORY}

    def fixture(self, root):
        root.mkdir(parents=True)
        (root / 'resources').mkdir()
        (root / 'addon.xml').write_text('<addon id="script.infinity.cobra.theme" version="1.3.9"/>')
        ui = {'schema': 1, 'version': '1.3.9', 'runtime': {'minimum_runtime': 3, 'minimum_build': 2103154},
              'presentation': {'adaptive_mode_layouts': True}, 'views': {'mobile': {'renderer': 'touch_dashboard'},
              'tv_guide': {'view_modes': {'grid': 'broadcast_duration_timeline_all_orientations',
              'compact': 'dense_channel_directory', 'cards': 'responsive_channel_identity_wall',
              'focus': 'watch_first_channel_or_schedule_queue'}}}}
        (root/'resources/cobra-ui.json').write_text(json.dumps(ui))
        (root/'resources/cobra-theme.json').write_text('{"schema":2}')
        return ui

    def test_accepts_exact_environment(self):
        guard.validate_environment(self.valid_env())

    def test_rejects_missing_pin(self):
        env = self.valid_env(); del env['RUNTIME_COMMIT']
        with self.assertRaisesRegex(RuntimeError, 'RUNTIME_COMMIT'):
            guard.validate_environment(env)

    def test_rejects_empty_pin(self):
        env = self.valid_env(); env['RUNTIME_COMMIT'] = ''
        with self.assertRaises(RuntimeError): guard.validate_environment(env)

    def test_rejects_mutable_pin(self):
        env = self.valid_env(); env['RUNTIME_COMMIT'] = 'main'
        with self.assertRaises(RuntimeError): guard.validate_environment(env)

    def test_rejects_other_commit(self):
        env = self.valid_env(); env['RUNTIME_COMMIT'] = 'a' * 40
        with self.assertRaises(RuntimeError): guard.validate_environment(env)

    def test_rejects_wrong_repository(self):
        env = self.valid_env(); env['GITHUB_REPOSITORY'] = 'other/repo'
        with self.assertRaises(RuntimeError): guard.validate_environment(env)

    def test_rejects_missing_ndk(self):
        env = self.valid_env(); del env['NDK_VER']
        with self.assertRaises(RuntimeError): guard.validate_environment(env)

    def test_file_hash_accepts_exact_and_rejects_changed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'input'; path.write_bytes(b'original')
            expected = hashlib.sha256(b'original').hexdigest()
            self.assertEqual(guard.check_file(path, expected), expected)
            path.write_bytes(b'changed')
            with self.assertRaises(RuntimeError): guard.check_file(path, expected)

    def test_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError): guard.check_file(Path(d)/'missing', '0'*64)

    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)/'real'; target.write_bytes(b'data')
            path = Path(d)/'link'; path.symlink_to(target)
            with self.assertRaises(RuntimeError): guard.check_file(path, guard.sha(target))

    def test_matching_ui_roundtrip_excludes_bytecode(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'addon'; self.fixture(root)
            (root/'__pycache__').mkdir(); (root/'__pycache__/x.pyc').write_bytes(b'cache')
            (root/'lib').mkdir(); (root/'lib/module.py').write_text('# required addon module\n')
            output = Path(d)/'delivery/Infinity-Cobra-UI-1.3.9.zip'
            report = guard.package_ui(root, output)
            self.assertEqual(report['version'], '1.3.9')
            self.assertFalse(report['device_visual_acceptance'])
            with zipfile.ZipFile(output) as z:
                self.assertEqual(len(z.namelist()), 4)
                self.assertIn(guard.ADDON+'/lib/module.py', z.namelist())
                self.assertFalse(any('__pycache__' in name for name in z.namelist()))
            self.assertTrue(output.with_suffix('.zip.sha256').exists())

    def test_stale_addon_rejected_before_zip_is_created(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'addon'; self.fixture(root)
            (root/'addon.xml').write_text('<addon id="script.infinity.cobra.theme" version="1.3.7"/>')
            output = Path(d)/'ui.zip'
            with self.assertRaises(RuntimeError): guard.package_ui(root, output)
            self.assertFalse(output.exists())

    def test_wrong_runtime_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'addon'; ui = self.fixture(root); ui['runtime']['minimum_runtime'] = 2
            (root/'resources/cobra-ui.json').write_text(json.dumps(ui))
            with self.assertRaises(RuntimeError): guard.package_ui(root, Path(d)/'ui.zip')

    def test_old_grid_contract_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'addon'; ui = self.fixture(root)
            ui['views']['tv_guide']['view_modes']['grid'] = 'orientation_adaptive_timeline'
            (root/'resources/cobra-ui.json').write_text(json.dumps(ui))
            with self.assertRaises(RuntimeError): guard.package_ui(root, Path(d)/'ui.zip')

    def test_native_payload_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'addon'; self.fixture(root); (root/'native.so').write_bytes(b'not UI')
            with self.assertRaises(RuntimeError): guard.package_ui(root, Path(d)/'ui.zip')

    def test_ui_output_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'addon'; self.fixture(root)
            output = Path(d)/'ui.zip'; output.write_bytes(b'existing')
            with self.assertRaises(FileExistsError): guard.package_ui(root, output)
            self.assertEqual(output.read_bytes(), b'existing')


if __name__ == '__main__':
    unittest.main(verbosity=2)
