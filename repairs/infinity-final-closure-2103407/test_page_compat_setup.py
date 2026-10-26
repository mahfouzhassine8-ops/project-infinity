import unittest
import api37_page_compat_setup as setup


class PageCompatSetupTests(unittest.TestCase):
    def request(self):return dict(candidate_apk_sha256='0b202e3af93ce25be8cd5ecb2853043411ba5fbbf88dac0df94ef4b2ce55605a',emulator_api='37.1',emulator_target='google_apis_ps16k',os_page_compat=True)
    def transport(self,change=None):
        values={('getprop','ro.kernel.qemu'):'1',('getprop','ro.build.version.sdk'):'37',('getprop','ro.build.version.release'):'17',('getconf','PAGE_SIZE'):'16384',('getprop','ro.product.cpu.abilist'):'x86_64,arm64-v8a',('pm','list','packages',setup.PACKAGE):'',('pidof',setup.PACKAGE):'',('id','-u'):'0',('getenforce',):'Enforcing'}
        if change:values.update(change)
        calls=[]
        def shell(*args):
            calls.append(args)
            if args[0]=='setprop':values[('getprop',args[1])]=args[2]
            return values.get(args,'')
        return shell,lambda *a,**k:calls.append(('adb',*a)),calls
    def test_exact_explicit_mode_reads_back_only_two_os_properties_without_application_claim(self):
        shell,adb,calls=self.transport();report=setup.configure(shell,adb,self.request())
        self.assertEqual(report['after'],setup.PROPERTIES)
        self.assertEqual([c for c in calls if c[0]=='setprop'],[('setprop',k,v) for k,v in setup.PROPERTIES.items()])
        self.assertFalse(report['application_test_passed']);self.assertFalse(report['strict16KiB_compliance'])
        self.assertFalse(report['APK_or_native_or_manifest_changed'])
    def test_physical_wrong_platform_existing_application_or_nonroot_refused(self):
        for change in [{('getprop','ro.kernel.qemu'):'0'},{('getconf','PAGE_SIZE'):'4096'},{('pm','list','packages',setup.PACKAGE):setup.PACKAGE},{('pidof',setup.PACKAGE):'123'},{('id','-u'):'2000'}]:
            shell,adb,calls=self.transport(change)
            with self.assertRaises(ValueError):setup.configure(shell,adb,self.request())
            self.assertFalse(any(c[0]=='setprop' for c in calls))
    def test_unselected_mode_wrong_APK_or_property_readback_refused(self):
        for key,value in [('os_page_compat',False),('candidate_apk_sha256','b'*64),('emulator_api','36')]:
            shell,adb,calls=self.transport()
            with self.assertRaises(ValueError):setup.configure(shell,adb,dict(self.request(),**{key:value}))
            self.assertEqual(calls,[])
        shell,adb,calls=self.transport()
        def broken(*a):return 'false' if a[:2]==('getprop','bionic.linker.16kb.app_compat.enabled') else shell(*a)
        with self.assertRaises(RuntimeError):setup.configure(broken,adb,self.request())


if __name__=='__main__':unittest.main(verbosity=2)
