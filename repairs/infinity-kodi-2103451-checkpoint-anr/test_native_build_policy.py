"""Only native-build input/refusal and orchestration policy, no app execution."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('p0_native_build', HERE / 'native_build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class NativeBuildPolicy(unittest.TestCase):
    def test_exact_five_file_delta_and_refuse_inventory_or_unrelated_source(self):
        proof = json.loads((HERE / 'evidence/NATIVE-INTEGRATION-RESTORED.json').read_text())
        before = {f'unchanged/{n}': '1' * 64 for n in range(9406)}
        before.update(proof['before'])
        after = dict(before, **proof['after'])
        self.assertEqual(build.verify_maps(before, after, proof), sorted(proof['before']))
        bad = dict(after)
        bad['unchanged/1'] = '2' * 64
        with self.assertRaises(ValueError): build.verify_maps(before, bad, proof)
        bad = dict(after)
        bad.pop('unchanged/1')
        with self.assertRaises(ValueError): build.verify_maps(before, bad, proof)
        bad = dict(after)
        bad[next(iter(proof['after']))] = '2' * 64
        with self.assertRaises(ValueError): build.verify_maps(before, bad, proof)
        bad_proof = copy.deepcopy(proof)
        bad_proof['baseline_engine_sha256'] = '0' * 64
        with self.assertRaises(ValueError): build.verify_maps(before, after, bad_proof)

    def test_source_artifact_is_exact_authenticated_preflight(self):
        build.inputs.ASSETS['verified_source'] = build.SOURCE_ASSET
        identity, run, name, size, digest = build.SOURCE_ASSET
        metadata = dict(id=identity, workflow_run={'id': run}, name=name, size_in_bytes=size,
                        digest='sha256:' + digest, expired=False)
        self.assertEqual(build.inputs.validate_metadata('verified_source', metadata)['id'], 13274901825)
        for key, value in [('id', 0), ('workflow_run', {'id': 0}), ('digest', 'sha256:' + '0'*64),
                           ('expired', True)]:
            bad = copy.deepcopy(metadata)
            bad[key] = value
            with self.assertRaises(ValueError): build.inputs.validate_metadata('verified_source', bad)

    def test_native_only_workflow_and_existing_producer_stop_before_apk(self):
        workflow = (ROOT / '.github/workflows/infinity-kodi451-p0-native-build.yml').read_text()
        self.assertIn('contents: read\n  actions: read', workflow)
        self.assertIn("if: github.ref == 'refs/heads/" + build.inputs.BRANCH + "'", workflow)
        self.assertIn('NATIVE-BUILD-REQUEST.json', workflow)
        self.assertIn("artifact-ids: '13274901825'\n          run-id: '41726452356'", workflow)
        self.assertIn("artifact-ids: '11698374892'\n          run-id: '38132105717'", workflow)
        for forbidden in ('secrets.', 'contents: write', 'actions: write', 'apksigner sign',
                          'continue-on-error', 'emulator-runner', 'adb shell', 'needs:',
                          'infinity-shutdown', 'producer.prepare(', 'build.py prepare'):
            self.assertNotIn(forbidden, workflow)
        producer = (ROOT / 'repairs/universal-persistence-2103401/build.py').read_text()
        self.assertIn("stage=stage[:stage.index(marker)]", producer)
        self.assertIn("marker='make -C \"$BUILD_DIR\" apk -j\"$(nproc)\"'", producer)
        self.assertIn('producer.compile_engine()', (HERE / 'native_build.py').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
