"""Safety contracts for the automatic INTERNAL Kodi candidate builder."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / 'upstream'
BUILDER = ROOT / '.github/workflows/kodi-candidate-builder.yml'
WATCHER = ROOT / '.github/workflows/infinity-kodi-watch.yml'
BASELINE = json.loads((UPSTREAM / 'baseline.json').read_text())


class CandidateBuilderContracts(unittest.TestCase):
    def test_builder_is_internal_only_and_never_uses_retained_signing(self):
        text = BUILDER.read_text()
        self.assertIn('workflow_call:', text)
        self.assertIn('workflow_dispatch:', text)
        self.assertIn('persist-credentials: false', text)
        self.assertIn('5f7d9b311568cca053d9c0e082463baca1bd99e0', text)
        self.assertIn('python3 upstream/port.py', text)
        self.assertIn("report['status']=='source_prepared_review_required'", text)
        self.assertIn('INTERNAL-SIDEBYSIDE-CANDIDATE', text)
        self.assertIn('Disposable Kodi Candidate', text)
        self.assertIn('NOT production-signed. NOT released. NOT installed. NOT promoted.', text)
        for forbidden in (
            'contents: write', 'actions: write', 'issues: write', 'pull-requests: write',
            'secrets.', 'INFINITY_KEYSTORE', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD',
            'INFINITY_KEY_ALIAS', 'gh release', 'adb install', 'apksigner sign',
            'pull_request_target', 'secrets: inherit'):
            self.assertNotIn(forbidden, text)

    def test_builder_candidate_is_side_by_side_and_userdata_isolated(self):
        text = BUILDER.read_text()
        self.assertIn('RUNTIME_NAMESPACE: com.projectinfinity.kodi', text)
        self.assertIn('CANDIDATE_PACKAGE: com.projectinfinity.kodi.candidate', text)
        self.assertIn('applicationId "{candidate}"', text)
        self.assertIn('Infinity runtime namespace preserved', text)
        self.assertIn("package: name='$CANDIDATE_PACKAGE'", text)
        self.assertIn("package: name='com.projectinfinity.kodi'", text)
        self.assertIn('Refusing internal candidate that could collide with production package ID', text)
        self.assertIn('Uses separate Android app data/userdata from production Infinity.', text)
        self.assertNotIn('-DAPP_PACKAGE="$CANDIDATE_PACKAGE"', text)
        self.assertIn("runtime=b'Lcom/projectinfinity/kodi/Main;'", text)
        self.assertIn("renamed=b'Lcom/projectinfinity/kodi/candidate/Main;'", text)
        self.assertIn('Side-by-side application ID must not rename Infinity runtime classes', text)

    def test_builder_isolates_provider_authorities_without_runtime_namespace_mutation(self):
        text = BUILDER.read_text()
        for suffix in ('media', 'file', 'ytdl'):
            self.assertIn(f"com.projectinfinity.kodi.candidate.{suffix}", text)
        self.assertIn('Unexpected Kodi namespace template contract', text)
        self.assertIn('Unexpected Kodi applicationId template contract', text)
        self.assertIn('Provider authorities isolated to candidate application ID.', text)

    def test_builder_cannot_silently_become_production_promotion(self):
        text = BUILDER.read_text()
        self.assertIn("production=baseline['runtime']['signer_sha256'].lower()", text)
        self.assertIn('Production Infinity signer must never be used by automatic candidate builds', text)
        self.assertIn('Human review and device acceptance are required', text)
        policy = BASELINE['policy']
        self.assertFalse(policy['auto_sign'])
        self.assertFalse(policy['auto_merge'])
        self.assertFalse(policy['auto_install'])
        self.assertFalse(policy['auto_change_baseline'])

    def test_watcher_requires_successful_source_analysis_before_candidate_build(self):
        text = WATCHER.read_text()
        self.assertIn('candidate-build:', text)
        self.assertIn('needs: [alert, source-analysis]', text)
        self.assertIn("needs.source-analysis.result == 'success'", text)
        self.assertIn('uses: ./.github/workflows/kodi-candidate-builder.yml', text)
        self.assertIn('target_tag: ${{ needs.alert.outputs.tag }}', text)
        self.assertIn('target_sha: ${{ needs.alert.outputs.target_sha }}', text)

    def test_source_analyzer_itself_still_does_not_authorize_a_build(self):
        import sys
        sys.path.insert(0, str(UPSTREAM))
        import port
        gates = port.review_gates()
        self.assertFalse(gates['automatic_build_allowed'])
        self.assertFalse(gates['automatic_install_allowed'])
        self.assertFalse(gates['release_ready'])


if __name__ == '__main__':
    unittest.main()
