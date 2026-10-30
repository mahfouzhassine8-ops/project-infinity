"""Two selected QA-observer contracts; simulated ADB, never an application test."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock
import android_probe435 as observer

class NoticeProtocolTest(unittest.TestCase):
    def simulate(self, after, out):
        notices = (ROOT / 'native41129090323/runtime-results/signed435/cold-probe/android-compatibility-notice.xml').read_text()
        frames = iter([notices, notices, *after])
        calls = []
        def adb(*args, **kwargs):
            calls.append(args)
            if args == ('get-serialno',): return 'emulator-5554'
            if args[:2] == ('shell', 'getprop'):
                return {'ro.build.version.sdk':'37', 'ro.kernel.qemu':'1', 'ro.product.cpu.abilist':'x86_64,arm64-v8a'}[args[2]]
            if args[:3] == ('shell','pm','path'): return ''
            if args[:2] == ('shell','getconf'): return '16384'
            if args[0] == 'install': return 'Success: SIMULATED_ADB_NO_INSTALL'
            if args[:3] == ('shell','am','start'):
                return 'Starting: Intent { cmp=com.projectinfinity.kodi/.InfinityLiveActivity }\nStatus: ok\nActivity: com.projectinfinity.kodi/.InfinityLiveActivity\n'
            if args[:2] == ('shell','cat'): return next(frames)
            return 'SIMULATED_OS_OBSERVATION_NO_DEVICE'
        png=(ROOT / 'native41129090323/runtime-results/signed435/cold-probe/screen.png').read_bytes()
        with mock.patch.object(observer,'adb',side_effect=adb), \
             mock.patch.object(observer,'confirm_installed_apk',return_value={'simulated_only':True}), \
             mock.patch.object(observer.time,'sleep'), \
             mock.patch.object(observer.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=png)):
            try: observer.probe(APK,out,APK_SHA)
            finally:
                ok=[c for c in calls if c[:3]==('shell','input','tap')]
                self.assertEqual(1,len(ok),'Exactly one OK; never repeat notice input')
                self.assertFalse(any('settings' in c or 'setprop' in c or 'uninstall' in c for c in calls))
        return json.loads((out/'OUTCOME.json').read_text())

    def test_same_notice_pending_then_actual_first_screen_accepts_one_OK(self):
        notices=(ROOT / 'native41129090323/runtime-results/signed435/cold-probe/android-compatibility-notice.xml').read_text()
        welcome=(ROOT / 'native41127665715/runtime-results/signed435/cold-probe/last-ui.xml').read_text()
        result=self.simulate([notices,welcome],OUT/'same-notice')
        self.assertEqual('COBRA_FIRST_SCREEN_OBSERVED',result['status'])
        self.assertEqual(1,result['notice_pending_snapshots'])
        self.assertTrue(result['notice_dismissal_observed'])
        self.assertEqual(1,result['notice_OK_presses'])

    def test_new_notice_after_observed_dismissal_refuses_second_OK(self):
        notices=(ROOT / 'native41129090323/runtime-results/signed435/cold-probe/android-compatibility-notice.xml').read_text()
        # Explicit negative-only synthetic intermediate snapshot: warning absent,
        # destination still not ready. A subsequent notice must fail closed.
        intermediate='<hierarchy><node package="com.projectinfinity.kodi" text="Starting" /></hierarchy>'
        with self.assertRaisesRegex(AssertionError,'Genuine repeated compatibility notice'):
            self.simulate([intermediate,notices],OUT/'genuine-repeat')
        result=json.loads((OUT/'genuine-repeat/OUTCOME.json').read_text())
        self.assertEqual('BLOCKED_BEFORE_FEATURE_OBSERVATION',result['status'])
        self.assertEqual(1,result['notice_OK_presses'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence-root',type=Path,required=True);p.add_argument('--apk',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    ROOT,APK,OUT=a.evidence_root,a.apk,a.out;assert not OUT.exists();OUT.mkdir(parents=True)
    APK_SHA='16f02a9625c057a3fe4d4b55da8a554fdb2bff0f1b19c8f567bdf56af41eb465'
    scope=json.loads((Path(__file__).parent/'NOTICE-OBSERVATION-CORRECTION.json').read_text());names=scope['selected_QA_protocol_tests'];assert scope['selected_before_execution'] is True and len(set(names))==2
    suite=unittest.TestSuite(NoticeProtocolTest(n) for n in names)
    with (OUT/'PROTOCOL-OUTPUT.txt').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    record=dict(status='PASS_QA_NOTICE_PROTOCOL_ONLY' if result.wasSuccessful() else 'FAIL_QA_NOTICE_PROTOCOL_ONLY',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),selected=names,fixtures='Captured native435 warning+actual Welcome XML; negative intermediate explicitly simulated',APK='Read-only immutable434 bytes for identical47-native-library whitelist; no app/device execution',source_sha256=hashlib.sha256(Path(observer.__file__).read_bytes()).hexdigest(),shutdown='NOT_RUN')
    (OUT/'PROTOCOL-RESULT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
    if not result.wasSuccessful() or result.testsRun!=2 or result.skipped:raise SystemExit(1)
