"""Negative tests for the exact authorized PNG delta; never Android acceptance."""
from pathlib import Path
import copy
import hashlib
import json
import struct
import tempfile
import unittest
import zipfile
import zlib
from branding_package import resource_slots, validate_rows, verify_exact_payload_delta, replace_reviewed_pngs

def png(value=0, width=1):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    header = struct.pack('>IIBBBBB', width, 1, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(b'\x00' + bytes([value, 0, 0, 255]) * width)) + chunk(b'IEND', b'')

def digest(data):
    return hashlib.sha256(data).hexdigest()

class BrandingDeltaGuardTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cobra208-guard-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old, self.new = png(30), png(200)
        self.row = dict(source='tools/android/packaging/xbmc/res/drawable-nodpi/infinity_splash_icon.png',
            slot=['drawable/infinity_splash_icon', 'nodpi'], entry='res/rk.png',
            before=digest(self.old), after=digest(self.new), dimensions=[1, 1])
        self.payload = {'AndroidManifest.xml': b'manifest', 'classes.dex': b'dex',
            'resources.arsc': b'immutable resource table', 'lib/arm64-v8a/libkodi.so': b'precious native engine',
            'assets/provider.json': b'provider', 'res/rk.png': self.old, 'res/other.png': png(25),
            'res/IG.xml': b'adaptive XML', 'META-INF/CERT.SF': b'signing'}
        self.base = self.write('base.apk', self.payload)
        self.target = dict(self.payload)
        self.target['res/rk.png'] = self.new

    def write(self, name, values):
        path = self.root / name
        with zipfile.ZipFile(path, 'w') as archive:
            for key, value in values.items():
                archive.writestr(key, value)
        return path

    def verify(self, target=None, rows=None):
        return verify_exact_payload_delta(self.base, self.write('target.apk', self.target if target is None else target), [self.row] if rows is None else rows)

    def test_exact_approved_replacement_passes(self):
        result = self.verify()
        self.assertTrue(result['resource_table_byte_identical'])
        self.assertTrue(result['unrelated_resources_byte_identical'])
        self.assertFalse(result['android_resources_byte_identical'])
        self.assertEqual(['res/rk.png'], result['approved_branding_resource_entries'])

    def test_native_change_rejected(self):
        self.target['lib/arm64-v8a/libkodi.so'] = b'changed'
        with self.assertRaisesRegex(RuntimeError, 'Protected APK payload changed'):
            self.verify()

    def test_provider_asset_change_rejected(self):
        self.target['assets/provider.json'] = b'changed'
        with self.assertRaisesRegex(RuntimeError, 'Protected APK payload changed'):
            self.verify()

    def test_resource_table_change_rejected(self):
        self.target['resources.arsc'] = b'changed'
        with self.assertRaisesRegex(RuntimeError, 'Protected APK payload changed'):
            self.verify()

    def test_adaptive_xml_change_rejected(self):
        self.target['res/IG.xml'] = b'changed'
        with self.assertRaisesRegex(RuntimeError, 'Protected APK payload changed'):
            self.verify()

    def test_unlisted_png_change_rejected(self):
        self.target['res/other.png'] = self.new
        with self.assertRaisesRegex(RuntimeError, 'Protected APK payload changed'):
            self.verify()

    def test_added_resource_rejected(self):
        self.target['res/new.png'] = self.new
        with self.assertRaisesRegex(RuntimeError, 'inventory'):
            self.verify()

    def test_deleted_resource_rejected(self):
        del self.target['res/other.png']
        with self.assertRaisesRegex(RuntimeError, 'inventory'):
            self.verify()

    def test_wrong_candidate_icon_hash_rejected(self):
        self.target['res/rk.png'] = png(100)
        with self.assertRaisesRegex(RuntimeError, 'Candidate approved PNG drift'):
            self.verify()

    def test_wrong_parent_icon_hash_rejected(self):
        self.row['before'] = '0' * 64
        with self.assertRaisesRegex(RuntimeError, 'Parent approved PNG drift'):
            self.verify()

    def test_duplicate_approved_entry_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Duplicate'):
            self.verify(rows=[self.row, self.row])

    def test_new_source_identity_rejected(self):
        self.row['source'] = 'tools/android/packaging/xbmc/res/drawable-nodpi/new.png'
        with self.assertRaisesRegex(RuntimeError, 'Unapproved branding source'):
            self.verify()

    def test_wrong_named_resource_slot_rejected(self):
        self.row['slot'] = ['drawable/other', 'nodpi']
        with self.assertRaisesRegex(RuntimeError, 'Wrong named icon slot'):
            self.verify()

    def test_reviewed_digest_cannot_hide_dimension_change(self):
        content = png(200, width=2)
        self.target['res/rk.png'] = content
        self.row['after'] = digest(content)
        with self.assertRaisesRegex(RuntimeError, 'dimensions'):
            self.verify()

    def test_resources_arsc_cannot_be_allowlisted(self):
        self.row['entry'] = 'resources.arsc'
        with self.assertRaisesRegex(RuntimeError, 'Invalid PNG payload target'):
            self.verify()

    def test_unchanged_payload_not_exempted(self):
        self.row['after'] = self.row['before']
        with self.assertRaisesRegex(RuntimeError, 'Unchanged payload'):
            self.verify()

    def test_resource_slots_reject_ambiguous_mapping(self):
        text = 'resource 0x7f040007 drawable/infinity_splash_icon\n  (nodpi) (file) res/rk.png type=PNG\n  (nodpi) (file) res/other.png type=PNG\n'
        with self.assertRaisesRegex(RuntimeError, 'Ambiguous'):
            resource_slots(text)

    def test_replacement_requires_matching_named_base_mapping(self):
        source = self.root / self.row['source']
        source.parent.mkdir(parents=True)
        source.write_bytes(self.new)
        report = self.root / 'resources.txt'
        report.write_text('resource 0x7f040007 drawable/infinity_splash_icon\n  (nodpi) (file) res/other.png type=PNG\n')
        with self.assertRaisesRegex(RuntimeError, 'mapping drift'):
            replace_reviewed_pngs(self.base, self.root, [self.row], report)
        with zipfile.ZipFile(self.base) as archive:
            self.assertEqual(self.old, archive.read('res/rk.png'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
