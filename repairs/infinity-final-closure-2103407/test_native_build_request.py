"""Narrow existing-workflow routing; no Android feature or shutdown execution."""
from pathlib import Path
import unittest
import native_build_request as request


class NativeBuildRequestTests(unittest.TestCase):
    def event(self):return dict(ref=request.BRANCH,after='a'*40,repository={'full_name':'mahfouzhassine8-ops/project-infinity'})

    def test_exact_explicit_engine_request_on_existing_branch(self):
        self.assertTrue(request.validate(request.EXPECTED,self.event(),'a'*40,[request.REQUEST]))
        self.assertEqual(request.EXPECTED['source_count'],9411)
        self.assertEqual(request.EXPECTED['existing_source_changes'],7)

    def test_unrelated_branch_source_packaging_or_weakened_scope_rejected(self):
        for event in (dict(self.event(),ref='refs/heads/main'),dict(self.event(),after='b'*40),dict(self.event(),deleted=True)):
            with self.assertRaises(ValueError):request.validate(request.EXPECTED,event,'a'*40,[request.REQUEST])
        for field,value in (('kind','signed-final-apk'),('protected_commit','0'*40),('existing_source_changes',0),('authorization','')):
            with self.assertRaises(ValueError):request.validate(dict(request.EXPECTED,**{field:value}),self.event(),'a'*40,[request.REQUEST])
        for changed in ([],[request.REQUEST,'xbmc/video/VideoPlayer.cpp']):
            with self.assertRaises(ValueError):request.validate(request.EXPECTED,self.event(),'a'*40,changed)

    def test_existing_producer_dependencies_signer_verification_and_separate_scopes_retained(self):
        root=Path(__file__).resolve().parents[2]
        text=(root/'.github/workflows/infinity-2103402-native-owner-build.yml').read_text()
        final=text.split('\n  final-native:\n',1)[1]
        for literal in ('40158384817','40230842944','38132105717','21.4.7075529',
                        'producer.compile_engine()',"reviewed_file_count']==9411",'test_native_integration.py',
                        'test_identity_audit.py','apksigner" verify','InfinityCommandCenterIdentityV1',
                        'INTERNAL-NOT-APK','signed407-native/SIGNED407-NATIVE-SOURCE-MAP.json'):
            self.assertIn(literal,final)
        for forbidden in ('needs:','continue-on-error','secrets.','android_feature_probe.py','shutdown_runtime_probe'):
            self.assertNotIn(forbidden,final)
        self.assertIn("if: github.ref == 'refs/heads/work/infinity-2103402-native-owner-corrective-20261024'",text)


if __name__=='__main__':unittest.main(verbosity=2)
