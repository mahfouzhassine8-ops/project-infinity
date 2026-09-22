#!/usr/bin/env python3
"""2103220: enforce drawer-selected Cobra active section across Android native back + lifecycle.

Parent: successful 2103219 active-section owner.
Smart Return implementation is byte-preserved and untouched.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103220
OLD_VERSION=2103219
OLD_NAME='1.0.9-Cobra-Active-Section-Owner-RC1'
NEW_NAME='1.0.9-Cobra-Active-Section-Lifecycle-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def hb(b):return hashlib.sha256(b).hexdigest()
def sha(p):return hb(Path(p).read_bytes())
def req(v,m):
 if not v:raise RuntimeError(m)
def once(s,a,b,label):
 req(s.count(a)==1,f'{label} anchor drift ({s.count(a)})');return s.replace(a,b,1)
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
 'private void cobraShowSmartReturnSetting()',
 'private boolean cobraTrySmartReturn()',
 'private void cobraSaveSmartReturn()',
]
def hashes(s):return {x:hb(method(s,x).encode()) for x in PROTECT}

def patch_activity(path):
 s=path.read_text();before=hashes(s)

 # Native back callback storage is Object so pre-Android-13 class verification stays isolated.
 field='  private String mCobraActiveSection="";\n'
 repl='''  private String mCobraActiveSection="";
  private Object mCobraNativeBackCallback;
'''
 s=once(s,field,repl,'Native back field')

 marker='  private void cobraDiscardVodLandingReturn(){'
 helpers='''  private String cobraVisibleOwnedSection(){
    if(mCobraVodReturnCaptured)return mCobraVodReturnSeries?COBRA_SECTION_SHOWS:COBRA_SECTION_MOVIES;
    if(mCobraSmartWatchlist)return COBRA_SECTION_MY_LIST;
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return COBRA_SECTION_LIVE;
    String title=mCobraStageTitle==null?"":mCobraStageTitle;
    if("COBRA • MOVIES".equals(title))return COBRA_SECTION_MOVIES;
    if("COBRA • TV SHOWS".equals(title)||"COBRA • SERIES".equals(title))return COBRA_SECTION_SHOWS;
    if("COBRA • RECORDINGS".equals(title))return COBRA_SECTION_RECORDINGS;
    if("COBRA • LIVE TV".equals(title)||"COBRA • TV GRID".equals(title))return COBRA_SECTION_LIVE;
    if(mCobraActiveSeriesItem!=null&&title.startsWith("COBRA • ")&&
        !"COBRA • SETTINGS".equals(title)&&!"COBRA • SOURCES".equals(title))return COBRA_SECTION_SHOWS;
    return "";
  }

  private void cobraRestoreActiveSectionOnEntry(){
    if(mPrefs==null||mStage==null||isFinishing()||mSources.isEmpty())return;
    if(mPlayerOverlay!=null||mMultiOverlay!=null||isCobraInPictureInPicture())return;
    cobraReturnToActiveSection();
  }

  private void cobraEnforceActiveSectionLifecycle(){
    if(mPrefs==null||mStage==null||isFinishing())return;
    if(mPlayerOverlay!=null||mMultiOverlay!=null||isCobraInPictureInPicture())return;
    String owner=cobraActiveSection(),visible=cobraVisibleOwnedSection();
    // Empty means a legitimate temporary surface (Settings/Search/Sources/etc). Do not disturb it.
    if(visible.isEmpty()||owner.equals(visible))return;
    cobraReturnToActiveSection();
  }

  private void cobraRegisterNativeBack(){
    if(Build.VERSION.SDK_INT<33||mCobraNativeBackCallback!=null)return;
    mCobraNativeBackCallback=CobraBackApi33.register(this,()->onBackPressed());
  }

  private void cobraUnregisterNativeBack(){
    if(Build.VERSION.SDK_INT<33||mCobraNativeBackCallback==null)return;
    CobraBackApi33.unregister(this,mCobraNativeBackCallback);mCobraNativeBackCallback=null;
  }

  private static final class CobraBackApi33{
    static Object register(InfinityLiveActivity activity,Runnable action){
      android.window.OnBackInvokedCallback callback=()->action.run();
      activity.getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
          android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,callback);
      return callback;
    }
    static void unregister(InfinityLiveActivity activity,Object raw){
      if(raw instanceof android.window.OnBackInvokedCallback)
        activity.getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(
            (android.window.OnBackInvokedCallback)raw);
    }
  }

'''
 s=once(s,marker,helpers+marker,'Lifecycle helpers')

 # Android native predictive/edge Back must feed the same Cobra Back owner.
 oc=method(s,'protected void onCreate(Bundle state)')
 req('buildShell();' in oc,'onCreate buildShell anchor missing')
 oc=oc.replace('    buildShell();','    buildShell();\n    cobraRegisterNativeBack();',1)
 s=replace_method(s,'protected void onCreate(Bundle state)',oc)

 od=method(s,'protected void onDestroy()')
 req('super.onDestroy();' in od,'onDestroy super anchor missing')
 od=od.replace('    super.onDestroy();','    cobraUnregisterNativeBack();\n    super.onDestroy();',1)
 s=replace_method(s,'protected void onDestroy()',od)

 # Re-entry while Activity survived: only correct an actual top-level owner mismatch.
 resume=method(s,'protected void onResume()')
 anchor='    mMain.post(()->{cobraConsumeLauncherPipReturn();cobraApplySystemBarsForSurface();});'
 req(anchor in resume,'onResume lifecycle anchor missing')
 resume=resume.replace(anchor,anchor+'\n    mMain.postDelayed(this::cobraEnforceActiveSectionLifecycle,120L);',1)
 s=replace_method(s,'protected void onResume()',resume)

 # Cold/warm library entry: preserve Smart Return call exactly, but if it declines,
 # restore drawer owner instead of old Live TV primary fallback. If Smart Return succeeds
 # to a stale top-level destination, owner enforcement corrects only that top-level mismatch.
 fallback='if(!cobraTrySmartReturn())showCobraPrimaryView();'
 count=s.count(fallback);req(count>=2,'Expected startup primary fallbacks')
 s=s.replace(fallback,'if(!cobraTrySmartReturn())cobraRestoreActiveSectionOnEntry();else mMain.post(this::cobraEnforceActiveSectionLifecycle);')

 # The active-section owner itself remains drawer-written only.
 drawer=method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)')
 req('cobraSelectActiveSection(destination);' in drawer,'Drawer owner write missing')
 req(s.count('cobraSelectActiveSection(destination);')==1,'Active owner must only be written by drawer destination')

 for token in ('CobraBackApi33','cobraRegisterNativeBack()','cobraEnforceActiveSectionLifecycle',
               'cobraRestoreActiveSectionOnEntry','cobra_active_section_owner'):
  req(token in s,'2103220 lifecycle contract missing '+token)

 path.write_text(s)
 req(hashes(s)==before,'Smart Return or protected behavior changed')

def identity(shell):
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
 g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
 g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
 runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
 r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime code')
 r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime name');runtime.write_text(r)
 pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
 req(p.count(old)>=2,'packager drift');pack.write_text(p.replace(old,new));return gradle

def apply(shell):
 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
 req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected successful 2103219 replay')
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in');smart=shell/(SOURCE+'CobraSmartReturn.java.in')
 splash=shell/(SOURCE+'Splash.java.in');main=shell/(SOURCE+'Main.java.in')
 for p in (activity,smart,splash,main):req(p.is_file(),'Missing '+str(p))
 smart_before=sha(smart);splash_before=sha(splash);main_before=sha(main)
 patch_activity(activity);gradle=identity(shell)
 req(sha(smart)==smart_before,'Smart Return file changed')
 req(sha(splash)==splash_before,'Chooser/Health changed')
 req(sha(main)==main_before,'Kodi Main changed')
 req(receipt.get('native_engine_sha256')==NATIVE,'Native engine drift')
 for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'CobraSmartReturn.java.in',SOURCE+'Splash.java.in',SOURCE+'Main.java.in'):
  req(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
   active_section_owner=True,active_section_changes_only_from_drawer=True,
   native_back_routes_through_cobra=True,android13_predictive_back_registered=True,
   cold_entry_restores_active_section=True,resume_enforces_active_section=True,
   smart_return_untouched=True,smart_return_file_sha256=smart_before,
   media_return_context_preserved=True,settings_top_left_drawer=True,
   live_tv_blue_ambient_unchanged=True,health_center_unchanged=True,
   playback_unchanged=True,providers_unchanged=True)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Receipt drift '+name)
 Path('audit220').mkdir(exist_ok=True)
 Path('audit220/scope.json').write_text(json.dumps({
  'build':VERSION,'parent':OLD_VERSION,'smart_return_untouched':True,'smart_return_sha256':smart_before,
  'only_drawer_changes_active_section':True,
  'android_native_back_routes_to_cobra_back':True,
  'cold_entry_restores_drawer_owner':True,
  'warm_resume_corrects_top_level_owner_mismatch':True,
  'temporary_surfaces_not_forcibly_closed':True,
  'acceptance':[
    'Drawer > Movies; Android edge swipe/back out; reopen Cobra => Movies',
    'Drawer > TV Shows; Android edge swipe/back out; reopen Cobra => TV Shows',
    'Drawer > Live TV => Live TV remains owner',
    'See All/Genre Back remains inside its media owner'
  ],
  'native_engine_rebuilt':False,'playback_unchanged':True,'providers_unchanged':True,
  'health_center_unchanged':True,'status':'TEST CANDIDATE'
 },indent=2)+'\n')
 print('PASS: 2103220 native-back + lifecycle active-section enforcement; Smart Return untouched')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
