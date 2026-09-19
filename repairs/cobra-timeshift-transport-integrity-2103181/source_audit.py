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
    transport=block(text,'CobraTimeshiftTransportPolicy','class');ts=block(text,'CobraLocalTimeshiftSession','class');playlist=block(text,'playlist');finish=block(text,'finishSegment');serve=block(text,'serve');watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    checks={
      'exact_2103180_parent':patch.get('base_build')==2103180 and patch.get('base_commit')=='c7a52ef5553152d75f54b713e8975c8e2794e09b',
      'fast_read_timeout_restored':'READ_TIMEOUT_MS=5000' in transport,
      'fifteen_second_live_reserve_preserved':'LIVE_RESERVE_MS=15000L' in transport and 'TIME-OFFSET=-15.0' in transport,
      'published_duration_is_bounded':'publishedSegmentDurationMs' in transport and 'MAX_PUBLISHED_SEGMENT_MS=4500L' in transport,
      'outage_time_not_used_as_extinf':'SystemClock.elapsedRealtime()-segmentStartElapsed' not in finish and 'publishedSegmentDurationMs(segmentStartElapsed,segmentLastPacketElapsed)' in finish,
      'last_packet_clock_updates':'segmentLastPacketElapsed=now' in ts and 'providerLastPacketElapsed=now' in ts,
      'discontinuity_sequence_header':'#EXT-X-DISCONTINUITY-SEQUENCE:' in transport and 'playlistHeader(list.get(0).seq,list.get(0).discontinuitySequence)' in playlist,
      'discontinuity_sequence_monotonic':'segmentDiscontinuitySequence=discontinuitiesBefore' in ts and 'if(segmentDiscontinuity)discontinuitiesBefore++' in ts,
      'removed_segments_retained_longer':'retainedSegmentCount(maxSegments)' in ts and 'playlistSegments*2+4' in transport,
      'storage_still_bounded':'retainedByteLimit' in transport and '384L*1024L*1024L' in transport,
      'segment_404s_visible':'segment404s++' in serve and 'timeshift_segment_404s' in text,
      'freshness_diagnostics':'providerPacketAgeMs' in ts and 'latestSegmentAgeMs' in ts and 'timeshift_provider_packet_age_ms' in text and 'timeshift_latest_segment_age_ms' in text,
      'published_extinf_diagnostic':'maxPublishedDurationMs' in ts and 'timeshift_max_published_extinf_ms' in text,
      'unified_blue_timeline_preserved':'cobra_unified_live_timeline' in text and 'footer.addView(mCobraTimeshiftSeek' not in block(text,'cobraBuildPlayerChrome'),
      'phone_call_continuity_preserved':'CobraCallAudioPolicy' in text and 'video_preserved=true' in text,
      'pro_watchdog_preserved':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'bounded_auto_live_recovery_preserved':'MAX_AUTO_LIVE_EDGE_ATTEMPTS=2' in text and 'RECOVERY_COOLDOWN_MS=60000L' in text,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v];result={'passed':not failed,'checks':checks,'failed':failed,'build':2103181,'physical_device_verified':False};a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed:raise RuntimeError('2103181 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103181 timeshift transport-integrity source checks')
if __name__=='__main__':main()
