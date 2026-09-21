"""Timestamp-only baseline restoration guards; not Android acceptance."""
from pathlib import Path
import json
import struct
import tempfile
import unittest
from unittest import mock
import zipfile
import zlib
import canonicalize_parent_png as canonical

PATH = 'media/applaunch_screen.png'

def chunk(kind, value):
    return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value) & 0xffffffff)

def png(hour=1, pixel=10, width=1, comment=b'approved', date_key=b'date:create'):
    return b'\x89PNG\r\n\x1a\n' + b''.join([
        chunk(b'IHDR', struct.pack('>IIBBBBB', width, 1, 8, 6, 0, 0, 0)),
        chunk(b'tIME', struct.pack('>HBBBBB', 2026, 9, 21, hour, 0, 0)),
        chunk(b'tEXt', date_key + b'\0' + ('2026-09-21T%02d:00:00+00:00' % hour).encode()),
        chunk(b'tEXt', b'date:modify\0' + ('2026-09-21T%02d:00:00+00:00' % hour).encode()),
        chunk(b'tEXt', b'Comment\0' + comment),
        chunk(b'IDAT', zlib.compress(b'\0' + bytes([pixel, 0, 0, 255]) * width)),
        chunk(b'IEND', b'')])

class ParentPngTimestampTest(unittest.TestCase):
    def test_timestamp_only_same_encoded_image_allowed(self):
        self.assertEqual(['tIME', 'date:create', 'date:modify'], canonical.prove_timestamp_only(PATH, png(2), png(1)))

    def test_identical_source_is_accepted(self):
        self.assertEqual([], canonical.prove_timestamp_only(PATH, png(), png()))

    def test_pixel_change_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'non-timestamp'):
            canonical.prove_timestamp_only(PATH, png(pixel=50), png())

    def test_ihdr_change_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'non-timestamp'):
            canonical.prove_timestamp_only(PATH, png(width=2), png())

    def test_unknown_text_change_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'non-timestamp'):
            canonical.prove_timestamp_only(PATH, png(comment=b'altered'), png())

    def test_timestamp_text_key_cannot_be_renamed(self):
        with self.assertRaisesRegex(RuntimeError, 'non-timestamp'):
            canonical.prove_timestamp_only(PATH, png(date_key=b'date:other'), png())

    def test_timestamp_crc_corruption_rejected(self):
        corrupt = bytearray(png(2))
        corrupt[50] ^= 1
        with self.assertRaisesRegex(RuntimeError, 'CRC'):
            canonical.prove_timestamp_only(PATH, bytes(corrupt), png())

    def test_unapproved_png_path_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Unapproved timestamp source'):
            canonical.prove_timestamp_only('media/new.png', png(2), png(1))

    def test_trailing_data_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'trailing'):
            canonical.prove_timestamp_only(PATH, png() + b'other', png())

    def test_deleted_timestamp_chunk_rejected(self):
        candidate = b'\x89PNG\r\n\x1a\n' + b''.join(raw for kind, value, raw in canonical.png_chunks(png()) if kind != b'tIME')
        with self.assertRaisesRegex(RuntimeError, 'inventory'):
            canonical.prove_timestamp_only(PATH, candidate, png())

    def setup_tree(self, folder, other=b'approved Java'):
        source = folder / 'source'
        (source / 'media').mkdir(parents=True)
        (source / PATH).write_bytes(png(2))
        (source / 'Activity.java').write_bytes(other)
        archive = folder / 'parent.zip'
        with zipfile.ZipFile(archive, 'w') as out:
            out.writestr(PATH, png())
            out.writestr('Activity.java', b'approved Java')
        inventory = {PATH: canonical.digest(png()), 'Activity.java': canonical.digest(b'approved Java')}
        receipt = folder / 'receipt.json'
        receipt.write_text(json.dumps({'files': {PATH: {'after': canonical.digest(png(2))},
            'Activity.java': {'after': canonical.digest(other)}}}))
        return source, archive, inventory, receipt, folder / 'report.json'

    def test_exact_restore_and_receipt_and_before_after_evidence(self):
        with tempfile.TemporaryDirectory(prefix='cobra208-png-test-') as directory:
            args = self.setup_tree(Path(directory))
            with mock.patch.object(canonical, 'PARENT_SOURCE', canonical.digest(args[1].read_bytes())):
                rows = canonical.canonicalize(*args)
            self.assertEqual(png(), (args[0] / PATH).read_bytes())
            self.assertEqual(canonical.digest(png(2)), rows[0]['before_sha256'])
            self.assertEqual(canonical.digest(png()), rows[0]['after_sha256'])
            self.assertEqual(canonical.digest(png()), json.loads(args[3].read_text())['files'][PATH]['after'])
            self.assertEqual(2, json.loads(args[4].read_text())['canonical_source_files_verified'])

    def test_unknown_source_drift_rejected_before_any_restore(self):
        with tempfile.TemporaryDirectory(prefix='cobra208-png-test-') as directory:
            args = self.setup_tree(Path(directory), other=b'changed Java')
            with mock.patch.object(canonical, 'PARENT_SOURCE', canonical.digest(args[1].read_bytes())):
                with self.assertRaisesRegex(RuntimeError, 'Unapproved timestamp source'):
                    canonical.canonicalize(*args)
            self.assertEqual(png(2), (args[0] / PATH).read_bytes())
            self.assertFalse(args[4].exists())

    def test_wrong_archive_hash_rejected_before_any_restore(self):
        with tempfile.TemporaryDirectory(prefix='cobra208-png-test-') as directory:
            args = self.setup_tree(Path(directory))
            with self.assertRaisesRegex(RuntimeError, 'Wrong locked source archive'):
                canonical.canonicalize(*args)
            self.assertEqual(png(2), (args[0] / PATH).read_bytes())

    def test_original_receipt_drift_rejected_before_any_restore(self):
        with tempfile.TemporaryDirectory(prefix='cobra208-png-test-') as directory:
            args = self.setup_tree(Path(directory))
            data = json.loads(args[3].read_text())
            data['files'][PATH]['after'] = '0' * 64
            args[3].write_text(json.dumps(data))
            with mock.patch.object(canonical, 'PARENT_SOURCE', canonical.digest(args[1].read_bytes())):
                with self.assertRaisesRegex(RuntimeError, 'Original source receipt drift'):
                    canonical.canonicalize(*args)
            self.assertEqual(png(2), (args[0] / PATH).read_bytes())

if __name__ == '__main__':
    unittest.main(verbosity=2)
