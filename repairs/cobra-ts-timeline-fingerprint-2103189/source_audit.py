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
    ms=list(pat.finditer(text)); require(len(ms)==1,f'{name} cardinality={len(ms)}')
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
    timeline=block(text,'CobraTsTimelinePolicy','class');session=block(text,'CobraLocalTimeshiftSession','class');binding=block(text,'CobraPlayerBinding','class');vitals=block(text,'CobraSessionVitals','class');health=block(text,'cobraAddSessionHealth');parser=block(text,'CobraTsParserPolicy','class')
    checks={
      'exact_2103188_parent':patch.get('base_build')==2103188 and patch.get('base_commit')=='81390fd1e7f53c9cd55d33aaa25fbca26dd7a509',
      'timeline_probe_only':patch.get('timeline_probe_only') is True and patch.get('playback_behavior_changed') is False,
      'wrap_math':'PTS_MOD=1L<<33' in timeline and 'signedDiff90k' in timeline and 'ratePermille' in timeline,
      'pat_pmt_probe':'observeProgramMap' in session and 'timelinePmtPid' in session and 'timelineVideoPid' in session and 'timelineAudioPid' in session,
      'pts_dts_probe':'videoPtsRoleSamples' in session and 'videoDtsRoleSamples' in session and 'audioPtsRoleSamples' in session,
      'nal_probe':'observeVideoNals' in session and 'videoIdrNals' in session and 'videoNonIdrIntraFrames' in session,
      'slice_probe':'firstSliceType' in session and 'intraSliceType' in timeline,
      'rebuffer_correlation':'videoPtsAgeAtRebufferLastMs' in vitals and 'videoPtsAgeMs()' in binding and 'intraAgeAtRebufferLastMs' in vitals,
      'health_exports_clock_rates':all(x in health for x in ('timeshift_video_pts_rate_permille','timeshift_video_dts_rate_permille','timeshift_audio_pts_rate_permille')),
      'health_exports_av_drift':all(x in health for x in ('timeshift_av_drift_latest_ms','timeshift_av_drift_max_abs_ms')),
      'health_exports_keyframes':all(x in health for x in ('timeshift_video_idr_nals','timeshift_video_non_idr_intra_frames','timeshift_intra_interval_max_ms')),
      'health_exports_rebuffer_timeline':all(x in health for x in ('video_pts_age_at_rebuffer_last_ms','video_dts_age_at_rebuffer_last_ms','audio_pts_age_at_rebuffer_last_ms','av_drift_at_rebuffer_last_ms','intra_age_at_rebuffer_last_ms')),
      'schema_4':'root.put("stream_fingerprint_schema",4)' in health,
      '2103188_parser_flags_preserved':'FLAG_DETECT_ACCESS_UNITS' in parser and 'FLAG_ALLOW_NON_IDR_KEYFRAMES' in parser,
      'frozen_snapshot_preserved':'last_live_before_navigation' in text and 'live_snapshot_frozen_before_navigation' in text,
      'cadence_preserved':'timeshift_provider_max_gap_ms' in health and 'timeshift_proxy_max_gap_ms' in health,
      'network_preserved':'CobraHappyEyeballs' in text and 'IPv4 only' in text and 'IPv6 only' in text,
      'rewind_preserved':'/live.ts' in session and 'rewind-ready-background' in text,
      'timeline_preserved':'cobra_unified_live_timeline' in text,
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
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103189,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103189 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103189 source checks')

if __name__=='__main__':main()
