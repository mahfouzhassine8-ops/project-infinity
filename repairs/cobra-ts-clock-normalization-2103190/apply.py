#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103189
BASE_NAME='1.0.9-Cobra-TS-Timeline-Fingerprint-RC1'
BASE_COMMIT='af44c82189b37312abf5f75d9237eef1e3d89dc8'

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

POLICY=r'''
  static final class CobraTimelineNormalizerPolicy {
    static final long MIN_WALL_MS=5000L,MIN_VIDEO_PTS_SAMPLES=120L,MIN_AUDIO_PTS_SAMPLES=20L;
    static final long MIN_UNDERCLOCK_PERMILLE=450L,MAX_UNDERCLOCK_PERMILLE=800L,MAX_TRACK_DELTA_PERMILLE=35L;
    static boolean eligible(long wallMs,long videoSamples,long audioSamples,long videoRate,long audioRate,long dtsRate){
      if(wallMs<MIN_WALL_MS||videoSamples<MIN_VIDEO_PTS_SAMPLES||audioSamples<MIN_AUDIO_PTS_SAMPLES)return false;
      if(videoRate<MIN_UNDERCLOCK_PERMILLE||videoRate>MAX_UNDERCLOCK_PERMILLE)return false;
      if(audioRate<MIN_UNDERCLOCK_PERMILLE||audioRate>MAX_UNDERCLOCK_PERMILLE)return false;
      if(Math.abs(videoRate-audioRate)>MAX_TRACK_DELTA_PERMILLE)return false;
      return dtsRate<0L||Math.abs(videoRate-dtsRate)<=MAX_TRACK_DELTA_PERMILLE;
    }
    static long referenceRatePermille(long videoRate,long audioRate,long dtsRate){
      return dtsRate>0L?(videoRate+audioRate+dtsRate)/3L:(videoRate+audioRate)/2L;
    }
    static long scalePpm(long rawRatePermille){
      if(rawRatePermille<=0L)return 1000000L;
      return Math.max(1000000L,Math.min(2300000L,(1000000000L+(rawRatePermille/2L))/rawRatePermille));
    }
    static long scaleDelta90k(long delta,long scalePpm){return (delta*scalePpm)/1000000L;}
  }
'''

HELPERS=r'''    private void maybeScheduleTimelineNormalizer(){
      if(timelineNormalizerActive||timelineNormalizerPending)return;
      long wall=videoPtsWallSpanMs(),vr=videoPtsRatePermille(),ar=audioPtsRatePermille(),dr=videoDtsRatePermille();
      if(!CobraTimelineNormalizerPolicy.eligible(wall,videoPtsRoleSamples,audioPtsRoleSamples,vr,ar,dr))return;
      long ref=CobraTimelineNormalizerPolicy.referenceRatePermille(vr,ar,dr);
      timelineNormalizerPendingRawRatePermille=ref;
      timelineNormalizerPendingScalePpm=CobraTimelineNormalizerPolicy.scalePpm(ref);
      timelineNormalizerPending=true;
    }
    private void activatePendingTimelineNormalizer(){
      if(timelineNormalizerActive||!timelineNormalizerPending)return;
      synchronized(liveLock){if(liveOut!=null&&liveSocket!=null&&!liveQueue.isEmpty())return;}
      timelineNormalizerRawRatePermille=timelineNormalizerPendingRawRatePermille;
      timelineNormalizerScalePpm=timelineNormalizerPendingScalePpm;
      for(int i=0;i<normalizerPtsAnchor90k.length;i++){normalizerPtsAnchor90k[i]=lastPts90k[i];normalizerPcrAnchor90k[i]=lastPcr90k[i];normalizerDtsAnchor90k[i]=-1L;}
      if(timelineVideoPid>=0&&timelineVideoPid<normalizerDtsAnchor90k.length&&lastVideoDts90k>=0L)normalizerDtsAnchor90k[timelineVideoPid]=lastVideoDts90k;
      timelineNormalizerActivatedElapsed=android.os.SystemClock.elapsedRealtime();
      timelineNormalizerActive=true;timelineNormalizerPending=false;
    }
    private void resetTimelineNormalizerAnchors(){
      java.util.Arrays.fill(normalizerPtsAnchor90k,-1L);java.util.Arrays.fill(normalizerDtsAnchor90k,-1L);java.util.Arrays.fill(normalizerPcrAnchor90k,-1L);
    }
    private long normalize33(long raw,long[] anchors,int pid){
      if(!timelineNormalizerActive||pid<0||pid>=anchors.length)return raw;
      long anchor=anchors[pid];if(anchor<0L){anchors[pid]=raw;return raw;}
      long delta=CobraTsTimelinePolicy.signedDiff90k(raw,anchor);
      return (anchor+CobraTimelineNormalizerPolicy.scaleDelta90k(delta,timelineNormalizerScalePpm))&(CobraTsTimelinePolicy.PTS_MOD-1L);
    }
    private static void encodePts90k(byte[] data,int p,long value){
      long v=value&0x1ffffffffL;int prefix=data[p]&0xf0;
      data[p]=(byte)(prefix|(((v>>30)&7L)<<1)|1);data[p+1]=(byte)(v>>22);data[p+2]=(byte)((((v>>15)&0x7fL)<<1)|1);data[p+3]=(byte)(v>>7);data[p+4]=(byte)(((v&0x7fL)<<1)|1);
    }
    private void normalizeTimelinePacket(byte[] data,int offset){
      if(!timelineNormalizerActive)return;int packetEnd=Math.min(data.length,offset+PACKET);if(offset+4>=packetEnd)return;
      int pid=((data[offset+1]&0x1f)<<8)|(data[offset+2]&255),afc=(data[offset+3]>>4)&3;boolean payload=afc==1||afc==3,pusi=(data[offset+1]&0x40)!=0;int adaptationLength=0;
      if((afc==2||afc==3)&&offset+5<packetEnd){adaptationLength=data[offset+4]&255;boolean disc=adaptationLength>0&&(data[offset+5]&0x80)!=0;if(disc&&pid<normalizerPtsAnchor90k.length){normalizerPtsAnchor90k[pid]=-1L;normalizerDtsAnchor90k[pid]=-1L;normalizerPcrAnchor90k[pid]=-1L;}
        if(adaptationLength>=7&&offset+11<packetEnd&&(data[offset+5]&0x10)!=0){int p=offset+6;long raw=((long)(data[p]&255)<<25)|((long)(data[p+1]&255)<<17)|((long)(data[p+2]&255)<<9)|((long)(data[p+3]&255)<<1)|((data[p+4]&0x80)>>7);long norm=normalize33(raw,normalizerPcrAnchor90k,pid);if(norm!=raw){data[p]=(byte)(norm>>25);data[p+1]=(byte)(norm>>17);data[p+2]=(byte)(norm>>9);data[p+3]=(byte)(norm>>1);data[p+4]=(byte)((data[p+4]&0x7f)|((norm&1L)<<7));timelineNormalizerRewrittenPcr++;}}}
      int payloadOffset=offset+4;if(afc==3)payloadOffset=offset+5+adaptationLength;
      if(payload&&pusi&&payloadOffset+14<=packetEnd&&(data[payloadOffset]&255)==0&&(data[payloadOffset+1]&255)==0&&(data[payloadOffset+2]&255)==1){
        int ptsFlags=(data[payloadOffset+7]>>6)&3;if(ptsFlags>=2){int p=payloadOffset+9;long raw=decodePts90k(data,p),norm=normalize33(raw,normalizerPtsAnchor90k,pid);if(norm!=raw){encodePts90k(data,p,norm);timelineNormalizerRewrittenPts++;}}
        if(ptsFlags==3&&payloadOffset+19<=packetEnd){int p=payloadOffset+14;long raw=decodePts90k(data,p),norm=normalize33(raw,normalizerDtsAnchor90k,pid);if(norm!=raw){encodePts90k(data,p,norm);timelineNormalizerRewrittenDts++;}}
      }
    }
    private void broadcastNormalizedPacket(byte[] data,int offset){
      if(liveOut==null||liveSocket==null)return;
      if(normalizedLiveBatchLen+PACKET>normalizedLiveBatch.length)flushNormalizedLiveBatch();
      System.arraycopy(data,offset,normalizedLiveBatch,normalizedLiveBatchLen,PACKET);normalizedLiveBatchLen+=PACKET;
      if(normalizedLiveBatchLen==normalizedLiveBatch.length)flushNormalizedLiveBatch();
    }
    private void flushNormalizedLiveBatch(){if(normalizedLiveBatchLen<=0)return;broadcastLive(normalizedLiveBatch,normalizedLiveBatchLen);normalizedLiveBatchLen=0;}
    boolean timelineNormalizerActive(){return timelineNormalizerActive;}boolean timelineNormalizerPending(){return timelineNormalizerPending;}long timelineNormalizerRawRatePermille(){return timelineNormalizerRawRatePermille;}long timelineNormalizerScalePpm(){return timelineNormalizerScalePpm;}long timelineNormalizerActivatedAfterMs(){return timelineNormalizerActivatedElapsed<0L?-1L:Math.max(0L,timelineNormalizerActivatedElapsed-startedElapsed);}long timelineNormalizerRewrittenPcr(){return timelineNormalizerRewrittenPcr;}long timelineNormalizerRewrittenPts(){return timelineNormalizerRewrittenPts;}long timelineNormalizerRewrittenDts(){return timelineNormalizerRewrittenDts;}
'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:raise RuntimeError('Expected exact passed 2103189 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode();expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected:raise RuntimeError('2103189 Activity preimage mismatch')
    text=before

    protected_methods=['buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraWatchTimeshiftReady','cobraActivateLocalTimeshift','cobraRewindLive','cobraGoLive','cobraStopLocalTimeshift','cobraDisposePlayer','cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraStartProviderCatchup','showCobraDiagnosticExport','cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport','onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus','cobraApplyDisplayPerformance','cobraTuneLastChannel']
    method_guards={n:sha(member(before,n)) for n in protected_methods}
    class_guards={n:sha(member(before,n,'class')) for n in ['CobraNetworkFamilyPolicy','CobraDiagnosticFreezePolicy','CobraStreamCadencePolicy','CobraTsParserPolicy','CobraTsTimelinePolicy']}

    marker='  static final class CobraTsTimelinePolicy {'
    if text.count(marker)!=1:raise RuntimeError('timeline marker drift')
    text=text.replace(marker,POLICY.rstrip()+'\n\n'+marker,1)

    ts=member(text,'CobraLocalTimeshiftSession',kind='class')
    ts=once(ts,
      '    private volatile long lastIdrElapsed=-1,lastIntraElapsed=-1,lastIdrPts90k=-1,lastIntraPts90k=-1,idrPtsIntervalSamples=0,idrPtsIntervalTotal90k=0,idrPtsIntervalMax90k=0,intraPtsIntervalSamples=0,intraPtsIntervalTotal90k=0,intraPtsIntervalMax90k=0,idrWallIntervalMaxMs=0,intraWallIntervalMaxMs=0;',
      '''    private volatile long lastIdrElapsed=-1,lastIntraElapsed=-1,lastIdrPts90k=-1,lastIntraPts90k=-1,idrPtsIntervalSamples=0,idrPtsIntervalTotal90k=0,idrPtsIntervalMax90k=0,intraPtsIntervalSamples=0,intraPtsIntervalTotal90k=0,intraPtsIntervalMax90k=0,idrWallIntervalMaxMs=0,intraWallIntervalMaxMs=0;
    private volatile boolean timelineNormalizerPending=false,timelineNormalizerActive=false;private volatile long timelineNormalizerPendingRawRatePermille=-1,timelineNormalizerPendingScalePpm=1000000,timelineNormalizerRawRatePermille=-1,timelineNormalizerScalePpm=1000000,timelineNormalizerActivatedElapsed=-1,timelineNormalizerRewrittenPcr=0,timelineNormalizerRewrittenPts=0,timelineNormalizerRewrittenDts=0;
    private final long[] normalizerPtsAnchor90k=new long[8192],normalizerDtsAnchor90k=new long[8192],normalizerPcrAnchor90k=new long[8192];
    private final byte[] normalizedLiveBatch=new byte[PACKET*32];private int normalizedLiveBatchLen=0;''',
      'normalizer fields')

    ts=once(ts,
      'java.util.Arrays.fill(lastPts90k,-1L);directory=new File(cache,"cobra-timeshift-"+Long.toHexString(System.nanoTime()));',
      'java.util.Arrays.fill(lastPts90k,-1L);java.util.Arrays.fill(normalizerPtsAnchor90k,-1L);java.util.Arrays.fill(normalizerDtsAnchor90k,-1L);java.util.Arrays.fill(normalizerPcrAnchor90k,-1L);directory=new File(cache,"cobra-timeshift-"+Long.toHexString(System.nanoTime()));',
      'normalizer ctor')

    anchor='    private void serveLive(java.net.Socket s,boolean head)throws Exception{'
    if ts.count(anchor)!=1:raise RuntimeError('normalizer helper anchor drift')
    ts=ts.replace(anchor,HELPERS.rstrip()+'\n\n'+anchor,1)

    ingest=member(ts,'ingestLoop')
    ingest=once(ingest,
      'if(n==0)continue;observeProviderRead(n);bytesRead+=n;broadcastLive(b,n);consume(b,n);',
      'if(n==0)continue;observeProviderRead(n);bytesRead+=n;if(!timelineNormalizerActive)broadcastLive(b,n);consume(b,n);activatePendingTimelineNormalizer();',
      'conditional live fanout')
    ingest=once(ingest,
      'java.util.Arrays.fill(lastPts90k,-1L);lastError=e.getClass().getSimpleName();',
      'java.util.Arrays.fill(lastPts90k,-1L);resetTimelineNormalizerAnchors();lastError=e.getClass().getSimpleName();',
      'reconnect normalizer reset')
    ts=replace_member(ts,'ingestLoop',ingest)

    write=member(ts,'writePacket')
    write=once(write,
      'observeContinuity(data,offset);segmentOut.write(data,offset,PACKET);',
      'observeContinuity(data,offset);maybeScheduleTimelineNormalizer();if(timelineNormalizerActive){normalizeTimelinePacket(data,offset);broadcastNormalizedPacket(data,offset);}segmentOut.write(data,offset,PACKET);',
      'normalize before storage')
    ts=replace_member(ts,'writePacket',write)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,kind='class')

    health=member(text,'cobraAddSessionHealth')
    health=once(health,
      'root.put("timeshift_last_intra_age_ms",mCobraTimeshiftSession.lastIntraAgeMs());',
      '''root.put("timeshift_last_intra_age_ms",mCobraTimeshiftSession.lastIntraAgeMs());root.put("timeshift_timeline_normalizer_pending",mCobraTimeshiftSession.timelineNormalizerPending());root.put("timeshift_timeline_normalizer_active",mCobraTimeshiftSession.timelineNormalizerActive());root.put("timeshift_timeline_normalizer_raw_rate_permille",mCobraTimeshiftSession.timelineNormalizerRawRatePermille());root.put("timeshift_timeline_normalizer_scale_ppm",mCobraTimeshiftSession.timelineNormalizerScalePpm());root.put("timeshift_timeline_normalizer_activated_after_ms",mCobraTimeshiftSession.timelineNormalizerActivatedAfterMs());root.put("timeshift_timeline_normalizer_rewritten_pcr",mCobraTimeshiftSession.timelineNormalizerRewrittenPcr());root.put("timeshift_timeline_normalizer_rewritten_pts",mCobraTimeshiftSession.timelineNormalizerRewrittenPts());root.put("timeshift_timeline_normalizer_rewritten_dts",mCobraTimeshiftSession.timelineNormalizerRewrittenDts());''',
      'normalizer health')
    health=once(health,'root.put("stream_fingerprint_schema",4);','root.put("stream_fingerprint_schema",5);','schema 5')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in method_guards.items():
        if sha(member(text,n))!=h:raise RuntimeError('Protected owner changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h:raise RuntimeError('Protected class changed: '+n)

    required=['CobraTimelineNormalizerPolicy','MIN_UNDERCLOCK_PERMILLE=450L','MAX_UNDERCLOCK_PERMILLE=800L','maybeScheduleTimelineNormalizer','activatePendingTimelineNormalizer','normalizeTimelinePacket','encodePts90k','broadcastNormalizedPacket','timeshift_timeline_normalizer_active','timeshift_timeline_normalizer_scale_ppm','root.put("stream_fingerprint_schema",5)','DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES','timeshift_video_pts_rate_permille','timeshift_video_dts_rate_permille','timeshift_audio_pts_rate_permille','last_live_before_navigation','cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart']
    for token in required:
        if token not in text:raise RuntimeError('2103190 contract missing: '+token)
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    if 'mPlayer.prepare()' in watchdog or 'mPlayer.play()' in watchdog:raise RuntimeError('watchdog regained restart behavior')

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'stream_fingerprint_schema':5,'conditional_clock_normalization':True,'activation_min_wall_ms':5000,'activation_rate_permille':[450,800],'activation_track_delta_permille':35,
      'normalizes_pcr':True,'normalizes_pts':True,'normalizes_dts':True,'preserves_good_stream_raw_proxy_until_detection':True,'normalizes_rewind_segments_after_activation':True,
      'network_selection_changed':False,'timeshift_ownership_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103190 conditional TS clock normalization applied over exact passed 2103189')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
