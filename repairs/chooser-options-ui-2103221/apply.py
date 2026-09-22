#!/usr/bin/env python3
"""2103221: restore Infinity-styled options UI for BOTH chooser gears.

Parent: successful 2103220 Active Section Lifecycle.
Authorized delta: Splash.showExperienceCardSettings presentation builder only + version identity.
No option/action/routing changes. Smart Return, Cobra lifecycle owner, playback and native are untouched.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103221
OLD_VERSION=2103220
OLD_NAME='1.0.9-Cobra-Active-Section-Lifecycle-RC1'
NEW_NAME='1.0.9-Cobra-Chooser-Options-UI-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def hb(b):return hashlib.sha256(b).hexdigest()
def sha(p):return hb(Path(p).read_bytes())
def req(v,m):
 if not v:raise RuntimeError(m)
def once(s,a,b,label):
 req(s.count(a)==1,f'{label} anchor drift ({s.count(a)})')
 return s.replace(a,b,1)
def mr(s,sig):
 i=s.find(sig);req(i>=0,'Missing '+sig);b=s.find('{',i);d=0
 for j in range(b,len(s)):
  if s[j]=='{':d+=1
  elif s[j]=='}':
   d-=1
   if d==0:return i,j+1
 raise RuntimeError('Unbalanced '+sig)
def method(s,sig):
 a,b=mr(s,sig);return s[a:b]
def replace_method(s,sig,new):
 a,b=mr(s,sig);return s[:a]+new.rstrip()+s[b:]

def patch_splash(path:Path):
 s=path.read_text()
 sig='private void showExperienceCardSettings(String experience)'
 before=method(s,sig)

 # This is the exact bad split visible on-device: Cobra gets stock Material AlertDialog,
 # Infinity gets the approved chooser visual renderer.
 old='''    (cobra ? new android.app.AlertDialog.Builder(this,
        "light".equals(chooserAppearanceMode())?android.R.style.Theme_Material_Light_Dialog_Alert:
        android.R.style.Theme_Material_Dialog_Alert)
        : new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings"))
'''
 new='''    new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings")
'''
 req(old in before,'Stock Cobra chooser builder preimage not found')
 after=before.replace(old,new,1)

 # Presentation only. The choices and callbacks remain exactly the same.
 for token in (
   '"Remember & launch " + label',
   '"Launch " + label + " just this time"',
   '"Ask every time"',
   '"Infinity Health Center"',
   '"Cobra Recovery"',
   'launchInfinityExperience(experience);',
   'showInfinityHealthCenter();',
   'showCobraRecovery();',
   '.remove(INFINITY_EXPERIENCE_DEFAULT).apply();',
 ):
  req(token in before and token in after,'Chooser behavior drift: '+token)
 req('Smart Return' not in after and 'cobra_smart_return' not in after,
     'Smart Return unexpectedly returned to chooser gear')
 req('new android.app.AlertDialog.Builder(this' not in after,
     'Stock chooser AlertDialog survived')
 req(after.count('new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings")')==1,
     'Unified chooser renderer missing')

 s=replace_method(s,sig,after)
 path.write_text(s)
 return hb(before.encode()),hb(after.encode())

def identity(shell:Path):
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
 g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
 g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName')
 gradle.write_text(g)

 runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
 r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime code')
 r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime name')
 runtime.write_text(r)

 pack=Path('scripts/package_background_resume.py');p=pack.read_text()
 old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
 req(p.count(old)>=2,'packager identity drift')
 pack.write_text(p.replace(old,new))
 return gradle

def apply(shell:Path):
 receipt_path=Path('engine/background-resume-source.json')
 receipt=json.loads(receipt_path.read_text())
 req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
     'Expected exact successful 2103220 replay')
 req(receipt.get('native_engine_sha256')==NATIVE,'Native engine receipt drift')

 splash=shell/(SOURCE+'Splash.java.in')
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
 smart=shell/(SOURCE+'CobraSmartReturn.java.in')
 main=shell/(SOURCE+'Main.java.in')
 for p in (splash,activity,smart,main):req(p.is_file(),'Missing '+str(p))

 activity_before=sha(activity);smart_before=sha(smart);main_before=sha(main)
 splash_before=sha(splash)
 method_before,method_after=patch_splash(splash)
 gradle=identity(shell)

 req(sha(activity)==activity_before,'Active section/lifecycle Activity changed')
 req(sha(smart)==smart_before,'Smart Return changed')
 req(sha(main)==main_before,'Kodi Main changed')

 for name in (SOURCE+'Splash.java.in',SOURCE+'InfinityLiveActivity.java.in',
              SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
  req(name in receipt['files'],'Receipt missing '+name)
  receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in'
 receipt['files'][rel]['after']=sha(gradle)

 receipt.update(
   version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
   chooser_options_ui_restored=True,
   infinity_options_renderer='chooser.settings',
   cobra_options_renderer='chooser.settings',
   stock_cobra_options_dialog_removed=True,
   chooser_option_actions_unchanged=True,
   smart_return_untouched=True,smart_return_file_sha256=smart_before,
   active_section_lifecycle_untouched=True,
   playback_unchanged=True,providers_unchanged=True,health_center_behavior_unchanged=True
 )
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Receipt drift '+name)

 Path('audit221').mkdir(exist_ok=True)
 Path('audit221/scope.json').write_text(json.dumps({
   'build':VERSION,'parent':OLD_VERSION,
   'splash_before_sha256':splash_before,'options_method_before_sha256':method_before,
   'options_method_after_sha256':method_after,
   'both_gears_use_renderer':'chooser.settings',
   'stock_cobra_alert_dialog_removed':True,
   'option_actions_unchanged':True,
   'smart_return_untouched':True,'smart_return_sha256':smart_before,
   'activity_unchanged_sha256':activity_before,
   'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,
   'status':'TEST CANDIDATE'
 },indent=2)+'\n')
 print('PASS: 2103221 both Infinity/Cobra chooser option menus use approved chooser renderer; behavior untouched')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True)
 a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
