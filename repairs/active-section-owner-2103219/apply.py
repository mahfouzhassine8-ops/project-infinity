#!/usr/bin/env python3
"""2103219: Cobra active-section ownership.

Smart Return is byte-preserved and untouched.
Only explicit Cobra drawer selections change the active top-level section.
Back/deeper navigation resolves within that section instead of falling through to Live TV.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103219
OLD_VERSION=2103217
OLD_NAME='1.0.9-Cobra-Media-Return-Context-RC1'
NEW_NAME='1.0.9-Cobra-Active-Section-Owner-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def require(v,m):
 if not v:raise RuntimeError(m)
def once(s,a,b,label):
 require(s.count(a)==1,f'{label} anchor drift ({s.count(a)})');return s.replace(a,b,1)
def method_range(s,sig):
 i=s.find(sig);require(i>=0,'Missing '+sig);b=s.find('{',i);d=0
 for j in range(b,len(s)):
  if s[j]=='{':d+=1
  elif s[j]=='}':
   d-=1
   if d==0:return i,j+1
 raise RuntimeError('Unbalanced '+sig)
def method(s,sig):
 a,b=method_range(s,sig);return s[a:b]
def replace_method(s,sig,new):
 a,b=method_range(s,sig);return s[:a]+new.rstrip()+s[b:]

PROTECT=[
 'private void cobraRefreshAmbient()',
 'private void cobraApplyNightCinema(View header,View footer,View pause)',
 'private void cobraShowVodDetails(VodItem item)',
 'private void openSeries(VodItem item)',
 'private void startSinglePlayer(String url)',
 'private void playChannel(Channel channel)',
 'private void cobraStartLocalTimeshift',
 'private LoadResult loadXtream(LiveSource source)',
 'private LoadResult loadM3u(LiveSource source)',
 'private void showSettings()',
]
def hashes(s):return {x:sha_bytes(method(s,x).encode()) for x in PROTECT}

def patch_activity(path):
 s=path.read_text();before=hashes(s)

 # Explicitly separate active-section ownership from Smart Return.
 marker='  private final ArrayList<View> mCobraVodReturnViews = new ArrayList<>();\n'
 fields='''  private static final String COBRA_ACTIVE_SECTION_PREF="cobra_active_section_owner";
  private static final String COBRA_SECTION_LIVE="live";
  private static final String COBRA_SECTION_MOVIES="movies";
  private static final String COBRA_SECTION_SHOWS="shows";
  private static final String COBRA_SECTION_RECORDINGS="recordings";
  private static final String COBRA_SECTION_MY_LIST="my_list";
  private String mCobraActiveSection="";
'''+marker
 s=once(s,marker,fields,'Active section fields')

 marker2='  private void cobraDiscardVodLandingReturn(){'
 helpers='''  private String cobraNormalizeActiveSection(String value){
    if(COBRA_SECTION_MOVIES.equals(value)||COBRA_SECTION_SHOWS.equals(value)||
        COBRA_SECTION_RECORDINGS.equals(value)||COBRA_SECTION_MY_LIST.equals(value)||
        COBRA_SECTION_LIVE.equals(value))return value;
    return COBRA_SECTION_LIVE;
  }

  private String cobraActiveSection(){
    if(mCobraActiveSection==null||mCobraActiveSection.isEmpty())
      mCobraActiveSection=cobraNormalizeActiveSection(mPrefs.getString(COBRA_ACTIVE_SECTION_PREF,COBRA_SECTION_LIVE));
    return mCobraActiveSection;
  }

  private void cobraSelectActiveSection(String destination){
    String section=null;
    if("TV".equals(destination))section=COBRA_SECTION_LIVE;
    else if("MOVIES".equals(destination))section=COBRA_SECTION_MOVIES;
    else if("SHOWS".equals(destination))section=COBRA_SECTION_SHOWS;
    else if("RECORDINGS".equals(destination))section=COBRA_SECTION_RECORDINGS;
    else if("MY LIST".equals(destination))section=COBRA_SECTION_MY_LIST;
    if(section==null)return;
    mCobraActiveSection=section;
    mPrefs.edit().putString(COBRA_ACTIVE_SECTION_PREF,section).apply();
  }

  private boolean cobraReturnToActiveSection(){
    String section=cobraActiveSection();
    if(COBRA_SECTION_MOVIES.equals(section)){
      if("COBRA • MOVIES".equals(mCobraStageTitle))return true;
      showMovies();return true;
    }
    if(COBRA_SECTION_SHOWS.equals(section)){
      if("COBRA • TV SHOWS".equals(mCobraStageTitle)||"COBRA • SERIES".equals(mCobraStageTitle))return true;
      showSeries();return true;
    }
    if(COBRA_SECTION_RECORDINGS.equals(section)){
      if("COBRA • RECORDINGS".equals(mCobraStageTitle))return true;
      showRecordings();return true;
    }
    if(COBRA_SECTION_MY_LIST.equals(section)){
      if(mCobraSmartWatchlist)return true;
      showWatchlist();return true;
    }
    // Live TV is the default only when Live TV is the section the user selected.
    if(mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow())cobraOpenLiveTv();
    return true;
  }

'''
 s=once(s,marker2,helpers+marker2,'Active section helpers')

 # Only drawer navigation is allowed to change the active owner.
 drawer=method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)')
 old='''      if(!settingsDestination)cobraDiscardVodLandingReturn();
      action.run();'''
 new='''      if(!settingsDestination)cobraDiscardVodLandingReturn();
      cobraSelectActiveSection(destination);
      action.run();'''
 require(old in drawer,'Drawer active-section anchor drift')
 drawer=drawer.replace(old,new,1)
 s=replace_method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)',drawer)

 # Back gets one final section-owner guard before any legacy guide/live fallback.
 back=method(s,'public void onBackPressed()')
 marker_back='    if("grid".equals(mCobraGuideStyle)&&mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){'
 if marker_back not in back:
  marker_back='    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&"channels".equals(mCobraGuideRoute))'
 require(marker_back in back,'Back active-section marker missing')
 back=back.replace(marker_back,'''    if(!COBRA_SECTION_LIVE.equals(cobraActiveSection())){
      cobraReturnToActiveSection();return;
    }
'''+marker_back,1)
 s=replace_method(s,'public void onBackPressed()',back)

 # The 2103217 exact landing restoration remains first for See All/Genre. The active owner is the safety net.
 require(back.index('cobraRestoreVodLandingReturn()') < back.index('cobraReturnToActiveSection()'),
         'Exact media parent return must precede active-section fallback')

 # Smart Return source/method must remain semantically untouched by this pass.
 for token in ('CobraSmartReturn.enabled(mPrefs)','cobraTrySmartReturn()','cobraSaveSmartReturn()',
               'cobra_smart_return_experience_display'):
  require(token in s,'Smart Return contract lost: '+token)

 for token in ('COBRA_ACTIVE_SECTION_PREF','cobraSelectActiveSection(destination)',
               'COBRA_SECTION_MOVIES','COBRA_SECTION_SHOWS','cobraReturnToActiveSection()'):
  require(token in s,'Active-section contract missing: '+token)
 path.write_text(s)
 require(hashes(s)==before,'Protected playback/media/settings behavior changed')

def identity(shell):
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
 g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
 g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
 runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
 r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime code')
 r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime name');runtime.write_text(r)
 pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
 require(p.count(old)>=2,'packager drift');pack.write_text(p.replace(old,new));return gradle

def apply(shell):
 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
 require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103217')
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in');smart=shell/(SOURCE+'CobraSmartReturn.java.in')
 splash=shell/(SOURCE+'Splash.java.in');main=shell/(SOURCE+'Main.java.in')
 for p in (activity,smart,splash,main):require(p.is_file(),'Missing '+str(p))
 smart_before=sha(smart);splash_before=sha(splash);main_before=sha(main)
 patch_activity(activity);gradle=identity(shell)
 require(sha(smart)==smart_before,'Smart Return file changed')
 require(sha(splash)==splash_before,'Chooser/Health changed')
 require(sha(main)==main_before,'Kodi Main changed')
 require(receipt.get('native_engine_sha256')==NATIVE,'Native engine drift')
 for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'CobraSmartReturn.java.in',SOURCE+'Splash.java.in',SOURCE+'Main.java.in'):
  require(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
   cobra_active_section_owner=True,active_section_changes_only_from_drawer=True,
   active_sections=['Live TV','Movies','TV Shows','Recordings','My List'],
   movies_stays_movies=True,tv_shows_stays_tv_shows=True,live_tv_stays_live_tv=True,
   smart_return_untouched=True,smart_return_file_sha256=smart_before,
   media_return_context_preserved=True,settings_top_left_drawer=True,
   live_tv_blue_ambient_unchanged=True,health_center_unchanged=True,
   playback_unchanged=True,providers_unchanged=True,video_recolored=False)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Receipt drift '+name)
 Path('audit219').mkdir(exist_ok=True)
 Path('audit219/scope.json').write_text(json.dumps({
  'build':VERSION,'parent':OLD_VERSION,'smart_return_untouched':True,'smart_return_sha256':smart_before,
  'active_section_changes_only_from_drawer':True,
  'behavior':{
    'Movies':'deeper/back/player/settings remain Movies until drawer changes section',
    'TV Shows':'deeper/back/player/settings remain TV Shows until drawer changes section',
    'Live TV':'remains Live TV until drawer changes section',
    'Recordings':'remains Recordings until drawer changes section',
    'My List':'remains My List until drawer changes section'
  },
  'media_return_context_preserved':True,'native_engine_rebuilt':False,
  'playback_unchanged':True,'providers_unchanged':True,'health_center_unchanged':True,
  'status':'TEST CANDIDATE'
 },indent=2)+'\n')
 print('PASS: 2103219 Cobra active-section owner applied; Smart Return byte-untouched')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
