"""Selected exporter failure reproduction and read-only source-collection contract.

Disposable local fixtures/fake ADB only; no device or original database access.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import os

HERE = Path(__file__).resolve().parent
ROOT = '/sdcard/Android/data/com.projectinfinity.kodi/files/.kodi/addons/'
CC = 'script.infinity.commandcenter/'
APK = '/data/app/~~example/com.projectinfinity.kodi-example/base.apk'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collector = load(HERE / 'read_device_inventory.py', 'selected_read_device_inventory')


class FakeADB:
    def __init__(self):
        self.calls = []
        self.files = {
            CC + 'INFINITY-MODULES.v1': (
                b'INFINITY-MODULES/1\npackage\t0.3.5.62\nfile\t' + b'a' * 64 +
                b'\tscript.infinity.commandcenter/provider_inventory.py\n'),
            CC + 'INFINITY-MODULES.v1.sig': b'fake signature, not release authentication',
        }
        for aid in ('plugin.video.umbrella', 'plugin.video.pov',
                    'script.module.tmdbhelper.sync.trakt',
                    'script.infinity.commandcenter', 'script.kodihealthcenter'):
            self.files[aid + '/addon.xml'] = ('<addon id="' + aid + '" version="fixture"/>').encode()
        for aid, names in (
                ('plugin.video.umbrella', ('umbrella.py', 'resources/lib/modules/router.py',
                                          'resources/lib/menus/movies.py', 'resources/lib/menus/tvshows.py')),
                ('plugin.video.pov', ('resources/lib/router.py', 'resources/lib/modules/entry.py',
                                     'resources/lib/menus/movies.py', 'resources/lib/menus/tvshows.py')),
                ('script.module.tmdbhelper.sync.trakt', ('resources/script.py', 'resources/settings.xml',
                    'resources/language/resource.language.en_gb/strings.po',
                    'resources/lib/tmdbhelper_sync_trakt/account.py',
                    'resources/lib/tmdbhelper_sync_trakt/api/api.py',
                    'resources/lib/tmdbhelper_sync_trakt/api/authenticator.py',
                    'resources/lib/tmdbhelper_sync_trakt/api/token.py',
                    'resources/lib/tmdbhelper_sync_trakt/api/recovery.py')),
                ('script.infinity.commandcenter', ('provider_inventory.py',)),
                ('script.kodihealthcenter', ('default.py', 'khc_exports.py', 'khc_safety.py'))):
            for name in names:
                self.files[aid + '/' + name] = b'# public source fixture\n'
        self.files['plugin.video.umbrella/unreadable.db'] = b'PRIVATE DATABASE FIXTURE MUST NEVER BE READ'

    def run(self, args, **kwargs):
        assert kwargs == dict(capture_output=True, timeout=60)
        command = args[1:]
        self.calls.append(command)
        code, raw = 0, b''
        if command == ['shell', 'dumpsys', 'package', 'com.projectinfinity.kodi']:
            raw = b'versionCode=2103464 minSdk=23\n'
        elif command == ['shell', 'pm', 'path', 'com.projectinfinity.kodi']:
            raw = ('package:' + APK + '\n').encode()
        elif command[:2] == ['exec-out', 'sha256sum']:
            for name in command[2:]:
                if name == APK:
                    digest = 'b' * 64
                else:
                    assert name.startswith(ROOT)
                    relative = name[len(ROOT):]
                    assert relative in self.files
                    digest = hashlib.sha256(self.files[relative]).hexdigest()
                raw += (digest + '  ' + name + '\n').encode()
        elif command[:3] == ['exec-out', 'head', '-c']:
            assert len(command) == 5 and command[4].startswith(ROOT)
            relative = command[4][len(ROOT):]
            if relative in self.files:
                raw = self.files[relative][:int(command[3])]
            else:
                code = 1
        else:
            raise AssertionError('Unselected ADB command: ' + repr(command))
        return subprocess.CompletedProcess(args, code, raw, b'')


class ReadOnlySourceInventory(unittest.TestCase):
    def invoke(self, transport, report, sources):
        args = ['read_device_inventory.py', '--out', str(report), '--sources-out', str(sources)]
        with patch.object(sys, 'argv', args), patch.object(collector.subprocess, 'run', transport.run), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            collector.main()

    def test_only_selected_sources_copied_no_database_or_profile_reads(self):
        fake = FakeADB()
        before = dict(fake.files)
        with tempfile.TemporaryDirectory(prefix='inventory-selected-') as tmp:
            out, sources = Path(tmp) / 'report.json', Path(tmp) / 'sources'
            self.invoke(fake, out, sources)
            report = json.loads(out.read_text())
            self.assertFalse(report['phone_writes'])
            self.assertFalse(report['settings_or_database_reads'])
            self.assertEqual(report['apk_version_code'], 2103464)
            actual = {p.relative_to(sources).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sources.rglob('*') if p.is_file()}
            self.assertEqual(actual, report['source_copies_on_computer'])
            self.assertGreaterEqual(len(actual), 25)
            self.assertNotIn('plugin.video.umbrella/unreadable.db', actual)
            self.assertEqual(report['inspection_source_hashes']['script.infinity.commandcenter']
                             ['native_search_compatibility.py'], 'UNREADABLE')
            for command in fake.calls:
                for argument in command:
                    self.assertNotIn('unreadable.db', argument)
                    self.assertNotIn('/userdata/', argument)
                    self.assertNotIn('/addon_data/', argument)
            self.assertEqual(before, fake.files)

    def test_database_record_rejected_before_hash_read(self):
        fake = FakeADB()
        fake.files[CC + 'INFINITY-MODULES.v1'] = (
            b'INFINITY-MODULES/1\nfile\t' + b'a' * 64 + b'\tscript.infinity.commandcenter/private.db\n')
        with tempfile.TemporaryDirectory(prefix='inventory-selected-') as tmp:
            out, sources = Path(tmp) / 'report.json', Path(tmp) / 'sources'
            with self.assertRaisesRegex(RuntimeError, 'Invalid module record'):
                self.invoke(fake, out, sources)
            self.assertFalse(out.exists())
            self.assertFalse(sources.exists())
        self.assertFalse(any('private.db' in arg for cmd in fake.calls for arg in cmd))

    def test_oversized_source_is_not_copied(self):
        fake = FakeADB()
        relative = 'script.module.tmdbhelper.sync.trakt/resources/script.py'
        fake.files[relative] = b'x' * (512 * 1024 + 1)
        with tempfile.TemporaryDirectory(prefix='inventory-selected-') as tmp:
            out, sources = Path(tmp) / 'report.json', Path(tmp) / 'sources'
            self.invoke(fake, out, sources)
            self.assertEqual(json.loads(out.read_text())['trakt_source_hashes']['resources/script.py'], 'UNREADABLE')
            self.assertFalse((sources / relative).exists())

    def test_existing_local_output_folder_is_preserved(self):
        fake = FakeADB()
        with tempfile.TemporaryDirectory(prefix='inventory-selected-') as tmp:
            sources = Path(tmp) / 'sources'
            sources.mkdir()
            sentinel = sources / 'sentinel.txt'
            sentinel.write_bytes(b'preserve existing computer files')
            with self.assertRaises(SystemExit):
                self.invoke(fake, Path(tmp) / 'report.json', sources)
            self.assertEqual(sentinel.read_bytes(), b'preserve existing computer files')
            self.assertEqual(fake.calls, [])

    def test_exact_exporter_refusal_with_source_only_selection(self):
        # External APK is a preserved authenticated input, never a device path.
        apk = Path(os.environ['HEALTH_REFERENCE_APK'])
        with ZipFile(apk) as z:
            exports = z.read('assets/addons/script.kodihealthcenter/khc_exports.py')
            safety = z.read('assets/addons/script.kodihealthcenter/khc_safety.py')
        self.assertEqual(hashlib.sha256(exports).hexdigest(), '392c4a41a40f4cc8c7885ec1b399ef4698a36a3691474ee921b257b862cc8dfa')
        self.assertEqual(hashlib.sha256(safety).hexdigest(), 'cf0f63eb529700393798fd45258a8d45f2bf6a54f2b12405445cac72d408aefc')
        with tempfile.TemporaryDirectory(prefix='health-source-refusal-') as tmp:
            root = Path(tmp)
            (root / 'khc_safety.py').write_bytes(safety)
            (root / 'khc_exports.py').write_bytes(exports)
            module = load(root / 'khc_safety.py', 'reference_khc_safety')
            with patch.dict(sys.modules, {'khc_safety': module}):
                exporter = load(root / 'khc_exports.py', 'reference_khc_exports')
            source, database = root / 'addon.py', root / 'unreadable.db'
            source.write_bytes(b'# source fixture\n')
            database.write_bytes(b'non-SQLite fixture; not a real database')
            originals = {p: p.read_bytes() for p in (source, database)}
            with patch.object(module.sqlite3, 'connect', side_effect=AssertionError('No SQLite open authorized')) as connect:
                with self.assertRaisesRegex(RuntimeError, '^Database has no readable SQLite header; raw fallback refused$'):
                    exporter.export_entries(str(root / 'out.zip'),
                        [(str(p), 'plugin.video.umbrella/' + p.name) for p in originals],
                        {'includes_saved_data': False}, 'KHC_ADDON_EXPORT_MANIFEST.json')
                connect.assert_not_called()
            self.assertEqual({p: p.read_bytes() for p in originals}, originals)
            self.assertFalse((root / 'out.zip').exists())
            self.assertFalse(list(root.glob('*.partial')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
