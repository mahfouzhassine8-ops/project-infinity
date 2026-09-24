#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
PARENT='1324e98736c24e203941261cc34c468596892a7897e0679b51f5915e26bd34b6'

def hb(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)
def block(text,name,kind='method'):
    if kind=='method':p=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:p=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
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
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--scope',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/ACT).read_text();scope=json.loads(a.scope.read_text())
    policy=block(text,'CobraPlayingIndicatorPolicy','class');owner=block(text,'cobraPlayingIndicatorOwner');match=block(text,'cobraChannelActuallyPlaying');color=block(text,'cobraPlayingIndicatorColor');refresh=block(text,'cobraRefreshPlayingIndicators');dot=block(text,'CobraPlayingDot','class');row=block(text,'CobraBroadcastRow','class');programme=block(text,'cobraRefreshProgrammeLabels')
    checks={
      'exact_parent':scope.get('activity_before_sha256')==PARENT and scope.get('parent')==2103230,
      'real_session_states':'state==Player.STATE_READY||state==Player.STATE_BUFFERING' in policy,
      'requires_live_requested_unsuppressed':'live&&requested&&!error&&suppression==Player.PLAYBACK_SUPPRESSION_REASON_NONE' in policy,
      'fullscreen_owner':'mPlayer!=null&&mPlayingVodKey.isEmpty()&&!mCobraProviderCatchupActive' in owner,
      'multiview_audio_owner':'mMultiPlayers[mAudioTile]' in owner and 'mAudioTile<mMultiPlayers.length' in owner,
      'preview_owner':'mCobraPreviewPlayer' in owner,
      'background_owner':'mCobraMiniBackgroundPlayer' in owner,
      'binding_current':'mCobraPlayerBindings.get(player)' in owner and 'binding.current()' in owner,
      'not_focus_or_selection_owned':'mGuidePreviewChannel' not in owner and 'cobraModeSelected' not in owner and 'mCobraInspectedChannel' not in owner,
      'channel_match_by_id':'channel.id.equals(owner.channel.id)' in match,
      'ambient_adaptive':'CobraPresentationEffects.ambientMode(mPrefs)' in dot and 'CobraPresentationEffects.IMMERSIVE' in dot,
      'cinema_adaptive':'CobraPresentationEffects.NIGHT' in color and 'COBRA_LIVE_AMBIENT_BLUE' in color and 'pulsePeriodMs(cinema)' in dot,
      'subtle_pulse':'postInvalidateOnAnimation()' in dot and 'glowAlpha' in dot,
      'grid_channel_side_only':'final CobraPlayingDot playing=new CobraPlayingDot()' in row and 'playing.bind(c)' in row and 'labelWidth-indicator' in row,
      'indicator_space_reserved':'indicatorPad=Math.max' in row and 'dp(28)' in row,
      'periodic_live_refresh':'cobraRefreshPlayingIndicators();' in programme,
      'no_fake_playing_copy':'setText("PLAYING"' not in dot and 'setText("LIVE"' not in dot,
    }
    forbidden=('prepare(','setMediaItem(','release(','seekTo(','play();','pause();','setVolume(','startCobraPlayer(','playChannel(','cobraRetryMultiTile(')
    for name,body in {'owner':owner,'match':match,'color':color,'refresh':refresh,'dot':dot}.items():
        hits=[x for x in forbidden if x in body];checks['no_playback_mutation_'+name]=not hits
    protected={}
    for n,d in scope.get('protected_methods_sha256',{}).items():protected[n]=hb(block(text,n))==d
    for n,d in scope.get('protected_classes_sha256',{}).items():protected['class:'+n]=hb(block(text,n,'class'))==d
    checks['protected_playback_owners_unchanged']=all(protected.values())
    failed=[k for k,v in checks.items() if not v]
    result={'build':2103235,'parent':2103230,'passed':not failed,'checks':checks,'failed':failed,'protected':protected,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed:raise RuntimeError('2103235 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'true-playing indicator source/ownership gates')
if __name__=='__main__':main()
