import io
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile
import zlib

LIB = Path(__file__).resolve().parents[1] / 'delta/resources/lib'
sys.path.insert(0, str(LIB))
import infinity_zip_metadata as metadata
from infinity_preview_state import Session

MANIFEST = '''<addon id="script.preview.test" name="Preview Test" version="1.2.3" provider-name="Infinity"><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><description lang="en_GB">A safe description.</description><assets><icon>icon.png</icon></assets></extension></addon>'''


def png(width=1, height=1):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\x00\x00\x00\x00\xff')) + chunk(b'IEND', b'')


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.archive = self.directory / 'Preview [test].zip'

    def tearDown(self):
        self.temp.cleanup()

    def make(self, manifest=MANIFEST, extras=None, compression=zipfile.ZIP_DEFLATED):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.archive, 'w', compression=compression) as archive:
                archive.writestr('script.preview.test/addon.xml', manifest)
                if 'script.preview.test/icon.png' not in (extras or {}):
                    archive.writestr('script.preview.test/icon.png', png())
                for name, value in (extras or {}).items():
                    if isinstance(value, zipfile.ZipInfo):
                        archive.writestr(value, b'../outside')
                    else:
                        archive.writestr(name, value)
        return metadata.inspect(str(self.archive))

    def test_real_fields_and_bounded_icon(self):
        result = self.make()
        self.assertTrue(result.compatible, result.status)
        self.assertEqual((result.name, result.addon_id, result.version, result.author, result.addon_type),
                         ('Preview Test', 'script.preview.test', '1.2.3', 'Infinity', 'Script'))
        self.assertEqual(result.description, 'A safe description.')
        self.assertTrue(result.icon.startswith('zip://'))
        self.assertLessEqual(result.bytes_read, metadata.MAX_READ)
        self.assertEqual(result.entries_seen, 2)

    def test_stored_zip_supported(self):
        self.assertTrue(self.make(compression=zipfile.ZIP_STORED).compatible)

    def test_local_file_uri(self):
        self.make()
        self.assertTrue(metadata.inspect(self.archive.as_uri()).compatible)

    def test_no_archive_execution_or_extraction(self):
        sentinel = self.directory / 'executed'
        code = 'open(' + repr(str(sentinel)) + ',"w").write("executed")'
        result = self.make(extras={'script.preview.test/default.py': code})
        self.assertTrue(result.compatible)
        self.assertFalse(sentinel.exists())
        self.assertEqual(sorted(p.name for p in self.directory.iterdir()), [self.archive.name])

    def test_markup_is_literal(self):
        result = self.make(MANIFEST.replace('Preview Test', '[COLOR red]Preview[/COLOR]').replace('A safe description.', '[B]literal[/B]'))
        self.assertTrue(result.compatible)
        self.assertNotIn('[COLOR', result.name)
        self.assertNotIn('[B]', result.description)
        self.assertIn('［B］', result.description)

    def test_folders_do_not_scan_or_install(self):
        result = metadata.inspect(str(self.directory), folder=True, label='Folder')
        self.assertEqual(result.kind, 'Folder')
        self.assertFalse(result.compatible)
        self.assertEqual(result.bytes_read, 0)

    def test_ordinary_file_information(self):
        file = self.directory / 'movie.txt'
        file.write_text('contents')
        result = metadata.inspect(str(file))
        self.assertEqual(result.size, 8)
        self.assertFalse(result.compatible)
        self.assertEqual(result.bytes_read, 0)

    def test_remote_urls_are_not_opened_and_credentials_are_redacted(self):
        result = metadata.inspect('smb://user:secret@example.local/share/a.zip?token=private')
        self.assertFalse(result.compatible)
        self.assertNotIn('secret', result.path)
        self.assertNotIn('user', result.path)
        self.assertNotIn('private', result.path)
        self.assertEqual(result.bytes_read, 0)

    def test_truncated_and_non_zip(self):
        for data in (b'', b'not a zip', b'PK\x03\x04' + b'\x00' * 10):
            with self.subTest(data=data):
                self.archive.write_bytes(data)
                self.assertFalse(metadata.inspect(str(self.archive)).compatible)

    def test_unsafe_paths(self):
        for path in ('../outside', '/absolute', 'C:/absolute', 'script.preview.test/../outside',
                     'script.preview.test\\bad.py', 'script.preview.test//bad.py', 'script.preview.test/./bad.py'):
            with self.subTest(path=path):
                result = self.make(extras={path: b'x'})
                self.assertFalse(result.compatible, path)

    def test_symlink_rejected(self):
        link = zipfile.ZipInfo('script.preview.test/link')
        link.create_system = 3
        link.external_attr = (0o120777 << 16)
        self.assertFalse(self.make(extras={'link': link}).compatible)

    def test_duplicate_paths_rejected(self):
        self.assertFalse(self.make(extras={'script.preview.test/ADDON.XML': MANIFEST}).compatible)
        self.assertFalse(self.make(extras={'script.preview.test/addon.xml': MANIFEST}).compatible)

    def test_mismatched_addon_folder_and_multiple_packages(self):
        self.assertFalse(self.make(MANIFEST.replace('id="script.preview.test"', 'id="script.other"')).compatible)
        self.assertFalse(self.make(extras={'other/addon.xml': MANIFEST}).compatible)
        self.assertFalse(self.make(extras={'outside.txt': 'x'}).compatible)

    def test_invalid_xml_and_entity_expansion(self):
        for xml in ('<addon', '<!DOCTYPE addon [<!ENTITY x "value">]>' + MANIFEST,
                    MANIFEST.encode('utf-16'), MANIFEST.replace('A safe description.', '&unknown;')):
            with self.subTest(xml=str(xml)[:50]):
                self.assertFalse(self.make(xml).compatible)

    def test_missing_required_metadata(self):
        for old in ('id="script.preview.test"', 'name="Preview Test"', 'version="1.2.3"'):
            with self.subTest(field=old):
                self.assertFalse(self.make(MANIFEST.replace(old, '')).compatible)

    def test_xml_bomb_bound_before_decompression(self):
        result = self.make(MANIFEST.replace('A safe description.', 'A' * (metadata.MAX_XML + 1)))
        self.assertFalse(result.compatible)
        self.assertLess(result.bytes_read, metadata.MAX_XML)

    def test_entry_count_bound(self):
        result = self.make(extras={f'script.preview.test/data/{index}': b'' for index in range(metadata.MAX_ENTRIES)})
        self.assertFalse(result.compatible)
        self.assertLessEqual(result.bytes_read, 65557)

    def test_damaged_metadata_crc(self):
        self.make(compression=zipfile.ZIP_STORED)
        data = bytearray(self.archive.read_bytes())
        index = data.index(b'<addon')
        data[index + 1] ^= 1
        self.archive.write_bytes(data)
        self.assertFalse(metadata.inspect(str(self.archive)).compatible)

    def test_inconsistent_local_header(self):
        self.make()
        data = bytearray(self.archive.read_bytes())
        struct.pack_into('<I', data, 22, 0x12345678)
        self.archive.write_bytes(data)
        self.assertFalse(metadata.inspect(str(self.archive)).compatible)

    def test_zip64_and_split_archives_refused(self):
        for field, value in ((4, 1), (6, 1), (10, 65535), (12, 0xffffffff)):
            with self.subTest(field=field):
                self.make()
                data = bytearray(self.archive.read_bytes())
                end = data.rfind(b'PK\x05\x06')
                struct.pack_into('<I' if field == 12 else '<H', data, end + field, value)
                self.archive.write_bytes(data)
                self.assertFalse(metadata.inspect(str(self.archive)).compatible)

    def test_large_or_external_icons_do_not_block_valid_metadata(self):
        result = self.make(extras={'script.preview.test/icon.png': png(4096, 4096)})
        self.assertTrue(result.compatible)
        self.assertEqual(result.icon, '')
        result = self.make(MANIFEST.replace('icon.png', 'https://example.invalid/icon.png'))
        self.assertTrue(result.compatible)
        self.assertEqual(result.icon, '')

    def test_corrupt_png_does_not_reach_decoder(self):
        self.assertEqual(metadata.image_dimensions(b'\x89PNG\r\n\x1a\n' + b'\x00' * 40), (0, 0))

    def test_cancelled_read_cannot_enable_install(self):
        self.make()
        result = metadata.inspect(str(self.archive), cancel=lambda: True)
        self.assertFalse(result.compatible)
        self.assertEqual(result.bytes_read, 0)

    def test_metadata_changes_invalidate_install(self):
        old = self.make()
        same = metadata.inspect(str(self.archive))
        self.assertTrue(metadata.same_metadata(old, same))
        changed = self.make(MANIFEST.replace('version="1.2.3"', 'version="1.2.4"'))
        self.assertFalse(metadata.same_metadata(old, changed))

    def test_session_requires_explicit_install(self):
        session = Session()
        self.assertFalse(session.request_install())
        self.assertTrue(session.loaded(self.make()))
        self.assertEqual(session.state, 'ready')
        self.assertTrue(session.request_install())
        self.assertFalse(session.request_install())
        self.assertTrue(session.checked(metadata.inspect(str(self.archive))))
        self.assertEqual(session.state, 'install')

    def test_cancel_wins_over_late_results(self):
        for stage in ('loading', 'ready', 'checking'):
            with self.subTest(stage=stage):
                session = Session()
                result = self.make()
                if stage != 'loading':
                    session.loaded(result)
                if stage == 'checking':
                    session.request_install()
                session.cancel()
                self.assertFalse(session.loaded(result))
                self.assertFalse(session.request_install())
                self.assertFalse(session.checked(result))
                self.assertEqual(session.state, 'closed')

    def test_changed_file_requires_second_deliberate_install(self):
        session = Session()
        session.loaded(self.make())
        session.request_install()
        current = self.make(MANIFEST.replace('version="1.2.3"', 'version="1.2.4"'))
        self.assertFalse(session.checked(current))
        self.assertEqual(session.state, 'ready')
        self.assertTrue(session.request_install())
        self.assertTrue(session.checked(metadata.inspect(str(self.archive))))

    def test_repeated_sessions_release_state(self):
        result = self.make()
        for _ in range(1000):
            session = Session()
            self.assertTrue(session.loaded(result))
            session.cancel()
            self.assertFalse(session.request_install())


if __name__ == '__main__':
    unittest.main(verbosity=2)
