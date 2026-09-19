#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103184
BASE_NAME='1.0.9-Cobra-Stream-Network-Optimization-RC1'
BASE_COMMIT='fa77159f3a24cbb86d6ab34e24f7d3326139b0e0'

def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()

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

def insert_before_final(text,block):
    i=text.rfind('\n}')
    if i<0: raise RuntimeError('class final brace missing')
    return text[:i]+'\n'+block.rstrip()+'\n'+text[i:]

HELPERS=r'''
  private String mCobraLastLiveDiagnosticsSnapshot;
  private long mCobraLastLiveDiagnosticsCapturedAt=0L;
  private String mCobraLastLiveDiagnosticsReason="none";
  private boolean mCobraLastLiveDiagnosticsHadTimeshift=false;

  static final class CobraDiagnosticFreezePolicy {
    static final long MAX_FROZEN_AGE_MS=10L*60L*1000L;
    static boolean hasActiveEvidence(int players,boolean timeshift){return players>0||timeshift;}
    static boolean useFrozen(boolean currentActive,String frozen,long frozenAt,long now){
      return !currentActive&&frozen!=null&&!frozen.isEmpty()&&frozenAt>0L&&now>=frozenAt&&now-frozenAt<=MAX_FROZEN_AGE_MS;
    }
  }

  private String cobraDecorateDiagnosticSnapshot(String raw,String source,String reason,long capturedAt){
    if(raw==null||raw.isEmpty())return raw;
    try{
      JSONObject root=new JSONObject(raw);long now=System.currentTimeMillis();
      root.put("export_snapshot_source",source);
      root.put("export_requested_at_ms",now);
      root.put("live_snapshot_freeze_reason",reason==null?"none":reason);
      root.put("live_snapshot_frozen_at_ms",capturedAt);
      root.put("frozen_snapshot_age_ms",capturedAt<=0L?0L:Math.max(0L,now-capturedAt));
      return root.toString(2);
    }catch(Exception ignored){return raw;}
  }

  private void cobraRememberLiveDiagnostics(String reason){
    final boolean hasTimeshift=mCobraTimeshiftSession!=null;
    final int players=mCobraPlayerBindings.size();
    if(!CobraDiagnosticFreezePolicy.hasActiveEvidence(players,hasTimeshift))return;
    long now=System.currentTimeMillis();
    // Teardown can dispose the player immediately after stopping timeshift. Preserve
    // the richer timeshift snapshot instead of replacing it with a poorer follow-up.
    if(!hasTimeshift&&mCobraLastLiveDiagnosticsHadTimeshift&&now-mCobraLastLiveDiagnosticsCapturedAt<3000L)return;
    String snapshot=cobraFreshHealthSnapshot();
    if(snapshot==null||snapshot.isEmpty()||snapshot.startsWith("Snapshot unavailable"))return;
    try{
      JSONObject root=new JSONObject(snapshot);
      root.put("live_snapshot_frozen_before_navigation",true);
      root.put("live_snapshot_freeze_reason",reason==null?"unspecified":reason);
      root.put("live_snapshot_frozen_at_ms",now);
      root.put("live_snapshot_had_timeshift",hasTimeshift);
      root.put("live_snapshot_player_count",players);
      snapshot=root.toString(2);
    }catch(Exception ignored){}
    mCobraLastLiveDiagnosticsSnapshot=snapshot;
    mCobraLastLiveDiagnosticsCapturedAt=now;
    mCobraLastLiveDiagnosticsReason=reason==null?"unspecified":reason;
    mCobraLastLiveDiagnosticsHadTimeshift=hasTimeshift;
    InfinityCobraDiagnostics.record(this,"diagnostics","live-snapshot-frozen",
        "reason="+mCobraLastLiveDiagnosticsReason+"; players="+players+"; timeshift="+hasTimeshift);
  }

  private String cobraDiagnosticSnapshotForExport(){
    final boolean currentActive=CobraDiagnosticFreezePolicy.hasActiveEvidence(mCobraPlayerBindings.size(),mCobraTimeshiftSession!=null);
    final long now=System.currentTimeMillis();
    if(currentActive){
      String fresh=cobraFreshHealthSnapshot();
      mCobraLastLiveDiagnosticsSnapshot=fresh;
      mCobraLastLiveDiagnosticsCapturedAt=now;
      mCobraLastLiveDiagnosticsReason="export-live";
      mCobraLastLiveDiagnosticsHadTimeshift=mCobraTimeshiftSession!=null;
      return cobraDecorateDiagnosticSnapshot(fresh,"current_live","export-live",now);
    }
    if(CobraDiagnosticFreezePolicy.useFrozen(false,mCobraLastLiveDiagnosticsSnapshot,mCobraLastLiveDiagnosticsCapturedAt,now)){
      return cobraDecorateDiagnosticSnapshot(mCobraLastLiveDiagnosticsSnapshot,
          "last_live_before_navigation",mCobraLastLiveDiagnosticsReason,mCobraLastLiveDiagnosticsCapturedAt);
    }
    return cobraDecorateDiagnosticSnapshot(cobraFreshHealthSnapshot(),"current_inactive","no_recent_live_snapshot",now);
  }
'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103184 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode()
    expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103184 Activity preimage mismatch')
    text=before

    protected_methods=[
      'buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraRewindLive','cobraGoLive',
      'promoteCobraPreviewToFullscreen','cobraActivateLocalTimeshift','cobraWatchTimeshiftReady',
      'onStop','onPictureInPictureModeChanged','cobraHandleAudioFocus','cobraClaimAudioFocus',
      'cobraBuildPlayerChrome','cobraUpdateTimeshiftSeek','cobraApplyDisplayPerformance','cobraTuneLastChannel'
    ]
    guards={n:sha(member(before,n)) for n in protected_methods}
    protected_classes=['CobraNetworkFamilyPolicy','CobraLocalTimeshiftSession','CobraSessionVitals']
    class_guards={n:sha(member(before,n,'class')) for n in protected_classes}

    text=insert_before_final(text,HELPERS)

    health=member(text,'showCobraHealthCenter')
    brace=health.index('{')+1
    health=health[:brace]+'\n    cobraRememberLiveDiagnostics("health-center-open");'+health[brace:]
    text=replace_member(text,'showCobraHealthCenter',health)

    stop=member(text,'cobraStopLocalTimeshift')
    brace=stop.index('{')+1
    stop=stop[:brace]+'\n    cobraRememberLiveDiagnostics("timeshift-stop:"+(reason==null?"unknown":reason));'+stop[brace:]
    text=replace_member(text,'cobraStopLocalTimeshift',stop)

    dispose=member(text,'cobraDisposePlayer')
    brace=dispose.index('{')+1
    dispose=dispose[:brace]+'\n    cobraRememberLiveDiagnostics("player-dispose");'+dispose[brace:]
    text=replace_member(text,'cobraDisposePlayer',dispose)

    export=member(text,'showCobraDiagnosticExport')
    old='mCobraDiagnosticsSnapshot=cobraFreshHealthSnapshot();mCobraDiagnosticsPicker=true;'
    if export.count(old)!=1: raise RuntimeError('diagnostic export capture anchor drift')
    export=export.replace(old,'mCobraDiagnosticsSnapshot=cobraDiagnosticSnapshotForExport();mCobraDiagnosticsPicker=true;',1)
    text=replace_member(text,'showCobraDiagnosticExport',export)

    preview=member(text,'cobraCapturePreviewDiagnostics')
    old='mCobraDiagnosticsCaptureContext="mini_preview_direct";mCobraDiagnosticsSnapshot=cobraFreshHealthSnapshot();mCobraDiagnosticsCaptureContext="normal";mCobraDiagnosticsPicker=true;'
    if preview.count(old)!=1: raise RuntimeError('preview diagnostic capture anchor drift')
    preview=preview.replace(old,'mCobraDiagnosticsCaptureContext="mini_preview_direct";mCobraDiagnosticsSnapshot=cobraDiagnosticSnapshotForExport();mCobraDiagnosticsCaptureContext="normal";mCobraDiagnosticsPicker=true;',1)
    text=replace_member(text,'cobraCapturePreviewDiagnostics',preview)

    for n,h in guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected 2103184 playback contract changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h: raise RuntimeError('Protected 2103184 class changed: '+n)

    required=[
      'CobraDiagnosticFreezePolicy','MAX_FROZEN_AGE_MS=10L*60L*1000L',
      'cobraRememberLiveDiagnostics("health-center-open")',
      'cobraRememberLiveDiagnostics("timeshift-stop:"',
      'cobraRememberLiveDiagnostics("player-dispose")',
      'mCobraDiagnosticsSnapshot=cobraDiagnosticSnapshotForExport()',
      '"last_live_before_navigation"','"current_live"','"current_inactive"',
      '"live_snapshot_frozen_before_navigation"','"frozen_snapshot_age_ms"',
      'stream_fingerprint_schema', 'timeshift_pcr_backwards','timeshift_pts_backwards',
      'network_connected_family','provider-startup-failed','cobra_unified_live_timeline',
      'CobraCallAudioPolicy','buffer_observed_no_restart'
    ]
    for token in required:
        if token not in text: raise RuntimeError('2103185 contract missing: '+token)

    helpers=text[text.index('private String mCobraLastLiveDiagnosticsSnapshot'):]
    forbidden=['setMediaItem(','player.prepare()','mPlayer.prepare()','player.play()','mPlayer.play()','seekTo(']
    for token in forbidden:
        if token in helpers: raise RuntimeError('Diagnostics freeze helper must remain observation-only: '+token)

    after=text.encode();path.write_bytes(after)
    out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True)
    (out/'source-before'/path.name).write_bytes(before_b)
    report={
      'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,
      'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'frozen_live_snapshot':True,'frozen_live_snapshot_max_age_ms':600000,
      'freeze_before_health_navigation':True,'freeze_before_timeshift_teardown':True,'freeze_before_player_dispose':True,
      'export_prefers_current_live_then_recent_frozen_live':True,
      'diagnostic_capture_observation_only':True,
      'stream_fingerprint_schema_preserved':2,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False
    }
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103185 live diagnostics freeze applied over exact passed 2103184')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.out)
