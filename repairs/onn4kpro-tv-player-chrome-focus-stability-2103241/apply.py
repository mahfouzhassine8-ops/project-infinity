#!/usr/bin/env python3
"""2103241 RC21 — TV player chrome/focus/back stability over locked RC20.

Scope:
- Restore the intended fullscreen player chrome inactivity timeout/fade that RC21 audit proved was
  disabled by an empty scheduleChromeHide().
- Keep open player menus visible; interaction re-shows chrome and restarts the inactivity timer.
- Back hierarchy: submenu -> player chrome; visible chrome -> hide only; hidden chrome -> exit fullscreen.
- Repair Channel playback vertical focus with one post-layout focus owner and explicit linear row links.
- Suppress remote-bounce double Play/Pause toggles and recover only confirmed NON-USER unexpected
  playWhenReady=false events while fullscreen TV playback remains active.
- Buffering itself remains observation-only: no media-item replacement, prepare/restart, forced live seek,
  parser change, timeshift rewrite or native-engine change.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103241
OLD_VERSION=2103240
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Search-Remote-Hardening-RC20'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Player-Chrome-Focus-Stability-RC21'
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
    req('cobra_tv_movies_landing_search_2103240' in s and 'COBRA_TV_REMOTE_EDGE_GUARD_MS=120L' in s,'Expected exact locked RC20 TV source')
    req('private void scheduleChromeHide()' in s,'Player chrome timer method missing')
    req('mMain.removeCallbacks(mHideChrome);' in member(s,'scheduleChromeHide'),'Expected disabled RC20 chrome timer')
    req('cobra-channel-restart-live' in member(s,'cobraShowChannelPreferences'),'Channel playback menu missing')
    req('buffer_observed_no_restart' in s,'Observation-only stall policy missing')

    protected_methods=[
      'playChannel','startCobraPreview','promoteCobraPreviewToFullscreen','cobraReturnToMultiFromFullscreen',
      'setMultiAudio','cobraLayoutPlayerPanels','cobraTvChannelPlaybackState','cobraTvChannelPlaying',
      'cobraTvPlayingDotColor','cobraTvHandleDrawerKey','cobraDirectory','cobraTvHandleGuideKey',
      'cobraLayoutGuide','cobraRenderGuideBrowser','cobraBuildPlayerChrome','cobraTvPlayerFocusGraph',
      'cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraRecoverTimeshiftStall',
      'cobraStartProviderCatchup','cobraGoLive','cobraTimeshiftSeconds','cobraUpdateTimeshiftSeek',
      'cobraAttachVideo','cobraStartDirectSinglePlayer','cobraStartDirectPreview','mediaItem','buildPlayer'
    ]
    protected={n:hb(member(s,n).strip()) for n in protected_methods}
    dot_hash=hb(member(s,'CobraTvPlayingDot','class'))
    watchdog=s[s.index('private final Runnable mStallWatchdog'):s.index('private final Runnable mAutoRefresh')]
    watchdog_hash=hb(watchdog)

    helpers=r'''  private static final long COBRA_TV_TRANSPORT_TOGGLE_GUARD_MS=220L;
  private int mCobraSheetFocusEpoch=0;
  private boolean mCobraTvPlayerUserPaused=false;
  private long mCobraTvLastTransportToggleAt=0L;
  private int mCobraTvUnexpectedPauseRecoveries=0;

  private void cobraTvWireLinearFocus(View... views){
    ArrayList<View> rows=new ArrayList<>();
    if(views!=null)for(View row:views)if(row!=null&&row.isShown()&&row.isEnabled()&&row.isFocusable()){
      if(row.getId()==View.NO_ID)row.setId(View.generateViewId());rows.add(row);
    }
    for(int i=0;i<rows.size();i++){
      View row=rows.get(i);
      if(i>0)row.setNextFocusUpId(rows.get(i-1).getId());
      if(i+1<rows.size())row.setNextFocusDownId(rows.get(i+1).getId());
    }
  }

  private void cobraTvRecoverUnexpectedPause(ExoPlayer proof,int reason){
    if(proof==null||proof!=mPlayer||mPlayerOverlay==null||mBackgroundStopped||mInPictureInPicture||
        mCobraTvPlayerUserPaused||reason==Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST)return;
    mMain.postDelayed(()->{
      if(proof!=mPlayer||mPlayerOverlay==null||mBackgroundStopped||mInPictureInPicture||
          mCobraTvPlayerUserPaused||proof.getPlayWhenReady()||
          proof.getPlaybackState()==Player.STATE_IDLE||proof.getPlaybackState()==Player.STATE_ENDED)return;
      mCobraTvUnexpectedPauseRecoveries++;
      InfinityCobraDiagnostics.record(this,"tv-player","unexpected-pause-recovery",
          "count="+mCobraTvUnexpectedPauseRecoveries+"; reason="+reason+"; no_restart=true; state="+proof.getPlaybackState());
      cobraUserPlay(proof);
    },280L);
  }

'''
    marker='  private void scheduleChromeHide()'
    req(s.count(marker)==1,'RC21 helper insertion drift')
    s=s.replace(marker,helpers+marker,1)

    s=repl(s,'scheduleChromeHide',r'''  private void scheduleChromeHide() {
    mMain.removeCallbacks(mHideChrome);
    if(mPlayerChrome!=null&&!mCobraPlayerLocked&&!mInPictureInPicture&&
        mCobraActionSheet==null&&mCobraPlayerDrawer==null&&mCobraMultiPicker==null)
      mMain.postDelayed(mHideChrome,CobraPresentationEffects.chromeDelay(cobraNightCinemaActive()));
  }''')

    # One sheet owns initial focus. The old method posted cobraTvFocusFirst(items) twice, which could
    # race the user's first Down press and snap focus back to Recents.
    sheet=member(s,'cobraOpenSheet')
    sheet=once(sheet,
      '    View sheetAnchor=cobraResolveSheetAnchor(kind),sheetPane=cobraResolveSheetPane(sheetAnchor);',
      '    View sheetAnchor=cobraResolveSheetAnchor(kind),sheetPane=cobraResolveSheetPane(sheetAnchor);\n    if(mPlayerOverlay!=null)mMain.removeCallbacks(mHideChrome);',
      'sheet cancels chrome timeout')
    req(sheet.count('items.post(()->cobraTvFocusFirst(items));')==2,'Expected duplicate RC20 sheet focus posts')
    sheet=sheet.replace('items.post(()->cobraTvFocusFirst(items));cobraRefreshVisualEffects();','cobraRefreshVisualEffects();',1)
    sheet=sheet.replace(
      '    items.post(()->cobraTvFocusFirst(items));vtheme().tree(panel,"sheet."+kind);return items;',
      '    final int focusEpoch=++mCobraSheetFocusEpoch;items.post(()->{if(focusEpoch==mCobraSheetFocusEpoch&&items.isAttachedToWindow())cobraTvFocusFirst(items);});vtheme().tree(panel,"sheet."+kind);return items;',
      1)
    s=repl(s,'cobraOpenSheet',sheet)

    close_sheet=member(s,'closeCobraActionSheet')
    close_sheet=once(close_sheet,'    if(mCobraActionSheet==null)return false;',
      '    if(mCobraActionSheet==null)return false;\n    mCobraSheetFocusEpoch++;',
      'cancel stale sheet focus')
    close_sheet=once(close_sheet,
      '    if(mCobraSheetPreviousFocus!=null&&mCobraSheetPreviousFocus.isAttachedToWindow())mCobraSheetPreviousFocus.requestFocus();',
      '    if(mCobraSheetPreviousFocus!=null&&mCobraSheetPreviousFocus.isAttachedToWindow()&&mCobraSheetPreviousFocus.getWindowToken()!=null&&mCobraSheetPreviousFocus.isShown()&&mCobraSheetPreviousFocus.isEnabled()&&mCobraSheetPreviousFocus.isFocusable())mCobraSheetPreviousFocus.requestFocus();',
      'safe sheet focus restore')
    s=repl(s,'closeCobraActionSheet',close_sheet)

    prefs=member(s,'cobraShowChannelPreferences')
    prefs=once(prefs,
      '    cobraInfoText(rows,"Channel preferences apply to this channel, source and profile. Display is in the video toolbar. Language preferences are in Audio & subtitles.");',
      '''    cobraTvWireLinearFocus(
        rows.findViewWithTag("cobra-channel-recents"),
        rows.findViewWithTag("cobra-channel-restart-live"),
        rows.findViewWithTag("cobra-channel-rewind"),
        rows.findViewWithTag("cobra-channel-fallback"),
        rows.findViewWithTag("cobra-channel-recovery"),
        rows.findViewWithTag("cobra-channel-reset"));
    cobraInfoText(rows,"Channel preferences apply to this channel, source and profile. Display is in the video toolbar. Language preferences are in Audio & subtitles.");''',
      'channel playback linear focus graph')
    s=repl(s,'cobraShowChannelPreferences',prefs)

    s=repl(s,'toggleCobraPlayerPlayPause',r'''  private void toggleCobraPlayerPlayPause() {
    if(mPlayer==null||mCobraPlayerLocked)return;
    long now=android.os.SystemClock.uptimeMillis();
    if(now-mCobraTvLastTransportToggleAt<COBRA_TV_TRANSPORT_TOGGLE_GUARD_MS)return;
    mCobraTvLastTransportToggleAt=now;
    if(mPlayer.isPlaying()||mPlayer.getPlayWhenReady()){
      mCobraTvPlayerUserPaused=true;mPlayer.pause();
    }else{
      mCobraTvPlayerUserPaused=false;cobraUserPlay(mPlayer);
    }
    updateCobraPlayerPlayPause();showPlayerChromeTemporarily();
  }''')

    binding=member(s,'CobraPlayerBinding',kind='class')
    binding=once(binding,
'''    @Override public void onPlayWhenReadyChanged(boolean requested,int reason){if(current()){
      if(!requested&&(!mBackgroundStopped||reason!=Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST)){mCobraPlaybackPolicy.epoch++;mBackgroundResumePlayers.remove(player);}
      if(player==mPlayer)configureCobraPip(requested);cobraPublishMiniState();
    }}''',
'''    @Override public void onPlayWhenReadyChanged(boolean requested,int reason){if(current()){
      if(player==mPlayer&&requested)mCobraTvPlayerUserPaused=false;
      if(!requested&&(!mBackgroundStopped||reason!=Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST)){mCobraPlaybackPolicy.epoch++;mBackgroundResumePlayers.remove(player);}
      if(player==mPlayer&&!requested)cobraTvRecoverUnexpectedPause(player,reason);
      if(player==mPlayer)configureCobraPip(requested);cobraPublishMiniState();
    }}''',
'non-user pause intent recovery')
    s=repl(s,'CobraPlayerBinding',binding,kind='class')

    s=repl(s,'cobraTvHandlePlayerKey',r'''  private boolean cobraTvHandlePlayerKey(KeyEvent event){
    if(event.getAction()!=KeyEvent.ACTION_DOWN||mPlayerOverlay==null||mCobraPlayerLocked)return false;
    int code=event.getKeyCode();
    if(mCobraPlayerDrawer!=null){if(code==KeyEvent.KEYCODE_BACK||code==KeyEvent.KEYCODE_DPAD_LEFT){closeCobraPlayerDrawer();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}return false;}
    if(mCobraMultiPicker!=null){if(code==KeyEvent.KEYCODE_BACK){closeCobraMultiPicker(false);showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}return false;}
    if(mCobraActionSheet!=null){if(code==KeyEvent.KEYCODE_BACK){closeCobraActionSheet();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}return false;}
    if(code==KeyEvent.KEYCODE_MENU){if(mCobraMultiFullscreenActive){cobraReturnToMultiFromFullscreen();return true;}if(cobraOnDemandPlayer())showPlayerSettingsDrawer();else showCobraPlayerDrawer();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE){toggleCobraPlayerPlayPause();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_REWIND){if(cobraOnDemandPlayer())return cobraSeekOnDemandBy(-30000L);cobraRewindLive(30000L);return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_FAST_FORWARD){if(cobraOnDemandPlayer())return cobraSeekOnDemandBy(30000L);if(!cobraTvNudgeTimeline(1))cobraGoLive();return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_UP&&!mCobraMultiFullscreenActive){if(cobraOnDemandPlayer())return true;stepChannel(1);return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_DOWN&&!mCobraMultiFullscreenActive){if(cobraOnDemandPlayer())return true;stepChannel(-1);return true;}
    if(code==KeyEvent.KEYCODE_BACK){
      if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE){cobraTvHidePlayerChrome();return true;}
      return false;
    }
    View focus=getCurrentFocus();boolean inChrome=mPlayerChrome!=null&&cobraTvViewInside(mPlayerChrome,focus);
    if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE&&inChrome&&(code==KeyEvent.KEYCODE_DPAD_UP||code==KeyEvent.KEYCODE_DPAD_DOWN))
      if(cobraTvPlayerFocusGraph(code))return true;
    if(code==KeyEvent.KEYCODE_DPAD_CENTER||code==KeyEvent.KEYCODE_ENTER||code==KeyEvent.KEYCODE_DPAD_UP||code==KeyEvent.KEYCODE_DPAD_DOWN||code==KeyEvent.KEYCODE_DPAD_LEFT||code==KeyEvent.KEYCODE_DPAD_RIGHT){
      if(mPlayerChrome==null||mPlayerChrome.getVisibility()!=View.VISIBLE||!inChrome){showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}
    }
    return false;
  }''')

    back=member(s,'onBackPressed')
    back=once(back,
      '    if(mCobraPlayerDrawer!=null){if(mCobraDrawerFilter.startsWith("GROUP:")){cobraRenderPlayerDrawer("CATEGORIES");return;}closeCobraPlayerDrawer();return;}',
      '    if(mCobraPlayerDrawer!=null){if(mCobraDrawerFilter.startsWith("GROUP:")){cobraRenderPlayerDrawer("CATEGORIES");return;}closeCobraPlayerDrawer();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return;}',
      'Back from player drawer returns chrome')
    back=once(back,
      '    if(mPlayerOverlay!=null){closeFullscreenToCobraView();return;}',
      '    if(mPlayerOverlay!=null){if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE){cobraTvHidePlayerChrome();return;}closeFullscreenToCobraView();return;}',
      'Back hide chrome before fullscreen exit')
    s=repl(s,'onBackPressed',back)

    # Scope/preservation gates.
    for n,h in protected.items():req(hb(member(s,n).strip())==h,'Protected playback/timeshift/TV method changed: '+n)
    req(hb(member(s,'CobraTvPlayingDot','class'))==dot_hash,'RC16 pulsing dot changed')
    watchdog_after=s[s.index('private final Runnable mStallWatchdog'):s.index('private final Runnable mAutoRefresh')]
    req(hb(watchdog_after)==watchdog_hash,'Observation-only stall watchdog changed')
    req('buffer_observed_no_restart' in watchdog_after and 'mPlayer.prepare()' not in watchdog_after,'Buffer watchdog restart regression')
    req('mMain.postDelayed(mHideChrome,CobraPresentationEffects.chromeDelay(cobraNightCinemaActive()))' in member(s,'scheduleChromeHide'),'Chrome inactivity timer not restored')
    req(member(s,'cobraOpenSheet').count('cobraTvFocusFirst(items)')==1,'Sheet retains duplicate initial focus post')
    req('cobraTvWireLinearFocus' in member(s,'cobraShowChannelPreferences'),'Channel playback linear focus missing')
    req('if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE){cobraTvHidePlayerChrome();return true;}' in member(s,'cobraTvHandlePlayerKey'),'First Back does not dismiss chrome')
    req('closeFullscreenToCobraView();return;' in member(s,'onBackPressed'),'Second Back fullscreen exit lost')
    req('COBRA_TV_TRANSPORT_TOGGLE_GUARD_MS=220L' in s,'Play/Pause remote-bounce guard missing')
    req('reason!=Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST' in s and 'unexpected-pause-recovery' in s,'Non-user pause recovery missing')
    req('cobra_tv_movies_landing_search_2103240' in s and 'COBRA_TV_REMOTE_EDGE_GUARD_MS=120L' in s,'RC20 search/remote hardening lost')
    req('AMBIENT MODE  •' not in s,'TV Ambient Mode returned')
    path.write_text(s)
    return hb(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked RC20 source parent')
    req(receipt.get('tv_vod_landing_search_inline') is True and receipt.get('tv_remote_crash_hardening') is True,'RC20 search/remote baseline missing')
    req(receipt.get('tv_live_structure_unchanged') is True and receipt.get('playback_engine_unchanged') is True,'RC20 playback preservation missing')
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
      tv_player_chrome_auto_hide_restored=True,tv_player_chrome_uses_existing_delay_policy=True,
      tv_player_menu_holds_chrome=True,tv_player_back_first_hides_chrome=True,tv_player_back_second_exits=True,
      tv_channel_playback_linear_focus=True,tv_channel_playback_single_initial_focus_post=True,
      tv_sheet_stale_focus_cancelled=True,tv_sheet_focus_restore_attachment_guard=True,
      tv_transport_toggle_guard_ms=220,tv_transport_duplicate_toggle_suppressed=True,
      tv_unexpected_non_user_pause_recovery=True,tv_unexpected_pause_recovery_delay_ms=280,
      tv_unexpected_pause_no_restart=True,tv_buffering_policy_observation_only=True,
      tv_buffering_media_restart_forbidden=True,tv_timeshift_engine_unchanged=True,
      tv_player_engine_unchanged=True,tv_remote_crash_hardening=True,tv_live_structure_unchanged=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    out=Path('audit241');out.mkdir(exist_ok=True)
    (out/'tv-player-chrome-focus-stability-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,
      'player_chrome':{
        'auto_hide_restored':True,'existing_delay_policy':True,'menus_hold_visible':True,
        'back_first_hides':True,'back_second_exits':True
      },
      'channel_playback_focus':{
        'linear':True,'single_initial_focus_post':True,
        'order':['Recents','Restart live playback','Live TV Rewind','Configured stream fallback','Automatic video-surface recovery','Reset this channel']
      },
      'pause_buffer_safety':{
        'transport_toggle_guard_ms':220,'recover_non_user_pause_only':True,'recovery_delay_ms':280,
        'buffering_observation_only':True,'media_restart_forbidden':True,'prepare_forbidden':True,
        'timeshift_engine_unchanged':True
      },
      'preservation':{
        'live_tv_structure_unchanged':True,'playback_engine_unchanged':True,
        'native_engine_rebuilt':False,'mobile_fold_untouched':True
      },
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103241 RC21 player chrome/focus/back stability applied over exact locked RC20')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
