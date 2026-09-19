#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103182
BASE_NAME='1.0.9-Cobra-Timeshift-Startup-Reserve-RC1'
BASE_COMMIT='3785ed0bf6fe2cd65eae534f1c394d7001285537'

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
            if d==0: return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+'\n'+text[b:]
def insert_before_final(text,block):
    i=text.rfind('\n}')
    if i<0: raise RuntimeError('class final brace missing')
    return text[:i]+'\n'+block.rstrip()+'\n'+text[i:]

NETWORK_HELPERS=r'''  static final class CobraProviderConnection {
    final HttpURLConnection connection;final String family,hostHeader;final int ipv4Count,ipv6Count;
    CobraProviderConnection(HttpURLConnection c,String f,String h,int v4,int v6){connection=c;family=f;hostHeader=h;ipv4Count=v4;ipv6Count=v6;}
  }

  static final class CobraNetworkFamilyPolicy {
    static final int AUTO=0,IPV4=4,IPV6=6;
    private static final java.util.concurrent.atomic.AtomicInteger NEXT=new java.util.concurrent.atomic.AtomicInteger();

    static int sanitize(int mode){return mode==IPV4||mode==IPV6?mode:AUTO;}
    static String label(int mode){mode=sanitize(mode);return mode==IPV4?"IPv4 only":mode==IPV6?"IPv6 only":"Automatic (IPv4 + IPv6)";}
    static String shortLabel(int mode){mode=sanitize(mode);return mode==IPV4?"IPv4":mode==IPV6?"IPv6":"AUTO";}
    static boolean matches(java.net.InetAddress address,int mode){
      mode=sanitize(mode);return mode==AUTO||(mode==IPV4&&address instanceof java.net.Inet4Address)||(mode==IPV6&&address instanceof java.net.Inet6Address);
    }
    static boolean ipv4Literal(String host){
      if(host==null)return false;String[] p=host.split("\\.",-1);if(p.length!=4)return false;
      try{for(String x:p){if(x.isEmpty()){return false;}int v=Integer.parseInt(x);if(v<0||v>255)return false;}}catch(NumberFormatException e){return false;}return true;
    }
    static boolean ipv6Literal(String host){return host!=null&&host.indexOf(':')>=0;}
    static String literalForUrl(java.net.InetAddress address){
      String h=address.getHostAddress();int scope=h.indexOf('%');if(scope>=0)h=h.substring(0,scope);
      return address instanceof java.net.Inet6Address?"["+h+"]":h;
    }
    static String hostHeader(java.net.URL original){
      String host=original.getHost();if(ipv6Literal(host)&&!host.startsWith("["))host="["+host+"]";
      int port=original.getPort();return port<0||port==original.getDefaultPort()?host:host+":"+port;
    }
    static java.net.URL routedUrl(java.net.URL original,java.net.InetAddress address)throws java.net.MalformedURLException{
      String user=original.getUserInfo()==null?"":original.getUserInfo()+"@";
      String port=original.getPort()<0?"":":"+original.getPort();
      return new java.net.URL(original.getProtocol()+"://"+user+literalForUrl(address)+port+original.getFile());
    }
    static CobraProviderConnection open(String source,int requested)throws Exception{
      final int mode=sanitize(requested);final java.net.URL original=new java.net.URL(source);
      if(mode==AUTO)return new CobraProviderConnection((HttpURLConnection)original.openConnection(),"AUTO",null,-1,-1);
      final String host=original.getHost();
      if(ipv4Literal(host)||ipv6Literal(host)){
        java.net.InetAddress literal=java.net.InetAddress.getByName(host);
        if(!matches(literal,mode))throw new java.net.UnknownHostException("Provider URL is not "+shortLabel(mode));
        return routed(original,literal,mode,1,0);
      }
      java.net.InetAddress[] all=java.net.InetAddress.getAllByName(host);
      java.util.ArrayList<java.net.InetAddress> selected=new java.util.ArrayList<>();int v4=0,v6=0;
      for(java.net.InetAddress a:all){
        if(a instanceof java.net.Inet4Address)v4++;else if(a instanceof java.net.Inet6Address)v6++;
        if(matches(a,mode))selected.add(a);
      }
      if(selected.isEmpty())throw new java.net.UnknownHostException("No "+shortLabel(mode)+" address for "+host);
      int pick=Math.floorMod(NEXT.getAndIncrement(),selected.size());
      return routed(original,selected.get(pick),mode,v4,v6);
    }
    private static CobraProviderConnection routed(java.net.URL original,java.net.InetAddress address,int mode,int v4,int v6)throws Exception{
      java.net.URL routed=routedUrl(original,address);HttpURLConnection c=(HttpURLConnection)routed.openConnection();
      if(c instanceof javax.net.ssl.HttpsURLConnection){
        final String verifyHost=original.getHost();javax.net.ssl.HttpsURLConnection https=(javax.net.ssl.HttpsURLConnection)c;
        javax.net.ssl.SSLSocketFactory delegate=(javax.net.ssl.SSLSocketFactory)javax.net.ssl.SSLSocketFactory.getDefault();
        https.setSSLSocketFactory(new CobraSniSocketFactory(delegate,verifyHost));
        final javax.net.ssl.HostnameVerifier verifier=javax.net.ssl.HttpsURLConnection.getDefaultHostnameVerifier();
        https.setHostnameVerifier((ignored,session)->verifier.verify(verifyHost,session));
      }
      return new CobraProviderConnection(c,shortLabel(mode),hostHeader(original),v4,v6);
    }
  }

  static final class CobraSniSocketFactory extends javax.net.ssl.SSLSocketFactory {
    private final javax.net.ssl.SSLSocketFactory delegate;private final String serverName;
    CobraSniSocketFactory(javax.net.ssl.SSLSocketFactory d,String host){delegate=d;serverName=host;}
    @Override public String[] getDefaultCipherSuites(){return delegate.getDefaultCipherSuites();}
    @Override public String[] getSupportedCipherSuites(){return delegate.getSupportedCipherSuites();}
    private java.net.Socket tune(java.net.Socket socket){
      if(socket instanceof javax.net.ssl.SSLSocket&&android.os.Build.VERSION.SDK_INT>=24&&serverName!=null&&!serverName.isEmpty()&&!CobraNetworkFamilyPolicy.ipv4Literal(serverName)&&!CobraNetworkFamilyPolicy.ipv6Literal(serverName)){
        try{
          javax.net.ssl.SSLSocket ssl=(javax.net.ssl.SSLSocket)socket;javax.net.ssl.SSLParameters p=ssl.getSSLParameters();
          p.setServerNames(java.util.Collections.singletonList(new javax.net.ssl.SNIHostName(serverName)));ssl.setSSLParameters(p);
        }catch(RuntimeException ignored){}
      }
      return socket;
    }
    @Override public java.net.Socket createSocket()throws java.io.IOException{return tune(delegate.createSocket());}
    @Override public java.net.Socket createSocket(java.net.Socket s,String host,int port,boolean autoClose)throws java.io.IOException{return tune(delegate.createSocket(s,serverName,port,autoClose));}
    @Override public java.net.Socket createSocket(String host,int port)throws java.io.IOException{return tune(delegate.createSocket(host,port));}
    @Override public java.net.Socket createSocket(String host,int port,java.net.InetAddress local,int localPort)throws java.io.IOException{return tune(delegate.createSocket(host,port,local,localPort));}
    @Override public java.net.Socket createSocket(java.net.InetAddress host,int port)throws java.io.IOException{return tune(delegate.createSocket(host,port));}
    @Override public java.net.Socket createSocket(java.net.InetAddress host,int port,java.net.InetAddress local,int localPort)throws java.io.IOException{return tune(delegate.createSocket(host,port,local,localPort));}
  }'''

UI_HELPERS=r'''  private static final String COBRA_PROVIDER_NETWORK_PREFS="cobra_provider_network";
  private static final String COBRA_PROVIDER_NETWORK_FAMILY="address_family";

  private int cobraNetworkFamilyMode(){
    return CobraNetworkFamilyPolicy.sanitize(getSharedPreferences(COBRA_PROVIDER_NETWORK_PREFS,MODE_PRIVATE).getInt(COBRA_PROVIDER_NETWORK_FAMILY,CobraNetworkFamilyPolicy.AUTO));
  }
  private String cobraNetworkFamilyLabel(){return CobraNetworkFamilyPolicy.label(cobraNetworkFamilyMode());}
  private void cobraSaveNetworkFamilyMode(int mode){
    getSharedPreferences(COBRA_PROVIDER_NETWORK_PREFS,MODE_PRIVATE).edit().putInt(COBRA_PROVIDER_NETWORK_FAMILY,CobraNetworkFamilyPolicy.sanitize(mode)).apply();
  }
  private void showCobraNetworkFamilyPicker(){
    LinearLayout rows=cobraOpenSheet("Provider Network","Automatic keeps Android dual-stack. IPv4 only or IPv6 only affects Cobra's upstream Live TV provider connection; it does not change Verizon, Xfinity, VPN, Wi-Fi or any other app. The choice applies the next time playback starts.","provider-network-family");
    boolean dark=cobraSheetIsDark();int current=cobraNetworkFamilyMode();
    LinearLayout automatic=cobraSheetRow("settings","Automatic (IPv4 + IPv6)",current==CobraNetworkFamilyPolicy.AUTO?"Selected":"Android chooses the working address",false,dark,()->{
      cobraSaveNetworkFamilyMode(CobraNetworkFamilyPolicy.AUTO);closeCobraActionSheet();toast("Provider network • Automatic • restart the channel to apply");showSettings();
    });automatic.setTag("cobra-provider-network:auto");rows.addView(automatic);
    LinearLayout ipv4=cobraSheetRow("settings","IPv4 only",current==CobraNetworkFamilyPolicy.IPV4?"Selected":"Use only IPv4 provider addresses",false,dark,()->{
      cobraSaveNetworkFamilyMode(CobraNetworkFamilyPolicy.IPV4);closeCobraActionSheet();toast("Provider network • IPv4 only • restart the channel to apply");showSettings();
    });ipv4.setTag("cobra-provider-network:ipv4");rows.addView(ipv4);
    LinearLayout ipv6=cobraSheetRow("settings","IPv6 only",current==CobraNetworkFamilyPolicy.IPV6?"Selected":"Use only IPv6 provider addresses",false,dark,()->{
      cobraSaveNetworkFamilyMode(CobraNetworkFamilyPolicy.IPV6);closeCobraActionSheet();toast("Provider network • IPv6 only • restart the channel to apply");showSettings();
    });ipv6.setTag("cobra-provider-network:ipv6");rows.addView(ipv6);
  }'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103182 source receipt')
    path=source/REL;before_b=path.read_bytes();before=before_b.decode()
    expected=receipt.get('files',{}).get(str(REL),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103182 Activity preimage mismatch')
    text=before

    protected=['cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','promoteCobraPreviewToFullscreen','cobraStartProviderCatchup',
      'cobraGoLive','cobraRewindLive','onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus',
      'cobraApplyDisplayPerformance','cobraTuneLastChannel']
    guards={n:sha(member(before,n)) for n in protected}

    marker='  private static final class CobraLocalTimeshiftSession {'
    if text.count(marker)!=1: raise RuntimeError('timeshift class marker drift')
    text=text.replace(marker,NETWORK_HELPERS.rstrip()+'\n\n'+marker,1)

    # Settings: explicit user-controlled Automatic / IPv4 / IPv6 mode.
    settings=member(text,'showSettings')
    settings=once(settings,
'''    Button backgroundMode = action("BACKGROUND MODE  •  " + cobraBackgroundModeLabel());
    backgroundMode.setTag("cobra_background_mode");
    backgroundMode.setOnClickListener(v -> showCobraBackgroundModePicker());''',
'''    Button backgroundMode = action("BACKGROUND MODE  •  " + cobraBackgroundModeLabel());
    backgroundMode.setTag("cobra_background_mode");
    backgroundMode.setOnClickListener(v -> showCobraBackgroundModePicker());

    Button providerNetwork = action("PROVIDER NETWORK  •  " + cobraNetworkFamilyLabel());
    providerNetwork.setTag("cobra_provider_network_family");
    providerNetwork.setOnClickListener(v -> showCobraNetworkFamilyPicker());''',
'network settings button')
    settings=once(settings,
'    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));',
'''    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(providerNetwork, new LinearLayout.LayoutParams(-1, dp(56)));''',
'network settings row')
    text=replace_member(text,'showSettings',settings)
    text=insert_before_final(text,UI_HELPERS)

    # Bind the selected family to each new upstream timeshift/provider session.
    full=member(text,'cobraStartLocalTimeshift')
    full=once(full,
'new CobraLocalTimeshiftSession(getCacheDir(),sourceUrl,channel.headers,cobraTimeshiftSeconds())',
'new CobraLocalTimeshiftSession(getCacheDir(),sourceUrl,channel.headers,cobraTimeshiftSeconds(),cobraNetworkFamilyMode())',
'fullscreen provider family')
    text=replace_member(text,'cobraStartLocalTimeshift',full)

    preview=member(text,'cobraStartLocalTimeshiftPreview')
    preview=once(preview,
'new CobraLocalTimeshiftSession(getCacheDir(),sourceUrl,channel.headers,cobraTimeshiftSeconds())',
'new CobraLocalTimeshiftSession(getCacheDir(),sourceUrl,channel.headers,cobraTimeshiftSeconds(),cobraNetworkFamilyMode())',
'preview provider family')
    text=replace_member(text,'cobraStartLocalTimeshiftPreview',preview)

    ts=member(text,'CobraLocalTimeshiftSession',kind='class')
    ctor='CobraLocalTimeshiftSession(File cache,String url,Map<String,String> requestHeaders,int seconds){windowSeconds=CobraFinalFeaturePolicy.timeshiftSeconds(seconds);maxSegments=Math.max(6,(windowSeconds*1000)/SEGMENT_MS);storageSegments=CobraTimeshiftTransportPolicy.retainedSegmentCount(maxSegments);maxBytes=CobraTimeshiftTransportPolicy.retainedByteLimit(windowSeconds);source=url;headers=requestHeaders==null?Collections.emptyMap():new HashMap<>(requestHeaders);directory=new File(cache,"cobra-timeshift-"+Long.toHexString(System.nanoTime()));}'
    new_ctor='''    private final int networkFamily;
    private volatile String lastProviderFamily="AUTO";private volatile int resolvedIpv4=-1,resolvedIpv6=-1;
    CobraLocalTimeshiftSession(File cache,String url,Map<String,String> requestHeaders,int seconds,int familyMode){windowSeconds=CobraFinalFeaturePolicy.timeshiftSeconds(seconds);maxSegments=Math.max(6,(windowSeconds*1000)/SEGMENT_MS);storageSegments=CobraTimeshiftTransportPolicy.retainedSegmentCount(maxSegments);maxBytes=CobraTimeshiftTransportPolicy.retainedByteLimit(windowSeconds);source=url;headers=requestHeaders==null?Collections.emptyMap():new HashMap<>(requestHeaders);networkFamily=CobraNetworkFamilyPolicy.sanitize(familyMode);directory=new File(cache,"cobra-timeshift-"+Long.toHexString(System.nanoTime()));}'''
    ts=once(ts,ctor,new_ctor,'timeshift constructor family binding')

    access='''    String providerNetworkPreference(){return CobraNetworkFamilyPolicy.label(networkFamily);}
    String providerAddressFamily(){return lastProviderFamily;}
    int resolvedIpv4Count(){return resolvedIpv4;}int resolvedIpv6Count(){return resolvedIpv6;}'''
    ts=once(ts,
'    long startupReadyAfterMs(){long v=readyElapsed;return v<=0L?-1L:Math.max(0L,v-startedElapsed);}',
'''    long startupReadyAfterMs(){long v=readyElapsed;return v<=0L?-1L:Math.max(0L,v-startedElapsed);}
'''+access,
'network diagnostics accessors')

    diag=member(ts,'diagnostic')
    diag=once(diag,
'+"; bytes="+diskBytes()',
'+"; network_pref="+providerNetworkPreference()+"; provider_family="+lastProviderFamily+"; resolved_v4="+resolvedIpv4+"; resolved_v6="+resolvedIpv6+"; bytes="+diskBytes()',
'network diagnostic summary')
    ts=replace_member(ts,'diagnostic',diag)

    ingest=member(ts,'ingestLoop')
    ingest=once(ingest,
'          c=(HttpURLConnection)new URL(source).openConnection();',
'''          CobraProviderConnection opened=CobraNetworkFamilyPolicy.open(source,networkFamily);
          c=opened.connection;lastProviderFamily=opened.family;resolvedIpv4=opened.ipv4Count;resolvedIpv6=opened.ipv6Count;''',
'provider family connection')
    ingest=once(ingest,
'          for(Map.Entry<String,String> h:headers.entrySet())if(h.getKey()!=null&&h.getValue()!=null&&!h.getKey().isEmpty())c.setRequestProperty(h.getKey(),h.getValue());',
'''          for(Map.Entry<String,String> h:headers.entrySet())if(h.getKey()!=null&&h.getValue()!=null&&!h.getKey().isEmpty())c.setRequestProperty(h.getKey(),h.getValue());
          if(opened.hostHeader!=null&&!opened.hostHeader.isEmpty())c.setRequestProperty("Host",opened.hostHeader);''',
'preserve original provider host')
    ts=replace_member(ts,'ingestLoop',ingest)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,kind='class')

    health=member(text,'cobraAddSessionHealth')
    brace=health.index('{')+1
    health=health[:brace]+'\n    root.put("provider_network_preference",cobraNetworkFamilyLabel());'+health[brace:]
    health=once(health,
'root.put("timeshift_startup_ready_after_ms",mCobraTimeshiftSession.startupReadyAfterMs());',
'root.put("timeshift_startup_ready_after_ms",mCobraTimeshiftSession.startupReadyAfterMs());root.put("timeshift_provider_network_preference",mCobraTimeshiftSession.providerNetworkPreference());root.put("timeshift_provider_address_family",mCobraTimeshiftSession.providerAddressFamily());root.put("timeshift_resolved_ipv4",mCobraTimeshiftSession.resolvedIpv4Count());root.put("timeshift_resolved_ipv6",mCobraTimeshiftSession.resolvedIpv6Count());',
'health family detail')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected 2103182 contract changed: '+n)

    required=[
      'cobra_provider_network_family','showCobraNetworkFamilyPicker','cobra-provider-network:ipv4','cobra-provider-network:ipv6',
      'CobraNetworkFamilyPolicy','CobraProviderConnection','CobraSniSocketFactory','IPv4 only','IPv6 only',
      'InetAddress.getAllByName','instanceof java.net.Inet4Address','instanceof java.net.Inet6Address',
      'setRequestProperty("Host",opened.hostHeader)','HostnameVerifier','SNIHostName',
      'provider_network_preference','timeshift_provider_address_family','timeshift_resolved_ipv4','timeshift_resolved_ipv6',
      'STARTUP_RESERVE_MS=21000L','LIVE_RESERVE_MS=15000L','READ_TIMEOUT_MS=5000',
      'EXT-X-DISCONTINUITY-SEQUENCE','cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart'
    ]
    for token in required:
        if token not in text: raise RuntimeError('2103183 contract missing: '+token)
    if 'java.net.preferIPv4Stack' in text or 'java.net.preferIPv6Addresses' in text:
        raise RuntimeError('Global JVM family switch is not allowed; selection must stay Cobra-only')
    if 'VpnService' in text or 'ProxySelector.setDefault' in text:
        raise RuntimeError('2103183 must not create a VPN or global proxy')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    if 'mPlayer.prepare()' in watchdog or 'mPlayer.play()' in watchdog:
        raise RuntimeError('watchdog regained restart behavior')

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True)
    (out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={
      'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(REL):{'before':sha(before_b),'after':sha(after)}},
      'provider_network_modes':['AUTO','IPV4_ONLY','IPV6_ONLY'],'automatic_default':True,
      'provider_family_scope':'cobra_live_upstream_timeshift_ingest','does_not_change_device_apn':True,
      'does_not_change_wifi_or_other_apps':True,'does_not_create_vpn_or_proxy':True,
      'https_original_hostname_verification_preserved':True,'https_sni_original_hostname_preserved':True,
      'host_header_original_hostname_preserved':True,'same_family_address_rotation_on_reconnect':True,
      'startup_reserve_ms':21000,'live_reserve_ms':15000,'provider_read_timeout_ms':5000,
      'transport_integrity_preserved':True,'unified_blue_timeline_preserved':True,
      'phone_call_video_continuity_preserved':True,'pro_buffer_safeguards_preserved':True,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103183 Cobra-only Automatic / IPv4-only / IPv6-only provider network control applied')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
