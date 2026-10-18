#!/usr/bin/env python3
"""Execute the actual packaged service/distro with controlled external inputs."""
import argparse
import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

import versioncheck_android as repair

APK = None


class VersionCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.candidate = repair.candidate_files(APK)

    def run_service(self, files, *, android, enabled=True):
        calls = []
        addon = types.SimpleNamespace(getSetting=lambda key: 'true' if enabled else 'false')
        common = types.ModuleType('version_check.common')
        common.ADDON, common.ADDON_NAME, common.ADDON_VERSION = addon, 'Version Check', repair.VERSION
        for name in ('dialog_yes_no', 'localise', 'log', 'wait_for_abort', 'message_restart',
                     'message_upgrade_success', 'upgrade_message', 'upgrade_message2'):
            setattr(common, name, lambda *a, _name=name: calls.append((_name, a)) or False)
        interface = types.ModuleType('version_check.json_interface')
        interface.get_version_file_list = lambda: calls.append(('version_list',)) or {}
        interface.get_installed_version = lambda: calls.append(('installed_version',)) or {}
        versions = types.ModuleType('version_check.versions')
        versions.compare_version = lambda *a: (False, {}, {}, {})
        xbmc = types.ModuleType('xbmc')
        xbmc.getCondVisibility = lambda key: android if key == 'System.Platform.Android' else not android
        xbmcgui = types.ModuleType('xbmcgui')
        fake = {'version_check.common': common, 'version_check.json_interface': interface,
                'version_check.versions': versions, 'xbmc': xbmc, 'xbmcgui': xbmcgui}

        def output(command, *args, **kwargs):
            # Exercise the bundled distro code, including its real /dev/null
            # open. Never execute an external command during this host test.
            calls.append(('child', tuple(command)))
            if tuple(command) == ('lsb_release', '-a'):
                return b'Distributor ID:\tUbuntu\nDescription:\tUbuntu\nRelease:\t22.04\nCodename:\tjammy\n'
            if tuple(command) == ('uname', '-rs'):
                return b'Linux 6.8\n'
            raise AssertionError('Unexpected distro command: ' + repr(command))

        saved = {key: value for key, value in sys.modules.items() if key == 'version_check' or key.startswith('version_check.')}
        for key in saved:
            del sys.modules[key]
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                for name, data in files.items():
                    if name.startswith('resources/lib/'):
                        p = root / name[len('resources/lib/'):]
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_bytes(data)
                sys.path.insert(0, td)
                try:
                    with patch.dict(sys.modules, fake), patch('sys.platform', 'linux'), \
                         patch('subprocess.check_output', output), patch('platform.uname', return_value=('Linux',)):
                        service = importlib.import_module('version_check.service')
                        # Cryptography is unrelated to the distribution import
                        # under test. Keep all original service run/setting logic.
                        with patch.object(service, '_check_cryptography'):
                            service.run()
                        return service.DISTRIBUTION, calls
                finally:
                    sys.path.remove(td)
        finally:
            for key in list(sys.modules):
                if key == 'version_check' or key.startswith('version_check.'):
                    del sys.modules[key]
            sys.modules.update(saved)

    def test_original_android_reproduces_lsb_attempt_even_when_disabled(self):
        _, calls = self.run_service(self.original, android=True, enabled=False)
        self.assertIn(('child', ('lsb_release', '-a')), calls)
        self.assertIn(('log', ('Disabled',)), calls)

    def test_android_preserves_enabled_version_check_without_distribution_child(self):
        distribution, calls = self.run_service(self.candidate, android=True)
        self.assertEqual('android', distribution)
        self.assertFalse(any(c[0] == 'child' for c in calls), calls)
        self.assertIn(('version_list',), calls)
        self.assertIn(('installed_version',), calls)

    def test_disabled_setting_preserved_without_import_side_effect(self):
        distribution, calls = self.run_service(self.candidate, android=True, enabled=False)
        self.assertEqual('android', distribution)
        self.assertFalse(any(c[0] in ('child', 'version_list', 'installed_version') for c in calls))
        self.assertIn(('log', ('Disabled',)), calls)

    def test_non_android_linux_distribution_probe_unchanged(self):
        before = self.run_service(self.original, android=False, enabled=False)
        after = self.run_service(self.candidate, android=False, enabled=False)
        self.assertEqual(before, after)
        self.assertIn(('child', ('lsb_release', '-a')), after[1])

    def test_unknown_original_source_refused(self):
        with self.assertRaisesRegex(ValueError, 'unverified original'):
            repair.patch_service(self.original[repair.SERVICE] + b'\n')

    def test_package_preserves_all_other_files_and_roundtrips(self):
        self.assertEqual(103, len(self.original))
        self.assertEqual(['addon.xml', repair.SERVICE],
                         [n for n in sorted(self.original) if self.original[n] != self.candidate[n]])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            first = repair.build(APK, p / 'one')
            second = repair.build(APK, p / 'two')
            self.assertEqual(first, second)
            staged = repair.stage(p / 'one' / repair.ARCHIVE, p / 'addons')
            self.assertEqual(repair.VERSION, staged['version'])
            self.assertEqual(self.candidate,
                             {f.relative_to(p / 'addons' / repair.ADDON).as_posix(): f.read_bytes()
                              for f in (p / 'addons' / repair.ADDON).rglob('*') if f.is_file()})
            with self.assertRaisesRegex(ValueError, 'refuse to overwrite'):
                repair.stage(p / 'one' / repair.ARCHIVE, p / 'addons')

    def test_mutated_archive_and_matching_proof_cannot_replace_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            proof = repair.build(APK, p)
            archive = p / repair.ARCHIVE
            # Even a matching rewritten sidecar cannot invent new provenance.
            archive.write_bytes(archive.read_bytes() + b'unapproved-change')
            proof['archive_sha256'] = repair.sha(archive.read_bytes())
            (p / 'BUILD-VERSIONCHECK-ANDROID.json').write_text(json.dumps(proof))
            with self.assertRaisesRegex(ValueError, 'package hash mismatch'):
                repair.stage(archive, p / 'addons')

    def test_existing_dangling_addon_symlink_refused(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            repair.build(APK, p)
            stage = p / 'addons'
            stage.mkdir()
            (stage / repair.ADDON).symlink_to(p / 'missing')
            with self.assertRaisesRegex(ValueError, 'refuse to overwrite'):
                repair.stage(p / repair.ARCHIVE, stage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    APK = args.apk
    unittest.main(argv=[sys.argv[0], *remaining])
