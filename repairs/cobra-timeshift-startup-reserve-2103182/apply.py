#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103181
BASE_NAME='1.0.9-Cobra-Timeshift-Transport-Integrity-RC1'
BASE_COMMIT='bfc69d84552dd64ef39946bdd2b368e7ff1def52'

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
    c=s.count(a)
    if c!=1:raise RuntimeError(f'{label}: expected one anchor, got {c}')
    return s.replace(a,b,1)
def matches(text,name,kind='method'):
    if kind=='method':return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
    return list(re.finditer(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M))
def span(text,name,kind='method'):
    ms=matches(text,name,kind)
    if len(ms)!=1:raise RuntimeError(f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False;i+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':block=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
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
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:raise RuntimeError('Expected exact passed 2103181 source receipt')
    path=source/REL;before_b=path.read_bytes();before=before_b.decode();expected=receipt.get('files',{}).get(str(REL),{}).get('after')
    if not expected or sha(before_b)!=expected:raise RuntimeError('2103181 Activity preimage mismatch')
    text=before

    protected=['cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','promoteCobraPreviewToFullscreen','cobraStartProviderCatchup',
      'cobraGoLive','cobraRewindLive','onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus',
      'cobraApplyDisplayPerformance','cobraTuneLastChannel']
    guards={n:sha(member(before,n)) for n in protected}

    transport=member(text,'CobraTimeshiftTransportPolicy',kind='class')
    transport=once(transport,
'    static final long SEGMENT_TARGET_MS=3000L,MAX_PUBLISHED_SEGMENT_MS=4500L;',
'''    static final long SEGMENT_TARGET_MS=3000L,MAX_PUBLISHED_SEGMENT_MS=4500L;
    static final long STARTUP_RESERVE_MS=21000L,STARTUP_WAIT_MS=32000L;
    static boolean startupReady(long windowMs){return windowMs>=STARTUP_RESERVE_MS;}''',
'startup reserve policy')
    text=replace_member(text,'CobraTimeshiftTransportPolicy',transport,kind='class')

    ts=member(text,'CobraLocalTimeshiftSession',kind='class')
    ts=once(ts,'    private static final int PACKET=188,SEGMENT_MS=3000,READY_SEGMENTS=3;',
                 '    private static final int PACKET=188,SEGMENT_MS=3000;','remove premature ready count')
    ts=once(ts,
'    private volatile boolean stopped=false,ready=false;private volatile String state="STARTING",lastError="",lastHttpError="";private volatile long bytesRead=0,reconnects=0,stallMs=0,httpRequests=0,httpFailures=0,playlistRequests=0,segmentRequests=0,segment404s=0,providerLastPacketElapsed=0,lastSegmentPublishedElapsed=0,maxPublishedDurationMs=0;private volatile long startedElapsed=android.os.SystemClock.elapsedRealtime();',
'    private volatile boolean stopped=false,ready=false;private volatile String state="STARTING",lastError="",lastHttpError="";private volatile long bytesRead=0,reconnects=0,stallMs=0,httpRequests=0,httpFailures=0,playlistRequests=0,segmentRequests=0,segment404s=0,providerLastPacketElapsed=0,lastSegmentPublishedElapsed=0,maxPublishedDurationMs=0,readyElapsed=0;private volatile long startedElapsed=android.os.SystemClock.elapsedRealtime();',
'ready timing')
    ts=once(ts,
'    long maxPublishedDurationMs(){return maxPublishedDurationMs;}',
'''    long maxPublishedDurationMs(){return maxPublishedDurationMs;}
    long startupReadyAfterMs(){long v=readyElapsed;return v<=0L?-1L:Math.max(0L,v-startedElapsed);}''',
'ready timing accessor')
    ts=once(ts,
'    String diagnostic(){return "state="+state+"; window_s="+Math.round(windowDurationMs()/1000f)+"; bytes="+diskBytes()+"; provider_kbps="+ingestKbps()+"; reconnects="+reconnects+"; stall_ms="+stallMs+"; packet_age_ms="+providerPacketAgeMs()+"; segment_age_ms="+latestSegmentAgeMs()+"; max_extinf_ms="+maxPublishedDurationMs+"; http="+httpRequests+"/"+httpFailures+"; segment_404s="+segment404s+"; playlists="+playlistRequests+"; segments="+segmentRequests+(lastError.isEmpty()?"":"; last="+lastError)+(lastHttpError.isEmpty()?"":"; local_http="+lastHttpError);}',
'    String diagnostic(){return "state="+state+"; window_s="+Math.round(windowDurationMs()/1000f)+"; startup_target_s="+Math.round(CobraTimeshiftTransportPolicy.STARTUP_RESERVE_MS/1000f)+"; ready_after_ms="+startupReadyAfterMs()+"; bytes="+diskBytes()+"; provider_kbps="+ingestKbps()+"; reconnects="+reconnects+"; stall_ms="+stallMs+"; packet_age_ms="+providerPacketAgeMs()+"; segment_age_ms="+latestSegmentAgeMs()+"; max_extinf_ms="+maxPublishedDurationMs+"; http="+httpRequests+"/"+httpFailures+"; segment_404s="+segment404s+"; playlists="+playlistRequests+"; segments="+segmentRequests+(lastError.isEmpty()?"":"; last="+lastError)+(lastHttpError.isEmpty()?"":"; local_http="+lastHttpError);}',
'startup diagnostic detail')

    finish=member(ts,'finishSegment')
    finish=once(finish,
'if(!ready&&segments.size()>=READY_SEGMENTS){ready=true;state="READY";readyLatch.countDown();}else if(ready)state="READY";',
'if(!ready&&CobraTimeshiftTransportPolicy.startupReady(windowDurationMs())){ready=true;readyElapsed=android.os.SystemClock.elapsedRealtime();state="READY";readyLatch.countDown();}else if(ready)state="READY";',
'ready only after real reserve')
    ts=replace_member(ts,'finishSegment',finish)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,kind='class')

    full=member(text,'cobraStartLocalTimeshift')
    full=once(full,'boolean ready=session.awaitReady(18000L);','boolean ready=session.awaitReady(CobraTimeshiftTransportPolicy.STARTUP_WAIT_MS);','fullscreen startup wait')
    text=replace_member(text,'cobraStartLocalTimeshift',full)

    preview=member(text,'cobraStartLocalTimeshiftPreview')
    preview=once(preview,'boolean ready=session.awaitReady(18000L);','boolean ready=session.awaitReady(CobraTimeshiftTransportPolicy.STARTUP_WAIT_MS);','preview startup wait')
    text=replace_member(text,'cobraStartLocalTimeshiftPreview',preview)

    health=member(text,'cobraAddSessionHealth')
    health=once(health,
'root.put("timeshift_max_published_extinf_ms",mCobraTimeshiftSession.maxPublishedDurationMs());root.put("timeshift_last_http_error",mCobraTimeshiftSession.lastHttpError());',
'root.put("timeshift_max_published_extinf_ms",mCobraTimeshiftSession.maxPublishedDurationMs());root.put("timeshift_startup_reserve_ms",CobraTimeshiftTransportPolicy.STARTUP_RESERVE_MS);root.put("timeshift_startup_ready_after_ms",mCobraTimeshiftSession.startupReadyAfterMs());root.put("timeshift_last_http_error",mCobraTimeshiftSession.lastHttpError());',
'startup diagnostics')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in guards.items():
        if sha(member(text,n))!=h:raise RuntimeError('Protected 2103181 contract changed: '+n)

    required=['STARTUP_RESERVE_MS=21000L','STARTUP_WAIT_MS=32000L','startupReady(long windowMs)',
      'startupReady(windowDurationMs())','readyElapsed=android.os.SystemClock.elapsedRealtime()',
      'awaitReady(CobraTimeshiftTransportPolicy.STARTUP_WAIT_MS)','timeshift_startup_reserve_ms','timeshift_startup_ready_after_ms',
      'LIVE_RESERVE_MS=15000L','READ_TIMEOUT_MS=5000','EXT-X-DISCONTINUITY-SEQUENCE','cobra_unified_live_timeline',
      'CobraCallAudioPolicy','buffer_observed_no_restart','MAX_AUTO_LIVE_EDGE_ATTEMPTS=2']
    for token in required:
        if token not in text:raise RuntimeError('2103182 contract missing: '+token)
    if 'READY_SEGMENTS' in member(text,'CobraLocalTimeshiftSession',kind='class'):raise RuntimeError('premature segment-count readiness survived')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    if 'mPlayer.prepare()' in watchdog or 'mPlayer.play()' in watchdog:raise RuntimeError('watchdog regained restart behavior')

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(REL):{'before':sha(before_b),'after':sha(after)}},
      'startup_reserve_ms':21000,'startup_wait_ms':32000,'live_reserve_ms':15000,'provider_read_timeout_ms':5000,
      'readiness_uses_actual_window_duration':True,'premature_nine_second_start_removed':True,
      'transport_integrity_preserved':True,'unified_blue_timeline_preserved':True,'phone_call_video_continuity_preserved':True,
      'pro_buffer_safeguards_preserved':True,'dns_pin_or_custom_resolver_added':False,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103182 startup-reserve repair applied; playback no longer starts before the configured live reserve exists')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
