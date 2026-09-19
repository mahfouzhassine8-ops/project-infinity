#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')

def require(v,msg):
    if not v:raise RuntimeError(msg)

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
    text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
    transport=block(text,'CobraTimeshiftTransportPolicy','class')
    ts=block(text,'CobraLocalTimeshiftSession','class')
    full=block(text,'cobraStartLocalTimeshift');preview=block(text,'cobraStartLocalTimeshiftPreview')
    chrome=block(text,'cobraBuildPlayerChrome');audio=block(text,'cobraHandleAudioFocus')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    checks={
      'exact_2103181_parent':patch.get('base_build')==2103181 and patch.get('base_commit')=='bfc69d84552dd64ef39946bdd2b368e7ff1def52',
      'startup_reserve_21s':'STARTUP_RESERVE_MS=21000L' in transport,
      'startup_wait_32s':'STARTUP_WAIT_MS=32000L' in transport,
      'startup_uses_actual_window':'startupReady(long windowMs)' in transport and 'startupReady(windowDurationMs())' in ts,
      'nine_second_segment_gate_removed':'READY_SEGMENTS' not in ts,
      'fullscreen_wait_uses_policy':'awaitReady(CobraTimeshiftTransportPolicy.STARTUP_WAIT_MS)' in full,
      'preview_wait_uses_policy':'awaitReady(CobraTimeshiftTransportPolicy.STARTUP_WAIT_MS)' in preview,
      'ready_time_recorded':'readyElapsed=android.os.SystemClock.elapsedRealtime()' in ts and 'startupReadyAfterMs' in ts,
      'diagnostics_export_reserve':'timeshift_startup_reserve_ms' in text and 'timeshift_startup_ready_after_ms' in text,
      'fifteen_second_live_target_preserved':'LIVE_RESERVE_MS=15000L' in transport and 'TIME-OFFSET=-15.0' in transport,
      'fast_provider_reconnect_preserved':'READ_TIMEOUT_MS=5000' in transport,
      'hls_transport_integrity_preserved':'#EXT-X-DISCONTINUITY-SEQUENCE:' in transport and 'publishedSegmentDurationMs' in transport and 'segment404s' in ts,
      'unified_blue_timeline_preserved':'cobra_unified_live_timeline' in chrome and 'footer.addView(mCobraTimeshiftSeek' not in chrome,
      'phone_call_video_continuity_preserved':'video_preserved=true' in audio and '.pause(' not in audio,
      'pro_watchdog_preserved':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'bounded_auto_live_recovery_preserved':'MAX_AUTO_LIVE_EDGE_ATTEMPTS=2' in text and 'RECOVERY_COOLDOWN_MS=60000L' in text,
      'no_custom_dns_pinning':patch.get('dns_pin_or_custom_resolver_added') is False,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103182,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed:raise RuntimeError('2103182 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103182 startup-reserve source checks')

if __name__=='__main__':main()
