#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re

REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')

def require(v,msg):
    if not v: raise RuntimeError(msg)

def method(text,name):
    pat=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    ms=list(pat.finditer(text));require(len(ms)==1,f'{name} cardinality={len(ms)}')
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
            if d==0:return text[start:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)

def class_block(text,name):
    m=re.search(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M)
    require(m is not None,'missing class '+name);start=m.start();i=text.index('{',m.end());d=0;q=None;esc=line=block=False
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
            if d==0:return text[start:i+1]
        i+=1
    raise RuntimeError('unclosed class '+name)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/REL).read_text();patch=json.loads(a.patch.read_text())
    ts=class_block(text,'CobraLocalTimeshiftSession');transport=class_block(text,'CobraTimeshiftTransportPolicy')
    watchdog=text[text.index('private final Runnable mStallWatchdog'):text.index('private final Runnable mAutoRefresh')]
    preview=method(text,'startCobraPreview');promote=method(text,'promoteCobraPreviewToFullscreen');capture=method(text,'cobraCapturePreviewDiagnostics')
    checks={
      'exact_locked_parent':patch.get('base_build')==2103177 and patch.get('base_commit')=='3c51f790018eda816beeac6328d050e1fe242d6e',
      'real_http_crlf_policy':'"\\r\\n"' in transport and '"\\r\\n\\r\\n"' in transport and '\\\\r\\\\n' not in transport,
      'real_hls_line_policy':'#EXTM3U\\n#EXT-X-VERSION:3\\n' in transport and '#EXTM3U\\\\n' not in transport,
      'server_uses_policy':'CobraTimeshiftTransportPolicy.httpHeader' in ts and 'CobraTimeshiftTransportPolicy.playlistHeader' in ts,
      'server_supports_get_head':'"HEAD".equalsIgnoreCase(method)' in ts and '"GET".equalsIgnoreCase(method)' in ts,
      'server_http_diagnostics':all(x in ts for x in ('httpRequests++','httpFailures++','playlistRequests++','segmentRequests++','lastHttpError')),
      'timeshift_direct_fallback':'timeshift-transport-fallback' in text and 'cobraStartDirectSinglePlayer' in class_block(text,'CobraPlayerBinding') and 'cobraStartDirectPreview' in class_block(text,'CobraPlayerBinding'),
      'preview_local_reserve':'cobraShouldUseLocalTimeshift(channel,channel.primaryUrl)' in preview and 'cobraStartLocalTimeshiftPreview' in preview,
      'preview_local_one_provider_path':'session.playlistUrl()' in method(text,'cobraStartLocalTimeshiftPreview') and 'channel.primaryUrl' not in method(text,'cobraStartLocalTimeshiftPreview'),
      'preview_same_player_handoff':'session==mCobraTimeshiftPlayer' in promote and 'mCobraTimeshiftPlayer=session' in promote and 'preview-timeshift-fullscreen' in promote,
      'preview_diagnostic_capture':'mini_preview_direct' in capture and 'cobraFreshHealthSnapshot()' in capture and 'startActivityForResult' in capture,
      'preview_action_exposed':'Capture diagnostics' in method(text,'cobraShowPreviewActions'),
      'preview_lifecycle_counters':all(x in text for x in ('preview_start_count','preview_direct_starts','preview_timeshift_starts','preview_handoffs','preview_stops')),
      'prepare_surface_observation':all(x in text for x in ('prepare_calls','last_prepare_reason','surface_attach_calls','surfaceAttachCalls++')),
      'timeshift_http_snapshot':all(x in text for x in ('timeshift_http_requests','timeshift_http_failures','timeshift_playlist_requests','timeshift_segment_requests','timeshift_last_http_error')),
      'timeshift_explicit_ui_states':all(x in text for x in ('"STARTING"','"READY"','"RECONNECTING"','"UNSUPPORTED"','"FAILED"')) and 'cobraTimeshiftStatusText()' in method(text,'cobraUpdatePerformanceOverlay'),
      'watchdog_no_reprepare':'buffer_observed_no_restart' in watchdog and 'mPlayer.prepare()' not in watchdog and 'mPlayer.play()' not in watchdog,
      'refresh_rate_preserved':'preferredDisplayModeId' in text and 'mCobraActiveHz' in text and 'DISPLAY & PERFORMANCE' in text,
      'provider_catchup_preserved':'tv_archive' in text and 'cobraStartProviderCatchup' in text and '/timeshift/' in text,
      'last_channel_preserved':'cobra_last_channel' in text and 'cobraTuneLastChannel' in text,
      'statusbar_contract_preserved':'cobra-browse-background' in text and 'cobra-browse-safe-content' in text and 'cobraApplySystemBarsForSurface' in text,
      'file_picker_preserved':'cobraOpenFilePicker' in text and 'cobraLaunchFilePicker' in text,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_zip_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    out={'passed':not failed,'checks':checks,'failed':failed,'build':2103178,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    if failed:raise RuntimeError('2103178 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103178 timeshift/mini-player source checks')
if __name__=='__main__':main()
