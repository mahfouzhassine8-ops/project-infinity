#!/usr/bin/env python3
"""2103215: move Smart Return into Cobra Experience options and make Settings use the top-left drawer.

Parent: exact locked 2103214.
Scope is navigation/preferences only. No media, Live TV, playback, Health, provider, native, ambient or player changes.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103215
OLD_VERSION=2103214
OLD_NAME='1.0.9-Cobra-Media-Details-Final-RC1'
NEW_NAME='1.0.9-Cobra-Smart-Return-Experience-Drawer-RC1'
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

 back='''    Button settingsBack=action("‹  BACK");
    settingsBack.setTag("cobra_settings_return");
    settingsBack.setContentDescription("Return to previous Cobra screen");
    settingsBack.setOnClickListener(v->cobraReturnFromSettings());
'''
 require(s.count(back)==1,'Settings back row drift')
 s=s.replace(back,'',1)
 s=once(s,'    list.addView(settingsBack, new LinearLayout.LayoutParams(-1, dp(52)));\n','',
        'Remove Settings back placement')

 smart='''    Button smartReturn=action("SMART RETURN  •  "+(CobraSmartReturn.enabled(mPrefs)?"ON":"OFF"));smartReturn.setTag("cobra_smart_return_setting");smartReturn.setOnClickListener(v->cobraShowSmartReturnSetting());list.addView(smartReturn,new LinearLayout.LayoutParams(-1,dp(56)));
'''
 require(s.count(smart)==1,'Smart Return full Settings row drift')
 s=s.replace(smart,'',1)

 anchor='''    clearStage("COBRA • SETTINGS");
    CobraBrandDrawable settingsBrand=new CobraBrandDrawable();settingsBrand.setBounds(0,0,dp(40),dp(32));mHeader.setCompoundDrawablePadding(dp(8));mHeader.setCompoundDrawablesRelative(null,null,settingsBrand,null);
'''
 repl='''    clearStage("COBRA • SETTINGS");
    if(mHeader!=null){
      mHeader.setText("☰  COBRA • SETTINGS");
      mHeader.setClickable(true);mHeader.setFocusable(true);
      mHeader.setContentDescription("Open Cobra navigation drawer");
      mHeader.setTag("cobra_settings_drawer_header");
      mHeader.setOnClickListener(v->toggleCobraDrawer());
    }
    CobraBrandDrawable settingsBrand=new CobraBrandDrawable();settingsBrand.setBounds(0,0,dp(40),dp(32));mHeader.setCompoundDrawablePadding(dp(8));mHeader.setCompoundDrawablesRelative(null,null,settingsBrand,null);
'''
 s=once(s,anchor,repl,'Settings top-left drawer ownership')

 for token in ('cobra_settings_return','Button settingsBack=','SMART RETURN  •  '):
  require(token not in method(s,'private void showSettings()'),'Obsolete Settings control survived: '+token)
 settings=method(s,'private void showSettings()')
 for token in ('☰  COBRA • SETTINGS','toggleCobraDrawer()','cobra_settings_drawer_header'):
  require(token in settings,'Settings drawer contract missing: '+token)
 path.write_text(s)
 require(mh(s,ACTIVITY_PROTECT)==before,'Protected 2103214 activity behavior changed')

def patch_smart_return(path):
 s=path.read_text()
 old='''  static boolean enabled(SharedPreferences preferences){
    try{return preferences!=null&&preferences.getBoolean(ENABLED,false);}catch(ClassCastException invalid){return false;}
  }'''
 new='''  static boolean enabled(SharedPreferences preferences){
    try{return preferences!=null&&preferences.getBoolean(ENABLED,true);}catch(ClassCastException invalid){return true;}
  }'''
 s=once(s,old,new,'Smart Return default ON')
 path.write_text(s)

def patch_splash(path):
 s=path.read_text();before=mh(s,SPLASH_PROTECT)
 old='''    final String[] options = cobra ? new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Cobra Recovery"
    } : new String[]{'''
 new='''    final boolean smartReturn = getSharedPreferences("infinity_cobra_live", MODE_PRIVATE)
        .getBoolean("cobra_smart_return", true);
    final String[] options = cobra ? new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Smart Return  •  " + (smartReturn ? "ON" : "OFF"),
        "Cobra Recovery"
    } : new String[]{'''
 s=once(s,old,new,'Cobra Experience Smart Return row')

 old_handler='''          else if(which==3&&cobra)
          {
            showCobraRecovery();
          }
          else
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()'''
 new_handler='''          else if(which==3&&cobra)
          {
            getSharedPreferences("infinity_cobra_live", MODE_PRIVATE).edit()
                .putBoolean("cobra_smart_return", !smartReturn).apply();
            showExperienceCardSettings(experience);
          }
          else if(which==4&&cobra)
          {
            showCobraRecovery();
          }
          else
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()'''
 s=once(s,old_handler,new_handler,'Cobra Experience Smart Return action')
 exp=method(s,'private void showExperienceCardSettings(String experience)')
 for token in ('Smart Return  •  ','infinity_cobra_live','cobra_smart_return','which==4&&cobra'):
  require(token in exp,'Experience Smart Return contract missing: '+token)
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
 receipt_path=Path('engine/background-resume-source.json')
 receipt=json.loads(receipt_path.read_text())
 require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
         'Expected exact locked 2103214 replay')

 activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
 splash=shell/(SOURCE+'Splash.java.in')
 smart=shell/(SOURCE+'CobraSmartReturn.java.in')
 main=shell/(SOURCE+'Main.java.in')
 require(activity.is_file() and splash.is_file() and smart.is_file() and main.is_file(),'Required 2103214 source missing')

 before_main=sha(main);before_native=receipt.get('native_engine_sha256')
 patch_activity(activity);patch_splash(splash);patch_smart_return(smart);gradle=patch_identity(shell)
 require(sha(main)==before_main,'Kodi Main changed unexpectedly')
 require(before_native==NATIVE_SHA,'Wrong protected native engine receipt')

 for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'Splash.java.in',SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
  require(name in receipt['files'],'Receipt missing '+name)
  receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE_SHA,
   smart_return_default_on=True,smart_return_location='Cobra Experience options',
   smart_return_removed_from_full_settings=True,settings_inline_back_removed=True,
   settings_navigation='top-left Cobra drawer',locked_2103214_media_unchanged=True,
   live_tv_blue_ambient_unchanged=True,settings_return_state_engine_preserved=True,
   health_center_unchanged=True,playback_unchanged=True,providers_unchanged=True,video_recolored=False)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final receipt drift: '+name)

 Path('audit215').mkdir(exist_ok=True)
 Path('audit215/scope.json').write_text(json.dumps({
   'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,
   'smart_return_default_on':True,'smart_return_location':'Cobra Experience options',
   'smart_return_full_settings_row_removed':True,'settings_inline_back_removed':True,
   'settings_top_left_drawer':True,'settings_return_state_engine_preserved':True,
   'locked_2103214_media_unchanged':True,'live_tv_blue_ambient_unchanged':True,
   'health_center_unchanged':True,'playback_unchanged':True,'providers_unchanged':True,
   'native_engine_rebuilt':False,'video_recolored':False,'status':'TEST CANDIDATE'
 },indent=2)+'\n')
 print('PASS: 2103215 Smart Return moved to Experience options; Settings uses top-left drawer; locked 2103214 preserved')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);args=p.parse_args();apply(args.shell)
if __name__=='__main__':main()
