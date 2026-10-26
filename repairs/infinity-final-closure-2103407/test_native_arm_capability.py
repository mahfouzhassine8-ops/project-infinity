import json
from pathlib import Path
import unittest
import native_arm_capability as probe


class CapabilityRequestTests(unittest.TestCase):
    def request(self):return json.loads(Path(__file__).with_name('NATIVE-ARM-CAPABILITY-REQUEST.json').read_text())
    def test_exact_platform_only_request_admitted_without_application_claim(self):
        request=probe.validate(self.request())
        self.assertIs(request['application_APK_installed'],False)
        self.assertIs(request['application_tests_selected'],False)
    def test_wrong_api_host_accel_or_application_scope_refused(self):
        for key,value in [('image','system-images;android-36;default;arm64-v8a'),('runner','macos-15-intel'),
                          ('application_APK_installed',True),('application_tests_selected',True),('acceleration','auto'),('schema',True)]:
            with self.assertRaises(ValueError):probe.validate(dict(self.request(),**{key:value}))
        with self.assertRaises(ValueError):probe.validate(dict(self.request(),extra=True))
    def test_capability_has_no_application_transport_or_signature_access(self):
        source=Path(probe.__file__).read_text()
        for forbidden in ("'install'",'CLOSE_KODI','force-stop','uninstall','KEYSTORE','Player.Open'):
            self.assertNotIn(forbidden,source)
        self.assertIn("report['page_size']!=4096",source)
        self.assertIn("report['sdk']!='37'",source)
        self.assertIn("if not booted:raise",source)


if __name__=='__main__':unittest.main(verbosity=2)
