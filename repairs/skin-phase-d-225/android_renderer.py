"""Actual unchanged signed TEST3 APK; disposable emulator, no native rebuild.

Only the fixture skin's dependency list is shortened for offline rendering.
The production skin ID, viewport declaration, XML, scripts, and assets remain exact.
This does not certify third-party providers, Samsung input, PiP, or shutdown.
"""
import argparse,hashlib,importlib.util,json,shutil,time,traceback
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
  probe.adb('root');probe.adb('wait-for-device')
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
  helper=staging/ADDON;helper.mkdir()
  (helper/'addon.xml').write_text('<addon id="'+ADDON+'" name="Phase D renderer" version="1.0.0" provider-name="Infinity CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable renderer</summary><description lang="en_GB">Actual native renderer evidence</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
  shutil.copyfile(HERE/'runtime.py',helper/'default.py');probe.adb('push',helper,probe.PROFILE+'/../addons/'+ADDON)
  backing='/data/media/0/Android/data/'+probe.PACKAGE
  probe.shell('chown','-R',uid+':'+uid,backing,probe.PRIVATE+'/shared_prefs');probe.shell('restorecon','-RF',backing,probe.PRIVATE+'/shared_prefs')
  stage('launching-normal-APK-profile')
  probe.adb('logcat','-c');probe.shell('am','start','-W','-n',probe.PACKAGE+'/.Splash')
  report['first_party']=probe.enable_first_party(a.out)
  report['owner']=probe.wait_ready()
  assert probe.rpc('Settings.SetSettingValue',{'setting':'general.addonupdates','value':2}) is True
  for name in (skin.name,ADDON):assert probe.rpc('Addons.SetAddonEnabled',{'addonid':name,'enabled':True})=='OK'
  assert probe.rpc('Settings.SetSettingValue',{'setting':'lookandfeel.skin','value':skin.name}) is True
  time.sleep(4)
  # Public RPC acknowledges Kodi's normal keep-skin dialog if one is shown.
  window=probe.rpc('GUI.GetProperties',{'properties':['currentwindow']}).get('currentwindow',{})
  if window.get('id')==10100:probe.rpc('Input.ExecuteAction',{'action':'select'})
  for name,w,h in [('cover',1080,2400),('inner',1800,1440),('wide',2400,1080)]:
   stage('rendering-'+name)
   probe.shell('wm','size',f'{w}x{h}');probe.shell('wm','density','320');time.sleep(3)
   config=a.out/'phase-d-config.json';config.write_text(json.dumps({'version':a.version,'width':w,'height':h,'android':True,'skin_id':skin.name}))
   probe.adb('push',config,probe.PROFILE+'/phase-d-config.json')
   probe.shell('rm','-rf',probe.PROFILE+'/phase-d-results') # Disposable test output only.
   assert probe.rpc('Addons.ExecuteAddon',{'addonid':ADDON,'params':['run'],'wait':False})=='OK'
   deadline=time.monotonic()+300
   while time.monotonic()<deadline:
    r=probe.read_json(probe.PROFILE+'/phase-d-results/result.json')
    if r:break
    time.sleep(1)
   else:raise RuntimeError('Renderer timed out: '+name)
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
