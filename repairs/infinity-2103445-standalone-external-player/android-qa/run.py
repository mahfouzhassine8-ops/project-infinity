"""Finite real Android source/provider -> Splash -> decoder -> UI -> source journey.

Only a fresh emulator, QA-key copy, public input, OS evidence and synthetic media.
No callbacks are invoked directly. No app shutdown, force-stop, clear or uninstall.
"""
import argparse,hashlib,json,re,subprocess,time,traceback,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
import io
P='com.projectinfinity.kodi';SOURCE='qa.external.source'
steps=[];sequence=0;out=None
def run(*args,timeout=45):return subprocess.check_output(list(map(str,args)),timeout=timeout)
def adb(*args,timeout=45):return run('adb',*args,timeout=timeout)
def shell(*args,timeout=45):return adb('shell',*args,timeout=timeout).decode(errors='replace')
def check(ok,why):
 if not ok:raise AssertionError(why)
def record(check_name,**values):steps.append(dict(check=check_name,**values))
def screenshot(name):
 raw=adb('exec-out','screencap','-p');(out/(name+'.png')).write_bytes(raw);return Image.open(io.BytesIO(raw)).convert('RGB')
def nodes():
 shell('uiautomator','dump','/sdcard/external-player-window.xml',timeout=20)
 raw=shell('cat','/sdcard/external-player-window.xml');return ET.fromstring(raw)
def bounds(n):return list(map(int,re.findall(r'\d+',n.attrib.get('bounds',''))))
def find(tree,label):
 for n in tree.iter('node'):
  if label in (n.attrib.get('text'),n.attrib.get('content-desc')):
   b=bounds(n)
   if len(b)==4 and b[2]>b[0] and b[3]>b[1] and n.attrib.get('enabled')=='true':return n
 return None
def text(tree):return '\n'.join(n.attrib.get('text','') for n in tree.iter('node'))
def tap(label):
 tree=nodes();n=find(tree,label);check(n is not None,'Visible actual target: '+label)
 b=bounds(n);shell('input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));record('real_touch',label=label,bounds=b)
def await_text(label,seconds=18):
 start=time.monotonic();last=None
 while time.monotonic()-start<seconds:
  last=nodes()
  if find(last,label) is not None:return last
  # Preserve the already known platform warning. Dismiss OK only, never disable.
  t=text(last)
  if ('page size' in t.lower() or '16 kb' in t.lower()) and find(last,'OK') is not None:
   screenshot('platform-page-size-notice');tap('OK');record('platform_notice_dismissed_once')
  time.sleep(.2)
 if last is not None:(out/'missing-target.xml').write_bytes(ET.tostring(last))
 raise AssertionError('UI target not observed: '+label)
def no_kodi():
 probe=subprocess.run(['adb','shell','pidof',P+':kodi'],capture_output=True,text=True,timeout=15)
 check(probe.returncode in (0,1),'Process observation failed')
 observed=probe.stdout.strip()
 check(not observed,'External playback unexpectedly started Kodi: '+observed)
 top=shell('dumpsys','activity','activities');check('InfinityExternalPlayerActivity' in top,'Private external Activity missing')
 record('no_kodi_process',kodi_pid=observed,external_pid=shell('pidof',P+':externalplayer').strip())
def open_video(label,color,title):
 await_text(label);tap(label);await_text(title);strip_to('Pause');await_text('Pause')
 im=screenshot('video-'+title.replace('.','-')+'-'+str(len(steps)))
 w,h=im.size;matches=0
 for y in range(h//3,h*2//3,max(1,h//30)):
  for x in range(w//4,w*3//4,max(1,w//30)):
   r,g,b=im.getpixel((x,y))
   if (color=='red' and r>80 and r>g*2 and r>b*2) or (color=='green' and g>50 and g>r*2 and g>b*2) or (color=='blue' and b>80 and b>r*2 and b>g*2):matches+=1
 check(matches>30,'Decoded expected video pixels: '+title+' '+str(matches))
 check('Loading' not in text(nodes()) and 'Buffering' not in text(nodes()),'Stale loading during playback')
 no_kodi();record('actual_video_decoded',title=title,color_samples=matches)
def source_return(action='Back'):
 if action=='Back':shell('input','keyevent','4');record('real_android_back')
 else:strip_to(action);tap(action)
 await_text('External video source fixture');record('originating_activity_return',action=action)
def strip_to(label):
 for _ in range(4):
  tree=nodes()
  if find(tree,label) is not None:return
  strips=[n for n in tree.iter('node') if n.attrib.get('class')=='android.widget.HorizontalScrollView']
  check(strips,'Playback control scroll owner missing');b=bounds(strips[0]);y=(b[1]+b[3])//2
  left=b[0]+30;right=b[2]-30
  start,end=(left,right) if label in ('Pause','Play','Stop') else (right,left)
  shell('input','swipe',str(start),str(y),str(end),str(y),'250')
 raise AssertionError('Control not reachable: '+label)
def body(a):
 serial=shell('getprop','ro.kernel.qemu').strip();check(serial=='1','Fresh Android emulator only')
 check(not shell('pm','list','packages',P).strip(),'Do not replace an existing app installation')
 for name in ['candidate','source']:
  apk=a.prepared/(name+'-qa.apk');start=time.monotonic()
  adb('install','--no-streaming',str(apk),timeout=240);elapsed=time.monotonic()-start
  record('fresh_fixture_install',name=name,seconds=elapsed,bytes=apk.stat().st_size,sha256=hashlib.sha256(apk.read_bytes()).hexdigest())
 remote=shell('pm','path',P).strip().split('package:')[-1]
 installed=shell('sha256sum',remote).split()[0]
 check(installed==hashlib.sha256((a.prepared/'candidate-qa.apk').read_bytes()).hexdigest(),'Installed APK exact bytes')
 shell('am','start','-n',SOURCE+'/qa.external.SourceActivity');await_text('Open A')
 tap('Handler labels');await_text('Handlers: 1');check('Infinity Preview | Infinity' in text(nodes()),'Global video handler/application labels')
 screenshot('handler-labels');tap('OK');record('one_handler_label',application='Infinity',handler='Infinity Preview')
 open_video('Open A','red','a.mp4')
 # Public decoded/audio evidence is captured while the real fixture is playing.
 for service in ['media.player','media.codec','media.metrics','media.audio_flinger','audio','activity processes']:
  try:(out/(service.replace(' ','-')+'.txt')).write_text(shell('dumpsys',*service.split()))
  except Exception as e:record('optional_OS_dump_unavailable',service=service,error=str(e))
 before=text(nodes());time.sleep(1.2);after=text(nodes());check(before!=after,'Actual playback time must advance');record('advancing_media_clock')
 tap('Pause');await_text('Play');paused=text(nodes());time.sleep(1.2);check(text(nodes())==paused,'Paused clock changed');record('pause_stops_clock')
 tap('Play');await_text('Pause')
 tree=nodes();s=find(tree,'Seek video');check(s is not None,'Actual seekbar');b=bounds(s)
 shell('input','tap',str(b[0]+(b[2]-b[0])//4),str((b[1]+b[3])//2));time.sleep(.5)
 clock=text(nodes());match=re.search(r'\b(\d+):(\d\d) / 10:00',clock)
 check(match is not None and 130<=int(match[1])*60+int(match[2])<=175,'Seek changes actual playback position');record('seek_changes_position')
 strip_to('Mute');tap('Mute');await_text('Unmute');tap('Unmute');await_text('Mute');record('mute_toggle')
 strip_to('Audio');tap('Audio');await_text('Audio');screenshot('audio-menu');shell('input','keyevent','4')
 strip_to('Subtitles');tap('Subtitles');await_text('Subtitles');screenshot('subtitle-menu');shell('input','keyevent','4')
 strip_to('Display');tap('Display');await_text('Fill (crop)');tap('Fill (crop)');record('display_real_choice')
 strip_to('Auto rotate');tap('Auto rotate');await_text('Rotation locked');tap('Rotation locked');await_text('Auto rotate');record('rotation_toggle')
 # Real viewport change uses the same Activity and current request.
 shell('wm','size','1600x1680');shell('wm','density','320');await_text('a.mp4');screenshot('inner-video');no_kodi();record('inner_resize')
 shell('wm','size','1680x1600');await_text('a.mp4');screenshot('landscape-video');record('landscape_resize')
 shell('wm','size','1080x2520');shell('wm','density','420');await_text('a.mp4')
 # Home/return does not create another player or wake Kodi.
 shell('input','keyevent','3');time.sleep(.5)
 shell('am','start','-n',SOURCE+'/qa.external.SourceActivity');await_text('Open B')
 open_video('Open B','green','b.mp4');source_return('Stop')
 open_video('Share B','green','b.mp4');source_return()
 open_video('Rapid A B C','blue','c.mp4');time.sleep(1);await_text('c.mp4');source_return()
 open_video('Open A','red','a.mp4');source_return();open_video('Open A','red','a.mp4');source_return()
 open_video('HTTP A','red','a.mp4');source_return()
 for label in ['Denied A','Open BAD','Open AUDIO']:
  tap(label);await_text('Retry');check('Loading' not in text(nodes()),'Error must remove loading');screenshot(label.replace(' ','-'));source_return();record('source_failure',source=label)
 tap('Open END');await_text('Video ended',20);check('Loading' not in text(nodes()),'Natural completion loading');source_return();record('natural_end')
 # All external Activities have finished; OS may retain an idle process.
 activity=shell('dumpsys','activity','activities');(out/'final-activities.txt').write_text(activity)
 check('mResumedActivity' in activity and 'qa.external.SourceActivity' in activity,'Source remains active')
 logs=shell('logcat','-d','-v','threadtime');(out/'logcat.txt').write_text(logs)
 check('FATAL EXCEPTION' not in logs,'Android crash in selected journey')
 record('journey_complete')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out;out.mkdir(parents=True)
 status='FAIL'
 try:body(a);status='PASS'
 except Exception:
  (out/'FAILURE.txt').write_text(traceback.format_exc())
  try:screenshot('failure');(out/'failure-logcat.txt').write_text(shell('logcat','-d','-v','threadtime'))
  except Exception:pass
  raise
 finally:
  (out/'RESULT.json').write_text(json.dumps({'status':status,'checks':steps,'source_build':json.loads((a.prepared/'BUILD.json').read_text()),'physical_fold':'NOT_TESTED','third_party_accounts':'NOT_TESTED','shutdown':'NOT_RUN'},indent=2)+'\n')
