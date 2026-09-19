#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
 helper=text[text.index('// 2103177 final feature-freeze:'):]
 checks={
  'display_setting': 'cobra_display_performance' in text and 'DISPLAY & PERFORMANCE' in text,
  'refresh_modes': all(x in helper for x in ['"auto"','"60"','"90"','"120"','"max"']),
  'android_mode_request': 'preferredDisplayModeId' in helper and 'getSupportedModes()' in helper,
  'active_hz_proof': 'cobraDisplayActiveHz()' in helper and 'cobraDisplayMaxHz()' in helper and 'Requested %.2f Hz • Active %.2f Hz • Max %.2f Hz' in helper,
  'fps_proof': 'android.view.Choreographer.FrameCallback' in helper and 'cobra_refresh_proof_overlay' in helper and 'UI %.0f fps' in helper,
  'video_yields_refresh': 'mPlayerOverlay!=null||mMultiOverlay!=null||isCobraInPictureInPicture()' in helper and 'if(video)return 0f' in helper,
  'battery_thermal_fallback': 'isPowerSaveMode()' in helper and 'THERMAL_STATUS_SEVERE' in helper,
  'timeshift_default_off': 'mPrefs.getBoolean(COBRA_LOCAL_TIMESHIFT,false)' in helper,
  'timeshift_bounded': 'WINDOW_MS=120000L' in helper and 'CACHE_CAP_BYTES=160L*1024L*1024L' in helper and 'CACHE_TRIM_BYTES=150L*1024L*1024L' in helper,
  'timeshift_same_player': 'CobraTimeshiftDataSourceFactory' in helper and 'new ExoPlayer' not in helper,
  'timeshift_segments_only': 'segmentUris.contains(uri.toString())' in helper,
  'timeshift_hls_safety': all(x in helper for x in ['#EXT-X-PART','#EXT-X-MAP','#EXT-X-BYTERANGE','#EXT-X-KEY','#EXT-X-DISCONTINUITY']),
  'provider_rewind_preserved': 'tv_archive' in text and 'cobraStartProviderCatchup' in text and 'cobra_live_rewind_30' in text,
  'smart_buffer_auto': 'else control=new DefaultLoadControl();' in text,
  'smart_buffer_resilient': 'setBufferDurationsMs(20000,90000,2500,8000)' in text and 'setPrioritizeTimeOverSizeThresholds(true)' in text,
  'multiview_buffer_preserved': 'setBufferDurationsMs(6000,30000,1500,3000)' in text and '12*1024*1024' in text,
  'watchdog_no_reprepare': 'buffering_observed_12s' in text and 'player was not re-prepared' in text and 'try { mPlayer.prepare(); mPlayer.play(); }' not in text,
  'diagnostics': all(x in text for x in ['rebuffer_count','bandwidth_estimate_bps','buffered_duration_ms','live_offset_ms','network_transport','local_timeshift_ms','cobra_playback_diagnostics_overlay']),
  'network_transport': 'TRANSPORT_VPN' in helper and 'TRANSPORT_WIFI' in helper and 'TRANSPORT_CELLULAR' in helper,
  'last_channel': 'cobra_last_channel' in text and 'CobraLastChannelPolicy' in helper,
  'settings_polish': all(x in text for x in ['cobraSettingsSection("Experience")','cobraSettingsSection("Playback")','cobraSettingsSection("System")','cobraSettingsSection("Diagnostics")','cobra.settings.enter']),
  'screen_contract_preserved': 'cobra-browse-background' in text and 'cobra-browse-safe-content' in text and 'experience-safe-content' not in text,
  'file_picker_preserved': 'ACTION_GET_CONTENT' in text and 'MiXplorer' in text,
  'pip_background_preserved': 'cobraBeginMiniBackgroundPlayback' in text and 'enterCobraPictureInPicture' in text,
  'native_unchanged': patch.get('native_changed') is False,
  'physical_unverified': patch.get('physical_device_verified') is False,
 }
 failed=[k for k,v in checks.items() if not v]
 result={'passed':not failed,'checks':checks,'failed':failed,'build':2103177,'physical_device_verified':False}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 if failed:raise RuntimeError('2103177 source audit failed: '+', '.join(failed))
 print('PASS:',len(checks),'2103177 feature-freeze source checks')
if __name__=='__main__':main()
