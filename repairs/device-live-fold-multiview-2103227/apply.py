#!/usr/bin/env python3
"""2103227: device-audited Live Ended + Fold Fit + Multi-View correction.

Parent source: exact audited 2103226 replay over locked 2103225.

Authorized delta:
- Live TV: recover an unexpected ExoPlayer STATE_ENDED without showing a stale "Ended"
  badge or entering an unbounded restart loop. VOD completion behavior is excluded.
- Fold Fit: supersede the device-rejected whole-frame mode-12 geometry with a balanced,
  proportional fit that materially reduces oversized black bands. Fold Fill remains the
  full-pane minimum-center-crop choice.
- Multi-View: preserve existing controls and add only missing per-screen controls:
  Search and add, Pause/Resume, Enlarge/Restore grid, reversible Full screen.
- Full screen from Multi-View must preserve every tile/player and return to the same
  Multi-View session with Back or the player Multi-View action.

No native rebuild. No provider, VOD, movie/show detail, Smart Return, chooser, Health
Center, skin, recording, or unrelated navigation redesign.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103227
OLD_VERSION=2103226
OLD_NAME='1.0.9-Cobra-Fold-Fit-Fill-Audited-RC1'
NEW_NAME='1.0.9-Cobra-Device-Live-Fold-MultiView-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
ACT=SOURCE+'InfinityLiveActivity.java.in'
PARENT_ACTIVITY='f02e1aa2550e56e0222fafaa3e8b74bf5ee8585353535891e60da709e1d3cdd0'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PREAUDIT_RUN=35805468435

def hb(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    c=s.count(a); req(c==1,f'{label}: expected one anchor, got {c}'); return s.replace(a,b,1)

def span(text,name,kind='method'):
    if kind=='method':
        pat=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:
        pat=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    ms=list(pat.finditer(text)); req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    st=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=com=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif com:
            if c=='*' and n=='/':com=False;i+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':com=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return st,i+1
        i+=1
    raise RuntimeError('unclosed '+name)

def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+text[b:]
def hashes(text,names,kind='method'):
    return {n:hb(member(text,n,kind)) for n in names}

PROTECTED_METHODS=[
  'buildPlayer','startSinglePlayer','cobraStartDirectSinglePlayer','cobraStartLocalTimeshift',
  'cobraRecoverLocalTimeshiftSource','cobraFallbackFromLocalTimeshift','cobraRewindLive','cobraGoLive',
  'playVodUrl','openSeries','cobraRenderMovieDetailPage','cobraRenderSeriesDetailPage',
  'loadXtream','loadM3u','multiToSingle','openMultiView','rebuildCobraMultiPreservingSessions',
  'cobraSyncMultiArrays','setMultiAudio','selectCobraMultiChannel','removeCobraMultiTileClean',
  'cobraAttachVideo','cobraDisposePlayer','cobraRetryMultiTile','applyCobraAspectTransform',
  'cobraBindingAspect','cobraChannelAspect','showSettings'
]
PROTECTED_CLASSES=['CobraLayoutMath','CobraTimelineNormalizerPolicy','CobraProviderPacePolicy','CobraTimeshiftTransportPolicy']

FOLD_POLICY=r'''  static final class CobraFoldAspectPolicy {
    static final int MODE=12;
    static final int FIT_MODE=MODE;
    static final int FILL_MODE=13;
    static final int MAX_MODE=FILL_MODE;
    static final float SMART_TARGET=.78f;

    static boolean foldMode(int mode){return mode==FIT_MODE||mode==FILL_MODE;}

    static float[] contain(int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      if(videoWidth<=0||videoHeight<=0||viewportWidth<=0||viewportHeight<=0)return new float[]{1f,1f};
      float source=videoWidth*(pixelRatio>0?pixelRatio:1f)/videoHeight;
      float view=(float)viewportWidth/viewportHeight;
      float sx=source<view?source/view:1f,sy=source>view?view/source:1f;
      return new float[]{sx,sy};
    }

    // Device-audited Fold Fit: preserve proportions, but reduce the giant black
    // bands produced by strict whole-frame containment on the Fold inner display.
    // Fold Fill remains the stronger no-bars choice.
    static float[] fit(int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      float[] base=contain(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight);
      if(videoWidth<=0||videoHeight<=0||viewportWidth<=0||viewportHeight<=0)return base;
      float smaller=Math.min(base[0],base[1]);
      if(smaller>=SMART_TARGET)return base;
      float view=(float)viewportWidth/viewportHeight;
      float fillZoom=Math.max(1f/base[0],1f/base[1]);
      float cap=(view>=.65f&&view<=1.35f)?1.70f:2.40f;
      float smart=Math.max(1f,SMART_TARGET/Math.max(.0001f,smaller));
      float zoom=Math.min(fillZoom,Math.min(cap,smart));
      return new float[]{base[0]*zoom,base[1]*zoom};
    }

    static float[] fill(int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      float[] base=contain(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight);
      if(videoWidth<=0||videoHeight<=0||viewportWidth<=0||viewportHeight<=0)return base;
      float zoom=Math.max(1f/base[0],1f/base[1]);
      return new float[]{base[0]*zoom,base[1]*zoom};
    }

    // Saved mode 12 remains valid; only its presentation geometry is superseded.
    static float[] scale(int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      return fit(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight);
    }

    static float[] scaleForMode(int mode,int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      return mode==FILL_MODE?fill(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight)
          :fit(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight);
    }
  }'''

LIVE_HELPERS=r'''  static final class CobraLiveEndedPolicy {
    static final int MAX_RECOVERIES=2;
    static boolean eligible(boolean live,boolean vod,boolean requested,int state){
      return live&&!vod&&requested&&state==Player.STATE_ENDED;
    }
  }

  private void cobraRecoverUnexpectedLiveEnded(final CobraPlayerBinding binding){
    if(binding==null||!binding.current()
        ||!CobraLiveEndedPolicy.eligible(binding.vitals.live,!mPlayingVodKey.isEmpty(),
            binding.player.getPlayWhenReady(),binding.player.getPlaybackState()))return;
    final ExoPlayer ended=binding.player;final Channel channel=binding.channel;
    boolean fullscreen=ended==mPlayer&&mPlaying!=null&&channel!=null&&channel.id.equals(mPlaying.id);
    boolean multi=cobraMultiViewPlayer(ended)&&channel!=null&&mCobraTiles.get(channel.id)!=null;
    if((!fullscreen&&!multi)||binding.liveEndedRecovering)return;

    binding.liveEndedRecovering=true;
    binding.liveEndedRecoveryAt=android.os.SystemClock.elapsedRealtime();
    mMain.postDelayed(()->{
      if(!binding.current()||ended.getPlaybackState()!=Player.STATE_ENDED||!ended.getPlayWhenReady()){
        binding.liveEndedRecovering=false;return;
      }

      // Existing local-timeshift ownership decides its own safe fallback.
      if(ended==mCobraTimeshiftPlayer||ended==mCobraTimeshiftProxyPlayer){
        binding.liveEndedRecoveries++;binding.liveEndedRecovering=false;
        cobraFallbackFromLocalTimeshift(ended,channel,"unexpected-live-ended");return;
      }

      // No unbounded restart loop: at most two same-session recovery attempts.
      if(binding.liveEndedRecoveries>=CobraLiveEndedPolicy.MAX_RECOVERIES){
        binding.liveEndedRecovering=false;binding.error="LIVE_ENDED";
        cobraUpdatePlaybackLabels();return;
      }

      boolean useFallback=binding.liveEndedRecoveries>0&&!binding.fallback
          &&!"primary".equals(binding.vitals.preferences.fallback)
          &&channel!=null&&!channel.fallbackUrl.isEmpty()
          &&!channel.fallbackUrl.equals(channel.primaryUrl);
      binding.liveEndedRecoveries++;
      try{
        if(useFallback){binding.fallback=true;ended.setMediaItem(mediaItem(channel.fallbackUrl));}
        else ended.seekToDefaultPosition();
        ended.prepare();startCobraPlayer(ended);
        InfinityCobraDiagnostics.record(this,"playback","live-ended-recovery",
            useFallback?"fallback":"same-player-reprepare");
        final int recovery=binding.liveEndedRecoveries;
        mMain.postDelayed(()->{
          if(binding.current()&&binding.liveEndedRecoveries==recovery
              &&ended.getPlaybackState()==Player.STATE_READY&&ended.getPlayWhenReady())
            binding.liveEndedRecoveries=0;
        },30000L);
      }catch(RuntimeException failure){
        binding.liveEndedRecovering=false;binding.error="LIVE_ENDED";
        InfinityCobraDiagnostics.failure(this,"live-ended-recovery",failure);
        cobraUpdatePlaybackLabels();
      }
    },420L);
  }

'''

MULTI_HELPERS=r'''  static final class CobraMultiLayoutPolicy {
    static int[] rect(int index,int count,int width,int height,int enlarged){
      if(enlarged<0||enlarged>=count||count<2)return CobraLayoutMath.tile(index,count,width,height);
      float largeFraction=height>=width?.62f:.70f;
      int largeH=Math.max(1,Math.min(height-1,Math.round(height*largeFraction)));
      if(index==enlarged)return new int[]{0,0,width,largeH};
      int rank=index<enlarged?index:index-1,smallCount=count-1,stripH=height-largeH;
      if(smallCount==1){
        int sw=Math.max(1,Math.round(width*(height>=width?.72f:.48f)));
        return new int[]{(width-sw)/2,largeH,sw,stripH};
      }
      int x=width*rank/smallCount,right=width*(rank+1)/smallCount;
      return new int[]{x,largeH,right-x,stripH};
    }
  }

  private void cobraToggleMultiTilePause(String key){
    CobraVideoTile tile=mCobraTiles.get(key);if(tile==null||tile.player==null)return;
    if(tile.player.getPlayWhenReady()){
      tile.player.pause();if(cobraMultiIndex(key)==mAudioTile)cobraReleaseAudioFocus(tile.player);
    }else cobraUserPlay(tile.player);
    cobraUpdatePlaybackLabels();int i=cobraMultiIndex(key);if(i>=0)showCobraMultiTileActions(i);
  }

  private void cobraToggleMultiEnlarge(String key){
    if(key==null||mCobraTiles.get(key)==null)return;
    mCobraMultiEnlargedKey=key.equals(mCobraMultiEnlargedKey)?"":key;
    closeCobraActionSheet();cobraLayoutMultiTiles();showMultiChromeTemporarily();
  }

  private void cobraShowMultiSearchAdd(){
    if(mCobraTiles.keys().size()>=4){toast("Multi-View already has 4 screens");return;}
    mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);
    if(mCobraMultiPicker==null)return;
    View raw=mCobraMultiPicker.findViewWithTag("cobra_multi_search");
    if(raw instanceof EditText){
      EditText input=(EditText)raw;input.requestFocus();
      input.post(()->((android.view.inputmethod.InputMethodManager)getSystemService(INPUT_METHOD_SERVICE))
          .showSoftInput(input,android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT));
    }
  }

  private void renderCobraMultiPickerSearch(String query){
    if(mCobraMultiPicker==null)return;
    View view=mCobraMultiPicker.findViewWithTag("cobra_multi_picker_list");
    if(!(view instanceof android.widget.ListView))return;
    final String needle=query==null?"":query.trim().toLowerCase(Locale.ROOT);
    if(needle.isEmpty()){renderCobraMultiPicker("RECENT");return;}
    final ArrayList<Channel> channels=new ArrayList<>();
    for(Channel c:mChannels){
      String name=c.name==null?"":c.name.toLowerCase(Locale.ROOT);
      String group=c.group==null?"":c.group.toLowerCase(Locale.ROOT);
      if(cobraChannelAllowed(c)&&mCobraTiles.get(c.id)==null
          &&(name.contains(needle)||group.contains(needle)))channels.add(c);
    }
    android.widget.ListView list=(android.widget.ListView)view;
    list.setAdapter(new android.widget.BaseAdapter(){
      public int getCount(){return channels.size();}
      public Channel getItem(int p){return channels.get(p);}
      public long getItemId(int p){return p;}
      public View getView(int p,View old,android.view.ViewGroup host){
        Channel c=channels.get(p);
        Button row=old instanceof Button?(Button)old:cobraTextButton("",true,()->{});
        GuideProgram current=cobraCurrentProgram(c);
        row.setText(c.name+"\n"+(current==null?cobraGuideStatus(c):current.title));
        row.setTextColor(Color.WHITE);row.setTextSize(13);
        row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
        row.setPadding(dp(12),0,dp(12),0);row.setMaxLines(2);
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(64)));
        row.setOnClickListener(v->selectCobraMultiChannel(c));return row;
      }
    });
  }

  private void cobraPromoteMultiTileFullscreen(String key){
    if(mCobraMultiFullscreenActive||key==null)return;
    int index=cobraMultiIndex(key);CobraVideoTile tile=mCobraTiles.get(key);
    if(index<0||tile==null||tile.player==null||mMultiOverlay==null)return;
    closeCobraActionSheet();closeCobraMultiPicker(true);setMultiAudio(index);
    mCobraMultiFullscreenActive=true;mCobraMultiFullscreenKey=key;
    mPlaying=tile.channel;mPlayingIndex=mChannels.indexOf(tile.channel);
    mPlayingVodKey="";mPendingResumeMs=0L;
    openPlayerOverlay(tile.channel);mPlayer=tile.player;
    cobraAttachVideo(mPlayer,mPlayerTexture);mPlayer.setVolume(1f);cobraClaimAudioFocus(mPlayer);
    mMultiOverlay.setVisibility(View.GONE);
    configureCobraPip(true);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("multiview-fullscreen");
  }

  private boolean cobraReturnToMultiFromFullscreen(){
    if(!mCobraMultiFullscreenActive)return false;
    String key=mCobraMultiFullscreenKey;CobraVideoTile tile=mCobraTiles.get(key);ExoPlayer session=mPlayer;
    if(tile==null||session==null||tile.player!=session||mMultiOverlay==null){
      mCobraMultiFullscreenActive=false;mCobraMultiFullscreenKey="";return false;
    }
    closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(true);
    clearCobraPlayerLockState(false);
    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"multiview-return");
    mMain.removeCallbacks(mHideChrome);mMain.removeCallbacks(mStallWatchdog);
    FrameLayout overlay=mPlayerOverlay;cobraResetMotion(mPlayerChrome);

    // Important: relinquish fullscreen ownership without releasing the ExoPlayer.
    mCobraMultiFullscreenActive=false;mCobraMultiFullscreenKey="";
    mPlayer=null;mPlayerOverlay=null;mPlayerTexture=null;mPlayerChrome=null;
    mCobraPlayerRotationButton=null;mCobraLiveRewindButton=null;mCobraGoLiveButton=null;
    mCobraPlayerProgram=null;mCobraPlayerSchedule=null;mCobraPlayerUpcoming=null;
    mCobraPlayerProgramProgress=null;mPlaying=null;mPlayingIndex=-1;
    mPlayingVodKey="";mPlayingVodTitle="";mPendingResumeMs=0L;

    cobraAttachVideo(session,tile.texture);
    if(overlay!=null&&overlay.getParent() instanceof android.view.ViewGroup)
      ((android.view.ViewGroup)overlay.getParent()).removeView(overlay);
    mMultiOverlay.setVisibility(View.VISIBLE);
    int index=cobraMultiIndex(key);if(index>=0)setMultiAudio(index);
    cobraLayoutMultiTiles();showMultiChromeTemporarily();configureCobraPip(false);
    cobraStartPresentationTicker();cobraApplyDisplayPerformance("multiview-return");
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("multiview-return");
    mMain.post(this::cobraApplySystemBarsForSurface);return true;
  }

'''

def patch_activity(path:Path):
    before_b=path.read_bytes();req(hb(before_b)==PARENT_ACTIVITY,'Not exact audited 2103226 Activity preimage')
    s=before_b.decode()
    protected_methods=hashes(s,PROTECTED_METHODS)
    protected_classes=hashes(s,PROTECTED_CLASSES,'class')

    s=once(s,'  private boolean mCobraCreatingMulti = false;\n',
'''  private boolean mCobraCreatingMulti = false;
  // Device-audited Multi-View presentation state. These fields never own or create players.
  private String mCobraMultiEnlargedKey = "";
  private boolean mCobraMultiFullscreenActive = false;
  private String mCobraMultiFullscreenKey = "";
''','Multi-View state fields')

    s=replace_member(s,'CobraFoldAspectPolicy',FOLD_POLICY,'class')
    s=s.replace(
      'Fold Fit keeps the whole frame. Fold Fill fills the current video pane with the minimum center crop. Both follow cover/inner, rotation and window changes without restarting playback.',
      'Fold Fit reduces oversized black bands while preserving proportions. Fold Fill uses the full pane with the minimum center crop. Both follow cover/inner, rotation and window changes without restarting playback.')
    s=s.replace(
      'selected==CobraFoldAspectPolicy.FIT_MODE?"Whole frame • no crop":selected==CobraFoldAspectPolicy.FILL_MODE?"Fill pane • minimum center crop":null',
      'selected==CobraFoldAspectPolicy.FIT_MODE?"Balanced fit • reduced black bands":selected==CobraFoldAspectPolicy.FILL_MODE?"Fill pane • minimum center crop":null')

    marker='  private final class CobraPlayerBinding implements Player.Listener {'
    req(s.count(marker)==1,'CobraPlayerBinding insertion marker drift')
    s=s.replace(marker,LIVE_HELPERS+marker,1)

    binding=member(s,'CobraPlayerBinding','class')
    binding=once(binding,'    String error="";\n',
      '    String error="";\n    int liveEndedRecoveries=0;long liveEndedRecoveryAt=0L;boolean liveEndedRecovering=false;\n',
      'live-ended binding state')
    binding=once(binding,'      if(state==Player.STATE_READY){\n',
      '      if(state==Player.STATE_READY){\n        liveEndedRecovering=false;\n',
      'live-ended READY clear')
    binding=once(binding,
'''        if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("player-state-"+state);
      }
      cobraUpdatePlaybackLabels();cobraStartPresentationTicker();''',
'''        if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("player-state-"+state);
      }
      if(CobraLiveEndedPolicy.eligible(vitals.live,!mPlayingVodKey.isEmpty(),player.getPlayWhenReady(),state))
        cobraRecoverUnexpectedLiveEnded(this);
      cobraUpdatePlaybackLabels();cobraStartPresentationTicker();''',
      'live-ended recovery hook')
    s=replace_member(s,'CobraPlayerBinding',binding,'class')

    state=member(s,'cobraPlayerState')
    state=once(state,'    if(player.getPlaybackState()==Player.STATE_ENDED)return "Ended";',
'''    if(player.getPlaybackState()==Player.STATE_ENDED){
      if(binding!=null&&binding.vitals.live)
        return binding.liveEndedRecovering?"Reconnecting…":"Stream unavailable";
      return "Ended";
    }''','live-ended visible label')
    s=replace_member(s,'cobraPlayerState',state)

    marker='  private void openMultiView(List<Channel> channels) {'
    req(s.count(marker)==1,'Multi-View helper insertion marker drift')
    s=s.replace(marker,MULTI_HELPERS+marker,1)

    picker=member(s,'showCobraMultiPicker')
    anchor='    LinearLayout filters=new LinearLayout(this);String[] labels={"Favorites","Recent","All","Groups"},keys={"FAVORITES","RECENT","ALL","CATEGORIES"};'
    search='''    EditText search=new EditText(this);search.setTag("cobra_multi_search");search.setSingleLine(true);search.setHint("Search channels");search.setTextColor(Color.WHITE);search.setHintTextColor(0xff9fb0c2);search.setBackground(cobraPanelSurface(0xff101722,14,0xff293244));search.setPadding(dp(12),0,dp(12),0);search.addTextChangedListener(new android.text.TextWatcher(){public void beforeTextChanged(CharSequence x,int a,int b,int c){}public void onTextChanged(CharSequence x,int a,int b,int c){}public void afterTextChanged(android.text.Editable e){renderCobraMultiPickerSearch(e.toString());}});content.addView(search,new LinearLayout.LayoutParams(-1,dp(48)));
'''+anchor
    picker=once(picker,anchor,search,'Multi-View picker search')
    s=replace_member(s,'showCobraMultiPicker',picker)

    actions=member(s,'showCobraMultiTileActions')
    actions=once(actions,
'''    rows.addView(cobraSheetRow("audio","Use audio here",null,false,true,()->cobraUseMultiAudioHere(key)));
    rows.addView(cobraSheetRow("guide","Change channel",null,false,true,()->{mCobraMultiReplaceIndex=cobraMultiIndex(key);if(mCobraMultiReplaceIndex>=0)showCobraMultiPicker(true);}));
    if(mCobraTiles.keys().size()<4)rows.addView(cobraSheetRow("add","Add screen",null,false,true,()->{mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);}));
    rows.addView(cobraSheetRow("fullscreen","Watch fullscreen",null,false,true,()->{int i=cobraMultiIndex(key);if(i>=0){setMultiAudio(i);multiToSingle();}}));''',
'''    rows.addView(cobraSheetRow("audio","Use audio here",null,false,true,()->cobraUseMultiAudioHere(key)));
    rows.addView(cobraSheetRow("guide","Change channel",null,false,true,()->{mCobraMultiReplaceIndex=cobraMultiIndex(key);if(mCobraMultiReplaceIndex>=0)showCobraMultiPicker(true);}));
    if(mCobraTiles.keys().size()<4){rows.addView(cobraSheetRow("add","Add screen",null,false,true,()->{mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);}));rows.addView(cobraSheetRow("search","Search and add",null,false,true,()->cobraShowMultiSearchAdd()));}
    ExoPlayer tilePlayer=tile.player;rows.addView(cobraSheetRow(tilePlayer!=null&&tilePlayer.getPlayWhenReady()?"pause":"play",tilePlayer!=null&&tilePlayer.getPlayWhenReady()?"Pause":"Resume","Only this screen",false,true,()->cobraToggleMultiTilePause(key)));
    rows.addView(cobraSheetRow("multi",key.equals(mCobraMultiEnlargedKey)?"Restore grid":"Enlarge screen",key.equals(mCobraMultiEnlargedKey)?"Return to equal Multi-View":"Keep the other screens visible",false,true,()->cobraToggleMultiEnlarge(key)));
    rows.addView(cobraSheetRow("fullscreen","Full screen","Return to Multi-View without rebuilding players",false,true,()->cobraPromoteMultiTileFullscreen(key)));''',
      'Multi-View tile controls')
    s=replace_member(s,'showCobraMultiTileActions',actions)

    layout=member(s,'cobraLayoutMultiTiles')
    layout=once(layout,
'''    if(mCobraMultiCanvas==null)return;int w=mCobraMultiCanvas.getWidth(),h=mCobraMultiCanvas.getHeight();if(w<=0||h<=0)return;ArrayList<CobraVideoTile> tiles=mCobraTiles.values();
    for(int i=0;i<tiles.size();i++){int[] rect=CobraLayoutMath.tile(i,tiles.size(),w,h);cobraPosition(tiles.get(i).view,rect[0],rect[1],rect[2],rect[3]);}''',
'''    if(mCobraMultiCanvas==null)return;int w=mCobraMultiCanvas.getWidth(),h=mCobraMultiCanvas.getHeight();if(w<=0||h<=0)return;ArrayList<CobraVideoTile> tiles=mCobraTiles.values();
    int enlarged=mCobraMultiEnlargedKey.isEmpty()?-1:cobraMultiIndex(mCobraMultiEnlargedKey);if(enlarged<0)mCobraMultiEnlargedKey="";
    for(int i=0;i<tiles.size();i++){int[] rect=CobraMultiLayoutPolicy.rect(i,tiles.size(),w,h,enlarged);cobraPosition(tiles.get(i).view,rect[0],rect[1],rect[2],rect[3]);}''',
      'Multi-View enlarged layout')
    s=replace_member(s,'cobraLayoutMultiTiles',layout)

    release=member(s,'releaseMulti')
    release=once(release,'  private void releaseMulti() {\n',
      '  private void releaseMulti() {\n    mCobraMultiEnlargedKey="";mCobraMultiFullscreenActive=false;mCobraMultiFullscreenKey="";\n',
      'Multi-View state reset')
    s=replace_member(s,'releaseMulti',release)

    close=member(s,'closeFullscreenToCobraView')
    close=once(close,'  private void closeFullscreenToCobraView() {\n    if(mCobraPlayerLocked)',
      '  private void closeFullscreenToCobraView() {\n    if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return;}\n    if(mCobraPlayerLocked)',
      'Fullscreen Back returns Multi-View')
    s=replace_member(s,'closeFullscreenToCobraView',close)

    back=member(s,'onBackPressed')
    back=once(back,
'''    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions()||closeCobraExperienceDrawer())return;
    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}''',
'''    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions()||closeCobraExperienceDrawer())return;
    if(mCobraMultiFullscreenActive&&mPlayerOverlay!=null){cobraReturnToMultiFromFullscreen();return;}
    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}''',
      'Android Back returns Multi-View')
    s=replace_member(s,'onBackPressed',back)

    pip=member(s,'cobraPrepareMultiForPip')
    pip=once(pip,'  private void cobraPrepareMultiForPip(){\n    if(mMultiChannels==null',
      '  private void cobraPrepareMultiForPip(){\n    if(mCobraMultiFullscreenActive)return;\n    if(mMultiChannels==null',
      'Promoted Multi-View PiP ownership')
    s=replace_member(s,'cobraPrepareMultiForPip',pip)

    chrome=member(s,'cobraBuildPlayerChrome')
    chrome=once(chrome,
      '    header.addView(cobraIcon("back","Return to preview",true,v->closeFullscreenToCobraView()),',
      '    header.addView(cobraIcon("back",mCobraMultiFullscreenActive?"Return to Multi-View":"Return to preview",true,v->closeFullscreenToCobraView()),',
      'Player Back affordance')
    chrome=once(chrome,'    CobraIconButton next=cobraIcon("next","Next channel",true,v->stepChannel(1));',
'''    CobraIconButton next=cobraIcon("next","Next channel",true,v->stepChannel(1));
    if(mCobraMultiFullscreenActive){prev.setEnabled(false);next.setEnabled(false);}''',
      'Disable destructive channel step in promoted fullscreen')
    chrome=once(chrome,
'''    LinearLayout tools=new LinearLayout(this);String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display","Multi-View","More"};
    for(int i=0;i<4;i++){final int action=i;CobraIconButton b=cobraIcon(glyphs[i],labels[i],true,v->{if(action==0)showCobraPlayerDrawer();else if(action==1)showCobraAspectPicker();else if(action==2)beginMultiView();else showPlayerSettingsDrawer();});b.caption(labels[i]);if(action==1)b.setTag("cobra_player_aspect_anchor");if(action==3)b.setTag("cobra_player_options_anchor");tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",52)),1));}''',
'''    LinearLayout tools=new LinearLayout(this);String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display",mCobraMultiFullscreenActive?"Return Multi":"Multi-View","More"};
    for(int i=0;i<4;i++){final int action=i;CobraIconButton b=cobraIcon(glyphs[i],labels[i],true,v->{if(action==0){if(mCobraMultiFullscreenActive)toast("Return to Multi-View to change screens");else showCobraPlayerDrawer();}else if(action==1)showCobraAspectPicker();else if(action==2){if(mCobraMultiFullscreenActive)cobraReturnToMultiFromFullscreen();else beginMultiView();}else showPlayerSettingsDrawer();});b.caption(labels[i]);if(action==1)b.setTag("cobra_player_aspect_anchor");if(action==3)b.setTag("cobra_player_options_anchor");tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",52)),1));}''',
      'Player Return Multi action')
    s=replace_member(s,'cobraBuildPlayerChrome',chrome)

    settings=member(s,'showPlayerSettingsDrawer')
    settings=once(settings,
'''    rows.addView(cobraSheetRow("source","Manage sources","Leaves this player",false,true,()->{closePlayer();stopCobraPreview();mCobraInternalScreen="internal";showSources();}));
    rows.addView(cobraSheetRow("close","Close player","Stop playback and return to browsing",true,true,()->{mCobraPreviewAutoplayAllowed=false;closePlayer();showCobraPrimaryView();cobraUpdatePlaybackLabels();}));''',
'''    rows.addView(cobraSheetRow("source","Manage sources","Leaves this player",false,true,()->{if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();releaseMulti();}else closePlayer();stopCobraPreview();mCobraInternalScreen="internal";showSources();}));
    rows.addView(cobraSheetRow("close",mCobraMultiFullscreenActive?"Return to Multi-View":"Close player",mCobraMultiFullscreenActive?"Keep every Multi-View screen running":"Stop playback and return to browsing",true,true,()->{if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return;}mCobraPreviewAutoplayAllowed=false;closePlayer();showCobraPrimaryView();cobraUpdatePlaybackLabels();}));''',
      'Player settings Multi-View return')
    s=replace_member(s,'showPlayerSettingsDrawer',settings)

    req('multiToSingle();' not in member(s,'showCobraMultiTileActions'),'Tile Full screen still tears down Multi-View')
    req('cobraDisposePlayer' not in member(s,'cobraPromoteMultiTileFullscreen'),'Fullscreen promotion disposes player')
    req('cobraDisposePlayer' not in member(s,'cobraReturnToMultiFromFullscreen'),'Multi-View return disposes player')
    req('releaseMulti();' not in member(s,'cobraPromoteMultiTileFullscreen'),'Fullscreen promotion releases Multi-View')
    req('releaseSinglePlayer' not in member(s,'cobraReturnToMultiFromFullscreen'),'Return releases promoted player')
    req('CobraLiveEndedPolicy.eligible(vitals.live,!mPlayingVodKey.isEmpty()' in s,'VOD exclusion missing')
    req('SMART_TARGET=.78f' in s,'Device Fold Fit policy missing')

    for n,h in protected_methods.items(): req(hb(member(s,n))==h,'Protected method changed: '+n)
    for n,h in protected_classes.items(): req(hb(member(s,n,'class'))==h,'Protected class changed: '+n)

    path.write_text(s)
    return {
      'activity_before_sha256':hb(before_b),'activity_after_sha256':sha(path),
      'protected_methods_sha256':protected_methods,'protected_classes_sha256':protected_classes,
      'modified_members':['CobraFoldAspectPolicy','CobraPlayerBinding','cobraPlayerState',
        'showCobraMultiPicker','showCobraMultiTileActions','cobraLayoutMultiTiles','releaseMulti',
        'closeFullscreenToCobraView','onBackPressed','cobraPrepareMultiForPip',
        'cobraBuildPlayerChrome','showPlayerSettingsDrawer'],
      'added_members':['CobraLiveEndedPolicy','cobraRecoverUnexpectedLiveEnded',
        'CobraMultiLayoutPolicy','cobraToggleMultiTilePause','cobraToggleMultiEnlarge',
        'cobraShowMultiSearchAdd','renderCobraMultiPickerSearch',
        'cobraPromoteMultiTileFullscreen','cobraReturnToMultiFromFullscreen']
    }

def patch_identity(shell:Path):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime release');runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'packager identity drift');pack.write_text(p.replace(old,new));return gradle

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact audited 2103226 replay')
    req(receipt.get('native_engine_sha256')==NATIVE,'Native engine receipt drift')

    activity=shell/ACT;splash=shell/(SOURCE+'Splash.java.in');smart=shell/(SOURCE+'CobraSmartReturn.java.in')
    main=shell/(SOURCE+'Main.java.in');renderer=shell/(SOURCE+'CobraVisualRenderer.java.in')
    for p in (activity,splash,smart,main,renderer):req(p.is_file(),'Missing '+str(p))
    frozen={'splash':sha(splash),'smart_return':sha(smart),'main':sha(main),'visual_renderer':sha(renderer)}
    scope=patch_activity(activity);gradle=patch_identity(shell)
    req(sha(splash)==frozen['splash'],'Choose Your Experience / Health changed')
    req(sha(smart)==frozen['smart_return'],'Smart Return changed')
    req(sha(main)==frozen['main'],'Kodi Main changed')
    req(sha(renderer)==frozen['visual_renderer'],'Global visual renderer changed')

    for name in (ACT,SOURCE+'Splash.java.in',SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
        req(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
    rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)

    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
      candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
      native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
      device_live_fold_multiview_audited=True,
      live_ended_auto_recovery=True,live_ended_recovery_bounded=2,vod_end_behavior_unchanged=True,
      fold_fit_device_balanced=True,fold_fill_preserved=True,fold_switch_player_recreated=False,
      multiview_search_add=True,multiview_pause_resume=True,multiview_enlarge=True,
      multiview_fullscreen_reversible=True,multiview_fullscreen_player_recreated=False,
      multiview_back_returns=True,multiview_existing_controls_preserved=True,
      playback_core_unchanged=True,providers_unchanged=True,timeshift_core_unchanged=True,
      movie_tv_details_unchanged=True,tv_show_typography_unchanged=True,
      drawer_owner_preserved=True,smart_return_preserved=True,choose_experience_ui_unchanged=True,
      health_center_unchanged=True,global_visual_renderer_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Receipt drift '+name)

    Path('audit227').mkdir(exist_ok=True)
    scope.update({
      'build':VERSION,'parent':OLD_VERSION,
      'locked_source_parent':'locked-infinity-cobra-2103225-tv-show-typography-passed',
      'audited_feature_parent':'2103226 Fold Fit/Fill test candidate',
      'preaudit_run':PREAUDIT_RUN,'preaudit_activity_sha256':PARENT_ACTIVITY,
      'authorized_delta':'device-reported Live Ended + Fold Fit + missing Multi-View controls/reversible fullscreen',
      'frozen_files_sha256':frozen,'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,
      'live_ended':{'vod_excluded':True,'max_automatic_recoveries':2,'same_player_first':True,'unbounded_loop':False},
      'fold_fit':{'mode':12,'balanced_proportional':True,'target_short_axis':.78,'reduced_black_bands':True},
      'fold_fill':{'mode':13,'minimum_center_crop':True,'preserved':True},
      'multiview':{
        'existing_controls_preserved':True,'search_and_add':True,'pause_resume_per_tile':True,
        'enlarge_without_fullscreen':True,'fullscreen_reversible':True,'back_returns_to_multiview':True,
        'fullscreen_player_recreated':False,'other_tiles_released':False
      },
      'physical_device_verified':False,'status':'TEST CANDIDATE'
    })
    Path('audit227/scope.json').write_text(json.dumps(scope,indent=2,sort_keys=True)+'\n')
    print('PASS: 2103227 device-audited Live/Fold/Multi-View delta applied over exact 2103226 replay')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
