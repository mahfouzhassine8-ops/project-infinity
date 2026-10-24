"""Source/packaging regression tests. No device-runtime claims are made here."""
from pathlib import Path
import hashlib, importlib.util, json, os, re, shutil, struct, subprocess, sys, tempfile, unittest, zipfile
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'scripts'))
import infinity71 as m
from infinity71_axml import package_name

class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(os.environ['INFINITY_KODI_SOURCE'])
        cls.spec=m.contract()
    def text(self,name):return (self.source/name).read_text()
    def test_postimages_match(self):
        for name,h in self.spec['files'].items():self.assertEqual(m.sha((self.source/name).read_bytes()),h['after'],name)
    def test_java_and_jni_declarations_match(self):
        java=self.text('tools/android/packaging/xbmc/src/Main.java.in')
        conv={'boolean':'Z','int':'I','float':'F','void':'V','long[]':'[J'}
        actual={name:'()'+conv[typ] for typ,name in re.findall(r'public native (\w+(?:\[\])?) (_infinity\w+)\(\);',java)}
        self.assertEqual(actual,self.spec['jni'])
        cpp=self.text('xbmc/platform/android/activity/JNIMainActivity.cpp')
        registered=dict(re.findall(r'\{"(_infinity\w+)", "([^"\n]+)"',cpp))
        self.assertEqual(registered,actual)
    def test_upstream_lifecycle_is_preserved(self):
        java=self.text('tools/android/packaging/xbmc/src/Main.java.in')
        for name in ('onCreate','onStart','onResume','onPause','onDestroy','onActivityResult','onNewIntent'):
            self.assertEqual(java.count('super.'+name+'('),1,name)
        self.assertIn('mDelayedIntents.clear();',java)
        self.assertIn('manager.unregisterInputDeviceListener(mInputDeviceListener);',java)
    def test_source_cmake_includes_bridge(self):
        self.assertIn('src/InfinityCoreBridge.java',self.text('cmake/scripts/android/Install.cmake'))
    def test_geometry_is_render_thread_owned(self):
        cpp=self.text('xbmc/platform/android/activity/XBMCApp.cpp')
        resize=cpp.split('void CXBMCApp::onResizeWindow()',1)[1].split('\n}',1)[0]
        sync=cpp.split('void CXBMCApp::InfinitySyncDisplayState()',1)[1].split('\n}',1)[0]
        display=cpp.split('void CXBMCApp::onDisplayChanged(int displayId)',1)[1].split('\n}',1)[0]
        self.assertNotIn('m_window.reset()',resize)
        self.assertNotIn('UpdateDisplayModes()',sync)
        self.assertNotIn('UpdateDisplayModes()',display)
        self.assertIn('m_infinity.QueueDisplayModes()',display)
        win=self.text('xbmc/windowing/android/WinSystemAndroid.cpp')
        self.assertIn('graphics.ApplyModeChange(active);',win)
        self.assertIn('state.CommitGeometry(request)',win)
    def test_modern_pip_does_not_bypass_native_activity(self):
        cpp=self.text('xbmc/platform/android/activity/XBMCApp.cpp')
        self.assertIn('!m_hasReqVisible && !infinityIsPictureInPicture()',cpp)
        self.assertIn('messenger->PostMsg(TMSG_SWITCHTOFULLSCREEN)',cpp)
        java=self.text('tools/android/packaging/xbmc/src/Main.java.in')
        pause=java.split('public void onPause()',1)[1].split('\n  }',1)[0]
        self.assertIn('super.onPause();',pause)
        self.assertNotIn('return;',pause)
    def test_playback_updates_before_home_without_polling(self):
        cpp=self.text('xbmc/platform/android/activity/XBMCApp.cpp')
        self.assertIn('InfinityUpdatePlaybackState(message == "OnStop")',cpp)
        bridge=self.text('tools/android/packaging/xbmc/src/InfinityCoreBridge.java.in')
        self.assertIn('setAutoEnterEnabled(autoEnter)',bridge)
        self.assertNotIn('postDelayed',bridge)
        self.assertNotIn('getActivePlayers',bridge)
        self.assertIn('_infinityCanEnterPictureInPicture()',bridge)
    def test_manifest_survives_fold(self):
        import xml.etree.ElementTree as E
        root=E.fromstring(self.text('tools/android/packaging/xbmc/AndroidManifest.xml.in'))
        ns='{http://schemas.android.com/apk/res/android}'
        main=next(e for e in root.iter('activity') if e.get(ns+'name')=='.Main')
        self.assertEqual(main.get(ns+'supportsPictureInPicture'),'true')
        for flag in ('density','smallestScreenSize','uiMode','screenSize','orientation'):
            self.assertIn(flag,main.get(ns+'configChanges').split('|'))
    def test_no_theme_or_resume_mutation(self):
        paths=self.spec['files']
        self.assertFalse(any('VideoDatabase' in p or 'VideoPlayer' in p for p in paths))
        self.assertTrue(all(p.startswith('assets/addons/skin.estuary/') for p in m.OVERLAY_ALLOWLIST))
        self.assertFalse(any('/colors/' in p for p in m.OVERLAY_ALLOWLIST))
    def test_preserved_assets_have_provenance(self):m.asset_check()
    def test_idempotent_preparation(self):m.prepare_source(self.source)
    def test_mixed_source_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,h in self.spec['files'].items():
                f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((self.source/name).read_bytes())
            changed=root/'version.txt';changed.write_text(changed.read_text()+'\nUNEXPECTED CHANGE\n')
            before={str(f.relative_to(root)):m.sha(f.read_bytes()) for f in root.rglob('*') if f.is_file()}
            with self.assertRaises(ValueError):m.prepare_source(root)
            self.assertEqual(before,{str(f.relative_to(root)):m.sha(f.read_bytes()) for f in root.rglob('*') if f.is_file()})

@unittest.skipUnless(os.environ.get('INFINITY_TEST_DEX'),'DEX fixture compiled in separate Java gate')
class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.base=self.root/'FIXTURE-NOT-AN-APP.apk';self.man=self.root/'engine.json'
        # Deliberately a test-only ZIP fixture, not a linked or installable application.
        with zipfile.ZipFile(self.base,'w') as z:
            z.writestr('AndroidManifest.xml',b'<manifest package="com.projectinfinity.kodi"/>')
            z.write(os.environ['INFINITY_TEST_DEX'],'classes.dex')
            z.writestr('lib/arm64-v8a/libkodi.so',b'NOT-AN-ENGINE-UNIT-TEST')
            z.writestr('lib/arm64-v8a/libc++_shared.so',b'NOT-A-RUNTIME-UNIT-TEST')
            source=Path(os.environ['INFINITY_KODI_SOURCE'])
            z.write(source/'addons/skin.estuary/xml/VideoOSD.xml',m.SKIN+'xml/VideoOSD.xml')
            z.writestr('assets/addons/xbmc.python/addon.xml',b'<addon version="3.0.1"/>')
            z.writestr('assets/protected-stock-marker',b'untouched-21.3')
            z.writestr('META-INF/OLD.SF',b'obsolete signature')
        m.record_engine(self.base,self.man,'unit-test-not-native-build')
    def tearDown(self):self.tmp.cleanup()
    def test_actual_dex_declarations_not_strings(self):m.check_apk_contract(self.base)
    def test_overlay_preserves_all_protected_bytes(self):
        out=self.root/'overlay.apk';m.overlay(self.base,self.man,out)
        m.verify_overlay(out,self.man)
        with zipfile.ZipFile(out) as z:
            self.assertNotIn('META-INF/OLD.SF',z.namelist())
            for name,path in m.LOCK_FILES.items():self.assertEqual(z.read(path),(m.ASSETS/name).read_bytes())
    def test_tampered_engine_is_rejected(self):
        with zipfile.ZipFile(self.base,'a') as z:z.writestr('injected',b'wrong')
        with self.assertRaises(ValueError):m.check_engine(self.base,self.man)
    def test_wrong_package_is_rejected(self):
        bad=self.root/'wrong.apk'
        with zipfile.ZipFile(self.base) as src,zipfile.ZipFile(bad,'w') as dst:
            for name in src.namelist():dst.writestr(name,b'<manifest package="org.xbmc.kodi"/>' if name=='AndroidManifest.xml' else src.read(name))
        with self.assertRaises(ValueError):m.check_apk_contract(bad)
    def test_changed_native_library_is_rejected(self):
        out=self.root/'overlay.apk';bad=self.root/'bad.apk';m.overlay(self.base,self.man,out)
        with zipfile.ZipFile(out) as src,zipfile.ZipFile(bad,'w') as dst:
            for name in src.namelist():dst.writestr(name,b'wrong-native' if name.endswith('libkodi.so') else src.read(name))
        with self.assertRaises(ValueError):m.verify_overlay(bad,self.man)
    def test_wrong_bridge_version_is_rejected(self):
        j=json.loads(self.man.read_text());j['bridge_version']=2;self.man.write_text(json.dumps(j))
        with self.assertRaises(ValueError):m.check_engine(self.base,self.man)

if __name__=='__main__':unittest.main(verbosity=2)
