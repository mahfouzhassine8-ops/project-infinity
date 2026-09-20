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
    pace=block(text,'CobraProviderPacePolicy','class');norm=block(text,'CobraTimelineNormalizerPolicy','class');session=block(text,'CobraLocalTimeshiftSession','class');health=block(text,'cobraAddSessionHealth');parser=block(text,'CobraTsParserPolicy','class')
    checks={
      'exact_2103191_parent':patch.get('base_build')==2103191 and patch.get('base_commit')=='23fab77d21e97e6f74f04f397d3fa0a63a24bc2e',
      'pace_gate_is_narrow':'MIN_RATE_PERMILLE=450L' in pace and 'MAX_RATE_PERMILLE=800L' in pace and 'MAX_TRACK_DELTA_PERMILLE=35L' in pace,
      'pace_requires_sustained_proof':'MIN_WALL_MS=15000L' in pace and 'MIN_VIDEO_PTS_SAMPLES=240L' in pace and 'MIN_AUDIO_PTS_SAMPLES=40L' in pace,
      'pace_requires_clean_continuous_ingest':'MAX_PROVIDER_AGE_MS=500L' in pace and 'MAX_PROVIDER_GAP_MS=1000L' in pace and 'zeroBuckets>0L' in pace and 'continuityErrors==0L&&syncLosses==0L' in pace,
      'clock_rewrite_disabled':'REWRITE_ENABLED=false' in norm and 'if(!CobraTimelineNormalizerPolicy.REWRITE_ENABLED){timelineNormalizerPending=false;return;}' in session,
      'no_auto_hls_handoff':'pace-reserve-auto' not in text,
      'no_new_buffer_numbers':patch.get('buffer_policy_changed') is False,
      'pace_diagnostics':'timeshift_provider_pace_limited' in health and 'timeshift_timeline_normalizer_rewrite_enabled' in health,
      'schema_7':'root.put("stream_fingerprint_schema",7)' in health,
      'route_fingerprint_preserved':'timeshift_provider_remote_hash' in health and 'timeshift_provider_dns_hashes' in health,
      'parser_flags_preserved':'FLAG_DETECT_ACCESS_UNITS' in parser and 'FLAG_ALLOW_NON_IDR_KEYFRAMES' in parser,
      'playback_behavior_unchanged':patch.get('playback_behavior_changed') is False,
      'network_selection_unchanged':patch.get('network_selection_changed') is False,
      'timeshift_ownership_unchanged':patch.get('timeshift_ownership_changed') is False,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
      'rewind_preserved':'/live.ts' in session and 'timeshift-enter-on-demand' in text,
      'blue_timeline_preserved':'cobra_unified_live_timeline' in text,
      'watchdog_observation_only':'buffer_observed_no_restart' in text,
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103192,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103192 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103192 source checks')
if __name__=='__main__':main()
