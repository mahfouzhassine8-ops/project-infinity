#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103193
BASE_NAME='1.0.9-Cobra-Source-Manager-Restore-RC1'
BASE_COMMIT='65cee6f8fdc60757a1e9bdaaac113be1ea344a2c'

def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
    c=s.count(a)
    if c!=1: raise RuntimeError(f'{label}: expected one anchor, got {c}')
    return s.replace(a,b,1)
def matches(text,name,kind='method'):
    if kind=='method':
        return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
    return list(re.finditer(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',text,re.M))
def span(text,name,kind='method'):
    ms=matches(text,name,kind)
    if len(ms)!=1: raise RuntimeError(f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False;i+=1
        elif q:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q:q=None
        elif c=='/' and n=='/': line=True;i+=1
        elif c=='/' and n=='*': block=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)
def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+'\n'+text[b:]

FOLD_POLICY=r'''  static final class CobraFoldAspectPolicy {
    static final int MODE=12;
    static final float MAX_CROP=1.06f;
    static float[] scale(int videoWidth,int videoHeight,float pixelRatio,int viewportWidth,int viewportHeight){
      if(videoWidth<=0||videoHeight<=0||viewportWidth<=0||viewportHeight<=0)return new float[]{1f,1f};
      float source=videoWidth*(pixelRatio>0?pixelRatio:1f)/videoHeight;
      float view=(float)viewportWidth/viewportHeight;
      float sx=source<view?source/view:1f,sy=source>view?view/source:1f;
      // Fold Adaptive is conservative: preserve the entire frame on extreme/narrow
      // windows, and use only a tiny center crop on near-matching large viewports.
      float mismatch=Math.max(source/view,view/source);
      boolean roomy=Math.min(viewportWidth,viewportHeight)>=600;
      if(roomy&&mismatch<=1.18f){
        float z=Math.min(MAX_CROP,Math.max(1f/sx,1f/sy));sx*=z;sy*=z;
      }
      return new float[]{sx,sy};
    }
  }'''

def apply(source,receipt_path,out):
    source=Path(source);out=Path(out);receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('version_code')!=BASE_BUILD or receipt.get('version_name')!=BASE_NAME:
        raise RuntimeError('Expected exact passed 2103193 source receipt')
    path=source/ACT;before_b=path.read_bytes();before=before_b.decode()
    expected=receipt.get('files',{}).get(str(ACT),{}).get('after')
    if not expected or sha(before_b)!=expected: raise RuntimeError('2103193 Activity preimage mismatch')
    text=before

    protected_methods=[
      'buildPlayer','cobraStartLocalTimeshift','cobraStartLocalTimeshiftPreview','cobraWatchTimeshiftReady','cobraActivateLocalTimeshift',
      'cobraRewindLive','cobraGoLive','cobraStopLocalTimeshift','cobraDisposePlayer','cobraUpdateTimeshiftSeek','cobraStartProviderCatchup',
      'showCobraDiagnosticExport','cobraCapturePreviewDiagnostics','cobraDiagnosticSnapshotForExport','onStop','onPictureInPictureModeChanged',
      'cobraHandleAudioFocus','cobraClaimAudioFocus','cobraApplyDisplayPerformance','cobraTuneLastChannel',
      'showSources','showSourceActions','chooseSourceType','loadActiveSource','loadAllEnabledSources','editCustomEpg','showProfiles'
    ]
    method_guards={n:sha(member(before,n)) for n in protected_methods}
    class_guards={n:sha(member(before,n,'class')) for n in [
      'CobraNetworkFamilyPolicy','CobraDiagnosticFreezePolicy','CobraStreamCadencePolicy','CobraTsParserPolicy',
      'CobraTsTimelinePolicy','CobraTimelineNormalizerPolicy','CobraProviderPacePolicy'
    ]}

    # New presentation-only policy beside the existing layout math.
    a,b=span(text,'CobraLayoutMath','class')
    text=text[:b]+'\n\n'+FOLD_POLICY+text[b:]

    label=member(text,'cobraAspectLabel')
    label=once(label,'    switch (mode) {','    switch (mode) {\n      case 12: return "Fold Adaptive";','Fold Adaptive label')
    text=replace_member(text,'cobraAspectLabel',label)

    channel_aspect=member(text,'cobraShowChannelAspect')
    channel_aspect=once(channel_aspect,
      '    for(int i=-1;i<=11;i++){final int value=i;cobraAddDetail(rows,"aspect",i<0?"Inherit default":cobraAspectLabel(i),null,"cobra-channel-aspect:"+i,prefs.aspect==i,()->{\n      CobraChannelPreferences p=cobraReadPreferences(key);p.aspect=value;if(cobraSavePreferences(channel,key,p,false)){if(value==11)cobraShowChannelCustomAspect(channel);else cobraShowChannelPreferences(channel);}\n    });}',
      '''    final int[] modes={CobraFoldAspectPolicy.MODE,-1,0,1,2,3,4,5,6,7,8,9,10,11};
    for(int value:modes){final int selected=value;cobraAddDetail(rows,"aspect",selected<0?"Inherit default":cobraAspectLabel(selected),null,"cobra-channel-aspect:"+selected,prefs.aspect==selected,()->{
      CobraChannelPreferences p=cobraReadPreferences(key);p.aspect=selected;if(cobraSavePreferences(channel,key,p,false)){if(selected==11)cobraShowChannelCustomAspect(channel);else cobraShowChannelPreferences(channel);}
    });}''',
      'channel aspect ordering')
    text=replace_member(text,'cobraShowChannelAspect',channel_aspect)

    picker=member(text,'showCobraAspectPicker')
    picker=once(picker,
      '    LinearLayout rows=cobraOpenSheet("Aspect / Display","Best Fit preserves the source proportions","aspect");\n    for(int i=0;i<12;i++){final int mode=i;rows.addView(cobraSheetRow("aspect",cobraAspectLabel(i),mAspectMode==i?"Selected":null,false,true,()->{\n      mAspectMode=mode;mPrefs.edit().putInt(COBRA_ASPECT_MODE,mode).apply();applyCobraAspectTransform();if(mode==11)showCobraCustomAspectEditor();}));}',
      '''    LinearLayout rows=cobraOpenSheet("Aspect / Display","Fold Adaptive automatically follows the usable screen size without restarting playback","aspect");
    final int[] modes={CobraFoldAspectPolicy.MODE,0,1,2,3,4,5,6,7,8,9,10,11};
    for(int mode:modes){final int selected=mode;String label=selected==CobraFoldAspectPolicy.MODE?"Fold Adaptive":cobraAspectLabel(selected);
      rows.addView(cobraSheetRow("aspect",label,mAspectMode==selected?"Selected":null,false,true,()->{
        mAspectMode=selected;mPrefs.edit().putInt(COBRA_ASPECT_MODE,selected).apply();applyCobraAspectTransform();if(selected==11)showCobraCustomAspectEditor();}));}''',
      'aspect picker ordering')
    text=replace_member(text,'showCobraAspectPicker',picker)

    fit=member(text,'cobraFitVideo')
    fit=once(fit,
      '    float[] scale=CobraLayoutMath.fit(size.width,size.height,size.pixelWidthHeightRatio,\n        texture.getWidth(),texture.getHeight(),mode,customX,customY);',
      '''    float[] scale=mode==CobraFoldAspectPolicy.MODE
        ?CobraFoldAspectPolicy.scale(size.width,size.height,size.pixelWidthHeightRatio,texture.getWidth(),texture.getHeight())
        :CobraLayoutMath.fit(size.width,size.height,size.pixelWidthHeightRatio,
            texture.getWidth(),texture.getHeight(),mode,customX,customY);''',
      'fold adaptive fit')
    text=replace_member(text,'cobraFitVideo',fit)

    # Ensure the full-screen texture reacts to cover/inner/split-window geometry changes
    # without player replacement. The binding listener already does this for attached peers.
    build=member(text,'cobraBuildPlayerChrome')
    # Existing player texture listener is installed during player UI construction; add no player operation here.
    # We intentionally rely on the already-proven TextureView/layout listener and applyCobraAspectTransform path.

    for n,h in method_guards.items():
        if sha(member(text,n))!=h: raise RuntimeError('Protected playback/source owner changed: '+n)
    for n,h in class_guards.items():
        if sha(member(text,n,'class'))!=h: raise RuntimeError('Protected class changed: '+n)

    required=[
      'CobraFoldAspectPolicy','static final int MODE=12','case 12: return "Fold Adaptive"','Fold Adaptive','final int[] modes={CobraFoldAspectPolicy.MODE,0,1','final int[] modes={CobraFoldAspectPolicy.MODE,-1,0,1',
      'mode==CobraFoldAspectPolicy.MODE','mPlayerTexture.addOnLayoutChangeListener','applyCobraAspectTransform()',
      'cobra_tv_sources','timeshift_provider_pace_limited','REWRITE_ENABLED=false','DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES',
      'cobra_unified_live_timeline','CobraCallAudioPolicy','buffer_observed_no_restart'
    ]
    for token in required:
        if token not in text: raise RuntimeError('2103194 contract missing: '+token)

    after=text.encode();path.write_bytes(after);out.mkdir(parents=True,exist_ok=True);(out/'source-before').mkdir(exist_ok=True);(out/'source-before'/path.name).write_bytes(before_b)
    report={
      'base_build':BASE_BUILD,'base_commit':BASE_COMMIT,'files':{str(ACT):{'before':sha(before_b),'after':sha(after)}},
      'fold_adaptive_aspect':True,'fold_adaptive_mode':12,'fold_adaptive_first_choice':True,'fold_adaptive_max_crop':1.06,
      'fold_adaptive_reacts_to_viewport':True,'player_recreated_on_resize':False,'pip_authority_preserved':True,
      'source_manager_route_preserved':True,'playback_behavior_changed':False,'network_selection_changed':False,
      'timeshift_ownership_changed':False,'buffer_policy_changed':False,'parser_flags_changed':False,'clock_rewrite_changed':False,
      'native_changed':False,'theme_zip_changed':False,'physical_device_verified':False
    }
    (out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 2103194 Fold Adaptive added as first aspect choice over exact passed 2103193; protected playback/source stack preserved')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.receipt,a.out)
