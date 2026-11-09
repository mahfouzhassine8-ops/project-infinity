"""Selected changed intake guards; no app, signing or provider execution."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import admit_tracking_android as intake

HERE=Path(__file__).resolve().parent

class OriginIntake(unittest.TestCase):
    def setUp(self):
        self.request=dict(execution_focus='infinity-origin-acceptance', direct_provider_acceptance=False,
            direct_provider_fallback=False, maximum_new_attempts=1, automatic_retries=0,
            protected_source_checkpoint=intake.REVIEWED, retained_environment_failure_run=42570831467)

    def test_current_owner_contract_and_frozen_sources(self):
        intake.checked_focus(self.request)

    def test_old_diagnostic_focus_refused(self):
        self.request['execution_focus']='independent-movie'
        with self.assertRaisesRegex(RuntimeError,'EXACT_INFINITY_ORIGIN_FOCUS_ONLY'):
            intake.checked_focus(self.request)

    def test_direct_acceptance_or_fallback_refused(self):
        for key in ('direct_provider_acceptance','direct_provider_fallback'):
            request=dict(self.request,**{key:True})
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError,'NO_PROVIDER_BYPASS'):
                intake.checked_focus(request)

    def test_retries_or_extra_attempts_refused(self):
        for values in ({'maximum_new_attempts':2},{'automatic_retries':1}):
            request=dict(self.request,**values)
            with self.subTest(values=values), self.assertRaisesRegex(RuntimeError,'ONE_NEW_ORIGIN_ATTEMPT'):
                intake.checked_focus(request)

    def test_different_source_or_hidden_startup_failure_refused(self):
        for values in ({'protected_source_checkpoint':'0'*40},{'retained_environment_failure_run':None}):
            with self.subTest(values=values), self.assertRaisesRegex(RuntimeError,'FROZEN_E410_AND_RETAINED'):
                intake.checked_focus(dict(self.request,**values))

    def test_owner_navigation_cannot_become_tracking_pass(self):
        contract=json.loads((HERE/'INFINITY-ORIGIN-ACCEPTANCE.json').read_text())
        contract['owner_confirmed_navigation']['tracking_acceptance']=True
        with patch.object(intake,'load',return_value=contract):
            with self.assertRaisesRegex(RuntimeError,'PRESERVE_OWNER_NAVIGATION_CONFIRMATION'):
                intake.checked_focus(self.request)

    def test_stale_internal_fixture_refused(self):
        stale=dict(run=42555855742,source='9d64ffb84404036ce6e02d6cb160fb004a029b33',
            workflow_id=397702717,workflow_path='.github/workflows/infinity-combined-release.yml',
            APK_build=False,publication=False)
        with patch.object(intake,'load',return_value=stale):
            with self.assertRaisesRegex(RuntimeError,'MATCHING_ORIGINAL_KEY_E410_MODULE_FIXTURE'):
                intake.checked_module_pin()

if __name__=='__main__': unittest.main(verbosity=2)
