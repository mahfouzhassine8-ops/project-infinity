"""Actual binary manifest checks using disposable resource-only APK fixtures."""
import importlib.util,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('package_check',ROOT/'scripts/infinity_mobile_package_check.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PackageMetadata(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='infinity-metadata-fixture-'); self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def fixture(self,debug=False,version='2103100',label='Infinity'):
  manifest=self.root/'AndroidManifest.xml'
  manifest.write_text(f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.kodi" android:versionCode="{version}" android:versionName="21.3-Infinity-Android-First"><uses-sdk android:minSdkVersion="21" android:targetSdkVersion="34"/><application android:label="{label}" android:debuggable="{str(debug).lower()}"/></manifest>''')
  apk=self.root/'fixture.apk';sdk=Path(os.environ['ANDROID_HOME'])
  subprocess.run([str(sdk/'build-tools/34.0.0/aapt2'),'link','--manifest',str(manifest),'-I',str(sdk/'platforms/android-34/android.jar'),'-o',str(apk)],check=True,capture_output=True)
  return apk
 def test_actual_binary_release_metadata(self):m.check(self.fixture(),self.root/'report.json')
 def test_reject_debuggable(self):
  with self.assertRaisesRegex(ValueError,'debuggable'):m.check(self.fixture(debug=True),self.root/'report.json')
 def test_reject_old_version(self):
  with self.assertRaisesRegex(ValueError,'version'):m.check(self.fixture(version='2103000'),self.root/'report.json')
 def test_reject_stock_label(self):
  with self.assertRaisesRegex(ValueError,'label'):m.check(self.fixture(label='Kodi'),self.root/'report.json')
if __name__=='__main__':unittest.main(verbosity=2)
