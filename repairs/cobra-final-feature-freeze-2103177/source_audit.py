#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')

def require(v,msg):
    if not v: raise RuntimeError(msg)

def method(text,name):
    pat=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    ms=list(pat.finditer(text));require(len(ms)==1,f'{name} cardinality={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False;i+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':block=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return text[start:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    build=method(text,'buildPlayer')
    checks={
      'display_modes_present': all(x in text for x in ('"auto"','"60"','"90"','"120"','"max"')) and 'DISPLAY & PERFORMANCE  •  ' in text,
      'real_android_mode_request':'preferredDisplayModeId' in text and 'getSupportedModes()' in text and 'getMode().getRefreshRate()' in text,
      'active_hz_proof': all(x in text for x in ('mCobraRequestedHz','mCobraActiveHz','mCobraMaxHz','mCobraRefreshStatus')),
      'ui_fps_proof':'android.view.Choreographer.FrameCallback' in text and 'cobra_performance_proof_overlay' in text,
      'power_thermal_safety':'isPowerSaveMode()' in text and 'THERMAL_STATUS_SEVERE' in text,
      'video_refresh_independent':'VIDEO OWNS REFRESH' in text and 'cobraVideoOwnsRefresh()' in text,
      'timeshift_runtime':'CobraLocalTimeshiftSession' in text and 'CobraTimeshiftIngest' in text and 'CobraTimeshiftServer' in text,
      'timeshift_loopback_only':'127.0.0.1' in text and '/live.m3u8' in text and 'mPlayer.setMediaItem(mediaItem(session.playlistUrl()))' in text,
      'timeshift_rolling_hls':'EXT-X-MEDIA-SEQUENCE' in text and 'EXT-X-DISCONTINUITY' in text and 'EXT-X-START:TIME-OFFSET=-6.0' in text,
      'timeshift_bounded': all(x in text for x in ('60,120,180','maxSegments','storageSegments','maxBytes')),
      'timeshift_raw_ts_only':'localTsEligible' in text and 'l.contains(".m3u8")' in text and '"ts".equalsIgnoreCase(extension)' in text,
      'single_provider_ingest': 'mCobraTimeshiftPlayer=mPlayer' in text and 'new ExoPlayer' not in method(text,'cobraStartLocalTimeshift'),
      'smart_reserve_documented':'brief provider/network stalls can be absorbed' in text,
      'single_view_media3_default':'new DefaultLoadControl();' in build,
      'multiview_bounded_buffer':'setBufferDurationsMs(6000,30000,1500,3000)' in build and '12*1024*1024' in build,
      'watchdog_observation_only':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'network_diagnostics':all(x in text for x in ('network_transport','last_media_load_kbps','rebuffer_events','long_stalls','timeshift_network_stall_ms')),
      'vpn_transport_detection':'TRANSPORT_VPN' in text,
      'live_edge_diagnostics':'getCurrentLiveOffset()' in text,
      'last_channel':all(x in text for x in ('cobra_last_channel','COBRA_LAST_PREVIOUS','cobraTuneLastChannel()','KEYCODE_LAST_CHANNEL')),
      'settings_polish':all(x in text for x in ('EXPERIENCE & DISPLAY','PLAYBACK','SYSTEM & SOURCES','HEALTH & DIAGNOSTICS')),
      'chrome_polish':'setDuration(150)' in text and 'setDuration(120)' in text,
      'timeshift_scrubber':'cobra_live_timeshift_seek' in text and 'mCobraTimeshiftDragging' in text,
      'statusbar_contract_preserved':'cobra-browse-background' in text and 'cobra-browse-safe-content' in text and 'cobraApplySystemBarsForSurface' in text,
      'file_picker_preserved':'cobraOpenFilePicker' in text and 'cobraLaunchFilePicker' in text,
      'provider_catchup_preserved':'tv_archive' in text and 'tv_archive_duration' in text and 'cobraStartProviderCatchup' in text,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    out={'passed':not failed,'checks':checks,'failed':failed,'build':2103177,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    if failed: raise RuntimeError('2103177 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'final feature-freeze source checks')
if __name__=='__main__':main()
