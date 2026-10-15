#!/usr/bin/env python3
"""2103216: put Smart Return in Cobra Settings > Experience & Display.

Parent: exact successful 2103215.
Only relocates the Smart Return control. The 2103215 top-left Settings drawer fix stays.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103216
OLD_VERSION=2103215
OLD_NAME='1.0.9-Cobra-Smart-Return-Experience-Drawer-RC1'
NEW_NAME='1.0.9-Cobra-Smart-Return-Experience-Display-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE_SHA='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(v,m):
 if not v:raise RuntimeError(m)
def once(text,old,new,label):
 require(text.count(old)==1,f'{label} anchor drift ({text.count(old)})')
 return text.replace(old,new,1)
def method_range(text,sig):
 i=text.find(sig);require(i>=0,'Missing method: '+sig);b=text.find('{',i);d=0
 for j in range(b,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return i,j+1
 raise RuntimeError('Unbalanced method: '+sig)
def method(text,sig):
 a,b=method_range(text,sig);return text[a:b]
def mh(text,sigs):return {sig:sha_bytes(method(text,sig).encode()) for sig in sigs}

ACTIVITY_PROTECT=[
 'private void cobraRefreshAmbient()',
 'private void cobraRefreshLiveAmbientSurfaces(int mode,boolean live,int tint)',
 'private void cobraApplyNightCinema(View header,View footer,View pause)',
 'private void cobraReturnFromSettings()',
 'private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures)',
 'private void cobraShowVodDetails(VodItem item)',
 'private void openSeries(VodItem item)',
 'private void cobraShowVodCompletion()',
 'private void startSinglePlayer(String url)',
 'private void playChannel(Channel channel)',
 'private void cobraStartLocalTimeshift',
 'private LoadResult loadXtream(LiveSource source)',
 'private LoadResult loadM3u(LiveSource source)',
]
SPLASH_PROTECT=[
 'private void showInfinityHealthCenter()',
 'private void infinityShowHealthText(String title,String body)',
 'private String infinityHealthExitHistory(boolean includeTrace)',
 'private String infinityHealthReport()',
]

def patch_activity(path):
 s=path.read_text();before=mh(s,ACTIVITY_PROTECT)
 settings=method(s,'private void showSettings()')
 require('cobra_settings_drawer_header' in settings and 'toggleCobraDrawer()' in settings,
         '2103215 top-left Settings drawer correction missing')
 require('cobra_settings_return' not in settings and 'Button settingsBack=' not in settings,
         'Obsolete inline Back control returned')
 require('Button smartReturn=action("SMART RETURN' not in settings,
         'Unexpected pre-existing Smart Return row in full Settings')

 anchor='    list.addView(appearance, new LinearLayout.LayoutParams(-1, dp(56)));\n'
 insertion='''    list.addView(appearance, new LinearLayout.LayoutParams(-1, dp(56)));
    Button smartReturn=action("SMART RETURN  •  "+(CobraSmartReturn.enabled(mPrefs)?"ON":"OFF"));
    smartReturn.setTag("cobra_smart_return_experience_display");
    smartReturn.setContentDescription("Smart Return. Remember the last Cobra destination and browsing position.");
    smartReturn.setOnClickListener(v->cobraShowSmartReturnSetting());
    list.addView(smartReturn,new LinearLayout.LayoutParams(-1,dp(56)));
'''
 s=once(s,anchor,insertion,'Experience & Display Smart Return placement')
 settings=method(s,'private void showSettings()')
 require(settings.index('list.addView(appearance') < settings.index('cobra_smart_return_experience_display'),
         'Smart Return not placed after Appearance')
 require('cobraAddPresentationSettings(list)' in settings,'Experience & Display presentation controls missing')
 require(settings.index('cobra_smart_return_experience_display') < settings.index('cobraAddPresentationSettings(list)'),
         'Smart Return not kept inside Experience & Display block')
 path.write_text(s)
 require(mh(s,ACTIVITY_PROTECT)==before,'Protected 2103215 activity behavior changed')

def patch_splash(path):
 s=path.read_text();before=mh(s,SPLASH_PROTECT)
 a,b=method_range(s,'private void showExperienceCardSettings(String experience)')
 replacement='''  private void showExperienceCardSettings(String experience)
  {
    final boolean cobra = "live".equals(experience);
    final String title = cobra ? "Cobra options" : "Infinity options";
    final String label = cobra ? "Cobra" : "Infinity";
    final String[] options = cobra ? new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Infinity Health Center",
        "Cobra Recovery"
    } : new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Infinity Health Center"
    };
    (cobra ? new android.app.AlertDialog.Builder(this,
        "light".equals(chooserAppearanceMode())?android.R.style.Theme_Material_Light_Dialog_Alert:
        android.R.style.Theme_Material_Dialog_Alert)
        : new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings"))
        .setTitle(title)
        .setItems(options, (dialog, which) -> {
          if (which == 0)
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .putString(INFINITY_EXPERIENCE_DEFAULT, experience).apply();
            launchInfinityExperience(experience);
          }
          else if (which == 1)
          {
            launchInfinityExperience(experience);
          }
          else if (which == 2)
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .remove(INFINITY_EXPERIENCE_DEFAULT).apply();
            android.widget.Toast.makeText(this,
                "Infinity will ask which experience to open next time.",
                android.widget.Toast.LENGTH_SHORT).show();
          }
          else if (which == 3)
          {
            showInfinityHealthCenter();
          }
          else if (which == 4 && cobra)
          {
            showCobraRecovery();
          }
        })
        .setNegativeButton("Cancel", null)
        .show();
  }'''
 s=s[:a]+replacement+s[b:]
 exp=method(s,'private void showExperienceCardSettings(String experience)')
 require('Smart Return' not in exp and 'cobra_smart_return' not in exp,
         'Smart Return still exposed in Choose Your Experience gear options')
 for token in ('Infinity Health Center','showInfinityHealthCenter()','Cobra Recovery'):
  require(token in exp,'Chooser contract lost: '+token)
 path.write_text(s)
 require(mh(s,SPLASH_PROTECT)==before,'Infinity Health Center behavior changed')

def patch_identity(shell):
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
 g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','Gradle version')
 g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','Gradle name');gradle.write_text(g)
 runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
 r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','Runtime version')
 r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'Runtime name');runtime.write_text(r)
 pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
 require(p.count(old)>=2,'Packager identity drift');pack.write_text(p.replace(old,new));return gradle

def apply(shell):
 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
 require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
         'Expected exact successful 2103215 replay')
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
 splash=shell/(SOURCE+'Splash.java.in')
 smart=shell/(SOURCE+'CobraSmartReturn.java.in')
 main=shell/(SOURCE+'Main.java.in')
 for p in (activity,splash,smart,main):require(p.is_file(),'Required 2103215 source missing: '+str(p))
 before_main=sha(main);before_smart=sha(smart)
 patch_activity(activity);patch_splash(splash);gradle=patch_identity(shell)
 require(sha(main)==before_main,'Kodi Main changed')
 require(sha(smart)==before_smart,'Smart Return engine/default changed')
 require('getBoolean(ENABLED,true)' in smart.read_text(),'Smart Return default-ON behavior lost')
 require(receipt.get('native_engine_sha256')==NATIVE_SHA,'Wrong protected native engine receipt')

 for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'Splash.java.in',SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
  require(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE_SHA,
   smart_return_default_on=True,smart_return_location='Cobra Settings > Experience & Display',
   smart_return_removed_from_chooser_options=True,settings_inline_back_removed=True,
   settings_navigation='top-left Cobra drawer',locked_2103214_media_unchanged=True,
   live_tv_blue_ambient_unchanged=True,health_center_unchanged=True,
   playback_unchanged=True,providers_unchanged=True,video_recolored=False)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final receipt drift: '+name)

 Path('audit216').mkdir(exist_ok=True)
 Path('audit216/scope.json').write_text(json.dumps({
   'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,
   'smart_return_default_on':True,'smart_return_location':'Cobra Settings > Experience & Display',
   'smart_return_chooser_removed':True,'settings_inline_back_removed':True,'settings_top_left_drawer':True,
   'locked_2103214_media_unchanged':True,'live_tv_blue_ambient_unchanged':True,
   'health_center_unchanged':True,'playback_unchanged':True,'providers_unchanged':True,
   'native_engine_rebuilt':False,'video_recolored':False,'status':'TEST CANDIDATE'
 },indent=2)+'\n')
 print('PASS: 2103216 Smart Return is in Experience & Display; chooser option removed; Settings drawer preserved')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);args=p.parse_args();apply(args.shell)
if __name__=='__main__':main()
