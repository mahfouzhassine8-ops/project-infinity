"""Only new post-sign test-tool refusal controls; never Android evidence."""
import ast
from collections import Counter
import copy
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent


def selected(namespace):
    names = {'require', 'check_pair', 'check_installed_observation', 'reserve_start', 'new_package_crash',
             'compare_inventory', 'outcome', 'failure_status', 'result_statuses', 'final_liveness', 'initialize_report'}
    tree = ast.parse((HERE / 'verify_tracking_install.py').read_text())
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names: raise RuntimeError('Exact selected source required')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'verify_tracking_install.py', 'exec', optimize=1), namespace)


class InstallGuards(unittest.TestCase):
    def setUp(self):
        self.ns = dict(re=re, Counter=Counter, VERSIONS=(2103469, 2103474, 2103475),
            DECLARED=('guisettings.xml', 'sources.xml', 'addon_data/skin.infinity.diggz/settings.xml',
                      'addon_data/script.infinity.commandcenter/continue-watching.json'),
            base=SimpleNamespace(APK_SHA='a' * 64, CERT='b' * 64, PACKAGE='com.projectinfinity.kodi'))
        selected(self.ns)

    def rows(self):
        return [dict(role=role, versionCode=version, filename='official-' + str(version) + '.apk', sha256=('a' if index == 0 else str(index)) * 64,
            size=100, certificate_sha256='b' * 64, module_sources={str(i): 'c' * 64 for i in range(80)}, manifest_sha256='d' * 64)
            for index, (role, version) in enumerate(zip(('baseline', 'candidate', 'recovery'), self.ns['VERSIONS']))]

    def test_fixed_chain_original_cert_and_full80_expectations(self):
        check, rows = self.ns['check_pair'], self.rows()
        check(rows)
        for field, value in (('versionCode', 2103468), ('certificate_sha256', 'e' * 64), ('module_sources', {}), ('filename', '../escape.apk')):
            wrong = copy.deepcopy(rows); wrong[1][field] = value
            with self.assertRaises(RuntimeError): check(wrong)
        wrong = copy.deepcopy(rows); wrong[0]['sha256'] = 'f' * 64
        with self.assertRaisesRegex(RuntimeError, 'PROTECTED_ORIGINAL69'): check(wrong)
        with self.assertRaises(RuntimeError): check([rows[0], rows[2], rows[1]])

    def test_installed_identity_is_parameter_bound_and_uid_cannot_change(self):
        check, expected = self.ns['check_installed_observation'], self.rows()[1]
        observed = dict(versionCode=2103474, sha256=expected['sha256'], uid=10123, path='/data/app/example/base.apk')
        self.assertEqual(check(observed, expected, 10123)['status'], 'PASS_ACTUAL_PACKAGEMANAGER_IDENTITY')
        for field, value in (('versionCode', 2103469), ('sha256', 'a' * 64), ('uid', 10124)):
            with self.assertRaises(RuntimeError): check(dict(observed, **{field: value}), expected, 10123)
        self.assertEqual(self.ns['base'].APK_SHA, 'a' * 64)

    def inventory(self):
        return {name: dict(exists=False, domain='NO_USER_FIXTURE_OBSERVED') for name in self.ns['DECLARED']}

    def test_absent_data_is_not_preservation_and_mutation_refuses(self):
        compare, before = self.ns['compare_inventory'], self.inventory()
        self.assertEqual(compare(before, copy.deepcopy(before))['status'], 'NOT_OBSERVED_USER_FIXTURE')
        path = 'guisettings.xml'; before[path] = dict(exists=True, domain='HARNESS_BOOTSTRAP', size=1, sha256='a' * 64)
        self.assertEqual(compare(before, copy.deepcopy(before))['status'], 'NOT_OBSERVED_USER_FIXTURE')
        path = 'addon_data/script.infinity.commandcenter/continue-watching.json'
        before[path] = dict(exists=True, domain='LEGITIMATE_UI_WATCHLIST', size=12, sha256='c' * 64)
        self.assertEqual(compare(before, copy.deepcopy(before))['status'], 'PASS_OBSERVED_USER_FIXTURE_BYTES_ONLY')
        for wrong in (dict(exists=False), dict(exists=True, size=12, sha256='d' * 64)):
            after = copy.deepcopy(before); after[path] = wrong
            with self.assertRaisesRegex(RuntimeError, 'BYTES_NOT_RETAINED'): compare(before, after)

    def test_single_start_reservation_refuses_retry_or_unknown_version(self):
        reserve, attempts = self.ns['reserve_start'], []
        reserve(attempts, 2103469); reserve(attempts, 2103474); reserve(attempts, 2103475)
        self.assertEqual(attempts, list(self.ns['VERSIONS']))
        for version in (2103469, 2103474, 2103475, 2103476):
            with self.assertRaisesRegex(RuntimeError, 'NO_RETRY'): reserve(attempts, version)
        self.assertEqual(len(attempts), 3)

    def test_new_crash_attribution_preserves_old_and_rejects_new_package_crash(self):
        parse = self.ns['new_package_crash']
        old = '100.100 1 1 F DEBUG : >>> com.projectinfinity.kodi:kodi <<<\n'
        other = '101.100 9 9 F DEBUG : >>> com.unrelated.application <<<\n'
        new = '102.100 5 5 F DEBUG : >>> com.projectinfinity.kodi:kodi <<<\n'
        self.assertEqual(parse(old, old + other, 101), [])
        self.assertEqual(parse(old, old + other + new, 101), [new.strip()])
        self.assertEqual(parse('', old, 101), [])
        # Repeated old bytes remain evidence; only a newly appended current package line is a new fatal.
        self.assertEqual(parse(old, old + old, 100), [old.strip()])
        self.assertEqual(self.ns['outcome'](RuntimeError('NEW_PHASE_PACKAGE_CRASH_NO_RETRY')), 'FAIL_NATIVE_STARTUP_OR_PROCESS')

    def test_initial_blocked_setup_has_no_fabricated_functional_pass(self):
        report = self.ns['initialize_report']()
        self.assertFalse(report['release_acceptance'])
        self.assertEqual(report['functional_recovery'], 'NOT_RUN')
        self.assertTrue(all(case['status'] == 'NOT_RUN' for phase in report['versions'].values() for case in phase.values()))
        self.assertEqual(self.ns['outcome'](TimeoutError('SDK transport timeout')), 'BLOCKED_PREREQUISITE')
        self.assertEqual(report['versions']['2103474']['runtime']['status'], 'NOT_RUN')

    def test_observed_native_failure_cannot_become_blocked_inside_optional_work(self):
        classify = self.ns['failure_status']
        for native in ('NEW_PHASE_PACKAGE_CRASH_NO_RETRY', 'NATIVE_ENGINE_DIED_OR_RESTARTED', 'NATIVE_PID_REUSED'):
            for fallback in ('BLOCKED', 'BLOCKED_FIXTURE_PREPARATION', 'BLOCKED_RUNTIME_PREREQUISITE'):
                self.assertEqual(classify(RuntimeError(native), fallback), 'FAIL_NATIVE_STARTUP_OR_PROCESS')
        self.assertEqual(classify(TimeoutError('SDK observation timeout'), 'BLOCKED_OBSERVER'), 'BLOCKED_OBSERVER')
        self.assertEqual(classify(RuntimeError('Observed functional mismatch'), 'FAIL'), 'FAIL')

    def test_expired_work_budget_cannot_mask_terminal_native_crash(self):
        observed = []
        class PhaseDevice:
            operation_deadline = -1
            def alive(device):
                observed.append(device.operation_deadline)
                if device.operation_deadline is not None: raise TimeoutError('Expired work budget')
                raise RuntimeError('NEW_PHASE_PACKAGE_CRASH_NO_RETRY')
        with self.assertRaisesRegex(RuntimeError, 'NEW_PHASE_PACKAGE_CRASH_NO_RETRY'):
            self.ns['final_liveness'](PhaseDevice())
        self.assertEqual(observed, [None])
        self.assertEqual(self.ns['outcome'](RuntimeError('NEW_PHASE_PACKAGE_CRASH_NO_RETRY')), 'FAIL_NATIVE_STARTUP_OR_PROCESS')

    def test_nested_observed_failures_remain_visible(self):
        nested = dict(fixture=dict(status='AVAILABLE_CASES_RECORDED', watchlist=dict(status='FAIL')), runtime=dict(status='NOT_RUN'))
        self.assertIn('FAIL', list(self.ns['result_statuses'](nested)))
        self.assertEqual(self.ns['outcome'](RuntimeError('OBSERVED_PACKAGEMANAGER_REJECTED')), 'FAIL_OBSERVED_INSTALL_OR_DATA_MISMATCH')
        self.assertEqual(self.ns['outcome'](RuntimeError('RECOVERY_AUTHENTICATED_AVAILABLE_STATE_NOT_RETAINED')), 'FAIL_OBSERVED_INSTALL_OR_DATA_MISMATCH')


if __name__ == '__main__': unittest.main(verbosity=2)
