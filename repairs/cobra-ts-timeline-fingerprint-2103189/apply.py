#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103188
BASE_NAME='1.0.9-Cobra-TS-Keyframe-Compatibility-RC1'
BASE_COMMIT='81390fd1e7f53c9cd55d33aaa25fbca26dd7a509'

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
    start=ms[0].start(); i=text.index('{',ms[0].end()); d=0; q=None; esc=line=block=False
    while i<len(text):
        c=text[i]; n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False; i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q: q=None
        elif c=='/' and n=='/': line=True; i+=1
        elif c=='/' and n=='*': block=True; i+=1
        elif c in ('"',"'"): q=c
        elif c=='{': d+=1
        elif c=='}':
            d-=1
            if d==0: return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind); return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind); return text[:a]+new.rstrip()+'\n'+text[b:]

POLICY=r'''
  static final class CobraTsTimelinePolicy {
    static final long PTS_MOD=1L<<33,PTS_HALF=PTS_MOD>>1;
    static long forwardDiff90k(long newer,long older){return (newer-older)&(PTS_MOD-1L);}
    static long signedDiff90k(long newer,long older){long d=forwardDiff90k(newer,older);return d>PTS_HALF?d-PTS_MOD:d;}
    static long ticksToMs(long ticks){return ticks<0L?-1L:(ticks*1000L)/90000L;}
    static boolean intraSliceType(int sliceType){int t=Math.floorMod(sliceType,5);return t==2||t==4;}
    static long ratePermille(long first90k,long max90k,long firstElapsed,long lastElapsed){
      if(first90k<0L||max90k<0L||firstElapsed<0L||lastElapsed<=firstElapsed)return -1L;
      long wall=Math.max(1L,lastElapsed-firstElapsed),media=ticksToMs(forwardDiff90k(max90k,first90k));
      return (media*1000L)/wall;
    }
  }
'''

OBSERVE=r'''    private void observeContinuity(byte[] data,int offset){
      tsPackets++;int pid=((data[offset+1]&0x1f)<<8)|(data[offset+2]&255),afc=(data[offset+3]>>4)&3,cc=data[offset+3]&15;boolean payload=afc==1||afc==3,pusi=(data[offset+1]&0x40)!=0,disc=false;int adaptationLength=0;
      if((afc==2||afc==3)&&offset+5<data.length){adaptationLength=data[offset+4]&255;if(adaptationLength>0&&offset+5<data.length)disc=(data[offset+5]&0x80)!=0;}
      if(disc){continuity[pid]=-1;lastPcr90k[pid]=-1L;lastPts90k[pid]=-1L;}
      if(payload&&pid!=0x1fff){int prev=continuity[pid];if(prev>=0&&cc!=prev&&cc!=((prev+1)&15))tsContinuityErrors++;continuity[pid]=cc;}
      if((afc==2||afc==3)&&adaptationLength>=7&&offset+11<offset+PACKET&&(data[offset+5]&0x10)!=0){long pcr=((long)(data[offset+6]&255)<<25)|((long)(data[offset+7]&255)<<17)|((long)(data[offset+8]&255)<<9)|((long)(data[offset+9]&255)<<1)|((data[offset+10]&0x80)>>7);pcrSamples++;long prev=lastPcr90k[pid];if(prev>=0){long gap=(pcr-prev)&0x1ffffffffL;if(gap>0x100000000L)pcrBackwards++;else{maxPcrGap90k=Math.max(maxPcrGap90k,gap);if(gap>450000L)pcrLargeJumps++;}}lastPcr90k[pid]=pcr;}
      int payloadOffset=offset+4;if(afc==3)payloadOffset=offset+5+adaptationLength;int packetEnd=Math.min(data.length,offset+PACKET);
      if(payload&&payloadOffset<packetEnd)observeProgramMap(data,offset,pid,payloadOffset,packetEnd,pusi);
      int role=pid==timelineVideoPid?1:pid==timelineAudioPid?2:0;
      if(payload&&pusi&&payloadOffset+14<=packetEnd&&(data[payloadOffset]&255)==0&&(data[payloadOffset+1]&255)==0&&(data[payloadOffset+2]&255)==1){
        int streamId=data[payloadOffset+3]&255;if(role==0){if((streamId&0xf0)==0xe0){role=1;if(timelineVideoPid<0)timelineVideoPid=pid;}else if((streamId&0xe0)==0xc0){role=2;if(timelineAudioPid<0)timelineAudioPid=pid;}}
        int ptsFlags=(data[payloadOffset+7]>>6)&3;long pts=-1L,dts=-1L;if(ptsFlags>=2&&payloadOffset+14<=packetEnd)pts=decodePts90k(data,payloadOffset+9);if(ptsFlags==3&&payloadOffset+19<=packetEnd)dts=decodePts90k(data,payloadOffset+14);
        if(pts>=0L){ptsSamples++;long prev=lastPts90k[pid];if(prev>=0){long gap=(pts-prev)&0x1ffffffffL;if(gap>0x100000000L)ptsBackwards++;else{maxPtsGap90k=Math.max(maxPtsGap90k,gap);if(gap>180000L)ptsLargeJumps++;}}lastPts90k[pid]=pts;}
        observeRoleTimestamps(role,pts,dts,android.os.SystemClock.elapsedRealtime());
      }
      if(payload&&role==1&&payloadOffset<packetEnd)observeVideoNals(data,payloadOffset,packetEnd);
    }'''

HELPERS=r'''    private void observeProgramMap(byte[] data,int packetOffset,int pid,int payloadOffset,int packetEnd,boolean pusi){
      if(!pusi||payloadOffset>=packetEnd)return;int p=payloadOffset,pointer=data[p]&255;p+=1+pointer;if(p+3>packetEnd)return;int table=data[p]&255,section=((data[p+1]&15)<<8)|(data[p+2]&255),sectionEnd=Math.min(packetEnd,p+3+section),loopEnd=Math.max(p,sectionEnd-4);
      if(pid==0&&table==0){timelinePatSections++;for(int q=p+8;q+4<=loopEnd;q+=4){int program=((data[q]&255)<<8)|(data[q+1]&255);if(program!=0){timelinePmtPid=((data[q+2]&31)<<8)|(data[q+3]&255);break;}}}
      else if(pid==timelinePmtPid&&table==2&&p+12<=packetEnd){timelinePmtSections++;int info=((data[p+10]&15)<<8)|(data[p+11]&255);for(int q=p+12+info;q+5<=loopEnd;){int type=data[q]&255,es=((data[q+1]&31)<<8)|(data[q+2]&255),len=((data[q+3]&15)<<8)|(data[q+4]&255);if(timelineVideoPid<0&&(type==0x1b||type==0x24)){timelineVideoPid=es;timelineVideoStreamType=type;}if(timelineAudioPid<0&&(type==0x0f||type==0x11||type==0x03||type==0x04)){timelineAudioPid=es;timelineAudioStreamType=type;}q+=5+len;}}
    }
    private void observeRoleTimestamps(int role,long pts,long dts,long now){
      if(role==1){videoPesStarts++;if(pts>=0L){videoPtsRoleSamples++;if(firstVideoPts90k<0L){firstVideoPts90k=pts;maxVideoPts90k=pts;firstVideoPtsElapsed=now;}else{if(CobraTsTimelinePolicy.signedDiff90k(pts,lastVideoPtsRole90k)<0L)videoPtsRoleBackwards++;if(CobraTsTimelinePolicy.signedDiff90k(pts,maxVideoPts90k)>0L)maxVideoPts90k=pts;}lastVideoPtsRole90k=pts;lastVideoPtsElapsed=now;}if(dts>=0L){videoDtsRoleSamples++;if(firstVideoDts90k<0L){firstVideoDts90k=dts;maxVideoDts90k=dts;firstVideoDtsElapsed=now;}else{if(CobraTsTimelinePolicy.signedDiff90k(dts,lastVideoDts90k)<0L)videoDtsRoleBackwards++;if(CobraTsTimelinePolicy.signedDiff90k(dts,maxVideoDts90k)>0L)maxVideoDts90k=dts;}lastVideoDts90k=dts;lastVideoDtsElapsed=now;}}
      else if(role==2){audioPesStarts++;if(pts>=0L){audioPtsRoleSamples++;if(firstAudioPts90k<0L){firstAudioPts90k=pts;maxAudioPts90k=pts;firstAudioPtsElapsed=now;}else{if(CobraTsTimelinePolicy.signedDiff90k(pts,lastAudioPtsRole90k)<0L)audioPtsRoleBackwards++;if(CobraTsTimelinePolicy.signedDiff90k(pts,maxAudioPts90k)>0L)maxAudioPts90k=pts;}lastAudioPtsRole90k=pts;lastAudioPtsElapsed=now;}}
      if(lastVideoPtsRole90k>=0L&&lastAudioPtsRole90k>=0L){long drift=CobraTsTimelinePolicy.ticksToMs(Math.abs(CobraTsTimelinePolicy.signedDiff90k(lastVideoPtsRole90k,lastAudioPtsRole90k)));latestAvDriftMs=drift;maxAbsAvDriftMs=Math.max(maxAbsAvDriftMs,drift);}
    }
    private static int readUe(byte[] b,int[] bit,int bits){int zeros=0;while(bit[0]<bits){int v=(b[bit[0]>>3]>>(7-(bit[0]&7)))&1;bit[0]++;if(v!=0)break;if(++zeros>30)return -1;}int suffix=0;for(int i=0;i<zeros;i++){if(bit[0]>=bits)return -1;suffix=(suffix<<1)|((b[bit[0]>>3]>>(7-(bit[0]&7)))&1);bit[0]++;}return ((1<<zeros)-1)+suffix;}
    private static int firstSliceType(byte[] data,int start,int end){byte[] rbsp=new byte[Math.min(32,Math.max(0,end-start))];int n=0,zeros=0;for(int i=start;i<end&&n<rbsp.length;i++){int v=data[i]&255;if(zeros>=2&&v==3){zeros=0;continue;}rbsp[n++]=(byte)v;if(v==0)zeros++;else zeros=0;}if(n==0)return -1;int[] bit={0};int first=readUe(rbsp,bit,n*8);int type=readUe(rbsp,bit,n*8);return first==0?type:-1;}
    private void observeVideoNals(byte[] data,int start,int end){for(int i=start;i+4<end;i++){int n=-1;if((data[i]&255)==0&&(data[i+1]&255)==0&&(data[i+2]&255)==1)n=i+3;else if(i+4<end&&(data[i]&255)==0&&(data[i+1]&255)==0&&(data[i+2]&255)==0&&(data[i+3]&255)==1)n=i+4;if(n<0||n>=end)continue;int type=data[n]&31;if(type==5){videoIdrNals++;markIntra(true);}else if(type==1){videoNonIdrSliceNals++;int slice=firstSliceType(data,n+1,end);if(slice>=0&&CobraTsTimelinePolicy.intraSliceType(slice)){videoNonIdrIntraFrames++;markIntra(false);}}else if(type==9)videoAudNals++;else if(type==7)videoSpsNals++;else if(type==8)videoPpsNals++;i=n;}}
    private void markIntra(boolean idr){long now=android.os.SystemClock.elapsedRealtime(),pts=lastVideoPtsRole90k;if(idr){if(lastIdrElapsed>0L)idrWallIntervalMaxMs=Math.max(idrWallIntervalMaxMs,now-lastIdrElapsed);lastIdrElapsed=now;if(pts>=0L&&lastIdrPts90k>=0L){long d=CobraTsTimelinePolicy.signedDiff90k(pts,lastIdrPts90k);if(d>0L){idrPtsIntervalSamples++;idrPtsIntervalTotal90k+=d;idrPtsIntervalMax90k=Math.max(idrPtsIntervalMax90k,d);}}if(pts>=0L)lastIdrPts90k=pts;}if(lastIntraElapsed>0L)intraWallIntervalMaxMs=Math.max(intraWallIntervalMaxMs,now-lastIntraElapsed);lastIntraElapsed=now;if(pts>=0L&&lastIntraPts90k>=0L){long d=CobraTsTimelinePolicy.signedDiff90k(pts,lastIntraPts90k);if(d>0L){intraPtsIntervalSamples++;intraPtsIntervalTotal90k+=d;intraPtsIntervalMax90k=Math.max(intraPtsIntervalMax90k,d);}}if(pts>=0L)lastIntraPts90k=pts;}
    int timelinePmtPid(){return timelinePmtPid;}int timelineVideoPid(){return timelineVideoPid;}int timelineAudioPid(){return timelineAudioPid;}int timelineVideoStreamType(){return timelineVideoStreamType;}int timelineAudioStreamType(){return timelineAudioStreamType;}long timelinePatSections(){return timelinePatSections;}long timelinePmtSections(){return timelinePmtSections;}
    long videoPesStarts(){return videoPesStarts;}long audioPesStarts(){return audioPesStarts;}long videoPtsRoleSamples(){return videoPtsRoleSamples;}long videoDtsRoleSamples(){return videoDtsRoleSamples;}long audioPtsRoleSamples(){return audioPtsRoleSamples;}long videoPtsRoleBackwards(){return videoPtsRoleBackwards;}long videoDtsRoleBackwards(){return videoDtsRoleBackwards;}long audioPtsRoleBackwards(){return audioPtsRoleBackwards;}
    long videoPtsSpanMs(){return firstVideoPts90k<0L||maxVideoPts90k<0L?-1L:CobraTsTimelinePolicy.ticksToMs(CobraTsTimelinePolicy.forwardDiff90k(maxVideoPts90k,firstVideoPts90k));}long videoDtsSpanMs(){return firstVideoDts90k<0L||maxVideoDts90k<0L?-1L:CobraTsTimelinePolicy.ticksToMs(CobraTsTimelinePolicy.forwardDiff90k(maxVideoDts90k,firstVideoDts90k));}long audioPtsSpanMs(){return firstAudioPts90k<0L||maxAudioPts90k<0L?-1L:CobraTsTimelinePolicy.ticksToMs(CobraTsTimelinePolicy.forwardDiff90k(maxAudioPts90k,firstAudioPts90k));}
    long videoPtsWallSpanMs(){return firstVideoPtsElapsed<0L||lastVideoPtsElapsed<0L?-1L:lastVideoPtsElapsed-firstVideoPtsElapsed;}long videoDtsWallSpanMs(){return firstVideoDtsElapsed<0L||lastVideoDtsElapsed<0L?-1L:lastVideoDtsElapsed-firstVideoDtsElapsed;}long audioPtsWallSpanMs(){return firstAudioPtsElapsed<0L||lastAudioPtsElapsed<0L?-1L:lastAudioPtsElapsed-firstAudioPtsElapsed;}
    long videoPtsRatePermille(){return CobraTsTimelinePolicy.ratePermille(firstVideoPts90k,maxVideoPts90k,firstVideoPtsElapsed,lastVideoPtsElapsed);}long videoDtsRatePermille(){return CobraTsTimelinePolicy.ratePermille(firstVideoDts90k,maxVideoDts90k,firstVideoDtsElapsed,lastVideoDtsElapsed);}long audioPtsRatePermille(){return CobraTsTimelinePolicy.ratePermille(firstAudioPts90k,maxAudioPts90k,firstAudioPtsElapsed,lastAudioPtsElapsed);}
    long videoPtsAgeMs(){return lastVideoPtsElapsed<0L?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-lastVideoPtsElapsed);}long videoDtsAgeMs(){return lastVideoDtsElapsed<0L?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-lastVideoDtsElapsed);}long audioPtsAgeMs(){return lastAudioPtsElapsed<0L?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-lastAudioPtsElapsed);}long latestAvDriftMs(){return latestAvDriftMs;}long maxAbsAvDriftMs(){return maxAbsAvDriftMs;}
    long videoIdrNals(){return videoIdrNals;}long videoNonIdrSliceNals(){return videoNonIdrSliceNals;}long videoNonIdrIntraFrames(){return videoNonIdrIntraFrames;}long videoAudNals(){return videoAudNals;}long videoSpsNals(){return videoSpsNals;}long videoPpsNals(){return videoPpsNals;}
    long idrPtsIntervalAvgMs(){return idrPtsIntervalSamples<=0L?-1L:CobraTsTimelinePolicy.ticksToMs(idrPtsIntervalTotal90k/idrPtsIntervalSamples);}long idrPtsIntervalMaxMs(){return CobraTsTimelinePolicy.ticksToMs(idrPtsIntervalMax90k);}long intraPtsIntervalAvgMs(){return intraPtsIntervalSamples<=0L?-1L:CobraTsTimelinePolicy.ticksToMs(intraPtsIntervalTotal90k/intraPtsIntervalSamples);}long intraPtsIntervalMaxMs(){return CobraTsTimelinePolicy.ticksToMs(intraPtsIntervalMax90k);}long idrWallIntervalMaxMs(){return idrWallIntervalMaxMs;}long intraWallIntervalMaxMs(){return intraWallIntervalMaxMs;}long lastIntraAgeMs(){return lastIntraElapsed<0L?-1L:Math.max(0L,android.os.SystemClock.elapsedRealtime()-lastIntraElapsed);}
'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME: raise RuntimeError('Expected exact passed 2103188 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode();expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103188 Activity preimage mismatch')
    text=before

    protected_methods=['buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraWatchTimeshiftReady','cobraActivateLocalTimeshift','cobraRewindLive','cobraGoLive','cobraStopLocalTimeshift','cobraDisposePlayer','cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraStartProviderCatchup','showCobraDiagnosticExport','cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport','onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus','cobraApplyDisplayPerformance','cobraTuneLastChannel']
    method_guards={n:sha(member(before,n)) for n in protected_methods}
    class_guards={n:sha(member(before,n,'class')) for n in ['CobraNetworkFamilyPolicy','CobraDiagnosticFreezePolicy','CobraStreamCadencePolicy','CobraTsParserPolicy']}

    marker='  static final class CobraTsParserPolicy {'
    if text.count(marker)!=1: raise RuntimeError('parser policy marker drift')
    text=text.replace(marker,POLICY.rstrip()+'\n\n'+marker,1)

    ts=member(text,'CobraLocalTimeshiftSession',kind='class')
    ts=once(ts,'    private volatile long pcrSamples=0,pcrBackwards=0,pcrLargeJumps=0,maxPcrGap90k=0,ptsSamples=0,ptsBackwards=0,ptsLargeJumps=0,maxPtsGap90k=0;',
'''    private volatile long pcrSamples=0,pcrBackwards=0,pcrLargeJumps=0,maxPcrGap90k=0,ptsSamples=0,ptsBackwards=0,ptsLargeJumps=0,maxPtsGap90k=0;
    private volatile int timelinePmtPid=-1,timelineVideoPid=-1,timelineAudioPid=-1,timelineVideoStreamType=-1,timelineAudioStreamType=-1;
    private volatile long timelinePatSections=0,timelinePmtSections=0,videoPesStarts=0,audioPesStarts=0;
    private volatile long videoPtsRoleSamples=0,videoDtsRoleSamples=0,audioPtsRoleSamples=0,videoPtsRoleBackwards=0,videoDtsRoleBackwards=0,audioPtsRoleBackwards=0;
    private volatile long firstVideoPts90k=-1,maxVideoPts90k=-1,lastVideoPtsRole90k=-1,firstVideoPtsElapsed=-1,lastVideoPtsElapsed=-1;
    private volatile long firstVideoDts90k=-1,maxVideoDts90k=-1,lastVideoDts90k=-1,firstVideoDtsElapsed=-1,lastVideoDtsElapsed=-1;
    private volatile long firstAudioPts90k=-1,maxAudioPts90k=-1,lastAudioPtsRole90k=-1,firstAudioPtsElapsed=-1,lastAudioPtsElapsed=-1;
    private volatile long latestAvDriftMs=-1,maxAbsAvDriftMs=0;
    private volatile long videoIdrNals=0,videoNonIdrSliceNals=0,videoNonIdrIntraFrames=0,videoAudNals=0,videoSpsNals=0,videoPpsNals=0;
    private volatile long lastIdrElapsed=-1,lastIntraElapsed=-1,lastIdrPts90k=-1,lastIntraPts90k=-1,idrPtsIntervalSamples=0,idrPtsIntervalTotal90k=0,idrPtsIntervalMax90k=0,intraPtsIntervalSamples=0,intraPtsIntervalTotal90k=0,intraPtsIntervalMax90k=0,idrWallIntervalMaxMs=0,intraWallIntervalMaxMs=0;''','timeline fields')

    obs=member(ts,'observeContinuity');ts=replace_member(ts,'observeContinuity',OBSERVE)
    anchor='    private void serveLive(java.net.Socket s,boolean head)throws Exception{'
    if ts.count(anchor)!=1: raise RuntimeError('serveLive helper anchor drift')
    ts=ts.replace(anchor,HELPERS.rstrip()+'\n\n'+anchor,1)
    text=replace_member(text,'CobraLocalTimeshiftSession',ts,kind='class')

    vit=member(text,'CobraSessionVitals',kind='class')
    vit=once(vit,'    long providerAgeAtRebufferLastMs=-1,providerAgeAtRebufferTotalMs=0,providerAgeAtRebufferMaxMs=0;\n    long proxyAgeAtRebufferLastMs=-1,proxyAgeAtRebufferTotalMs=0,proxyAgeAtRebufferMaxMs=0;int cadenceRebufferSamples=0,providerAgeRebufferSamples=0,proxyAgeRebufferSamples=0;',
'''    long providerAgeAtRebufferLastMs=-1,providerAgeAtRebufferTotalMs=0,providerAgeAtRebufferMaxMs=0;
    long proxyAgeAtRebufferLastMs=-1,proxyAgeAtRebufferTotalMs=0,proxyAgeAtRebufferMaxMs=0;int cadenceRebufferSamples=0,providerAgeRebufferSamples=0,proxyAgeRebufferSamples=0;
    long videoPtsAgeAtRebufferLastMs=-1,videoDtsAgeAtRebufferLastMs=-1,audioPtsAgeAtRebufferLastMs=-1,avDriftAtRebufferLastMs=-1,intraAgeAtRebufferLastMs=-1;''','rebuffer timeline fields')
    text=replace_member(text,'CobraSessionVitals',vit,kind='class')

    binding=member(text,'CobraPlayerBinding',kind='class')
    old='if(player==mCobraTimeshiftProxyPlayer&&mCobraTimeshiftSession!=null){long providerAge=mCobraTimeshiftSession.providerReadAgeMs(),proxyAge=mCobraTimeshiftSession.proxyWriteAgeMs();vitals.providerAgeAtRebufferLastMs=providerAge;vitals.proxyAgeAtRebufferLastMs=proxyAge;if(providerAge>=0L){vitals.providerAgeAtRebufferTotalMs+=providerAge;vitals.providerAgeAtRebufferMaxMs=Math.max(vitals.providerAgeAtRebufferMaxMs,providerAge);vitals.providerAgeRebufferSamples++;}if(proxyAge>=0L){vitals.proxyAgeAtRebufferTotalMs+=proxyAge;vitals.proxyAgeAtRebufferMaxMs=Math.max(vitals.proxyAgeAtRebufferMaxMs,proxyAge);vitals.proxyAgeRebufferSamples++;}vitals.cadenceRebufferSamples++;}'
    new='if(player==mCobraTimeshiftProxyPlayer&&mCobraTimeshiftSession!=null){long providerAge=mCobraTimeshiftSession.providerReadAgeMs(),proxyAge=mCobraTimeshiftSession.proxyWriteAgeMs();vitals.providerAgeAtRebufferLastMs=providerAge;vitals.proxyAgeAtRebufferLastMs=proxyAge;if(providerAge>=0L){vitals.providerAgeAtRebufferTotalMs+=providerAge;vitals.providerAgeAtRebufferMaxMs=Math.max(vitals.providerAgeAtRebufferMaxMs,providerAge);vitals.providerAgeRebufferSamples++;}if(proxyAge>=0L){vitals.proxyAgeAtRebufferTotalMs+=proxyAge;vitals.proxyAgeAtRebufferMaxMs=Math.max(vitals.proxyAgeAtRebufferMaxMs,proxyAge);vitals.proxyAgeRebufferSamples++;}vitals.videoPtsAgeAtRebufferLastMs=mCobraTimeshiftSession.videoPtsAgeMs();vitals.videoDtsAgeAtRebufferLastMs=mCobraTimeshiftSession.videoDtsAgeMs();vitals.audioPtsAgeAtRebufferLastMs=mCobraTimeshiftSession.audioPtsAgeMs();vitals.avDriftAtRebufferLastMs=mCobraTimeshiftSession.latestAvDriftMs();vitals.intraAgeAtRebufferLastMs=mCobraTimeshiftSession.lastIntraAgeMs();vitals.cadenceRebufferSamples++;}'
    binding=once(binding,old,new,'rebuffer timeline correlation');text=replace_member(text,'CobraPlayerBinding',binding,kind='class')

    health=member(text,'cobraAddSessionHealth')
    health=once(health,'row.put("proxy_age_at_rebuffer_max_ms",s.proxyAgeAtRebufferMaxMs);',
      'row.put("proxy_age_at_rebuffer_max_ms",s.proxyAgeAtRebufferMaxMs);row.put("video_pts_age_at_rebuffer_last_ms",s.videoPtsAgeAtRebufferLastMs);row.put("video_dts_age_at_rebuffer_last_ms",s.videoDtsAgeAtRebufferLastMs);row.put("audio_pts_age_at_rebuffer_last_ms",s.audioPtsAgeAtRebufferLastMs);row.put("av_drift_at_rebuffer_last_ms",s.avDriftAtRebufferLastMs);row.put("intra_age_at_rebuffer_last_ms",s.intraAgeAtRebufferLastMs);',
      'rebuffer timeline health')
    health=once(health,'root.put("timeshift_proxy_500ms_bytes_max",mCobraTimeshiftSession.proxyMaxBucketBytes());',
'''root.put("timeshift_proxy_500ms_bytes_max",mCobraTimeshiftSession.proxyMaxBucketBytes());
root.put("timeshift_timeline_pmt_pid",mCobraTimeshiftSession.timelinePmtPid());root.put("timeshift_timeline_video_pid",mCobraTimeshiftSession.timelineVideoPid());root.put("timeshift_timeline_audio_pid",mCobraTimeshiftSession.timelineAudioPid());root.put("timeshift_timeline_video_stream_type",mCobraTimeshiftSession.timelineVideoStreamType());root.put("timeshift_timeline_audio_stream_type",mCobraTimeshiftSession.timelineAudioStreamType());root.put("timeshift_timeline_pat_sections",mCobraTimeshiftSession.timelinePatSections());root.put("timeshift_timeline_pmt_sections",mCobraTimeshiftSession.timelinePmtSections());root.put("timeshift_video_pes_starts",mCobraTimeshiftSession.videoPesStarts());root.put("timeshift_audio_pes_starts",mCobraTimeshiftSession.audioPesStarts());
root.put("timeshift_video_pts_samples",mCobraTimeshiftSession.videoPtsRoleSamples());root.put("timeshift_video_pts_backwards",mCobraTimeshiftSession.videoPtsRoleBackwards());root.put("timeshift_video_pts_span_ms",mCobraTimeshiftSession.videoPtsSpanMs());root.put("timeshift_video_pts_wall_span_ms",mCobraTimeshiftSession.videoPtsWallSpanMs());root.put("timeshift_video_pts_rate_permille",mCobraTimeshiftSession.videoPtsRatePermille());root.put("timeshift_video_pts_age_ms",mCobraTimeshiftSession.videoPtsAgeMs());
root.put("timeshift_video_dts_samples",mCobraTimeshiftSession.videoDtsRoleSamples());root.put("timeshift_video_dts_backwards",mCobraTimeshiftSession.videoDtsRoleBackwards());root.put("timeshift_video_dts_span_ms",mCobraTimeshiftSession.videoDtsSpanMs());root.put("timeshift_video_dts_wall_span_ms",mCobraTimeshiftSession.videoDtsWallSpanMs());root.put("timeshift_video_dts_rate_permille",mCobraTimeshiftSession.videoDtsRatePermille());root.put("timeshift_video_dts_age_ms",mCobraTimeshiftSession.videoDtsAgeMs());
root.put("timeshift_audio_pts_samples",mCobraTimeshiftSession.audioPtsRoleSamples());root.put("timeshift_audio_pts_backwards",mCobraTimeshiftSession.audioPtsRoleBackwards());root.put("timeshift_audio_pts_span_ms",mCobraTimeshiftSession.audioPtsSpanMs());root.put("timeshift_audio_pts_wall_span_ms",mCobraTimeshiftSession.audioPtsWallSpanMs());root.put("timeshift_audio_pts_rate_permille",mCobraTimeshiftSession.audioPtsRatePermille());root.put("timeshift_audio_pts_age_ms",mCobraTimeshiftSession.audioPtsAgeMs());root.put("timeshift_av_drift_latest_ms",mCobraTimeshiftSession.latestAvDriftMs());root.put("timeshift_av_drift_max_abs_ms",mCobraTimeshiftSession.maxAbsAvDriftMs());
root.put("timeshift_video_idr_nals",mCobraTimeshiftSession.videoIdrNals());root.put("timeshift_video_non_idr_slice_nals",mCobraTimeshiftSession.videoNonIdrSliceNals());root.put("timeshift_video_non_idr_intra_frames",mCobraTimeshiftSession.videoNonIdrIntraFrames());root.put("timeshift_video_aud_nals",mCobraTimeshiftSession.videoAudNals());root.put("timeshift_video_sps_nals",mCobraTimeshiftSession.videoSpsNals());root.put("timeshift_video_pps_nals",mCobraTimeshiftSession.videoPpsNals());root.put("timeshift_idr_interval_avg_ms",mCobraTimeshiftSession.idrPtsIntervalAvgMs());root.put("timeshift_idr_interval_max_ms",mCobraTimeshiftSession.idrPtsIntervalMaxMs());root.put("timeshift_intra_interval_avg_ms",mCobraTimeshiftSession.intraPtsIntervalAvgMs());root.put("timeshift_intra_interval_max_ms",mCobraTimeshiftSession.intraPtsIntervalMaxMs());root.put("timeshift_idr_wall_interval_max_ms",mCobraTimeshiftSession.idrWallIntervalMaxMs());root.put("timeshift_intra_wall_interval_max_ms",mCobraTimeshiftSession.intraWallIntervalMaxMs());root.put("timeshift_last_intra_age_ms",mCobraTimeshiftSession.lastIntraAgeMs());''',
      'timeline root health')
    health=once(health,'root.put("stream_fingerprint_schema",3);','root.put("stream_fingerprint_schema",4);','schema 4')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in method_guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected playback/diagnostic owner changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h: raise RuntimeError('Protected class changed: '+n)

    required=['CobraTsTimelinePolicy','signedDiff90k','intraSliceType','observeProgramMap','observeRoleTimestamps','observeVideoNals','firstSliceType','timeshift_video_dts_rate_permille','timeshift_video_non_idr_intra_frames','timeshift_av_drift_max_abs_ms','video_pts_age_at_rebuffer_last_ms','root.put("stream_fingerprint_schema",4)','DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES','timeshift_provider_max_gap_ms','timeshift_proxy_max_gap_ms','last_live_before_navigation','cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart']
    for token in required:
        if token not in text: raise RuntimeError('2103189 contract missing: '+token)

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'stream_fingerprint_schema':4,'timeline_probe_only':True,'pat_pmt_probe':True,'video_pts_probe':True,'video_dts_probe':True,'audio_pts_probe':True,'av_drift_probe':True,'h264_nal_probe':True,'intra_cadence_probe':True,'rebuffer_timeline_correlation':True,
      'playback_behavior_changed':False,'network_selection_changed':False,'timeshift_ownership_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False}
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103189 TS timeline fingerprint applied over exact passed 2103188 without playback changes')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
