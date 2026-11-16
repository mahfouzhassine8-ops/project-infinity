"""One actual application lock journey. No shutdown, reset, provider or owner data access."""
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,time,urllib.request,xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('existing_feature_transport',ROOT/'repairs/save-later-multiimage-20261023/android_feature_device.py')
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
PACKAGE='com.projectinfinity.kodi';HOME='/sdcard/Android/data/'+PACKAGE+'/files/.kodi'
QA='script.infinity.lockapplicationqa';QAROOT=HOME+'/userdata/addon_data/'+QA

def main():
 work=ROOT/'lock-app-work';out=work/'evidence';apk=work/'INTERNAL-LOCK-QA-NOT-FOR-OWNER.apk'
 report={'status':'RUNNING_SELECTED_LOCK_APPLICATION_CASE','shutdown':'NOT_SELECTED','physical_Fold':'NOT_RUN','owner_installer':False,'cases':[]}
 def save():(out/'APPLICATION.json').write_text(json.dumps(report,indent=2)+'\n')
 def stamp():return {'UTC':datetime.now(timezone.utc).isoformat(),'monotonic':time.monotonic(),'engine_pid':pid}
 def passed(name,**data):report['cases'].append({'case':name,'pass':True,**stamp(),**data});save()
 def record(name,value):report.setdefault('observations',[]).append({'event':name,'value':value,**stamp()});save()
 def redact(raw):
  raw=re.sub(r'https?://[^\s\"\'<>]+','<URL_REDACTED>',raw)
  raw=re.sub(r'(?i)((?:authorization|cookie|password|access_token|refresh_token|api_key)[\"\']?\s*[:=]\s*)[^\r\n]+',r'\1<REDACTED>',raw)
  return raw
 shell=transport.shell;adb=transport.adb;rpc=transport.rpc;pid=None;sequence=0
 def until(fn,label,seconds=30):
  deadline=time.monotonic()+seconds;last=None
  while time.monotonic()<deadline:
   try:
    value=fn()
    if value:return value
   except (OSError,ValueError,RuntimeError) as error:last=type(error).__name__+': '+str(error)
   time.sleep(.2)
  raise RuntimeError('Timed out '+label+'; '+str(last))
 def alive():assert shell('pidof',PACKAGE+':kodi',check=False).strip()==str(pid),'ENGINE_DIED_OR_RESTARTED'
 def nodes(label):
  shell('uiautomator','dump','/sdcard/Download/infinity502-lock-ui.xml')
  raw=shell('cat','/sdcard/Download/infinity502-lock-ui.xml');(out/(label+'.xml')).write_text(raw);return ET.fromstring(raw)
 def bounds(node):
  match=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''));assert match
  return tuple(map(int,match.groups()))
 def observer(action,**arguments):
  nonlocal sequence
  alive();sequence+=1
  assert not {'pid','sequence','action'}.intersection(arguments)
  if action in ('watched_select','watched_button'):
   record('watched_input_dispatch',{'sequence':sequence,'action':action,
          **{k:arguments[k] for k in ('window','dialog','control','label','input') if k in arguments}})
  path=work/'request.json';path.write_text(json.dumps({'pid':pid,'sequence':sequence,'action':action,**arguments}));adb('push',path,QAROOT+'/request.json')
  def read():
   value=transport.read_json(QAROOT+'/reply.json')
   return value if value.get('pid')==pid and value.get('sequence')==sequence else None
  reply=until(read,'exact observer reply '+action,15);assert reply['pass'],reply
  alive();return reply['result']
 def lock_node(label):
  found=[n for n in nodes(label).iter('node') if n.get('content-desc','')=='Video locked. Hold the top-left lock continuously for two seconds to unlock.']
  assert len(found)<=1,'AMBIGUOUS_LOCK_WINDOW';return found[0] if found else None
 def unlocked(label):return lock_node(label) is None
 try:
  assert shell('getprop','ro.kernel.qemu').strip()=='1','DISPOSABLE_EMULATOR_ONLY'
  assert not shell('pm','list','packages',PACKAGE).strip(),'FRESH_INSTALL_ONLY'
  environment={n:shell('getprop',n).strip() for n in ('ro.build.version.sdk','ro.product.cpu.abilist','ro.dalvik.vm.native.bridge','ro.build.fingerprint')}
  assert environment['ro.build.version.sdk']=='36' and 'arm64-v8a' in environment['ro.product.cpu.abilist'] and environment['ro.dalvik.vm.native.bridge']=='libndk_translation.so'
  assert shell('getconf','PAGESIZE').strip()=='4096'
  report['environment']=environment;save()
  install_args=['adb','install','--no-streaming',str(apk)];transport.guard(install_args)
  installed=subprocess.run(install_args,capture_output=True,text=True,timeout=300)
  install=installed.stdout+installed.stderr;(out/'INSTALL.txt').write_text(install);assert installed.returncode==0 and 'Success' in install
  for args in [('appops','set',PACKAGE,'MANAGE_EXTERNAL_STORAGE','allow'),('pm','grant',PACKAGE,'android.permission.RECORD_AUDIO'),('pm','grant',PACKAGE,'android.permission.POST_NOTIFICATIONS')]:shell(*args)
  fixture=work/'fixture';addon=fixture/'addons'/QA;addon.mkdir(parents=True);profile=fixture/'userdata';profile.mkdir()
  (addon/'addon.xml').write_text('<addon id="'+QA+'" name="Disposable Lock Application QA" version="1.0.0" provider-name="Infinity engineering"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="qa.py"><provides>executable</provides></extension><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable selected lock check</summary><platform>all</platform></extension></addon>')
  (addon/'qa.py').write_bytes((HERE/'qa.py').read_bytes())
  crashes=HERE.parent.parent/'crashes'
  (addon/'watched_probe.py').write_bytes((crashes/'watched_probe.py').read_bytes())
  # New disposable profile only. No existing records, provider data or user settings.
  (profile/'guisettings.xml').write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">false</setting></settings>')
  clip=profile/'infinity502-lock-fixture.mp4'
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','testsrc2=size=640x360:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','180','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(clip)],check=True,timeout=120)
  public=json.loads((crashes/'WATCHED-PUBLIC-FIXTURE.json').read_bytes());archive=work/'public-film.zip'
  with urllib.request.urlopen(public['original_media'],timeout=90) as source,archive.open('wb') as dest:shutil.copyfileobj(source,dest,1024*1024)
  assert archive.stat().st_size==public['archive_size']
  with archive.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==public['archive_sha256']
  film_dir=profile/'infinity502-watched-fixture';film_dir.mkdir();film=film_dir/public['movie_member']
  with ZipFile(archive) as source:
   assert source.namelist()==[public['movie_member']] and source.getinfo(public['movie_member']).file_size==public['movie_size']
   with source.open(public['movie_member']) as inp,film.open('wb') as dest:shutil.copyfileobj(inp,dest,1024*1024)
  with film.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==public['movie_sha256']
  film.with_suffix('.nfo').write_text('<movie><title>Big Buck Bunny</title><year>2008</year><uniqueid type="imdb" default="true">tt1254207</uniqueid></movie>')
  film_directory=HOME+'/userdata/infinity502-watched-fixture/'
  (profile/'sources.xml').write_text('<sources><video><source><name>Infinity502 engineering movie</name><path pathversion="1">'+film_directory+'</path><allowsharing>false</allowsharing></source></video></sources>')
  adb('root');adb('wait-for-device');shell('mkdir','-p',HOME);adb('push',str(fixture)+'/.',HOME)
  uid=shell('stat','-c','%u','/data/user/0/'+PACKAGE).strip();assert uid.isdigit() and int(uid)>=10000
  backing='/data/media/0/Android/data/'+PACKAGE;shell('chown','-R',uid+':'+uid,backing);shell('restorecon','-RF',backing)
  report['fixture']={'fresh_profile_only':True,'clip_sha256':hashlib.sha256(clip.read_bytes()).hexdigest(),'owner_data':'NOT_ACCESSED','application_UID':int(uid)};save()
  # Acknowledge only the stock emulator's first-use fullscreen tutorial, not app dialogs.
  original_education=shell('settings','get','secure','immersive_mode_confirmations').strip()
  shell('settings','put','secure','immersive_mode_confirmations','confirmed')
  report['education_before']=original_education
  shell('am','start','-W','-n',PACKAGE+'/.Splash')
  deadline=time.monotonic()+120;tapped=False
  while time.monotonic()<deadline:
   current=shell('pidof',PACKAGE+':kodi',check=False).strip()
   if current.isdigit():pid=int(current);break
   tree=nodes('chooser');parents={c:p for p in tree.iter() for c in p}
   choices=[]
   for n in tree.iter('node'):
    if n.get('text','').strip().lower()!='infinity':continue
    while n is not None and n.get('clickable')!='true':n=parents.get(n)
    if n is not None:choices.append(bounds(n))
   if choices and not tapped:
    assert len(set(choices))==1;a,b,c,d=choices[0];shell('input','tap',(a+c)//2,(b+d)//2);tapped=True
   time.sleep(.5)
  assert pid is not None,'NORMAL_CHOOSER_DID_NOT_START_KODI'
  adb('forward','tcp:19090','tcp:9090')
  until(lambda:rpc('JSONRPC.Ping')=='pong','actual Kodi RPC',240);alive()
  details=rpc('Addons.GetAddonDetails',{'addonid':QA,'properties':['enabled']})['addon']
  if not details['enabled']:assert rpc('Addons.SetAddonEnabled',{'addonid':QA,'enabled':True})=='OK'
  assert rpc('Addons.ExecuteAddon',{'addonid':QA})=='OK'
  until(lambda:transport.read_json(QAROOT+'/ready.json').get('pid')==pid,'actual embedded Python observer',60)
  first=observer('snapshot');assert first['skin']=='skin.infinity.diggz'
  with ZipFile(apk) as z:
   for aid in ('script.infinity.commandcenter','skin.infinity.diggz'):
    for name,sha in first[aid]['files'].items():assert hashlib.sha256(z.read('assets/addons/'+aid+'/'+name)).hexdigest()==sha,(aid,name)
  passed('normal_entry_native_and_Python_ready',pid=pid,snapshot=first)
  identity=observer('native_identity')
  assembly=json.loads((out/'ASSEMBLY.json').read_bytes())
  assert identity['engine_sha256']==assembly['native']['member_sha256'],'ACTUAL_MAPPED_ENGINE_DIFFERS'
  assert identity['build_id']==assembly['native']['build_id'] and identity['build_id_status']==assembly['native']['build_id_status'],'ACTUAL_ELF_NOTE_DIFFERS'
  report['native_identity']=identity;save()
  assert rpc('Player.Open',{'item':{'file':'special://profile/infinity502-lock-fixture.mp4'}})=='OK'
  first=until(lambda:(lambda s:s if s.get('playing') and s.get('time',0)>1 else None)(observer('snapshot')),'actual local playback',45)
  if not observer('snapshot')['osd']:assert rpc('Input.ExecuteAction',{'action':'showosd'})=='OK'
  until(lambda:observer('snapshot')['osd'],'original video OSD',15)
  observer('focus_lock');until(lambda:observer('snapshot').get('focused_control')==262,'original control262 focus',10)
  assert rpc('Input.Select')=='OK'
  node=until(lambda:(lambda n:(n,) if n is not None else None)(lock_node('lock-entry')),'actual native-to-Java lock window',15)[0];alive()
  before_clock=time.monotonic();before=observer('snapshot');assert before['playing'] and not before['lock_entry'],'1199 must close after actual READY'
  a,b,c,d=bounds(node);assert c>a and d>b
  # Component geometry was separately verified; here use the focused fullscreen
  # input window bounds, retaining the real native/Java path and injected touch.
  x=round(a+(c-a)*(.037037+.0851851/2));y=round(b+(d-b)*(.0225+(92/2400)/2))
  shell('input','swipe',x,y,x,y,250);shell('input','keyevent','KEYCODE_BACK')
  assert lock_node('after-short-hold-and-back') is not None
  assert rpc('Input.ExecuteAction',{'action':'stepforward'})=='OK'
  shell('input','tap',(a+c)//2,(b+d)//2);time.sleep(1)
  after=observer('snapshot');elapsed=time.monotonic()-before_clock
  assert after['playing'] and after['source_sha256']==before['source_sha256']
  assert 0<after['time']-before['time']<elapsed+3,'PLAYBACK_PAUSED_OR_UNEXPECTED_SEEK'
  assert lock_node('locked-native-input-barrier') is not None
  passed('actual_lock_entry_and_input_barrier',before=before,after=after,window_bounds=[a,b,c,d],short_hold_ms=250)
  observer('arm_restore')
  shell('input','swipe',x,y,x,y,2300)
  until(lambda:unlocked('after-intentional-hold'),'actual native ACK and window dismissal',15)
  after_unlock=observer('snapshot');assert after_unlock['playing'] and after_unlock['source_sha256']==before['source_sha256'] and after_unlock['time']>after['time']
  restored=transport.read_json(QAROOT+'/restored-osd.json')
  assert restored.get('pid')==pid and restored.get('status')=='OBSERVED','ORIGINAL_OSD_NOT_OBSERVED'
  assert restored['snapshot']['osd'] and restored['snapshot']['playing'] and restored['snapshot']['source_sha256']==before['source_sha256']
  alive();passed('native_restoration_and_continuous_playback',snapshot=after_unlock,first_restored_osd=restored,hold_ms=2300)
  # Positive control uses the same action as the locked negative check.
  seek_clock=time.monotonic();seek_before=observer('snapshot')
  assert rpc('Input.ExecuteAction',{'action':'stepforward'})=='OK'
  def seek_completed():
   state=observer('snapshot')
   assert state['playing'] and state['source_sha256']==before['source_sha256']
   return state if state['time']-seek_before['time']>time.monotonic()-seek_clock+3 else None
  seek_after=until(seek_completed,'unlocked positive seek control',10)
  passed('actual_input_barrier_released',before=seek_before,after=seek_after)
  if not observer('snapshot')['osd']:assert rpc('Input.ExecuteAction',{'action':'showosd'})=='OK'
  until(lambda:observer('snapshot')['osd'],'original OSD for Stop',10)
  observer('focus_stop');until(lambda:observer('snapshot').get('focused_control')==253,'original Stop control253',10)
  record('original_Stop_dispatch',{'control':253})
  assert rpc('Input.Select')=='OK'
  until(lambda:not observer('snapshot')['playing'],'actual original OSD media Stop',10)
  alive();passed('original_OSD_Stop_same_engine_alive',pid=pid,control=253)
  watched_spec=importlib.util.spec_from_file_location('selected_watched_case',crashes/'watched_case.py')
  watched=importlib.util.module_from_spec(watched_spec);watched_spec.loader.exec_module(watched)
  report['watched_case']=watched.run(rpc,observer,until,passed,record,alive,film_directory,film_directory+public['movie_member'])
  identity_after=observer('native_identity');assert identity_after==identity,'MAPPED_ENGINE_OR_PROCESS_CHANGED'
  observer('finish');until(lambda:transport.read_json(QAROOT+'/retired.json').get('normal_completion') is True,'observer retirement',10);alive()
  passed('normal_media_stop_and_observer_retirement',same_pid=pid)
  report['status']='PASS_SELECTED_ACTUAL_APPLICATION_LOCK_STOP_WATCHED_CASES'
 except Exception as error:
  report['status']='FAIL_SELECTED_ACTUAL_APPLICATION_LOCK_STOP_WATCHED_CASES';report['error']=type(error).__name__+': '+str(error);report['failure_time']=stamp();raise
 finally:
  if 'original_education' in locals():
   try:
    shell('settings','delete','secure','immersive_mode_confirmations') if original_education=='null' else shell('settings','put','secure','immersive_mode_confirmations',original_education)
    report['education_restored']=shell('settings','get','secure','immersive_mode_confirmations').strip()
    assert report['education_restored']==original_education
   except Exception as error:report['fixture_restore_error']=str(error);report['status']='FAIL_SELECTED_ACTUAL_APPLICATION_LOCK_STOP_WATCHED_CASES'
  for name,command in [('logcat.txt',('logcat','-d','-v','threadtime')),('crash-buffer.txt',('logcat','-d','-b','crash','-v','threadtime')),
                       ('exit-info.txt',('shell','dumpsys','activity','exit-info',PACKAGE)),('windows.txt',('shell','dumpsys','window','windows'))]:
   try:
    (out/name).write_text(redact(adb(*command)))
   except Exception as error:report.setdefault('capture_errors',[]).append(name+': '+str(error))
  # Never upload raw tombstones or memory dumps. Preserve only matching-PID
  # signal/ABI/timestamp/stack frames and a digest of the actual captured file.
  if pid is not None and report['status'].startswith('FAIL'):
   try:
    names=[n for n in shell('ls','-t','/data/tombstones',check=False).splitlines() if re.fullmatch(r'tombstone_[0-9]+',n)][:8]
    matching=[]
    for name in names:
     raw=shell('cat','/data/tombstones/'+name,check=False)
     if not re.search(r'pid:\s*'+str(pid)+r'\b',raw) or PACKAGE+':kodi' not in raw:continue
     lines=[line for line in raw.splitlines() if re.match(r"\s*(?:pid:|signal [0-9]|Abort message:|#[0-9]+ pc |Cmdline:|Build fingerprint:|Timestamp:|ABI:|Revision:)",line)]
     matching.append({'source_file':name,'source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'pid':pid,'frames':redact('\n'.join(lines))})
    (out/'MATCHING-CRASH-FRAMES.json').write_text(json.dumps({'selected_pid':pid,'matches':matching,'raw_tombstones_uploaded':False},indent=2)+'\n')
   except Exception as error:report.setdefault('capture_errors',[]).append('matching tombstone: '+str(error))
  save()
 if report['status']!='PASS_SELECTED_ACTUAL_APPLICATION_LOCK_STOP_WATCHED_CASES':raise RuntimeError(report['status'])

if __name__=='__main__':main()
