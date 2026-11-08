"""Selected read-only collector checks; no Kodi, account, database or app test."""
import builtins
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ADDON = HERE / 'addon/script.infinity.readonlyinventory'
spec = importlib.util.spec_from_file_location('readonly_collector', ADDON / 'collector.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
PINS = json.loads((ADDON / 'resources/identity-pins.json').read_text())
BASE = Path('/workspace/scratch/compressed-signed464/Infinity-2103464-Combined-Original-Signer.apk')
DEVICE = Path('/workspace/scratch/fold-source-audit/installed')


class CollectorChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='infinity-identity-check-')
        self.root = Path(self.temp.name)
        for aid in (collector.CC, collector.TRAKT):
            shutil.copytree(DEVICE / aid, self.root / aid)
        with ZipFile(BASE) as z:
            for name in PINS['allowed_module_files']:
                target = self.root / name
                if target.exists() or name.endswith('native_search_compatibility.py'):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read('assets/addons/' + name))
        self.versions = dict(zip(collector.OWNED, ('0.3.5.62', '0.2.8', '0.1.23', '1.0.21')))
        self.versions[collector.TRAKT] = '1.2.8'

    def tearDown(self):
        self.temp.cleanup()

    def info(self, aid):
        return dict(id=aid, version=self.versions[aid], path=str(self.root / aid))

    def hashes(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file() and not p.is_symlink()}

    def test_exact_active_sources_and_no_database_or_account_reads(self):
        forbidden = self.root / collector.TRAKT / 'unexpected.db'
        forbidden.write_bytes(b'Not a SQLite file; must never be opened')
        account = self.root / collector.TRAKT / 'userdata/settings.xml'
        account.parent.mkdir();account.write_bytes(b'PRIVATE ACCOUNT SENTINEL')
        before = self.hashes()
        real_open = builtins.open
        opened = []

        def read_only(path, mode='r', *args, **kwargs):
            path = Path(path)
            self.assertFalse(any(c in mode for c in 'wax+'), mode)
            self.assertNotEqual(path, forbidden)
            self.assertNotEqual(path, account)
            opened.append(path)
            return real_open(path, mode, *args, **kwargs)

        with patch('builtins.open', read_only):
            result = collector.collect(self.info, PINS)
        self.assertEqual(result['command_center']['known_verified_manifest_signature_reference'], '0.3.5.62')
        self.assertTrue(result['command_center']['all_declared_files_match'])
        self.assertEqual(len(result['command_center']['files']), 78)
        self.assertEqual(result['command_center']['additional_unlisted_known_sources'][collector.CC+'/native_search_compatibility.py']['status'], 'MATCH')
        self.assertTrue(result['trakt']['all_reference_files_match'])
        self.assertEqual(len(result['trakt']['files']), 145)
        self.assertIn('unexpected.db', result['trakt']['unexpected_files'])
        self.assertFalse(result['trakt']['complete_known_tree_match'])
        self.assertEqual(before, self.hashes())
        self.assertEqual(result['apk']['status'], 'APK_UNREADABLE')
        self.assertNotIn('sha256', result['apk'])

    def test_permission_denied_APK_is_explicit_without_hash(self):
        real_open = builtins.open
        blocked = self.root / 'blocked.apk'

        def denied(path, *args, **kwargs):
            if str(path) == str(blocked):
                raise PermissionError('Android denied APK read')
            return real_open(path, *args, **kwargs)

        with patch('builtins.open', denied):
            result = collector.apk_identity(str(blocked), PINS)
        self.assertEqual(result['status'], 'APK_UNREADABLE')
        self.assertIn('PermissionError', result['limitation'])
        self.assertNotIn('sha256', result)
        self.assertNotIn('known_verified_APK_reference', result)

    def test_unknown_manifest_path_refused_and_mismatch_visible(self):
        p = self.root / collector.CC / 'provider_inventory.py'
        p.write_bytes(p.read_bytes() + b'\n# unknown installed generation\n')
        manifest = self.root / collector.CC / 'INFINITY-MODULES.v1'
        manifest.write_bytes(manifest.read_bytes() + b'file\t' + b'a'*64 + b'\tscript.infinity.commandcenter/../userdata/settings.xml\n')
        before = self.hashes()
        result = collector.module_inventory(self.info, PINS)
        self.assertIsNone(result['known_verified_manifest_signature_reference'])
        self.assertEqual(result['files'][collector.CC+'/provider_inventory.py']['status'], 'MISMATCH')
        self.assertEqual(result['files'][collector.CC+'/../userdata/settings.xml']['status'], 'UNREADABLE_OR_REFUSED')
        self.assertFalse(result['all_declared_files_match'])
        self.assertEqual(before, self.hashes())

    def test_symlink_escape_refused(self):
        source = self.root / collector.TRAKT / 'resources/lib/tmdbhelper_sync_trakt/api/token.py'
        source.unlink();source.symlink_to(self.root / collector.CC / 'provider_inventory.py')
        result = collector.trakt_inventory(self.info, PINS)
        self.assertEqual(result['files']['resources/lib/tmdbhelper_sync_trakt/api/token.py']['status'], 'UNREADABLE_OR_REFUSED')
        self.assertFalse(result['complete_known_tree_match'])

    def test_active_source_in_Kodi_APK_cache_allowed(self):
        target = self.root / 'cache/apk/assets/addons' / collector.TRAKT
        target.parent.mkdir(parents=True)
        shutil.copytree(self.root / collector.TRAKT, target)

        def cached(aid):
            value = self.info(aid)
            if aid == collector.TRAKT:
                value['path'] = str(target)
            return value

        result = collector.trakt_inventory(cached, PINS)
        self.assertTrue(result['complete_known_tree_match'])
        self.assertEqual(result['identity']['path'], str(target))

    def test_unknown_active_version_hashes_collected_without_reference_claim(self):
        self.versions[collector.TRAKT] = '99.0.0'
        result = collector.trakt_inventory(self.info, PINS)
        self.assertFalse(result['all_reference_files_match'])
        self.assertEqual({r['status'] for r in result['files'].values()}, {'UNKNOWN_GENERATION_HASH_COLLECTED'})

    def test_real_APK_identity_and_no_assumed_hash(self):
        result = collector.apk_identity(str(BASE), PINS)
        self.assertEqual(result['sha256'], PINS['apks']['2103464']['sha256'])
        self.assertEqual(result['manifest']['package'], 'com.projectinfinity.kodi')
        self.assertEqual(result['manifest']['versionCode'], 2103464)
        self.assertEqual(result['known_verified_APK_reference'], '2103464')
        self.assertFalse(result['signature_verified_on_device'])

    def test_other_signed_manifest_versions_parse_actual_values(self):
        for version in (2103466, 2103467):
            path = Path('/workspace/scratch/three-signed') / str(version) / ('Infinity-'+str(version)+'-Combined-Original-Signer.apk')
            with ZipFile(path) as z:
                result = collector.manifest_identity(z.read('AndroidManifest.xml'))
                self.assertEqual(result['versionCode'], version)

    def test_report_writer_creates_new_file_and_preserves_existing_file(self):
        modules = {'xbmc': types.SimpleNamespace(), 'xbmcaddon': types.SimpleNamespace(),
                   'xbmcgui': types.SimpleNamespace(), 'xbmcvfs': types.SimpleNamespace(exists=lambda p: Path(p).exists()),
                   'collector': collector}
        spec = importlib.util.spec_from_file_location('readonly_manual_entry', ADDON / 'default.py')
        entry = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', modules):
            spec.loader.exec_module(entry)
        destination = Path(entry.write_new(str(self.root), 'new-report.json', b'{"safe":true}\n'))
        self.assertEqual(destination.read_bytes(), b'{"safe":true}\n')
        with self.assertRaises(OSError):
            entry.write_new(str(self.root), 'new-report.json', b'overwrite refused')
        self.assertEqual(destination.read_bytes(), b'{"safe":true}\n')


if __name__ == '__main__':
    unittest.main()
