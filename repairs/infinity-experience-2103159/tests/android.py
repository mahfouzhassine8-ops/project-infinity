#!/usr/bin/env python3
"""Run Cobra 2103159 regression/UI gates, then exercise the real Splash theme bridge."""
from pathlib import Path
import argparse,os,shutil,signal,subprocess,threading
from contextlib import contextmanager

RELEASE_SECRETS=('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')

def test_environment(out,theme=None,*,environ=None,keystore=None):
 # Unit tests evaluate the release Gradle project, but never sign the delivery APK.
 # Match the locked 2103158 harness's KODI_ANDROID_* contract, not INFINITY_* secrets.
 store=(Path.home()/'.android/debug.keystore' if keystore is None else Path(keystore)).resolve()
 if not store.is_file() or store.stat().st_size==0:
  raise RuntimeError('Android UI tests require the reconstruction debug.keystore; release signing is not a fallback')
 env=dict(os.environ if environ is None else environ)
 for key in RELEASE_SECRETS:env.pop(key,None)
 env.update(COBRA_EVIDENCE=str(Path(out).resolve()/'screenshots'),KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(store))
 if theme is not None:
  source=Path(theme).resolve()
  if not source.is_file():raise RuntimeError('Experience UI test theme is missing: '+str(source))
  env['EXPERIENCE_THEME_SOURCE']=str(source)
 return env

@contextmanager
def health_navigation_fixture(health):
 # Adapt only a disposable inherited test checkout, and restore it even on failure.
 # The dedicated 2103159 UI test exercises the actual Settings -> Health button.
 original=health.read_bytes();text=original.decode('utf-8')
 old='call(a,"toggleCobraDrawer");click(a,"cobra-drawer-health");'
 new='call(a,"showSettings");ui.measure(a,412,915);call(a,"showCobraHealthCenter");'
 if text.count(old)!=1:raise RuntimeError('Locked health navigation test anchor changed')
 try:
  health.write_bytes(text.replace(old,new,1).encode('utf-8'));yield
 finally:health.write_bytes(original)


def run_process(command,cwd,env,out,timeout=300):
 out.mkdir(parents=True,exist_ok=True);process=subprocess.Popen(command,cwd=cwd,env=env,start_new_session=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 def log():
  with (out/'android-tests.log').open('w') as f:
   for line in process.stdout:f.write(line);f.flush();print(line,end='',flush=True)
 reader=threading.Thread(target=log,daemon=True);reader.start()
 try:process.wait(timeout=timeout)
 finally:
  if process.poll() is None:
   os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
  reader.join(timeout=5)
  if not reader.is_alive():process.stdout.close()
 if process.returncode:raise subprocess.CalledProcessError(process.returncode,command)
def copy_results(app,out):
 for rel in ('build/test-results/testReleaseUnitTest','build/reports/tests/testReleaseUnitTest'):
  src=app/rel
  if src.exists():shutil.copytree(src,out/src.parent.name,dirs_exist_ok=True)
def run_ui_gate(command,build,env,out):
 try:run_process(command,build,env,out,300)
 finally:copy_results(build/'xbmc',out)

def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 here=Path(__file__).resolve().parent
 parent=out/'cobra-regression';exp=out/'experience'
 parent_env=test_environment(parent)
 env=test_environment(exp,here.parent/'experience-theme.json')
 with health_navigation_fixture(Path('health-delta/repairs/cobra-health-2103158/tests/CobraHealthUiTest.java')):
  subprocess.run(['python3','health-delta/repairs/cobra-health-2103158/tests/android.py','--build',str(build),'--out',str(parent)],env=parent_env,check=True)
 app=build/'xbmc';test=app/'src/test/java/com/projectinfinity/kodi';test.mkdir(parents=True,exist_ok=True)
 here=Path(__file__).resolve().parent;shutil.copy2(here/'ExperienceChooserUiTest.java',test);shutil.copy2(here/'Cobra2103159UiTest.java',test)
 with (app/'build.gradle').open('a') as f:f.write('''\nandroid.testOptions.unitTests.all { systemProperty "experience.theme.source", System.getenv("EXPERIENCE_THEME_SOURCE") }\n''')
 command=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest','--tests','com.projectinfinity.kodi.ExperienceChooserUiTest','--tests','com.projectinfinity.kodi.Cobra2103159UiTest','--stacktrace']
 run_ui_gate(command,build,env,exp)
 print('PASS: inherited Cobra health/navigation gates + 2103159 drawer/settings/power + themed Splash rendering; physical display acceptance pending')
if __name__=='__main__':main()
