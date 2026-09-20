#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103185
BASE_NAME='1.0.9-Cobra-Live-Diagnostics-Freeze-RC1'
BASE_COMMIT='41912bf61440b263898c3e67ad6ba48279473f78'

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
    c=s.count(a)
    if c!=1:raise RuntimeError(f'{label}: expected one anchor, got {c}')
    return s.replace(a,b,1)
def matches(text,name,kind='method'):
    if kind=='method':
        return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
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

POLICY=r'''
  static final class CobraStreamCadencePolicy {
    static final long BUCKET_MS=500L;
    static final long GAP_WARN_MS=500L,GAP_BAD_MS=1000L,GAP_SEVERE_MS=2000L;
    static long bucket(long elapsed){return Math.max(0L,elapsed)/BUCKET_MS;}
    static int gapTier(long gap){return gap>=GAP_SEVERE_MS?3:gap>=GAP_BAD_MS?2:gap>=GAP_WARN_MS?1:0;}
  }
'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103185 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode()
    expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected:raise RuntimeError('2103185 Activity preimage mismatch')
    text=before

    protected_methods=[
      'buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraRewindLive','cobraGoLive',
      'promoteCobraPreviewToFullscreen','cobraActivateLocalTimeshift','cobraWatchTimeshiftReady',
      'showCobraDiagnosticExport','cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport',
      'onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus',
      'cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraApplyDisplayPerformance','cobraTuneLastChannel'
    ]
    guards={n:sha(member(before,n)) for n in protected_methods}
    class_guards={n:sha(member(before,n,'class')) for n in ['CobraNetworkFamilyPolicy','CobraDiagnosticFreezePolicy']}

    marker='  private static final class CobraLocalTimeshiftSession {'
    if text.count(marker)!=1:raise RuntimeError('timeshift marker drift')
    text=text.replace(marker,POLICY.rstrip()+'\n\n'+marker,1)

    # Add provider-ingress and local-proxy cadence state. Each stream is single-writer for its own metrics.
    ts=member(text,'CobraLocalTimeshiftSession',kind='class')
    ts=once(ts,
      '    private volatile long pcrSamples=0,pcrBackwards=0,pcrLargeJumps=0,maxPcrGap90k=0,ptsSamples=0,ptsBackwards=0,ptsLargeJumps=0,maxPtsGap90k=0;',
      '''    private volatile long pcrSamples=0,pcrBackwards=0,pcrLargeJumps=0,maxPcrGap90k=0,ptsSamples=0,ptsBackwards=0,ptsLargeJumps=0,maxPtsGap90k=0;
    private volatile long providerReadEvents=0,providerLastReadElapsed=0,providerLastGapMs=0,providerMaxGapMs=0,providerGap500=0,providerGap1000=0,providerGap2000=0;
    private volatile long providerBucket=-1,providerBucketBytes=0,providerBucketCount=0,providerZeroBuckets=0,providerBucketTotalBytes=0,providerMinBucketBytes=Long.MAX_VALUE,providerMaxBucketBytes=0;
    private volatile long proxyWriteEvents=0,proxyLastWriteElapsed=0,proxyLastGapMs=0,proxyMaxGapMs=0,proxyGap500=0,proxyGap1000=0,proxyGap2000=0;
    private volatile long proxyBucket=-1,proxyBucketBytes=0,proxyBucketCount=0,proxyZeroBuckets=0,proxyBucketTotalBytes=0,proxyMinBucketBytes=Long.MAX_VALUE,proxyMaxBucketBytes=0;''',
      'cadence fields')

    # Add accessors next to existing transport diagnostics.
    ts=once(ts,
      'long maxPtsGap90k(){return maxPtsGap90k;}',
      '''long maxPtsGap90k(){return maxPtsGap90k;}
    long providerReadEvents(){return providerReadEvents;}long providerReadAgeMs(){return providerLastReadElapsed<=0L?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-providerLastReadElapsed);}long providerLastGapMs(){return providerLastGapMs;}long providerMaxGapMs(){return providerMaxGapMs;}long providerGap500(){return providerGap500;}long providerGap1000(){return providerGap1000;}long providerGap2000(){return providerGap2000;}long providerCadenceBuckets(){return providerBucket<0?providerBucketCount:providerBucketCount+1L;}long providerZeroBuckets(){return providerZeroBuckets;}long providerAvgBucketBytes(){long c=providerCadenceBuckets();return c<=0?-1L:(providerBucketTotalBytes+providerBucketBytes)/c;}long providerMinBucketBytes(){if(providerCadenceBuckets()<=0)return -1L;if(providerZeroBuckets>0)return 0L;return Math.min(providerMinBucketBytes==Long.MAX_VALUE?providerBucketBytes:providerMinBucketBytes,providerBucketBytes);}long providerMaxBucketBytes(){return Math.max(providerMaxBucketBytes,providerBucketBytes);}
    long proxyWriteEvents(){return proxyWriteEvents;}long proxyWriteAgeMs(){return proxyLastWriteElapsed<=0L?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-proxyLastWriteElapsed);}long proxyLastGapMs(){return proxyLastGapMs;}long proxyMaxGapMs(){return proxyMaxGapMs;}long proxyGap500(){return proxyGap500;}long proxyGap1000(){return proxyGap1000;}long proxyGap2000(){return proxyGap2000;}long proxyCadenceBuckets(){return proxyBucket<0?proxyBucketCount:proxyBucketCount+1L;}long proxyZeroBuckets(){return proxyZeroBuckets;}long proxyAvgBucketBytes(){long c=proxyCadenceBuckets();return c<=0?-1L:(proxyBucketTotalBytes+proxyBucketBytes)/c;}long proxyMinBucketBytes(){if(proxyCadenceBuckets()<=0)return -1L;if(proxyZeroBuckets>0)return 0L;return Math.min(proxyMinBucketBytes==Long.MAX_VALUE?proxyBucketBytes:proxyMinBucketBytes,proxyBucketBytes);}long proxyMaxBucketBytes(){return Math.max(proxyMaxBucketBytes,proxyBucketBytes);}''',
      'cadence accessors')

    # Add observation helpers before serveLive.
    anchor='    private void serveLive(java.net.Socket s,boolean head)throws Exception{'
    if ts.count(anchor)!=1:raise RuntimeError('serveLive anchor drift')
    cadence_helpers=r'''    private void observeProviderRead(int bytes){
      long now=android.os.SystemClock.elapsedRealtime();providerReadEvents++;
      if(providerLastReadElapsed>0L){long gap=Math.max(0L,now-providerLastReadElapsed);providerLastGapMs=gap;providerMaxGapMs=Math.max(providerMaxGapMs,gap);int tier=CobraStreamCadencePolicy.gapTier(gap);if(tier>=1)providerGap500++;if(tier>=2)providerGap1000++;if(tier>=3)providerGap2000++;}
      providerLastReadElapsed=now;long bucket=CobraStreamCadencePolicy.bucket(now);
      if(providerBucket<0L)providerBucket=bucket;
      else if(bucket!=providerBucket){providerBucketCount++;providerBucketTotalBytes+=providerBucketBytes;providerMinBucketBytes=Math.min(providerMinBucketBytes,providerBucketBytes);providerMaxBucketBytes=Math.max(providerMaxBucketBytes,providerBucketBytes);long skipped=Math.max(0L,bucket-providerBucket-1L);if(skipped>0L){providerZeroBuckets+=skipped;providerBucketCount+=skipped;providerMinBucketBytes=0L;}providerBucket=bucket;providerBucketBytes=0L;}
      providerBucketBytes+=Math.max(0,bytes);
    }
    private void observeProxyWrite(int bytes){
      long now=android.os.SystemClock.elapsedRealtime();proxyWriteEvents++;
      if(proxyLastWriteElapsed>0L){long gap=Math.max(0L,now-proxyLastWriteElapsed);proxyLastGapMs=gap;proxyMaxGapMs=Math.max(proxyMaxGapMs,gap);int tier=CobraStreamCadencePolicy.gapTier(gap);if(tier>=1)proxyGap500++;if(tier>=2)proxyGap1000++;if(tier>=3)proxyGap2000++;}
      proxyLastWriteElapsed=now;long bucket=CobraStreamCadencePolicy.bucket(now);
      if(proxyBucket<0L)proxyBucket=bucket;
      else if(bucket!=proxyBucket){proxyBucketCount++;proxyBucketTotalBytes+=proxyBucketBytes;proxyMinBucketBytes=Math.min(proxyMinBucketBytes,proxyBucketBytes);proxyMaxBucketBytes=Math.max(proxyMaxBucketBytes,proxyBucketBytes);long skipped=Math.max(0L,bucket-proxyBucket-1L);if(skipped>0L){proxyZeroBuckets+=skipped;proxyBucketCount+=skipped;proxyMinBucketBytes=0L;}proxyBucket=bucket;proxyBucketBytes=0L;}
      proxyBucketBytes+=Math.max(0,bytes);
    }

'''
    ts=ts.replace(anchor,cadence_helpers+anchor,1)

    # Provider cadence is measured immediately when upstream bytes arrive, before local fanout or TS parsing.
    ingest=member(ts,'ingestLoop')
    ingest=once(ingest,
      'while(!stopped&&(n=in.read(b))>=0){if(n==0)continue;bytesRead+=n;broadcastLive(b,n);consume(b,n);}',
      'while(!stopped&&(n=in.read(b))>=0){if(n==0)continue;observeProviderRead(n);bytesRead+=n;broadcastLive(b,n);consume(b,n);}',
      'provider read cadence')
    ts=replace_member(ts,'ingestLoop',ingest)

    # Proxy cadence measures completed writes to the local player socket, independently of provider ingress.
    writer=member(ts,'liveWriterLoop')
    writer=once(writer,
      'out.write(chunk);out.flush();liveProxyBytes+=chunk.length;',
      'out.write(chunk);out.flush();liveProxyBytes+=chunk.length;observeProxyWrite(chunk.length);',
      'proxy write cadence')
    ts=replace_member(ts,'liveWriterLoop',writer)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,kind='class')

    # Bind rebuffer events to the exact buffer-ahead and live-ingress/proxy ages at that instant.
    vit=member(text,'CobraSessionVitals',kind='class')
    vit=once(vit,
      '    long lastLoadCompletedElapsed=-1,lastLoadIntervalMs=-1,loadIntervalTotalMs=0,minLoadIntervalMs=Long.MAX_VALUE,maxLoadIntervalMs=0;int loadIntervalSamples=0;',
      '''    long lastLoadCompletedElapsed=-1,lastLoadIntervalMs=-1,loadIntervalTotalMs=0,minLoadIntervalMs=Long.MAX_VALUE,maxLoadIntervalMs=0;int loadIntervalSamples=0;
    long rebufferAheadLastMs=-1,rebufferAheadTotalMs=0,rebufferAheadMinMs=Long.MAX_VALUE,rebufferAheadMaxMs=0;
    long providerAgeAtRebufferLastMs=-1,providerAgeAtRebufferTotalMs=0,providerAgeAtRebufferMaxMs=0;
    long proxyAgeAtRebufferLastMs=-1,proxyAgeAtRebufferTotalMs=0,proxyAgeAtRebufferMaxMs=0;int cadenceRebufferSamples=0,providerAgeRebufferSamples=0,proxyAgeRebufferSamples=0;''',
      'rebuffer cadence fields')
    text=replace_member(text,'CobraSessionVitals',vit,kind='class')

    binding=member(text,'CobraPlayerBinding',kind='class')
    binding=once(binding,
      '        vitals.bufferingTransitions++;',
      '''        long ahead=Math.max(0L,player.getTotalBufferedDuration());vitals.rebufferAheadLastMs=ahead;vitals.rebufferAheadTotalMs+=ahead;vitals.rebufferAheadMinMs=Math.min(vitals.rebufferAheadMinMs,ahead);vitals.rebufferAheadMaxMs=Math.max(vitals.rebufferAheadMaxMs,ahead);
        if(player==mCobraTimeshiftProxyPlayer&&mCobraTimeshiftSession!=null){long providerAge=mCobraTimeshiftSession.providerReadAgeMs(),proxyAge=mCobraTimeshiftSession.proxyWriteAgeMs();vitals.providerAgeAtRebufferLastMs=providerAge;vitals.proxyAgeAtRebufferLastMs=proxyAge;if(providerAge>=0L){vitals.providerAgeAtRebufferTotalMs+=providerAge;vitals.providerAgeAtRebufferMaxMs=Math.max(vitals.providerAgeAtRebufferMaxMs,providerAge);vitals.providerAgeRebufferSamples++;}if(proxyAge>=0L){vitals.proxyAgeAtRebufferTotalMs+=proxyAge;vitals.proxyAgeAtRebufferMaxMs=Math.max(vitals.proxyAgeAtRebufferMaxMs,proxyAge);vitals.proxyAgeRebufferSamples++;}vitals.cadenceRebufferSamples++;}
        vitals.bufferingTransitions++;''',
      'rebuffer instant fingerprint')
    text=replace_member(text,'CobraPlayerBinding',binding,kind='class')

    health=member(text,'cobraAddSessionHealth')
    health=once(health,
      'row.put("load_interval_avg_ms",s.loadIntervalSamples<=0?-1:s.loadIntervalTotalMs/s.loadIntervalSamples);',
      '''row.put("load_interval_avg_ms",s.loadIntervalSamples<=0?-1:s.loadIntervalTotalMs/s.loadIntervalSamples);row.put("rebuffer_buffer_ahead_last_ms",s.rebufferAheadLastMs);row.put("rebuffer_buffer_ahead_avg_ms",s.bufferingTransitions<=0?-1:s.rebufferAheadTotalMs/Math.max(1,s.bufferingTransitions));row.put("rebuffer_buffer_ahead_min_ms",s.rebufferAheadMinMs==Long.MAX_VALUE?-1:s.rebufferAheadMinMs);row.put("rebuffer_buffer_ahead_max_ms",s.rebufferAheadMaxMs);row.put("cadence_rebuffer_samples",s.cadenceRebufferSamples);row.put("provider_age_at_rebuffer_last_ms",s.providerAgeAtRebufferLastMs);row.put("provider_age_at_rebuffer_avg_ms",s.providerAgeRebufferSamples<=0?-1:s.providerAgeAtRebufferTotalMs/s.providerAgeRebufferSamples);row.put("provider_age_at_rebuffer_max_ms",s.providerAgeAtRebufferMaxMs);row.put("proxy_age_at_rebuffer_last_ms",s.proxyAgeAtRebufferLastMs);row.put("proxy_age_at_rebuffer_avg_ms",s.proxyAgeRebufferSamples<=0?-1:s.proxyAgeAtRebufferTotalMs/s.proxyAgeRebufferSamples);row.put("proxy_age_at_rebuffer_max_ms",s.proxyAgeAtRebufferMaxMs);''',
      'session cadence health')

    health=once(health,
      'root.put("timeshift_last_http_error",mCobraTimeshiftSession.lastHttpError());',
      '''root.put("timeshift_provider_read_events",mCobraTimeshiftSession.providerReadEvents());root.put("timeshift_provider_read_age_ms",mCobraTimeshiftSession.providerReadAgeMs());root.put("timeshift_provider_last_gap_ms",mCobraTimeshiftSession.providerLastGapMs());root.put("timeshift_provider_max_gap_ms",mCobraTimeshiftSession.providerMaxGapMs());root.put("timeshift_provider_gap_500_count",mCobraTimeshiftSession.providerGap500());root.put("timeshift_provider_gap_1000_count",mCobraTimeshiftSession.providerGap1000());root.put("timeshift_provider_gap_2000_count",mCobraTimeshiftSession.providerGap2000());root.put("timeshift_provider_500ms_buckets",mCobraTimeshiftSession.providerCadenceBuckets());root.put("timeshift_provider_zero_500ms_buckets",mCobraTimeshiftSession.providerZeroBuckets());root.put("timeshift_provider_500ms_bytes_avg",mCobraTimeshiftSession.providerAvgBucketBytes());root.put("timeshift_provider_500ms_bytes_min",mCobraTimeshiftSession.providerMinBucketBytes());root.put("timeshift_provider_500ms_bytes_max",mCobraTimeshiftSession.providerMaxBucketBytes());root.put("timeshift_proxy_write_events",mCobraTimeshiftSession.proxyWriteEvents());root.put("timeshift_proxy_write_age_ms",mCobraTimeshiftSession.proxyWriteAgeMs());root.put("timeshift_proxy_last_gap_ms",mCobraTimeshiftSession.proxyLastGapMs());root.put("timeshift_proxy_max_gap_ms",mCobraTimeshiftSession.proxyMaxGapMs());root.put("timeshift_proxy_gap_500_count",mCobraTimeshiftSession.proxyGap500());root.put("timeshift_proxy_gap_1000_count",mCobraTimeshiftSession.proxyGap1000());root.put("timeshift_proxy_gap_2000_count",mCobraTimeshiftSession.proxyGap2000());root.put("timeshift_proxy_500ms_buckets",mCobraTimeshiftSession.proxyCadenceBuckets());root.put("timeshift_proxy_zero_500ms_buckets",mCobraTimeshiftSession.proxyZeroBuckets());root.put("timeshift_proxy_500ms_bytes_avg",mCobraTimeshiftSession.proxyAvgBucketBytes());root.put("timeshift_proxy_500ms_bytes_min",mCobraTimeshiftSession.proxyMinBucketBytes());root.put("timeshift_proxy_500ms_bytes_max",mCobraTimeshiftSession.proxyMaxBucketBytes());root.put("timeshift_last_http_error",mCobraTimeshiftSession.lastHttpError());''',
      'timeshift cadence health')
    health=once(health,'root.put("stream_fingerprint_schema",2);','root.put("stream_fingerprint_schema",3);','schema 3')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in guards.items():
        if sha(member(text,n))!=h:raise RuntimeError('Protected 2103185 playback/diagnostic contract changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h:raise RuntimeError('Protected 2103185 class changed: '+n)

    required=[
      'CobraStreamCadencePolicy','BUCKET_MS=500L','GAP_WARN_MS=500L','GAP_BAD_MS=1000L','GAP_SEVERE_MS=2000L',
      'observeProviderRead(n)','observeProxyWrite(chunk.length)','providerMaxGapMs','providerZeroBuckets','proxyMaxGapMs','proxyZeroBuckets',
      'rebuffer_buffer_ahead_last_ms','provider_age_at_rebuffer_last_ms','proxy_age_at_rebuffer_last_ms',
      'timeshift_provider_zero_500ms_buckets','timeshift_proxy_zero_500ms_buckets',
      'root.put("stream_fingerprint_schema",3)',
      'last_live_before_navigation','live_snapshot_frozen_before_navigation',
      'CobraHappyEyeballs','IPv4 only','IPv6 only','cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart'
    ]
    for token in required:
        if token not in text:raise RuntimeError('2103186 contract missing: '+token)

    # New cadence logic is diagnostic-only. No media/session ownership or recovery actions are allowed in it.
    policy=member(text,'CobraStreamCadencePolicy','class')
    for token in ('setMediaItem(','prepare()','play()','seekTo(','release()'):
        if token in policy:raise RuntimeError('Cadence policy became playback owner: '+token)

    after=text.encode();path.write_bytes(after)
    out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={
      'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'stream_fingerprint_schema':3,'cadence_bucket_ms':500,'gap_thresholds_ms':[500,1000,2000],
      'provider_ingress_cadence':True,'local_proxy_write_cadence':True,'rebuffer_instant_correlation':True,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,
      'frozen_live_snapshot_preserved':True,'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False
    }
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103186 stream cadence fingerprint applied over exact passed 2103185')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
