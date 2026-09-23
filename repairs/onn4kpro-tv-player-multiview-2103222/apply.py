#!/usr/bin/env python3
"""2103222 onn. 4K Pro TV player / Multi-View / full-canvas repair.

Parent: exact locked 2103221 TV Remote UI RC4 source.
Scope: generated Android TV layer only. The ARM64 phone/Fold line is untouched.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103222
OLD_VERSION=2103221
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Remote-UI-RC4'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Player-MultiView-RC5'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def hb(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def sha(path:Path)->str:return hb(path.read_bytes())
def req(value,message):
    if not value:raise RuntimeError(message)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label} anchor drift ({text.count(old)})')
    return text.replace(old,new,1)

def member_span(text:str,name:str,kind='method'):
    if kind=='class':
        m=re.search(r'(?m)^\s*(?:(?:public|private|protected|static|final|abstract)\s+)*class\s+'+re.escape(name)+r'\b',text)
    elif kind=='ctor':
        m=re.search(r'(?m)^\s*'+re.escape(name)+r'\s*\([^;\n]*\)\s*\{',text)
    else:
        m=re.search(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{',text)
    req(m is not None,'Missing '+kind+' member: '+name)
    start=m.start();brace=text.find('{',m.start());req(brace>=0,'Missing brace: '+name)
    depth=0;quote=None;escape=False;line=False;block=False;i=brace
    while i<len(text):
        ch=text[i];nx=text[i+1] if i+1<len(text) else ''
        if line:
            if ch=='\n':line=False
        elif block:
            if ch=='*' and nx=='/':block=False;i+=1
        elif quote:
            if escape:escape=False
            elif ch=='\\':escape=True
            elif ch==quote:quote=None
        else:
            if ch=='/' and nx=='/':line=True;i+=1
            elif ch=='/' and nx=='*':block=True;i+=1
            elif ch in ('"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return start,i+1
        i+=1
    raise RuntimeError('Unclosed '+kind+' member: '+name)

def member(text,name,kind='method'):
    a,b=member_span(text,name,kind);return text[a:b]
def replace_member(text,name,replacement,kind='method'):
    a,b=member_span(text,name,kind);return text[:a]+replacement+text[b:]

TV_HANDOFF_HELPERS=r'''  private static final String COBRA_TV_PLAYER_MULTIVIEW_BUILD="cobra_tv_player_multiview_2103222";
  private View mCobraTvFullscreenReturnFocus;
  private int mCobraTvSurfaceHandoffGeneration=0;
  private LinearLayout mCobraTvPlayerHeader;
  private LinearLayout mCobraTvPlayerTransport;
  private LinearLayout mCobraTvPlayerTools;
  private String mCobraMultiEnlargedKey="";
  private boolean mCobraMultiFullscreenActive=false;
  private String mCobraMultiFullscreenKey="";

  private void cobraTvAttachSurfaceWhenReady(ExoPlayer player,TextureView texture,Runnable ready){
    if(player==null||texture==null)return;
    final int generation=++mCobraTvSurfaceHandoffGeneration;
    texture.setAlpha(0f);texture.setVisibility(View.VISIBLE);
    final Runnable[] poll=new Runnable[1];final int[] tries={0};
    poll[0]=()->{
      if(generation!=mCobraTvSurfaceHandoffGeneration||player==null||texture==null)return;
      if(texture.isAvailable()||tries[0]++>=180){
        cobraAttachVideo(player,texture);texture.setAlpha(1f);
        texture.postOnAnimation(()->{if(generation==mCobraTvSurfaceHandoffGeneration&&ready!=null)ready.run();});
        return;
      }
      texture.postDelayed(poll[0],16L);
    };
    texture.post(poll[0]);
  }

  private void cobraTvRemoveOverlayAfterSurface(FrameLayout overlay,Runnable after){
    if(overlay==null){if(after!=null)after.run();return;}
    overlay.postOnAnimation(()->overlay.postOnAnimation(()->{
      if(overlay.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)overlay.getParent()).removeView(overlay);
      if(after!=null)after.run();
    }));
  }

  private View cobraTvPlayerTag(String tag){
    return mPlayerChrome==null?null:mPlayerChrome.findViewWithTag(tag);
  }

  private boolean cobraTvFocusPlayerTag(String tag){
    View target=cobraTvPlayerTag(tag);
    if(target!=null&&target.isShown()&&target.isEnabled()&&target.isFocusable()){target.requestFocus();return true;}
    return false;
  }

  private boolean cobraTvPlayerFocusGraph(int code){
    View focus=getCurrentFocus();if(focus==null||mPlayerChrome==null||!cobraTvViewInside(mPlayerChrome,focus))return false;
    Object raw=focus.getTag();String tag=raw instanceof String?(String)raw:"";
    boolean header=tag.startsWith("cobra_tv_player_header")||"cobra_last_channel".equals(tag);
    boolean transport=tag.startsWith("cobra_tv_player_transport")||"cobra_live_rewind_30".equals(tag)||"cobra_player_play_pause".equals(tag)||"cobra_live_edge".equals(tag);
    boolean tools=tag.startsWith("cobra_tv_player_tool");
    boolean timeline="cobra_live_timeshift_seek".equals(tag);
    if(code==KeyEvent.KEYCODE_DPAD_UP){
      if(tools){if(mCobraTimeshiftSeek!=null&&mCobraTimeshiftSeek.getVisibility()==View.VISIBLE)return mCobraTimeshiftSeek.requestFocus();return cobraTvFocusPlayerTag("cobra_player_play_pause");}
      if(timeline)return cobraTvFocusPlayerTag("cobra_player_play_pause");
      if(transport)return cobraTvFocusPlayerTag("cobra_tv_player_header_back");
      if(header)return true;
    }
    if(code==KeyEvent.KEYCODE_DPAD_DOWN){
      if(header)return cobraTvFocusPlayerTag("cobra_player_play_pause");
      if(transport){if(mCobraTimeshiftSeek!=null&&mCobraTimeshiftSeek.getVisibility()==View.VISIBLE)return mCobraTimeshiftSeek.requestFocus();return cobraTvFocusPlayerTag("cobra_tv_player_tool_channels");}
      if(timeline)return cobraTvFocusPlayerTag("cobra_tv_player_tool_channels");
      if(tools)return true;
    }
    return false;
  }

  private void cobraTvRestoreGuideFocus(){
    View restore=mCobraTvFullscreenReturnFocus;mCobraTvFullscreenReturnFocus=null;
    if(restore!=null&&restore.isAttachedToWindow()&&restore.isShown()){restore.requestFocus();return;}
    if(mCobraGuideList!=null&&mCobraGuideList.isAttachedToWindow()){
      View current=mGuidePreviewChannel==null?null:mCobraGuideList.findViewWithTag("cobra-channel:"+mGuidePreviewChannel.id);
      if(current!=null){current.requestFocus();return;}
      if(mCobraGuideList.getChildCount()>0){
        View first=mCobraGuideList.getChildAt(0);if(first instanceof android.view.ViewGroup)cobraTvFocusFirst((android.view.ViewGroup)first);else first.requestFocus();
      }
    }
  }

  static final class CobraMultiLayoutPolicy {
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

  private void cobraTvFocusCurrentMultiTile(){
    if(mMultiChannels==null||mMultiChannels.length==0)return;
    int index=Math.max(0,Math.min(mAudioTile,mMultiChannels.length-1));CobraVideoTile tile=mCobraTiles.get(mMultiChannels[index].id);
    if(tile!=null&&tile.view!=null&&tile.view.isAttachedToWindow())tile.view.requestFocus();
  }

  private void cobraToggleMultiTilePause(String key){
    CobraVideoTile tile=mCobraTiles.get(key);if(tile==null||tile.player==null)return;
    if(tile.player.getPlayWhenReady()){tile.player.pause();if(cobraMultiIndex(key)==mAudioTile)cobraReleaseAudioFocus(tile.player);}
    else cobraUserPlay(tile.player);
    cobraUpdatePlaybackLabels();int i=cobraMultiIndex(key);if(i>=0)showCobraMultiTileActions(i);
  }

  private void cobraToggleMultiEnlarge(String key){
    if(key==null||mCobraTiles.get(key)==null)return;
    mCobraMultiEnlargedKey=key.equals(mCobraMultiEnlargedKey)?"":key;
    closeCobraActionSheet();cobraLayoutMultiTiles();showMultiChromeTemporarily();
    CobraVideoTile tile=mCobraTiles.get(key);if(tile!=null)tile.view.post(tile.view::requestFocus);
  }

  private void cobraShowMultiSearchAdd(){
    if(mCobraTiles.keys().size()>=4){toast("Multi-View already has 4 screens");return;}
    mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);
    if(mCobraMultiPicker==null)return;
    View raw=mCobraMultiPicker.findViewWithTag("cobra_multi_search");
    if(raw instanceof EditText){
      EditText input=(EditText)raw;input.requestFocus();
      input.post(()->{
        android.view.inputmethod.InputMethodManager keyboard=(android.view.inputmethod.InputMethodManager)getSystemService(INPUT_METHOD_SERVICE);
        if(keyboard!=null)keyboard.showSoftInput(input,android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT);
      });
    }
  }

  private void renderCobraMultiPickerSearch(String query){
    if(mCobraMultiPicker==null)return;View view=mCobraMultiPicker.findViewWithTag("cobra_multi_picker_list");
    if(!(view instanceof android.widget.ListView))return;
    final String needle=query==null?"":query.trim().toLowerCase(Locale.ROOT);
    if(needle.isEmpty()){renderCobraMultiPicker("RECENT");return;}
    final ArrayList<Channel> channels=new ArrayList<>();
    for(Channel c:mChannels){
      String name=c.name==null?"":c.name.toLowerCase(Locale.ROOT),group=c.group==null?"":c.group.toLowerCase(Locale.ROOT);
      if(cobraChannelAllowed(c)&&mCobraTiles.get(c.id)==null&&(name.contains(needle)||group.contains(needle)))channels.add(c);
    }
    android.widget.ListView list=(android.widget.ListView)view;
    list.setAdapter(new android.widget.BaseAdapter(){
      public int getCount(){return channels.size();}public Channel getItem(int p){return channels.get(p);}public long getItemId(int p){return p;}
      public View getView(int p,View old,android.view.ViewGroup host){
        Channel c=channels.get(p);Button row=old instanceof Button?(Button)old:cobraTextButton("",true,()->{});
        GuideProgram current=cobraCurrentProgram(c);row.setText(c.name+"\n"+(current==null?cobraGuideStatus(c):current.title));row.setTextColor(Color.WHITE);row.setTextSize(14);
        row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setPadding(dp(14),0,dp(14),0);row.setMaxLines(2);row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(70)));
        row.setOnClickListener(v->selectCobraMultiChannel(c));return row;
      }});
    list.post(()->{if(list.getChildCount()>0)list.getChildAt(0).requestFocus();});
  }

  private void cobraPromoteMultiTileFullscreen(String key){
    if(mCobraMultiFullscreenActive||key==null)return;int index=cobraMultiIndex(key);CobraVideoTile tile=mCobraTiles.get(key);
    if(index<0||tile==null||tile.player==null||mMultiOverlay==null)return;
    closeCobraActionSheet();closeCobraMultiPicker(true);setMultiAudio(index);
    mCobraMultiFullscreenActive=true;mCobraMultiFullscreenKey=key;mPlaying=tile.channel;mPlayingIndex=mChannels.indexOf(tile.channel);mPlayingVodKey="";mPendingResumeMs=0L;
    openPlayerOverlay(tile.channel);mPlayer=tile.player;final FrameLayout multi=mMultiOverlay;
    cobraTvAttachSurfaceWhenReady(mPlayer,mPlayerTexture,()->{
      if(mPlayerOverlay!=null)mPlayerOverlay.setBackgroundColor(Color.BLACK);
      if(mPlayerTexture!=null)mPlayerTexture.setOpaque(true);
      if(multi!=null)multi.setVisibility(View.GONE);
      if(mPlayer!=null){mPlayer.setVolume(1f);cobraClaimAudioFocus(mPlayer);}
      showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();
    });
    configureCobraPip(false);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("multiview-fullscreen");
  }

  private boolean cobraReturnToMultiFromFullscreen(){
    if(!mCobraMultiFullscreenActive)return false;
    String key=mCobraMultiFullscreenKey;CobraVideoTile tile=mCobraTiles.get(key);ExoPlayer session=mPlayer;
    if(tile==null||session==null||tile.player!=session||mMultiOverlay==null){mCobraMultiFullscreenActive=false;mCobraMultiFullscreenKey="";return false;}
    closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(true);clearCobraPlayerLockState(false);
    mMain.removeCallbacks(mHideChrome);mMain.removeCallbacks(mStallWatchdog);FrameLayout overlay=mPlayerOverlay;FrameLayout multi=mMultiOverlay;cobraResetMotion(mPlayerChrome);
    mCobraMultiFullscreenActive=false;mCobraMultiFullscreenKey="";
    mPlayer=null;mPlayerOverlay=null;mPlayerTexture=null;mPlayerChrome=null;mCobraPlayerRotationButton=null;mCobraLiveRewindButton=null;mCobraGoLiveButton=null;
    mCobraPlayerProgram=null;mCobraPlayerSchedule=null;mCobraPlayerUpcoming=null;mCobraPlayerProgramProgress=null;mPlaying=null;mPlayingIndex=-1;mPlayingVodKey="";mPlayingVodTitle="";mPendingResumeMs=0L;
    if(multi!=null)multi.setVisibility(View.VISIBLE);
    cobraTvAttachSurfaceWhenReady(session,tile.texture,()->cobraTvRemoveOverlayAfterSurface(overlay,()->{
      int at=cobraMultiIndex(key);if(at>=0)setMultiAudio(at);cobraLayoutMultiTiles();showMultiChromeTemporarily();cobraTvFocusCurrentMultiTile();
    }));
    configureCobraPip(false);cobraStartPresentationTicker();if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("multiview-return");mMain.post(this::cobraApplySystemBarsForSurface);return true;
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()

    # Insert TV-only helpers immediately before the existing remote helper marker.
    marker='  private static final String COBRA_TV_REMOTE_UI_BUILD="cobra_tv_remote_ui_2103221";'
    req(s.count(marker)==1,'2103221 helper marker drift')
    s=s.replace(marker,TV_HANDOFF_HELPERS+marker,1)

    # TV system bars: this dedicated TV build always owns the whole display canvas.
    s=replace_member(s,'cobraApplySystemBarsForSurface',r'''  private void cobraApplySystemBarsForSurface(){
    Window window=getWindow();View decor=window.getDecorView();
    window.clearFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    int flags=View.SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
        |View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY;
    decor.setSystemUiVisibility(flags);window.setStatusBarColor(Color.TRANSPARENT);window.setNavigationBarColor(Color.TRANSPARENT);
    if(Build.VERSION.SDK_INT>=30&&window.getInsetsController()!=null){
      android.view.WindowInsetsController controller=window.getInsetsController();
      controller.setSystemBarsBehavior(android.view.WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
      controller.hide(android.view.WindowInsets.Type.statusBars()|android.view.WindowInsets.Type.navigationBars());
    }
    if(mRoot!=null){
      mRoot.setOnApplyWindowInsetsListener((v,insets)->{v.setPadding(0,0,0,0);return insets;});
      mRoot.setPadding(0,0,0,0);mRoot.requestLayout();
    }
    decor.requestLayout();if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())mCobraGuideShell.requestLayout();
  }''')

    # Full-canvas, clamped guide layout. The root no longer reserves phone bar insets.
    s=replace_member(s,'cobraLayoutGuide',r'''  private void cobraLayoutGuide(){
    if(mCobraGuideShell==null)return;int w=mCobraGuideShell.getWidth(),h=mCobraGuideShell.getHeight();if(w<=0||h<=0)return;
    float density=Math.max(.01f,getResources().getDisplayMetrics().density);
    mCobraModeLayout=CobraModeLayout.solve("grid",Math.max(1,Math.round(w/density)),Math.max(1,Math.round(h/density)),getResources().getConfiguration().fontScale,false);
    int[][] boxes={mCobraModeLayout.toolbar,mCobraModeLayout.rail,mCobraModeLayout.directory,mCobraModeLayout.video,mCobraModeLayout.details,mCobraModeLayout.browser,mCobraModeLayout.footer};
    View[] views={mCobraModeToolbar,mCobraModeRail,mCobraGuideDirectory,mCobraGuideVideo,mCobraGuideDetails,mCobraGuideBrowser,mCobraModeFooter};
    for(int i=0;i<boxes.length;i++){
      int[] r=boxes[i];int x=Math.max(0,Math.min(w,Math.round(r[0]*density))),y=Math.max(0,Math.min(h,Math.round(r[1]*density)));
      int rw=Math.max(0,Math.min(w-x,Math.round(r[2]*density))),rh=Math.max(0,Math.min(h-y,Math.round(r[3]*density)));
      if(views[i]==null)continue;if(rw<=0||rh<=0){views[i].setVisibility(View.GONE);continue;}
      views[i].setVisibility(View.VISIBLE);cobraPosition(views[i],x,y,rw,rh);
    }
    if(mCobraModeLayout!=null)mCobraModeLayout.width=Math.max(1,Math.round(w/density));
  }''')

    # Preserve the working group overlay but fit it to the TV canvas instead of phone safe areas.
    directory=member(s,'cobraOpenTvDirectory')
    old='''    int w=decor.getWidth()>0?decor.getWidth():getResources().getDisplayMetrics().widthPixels,h=decor.getHeight()>0?decor.getHeight():getResources().getDisplayMetrics().heightPixels;
    int top=dp(28),bottom=dp(20);if(Build.VERSION.SDK_INT>=23&&decor.getRootWindowInsets()!=null){top+=decor.getRootWindowInsets().getSystemWindowInsetTop();bottom+=decor.getRootWindowInsets().getSystemWindowInsetBottom();}
    int width=Math.max(dp(320),Math.min(dp(430),Math.round(w*.42f)));FrameLayout.LayoutParams position=new FrameLayout.LayoutParams(Math.min(width,w-dp(24)),Math.max(1,h-top-bottom),Gravity.TOP|Gravity.LEFT);position.topMargin=top;position.bottomMargin=bottom;'''
    new='''    int w=decor.getWidth()>0?decor.getWidth():getResources().getDisplayMetrics().widthPixels,h=decor.getHeight()>0?decor.getHeight():getResources().getDisplayMetrics().heightPixels;
    int inset=dp(16);int width=Math.max(dp(340),Math.min(dp(460),Math.round(w*.38f)));FrameLayout.LayoutParams position=new FrameLayout.LayoutParams(Math.min(width,w-inset*2),Math.max(1,h-inset*2),Gravity.TOP|Gravity.LEFT);position.leftMargin=inset;position.topMargin=inset;position.bottomMargin=inset;'''
    directory=once(directory,old,new,'TV group canvas fit')
    directory=directory.replace('panel.setTranslationX(-position.width);panel.animate().translationX(0f).setDuration(80L).start();',
                                'panel.setTranslationX(-position.width);panel.animate().translationX(0f).setDuration(70L).start();')
    s=replace_member(s,'cobraOpenTvDirectory',directory)

    # Open player overlay transparently so the already-rendered guide/preview remains visible until video surface handoff.
    player=member(s,'openPlayerOverlay')
    player=once(player,
      'mPlayerOverlay=new FrameLayout(this);mPlayerOverlay.setBackgroundColor(vtheme().color("cobra.openPlayerOverlay.colors.1",Color.BLACK));mPlayerOverlay.setFocusable(true);mPlayerOverlay.setFocusableInTouchMode(false);',
      'mPlayerOverlay=new FrameLayout(this);mPlayerOverlay.setBackgroundColor(Color.TRANSPARENT);mPlayerOverlay.setFocusable(true);mPlayerOverlay.setFocusableInTouchMode(false);',
      'transparent player handoff overlay')
    player=once(player,
      'mPlayerTexture=new TextureView(this);mAspectMode=cobraChannelAspect(channel);mPlayerOverlay.addView(mPlayerTexture,new FrameLayout.LayoutParams(-1,-1));',
      'mPlayerTexture=new TextureView(this);mPlayerTexture.setOpaque(false);mPlayerTexture.setAlpha(0f);mAspectMode=cobraChannelAspect(channel);mPlayerOverlay.addView(mPlayerTexture,new FrameLayout.LayoutParams(-1,-1));',
      'transparent destination texture')
    s=replace_member(s,'openPlayerOverlay',player)

    # Preview -> fullscreen keeps the guide/preview visible until fullscreen TextureView is available.
    s=replace_member(s,'promoteCobraPreviewToFullscreen',r'''  private void promoteCobraPreviewToFullscreen(Channel channel) {
    if(channel==null)return;ExoPlayer session=cobraChannelKey(channel).equals(mCobraPreviewSessionKey)?mCobraPreviewPlayer:null;
    boolean local=session==mCobraTimeshiftPlayer&&mCobraTimeshiftSession!=null,proxy=session==mCobraTimeshiftProxyPlayer&&mCobraTimeshiftSession!=null;
    mCobraTvFullscreenReturnFocus=getCurrentFocus();cobraEndMiniBackgroundPlayback();
    mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";mCobraPreviewHandoffs++;
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mTriedFallback=false;openPlayerOverlay(channel);mPlayer=session;
    if(local)mCobraTimeshiftPlayer=session;if(proxy)mCobraTimeshiftProxyPlayer=session;
    if(session!=null){
      cobraTvAttachSurfaceWhenReady(session,mPlayerTexture,()->{
        if(mPlayerOverlay!=null)mPlayerOverlay.setBackgroundColor(Color.BLACK);
        if(mPlayerTexture!=null)mPlayerTexture.setOpaque(true);
        session.setAudioAttributes(session.getAudioAttributes(),false);session.setVolume(1f);cobraClaimAudioFocus(session);
        showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();
      });
    }else startSinglePlayer(channel.primaryUrl);
    cobraStartPresentationTicker();cobraUpdatePlaybackLabels();configureCobraPip(false);
    cobraSetTimeshiftUiState((local||proxy)&&mCobraTimeshiftSession.ready()?"READY":(local||proxy)?"RECORDING":cobraChannelRewindEnabled(channel)&&cobraLiveChannel(channel)?"UNSUPPORTED":"OFF",(local||proxy)?Math.round(mCobraTimeshiftSession.windowDurationMs()/1000f)+"s":"");
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged(local?"preview-timeshift-fullscreen":"preview-fullscreen");
  }''')

    # Fullscreen -> guide keeps fullscreen frame up until the existing preview TextureView owns the session.
    s=replace_member(s,'closeFullscreenToCobraView',r'''  private void closeFullscreenToCobraView() {
    if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return;}
    if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}
    if(mCobraProviderCatchupActive){mCobraProviderCatchupActive=false;mCobraLiveRewindChannel=null;closePlayer();showCobraPrimaryView();return;}
    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"fullscreen-preview");mCobraPlayerRotationButton=null;
    if(mPlayer==null||mPlaying==null||!mPlayingVodKey.isEmpty()){closePlayer();showCobraPrimaryView();return;}
    Channel channel=mPlaying;ExoPlayer session=mPlayer;closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(true);clearCobraPlayerLockState(false);
    mPlayer=null;mPlaying=null;mPlayingIndex=-1;mMain.removeCallbacks(mHideChrome);mMain.removeCallbacks(mStallWatchdog);
    FrameLayout overlay=mPlayerOverlay;mPlayerOverlay=null;mPlayerTexture=null;mPlayerChrome=null;
    mCobraPlayerProgram=null;mCobraPlayerSchedule=null;mCobraPlayerUpcoming=null;mCobraPlayerProgramProgress=null;
    mGuidePreviewChannel=channel;mGuidePreviewKey=cobraChannelKey(channel);mGuidePreviewArmed=true;mCobraPreviewPlayer=session;mCobraPreviewSessionKey=cobraChannelKey(channel);
    if(mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow())cobraShowGuideShell();else cobraLayoutGuide();
    if(mCobraPreviewTexture==null){cobraTvRemoveOverlayAfterSurface(overlay,()->{cobraRenderGuideBrowser();cobraTvRestoreGuideFocus();});return;}
    mCobraPreviewTexture.setVisibility(View.VISIBLE);
    cobraTvAttachSurfaceWhenReady(session,mCobraPreviewTexture,()->{
      if(mCobraPreviewMuted){cobraReleaseAudioFocus(session);session.setVolume(0f);}else cobraClaimAudioFocus(session);
      cobraTvRemoveOverlayAfterSurface(overlay,()->{cobraTvRestoreGuideFocus();cobraApplySystemBarsForSurface();});
    });
    configureCobraPip(false);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged("fullscreen-preview");
  }''')

    # Multi-View helper insertion before existing openMultiView.
    marker='  private void openMultiView(List<Channel> channels) {'
    req(s.count(marker)==1,'Multi-View helper insertion drift')
    s=s.replace(marker,marker,1)

    # Picker gets Search and remote-first focus.
    picker=member(s,'showCobraMultiPicker')
    anchor='    LinearLayout filters=new LinearLayout(this);String[] labels={"Favorites","Recent","All","Groups"},keys={"FAVORITES","RECENT","ALL","CATEGORIES"};'
    search='''    EditText search=new EditText(this);search.setTag("cobra_multi_search");search.setSingleLine(true);search.setHint("Search channels");search.setTextColor(Color.WHITE);search.setHintTextColor(0xff9fb0c2);search.setBackground(cobraPanelSurface(0xff101722,14,0xff293244));search.setPadding(dp(14),0,dp(14),0);search.setFocusable(true);search.setFocusableInTouchMode(false);search.addTextChangedListener(new android.text.TextWatcher(){public void beforeTextChanged(CharSequence x,int a,int b,int c){}public void onTextChanged(CharSequence x,int a,int b,int c){}public void afterTextChanged(android.text.Editable e){renderCobraMultiPickerSearch(e.toString());}});content.addView(search,new LinearLayout.LayoutParams(-1,dp(54)));
'''+anchor
    picker=once(picker,anchor,search,'TV Multi-View search')
    s=replace_member(s,'showCobraMultiPicker',picker)

    render=member(s,'renderCobraMultiPicker')
    render=render.replace('list.setFastScrollEnabled(true);','list.setFastScrollEnabled(false);')
    tail='''      if(groups){String g=names.get(p);row.setText(g);row.setOnClickListener(v->renderCobraMultiPicker("GROUP:"+g));}else{Channel c=channels.get(p);GuideProgram current=cobraCurrentProgram(c);row.setText(c.name+"\\n"+(current==null?cobraGuideStatus(c):current.title));row.setOnClickListener(v->selectCobraMultiChannel(c));}return row;}});'''
    if tail in render:
      render=render.replace(tail,tail+'\n    list.post(()->{if(list.getChildCount()>0)list.getChildAt(0).requestFocus();});',1)
    s=replace_member(s,'renderCobraMultiPicker',render)

    # Port approved phone Multi-View tile controls.
    actions=member(s,'showCobraMultiTileActions')
    old='''    rows.addView(cobraSheetRow("audio","Use audio here",null,false,true,()->cobraUseMultiAudioHere(key)));
    rows.addView(cobraSheetRow("guide","Change channel",null,false,true,()->{mCobraMultiReplaceIndex=cobraMultiIndex(key);if(mCobraMultiReplaceIndex>=0)showCobraMultiPicker(true);}));
    if(mCobraTiles.keys().size()<4)rows.addView(cobraSheetRow("add","Add screen",null,false,true,()->{mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);}));
    rows.addView(cobraSheetRow("fullscreen","Watch fullscreen",null,false,true,()->{int i=cobraMultiIndex(key);if(i>=0){setMultiAudio(i);multiToSingle();}}));'''
    new='''    rows.addView(cobraSheetRow("audio","Use audio here",null,false,true,()->cobraUseMultiAudioHere(key)));
    rows.addView(cobraSheetRow("guide","Change channel",null,false,true,()->{mCobraMultiReplaceIndex=cobraMultiIndex(key);if(mCobraMultiReplaceIndex>=0)showCobraMultiPicker(true);}));
    if(mCobraTiles.keys().size()<4){rows.addView(cobraSheetRow("add","Add screen",null,false,true,()->{mCobraMultiReplaceIndex=-1;showCobraMultiPicker(true);}));rows.addView(cobraSheetRow("search","Search and add",null,false,true,()->cobraShowMultiSearchAdd()));}
    ExoPlayer tilePlayer=tile.player;rows.addView(cobraSheetRow(tilePlayer!=null&&tilePlayer.getPlayWhenReady()?"pause":"play",tilePlayer!=null&&tilePlayer.getPlayWhenReady()?"Pause":"Resume","Only this screen",false,true,()->cobraToggleMultiTilePause(key)));
    rows.addView(cobraSheetRow("multi",key.equals(mCobraMultiEnlargedKey)?"Restore grid":"Enlarge screen",key.equals(mCobraMultiEnlargedKey)?"Return to equal Multi-View":"Keep the other screens visible",false,true,()->cobraToggleMultiEnlarge(key)));
    rows.addView(cobraSheetRow("fullscreen","Full screen","Return to Multi-View without rebuilding players",false,true,()->cobraPromoteMultiTileFullscreen(key)));'''
    actions=once(actions,old,new,'Multi-View tile controls')
    s=replace_member(s,'showCobraMultiTileActions',actions)

    s=replace_member(s,'cobraLayoutMultiTiles',r'''  private void cobraLayoutMultiTiles() {
    if(mCobraMultiCanvas==null)return;int w=mCobraMultiCanvas.getWidth(),h=mCobraMultiCanvas.getHeight();if(w<=0||h<=0)return;ArrayList<CobraVideoTile> tiles=mCobraTiles.values();
    int enlarged=mCobraMultiEnlargedKey.isEmpty()?-1:cobraMultiIndex(mCobraMultiEnlargedKey);if(enlarged<0)mCobraMultiEnlargedKey="";
    for(int i=0;i<tiles.size();i++){int[] rect=CobraMultiLayoutPolicy.rect(i,tiles.size(),w,h,enlarged);cobraPosition(tiles.get(i).view,rect[0],rect[1],rect[2],rect[3]);}
  }''')

    release=member(s,'releaseMulti')
    release=once(release,'  private void releaseMulti() {\n','  private void releaseMulti() {\n    mCobraMultiEnlargedKey="";mCobraMultiFullscreenActive=false;mCobraMultiFullscreenKey="";\n','Multi-View state reset')
    s=replace_member(s,'releaseMulti',release)

    # Tile focus language and strong TV focus.
    tile_ctor=member(s,'CobraVideoTile','ctor')
    tile_ctor=once(tile_ctor,
      'view.setFocusable(true);view.setFocusableInTouchMode(false);view.setOnClickListener',
      'view.setFocusable(true);view.setFocusableInTouchMode(false);cobraPolishFocusable(view);view.setContentDescription(c.name+" Multi-View screen; Select for audio, Menu for actions");view.setOnClickListener',
      'Multi-View tile remote polish')
    s=replace_member(s,'CobraVideoTile',tile_ctor,'ctor')

    # Back returns from promoted Multi-View without releasing other tiles.
    back=member(s,'onBackPressed')
    back=once(back,
      '    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions()||closeCobraExperienceDrawer())return;\n    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}',
      '    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions()||closeCobraExperienceDrawer())return;\n    if(mCobraMultiFullscreenActive&&mPlayerOverlay!=null){cobraReturnToMultiFromFullscreen();return;}\n    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}',
      'Back returns Multi-View')
    s=replace_member(s,'onBackPressed',back)

    # Explicit three-zone player focus graph plus Return Multi behavior.
    chrome=member(s,'cobraBuildPlayerChrome')
    chrome=once(chrome,
      '    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);',
      '    LinearLayout header=new LinearLayout(this);mCobraTvPlayerHeader=header;header.setGravity(Gravity.CENTER_VERTICAL);',
      'player header owner')
    chrome=once(chrome,
      '    header.addView(cobraIcon("back","Return to preview",true,v->closeFullscreenToCobraView()),new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.5",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.6",48))));',
      '    CobraIconButton headerBack=cobraIcon("back",mCobraMultiFullscreenActive?"Return to Multi-View":"Return to preview",true,v->closeFullscreenToCobraView());headerBack.setTag("cobra_tv_player_header_back");header.addView(headerBack,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.5",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.6",48))));',
      'player header back tag')
    chrome=once(chrome,
      '    header.addView(cobraIcon(mPlaying!=null&&mFavorites.contains(mPlaying.id)?"favorite_on":"favorite","Favorite",true,v->{if(mPlaying!=null){toggleFavorite(mPlaying);((CobraIconButton)v).icon(mFavorites.contains(mPlaying.id)?"favorite_on":"favorite");}}),new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.10",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.11",48))));',
      '    CobraIconButton headerFavorite=cobraIcon(mPlaying!=null&&mFavorites.contains(mPlaying.id)?"favorite_on":"favorite","Favorite",true,v->{if(mPlaying!=null){toggleFavorite(mPlaying);((CobraIconButton)v).icon(mFavorites.contains(mPlaying.id)?"favorite_on":"favorite");}});headerFavorite.setTag("cobra_tv_player_header_favorite");header.addView(headerFavorite,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.10",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.11",48))));',
      'player header favorite tag')
    chrome=once(chrome,
      '    header.addView(cobraIcon("lock","Lock controls",true,v->lockCobraPlayer()),new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.12",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.13",48))));chrome.addView(header,new LinearLayout.LayoutParams(-1,-2));',
      '    CobraIconButton headerLock=cobraIcon("lock","Lock controls",true,v->lockCobraPlayer());headerLock.setTag("cobra_tv_player_header_lock");header.addView(headerLock,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.12",48)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.13",48))));chrome.addView(header,new LinearLayout.LayoutParams(-1,-2));',
      'player header lock tag')
    chrome=once(chrome,
      '    LinearLayout transport=new LinearLayout(this);transport.setGravity(Gravity.CENTER);',
      '    LinearLayout transport=new LinearLayout(this);mCobraTvPlayerTransport=transport;transport.setGravity(Gravity.CENTER);',
      'player transport owner')
    chrome=once(chrome,'    CobraIconButton prev=cobraIcon("prev","Previous channel",true,v->stepChannel(-1));',
      '    CobraIconButton prev=cobraIcon("prev","Previous channel",true,v->stepChannel(-1));prev.setTag("cobra_tv_player_transport_prev");',
      'transport prev tag')
    chrome=once(chrome,'    CobraIconButton next=cobraIcon("next","Next channel",true,v->stepChannel(1));',
      '    CobraIconButton next=cobraIcon("next","Next channel",true,v->stepChannel(1));next.setTag("cobra_tv_player_transport_next");\n    if(mCobraMultiFullscreenActive){prev.setEnabled(false);next.setEnabled(false);}',
      'transport next / promoted lock')
    oldtools='''    LinearLayout tools=new LinearLayout(this);String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display","Multi-View","More"};
    for(int i=0;i<4;i++){final int action=i;CobraIconButton b=cobraIcon(glyphs[i],labels[i],true,v->{if(action==0)showCobraPlayerDrawer();else if(action==1)showCobraAspectPicker();else if(action==2)beginMultiView();else showPlayerSettingsDrawer();});b.caption(labels[i]);if(action==1)b.setTag("cobra_player_aspect_anchor");if(action==3)b.setTag("cobra_player_options_anchor");tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",52)),1));}'''
    newtools='''    LinearLayout tools=new LinearLayout(this);mCobraTvPlayerTools=tools;String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display",mCobraMultiFullscreenActive?"Return Multi":"Multi-View","More"};
    for(int i=0;i<4;i++){final int action=i;CobraIconButton b=cobraIcon(glyphs[i],labels[i],true,v->{if(action==0){if(mCobraMultiFullscreenActive)toast("Return to Multi-View to change screens");else showCobraPlayerDrawer();}else if(action==1)showCobraAspectPicker();else if(action==2){if(mCobraMultiFullscreenActive)cobraReturnToMultiFromFullscreen();else beginMultiView();}else showPlayerSettingsDrawer();});b.caption(labels[i]);b.setTag(action==0?"cobra_tv_player_tool_channels":action==1?"cobra_tv_player_tool_display":action==2?"cobra_tv_player_tool_multi":"cobra_tv_player_tool_more");tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",58)),1));}'''
    chrome=once(chrome,oldtools,newtools,'TV player tools graph')
    s=replace_member(s,'cobraBuildPlayerChrome',chrome)

    # Player D-pad now routes between header/transport/timeline/footer instead of relying on Android guesswork.
    s=replace_member(s,'cobraTvHandlePlayerKey',r'''  private boolean cobraTvHandlePlayerKey(KeyEvent event){
    if(event.getAction()!=KeyEvent.ACTION_DOWN||mPlayerOverlay==null||mCobraPlayerLocked)return false;
    int code=event.getKeyCode();
    if(mCobraPlayerDrawer!=null){if(code==KeyEvent.KEYCODE_BACK||code==KeyEvent.KEYCODE_DPAD_LEFT){closeCobraPlayerDrawer();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}return false;}
    if(mCobraMultiPicker!=null){if(code==KeyEvent.KEYCODE_BACK){closeCobraMultiPicker(false);showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}return false;}
    if(mCobraActionSheet!=null){if(code==KeyEvent.KEYCODE_BACK){closeCobraActionSheet();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}return false;}
    if(code==KeyEvent.KEYCODE_MENU){if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return true;}showCobraPlayerDrawer();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE){toggleCobraPlayerPlayPause();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_REWIND){cobraRewindLive(30000L);return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_FAST_FORWARD){if(!cobraTvNudgeTimeline(1))cobraGoLive();return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_UP&&!mCobraMultiFullscreenActive){stepChannel(1);return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_DOWN&&!mCobraMultiFullscreenActive){stepChannel(-1);return true;}
    if(code==KeyEvent.KEYCODE_BACK){if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE){cobraTvHidePlayerChrome();return true;}return false;}
    View focus=getCurrentFocus();boolean inChrome=mPlayerChrome!=null&&cobraTvViewInside(mPlayerChrome,focus);
    if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE&&inChrome&&(code==KeyEvent.KEYCODE_DPAD_UP||code==KeyEvent.KEYCODE_DPAD_DOWN))
      if(cobraTvPlayerFocusGraph(code))return true;
    if(code==KeyEvent.KEYCODE_DPAD_CENTER||code==KeyEvent.KEYCODE_ENTER||code==KeyEvent.KEYCODE_DPAD_UP||code==KeyEvent.KEYCODE_DPAD_DOWN||code==KeyEvent.KEYCODE_DPAD_LEFT||code==KeyEvent.KEYCODE_DPAD_RIGHT){
      if(mPlayerChrome==null||mPlayerChrome.getVisibility()!=View.VISIBLE||!inChrome){showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}
    }
    return false;
  }''')

    # Player settings respects reversible promoted Multi-View.
    settings=member(s,'showPlayerSettingsDrawer')
    settings=once(settings,
'''    rows.addView(cobraSheetRow("source","Manage sources","Leaves this player",false,true,()->{closePlayer();stopCobraPreview();mCobraInternalScreen="internal";showSources();}));
    rows.addView(cobraSheetRow("close","Close player","Stop playback and return to browsing",true,true,()->{mCobraPreviewAutoplayAllowed=false;closePlayer();showCobraPrimaryView();cobraUpdatePlaybackLabels();}));''',
'''    rows.addView(cobraSheetRow("source","Manage sources","Leaves this player",false,true,()->{if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();releaseMulti();}else closePlayer();stopCobraPreview();mCobraInternalScreen="internal";showSources();}));
    rows.addView(cobraSheetRow("close",mCobraMultiFullscreenActive?"Return to Multi-View":"Close player",mCobraMultiFullscreenActive?"Keep every Multi-View screen running":"Stop playback and return to browsing",true,true,()->{if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return;}mCobraPreviewAutoplayAllowed=false;closePlayer();showCobraPrimaryView();cobraUpdatePlaybackLabels();}));''',
      'Player settings Multi-View return')
    s=replace_member(s,'showPlayerSettingsDrawer',settings)

    # source-level safety: Full screen action may not call the destructive multiToSingle path.
    req('multiToSingle();' not in member(s,'showCobraMultiTileActions'),'Tile Full screen still tears down Multi-View')
    req('releaseMulti();' not in member(s,'cobraPromoteMultiTileFullscreen'),'Fullscreen promotion releases Multi-View')
    req('cobraDisposePlayer' not in member(s,'cobraPromoteMultiTileFullscreen'),'Fullscreen promotion disposes player')
    req('cobraDisposePlayer' not in member(s,'cobraReturnToMultiFromFullscreen'),'Multi-View return disposes player')
    req('mCobraGuideDirectory.requestFocus();return;' not in s,'Invisible TV directory focus path regressed')
    path.write_text(s)
    return hb(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103221 TV parent')
    req(receipt.get('tv_variant') is True and receipt.get('tv_target_abi')=='armeabi-v7a','Expected ARMv7 TV parent')
    req(receipt.get('tv_remote_ui') is True,'Expected 2103221 remote UI parent')
    activity=shell/ACT;gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,gradle):req(p.is_file(),'Missing '+str(p))
    activity_before,activity_after=patch_activity(activity)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode');g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)

    for rel in (ACT,SOURCE+'build.gradle.in'):
      req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_player_focus_graph=True,tv_full_canvas=True,tv_preview_fullscreen_seamless=True,
      tv_black_handoff_guard=True,tv_group_fit_polished=True,
      multiview_search_add=True,multiview_pause_resume=True,multiview_enlarge=True,
      multiview_fullscreen_reversible=True,multiview_fullscreen_player_recreated=False,
      multiview_back_returns=True,multiview_other_tiles_preserved=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit222').mkdir(exist_ok=True)
    Path('audit222/tv-player-multiview-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':activity_before,'activity_after_sha256':activity_after,
      'marker':'cobra_tv_player_multiview_2103222','mobile_fold_untouched':True,
      'full_canvas':True,'player_three_zone_focus':True,'top_controls_remote':True,'bottom_controls_remote':True,
      'preview_fullscreen_surface_guard':True,'guide_rebuild_on_normal_fullscreen_return':False,
      'group_overlay_full_canvas_fit':True,
      'multiview_search_add':True,'multiview_pause_resume':True,'multiview_enlarge':True,
      'multiview_fullscreen_reversible':True,'multiview_other_tiles_released':False,
      'multiview_player_recreated_on_fullscreen':False,'native_engine_rebuilt':False,
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103222 TV player/Multi-View/full-canvas source applied over exact locked 2103221')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
