#!/usr/bin/env python3
"""Host-only regression checks for run 35273743474's missing Gradle test environment."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('experience_android_runner',Path(__file__).with_name('android.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class AndroidRunnerTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);self.store=self.root/'debug.keystore'
  self.store.write_bytes(b'fixture-only; never used for APK signing')
  self.theme=self.root/'experience.json';self.theme.write_text('{}')
 def env(self,**kwargs):
  return runner.test_environment(self.root/'evidence',self.theme,environ=kwargs,keystore=self.store)
 def test_missing_kodi_variables_are_supplied_not_inferred_from_infinity_secrets(self):
  source={'INFINITY_KEYSTORE_B64':'not-a-store-path'}
  self.assertNotIn('KODI_ANDROID_STORE_FILE',source)
  env=self.env(**source)
  self.assertEqual(env['KODI_ANDROID_STORE_FILE'],str(self.store.resolve()))
  self.assertEqual(env['KODI_ANDROID_KEY_ALIAS'],'androiddebugkey')
  self.assertEqual(env['KODI_ANDROID_KEY_PASSWORD'],'android')
  self.assertEqual(env['KODI_ANDROID_STORE_PASSWORD'],'android')
 def test_release_credentials_are_not_forwarded_or_mutated(self):
  source={key:'private-fixture' for key in runner.RELEASE_SECRETS}
  source.update(KODI_ANDROID_STORE_FILE='production.jks',KODI_ANDROID_KEY_ALIAS='release',PATH='/test/path')
  original=dict(source);env=self.env(**source)
  self.assertEqual(source,original)
  self.assertTrue(all(key not in env for key in runner.RELEASE_SECRETS))
  self.assertNotEqual(env['KODI_ANDROID_STORE_FILE'],'production.jks')
  self.assertEqual(env['PATH'],'/test/path')
 def test_missing_or_empty_debug_store_fails_closed(self):
  for path in (self.root/'missing.jks',self.root/'empty.jks',self.root):
   if path.name=='empty.jks':path.touch()
   with self.subTest(path=path),self.assertRaisesRegex(RuntimeError,'debug.keystore'):
    runner.test_environment(self.root,environ={},keystore=path)
 def test_missing_theme_fails_before_gradle(self):
  with self.assertRaisesRegex(RuntimeError,'theme is missing'):
   runner.test_environment(self.root,self.root/'missing.json',environ={},keystore=self.store)
 def test_paths_are_absolute_and_evidence_is_suite_specific(self):
  env=self.env()
  self.assertEqual(env['COBRA_EVIDENCE'],str(self.root/'evidence/screenshots'))
  self.assertEqual(env['EXPERIENCE_THEME_SOURCE'],str(self.theme))
  parent=runner.test_environment(self.root/'parent',environ={},keystore=self.store)
  self.assertNotEqual(parent['COBRA_EVIDENCE'],env['COBRA_EVIDENCE'])
 def test_real_child_process_receives_complete_test_contract(self):
  script="import os; from pathlib import Path; assert Path(os.environ['KODI_ANDROID_STORE_FILE']).is_file(); assert os.environ['KODI_ANDROID_KEY_ALIAS']=='androiddebugkey'; assert os.environ['KODI_ANDROID_STORE_PASSWORD']=='android'; assert os.environ['KODI_ANDROID_KEY_PASSWORD']=='android'; assert 'INFINITY_KEYSTORE_B64' not in os.environ; print('test environment received')"
  with contextlib.redirect_stdout(io.StringIO()):
   runner.run_process([sys.executable,'-c',script],self.root,self.env(),self.root/'child',10)
  self.assertIn('test environment received',(self.root/'child/android-tests.log').read_text())
 def test_failed_tests_keep_reports_and_remain_failed(self):
  build=self.root/'build';app=build/'xbmc'
  xml=app/'build/test-results/testReleaseUnitTest/TEST-failed.xml';xml.parent.mkdir(parents=True);xml.write_text('<testsuite failures="1"/>')
  html=app/'build/reports/tests/testReleaseUnitTest/index.html';html.parent.mkdir(parents=True);html.write_text('failure evidence')
  with patch.object(runner,'run_process',side_effect=subprocess.CalledProcessError(1,['gradle'])):
   with self.assertRaises(subprocess.CalledProcessError):runner.run_ui_gate(['gradle'],build,self.env(),self.root/'failed')
  self.assertEqual((self.root/'failed/test-results/TEST-failed.xml').read_bytes(),xml.read_bytes())
  self.assertEqual((self.root/'failed/tests/index.html').read_bytes(),html.read_bytes())
 def health_file(self):
  p=self.root/'CobraHealthUiTest.java'
  p.write_bytes(b'// retained\r\ncall(a,"toggleCobraDrawer");click(a,"cobra-drawer-health");\r\n// assertions retained\r\n');return p
 def test_inherited_fixture_restored_after_success(self):
  p=self.health_file();original=p.read_bytes()
  with runner.health_navigation_fixture(p):
   self.assertIn(b'call(a,"showSettings")',p.read_bytes())
   self.assertIn(b'// assertions retained\r\n',p.read_bytes())
  self.assertEqual(p.read_bytes(),original)
 def test_inherited_fixture_restored_after_failure(self):
  p=self.health_file();original=p.read_bytes()
  with self.assertRaisesRegex(RuntimeError,'test failed'):
   with runner.health_navigation_fixture(p):raise RuntimeError('test failed')
  self.assertEqual(p.read_bytes(),original)
 def test_changed_inherited_anchor_is_rejected_without_writing(self):
  p=self.health_file();p.write_text('unknown fixture');original=p.read_bytes()
  with self.assertRaisesRegex(RuntimeError,'anchor changed'):
   with runner.health_navigation_fixture(p):self.fail('must not run')
  self.assertEqual(p.read_bytes(),original)
 def test_main_supplies_both_gradle_stages_and_preserves_release_sentinel(self):
  build=self.root/'build';app=build/'xbmc';app.mkdir(parents=True);(app/'build.gradle').write_text('// fixture')
  home=self.root/'home';(home/'.android').mkdir(parents=True);(home/'.android/debug.keystore').write_bytes(self.store.read_bytes())
  health=self.root/'health-delta/repairs/cobra-health-2103158/tests/CobraHealthUiTest.java';health.parent.mkdir(parents=True);health.write_bytes(self.health_file().read_bytes());original=health.read_bytes()
  release=self.root/'signed159/already-signed.apk';release.parent.mkdir();release.write_bytes(b'untouched signed delivery');signed=release.read_bytes()
  previous=Path.cwd()
  try:
   os.chdir(self.root)
   with patch.object(Path,'home',return_value=home),patch.dict(os.environ,{},clear=True),patch.object(sys,'argv',['android.py','--build',str(build),'--out',str(self.root/'out')]),patch.object(runner.subprocess,'run') as inherited,patch.object(runner,'run_process') as current,contextlib.redirect_stdout(io.StringIO()):
    runner.main()
   parent_env=inherited.call_args.kwargs['env'];child_env=current.call_args.args[2]
   for key in ('KODI_ANDROID_STORE_FILE','KODI_ANDROID_STORE_PASSWORD','KODI_ANDROID_KEY_PASSWORD','KODI_ANDROID_KEY_ALIAS'):
    self.assertTrue(parent_env[key]);self.assertEqual(parent_env[key],child_env[key])
   command=current.call_args.args[0]
   self.assertIn('com.projectinfinity.kodi.ExperienceChooserUiTest',command)
   self.assertIn('com.projectinfinity.kodi.Cobra2103159UiTest',command)
   self.assertEqual(health.read_bytes(),original);self.assertEqual(release.read_bytes(),signed)
  finally:os.chdir(previous)

if __name__=='__main__':unittest.main(verbosity=2)
