"""Adversarial guards for the one explicit theme-preview fixture adaptation."""
from pathlib import Path
import argparse
import importlib.util
import json
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('theme_fixture_adapter', HERE / 'theme-fixture-adapter.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
FIXTURE = None


class ThemeFixtureAdapterGuards(unittest.TestCase):
    def setUp(self):
        self.original = FIXTURE.read_text()

    def test_only_reviewed_workflow_inserted_and_historical_bytes_untouched(self):
        before = FIXTURE.read_bytes()
        adapted, status = adapter.adapt_text(self.original)
        self.assertEqual('adapted', status)
        self.assertEqual(self.original, adapted.replace(adapter.BEFORE, '', 1).replace(adapter.AFTER, '', 1))
        self.assertEqual(before, FIXTURE.read_bytes())
        self.assertEqual(adapter.SOURCE_SHA256, adapter.digest(self.original))

    def test_all_case_identities_and_every_original_assertion_remain(self):
        adapted, _ = adapter.adapt_text(self.original)
        self.assertEqual(adapter.case_names(self.original), adapter.case_names(adapted))
        self.assertEqual(1, adapted.count(adapter.ORIGINAL_ASSERTIONS))
        # Removing only the additions restores every old assertion byte-for-byte.
        self.assertEqual(self.original, adapted.replace(adapter.BEFORE, '', 1).replace(adapter.AFTER, '', 1))

    def test_prompt_and_uncommitted_preview_checked_before_real_keep(self):
        adapted, _ = adapter.adapt_text(self.original)
        position = adapted.index(adapter.BEFORE)
        keep = adapted.index('keep.performClick()', position)
        for check in ['previewRenderer.effective().id', 'previewRenderer.effective().directory',
                      'Preview cannot commit before Keep', 'confirmation.isShowing()',
                      'Keep Theme', 'keep.isEnabled()', 'CobraVisualTheme.load(a).id']:
            self.assertLess(adapted.index(check, position), keep)
        self.assertLess(keep, adapted.index(adapter.ORIGINAL_ASSERTIONS))
        self.assertGreater(adapted.index(adapter.AFTER), adapted.index(adapter.ORIGINAL_ASSERTIONS))
        self.assertTrue(adapter.BEFORE.startswith('      try {\n'))
        self.assertIn('finally{CobraPresentationSafety.cancel(a,false);}', adapter.AFTER)

    def test_historical_assertion_and_case_drift_rejected(self):
        for bad in [self.original.replace('The exact installed theme must be restored', 'weakened'),
                    self.original.replace(adapter.CASE, 'renamed_case'),
                    self.original + '\n']:
            with self.assertRaisesRegex(RuntimeError, 'drift'):
                adapter.adapt_text(bad)

    def test_adapted_assertion_or_keep_drift_rejected(self):
        adapted, _ = adapter.adapt_text(self.original)
        for bad in [adapted.replace('assertTrue(keep.isEnabled())', 'assertTrue(true)'),
                    adapted.replace('keep.performClick()', 'true'),
                    adapted.replace('Theme "+id', 'Other "+id')]:
            with self.assertRaisesRegex(RuntimeError, 'drift'):
                adapter.adapt_text(bad)

    def test_repeat_adaptation_is_idempotent_and_inserted_once(self):
        adapted, _ = adapter.adapt_text(self.original)
        repeated, status = adapter.adapt_text(adapted)
        self.assertEqual('already_adapted', status)
        self.assertEqual(adapted, repeated)
        self.assertEqual(1, repeated.count(adapter.BEFORE))
        self.assertEqual(1, repeated.count(adapter.AFTER))

    def test_runner_only_rewrites_generated_copy_and_reports_exact_hashes(self):
        with tempfile.TemporaryDirectory(prefix='cobra205-theme-fixture-') as directory:
            root = Path(directory)
            generated = root / adapter.BUILD_COPY
            generated.parent.mkdir(parents=True)
            generated.write_text(self.original)
            report = root / 'evidence/theme-fixture-adaptation.json'
            first = adapter.main(root, report)
            self.assertFalse(first['historical_repository_tests_modified'])
            self.assertEqual(adapter.SOURCE_SHA256, first['input_sha256'])
            self.assertEqual(adapter.digest(generated.read_text()), first['output_sha256'])
            second = adapter.main(root, report)
            self.assertEqual('already_adapted', second['status'])
            self.assertEqual(first['output_sha256'], second['output_sha256'])
            self.assertEqual(self.original, FIXTURE.read_text())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    FIXTURE = args.fixture
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ThemeFixtureAdapterGuards))
    receipt = {'suite': '205 explicit theme-preview fixture adapter guards', 'tests': result.testsRun,
               'failures': len(result.failures), 'errors': len(result.errors),
               'passed': result.wasSuccessful(), 'physical_device_verified': False}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if result.wasSuccessful() else 1)
