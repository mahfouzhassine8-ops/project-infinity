#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,re
from pathlib import Path

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
PARENT_LAYOUT='2d16cef09fe3151af6b2600fdab40037de4eb49df6f3f32a5674eaff7c0cacce'

def hb(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def req(v,m):
    if not v:raise RuntimeError(m)

def block(text,name,kind='method'):
    if kind=='method':
        p=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:
        p=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    ms=list(p.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    s=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=com=False
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
            if d==0:return text[s:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)

def fit(vw,vh,pixel,w,h):
    if vw<=0 or vh<=0 or w<=0 or h<=0:return (1.0,1.0)
    source=vw*(pixel if pixel>0 else 1.0)/vh
    view=w/h
    return (source/view if source<view else 1.0, view/source if source>view else 1.0)

def fill(vw,vh,pixel,w,h):
    if vw<=0 or vh<=0 or w<=0 or h<=0:return (1.0,1.0)
    sx,sy=fit(vw,vh,pixel,w,h);z=max(1.0/sx,1.0/sy);return (sx*z,sy*z)

def geometry_audit():
    viewports=[
        (1812,2176,'inner-portrait'),(2176,1812,'inner-landscape'),
        (904,2316,'cover-portrait'),(2316,904,'cover-landscape'),
        (1088,1812,'split-inner'),(452,2316,'split-cover'),
        (1600,900,'landscape-window'),(900,1600,'portrait-window'),
        (601,601,'square'),(320,240,'small-pane')
    ]
    sources=[
        (1920,1080,1.0,'16:9'),(1080,1920,1.0,'9:16'),
        (720,576,16/15,'anamorphic'),(3840,2160,1.0,'4k-16:9'),
        (1440,1080,1.0,'4:3')
    ]
    rows=[]
    for w,h,vname in viewports:
        for vw,vh,pixel,sname in sources:
            source=vw*pixel/vh
            sf=fit(vw,vh,pixel,w,h);sg=fill(vw,vh,pixel,w,h)
            fw,fh=w*sf[0],h*sf[1];gw,gh=w*sg[0],h*sg[1]
            req(fw<=w+1e-5 and fh<=h+1e-5,'Fold Fit cropped '+vname+' '+sname)
            req(abs(fw-w)<1e-4 or abs(fh-h)<1e-4,'Fold Fit does not meet an edge '+vname+' '+sname)
            req(abs((fw/fh)-source)<1e-5,'Fold Fit distorted '+vname+' '+sname)
            req(gw+1e-5>=w and gh+1e-5>=h,'Fold Fill left bars '+vname+' '+sname)
            req(abs(gw-w)<1e-4 or abs(gh-h)<1e-4,'Fold Fill crop is not minimum '+vname+' '+sname)
            req(abs((gw/gh)-source)<1e-5,'Fold Fill distorted '+vname+' '+sname)
            req(sg[0]>=1-1e-6 and sg[1]>=1-1e-6,'Fold Fill unexpectedly shrank pane '+vname+' '+sname)
            rows.append({'viewport':vname,'source':sname,'fit':[round(x,6) for x in sf],'fill':[round(x,6) for x in sg]})
    req(fit(0,1080,1,1000,1000)==(1.0,1.0),'Fit invalid geometry unsafe')
    req(fill(1920,0,1,1000,1000)==(1.0,1.0),'Fill invalid geometry unsafe')
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--scope',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/ACT).read_text();scope=json.loads(a.scope.read_text())
    policy=block(text,'CobraFoldAspectPolicy','class')
    layout=block(text,'CobraLayoutMath','class')
    picker=block(text,'showCobraAspectPicker')
    channel=block(text,'cobraShowChannelAspect')
    label=block(text,'cobraAspectLabel')
    bind=block(text,'cobraBindingAspect')
    fitvideo=block(text,'cobraFitVideo')
    fitbinding=block(text,'cobraFitBinding')
    attach=block(text,'cobraAttachVideo')
    defaults=block(text,'cobraShowPlaybackDefaults')
    save=block(text,'cobraSavePreferences')

    checks={
        'exact_parent_recorded':scope.get('parent')==2103225 and scope.get('preaudit_activity_sha256')=='2fee5673e153ac152ecfec495d3c6c076eac1bb55a6221a1c03535742698de9a',
        'legacy_mode12_preserved':'static final int MODE=12;' in policy and 'static final int FIT_MODE=MODE;' in policy,
        'fill_mode13':'static final int FILL_MODE=13;' in policy and 'static final int MAX_MODE=FILL_MODE;' in policy,
        'fit_whole_frame':'float sx=source<view?source/view:1f,sy=source>view?view/source:1f;' in policy,
        'fill_minimum_cover':'float zoom=Math.max(1f/fit[0],1f/fit[1]);' in policy and 'return new float[]{fit[0]*zoom,fit[1]*zoom};' in policy,
        'legacy_scale_compat':'return fit(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight);' in policy,
        'dispatch':'CobraFoldAspectPolicy.foldMode(mode)' in fitvideo and 'CobraFoldAspectPolicy.scaleForMode' in fitvideo,
        'old_modes_math_unchanged':hb(layout)==PARENT_LAYOUT,
        'labels':'case 12: return "Fold Fit";' in label and 'case 13: return "Fold Fill";' in label,
        'picker_order':'{CobraFoldAspectPolicy.FIT_MODE,CobraFoldAspectPolicy.FILL_MODE,0,1' in picker,
        'channel_order':'{CobraFoldAspectPolicy.FIT_MODE,CobraFoldAspectPolicy.FILL_MODE,-1,0,1' in channel,
        'default_order':'{CobraFoldAspectPolicy.FIT_MODE,CobraFoldAspectPolicy.FILL_MODE,0,1' in defaults,
        'global_persistence':'mode<=CobraFoldAspectPolicy.MAX_MODE' in block(text,'cobraChannelAspect'),
        'channel_persistence':'value<=CobraFoldAspectPolicy.MAX_MODE' in text,
        'multiview_fold_only':'cobraMultiViewPlayer(binding.player)&&CobraFoldAspectPolicy.foldMode(global)?global:0' in bind,
        'channel_override_authoritative':'if(binding.vitals.live&&binding.vitals.preferences.aspect>=0)mode=binding.vitals.preferences.aspect;' in bind,
        'pip_best_fit':'mInPictureInPicture?0:mode' in fitbinding,
        'viewport_listener':'texture.addOnLayoutChangeListener(binding.layoutListener);' in attach and 'cobraFitBinding(binding)' in attach,
        'configuration_multiview_reflow':'if(mMultiOverlay!=null){cobraLayoutPlayerPanels();cobraLayoutMultiTiles();return;}' in block(text,'onConfigurationChanged'),
        'save_preferences_reflows_not_restarts':'cobraFitBinding(b);' in save,
        'player_not_recreated':scope.get('switching',{}).get('player_recreated') is False,
        'retune_not_added':scope.get('switching',{}).get('retune') is False,
        'seek_not_added':scope.get('switching',{}).get('seek') is False,
        'native_unchanged':scope.get('native_engine_rebuilt') is False,
        'physical_unverified':scope.get('physical_device_verified') is False,
    }

    forbidden=('setMediaItem','prepare()','release()','seekTo(','stop()','playChannel(','playVodUrl(','startSinglePlayer(','cobraRestartLiveChannel(')
    mutation_blocks={'picker':picker,'channel':channel,'fitvideo':fitvideo,'binding':bind,'multi_helper':block(text,'cobraMultiViewPlayer')}
    forbidden_found={}
    for name,body in mutation_blocks.items():
        hits=[token for token in forbidden if token in body]
        forbidden_found[name]=hits
        checks['no_playback_mutation_'+name]=not hits

    protected_ok={}
    for name,digest in scope.get('protected_methods_sha256',{}).items():
        current=hb(block(text,name));protected_ok[name]=current==digest
    for name,digest in scope.get('protected_classes_sha256',{}).items():
        current=hb(block(text,name,'class'));protected_ok['class:'+name]=current==digest
    checks['protected_members_unchanged']=all(protected_ok.values())

    geometry=geometry_audit()
    failed=[k for k,v in checks.items() if not v]
    result={
        'build':2103226,'parent':2103225,'passed':not failed,'checks':checks,'failed':failed,
        'protected':protected_ok,'forbidden_playback_tokens':forbidden_found,
        'geometry_cases':geometry,'geometry_case_count':len(geometry),
        'physical_device_verified':False
    }
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed:raise RuntimeError('2103226 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'source/ownership checks and',len(geometry),'Fold geometry cases')

if __name__=='__main__':main()
