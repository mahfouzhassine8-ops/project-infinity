"""Actual unchanged signed TEST3 APK; disposable emulator, no native rebuild.

Only the fixture skin's dependency list is shortened for offline rendering.
The production skin ID, viewport declaration, XML, scripts, and assets remain exact.
This does not certify third-party providers, Samsung input, PiP, or shutdown.
"""
import argparse,hashlib,importlib.util,json,shutil,time,traceback,subprocess
from pathlib import Path
import xml.etree.ElementTree as E

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('preserved_probe',HERE.parent/'android-checkpoint-shutdown/runtime-tests/essential_android_probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
ADDON='script.infinity.phased.test'

def main(a):
 a.out.mkdir(parents=True,exist_ok=True);report={'passed':False,'physical_fold':False,'native_rebuilt':False,'version':a.version,'viewports':[]}
 def stage(name):
  report['stage']=name;(a.out/'ANDROID-RENDERER.json').write_text(json.dumps(report,indent=2));print(name,flush=True)
 try:
  report['apk_sha256']=hashlib.sha256(a.apk.read_bytes()).hexdigest()
  assert report['apk_sha256']=='6e28bfea7cdb5e497ee21601a714e738db7a57edc3c5c0d29a9c19d461031854'
  stage('installing-existing-signed-TEST3')
  # Android Emulator restarts adbd when "adb root" is requested. During
  # that expected restart the CLI can return "connection closed" even
  # though the device comes back correctly. Retry only this bootstrap
  # handshake and insist on an actual root UID; never waive render checks.
  bootstrap_errors=[]
  for attempt in range(1,7):
   try:
    probe.adb('root',check=False)
    probe.adb('wait-for-device')
    if probe.shell('id','-u').strip()=='0':break
    bootstrap_errors.append('attempt '+str(attempt)+': shell uid was not root')
   except (RuntimeError,subprocess.TimeoutExpired) as error:
    bootstrap_errors.append('attempt '+str(attempt)+': '+str(error)[-300:])
   time.sleep(1.2)
  else:raise RuntimeError('Disposable emulator adbd never became root: '+repr(bootstrap_errors))
  report['adb_root_attempts']=attempt
  assert probe.shell('getprop','ro.kernel.qemu').strip()=='1'
  assert probe.PACKAGE not in probe.shell('pm','list','packages',probe.PACKAGE)
  assert 'arm64-v8a' in probe.shell('getprop','ro.product.cpu.abilist')
  assert 'Success' in probe.adb('install','--no-incremental',a.apk)
  probe.shell('input','keyevent','82')
  for permission in ('android.permission.READ_EXTERNAL_STORAGE','android.permission.WRITE_EXTERNAL_STORAGE'):
   probe.shell('pm','grant',probe.PACKAGE,permission,check=False)
  probe.shell('appops','set',probe.PACKAGE,'MANAGE_EXTERNAL_STORAGE','allow',check=False)
  probe.shell('mkdir','-p',probe.PRIVATE+'/shared_prefs',probe.PROFILE+'/../addons')
  uid=probe.shell('stat','-c','%u',probe.PRIVATE).strip();assert uid.isdigit();probe.APP_UID=uid
  prefs=a.out/'experience.xml';prefs.write_text('<map><string name="default">infinity</string></map>')
  probe.adb('push',prefs,probe.PRIVATE+'/shared_prefs/infinity_experience.xml')
  for command,loopback in (('iptables','127.0.0.0/8'),('ip6tables','::1/128')):
   probe.shell(command,'--wait','5','-I','OUTPUT','-m','owner','--uid-owner',uid,'!','-d',loopback,'-j','REJECT')
  staging=a.out/'staging';staging.mkdir()
  for name in probe.FIRST_PARTY:
   shutil.copytree(a.installed_addons/name,staging/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
   probe.adb('push',staging/name,probe.PROFILE+'/../addons/'+name)
  skin=staging/'skin.infinity.diggz';shutil.copytree(a.skin,skin)
  report['skin_source_sha256']={str(p.relative_to(skin)):hashlib.sha256(p.read_bytes()).hexdigest() for p in skin.rglob('*') if p.is_file()}
  t=E.parse(skin/'addon.xml');requires=t.getroot().find('requires')
  for n in list(requires):
   if n.get('addon') not in ('xbmc.gui','xbmc.python','script.infinity.commandcenter'):requires.remove(n)
  t.write(skin/'addon.xml',encoding='utf-8')
  report['fixture_only_manifest_override']='Offline rendering omits skinshortcuts, external studio/label resources and Rails dependency declarations. Production package is unchanged; provider content and helper integration are not certified.'
  probe.adb('push',skin,probe.PROFILE+'/../addons/'+skin.name)
  # Represent an established Infinity installation at native boot. Selecting
  # a 2,000+ XML skin over slow ARM-on-x86 translation can consume Kodi's
  # entire ten-second "keep this skin" countdown before the dialog is usable.
  # Seed only the disposable fixture's own normal Kodi setting. This is not
  # a production APK/skin change or a forced success receipt.
  skin_settings=a.out/'fixture-startup-guisettings.xml'
  skin_settings.write_text('<settings version="2"><setting id="lookandfeel.skin">'+skin.name+'</setting></settings>')
  probe.adb('push',skin_settings,probe.PROFILE+'/guisettings.xml')
  helper=staging/ADDON;helper.mkdir()
  (helper/'addon.xml').write_text('<addon id="'+ADDON+'" name="Phase D renderer" version="1.0.0" provider-name="Infinity CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable renderer</summary><description lang="en_GB">Actual native renderer evidence</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
  shutil.copyfile(HERE/'runtime.py',helper/'default.py');probe.adb('push',helper,probe.PROFILE+'/../addons/'+ADDON)
  # This transient test addon only acknowledges Kodi's *real* keep-skin
  # dialog. On ARM-translated emulators the skin can take almost the whole
  # countdown to load; polling from the host after RPC returns is too late.
  # No native code, production skin file, or user profile is modified.
  confirm_id='script.infinity.phaseconfirm.test'
  confirm_addon=staging/confirm_id;confirm_addon.mkdir()
  (confirm_addon/'addon.xml').write_text(
   '<addon id="'+confirm_id+'" name="Infinity skin dialog verifier" version="1.0.0" provider-name="Infinity CI">'
   '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
   '<extension point="xbmc.python.script" library="default.py"/>'
   '<extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable skin confirmation</summary>'
   '<description lang="en_GB">Approve the actual native keep-skin dialog in an emulator fixture</description>'
   '<platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
  (confirm_addon/'default.py').write_text("""
import json
import time
from pathlib import Path
import xbmc
import xbmcgui
import xbmcvfs
out = Path(xbmcvfs.translatePath('special://profile/phase-d-skin-confirm.json'))
def record(stage, **extra):
    tmp=out.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(dict(stage=stage, monotonic=time.monotonic(), **extra)))
    tmp.replace(out)
record('armed')
watch = xbmc.Monitor()
until = time.monotonic()+90
while not watch.abortRequested() and time.monotonic() < until:
    dialog = xbmcgui.getCurrentWindowDialogId()
    if dialog == 10100 and xbmc.getSkinDir() == 'skin.infinity.diggz':
        try:
            # The Python Window wrapper can report focus 0 for a native modal
            # even while the actual dialog is active. Route user-like actions
            # to the active Kodi GUI instead; then prove the skin stayed loaded.
            # Approved Infinity DialogConfirm.xml: 9000 = button group,
            # 11 = OK (left button), 10 = Cancel (right button).
            window=xbmcgui.Window(dialog)
            focus_before=window.getFocusId()
            xbmc.executebuiltin('SetFocus(9000)', True)
            xbmc.executebuiltin('SetFocus(11)', True)
            xbmc.sleep(70)
            focus_after=window.getFocusId()
            xbmc.executebuiltin('Action(Select)', True)
            record('submitted_native_ok', dialog=dialog,
                   observed_focus_before=focus_before, observed_focus_after=focus_after)
        except Exception as exc:
            record('dialog_error', error=repr(exc), dialog=dialog)
        break
    xbmc.sleep(80)
else:
    record('native_dialog_not_seen')
""")
  probe.adb('push',confirm_addon,probe.PROFILE+'/../addons/'+confirm_id)
  backing='/data/media/0/Android/data/'+probe.PACKAGE
  probe.shell('chown','-R',uid+':'+uid,backing,probe.PRIVATE+'/shared_prefs');probe.shell('restorecon','-RF',backing,probe.PRIVATE+'/shared_prefs')
  stage('launching-normal-APK-profile')
  probe.adb('logcat','-c');probe.shell('am','start','-W','-n',probe.PACKAGE+'/.Splash')
  report['first_party']=probe.enable_first_party(a.out)
  report['owner']=probe.wait_ready()
  assert probe.rpc('Settings.SetSettingValue',{'setting':'general.addonupdates','value':2}) is True
  for name in (skin.name,ADDON):assert probe.rpc('Addons.SetAddonEnabled',{'addonid':name,'enabled':True})=='OK'
  stage('verify-native-infinity-skin')
  engine_log_path=probe.PROFILE+'/../temp/kodi.log'
  expected_skin='/addons/'+skin.name+'/'
  initial_log=probe.shell('cat',engine_log_path,check=False)
  loaded=[line for line in initial_log.splitlines() if 'load skin from: ' in line]
  if not any(expected_skin in line for line in loaded):
   # A valid Kodi guisettings.xml may name Infinity while the very first
   # boot still displays Estuary until addon discovery finishes. A setting
   # string alone is NOT proof of actual Infinity rendering.
   report['initial_boot_skin']='skin.estuary despite configured '+skin.name
   stage('reselecting-native-infinity-skin-after-addon-discovery')
   assert probe.rpc('Addons.SetAddonEnabled',{'addonid':confirm_id,'enabled':True})=='OK'
   assert probe.rpc('Settings.SetSettingValue',{'setting':'lookandfeel.skin','value':'skin.estuary'}) is True
   assert probe.rpc('Addons.ExecuteAddon',{'addonid':confirm_id,'params':['arm'],'wait':False})=='OK'
   deadline=time.monotonic()+20
   armed={}
   while time.monotonic()<deadline:
    armed=probe.read_json(probe.PROFILE+'/phase-d-skin-confirm.json')
    if armed.get('stage')=='armed':break
    time.sleep(.15)
   assert armed.get('stage')=='armed',('Native confirmation helper did not arm',armed)
   assert probe.rpc('Settings.SetSettingValue',{'setting':'lookandfeel.skin','value':skin.name}) is True
   deadline=time.monotonic()+65
   confirmation={}
   while time.monotonic()<deadline:
    state=probe.read_json(probe.PROFILE+'/phase-d-skin-confirm.json')
    # A partially read/missing JSON receipt is not a negative result.
    # The helper publishes atomically; wait for an explicit terminal state.
    if state.get('stage') in ('submitted_native_ok','dialog_error','native_dialog_not_seen'):
     confirmation=state
     break
    time.sleep(.2)
   report['native_skin_confirmation']=confirmation
   assert confirmation.get('stage')=='submitted_native_ok',('Native keep-skin OK was not submitted',confirmation)
  # The actual rendered skin MUST be Infinity, and it must stay so after
  # the native dialog countdown. No synthetic success or forced XML rewrite.
  time.sleep(4)
  selected=probe.rpc('Settings.GetSettingValue',{'setting':'lookandfeel.skin'}).get('value')
  engine_log=probe.shell('cat',engine_log_path,check=False)
  signature='load skin from: '
  loaded=[line for line in engine_log.splitlines() if signature in line]
  assert selected==skin.name, ('Signed engine did not retain Infinity skin setting',selected,loaded[-4:])
  assert loaded and expected_skin in loaded[-1],('Signed engine still rendered another skin',loaded[-5:])
  assert 'skin loaded...' in engine_log, 'Signed engine did not finish loading its skin'
  report['selected_skin']=selected
  report['native_loaded_skin']=loaded[-1].strip()
  report['actual_signed_engine_skin_verified']=True
  for name,w,h in [('cover',1080,2400),('inner',1800,1440),('wide',2400,1080)]:
   stage('rendering-'+name)
   probe.shell('wm','size',f'{w}x{h}');probe.shell('wm','density','320');time.sleep(3)
   config=a.out/'phase-d-config.json';config.write_text(json.dumps({'version':a.version,'width':w,'height':h,'android':True,'skin_id':skin.name}))
   probe.adb('push',config,probe.PROFILE+'/phase-d-config.json')
   # adb runs as root on this disposable emulator. A pushed file can remain
   # root-owned and mode 0600, making the actual Infinity Python addon fail
   # with PermissionError before it writes a renderer result. Fix only the
   # temporary fixture file, never the installed APK or production skin.
   raw_config='/data/media/0/Android/data/'+probe.PACKAGE+'/files/.kodi/userdata/phase-d-config.json'
   probe.shell('chown',uid+':'+uid,raw_config)
   probe.shell('chmod','644',raw_config)
   probe.shell('restorecon','-F',raw_config,check=False)
   config_stat=probe.shell('stat','-c','%u:%a',raw_config).strip()
   assert config_stat.split(':')[0]==uid, ('Renderer config owner mismatch',config_stat,uid)
   report['fixture_config_permissions']=config_stat
   probe.shell('rm','-rf',probe.PROFILE+'/phase-d-results') # Disposable test output only.
   assert probe.rpc('Addons.ExecuteAddon',{'addonid':ADDON,'params':['run'],'wait':False})=='OK'
   # Real signed ARM64 Infinity translates on an x86 emulator. Forty-two
   # screenshots plus sixty dialog/focus cycles can legitimately take more
   # than five minutes. Give progressing work a bounded 8-minute window;
   # independently reject a GUI that makes no progress for 100 seconds.
   deadline=time.monotonic()+480
   last_observation=0
   last_marker=None
   last_advance=time.monotonic()
   observation={}
   while time.monotonic()<deadline:
    r=probe.read_json(probe.PROFILE+'/phase-d-results/result.json')
    if r:break
    if time.monotonic()-last_observation>=12:
     now=time.monotonic()
     last_observation=now
     progress=probe.read_json(probe.PROFILE+'/phase-d-results/progress.json')
     live=probe.read_json(probe.PROFILE+'/phase-d-results/phase-state.json')
     marker=(live.get('phase'),live.get('screens'),live.get('cycle'))
     if marker!=(None,None,None) and marker!=last_marker:
      last_marker=marker
      last_advance=now
     observation={'viewport':name,'seconds_remaining':round(deadline-now),
                  'progress_screens':len(progress.get('screens',[])) if isinstance(progress,dict) else None,
                  'live_phase':live.get('phase'),'live_cycle':live.get('cycle'),
                  'seconds_without_progress':round(now-last_advance),
                  'current_window':'not queried during possible GUI deadlock'}
     report['last_renderer_observation']=observation
     (a.out/'last-renderer-observation.json').write_text(json.dumps(observation,indent=2))
     print('Renderer progress:',json.dumps(observation),flush=True)
     if now-last_advance>100:
      probe.adb('pull',probe.PROFILE+'/phase-d-results',a.out/('timeout-progress-'+name),check=False)
      raise RuntimeError('Real Infinity GUI stopped advancing: '+json.dumps(observation))
    time.sleep(1)
   else:
    probe.adb('pull',probe.PROFILE+'/phase-d-results',a.out/('timeout-progress-'+name),check=False)
    raise RuntimeError('Renderer timed out after 480 seconds: '+name+'; '+json.dumps(observation))
   target=a.out/name;target.mkdir();probe.adb('pull',probe.PROFILE+'/phase-d-results',target)
   report['viewports'].append({'name':name,'result':r});assert r.get('passed'),r.get('failure')
  report['passed']=True;stage('actual-native-renderer-completed')
 except Exception:
  report['failure']=traceback.format_exc();raise
 finally:
  (a.out/'ANDROID-RENDERER.json').write_text(json.dumps(report,indent=2))
  (a.out/'kodi.log').write_text(probe.shell('cat',probe.PROFILE+'/../temp/kodi.log',check=False))
  (a.out/'logcat.txt').write_text(probe.adb('logcat','-d'))
  probe.adb('pull',probe.PROFILE+'/phase-d-results',a.out/'last-progress',check=False)

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('apk','installed-addons','skin','out'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--version',required=True);main(p.parse_args())
