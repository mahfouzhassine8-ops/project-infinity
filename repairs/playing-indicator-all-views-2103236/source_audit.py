#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
PARENT='edaf4a757ceded3099fc0e2adbbcfb5dbf98d394c713b321d41efe62ae6a7d54'
PATCHED='0b1e50528f790dd6fdbc71a880eeffbd0c6c6bb13f9606ffacb8e7971f149dbf'

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

    policy=block(text,'CobraPlayingIndicatorPolicy','class')
    owner=block(text,'cobraPlayingIndicatorOwner')
    truth=block(text,'cobraChannelActuallyPlaying')
    color=block(text,'cobraPlayingIndicatorColor')
    refresh=block(text,'cobraRefreshPlayingIndicators')
    dot=block(text,'CobraPlayingDot','class')
    mobile=block(text,'CobraMobileChannelRow','class')
    compact=block(text,'CobraCompactChannelRow','class')
    cards=block(text,'CobraPosterChannelCard','class')
    focus=block(text,'CobraFocusQueueRow','class')
    grid=block(text,'CobraBroadcastRow','class')

    checks={
      'exact_parent':scope.get('activity_before_sha256')==PARENT and scope.get('parent')==2103235,
      'exact_postimage':hb(raw)==PATCHED,
      'cinema_amber_constant':'CINEMA_AMBER=0xffffc247' in policy,
      'cinema_amber_mapping':'cinema?CobraPlayingIndicatorPolicy.CINEMA_AMBER:cobraModeColor("accent")' in color,
      'pulse_policy_preserved':'cinema?1900L:1320L' in policy and 'if(cinema)return 58' in policy,
      'session_truth_preserved':'mCobraPlayerBindings.get(player)' in owner and 'binding.current()' in owner and 'channel.id.equals(owner.channel.id)' in truth,
      'focus_cannot_own_session':'mGuidePreviewChannel' not in owner and 'mCobraInspectedChannel' not in owner and 'cobraModeSelected' not in owner,
      'tv_grid_renderer_preserved':hb(grid)==scope['protected_classes_sha256']['CobraBroadcastRow'],
      'dot_renderer_preserved':hb(dot)==scope['protected_classes_sha256']['CobraPlayingDot'],
      'mobile_has_dot':'final CobraPlayingDot playing=new CobraPlayingDot()' in mobile and 'headline.addView(playing,dot)' in mobile and 'playing.bind(c)' in mobile and 'void refreshPlaying(){playing.sync();}' in mobile,
      'compact_has_dot':'final CobraPlayingDot playing=new CobraPlayingDot()' in compact and 'addView(playing,dot)' in compact and 'playing.bind(c)' in compact and 'void refreshPlaying(){playing.sync();}' in compact,
      'cards_has_dot':'final CobraPlayingDot playing=new CobraPlayingDot()' in cards and 'hero.addView(playing,dot)' in cards and 'playing.bind(c)' in cards and 'void refreshPlaying(){playing.sync();}' in cards,
      'focus_has_dot':'final CobraPlayingDot playing=new CobraPlayingDot()' in focus and 'addView(playing,dot)' in focus and 'playing.bind(c)' in focus and 'void refreshPlaying(){playing.sync();}' in focus,
      'refreshes_all_five':'CobraBroadcastRow' in refresh and 'CobraMobileChannelRow' in refresh and 'CobraCompactChannelRow' in refresh and 'CobraPosterChannelCard' in refresh and 'CobraFocusQueueRow' in refresh,
      'cards_selection_still_separate':'SELECTED CHANNEL' in cards and 'playing.bind(c)' in cards,
      'focus_selection_still_separate':'cobraModeSelected(c)?"●"' in focus and 'playing.bind(c)' in focus,
    }

    # Newly added renderer plumbing may never mutate playback.
    forbidden=('prepare(','setMediaItem(','release(','seekTo(','startCobraPlayer(','playChannel(','cobraRetryMultiTile(','setVolume(','pause();','play();')
    for name,body in {'color':color,'refresh':refresh,'mobile':mobile,'compact':compact,'cards':cards,'focus':focus}.items():
        hits=[x for x in forbidden if x in body]
        checks['presentation_only_'+name]=not hits

    protected={}
    for n,d in scope.get('protected_methods_sha256',{}).items():
        protected[n]=hb(block(text,n))==d
    for n,d in scope.get('protected_classes_sha256',{}).items():
        protected['class:'+n]=hb(block(text,n,'class'))==d
    checks['protected_session_playback_unchanged']=all(protected.values())

    failed=[k for k,v in checks.items() if not v]
    result={
      'build':2103236,'parent':2103235,'passed':not failed,'checks':checks,'failed':failed,
      'protected':protected,'views':['grid','mobile','compact','cards','focus'],
      'cinema_color':'0xffffc247','physical_device_verified':False
    }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'source-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if failed:raise RuntimeError('2103236 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'all-view indicator source/preservation gates')
if __name__=='__main__':main()
