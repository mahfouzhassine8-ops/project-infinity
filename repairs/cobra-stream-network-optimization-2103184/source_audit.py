#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
GRADLE=Path('tools/android/packaging/xbmc/build.gradle.in')
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
 text=(a.source/ACT).read_text();gradle=(a.source/GRADLE).read_text();patch=json.loads(a.patch.read_text())
 network=block(text,'CobraNetworkFamilyPolicy','class');session=block(text,'CobraLocalTimeshiftSession','class');binding=block(text,'CobraPlayerBinding','class');vitals=block(text,'CobraSessionVitals','class');health=block(text,'cobraAddSessionHealth');full=block(text,'cobraStartLocalTimeshift');preview=block(text,'cobraStartLocalTimeshiftPreview');rewind=block(text,'cobraRewindLive');build=block(text,'buildPlayer')
 checks={
  'exact_2103183_parent':patch.get('base_build')==2103183 and patch.get('base_commit')=='1b0fd6365715895f4325e10082df6d8470b26632',
  'media3_okhttp_added':'androidx.media3:media3-datasource-okhttp:1.7.1' in gradle,
  'direct_player_family_control':'OkHttpDataSource.Factory' in build and 'cobraNetworkFamilyMode()' in build and 'FamilyDns' in build,
  'happy_eyeballs_auto':'CobraHappyEyeballs' in network and 'HAPPY_DELAY_MS=250L' in network and 'autoOrder' in network,
  'route_memory':'HAPPY_MEMORY_MS=300000L' in network and 'rememberedFamily' in network and 'recordSuccess' in network and 'recordFailure' in network,
  'manual_modes_preserved':all(x in text for x in ('Automatic (IPv4 + IPv6)','IPv4 only','IPv6 only','cobra-provider-network:auto','cobra-provider-network:ipv4','cobra-provider-network:ipv6')),
  'no_global_network_mutation':'java.net.preferIPv4Stack' not in text and 'java.net.preferIPv6Addresses' not in text and 'ProxySelector.setDefault' not in text and 'VpnService' not in text,
  'local_loopback_not_family_blocked':'loopbackHost' in network,
  'seamless_fullscreen':'session.liveUrl()' in full and 'awaitReady' not in full and 'fullscreen-live-proxy' in full,
  'seamless_preview':'session.liveUrl()' in preview and 'awaitReady' not in preview and 'preview-live-proxy' in preview,
  'single_provider_ingest':'providerClient.newCall' in session and 'broadcastLive' in session and '/live.ts' in session,
  'rewind_switches_on_demand':'cobraActivateLocalTimeshift' in text and 'timeshift-enter-on-demand' in text and 'mCobraPendingLocalRewindMs' in binding,
  'background_rewind_ready':'rewind-ready-background' in text and 'cobraWatchTimeshiftReady' in text,
  'stream_format_fingerprint':all(x in vitals for x in ('videoMime','videoCodecs','audioMime','audioCodecs','videoFrameRate')),
  'buffer_periodicity_fingerprint':all(x in vitals for x in ('lastBufferIntervalMs','bufferIntervalTotalMs','lastLoadIntervalMs','loadIntervalTotalMs')),
  'ts_integrity_fingerprint':all(x in session for x in ('tsContinuityErrors','tsSyncLosses','observeContinuity','publishedSegments')),
  'network_fingerprint':all(x in health for x in ('network_connected_family','happy_eyeballs_race_ms','dns_ipv4','dns_ipv6')),
  'timeshift_fingerprint':all(x in health for x in ('timeshift_ts_continuity_errors','timeshift_ts_sync_losses','timeshift_segment_bytes_avg','timeshift_live_proxy_bytes')),
  'fingerprint_schema':'stream_fingerprint_schema' in health,
  'blue_timeline_preserved':'cobra_unified_live_timeline' in text,
  'call_audio_preserved':'CobraCallAudioPolicy' in text,
  'watchdog_no_restart':'buffer_observed_no_restart' in text,
  'native_unchanged':patch.get('native_changed') is False,
  'theme_unchanged':patch.get('theme_zip_changed') is False,
  'physical_unverified':patch.get('physical_device_verified') is False,
 }
 failed=[k for k,v in checks.items() if not v];result={'passed':not failed,'checks':checks,'failed':failed,'build':2103184,'physical_device_verified':False}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 if failed:raise RuntimeError('2103184 source audit failed: '+', '.join(failed))
 print('PASS:',len(checks),'2103184 source checks')
if __name__=='__main__':main()
