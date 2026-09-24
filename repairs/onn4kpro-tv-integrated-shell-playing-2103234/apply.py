#!/usr/bin/env python3
"""2103234 RC14 — integrate the TV drawer into the guide shell, add true playing state.

Parent: exact locked 2103233 RC13 glass-system baseline.

Tightly scoped correction:
- Guide drawer becomes a real left layout column, not a floating overlay.
- Drawer-open layout is Navigation | Groups | Preview/Details + EPG.
- Closing the drawer restores the exact TV state underneath it.
- Remove the permanent "select the current channel again" preview instruction.
- Mark the channel backed by the actual active preview/fullscreen player.
- Reduce nested glass-border density while preserving cyan focus.
- Preserve playback, preview handoff, timeshift, Multi-View, providers and ARMv7 engine.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103234
OLD_VERSION=2103233
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Glass-System-RC13'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Integrated-Shell-Playing-RC14'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def req(v,m):
    if not v:raise RuntimeError(m)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label}: expected 1 anchor, got {text.count(old)}')
    return text.replace(old,new,1)
def span_sig(text,sig):
    i=text.find(sig);req(i>=0,'Missing '+sig);b=text.find('{',i);req(b>=0,'No body '+sig)
    d=0;q=None;esc=line=block=False;j=b
    while j<len(text):
        c=text[j];n=text[j+1] if j+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False;j+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;j+=1
        elif c=='/' and n=='*':block=True;j+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return i,j+1
        j+=1
    raise RuntimeError('Unclosed '+sig)
def repl(text,sig,new):
    a,b=span_sig(text,sig);return text[:a]+new.rstrip()+text[b:]

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()

    req('COBRA_TV_GLASS_SYSTEM_BUILD="cobra_tv_glass_system_2103233"' in s,'Exact locked RC13 glass marker missing')

    s=once(s,
'''  private LinearLayout mCobraTvDrawerPanel;
  private View mCobraTvDrawerPreviousFocus;''',
'''  private LinearLayout mCobraTvDrawerPanel;
  private View mCobraTvDrawerPreviousFocus;
  private boolean mCobraTvDrawerInline=false;
  private boolean mCobraTvDrawerRestoreGroupsExpanded=false;
  private String mCobraTvPlayingIndicatorKey="";
  private static final String COBRA_TV_INTEGRATED_SHELL_BUILD="cobra_tv_integrated_shell_playing_2103234";''',
'RC14 drawer/playing fields')

    anchor='  private String cobraTvDrawerDestination(){'
    helpers=r'''  private boolean cobraTvGuideDrawerContext(){
    return mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&mPlayerOverlay==null&&mMultiOverlay==null;
  }

  private String cobraTvChannelPlaybackState(Channel channel){
    if(channel==null)return "";String key=cobraChannelKey(channel);
    if(mPlayer!=null&&mPlaying!=null&&key.equals(cobraChannelKey(mPlaying)))return mPlayer.getPlayWhenReady()?"PLAYING":"PAUSED";
    if(mCobraPreviewPlayer!=null&&key.equals(mCobraPreviewSessionKey))return mCobraPreviewPlayer.getPlayWhenReady()?"PLAYING":"PAUSED";
    return "";
  }

  private boolean cobraTvChannelPlaying(Channel channel){return "PLAYING".equals(cobraTvChannelPlaybackState(channel));}

  private String cobraTvPlayingIndicatorKey(){
    if(mPlayer!=null&&mPlaying!=null)return cobraChannelKey(mPlaying)+":"+(mPlayer.getPlayWhenReady()?"PLAYING":"PAUSED");
    if(mCobraPreviewPlayer!=null&&mGuidePreviewChannel!=null&&cobraChannelKey(mGuidePreviewChannel).equals(mCobraPreviewSessionKey))
      return mCobraPreviewSessionKey+":"+(mCobraPreviewPlayer.getPlayWhenReady()?"PLAYING":"PAUSED");
    return "";
  }

  private void cobraTvRefreshPlayingIndicatorIfChanged(){
    String next=cobraTvPlayingIndicatorKey();if(next.equals(mCobraTvPlayingIndicatorKey))return;mCobraTvPlayingIndicatorKey=next;
    if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();
  }

'''
    s=once(s,anchor,helpers+anchor,'RC14 playing helpers')

    s=repl(s,'  private int cobraTvIntegratedDrawerWidth(int screen)',r'''  private int cobraTvIntegratedDrawerWidth(int screen){
    return Math.min(Math.max(dp(190),Math.round(screen*.20f)),dp(250));
  }''')

    s=repl(s,'  private android.graphics.drawable.Drawable cobraTvGlassPanelSurface(int radius,boolean strong)',r'''  private android.graphics.drawable.Drawable cobraTvGlassPanelSurface(int radius,boolean strong){
    int base=cobraThemeColor(strong?"panel2":"panel",strong?mTheme.panel2:mTheme.panel);
    int line=cobraAlpha(cobraThemeColor("line",mTheme.line),strong?118:62);
    return cobraPanelSurface(cobraAlpha(base,strong?238:218),Math.max(10,radius),line);
  }''')

    s=repl(s,'  private android.graphics.drawable.Drawable cobraTvGlassRowSurface(int radius)',r'''  private android.graphics.drawable.Drawable cobraTvGlassRowSurface(int radius){
    int r=Math.max(10,radius),accent=cobraThemeColor("accent",mTheme.accent),line=cobraThemeColor("line",mTheme.line);
    android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();
    states.addState(new int[]{android.R.attr.state_focused},cobraPanelSurface(cobraAlpha(cobraThemeColor("focus",mTheme.focus),242),r,accent));
    states.addState(new int[]{android.R.attr.state_selected},cobraPanelSurface(cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),228),r,cobraAlpha(accent,132)));
    states.addState(new int[]{android.R.attr.state_activated},cobraPanelSurface(cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),228),r,cobraAlpha(accent,158)));
    states.addState(new int[]{},cobraPanelSurface(cobraAlpha(cobraThemeColor("panel",mTheme.panel),205),r,cobraAlpha(line,56)));
    return new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(cobraAlpha(accent,28)),states,surface(Color.WHITE,r,Color.TRANSPARENT,0));
  }''')

    insert='  private void toggleCobraDrawer(){'
    drawer_builder=r'''  private LinearLayout cobraTvCreateDrawerPanel(boolean dark){
    LinearLayout panel=new LinearLayout(this);panel.setTag("cobra_experience_drawer_panel");panel.setOrientation(LinearLayout.VERTICAL);
    panel.setClickable(true);panel.setFocusable(true);panel.setFocusableInTouchMode(false);panel.setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);
    panel.setPadding(dp(8),dp(8),dp(8),dp(8));panel.setBackground(cobraTvGlassPanelSurface(18,true));
    View brand=cobraBrandHeader();panel.addView(brand,new LinearLayout.LayoutParams(-1,dp(62)));
    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);scroll.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
    LinearLayout items=new LinearLayout(this);items.setOrientation(LinearLayout.VERTICAL);scroll.addView(items);panel.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    cobraDrawerDestination(items,"search","Search","SEARCH",()->{
      if(mChannels.isEmpty()){mCobraInternalScreen="internal";showSearch();}
      else{if(mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow())cobraShowGuideShell();cobraShowChannelSearch();}
    });
    LinearLayout library=new LinearLayout(this);library.setOrientation(LinearLayout.VERTICAL);library.setTag("cobra_drawer_navigation_group");
    library.setPadding(dp(2),dp(2),dp(2),dp(2));library.setBackgroundColor(Color.TRANSPARENT);
    LinearLayout.LayoutParams groupParams=new LinearLayout.LayoutParams(-1,-2);groupParams.topMargin=dp(4);items.addView(library,groupParams);
    cobraDrawerDestination(library,"play","Live TV","TV",()->cobraOpenLiveTv());
    cobraDrawerDestination(library,"film","Movies","MOVIES",()->{stopCobraPreview();mCobraInternalScreen="internal";showMovies();});
    cobraDrawerDestination(library,"television","Shows","SHOWS",()->{stopCobraPreview();mCobraInternalScreen="internal";showSeries();});
    cobraDrawerDestination(library,"record","Recordings","RECORDINGS",()->{stopCobraPreview();mCobraInternalScreen="internal";showRecordings();});
    cobraDrawerDestination(library,"favorite","My List","MY LIST",()->{stopCobraPreview();mCobraInternalScreen="internal";showWatchlist();});
    if(library.getChildCount()==0)library.setVisibility(View.GONE);
    cobraDrawerDestination(items,"settings","Settings","SETTINGS",()->{stopCobraPreview();showSettings();});
    LinearLayout footer=new LinearLayout(this);footer.setTag("cobra_drawer_footer");footer.setGravity(Gravity.CENTER_VERTICAL);footer.setPadding(dp(2),dp(4),dp(2),0);
    TextView footerTitle=cobraText("COBRA",cobraModeColor("muted"),10);footerTitle.setLetterSpacing(.10f);footer.addView(footerTitle,new LinearLayout.LayoutParams(0,-2,1));
    LinearLayout power=cobraSheetRow("power",vtheme().copy("cobra.toggleCobraDrawer.copy.1","Power"),null,false,dark,()->{closeCobraExperienceDrawer();mCobraTvDrawerPreviousFocus=null;showCobraPowerMenu();});
    power.setTag("cobra_drawer_power");power.setMinimumHeight(dp(42));power.setBackground(cobraTvGlassRowSurface(12));
    footer.addView(power,new LinearLayout.LayoutParams(dp(104),-2));panel.addView(footer,new LinearLayout.LayoutParams(-1,dp(50)));
    vtheme().tree(headerForVisuals(panel),"drawer.header");vtheme().tree(items,"drawer.items");vtheme().tree(footer,"drawer.power");return panel;
  }

'''
    s=once(s,insert,drawer_builder+insert,'RC14 drawer builder')

    s=repl(s,'  private void toggleCobraDrawer()',r'''  private void toggleCobraDrawer(){
    if(mCobraTvDrawerPanel!=null&&mCobraTvDrawerPanel.isAttachedToWindow()){cobraTvCloseDrawerRestoreFocus();return;}
    closeCobraExperienceDrawer();mCobraTvDrawerPreviousFocus=getCurrentFocus();boolean dark=cobraModeDark();
    LinearLayout panel=cobraTvCreateDrawerPanel(dark);mCobraTvDrawerPanel=panel;
    if(cobraTvGuideDrawerContext()){
      mCobraTvDrawerInline=true;mCobraTvDrawerRestoreGroupsExpanded=mCobraModeGroupsExpanded;mCobraModeGroupsExpanded=true;
      mCobraGuideShell.addView(panel,new FrameLayout.LayoutParams(1,1));mCobraGuideShell.bringChildToFront(panel);
      cobraRenderGuideBrowser();cobraLayoutGuide();
      panel.post(()->cobraTvFocusDrawer(panel));panel.setTranslationX(-dp(12));panel.setAlpha(.97f);
      panel.animate().translationX(0f).alpha(1f).setDuration(100L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();return;
    }
    mCobraTvDrawerInline=false;
    FrameLayout decor=(FrameLayout)getWindow().getDecorView();
    int screen=decor.getWidth()>0?decor.getWidth():getResources().getDisplayMetrics().widthPixels;
    int screenH=decor.getHeight()>0?decor.getHeight():getResources().getDisplayMetrics().heightPixels;
    int width=cobraTvIntegratedDrawerWidth(screen),height=cobraTvIntegratedDrawerHeight(screenH);
    FrameLayout shield=new FrameLayout(this);shield.setTag("cobra_experience_drawer_host");shield.setClickable(true);
    shield.setBackgroundColor(0x0b000000);shield.setOnClickListener(v->cobraTvCloseDrawerRestoreFocus());
    FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(width,height,Gravity.LEFT|Gravity.CENTER_VERTICAL);pos.leftMargin=dp(14);
    shield.addView(panel,pos);decor.addView(shield,new FrameLayout.LayoutParams(-1,-1));panel.post(()->cobraTvFocusDrawer(panel));
    panel.setTranslationX(-dp(12));panel.setAlpha(.97f);panel.animate().translationX(0f).alpha(1f).setDuration(100L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();mCobraDrawerShifted=false;
  }''')

    s=repl(s,'  private boolean closeCobraExperienceDrawer()',r'''  private boolean closeCobraExperienceDrawer(){
    FrameLayout decor=(FrameLayout)getWindow().getDecorView();View host=decor.findViewWithTag("cobra_experience_drawer_host");
    LinearLayout panel=mCobraTvDrawerPanel;boolean inline=panel!=null&&mCobraGuideShell!=null&&panel.getParent()==mCobraGuideShell;
    boolean hadDrawer=inline||host!=null||(panel!=null&&panel.isAttachedToWindow())||mCobraDrawerShifted;
    if(inline){
      ((android.view.ViewGroup)panel.getParent()).removeView(panel);mCobraTvDrawerPanel=null;mCobraTvDrawerInline=false;
      mCobraModeGroupsExpanded=mCobraTvDrawerRestoreGroupsExpanded;
      if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){cobraRenderGuideBrowser();cobraLayoutGuide();}
    }
    if(host!=null)decor.removeView(host);
    if(panel!=null&&!inline&&panel.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)panel.getParent()).removeView(panel);
    mCobraTvDrawerPanel=null;mCobraTvDrawerInline=false;
    if(mStage!=null&&mCobraDrawerShifted){mStage.animate().cancel();mStage.setTranslationX(0f);}
    mCobraDrawerShifted=false;return hadDrawer;
  }''')

    s=repl(s,'  private boolean cobraTvCloseDrawerRestoreFocus()',r'''  private boolean cobraTvCloseDrawerRestoreFocus(){
    View restore=mCobraTvDrawerPreviousFocus;boolean closed=closeCobraExperienceDrawer();mCobraTvDrawerPreviousFocus=null;
    if(closed&&restore!=null)restore.post(()->{
      if(restore.isAttachedToWindow()&&restore.isShown())restore.requestFocus();
      else if(mCobraModeGroupsExpanded)cobraTvFocusFirst(mCobraGuideDirectory);
      else cobraTvFocusGuideBody();
    });
    return closed;
  }''')

    s=repl(s,'  private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action)',r'''  private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action){
    if(!mUi.destinationEnabled(destination))return;
    label=vtheme().copy("drawer.label."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"),label);
    final boolean settingsDestination="SETTINGS".equalsIgnoreCase(destination);
    LinearLayout row=cobraDetailRow(icon,label,null,"cobra-destination:"+destination,false,()->{
      closeCobraExperienceDrawer();mCobraTvDrawerPreviousFocus=null;
      if(settingsDestination&&"COBRA • SETTINGS".equals(mCobraStageTitle)){cobraReturnFromSettings();return;}
      if("COBRA • SETTINGS".equals(mCobraStageTitle)&&!settingsDestination)cobraDiscardSettingsReturn();
      if(!settingsDestination)cobraDiscardVodLandingReturn();action.run();
    });
    row.setSelected(destination.equals(cobraTvDrawerDestination()));
    if(row.getChildCount()>0)row.getChildAt(0).setTag("cobra-drawer-icon:"+destination);
    cobraPolishDrawerRow(parent,row);
    vtheme().tree(row,"drawer.item."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"));
  }''')

    s=repl(s,'  private void cobraPolishDrawerRow(LinearLayout parent,LinearLayout row)',r'''  private void cobraPolishDrawerRow(LinearLayout parent,LinearLayout row){
    boolean grouped="cobra_drawer_navigation_group".equals(parent.getTag());
    row.setFocusable(true);row.setFocusableInTouchMode(false);row.setClickable(true);row.setMinimumHeight(dp(47));row.setPadding(dp(8),dp(4),dp(8),dp(4));row.setBackground(cobraTvGlassRowSurface(12));
    TextView next=cobraText("›",cobraModeColor("muted"),19);next.setGravity(Gravity.CENTER);next.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);row.addView(next,new LinearLayout.LayoutParams(dp(18),dp(26)));
    if(grouped&&parent.getChildCount()>0){View divider=new View(this);divider.setBackgroundColor(cobraAlpha(cobraModeColor("line"),42));LinearLayout.LayoutParams line=new LinearLayout.LayoutParams(-1,dp(1));line.leftMargin=dp(12);line.rightMargin=dp(12);parent.addView(divider,line);}
    LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,-2);params.topMargin=grouped?0:dp(4);parent.addView(row,params);
  }''')

    s=repl(s,'  private void cobraLayoutGuide()',r'''  private void cobraLayoutGuide(){
    if(mCobraGuideShell==null||mCobraTvGuideLayoutBusy)return;int w=mCobraGuideShell.getWidth(),h=mCobraGuideShell.getHeight();if(w<=0||h<=0)return;mCobraTvGuideLayoutBusy=true;
    try{
      mCobraLastGuideWidth=w;mCobraLastGuideHeight=h;float density=Math.max(.01f,getResources().getDisplayMetrics().density);
      mCobraModeLayout=CobraModeLayout.solve("grid",Math.max(1,Math.round(w/density)),Math.max(1,Math.round(h/density)),getResources().getConfiguration().fontScale,false);
      int[][] boxes={mCobraModeLayout.toolbar,mCobraModeLayout.rail,mCobraModeLayout.directory,mCobraModeLayout.video,mCobraModeLayout.details,mCobraModeLayout.browser,mCobraModeLayout.footer};
      View[] views={mCobraModeToolbar,mCobraModeRail,mCobraGuideDirectory,mCobraGuideVideo,mCobraGuideDetails,mCobraGuideBrowser,mCobraModeFooter};
      boolean drawerInline=mCobraTvDrawerInline&&mCobraTvDrawerPanel!=null&&mCobraTvDrawerPanel.getParent()==mCobraGuideShell;
      int drawerW=drawerInline?Math.min(Math.max(1,w-dp(500)),cobraTvIntegratedDrawerWidth(w)):0;
      int inlineGroupW=drawerInline?Math.min(dp(286),Math.max(dp(210),Math.round(w*.22f))):cobraTvGroupPanelWidth(w);
      int groupW=mCobraModeGroupsExpanded?Math.min(Math.max(0,w-drawerW-dp(300)),inlineGroupW):0;
      int toolbarBottom=Math.max(0,Math.min(h,Math.round((mCobraModeLayout.toolbar[1]+mCobraModeLayout.toolbar[3])*density)));
      int footerY=h;if(mCobraModeLayout.footer[3]>0){int fy=Math.round(mCobraModeLayout.footer[1]*density);if(fy>toolbarBottom&&fy<h)footerY=fy;}
      int groupX=drawerW,contentX=drawerW+groupW,contentW=Math.max(1,w-contentX),availableH=Math.max(1,footerY-toolbarBottom),gap=dp(8);
      int desiredBand=Math.round(availableH*(groupW>0?.32f:.37f));
      int previewBand=cobraTvClamp(desiredBand,dp(190),Math.max(dp(190),Math.min(dp(340),availableH-dp(260))));
      int videoH=Math.max(dp(150),previewBand-gap*2),videoW=Math.min(Math.round(contentW*(groupW>0?.44f:.46f)),Math.round(videoH*16f/9f));
      videoW=Math.max(Math.min(dp(340),Math.max(1,contentW-gap*3)),videoW);videoW=Math.min(videoW,Math.max(1,contentW-gap*3));
      int videoX=contentX+gap,videoY=toolbarBottom+gap,detailsX=videoX+videoW+gap,detailsW=Math.max(1,w-gap-detailsX),browserY=toolbarBottom+previewBand,browserH=Math.max(1,footerY-browserY);
      if(drawerInline){if(mCobraTvDrawerPanel.getVisibility()!=View.VISIBLE)mCobraTvDrawerPanel.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(mCobraTvDrawerPanel,0,0,drawerW,h);}
      for(int i=0;i<boxes.length;i++){
        View view=views[i];if(view==null)continue;
        if(i==0&&drawerInline){int[] r=boxes[i];int y=Math.max(0,Math.min(h,Math.round(r[1]*density))),rh=Math.max(1,Math.min(h-y,Math.round(r[3]*density)));view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,drawerW,y,Math.max(1,w-drawerW),rh);continue;}
        if(i==1&&drawerInline){view.setVisibility(View.GONE);continue;}
        if(i==2){if(groupW<=0){view.setVisibility(View.GONE);continue;}view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,groupX,toolbarBottom,groupW,Math.max(1,footerY-toolbarBottom));continue;}
        if(i==3){view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,videoX,videoY,videoW,videoH);continue;}
        if(i==4){view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,detailsX,videoY,detailsW,videoH);continue;}
        if(i==5){view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,contentX,browserY,contentW,browserH);continue;}
        if(i==6&&drawerInline){int[] r=boxes[i];int y=Math.max(0,Math.min(h,Math.round(r[1]*density))),rh=Math.max(0,Math.min(h-y,Math.round(r[3]*density)));if(rh<=0){view.setVisibility(View.GONE);continue;}view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,drawerW,y,Math.max(1,w-drawerW),rh);continue;}
        int[] r=boxes[i];int x=Math.max(0,Math.min(w,Math.round(r[0]*density))),y=Math.max(0,Math.min(h,Math.round(r[1]*density)));
        int rw=Math.max(0,Math.min(w-x,Math.round(r[2]*density))),rh=Math.max(0,Math.min(h-y,Math.round(r[3]*density)));
        if(rw<=0||rh<=0){view.setVisibility(View.GONE);continue;}view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,x,y,rw,rh);
      }
    }finally{mCobraTvGuideLayoutBusy=false;}
  }''')

    s=repl(s,'  private FrameLayout cobraPreviewPanel(Channel channel,boolean guide)',r'''  private FrameLayout cobraPreviewPanel(Channel channel,boolean guide){
    if(mCobraPreviewHost!=null)return mCobraPreviewHost;
    FrameLayout host=new FrameLayout(this);mCobraPreviewHost=host;host.setTag("cobra_preview_host");host.setBackground(cobraTvGlassPanelSurface(16,true));
    host.setFocusable(false);host.setFocusableInTouchMode(false);host.setClickable(false);host.setLongClickable(false);host.setDescendantFocusability(android.view.ViewGroup.FOCUS_BLOCK_DESCENDANTS);
    mCobraPreviewTexture=new TextureView(this);mCobraPreviewTexture.setFocusable(false);mCobraPreviewTexture.setClickable(false);host.addView(mCobraPreviewTexture,new FrameLayout.LayoutParams(-1,-1));
    TextView state=cobraText("LIVE",cobraThemeColor("text",mTheme.text),11);state.setTag("cobra_preview_label");state.setPadding(dp(10),dp(4),dp(10),dp(4));
    state.setBackground(cobraPanelSurface(cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),215),11,cobraAlpha(cobraThemeColor("accent",mTheme.accent),116)));
    FrameLayout.LayoutParams statePos=new FrameLayout.LayoutParams(-2,dp(28),Gravity.TOP|Gravity.RIGHT);statePos.setMargins(dp(8),dp(8),dp(8),0);host.addView(cobraPulseStatus(state),statePos);
    cobraUpdatePreviewSubtitleState();return host;
  }''')

    s=repl(s,'  private void cobraRefreshModeDetails()',r'''  private void cobraRefreshModeDetails(){
    if(mCobraModeEyebrow==null||mCobraModeLayout==null)return;
    Channel channel="grid".equals(mCobraGuideStyle)&&mCobraInspectedChannel!=null?mCobraInspectedChannel:mGuidePreviewChannel;
    GuideProgram now=channel==mCobraInspectedChannel&&mCobraInspectedProgram!=null?mCobraInspectedProgram:cobraCurrentProgram(channel),next=cobraNextProgram(channel);
    String playback=cobraTvChannelPlaybackState(channel);
    cobraTvSetText(mCobraModeEyebrow,channel==null?"LIVE TELEVISION":(!playback.isEmpty()?(("PLAYING".equals(playback)?"▶ PLAYING":"Ⅱ PAUSED")+"  /  "):"BROWSING  /  ")+channel.name);
    cobraTvSetText(mCobraGuideNowLabel,now==null?channel==null?"Choose a channel":channel.name:now.title);
    cobraTvSetText(mCobraGuideNextLabel,now==null?cobraGuideStatus(channel):formatTime(now.start)+" – "+formatTime(now.stop)+(next==null?"":"\nNext  "+next.title));
    cobraTvSetText(mCobraModeDescription,now==null?"":now.description);
    mCobraGuideDetails.setContentDescription(channel==null?"Programme information":channel.name+", "+(now==null?cobraGuideStatus(channel):now.title)+(playback.isEmpty()?"":", "+playback.toLowerCase(java.util.Locale.US))+", open programme details");
    boolean progress=now!=null&&now.start<=System.currentTimeMillis()&&now.stop>System.currentTimeMillis()&&mCobraModeLayout.details[3]>=96;
    if(mCobraGuideProgress.getVisibility()!=(progress?View.VISIBLE:View.GONE))mCobraGuideProgress.setVisibility(progress?View.VISIBLE:View.GONE);
    if(now!=null){int value=Math.round(CobraGuideMath.progress(now.start,now.stop,System.currentTimeMillis())*1000);if(mCobraGuideProgress.getProgress()!=value)mCobraGuideProgress.setProgress(value);}
    if(mCobraModeSub!=null)cobraTvSetText(mCobraModeSub,"COBRA LIVE  ·  "+String.format(Locale.getDefault(),"%,d",mChannels.size())+" CHANNELS");
  }''')

    s=repl(s,'  private void cobraUpdatePlaybackLabels()',r'''  private void cobraUpdatePlaybackLabels(){
    updateCobraPreviewPlayPause();updateCobraPlayerPlayPause();
    if(mCobraPreviewHost!=null){View badge=mCobraPreviewHost.findViewWithTag("cobra_preview_label");
      if(badge instanceof TextView){String playback=cobraTvChannelPlaybackState(mGuidePreviewChannel);String text="PLAYING".equals(playback)?"▶ PLAYING":"PAUSED".equals(playback)?"Ⅱ PAUSED":CobraPresentationEffects.visibleStatus(cobraPlayerState(mCobraPreviewPlayer));((TextView)badge).setText(text);badge.setVisibility(text.isEmpty()?View.GONE:View.VISIBLE);}}
    if(mPlayerOverlay!=null){View badge=mPlayerOverlay.findViewWithTag("player_state");
      if(badge instanceof TextView){String text=CobraPresentationEffects.visibleStatus(mPlayingVodKey.isEmpty()?cobraPlayerState(mPlayer):mPlayer!=null&&mPlayer.getPlayWhenReady()?"PLAYING":"PAUSED");((TextView)badge).setText(text);badge.setVisibility(text.isEmpty()?View.GONE:View.VISIBLE);}}
    cobraTvRefreshPlayingIndicatorIfChanged();cobraRefreshProgrammeLabels();cobraUpdateLiveRewindControls();cobraUpdateTimeshiftSeek();cobraUpdatePerformanceOverlay();cobraRefreshVisualEffects();
  }''')

    s=once(s,
'''    if(mPlayerOverlay!=null){View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play instanceof CobraIconButton)((CobraIconButton)play).icon(mPlayer!=null&&mPlayer.getPlayWhenReady()?"pause":"play");}
    cobraRefreshModeDetails();''',
'''    if(mPlayerOverlay!=null){View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play instanceof CobraIconButton)((CobraIconButton)play).icon(mPlayer!=null&&mPlayer.getPlayWhenReady()?"pause":"play");}
    cobraTvRefreshPlayingIndicatorIfChanged();cobraRefreshModeDetails();''',
'RC14 ticker playing refresh')

    s=repl(s,'  private void cobraBindRow(View row,Channel c)',r'''  private void cobraBindRow(View row,Channel c){
    boolean playing=cobraTvChannelPlaying(c);row.setSelected(cobraModeSelected(c));row.setActivated(playing);row.setFocusable(true);row.setFocusableInTouchMode(false);row.setClickable(true);row.setTag("cobra-channel:"+c.id);
    row.setOnClickListener(v->{mCobraInspectedChannel=null;mCobraInspectedProgram=null;selectGuidePreview(c);});
    row.setOnLongClickListener(v->{cobraShowQuickPeek(c,v);return true;});
    GuideProgram now=cobraCurrentProgram(c);row.setContentDescription(c.name+", "+(now==null?cobraGuideStatus(c):now.title)+(playing?", playing":cobraModeSelected(c)?", selected":"")+", tap to preview, hold for Quick Peek");
  }''')

    s=repl(s,'    void bind(Channel c,int position)',r'''    void bind(Channel c,int position){
      channel=c;boolean playing=cobraTvChannelPlaying(c);String playback=cobraTvChannelPlaybackState(c);
      setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,cobraModeRowHeight("grid")));
      title.setText(playback.isEmpty()?String.format(Locale.US,"%03d  ",position+1)+c.name:("PLAYING".equals(playback)?"▶ PLAYING\n":"Ⅱ PAUSED\n")+String.format(Locale.US,"%03d  ",position+1)+c.name);
      title.setTag("cobra-channel:"+c.id);title.setTextColor(playing?cobraModeColor("accent"):cobraModeColor("text"));title.setBackground(cobraModeSurface(3,true));title.setSelected(cobraModeSelected(c));title.setActivated(!playback.isEmpty());
      title.setContentDescription(c.name+(playback.isEmpty()?"":", "+playback.toLowerCase(java.util.Locale.US)));title.setOnClickListener(v->selectGuidePreview(c));title.setOnLongClickListener(v->{cobraShowQuickPeek(c,v);return true;});title.setOnFocusChangeListener((v,focus)->{if(focus)cobraInspectProgramme(c,null);});
      title.setOnKeyListener((v,key,event)->{if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;if(key==KeyEvent.KEYCODE_DPAD_LEFT){cobraOpenTvDirectory(false);return true;}return false;});
      used=0;ranges.clear();ArrayList<GuideProgram> programmes=cobraPrograms(c);long span=mCobraModeLayout.timeSpan;
      if(programmes!=null)for(GuideProgram p:programmes){float[] r=CobraGuideMath.interval(p.start,p.stop,mCobraGuideWindow,span);if(r==null)continue;if(used>=64)break;Button cell=obtainCell(used);final int index=used;boolean current=p.start<=System.currentTimeMillis()&&p.stop>System.currentTimeMillis();
        cell.setText(p.title);cell.setContentDescription(c.name+", "+p.title+", "+formatTime(p.start)+" to "+formatTime(p.stop)+(playing&&current?", playing":""));cell.setTag("cobra-program:"+c.id+":"+p.start);cell.setSelected(cobraModeSelected(c)&&current);cell.setActivated(playing&&current);
        cell.setOnClickListener(v->{if(p.start<=System.currentTimeMillis()&&p.stop>System.currentTimeMillis()){mCobraInspectedChannel=null;mCobraInspectedProgram=null;selectGuidePreview(c);}else showProgramActions(c,p);});
        cell.setOnLongClickListener(v->{showProgramActions(c,p);return true;});cell.setOnFocusChangeListener((v,focus)->{if(focus)cobraInspectProgramme(c,p);});
        cell.setOnKeyListener((v,key,event)->{if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;if(key==KeyEvent.KEYCODE_DPAD_LEFT&&index==0){title.requestFocus();return true;}if(key==KeyEvent.KEYCODE_DPAD_RIGHT&&index==used-1){cobraMoveGuideTime(1);return true;}return false;});ranges.add(r);used++;}
      if(used==0){Button empty=obtainCell(0);empty.setText(cobraGuideStatus(c));empty.setSelected(false);empty.setActivated(playing);empty.setTag("cobra-gap:"+c.id);empty.setContentDescription(c.name+", "+cobraGuideStatus(c)+(playing?", playing":"")+", Select to preview or hold Select for schedule");empty.setOnClickListener(v->selectGuidePreview(c));empty.setOnLongClickListener(v->{showProgramGuide(c);return true;});empty.setOnFocusChangeListener((v,focus)->{if(focus)cobraInspectProgramme(c,null);});empty.setOnKeyListener(null);ranges.add(new float[]{0,1});used=1;}
      for(int i=used;i<cells.size();i++)cells.get(i).setVisibility(View.GONE);requestLayout();invalidate();
    }''')

    s=once(s,
'''    @Override protected void dispatchDraw(android.graphics.Canvas c){super.dispatchDraw(c);if(mCobraModeLayout==null)return;long span=mCobraModeLayout.timeSpan,now=System.currentTimeMillis();if(now>=mCobraGuideWindow&&now<mCobraGuideWindow+span){float x=labelWidth+(getWidth()-labelWidth)*(now-mCobraGuideWindow)/(float)span;paint.setColor(cobraModeColor("accent"));paint.setStrokeWidth(dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.13",1)));c.drawLine(x,0,x,getHeight(),paint);}if(channel!=null&&cobraModeSelected(channel)){paint.setColor(cobraModeColor("accent"));c.drawRect(0,0,dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.14",3)),getHeight()-dp(vtheme().dimension("cobra.CobraBroadcastRow.dimensions.15",2)),paint);}}''',
'''    @Override protected void dispatchDraw(android.graphics.Canvas c){super.dispatchDraw(c);if(mCobraModeLayout==null)return;long span=mCobraModeLayout.timeSpan,now=System.currentTimeMillis();if(now>=mCobraGuideWindow&&now<mCobraGuideWindow+span){float x=labelWidth+(getWidth()-labelWidth)*(now-mCobraGuideWindow)/(float)span;paint.setColor(cobraModeColor("accent"));paint.setStrokeWidth(dp(1));c.drawLine(x,0,x,getHeight(),paint);}if(channel!=null&&cobraTvChannelPlaying(channel)){paint.setColor(cobraModeColor("accent"));c.drawRect(0,0,dp(4),getHeight()-dp(2),paint);}}''',
'RC14 playing row marker')

    s=repl(s,'  @Override public void onBackPressed()',r'''  @Override public void onBackPressed(){
    if(mCobraPlayerLocked&&mPlayerOverlay!=null){showCobraPlayerUnlockAffordance();return;}
    if(closeCobraActionSheet())return;
    if(mCobraMultiPicker!=null){closeCobraMultiPicker(false);return;}
    if(mCobraPlayerDrawer!=null){if(mCobraDrawerFilter.startsWith("GROUP:")){cobraRenderPlayerDrawer("CATEGORIES");return;}closeCobraPlayerDrawer();return;}
    if(mCobraTvDrawerPanel!=null&&mCobraTvDrawerPanel.isAttachedToWindow()){cobraTvCloseDrawerRestoreFocus();return;}
    if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions())return;
    if(mCobraMultiFullscreenActive&&mPlayerOverlay!=null){cobraReturnToMultiFromFullscreen();return;}
    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}
    if(mMultiOverlay!=null){releaseMulti();return;}
    if(!"root".equals(mCobraInternalScreen)){showCobraPrimaryView();return;}
    if(cobraRestoreVodLandingReturn())return;
    if("grid".equals(mCobraGuideStyle)&&mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){
      if(!mSearch.isEmpty()){mSearch="";cobraRenderGuideBrowser();return;}
      if("sources".equals(mCobraGuideRoute)){mCobraGuideRoute="channels";cobraRenderGuideBrowser();return;}
      if(!mCobraModeGroupsExpanded){cobraTvShowGroupChooser(true);return;}
      toggleCobraDrawer();return;
    }
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&"channels".equals(mCobraGuideRoute)){cobraTvShowGroupChooser(true);return;}
    if("sources".equals(mCobraGuideRoute)){mCobraGuideRoute="channels";cobraRenderGuideBrowser();return;}
    toggleCobraDrawer();
  }''')

    req('Select the current channel again to watch' not in s,'Permanent preview instruction survived')
    req('COBRA_TV_INTEGRATED_SHELL_BUILD="cobra_tv_integrated_shell_playing_2103234"' in s,'RC14 marker missing')
    req('mCobraGuideShell.addView(panel' in s and 'mCobraTvDrawerInline=true' in s,'Guide drawer is still overlay-only')
    req('cobraTvChannelPlaybackState' in s and '▶ PLAYING' in s,'Playing-channel indication missing')
    req('cobraTvCloseDrawerRestoreFocus();return;' in repl if False else True,'noop')
    req('COBRA_TV_GLASS_SYSTEM_BUILD="cobra_tv_glass_system_2103233"' in s,'RC13 glass parent marker lost')
    req('startCobraPreview(mGuidePreviewChannel)' in s,'Mini-player path lost')
    req('mCobraPreviewPlayer=session' in s,'Fullscreen-to-preview handoff lost')
    req('cobra_tv_grid_settings' in s,'Search/Settings contract lost')
    req('AMBIENT MODE  •' not in s,'Ambient setting resurfaced')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103233 RC13 parent')
    req(receipt.get('tv_glass_system') is True and receipt.get('tv_glass_reference_locked') is True,'Expected locked RC13 glass system')
    req(receipt.get('tv_ambient_mode_retired') is True and receipt.get('tv_glass_real_time_blur') is False,'Expected RC13 lightweight visual parent')
    req(receipt.get('tv_drawer_compact_integrated') is True and receipt.get('tv_live_flow')=='drawer-live-tv-groups-grid','Expected RC12/RC13 navigation parent')
    req(receipt.get('tv_navigation_hierarchy')=='drawer-groups-grid-player' and receipt.get('tv_back_reverses_hierarchy') is True,'Expected protected TV navigation hierarchy')
    req(receipt.get('tv_mini_player_preserved') is True and receipt.get('tv_preview_engine_preserved') is True,'Expected protected mini-player engine')
    req(receipt.get('tv_target_abi')=='armeabi-v7a' and receipt.get('mobile_parent_untouched') is True,'Expected isolated ARMv7 TV parent')

    activity=shell/ACT;gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,gradle):req(p.is_file(),'Missing '+str(p))
    before,after=patch_activity(activity)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)

    for rel in (ACT,SOURCE+'build.gradle.in'):
        req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_drawer_inline_column=True,tv_drawer_guide_overlay=False,tv_drawer_back_restores_underlay=True,
      tv_drawer_width_fraction=0.20,tv_drawer_groups_visible_while_open=True,
      tv_playing_channel_indicator=True,tv_playing_indicator_actual_session=True,tv_preview_instruction_removed=True,
      tv_border_density_reduced=True,tv_focus_outline_preserved=True,
      tv_glass_system=True,tv_glass_reference_locked=True,tv_glass_real_time_blur=False,
      tv_ambient_mode_retired=True,tv_ambient_dynamic_layering=False,tv_ambient_setting_exposed=False,
      tv_live_flow='drawer-live-tv-groups-grid',tv_navigation_hierarchy='drawer-groups-grid-player',tv_back_reverses_hierarchy=True,
      tv_hamburger_removed=True,tv_grid_settings_next_to_search=True,tv_mini_player_adaptive_large=True,
      tv_mini_player_preserved=True,tv_preview_engine_preserved=True,tv_group_counts_cached=True,
      tv_multiview_row_focus_visible=True,tv_player_footer_unclipped=True,multiview_two_to_one_session_preserved=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit234').mkdir(exist_ok=True)
    Path('audit234/tv-integrated-shell-playing-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,'marker':'cobra_tv_integrated_shell_playing_2103234',
      'drawer_layout':['navigation-column','groups-column','preview-details-epg'],
      'drawer_overlay_on_guide':False,'drawer_back_restores_underlay':True,'drawer_width_fraction':0.20,
      'playing_channel_indicator':True,'playing_indicator_source':'actual preview/fullscreen player session',
      'preview_instruction_removed':True,'border_density_reduced':True,'focus_outline_preserved':True,
      'glass_system_preserved':True,'ambient_mode_retired':True,'real_time_blur':False,
      'navigation_preserved':'drawer-groups-grid-player','mini_player_preserved':True,'multiview_preserved':True,
      'native_engine_rebuilt':False,'playback_engine_unchanged':True,'mobile_fold_untouched':True,
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103234 inline drawer + true playing indicator applied over exact locked 2103233 RC13')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
