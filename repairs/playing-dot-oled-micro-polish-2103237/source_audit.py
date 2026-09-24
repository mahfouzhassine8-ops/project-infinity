#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
PARENT='0b1e50528f790dd6fdbc71a880eeffbd0c6c6bb13f9606ffacb8e7971f149dbf'
PATCHED='afa638f0f881c2d437fb5cad56c22453972a5900dcee18eac962537dba0bc255'

def hb(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)
def block(text,name,kind='method'):
    if kind=='method':
        p=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:
        p=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    st=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=com=False
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
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--scope',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=(a.source/ACT).read_bytes();text=raw.decode();scope=json.loads(a.scope.read_text())
    policy=block(text,'CobraPlayingIndicatorPolicy','class');dot=block(text,'CobraPlayingDot','class')
    color=block(text,'cobraPlayingIndicatorColor');refresh=block(text,'cobraRefreshPlayingIndicators')
    owner=block(text,'cobraPlayingIndicatorOwner');truth=block(text,'cobraChannelActuallyPlaying')

    checks={
      'exact_parent':scope.get('activity_before_sha256')==PARENT and scope.get('parent')==2103236,
      'exact_postimage':hb(raw)==PATCHED,
      'actual_session_owner_preserved':'mCobraPlayerBindings.get(player)' in owner and 'binding.current()' in owner,
      'actual_channel_truth_preserved':'channel.id.equals(owner.channel.id)' in truth,
      'focus_cannot_own_truth':'mGuidePreviewChannel' not in owner and 'mCobraInspectedChannel' not in owner and 'cobraModeSelected' not in owner,
      'cinema_amber_preserved':'CINEMA_AMBER=0xffffc247' in policy and 'CobraPlayingIndicatorPolicy.CINEMA_AMBER' in color,
      'handoff_180ms':'HANDOFF_MS=180L' in policy and 'handoffAlpha' in policy and 'handoffDirection' in dot,
      'handoff_only_visual':'setVisibility(View.VISIBLE)' in dot and 'cobraPlayingIndicatorOwner()' in dot,
      'color_morph_240ms':'COLOR_MORPH_MS=240L' in policy and 'blendColor' in policy and 'renderedColor' in dot and 'interpolatedColor' in dot,
      'oled_core_floor':'OLED_CORE_FLOOR_ALPHA=218' in policy and 'oledCoreAlpha' in policy and 'coreAlpha' in dot,
      'oled_glow_floor':'OLED_GLOW_FLOOR=.58f' in policy and 'oledGlowFactor' in policy,
      'oled_transparent_micro_bloom':'outerAlpha' in dot and 'innerAlpha' in dot and 'canvas.drawCircle' in dot and 'setBackground' not in dot,
      'cinema_slow_pulse_preserved':'cinema?1900L:1320L' in policy and 'if(cinema)return 58' in policy,
      'buffering_truth_preserved':'Player.STATE_BUFFERING' in policy,
      'all_five_view_refresh_preserved':all(x in refresh for x in ('CobraBroadcastRow','CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow')),
      'new_bind_avoids_recycled_row_ghost':'java.util.Objects.equals(channel.id,value.id)' in dot and 'sync(same)' in dot,
      'stop_without_replacement_clears_immediately':'else{visualActive=false;handoffDirection=0;setVisibility(View.INVISIBLE);}' in dot,
    }

    forbidden=('setMediaItem(','prepare(','seekTo(','release(','setPlayWhenReady(','pause();','play();','playChannel(','startSinglePlayer(','cobraRetryMultiTile(')
    hits=[token for token in forbidden if token in dot]
    checks['renderer_has_no_playback_mutation']=not hits

    protected={}
    for n,d in scope.get('protected_methods_sha256',{}).items():protected[n]=hb(block(text,n))==d
    for n,d in scope.get('protected_classes_sha256',{}).items():protected['class:'+n]=hb(block(text,n,'class'))==d
    checks['all_protected_playback_and_placements_unchanged']=all(protected.values())

    failed=[k for k,v in checks.items() if not v]
    result={
      'build':2103237,'parent':2103236,'passed':not failed,'checks':checks,'failed':failed,
      'protected':protected,'forbidden_renderer_hits':hits,
      'views':['TV Grid','Mobile','Compact','Cards','Focus'],
      'handoff_ms':180,'color_morph_ms':240,'oled_core_floor_alpha':218,'oled_glow_floor':0.58,
      'cinema_color':'0xffffc247','buffering_animation_untouched':True,'physical_device_verified':False
    }
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if failed:raise RuntimeError('2103237 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'OLED micro-polish source/preservation gates')
if __name__=='__main__':main()
