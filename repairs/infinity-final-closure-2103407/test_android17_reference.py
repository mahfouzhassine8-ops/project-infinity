import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import android17_request as guard
import prepare_signed407_fixture as fixture


ROOT = Path(__file__).parent


class ReferenceRoutingTests(unittest.TestCase):
    def test_only_exact_branch_request_source_and_signed_reference_are_selected(self):
        head = 'a' * 40
        event = dict(ref=guard.BRANCH, after=head,
                     repository={'full_name':'mahfouzhassine8-ops/project-infinity'})
        output = guard.validate(guard.EXPECTED, event, head, [guard.REQUEST])
        self.assertEqual(output['CANDIDATE_BUILD'], '40230842944')
        self.assertEqual(output['SELECTED_CASE'], 'final-search-all-enter')
        for field, value in (('candidate_build',1), ('selected_case','final-continue'),
                             ('baseline_apk_sha256','0'*64), ('authorization',''),
                             ('baseline_commit','b'*40)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                guard.validate(dict(guard.EXPECTED, **{field:value}), event, head, [guard.REQUEST])
        for bad in (dict(event, ref='refs/heads/main'), dict(event, after='b'*40), dict(event, deleted=True)):
            with self.assertRaises(ValueError):
                guard.validate(guard.EXPECTED, bad, head, [guard.REQUEST])
        for changes in ([], [guard.REQUEST,'unrelated/source.cpp']):
            with self.assertRaises(ValueError):
                guard.validate(guard.EXPECTED, event, head, changes)

    def test_existing_manual_provider_signature_source_and_api37_gates_are_retained(self):
        workflow = (ROOT.parents[1]/'.github/workflows/infinity-saved-navigation-android.yml').read_text()
        for required in ('workflow_dispatch:', 'delivery92.verify_signature', 'sha256sum -c SHA256SUMS',
                         "run['head_sha']==r['source_commit']", "run['conclusion']=='success'",
                         "api-level: '37.0'", 'android37_gate.py', 'android_feature_probe.py',
                         'source_ref:', 'cancel-in-progress: false', guard.REQUEST,
                         'repairs/infinity-2103402-final/android17/push_request.py'):
            self.assertIn(required, workflow)
        self.assertNotIn('continue-on-error', workflow)
        self.assertNotIn('needs:', workflow)

    def test_metadata_adapter_uses_verified_bytes_and_refuses_existing_or_modified_input(self):
        baseline = os.environ.get('INFINITY_SIGNED407_ARTIFACT')
        if baseline is None:
            # CI downloads the same immutable artifact immediately before this
            # selected test. It is never a substitute for an APK/signature test.
            baseline = str(ROOT.parents[1]/'signed407')
        baseline = Path(baseline)
        self.assertTrue(baseline.is_dir(), 'Exact signed407 fixture directory required')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root/'release'
            nested.mkdir()
            originals = [p for p in baseline.rglob('*') if p.is_file() and
                         (p.suffix=='.apk' or p.name in fixture.EXPECTED_COMPONENTS)]
            self.assertEqual(len(originals),5)
            for source in originals:
                os.link(source,nested/source.name)
            with mock.patch.object(fixture,'BASELINE_SHA','0'*64), self.assertRaises(ValueError):
                fixture.prepare(root)
            receipt = fixture.prepare(root)
            self.assertFalse(receipt['apk_bytes_changed'])
            self.assertFalse(receipt['release_accepted'])
            self.assertEqual(receipt['matching_component_versions']['script.infinity.commandcenter'],'0.3.5.39')
            for source in originals:
                self.assertEqual(fixture.digest(source),fixture.digest(root/source.name))
            with self.assertRaises(ValueError):
                fixture.prepare(root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
