#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
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
 text=(a.source/ACT).read_text();patch=json.loads(a.patch.read_text())
 policy=block(text,'CobraStreamCadencePolicy','class');session=block(text,'CobraLocalTimeshiftSession','class');binding=block(text,'CobraPlayerBinding','class');vitals=block(text,'CobraSessionVitals','class');health=block(text,'cobraAddSessionHealth')
 checks={
  'exact_2103185_parent':patch.get('base_build')==2103185 and patch.get('base_commit')=='41912bf61440b263898c3e67ad6ba48279473f78',
  'bucket_500ms':'BUCKET_MS=500L' in policy,
  'gap_thresholds':all(x in policy for x in ('GAP_WARN_MS=500L','GAP_BAD_MS=1000L','GAP_SEVERE_MS=2000L')),
  'provider_ingress_measured':'observeProviderRead(n)' in session and 'providerMaxGapMs' in session and 'providerZeroBuckets' in session,
  'proxy_write_measured':'observeProxyWrite(chunk.length)' in session and 'proxyMaxGapMs' in session and 'proxyZeroBuckets' in session,
  'provider_measured_before_fanout':session.index('observeProviderRead(n)')<session.index('broadcastLive(b,n)'),
  'proxy_measured_after_write':session.index('observeProxyWrite(chunk.length)')>session.index('out.write(chunk)'),
  'rebuffer_buffer_ahead_captured':'rebufferAheadLastMs' in vitals and 'player.getTotalBufferedDuration()' in binding,
  'rebuffer_provider_age_captured':'providerAgeAtRebufferLastMs' in vitals and 'providerReadAgeMs()' in binding,
  'rebuffer_proxy_age_captured':'proxyAgeAtRebufferLastMs' in vitals and 'proxyWriteAgeMs()' in binding,
  'health_exports_provider_cadence':all(x in health for x in ('timeshift_provider_max_gap_ms','timeshift_provider_gap_1000_count','timeshift_provider_zero_500ms_buckets','timeshift_provider_500ms_bytes_avg')),
  'health_exports_proxy_cadence':all(x in health for x in ('timeshift_proxy_max_gap_ms','timeshift_proxy_gap_1000_count','timeshift_proxy_zero_500ms_buckets','timeshift_proxy_500ms_bytes_avg')),
  'health_exports_rebuffer_correlation':all(x in health for x in ('rebuffer_buffer_ahead_last_ms','provider_age_at_rebuffer_last_ms','proxy_age_at_rebuffer_last_ms')),
  'fingerprint_schema_3':'root.put("stream_fingerprint_schema",3)' in health,
  'frozen_snapshot_preserved':'last_live_before_navigation' in text and 'live_snapshot_frozen_before_navigation' in text,
  'smart_network_preserved':'CobraHappyEyeballs' in text and 'IPv4 only' in text and 'IPv6 only' in text,
  'seamless_rewind_preserved':'/live.ts' in session and 'liveWriterLoop' in session and 'rewind-ready-background' in text,
  'blue_timeline_preserved':'cobra_unified_live_timeline' in text,
  'call_audio_preserved':'CobraCallAudioPolicy' in text,
  'watchdog_no_restart':'buffer_observed_no_restart' in text,
  'playback_behavior_unchanged':patch.get('playback_behavior_changed') is False,
  'network_selection_unchanged':patch.get('network_selection_changed') is False,
  'timeshift_ownership_unchanged':patch.get('timeshift_ownership_changed') is False,
  'native_unchanged':patch.get('native_changed') is False,
  'theme_unchanged':patch.get('theme_zip_changed') is False,
  'physical_unverified':patch.get('physical_device_verified') is False,
 }
 for tok in ('setMediaItem(','prepare()','play()','seekTo(','release()'):
  checks['policy_no_'+re.sub('[^a-z0-9]+','_',tok.lower()).strip('_')]=tok not in policy
 failed=[k for k,v in checks.items() if not v];result={'passed':not failed,'checks':checks,'failed':failed,'build':2103186,'physical_device_verified':False}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 if failed:raise RuntimeError('2103186 source audit failed: '+', '.join(failed))
 print('PASS:',len(checks),'2103186 source checks')
if __name__=='__main__':main()
