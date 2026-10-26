from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest import TestCase,main
from unittest.mock import patch
import android_bootstrap_root as bootstrap
import android17_candidate_probe as candidate
import sys
sys.path.insert(0,str(candidate.OLD))
import android_feature_device as retained


class BootstrapRootTests(TestCase):
    def device(self,**changes):
        value=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',qemu='1',sdk='37',installed='',engine=None)
        for k,v in changes.items():setattr(value,k,v)
        value.shell=lambda *a:value.qemu if a[-1]=='ro.kernel.qemu' else value.sdk if a[-1]=='ro.build.version.sdk' else value.installed
        value.running_engine=lambda:value.engine
        return value

    def test_one_transport_retry_before_app_and_other_errors_do_not_retry(self):
        calls=[]
        def adb(*args,check=True,binary=False):
            calls.append(args)
            if len(calls)==1:raise RuntimeError('adb: unable to connect for root: closed')
            return 'restarting adbd as root'
        with tempfile.TemporaryDirectory() as temp,patch.object(bootstrap.subprocess,'run',return_value=SimpleNamespace(returncode=0,stderr='')) as wait:
            self.assertIn('root',bootstrap.root(self.device(),adb,Path(temp)))
            self.assertTrue((Path(temp)/'ADB-ROOT-TRANSPORT-RECOVERY.json').is_file())
            wait.assert_called_once_with(['adb','wait-for-device'],capture_output=True,text=True,timeout=30)
        self.assertEqual(calls,[('root',),('root',)])
        for message in ('permission denied','device unauthorized','unknown root failure'):
            calls=[]
            def fail(*args,**kwargs):calls.append(args);raise RuntimeError(message)
            with self.assertRaises(RuntimeError):bootstrap.root(self.device(),fail,Path('/unused'))
            self.assertEqual(calls,[('root',)])

    def test_physical_existing_live_and_second_failure_never_become_pass(self):
        for changes in ({'qemu':'0'},{'sdk':'36'},{'PACKAGE':'other'}, {'installed':'package:com.projectinfinity.kodi'}, {'engine':{'pid':123}},{}):
            calls=[]
            def adb(*args,**kwargs):
                calls.append(args)
                if args==('root',):raise RuntimeError('unable to connect for root: closed')
                return ''
            with tempfile.TemporaryDirectory() as temp,patch.object(bootstrap.subprocess,'run',return_value=SimpleNamespace(returncode=0,stderr='')),self.assertRaises((ValueError,RuntimeError)):
                bootstrap.root(self.device(**changes),adb,Path(temp))
            self.assertEqual(calls.count(('root',)),2 if not changes else 1)

    def test_actual_retained_transport_signature_and_both_real_subprocess_budgets(self):
        calls=[]
        def process(command,**kwargs):
            calls.append((command,kwargs))
            closed=len(calls)==1
            return SimpleNamespace(returncode=1 if closed else 0,
                stderr='adb: unable to connect for root: closed' if closed else '',stdout='root ready')
        with tempfile.TemporaryDirectory() as temp,patch.object(bootstrap.subprocess,'run',side_effect=process):
            self.assertEqual(bootstrap.root(self.device(),retained.adb,Path(temp)),'root ready')
        self.assertEqual([v[0] for v in calls],[['adb','root'],['adb','wait-for-device'],['adb','root']])
        self.assertEqual([v[1]['timeout'] for v in calls],[90,30,90])


if __name__=='__main__':main(verbosity=2)
