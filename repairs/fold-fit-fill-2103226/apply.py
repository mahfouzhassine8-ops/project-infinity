#!/usr/bin/env python3
"""2103226: audited Fold Fit / Fold Fill video-surface presentation modes.

Parent: exact locked 2103225 TV Show Typography.

Scope:
- Preserve saved mode 12 behavior exactly (whole-frame Fold Adaptive fit) and relabel it
  as Fold Fit.
- Add mode 13 Fold Fill: proportional cover of the *measured* TextureView with only
  the center crop mathematically required to fill that pane.
- Apply Fold Fit/Fill to Multi-View tiles when the global default is a Fold mode;
  per-channel overrides remain authoritative.
- Keep PiP on the existing Best Fit contract.
- Reflow exclusively through the existing TextureView matrix/layout-listener path.

No player creation/replacement, media prepare, stream URL, seek/timeshift, audio,
provider, rotation, PiP ownership, native engine, skin, or unrelated UI behavior changes.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103226
OLD_VERSION=2103225
OLD_NAME='1.0.9-Cobra-TV-Show-Typography-RC1'
NEW_NAME='1.0.9-Cobra-Fold-Fit-Fill-Audited-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
ACT=SOURCE+'InfinityLiveActivity.java.in'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT_ACTIVITY='2fee5673e153ac152ecfec495d3c6c076eac1bb55a6221a1c03535742698de9a'
PREAUDIT_RUN=35797116699

def hb(b):return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def sha(p):return hb(Path(p).read_bytes())
def req(v,m):
    if not v:raise RuntimeError(m)
def once(s,a,b,label):
    c=s.count(a);req(c==1,f'{label} anchor drift ({c})');return s.replace(a,b,1)

def span(text,name,kind='method'):
    if kind=='method':
        pat=re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
    else:
        pat=re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M)
    ms=list(pat.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
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
            if d==0:return start,i+1
        i+=1
    raise RuntimeError('Unclosed '+name)

def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+text[b:]
def hashes(text,names,kind='method'):
    return {n:hb(member(text,n,kind)) for n in names}

PROTECTED_METHODS=[
    'buildPlayer','startCobraPlayer','playChannel','playVodUrl',
    'cobraStartLocalTimeshift','cobraRewindLive','cobraGoLive','cobraDisposePlayer',
    'openMultiView','multiToSingle','cobraPrepareMultiForPip','cobraRestoreMultiAfterPip',
    'onPictureInPictureModeChanged','onMultiWindowModeChanged','onConfigurationChanged',
    'cobraApplyPlayerRotation','cobraApplyDisplayPerformance','cobraBuildPlayerChrome',
    'cobraUpdateTimeshiftSeek','cobraFitCaptions','cobraFitBinding','cobraAttachVideo',
    'cobraSavePreferences','applyCobraAspectTransform','showSettings',
    'cobraRenderMovieDetailPage','cobraRenderSeriesDetailPage'
]
PROTECTED_CLASSES=[
    'CobraLayoutMath','CobraTimelineNormalizerPolicy','CobraProviderPacePolicy',
    'CobraTimeshiftTransportPolicy','CobraNetworkFamilyPolicy'
]

POLICY=r'''  static final class CobraFoldAspectPolicy {
    // Mode 12 is the saved legacy Fold Adaptive value. Its whole-frame behavior
    // remains unchanged and is now presented as Fold Fit.
    static final int MODE=12;
    static final int FIT_MODE=MODE;
    static final int FILL_MODE=13;
    static final int MAX_MODE=FILL_MODE;

    static boolean foldMode(int mode){return mode==FIT_MODE||mode==FILL_MODE;}

    static float[] fit(int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      if(videoWidth<=0||videoHeight<=0||viewportWidth<=0||viewportHeight<=0)return new float[]{1f,1f};
      float source=videoWidth*(pixelRatio>0?pixelRatio:1f)/videoHeight;
      float view=(float)viewportWidth/viewportHeight;
      float sx=source<view?source/view:1f,sy=source>view?view/source:1f;
      return new float[]{sx,sy};
    }

    static float[] fill(int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      if(videoWidth<=0||videoHeight<=0||viewportWidth<=0||viewportHeight<=0)return new float[]{1f,1f};
      float[] fit=fit(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight);
      // The fit transform already preserves source proportions. Scaling both axes
      // by the smallest factor that removes every uncovered edge produces the
      // unique minimum proportional center crop for this exact pane.
      float zoom=Math.max(1f/fit[0],1f/fit[1]);
      return new float[]{fit[0]*zoom,fit[1]*zoom};
    }

    // Compatibility for inherited mode-12 Fold Adaptive tests and saved settings.
    static float[] scale(int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      return fit(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight);
    }

    static float[] scaleForMode(int mode,int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      return mode==FILL_MODE?fill(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight)
          :fit(videoWidth,videoHeight,pixelRatio,viewportWidth,viewportHeight);
    }
  }'''

def patch_activity(path:Path):
    before_b=path.read_bytes();req(hb(before_b)==PARENT_ACTIVITY,'Not exact locked 2103225 Activity preimage')
    s=before_b.decode()
    protected_methods=hashes(s,PROTECTED_METHODS)
    protected_classes=hashes(s,PROTECTED_CLASSES,'class')

    # The old Fold Adaptive policy is the exact approved whole-frame fit. Mode 12
    # stays the same value and implementation contract; add the paired Fill mode.
    old_policy=member(s,'CobraFoldAspectPolicy','class')
    req('static final int MODE=12;' in old_policy,'Legacy Fold mode changed')
    req('return new float[]{sx,sy};' in old_policy,'Legacy Fold Fit math changed')
    s=replace_member(s,'CobraFoldAspectPolicy',POLICY,'class')

    label=member(s,'cobraAspectLabel')
    label=once(label,'      case 12: return "Fold Adaptive";',
               '      case 12: return "Fold Fit";\n      case 13: return "Fold Fill";',
               'Fold labels')
    s=replace_member(s,'cobraAspectLabel',label)

    picker=member(s,'showCobraAspectPicker')
    picker=once(picker,
'''    LinearLayout rows=cobraOpenSheet("Aspect / Display","Fold Adaptive automatically follows the usable screen size without restarting playback","aspect");
    final int[] modes={CobraFoldAspectPolicy.MODE,0,1,2,3,4,5,6,7,8,9,10,11};
    for(int mode:modes){final int selected=mode;String label=selected==CobraFoldAspectPolicy.MODE?"Fold Adaptive":cobraAspectLabel(selected);
      rows.addView(cobraSheetRow("aspect",label,mAspectMode==selected?"Selected":null,false,true,()->{''',
'''    LinearLayout rows=cobraOpenSheet("Aspect / Display","Fold Fit keeps the whole frame. Fold Fill fills the current video pane with the minimum center crop. Both follow cover/inner, rotation and window changes without restarting playback.","aspect");
    final int[] modes={CobraFoldAspectPolicy.FIT_MODE,CobraFoldAspectPolicy.FILL_MODE,0,1,2,3,4,5,6,7,8,9,10,11};
    for(int mode:modes){final int selected=mode;String label=cobraAspectLabel(selected);
      String detail=selected==CobraFoldAspectPolicy.FIT_MODE?"Whole frame • no crop":selected==CobraFoldAspectPolicy.FILL_MODE?"Fill pane • minimum center crop":null;
      rows.addView(cobraSheetRow("aspect",label,mAspectMode==selected?"Selected":detail,false,true,()->{''',
               'Aspect picker Fold pair')
    s=replace_member(s,'showCobraAspectPicker',picker)

    channel=member(s,'cobraShowChannelAspect')
    channel=once(channel,
'''    final int[] modes={CobraFoldAspectPolicy.MODE,-1,0,1,2,3,4,5,6,7,8,9,10,11};
    for(int value:modes){final int selected=value;cobraAddDetail(rows,"aspect",selected<0?"Inherit default":cobraAspectLabel(selected),null,"cobra-channel-aspect:"+selected,prefs.aspect==selected,()->{''',
'''    final int[] modes={CobraFoldAspectPolicy.FIT_MODE,CobraFoldAspectPolicy.FILL_MODE,-1,0,1,2,3,4,5,6,7,8,9,10,11};
    for(int value:modes){final int selected=value;
      String detail=selected==CobraFoldAspectPolicy.FIT_MODE?"Whole frame • no crop":selected==CobraFoldAspectPolicy.FILL_MODE?"Fill pane • minimum center crop":null;
      cobraAddDetail(rows,"aspect",selected<0?"Inherit default":cobraAspectLabel(selected),detail,"cobra-channel-aspect:"+selected,prefs.aspect==selected,()->{''',
               'Channel Fold pair')
    s=replace_member(s,'cobraShowChannelAspect',channel)

    # Mode 13 must survive both global and per-channel preference sanitization.
    s=once(s,
        '    static int aspect(int value){return value>=-1&&value<=CobraFoldAspectPolicy.MODE?value:-1;}',
        '    static int aspect(int value){return value>=-1&&value<=CobraFoldAspectPolicy.MAX_MODE?value:-1;}',
        'Channel preference Fold Fill persistence')

    global_mode=member(s,'cobraChannelAspect')
    global_mode=once(global_mode,
        '    int mode=mPrefs.getInt(COBRA_ASPECT_MODE,0);return mode>=0&&mode<=CobraFoldAspectPolicy.MODE?mode:0;',
        '    int mode=mPrefs.getInt(COBRA_ASPECT_MODE,0);return mode>=0&&mode<=CobraFoldAspectPolicy.MAX_MODE?mode:0;',
        'Global Fold Fill persistence')
    s=replace_member(s,'cobraChannelAspect',global_mode)

    defaults=member(s,'cobraShowPlaybackDefaults')
    defaults=once(defaults,
        '      LinearLayout choices=cobraOpenSheet("Default fullscreen aspect","Inherited in fullscreen. Previews keep Best Fit unless the channel overrides it.","default-aspect");',
        '      LinearLayout choices=cobraOpenSheet("Default fullscreen aspect","Inherited in fullscreen. Previews keep Best Fit. Multi-View tiles inherit Fold Fit / Fold Fill unless a channel overrides them.","default-aspect");',
        'Default aspect description')
    defaults=once(defaults,
        '      final int[] modes={CobraFoldAspectPolicy.MODE,0,1,2,3,4,5,6,7,8,9,10};',
        '      final int[] modes={CobraFoldAspectPolicy.FIT_MODE,CobraFoldAspectPolicy.FILL_MODE,0,1,2,3,4,5,6,7,8,9,10};',
        'Default Fold pair')
    s=replace_member(s,'cobraShowPlaybackDefaults',defaults)

    # Multi-View: only the two Fold modes inherit globally. All other historic
    # global aspect modes keep the existing preview/Multi-View Best Fit behavior.
    anchor='  private int cobraBindingAspect(CobraPlayerBinding binding){'
    req(s.count(anchor)==1,'Binding aspect insertion drift')
    helper='''  private boolean cobraMultiViewPlayer(ExoPlayer player){
    if(player==null||mMultiPlayers==null)return false;
    for(ExoPlayer multi:mMultiPlayers)if(multi==player)return true;
    return false;
  }

'''
    s=s.replace(anchor,helper+anchor,1)
    binding=member(s,'cobraBindingAspect')
    binding=once(binding,
'''    int mode=binding.player==mPlayer?cobraChannelAspect(binding.channel):0;
    if(binding.vitals.live&&binding.vitals.preferences.aspect>=0)mode=binding.vitals.preferences.aspect;
    return mode;''',
'''    int global=mPrefs.getInt(COBRA_ASPECT_MODE,0);
    if(global<0||global>CobraFoldAspectPolicy.MAX_MODE)global=0;
    int mode=binding.player==mPlayer?cobraChannelAspect(binding.channel)
        :cobraMultiViewPlayer(binding.player)&&CobraFoldAspectPolicy.foldMode(global)?global:0;
    if(binding.vitals.live&&binding.vitals.preferences.aspect>=0)mode=binding.vitals.preferences.aspect;
    return mode;''',
        'Multi-View Fold inheritance')
    s=replace_member(s,'cobraBindingAspect',binding)

    fit=member(s,'cobraFitVideo')
    fit=once(fit,
'''    float[] scale=mode==CobraFoldAspectPolicy.MODE
        ?CobraFoldAspectPolicy.scale(size.width,size.height,size.pixelWidthHeightRatio,texture.getWidth(),texture.getHeight())
        :CobraLayoutMath.fit(size.width,size.height,size.pixelWidthHeightRatio,
            texture.getWidth(),texture.getHeight(),mode,customX,customY);''',
'''    float[] scale=CobraFoldAspectPolicy.foldMode(mode)
        ?CobraFoldAspectPolicy.scaleForMode(mode,size.width,size.height,size.pixelWidthHeightRatio,texture.getWidth(),texture.getHeight())
        :CobraLayoutMath.fit(size.width,size.height,size.pixelWidthHeightRatio,
            texture.getWidth(),texture.getHeight(),mode,customX,customY);''',
        'Fold Fit Fill transform dispatch')
    s=replace_member(s,'cobraFitVideo',fit)

    # Strong negative gate: switching display modes must stay presentation-only.
    forbidden=('setMediaItem','prepare()','release()','seekTo(','stop()','playChannel(','playVodUrl(','startSinglePlayer(','cobraRestartLiveChannel(')
    for name in ('showCobraAspectPicker','cobraShowChannelAspect','cobraFitVideo','cobraBindingAspect','cobraMultiViewPlayer'):
        block=member(s,name)
        for token in forbidden:req(token not in block,f'Playback mutation leaked into {name}: {token}')

    # Existing PiP Best Fit and geometry-reflow ownership must remain byte-identical.
    for n,h in protected_methods.items():req(hb(member(s,n))==h,'Protected method changed: '+n)
    for n,h in protected_classes.items():req(hb(member(s,n,'class'))==h,'Protected class changed: '+n)

    required=(
        'static final int MODE=12','static final int FIT_MODE=MODE','static final int FILL_MODE=13',
        'static final int MAX_MODE=FILL_MODE','case 12: return "Fold Fit"','case 13: return "Fold Fill"',
        'final int[] modes={CobraFoldAspectPolicy.FIT_MODE,CobraFoldAspectPolicy.FILL_MODE,0,1',
        'final int[] modes={CobraFoldAspectPolicy.FIT_MODE,CobraFoldAspectPolicy.FILL_MODE,-1,0,1',
        'value<=CobraFoldAspectPolicy.MAX_MODE','mode<=CobraFoldAspectPolicy.MAX_MODE',
        'CobraFoldAspectPolicy.scaleForMode','cobraMultiViewPlayer(binding.player)',
        'texture.addOnLayoutChangeListener(binding.layoutListener)','mInPictureInPicture?0:mode',
        'String[] glyphs={"guide","aspect","multi","more"}'
    )
    for token in required:req(token in s,'2103226 contract missing: '+token)

    path.write_text(s)
    after=sha(path)
    return {
        'activity_before_sha256':hb(before_b),'activity_after_sha256':after,
        'protected_methods_sha256':protected_methods,'protected_classes_sha256':protected_classes,
        'fold_policy_before_sha256':hb(old_policy),'fold_policy_after_sha256':hb(member(s,'CobraFoldAspectPolicy','class')),
        'modified_methods':[
            'cobraAspectLabel','showCobraAspectPicker','cobraShowChannelAspect',
            'cobraChannelAspect','cobraShowPlaybackDefaults','cobraBindingAspect',
            'cobraFitVideo','CobraPreferencePolicy.aspect'
        ],
        'added_methods':['cobraMultiViewPlayer'],
    }

def patch_identity(shell:Path):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime release');runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'packager identity drift');pack.write_text(p.replace(old,new));return gradle

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103225 replay')
    req(receipt.get('native_engine_sha256')==NATIVE,'Native engine receipt drift')

    activity=shell/ACT;splash=shell/(SOURCE+'Splash.java.in');smart=shell/(SOURCE+'CobraSmartReturn.java.in');main=shell/(SOURCE+'Main.java.in');renderer=shell/(SOURCE+'CobraVisualRenderer.java.in')
    for p in (activity,splash,smart,main,renderer):req(p.is_file(),'Missing '+str(p))
    frozen={'splash':sha(splash),'smart_return':sha(smart),'main':sha(main),'visual_renderer':sha(renderer)}

    scope=patch_activity(activity);gradle=patch_identity(shell)

    req(sha(splash)==frozen['splash'],'Choose Your Experience/Health changed')
    req(sha(smart)==frozen['smart_return'],'Smart Return changed')
    req(sha(main)==frozen['main'],'Kodi Main changed')
    req(sha(renderer)==frozen['visual_renderer'],'Global visual renderer changed')

    for name in (ACT,SOURCE+'Splash.java.in',SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
        req(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
    rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)

    receipt.update(
        version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
        candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
        native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
        fold_fit_fill_audited=True,fold_fit_mode=12,fold_fill_mode=13,
        fold_mode12_behavior_preserved=True,fold_fill_minimum_center_crop=True,
        fold_viewport_reactive=True,fold_cover_inner_reactive=True,fold_rotation_reactive=True,
        fold_multi_view_reactive=True,fold_pip_best_fit_preserved=True,
        player_recreated_on_fold_switch=False,retune_on_fold_switch=False,seek_on_fold_switch=False,
        timeshift_unchanged=True,audio_unchanged=True,providers_unchanged=True,playback_unchanged=True,
        movie_tv_details_unchanged=True,tv_show_typography_unchanged=True,
        live_tv_transport_unchanged=True,drawer_owner_preserved=True,smart_return_preserved=True,
        choose_experience_ui_unchanged=True,health_center_unchanged=True,global_visual_renderer_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Receipt drift '+name)

    Path('audit226').mkdir(exist_ok=True)
    scope.update({
        'build':VERSION,'parent':OLD_VERSION,'parent_locked_branch':'locked-infinity-cobra-2103225-tv-show-typography-passed',
        'preaudit_run':PREAUDIT_RUN,'preaudit_activity_sha256':PARENT_ACTIVITY,
        'authorized_delta':'Fold Fit / Fold Fill presentation modes + Fold-mode Multi-View inheritance only',
        'frozen_files_sha256':frozen,'native_engine_sha256':NATIVE,'native_engine_rebuilt':False,
        'fold_fit':{'mode':12,'legacy_mode12_value_preserved':True,'whole_frame':True,'crop':False},
        'fold_fill':{'mode':13,'proportional':True,'minimum_center_crop':True,'fills_measured_pane':True},
        'reactivity':['cover/inner viewport','portrait/landscape','multi-window','fullscreen drawer resize','Multi-View tile resize'],
        'pip':'existing Best Fit forced by mInPictureInPicture path',
        'switching':{'player_recreated':False,'retune':False,'seek':False,'audio_interrupt':False,'timeshift_reset':False},
        'physical_device_verified':False,'status':'TEST CANDIDATE'
    })
    Path('audit226/scope.json').write_text(json.dumps(scope,indent=2,sort_keys=True)+'\n')
    print('PASS: 2103226 Fold Fit / Fold Fill applied over exact locked 2103225 with playback ownership protected')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
