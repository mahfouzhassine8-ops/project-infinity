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
    start=ms[0].start(); i=text.index('{',ms[0].end()); d=0; q=None; esc=line=comment=False
    while i<len(text):
        c=text[i]; n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif comment:
            if c=='*' and n=='/': comment=False; i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q: q=None
        elif c=='/' and n=='/': line=True; i+=1
        elif c=='/' and n=='*': comment=True; i+=1
        elif c in ('"',"'"): q=c
        elif c=='{': d+=1
        elif c=='}':
            d-=1
            if d==0: return text[start:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True); p.add_argument('--patch',type=Path,required=True); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    text=(a.source/ACT).read_text(); patch=json.loads(a.patch.read_text())
    build=block(text,'buildPlayer'); health=block(text,'cobraAddSessionHealth'); policy=block(text,'CobraTsParserPolicy','class'); cadence=block(text,'CobraStreamCadencePolicy','class')
    checks={
      'exact_2103186_parent':patch.get('base_build')==2103186 and patch.get('base_commit')=='431d8d00e814a47d9ec4df972667c1c1f700413b',
      'detect_access_units_enabled':'FLAG_DETECT_ACCESS_UNITS' in policy and 'detectsAccessUnits' in policy,
      'non_idr_not_enabled':'TS_FLAGS=androidx.media3.extractor.ts.TsExtractor.FLAG_DETECT_ACCESS_UNITS' in policy and 'FLAG_ALLOW_NON_IDR_KEYFRAMES' not in build,
      'custom_extractors_factory':'DefaultExtractorsFactory' in build,
      'extractors_wired_to_media_source':'new DefaultMediaSourceFactory(data,extractors)' in build,
      'diagnostic_marker':all(x in health for x in ('ts_access_unit_detection','ts_allow_non_idr_keyframes','ts_extractor_profile')),
      'cadence_schema_preserved':'BUCKET_MS=500L' in cadence and 'timeshift_provider_max_gap_ms' in health and 'timeshift_proxy_max_gap_ms' in health,
      'frozen_snapshot_preserved':'last_live_before_navigation' in text and 'live_snapshot_frozen_before_navigation' in text,
      'smart_network_preserved':'CobraHappyEyeballs' in text and 'IPv4 only' in text and 'IPv6 only' in text,
      'seamless_rewind_preserved':'/live.ts' in text and 'rewind-ready-background' in text,
      'blue_timeline_preserved':'cobra_unified_live_timeline' in text,
      'call_audio_preserved':'CobraCallAudioPolicy' in text,
      'watchdog_observation_only':'buffer_observed_no_restart' in text,
      'network_selection_unchanged':patch.get('network_selection_changed') is False,
      'timeshift_ownership_unchanged':patch.get('timeshift_ownership_changed') is False,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103187,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True); (a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103187 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103187 source checks')
if __name__=='__main__': main()
