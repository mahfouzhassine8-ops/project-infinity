#!/usr/bin/env python3
"""2103213: Live TV blue Ambient coverage + player/Night Cinema chrome + Settings return.

Parent: exact locked 2103212. Presentation/navigation only.
Never changes native engine, provider/playback/timeshift/PiP/background ownership or VOD library structure.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103213
OLD_VERSION=2103212
OLD_NAME='1.0.9-Cobra-Health-Media-Trim-RC1'
NEW_NAME='1.0.9-Cobra-Live-Blue-Ambient-Return-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE_SHA='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT={
 SOURCE+'InfinityLiveActivity.java.in':'18f1adf33bedeeefb856e68dda7fa8eca1edbdb86b4c7da11b43bf284dd496cf',
 SOURCE+'Splash.java.in':'7c9e8930a41da2e7c5a75fd9d18195413e1f09701d6e3dcaa196a2f848baca9c',
 SOURCE+'Main.java.in':'ddf18d30c4040369b30e861ded588a53846ff3de319a89a219344771f8db9318',
}
PROTECTED={
 'private void cobraOpenLiveTv()':'ca2104682cc43724a138310dac87361973d57a40a00a5db0e6557a3fa8f6a602',
 'private void showGuide()':'f57772610779aea49fc43c6d94db2df804e911e9c82cf224d9e5f6f96f9a93a4',
 'private void startSinglePlayer(String url)':'1c1a40c28072b5876e61ecedc5c64cfb6483b8d1c464041a16ee2b0128213708',
 'private void cobraShowQuickPeek(Channel channel,View anchor)':'bea049b1f6941709e13545eefd647915c64c2500e6b6716da2e246ab3718f869',
 'private void cobraStartLocalTimeshift':'758df5bc2d2c32df5836b13c23b33a44c35a90ef910cf3513516e4f8a3a6800a',
 'private void playChannel(Channel channel)':'48729254f6a27441b487fe8425b899ede48a804819c3d6bb466695d654087de3',
 'private void startCobraPreview(Channel channel)':'db8403d7256e8d353c9b7cef8397076ef7874646782d3972e7b3db2afa0a227c',
 'private void releaseSinglePlayer()':'1cd0ff7182a28e632f6601202c57050c87de10a923080ee64c062ced76f5b385',
 'private void releaseMulti()':'cc1a975f97fbb11dc9faa12f07e76045980e89911ed1f6cc7f0d8899886a1cad',
 'private LoadResult loadXtream(LiveSource source)':'6e9c2300e1c65095f2f8340f8764783e6852cbd8ccbc23ad238d14172e3ac2cb',
 'private LoadResult loadM3u(LiveSource source)':'ba2a26616379cd59e6b0514258e2734a19925f48627065ca33095793977d11b0',
}
VOD_METHODS=[
 'private void renderVodBrowse(ArrayList<VodItem> items, boolean series, ArrayList<String> failures)',
 'private View cobraVodHero(VodItem item, boolean series, android.widget.ViewFlipper carousel)',
 'private View cobraVodCard(VodItem item,boolean progress)',
 'private void cobraAddVodGenres(LinearLayout page,ArrayList<VodItem> items,boolean series)',
]
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(v,m):
 if not v: raise RuntimeError(m)
def once(text,old,new,label):
 require(text.count(old)==1,label+' anchor drift');return text.replace(old,new,1)
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
def contract(text):
 out={}
 for sig,expected in PROTECTED.items():
  digest=sha_bytes(method(text,sig).encode());require(digest==expected,'Protected owner drift: '+sig);out[sig]=digest
 return out
def method_hashes(text,sigs):
 return {sig:sha_bytes(method(text,sig).encode()) for sig in sigs}

def patch_activity(path):
 s=path.read_text();before=contract(s);vod_before=method_hashes(s,VOD_METHODS)

 field='  private final HashMap<View,String> mCobraVodTrimRoles=new HashMap<>();\n'
 fields='''  private final HashMap<View,String> mCobraVodTrimRoles=new HashMap<>();
  private static final int COBRA_LIVE_AMBIENT_BLUE=0xff49a9ff;
  private static final String COBRA_LIVE_AMBIENT_CONTRACT="LIVE TV AMBIENT BLUE";
  private final java.util.WeakHashMap<View,android.graphics.drawable.Drawable> mCobraAmbientSurfaceBase=new java.util.WeakHashMap<>();
  private final java.util.WeakHashMap<View,android.graphics.drawable.Drawable> mCobraAmbientSurfaceApplied=new java.util.WeakHashMap<>();
  private final ArrayList<View> mCobraSettingsReturnViews=new ArrayList<>();
  private boolean mCobraSettingsReturnCaptured=false;
  private boolean mCobraSettingsReturnGuide=false;
  private String mCobraSettingsReturnTitle="";
  private String mCobraSettingsReturnHeader="";
  private String mCobraSettingsReturnStatus="";
  private String mCobraSettingsReturnInternal="";
  private String mCobraSettingsReturnGuideRoute="";
  private String mCobraSettingsReturnGuideStyle="";
'''
 s=once(s,field,fields,'2103213 fields')

 ambient_helpers='''  private boolean cobraLiveAmbientContext(){
    if(mCobraStageTitle!=null&&
        (mCobraStageTitle.contains("MOVIES")||mCobraStageTitle.contains("TV SHOWS")))return false;
    if(mPlayerOverlay!=null&&mPlayingVodKey!=null&&mPlayingVodKey.isEmpty())return true;
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return true;
    return false;
  }

  private View cobraCurrentSheetPanel(){
    if(!(mCobraActionSheet instanceof android.view.ViewGroup))return null;
    android.view.ViewGroup group=(android.view.ViewGroup)mCobraActionSheet;
    return group.getChildCount()>0?group.getChildAt(0):null;
  }

  private void cobraAmbientSurface(View view,int tint,int mode,int radius,boolean night){
    if(view==null)return;
    android.graphics.drawable.Drawable current=view.getBackground();
    android.graphics.drawable.Drawable applied=mCobraAmbientSurfaceApplied.get(view);
    if(applied!=null&&current!=applied){
      mCobraAmbientSurfaceBase.put(view,current);mCobraAmbientSurfaceApplied.remove(view);applied=null;
    }
    if(!mCobraAmbientSurfaceBase.containsKey(view))mCobraAmbientSurfaceBase.put(view,current);
    if(mode==CobraPresentationEffects.OFF&&!night){
      if(applied!=null&&view.getBackground()==applied)view.setBackground(mCobraAmbientSurfaceBase.get(view));
      mCobraAmbientSurfaceApplied.remove(view);mCobraAmbientSurfaceBase.remove(view);return;
    }
    android.graphics.drawable.Drawable base=mCobraAmbientSurfaceBase.get(view);
    if(base==null)base=new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT);
    int edgeAlpha=night?230:(mode==CobraPresentationEffects.IMMERSIVE?245:150);
    int washAlpha=night?218:(mode==CobraPresentationEffects.IMMERSIVE?30:13);
    int edge=Color.argb(edgeAlpha,Color.red(tint),Color.green(tint),Color.blue(tint));
    int wash=night?Color.argb(washAlpha,0,0,0):
        Color.argb(washAlpha,Color.red(tint),Color.green(tint),Color.blue(tint));
    android.graphics.drawable.GradientDrawable glow=new android.graphics.drawable.GradientDrawable(
        android.graphics.drawable.GradientDrawable.Orientation.TL_BR,
        new int[]{wash,Color.TRANSPARENT,Color.TRANSPARENT});
    glow.setCornerRadius(dp(radius));
    android.graphics.drawable.GradientDrawable rim=new android.graphics.drawable.GradientDrawable();
    rim.setColor(Color.TRANSPARENT);rim.setCornerRadius(dp(radius));
    rim.setStroke(Math.max(1,dp(mode==CobraPresentationEffects.IMMERSIVE||night?2:1)),edge);
    android.graphics.drawable.LayerDrawable layer=new android.graphics.drawable.LayerDrawable(
        new android.graphics.drawable.Drawable[]{base,glow,rim});
    if(Build.VERSION.SDK_INT>=23)layer.setPaddingMode(android.graphics.drawable.LayerDrawable.PADDING_MODE_STACK);
    view.setBackground(layer);mCobraAmbientSurfaceApplied.put(view,layer);
  }

  private void cobraRefreshLiveAmbientSurfaces(int mode,boolean live,int tint){
    boolean night=cobraNightCinemaActive();
    int surfaceMode=live?mode:CobraPresentationEffects.OFF;
    cobraAmbientSurface(mCobraGuideShell,COBRA_LIVE_AMBIENT_BLUE,surfaceMode,3,false);
    cobraAmbientSurface(mCobraModeRail,COBRA_LIVE_AMBIENT_BLUE,surfaceMode,16,false);
    cobraAmbientSurface(mCobraModeToolbar,COBRA_LIVE_AMBIENT_BLUE,surfaceMode,16,false);
    cobraAmbientSurface(mCobraGuideDirectory,COBRA_LIVE_AMBIENT_BLUE,surfaceMode,12,false);
    cobraAmbientSurface(mCobraGuideDetails,COBRA_LIVE_AMBIENT_BLUE,surfaceMode,16,false);
    int playerTint=live?COBRA_LIVE_AMBIENT_BLUE:tint;
    int raw=CobraPresentationEffects.ambientMode(mPrefs);
    cobraAmbientSurface(mCobraPlayerDrawer,playerTint,night?CobraPresentationEffects.OFF:raw,20,night);
    cobraAmbientSurface(cobraCurrentSheetPanel(),playerTint,night?CobraPresentationEffects.OFF:raw,22,night);
    for(View view:new View[]{mCobraModeRail,mCobraModeToolbar,mCobraGuideDirectory,mCobraGuideDetails}){
      if(view!=null)view.invalidate();
    }
  }

'''
 marker='  private void cobraRefreshAmbient(){'
 require(s.count(marker)==1,'Ambient helper insertion drift')
 s=s.replace(marker,ambient_helpers+marker,1)

 refresh='''  private void cobraRefreshAmbient(){
    if(mCobraEffects==null)return;
    int mode=cobraAmbientMode();
    boolean live=cobraLiveAmbientContext();
    Channel context=mCobraInspectedChannel!=null?mCobraInspectedChannel:mPlaying!=null?mPlaying:mGuidePreviewChannel;
    String key=(live?"@live-blue:":("@content:"))+(context==null?"":context.id);
    if(!key.equals(mCobraAmbientContext)){
      mCobraAmbientContext=key;
      mCobraAmbientTint=live?COBRA_LIVE_AMBIENT_BLUE:
          context==null?0xff62aaff:CobraPresentationEffects.contextTint(mFeatures.sourceColor(sourceIdForChannel(context)));
    }
    mCobraEffects.backdrop(mCobraBrowseBackground,cobraThemeColor("background",mTheme.background),mCobraAmbientTint,mode);
    mCobraEffects.backdrop(mCobraGuideShell,cobraModeColor("background"),live?COBRA_LIVE_AMBIENT_BLUE:mCobraAmbientTint,mode);
    cobraRefreshVodAmbientTrim();
    cobraRefreshLiveAmbientSurfaces(mode,live,mCobraAmbientTint);
  }'''
 s=replace_method(s,'  private void cobraRefreshAmbient()',refresh)

 player='''  private void cobraApplyNightCinema(View header,View footer,View pause){
    if(header==null||footer==null)return;
    boolean night=cobraNightCinemaActive();
    int raw=CobraPresentationEffects.ambientMode(mPrefs);
    int tint=(mPlayingVodKey==null||mPlayingVodKey.isEmpty())?COBRA_LIVE_AMBIENT_BLUE:mCobraAmbientTint;
    if(night){
      int blue=COBRA_LIVE_AMBIENT_BLUE;
      header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{
          Color.argb(58,Color.red(blue),Color.green(blue),Color.blue(blue)),0xff000000,0xb8000000,Color.TRANSPARENT}));
      footer.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{
          Color.TRANSPARENT,0xe3000000,0xff000000,Color.argb(48,Color.red(blue),Color.green(blue),Color.blue(blue))}));
      if(pause!=null)pause.setBackground(surface(0xd9000000,14,blue,2));
      if(mCobraPlayerSchedule!=null)mCobraPlayerSchedule.setVisibility(View.GONE);
      if(mCobraPlayerUpcoming!=null)mCobraPlayerUpcoming.setVisibility(View.GONE);
      return;
    }
    if(raw==CobraPresentationEffects.OFF||!cobraVisualEffectsAllowed())return;
    int alpha=raw==CobraPresentationEffects.IMMERSIVE?78:36;
    int edge=raw==CobraPresentationEffects.IMMERSIVE?190:105;
    int tintTop=Color.argb(alpha,Color.red(tint),Color.green(tint),Color.blue(tint));
    int tintEdge=Color.argb(edge,Color.red(tint),Color.green(tint),Color.blue(tint));
    header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{
        tintTop,0x98000000,0x48000000,Color.TRANSPARENT}));
    footer.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{
        Color.TRANSPARENT,0x9c000000,0xe0000000,tintTop}));
    if(pause!=null)pause.setBackground(surface(0x9a000000,14,tintEdge,raw==CobraPresentationEffects.IMMERSIVE?2:1));
  }'''
 s=replace_method(s,'  private void cobraApplyNightCinema(View header,View footer,View pause)',player)

 # Make mode changes immediately repaint the guide, not just the hidden palette.
 old='''      mPrefs.edit().putString(CobraPresentationEffects.AMBIENT,value).apply();mCobraAmbientContext="@refresh";cobraRefreshVisualEffects();cobraRefreshModeDetails();
    });}'''
 new='''      mPrefs.edit().putString(CobraPresentationEffects.AMBIENT,value).apply();mCobraAmbientContext="@refresh";cobraRefreshVisualEffects();
      if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){cobraRestyleGuide();cobraRenderGuideBrowser();}
      cobraRefreshModeDetails();
    });}'''
 s=once(s,old,new,'Visual menu ambient repaint')

 # Refresh ambient decoration after player drawer/sheet creation.
 s=once(s,'mPlayerOverlay.addView(panel,new FrameLayout.LayoutParams(1,1));mPlayerChrome.setVisibility(View.GONE);cobraRenderPlayerDrawer(mCobraDrawerFilter);cobraLayoutPlayerPanels();panel.post(()->{if(panel==mCobraPlayerDrawer&&panel.isAttachedToWindow())cobraAnimatePanelIn(panel,!isPortrait());});vtheme().tree(content,"player.channels");',
        'mPlayerOverlay.addView(panel,new FrameLayout.LayoutParams(1,1));mPlayerChrome.setVisibility(View.GONE);cobraRenderPlayerDrawer(mCobraDrawerFilter);cobraLayoutPlayerPanels();panel.post(()->{if(panel==mCobraPlayerDrawer&&panel.isAttachedToWindow())cobraAnimatePanelIn(panel,!isPortrait());});vtheme().tree(content,"player.channels");cobraRefreshVisualEffects();',
        'Player drawer ambient refresh')
 s=once(s,'pos.setMargins(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.14",12)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.15",12)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.16",12)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.17",22)));scrim.addView(panel,pos);parent.addView(scrim,new FrameLayout.LayoutParams(-1,-1));',
        'pos.setMargins(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.14",12)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.15",12)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.16",12)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.17",22)));scrim.addView(panel,pos);parent.addView(scrim,new FrameLayout.LayoutParams(-1,-1));cobraRefreshVisualEffects();',
        'Action sheet ambient refresh')

 settings_helpers='''  private void cobraCaptureSettingsReturn(){
    if(mCobraSettingsReturnCaptured)return;
    mCobraSettingsReturnCaptured=true;
    mCobraSettingsReturnGuide=mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow();
    mCobraSettingsReturnTitle=mCobraStageTitle==null?"":mCobraStageTitle;
    mCobraSettingsReturnHeader=mHeader==null?"":String.valueOf(mHeader.getText());
    mCobraSettingsReturnStatus=mStatus==null?"":String.valueOf(mStatus.getText());
    mCobraSettingsReturnInternal=mCobraInternalScreen==null?"":mCobraInternalScreen;
    mCobraSettingsReturnGuideRoute=mCobraGuideRoute==null?"":mCobraGuideRoute;
    mCobraSettingsReturnGuideStyle=mCobraGuideStyle==null?"":mCobraGuideStyle;
    mCobraSettingsReturnViews.clear();
    if(!mCobraSettingsReturnGuide&&mStage!=null){
      while(mStage.getChildCount()>2){
        View child=mStage.getChildAt(2);mStage.removeViewAt(2);mCobraSettingsReturnViews.add(child);
      }
    }
  }

  private void cobraDiscardSettingsReturn(){
    mCobraSettingsReturnCaptured=false;mCobraSettingsReturnGuide=false;mCobraSettingsReturnViews.clear();
    mCobraSettingsReturnTitle="";mCobraSettingsReturnHeader="";mCobraSettingsReturnStatus="";
    mCobraSettingsReturnInternal="";mCobraSettingsReturnGuideRoute="";mCobraSettingsReturnGuideStyle="";
  }

  private void cobraReturnFromSettings(){
    if(!mCobraSettingsReturnCaptured){showCobraPrimaryView();return;}
    final boolean guide=mCobraSettingsReturnGuide;
    final String title=mCobraSettingsReturnTitle;
    final String header=mCobraSettingsReturnHeader,statusText=mCobraSettingsReturnStatus;
    final String internal=mCobraSettingsReturnInternal,route=mCobraSettingsReturnGuideRoute,style=mCobraSettingsReturnGuideStyle;
    final ArrayList<View> saved=new ArrayList<>(mCobraSettingsReturnViews);
    cobraDiscardSettingsReturn();mCobraNavigation.advance();
    if(guide){
      if(!style.isEmpty())mCobraGuideStyle=style;if(!route.isEmpty())mCobraGuideRoute=route;
      cobraShowGuideShell();cobraLayoutGuide();cobraRenderGuideBrowser();cobraRefreshVisualEffects();return;
    }
    if(!saved.isEmpty()&&mStage!=null){
      while(mStage.getChildCount()>2)mStage.removeViewAt(2);
      mCobraStageTitle=title;mCobraInternalScreen=internal;
      if(mHeader!=null){mHeader.setVisibility(View.VISIBLE);mHeader.setText(header);}
      if(mStatus!=null){mStatus.setVisibility(View.VISIBLE);mStatus.setText(statusText);}
      for(View child:saved){
        if(child.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)child.getParent()).removeView(child);
        mStage.addView(child);
      }
      cobraRefreshVisualEffects();return;
    }
    String upper=title==null?"":title.toUpperCase(Locale.US);
    if(upper.contains("MOVIES")){showMovies();return;}
    if(upper.contains("SHOWS")){showSeries();return;}
    if(upper.contains("RECORDINGS")){showRecordings();return;}
    if(upper.contains("MY LIST")){showWatchlist();return;}
    if(upper.contains("SEARCH")){showSearch();return;}
    showCobraPrimaryView();
  }

'''
 marker='  private void showSettings() {'
 require(s.count(marker)==1,'Settings helper insertion drift')
 s=s.replace(marker,settings_helpers+marker,1)

 # Capture previous screen before Settings destroys/replaces the stage.
 s=once(s,'  private void showSettings() {\n    mCobraInternalScreen = "internal";',
        '  private void showSettings() {\n    cobraCaptureSettingsReturn();\n    mCobraInternalScreen = "internal";',
        'Settings return capture')
 # Explicit back control at top of Settings.
 anchor='''    LinearLayout list = new LinearLayout(this);
    list.setOrientation(LinearLayout.VERTICAL);
    list.setPadding(0, dp(vtheme().dimension("cobra.showSettings.dimensions.1",4)), 0, dp(vtheme().dimension("cobra.showSettings.dimensions.2",12)));
'''
 repl=anchor+'''    Button settingsBack=action("‹  BACK");
    settingsBack.setTag("cobra_settings_return");
    settingsBack.setContentDescription("Return to previous Cobra screen");
    settingsBack.setOnClickListener(v->cobraReturnFromSettings());
'''
 s=once(s,anchor,repl,'Settings back control')
 s=once(s,'    list.addView(chooser, new LinearLayout.LayoutParams(-1, dp(56)));',
        '    list.addView(settingsBack, new LinearLayout.LayoutParams(-1, dp(52)));\n    list.addView(chooser, new LinearLayout.LayoutParams(-1, dp(56)));',
        'Settings back placement')

 # Do not erase the prior destination before Settings captures it.
 s=once(s,'cobraDrawerDestination(items,"settings","Settings","SETTINGS",()->{stopCobraPreview();mCobraInternalScreen="internal";showSettings();});',
        'cobraDrawerDestination(items,"settings","Settings","SETTINGS",()->{stopCobraPreview();showSettings();});',
        'Settings drawer capture ownership')

 drawer='''  private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action){
    if(!mUi.destinationEnabled(destination))return;
    label=vtheme().copy("drawer.label."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"),label);
    final boolean settingsDestination="SETTINGS".equalsIgnoreCase(destination);
    LinearLayout row=cobraDetailRow(icon,label,null,"cobra-destination:"+destination,false,()->{
      closeCobraExperienceDrawer();
      if(settingsDestination&&"COBRA • SETTINGS".equals(mCobraStageTitle)){cobraReturnFromSettings();return;}
      if("COBRA • SETTINGS".equals(mCobraStageTitle)&&!settingsDestination)cobraDiscardSettingsReturn();
      action.run();
    });
    if(row.getChildCount()>0)row.getChildAt(0).setTag("cobra-drawer-icon:"+destination);
    cobraPolishDrawerRow(parent,row);
    vtheme().tree(row,"drawer.item."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"));
  }'''
 s=replace_method(s,'  private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)',drawer)

 for token in ('LIVE TV AMBIENT BLUE','COBRA_LIVE_AMBIENT_BLUE','cobraReturnFromSettings()',
               '"cobra_settings_return"','cobraRefreshLiveAmbientSurfaces','cobraAmbientSurface('):
  require(token in s,'2103213 contract missing: '+token)

 require(method_hashes(s,VOD_METHODS)==vod_before,'Movies/TV Shows locked implementation changed')
 path.write_text(s)
 require(contract(s)==before,'Playback/provider/Live TV owner methods changed')

def patch_identity(shell):
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
 g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','Gradle version')
 g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','Gradle name');gradle.write_text(g)
 runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
 r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','Runtime version')
 r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'Runtime name');runtime.write_text(r)
 pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
 require(p.count(old)>=2,'Packager identity drift');pack.write_text(p.replace(old,new))
 return gradle

def apply(shell):
 for name,digest in PARENT.items():require(sha(shell/name)==digest,'Not exact locked 2103212 parent: '+name)
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in');patch_activity(activity)
 # Health Center and Main are byte-protected by this pass.
 require(sha(shell/(SOURCE+'Splash.java.in'))==PARENT[SOURCE+'Splash.java.in'],'Infinity Health changed')
 require(sha(shell/(SOURCE+'Main.java.in'))==PARENT[SOURCE+'Main.java.in'],'Kodi Main changed')
 gradle=patch_identity(shell)

 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
 require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Wrong 2103212 receipt')
 for name in PARENT:
  require(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE_SHA,
   presentation_navigation_only=True,live_tv_ambient_blue=True,
   live_tv_ambient_coverage=['guide','rail','toolbar','details','player drawer','visual/settings sheets','player chrome'],
   movie_tv_library_unchanged=True,night_cinema_player_chrome_expanded=True,
   settings_returns_to_previous=True,settings_fallback='Cobra primary Live TV',
   health_center_unchanged=True,video_recolored=False)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final receipt drift: '+name)

 Path('audit213').mkdir(exist_ok=True)
 Path('audit213/scope.json').write_text(json.dumps({
   'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,
   'changed_java_files':[SOURCE+'InfinityLiveActivity.java.in'],
   'health_center_unchanged':True,'main_unchanged':True,'native_engine_rebuilt':False,
   'live_tv_blue':True,'live_tv_blue_hex':'#49A9FF',
   'ambient_off':'original surfaces restored','ambient_subtle':'blue edge + restrained wash',
   'ambient_immersive':'strong blue edge + atmospheric wash',
   'player_drawer_ambient':True,'player_chrome_ambient':True,'night_cinema_player_chrome':True,
   'settings_return_previous':True,'settings_return_fallback':'Cobra primary Live TV',
   'movie_tv_library_unchanged':True,'video_recolored':False,
   'protected_methods':contract(activity.read_text()),
 },indent=2)+'\n')
 print('PASS: 2103213 blue Live TV ambient + player/night chrome + Settings return; locked media/native/health preserved')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);args=p.parse_args();apply(args.shell)
if __name__=='__main__':main()
