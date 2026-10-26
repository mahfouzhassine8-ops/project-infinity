from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest import TestCase,main
import android_bootstrap_root as bootstrap


class BootstrapRootTests(TestCase):
    def device(self,**changes):
        value=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',qemu='1',sdk='37',installed='',engine=None)
        for k,v in changes.items():setattr(value,k,v)
        value.shell=lambda *a:value.qemu if a[-1]=='ro.kernel.qemu' else value.sdk if a[-1]=='ro.build.version.sdk' else value.installed
        value.running_engine=lambda:value.engine
        return value

    def test_one_transport_retry_before_app_and_other_errors_do_not_retry(self):
        calls=[]
        def adb(*args,**kwargs):
            calls.append((args,kwargs))
            if len(calls)==1:raise RuntimeError('adb: unable to connect for root: closed')
            return 'restarting adbd as root'
        with tempfile.TemporaryDirectory() as temp:
            self.assertIn('root',bootstrap.root(self.device(),adb,Path(temp)))
            self.assertTrue((Path(temp)/'ADB-ROOT-TRANSPORT-RECOVERY.json').is_file())
        self.assertEqual([v[0] for v in calls],[('root',),('wait-for-device',),('root',)])
        self.assertEqual(calls[1][1],{'timeout':30})
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
            with tempfile.TemporaryDirectory() as temp,self.assertRaises((ValueError,RuntimeError)):
                bootstrap.root(self.device(**changes),adb,Path(temp))
            self.assertEqual(calls.count(('root',)),2 if not changes else 1)


if __name__=='__main__':main(verbosity=2)
