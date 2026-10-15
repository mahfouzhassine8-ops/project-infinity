#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')

def require(v,msg):
    if not v: raise RuntimeError(msg)

def block(text,name,kind='method'):
    if kind=='method':
        pat=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:
        pat=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    ms=list(pat.finditer(text));require(len(ms)==1,f'{name} cardinality={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=comment=False
    while i<len(text):
      c=text[i];n=text[i+1] if i+1<len(text) else ''
      if line:
        if c=='\n':line=False
      elif comment:
        if c=='*' and n=='/':comment=False;i+=1
      elif q:
        if esc:esc=False
        elif c=='\\':esc=True
        elif c==q:q=None
      elif c=='/' and n=='/':line=True;i+=1
      elif c=='/' and n=='*':comment=True;i+=1
      elif c in ('"',"'"):q=c
      elif c=='{':d+=1
      elif c=='}':
        d-=1
        if d==0:return text[start:i+1]
      i+=1
    raise RuntimeError('unclosed '+name)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/ACT).read_text();patch=json.loads(a.patch.read_text())
    health=block(text,'showCobraHealthCenter')
    stop=block(text,'cobraStopLocalTimeshift')
    dispose=block(text,'cobraDisposePlayer')
    export=block(text,'showCobraDiagnosticExport')
    preview=block(text,'cobraCapturePreviewDiagnostics')
    network=block(text,'CobraNetworkFamilyPolicy','class')
    timeshift=block(text,'CobraLocalTimeshiftSession','class')
    checks={
      'exact_2103184_parent':patch.get('base_build')==2103184 and patch.get('base_commit')=='fa77159f3a24cbb86d6ab34e24f7d3326139b0e0',
      'freeze_policy_present':'CobraDiagnosticFreezePolicy' in text and 'MAX_FROZEN_AGE_MS=10L*60L*1000L' in text,
      'health_center_freezes_before_navigation':'cobraRememberLiveDiagnostics("health-center-open")' in health,
      'timeshift_freezes_before_teardown':'cobraRememberLiveDiagnostics("timeshift-stop:"' in stop and stop.index('cobraRememberLiveDiagnostics')<stop.index('mCobraTimeshiftSession=null'),
      'player_freezes_before_dispose':'cobraRememberLiveDiagnostics("player-dispose")' in dispose,
      'export_uses_frozen_aware_capture':'mCobraDiagnosticsSnapshot=cobraDiagnosticSnapshotForExport()' in export,
      'preview_export_uses_frozen_aware_capture':'mCobraDiagnosticsSnapshot=cobraDiagnosticSnapshotForExport()' in preview,
      'current_live_preferred':'"current_live"' in text and 'if(currentActive)' in text,
      'recent_frozen_live_fallback':'"last_live_before_navigation"' in text and 'useFrozen(false' in text,
      'inactive_fallback_explicit':'"current_inactive"' in text,
      'freeze_is_timestamped':all(x in text for x in ('live_snapshot_frozen_at_ms','frozen_snapshot_age_ms','export_requested_at_ms')),
      'freeze_reason_exported':'live_snapshot_freeze_reason' in text,
      'richer_timeshift_snapshot_protected':'mCobraLastLiveDiagnosticsHadTimeshift' in text and 'now-mCobraLastLiveDiagnosticsCapturedAt<3000L' in text,
      'fingerprint_v2_preserved':'root.put("stream_fingerprint_schema",2)' in text,
      'timing_fingerprint_preserved':'timeshift_pcr_backwards' in text and 'timeshift_pts_backwards' in text,
      'smart_network_preserved':'CobraHappyEyeballs' in network and 'HAPPY_DELAY_MS=250L' in network and 'IPv4 only' in text and 'IPv6 only' in text,
      'seamless_rewind_preserved':'/live.ts' in timeshift and 'liveWriterLoop' in timeshift and 'rewind-ready-background' in text,
      'watchdog_observation_only':'buffer_observed_no_restart' in text,
      'blue_timeline_preserved':'cobra_unified_live_timeline' in text,
      'call_continuity_preserved':'CobraCallAudioPolicy' in text,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    helper=text[text.index('private String mCobraLastLiveDiagnosticsSnapshot'):]
    for token in ('setMediaItem(','player.prepare()','mPlayer.prepare()','player.play()','mPlayer.play()','seekTo('):
      checks['observation_only_no_'+re.sub('[^a-z0-9]+','_',token.lower()).strip('_')]=token not in helper
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103185,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed:raise RuntimeError('2103185 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103185 source checks')

if __name__=='__main__':main()
