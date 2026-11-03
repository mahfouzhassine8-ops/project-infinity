"""Focused input identity, certificate refusal and read-only workflow guards."""
from pathlib import Path
import copy
import importlib.util
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('p0_readonly_artifacts', HERE / 'artifact_preflight.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class InputPolicy(unittest.TestCase):
    def test_pinned_metadata_and_fail_closed_mismatches(self):
        for name, (identity, run, title, size, digest) in preflight.ASSETS.items():
            valid = {'id': identity, 'workflow_run': {'id': run}, 'name': title,
                     'size_in_bytes': size, 'digest': 'sha256:' + digest, 'expired': False}
            self.assertEqual(preflight.validate_metadata(name, valid)['id'], identity)
            for key, value in [('id', 0), ('workflow_run', {'id': 0}), ('name', 'other'),
                               ('size_in_bytes', 0), ('digest', 'sha256:' + '0' * 64),
                               ('expired', True), ('expired', None)]:
                mutated = copy.deepcopy(valid)
                mutated[key] = value
                with self.subTest(asset=name, changed=key):
                    with self.assertRaises(ValueError):
                        preflight.validate_metadata(name, mutated)

    def test_original_certificate_and_actual_byte_pins(self):
        text = 'Signer #1 certificate SHA-256 digest: ' + preflight.CERTIFICATE
        self.assertEqual(preflight.verify_certificate(text), preflight.CERTIFICATE)
        for value in ['', text.replace(preflight.CERTIFICATE, '0' * 64), text + '\n' + text]:
            with self.assertRaises(ValueError):
                preflight.verify_certificate(value)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bytes'
            path.write_bytes(b'fixture bytes only')
            with self.assertRaises(ValueError):
                preflight.assert_sha(path, preflight.APK_SHA)

    def test_workflow_has_no_signing_or_application_route(self):
        workflow = (ROOT / '.github/workflows/infinity-kodi451-p0-input-preflight.yml').read_text()
        self.assertIn('contents: read\n  actions: read', workflow)
        self.assertIn("if: github.ref == 'refs/heads/" + preflight.BRANCH + "'", workflow)
        self.assertIn('ARTIFACT-PREFLIGHT-REQUEST.json', workflow)
        self.assertIn('persist-credentials: false', workflow)
        for forbidden in ['secrets.', 'write-all', 'contents: write', 'actions: write',
                          'apksigner sign', 'keytool -gen', 'adb shell', 'emulator-runner',
                          'compile_engine()', 'continue-on-error: true', 'curl ', 'wget ']:
            self.assertNotIn(forbidden, workflow)
        for identity, run, *_ in preflight.ASSETS.values():
            self.assertEqual(workflow.count("artifact-ids: '" + str(identity) + "'"), 1)
            self.assertIn("artifact-ids: '" + str(identity) + "'\n          run-id: '" + str(run) + "'", workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
