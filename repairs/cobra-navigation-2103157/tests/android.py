#!/usr/bin/env python3
"""Gate signed upload on real Android view/navigation tests; bounded host-vsync, no provider video."""
from pathlib import Path
import argparse,os,shutil,signal,subprocess,threading,time

def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 app=build/'xbmc';test=app/'src/test/java/com/projectinfinity/kodi';test.mkdir(parents=True,exist_ok=True)
 shutil.copy2(Path(__file__).with_name('CobraNavigationUiTest.java'),test)
 with (app/'build.gradle').open('a') as f:f.write('''
// Host test dependencies only. The already verified release APK contains none of these.
android.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
 maxHeapSize = "3g"
 maxParallelForks = 1
 systemProperty "cobra.evidence", System.getenv("COBRA_EVIDENCE")
 testLogging { events "started", "passed", "failed", "skipped"; showStandardStreams = true; exceptionFormat = "full" }
}
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1' }
''')
 env=dict(os.environ,COBRA_EVIDENCE=str(out/'screenshots'),KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
 command=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest','--tests','com.projectinfinity.kodi.CobraNavigationUiTest','--stacktrace']
 process=subprocess.Popen(command,cwd=build,env=env,start_new_session=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 def log():
  with (out/'android-tests.log').open('w') as f:
   for line in process.stdout:f.write(line);f.flush();print(line,end='',flush=True)
 reader=threading.Thread(target=log,daemon=True);reader.start()
 try:process.wait(timeout=300)
 except subprocess.TimeoutExpired:
  listing=subprocess.run(['jps','-l'],capture_output=True,text=True,timeout=10)
  for line in listing.stdout.splitlines():
   if 'GradleWorkerMain' in line:
    r=subprocess.run(['jcmd',line.split()[0],'Thread.print'],capture_output=True,text=True,timeout=15);(out/('threads-'+line.split()[0]+'.txt')).write_text(r.stdout+r.stderr)
  raise
 finally:
  if process.poll() is None:
   os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
  reader.join(timeout=5)
  for rel in ('build/test-results/testReleaseUnitTest','build/reports/tests/testReleaseUnitTest'):
   src=app/rel
   if src.exists():shutil.copytree(src,out/src.parent.name,dirs_exist_ok=True)
 if process.returncode:raise subprocess.CalledProcessError(process.returncode,command)
 print('PASS: Android navigation/rendering gate; physical decoder/provider acceptance still required')
if __name__=='__main__':main()
