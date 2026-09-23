#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
PARENT='d99ee556d5324e8f4467dde7a2fdf5ad7b9e29cbed6a44d3112a2e42199617c0'

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

def fill_rect(index,count,w,h,enlarged=-1):
    if count<1 or count>4 or index<0 or index>=count or w<=0 or h<=0:return (0,0,0,0)
    if count==1:return (0,0,w,h)
    portrait=h>w
    if 0<=enlarged<count:
        rank=index if index<enlarged else index-1;small=count-1
        if portrait:
            large=max(1,min(h-1,round(h*.68)))
            if index==enlarged:return (0,0,w,large)
            x=w*rank//small;right=w*(rank+1)//small;return (x,large,right-x,h-large)
        large=max(1,min(w-1,round(w*.72)))
        if index==enlarged:return (0,0,large,h)
        y=h*rank//small;bottom=h*(rank+1)//small;return (large,y,w-large,bottom-y)
    if count==2:
        if portrait:
            y=h*index//2;bottom=h*(index+1)//2;return (0,y,w,bottom-y)
        x=w*index//2;right=w*(index+1)//2;return (x,0,right-x,h)
    if count==3:
        if portrait:
            large=max(1,min(h-1,round(h*.60)))
            if index==0:return (0,0,w,large)
            rank=index-1;x=w*rank//2;right=w*(rank+1)//2;return (x,large,right-x,h-large)
        large=max(1,min(w-1,round(w*.60)))
        if index==0:return (0,0,large,h)
        rank=index-1;y=h*rank//2;bottom=h*(rank+1)//2;return (large,y,w-large,bottom-y)
    col=index%2;row=index//2;x=w*col//2;y=h*row//2;right=w*(col+1)//2;bottom=h*(row+1)//2
    return (x,y,right-x,bottom-y)

def geometry_audit():
    rows=[]
    for w,h,label in ((1812,2176,'inner-p'),(2176,1812,'inner-l'),(904,2316,'cover-p'),(2316,904,'cover-l'),(1600,900,'window-l'),(900,1600,'window-p'),(601,601,'square')):
        for count in (2,3,4):
            for enlarged in (-1,*range(count)):
                rects=[fill_rect(i,count,w,h,enlarged) for i in range(count)]
                area=sum(r[2]*r[3] for r in rects)
                req(area==w*h,f'Fill layout leaves/overlaps canvas: {label} count={count} enlarged={enlarged} area={area}/{w*h}')
                for x,y,rw,rh in rects:
                    req(rw>0 and rh>0 and x>=0 and y>=0 and x+rw<=w and y+rh<=h,'Fill rect out of bounds')
                rows.append({'viewport':label,'count':count,'enlarged':enlarged,'rects':rects,'area':area})
    # Explicit acceptance shapes.
    r=[fill_rect(i,2,1000,2000,-1) for i in range(2)]
    req(r==[(0,0,1000,1000),(0,1000,1000,1000)],'2 portrait is not contiguous top/bottom')
    r=[fill_rect(i,2,2000,1000,-1) for i in range(2)]
    req(r==[(0,0,1000,1000),(1000,0,1000,1000)],'2 landscape is not side-by-side')
    r=[fill_rect(i,4,2000,1000,-1) for i in range(4)]
    req(r==[(0,0,1000,500),(1000,0,1000,500),(0,500,1000,500),(1000,500,1000,500)],'4 tile layout is not 2x2')
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--scope',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/ACT).read_text();scope=json.loads(a.scope.read_text())
    policy=block(text,'CobraMultiLayoutPolicy','class');recovery_policy=block(text,'CobraMultiRecoveryPolicy','class')
    layout=block(text,'cobraLayoutMultiTiles');fit=block(text,'cobraFitBinding');setter=block(text,'cobraSetMultiFillScreen');chooser=block(text,'cobraShowMultiLayoutChooser')
    recover=block(text,'cobraRecoverMultiTileSession');inspect=block(text,'cobraInspectMultiHealth');actions=block(text,'showCobraMultiTileActions');retry=block(text,'cobraRetryMultiTile')
    checks={
      'exact_locked_parent':scope.get('preaudit_activity_sha256')==PARENT and scope.get('parent')==2103227,
      'layout_pref_persistent':'COBRA_MULTI_LAYOUT_FILL' in text and 'putBoolean(COBRA_MULTI_LAYOUT_FILL,fill)' in setter,
      'fit_preserved':'if(!fillScreen)return rect(index,count,width,height,enlarged);' in policy,
      'fill_policy_dispatch':'rect(i,tiles.size(),safeW,safeH,enlarged,fill)' in layout,
      'fill_safe_insets':'cobraMultiSafeInsets()' in layout and 'systemBars()|android.view.WindowInsets.Type.displayCutout()' in block(text,'cobraMultiSafeInsets'),
      'fill_minimum_center_crop':'CobraFoldAspectPolicy.fill' in fit,
      'fill_only_for_multiview':'cobraMultiViewPlayer(binding.player)&&cobraMultiFillScreen()' in fit,
      'layout_ui':'"Multi-View layout"' in actions and '"Fill Screen"' in chooser and '"Fit"' in chooser,
      'layout_switch_refits_only':'cobraLayoutMultiTiles();' in setter and 'cobraFitBinding(binding)' in setter,
      'recovery_bounded':'MAX_AUTOMATIC_REPREPARES=2' in recovery_policy and 'canAttempt' in recovery_policy,
      'recovery_error':'return "error"' in recovery_policy,
      'recovery_idle':'Player.STATE_IDLE' in recovery_policy and 'IDLE_GRACE_MS=6000L' in recovery_policy,
      'recovery_buffer':'Player.STATE_BUFFERING' in recovery_policy and 'BUFFER_STALL_MS=18000L' in recovery_policy,
      'recovery_does_not_stack_ended':'Player.STATE_ENDED' not in recovery_policy,
      'recovery_does_not_stack_ready_surface':'Player.STATE_READY' not in recovery_policy,
      'same_player_reprepare':'player.seekToDefaultPosition();player.prepare();startCobraPlayer(player);' in recover,
      'timeshift_excluded':'player==mCobraTimeshiftPlayer||player==mCobraTimeshiftProxyPlayer' in recover,
      'fullscreen_promotion_excluded':'mCobraMultiFullscreenActive' in recover,
      'manual_pause_preserved':'!player.getPlayWhenReady()' in recover,
      'diagnostic_per_tile':'"tile-state"' in inspect and 'auto_recoveries=' in inspect and 'channel_hash=' in inspect,
      'surface_recovery_kept_separate':'Video stalled' in inspect and 'cobraReattachObservedSurface' in text,
      'live_ended_recovery_kept_separate':'binding.liveEndedRecovering' in inspect and 'cobraRecoverUnexpectedLiveEnded' in text,
      'manual_retry_fresh_budget':'tile.autoRecoveries=0' in retry and 'tile.recovering=false' in retry,
      'stable_budget_reset':'STABLE_RESET_MS=60000L' in recovery_policy and 'recovery-budget-reset' in inspect,
    }
    forbidden_layout=('setMediaItem(','prepare()','startCobraPlayer(','cobraDisposePlayer(','buildPlayer(','releaseMulti();','multiToSingle();')
    layout_blocks={'setter':setter,'chooser':chooser,'layout':layout,'fit':fit}
    forbidden_found={}
    for name,body in layout_blocks.items():
        hits=[token for token in forbidden_layout if token in body];forbidden_found[name]=hits;checks['layout_no_playback_mutation_'+name]=not hits
    forbidden_recovery=('cobraDisposePlayer(','buildPlayer(','releaseMulti();','multiToSingle();','setMediaItem(')
    forbidden_found['auto_recovery']=[x for x in forbidden_recovery if x in recover]
    checks['auto_recovery_no_player_recreate_or_peer_teardown']=not forbidden_found['auto_recovery']
    protected={}
    for name,digest in scope.get('protected_methods_sha256',{}).items():protected[name]=hb(block(text,name))==digest
    for name,digest in scope.get('protected_classes_sha256',{}).items():protected['class:'+name]=hb(block(text,name,'class'))==digest
    checks['protected_members_unchanged']=all(protected.values())
    geometry=geometry_audit();checks['fill_geometry_cases']=len(geometry)>=80
    failed=[k for k,v in checks.items() if not v]
    result={'build':2103229,'parent':2103227,'passed':not failed,'checks':checks,'failed':failed,'protected':protected,
      'forbidden_playback_tokens':forbidden_found,'fill_geometry_case_count':len(geometry),'geometry_cases':geometry,
      'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed:raise RuntimeError('2103229 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'source/ownership checks and',len(geometry),'Fill Screen geometry cases')
if __name__=='__main__':main()
