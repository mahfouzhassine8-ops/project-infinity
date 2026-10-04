#!/usr/bin/env python3
import hashlib
from pathlib import Path
import struct
import unittest
import zlib
from restore_assets import (HERE, START, SIGNATURE, at_time, chunks, fixed_chunks,
                            locked_map, recover)


def png():
    values = [(b'IHDR', struct.pack('>2I5B', 1, 1, 8, 2, 0, 0, 0)),
              (b'tIME', b'\0' * 7),
              (b'IDAT', zlib.compress(b'\0\xff\0\0')),
              (b'tEXt', b'date:create\0unused'),
              (b'tEXt', b'date:modify\0unused'), (b'IEND', b'')]
    return at_time(values, START)


class PreservationTests(unittest.TestCase):
    def test_timestamp_recovery_reproduces_exact_locked_bytes(self):
        expected = png()
        from datetime import timedelta
        current = at_time(chunks(expected), START + timedelta(days=5))
        recovered, moment = recover(current, hashlib.sha256(expected).hexdigest())
        self.assertEqual(recovered, expected)
        self.assertEqual(moment, START.isoformat())
        self.assertEqual(fixed_chunks(current), fixed_chunks(recovered))

    def test_changed_image_cannot_be_accepted(self):
        values = chunks(png())
        values = [(kind, zlib.compress(b'\0\0\xff\0') if kind == b'IDAT' else data)
                  for kind, data in values]
        with self.assertRaisesRegex(ValueError, 'No exact locked PNG hash match'):
            recover(at_time(values, START), hashlib.sha256(png()).hexdigest())

    def test_corrupt_crc_is_rejected(self):
        data = bytearray(png())
        data[20] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC'):
            chunks(bytes(data))

    def test_unchanged_file_is_not_rewritten(self):
        data = png()
        self.assertEqual(recover(data, hashlib.sha256(data).hexdigest()), (data, None))

    def test_locked_engine_receipt_is_authenticated(self):
        mapping = locked_map(HERE / 'fixtures/locked-3305-source-manifest.json.gz')
        self.assertEqual(len(mapping), 9372)
        self.assertEqual(mapping['xbmc/addons/Skin.h'],
                         '4933bc3796dd39bbe8e7f5c62d3ba7c4301dcecf74866f9764853b09d9f7cffa')

    def test_modified_receipt_is_not_accepted(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'receipt.json'
            import gzip
            payload = gzip.decompress((HERE / 'fixtures/locked-3305-source-manifest.json.gz').read_bytes())
            file.write_bytes(payload + b' ')
            with self.assertRaisesRegex(ValueError, 'Unauthenticated'):
                locked_map(file)


if __name__ == '__main__':
    unittest.main(verbosity=2)
