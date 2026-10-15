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
    network=block(text,'CobraNetworkFamilyPolicy','class');session=block(text,'CobraLocalTimeshiftSession','class');health=block(text,'cobraAddSessionHealth');normalizer=block(text,'CobraTimelineNormalizerPolicy','class');parser=block(text,'CobraTsParserPolicy','class')
    checks={
      'exact_2103190_parent':patch.get('base_build')==2103190 and patch.get('base_commit')=='f31d1208be0357856a80b59b7118be093212c8a6',
      'route_hash_is_one_way':'MessageDigest.getInstance("SHA-256")' in network and 'routeFingerprint' in network,
      'remote_endpoint_hashed':'connectedRemoteHash' in network and 'getHostAddress()' in network,
      'dns_candidates_hashed':'lastAddressHashes' in network and 'fingerprints.append(routeFingerprint' in network,
      'response_final_host_hashed':'providerFinalHostHash' in session and 'response.request().url().host()' in session,
      'response_path_headers_hashed':'providerResponseHeaderHash' in session and 'response.header("Server")' in session and 'response.header("CF-Ray")' in session,
      'protocol_and_proxy_recorded':'connectedProtocol' in network and 'connectedProxy' in network,
      'raw_provider_url_not_exported':patch.get('raw_provider_url_logged') is False,
      'raw_remote_ip_not_exported':patch.get('raw_remote_ip_logged') is False,
      'diagnostic_fields_exported':all(x in health for x in ('timeshift_provider_remote_hash','timeshift_provider_dns_hashes','timeshift_provider_final_host_hash','timeshift_provider_response_header_hash','timeshift_provider_protocol','timeshift_provider_proxy')),
      'schema_6':'root.put("stream_fingerprint_schema",6)' in health,
      'clock_normalizer_preserved':'MIN_UNDERCLOCK_PERMILLE=450L' in normalizer and 'MAX_UNDERCLOCK_PERMILLE=800L' in normalizer and 'timeshift_timeline_normalizer_active' in health,
      'parser_flags_preserved':'FLAG_DETECT_ACCESS_UNITS' in parser and 'FLAG_ALLOW_NON_IDR_KEYFRAMES' in parser,
      'network_selection_unchanged':patch.get('network_selection_changed') is False,
      'playback_behavior_unchanged':patch.get('playback_behavior_changed') is False,
      'buffer_policy_unchanged':patch.get('buffer_policy_changed') is False,
      'parser_flags_unchanged':patch.get('parser_flags_changed') is False,
      'clock_normalization_unchanged':patch.get('clock_normalization_changed') is False,
      'timeshift_ownership_unchanged':patch.get('timeshift_ownership_changed') is False,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
      'rewind_preserved':'/live.ts' in session and 'timeshift-enter-on-demand' in text,
      'blue_timeline_preserved':'cobra_unified_live_timeline' in text,
      'watchdog_observation_only':'buffer_observed_no_restart' in text,
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103191,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103191 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103191 source checks')
if __name__=='__main__':main()
