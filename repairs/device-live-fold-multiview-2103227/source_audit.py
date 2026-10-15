#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,re
from pathlib import Path

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
PARENT='f02e1aa2550e56e0222fafaa3e8b74bf5ee8585353535891e60da709e1d3cdd0'

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

def contain(vw,vh,pixel,w,h):
    if min(vw,vh,w,h)<=0:return (1.,1.)
    source=vw*(pixel if pixel>0 else 1.)/vh;view=w/h
    return (source/view if source<view else 1.,view/source if source>view else 1.)

def fold_fit(vw,vh,pixel,w,h):
    b=contain(vw,vh,pixel,w,h)
    if min(vw,vh,w,h)<=0:return b
    smaller=min(b)
    if smaller>=.78:return b
    view=w/h;fill=max(1/b[0],1/b[1]);cap=1.70 if .65<=view<=1.35 else 2.40
    z=min(fill,min(cap,max(1.,.78/max(.0001,smaller))))
    return (b[0]*z,b[1]*z)

def fold_fill(vw,vh,pixel,w,h):
    b=contain(vw,vh,pixel,w,h)
    if min(vw,vh,w,h)<=0:return b
    z=max(1/b[0],1/b[1]);return (b[0]*z,b[1]*z)

def multi_rect(index,count,w,h,enlarged):
    if enlarged<0 or enlarged>=count or count<2:
        if count==1:return (0,0,w,h)
        if h>w:
            y=h*index//count;bottom=h*(index+1)//count;return (0,y,w,bottom-y)
        if count==2:
            x=w*index//2;return (x,0,w*(index+1)//2-x,h)
        col=index%2;row=index//2
        if count==3 and index==2:return (0,h//2,w,h-h//2)
        x=w*col//2;y=h*row//2;return (x,y,w*(col+1)//2-x,h*(row+1)//2-y)
    frac=.62 if h>=w else .70;large=max(1,min(h-1,round(h*frac)))
    if index==enlarged:return (0,0,w,large)
    rank=index if index<enlarged else index-1;small=count-1;strip=h-large
    if small==1:
        sw=max(1,round(w*(.72 if h>=w else .48)));return ((w-sw)//2,large,sw,strip)
    x=w*rank//small;right=w*(rank+1)//small;return (x,large,right-x,strip)

def geometry():
    views=[(1812,2176,'inner-p'),(2176,1812,'inner-l'),(904,2316,'cover-p'),(2316,904,'cover-l'),(1088,1812,'split-p'),(1600,900,'window-l'),(900,1600,'window-p'),(601,601,'square')]
    sources=[(1920,1080,1.,'16:9'),(1080,1920,1.,'9:16'),(720,576,16/15,'anamorphic'),(1440,1080,1.,'4:3')]
    rows=[]
    for w,h,vn in views:
        for vw,vh,pix,sn in sources:
            c=contain(vw,vh,pix,w,h);f=fold_fit(vw,vh,pix,w,h);g=fold_fill(vw,vh,pix,w,h)
            aspect=vw*pix/vh
            for name,sc in [('fit',f),('fill',g)]:
                rw,rh=w*sc[0],h*sc[1];req(abs(rw/rh-aspect)<1e-5,f'{name} distortion {vn}/{sn}')
            req(w*g[0]>=w-1e-4 and h*g[1]>=h-1e-4,f'fill bars {vn}/{sn}')
            req(f[0]<=g[0]+1e-5 and f[1]<=g[1]+1e-5,f'fit exceeds fill {vn}/{sn}')
            rows.append({'viewport':vn,'source':sn,'contain':c,'fit':f,'fill':g})
    # The reported Fold-inner 16:9 case must materially use more height than strict contain.
    c=contain(1920,1080,1,1812,2176);f=fold_fit(1920,1080,1,1812,2176)
    req(f[1]>=.75 and f[1]>c[1]*1.5,'device Fold Fit did not reduce reported black bands')
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--scope',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/ACT).read_text();scope=json.loads(a.scope.read_text())
    actions=block(text,'showCobraMultiTileActions');promote=block(text,'cobraPromoteMultiTileFullscreen');restore=block(text,'cobraReturnToMultiFromFullscreen')
    binding=block(text,'CobraPlayerBinding','class');state=block(text,'cobraPlayerState')
    fold=block(text,'CobraFoldAspectPolicy','class');layout=block(text,'CobraMultiLayoutPolicy','class')
    picker=block(text,'showCobraMultiPicker');back=block(text,'onBackPressed');pip=block(text,'cobraPrepareMultiForPip')
    chrome=block(text,'cobraBuildPlayerChrome')

    checks={
      'exact_parent_recorded':scope.get('preaudit_activity_sha256')==PARENT and scope.get('parent')==2103226,
      'live_ended_bounded':'MAX_RECOVERIES=2' in block(text,'CobraLiveEndedPolicy','class'),
      'live_ended_vod_excluded':'eligible(vitals.live,!mPlayingVodKey.isEmpty()' in binding,
      'live_ended_same_player_first':'ended.seekToDefaultPosition()' in block(text,'cobraRecoverUnexpectedLiveEnded') and 'ended.prepare()' in block(text,'cobraRecoverUnexpectedLiveEnded'),
      'live_ended_no_visible_ended_for_live':'liveEndedRecovering?"Reconnecting…":"Stream unavailable"' in state,
      'vod_completion_preserved':all(x in binding for x in ('saveVodProgress()','cobraMarkVodWatched','playNextEpisode()','cobraShowVodCompletion()')),
      'fold_modes_preserved':'FIT_MODE=MODE' in fold and 'FILL_MODE=13' in fold,
      'fold_balanced':'SMART_TARGET=.78f' in fold and 'cap=(view>=.65f&&view<=1.35f)?1.70f:2.40f' in fold,
      'fold_fill_preserved':'float zoom=Math.max(1f/base[0],1f/base[1]);' in fold,
      'multi_existing_audio':'"Use audio here"' in actions,
      'multi_existing_change':'"Change channel"' in actions,
      'multi_existing_add':'"Add screen"' in actions,
      'multi_existing_retry':'"Retry this screen"' in actions,
      'multi_existing_diagnostics':'"Playback details"' in actions,
      'multi_existing_remove':'"Remove screen"' in actions,
      'multi_existing_close':'"Close Multi-View"' in actions,
      'multi_search_add':'"Search and add"' in actions and 'cobra_multi_search' in picker and 'renderCobraMultiPickerSearch' in text,
      'multi_pause_resume':'"Pause":"Resume"' in actions and 'cobraToggleMultiTilePause' in actions,
      'multi_enlarge':'"Enlarge screen"' in actions and 'CobraMultiLayoutPolicy.rect' in block(text,'cobraLayoutMultiTiles'),
      'multi_fullscreen_reversible':'"Full screen"' in actions and 'cobraPromoteMultiTileFullscreen' in actions,
      'multi_fullscreen_not_destructive':'multiToSingle();' not in actions and 'releaseMulti();' not in promote and 'cobraDisposePlayer' not in promote,
      'multi_return_not_destructive':'cobraDisposePlayer' not in restore and 'releaseSinglePlayer' not in restore and 'cobraAttachVideo(session,tile.texture)' in restore,
      'multi_back_returns':'cobraReturnToMultiFromFullscreen' in back,
      'multi_player_action_returns':'mCobraMultiFullscreenActive?"Return Multi":"Multi-View"' in chrome,
      'multi_pip_does_not_teardown_promotion':'if(mCobraMultiFullscreenActive)return;' in pip,
      'physical_unverified':scope.get('physical_device_verified') is False,
      'native_unchanged':scope.get('native_engine_rebuilt') is False,
    }

    protected={}
    for name,digest in scope.get('protected_methods_sha256',{}).items():protected[name]=hb(block(text,name))==digest
    for name,digest in scope.get('protected_classes_sha256',{}).items():protected['class:'+name]=hb(block(text,name,'class'))==digest
    checks['protected_members_unchanged']=all(protected.values())

    geos=geometry()
    enlarged=[]
    for count in (2,3,4):
      for e in range(count):
        rects=[multi_rect(i,count,1600,900,e) for i in range(count)]
        req(rects[e][0]==0 and rects[e][1]==0 and rects[e][2]==1600,'enlarged tile not primary')
        for i,r in enumerate(rects):
          req(r[2]>0 and r[3]>0,'zero multi rect')
          if i!=e:req(r[1]>=rects[e][3],'small tile overlaps enlarged')
        enlarged.append({'count':count,'enlarged':e,'rects':rects})

    failed=[k for k,v in checks.items() if not v]
    result={'build':2103227,'parent':2103226,'passed':not failed,'checks':checks,'failed':failed,
      'protected':protected,'fold_geometry_cases':geos,'fold_geometry_case_count':len(geos),
      'multi_enlarge_cases':enlarged,'multi_enlarge_case_count':len(enlarged),'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed:raise RuntimeError('2103227 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'ownership checks,',len(geos),'Fold geometry cases,',len(enlarged),'Multi enlarge cases')

if __name__=='__main__':main()
