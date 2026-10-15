"""Separate adversarial host checks for the narrowly scoped fixture adapter."""
from pathlib import Path
import argparse
import json
import tempfile
import unittest
import host_timeshift_adapter as adapter

FIXTURE = None


class FixtureAdapterGuards(unittest.TestCase):
    def setUp(self):
        self.original = FIXTURE.read_text()

    def test_only_one_noop_collaborator_added(self):
        adapted = adapter.adapt(self.original)
        self.assertEqual(1, adapted.count(adapter.ADDED))
        self.assertEqual(self.original, adapted.replace(adapter.ADDED, '', 1))

    def test_all_fourteen_case_identities_unchanged(self):
        self.assertEqual(14, len(adapter.cases(self.original)))
        self.assertEqual(adapter.cases(self.original), adapter.cases(adapter.adapt(self.original)))

    def test_assertions_and_main_remain_byte_identical(self):
        marker = ' private static void check(boolean value,String message)'
        adapted = adapter.adapt(self.original)
        self.assertEqual(self.original[self.original.index(marker):], adapted[adapted.index(marker):])

    def test_production_extraction_is_unchanged(self):
        self.assertEqual(self.original.split(" j='''", 1)[0],
                         adapter.adapt(self.original).split(" j='''", 1)[0])

    def test_assertion_drift_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'fixture drift'):
            adapter.adapt(self.original.replace('progress==500', 'progress==499'))

    def test_extra_collaborator_or_repeat_rejected(self):
        for changed in (adapter.adapt(self.original), self.original.replace(adapter.ANCHOR, adapter.ANCHOR * 2)):
            with self.assertRaisesRegex(RuntimeError, 'fixture drift'):
                adapter.adapt(changed)

    def test_pinned_extractor_drift_rejected(self):
        with tempfile.TemporaryDirectory(prefix='cobra205-host-adapter-') as directory:
            root = Path(directory)
            (root / 'tests').mkdir()
            fixture = root / 'tests/host_timeshift.py'
            fixture.write_text(self.original)
            (root / 'apply_timeshift.py').write_text('# unreviewed extractor\n')
            with self.assertRaisesRegex(RuntimeError, 'extractor drift'):
                adapter.read_fixture(fixture)

    def test_reading_adapter_leaves_historical_bytes_unchanged(self):
        before = FIXTURE.read_bytes()
        original, adapted = adapter.read_fixture(FIXTURE)
        self.assertEqual(before, original)
        self.assertEqual(before, FIXTURE.read_bytes())
        self.assertEqual(adapter.FIXTURE_SHA256, adapter.digest(before))
        self.assertNotEqual(before.decode(), adapted)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True,
                        help='Pinned 199 fixture after inherited 201/202 adapters, as used by CI')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    FIXTURE = args.fixture
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FixtureAdapterGuards))
    receipt = {'suite': '205 inherited host-fixture adapter guards', 'tests': result.testsRun,
               'failures': len(result.failures), 'errors': len(result.errors),
               'passed': result.wasSuccessful(), 'physical_device_verified': False}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if result.wasSuccessful() else 1)
