"""G0 negative controls: partial exports and tampered bytes must never pass."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import source_gate as gate


class SourceGateTests(unittest.TestCase):
    def test_compiled_parent_manifests_and_recovered_native_preimages(self):
        native, parent = gate.compiled_manifest('native')
        gate.compiled_manifest('android')
        self.assertEqual(parent['compiled_parent_commit'],
                         '2515c1a281abf9e57cfdbf570244c69f751a1437')
        recovered = dict(parent['recovered_modified_native'],
                         **parent['recovered_additional_native'])
        self.assertEqual(len(recovered), 9)
        for name, digest in recovered.items():
            self.assertEqual(native[name], digest)
            self.assertEqual(gate.sha(gate.HERE / 'recovered-native' / name), digest)

    def test_partial_export_reports_missing_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'a.cpp').write_bytes(b'exact')
            expected = {'a.cpp': hashlib.sha256(b'exact').hexdigest(),
                        'missing.png': hashlib.sha256(b'locked asset').hexdigest()}
            self.assertEqual(gate.inspect(expected, root), ['missing.png'])

    def test_recovery_selects_exact_export_and_rejects_wrong_variant(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wrong, exact, output = root / 'wrong', root / 'exact', root / 'output'
            wrong.mkdir(); exact.mkdir()
            (wrong / 'file.cpp').write_bytes(b'upstream variant')
            (exact / 'file.cpp').write_bytes(b'compiled infinity variant')
            expected = {'file.cpp': hashlib.sha256(b'compiled infinity variant').hexdigest()}
            self.assertEqual(gate.recover(expected, [wrong, exact], output), [])
            self.assertEqual((output / 'file.cpp').read_bytes(), b'compiled infinity variant')
            (output / 'file.cpp').write_bytes(b'one byte of drift')
            self.assertEqual(gate.inspect(expected, output), ['file.cpp'])

    def test_no_overwrite_of_source_or_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                gate.recover({}, [root], root / 'inside-source')
            with self.assertRaises(ValueError):
                gate.recover({}, [], root)

    def test_absolute_parent_and_symlink_escape_are_rejected(self):
        for name in ('/etc/passwd', '../escape', 'a/../../escape'):
            with self.assertRaises(ValueError):
                gate.relative_path(name)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'; source.mkdir()
            outside = root / 'outside'; outside.write_bytes(b'exact')
            (source / 'escape').symlink_to(outside)
            expected = {'escape': hashlib.sha256(b'exact').hexdigest()}
            self.assertEqual(gate.select_exact(expected, [source])[1], ['escape'])
            self.assertEqual(gate.inspect(expected, source), ['escape'])


if __name__ == '__main__':
    unittest.main()
