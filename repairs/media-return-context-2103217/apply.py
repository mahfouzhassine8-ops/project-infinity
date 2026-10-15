#!/usr/bin/env python3
"""2103217: preserve Movies/TV Shows parent context across See All/Genre pages.

Parent: exact locked 2103216.
This is a media-navigation return fix only. It does not change playback, providers,
native engine, Live TV, Ambient, Health, or approved Movies/TV Shows presentation.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103217
OLD_VERSION=2103216
OLD_NAME='1.0.9-Cobra-Smart-Return-Experience-Display-RC1'
NEW_NAME='1.0.9-Cobra-Media-Return-Context-RC1'
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
def replace_method(text,sig,new):
 a,b=method_range(text,sig);return text[:a]+new.rstrip()+text[b:]
def mh(text,sigs):return {sig:sha_bytes(method(text,sig).encode()) for sig in sigs}

PROTECTED=[
 'private void cobraRefreshAmbient()',
 'private void cobraRefreshLiveAmbientSurfaces(int mode,boolean live,int tint)',
 'private void cobraApplyNightCinema(View header,View footer,View pause)',
 'private void cobraReturnFromSettings()',
 'private void cobraShowVodDetails(VodItem item)',
 'private void openSeries(VodItem item)',
 'private void cobraShowVodCompletion()',
 'private void startSinglePlayer(String url)',
 'private void playChannel(Channel channel)',
 'private void cobraStartLocalTimeshift',
 'private LoadResult loadXtream(LiveSource source)',
 'private LoadResult loadM3u(LiveSource source)',
 'private void showSettings()',
]

def patch_activity(path):
 s=path.read_text();before=mh(s,PROTECTED)

 field='''  private final ArrayList<VodItem> mCobraVodShowsCatalog = new ArrayList<>();
  private VodItem mCobraCurrentVodItem;
  private VodItem mCobraActiveSeriesItem;
'''
 replacement='''  private final ArrayList<VodItem> mCobraVodShowsCatalog = new ArrayList<>();
  private VodItem mCobraCurrentVodItem;
  private VodItem mCobraActiveSeriesItem;
  // Exact in-session parent context for Movies/TV Shows drill-down pages.
  private final ArrayList<View> mCobraVodReturnViews = new ArrayList<>();
  private boolean mCobraVodReturnCaptured=false;
  private boolean mCobraVodReturnSeries=false;
  private String mCobraVodReturnStageTitle="";
  private String mCobraVodReturnHeader="";
  private String mCobraVodReturnStatus="";
  private String mCobraVodReturnInternal="";
  private View mCobraVodReturnFocus;
'''
 s=once(s,field,replacement,'VOD return fields')

 marker='  private void cobraRenderVodCollection(CobraVodCollectionState state){'
 require(s.count(marker)==1,'VOD return helper insertion point drift')
 helpers='''  private void cobraDiscardVodLandingReturn(){
    mCobraVodReturnCaptured=false;mCobraVodReturnSeries=false;mCobraVodReturnViews.clear();
    mCobraVodReturnStageTitle="";mCobraVodReturnHeader="";mCobraVodReturnStatus="";
    mCobraVodReturnInternal="";mCobraVodReturnFocus=null;
  }

  private void cobraCaptureVodLandingReturn(boolean series){
    if(mStage==null||mCobraVodReturnCaptured)return;
    String expected=series?"COBRA • TV SHOWS":"COBRA • MOVIES";
    if(!expected.equals(mCobraStageTitle))return;
    mCobraVodReturnCaptured=true;mCobraVodReturnSeries=series;
    mCobraVodReturnStageTitle=mCobraStageTitle==null?expected:mCobraStageTitle;
    mCobraVodReturnHeader=mHeader==null?"":String.valueOf(mHeader.getText());
    mCobraVodReturnStatus=mStatus==null?"":String.valueOf(mStatus.getText());
    mCobraVodReturnInternal=mCobraInternalScreen==null?"":mCobraInternalScreen;
    mCobraVodReturnFocus=getCurrentFocus();mCobraVodReturnViews.clear();
    for(int i=2;i<mStage.getChildCount();i++)mCobraVodReturnViews.add(mStage.getChildAt(i));
  }

  private boolean cobraRestoreVodLandingReturn(){
    if(!mCobraVodReturnCaptured||mStage==null)return false;
    final String title=mCobraVodReturnStageTitle,header=mCobraVodReturnHeader;
    final String statusText=mCobraVodReturnStatus,internal=mCobraVodReturnInternal;
    final ArrayList<View> saved=new ArrayList<>(mCobraVodReturnViews);
    final View focus=mCobraVodReturnFocus;
    cobraDiscardVodLandingReturn();mCobraNavigation.advance();mCobraSmartWatchlist=false;
    while(mStage.getChildCount()>2)mStage.removeViewAt(2);
    mCobraStageTitle=title;mCobraInternalScreen=internal;
    if(mHeader!=null){mHeader.setVisibility(View.VISIBLE);mHeader.setText(header);}
    if(mStatus!=null){mStatus.setVisibility(View.VISIBLE);mStatus.setText(statusText);}
    for(View child:saved){
      if(child.getParent() instanceof android.view.ViewGroup)
        ((android.view.ViewGroup)child.getParent()).removeView(child);
      mStage.addView(child);
    }
    cobraRefreshVodAmbientTrim();cobraRefreshVisualEffects();
    if(focus!=null)focus.post(()->{if(focus.isAttachedToWindow())focus.requestFocus();});
    return true;
  }

'''
 s=s.replace(marker,helpers+marker,1)

 # A newly rendered top-level media landing is the new parent and invalidates stale return state.
 rb='''  private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {
    clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");'''
 rn='''  private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {
    cobraDiscardVodLandingReturn();
    clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");'''
 s=once(s,rb,rn,'Top-level VOD return reset')

 # Every See All / genre collection entered from the landing captures the exact parent View tree.
 old='''  private void cobraShowVodCollection(String title,ArrayList<VodItem> items,boolean series){
    cobraRenderVodCollection(new CobraVodCollectionState(title,items,series));
  }'''
 new='''  private void cobraShowVodCollection(String title,ArrayList<VodItem> items,boolean series){
    cobraCaptureVodLandingReturn(series);
    cobraRenderVodCollection(new CobraVodCollectionState(title,items,series));
  }'''
 s=once(s,old,new,'Collection parent capture')

 # Smart Return must classify both the TV Shows landing and media drill-down pages as media, never Guide/Live TV.
 oldsmart='''  private String cobraSmartDestination(){
    if("health-center".equals(mCobraSheetKind))return "health";
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return "guide";
    if(mCobraSmartWatchlist)return "watchlist";
    if("COBRA • SETTINGS".equals(mCobraStageTitle))return "settings";
    if("COBRA • SOURCES".equals(mCobraStageTitle))return "sources";
    if("COBRA • MOVIES".equals(mCobraStageTitle))return "movies";
    if("COBRA • SERIES".equals(mCobraStageTitle))return "shows";'''
 newsmart='''  private String cobraSmartDestination(){
    if("health-center".equals(mCobraSheetKind))return "health";
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return "guide";
    if(mCobraSmartWatchlist)return "watchlist";
    if(mCobraVodReturnCaptured)return mCobraVodReturnSeries?"shows":"movies";
    if("COBRA • SETTINGS".equals(mCobraStageTitle))return "settings";
    if("COBRA • SOURCES".equals(mCobraStageTitle))return "sources";
    if("COBRA • MOVIES".equals(mCobraStageTitle))return "movies";
    if("COBRA • TV SHOWS".equals(mCobraStageTitle)||"COBRA • SERIES".equals(mCobraStageTitle))return "shows";'''
 s=once(s,oldsmart,newsmart,'Smart Return media classification')

 # Back from See All/Genre returns to the exact landing View objects after overlay/player handling,
 # before any Live TV/guide fallback.
 back=method(s,'public void onBackPressed()')
 marker_back='    if("grid".equals(mCobraGuideStyle)&&mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){'
 if marker_back not in back:
  marker_back='    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&"channels".equals(mCobraGuideRoute))'
 require(marker_back in back,'Back navigation insertion marker missing')
 back=back.replace(marker_back,'    if(cobraRestoreVodLandingReturn())return;\n'+marker_back,1)
 s=replace_method(s,'public void onBackPressed()',back)

 # Drawer jumps to a different top-level destination intentionally abandon the media parent.
 drawer=method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)')
 anchor='''      if(settingsDestination&&"COBRA • SETTINGS".equals(mCobraStageTitle)){cobraReturnFromSettings();return;}
      if("COBRA • SETTINGS".equals(mCobraStageTitle)&&!settingsDestination)cobraDiscardSettingsReturn();
      action.run();'''
 repl='''      if(settingsDestination&&"COBRA • SETTINGS".equals(mCobraStageTitle)){cobraReturnFromSettings();return;}
      if("COBRA • SETTINGS".equals(mCobraStageTitle)&&!settingsDestination)cobraDiscardSettingsReturn();
      if(!settingsDestination)cobraDiscardVodLandingReturn();
      action.run();'''
 require(anchor in drawer,'Drawer VOD return boundary drift')
 drawer=drawer.replace(anchor,repl,1)
 s=replace_method(s,'private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)',drawer)

 for token in ('cobraCaptureVodLandingReturn(series)','cobraRestoreVodLandingReturn()',
               'mCobraVodReturnCaptured)return mCobraVodReturnSeries?"shows":"movies"',
               '"COBRA • TV SHOWS".equals(mCobraStageTitle)',
               'if(!settingsDestination)cobraDiscardVodLandingReturn()'):
  require(token in s,'2103217 contract missing: '+token)
 settings=method(s,'private void showSettings()')
 require('cobra_smart_return_experience_display' in settings,'Smart Return Experience & Display placement lost')
 require('cobra_settings_return' not in settings,'Inline Settings Back returned')
 path.write_text(s)
 require(mh(s,PROTECTED)==before,'Protected 2103216 behavior changed')

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
         'Expected exact locked 2103216 replay')
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
 smart=shell/(SOURCE+'CobraSmartReturn.java.in')
 splash=shell/(SOURCE+'Splash.java.in')
 main=shell/(SOURCE+'Main.java.in')
 for p in (activity,smart,splash,main):require(p.is_file(),'Required 2103216 source missing: '+str(p))
 before_smart=sha(smart);before_splash=sha(splash);before_main=sha(main)
 patch_activity(activity);gradle=patch_identity(shell)
 require(sha(smart)==before_smart,'Smart Return preference engine changed')
 require(sha(splash)==before_splash,'Experience chooser/Health changed')
 require(sha(main)==before_main,'Kodi Main changed')
 require(receipt.get('native_engine_sha256')==NATIVE_SHA,'Wrong protected native engine receipt')

 for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'CobraSmartReturn.java.in',SOURCE+'Splash.java.in',SOURCE+'Main.java.in'):
  require(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE_SHA,
   media_parent_return=True,media_parent_exact_view_restore=True,media_parent_scroll_preserved=True,
   movies_see_all_back='Movies landing',shows_see_all_back='TV Shows landing',
   smart_return_collection_classification_fixed=True,smart_return_tv_shows_title_fixed=True,
   smart_return_location='Cobra Settings > Experience & Display',smart_return_default_on=True,
   settings_top_left_drawer=True,settings_inline_back_removed=True,
   locked_2103214_media_presentation_unchanged=True,live_tv_blue_ambient_unchanged=True,
   health_center_unchanged=True,playback_unchanged=True,providers_unchanged=True,video_recolored=False)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final receipt drift: '+name)

 Path('audit217').mkdir(exist_ok=True)
 Path('audit217/scope.json').write_text(json.dumps({
   'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,
   'movies_see_all_back':'exact prior Movies landing view','shows_see_all_back':'exact prior TV Shows landing view',
   'scroll_position_preserved':True,'focus_best_effort_preserved':True,
   'genre_collection_back_uses_same_parent':True,
   'smart_return_collection_classification_fixed':True,'smart_return_tv_shows_title_fixed':True,
   'smart_return_location':'Cobra Settings > Experience & Display','smart_return_default_on':True,
   'settings_top_left_drawer':True,'settings_inline_back_removed':True,
   'locked_2103214_media_presentation_unchanged':True,'live_tv_blue_ambient_unchanged':True,
   'health_center_unchanged':True,'playback_unchanged':True,'providers_unchanged':True,
   'native_engine_rebuilt':False,'video_recolored':False,'status':'TEST CANDIDATE'
 },indent=2)+'\n')
 print('PASS: 2103217 media parent return + Smart Return media classification fixed; protected systems unchanged')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);args=p.parse_args();apply(args.shell)
if __name__=='__main__':main()
