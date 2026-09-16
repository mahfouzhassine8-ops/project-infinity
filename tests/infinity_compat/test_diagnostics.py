from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import infinity_diagnostics_source as source_patch


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def template(self, name):
        src = ROOT / 'patches/infinity-compat' / (name + '.java.in')
        dest = self.root / (name + '.java')
        dest.write_text(src.read_text().replace('@APP_PACKAGE@', 'com.projectinfinity.kodi'))
        return dest

    def test_real_jvm_file_writer_scenarios(self):
        source = self.template('InfinityDiagnosticFiles')
        harness = ROOT / 'tests/infinity_compat/DiagnosticFilesTest.java'
        subprocess.run(['javac', '--release', '8', '-d', str(self.root), str(source), str(harness)], check=True)
        result = subprocess.run(['java', '-cp', str(self.root), 'com.projectinfinity.kodi.DiagnosticFilesTest'],
                                check=True, capture_output=True, text=True)
        self.assertIn('seven file-I/O regression', result.stdout)

    def test_collector_compiles_against_real_android_sdk(self):
        jar = Path(os.environ.get('INFINITY_ANDROID_JAR', ROOT / 'validation/android.jar'))
        self.assertTrue(jar.is_file(), 'Real Android SDK jar required; do not count skipped compilation as passing')
        sources = [self.template(n) for n in ('InfinityDiagnosticFiles', 'InfinityExitDiagnostics')]
        subprocess.run(['javac', '--release', '8', '-cp', str(jar), '-d', str(self.root)] +
                       [str(p) for p in sources], check=True, capture_output=True, text=True)
        self.assertTrue((self.root / 'com/projectinfinity/kodi/InfinityExitDiagnostics.class').is_file())

    def fixture(self):
        base = Path(os.environ.get('INFINITY_PINNED_SOURCE', ROOT / 'kodi'))
        self.assertTrue(base.is_dir(), 'Pinned source fixture required')
        for name in source_patch.FILES:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(base / name, destination)

    def test_exact_source_call_and_packaging_registration(self):
        self.fixture()
        receipt = source_patch.apply(self.root)
        self.assertEqual(len(receipt['changes']), 4)
        self.assertFalse(receipt['crash_fixed'])
        main = (self.root / 'tools/android/packaging/xbmc/src/Main.java.in').read_text()
        self.assertEqual(main.count('InfinityExitDiagnostics.start(getApplicationContext());'), 1)
        self.assertLess(main.index('InfinityExitDiagnostics.start('), main.index('System.loadLibrary('))
        cmake = (self.root / 'cmake/scripts/android/Install.cmake').read_text()
        for name in ('InfinityDiagnosticFiles.java', 'InfinityExitDiagnostics.java'):
            self.assertEqual(cmake.count('src/' + name), 1)

    def test_preimage_failure_changes_nothing(self):
        self.fixture()
        path = self.root / 'cmake/scripts/android/Install.cmake'
        path.write_text(path.read_text() + '\n# unrelated change\n')
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'preimage'):
            source_patch.apply(self.root)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_duplicate_application_fails_without_changes(self):
        self.fixture()
        source_patch.apply(self.root)
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaises(ValueError):
            source_patch.apply(self.root)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_collector_does_not_touch_player_or_replace_crash_handler(self):
        text = (ROOT / 'patches/infinity-compat/InfinityExitDiagnostics.java.in').read_text()
        for unsafe in ('setDefaultUncaughtExceptionHandler(', 'Runtime.getRuntime().exec(',
                       'System.loadLibrary(', '_infinityGetState(', 'killProcess('):
            self.assertNotIn(unsafe, text)
        self.assertIn('getHistoricalProcessExitReasons(\n          app.getPackageName(), 0, MAX_RECORDS)', text)
        self.assertNotRegex(text, r'(?m)^\s*(?:public |private |protected )?(?:static )?native\s')
        self.assertIn('Build.VERSION.SDK_INT >= 30', text)
        self.assertIn('Build.VERSION.SDK_INT >= 31', text)


if __name__ == '__main__':
    unittest.main()
