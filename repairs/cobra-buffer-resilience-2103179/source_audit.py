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

def class_block(text,name):
    m=re.search(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M)
    require(m is not None,'missing class '+name);start=m.start();i=text.index('{',m.end());d=0;q=None;esc=line=block=False
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
    raise RuntimeError('unclosed class '+name)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
    transport=class_block(text,'CobraTimeshiftTransportPolicy')
    ts=class_block(text,'CobraLocalTimeshiftSession')
    binding=class_block(text,'CobraPlayerBinding')
    vitals=class_block(text,'CobraSessionVitals')
    stop=method(text,'onStop')
    recover=method(text,'cobraRecoverLocalTimeshiftSource')
    burst=method(text,'cobraObserveTimeshiftRebufferBurst')
    stall=method(text,'cobraRecoverTimeshiftStall')
    overlay=method(text,'cobraUpdatePerformanceOverlay')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    checks={
      'exact_2103178_parent':patch.get('base_build')==2103178 and patch.get('base_commit')=='56792d4e44b381cff2c900e7b86ed99265b55d04',
      'nine_second_live_reserve':'#EXT-X-START:TIME-OFFSET=-9.0,PRECISE=NO' in transport and '#EXT-X-START:TIME-OFFSET=-6.0,PRECISE=NO' not in transport,
      'bounded_connect_timeout':'CONNECT_TIMEOUT_MS=7000' in transport and 'setConnectTimeout(CobraTimeshiftTransportPolicy.CONNECT_TIMEOUT_MS)' in ts,
      'bounded_read_timeout':'READ_TIMEOUT_MS=5000' in transport and 'setReadTimeout(CobraTimeshiftTransportPolicy.READ_TIMEOUT_MS)' in ts,
      'fast_bounded_reconnect':all(x in transport for x in ('INITIAL_BACKOFF_MS=250L','MAX_BACKOFF_MS=1500L','nextBackoffMs')),
      'partial_ts_survives_provider_drop':'finishSegment(true)' in ts and 'pendingDiscontinuity=true' in ts,
      'stall_accounting_not_double_counted':'outageStart' in ts and 'elapsed>10000' not in ts,
      'multitask_resize_does_not_background_pause':'CobraWindowLifecyclePolicy.preservePlaybackOnStop(isInMultiWindowMode(),isFinishing())' in stop and 'multitask-window-stop' in stop,
      'timeshift_waits_for_new_local_segment':'awaitSequenceAfter' in ts and 'latestSequence' in ts,
      'timeshift_source_error_recovers_before_fallback':'CobraTimeshiftRecoveryPolicy.recoverable' in recover and 'timeshift-source-recovery' in recover and 'source-recovered' in recover,
      'rebuffer_burst_is_observation_only':'rebuffer-burst-observed' in burst and 'no_restart=true' in burst and all(x not in burst for x in ('setMediaItem(','.prepare(','seekToDefaultPosition','startCobraPlayer','cobraFallbackFromLocalTimeshift')),
      'rebuffer_burst_preserves_cache':'cobraStopLocalTimeshift' not in burst and 'releaseSinglePlayer' not in burst,
      'timeshift_stall_detects_both_surfaces':'player==mPlayer?"fullscreen":"preview"' in stall and 'stall-detected' in stall,
      'automatic_live_matches_manual_live_seek':'seekToDefaultPosition' in stall and 'auto-live-edge-seek' in stall and 'same_player=true' in stall,
      'automatic_live_does_not_restart_media':all(x not in stall for x in ('setMediaItem(','.prepare(','startCobraPlayer','cobraFallbackFromLocalTimeshift')),
      'automatic_live_edge_preserves_cache':'cobraStopLocalTimeshift' not in stall and 'releaseSinglePlayer' not in stall,
      'stall_persistence_defers_to_error_path':'stall-persists-after-live-edge' in stall and 'error_path_owns_restart=true' in stall,
      'pro_recovery_budget':'MAX_AUTO_LIVE_EDGE_ATTEMPTS=2' in text and 'RECOVERY_COOLDOWN_MS=60000L' in text and 'cobraPermitAutoLiveEdge' in text,
      'performance_overlay_reads_visible_player':'ExoPlayer proofPlayer=mPlayer!=null?mPlayer:mCobraPreviewPlayer' in overlay,
      'timeshift_error_no_immediate_session_kill':'if(localTimeshift)cobraStopLocalTimeshift("player-error")' not in binding,
      'http_framing_fix_preserved':'hasRealHttpFraming' in transport and '"\\r\\n\\r\\n"' in transport,
      'playlist_line_fix_preserved':'hasRealPlaylistLines' in transport and '#EXTM3U\\n' in transport,
      'visible_rebuffer_threshold':'bufferedFor>=750L' in binding and 'vitals.rebufferEvents++' in binding,
      'buffer_transition_evidence':'bufferingTransitions' in binding and 'bufferingTransitions' in vitals and 'rebufferDurationMs' in vitals,
      'rewind_seek_preserved':'cobra_live_timeshift_seek' in text and 'cobraUpdateTimeshiftSeek' in text,
      'same_player_handoff_preserved':'preview-timeshift-fullscreen' in text and 'session==mCobraTimeshiftPlayer' in method(text,'promoteCobraPreviewToFullscreen'),
      'direct_fallback_preserved':'timeshift-transport-fallback' in text,
      'provider_catchup_preserved':'tv_archive' in text and 'cobraStartProviderCatchup' in text,
      'last_channel_preserved':'cobra_last_channel' in text and 'cobraTuneLastChannel' in text,
      'refresh_120_preserved':'preferredDisplayModeId' in text and 'mCobraActiveHz' in text,
      'single_view_media3_default':'new DefaultLoadControl();' in method(text,'buildPlayer'),
      'watchdog_observation_only':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'multitask_patch_declared':patch.get('multitask_resize_playback_preserved') is True,
      'timeshift_recovery_declared':patch.get('timeshift_source_recovery') is True,
      'timeshift_stall_recovery_declared':patch.get('timeshift_stall_recovery') is True and patch.get('timeshift_stall_detect_ms')==6000,
      'rebuffer_burst_declared':patch.get('rebuffer_burst_observation_only') is True and patch.get('rebuffer_burst_count')==3 and patch.get('rebuffer_burst_window_ms')==12000,
      'auto_live_edge_declared':patch.get('auto_live_edge_first') is True and patch.get('auto_live_edge_verify_ms')==2500,
      'pro_budget_declared':patch.get('auto_live_edge_max_attempts')==2 and patch.get('auto_live_edge_cooldown_ms')==60000,
      'buffering_restart_forbidden_declared':patch.get('buffering_media_restart_forbidden') is True and patch.get('manual_live_seek_equivalent') is True,
      'overlay_source_aware_declared':patch.get('performance_overlay_source_aware') is True,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    out={'passed':not failed,'checks':checks,'failed':failed,'build':2103179,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    if failed:raise RuntimeError('2103179 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103179 buffer-resilience source checks')

if __name__=='__main__':main()
