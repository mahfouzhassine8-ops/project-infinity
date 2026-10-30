"""One finite exact-APK Cobra launch on a fresh disposable API37 emulator.
No Infinity launch, root/data injection, restart, clear, teardown or shutdown.
"""
import argparse,hashlib,json,math,re,subprocess,time,xml.etree.ElementTree as ET
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
  for i in range(30):
   adb('shell','uiautomator','dump','/sdcard/cobra-qa-ui.xml',check=False)
   raw=adb('shell','cat','/sdcard/cobra-qa-ui.xml',check=False)
   (out/'last-ui.xml').write_text(raw)
   try:tree=ET.fromstring(raw)
   except ET.ParseError:time.sleep(.5);continue
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
