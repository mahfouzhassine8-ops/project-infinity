#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103186
BASE_NAME='1.0.9-Cobra-Stream-Cadence-Fingerprint-RC1'
BASE_COMMIT='431d8d00e814a47d9ec4df972667c1c1f700413b'

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
    start=ms[0].start(); i=text.index('{',ms[0].end()); depth=0; quote=None; esc=line=block=False
    while i<len(text):
        c=text[i]; n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False; i+=1
        elif quote:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==quote: quote=None
        elif c=='/' and n=='/': line=True; i+=1
        elif c=='/' and n=='*': block=True; i+=1
        elif c in ('"',"'"): quote=c
        elif c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0: return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind); return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind); return text[:a]+new.rstrip()+'\n'+text[b:]

PARSER_POLICY=r'''
  static final class CobraTsParserPolicy {
    static final int TS_FLAGS=androidx.media3.extractor.ts.TsExtractor.FLAG_DETECT_ACCESS_UNITS;
    static boolean detectsAccessUnits(){return (TS_FLAGS&androidx.media3.extractor.ts.TsExtractor.FLAG_DETECT_ACCESS_UNITS)!=0;}
    static boolean allowsNonIdrKeyframes(){return (TS_FLAGS&androidx.media3.extractor.ts.TsExtractor.FLAG_ALLOW_NON_IDR_KEYFRAMES)!=0;}
  }
'''

def apply(source,receipt_path,out):
    source=Path(source); out=Path(out); receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103186 source receipt')
    path=source/ACT; before_b=path.read_bytes(); before=before_b.decode()
    expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103186 Activity preimage mismatch')
    text=before

    protected_methods=[
      'cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraWatchTimeshiftReady','cobraActivateLocalTimeshift',
      'cobraRewindLive','cobraGoLive','cobraStopLocalTimeshift','cobraDisposePlayer',
      'cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraStartProviderCatchup',
      'showCobraDiagnosticExport','cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport',
      'onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus',
      'cobraApplyDisplayPerformance','cobraTuneLastChannel'
    ]
    method_guards={n:sha(member(before,n)) for n in protected_methods}
    protected_classes=['CobraNetworkFamilyPolicy','CobraDiagnosticFreezePolicy','CobraStreamCadencePolicy','CobraLocalTimeshiftSession','CobraPlayerBinding','CobraSessionVitals']
    class_guards={n:sha(member(before,n,'class')) for n in protected_classes}

    marker='  static final class CobraStreamCadencePolicy {'
    if text.count(marker)!=1: raise RuntimeError('cadence policy marker drift')
    text=text.replace(marker,PARSER_POLICY.rstrip()+'\n\n'+marker,1)

    build=member(text,'buildPlayer')
    build=once(build,
      'DefaultDataSource.Factory data=new DefaultDataSource.Factory(this,http);',
      'DefaultDataSource.Factory data=new DefaultDataSource.Factory(this,http);androidx.media3.extractor.DefaultExtractorsFactory extractors=new androidx.media3.extractor.DefaultExtractorsFactory().setTsExtractorFlags(CobraTsParserPolicy.TS_FLAGS);',
      'extractor factory')
    build=once(build,
      'setMediaSourceFactory(new DefaultMediaSourceFactory(data))',
      'setMediaSourceFactory(new DefaultMediaSourceFactory(data,extractors))',
      'media source extractor wiring')
    text=replace_member(text,'buildPlayer',build)

    health=member(text,'cobraAddSessionHealth')
    health=once(health,
      'root.put("stream_fingerprint_schema",3);',
      'root.put("stream_fingerprint_schema",3);root.put("ts_access_unit_detection",CobraTsParserPolicy.detectsAccessUnits());root.put("ts_allow_non_idr_keyframes",CobraTsParserPolicy.allowsNonIdrKeyframes());root.put("ts_extractor_profile","DETECT_ACCESS_UNITS");',
      'parser diagnostic marker')
    text=replace_member(text,'cobraAddSessionHealth',health)

    for n,h in method_guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected playback/diagnostic method changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h: raise RuntimeError('Protected 2103186 class changed: '+n)

    build_after=member(text,'buildPlayer')
    required=[
      'CobraTsParserPolicy','FLAG_DETECT_ACCESS_UNITS','DefaultExtractorsFactory',
      'new DefaultMediaSourceFactory(data,extractors)','ts_access_unit_detection','ts_extractor_profile',
      'last_live_before_navigation','timeshift_provider_max_gap_ms','timeshift_proxy_max_gap_ms',
      'rebuffer_buffer_ahead_last_ms','CobraHappyEyeballs','IPv4 only','IPv6 only',
      'cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart'
    ]
    for token in required:
        if token not in text: raise RuntimeError('2103187 contract missing: '+token)
    if 'FLAG_ALLOW_NON_IDR_KEYFRAMES' in build_after:
        raise RuntimeError('2103187 must not enable non-IDR keyframes in player wiring')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    if 'mPlayer.prepare()' in watchdog or 'mPlayer.play()' in watchdog:
        raise RuntimeError('watchdog regained restart behavior')

    after=text.encode(); path.write_bytes(after)
    out.mkdir(parents=True,exist_ok=True); (out/'source-before').mkdir(exist_ok=True); (out/'source-before'/path.name).write_bytes(before_b)
    report={
      'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'ts_extractor_profile':'DETECT_ACCESS_UNITS','ts_detect_access_units':True,'ts_allow_non_idr_keyframes':False,
      'reason':'2103186 physical A/B showed continuous provider/proxy delivery while Problem Nicktoons repeatedly exhausted playable Media3 buffer',
      'playback_behavior_changed':True,'network_selection_changed':False,'timeshift_ownership_changed':False,
      'cadence_diagnostics_preserved':True,'frozen_live_snapshot_preserved':True,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False
    }
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103187 TS access-unit compatibility applied over exact passed 2103186')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True); p.add_argument('--receipt',type=Path,required=True); p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); apply(a.source,a.receipt,a.out)
