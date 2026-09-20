#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103194
BASE_NAME='1.0.9-Cobra-Fold-Adaptive-Aspect-RC1'
BASE_COMMIT='8c4a993afac76aafc295d482fe32e240e407ae14'

def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
    c=s.count(a)
    if c!=1: raise RuntimeError(f'{label}: expected one anchor, got {c}')
    return s.replace(a,b,1)
def matches(text,name,kind='method'):
    if kind=='method':
        return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
    return list(re.finditer(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M))
def span(text,name,kind='method'):
    ms=matches(text,name,kind)
    if len(ms)!=1: raise RuntimeError(f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False;i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q:q=None
        elif c=='/' and n=='/': line=True;i+=1
        elif c=='/' and n=='*': block=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+'\n'+text[b:]
def insert_before_final(text,addition):
    i=text.rfind('}')
    if i<0: raise RuntimeError('missing class close')
    return text[:i]+addition.rstrip()+'\n'+text[i:]

HELPERS=r'''
  private static final class CobraMotionSpec {
    static final long MICRO=120L, PANEL=190L, STAGGER=22L;
  }

  private void cobraPolishFocusable(View view){
    if(view==null)return;
    view.setOnFocusChangeListener((v,focused)->{
      v.animate().cancel();
      v.animate().scaleX(focused?1.018f:1f).scaleY(focused?1.018f:1f)
          .alpha(focused?1f:.97f).setDuration(focused?CobraMotionSpec.MICRO:100L)
          .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
    });
  }

  private void cobraAnimateChildrenIn(LinearLayout group){
    if(group==null)return;
    int count=Math.min(group.getChildCount(),14);
    for(int i=0;i<count;i++){
      View child=group.getChildAt(i);if(child==null)continue;
      child.animate().cancel();child.setAlpha(0f);child.setTranslationY(dp(8));child.setScaleX(.992f);child.setScaleY(.992f);
      child.animate().alpha(1f).translationY(0f).scaleX(1f).scaleY(1f)
          .setStartDelay(i*CobraMotionSpec.STAGGER).setDuration(CobraMotionSpec.PANEL)
          .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
    }
  }

  private void cobraAnimatePanelIn(View view,boolean horizontal){
    if(view==null)return;view.animate().cancel();view.setAlpha(0f);view.setScaleX(.985f);view.setScaleY(.985f);
    if(horizontal)view.setTranslationX(dp(18));else view.setTranslationY(dp(14));
    view.animate().alpha(1f).translationX(0f).translationY(0f).scaleX(1f).scaleY(1f)
        .setDuration(CobraMotionSpec.PANEL).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
  }

  private String cobraPlayerVideoSummary(){
    Format format=mPlayer==null?null:mPlayer.getVideoFormat();
    if(format==null)return "Waiting for video details";
    String size=format.width>0&&format.height>0?format.width+" × "+format.height:"Resolution pending";
    String rate=format.frameRate>0?String.format(Locale.US," • %.1f fps",format.frameRate):"";
    return size+rate+" • "+cobraAspectLabel(mAspectMode);
  }

  private void cobraTuneFromPlayerMenu(Channel channel){
    if(channel==null)return;closeCobraActionSheet();
    if(mPlaying!=null&&mPlaying.id.equals(channel.id)){showPlayerChromeTemporarily();return;}
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mPlayingVodKey="";mPendingResumeMs=0;
    startSinglePlayer(channel.primaryUrl);cobraBuildPlayerChrome();
  }

  private void cobraAddRecentPlayerStrip(LinearLayout parent){
    if(parent==null||mRecents.isEmpty())return;
    ArrayList<String> ids=new ArrayList<>(mRecents);Collections.reverse(ids);
    TextView label=cobraText("RECENT CHANNELS",vtheme().color("cobra.cobraOpenSheet.colors.6",0xff9fb2c6),10);
    label.setLetterSpacing(.10f);label.setPadding(dp(12),dp(10),dp(12),dp(6));parent.addView(label,new LinearLayout.LayoutParams(-1,-2));
    android.widget.HorizontalScrollView scroll=new android.widget.HorizontalScrollView(this);scroll.setHorizontalScrollBarEnabled(false);scroll.setOverScrollMode(View.OVER_SCROLL_NEVER);
    LinearLayout rail=new LinearLayout(this);rail.setOrientation(LinearLayout.HORIZONTAL);rail.setPadding(dp(4),0,dp(4),dp(6));scroll.addView(rail,new android.widget.HorizontalScrollView.LayoutParams(-2,-2));
    int shown=0;for(String id:ids){Channel c=findChannel(id);if(!cobraChannelAllowed(c))continue;final Channel selected=c;
      Button chip=cobraTextButton(c.name,true,()->cobraTuneFromPlayerMenu(selected));chip.setSingleLine(true);chip.setEllipsize(android.text.TextUtils.TruncateAt.END);
      chip.setTag("cobra-player-recent:"+c.id);chip.setSelected(mPlaying!=null&&mPlaying.id.equals(c.id));cobraPolishFocusable(chip);
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(150),dp(48));lp.rightMargin=dp(8);rail.addView(chip,lp);if(++shown>=8)break;
    }
    if(shown>0)parent.addView(scroll,new LinearLayout.LayoutParams(-1,dp(56)));
  }

  private void showCobraPlayerOptionsHub(){
    if(mPlayerOverlay==null||mCobraPlayerLocked||mInPictureInPicture)return;
    closeCobraPlayerDrawer();closeCobraMultiPicker(false);
    LinearLayout rows=cobraOpenSheet("Player options",mPlaying==null?"Quick playback controls":mPlaying.name+" • quick playback controls","player-hub");
    cobraAddRecentPlayerStrip(rows);
    cobraAddDetail(rows,"guide","Channels","Browse favorites, recent, all channels and groups","cobra-player-hub-channels",false,()->showCobraPlayerDrawer());
    cobraAddDetail(rows,"source","TV Guide","Return to the live guide without stopping playback","cobra-player-hub-guide",false,()->closeFullscreenToCobraView());
    if(mPlaying!=null)cobraAddDetail(rows,"favorite",mFavorites.contains(mPlaying.id)?"Remove from favorites":"Add to favorites","Keep this channel one tap away","cobra-player-hub-favorite",false,()->{toggleFavorite(mPlaying);showCobraPlayerOptionsHub();});
    cobraAddDetail(rows,"cc","Audio & subtitles","Choose tracks supplied by this stream","cobra-player-hub-tracks",false,()->showTrackChooser());
    cobraAddDetail(rows,"aspect","Video & display",cobraPlayerVideoSummary(),"cobra-player-hub-video",false,()->showCobraVideoOptions());
    cobraAddDetail(rows,"multi","Multi-View","Open the existing Cobra multi-screen picker","cobra-player-hub-multi",false,()->beginMultiView());
    cobraAddDetail(rows,"fullscreen","Picture in Picture","Hand video to Android PiP","cobra-player-hub-pip",false,()->enterCobraPictureInPicture());
    cobraAddDetail(rows,"record",mRecordingSession.isEmpty()?"Record now":"Stop recording","Use the current Cobra recording contract","cobra-player-hub-record",false,()->{if(mPlaying!=null)toggleRecording(mPlaying);});
    cobraAddDetail(rows,"health","Health Center","Observe playback without restarting the stream","cobra-player-hub-health",false,()->showCobraHealthCenter());
    cobraAddDetail(rows,"settings","Player settings","Playback, source and session controls","cobra-player-hub-settings",false,()->showPlayerSettingsDrawer());
    rows.post(()->cobraAnimateChildrenIn(rows));
  }

  private void showCobraVideoOptions(){
    if(mPlayerOverlay==null||mCobraPlayerLocked)return;
    LinearLayout rows=cobraOpenSheet("Video & display","Fold-aware picture, rotation and system display controls","video-options");
    cobraAddDetail(rows,"aspect","Display mode",cobraAspectLabel(mAspectMode),"cobra-video-options-aspect",false,()->showCobraAspectPicker());
    cobraAddDetail(rows,"health","Video details",cobraPlayerVideoSummary(),"cobra-video-options-details",false,()->showCobraHealthCenter());
    cobraAddDetail(rows,"rotate","Rotation",cobraPlayerRotationDescription(),"cobra-video-options-rotation",false,()->{cobraTogglePlayerRotation();showCobraVideoOptions();});
    cobraAddDetail(rows,"settings","Display & performance",cobraRefreshModeLabel(),"cobra-video-options-performance",false,()->showCobraDisplayPerformancePicker());
    cobraAddDetail(rows,"fullscreen","Picture in Picture","Use Android native PiP behavior","cobra-video-options-pip",false,()->enterCobraPictureInPicture());
    if(cobraLiveChannel(mPlaying))cobraAddDetail(rows,"settings","Channel playback","Per-channel display, languages and recovery","cobra-video-options-channel",false,()->cobraShowChannelPreferences(mPlaying));
    rows.post(()->cobraAnimateChildrenIn(rows));
  }
'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103194 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode()
    expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103194 Activity preimage mismatch')
    text=before

    protected_methods=[
      'buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraWatchTimeshiftReady','cobraActivateLocalTimeshift',
      'cobraRewindLive','cobraGoLive','cobraStopLocalTimeshift','cobraDisposePlayer','cobraUpdateTimeshiftSeek','cobraStartProviderCatchup',
      'showCobraDiagnosticExport','cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport','onStop','onPictureInPictureModeChanged',
      'cobraHandleAudioFocus','cobraClaimAudioFocus','cobraApplyDisplayPerformance','cobraTuneLastChannel',
      'showSourceActions','chooseSourceType','loadActiveSource','loadAllEnabledSources','editCustomEpg','showProfiles',
      'cobraFitVideo','showCobraAspectPicker','cobraShowChannelAspect','cobraAspectLabel'
    ]
    method_guards={n:sha(member(before,n)) for n in protected_methods}
    class_guards={n:sha(member(before,n,'class')) for n in [
      'CobraNetworkFamilyPolicy','CobraDiagnosticFreezePolicy','CobraStreamCadencePolicy','CobraTsParserPolicy',
      'CobraTsTimelinePolicy','CobraTimelineNormalizerPolicy','CobraProviderPacePolicy','CobraFoldAspectPolicy'
    ]}

    text=insert_before_final(text,HELPERS)

    sheet=member(text,'cobraOpenSheet')
    sheet=once(sheet,
      '    final boolean playerSettings="player-settings".equals(kind);\n    FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(Math.min(width-dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.12",24)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.13",440))),-2,\n        playerSettings?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:(isPortrait()?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:Gravity.RIGHT|Gravity.CENTER_VERTICAL));',
      '''    final boolean playerSettings="player-settings".equals(kind),playerHub="player-hub".equals(kind);
    int maxWidth=playerHub?dp(620):dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.13",440));
    FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(Math.min(width-dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.12",24)),maxWidth),-2,
        (playerSettings||playerHub)?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:(isPortrait()?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:Gravity.RIGHT|Gravity.CENTER_VERTICAL));''',
      'player hub sheet geometry')
    sheet=once(sheet,
      '    panel.setAlpha(0f);panel.setTranslationY(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.18",10)));panel.animate().alpha(1f).translationY(0f).setDuration(vtheme().motion("cobra.cobraOpenSheet.numbers.1",160)).start();',
      '''    panel.setAlpha(0f);panel.setTranslationY(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.18",12)));panel.setScaleX(.985f);panel.setScaleY(.985f);
    panel.animate().alpha(1f).translationY(0f).scaleX(1f).scaleY(1f).setDuration(vtheme().motion("cobra.cobraOpenSheet.numbers.1",190)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();''',
      'sheet motion')
    text=replace_member(text,'cobraOpenSheet',sheet)

    anchored=member(text,'cobraPositionAnchoredSheet')
    anchored=once(anchored,
      '    if(panel.getLeft()==rect[0]&&panel.getTop()==rect[1]&&panel.getWidth()==rect[2]&&!panel.isLayoutRequested())panel.setAlpha(1f);',
      '''    if(panel.getLeft()==rect[0]&&panel.getTop()==rect[1]&&panel.getWidth()==rect[2]&&!panel.isLayoutRequested()&&panel.getAlpha()==0f){
      panel.setScaleX(.985f);panel.setScaleY(.985f);panel.setTranslationX(dp(8));
      panel.animate().alpha(1f).translationX(0f).scaleX(1f).scaleY(1f).setDuration(CobraMotionSpec.PANEL).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
    }''',
      'anchored sheet motion')
    text=replace_member(text,'cobraPositionAnchoredSheet',anchored)

    row=member(text,'cobraSheetRow')
    row=once(row,'    row.setMinimumHeight(dp(subtitle==null||subtitle.isEmpty()?52:64));vtheme().tree(row,"sheet.row");return row;',
             '    row.setMinimumHeight(dp(subtitle==null||subtitle.isEmpty()?52:64));cobraPolishFocusable(row);vtheme().tree(row,"sheet.row");return row;','sheet row focus motion')
    text=replace_member(text,'cobraSheetRow',row)

    detail=member(text,'cobraDetailRow')
    detail=once(detail,'    row.setOnClickListener(v->{closeCobraActionSheet();action.run();});vtheme().tree(row,"sheet.detail");return row;',
                '    row.setOnClickListener(v->{closeCobraActionSheet();action.run();});cobraPolishFocusable(row);vtheme().tree(row,"sheet.detail");return row;','detail row focus motion')
    text=replace_member(text,'cobraDetailRow',detail)

    action=member(text,'action')
    action=once(action,'    vtheme().paint(button,"widget.action");return button;',
                '    cobraPolishFocusable(button);vtheme().paint(button,"widget.action");return button;','action focus motion')
    text=replace_member(text,'action',action)

    text_button=member(text,'cobraTextButton')
    text_button=once(text_button,'b.setOnClickListener(v->action.run());vtheme().paint(b,"widget.cobraTextButton");return b;',
                     'b.setOnClickListener(v->action.run());cobraPolishFocusable(b);vtheme().paint(b,"widget.cobraTextButton");return b;','text button focus motion')
    text=replace_member(text,'cobraTextButton',text_button)

    settings=member(text,'showSettings')
    settings=once(settings,'    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(-1,0,1));\n    refreshCobraSubscriptionStatus();',
                  '    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(-1,0,1));\n    list.post(()->cobraAnimateChildrenIn(list));\n    refreshCobraSubscriptionStatus();','settings stagger')
    text=replace_member(text,'showSettings',settings)

    sources=member(text,'showSources')
    sources=once(sources,'    mStage.addView(scroll, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));',
                 '    mStage.addView(scroll, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));\n    list.post(()->cobraAnimateChildrenIn(list));','sources stagger')
    text=replace_member(text,'showSources',sources)

    drawer=member(text,'showCobraPlayerDrawer')
    drawer=once(drawer,'    mPlayerOverlay.addView(panel,new FrameLayout.LayoutParams(1,1));mPlayerChrome.setVisibility(View.GONE);cobraRenderPlayerDrawer(mCobraDrawerFilter);cobraLayoutPlayerPanels();vtheme().tree(content,"player.channels");',
                '    mPlayerOverlay.addView(panel,new FrameLayout.LayoutParams(1,1));mPlayerChrome.setVisibility(View.GONE);cobraRenderPlayerDrawer(mCobraDrawerFilter);cobraLayoutPlayerPanels();panel.post(()->cobraAnimatePanelIn(panel,!isPortrait()));vtheme().tree(content,"player.channels");','player drawer motion')
    text=replace_member(text,'showCobraPlayerDrawer',drawer)

    render_drawer=member(text,'cobraRenderPlayerDrawer')
    render_drawer=once(render_drawer,
      '        return row;}});',
      '        return row;}});\n    mCobraPlayerDrawerList.setAlpha(.72f);mCobraPlayerDrawerList.setTranslationY(dp(5));mCobraPlayerDrawerList.animate().alpha(1f).translationY(0f).setDuration(150L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();',
      'player drawer filter motion')
    text=replace_member(text,'cobraRenderPlayerDrawer',render_drawer)

    settings_drawer=member(text,'showPlayerSettingsDrawer')
    settings_drawer=r'''  private void showPlayerSettingsDrawer() {
    if(mPlayerOverlay==null||mCobraPlayerLocked)return;
    closeCobraPlayerDrawer();if("player-settings".equals(mCobraSheetKind)){closeCobraActionSheet();return;}
    LinearLayout rows=cobraOpenSheet("Player settings","Playback, video and session controls","player-settings");
    cobraAddDetail(rows,"aspect","Video & display",cobraPlayerVideoSummary(),"cobra-player-settings-video",false,()->showCobraVideoOptions());
    cobraAddDetail(rows,"cc","Audio & subtitles","Available tracks in this stream","cobra-player-settings-tracks",false,()->showTrackChooser());
    if(cobraLiveChannel(mPlaying)){final Channel selected=mPlaying;cobraAddDetail(rows,"settings","Channel playback","Display, languages and recovery","cobra-player-channel-preferences",false,()->cobraShowChannelPreferences(selected));}
    cobraAddDetail(rows,"health","Health Center","Observe playback without stopping it","cobra-player-health",false,()->showCobraHealthCenter());
    if(cobraCanRestartCurrentProgram())cobraAddDetail(rows,"recent","Restart current program","Provider catch-up","cobra-player-restart",false,()->cobraRestartCurrentProgram());
    cobraAddDetail(rows,"record",mRecordingSession.isEmpty()?"Record now":"Stop recording",null,"cobra-player-record",false,()->{if(mPlaying!=null)toggleRecording(mPlaying);});
    cobraAddDetail(rows,"cast","Cast / Route","Open Android route controls","cobra-player-cast",false,()->openCastSettings());
    cobraAddDetail(rows,"source","Manage sources","Leaves this player","cobra-player-sources",false,()->{closePlayer();stopCobraPreview();mCobraInternalScreen="internal";showSources();});
    cobraAddDetail(rows,"close","Close player","Stop playback and return to browsing","cobra-player-close",false,()->{mCobraPreviewAutoplayAllowed=false;closePlayer();showCobraPrimaryView();cobraUpdatePlaybackLabels();});
    rows.post(()->cobraAnimateChildrenIn(rows));
  }'''
    text=replace_member(text,'showPlayerSettingsDrawer',settings_drawer)

    chrome=member(text,'cobraBuildPlayerChrome')
    chrome=once(chrome,
      '    LinearLayout tools=new LinearLayout(this);String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display","Multi-View","More"};\n    for(int i=0;i<4;i++){final int action=i;CobraIconButton b=cobraIcon(glyphs[i],labels[i],true,v->{if(action==0)showCobraPlayerDrawer();else if(action==1)showCobraAspectPicker();else if(action==2)beginMultiView();else showPlayerSettingsDrawer();});b.caption(labels[i]);if(action==1)b.setTag("cobra_player_aspect_anchor");if(action==3)b.setTag("cobra_player_options_anchor");tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",52)),1));}',
      '''    LinearLayout tools=new LinearLayout(this);boolean expandedTools=width>=dp(520)&&!shortScreen;
    String[] glyphs=expandedTools?new String[]{"guide","favorite","cc","aspect","multi","more"}:new String[]{"guide","aspect","multi","more"};
    String[] labels=expandedTools?new String[]{"Channels","Favorite","Audio","Display","Multi-View","Options"}:new String[]{"Channels","Display","Multi-View","Options"};
    for(int i=0;i<glyphs.length;i++){final String action=labels[i];CobraIconButton b=cobraIcon(glyphs[i],action,true,v->{
      if("Channels".equals(action))showCobraPlayerDrawer();
      else if("Favorite".equals(action)){if(mPlaying!=null){toggleFavorite(mPlaying);cobraBuildPlayerChrome();}}
      else if("Audio".equals(action))showTrackChooser();
      else if("Display".equals(action))showCobraVideoOptions();
      else if("Multi-View".equals(action))beginMultiView();
      else showCobraPlayerOptionsHub();
    });b.caption(action);if("Display".equals(action))b.setTag("cobra_player_aspect_anchor");if("Options".equals(action))b.setTag("cobra_player_options_anchor");tools.addView(b,new LinearLayout.LayoutParams(0,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.34",52)),1));}''',
      'TiviMate-inspired player toolbar')
    chrome=once(chrome,
      '    vtheme().tree(chrome,"player.chrome");cobraUpdatePlayerRotationButton();cobraApplyPlayerRotation("chrome");cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();cobraUpdateLiveRewindControls();cobraUpdateLastChannelButton();cobraUpdateTimeshiftSeek();',
      '    if(visible){chrome.setAlpha(0f);chrome.setTranslationY(dp(8));chrome.animate().alpha(1f).translationY(0f).setDuration(150L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();}\n    vtheme().tree(chrome,"player.chrome");cobraUpdatePlayerRotationButton();cobraApplyPlayerRotation("chrome");cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();cobraUpdateLiveRewindControls();cobraUpdateLastChannelButton();cobraUpdateTimeshiftSeek();',
      'player chrome motion')
    text=replace_member(text,'cobraBuildPlayerChrome',chrome)

    exp=member(text,'toggleCobraDrawer')
    exp=once(exp,
      '    panel.setTranslationX(-width);panel.animate().translationX(0).setDuration(vtheme().motion("cobra.toggleCobraDrawer.numbers.1",180)).start();animateCobraDrawerShift(Math.min(width,screen*.28f));',
      '    panel.setTranslationX(-width);panel.setAlpha(.90f);panel.setScaleX(.99f);panel.setScaleY(.99f);panel.animate().translationX(0).alpha(1f).scaleX(1f).scaleY(1f).setDuration(vtheme().motion("cobra.toggleCobraDrawer.numbers.1",210)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();animateCobraDrawerShift(Math.min(width,screen*.28f));',
      'experience drawer motion')
    text=replace_member(text,'toggleCobraDrawer',exp)

    shift=member(text,'animateCobraDrawerShift')
    shift=once(shift,
      '    if(mStage!=null)mStage.animate().translationX(translation).setDuration(vtheme().motion("cobra.animateCobraDrawerShift.numbers.1",180)).start();',
      '    if(mStage!=null)mStage.animate().translationX(translation).setDuration(vtheme().motion("cobra.animateCobraDrawerShift.numbers.1",210)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();',
      'drawer stage easing')
    text=replace_member(text,'animateCobraDrawerShift',shift)

    empty=member(text,'cobraModeEmpty')
    empty=r'''  private void cobraModeEmpty(LinearLayout parent,String value){
    TextView empty=cobraText(value,cobraModeColor("muted"),14);empty.setGravity(Gravity.CENTER);empty.setMaxLines(4);
    empty.setPadding(dp(24),dp(20),dp(24),dp(20));empty.setBackground(cobraModeSurface(18,true));
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,0,1);p.setMargins(dp(10),dp(12),dp(10),dp(12));parent.addView(empty,p);
    empty.setAlpha(0f);empty.setScaleX(.98f);empty.setScaleY(.98f);empty.animate().alpha(1f).scaleX(1f).scaleY(1f).setDuration(180L).start();
  }'''
    text=replace_member(text,'cobraModeEmpty',empty)

    browser=member(text,'cobraRenderGuideBrowser')
    browser=once(browser,
      '      mCobraGuideBrowser.setAlpha(.65f);mCobraGuideBrowser.animate().alpha(1f).setDuration(vtheme().motion("cobra.cobraRenderGuideBrowser.numbers.1",160)).start();mCobraRenderedMode=mCobraGuideStyle;',
      '      mCobraGuideBrowser.setAlpha(.62f);mCobraGuideBrowser.setTranslationY(dp(7));mCobraGuideBrowser.animate().alpha(1f).translationY(0f).setDuration(vtheme().motion("cobra.cobraRenderGuideBrowser.numbers.1",190)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();mCobraRenderedMode=mCobraGuideStyle;',
      'guide mode transition')
    text=replace_member(text,'cobraRenderGuideBrowser',browser)

    for n,h in method_guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected playback/source owner changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h: raise RuntimeError('Protected class changed: '+n)

    required=[
      'showCobraPlayerOptionsHub','showCobraVideoOptions','RECENT CHANNELS','TV Guide','Video & display','Picture in Picture',
      'cobra-player-hub-channels','cobra-player-hub-video','cobra-video-options-aspect','cobra-player-options-anchor',
      'CobraMotionSpec','cobraAnimateChildrenIn','cobraPolishFocusable','cobraAnimatePanelIn',
      'Fold Adaptive','cobra_tv_sources','timeshift_provider_pace_limited','REWRITE_ENABLED=false',
      'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES','cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart'
    ]
    for token in required:
        if token not in text: raise RuntimeError('2103195 contract missing: '+token)

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={
      'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'tivimate_inspired_player_hub':True,'recent_channel_strip':True,'video_display_submenu':True,
      'expanded_player_toolbar':True,'motion_polish':True,'settings_stagger':True,'sources_stagger':True,'guide_transition_polish':True,
      'fold_adaptive_preserved':True,'source_manager_route_preserved':True,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,
      'buffer_policy_changed':False,'parser_flags_changed':False,'clock_rewrite_changed':False,'native_changed':False,
      'theme_zip_changed':False,'physical_device_verified':False
    }
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103195 presentation polish + TiviMate-inspired player hub applied over exact 2103194; protected playback/source stack preserved')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
