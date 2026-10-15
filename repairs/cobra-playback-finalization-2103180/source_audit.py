#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
def require(v,msg):
    if not v:raise RuntimeError(msg)
def block(text,name,kind='method'):
    if kind=='method':pat=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:pat=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    ms=list(pat.finditer(text));require(len(ms)==1,f'{name} cardinality={len(ms)}');start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=comment=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif comment:
            if c=='*' and n=='/':comment=False;i+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
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
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
    transport=block(text,'CobraTimeshiftTransportPolicy','class');build=block(text,'buildPlayer');media=block(text,'mediaItem');chrome=block(text,'cobraBuildPlayerChrome');seek=block(text,'cobraUpdateTimeshiftSeek');labels=block(text,'cobraRefreshProgrammeLabels');audio=block(text,'cobraHandleAudioFocus');claim=block(text,'cobraClaimAudioFocus');dispose=block(text,'cobraDisposePlayer');burst=block(text,'cobraObserveTimeshiftRebufferBurst');stall=block(text,'cobraRecoverTimeshiftStall');watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    checks={
      'exact_2103179_parent':patch.get('base_build')==2103179 and patch.get('base_commit')=='0560b18c497e9861864126d96f9b784e488ebe32',
      'read_timeout_relaxed':'READ_TIMEOUT_MS=15000' in transport,
      'fifteen_second_reserve':'LIVE_RESERVE_MS=15000L' in transport and 'TIME-OFFSET=-15.0' in transport,
      'live_configuration_targets_reserve':'setTargetOffsetMs(CobraTimeshiftTransportPolicy.LIVE_RESERVE_MS)' in media and 'setMinOffsetMs(12000L)' in media and 'setMaxOffsetMs(24000L)' in media,
      'media3_default_single_buffer_preserved':'new DefaultLoadControl();' in build,
      'generic_watchdog_observation_only':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'rebuffer_burst_still_observation_only':'rebuffer-burst-observed' in burst and all(x not in burst for x in ('setMediaItem(','.prepare(','startCobraPlayer')),
      'stall_recovery_same_player_seek_only':'seekToDefaultPosition' in stall and all(x not in stall for x in ('setMediaItem(','.prepare(','startCobraPlayer')),
      'single_unified_timeline':'cobra_unified_live_timeline' in chrome and 'timeline.addView(mCobraPlayerProgramProgress' in chrome and 'timeline.addView(mCobraTimeshiftSeek' in chrome,
      'yellow_track_removed':'Color.TRANSPARENT' in chrome and 'footer.addView(mCobraTimeshiftSeek' not in chrome,
      'blue_line_tracks_timeshift':'mCobraPlayerProgramProgress.setProgress(value)' in seek and 'cobraTimeshiftTimelineAvailable' in seek,
      'program_progress_does_not_overwrite_timeshift':'!cobraTimeshiftTimelineAvailable()' in labels,
      'media3_managed_focus_disabled':',false);' in build and not re.search(r'setAudioAttributes\([^\n;]*,true\)',text),
      'call_focus_preserves_video':'video_preserved=true' in audio and '.pause(' not in audio and 'setVolume(0f)' in audio,
      'focus_claim_is_explicit':'requestAudioFocus' in claim and 'AUDIOFOCUS_GAIN' in claim,
      'focus_released_on_dispose':'cobraReleaseAudioFocus(player)' in dispose,
      'rewind_contract_preserved':'cobra_live_rewind_30' in text and 'cobra_live_edge' in text and 'cobra_live_timeshift_seek' in text,
      'native_unchanged':patch.get('native_changed') is False,'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'yellow_scrubber_declared':patch.get('yellow_scrubber_removed') is True,'call_continuity_declared':patch.get('phone_call_video_continuity') is True,'pro_safeguards_declared':patch.get('pro_buffer_safeguards_preserved') is True,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v];result={'passed':not failed,'checks':checks,'failed':failed,'build':2103180,'physical_device_verified':False};a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed:raise RuntimeError('2103180 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103180 playback-finalization source checks')
if __name__=='__main__':main()
