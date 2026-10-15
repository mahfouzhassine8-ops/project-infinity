import io
import json
import unittest
import zipfile
from unittest import mock
import test_verify_2103362 as f
import verify_2103367 as v


def previous_asset(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        manifest = json.loads(z.read('manifest.json'))
    files = {'manifest.json': b''}; rows = []
    for row in manifest['files']:
        if row['path'] in ('context.py', 'addon.xml'): continue
        rows.append(dict(path=row['path'], before=row['before'], previous=row['previous'], after=row['baseline']))
        files['payload/' + row['path']] = b'protected baseline fixture'
    manifest['files'] = rows; files['manifest.json'] = json.dumps(manifest).encode()
    with f.archive(files) as archive: return archive.fp.getvalue()


class Tests(unittest.TestCase):
    def fixture(self):
        old = {'AndroidManifest.xml': b'old', 'classes.dex': b'classes', 'lib/arm64-v8a/libkodi.so': b'old',
               'assets/skin.xml': b'protected skin', 'assets/health.py': b'protected health'}
        new = dict(old, **{'AndroidManifest.xml': b'new', 'lib/arm64-v8a/libkodi.so': b'new'})
        for name, payload in v.asset_bytes().items(): old[name] = previous_asset(payload); new[name] = payload
        return old, new
    def compare(self, old, new, contracts=None):
        contracts = contracts or [({'jni'}, {'old'}), ({'jni'}, {'old'} | v.ADDED)]
        with f.archive(old) as a, f.archive(new) as b, mock.patch.object(v, 'dex_contract', side_effect=contracts):
            return v.compare(a, b)
    def test_exact_current_production_assets(self):
        old, new = self.fixture(); result = self.compare(old, new)
        self.assertTrue(result['jni_unchanged'] and result['skin_payload_unchanged'] and result['health_center_payload_unchanged'])
        self.assertEqual(result['protected_entries_byte_identical'], 2)
    def test_unrelated_payload_and_inventory_refused(self):
        for name in ('assets/skin.xml', 'assets/health.py', 'assets/unknown'):
            old, new = self.fixture(); new[name] = b'changed'
            with self.assertRaises(RuntimeError): self.compare(old, new)
    def test_nonreviewed_asset_and_false_preimage_refused(self):
        old, new = self.fixture(); name = next(iter(v.ASSETS)); new[name] += b'extra'
        with self.assertRaises(RuntimeError): self.compare(old, new)
        old, new = self.fixture()
        with zipfile.ZipFile(io.BytesIO(old[name])) as z: files = {p: z.read(p) for p in z.namelist()}
        manifest = json.loads(files['manifest.json']); manifest['files'][0]['after'] = '0' * 64
        files['manifest.json'] = json.dumps(manifest).encode()
        with f.archive(files) as z: old[name] = z.fp.getvalue()
        with self.assertRaises(RuntimeError): self.compare(old, new)
    def test_protected_jni_and_classes(self):
        for contracts in ([({'jni'}, {'old'}), ({'other'}, {'old'})],
                          [({'jni'}, {'old'}), ({'jni'}, {'old', 'Lunknown/Class;'})],
                          [({'jni'}, {'old'}), ({'jni'}, set())]):
            old, new = self.fixture()
            with self.assertRaises(RuntimeError): self.compare(old, new, contracts)


if __name__ == '__main__': unittest.main()
