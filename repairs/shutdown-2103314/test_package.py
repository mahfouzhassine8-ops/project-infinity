#!/usr/bin/env python3
"""Exercise production merge/preservation guards with small APK-shaped fixtures."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import package_candidate as candidate


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='infinity-preservation-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / 'base.apk'
        self.donor = self.root / 'donor.apk'
        self.native = self.root / 'libkodi.so'
        self.final = self.root / 'candidate.apk'
        self.native.write_bytes(b'new-native')
        entries = {'AndroidManifest.xml': b'old-manifest', candidate.ENGINE: b'old-native',
                   'classes.dex': b'old-Cobra-and-Infinity-code', 'resources.arsc': b'locked-resources',
                   'assets/skin.xml': b'locked-skin', 'lib/arm64-v8a/libpython.so': b'locked-python',
                   'META-INF/CERT.RSA': b'old-signature'}
        with zipfile.ZipFile(self.base, 'w') as z:
            for name, data in entries.items():
                z.writestr(name, data)
        with zipfile.ZipFile(self.donor, 'w') as z:
            z.writestr('AndroidManifest.xml', b'versioned-manifest')
            z.writestr('classes.dex', b'new-diagnostic-code')
        self.mock_native = patch.object(candidate, 'BASE_NATIVE', candidate.sha(b'old-native'))
        self.mock_native.start()
        self.addCleanup(self.mock_native.stop)
        self.mock_dex = patch.object(candidate, 'dex_contract', return_value=({('same-JNI',)}, set()))
        self.mock_dex.start()
        self.addCleanup(self.mock_dex.stop)
        candidate.merge(self.base, self.donor, self.native, self.final)

    def rewrite(self, name, data):
        target = self.root / 'tampered.apk'
        with zipfile.ZipFile(self.final) as a, zipfile.ZipFile(target, 'w') as b:
            for info in a.infolist():
                b.writestr(info, data if info.filename == name else a.read(info.filename))
            if name not in a.namelist():
                b.writestr(name, data)
        return target

    def test_protected_payload_and_diagnostic_dex(self):
        self.assertEqual(len(candidate.native_patch.ALLOWED), 9)
        result = candidate.verify_bytes(self.base, self.final, self.native)
        self.assertTrue(result['jni_contract_unchanged'])
        self.assertEqual(result['other_native_libraries_byte_identical'], 1)
        with zipfile.ZipFile(self.final) as z:
            self.assertEqual(z.read('classes.dex'), b'new-diagnostic-code')
            self.assertEqual(z.read('AndroidManifest.xml'), b'versioned-manifest')

    def test_any_protected_change_rejected(self):
        for name in ('resources.arsc', 'assets/skin.xml', 'lib/arm64-v8a/libpython.so'):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                candidate.verify_bytes(self.base, self.rewrite(name, b'tampered'), self.native)

    def test_wrong_engine_rejected(self):
        with self.assertRaises(RuntimeError):
            candidate.verify_bytes(self.base, self.rewrite(candidate.ENGINE, b'tampered'), self.native)

    def test_extra_payload_rejected(self):
        with self.assertRaises(RuntimeError):
            candidate.verify_bytes(self.base, self.rewrite('assets/new.xml', b'extra'), self.native)

    def test_wrong_parent_native_rejected(self):
        with patch.object(candidate, 'BASE_NATIVE', 'incorrect'), self.assertRaises(RuntimeError):
            candidate.merge(self.base, self.donor, self.native, self.root / 'wrong.apk')


if __name__ == '__main__':
    unittest.main()
