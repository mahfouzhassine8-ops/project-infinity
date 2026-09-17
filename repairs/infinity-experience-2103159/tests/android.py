#!/usr/bin/env python3
"""Re-run all locked 2103158 Android gates, then exercise the real Splash theme bridge."""
from pathlib import Path
import argparse,os,shutil,signal,subprocess,threading

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
 if process.returncode:raise subprocess.CalledProcessError(process.returncode,command)
def copy_results(app,out):
 for rel in ('build/test-results/testReleaseUnitTest','build/reports/tests/testReleaseUnitTest'):
  src=app/rel
  if src.exists():shutil.copytree(src,out/src.parent.name,dirs_exist_ok=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 parent=out/'locked2103158';subprocess.run(['python3','health-delta/repairs/cobra-health-2103158/tests/android.py','--build',str(build),'--out',str(parent)],check=True)
 app=build/'xbmc';test=app/'src/test/java/com/projectinfinity/kodi';test.mkdir(parents=True,exist_ok=True);shutil.copy2(Path(__file__).with_name('ExperienceChooserUiTest.java'),test)
 with (app/'build.gradle').open('a') as f:f.write('''\nandroid.testOptions.unitTests.all { systemProperty "experience.theme.source", System.getenv("EXPERIENCE_THEME_SOURCE") }\n''')
 exp=out/'experience';env=dict(os.environ,COBRA_EVIDENCE=str(exp/'screenshots'),EXPERIENCE_THEME_SOURCE=str((Path('experience-delta/repairs/infinity-experience-2103159/experience-theme.json')).resolve()))
 command=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest','--tests','com.projectinfinity.kodi.ExperienceChooserUiTest','--stacktrace']
 run_process(command,build,env,exp,300);copy_results(app,exp)
 print('PASS: all locked 2103158 Android gates plus themed Splash rendering/behavior; physical display acceptance pending')
if __name__=='__main__':main()
