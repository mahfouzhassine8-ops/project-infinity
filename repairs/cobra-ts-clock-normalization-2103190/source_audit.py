#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')

def require(v,msg):
    if not v: raise RuntimeError(msg)

def block(text,name,kind='method'):
    if kind=='method':
        pat=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:
        pat=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    ms=list(pat.finditer(text));require(len(ms)==1,f'{name} cardinality={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=comment=False
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
    text=(a.source/ACT).read_text();patch=json.loads(a.patch.read_text())
    policy=block(text,'CobraTimelineNormalizerPolicy','class');timeline=block(text,'CobraTsTimelinePolicy','class');session=block(text,'CobraLocalTimeshiftSession','class');health=block(text,'cobraAddSessionHealth');parser=block(text,'CobraTsParserPolicy','class')
    checks={
      'exact_2103189_parent':patch.get('base_build')==2103189 and patch.get('base_commit')=='af44c82189b37312abf5f75d9237eef1e3d89dc8',
      'conditional_rate_gate':'MIN_UNDERCLOCK_PERMILLE=450L' in policy and 'MAX_UNDERCLOCK_PERMILLE=800L' in policy and 'MAX_TRACK_DELTA_PERMILLE=35L' in policy,
      'requires_sustained_evidence':'MIN_WALL_MS=5000L' in policy and 'MIN_VIDEO_PTS_SAMPLES=120L' in policy and 'MIN_AUDIO_PTS_SAMPLES=20L' in policy,
      'scale_math':'scalePpm' in policy and 'scaleDelta90k' in policy and '1000000000L' in policy,
      'good_stream_passthrough':'if(!timelineNormalizerActive)broadcastLive(b,n);consume(b,n);activatePendingTimelineNormalizer();' in session,
      'activation_waits_for_queue':'!liveQueue.isEmpty()' in session and 'timelineNormalizerPending' in session,
      'raw_timeline_measured_before_rewrite':'observeContinuity(data,offset);maybeScheduleTimelineNormalizer();if(timelineNormalizerActive){normalizeTimelinePacket(data,offset);broadcastNormalizedPacket(data,offset);}segmentOut.write' in session,
      'pcr_rewrite':'timelineNormalizerRewrittenPcr' in session and 'normalizerPcrAnchor90k' in session,
      'pts_rewrite':'timelineNormalizerRewrittenPts' in session and 'normalizerPtsAnchor90k' in session and 'encodePts90k' in session,
      'dts_rewrite':'timelineNormalizerRewrittenDts' in session and 'normalizerDtsAnchor90k' in session,
      'rewind_segments_normalized_after_activation':'normalizeTimelinePacket(data,offset)' in session and 'segmentOut.write(data,offset,PACKET)' in session,
      'normalized_proxy_batched':'normalizedLiveBatch' in session and 'broadcastNormalizedPacket' in session and 'flushNormalizedLiveBatch' in session,
      'reconnect_resets_anchors':'resetTimelineNormalizerAnchors();lastError=' in session,
      'diagnostics_export_normalizer':all(x in health for x in ('timeshift_timeline_normalizer_active','timeshift_timeline_normalizer_raw_rate_permille','timeshift_timeline_normalizer_scale_ppm','timeshift_timeline_normalizer_rewritten_pcr','timeshift_timeline_normalizer_rewritten_pts','timeshift_timeline_normalizer_rewritten_dts')),
      'schema_5':'root.put("stream_fingerprint_schema",5)' in health,
      'timeline_probe_preserved':'timeshift_video_pts_rate_permille' in health and 'timeshift_video_dts_rate_permille' in health and 'timeshift_audio_pts_rate_permille' in health,
      'parser_flags_preserved':'FLAG_DETECT_ACCESS_UNITS' in parser and 'FLAG_ALLOW_NON_IDR_KEYFRAMES' in parser,
      'diagnostic_freeze_preserved':'last_live_before_navigation' in text and 'live_snapshot_frozen_before_navigation' in text,
      'network_controls_preserved':'CobraHappyEyeballs' in text and 'IPv4 only' in text and 'IPv6 only' in text,
      'rewind_contract_preserved':'/live.ts' in session and 'rewind-ready-background' in text,
      'blue_timeline_preserved':'cobra_unified_live_timeline' in text,
      'call_audio_preserved':'CobraCallAudioPolicy' in text,
      'watchdog_observation_only':'buffer_observed_no_restart' in text,
      'network_selection_unchanged':patch.get('network_selection_changed') is False,
      'timeshift_ownership_unchanged':patch.get('timeshift_ownership_changed') is False,
      'buffer_policy_unchanged':patch.get('buffer_policy_changed') is False,
      'parser_flags_unchanged':patch.get('parser_flags_changed') is False,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103190,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103190 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103190 source checks')

if __name__=='__main__':main()
