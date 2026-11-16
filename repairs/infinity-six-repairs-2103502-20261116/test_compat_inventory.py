#!/usr/bin/env python3
"""Selected read-only inventory tests, exact502 preimage and reviewed overlay."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
MEMBER = 'assets/addons/script.kodihealthcenter/infinity_runtime_identity.py'
BASE_SHA = '9a87d2790f457af7965babce6fa7c45ff1c43b2dc938cc5defec64aa5442853c'
APK_SHA = 'f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28'
COMPAT = 'service.infinity.compat'
SERVICES = ('service.py', 'layout_service.py', 'theme_contract.py')


def module(raw, base):
    class Addon:
        def __init__(self, aid): self.aid = aid
        def getAddonInfo(self, key):
            return str(base / self.aid) if key == 'path' else 'fixture'
        def getSetting(self, key): return ''
    class Window:
        def __init__(self, *args): pass
        def getProperty(self, key): return ''
    for name, fields in {
        'xbmcaddon': dict(Addon=Addon),
        'xbmcvfs': dict(translatePath=lambda value: value),
        'xbmc': dict(getCondVisibility=lambda value: True),
        'xbmcgui': dict(Window=Window),
    }.items():
        stub = types.ModuleType(name); stub.__dict__.update(fields); sys.modules[name] = stub
    loaded = types.ModuleType('inventory_probe')
    exec(compile(raw, MEMBER, 'exec'), loaded.__dict__)
    # Test the inventory contract, not native module-signature verification.
    def native_unavailable(): raise RuntimeError('Native verifier not available in host probe')
    loaded._signed_inventory = native_unavailable
    return loaded


def compat_row(loaded):
    report = loaded.collect()
    assert report['module_signature']['state'] == 'UNVERIFIED'
    return next(row for row in report['addons'] if row['id'] == COMPAT)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='infinity502-inventory-')
        self.base = Path(self.tmp.name)
        self.root = self.base / COMPAT; self.root.mkdir()
        with zipfile.ZipFile(ARGS.apk) as archive:
            for name in archive.namelist():
                prefix = 'assets/addons/' + COMPAT + '/'
                if name.startswith(prefix) and not name.endswith('/'):
                    destination = self.root / name[len(prefix):]
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(name))
        self.loaded = module(CANDIDATE, self.base)

    def tearDown(self): self.tmp.cleanup()

    def manifest(self, libraries, aid=COMPAT):
        from xml.sax.saxutils import quoteattr
        content = '<addon id=' + quoteattr(aid) + '><requires/>'
        content += ''.join('<extension point="xbmc.service" library=' + quoteattr(leaf) +
                           ' start="startup"/>' for leaf in libraries)
        (self.root / 'addon.xml').write_text(content + '</addon>')

    def test_exact502_declared_services_and_source_hashes(self):
        before = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob('*') if p.is_file()}
        row = compat_row(self.loaded)
        self.assertEqual([d['library'] for d in row['declared_services']], list(SERVICES))
        for name in SERVICES:
            self.assertEqual(row['files'][name]['sha256'], before[name])
        self.assertNotIn('runtime_service.py', row['files'])
        after = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertTrue(all(d['state'] == 'DECLARED_NOT_EXECUTION_PROOF'
                            for d in row['declared_services']))

    def test_alternate_installed_entrypoint_without_downgrade(self):
        self.manifest(['runtime_service.py'])
        (self.root / 'runtime_service.py').write_text('raise AssertionError("must not execute")\n')
        row = compat_row(self.loaded)
        self.assertIn('sha256', row['files']['runtime_service.py'])
        self.assertNotIn('service.py', row['files'])

    def test_missing_declared_service_stays_visible(self):
        self.manifest(['absent.py'])
        row = compat_row(self.loaded)
        self.assertEqual(row['files']['absent.py']['state'], 'MISSING_OR_UNVERIFIED')

    def test_safe_nested_library(self):
        self.manifest(['resources/entry.py'])
        (self.root / 'resources/entry.py').write_text('not executed\n')
        self.assertIn('sha256', compat_row(self.loaded)['files']['resources/entry.py'])

    def test_unsafe_library_declarations_are_visible_and_unread(self):
        for leaf in ('../secret.py', '/secret.py', 'resources/../secret.py',
                     'resources//entry.py', 'C:\\secret.py', '', './service.py', 'entry.so'):
            with self.subTest(leaf=leaf):
                self.manifest([leaf])
                row = compat_row(self.loaded)
                self.assertEqual(row['declared_services'][0]['state'], 'REJECTED_UNSAFE_LIBRARY')
                self.assertNotIn(leaf, row['files'])

    def test_symlink_library_is_rejected_without_read(self):
        outside = self.base / 'private.py'; outside.write_text('private fixture')
        (self.root / 'link.py').symlink_to(outside)
        self.manifest(['link.py'])
        row = compat_row(self.loaded)
        self.assertEqual(row['declared_services'][0]['state'], 'REJECTED_UNSAFE_LIBRARY')
        self.assertNotIn('link.py', row['files'])

    def test_symlink_parent_is_rejected(self):
        (self.root / 'alias').symlink_to(self.root / 'resources', target_is_directory=True)
        self.manifest(['alias/entry.py'])
        self.assertEqual(compat_row(self.loaded)['declared_services'][0]['state'],
                         'REJECTED_UNSAFE_LIBRARY')

    def test_manifest_owner_mismatch_remains_unverified(self):
        self.manifest(['service.py'], aid='unrelated.addon')
        self.assertEqual(compat_row(self.loaded)['state'], 'UNVERIFIED')

    def test_dtd_entity_and_utf16_rejected(self):
        for raw in (b'<!DOCTYPE addon><addon id="service.infinity.compat"/>',
                    b'<!DOCTYPE addon [<!ENTITY x "value">]><addon id="service.infinity.compat"/>',
                    '<!DOCTYPE addon><addon id="service.infinity.compat"/>'.encode('utf-16')):
            with self.subTest(raw=raw[:20]):
                (self.root / 'addon.xml').write_bytes(raw)
                self.assertEqual(compat_row(self.loaded)['state'], 'UNVERIFIED')

    def test_manifest_symlink_rejected(self):
        manifest = self.root / 'addon.xml'; raw = manifest.read_bytes(); manifest.unlink()
        outside = self.base / 'manifest.xml'; outside.write_bytes(raw); manifest.symlink_to(outside)
        self.assertEqual(compat_row(self.loaded)['state'], 'UNVERIFIED')

    def test_manifest_size_limit(self):
        (self.root / 'addon.xml').write_bytes(b' ' * 262145)
        self.assertEqual(compat_row(self.loaded)['state'], 'UNVERIFIED')

    def test_existing_bootstrap_verification_unchanged(self):
        def function(raw, name):
            return ast.dump(next(n for n in ast.parse(raw).body
                                 if isinstance(n, ast.FunctionDef) and n.name == name))
        self.assertEqual(function(BASE, '_signed_inventory'), function(CANDIDATE, '_signed_inventory'))
        self.assertEqual(function(BASE, '_root'), function(CANDIDATE, '_root'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True); ARGS = parser.parse_args()
    with ARGS.apk.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == APK_SHA
    with zipfile.ZipFile(ARGS.apk) as archive: BASE = archive.read(MEMBER)
    assert hashlib.sha256(BASE).hexdigest() == BASE_SHA
    CANDIDATE = (HERE / 'overlay/script.kodihealthcenter/infinity_runtime_identity.py').read_bytes()
    # Baseline reproduction uses the same actual APK compat files as candidate.
    baseline = InventoryTests(); baseline.setUp()
    try:
        row = compat_row(module(BASE, baseline.base))
        reproduced = row['files']['runtime_service.py']['state'] == 'MISSING_OR_UNVERIFIED' and all(
            name not in row['files'] for name in SERVICES)
        assert reproduced
    finally: baseline.tearDown()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(InventoryTests))
    receipt = dict(baseline='EXACT_SIGNED_2103502', baseline_defect_reproduced=reproduced,
        source_before_sha256=BASE_SHA, source_after_sha256=hashlib.sha256(CANDIDATE).hexdigest(),
        cases=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        status='PASS' if result.wasSuccessful() else 'FAIL', owner_data='NOT_READ_OR_MODIFIED',
        scope='DECLARED_ENTRYPOINT_INVENTORY_ONLY', native_signature_test='NOT_RUN',
        Empty_Shell_cause='NOT_ESTABLISHED', Android='NOT_RUN')
    ARGS.out.write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
