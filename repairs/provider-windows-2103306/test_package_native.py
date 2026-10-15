#!/usr/bin/env python3
"""Fail-closed package contract tests, not ARM64/runtime/device validation."""
import copy
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile

from package_native import (ENGINE, FILES, HERE, VERSION, digest, manifest_delta,
    manifest_module, expected_source_changes, check_source_receipt, verify_bytes)
from restore_assets import locked_map, MAP_SHA

MANIFEST = (HERE / 'fixtures/locked-3305-AndroidManifest.xml').read_bytes()


def receipt():
    parent = locked_map(HERE / 'fixtures/locked-3305-source-manifest.json.gz')
    after = dict(parent)
    after.update(expected_source_changes())
    result = dict(candidate=VERSION, locked_apk_parent=2103305,
        locked_skin_parent='1.0.5.196', parent_source_map_sha256=MAP_SHA,
        before=parent, after=after, changed=sorted(FILES),
        active_skin_adaptation_preserved=True)
    for name in ('provider_python_changed', 'back_dispatch_policy_changed',
                 'back_freeze_resolved', 'shutdown_changed', 'weather_changed',
                 'video_framing_changed', 'physical_device_verified', 'crash_owner_proven'):
        result[name] = False
    return result


def archives(root, changes=None, additional=None):
    old = {'AndroidManifest.xml': MANIFEST, ENGINE: b'unit-test-old-engine',
           'classes.dex': b'unit-test-dex', 'resources.arsc': b'unit-test-resource',
           'assets/protected': b'protected', 'lib/arm64-v8a/companion.so': b'companion'}
    new = dict(old)
    new.update({'AndroidManifest.xml': manifest_delta(MANIFEST), ENGINE: b'unit-test-new-engine'})
    new.update(changes or {})
    new.update(additional or {})
    for name, files in [('base.apk', old), ('candidate.apk', new)]:
        with zipfile.ZipFile(root / name, 'w') as archive:
            for member, data in files.items():
                archive.writestr(member, data)
    native = root / 'native.so'
    native.write_bytes(b'unit-test-new-engine')
    return root / 'base.apk', root / 'candidate.apk', native


class PackageContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = receipt()

    def test_real_manifest_integer_only_change_round_trip(self):
        data = manifest_delta(MANIFEST)
        self.assertEqual(manifest_module.version_code(data)[1], VERSION)
        self.assertEqual(manifest_module.version_code(data, 2103305)[0], MANIFEST)
        self.assertEqual(len(data), len(MANIFEST))
        self.assertLessEqual(sum(a != b for a, b in zip(data, MANIFEST)), 4)

    def test_wrong_manifest_preimage_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Wrong locked compiled manifest'):
            manifest_delta(MANIFEST + b' ')

    def test_complete_authenticated_native_source_map_accepted(self):
        check_source_receipt(self.receipt)

    def test_parent_map_tampering_rejected(self):
        changed = copy.deepcopy(self.receipt)
        changed['before']['README.md'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Complete native preimage'):
            check_source_receipt(changed)

    def test_extra_native_source_change_rejected(self):
        changed = copy.deepcopy(self.receipt)
        changed['after']['README.md'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'three-file transform'):
            check_source_receipt(changed)

    def test_forged_three_file_candidate_rejected(self):
        changed = copy.deepcopy(self.receipt)
        changed['after'][FILES[0]] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'three-file transform'):
            check_source_receipt(changed)

    def test_unproven_back_fix_claim_rejected(self):
        changed = copy.deepcopy(self.receipt)
        changed['back_freeze_resolved'] = True
        with self.assertRaisesRegex(ValueError, 'unsupported claim'):
            check_source_receipt(changed)

    def test_only_native_and_version_payloads_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            report = verify_bytes(*archives(Path(temp)))
            self.assertEqual(report['unchanged_payload_count'], 4)
            self.assertEqual(report['changed_payloads'], ['AndroidManifest.xml', ENGINE])

    def test_any_protected_payload_drift_rejected(self):
        for member in ['classes.dex', 'resources.arsc', 'assets/protected',
                       'lib/arm64-v8a/companion.so']:
            with self.subTest(member=member), tempfile.TemporaryDirectory() as temp:
                with self.assertRaisesRegex(ValueError, 'Unexpected payload delta'):
                    verify_bytes(*archives(Path(temp), changes={member: b'changed'}))

    def test_new_payload_and_wrong_engine_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'member set drift'):
                verify_bytes(*archives(Path(temp), additional={'assets/extra': b'extra'}))
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'staged candidate'):
                verify_bytes(*archives(Path(temp), changes={ENGINE: b'wrong-engine'}))

    def test_duplicate_member_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            files = archives(Path(temp))
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with zipfile.ZipFile(files[1], 'a') as archive:
                    archive.writestr('classes.dex', b'duplicate')
            with self.assertRaisesRegex(ValueError, 'Duplicate APK members'):
                verify_bytes(*files)


if __name__ == '__main__':
    unittest.main(verbosity=2)
