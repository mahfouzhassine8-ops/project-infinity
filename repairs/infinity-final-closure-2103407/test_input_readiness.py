"""Readiness/observation source checks; no simulated device success."""
import hashlib
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import android_input_readiness as readiness
import android17_reference_observation as retained
import shutdown_environment as environment


class InputReadinessTests(unittest.TestCase):
    def test_actual_collector_supplies_required_service_sha(self):
        from zipfile import ZipFile
        import android17_shutdown_probe as shutdown
        apk=Path(os.environ['INFINITY_RUNTIME_CANDIDATE_APK'])
        with tempfile.TemporaryDirectory() as temp,ZipFile(apk) as z:
            root=Path(temp)
            for name in environment.FILES:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(z.read('assets/addons/service.xbmc.versioncheck/'+name))
            value=environment.collect(str(root),root)
            observed=value['versioncheck_source']['resources/lib/version_check/service.py']['sha256']
            self.assertEqual(observed,'8c192bef13ac77002568d561b7112ea073fc916d676cd6e9433e4b9b30988f56')
            shutdown.verify_runtime_service(value,apk)

    def test_current_drawn_IME_is_required_and_cold_or_wrong_process_is_refused(self):
        state='mInputShown=true\nmCurId='+readiness.IME
        line='10-26 10:15:44.299 1635 1635 I GoogleInputMethodService: GoogleInputMethodService$1.onKeyboardViewShown():344 onKeyboardViewShown: keyboardType=prime, keyboardViewType=BODY'
        self.assertTrue(readiness.proof(state,line,['1635'])['ready'])
        for changed,log,pids in ((state.replace('true','false'),line,['1635']),
            ('mInputShown=true',line,['1635']),(state,line,['9999']),
            (state,line.replace('BODY','HEADER'),['1635']),
            (state,line.replace('keyboardViewType','keyboardType'),['1635']),
            (state,line.replace('BODY','BODY_PENDING'),['1635']),(state,'',[])):
            self.assertFalse(readiness.proof(changed,log,pids)['ready'])

    def test_only_readiness_predicate_changes_in_frozen_actual_input_driver(self):
        path=retained.OLD/'universal/android_search_input.py';raw=path.read_bytes();driver=SimpleNamespace()
        readiness.instrument(driver,path,retained.DRIVER_SHA)
        text=raw.decode();updated=text.replace(readiness.DRIVER_BEFORE,readiness.DRIVER_AFTER,1)
        self.assertEqual(updated.replace(readiness.DRIVER_AFTER,readiness.DRIVER_BEFORE,1),text)
        self.assertIn("device.shell('input','text','The%sMatrix')",updated)
        self.assertIn("device.shell('input','keyevent','66')",updated)
        self.assertIn('device.until(keyboard,45)',updated)
        self.assertIn("raise RuntimeError('Actual Android search text was not confirmed')",updated)
        with self.assertRaises(ValueError):readiness.instrument(driver,path,'0'*64)

    def test_environment_observation_preserves_errno_and_never_executes_child(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in environment.FILES:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'original source')
            missing=root/'missing';value=environment.collect(str(root)+':'+str(missing),root)
            self.assertFalse(value['child_execution_attempted']);self.assertFalse(value['child_readonly_or_durable_proof'])
            self.assertEqual(value['search'][0]['candidate_observation']['errno'],2)
            self.assertEqual(value['search'][1]['directory_observation']['errno'],2)
            self.assertEqual(value['versioncheck_source']['addon.xml']['sha256'],hashlib.sha256(b'original source').hexdigest())
            self.assertEqual((root/'addon.xml').read_bytes(),b'original source')
        with self.assertRaises(ValueError):environment.collect('x'*8193,Path('/nonexistent'))


if __name__=='__main__':unittest.main(verbosity=2)
