"""Selected harness/environment controls only. No SDK or application execution."""
import ast
import copy
from pathlib import Path
import unittest
import yaml

import probe


class HarnessControls(unittest.TestCase):
    def setUp(self):
        self.platform = dict(qemu='1', sdk='37', release='17', serial='emulator-5554',
                             abis='x86_64,arm64-v8a', page_size='16384', uid='0', selinux='Enforcing')

    def test_actual_selected_platform_admitted(self):
        probe.platform_before_root(self.platform, '')
        probe.platform_guard(self.platform, '', '')

    def test_physical_existing_wrong_api_or_bridge_refused_before_root(self):
        for key, value in (('qemu', '0'), ('sdk', '36'), ('release', '16'), ('serial', 'physical-device'), ('abis', 'x86_64')):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                probe.platform_before_root(dict(self.platform, **{key: value}), '')
        with self.assertRaises(RuntimeError): probe.platform_before_root(self.platform, 'package:com.projectinfinity.kodi')

    def test_existing_profile_wrong_pages_or_security_refused(self):
        for key, value in (('page_size', '4096'), ('uid', '2000'), ('selinux', 'Permissive')):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                probe.platform_guard(dict(self.platform, **{key: value}), '', '')
        with self.assertRaises(RuntimeError): probe.platform_guard(self.platform, '', 'present')

    def test_bounded_fixed_observer_actions(self):
        tree = ast.parse((Path(__file__).parent / 'observer.py').read_text())
        accept = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'accept')
        namespace = dict(ACTIONS=('snapshot', 'movie-tab', 'tv-tab', 'movie-focus', 'search', 'finish'), MAX_REQUESTS=24)
        exec(compile(ast.Module(body=[accept], type_ignores=[]), '<actual-observer-accept>', 'exec'), namespace)
        good = dict(pid=123, sequence=1, action='movie-tab')
        self.assertTrue(namespace['accept'](good, 123, 1))
        for bad in (dict(good, pid=True), dict(good, sequence=2), dict(good, action='arbitrary-builtin'),
                    dict(good, extra=True), dict(good, sequence=25)):
            self.assertFalse(namespace['accept'](bad, 123, 1))

    def test_exact_card_identity_progress_and_visibility(self):
        expected = probe.fixture()['items']['a' * 64]
        import json
        selection = {key: expected[key] for key in ('key', 'identity', 'source', 'stable_source')}
        prefix = 'Container(8830).ListItem.'
        labels = {'Container(8830).NumItems': '1', prefix + 'Property(Infinity.Selection.Snapshot)': json.dumps(selection),
                  prefix + 'Property(Infinity.ResumeHub.Watched)': 'false', prefix + 'PercentPlayed': '33'}
        flags = {'Control.IsVisible(8830)': True}
        self.assertTrue(probe.observed_card(labels, flags, expected, 'movie'))
        self.assertFalse(probe.observed_card(labels, {}, expected, 'movie'))
        self.assertFalse(probe.observed_card(dict(labels, **{prefix + 'PercentPlayed': '0'}), flags, expected, 'movie'))
        changed = copy.deepcopy(expected)
        changed['identity']['ids']['tmdb'] = '604'
        self.assertFalse(probe.observed_card(labels, flags, changed, 'movie'))

    def test_runtime_job_is_manual_finite_and_has_no_signing_or_old_matrix(self):
        path = probe.REPO / '.github/workflows/infinity-saved-navigation-android.yml'
        workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        job = workflow['jobs']['performance-android']
        self.assertIn("github.event_name == 'workflow_dispatch'", job['if'])
        self.assertIn("inputs.feature == 'infinity-performance-android'", job['if'])
        self.assertNotIn('needs', job)
        serialized = str(job)
        for forbidden in ('INFINITY_KEYSTORE_B64', 'assemble.py sign', 'android17_stress.py', 'android_shutdown', 'continue-on-error'):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("inputs.feature != 'infinity-performance-android'", workflow['jobs']['android17']['if'])
        self.assertEqual(job['steps'][-2]['with']['disable-animations'], 'false')
        java = next(i for i, step in enumerate(job['steps']) if step.get('uses', '').startswith('actions/setup-java'))
        android = next(i for i, step in enumerate(job['steps']) if step.get('uses', '').startswith('android-actions/setup-android'))
        self.assertLess(java, android)
        self.assertEqual(job['steps'][java]['with']['java-version'], '17')

    def test_production_and_reset_commands_are_not_selected(self):
        for command in ('force-stop', 'pm clear', 'pm uninstall', 'Application.Quit', 'CLOSE_KODI', 'reboot'):
            with self.subTest(command=command), self.assertRaises(RuntimeError):
                probe.device.guard((command,))
        source = (Path(__file__).parent / 'probe.py').read_text()
        self.assertEqual(source.count("device.shell('am', 'start', '-W'"), 1)
        self.assertNotIn('android_probe', source)
        self.assertNotIn('android17_stress', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
