"""Negative tests against the real #5 class/manifest definitions, not fabricated success tokens."""
from pathlib import Path
import os,sys,tempfile,shutil,unittest,zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import g2_candidate6 as m

class MappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoded=Path(os.environ['G2_BASE_DECODED'])
        cls.base=Path(os.environ['G2_BASE_APK'])
        cls.allclasses=m.classes(cls.decoded)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        for desc in [m.MAIN,m.BRIDGE]+['Lcom/projectinfinity/kodi/'+n+';' for n in m.NATIVE_METHODS if n!='Main']:
            old=self.allclasses[desc];p=self.root/old.relative_to(self.decoded)
            p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old,p)
        shutil.copyfile(self.decoded/'AndroidManifest.xml',self.root/'AndroidManifest.xml')
        self.main=next(self.root.glob('smali*/com/projectinfinity/kodi/Main.smali'))
        self.bridge=next(self.root.glob('smali*/com/projectinfinity/kodi/InfinityCoreBridge.smali'))
    def tearDown(self):self.tmp.cleanup()
    def reject(self):
        with self.assertRaises((ValueError,KeyError)):m.check_map(self.root)
    def test_actual_baseline_passes(self):m.check_base(self.base);m.check_map(self.root)
    def test_wrong_apk_fails_closed(self):
        p=self.root/'wrong.apk';p.write_bytes(b'not the approved APK')
        with self.assertRaises(ValueError):m.check_base(p)
    def test_missing_onresume_fails(self):
        self.main.write_text(self.main.read_text().replace('.method public onResume()V','.method public wrongResume()V'));self.reject()
    def test_missing_call_is_not_validated_by_comment(self):
        s=self.main.read_text().replace('    invoke-static {p0}, '+m.BRIDGE+'->updateInfinityPictureInPictureParams','    # invoke-static {p0}, '+m.BRIDGE+'->updateInfinityPictureInPictureParams');self.main.write_text(s);self.reject()
    def test_duplicate_callback_rejected(self):
        self.main.write_text(self.main.read_text()+'\n'+m.method_map(self.main.read_text())['onResume()V'][1]);self.reject()
    def test_wrong_native_signature_rejected(self):
        self.main.write_text(self.main.read_text().replace('_infinityWindowWidth()I','_infinityWindowWidth()J'));self.reject()
    def test_static_native_rejected(self):
        self.main.write_text(self.main.read_text().replace('public native _infinity','public static native _infinity'));self.reject()
    def test_wrong_argument_mapping_rejected(self):
        self.main.write_text(self.main.read_text().replace('invoke-static {p0}, '+m.BRIDGE,'invoke-static {v0}, '+m.BRIDGE));self.reject()
    def test_missing_companion_rejected(self):
        next(self.root.glob('smali*/com/projectinfinity/kodi/XBMCMainView.smali')).unlink();self.reject()
    def test_duplicate_main_class_rejected(self):
        p=self.root/'smali_classes7/copy.smali';p.parent.mkdir(exist_ok=True);shutil.copyfile(self.main,p);self.reject()
    def test_wrong_superclass_rejected(self):
        self.main.write_text(self.main.read_text().replace('.super Landroid/app/NativeActivity;','.super Landroid/app/Activity;'));self.reject()
    def test_wrong_bridge_static_descriptor_rejected(self):
        self.bridge.write_text(self.bridge.read_text().replace('public static getBridgeVersion','public getBridgeVersion'));self.reject()
    def test_v3_method_injection_rejected(self):
        self.bridge.write_text(self.bridge.read_text().replace('_infinityHasActiveVideo()Z','_infinityCanEnterPictureInPicture()Z'));self.reject()
    def test_wrong_package_rejected(self):
        p=self.root/'AndroidManifest.xml';p.write_text(p.read_text().replace('package="com.projectinfinity.kodi"','package="org.xbmc.kodi"'));self.reject()
    def test_wrong_lib_rejected(self):
        p=self.root/'AndroidManifest.xml';p.write_text(p.read_text().replace('android:value="kodi"','android:value="wrong"'));self.reject()
    def test_no_callbacks_deleted_on_failed_replacement(self):
        before=m.inventory_smali(self.root);p=self.root/'invalid.smali';p.write_text(self.bridge.read_text().replace('public static getBridgeVersion','public getBridgeVersion'))
        with self.assertRaises(ValueError):m.install_bridge(self.root,p)
        self.assertEqual(before,m.inventory_smali(self.root))
    def test_unknown_bridge_not_overwritten(self):
        self.bridge.write_text(self.bridge.read_text()+'\n# unknown additional change\n')
        before=m.inventory_smali(self.root);p=self.root/'replacement.smali';p.write_bytes(self.allclasses[m.BRIDGE].read_bytes())
        with self.assertRaises(ValueError):m.install_bridge(self.root,p)
        self.assertEqual(before,m.inventory_smali(self.root))
    def test_identical_map_is_noop(self):
        p=self.root/'same.smali';p.write_bytes(self.bridge.read_bytes());before=m.inventory_smali(self.root)
        m.install_bridge(self.root,p);m.install_bridge(self.root,p)
        self.assertEqual(before,m.inventory_smali(self.root))
    def test_nested_method_rejected(self):
        with self.assertRaises(ValueError):m.method_map('.method public a()V\n.method public b()V\n.end method\n')
    def test_unclosed_method_rejected(self):
        with self.assertRaises(ValueError):m.method_map('.method public a()V\n')
    def test_unmatched_end_rejected(self):
        with self.assertRaises(ValueError):m.method_map('.end method\n')
    def test_class_without_access_flag_supported(self):
        self.assertTrue(any('.class L' in p.read_text() for p in self.allclasses.values()))

if __name__=='__main__':unittest.main(verbosity=2)
