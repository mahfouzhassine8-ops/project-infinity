"""Selected Preview resume checks; public touches, real decoder and synthetic grants.

Reuses the proven immediate OS observer and compatibility-notice handling.
Only a fresh disposable emulator: no user data, shutdown suite or app test hooks.
"""
import argparse,hashlib,importlib.util,json,re,sqlite3,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parents[1];R=H.parents[1]
spec=importlib.util.spec_from_file_location('external_observer',R/'repairs/infinity-2103445-standalone-external-player/android-qa/run.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
def seconds(value):
 parts=list(map(int,value.split(':')));return sum(n*60**i for i,n in enumerate(reversed(parts)))
def clock():
 m=re.search(r'(\d+:\d\d(?::\d\d)?) / 10:00',q.text(q.nodes()))
 q.check(m is not None,'Real media clock unavailable');return seconds(m[1])
def pause():
 q.strip_to('Pause');q.tap('Pause');q.await_text('Play');time.sleep(.3);return clock()
def seek(fraction):
 tree=q.nodes();n=q.find(tree,'Seek video');q.check(n is not None,'Real seekbar missing');b=q.bounds(n)
 q.shell('input','tap',str(b[0]+int((b[2]-b[0])*fraction)),str((b[1]+b[3])//2))
 deadline=q.feature_time()+18
 while q.feature_time()<deadline:
  value=clock()
  if abs(value-600*fraction)<12:return value
  time.sleep(.2)
 raise AssertionError('Actual seek did not reach expected region')
def offer(label,expected,choice='Resume'):
 q.await_text(label);q.tap(label);q.await_text('Resume video?')
 words=q.text(q.nodes());m=re.search(r'Continue from (\d+:\d\d(?::\d\d)?)\?',words)
 q.check(m is not None and abs(seconds(m[1])-expected)<=2,'Wrong per-video offered time: '+words)
 q.check('Loading' not in words,'Loading obscures prepared resume choice')
 q.screenshot('resume-choice-'+str(len(q.steps)));q.tap(choice);q.await_text('Pause');time.sleep(.3)
 value=clock();q.check(abs(value-(expected if choice=='Resume' else 0))<=3,'Actual chosen seek position: '+str(value))
 q.record('real_resume_choice',label=label,choice=choice,expected=expected,actual=value)
 q.no_kodi();return value
def history():
 # Read only this new synthetic fixture namespace; no Kodi/Cobra data access.
 raw=q.adb('exec-out','cat','/data/user/0/'+q.P+'/databases/infinity_preview_resume_v1.db')
 db=sqlite3.connect(':memory:');db.deserialize(raw)
 q.check(db.execute('pragma quick_check').fetchone()[0]=='ok','Consistent history snapshot')
 rows=db.execute('select position,duration from video').fetchall();db.close();return rows
def stop_observer():
 if q.observer is not None:
  try:q.observer.stdin.write(b'QUIT\n');q.observer.stdin.flush();q.observer.wait(timeout=5)
  except Exception:q.observer.terminate()
  q.observer=None
def source():q.shell('am','start','-n',q.SOURCE+'/qa.external.SourceActivity');q.await_text('Open A')
def body(a):
 q.check(q.shell('getprop','ro.kernel.qemu').strip()=='1','Disposable emulator only')
 q.check(not q.shell('pm','list','packages',q.P).strip(),'No existing installation may be replaced in this fixture')
 q.adb('root');q.adb('wait-for-device');q.check('uid=0' in q.shell('id'),'Read-only synthetic history observation requires emulator root')
 for name in ('candidate','source'):
  apk=a.prepared/(name+'-qa.apk');started=time.monotonic();q.adb('install','--no-streaming',apk,timeout=240)
  q.record('fresh_fixture_install',name=name,seconds=time.monotonic()-started,sha256=hashlib.sha256(apk.read_bytes()).hexdigest())
 remote=q.shell('pm','path',q.P).strip().split('package:')[-1]
 q.check(q.shell('sha256sum',remote).split()[0]==hashlib.sha256((a.prepared/'candidate-qa.apk').read_bytes()).hexdigest(),'Installed exact tested bytes')
 q.start_observer(a.prepared);source()
 q.open_video('Open A','red','a.mp4');seek(.25);a_position=pause();q.source_return()
 q.open_video('Open B','green','b.mp4');seek(.4);b_position=pause();q.source_return('Stop')
 offer('Open A',a_position);a_position=pause();q.source_return('Close')
 offer('Open B',b_position);b_position=pause();q.source_return()
 q.record('separate_A_B_A_B',A=a_position,B=b_position)
 offer('Alias A',a_position);a_position=pause();q.source_return()
 q.record('two_authorities_same_granted_file_share_identity',A=a_position)
 # Periodic save is observed while the real decoder is still playing, before
 # Pause/Back/background could create a lifecycle checkpoint.
 offer('Open A',a_position);seek(.5);time.sleep(11.5)
 now=clock();rows=history();q.check(any(0<=now*1000-p<=12000 for p,d in rows if 590000<=d<=610000),'Periodic checkpoint absent during active decoding')
 q.record('periodic_real_decoder_checkpoint',clock_seconds=now,stored_positions=rows)
 # Home followed by a fresh, granted source request; never directly start the
 # private non-exported Activity or alter its existing task/manifest behavior.
 q.shell('input','keyevent','3');time.sleep(.5)
 saved=max(p for p,d in history())//1000;source();offer('Open A',saved)
 q.check(clock()>=now-2,'Background progress lost');a_position=pause();q.source_return()
 q.record('background_progress_preserved',position=a_position)
 pid=q.shell('pidof',q.P+':externalplayer').strip();q.shell('am','kill',q.P)
 deadline=time.monotonic()+18
 while time.monotonic()<deadline:
  p=q.shell('sh','-c','pidof '+q.P+':externalplayer || true').strip()
  if not p:break
  time.sleep(.2)
 q.check(not p,'Stopped Preview process was not reclaimed')
 offer('Open A',a_position);q.check(q.shell('pidof',q.P+':externalplayer').strip()!=pid,'New decoder process required')
 a_position=pause();q.source_return();q.record('process_restart_keeps_progress',position=a_position)
 # Start Over clears every known alias for this video, including the original
 # provider URI when the choice was made through a second granted authority.
 offer('Alias A',a_position,'Start Over');q.source_return()
 q.open_video('Open A','red','a.mp4');q.source_return();q.record('start_over_clears_all_video_aliases')
 # Real device reboot, no reset, no application shutdown APIs or native engine.
 stop_observer();q.adb('reboot');q.adb('wait-for-device',timeout=120)
 deadline=time.monotonic()+120
 while time.monotonic()<deadline:
  if q.shell('getprop','sys.boot_completed').strip()=='1':break
  time.sleep(1)
 q.check(q.shell('getprop','sys.boot_completed').strip()=='1','Reboot not completed')
 q.shell('input','keyevent','224');q.shell('wm','dismiss-keyguard');q.start_observer(a.prepared);source()
 offer('Open B',b_position);b_position=pause();q.source_return();q.record('reboot_keeps_private_resume_database',B=b_position)
 # Cover, inner and landscape dimensions: actual observed screenshot bounds,
 # real seek/control-strip gestures; no claim of physical Fold hardware.
 for viewport in ('1080x2520','1600x1680','2520x1080'):
  q.shell('wm','size',viewport);source();q.open_video('Open C','blue','c.mp4')
  im=q.screenshot('viewport-'+viewport);q.check(tuple(map(int,viewport.split('x')))==im.size,'Actual viewport differs from requested dimensions')
  for theme in ('yes','no'):
   q.shell('cmd','uimode','night',theme);q.await_text('Pause');q.strip_to('Display');q.tap('Display');q.await_text('Best Fit');q.tap('Best Fit');q.strip_to('Pause')
   q.record('existing_dark_UI_controls_preserved_under_system_theme',viewport=viewport,system_night=theme)
  seek(.01);q.source_return()
 q.shell('wm','size','1080x2520');source()
 q.open_video('Rapid A B C','blue','c.mp4');q.source_return();q.record('rapid_replacement_keeps_latest_video')
 offer('Open B',b_position);seek(.98);q.source_return();q.open_video('Open B','green','b.mp4');q.source_return();q.record('near_end_resets_progress')
 for label in ('Denied A','Open BAD'):
  q.tap(label);q.await_text('Retry');q.check('Loading' not in q.text(q.nodes()),'Error leaves stale loading');q.source_return()
 q.final_cleanup();logs=q.shell('logcat','-d','-v','threadtime');(q.out/'logcat.txt').write_text(logs)
 q.check('FATAL EXCEPTION' not in logs,'Crash in selected journey');q.record('resume_journey_complete')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True);q.out=a.out;status='FAIL'
 try:body(a);status='PASS'
 except Exception:
  (a.out/'FAILURE.txt').write_text(traceback.format_exc())
  try:q.screenshot('failure');(a.out/'failure-logcat.txt').write_text(q.shell('logcat','-d','-v','threadtime'))
  except Exception:pass
  raise
 finally:
  stop_observer();(a.out/'RESULT.json').write_text(json.dumps(dict(status=status,checks=q.steps,source_build=json.loads((a.prepared/'BUILD.json').read_text()),physical_Fold='NOT_TESTED',proprietary_file_managers='NOT_TESTED',cinematic_design='UNIMPLEMENTED_PRESERVED_SEPARATELY',shutdown='NOT_RUN'),indent=2)+'\n')
