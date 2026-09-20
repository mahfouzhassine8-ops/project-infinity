#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103191
BASE_NAME='1.0.9-Cobra-Provider-Route-Fingerprint-RC1'
BASE_COMMIT='23fab77d21e97e6f74f04f397d3fa0a63a24bc2e'

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

PACE_POLICY=r'''  static final class CobraProviderPacePolicy {
    static final long MIN_WALL_MS=15000L,MIN_VIDEO_PTS_SAMPLES=240L,MIN_AUDIO_PTS_SAMPLES=40L;
    static final long MIN_RATE_PERMILLE=450L,MAX_RATE_PERMILLE=800L,MAX_TRACK_DELTA_PERMILLE=35L;
    static final long MAX_PROVIDER_AGE_MS=500L,MAX_PROVIDER_GAP_MS=1000L;
    static boolean shouldUseReserve(long wallMs,long videoSamples,long audioSamples,long videoRate,long audioRate,long dtsRate,long providerAge,long providerMaxGap,long zeroBuckets,long continuityErrors,long syncLosses){
      if(wallMs<MIN_WALL_MS||videoSamples<MIN_VIDEO_PTS_SAMPLES||audioSamples<MIN_AUDIO_PTS_SAMPLES)return false;
      if(videoRate<MIN_RATE_PERMILLE||videoRate>MAX_RATE_PERMILLE||audioRate<MIN_RATE_PERMILLE||audioRate>MAX_RATE_PERMILLE)return false;
      if(Math.abs(videoRate-audioRate)>MAX_TRACK_DELTA_PERMILLE)return false;
      if(dtsRate>0L&&Math.abs(videoRate-dtsRate)>MAX_TRACK_DELTA_PERMILLE)return false;
      if(providerAge<0L||providerAge>MAX_PROVIDER_AGE_MS||providerMaxGap>MAX_PROVIDER_GAP_MS||zeroBuckets>0L)return false;
      return continuityErrors==0L&&syncLosses==0L;
    }
  }'''

RELEASE_HELPER=r'''    private void maybeReleaseTimelineNormalizer()throws java.io.IOException{
      if(!timelineNormalizerActive)return;
      long wall=videoPtsWallSpanMs(),vr=videoPtsRatePermille(),ar=audioPtsRatePermille(),dr=videoDtsRatePermille();
      if(!CobraTimelineNormalizerPolicy.recovered(wall,videoPtsRoleSamples,audioPtsRoleSamples,vr,ar,dr))return;
      flushNormalizedLiveBatch();finishSegment(true);pendingDiscontinuity=true;
      timelineNormalizerActive=false;timelineNormalizerPending=false;timelineNormalizerReleasedElapsed=android.os.SystemClock.elapsedRealtime();timelineNormalizerReleases++;
      resetTimelineNormalizerAnchors();
    }
'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103191 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode()
    expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103191 Activity preimage mismatch')
    text=before

    protected_methods=['buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraActivateLocalTimeshift','cobraRewindLive','cobraGoLive','cobraStopLocalTimeshift','cobraDisposePlayer','cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraStartProviderCatchup','showCobraDiagnosticExport','cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport','onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus','cobraApplyDisplayPerformance','cobraTuneLastChannel']
    method_guards={n:sha(member(before,n)) for n in protected_methods}
    class_guards={n:sha(member(before,n,'class')) for n in ['CobraNetworkFamilyPolicy','CobraDiagnosticFreezePolicy','CobraStreamCadencePolicy','CobraTsParserPolicy','CobraTsTimelinePolicy']}

    normalizer=member(text,'CobraTimelineNormalizerPolicy','class')
    normalizer=once(normalizer,
      '    static final long MIN_WALL_MS=5000L,MIN_VIDEO_PTS_SAMPLES=120L,MIN_AUDIO_PTS_SAMPLES=20L;',
      '    static final long MIN_WALL_MS=5000L,MIN_VIDEO_PTS_SAMPLES=120L,MIN_AUDIO_PTS_SAMPLES=20L;\n    static final long RECOVERY_MIN_WALL_MS=15000L,RECOVERY_MIN_RATE_PERMILLE=900L,RECOVERY_MAX_RATE_PERMILLE=1100L;',
      'normalizer recovery constants')
    normalizer=once(normalizer,
      '    static long scaleDelta90k(long delta,long scalePpm){return (delta*scalePpm)/1000000L;}',
      '''    static long scaleDelta90k(long delta,long scalePpm){return (delta*scalePpm)/1000000L;}
    static boolean recovered(long wallMs,long videoSamples,long audioSamples,long videoRate,long audioRate,long dtsRate){
      if(wallMs<RECOVERY_MIN_WALL_MS||videoSamples<MIN_VIDEO_PTS_SAMPLES||audioSamples<MIN_AUDIO_PTS_SAMPLES)return false;
      if(videoRate<RECOVERY_MIN_RATE_PERMILLE||videoRate>RECOVERY_MAX_RATE_PERMILLE)return false;
      if(audioRate<RECOVERY_MIN_RATE_PERMILLE||audioRate>RECOVERY_MAX_RATE_PERMILLE)return false;
      if(Math.abs(videoRate-audioRate)>MAX_TRACK_DELTA_PERMILLE)return false;
      return dtsRate<0L||Math.abs(videoRate-dtsRate)<=MAX_TRACK_DELTA_PERMILLE;
    }''',
      'normalizer recovery predicate')
    text=replace_member(text,'CobraTimelineNormalizerPolicy',normalizer,'class')

    marker='  static final class CobraTimelineNormalizerPolicy {'
    a,b=span(text,'CobraTimelineNormalizerPolicy','class')
    if PACE_POLICY.strip() in text: raise RuntimeError('pace policy already present')
    text=text[:b]+'\n\n'+PACE_POLICY+text[b:]

    ts=member(text,'CobraLocalTimeshiftSession','class')
    ts=once(ts,
      '    private volatile boolean timelineNormalizerPending=false,timelineNormalizerActive=false;private volatile long timelineNormalizerPendingRawRatePermille=-1,timelineNormalizerPendingScalePpm=1000000,timelineNormalizerRawRatePermille=-1,timelineNormalizerScalePpm=1000000,timelineNormalizerActivatedElapsed=-1,timelineNormalizerRewrittenPcr=0,timelineNormalizerRewrittenPts=0,timelineNormalizerRewrittenDts=0;',
      '    private volatile boolean timelineNormalizerPending=false,timelineNormalizerActive=false;private volatile long timelineNormalizerPendingRawRatePermille=-1,timelineNormalizerPendingScalePpm=1000000,timelineNormalizerRawRatePermille=-1,timelineNormalizerScalePpm=1000000,timelineNormalizerActivatedElapsed=-1,timelineNormalizerReleasedElapsed=-1,timelineNormalizerReleases=0,timelineNormalizerRewrittenPcr=0,timelineNormalizerRewrittenPts=0,timelineNormalizerRewrittenDts=0;private volatile long paceReserveActivations=0;',
      'pace/release fields')
    ts=once(ts,
      '    private void resetTimelineNormalizerAnchors(){',
      RELEASE_HELPER+'    private void resetTimelineNormalizerAnchors(){',
      'normalizer release helper')
    # Accessors are a single dense line in the inherited source.
    ts=once(ts,
      'boolean timelineNormalizerActive(){return timelineNormalizerActive;}boolean timelineNormalizerPending(){return timelineNormalizerPending;}long timelineNormalizerRawRatePermille(){return timelineNormalizerRawRatePermille;}long timelineNormalizerScalePpm(){return timelineNormalizerScalePpm;}long timelineNormalizerActivatedAfterMs(){return timelineNormalizerActivatedElapsed<0L?-1L:Math.max(0L,timelineNormalizerActivatedElapsed-startedElapsed);}long timelineNormalizerRewrittenPcr(){return timelineNormalizerRewrittenPcr;}long timelineNormalizerRewrittenPts(){return timelineNormalizerRewrittenPts;}long timelineNormalizerRewrittenDts(){return timelineNormalizerRewrittenDts;}',
      'boolean timelineNormalizerActive(){return timelineNormalizerActive;}boolean timelineNormalizerPending(){return timelineNormalizerPending;}long timelineNormalizerRawRatePermille(){return timelineNormalizerRawRatePermille;}long timelineNormalizerScalePpm(){return timelineNormalizerScalePpm;}long timelineNormalizerActivatedAfterMs(){return timelineNormalizerActivatedElapsed<0L?-1L:Math.max(0L,timelineNormalizerActivatedElapsed-startedElapsed);}long timelineNormalizerReleasedAfterMs(){return timelineNormalizerReleasedElapsed<0L?-1L:Math.max(0L,timelineNormalizerReleasedElapsed-startedElapsed);}long timelineNormalizerReleases(){return timelineNormalizerReleases;}long timelineNormalizerRewrittenPcr(){return timelineNormalizerRewrittenPcr;}long timelineNormalizerRewrittenPts(){return timelineNormalizerRewrittenPts;}long timelineNormalizerRewrittenDts(){return timelineNormalizerRewrittenDts;}boolean paceReserveEligible(){return CobraProviderPacePolicy.shouldUseReserve(videoPtsWallSpanMs(),videoPtsRoleSamples,audioPtsRoleSamples,videoPtsRatePermille(),audioPtsRatePermille(),videoDtsRatePermille(),providerReadAgeMs(),providerMaxGapMs,providerZeroBuckets,tsContinuityErrors,tsSyncLosses);}void markPaceReserveActivation(){paceReserveActivations++;}long paceReserveActivations(){return paceReserveActivations;}',
      'pace/release accessors')

    ingest=member(ts,'ingestLoop')
    ingest=once(ingest,
      'if(n==0)continue;observeProviderRead(n);bytesRead+=n;if(!timelineNormalizerActive)broadcastLive(b,n);consume(b,n);activatePendingTimelineNormalizer();',
      'if(n==0)continue;observeProviderRead(n);bytesRead+=n;maybeReleaseTimelineNormalizer();if(!timelineNormalizerActive)broadcastLive(b,n);consume(b,n);activatePendingTimelineNormalizer();',
      'release normalizer before fanout')
    ts=replace_member(ts,'ingestLoop',ingest)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,'class')

    watch=member(text,'cobraWatchTimeshiftReady')
    watch=once(watch,
      '    if(session.ready()){cobraSetTimeshiftUiState("READY",Math.round(session.windowDurationMs()/1000f)+"s");cobraUpdateLiveRewindControls();cobraUpdateTimeshiftSeek();if(preview)cobraRefreshProgrammeLabels();else cobraUpdatePlaybackLabels();InfinityCobraDiagnostics.record(this,"timeshift","rewind-ready-background",session.diagnostic());return;}',
      '''    if(session.ready()){
      ExoPlayer live=preview?mCobraPreviewPlayer:mPlayer;
      if(session.paceReserveEligible()&&live!=null&&live==mCobraTimeshiftProxyPlayer&&cobraActivateLocalTimeshift(live,channel,0L)){session.markPaceReserveActivation();InfinityCobraDiagnostics.record(this,"timeshift","pace-reserve-auto","under-rate live path moved to protected HLS reserve; "+session.diagnostic());return;}
      cobraSetTimeshiftUiState("READY",Math.round(session.windowDurationMs()/1000f)+"s");cobraUpdateLiveRewindControls();cobraUpdateTimeshiftSeek();if(preview)cobraRefreshProgrammeLabels();else cobraUpdatePlaybackLabels();InfinityCobraDiagnostics.record(this,"timeshift","rewind-ready-background",session.diagnostic());return;
    }''',
      'automatic pace reserve activation')
    text=replace_member(text,'cobraWatchTimeshiftReady',watch)

    health=member(text,'cobraAddSessionHealth')
    health=once(health,
      'root.put("timeshift_timeline_normalizer_rewritten_dts",mCobraTimeshiftSession.timelineNormalizerRewrittenDts());',
      'root.put("timeshift_timeline_normalizer_rewritten_dts",mCobraTimeshiftSession.timelineNormalizerRewrittenDts());root.put("timeshift_timeline_normalizer_released_after_ms",mCobraTimeshiftSession.timelineNormalizerReleasedAfterMs());root.put("timeshift_timeline_normalizer_releases",mCobraTimeshiftSession.timelineNormalizerReleases());root.put("timeshift_pace_reserve_eligible",mCobraTimeshiftSession.paceReserveEligible());root.put("timeshift_pace_reserve_activations",mCobraTimeshiftSession.paceReserveActivations());',
      'pace/release health')
    health=once(health,'root.put("stream_fingerprint_schema",6);','root.put("stream_fingerprint_schema",7);','schema 7')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in method_guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected playback owner changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h: raise RuntimeError('Protected class changed: '+n)

    required=['CobraProviderPacePolicy','MAX_PROVIDER_AGE_MS=500L','MAX_PROVIDER_GAP_MS=1000L','paceReserveEligible','pace-reserve-auto',
      'RECOVERY_MIN_RATE_PERMILLE=900L','RECOVERY_MAX_RATE_PERMILLE=1100L','maybeReleaseTimelineNormalizer','timelineNormalizerReleases',
      'timeshift_pace_reserve_activations','timeshift_timeline_normalizer_releases','root.put("stream_fingerprint_schema",7)',
      'timeshift_provider_remote_hash','timeshift_provider_dns_hashes','DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES',
      'last_live_before_navigation','cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart']
    for token in required:
        if token not in text: raise RuntimeError('2103192 contract missing: '+token)

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'stream_fingerprint_schema':7,'provider_pace_reserve':True,'pace_reserve_uses_existing_hls':True,'pace_reserve_auto_activation':True,
      'pace_min_rate_permille':450,'pace_max_rate_permille':800,'pace_max_provider_age_ms':500,'pace_max_provider_gap_ms':1000,'pace_requires_zero_empty_buckets':True,'pace_requires_clean_ts':True,
      'timeline_normalizer_recovery_release':True,'normalizer_recovery_rate_permille':[900,1100],
      'provider_route_fingerprint_preserved':True,'network_selection_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,
      'timeshift_ownership_changed':False,'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103192 provider pace reserve applied over exact passed 2103191; existing HLS reserve reused and normalizer recovery guarded')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
