#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
MANIFEST=Path('tools/android/packaging/xbmc/AndroidManifest.xml.in')
BOOT='android.permission.RECEIVE_BOOT_COMPLETED'
BASE_COMMIT='b5fa21731a1662cc7206ac6dc45cb6d6682612cd'

def require(v,msg):
    if not v: raise RuntimeError(msg)

def block(text,name,kind='method'):
    pat=(re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
         if kind=='method' else re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M))
    ms=list(pat.finditer(text));require(len(ms)==1,f'{name} cardinality={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=comment=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif comment:
            if c=='*' and n=='/': comment=False;i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':comment=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return text[start:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--patch',type=Path,required=True)
    p.add_argument('--packager',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    text=(a.source/ACT).read_text()
    manifest=(a.source/MANIFEST).read_text()
    receipt=json.loads(a.receipt.read_text())
    patch=json.loads(a.patch.read_text())
    packager=a.packager.read_text()
    player=block(text,'showPlayerSettingsDrawer')
    chrome=block(text,'cobraBuildPlayerChrome')
    settings=block(text,'showSettings')
    channel=block(text,'cobraShowChannelAspect')
    pref=block(text,'CobraPreferencePolicy','class')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    boot_count=len(re.findall(r'<uses-permission\s+android:name="'+re.escape(BOOT)+r'"\s*/>',manifest))
    checks={
      'exact_2103197_parent':receipt.get('source_parent')==2103197 and receipt.get('source_parent_commit')==BASE_COMMIT,
      'locked_parent_canonical':receipt.get('locked_parent')==2103197 and receipt.get('locked_parent_commit')==BASE_COMMIT,
      'version_2103198':receipt.get('version_code')==2103198 and receipt.get('version_name')=='1.0.9-Cobra-Complete-Product-Audit-RC1',
      'boot_permission_unique':boot_count==1,
      'packager_normalizes_historical_duplicate':'old_boot' in packager and 'new_boot' in packager and 'Inherited base must contain exactly two boot permissions' in packager,
      'original_player_menu':all(x in player for x in ('Player settings','Channel playback','Health Center','Audio & subtitles','Aspect / Display','Cast / Route','Manage sources','Close player')),
      'no_duplicate_player_hub':all(x not in text for x in ('showCobraPlayerOptionsHub','cobraAddRecentPlayerStrip','RECENT CHANNELS','cobra-player-hub-')),
      'no_video_display_submenu':'showCobraVideoOptions' not in text and 'Video & display' not in player,
      'canonical_four_button_toolbar':'String[] glyphs={"guide","aspect","multi","more"},labels={"Channels","Display","Multi-View","More"};' in chrome,
      'toolbar_not_expanded':'expandedTools' not in chrome and '"Options"' not in chrome,
      'player_motion_preserved':'chrome.setTranslationY(dp(8))' in chrome and 'DecelerateInterpolator' in chrome,
      'sheet_motion_preserved':'setScaleX(.985f)' in block(text,'cobraOpenSheet') and 'DecelerateInterpolator' in block(text,'cobraOpenSheet'),
      'focus_motion_preserved':'setOnFocusChangeListener' in block(text,'cobraPolishFocusable') and 'focused?1.018f:1f' in block(text,'cobraPolishFocusable'),
      'settings_stagger':'cobraAnimateChildrenIn(list)' in settings,
      'source_manager_preserved':'cobra_tv_sources' in text and 'TV SOURCES' in text and '+  ADD TV SOURCE' in text,
      'source_refresh_controls':all(x in text for x in ('REFRESH CURRENT SOURCE','REFRESH ALL ENABLED SOURCES')),
      'five_views_preserved':all(x in text for x in ('"mobile"','"grid"','"compact"','"cards"','"focus"')),
      'appearance_modes_preserved':all(x in text for x in ('cobra_appearance_mode','cobra_system_dark_variant','"light"','"dark"','"oled"')),
      'theme_management_preserved':'cobra_theme_management' in text,
      'background_mode_preserved':'cobra_background_mode' in text and 'cobra-background-mode:normal' in text and 'cobra-background-mode:extended' in text,
      'health_center_preserved':'Cobra Health Center' in text and 'Playback defaults' in text,
      'display_refresh_modes':all(x in text for x in ('"auto"','"60"','"90"','"120"','"max"')) and 'preferredDisplayModeId' in text,
      'power_thermal_safety':'isPowerSaveMode()' in text and 'THERMAL_STATUS_SEVERE' in text,
      'fold_adaptive_preserved':'CobraFoldAspectPolicy' in text and 'case 12: return "Fold Adaptive"' in block(text,'cobraAspectLabel'),
      'fold_channel_persistence':'value<=CobraFoldAspectPolicy.MODE' in pref,
      'fold_global_persistence':'mode<=CobraFoldAspectPolicy.MODE' in block(text,'cobraChannelAspect'),
      'fold_first_live':'final int[] modes={CobraFoldAspectPolicy.MODE,-1,0,1' in channel,
      'statusbar_surface_contract':all(x in text for x in ('cobra-browse-background','cobra-browse-safe-content','cobraApplySystemBarsForSurface')),
      'pip_contract':'onPictureInPictureModeChanged' in text and 'isCobraInPictureInPicture' in text,
      'background_resume_contract':'InfinityExtendedBackgroundService' in text and 'mBackgroundStopped' in text,
      'timeshift_runtime':all(x in text for x in ('CobraLocalTimeshiftSession','CobraTimeshiftIngest','CobraTimeshiftServer')),
      'timeshift_loopback_only':'127.0.0.1' in text and '/live.m3u8' in text,
      'timeshift_bounded':all(x in text for x in ('maxSegments','storageSegments','maxBytes')),
      'provider_catchup_preserved':'tv_archive' in text and 'tv_archive_duration' in text and 'cobraStartProviderCatchup' in text,
      'network_family_control':all(x in text for x in ('TRANSPORT_VPN','network_transport','timeshift_provider_protocol')),
      'pace_guard_preserved':'timeshift_provider_pace_limited' in text and 'REWRITE_ENABLED=false' in text,
      'parser_preserved':'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES' in text,
      'watchdog_observation_only':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'diagnostics_preserved':all(x in text for x in ('rebuffer_events','long_stalls','last_media_load_kbps')),
      'activity_runtime_unchanged':patch.get('activity_runtime_changed') is False,
      'playback_unchanged':patch.get('playback_behavior_changed') is False,
      'network_unchanged':patch.get('network_selection_changed') is False,
      'timeshift_unchanged':patch.get('timeshift_ownership_changed') is False,
      'buffer_unchanged':patch.get('buffer_policy_changed') is False,
      'parser_unchanged':patch.get('parser_flags_changed') is False,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'acceptance_flags_canonical':receipt.get('tivimate_inspired_player_hub') is False and receipt.get('recent_channel_strip') is False,
      'release_metadata_reconciled':receipt.get('release_metadata_reconciled') is True,
      'current_device_guide':receipt.get('device_test_guide_current') is True,
      'physical_unverified':receipt.get('physical_device_verified') is False
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103198,'check_count':len(checks),'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103198 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'complete-product source checks; physical device remains separate')

if __name__=='__main__':main()
