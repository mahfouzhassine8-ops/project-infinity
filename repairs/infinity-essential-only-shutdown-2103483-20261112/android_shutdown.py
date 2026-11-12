#!/usr/bin/env python3
"""Independent selected normal Close on a disposable VM; never a signing prerequisite.

Exact83 installed unchanged; actual compiled ARM64 engine injected before first
launch. This verifies native behavior, not signed successor installation/Fold.
"""
import argparse,ast,hashlib,importlib.util,json,os,re,shutil,sqlite3,subprocess,sys,time,traceback,uuid
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BRANCH='work/infinity-essential-only-shutdown-2103483-20261112'
SELECTION=HERE/'ANDROID-SELECTION.json'
sys.path.insert(0,str(ROOT/'repairs/infinity-core-outcomes-qa-2103483-20261112'))
import android_probe as prior
base=prior.base;gui=prior.gui;require=prior.require;sha=prior.sha
FAVOURITE='Essential-only repair retained test favourite'
ESSENTIAL={'native_admission','background_jobs','playback','command_center','compat','kodi_settings','profiles','skin_settings','addon_settings','favourites','peripherals','audio_policy','deferred_dialog_state','xml_files','native_databases','pvr'}
def selected():
 row=base.load(SELECTION)
 require(row['enabled'] is True and row['shutdown_tests'] is True and row['owner_device'] is False and row['Core_path_correction'] is False,'EXPLICIT_INDEPENDENT_CLOSE_SELECTION')
 require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and os.environ.get('AUTHORIZED_SCOPE')=='Essential-only Core shutdown, process death and same-profile relaunch with retained data','EXACT_CI_AUTHORIZATION')
 require(os.environ.get('SELECTED_CASE')=='essential-only-core-outcomes','ONLY_SELECTED_SHUTDOWN')
 require(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==os.environ['SELECTED_SOURCE'],'EXACT_TEST_SOURCE')
 require(row['baseline']==base.load(prior.HERE/'ANDROID-SELECTION.json')['baseline'],'UNCHANGED_AUTHENTICATED83')
 for n in ('native/overlay','BASE83-NATIVE-SOURCE-MAP.json'):
  require(not subprocess.check_output(['git','diff','--name-only',row['native']['source'],'HEAD','--',str(HERE.relative_to(ROOT)/n)],text=True).strip(),'NATIVE_SOURCE_CHANGED_SINCE_BUILD')
 return row
prior.selected=selected;prior.SELECTION=SELECTION
class Device(prior.Device):
 METHODS=prior.Device.METHODS|{'Favourites.AddFavourite','Favourites.GetFavourites'}
 def rpc(self,method,params=None,timeout=5):
  if method=='Addons.SetAddonEnabled' and params in [dict(addonid=n,enabled=True) for n in ('script.infinity.commandcenter','service.infinity.compat')]:
   # The retained generic shutdown fixture normally enables these required
   # bundled services through this same supported Kodi API on a fresh VM.
   return prior.RetainedDevice.rpc(self,method,params,timeout)
  if method=='Favourites.AddFavourite':require(params==dict(title=FAVOURITE,type='window',window='home'),'ONLY_SYNTHETIC_NATIVE_FAVOURITE')
  if method=='Favourites.GetFavourites':require(params==dict(properties=['window','windowparameter']),'READ_ONLY_FAVOURITES')
  return super().rpc(method,params,timeout)
def fetch(out):
 row=selected();require(not out.exists(),'FRESH_INPUTS')
 baseline=prior.artifact(row['baseline'],out/'baseline');native=prior.artifact(row['native'],out/'native')
 apk=prior.one(baseline,'Infinity-2103483-Combined-Original-Signer.apk');library=prior.one(native,'libkodi.so');proof=base.load(prior.one(native,'ESSENTIAL-ONLY-ARM64.json'))
 require(sha(apk)==prior.APK_SHA and sha(library)==row['native']['native_sha256'],'EXACT_INPUT_BYTES')
 require(proof['status']=='PASS_FULL_ARM64_ESSENTIAL_ONLY_LINK_AND_BASELINE_ABI' and proof['source_commit']==row['native']['source'] and proof['native_sha256']==sha(library) and proof['Core_path_correction_activated'] is False and proof['signed'] is False,'ACTUAL_ARM64_SOURCE_AND_ABI')
 fixture=out/'publisher';fixture.mkdir()
 require(row['publisher']==base.load(prior.HERE/'ANDROID-SELECTION.json')['publisher'],'UNCHANGED_REVIEWED_INSTALLED_CORE')
 import urllib.request
 for item in row['publisher']['files']:
  target=fixture/item['name'];require(target.parent==fixture,'FLAT_PUBLISHER_NAME')
  with urllib.request.urlopen(item['url'],timeout=45) as response:data=response.read(item['size']+1)
  require(len(data)==item['size'] and hashlib.sha256(data).hexdigest()==item['sha256'],'PINNED_CORE_BYTES')
  target.write_bytes(data)
 base.save(out/'FETCH.json',dict(apk=str(apk.resolve()),native=str(library.resolve()),publisher=str(fixture.resolve()),selection_sha256=sha(SELECTION),native_source=row['native']['source']))
def read_json(device,path):
 try:return json.loads(device.shell('head','-c','1048576',path,check=False))
 except ValueError:return {}
def processes(device,uid):
 rows=[]
 for line in device.shell('ps','-A','-o','PID,UID,NAME').splitlines()[1:]:
  fields=line.split()
  if len(fields)==3 and fields[1]==uid:rows.append(dict(pid=int(fields[0]),uid=int(uid),name=fields[2]))
 return rows
# Reuse exact mature receipt assertions only, without its historical runner,
# fixtures, test matrices, shutdown commands or reset/cleanup behavior.
old=ROOT/'repairs/infinity-final-closure-2103407/android17_shutdown_probe.py'
node=next(n for n in ast.parse(old.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='verify_receipt')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(old), 'exec'))
def run(inputs,sdk,out):
 row=selected();proof=base.load(inputs/'INTAKE.json');require(not out.exists() and proof['selection_sha256']==sha(SELECTION),'CURRENT_FRESH_INPUTS')
 out.mkdir();report=dict(status='RUNNING',source=os.environ['SELECTED_SOURCE'],native_source=row['native']['source'],native_sha256=row['native']['native_sha256'],baseline_APK_sha256=prior.APK_SHA,native_injection=True,APK_install_acceptance=False,Fold='NOT_RUN',Core_path_changed=False,shutdown='NOT_RUN');device=None
 def save():base.save(out/'ANDROID-ESSENTIAL-ONLY.json',report)
 try:
  device=Device(out,sdk);report['environment']=base.environment(device,out)
  require(not device.shell('pm','list','packages',base.PACKAGE).strip(),'NEW_DISPOSABLE_VM_ONLY');base.root_reconnect(device,out)
  require(device.adb('install','--no-streaming',proof['apk'],timeout=300).strip().endswith('Success'),'EXACT83_INSTALL')
  require(not device.pids(),'BEFORE_FIRST_LAUNCH')
  installed=device.shell('pm','path',base.PACKAGE).strip().removeprefix('package:');require(device.shell('sha256sum',installed).split()[0]==prior.APK_SHA,'INSTALLED_ORIGINAL83')
  destination=prior.discover_native(device,installed,out);before=device.shell('stat','-c','%u:%g:%a:%C',destination).strip()
  staged='/data/local/tmp/infinity-essential-only-libkodi.so';device.adb('push',proof['native'],staged,timeout=300)
  require(device.shell('sha256sum',staged).split()[0]==row['native']['native_sha256'],'STAGED_NATIVE')
  device.shell('cp',staged,destination,timeout=120)
  require(device.shell('stat','-c','%u:%g:%a:%C',destination).strip()==before and device.shell('sha256sum',destination).split()[0]==row['native']['native_sha256'],'EXACT_NATIVE_AND_OWNERSHIP')
  require(not device.pids() and device.shell('sha256sum',installed).split()[0]==prior.APK_SHA,'UNCHANGED_APK_PRELAUNCH')
  device.shell('mkdir','-p',base.PROFILE,prior.REMOTE,prior.QP)
  settings=out/'FRESH-BOOTSTRAP-guisettings.xml';settings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting><setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>')
  sources=out/'FRESH-BOOTSTRAP-sources.xml';sources.write_text('<sources><files><source><name>Selected Essential-only QA</name><path pathversion="1">'+prior.REMOTE+'</path><allowsharing>false</allowsharing></source></files></sources>')
  device.adb('push',settings,base.PROFILE+'/guisettings.xml');device.adb('push',sources,base.PROFILE+'/sources.xml')
  for key in ('qa','core'):device.adb('push',inputs/proof[key]['archive'],prior.REMOTE+proof[key]['archive'])
  binary_dir=base.PROFILE+'/addon_data/'+prior.CORE+'/bin/android-arm64-v8a';device.shell('mkdir','-p',binary_dir)
  device.adb('push',Path(proof['publisher'])/'libadulthideout_core.so',binary_dir+'/libadulthideout_core.so')
  version=out/'FRESH-core-version.txt';version.write_text('1.0.1\n');device.adb('push',version,binary_dir+'/version.txt')
  uid=device.shell('stat','-c','%u','/data/user/0/'+base.PACKAGE).strip();require(uid.isdigit(),'ACTUAL_APP_UID')
  device.shell('chown','-R',uid+':'+uid,'/data/media/0/Android/data/'+base.PACKAGE);device.shell('restorecon','-RF','/data/media/0/Android/data/'+base.PACKAGE)
  device.adb('forward','tcp:19090','tcp:9090');report['startup']=base.start_once(device,1,out);save()
  report['first_party_activation']={}
  with ZipFile(proof['apk']) as archive:
   import xml.etree.ElementTree as ET
   for name in ('script.infinity.commandcenter','service.infinity.compat'):
    expected=ET.fromstring(archive.read('assets/addons/'+name+'/addon.xml')).get('version')
    details=device.rpc('Addons.GetAddonDetails',dict(addonid=name,properties=['version','enabled']))['addon']
    require(details['version']==expected,'EXACT_BUNDLED_FIRST_PARTY_VERSION:'+name)
    before=dict(details)
    if not details['enabled']:require(device.rpc('Addons.SetAddonEnabled',dict(addonid=name,enabled=True))=='OK','NORMAL_FIRST_PARTY_ENABLE')
    after=device.rpc('Addons.GetAddonDetails',dict(addonid=name,properties=['version','enabled']))['addon']
    require(after['enabled'] is True,'FIRST_PARTY_ENABLED')
    report['first_party_activation'][name]=dict(before=before,after=after)
  save()
  gui.install_zip(device,proof['qa'],dict(remote_zip_directory=prior.REMOTE),out,'local-observer')
  report['local_python']=prior.invoke(device,proof,out,'local-python',1,uuid.uuid4().hex);save()
  gui.install_zip(device,proof['core'],dict(remote_zip_directory=prior.REMOTE),out,'original-core');report['core_enable']=prior.enable(device,prior.CORE);save()
  log_path=base.HOME+'/temp/kodi.log';deadline=time.monotonic()+60
  while time.monotonic()<deadline:
   device.alive();log=device.shell('tail','-c','1048576',log_path,check=False)
   if '[AdultHideoutCore] In-process ctypes load failed:' in log and 'is not accessible for the namespace' in log:break
   time.sleep(.25)
  else:raise RuntimeError('ACTUAL_UNCHANGED_CORE_NAMESPACE_REJECTION_NOT_OBSERVED')
  (out/'core-before-close-kodi.log').write_text(log)
  require(device.shell('sha256sum',base.HOME+'/temp/libadulthideout_core.so').split()[0]==prior.CORE_BINARY,'ORIGINAL_COPIED_CORE_BINARY')
  source=base.HOME+'/addons/'+prior.CORE+'/service.py';require(device.shell('sha256sum',source).split()[0]==prior.CORE_SOURCE,'ORIGINAL_INSTALLED_SERVICE_SOURCE')
  private='/data/user/0/'+base.PACKAGE;control=base.PROFILE+'/addon_data/script.infinity.commandcenter/.android-checkpoint'
  owner=read_json(device,private+'/files/infinity-kodi-process.json');require(owner.get('phase')=='RUNNING' and owner.get('pid')==device.pid,'REAL_PROCESS_OWNER')
  report['before_owner']=owner
  # Reuse the existing shutdown transport's readiness contract. Home/JSON-RPC
  # alone does not establish first-party save participants are initialized.
  deadline=time.monotonic()+120
  while time.monotonic()<deadline:
   active=read_json(device,control+'/active.json');engine=read_json(device,control+'/engine.json');compat=read_json(device,control+'/compat-active.json');participant=read_json(device,control+'/participant.json')
   report['essential_readiness_observed']=dict(active=active,engine=engine,compat=compat,participant=participant);save()
   if (active.get('owner')==engine.get('owner')==compat.get('owner')==owner['owner'] and
       active.get('pid')==engine.get('pid')==compat.get('pid')==owner['pid'] and
       active.get('status')=='ACTIVE' and participant):break
   device.alive();time.sleep(.25)
  else:raise RuntimeError('ESSENTIAL_PARTICIPANTS_NOT_READY_NO_CLOSE_ATTEMPTED')
  report['essential_participants_ready']=dict(active=active,engine=engine,compat=compat,participant=participant)
  require(device.rpc('Favourites.AddFavourite',dict(title=FAVOURITE,type='window',window='home'))=='OK','NATIVE_PRESERVATION_RECORD')
  reply_path=prior.QP+'/reply.json';retained=device.shell('sha256sum',reply_path).split()[0]
  report['shutdown']='REQUESTED_NORMAL_CLOSE';save()
  report['close_command']=device.shell('am','start','-n',base.PACKAGE+'/.InfinityPowerControlActivity','-a',base.PACKAGE+'.action.CLOSE_KODI')
  deadline=time.monotonic()+45;receipt={}
  while time.monotonic()<deadline:
   receipt=read_json(device,private+'/files/infinity-checkpoint-close.json')
   if receipt.get('owner')==owner['owner']:
    if receipt.get('phase')=='CHECKPOINT_FAILED':break
    if receipt.get('phase')=='COMPLETE' and not processes(device,uid):break
   time.sleep(.25)
  report['close_receipt']=receipt;report['remaining_UID_processes']=processes(device,uid);save()
  require(not report['remaining_UID_processes'],'APPLICATION_UID_PROCESS_REMAINED')
  verify_receipt(receipt,owner);report['shutdown']='PASS_NORMAL_CLOSE_ESSENTIAL_DURABILITY_AND_UID_DEATH';save()
  require(device.shell('sha256sum',reply_path).split()[0]==retained,'PYTHON_SAVED_RECORD_RETAINED')
  require(device.shell('sha256sum',source).split()[0]==prior.CORE_SOURCE and device.shell('sha256sum',binary_dir+'/libadulthideout_core.so').split()[0]==prior.CORE_BINARY,'CORE_SOURCE_AND_USER_BINARY_RETAINED')
  device.adb('pull',base.PROFILE+'/Database',out/'Database',timeout=120)
  databases=list((out/'Database').glob('*.db'));require(databases,'REAL_DATABASES_PRESENT')
  for db in databases:
   with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as connection:require(connection.execute('PRAGMA integrity_check').fetchone()==('ok',),'DATABASE_INTEGRITY:'+db.name)
  report['database_integrity']=[p.name for p in databases]
  device.adb('forward','tcp:19090','tcp:9090');report['relaunch']=base.start_once(device,2,out);save()
  next_owner=read_json(device,private+'/files/infinity-kodi-process.json');require(next_owner.get('owner')!=owner['owner'] and next_owner.get('pid')==device.pid,'NEW_OWNER_SAME_PROFILE')
  require(device.shell('sha256sum',reply_path).split()[0]==retained,'SAVED_RECORD_SURVIVES_RELAUNCH')
  favourites=device.rpc('Favourites.GetFavourites',dict(properties=['window','windowparameter']))['favourites'];require(any(x.get('title')==FAVOURITE for x in favourites),'NATIVE_FAVOURITE_SURVIVES_RELAUNCH')
  report['local_python_after']=prior.invoke(device,proof,out,'local-python',2,uuid.uuid4().hex)
  require(device.shell('sha256sum',destination).split()[0]==row['native']['native_sha256'] and device.shell('sha256sum',installed).split()[0]==prior.APK_SHA,'RUNTIME_BYTES_RETAINED')
  report['status']='PASS_INDEPENDENT_NATIVE_INJECTION_SHUTDOWN_RELAUNCH_RETAINED_DATA_NOT_FOLD_ACCEPTANCE'
 except BaseException as error:
  report.update(status='FAIL',error=type(error).__name__+': '+str(error),traceback=traceback.format_exc())
 finally:
  save()
  if device:
   for path,name in [(base.HOME+'/temp/kodi.log','kodi.log'),('/data/user/0/'+base.PACKAGE+'/files/infinity-checkpoint-close.json','close.json'),('/data/user/0/'+base.PACKAGE+'/files/infinity-shutdown-native.jsonl','native-shutdown.jsonl')]+[(base.PROFILE+'/addon_data/script.infinity.commandcenter/.android-checkpoint/'+n,n) for n in ('active.json','engine.json','compat-active.json','participant.json')]:
    try:device.adb('pull',path,out/name,check=False,timeout=15)
    except Exception:pass
   try:(out/'logcat.txt').write_text(device.adb('logcat','-d','-v','threadtime',timeout=15))
   except Exception:pass
 print(json.dumps(dict(status=report['status'],error=report.get('error'))));require(report['status'].startswith('PASS_'),'INDEPENDENT_SHUTDOWN_FAILED')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=('gate','fetch','stage','run'));p.add_argument('--inputs',type=Path);p.add_argument('--sdk',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
 {'gate':selected,'fetch':lambda:fetch(a.out),'stage':lambda:prior.stage(a.inputs,a.sdk),'run':lambda:run(a.inputs,a.sdk,a.out)}[a.mode]()
