#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103190
BASE_NAME='1.0.9-Cobra-TS-Clock-Normalization-RC1'
BASE_COMMIT='f31d1208be0357856a80b59b7118be093212c8a6'

def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
    c=s.count(a)
    if c!=1: raise RuntimeError(f'{label}: expected one anchor, got {c}')
    return s.replace(a,b,1)
def matches(text,name,kind='method'):
    if kind=='method':
        return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
    return list(re.finditer(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M))
def span(text,name,kind='method'):
    ms=matches(text,name,kind)
    if len(ms)!=1: raise RuntimeError(f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False;i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q: q=None
        elif c=='/' and n=='/': line=True;i+=1
        elif c=='/' and n=='*': block=True;i+=1
        elif c in ('"',"'"): q=c
        elif c=='{': d+=1
        elif c=='}':
            d-=1
            if d==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+'\n'+text[b:]

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103190 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode()
    expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103190 Activity preimage mismatch')
    text=before

    protected_methods=['buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraWatchTimeshiftReady','cobraActivateLocalTimeshift','cobraRewindLive','cobraGoLive','cobraStopLocalTimeshift','cobraDisposePlayer','cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraStartProviderCatchup','showCobraDiagnosticExport','cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport','onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus','cobraApplyDisplayPerformance','cobraTuneLastChannel']
    method_guards={n:sha(member(before,n)) for n in protected_methods}
    class_guards={n:sha(member(before,n,'class')) for n in ['CobraDiagnosticFreezePolicy','CobraStreamCadencePolicy','CobraTsParserPolicy','CobraTsTimelinePolicy','CobraTimelineNormalizerPolicy']}

    network=member(text,'CobraNetworkFamilyPolicy','class')
    network=once(network,
      '    static String memoryKey(String host,int port){return (host==null?"":host.toLowerCase(Locale.US))+":"+port;}',
      '''    static String memoryKey(String host,int port){return (host==null?"":host.toLowerCase(Locale.US))+":"+port;}
    static String routeFingerprint(String value){if(value==null||value.isEmpty())return "";try{java.security.MessageDigest md=java.security.MessageDigest.getInstance("SHA-256");byte[] d=md.digest(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));StringBuilder b=new StringBuilder(16);for(int i=0;i<8;i++)b.append(String.format(Locale.US,"%02x",d[i]&255));return b.toString();}catch(Exception e){return Integer.toHexString(value.hashCode());}}''',
      'route fingerprint helper')

    network=once(network,
      '      final String key;volatile String connectedFamily="UNCONNECTED",happyPreferred="NONE";volatile long connectStarted=-1L,connectMs=-1L,happyRaceMs=-1L;volatile int connectFailures=0;',
      '      final String key;volatile String connectedFamily="UNCONNECTED",happyPreferred="NONE",connectedRemoteHash="",connectedProtocol="NONE",connectedProxy="NONE";volatile long connectStarted=-1L,connectMs=-1L,happyRaceMs=-1L;volatile int connectFailures=0;',
      'network telemetry fields')
    network=once(network,
      '      @Override public void connectEnd(okhttp3.Call call,java.net.InetSocketAddress address,java.net.Proxy proxy,okhttp3.Protocol protocol){connectMs=connectStarted<0?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-connectStarted);int f=family(address.getAddress());connectedFamily=shortLabel(f);recordSuccess(routeKey(address),f);}',
      '      @Override public void connectEnd(okhttp3.Call call,java.net.InetSocketAddress address,java.net.Proxy proxy,okhttp3.Protocol protocol){connectMs=connectStarted<0?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-connectStarted);int f=family(address.getAddress());connectedFamily=shortLabel(f);connectedRemoteHash=routeFingerprint(address.getAddress()==null?address.getHostString():address.getAddress().getHostAddress());connectedProtocol=protocol==null?"NONE":protocol.toString();connectedProxy=proxy==null?"NONE":proxy.type().name();recordSuccess(routeKey(address),f);}',
      'connect end route fingerprint')
    network=once(network,
      '      @Override public void connectionAcquired(okhttp3.Call call,okhttp3.Connection connection){try{java.net.InetSocketAddress address=connection.route().socketAddress();java.net.InetAddress a=address.getAddress();int f=family(a);connectedFamily=shortLabel(f);recordSuccess(routeKey(address),f);}catch(RuntimeException ignored){}}',
      '      @Override public void connectionAcquired(okhttp3.Call call,okhttp3.Connection connection){try{java.net.InetSocketAddress address=connection.route().socketAddress();java.net.InetAddress a=address.getAddress();int f=family(a);connectedFamily=shortLabel(f);connectedRemoteHash=routeFingerprint(a==null?address.getHostString():a.getHostAddress());connectedProtocol=connection.protocol()==null?"NONE":connection.protocol().toString();java.net.Proxy proxy=connection.route().proxy();connectedProxy=proxy==null?"NONE":proxy.type().name();recordSuccess(routeKey(address),f);}catch(RuntimeException ignored){}}',
      'connection acquired route fingerprint')

    network=once(network,
      '      final int mode,port;final NetworkTelemetry telemetry;volatile int lastV4=0,lastV6=0,lastSelected=0;volatile String lastPreferred="NONE";volatile long lookups=0,failures=0;',
      '      final int mode,port;final NetworkTelemetry telemetry;volatile int lastV4=0,lastV6=0,lastSelected=0;volatile String lastPreferred="NONE",lastAddressHashes="";volatile long lookups=0,failures=0;',
      'dns fingerprint field')
    network=once(network,
      '      @Override public java.util.List<java.net.InetAddress> lookup(String hostname)throws java.net.UnknownHostException{lookups++;try{java.net.InetAddress[] all=java.net.InetAddress.getAllByName(hostname);int v4=0,v6=0;for(java.net.InetAddress a:all){if(a instanceof java.net.Inet4Address)v4++;else if(a instanceof java.net.Inet6Address)v6++;}lastV4=v4;lastV6=v6;java.util.List<java.net.InetAddress> out;if(loopbackHost(hostname))out=new ArrayList<>(java.util.Arrays.asList(all));else if(mode==AUTO)out=autoOrder(hostname,port,all,telemetry);else out=filter(all,mode);lastSelected=out.size();lastPreferred=telemetry==null?shortLabel(mode):telemetry.happyPreferred;return out;}catch(java.net.UnknownHostException e){failures++;throw e;}}',
      '      @Override public java.util.List<java.net.InetAddress> lookup(String hostname)throws java.net.UnknownHostException{lookups++;try{java.net.InetAddress[] all=java.net.InetAddress.getAllByName(hostname);int v4=0,v6=0;StringBuilder fingerprints=new StringBuilder();for(java.net.InetAddress a:all){if(a instanceof java.net.Inet4Address)v4++;else if(a instanceof java.net.Inet6Address)v6++;if(fingerprints.length()>0)fingerprints.append(",");fingerprints.append(routeFingerprint(a.getHostAddress()));}lastV4=v4;lastV6=v6;lastAddressHashes=fingerprints.toString();java.util.List<java.net.InetAddress> out;if(loopbackHost(hostname))out=new ArrayList<>(java.util.Arrays.asList(all));else if(mode==AUTO)out=autoOrder(hostname,port,all,telemetry);else out=filter(all,mode);lastSelected=out.size();lastPreferred=telemetry==null?shortLabel(mode):telemetry.happyPreferred;return out;}catch(java.net.UnknownHostException e){failures++;throw e;}}',
      'dns address fingerprints')
    text=replace_member(text,'CobraNetworkFamilyPolicy',network,'class')

    ts=member(text,'CobraLocalTimeshiftSession','class')
    ts=once(ts,
      '    private final CobraNetworkFamilyPolicy.NetworkTelemetry providerTelemetry;private final CobraNetworkFamilyPolicy.FamilyDns providerDns;private final okhttp3.OkHttpClient providerClient;',
      '    private final CobraNetworkFamilyPolicy.NetworkTelemetry providerTelemetry;private final CobraNetworkFamilyPolicy.FamilyDns providerDns;private final okhttp3.OkHttpClient providerClient;private volatile int providerHttpCode=-1;private volatile long providerContentLength=-1;private volatile String providerFinalHostHash="",providerResponseProtocol="NONE",providerResponseHeaderHash="",providerContentType="";',
      'provider response fingerprint fields')
    ts=once(ts,
      '    long providerConnectMs(){return providerTelemetry.connectMs;}long happyRaceMs(){return providerTelemetry.happyRaceMs;}int providerConnectFailures(){return providerTelemetry.connectFailures;}boolean providerHasData(){return bytesRead>0L;}long startupElapsedMs(){return Math.max(0L,android.os.SystemClock.elapsedRealtime()-startedElapsed);}',
      '    long providerConnectMs(){return providerTelemetry.connectMs;}long happyRaceMs(){return providerTelemetry.happyRaceMs;}int providerConnectFailures(){return providerTelemetry.connectFailures;}boolean providerHasData(){return bytesRead>0L;}long startupElapsedMs(){return Math.max(0L,android.os.SystemClock.elapsedRealtime()-startedElapsed);}String providerRemoteHash(){return providerTelemetry.connectedRemoteHash;}String providerDnsHashes(){return providerDns.lastAddressHashes;}String providerProtocol(){return providerTelemetry.connectedProtocol;}String providerProxy(){return providerTelemetry.connectedProxy;}int providerHttpCode(){return providerHttpCode;}String providerFinalHostHash(){return providerFinalHostHash;}String providerResponseProtocol(){return providerResponseProtocol;}String providerResponseHeaderHash(){return providerResponseHeaderHash;}String providerContentType(){return providerContentType;}long providerContentLength(){return providerContentLength;}',
      'provider route accessors')
    ingest=member(ts,'ingestLoop')
    ingest=once(ingest,
      'response=providerClient.newCall(request.build()).execute();int code=response.code();if(code<200||code>=300)',
      'response=providerClient.newCall(request.build()).execute();int code=response.code();providerHttpCode=code;providerFinalHostHash=CobraNetworkFamilyPolicy.routeFingerprint(response.request().url().host());providerResponseProtocol=response.protocol()==null?"NONE":response.protocol().toString();providerResponseHeaderHash=CobraNetworkFamilyPolicy.routeFingerprint(String.valueOf(response.header("Server"))+"|"+String.valueOf(response.header("Via"))+"|"+String.valueOf(response.header("X-Cache"))+"|"+String.valueOf(response.header("CF-Ray"))+"|"+String.valueOf(response.header("Age")));providerContentType=response.body()!=null&&response.body().contentType()!=null?response.body().contentType().toString():"";providerContentLength=response.body()==null?-1L:response.body().contentLength();if(code<200||code>=300)',
      'provider response metadata')
    ts=replace_member(ts,'ingestLoop',ingest)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,'class')

    health=member(text,'cobraAddSessionHealth')
    health=once(health,
      'root.put("timeshift_provider_connect_failures",mCobraTimeshiftSession.providerConnectFailures());',
      'root.put("timeshift_provider_connect_failures",mCobraTimeshiftSession.providerConnectFailures());root.put("timeshift_provider_remote_hash",mCobraTimeshiftSession.providerRemoteHash());root.put("timeshift_provider_dns_hashes",mCobraTimeshiftSession.providerDnsHashes());root.put("timeshift_provider_protocol",mCobraTimeshiftSession.providerProtocol());root.put("timeshift_provider_proxy",mCobraTimeshiftSession.providerProxy());root.put("timeshift_provider_http_code",mCobraTimeshiftSession.providerHttpCode());root.put("timeshift_provider_final_host_hash",mCobraTimeshiftSession.providerFinalHostHash());root.put("timeshift_provider_response_protocol",mCobraTimeshiftSession.providerResponseProtocol());root.put("timeshift_provider_response_header_hash",mCobraTimeshiftSession.providerResponseHeaderHash());root.put("timeshift_provider_content_type",mCobraTimeshiftSession.providerContentType());root.put("timeshift_provider_content_length",mCobraTimeshiftSession.providerContentLength());',
      'route fingerprint health')
    health=once(health,'root.put("stream_fingerprint_schema",5);','root.put("stream_fingerprint_schema",6);','schema 6')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in method_guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected playback owner changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h: raise RuntimeError('Protected class changed: '+n)

    required=['routeFingerprint','connectedRemoteHash','lastAddressHashes','providerFinalHostHash','providerResponseHeaderHash','timeshift_provider_remote_hash','timeshift_provider_dns_hashes','timeshift_provider_final_host_hash','timeshift_provider_response_header_hash','root.put("stream_fingerprint_schema",6)','timeshift_timeline_normalizer_active','MIN_UNDERCLOCK_PERMILLE=450L','DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES','last_live_before_navigation','cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart']
    for token in required:
        if token not in text: raise RuntimeError('2103191 contract missing: '+token)

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'stream_fingerprint_schema':6,'provider_route_fingerprint':True,'provider_remote_hash':True,'provider_dns_hashes':True,'provider_final_host_hash':True,'provider_response_header_hash':True,'raw_provider_url_logged':False,'raw_remote_ip_logged':False,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,'clock_normalization_changed':False,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103191 provider-route fingerprint applied over exact passed 2103190 without playback/network behavior changes')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
