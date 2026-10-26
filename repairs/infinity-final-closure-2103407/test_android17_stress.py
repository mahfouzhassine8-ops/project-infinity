"""Host admission/partial failure boundaries; no simulated runtime pass."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import android17_stress as stress


class StressAdmissionTests(unittest.TestCase):
    def values(self):
        owner={'pid':123,'owner':'test-process'}
        device=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',
            shell=lambda *a:'1' if a[-1]=='ro.kernel.qemu' else '37',running_engine=lambda:owner)
        setup={'passed':True,'apk_sha256':'a'*64,'engine':owner}
        expected={'candidate_apk_sha256':'a'*64,'post_feature':dict(stress.COUNTS)}
        return device,setup,expected

    def test_explicit_exact_selection_only_after_actual_feature_pass(self):
        device,setup,expected=self.values();self.assertEqual(stress.admit(device,setup,expected),setup['engine'])
        for changed in (dict(expected,post_feature={}),dict(expected,post_feature={'search':50}),
            dict(expected,candidate_apk_sha256='b'*64)):
            with self.assertRaises(RuntimeError):stress.admit(device,setup,changed)
        for changed in (dict(setup,passed=False),dict(setup,engine={}),dict(setup,apk_sha256='b'*64)):
            with self.assertRaises(RuntimeError):stress.admit(device,changed,expected)

    def test_physical_wrong_platform_or_changed_process_refused(self):
        device,setup,expected=self.values()
        for change in ({'PACKAGE':'other'}, {'shell':lambda *a:'0'}, {'shell':lambda *a:'36'},
            {'running_engine':lambda:{'pid':124,'owner':'test-process'}},
            {'running_engine':lambda:{'pid':123,'owner':'stale'}}):
            changed=SimpleNamespace(**dict(vars(device),**change))
            with self.assertRaises(RuntimeError):stress.admit(changed,setup,expected)

    def test_independent_home_selection_is_exact_and_does_not_select_search(self):
        device,setup,expected=self.values()
        expected['post_feature']=dict(stress.HOME_COUNTS)
        self.assertEqual(stress.admit(device,setup,expected),setup['engine'])
        self.assertEqual(expected['post_feature']['search'],0)
        self.assertEqual(expected['post_feature']['playback_home'],30)
        self.assertEqual(expected['post_feature']['rotation'],20)
        for counts in ({'search':0,'playback_home':0,'rotation':0},
                       {'search':0,'playback_home':29,'rotation':20},
                       {'search':1,'playback_home':30,'rotation':20}):
            with self.assertRaises(RuntimeError):
                stress.admit(device,setup,dict(expected,post_feature=counts))

    def test_partial_actual_failure_remains_failed_and_keeps_completed_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);path=out/'STRESS-RESULT.json'
            path.write_text(json.dumps({'passed':False,'search':[{'cycle':0}],'playback_home':[],'rotation':[]}))
            with mock.patch.object(stress,'_run',side_effect=RuntimeError('actual evidence unavailable')):
                with self.assertRaises(RuntimeError):stress.run(None,None,None,out)
            value=json.loads(path.read_text());self.assertFalse(value['passed']);self.assertEqual(len(value['search']),1)
            self.assertIn('actual evidence unavailable',value['failure'])

    def test_driver_uses_feature_guard_and_no_shutdown_or_reset_transport(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'save-later-multiimage-20261023'))
        import android_feature_device as device
        for command in (('am','start','InfinityPowerControlActivity'),('pm','clear','com.projectinfinity.kodi'),('am','force-stop','com.projectinfinity.kodi')):
            with self.assertRaises(RuntimeError):device.guard(command)
        body=Path(stress.__file__).read_text()
        for forbidden in ('essential_android_probe','InfinityPowerControlActivity','CLOSE_KODI','force-stop','pm clear','uninstall'):
            self.assertNotIn(forbidden,body)
        self.assertIn('device.until(keyboard,45)',body);self.assertIn('Player.Open',body)
        self.assertIn("poster_paint_verified=card['poster_paint_verified']",body)
        self.assertIn("cached QA bitmap observed on native Android surface",body)
        self.assertIn('physical_fold=False',body)


if __name__=='__main__':unittest.main(verbosity=2)
