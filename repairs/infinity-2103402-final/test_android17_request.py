import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('push_request', ROOT / 'android17/push_request.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((ROOT / 'android17/REQUEST.json').read_text())
        self.head = 'a' * 40
        self.event = dict(ref=guard.BRANCH, after=self.head,
                          repository={'full_name': 'mahfouzhassine8-ops/project-infinity'})

    def test_reviewed_request_selects_one_existing_baseline_case(self):
        result = guard.validate(self.request, self.event, self.head, [guard.REQUEST])
        self.assertEqual(result['SELECTED_CASE'], 'final-search-all-enter')
        self.assertEqual(result['CANDIDATE_BUILD'], '40089463702')

    def test_unreviewed_build_scope_event_and_source_are_rejected(self):
        for field, value in (('candidate_build', 40089463703), ('case', 'final-continue'),
                             ('baseline_commit', 'b' * 40), ('baseline_apk_sha256', '0' * 64),
                             ('authorization', ''), ('request_id', 'automatic-repeat')):
            request = dict(self.request, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                guard.validate(request, self.event, self.head, [guard.REQUEST])
        for event in (dict(self.event, ref='refs/heads/main'), dict(self.event, deleted=True),
                      dict(self.event, after='c' * 40), dict(self.event, repository={'full_name': 'other/repo'})):
            with self.assertRaises(ValueError):
                guard.validate(self.request, event, self.head, [guard.REQUEST])
        for changed in ([], ['README.md'], [guard.REQUEST, 'unrelated/runtime.cpp']):
            with self.assertRaises(ValueError):
                guard.validate(self.request, self.event, self.head, changed)

    def test_existing_manual_runtime_and_integrity_guards_remain(self):
        text = (ROOT.parents[1] / '.github/workflows/infinity-saved-navigation-android.yml').read_text()
        for required in ('workflow_dispatch:', "paths: ['" + guard.REQUEST + "']",
                         'delivery92.verify_signature', "run['head_sha']==r['source_commit']",
                         'sha256sum -c SHA256SUMS', "api-level: '37.0'", 'SELECTED_CASE',
                         '--authorization "$AUTHORIZED_SCOPE"', 'android_feature_probe.py',
                         "request['baseline_apk_sha256']", 'cancel-in-progress: false'):
            self.assertIn(required, text)
        self.assertNotIn('continue-on-error', text)
        self.assertNotIn('needs:', text)
        self.assertNotIn('workflow_run:', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
