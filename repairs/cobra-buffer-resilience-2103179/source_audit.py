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
      'watchdog_observation_only':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'multitask_patch_declared':patch.get('multitask_resize_playback_preserved') is True,
      'timeshift_recovery_declared':patch.get('timeshift_source_recovery') is True,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    out={'passed':not failed,'checks':checks,'failed':failed,'build':2103179,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    if failed:raise RuntimeError('2103179 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103179 buffer-resilience source checks')

if __name__=='__main__':main()
