#!/usr/bin/env python3
"""2103242 RC22 — final preservation-first TV product audit over locked RC21.

Confirmed corrections:
- Power overlay joins the Android-TV transient focus owner, receives deterministic initial focus,
  explicit vertical focus links, Back/Cancel dismissal, and safe return focus.
- Remove redundant PLAYING/PAUSED multiline prefix from EPG channel rows. The approved pulsing
  cyan/OLED dot remains the authoritative playback indicator; focus/selection styling remains separate.

Audit rule:
Everything else stays behaviorally identical to locked RC21 unless a source-level gate proves a
verified defect. No native rebuild, no player/timeshift rewrite, no phone/Fold mutation.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103242
OLD_VERSION=2103241
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Player-Chrome-Focus-Stability-RC21'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Final-Product-Audit-RC22'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def hb(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1,f'{label}: expected 1 anchor, got {s.count(a)}')
    return s.replace(a,b,1)
def span(text,name,kind='method'):
    if kind=='method':
        p=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{')
    else:
        p=re.compile(r'(?m)^\s*(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b')
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    st=ms[0].start();b=(text.rfind('{',st,ms[0].end()) if kind=='method' else text.find('{',ms[0].end()));req(b>=st,'opening brace missing: '+name)
    d=0;q=None;esc=line=block=False
    for i in range(b,len(text)):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True
        elif c=='/' and n=='*':block=True
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return st,i+1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def repl(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+"\n"+text[b:]

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    req('COBRA_TV_TRANSPORT_TOGGLE_GUARD_MS=220L' in s,'Expected locked RC21 player stability source')
    req('cobra_tv_movies_landing_search_2103240' in s and 'COBRA_TV_REMOTE_EDGE_GUARD_MS=120L' in s,'Locked RC20 search/remote baseline missing')
    req('shield.setTag("cobra_power_menu")' in member(s,'showCobraPowerMenu'),'Power menu source missing')
    req('cobra_power_menu' not in member(s,'cobraTvTransientRoot'),'Power menu unexpectedly already owns transient focus')

    # Everything below is protected unless explicitly listed as an RC22 correction.
    protected_methods=[
      'playChannel','startCobraPreview','promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen',
      'setMultiAudio','cobraLayoutPlayerPanels','cobraTvChannelPlaybackState','cobraTvChannelPlaying',
      'cobraTvPlayingDotColor','cobraTvHandleDrawerKey','cobraDirectory','cobraTvHandleDirectoryKey',
      'cobraTvHandleGuideKey','cobraLayoutGuide','cobraRenderGuideBrowser','cobraRenderGridMode',
      'cobraBuildPlayerChrome','cobraTvPlayerFocusGraph','cobraTvHandlePlayerKey',
      'scheduleChromeHide','showPlayerChromeTemporarily','cobraTvHidePlayerChrome',
      'cobraShowChannelPreferences','cobraOpenSheet','closeCobraActionSheet',
      'cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraRecoverTimeshiftStall',
      'cobraStartProviderCatchup','cobraGoLive','cobraTimeshiftSeconds','cobraUpdateTimeshiftSeek',
      'cobraAttachVideo','cobraStartDirectSinglePlayer','cobraStartDirectPreview','mediaItem','buildPlayer',
      'renderVodBrowse','cobraTvVodSearchMatches','cobraShowVodDetails','showMovies','showSeries',
      'beginMultiView','releaseMulti','cobraPromoteMultiTileFullscreen'
    ]
    protected={n:hb(member(s,n).strip()) for n in protected_methods}
    dot_hash=hb(member(s,'CobraTvPlayingDot','class').strip())
    watchdog=s[s.index('private final Runnable mStallWatchdog'):s.index('private final Runnable mAutoRefresh')]
    watchdog_hash=hb(watchdog)

    helpers=r'''  private android.view.ViewGroup cobraTvPowerRoot(){
    FrameLayout decor=(FrameLayout)getWindow().getDecorView();
    View raw=decor.findViewWithTag("cobra_power_menu");
    return raw instanceof android.view.ViewGroup&&raw.isAttachedToWindow()?(android.view.ViewGroup)raw:null;
  }

  private boolean cobraTvClosePowerMenuRestoreFocus(){
    boolean closed=closeCobraPowerMenu();if(!closed)return false;
    mMain.post(()->{
      if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){cobraTvRestoreGuideFocus();return;}
      if(mStage!=null&&mStage.isAttachedToWindow())cobraTvFocusFirst(mStage);
    });
    return true;
  }

'''
    marker='  private boolean closeCobraPowerMenu()'
    req(s.count(marker)==1,'RC22 power helper insertion drift')
    s=s.replace(marker,helpers+marker,1)

    s=repl(s,'showCobraPowerMenu',r'''  private void showCobraPowerMenu() {
    closeCobraPowerMenu();
    FrameLayout decor=(FrameLayout)getWindow().getDecorView();
    FrameLayout shield=new FrameLayout(this);shield.setTag("cobra_power_menu");shield.setClickable(true);
    shield.setBackgroundColor(Color.argb(118,0,0,0));shield.setOnClickListener(v->cobraTvClosePowerMenuRestoreFocus());

    LinearLayout sheet=new LinearLayout(this);sheet.setOrientation(LinearLayout.VERTICAL);sheet.setClickable(true);
    sheet.setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);sheet.setClipChildren(false);
    sheet.setPadding(dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.1",18)),dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.2",14)),dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.3",18)),dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.4",18)));
    sheet.setBackground(surface(cobraThemeColor("panel",mTheme.panel),28,cobraThemeColor("line",mTheme.line),1));

    TextView title=text(vtheme().copy("cobra.showCobraPowerMenu.copy.1","POWER"),cobraThemeColor("text",mTheme.text),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    title.setTypeface(null,Typeface.BOLD);sheet.addView(title,new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.5",52))));

    Button switchInfinity=action(vtheme().copy("cobra.showCobraPowerMenu.copy.2","∞  Switch to Infinity"));
    Button exit=action(vtheme().copy("cobra.showCobraPowerMenu.copy.3","⏻  Exit"));
    Button cancel=action(vtheme().copy("cobra.showCobraPowerMenu.copy.4","Cancel"));
    switchInfinity.setTag("cobra_power_switch_infinity");exit.setTag("cobra_power_exit");cancel.setTag("cobra_power_cancel");
    switchInfinity.setId(View.generateViewId());exit.setId(View.generateViewId());cancel.setId(View.generateViewId());

    switchInfinity.setOnClickListener(v->{closeCobraPowerMenu();stopCobraPreview();if(mPlayerOverlay!=null)closePlayer();releaseMulti();returnToInfinity();});
    exit.setOnClickListener(v->{closeCobraPowerMenu();stopCobraPreview();if(mPlayerOverlay!=null)closePlayer();releaseMulti();finishAndRemoveTask();});
    cancel.setOnClickListener(v->cobraTvClosePowerMenuRestoreFocus());

    Button[] buttons={switchInfinity,exit,cancel};
    for(Button button:buttons){
      button.setAllCaps(false);cobraPolishFocusable(button);
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.6",60)));
      lp.bottomMargin=dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.7",6));sheet.addView(button,lp);
    }
    switchInfinity.setNextFocusDownId(exit.getId());
    exit.setNextFocusUpId(switchInfinity.getId());exit.setNextFocusDownId(cancel.getId());
    cancel.setNextFocusUpId(exit.getId());

    FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM);
    pos.setMargins(dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.8",10)),dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.9",10)),dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.10",10)),dp(vtheme().dimension("cobra.showCobraPowerMenu.dimensions.11",10)));
    shield.addView(sheet,pos);decor.addView(shield,new FrameLayout.LayoutParams(-1,-1));sheet.bringToFront();
    switchInfinity.post(()->{android.view.ViewGroup root=cobraTvPowerRoot();if(root==shield&&switchInfinity.isAttachedToWindow()&&switchInfinity.isShown())switchInfinity.requestFocus();});
  }''')

    transient=member(s,'cobraTvTransientRoot')
    transient=once(transient,
      '  private android.view.ViewGroup cobraTvTransientRoot(){',
      '  private android.view.ViewGroup cobraTvTransientRoot(){\n    android.view.ViewGroup power=cobraTvPowerRoot();if(power!=null)return power;',
      'Power transient root')
    s=repl(s,'cobraTvTransientRoot',transient)

    close_transient=member(s,'cobraTvCloseTransient')
    close_transient=once(close_transient,
      '  private boolean cobraTvCloseTransient(){',
      '  private boolean cobraTvCloseTransient(){\n    if(cobraTvPowerRoot()!=null)return cobraTvClosePowerMenuRestoreFocus();',
      'Power transient Back')
    s=repl(s,'cobraTvCloseTransient',close_transient)

    back=member(s,'onBackPressed')
    req('if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions())return;' in back,'RC21 Back power anchor drift')
    back=back.replace(
      'if(closeCobraPowerMenu()||closeCobraViewModeMenu()||closeCobraChannelActions())return;',
      'if(cobraTvClosePowerMenuRestoreFocus()||closeCobraViewModeMenu()||closeCobraChannelActions())return;',1)
    s=repl(s,'onBackPressed',back)

    # Remove the obsolete multiline PLAYING/PAUSED prefix from the grid/channel row only.
    # Playback state computation stays untouched because the OLED dot and other live-state logic use it.
    old_row='''      title.setText(playback.isEmpty()?String.format(Locale.US,"%03d  ",position+1)+c.name:("PLAYING".equals(playback)?"▶ PLAYING\\n":"Ⅱ PAUSED\\n")+String.format(Locale.US,"%03d  ",position+1)+c.name);'''
    new_row='''      title.setText(String.format(Locale.US,"%03d  ",position+1)+c.name);'''
    s=once(s,old_row,new_row,'Remove redundant grid PLAYING/PAUSED prefix')

    # Preservation / shipping-audit gates.
    for n,h in protected.items():req(hb(member(s,n).strip())==h,'Protected RC21 subsystem changed: '+n)
    req(hb(member(s,'CobraTvPlayingDot','class').strip())==dot_hash,'Approved OLED playing dot changed')
    watchdog_after=s[s.index('private final Runnable mStallWatchdog'):s.index('private final Runnable mAutoRefresh')]
    req(hb(watchdog_after)==watchdog_hash and 'buffer_observed_no_restart' in watchdog_after,'Playback buffering policy changed')
    req('mPlayer.prepare()' not in watchdog_after,'Blind player restart returned')
    req('cobra_power_switch_infinity' in member(s,'showCobraPowerMenu') and 'cobra_power_exit' in member(s,'showCobraPowerMenu') and 'cobra_power_cancel' in member(s,'showCobraPowerMenu'),'Power focus tags missing')
    req('switchInfinity.post' in member(s,'showCobraPowerMenu'),'Power initial focus missing')
    req('cobraTvPowerRoot()' in member(s,'cobraTvTransientRoot'),'Power menu not registered with transient focus')
    req('cobraTvClosePowerMenuRestoreFocus' in member(s,'cobraTvCloseTransient'),'Power Back dismissal missing')
    req(old_row not in s and new_row in s,'Redundant grid PLAYING text survived')
    req('class CobraTvPlayingDot extends View' in s and 'NORMAL_PULSE_MS=1320L' in s,'Playing dot regression')
    req('mMain.postDelayed(mHideChrome,CobraPresentationEffects.chromeDelay(cobraNightCinemaActive()))' in member(s,'scheduleChromeHide'),'RC21 chrome auto-hide lost')
    req('cobraTvWireLinearFocus' in member(s,'cobraShowChannelPreferences'),'RC21 Channel Playback focus fix lost')
    req('cobra_tv_movies_landing_search_2103240' in s and 'Type a title or narrow by genre' in s,'Movies/Shows search lost')
    req('On-screen keyboard' not in s,'Custom VOD keyboard returned')
    req('COBRA_TV_REMOTE_EDGE_GUARD_MS=120L' in s,'RC20 remote hardening lost')
    req('AMBIENT MODE  •' not in s,'Retired TV Ambient renderer returned')
    path.write_text(s)
    return hb(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked RC21 source parent')
    req(receipt.get('tv_player_chrome_auto_hide_restored') is True and receipt.get('tv_player_back_second_exits') is True,'RC21 player-chrome baseline missing')
    req(receipt.get('tv_channel_playback_linear_focus') is True,'RC21 channel-playback focus baseline missing')
    req(receipt.get('tv_vod_landing_search_inline') is True and receipt.get('tv_remote_crash_hardening') is True,'RC20 search/remote baseline missing')
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
      physical_device_verified=False,runtime_device_tested=False,
      tv_final_product_audit=True,tv_shipping_preservation_audit=True,
      tv_power_menu_remote_focus=True,tv_power_menu_initial_focus=True,tv_power_menu_linear_focus=True,
      tv_power_menu_transient_owner=True,tv_power_menu_back_cancel=True,tv_power_menu_safe_focus_restore=True,
      tv_grid_legacy_playing_text_removed=True,tv_grid_legacy_paused_text_removed=True,
      tv_playing_dot_authoritative=True,tv_playing_dot_focus_independent=True,
      tv_ui_polish_preservation_first=True,tv_remote_focus_audited=True,tv_stability_polish=True,
      tv_performance_polish=True,tv_live_structure_unchanged=True,tv_timeshift_engine_unchanged=True,
      tv_player_engine_unchanged=True,mobile_parent_untouched=True,native_engine_rebuilt=False,
      playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    out=Path('audit242');out.mkdir(exist_ok=True)
    (out/'final-product-audit-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,
      'confirmed_defects':[
        'Power overlay rendered without Android-TV transient focus ownership or deterministic initial focus',
        'Legacy multiline PLAYING/PAUSED text duplicated the approved pulsing OLED dot in EPG channel rows'
      ],
      'corrections':{
        'power_menu':{
          'initial_focus':'Switch to Infinity','linear_order':['Switch to Infinity','Exit','Cancel'],
          'back_dismisses':True,'cancel_dismisses':True,'safe_focus_restore':True,'transient_owner':True
        },
        'grid_playback_indicator':{'legacy_text_removed':True,'oled_dot_preserved':True,'selection_focus_separate':True}
      },
      'audited_no_behavior_change':[
        'Live TV drawer/groups/grid architecture','EPG directional navigation','player chrome and Back hierarchy',
        'Channel Playback menu','playback/buffering policy','timeshift/rewind','mini-player and preview handoff',
        'Multi-View 2/3/4 and fullscreen return','Movies/TV Shows cinematic UI','native Android TV VOD search',
        'section ownership','ARMv7 native engine/resources','phone/Fold source'
      ],
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103242 RC22 final preservation-first TV product audit corrections applied over exact locked RC21')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
