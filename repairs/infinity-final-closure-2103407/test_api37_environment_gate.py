"""Exact same-major API environment selection, never a runtime pass."""
from pathlib import Path
import tempfile
import unittest
import json
import api37_environment_gate as gate


class EnvironmentGateTests(unittest.TestCase):
    def test_catalog_gate_reuses_original_sdk_logic_and_only_changes_explicit_image(self):
        original=gate.LEGACY.read_bytes()
        module=gate.legacy()
        self.assertEqual(module.IMAGE,'system-images;android-37.1;google_apis_ps16k;x86_64')
        self.assertEqual(gate.LEGACY.read_bytes(),original)
        self.assertEqual(module.check.__code__.co_filename,str(gate.LEGACY))
        self.assertEqual(module.pin_tools.__code__.co_filename,str(gate.LEGACY))

    def test_current_request_and_workflow_bind_only_explicit_image_and_preserve_manual_default(self):
        import candidate_request
        request=dict(candidate_request.EXPECTED)
        result=candidate_request.validate(request)
        self.assertEqual(result['INFINITY_EMULATOR_API'],'37.1')
        self.assertEqual(result['INFINITY_EMULATOR_TARGET'],'google_apis_ps16k')
        self.assertEqual(request['emulator_api'],'37.1')
        for field,value in [('emulator_api','36'),('emulator_target','google_apis_playstore_ps16k')]:
            with self.assertRaises(ValueError):candidate_request.validate(dict(request,**{field:value}))
        workflow=(Path(__file__).resolve().parents[2]/'.github/workflows/infinity-saved-navigation-android.yml').read_text()
        self.assertIn("api-level: ${{ env.INFINITY_EMULATOR_API || '37.0' }}",workflow)
        self.assertIn("target: ${{ env.INFINITY_EMULATOR_TARGET || 'google_apis' }}",workflow)
        self.assertIn('${INFINITY_API37_GATE:-repairs/four-repair-20261018/android37_gate.py}',workflow)
        self.assertNotIn('continue-on-error',workflow)
        self.assertNotIn('needs:',workflow)

    def avd(self,root,target='android-37.1',image='system-images/android-37.1/google_apis_ps16k/x86_64/',abi='x86_64'):
        folder=root/'test.avd';folder.mkdir()
        (root/'infinity-four-repair-api37.ini').write_text('path='+str(folder)+'\ntarget='+target+'\n')
        (folder/'config.ini').write_text('abi.type='+abi+'\nimage.sysdir.1='+image+'\n')
        return root,root/'proof'

    def test_exact_avd_records_comparison_without_claiming_application_success(self):
        with tempfile.TemporaryDirectory() as t:
            home,out=self.avd(Path(t));gate.check_avd(home,out)
            value=json.loads((out/'API37-ENVIRONMENT-COMPARISON.json').read_text())
            self.assertEqual(value['exact_selected_image'],gate.IMAGE)
            for field in ('application_changed','application_restarted','application_test_passed','lower_API_fallback'):
                self.assertIs(value[field],False)

    def test_wrong_target_source_or_abi_refused_without_fallback(self):
        for args in ({'target':'android-37.0'},{'image':'system-images/android-37.0/google_apis/x86_64/'},
                     {'abi':'arm64-v8a'}):
            with tempfile.TemporaryDirectory() as t:
                home,out=self.avd(Path(t),**args)
                with self.assertRaises(RuntimeError):gate.check_avd(home,out)
                self.assertFalse(out.exists())


if __name__=='__main__':unittest.main(verbosity=2)
