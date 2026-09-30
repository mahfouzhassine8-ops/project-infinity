#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

def h(x):
    if isinstance(x,str):x=x.encode()
    return hashlib.sha256(x).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)
def span(text,name,kind='class'):
    if kind=='class':p=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    else:p=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}');st=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=com=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif com:
            if c=='*' and n=='/':com=False;i+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':com=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return text[st:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    text=(a.root/'shell-kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in').read_text()
    policy=span(text,'CobraPlayingIndicatorPolicy');owner=span(text,'cobraPlayingIndicatorOwner','method');match=span(text,'cobraChannelActuallyPlaying','method');color=span(text,'cobraPlayingIndicatorColor','method');refresh=span(text,'cobraRefreshPlayingIndicators','method');dot=span(text,'CobraPlayingDot')
    views={}
    for name in ['CobraBroadcastRow','CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow']:
        block=span(text,name);views[name]={
            'field':'CobraPlayingDot playing=new CobraPlayingDot()' in block,
            'bind':'playing.bind(c)' in block,
            'refresh':'refreshPlaying(){playing.sync();}' in block,
        }
        req(all(views[name].values()),'Playing dot missing from '+name)
    checks={
      'actual_state_truth':'state==Player.STATE_READY||state==Player.STATE_BUFFERING' in policy,
      'requires_live_requested_unsuppressed':'live&&requested&&!error&&suppression==Player.PLAYBACK_SUPPRESSION_REASON_NONE' in policy,
      'fullscreen_owner':'mPlayer!=null&&mPlayingVodKey.isEmpty()&&!mCobraProviderCatchupActive' in owner,
      'multiview_audio_owner':'mMultiPlayers[mAudioTile]' in owner,
      'preview_owner':'mCobraPreviewPlayer' in owner,
      'background_owner':'mCobraMiniBackgroundPlayer' in owner,
      'binding_current':'binding.current()' in owner,
      'focus_independent':'mGuidePreviewChannel' not in owner and 'cobraModeSelected' not in owner and 'mCobraInspectedChannel' not in owner,
      'channel_id_match':'channel.id.equals(owner.channel.id)' in match,
      'night_cinema_amber':'CINEMA_AMBER=0xffffc247' in policy and 'CobraPlayingIndicatorPolicy.CINEMA_AMBER' in color,
      'ambient_adaptive':'CobraPresentationEffects.ambientMode(mPrefs)' in dot,
      'handoff_180':'HANDOFF_MS=180L' in policy,
      'morph_240':'COLOR_MORPH_MS=240L' in policy,
      'oled_floor':'OLED_CORE_FLOOR_ALPHA=218' in policy and 'OLED_GLOW_FLOOR=.58f' in policy,
      'periodic_refresh':'cobraRefreshPlayingIndicators();' in span(text,'cobraRefreshProgrammeLabels','method'),
      'all_views_refresh':all(k in refresh for k in ['CobraBroadcastRow','CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow']),
      'no_fake_playing_text':'setText("PLAYING"' not in text,
      'no_hold_preserved':'mPlayerOverlay.setOnLongClickListener(v -> true);' in text,
      'buffer_animation_still_present':'CobraBuffering' in text or 'cobraBuffer' in text or 'BUFFERING' in text,
    }
    for k,v in checks.items():req(v,'Source check failed: '+k)
    result={'passed':True,'checks':checks,'views':views,'activity_sha256':h(text),'status':'source verified; device test still required'}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'playing-dot-source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS:',json.dumps(result))
if __name__=='__main__':main()
