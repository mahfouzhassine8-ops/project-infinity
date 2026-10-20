"""Host tests for evidence validation; these are explicitly NOT ART execution."""
import copy
import json
import unittest
import run

PINS = {'addon.xml': 'a' * 64, 'checkpoint_runtime.py': 'b' * 64,
        **{'file%d.py' % n: 'c' * 64 for n in range(11)}}


def record():
    names = run.expected_cases(PINS)
    value = dict(variant='candidate', api=37, android_release='17', passed=True,
                 cases=names, **{key: False for key in run.FALSE_FLAGS})
    return value


def output(value, names=None):
    if names is None: names = value['cases']
    return '\n'.join('ART_CASE_PASS ' + name for name in names) + '\nART_RESULT ' + json.dumps(value) + '\n'


class EvidenceGuards(unittest.TestCase):
    def test_01_complete_case_matrix(self):
        self.assertEqual(len(run.expected_cases(PINS)), 37)
        self.assertTrue(run.parse_result(output(record()), 'candidate', run.expected_cases(PINS), 37)['passed'])

    def test_02_missing_pin_rejected(self):
        with self.assertRaises(ValueError): run.expected_cases(dict(list(PINS.items())[:-1]))

    def test_03_unsafe_pin_paths_rejected(self):
        for bad in ('../addon.xml', '/addon.xml', 'a//b', 'a/./b', 'a\\b'):
            pins = dict(PINS); pins[bad] = pins.pop('addon.xml')
            with self.subTest(path=bad), self.assertRaises(ValueError): run.expected_cases(pins)

    def test_04_missing_duplicate_or_reordered_cases_rejected(self):
        cases = run.expected_cases(PINS)
        for replacement in (cases[:-1], cases + [cases[0]], list(reversed(cases))):
            value = record(); value['cases'] = replacement
            with self.subTest(cases=replacement[:2]), self.assertRaises(ValueError):
                run.parse_result(output(value), 'candidate', cases, 37)

    def test_05_claimed_summary_without_executed_rows_rejected(self):
        with self.assertRaises(ValueError):
            run.parse_result(output(record(), []), 'candidate', run.expected_cases(PINS), 37)

    def test_06_wrong_platform_or_variant_rejected(self):
        for key, replacement in [('api', 34), ('android_release', '14'), ('variant', 'baseline')]:
            value = record(); value[key] = replacement
            with self.subTest(field=key), self.assertRaises(ValueError):
                run.parse_result(output(value), 'candidate', run.expected_cases(PINS), 37)

    def test_07_scope_overclaims_rejected(self):
        for key in run.FALSE_FLAGS:
            value = record(); value[key] = True
            with self.subTest(field=key), self.assertRaises(ValueError):
                run.parse_result(output(value), 'candidate', run.expected_cases(PINS), 37)

    def test_08_duplicate_results_rejected(self):
        with self.assertRaises(ValueError):
            run.parse_result(output(record()) * 2, 'candidate', run.expected_cases(PINS), 37)

    def test_09_failed_result_cannot_be_green(self):
        value = record(); value['passed'] = False
        with self.assertRaises(ValueError): run.parse_result(output(value), 'candidate', run.expected_cases(PINS), 37)

    def test_10_original_apk_never_accepted_as_candidate_component(self):
        with self.assertRaises(ValueError):
            run.component_proof({'source_commit': 'wrong'}, None)


if __name__ == '__main__': unittest.main(verbosity=2)
