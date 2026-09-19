#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103180
BASE_NAME='1.0.9-Cobra-Playback-Finalization-RC1'
BASE_COMMIT='c7a52ef5553152d75f54b713e8975c8e2794e09b'

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
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:raise RuntimeError('Expected exact passed 2103180 source receipt')
    path=source/REL;before_b=path.read_bytes();before=before_b.decode();expected=receipt.get('files',{}).get(str(REL),{}).get('after')
    if not expected or sha(before_b)!=expected:raise RuntimeError('2103180 Activity preimage mismatch')
    text=before

    protected=['cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','promoteCobraPreviewToFullscreen',
      'cobraStartProviderCatchup','cobraGoLive','cobraRewindLive','onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus',
      'cobraApplyDisplayPerformance','cobraTuneLastChannel']
    guards={n:sha(member(before,n)) for n in protected}

    transport=member(text,'CobraTimeshiftTransportPolicy',kind='class')
    transport=once(transport,'    static final int READ_TIMEOUT_MS=15000;\n    static final long LIVE_RESERVE_MS=15000L;',
'''    static final int READ_TIMEOUT_MS=5000;
    static final long LIVE_RESERVE_MS=15000L;
    static final long SEGMENT_TARGET_MS=3000L,MAX_PUBLISHED_SEGMENT_MS=4500L;
    static long publishedSegmentDurationMs(long started,long lastPacket){
      if(started<=0L||lastPacket<=0L)return 250L;
      return Math.max(250L,Math.min(MAX_PUBLISHED_SEGMENT_MS,lastPacket-started));
    }
    static int retainedSegmentCount(int playlistSegments){return Math.max(12,playlistSegments*2+4);}
    static long retainedByteLimit(int windowSeconds){return Math.min(384L*1024L*1024L,Math.max(128L*1024L*1024L,windowSeconds*2048L*1024L));}''','transport correctness policy')
    old_header='''    static String playlistHeader(long mediaSequence){
      return "#EXTM3U\\n#EXT-X-VERSION:3\\n#EXT-X-TARGETDURATION:5\\n"
          +"#EXT-X-MEDIA-SEQUENCE:"+mediaSequence+"\\n"
          +"#EXT-X-START:TIME-OFFSET=-15.0,PRECISE=NO\\n";
    }'''
    new_header='''    static String playlistHeader(long mediaSequence){return playlistHeader(mediaSequence,0L);}
    static String playlistHeader(long mediaSequence,long discontinuitySequence){
      return "#EXTM3U\\n#EXT-X-VERSION:3\\n#EXT-X-TARGETDURATION:5\\n"
          +"#EXT-X-MEDIA-SEQUENCE:"+mediaSequence+"\\n"
          +"#EXT-X-DISCONTINUITY-SEQUENCE:"+Math.max(0L,discontinuitySequence)+"\\n"
          +"#EXT-X-START:TIME-OFFSET=-15.0,PRECISE=NO\\n";
    }'''
    transport=once(transport,old_header,new_header,'playlist discontinuity header')
    text=replace_member(text,'CobraTimeshiftTransportPolicy',transport,kind='class')

    ts=member(text,'CobraLocalTimeshiftSession',kind='class')
    ts=once(ts,
'    private volatile boolean stopped=false,ready=false;private volatile String state="STARTING",lastError="",lastHttpError="";private volatile long bytesRead=0,reconnects=0,stallMs=0,httpRequests=0,httpFailures=0,playlistRequests=0,segmentRequests=0;private volatile long startedElapsed=android.os.SystemClock.elapsedRealtime();',
'    private volatile boolean stopped=false,ready=false;private volatile String state="STARTING",lastError="",lastHttpError="";private volatile long bytesRead=0,reconnects=0,stallMs=0,httpRequests=0,httpFailures=0,playlistRequests=0,segmentRequests=0,segment404s=0,providerLastPacketElapsed=0,lastSegmentPublishedElapsed=0,maxPublishedDurationMs=0;private volatile long startedElapsed=android.os.SystemClock.elapsedRealtime();',
'transport timing diagnostics')
    ts=once(ts,
'    private java.net.ServerSocket server;private Thread serverThread,ingestThread;private long sequence=1,totalBytes=0;private java.io.BufferedOutputStream segmentOut;private File segmentPart;private long segmentStartElapsed,segmentStartWall,segmentBytes;private boolean segmentDiscontinuity,pendingDiscontinuity=false,everConnected=false;',
'    private java.net.ServerSocket server;private Thread serverThread,ingestThread;private long sequence=1,totalBytes=0,discontinuitiesBefore=0;private java.io.BufferedOutputStream segmentOut;private File segmentPart;private long segmentStartElapsed,segmentLastPacketElapsed,segmentStartWall,segmentBytes,segmentDiscontinuitySequence;private boolean segmentDiscontinuity,pendingDiscontinuity=false,everConnected=false;',
'segment timing/discontinuity state')
    ts=once(ts,
'    private static final class Segment {final long seq,durationMs,wallStart,length;final File file;final boolean discontinuity;Segment(long s,long d,long w,long l,File f,boolean x){seq=s;durationMs=d;wallStart=w;length=l;file=f;discontinuity=x;}}',
'    private static final class Segment {final long seq,durationMs,wallStart,length,discontinuitySequence;final File file;final boolean discontinuity;Segment(long s,long d,long w,long l,File f,boolean x,long ds){seq=s;durationMs=d;wallStart=w;length=l;file=f;discontinuity=x;discontinuitySequence=ds;}}',
'segment discontinuity identity')
    ts=once(ts,
'CobraLocalTimeshiftSession(File cache,String url,Map<String,String> requestHeaders,int seconds){windowSeconds=CobraFinalFeaturePolicy.timeshiftSeconds(seconds);maxSegments=Math.max(6,(windowSeconds*1000)/SEGMENT_MS);storageSegments=maxSegments+5;maxBytes=Math.min(256L*1024L*1024L,Math.max(80L*1024L*1024L,windowSeconds*1536L*1024L));source=url;headers=requestHeaders==null?Collections.emptyMap():new HashMap<>(requestHeaders);directory=new File(cache,"cobra-timeshift-"+Long.toHexString(System.nanoTime()));}',
'CobraLocalTimeshiftSession(File cache,String url,Map<String,String> requestHeaders,int seconds){windowSeconds=CobraFinalFeaturePolicy.timeshiftSeconds(seconds);maxSegments=Math.max(6,(windowSeconds*1000)/SEGMENT_MS);storageSegments=CobraTimeshiftTransportPolicy.retainedSegmentCount(maxSegments);maxBytes=CobraTimeshiftTransportPolicy.retainedByteLimit(windowSeconds);source=url;headers=requestHeaders==null?Collections.emptyMap():new HashMap<>(requestHeaders);directory=new File(cache,"cobra-timeshift-"+Long.toHexString(System.nanoTime()));}',
'segment retention')
    ts=once(ts,'server=new java.net.ServerSocket(0,8,java.net.InetAddress.getByName("127.0.0.1"));','server=new java.net.ServerSocket(0,32,java.net.InetAddress.getByName("127.0.0.1"));','local server backlog')
    ts=once(ts,
'    long diskBytes(){synchronized(lock){return totalBytes;}}long reconnects(){return reconnects;}long stallMs(){return stallMs;}long httpRequests(){return httpRequests;}long httpFailures(){return httpFailures;}long playlistRequests(){return playlistRequests;}long segmentRequests(){return segmentRequests;}String lastHttpError(){return lastHttpError;}long ingestKbps(){long elapsed=Math.max(1,android.os.SystemClock.elapsedRealtime()-startedElapsed);return (bytesRead*8L)/elapsed;}',
'''    long diskBytes(){synchronized(lock){return totalBytes;}}long reconnects(){return reconnects;}long stallMs(){return stallMs;}long httpRequests(){return httpRequests;}long httpFailures(){return httpFailures;}long playlistRequests(){return playlistRequests;}long segmentRequests(){return segmentRequests;}long segment404s(){return segment404s;}String lastHttpError(){return lastHttpError;}long ingestKbps(){long elapsed=Math.max(1,android.os.SystemClock.elapsedRealtime()-startedElapsed);return (bytesRead*8L)/elapsed;}
    long providerPacketAgeMs(){long last=providerLastPacketElapsed;return last<=0L?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-last);}
    long latestSegmentAgeMs(){long last=lastSegmentPublishedElapsed;return last<=0L?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-last);}
    long maxPublishedDurationMs(){return maxPublishedDurationMs;}''','transport timing accessors')
    ts=once(ts,
'    String diagnostic(){return "state="+state+"; window_s="+Math.round(windowDurationMs()/1000f)+"; bytes="+diskBytes()+"; provider_kbps="+ingestKbps()+"; reconnects="+reconnects+"; stall_ms="+stallMs+"; http="+httpRequests+"/"+httpFailures+"; playlists="+playlistRequests+"; segments="+segmentRequests+(lastError.isEmpty()?"":"; last="+lastError)+(lastHttpError.isEmpty()?"":"; local_http="+lastHttpError);}',
'    String diagnostic(){return "state="+state+"; window_s="+Math.round(windowDurationMs()/1000f)+"; bytes="+diskBytes()+"; provider_kbps="+ingestKbps()+"; reconnects="+reconnects+"; stall_ms="+stallMs+"; packet_age_ms="+providerPacketAgeMs()+"; segment_age_ms="+latestSegmentAgeMs()+"; max_extinf_ms="+maxPublishedDurationMs+"; http="+httpRequests+"/"+httpFailures+"; segment_404s="+segment404s+"; playlists="+playlistRequests+"; segments="+segmentRequests+(lastError.isEmpty()?"":"; last="+lastError)+(lastHttpError.isEmpty()?"":"; local_http="+lastHttpError);}',
'transport diagnostic detail')

    playlist=member(ts,'playlist')
    playlist=once(playlist,'StringBuilder p=new StringBuilder(CobraTimeshiftTransportPolicy.playlistHeader(list.get(0).seq));',
                           'StringBuilder p=new StringBuilder(CobraTimeshiftTransportPolicy.playlistHeader(list.get(0).seq,list.get(0).discontinuitySequence));',
                           'playlist discontinuity sequence')
    ts=replace_member(ts,'playlist',playlist)

    serve=member(ts,'serve')
    serve=once(serve,'if(file==null||!file.isFile()){reply(s,"404 Not Found","text/plain","missing".getBytes(StandardCharsets.UTF_8),head);return;}',
                     'if(file==null||!file.isFile()){segment404s++;reply(s,"404 Not Found","text/plain","missing".getBytes(StandardCharsets.UTF_8),head);return;}',
                     'segment 404 evidence')
    ts=replace_member(ts,'serve',serve)

    write=member(ts,'writePacket')
    write=once(write,
'private void writePacket(byte[] data,int offset)throws java.io.IOException{if(segmentOut==null)openSegment();segmentOut.write(data,offset,PACKET);segmentBytes+=PACKET;long now=android.os.SystemClock.elapsedRealtime();if(now-segmentStartElapsed>=SEGMENT_MS)finishSegment(true);}',
'private void writePacket(byte[] data,int offset)throws java.io.IOException{if(segmentOut==null)openSegment();segmentOut.write(data,offset,PACKET);segmentBytes+=PACKET;long now=android.os.SystemClock.elapsedRealtime();segmentLastPacketElapsed=now;providerLastPacketElapsed=now;if(now-segmentStartElapsed>=SEGMENT_MS)finishSegment(true);}',
'last packet timing')
    ts=replace_member(ts,'writePacket',write)

    opened=member(ts,'openSegment')
    opened=once(opened,
'private void openSegment()throws java.io.IOException{long seq=sequence++;segmentPart=new File(directory,"seg-"+seq+".part");segmentOut=new java.io.BufferedOutputStream(new java.io.FileOutputStream(segmentPart),65536);segmentStartElapsed=android.os.SystemClock.elapsedRealtime();segmentStartWall=System.currentTimeMillis();segmentBytes=0;segmentDiscontinuity=pendingDiscontinuity;pendingDiscontinuity=false;}',
'private void openSegment()throws java.io.IOException{long seq=sequence++;segmentPart=new File(directory,"seg-"+seq+".part");segmentOut=new java.io.BufferedOutputStream(new java.io.FileOutputStream(segmentPart),65536);segmentStartElapsed=android.os.SystemClock.elapsedRealtime();segmentLastPacketElapsed=segmentStartElapsed;segmentStartWall=System.currentTimeMillis();segmentBytes=0;segmentDiscontinuitySequence=discontinuitiesBefore;segmentDiscontinuity=pendingDiscontinuity;if(segmentDiscontinuity)discontinuitiesBefore++;pendingDiscontinuity=false;}',
'segment discontinuity sequence tracking')
    ts=replace_member(ts,'openSegment',opened)

    finish=member(ts,'finishSegment')
    old='long duration=Math.max(250,android.os.SystemClock.elapsedRealtime()-segmentStartElapsed);'
    new='long duration=CobraTimeshiftTransportPolicy.publishedSegmentDurationMs(segmentStartElapsed,segmentLastPacketElapsed);maxPublishedDurationMs=Math.max(maxPublishedDurationMs,duration);'
    finish=once(finish,old,new,'media duration excludes socket stall')
    finish=once(finish,'Segment seg=new Segment(seq,duration,segmentStartWall,segmentBytes,finalFile,segmentDiscontinuity);',
                         'Segment seg=new Segment(seq,duration,segmentStartWall,segmentBytes,finalFile,segmentDiscontinuity,segmentDiscontinuitySequence);lastSegmentPublishedElapsed=android.os.SystemClock.elapsedRealtime();',
                         'published segment timing')
    ts=replace_member(ts,'finishSegment',finish)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,kind='class')

    health=member(text,'cobraAddSessionHealth')
    health=once(health,
'root.put("timeshift_segment_requests",mCobraTimeshiftSession.segmentRequests());root.put("timeshift_last_http_error",mCobraTimeshiftSession.lastHttpError());',
'root.put("timeshift_segment_requests",mCobraTimeshiftSession.segmentRequests());root.put("timeshift_segment_404s",mCobraTimeshiftSession.segment404s());root.put("timeshift_provider_packet_age_ms",mCobraTimeshiftSession.providerPacketAgeMs());root.put("timeshift_latest_segment_age_ms",mCobraTimeshiftSession.latestSegmentAgeMs());root.put("timeshift_max_published_extinf_ms",mCobraTimeshiftSession.maxPublishedDurationMs());root.put("timeshift_last_http_error",mCobraTimeshiftSession.lastHttpError());',
'diagnostic transport ages')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in guards.items():
        if sha(member(text,n))!=h:raise RuntimeError('Protected 2103180 contract changed: '+n)

    required=['READ_TIMEOUT_MS=5000','publishedSegmentDurationMs','MAX_PUBLISHED_SEGMENT_MS=4500L','retainedSegmentCount','playlistHeader(long mediaSequence,long discontinuitySequence)',
      '#EXT-X-DISCONTINUITY-SEQUENCE:','segment404s','providerPacketAgeMs','latestSegmentAgeMs','maxPublishedDurationMs','storageSegments=CobraTimeshiftTransportPolicy.retainedSegmentCount(maxSegments)',
      'segmentDiscontinuitySequence=discontinuitiesBefore','if(segmentDiscontinuity)discontinuitiesBefore++','timeshift_segment_404s','timeshift_max_published_extinf_ms',
      'cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart']
    for token in required:
        if token not in text:raise RuntimeError('2103181 contract missing: '+token)
    if 'Math.max(250,android.os.SystemClock.elapsedRealtime()-segmentStartElapsed)' in text:raise RuntimeError('Wall-clock outage still inflates EXTINF')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    if 'mPlayer.prepare()' in watchdog or 'mPlayer.play()' in watchdog:raise RuntimeError('watchdog regained restart behavior')

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(REL):{'before':sha(before_b),'after':sha(after)}},
      'provider_read_timeout_ms':5000,'live_reserve_ms':15000,'segment_target_ms':3000,'max_published_segment_ms':4500,
      'segment_duration_excludes_network_idle':True,'discontinuity_sequence_stable':True,'retains_removed_segments_for_prior_snapshots':True,
      'segment_404_diagnostics':True,'provider_packet_age_diagnostics':True,'latest_segment_age_diagnostics':True,
      'unified_blue_timeline_preserved':True,'phone_call_video_continuity_preserved':True,'pro_buffer_safeguards_preserved':True,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103181 HLS transport-integrity repair applied without changing player/rewind ownership')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
