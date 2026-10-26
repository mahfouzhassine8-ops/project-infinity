"""Request binding only; no environment or application execution on host."""
from pathlib import Path
from unittest.mock import patch
import unittest
import candidate_request as selection


class SelectionTests(unittest.TestCase):
    def test_only_two_explicit_recorded_environments_bind_the_exact_gate(self):
        for pair,path in selection.ENVIRONMENTS.items():
            request=dict(selection.EXPECTED,emulator_api=pair[0],emulator_target=pair[1],os_page_compat=False)
            with patch.object(selection,'EXPECTED',request):result=selection.validate(request)
            self.assertEqual(result['INFINITY_API37_GATE'],path)
            self.assertEqual(result['INFINITY_PAGE_COMPAT'],'')
            self.assertEqual((result['INFINITY_EMULATOR_API'],result['INFINITY_EMULATOR_TARGET']),pair)
            self.assertTrue((Path(__file__).resolve().parents[2]/path).is_file())

    def test_wrong_minor_lower_api_playstore_or_generic_target_has_no_fallback(self):
        for pair in (('36.0','default'),('37.2','default'),('37.0','google_apis'),('37.1','google_apis_playstore_ps16k')):
            request=dict(selection.EXPECTED,emulator_api=pair[0],emulator_target=pair[1],os_page_compat=False)
            with patch.object(selection,'EXPECTED',request),self.assertRaises(ValueError):selection.validate(request)

    def test_feature_manual_default_and_independent_shutdown_environment_unchanged(self):
        workflows=Path(__file__).resolve().parents[2]/'.github/workflows'
        feature=(workflows/'infinity-saved-navigation-android.yml').read_text()
        shutdown=(workflows/'infinity-shutdown-verification.yml').read_text()
        self.assertIn("api-level: ${{ env.INFINITY_EMULATOR_API || '37.0' }}",feature)
        self.assertIn("target: ${{ env.INFINITY_EMULATOR_TARGET || 'google_apis' }}",feature)
        self.assertIn("api-level: '37.0'",shutdown)
        self.assertNotIn('INFINITY_EMULATOR_API',shutdown)
        self.assertNotIn('continue-on-error',feature)
        self.assertNotIn('needs:',feature)


if __name__=='__main__':unittest.main(verbosity=2)
