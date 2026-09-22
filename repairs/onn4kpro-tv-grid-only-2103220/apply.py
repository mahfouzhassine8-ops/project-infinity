#!/usr/bin/env python3
"""2103220 onn. 4K Pro TV-only simplification and remote ownership pass.

Parent: exact 2103219 TV Remote RC2 source.
Scope: armeabi-v7a TV branch only. Mobile/Fold ARM64 sources are not modified.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103220
OLD_VERSION=2103219
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Remote-RC2'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Grid-RC3'
SOURCE='tools/android/packaging/xbmc/'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def require(v,m):
    if not v: raise RuntimeError(m)
def once(text,old,new,label):
    require(text.count(old)==1,f'{label} anchor drift ({text.count(old)})')
    return text.replace(old,new,1)

def method_span(text:str, signature:str):
    start=text.find(signature)
    require(start>=0,'Missing method signature: '+signature)
    brace=text.find('{',start)
    require(brace>=0,'Missing method brace: '+signature)
    depth=0
    for i in range(brace,len(text)):
        ch=text[i]
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: return start,i+1
    raise RuntimeError('Unclosed method: '+signature)

def replace_method(text:str, signature:str, replacement:str):
    a,b=method_span(text,signature)
    return text[:a]+replacement+text[b:]

def method_by_name(text:str,name:str):
    pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:public|private|protected)\s+(?:static\s+)?[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{]*\)\s*\{')
    m=pat.search(text)
    require(m is not None,'Missing method by name: '+name)
    start=m.start(); brace=text.find('{',m.start())
    depth=0
    for i in range(brace,len(text)):
        if text[i]=='{': depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0: return start,brace,i+1
    raise RuntimeError('Unclosed method by name: '+name)

def replace_body(text:str,name:str,body:str):
    start,brace,end=method_by_name(text,name)
    indent=re.match(r'\s*',text[start:text.find('\n',start) if '\n' in text[start:] else brace]).group(0)
    rendered='{\n'+''.join(indent+'  '+line+'\n' for line in body.splitlines())+indent+'}'
    return text[:brace]+rendered+text[end:]

def remove_exact(text:str,block:str,label:str):
    require(text.count(block)==1,f'{label} anchor drift ({text.count(block)})')
    return text.replace(block,'',1)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json')
    receipt=json.loads(receipt_path.read_text())
    require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
            'Expected exact 2103219 TV Remote RC2 source replay')
    require(receipt.get('tv_variant') is True and receipt.get('tv_target_abi')=='armeabi-v7a',
            'Expected exact ARMv7 TV parent')
    require(receipt.get('tv_remote_optimized') is True,'Expected 2103219 remote optimization parent')

    gradle=shell/(SOURCE+'build.gradle.in')
    manifest=shell/(SOURCE+'AndroidManifest.xml.in')
    live=shell/(SOURCE+'src/InfinityLiveActivity.java.in')
    for p in (gradle,manifest,live): require(p.is_file(),'Missing TV source input: '+str(p))

    g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName')
    gradle.write_text(g)

    # Android TV has no phone-style PiP lifecycle in this variant.
    m=manifest.read_text()
    require(m.count('android:supportsPictureInPicture="true"')>=1,'PiP manifest anchor missing')
    m=m.replace('android:supportsPictureInPicture="true"','android:supportsPictureInPicture="false"')
    manifest.write_text(m)

    s=live.read_text()

    # --- TV Grid is the only TV layout. ---
    s=replace_method(s,'private String cobraGuideViewMode()','''private String cobraGuideViewMode() {
    return "grid";
  }''')
    s=replace_method(s,'private void showCobraViewModeMenu()','''private void showCobraViewModeMenu(){
    mCobraGuideStyle="grid";
  }''')
    s=replace_method(s,'private void cobraPremiumViewMenu()','''private void cobraPremiumViewMenu(){
    mCobraGuideStyle="grid";
    closeCobraActionSheet();
  }''')
    s=replace_method(s,'private void cobraSwitchMode(String mode)','''private void cobraSwitchMode(String mode){
    mCobraGuideStyle="grid";mCobraGuideRoute="channels";mCobraInspectedChannel=null;mCobraInspectedProgram=null;
    closeCobraActionSheet();closeCobraExperienceDrawer();cobraShowGuideShell();
  }''')
    s=once(s,'private void showCobraTvHub(){mCobraModeGroupsExpanded=true;mCobraGuideRoute="channels";mCobraGuideStyle=cobraGuideViewMode();cobraShowGuideShell();}',
           'private void showCobraTvHub(){mCobraModeGroupsExpanded=false;mCobraGuideRoute="channels";mCobraGuideStyle="grid";InfinityExtendedBackgroundService.setEnabled(this,false);cobraShowGuideShell();}',
           'TV hub grid lock')
    for old in (
        'private void showCobraMobileView(){mCobraGuideStyle="mobile";cobraShowGuideShell();}',
        'private void showGuideCompact(){mCobraGuideStyle="compact";cobraShowGuideShell();}',
        'private void showGuideCards(){mCobraGuideStyle="cards";cobraShowGuideShell();}',
        'private void showGuideFocus(){mCobraGuideStyle="focus";cobraShowGuideShell();}',
    ):
        if old in s: s=s.replace(old,'private void '+old.split('private void ',1)[1].split('(',1)[0]+'(){showGuideGrid();}',1)
    s=once(s,'static final String[] MODES={"mobile","grid","compact","cards","focus"};',
           'static final String[] MODES={"grid"};','TV mode inventory')
    s=replace_method(s,'private String cobraModeName(String key)','''private String cobraModeName(String key){return "TV Grid";}''')

    # Remove the View chooser from the drawer and toolbar. Grid title is informational only.
    s=once(s,'    cobraDrawerView(items);\n','', 'drawer view chooser')
    s=once(s,'title.addView(mCobraModeTitle);title.addView(mCobraModeSub);title.setOnClickListener(v->showCobraViewModeMenu());',
           'title.addView(mCobraModeTitle);title.addView(mCobraModeSub);title.setClickable(false);title.setFocusable(false);',
           'grid title selector')
    s=once(s,'    mCobraModeToolbar.addView(cobraIcon("multi","Choose one of five view modes",dark,v->showCobraViewModeMenu()),new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildModeChrome.dimensions.4",48)),-1));\n',
           '','toolbar mode selector')

    # TV Grid geometry: no permanent phone/tablet rail or category column. Give the EPG most of the screen.
    grid_start='      if("grid".equals(mode)){'
    grid_end='      }else if("compact".equals(mode)){'
    a=s.find(grid_start); require(a>=0,'grid layout start drift')
    b=s.find(grid_end,a); require(b>a,'grid layout end drift')
    grid='''      if("grid".equals(mode)){
        // 10-foot TV layout: full-width EPG, compact preview/details strip, no permanent side rails.
        int x=0,body=w;
        int hero=Math.min(Math.round(108+10*(f-1)),Math.max(76,avail*20/100));
        int vw=Math.min(Math.round(192+16*(f-1)),Math.min(Math.max(120,body/4),hero*16/9));
        box(p.video,x,y,vw,Math.min(hero,Math.max(54,vw*9/16)));
        box(p.details,x+vw+gap,y,Math.max(0,body-vw-gap),hero);
        box(p.browser,0,y+hero+gap,w,Math.max(1,h-y-hero-gap));
        p.channelWidth=Math.min(Math.round(156+16*(f-1)),Math.max(96,w/4));
        p.timeSpan=w>=900?10800000L:w>=540?7200000L:3600000L;
        p.smallPreview=true;
'''
    s=s[:a]+grid+s[b:]
    # Remove the one-time browser slide/fade; focus should feel immediate on TV.
    old_anim='''    if(!mCobraGuideStyle.equals(mCobraRenderedMode)){
      mCobraGuideBrowser.setAlpha(.62f);mCobraGuideBrowser.setTranslationY(dp(7));mCobraGuideBrowser.animate().alpha(1f).translationY(0f).setDuration(vtheme().motion("cobra.cobraRenderGuideBrowser.numbers.1",190)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();mCobraRenderedMode=mCobraGuideStyle;
    }'''
    s=once(s,old_anim,'    mCobraRenderedMode="grid";','TV guide entrance motion')

    # --- Proper TV drawer focus ownership. ---
    drawer_helpers='''  private static final String COBRA_TV_GRID_ONLY_BUILD="cobra_tv_grid_only_2103220";
  private LinearLayout mCobraTvDrawerPanel;
  private View mCobraTvDrawerPreviousFocus;

  private String cobraTvDrawerDestination(){
    String title=mCobraStageTitle==null?"":mCobraStageTitle.toUpperCase(java.util.Locale.US);
    if(title.contains("SETTINGS"))return "SETTINGS";
    if(title.contains("MOVIE"))return "MOVIES";
    if(title.contains("SHOW")||title.contains("SERIES"))return "SHOWS";
    if(title.contains("RECORD"))return "RECORDINGS";
    if(title.contains("MY LIST")||title.contains("WATCHLIST"))return "MY LIST";
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow())return "TV";
    return "TV";
  }

  private void cobraTvFocusFirst(android.view.ViewGroup root){
    if(root==null||!root.isAttachedToWindow())return;
    java.util.ArrayList<View> values=root.getFocusables(View.FOCUS_FORWARD);
    for(View value:values)if(value!=null&&value.isShown()&&value.isEnabled()&&value.isFocusable()){value.requestFocus();return;}
  }

  private void cobraTvFocusDrawer(LinearLayout panel){
    if(panel==null||!panel.isAttachedToWindow())return;
    View target=panel.findViewWithTag("cobra-destination:"+cobraTvDrawerDestination());
    if(target==null)target=panel.findViewWithTag("cobra-destination:TV");
    if(target==null)target=panel.findViewWithTag("cobra-destination:SEARCH");
    if(target!=null)target.requestFocus();else cobraTvFocusFirst(panel);
  }

  private java.util.ArrayList<View> cobraTvDrawerFocusables(){
    java.util.ArrayList<View> out=new java.util.ArrayList<>();
    if(mCobraTvDrawerPanel==null)return out;
    for(View value:mCobraTvDrawerPanel.getFocusables(View.FOCUS_FORWARD)){
      if(value==null||!value.isShown()||!value.isEnabled()||!value.isFocusable())continue;
      Object tag=value.getTag();String name=tag instanceof String?(String)tag:"";
      if(name.startsWith("cobra-destination:")||"cobra_drawer_power".equals(name))out.add(value);
    }
    return out;
  }

  private boolean cobraTvMoveDrawerFocus(int delta){
    java.util.ArrayList<View> values=cobraTvDrawerFocusables();if(values.isEmpty())return true;
    View current=getCurrentFocus();int at=values.indexOf(current);
    if(at<0){cobraTvFocusDrawer(mCobraTvDrawerPanel);return true;}
    int next=Math.max(0,Math.min(values.size()-1,at+delta));values.get(next).requestFocus();return true;
  }

  private boolean cobraTvCloseDrawerRestoreFocus(){
    View restore=mCobraTvDrawerPreviousFocus;boolean closed=closeCobraExperienceDrawer();
    mCobraTvDrawerPanel=null;mCobraTvDrawerPreviousFocus=null;
    if(closed&&restore!=null)restore.post(()->{if(restore.isAttachedToWindow())restore.requestFocus();});
    return closed;
  }

  private boolean cobraTvHandleDrawerKey(KeyEvent event){
    if(mCobraTvDrawerPanel==null||!mCobraTvDrawerPanel.isAttachedToWindow()||event.getAction()!=KeyEvent.ACTION_DOWN)return false;
    int code=event.getKeyCode();
    if(code==KeyEvent.KEYCODE_BACK||code==KeyEvent.KEYCODE_DPAD_LEFT){cobraTvCloseDrawerRestoreFocus();return true;}
    if(code==KeyEvent.KEYCODE_DPAD_UP)return cobraTvMoveDrawerFocus(-1);
    if(code==KeyEvent.KEYCODE_DPAD_DOWN)return cobraTvMoveDrawerFocus(1);
    if(code==KeyEvent.KEYCODE_DPAD_RIGHT)return true;
    return false;
  }

'''
    s=once(s,'  private void toggleCobraDrawer(){',drawer_helpers+'  private void toggleCobraDrawer(){','TV drawer helpers')
    s=once(s,'    if(closeCobraExperienceDrawer())return;\n',
           '    if(closeCobraExperienceDrawer()){mCobraTvDrawerPanel=null;mCobraTvDrawerPreviousFocus=null;return;}\n    mCobraTvDrawerPreviousFocus=getCurrentFocus();\n',
           'drawer previous focus')
    s=once(s,'    FrameLayout shield=new FrameLayout(this);shield.setTag("cobra_experience_drawer");shield.setClickable(true);shield.setBackgroundColor(vtheme().color("cobra.toggleCobraDrawer.colors.1",0x4d000000));shield.setOnClickListener(v->closeCobraExperienceDrawer());\n    LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setClickable(true);',
           '    FrameLayout shield=new FrameLayout(this);shield.setTag("cobra_experience_drawer");shield.setClickable(true);shield.setBackgroundColor(vtheme().color("cobra.toggleCobraDrawer.colors.1",0x4d000000));shield.setOnClickListener(v->closeCobraExperienceDrawer());\n    LinearLayout panel=new LinearLayout(this);mCobraTvDrawerPanel=panel;panel.setOrientation(LinearLayout.VERTICAL);panel.setClickable(true);panel.setFocusable(true);panel.setFocusableInTouchMode(false);panel.setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);',
           'drawer focus owner')
    s=once(s,'    shield.addView(panel,new FrameLayout.LayoutParams(width,-1,Gravity.LEFT));decor.addView(shield,new FrameLayout.LayoutParams(-1,-1));\n',
           '    shield.addView(panel,new FrameLayout.LayoutParams(width,-1,Gravity.LEFT));decor.addView(shield,new FrameLayout.LayoutParams(-1,-1));panel.post(()->cobraTvFocusDrawer(panel));\n',
           'drawer initial focus')
    s=once(s,'.setDuration(vtheme().motion("cobra.toggleCobraDrawer.numbers.1",210))',
           '.setDuration(vtheme().motion("cobra.toggleCobraDrawer.numbers.1",90))','drawer TV motion')
    s=once(s,'    LinearLayout row=cobraDetailRow(icon,label,null,"cobra-destination:"+destination,false,()->{',
           '    LinearLayout row=cobraDetailRow(icon,label,null,"cobra-destination:"+destination,false,()->{',
           'drawer destination anchor')
    s=once(s,'    if(row.getChildCount()>0)row.getChildAt(0).setTag("cobra-drawer-icon:"+destination);\n',
           '    row.setSelected(destination.equals(cobraTvDrawerDestination()));\n    if(row.getChildCount()>0)row.getChildAt(0).setTag("cobra-drawer-icon:"+destination);\n',
           'drawer current selection')
    s=once(s,'states.addState(new int[]{android.R.attr.state_focused},surface(cobraModeColor("panel"),14,cobraModeColor("muted"),1));',
           'states.addState(new int[]{android.R.attr.state_focused},surface(cobraModeColor("panel"),14,cobraModeColor("accent"),2));states.addState(new int[]{android.R.attr.state_selected},surface(cobraModeColor("panel"),14,cobraModeColor("accent"),1));',
           'drawer focus visibility')
    s=once(s,'  @Override public boolean dispatchKeyEvent(KeyEvent event) {\n',
           '  @Override public boolean dispatchKeyEvent(KeyEvent event) {\n    if(cobraTvHandleDrawerKey(event))return true;\n',
           'drawer key ownership')

    # Focus every Cobra sheet immediately; no blind remote presses.
    s=once(s,'scrim.addView(panel,pos);parent.addView(scrim,new FrameLayout.LayoutParams(-1,-1));cobraRefreshVisualEffects();',
           'scrim.addView(panel,pos);parent.addView(scrim,new FrameLayout.LayoutParams(-1,-1));items.post(()->cobraTvFocusFirst(items));cobraRefreshVisualEffects();',
           'sheet initial focus')

    # --- Remove phone/Fold-only settings from TV UI. ---
    for block,label in (
('''    Button displayPerformance = action("DISPLAY & PERFORMANCE  •  " + cobraRefreshModeLabel());
    displayPerformance.setTag("cobra_display_performance");
    displayPerformance.setOnClickListener(v -> showCobraDisplayPerformancePicker());

''','display performance setting'),
('''    Button backgroundMode = action("BACKGROUND MODE  •  " + cobraBackgroundModeLabel());
    backgroundMode.setTag("cobra_background_mode");
    backgroundMode.setOnClickListener(v -> showCobraBackgroundModePicker());

''','background mode setting'),
('''    Button miniBackground = action("PLAY IN BACKGROUND  •  " + cobraMiniBackgroundLabel());
    miniBackground.setTag("cobra_mini_background");
    miniBackground.setOnClickListener(v -> showCobraMiniBackgroundPicker());

''','play in background setting'),
('''    Button filePicker = action("FILE PICKER  •  " + cobraFilePickerLabel());
    filePicker.setTag("cobra_file_picker");
    filePicker.setOnClickListener(v -> showCobraFilePickerPicker());

''','file picker setting'),
    ):
        s=remove_exact(s,block,label)
    for line,label in (
('    list.addView(displayPerformance, new LinearLayout.LayoutParams(-1, dp(58)));\n','display performance row'),
('    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));\n','background mode row'),
('    list.addView(miniBackground, new LinearLayout.LayoutParams(-1, dp(56)));\n','background playback row'),
('    list.addView(filePicker, new LinearLayout.LayoutParams(-1, dp(56)));\n','file picker row'),
    ):
        s=remove_exact(s,line,label)
    s=once(s,'cobraSettingsSection("EXPERIENCE & DISPLAY")','cobraSettingsSection("EXPERIENCE")','TV settings heading')
    s=once(s,'    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(-1,0,1));\n    list.post(()->cobraAnimateChildrenIn(list));\n    refreshCobraSubscriptionStatus();',
           '    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(-1,0,1));\n    list.post(()->{cobraAnimateChildrenIn(list);cobraTvFocusFirst(list);});\n    refreshCobraSubscriptionStatus();','settings initial focus')

    # TV is 60 Hz focused; ignore stale 90/120/max preferences and disable stale FPS overlay work.
    s=replace_body(s,'cobraRefreshMode','return "60";')
    perf_line='boolean wanted=mPrefs!=null&&mPrefs.getBoolean(COBRA_PERFORMANCE_OVERLAY,false)&&!isFinishing()&&!isDestroyed();'
    require(perf_line in s,'performance overlay anchor missing')
    s=s.replace(perf_line,'boolean wanted=false;',1)

    # No TV PiP, mini-background or call-specific playback behavior.
    s=replace_body(s,'cobraWantsFullscreenPip','return false;')
    s=replace_body(s,'configureCobraPip','cobraReleasePipMediaSession();')
    s=replace_body(s,'enterCobraPictureInPicture','cobraEndMiniBackgroundPlayback();pauseCobraForBackground();')
    s=replace_method(s,'@Override protected void onUserLeaveHint()','''@Override protected void onUserLeaveHint(){
    super.onUserLeaveHint();
    cobraEndMiniBackgroundPlayback();
    pauseCobraForBackground();
  }''')
    # onStop policy must not revive stale background preferences.
    try:
        s=replace_body(s,'cobraBackgroundPlaybackRequested','return false;')
    except RuntimeError:
        raise RuntimeError('Missing central background playback policy method')
    s=replace_body(s,'cobraManualCallResumeEnabled','return false;')
    # Persistently collapse Extended mode as soon as TV Live is entered or Settings is opened.
    s=once(s,'  private void showSettings() {\n    cobraCaptureSettingsReturn();',
           '  private void showSettings() {\n    InfinityExtendedBackgroundService.setEnabled(this,false);cobraEndMiniBackgroundPlayback();\n    cobraCaptureSettingsReturn();',
           'TV settings background normalization')

    # Remove PiP/background/call rows from per-channel playback preferences.
    for line,label in (
('    cobraAddDetail(rows,"pip","Picture-in-picture",cobraChannelChoiceLabel(prefs.pip),"cobra-channel-pip",false,()->cobraShowChannelSwitch(channel,"pip"));\n','channel PiP'),
('    cobraAddDetail(rows,"audio","Play in background",cobraChannelChoiceLabel(prefs.background),"cobra-channel-background",false,()->cobraShowChannelSwitch(channel,"background"));\n','channel background'),
('    cobraAddDetail(rows,"audio","Media During Calls",cobraMediaDuringCallsLabel()+" • all Cobra playback","cobra-media-during-calls",false,()->cobraShowMediaDuringCalls(channel));\n','channel calls'),
    ):
        s=remove_exact(s,line,label)
    old_info='cobraInfoText(rows,"Channel preferences apply to this channel, source and profile. Media During Calls applies to all Cobra playback. Display is in the video toolbar. Language preferences are in Audio & subtitles.");'
    s=once(s,old_info,'cobraInfoText(rows,"Channel preferences apply to this channel, source and profile. Display is in the video toolbar. Language preferences are in Audio & subtitles.");','channel preference help')

    # Fixed TV orientation: no rotation button and no sensor unlock path.
    rotation='''    CobraIconButton rotation=cobraIcon("rotate",cobraPlayerRotationDescription(),true,v->cobraTogglePlayerRotation());
    rotation.setTag("cobra_player_rotation");mCobraPlayerRotationButton=rotation;cobraUpdatePlayerRotationButton();
    header.addView(rotation,new LinearLayout.LayoutParams(dp(48),dp(48)));
'''
    s=remove_exact(s,rotation,'player rotation button')
    s=replace_body(s,'cobraPlayerRotationMode','return COBRA_ROTATION_FOLLOW_DEVICE;')
    s=replace_method(s,'private void cobraApplyPlayerRotation(String reason)','''private void cobraApplyPlayerRotation(String reason){
    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,reason);
  }''')
    s=s.replace('Fold Adaptive automatically follows the usable screen size without restarting playback',
                'Auto Fit follows the TV display without restarting playback')
    s=s.replace('"Fold Adaptive"','"Auto Fit"')

    # This build is always a remote/Leanback target even if an OEM advertises touch hardware.
    s=replace_method(s,'private boolean cobraTouchFirstDevice()','''private boolean cobraTouchFirstDevice() {
    return false;
  }''')

    live.write_text(s)

    # Source-level gates.
    for token in (
        'COBRA_TV_GRID_ONLY_BUILD="cobra_tv_grid_only_2103220"',
        'static final String[] MODES={"grid"};',
        'private String cobraGuideViewMode() {\n    return "grid";',
        'mCobraTvDrawerPreviousFocus=getCurrentFocus();',
        'panel.post(()->cobraTvFocusDrawer(panel));',
        'if(cobraTvHandleDrawerKey(event))return true;',
        'return "60";',
        'private boolean cobraWantsFullscreenPip(){\n  return false;',
        'private boolean cobraTouchFirstDevice() {\n    return false;',
    ):
        require(token in s,'TV source gate missing: '+token)
    for forbidden in (
        'DISPLAY & PERFORMANCE  •',
        'BACKGROUND MODE  •',
        'PLAY IN BACKGROUND  •',
        'FILE PICKER  •',
        'cobraAddDetail(rows,"pip","Picture-in-picture"',
        'cobraAddDetail(rows,"audio","Play in background"',
        'cobraAddDetail(rows,"audio","Media During Calls"',
        'cobraDrawerView(items);',
        '"Choose one of five view modes"',
        'android:supportsPictureInPicture="true"',
    ):
        require(forbidden not in (s+m),'TV-only surface still exposed: '+forbidden)
    require(m.count('android:supportsPictureInPicture="false"')>=1,'PiP manifest was not disabled')

    # Update exact source receipt hashes only for the generated files changed in 2103220.
    for rel in (SOURCE+'build.gradle.in',SOURCE+'AndroidManifest.xml.in',SOURCE+'src/InfinityLiveActivity.java.in'):
        require(rel in receipt['files'],'Source receipt missing '+rel)
        receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
        version_code=VERSION,
        version_name=NEW_NAME,
        source_parent=OLD_VERSION,
        candidate_locked=False,
        physical_device_verified=False,
        runtime_device_tested=False,
        tv_variant=True,
        tv_target='onn. 4K Pro / Google TV',
        tv_target_abi='armeabi-v7a',
        tv_grid_only=True,
        tv_drawer_focus_owned=True,
        tv_drawer_current_destination_focus=True,
        tv_drawer_focus_trapped=True,
        tv_safe_grid_geometry=True,
        tv_settings_removed=['display_performance','background_mode','play_in_background','file_picker'],
        tv_pip_disabled=True,
        tv_rotation_ui_disabled=True,
        tv_calls_ui_disabled=True,
        tv_touch_first_disabled=True,
        tv_refresh_policy='60hz',
        mobile_parent_untouched=True,
        same_package=True,
        same_signer_required=True,
        playback_feature_set_preserved=True,
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():
        require(sha(shell/name)==row['after'],'Final 2103220 source receipt drift: '+name)

    Path('audit220').mkdir(exist_ok=True)
    Path('audit220/tv-grid-source.json').write_text(json.dumps({
        'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,
        'target':'onn. 4K Pro / Google TV','target_abi':'armeabi-v7a',
        'scope':'TV-only Grid + remote + phone-feature cleanup',
        'mobile_fold_untouched':True,
        'grid_only':True,'drawer_focus_owned':True,'drawer_restores_focus':True,
        'permanent_grid_side_rail':False,'permanent_grid_directory':False,
        'display_performance_setting':False,'background_mode_setting':False,
        'play_in_background_setting':False,'file_picker_setting':False,
        'pip_enabled':False,'rotation_control':False,'media_during_calls_setting':False,
        'refresh_policy':'60hz','touch_first':False,
        'marker':'cobra_tv_grid_only_2103220','physical_device_verified':False,
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103220 TV-only Grid/remote simplification applied; ARM64/mobile source untouched')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__': main()
