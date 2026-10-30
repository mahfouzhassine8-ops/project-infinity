"""One finite exact-APK Cobra launch on a fresh disposable API37 emulator.
No Infinity launch, root/data injection, restart, clear, teardown or shutdown.
"""
import argparse,hashlib,json,math,re,subprocess,time,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
PACKAGE='com.projectinfinity.kodi'
def adb(*args,check=True,timeout=30):
 p=subprocess.run(['adb',*args],capture_output=True,text=True,timeout=timeout)
 if check and p.returncode:raise RuntimeError('adb '+str(args[:2])+': '+p.stderr[-1500:])
 return p.stdout

def confirm_installed_apk(expected,apk_io_timeout=30):
 paths=adb('shell','pm','path',PACKAGE).strip().splitlines()
 assert len(paths)==1 and paths[0].startswith('package:'),'One installed base APK required'
 path=paths[0][len('package:'):]
 assert re.fullmatch(r'/data/app/[A-Za-z0-9_~+./=-]+/base\.apk',path) and '..' not in path.split('/'),'Unexpected installed APK path'
 observed=adb('shell','sha256sum',path,timeout=apk_io_timeout).split()
 assert observed and observed[0]==expected,'Installed APK does not match the exact signed artifact'
 return {'installed_base_apk':path,'installed_apk_sha256':observed[0]}

def compatibility_notice_ok(tree,native_paths):
 nodes=list(tree.iter('node'))
 def one(resource,text=None):
  matches=[n for n in nodes if n.get('package')=='android' and n.get('resource-id')==resource and (text is None or n.get('text')==text)]
  return matches[0] if len(matches)==1 else None
 title=one('android:id/alertTitle','Android App Compatibility')
 message=one('android:id/message');ok=one('android:id/button2','OK')
 persistent=one('android:id/button1',"Don't Show Again")
 if title is None or message is None or ok is None or persistent is None:return None
 body=message.get('text','')
 if ('This app will be run using page size compatible mode.' not in body or
     'LOAD segment and RELRO segment alignment checks failed.' not in body):return None
 libraries=set(re.findall(r'lib/arm64-v8a/[A-Za-z0-9_.+-]+\.so',body))
 if not libraries or not libraries<=native_paths:return None
 if ok.get('clickable')!='true' or ok.get('enabled')!='true':return None
 values=list(map(int,re.findall(r'\d+',ok.get('bounds',''))))
 if len(values)!=4 or values[2]-values[0]<32 or values[3]-values[1]<32:return None
 return {'coordinate':[(values[0]+values[2])//2,(values[1]+values[3])//2],
  'button_bounds':values,'warning':body,'native_members':sorted(libraries),
  'action':'ANDROID_INFORMATIONAL_OK_ONLY; NO_DONT_SHOW_AGAIN_OR_COMPAT_SETTING_CHANGE'}

def acknowledge_known_notice_after_launch(launch_text,out,native_paths=None):
 """Observe one successful Cobra launch; acknowledge only its known OS notice.

 Each caller owns a distinct successful am-start boundary. No persistent warning
 suppression or compatibility setting is changed. Normal app-state/action guards
 remain the responsibility of the caller after this finite OS-only observation.
 """
 assert 'Error' not in launch_text and 'Status: ok' in launch_text,'Successful Cobra launch required before OS notice observation'
 assert (PACKAGE+'/.InfinityLiveActivity' in launch_text or PACKAGE+'/'+PACKAGE+'.InfinityLiveActivity' in launch_text),'Expected Cobra Activity launch required'
 out=Path(out);out.mkdir(parents=True,exist_ok=False)
 report={'scope':'ONE_SUCCESSFUL_COBRA_LAUNCH_OS_NOTICE_ONLY','action':'NO_ACKNOWLEDGEMENT',
         'shutdown':'NOT_RUN','compatibility_settings':'UNCHANGED'}
 def observe(name):
  adb('shell','uiautomator','dump','/sdcard/cobra-launch-notice-qa.xml')
  raw=adb('shell','cat','/sdcard/cobra-launch-notice-qa.xml')
  (out/(name+'.xml')).write_text(raw)
  return ET.fromstring(raw)
 def android_dialog(tree):
  return any(n.get('package')=='android' and n.get('resource-id') in
   ('android:id/alertTitle','android:id/message','android:id/button1','android:id/button2') for n in tree.iter('node'))
 try:
  tree=observe('observed')
  notice=compatibility_notice_ok(tree,set(native_paths or ()))
  if notice is None:
   assert not android_dialog(tree),'Unrecognized Android dialog refused after Cobra launch'
   report['status']='NO_KNOWN_NOTICE_OBSERVED'
   return report
  # Keep the full warning and screenshot before touching anything. Refresh its
  # exact identity and bounds after screenshot I/O, then press only that OK.
  capture=subprocess.run(['adb','exec-out','screencap','-p'],capture_output=True,timeout=15)
  assert capture.returncode==0 and capture.stdout.startswith(b'\x89PNG\r\n\x1a\n'),'Compatibility notice PNG required before acknowledgement'
  (out/'observed.png').write_bytes(capture.stdout)
  fresh=compatibility_notice_ok(observe('fresh-before-OK'),set(native_paths or ()))
  assert fresh is not None and fresh==notice,'Compatibility notice changed before acknowledgement; no press injected'
  report['notice']=fresh
  adb('shell','input','tap',*[str(v) for v in fresh['coordinate']])
  report['action']='ONE_ANDROID_INFORMATIONAL_OK_ONLY'
  after=observe('after-OK')
  assert not android_dialog(after),'Repeated or unrecognized Android dialog refused after one OK'
  report['status']='KNOWN_NOTICE_ACKNOWLEDGED_ONCE'
  return report
 except Exception as exc:
  report['status']='FAILED_OS_NOTICE_OBSERVATION';report['error']=str(exc)
  raise
 finally:
  (out/'OUTCOME.json').write_text(json.dumps(report,indent=2)+'\n')

def probe(apk,out,expected):
 out.mkdir(parents=True);report={'runtime':'DISPOSABLE_ANDROID17_API37_X86_64_EMULATOR','physical_Fold':'NOT_RUN','shutdown':'NOT_RUN','Infinity':'NOT_LAUNCHED'}
 try:
  assert hashlib.file_digest(apk.open('rb'),'sha256').hexdigest()==expected
  serial=adb('get-serialno').strip();sdk=adb('shell','getprop','ro.build.version.sdk').strip();qemu=adb('shell','getprop','ro.kernel.qemu').strip()
  assert serial.startswith('emulator-') and sdk=='37' and qemu=='1','Fresh API37 emulator required'
  assert not adb('shell','pm','path',PACKAGE,check=False).strip(),'Existing application refused; never clear or replace data'
  report.update(serial=serial,sdk=sdk,abis=adb('shell','getprop','ro.product.cpu.abilist').strip(),page_size=adb('shell','getconf','PAGE_SIZE').strip(),apk_sha256=expected)
  install_started=time.monotonic()
  # Large-file QA I/O is separate from the unchanged short ADB/UI limits.
  # At measured18MB/s, transfer alone needs43s. Budget conservative10MiB/s
  # plus45s PackageManager/verification headroom, capped at120s.
  apk_io_timeout=min(120,max(30,math.ceil(apk.stat().st_size/(10*1024*1024))+45))
  report['APK_IO_timeout_seconds']=apk_io_timeout
  report['short_ADB_timeout_seconds']=30
  try:
   (out/'install.txt').write_text(adb('install','--no-incremental','-r',str(apk),timeout=apk_io_timeout))
   report['install_client']='COMPLETED'
  except subprocess.TimeoutExpired as exc:
   # PackageInstaller may finish while the streamed-install client still waits.
   # Never retry an uncertain install or increase the generic ADB deadline.
   def decoded(value):return value.decode(errors='replace') if isinstance(value,bytes) else value or ''
   report['install_client']='TIMEOUT_%d_SECONDS; EXACT_INSTALLED_BYTES_REQUIRED'%apk_io_timeout
   (out/'install-client-timeout.json').write_text(json.dumps({'command':'adb install --no-incremental -r',
     'timeout_seconds':exc.timeout,'stdout':decoded(exc.stdout),'stderr':decoded(exc.stderr)},indent=2)+'\n')
  report['install_confirmation']=confirm_installed_apk(expected,apk_io_timeout)
  report['install_seconds_including_confirmation']=round(time.monotonic()-install_started,3)
  start=time.monotonic();result=adb('shell','am','start','-W','-n',PACKAGE+'/.InfinityLiveActivity');(out/'launch.txt').write_text(result)
  assert 'Error' not in result,result
  assert 'Status: ok' in result and (PACKAGE+'/.InfinityLiveActivity' in result or PACKAGE+'/'+PACKAGE+'.InfinityLiveActivity' in result),'Expected Cobra Activity launch required'
  with zipfile.ZipFile(apk) as source:native_paths={n for n in source.namelist() if n.startswith('lib/arm64-v8a/') and n.endswith('.so')}
  for i in range(30):
   adb('shell','uiautomator','dump','/sdcard/cobra-qa-ui.xml',check=False)
   raw=adb('shell','cat','/sdcard/cobra-qa-ui.xml',check=False)
   (out/'last-ui.xml').write_text(raw)
   try:tree=ET.fromstring(raw)
   except ET.ParseError:time.sleep(.5);continue
   notice=compatibility_notice_ok(tree,native_paths)
   if notice is not None:
    assert 'Android_compatibility_notice' not in report,'Repeated compatibility notice refused'
    (out/'android-compatibility-notice.xml').write_text(raw)
    capture=subprocess.run(['adb','exec-out','screencap','-p'],capture_output=True,timeout=15)
    assert capture.returncode==0 and capture.stdout,'Compatibility notice capture required before acknowledgement'
    (out/'android-compatibility-notice.png').write_bytes(capture.stdout)
    report['Android_compatibility_notice']=notice
    adb('shell','input','tap',*[str(v) for v in notice['coordinate']])
    continue
   labels=[n.get('text','') or n.get('content-desc','') for n in tree.iter('node')]
   own=any(n.get('package')==PACKAGE for n in tree.iter('node'))
   if own and any(re.search(r'Channels|Guide|Add source|Add Source|Live TV|M3U|Sources',s) for s in labels):
    report.update(status='COBRA_FIRST_SCREEN_OBSERVED',first_screen_seconds=round(time.monotonic()-start,3),labels=labels)
    break
   if time.monotonic()-start>45:break
  else:pass
  assert report.get('status')=='COBRA_FIRST_SCREEN_OBSERVED','Cobra feature screen not observed; see last UI and logcat'
 finally:
  (out/'logcat.txt').write_text(adb('logcat','-d','-v','threadtime',check=False))
  (out/'activity.txt').write_text(adb('shell','dumpsys','activity','activities',check=False))
  (out/'meminfo.txt').write_text(adb('shell','dumpsys','meminfo',PACKAGE,check=False))
  p=subprocess.run(['adb','exec-out','screencap','-p'],capture_output=True,timeout=15);(out/'screen.png').write_bytes(p.stdout)
  report.setdefault('status','BLOCKED_BEFORE_FEATURE_OBSERVATION');(out/'OUTCOME.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--apk',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--expected',required=True);probe(**vars(p.parse_args()))
