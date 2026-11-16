"""Disposable fresh-profile observer. Not part of the candidate APK or owner profile."""
from pathlib import Path
import hashlib,json,os,struct,time
import xbmc,xbmcaddon,xbmcgui,xbmcvfs

ROOT=Path(xbmcvfs.translatePath('special://profile/addon_data/script.infinity.lockapplicationqa/'))
ROOT.mkdir(parents=True,exist_ok=True)

def write(name,value):
 temporary=ROOT/(name+'.tmp');temporary.write_text(json.dumps(value));os.replace(temporary,ROOT/name)

def native_identity():
 started=time.monotonic()
 def progress(stage,**details):
  write('native-identity-progress.json',{'pid':os.getpid(),'sequence':last,'stage':stage,
        'elapsed_seconds':time.monotonic()-started,**details})
 progress('locating_mapped_engine')
 root=Path(os.environ['KODI_ANDROID_LIBS']);assert root.is_absolute()
 target=(root/'libkodi.so').resolve();assert target.is_file()
 rows=[line.split(None,5) for line in Path('/proc/self/maps').read_text().splitlines() if 'libkodi.so' in line]
 assert rows and all(len(row)==6 and row[5]==str(target) for row in rows),'UNIQUE_ACTUAL_MAPPED_ENGINE_REQUIRED'
 build_id=None
 with target.open('rb') as stream:
  opened=os.fstat(stream.fileno())
  assert all(int(row[4])==opened.st_ino and tuple(int(n,16) for n in row[3].split(':'))==
             (os.major(opened.st_dev),os.minor(opened.st_dev)) for row in rows),'MAPPED_FILE_IDENTITY_DIFFERS'
  progress('mapped_file_identity_verified',bytes_total=opened.st_size)
  header=stream.read(64);assert header[:6]==b'\x7fELF\x02\x01'
  phoff=struct.unpack_from('<Q',header,32)[0];phsize,phcount=struct.unpack_from('<HH',header,54)
  assert phsize==56 and 0<phcount<256
  for index in range(phcount):
   stream.seek(phoff+index*phsize);ph=stream.read(phsize)
   if struct.unpack_from('<I',ph)[0]!=4:continue
   offset,size=struct.unpack_from('<Q',ph,8)[0],struct.unpack_from('<Q',ph,32)[0];assert size<1024*1024
   stream.seek(offset);notes=stream.read(size);position=0
   while position+12<=len(notes):
    n,d,t=struct.unpack_from('<III',notes,position);position+=12
    assert position+((n+3)&~3)+((d+3)&~3)<=len(notes)
    name=notes[position:position+n];position+=(n+3)&~3;desc=notes[position:position+d];position+=(d+3)&~3
    if name.rstrip(b'\0')==b'GNU' and t==3:build_id=desc.hex()
  progress('ELF_notes_verified',bytes_total=opened.st_size)
  progress('hashing_verified_mapped_file',bytes_total=opened.st_size,bytes_hashed=0)
  stream.seek(0);hasher=hashlib.sha256();hashed=0
  while chunk:=stream.read(4*1024*1024):
   hasher.update(chunk);hashed+=len(chunk)
   if hashed%(64*1024*1024)==0:
    progress('hashing_verified_mapped_file',bytes_total=opened.st_size,bytes_hashed=hashed)
  assert hashed==opened.st_size,'MAPPED_FILE_SIZE_CHANGED_DURING_HASH'
  digest=hasher.hexdigest()
  progress('complete',bytes_total=opened.st_size,bytes_hashed=hashed)
 return {'pid':os.getpid(),'engine_sha256':digest,'build_id':build_id,
         'build_id_status':'PRESENT_IN_VERIFIED_ELF' if build_id else 'ABSENT_IN_VERIFIED_ELF',
         'mapped_segments':len(rows),'inode':opened.st_ino,
         'process_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}

def snapshot():
 player=xbmc.Player();playing=player.isPlayingVideo()
 value={'pid':os.getpid(),'skin':xbmc.getSkinDir(),'window':xbmcgui.getCurrentWindowId(),
        'dialog':xbmcgui.getCurrentWindowDialogId(),'playing':playing,
        'osd':bool(xbmc.getCondVisibility('Window.IsVisible(videoosd)')),
        'lock_entry':bool(xbmc.getCondVisibility('Window.IsVisible(1199)'))}
 if playing:
  value.update(time=player.getTime(),duration=player.getTotalTime(),source_sha256=hashlib.sha256(player.getPlayingFile().encode()).hexdigest())
 if value['osd']:
  try:value['focused_control']=xbmcgui.Window(12901).getFocusId()
  except RuntimeError as error:value.update(focused_control=None,focus_observation_error=str(error))
 for aid in ('script.infinity.commandcenter','skin.infinity.diggz'):
  addon=xbmcaddon.Addon(aid);base=Path(xbmcvfs.translatePath(addon.getAddonInfo('path')))
  names=('addon.xml','INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig') if aid.endswith('commandcenter') else ('addon.xml','unified/VideoOSD.xml','unified/custom_1199_InfinityVideoLock.xml')
  value[aid]={'version':addon.getAddonInfo('version'),'files':{n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names}}
 return value

write('ready.json',{'pid':os.getpid(),'kind':'disposable_lock_observer'})
last=0;deadline=time.monotonic()+600;monitor=xbmc.Monitor();restore_probe=None
while time.monotonic()<deadline and not monitor.abortRequested():
 if restore_probe is not None:
  if xbmc.getCondVisibility('Window.IsVisible(videoosd)'):
   try:
    observed=snapshot()
    if observed['osd'] and observed['playing']:
     write('restored-osd.json',{'pid':os.getpid(),'status':'OBSERVED','snapshot':observed});restore_probe=None
   except RuntimeError as error:
    write('restored-osd.json',{'pid':os.getpid(),'status':'TRANSIENT_OBSERVATION_ERROR','error':str(error)})
   if restore_probe is not None and time.monotonic()>restore_probe:
    write('restored-osd.json',{'pid':os.getpid(),'status':'NOT_OBSERVED_BEFORE_DEADLINE'});restore_probe=None
  elif time.monotonic()>restore_probe:
   write('restored-osd.json',{'pid':os.getpid(),'status':'NOT_OBSERVED_BEFORE_DEADLINE'});restore_probe=None
 try:request=json.loads((ROOT/'request.json').read_text())
 except (OSError,ValueError):monitor.waitForAbort(.02 if restore_probe else .1);continue
 if request.get('pid')!=os.getpid() or request.get('sequence',0)<=last:monitor.waitForAbort(.02 if restore_probe else .1);continue
 last=request['sequence'];kind=request.get('action');stop=False
 try:
  assert kind in ('snapshot','native_identity','focus_lock','focus_stop','arm_restore','finish',
                  'watched_ui','watched_select','watched_button','watched_state'),'UNSELECTED_OBSERVER_ACTION'
  if kind in ('focus_lock','focus_stop'):
   assert xbmc.getSkinDir()=='skin.infinity.diggz' and xbmc.getCondVisibility('Window.IsVisible(videoosd)')
   xbmcgui.Window(12901).setFocusId(262 if kind=='focus_lock' else 253)
  if kind=='arm_restore':
   assert not xbmc.getCondVisibility('Window.IsVisible(videoosd)'),'OSD_ALREADY_VISIBLE_BEFORE_HOLD'
   restore_probe=time.monotonic()+20
   write('restored-osd.json',{'pid':os.getpid(),'status':'ARMED'})
  stop=kind=='finish'
  if kind.startswith('watched_'):
   import watched_probe
   result=watched_probe.action(request)
  else:result=native_identity() if kind=='native_identity' else snapshot()
  write('reply.json',{'pid':os.getpid(),'sequence':last,'pass':True,'result':result})
 except Exception as error:write('reply.json',{'pid':os.getpid(),'sequence':last,'pass':False,'error':type(error).__name__+': '+str(error)})
 if stop:break
 monitor.waitForAbort(.05)
write('retired.json',{'pid':os.getpid(),'last_sequence':last,'normal_completion':stop if 'stop' in globals() else False})
