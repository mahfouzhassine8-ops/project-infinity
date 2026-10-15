#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')

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
            if c=='\n': line=False
        elif comment:
            if c=='*' and n=='/': comment=False;i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q: q=None
        elif c=='/' and n=='/': line=True;i+=1
        elif c=='/' and n=='*': comment=True;i+=1
        elif c in ('"',"'"): q=c
        elif c=='{': d+=1
        elif c=='}':
            d-=1
            if d==0:return text[start:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
    network=block(text,'CobraNetworkFamilyPolicy','class')
    ssl=block(text,'CobraSniSocketFactory','class')
    session=block(text,'CobraLocalTimeshiftSession','class')
    settings=block(text,'showSettings')
    full=block(text,'cobraStartLocalTimeshift');preview=block(text,'cobraStartLocalTimeshiftPreview')
    health=block(text,'cobraAddSessionHealth')
    chrome=block(text,'cobraBuildPlayerChrome');audio=block(text,'cobraHandleAudioFocus')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]

    checks={
      'exact_2103182_parent':patch.get('base_build')==2103182 and patch.get('base_commit')=='3785ed0bf6fe2cd65eae534f1c394d7001285537',
      'automatic_ipv4_ipv6_ui':'cobra_provider_network_family' in settings and 'showCobraNetworkFamilyPicker' in settings,
      'three_explicit_modes':all(x in text for x in ('Automatic (IPv4 + IPv6)','IPv4 only','IPv6 only','cobra-provider-network:auto','cobra-provider-network:ipv4','cobra-provider-network:ipv6')),
      'automatic_is_default':'static final int AUTO=0,IPV4=4,IPV6=6' in network and 'sanitize(int mode)' in network,
      'family_selection_is_cobra_only':'InetAddress.getAllByName' in network and 'Inet4Address' in network and 'Inet6Address' in network,
      'no_global_java_family_switch':'java.net.preferIPv4Stack' not in text and 'java.net.preferIPv6Addresses' not in text,
      'no_vpn_or_global_proxy':'VpnService' not in text and 'ProxySelector.setDefault' not in text,
      'fullscreen_passes_preference':'cobraTimeshiftSeconds(),cobraNetworkFamilyMode())' in full,
      'preview_passes_preference':'cobraTimeshiftSeconds(),cobraNetworkFamilyMode())' in preview,
      'session_binds_family':'networkFamily=CobraNetworkFamilyPolicy.sanitize(familyMode)' in session,
      'forced_family_rewrites_endpoint':'routedUrl' in network and 'literalForUrl' in network,
      'original_http_host_preserved':'hostHeader(original)' in network and 'setRequestProperty("Host",opened.hostHeader)' in session,
      'https_sni_preserved':'SNIHostName' in ssl and 'serverName' in ssl,
      'https_hostname_verification_preserved':'HostnameVerifier' in network and 'verifier.verify(verifyHost,session)' in network,
      'same_family_rotation_on_reconnect':'Math.floorMod(NEXT.getAndIncrement(),selected.size())' in network,
      'network_diagnostics_exported':all(x in health for x in ('provider_network_preference','timeshift_provider_address_family','timeshift_resolved_ipv4','timeshift_resolved_ipv6')),
      'startup_reserve_preserved':'STARTUP_RESERVE_MS=21000L' in text and 'STARTUP_WAIT_MS=32000L' in text,
      'transport_integrity_preserved':'EXT-X-DISCONTINUITY-SEQUENCE:' in text and 'publishedSegmentDurationMs' in text and 'segment404s' in session,
      'unified_blue_timeline_preserved':'cobra_unified_live_timeline' in chrome and 'footer.addView(mCobraTimeshiftSeek' not in chrome,
      'phone_call_video_continuity_preserved':'video_preserved=true' in audio and '.pause(' not in audio,
      'pro_watchdog_preserved':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103183,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103183 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103183 network-family source checks')

if __name__=='__main__': main()
