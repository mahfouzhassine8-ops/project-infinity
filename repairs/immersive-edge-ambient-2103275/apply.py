#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,shutil

ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
RENDERER='tools/android/packaging/xbmc/src/CobraVisualRenderer.java.in'
IMMERSIVE='tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java.in'
PROUI='tools/android/packaging/xbmc/src/CobraProUi.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'\nINSTALL='cmake/scripts/android/Install.cmake'
CMAKE='cmake/scripts/android/Install.cmake'
PARENT_ACTIVITY_SHA='ab7bf1619090df8aa8fb5cff77a3e16ad1b503d1e45b26736fb959000c65915c'
PARENT_RENDERER_SHA='6d6d2a7d48a49bcd6fc646374339914e761c8cc73dfbf68acf3c892088dc5df0'
PARENT_PROUI_SHA='2ef9662b7cf2cb6b52ba686d6b04b37da9098a893393630ff5bc0720ef66d945'\nPARENT_INSTALL_SHA='809c8d60f539c743afb8d7a85c09f1517fb1cd6ec9912ff24dfa38d96590129d'\nAFTER_INSTALL_SHA='b7ecd52d6ae857c5dce4b9e4301d6d684b1a7c446e87d410151ec8c3d9cc926d'
PARENT_CMAKE_SHA='809c8d60f539c743afb8d7a85c09f1517fb1cd6ec9912ff24dfa38d96590129d'
AFTER_ACTIVITY_SHA='0ed5f50992bf637bd31ff7c4c299fc4837f5ae0ed3169a687511eec8ed07643c'
AFTER_RENDERER_SHA='d4eecc66ee0d021eca32b8c2edd9337c53da9eb58c1a18c9f0a79df566c1537d'
AFTER_CMAKE_SHA='4368634f2bd1fc17aa063b6961daeb0beb24f4ed9b22aed96233609b73c27eea'
PARENT_APK='c07f9f8872d7be892a3e0877ec129a893cbe2c106e3af33ca69b2e300b594e12'
PARENT_COMMIT='469afd4f2da4347ded4000164c48bf658a23fb33'
PARENT_RUN=36775670821
VERSION_CODE=2103275
RELEASE='1.0.9-Immersive-Edge-Ambient-RC1'


def sha(data): return hashlib.sha256(data).hexdigest()
def once(s,o,n,label='anchor'):
    c=s.count(o)
    if c!=1: raise AssertionError(f'{label}: expected one preimage, found {c}: {o[:120]!r}')
    return s.replace(o,n,1)

def patch_activity(s):
    s=once(s,'  private FrameLayout mCobraPreviewHost;\n','  private FrameLayout mCobraPreviewHost;\n  private CobraImmersiveAmbient mCobraImmersiveAmbient;\n','field')
    s=once(s,'    mCobraRotationResumed=true;cobraApplyPlayerRotation("resume");cobraApplyDisplayPerformance("resume");cobraSyncPerformanceOverlay();\n','    mCobraRotationResumed=true;cobraApplyPlayerRotation("resume");cobraApplyDisplayPerformance("resume");cobraSyncPerformanceOverlay();cobraRefreshImmersiveAmbient();\n','resume')
    s=once(s,'    mCobraPlaybackPolicy.pause();\n    super.onPause();\n','    mCobraPlaybackPolicy.pause();cobraSuspendImmersiveAmbient();\n    super.onPause();\n','pause')
    s=once(s,'    cobraApplyDisplayPerformance("pip");cobraSyncPerformanceOverlay();\n}','    cobraApplyDisplayPerformance("pip");cobraSyncPerformanceOverlay();cobraRefreshImmersiveAmbient();\n}','pip')
    s=once(s,'    return CobraPresentationEffects.ambientColor(key,cobraBuiltInAppearanceColor(mode,key,fallback),cobraAmbientMode(),mCobraAmbientTint);\n','    return CobraPresentationEffects.ambientColor(key,cobraBuiltInAppearanceColor(mode,key,fallback),cobraStaticAmbientMode(),mCobraAmbientTint);\n','theme color')
    s=once(s,'    if(view!=null)view.setContentDescription(wants?"Pause preview":"Play preview");\n  }','    if(view!=null)view.setContentDescription(wants?"Pause preview":"Play preview");\n    cobraRefreshImmersiveAmbient();\n  }','play pause')
    s=once(s,'    if(mCobraPreviewTexture!=null)mCobraPreviewTexture.setVisibility(View.INVISIBLE);\n  }','    if(mCobraPreviewTexture!=null)mCobraPreviewTexture.setVisibility(View.INVISIBLE);\n    cobraRefreshImmersiveAmbient();\n  }','stop preview')
    s=once(s,'    stopCobraPreviewPlayerOnly();mCobraPreviewTexture=null;mCobraPreviewHost=null;\n    mCobraGuideShell=null;mCobraGuideVideo=null;mCobraGuideAdapter=null;mCobraGuideList=null;\n','    stopCobraPreviewPlayerOnly();mCobraPreviewTexture=null;mCobraPreviewHost=null;\n    if(mCobraImmersiveAmbient!=null){mCobraImmersiveAmbient.release();mCobraImmersiveAmbient=null;}\n    mCobraGuideShell=null;mCobraGuideVideo=null;mCobraGuideAdapter=null;mCobraGuideList=null;\n','release')
    s=once(s,'    cobraEndMiniBackgroundPlayback();mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";mCobraPreviewHandoffs++;\n','    cobraEndMiniBackgroundPlayback();mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";mCobraPreviewHandoffs++;cobraRefreshImmersiveAmbient();\n','fullscreen handoff')
    s=once(s,'    configureCobraPip(false);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();\n','    configureCobraPip(false);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();cobraRefreshImmersiveAmbient();\n','fullscreen return')
    s=once(s,'      };mCobraGuideShell.setTag("cobra_persistent_guide_shell");\n      mCobraGuideVideo=cobraPreviewPanel(mGuidePreviewChannel,true);\n      mCobraGuideShell.addView(mCobraGuideVideo,new FrameLayout.LayoutParams(1,1));\n','      };mCobraGuideShell.setTag("cobra_persistent_guide_shell");\n      mCobraImmersiveAmbient=new CobraImmersiveAmbient(this);\n      mCobraGuideShell.addView(mCobraImmersiveAmbient,new FrameLayout.LayoutParams(-1,-1));\n      mCobraGuideVideo=cobraPreviewPanel(mGuidePreviewChannel,true);\n      mCobraGuideShell.addView(mCobraGuideVideo,new FrameLayout.LayoutParams(1,1));\n','guide z order')
    s=once(s,'    cobraRefreshProgrammeLabels();cobraStartPresentationTicker();\n','    cobraRefreshProgrammeLabels();cobraStartPresentationTicker();cobraRefreshImmersiveAmbient();\n','guide refresh')
    s=once(s,'    updateCobraPreviewPlayPause();cobraRefreshProgrammeLabels();\n  }\n  private void cobraStartLocalTimeshiftPreview','    updateCobraPreviewPlayPause();cobraRefreshProgrammeLabels();cobraRefreshImmersiveAmbient();\n  }\n  private void cobraStartLocalTimeshiftPreview','direct preview')
    s=once(s,'    updateCobraPreviewPlayPause();cobraRefreshProgrammeLabels();\n  }\n\n\n\n  private void cobraWatchTimeshiftReady','    updateCobraPreviewPlayPause();cobraRefreshProgrammeLabels();cobraRefreshImmersiveAmbient();\n  }\n\n\n\n  private void cobraWatchTimeshiftReady','timeshift preview')
    old='''  private View cobraCurrentSheetPanel(){\n    if(!(mCobraActionSheet instanceof android.view.ViewGroup))return null;\n    android.view.ViewGroup group=(android.view.ViewGroup)mCobraActionSheet;\n    return group.getChildCount()>0?group.getChildAt(0):null;\n  }\n\n'''
    new=old+'''  private boolean cobraImmersiveAmbientEligible(){\n    int mode=mPrefs==null?CobraPresentationEffects.OFF:CobraPresentationEffects.ambientMode(mPrefs);\n    boolean shell=mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow();\n    boolean host=mCobraPreviewHost!=null&&mCobraPreviewHost.isAttachedToWindow()&&mCobraPreviewHost.isShown();\n    boolean texture=mCobraPreviewTexture!=null&&mCobraPreviewTexture.isAvailable()&&mCobraPreviewTexture.isShown();\n    return CobraImmersiveAmbient.eligible(mode,cobraVisualEffectsAllowed(),mPlayerOverlay!=null,mMultiOverlay!=null,\n        mInPictureInPicture||isCobraInPictureInPicture(),mCobraMiniBackgroundActive||mBackgroundStopped,\n        shell,host,texture,mCobraPreviewPlayer!=null);\n  }\n  private int cobraStaticAmbientMode(){\n    int mode=cobraAmbientMode();\n    // Immersive owns its rich colour field through the frame renderer. Keep only a\n    // restrained glass tint so the old uniform live-blue wash cannot muddy the projection.\n    return mode==CobraPresentationEffects.IMMERSIVE&&cobraImmersiveAmbientEligible()?CobraPresentationEffects.SUBTLE:mode;\n  }\n  private void cobraSuspendImmersiveAmbient(){\n    if(mCobraImmersiveAmbient!=null)mCobraImmersiveAmbient.state(false,false);\n  }\n  private void cobraRefreshImmersiveAmbient(){\n    CobraImmersiveAmbient ambient=mCobraImmersiveAmbient;\n    if(ambient==null)return;\n    boolean active=cobraImmersiveAmbientEligible();\n    if(mCobraPreviewTexture!=null&&mCobraPreviewHost!=null)ambient.bind(mCobraPreviewTexture,mCobraPreviewHost,!cobraModeDark());\n    boolean moving=false;\n    if(active&&mCobraPreviewPlayer!=null)try{moving=mCobraPreviewPlayer.isPlaying()||mCobraPreviewPlayer.getPlayWhenReady();}catch(RuntimeException ignored){}\n    ambient.state(active,moving);\n  }\n\n'''
    s=once(s,old,new,'ambient helpers')
    s=once(s,'  private void cobraRefreshAmbient(){\n    if(mCobraEffects==null)return;\n    int mode=cobraAmbientMode();\n    boolean live=cobraLiveAmbientContext();\n','  private void cobraRefreshAmbient(){\n    if(mCobraEffects==null)return;\n    int mode=cobraAmbientMode();\n    boolean reactive=mode==CobraPresentationEffects.IMMERSIVE&&cobraImmersiveAmbientEligible();\n    int staticMode=reactive?CobraPresentationEffects.SUBTLE:mode;\n    int backdropMode=reactive?CobraPresentationEffects.OFF:mode;\n    boolean live=cobraLiveAmbientContext();\n','ambient refresh head')
    s=once(s,'    mCobraEffects.backdrop(mCobraBrowseBackground,cobraThemeColor("background",mTheme.background),mCobraAmbientTint,mode);\n    mCobraEffects.backdrop(mCobraGuideShell,cobraModeColor("background"),live?COBRA_LIVE_AMBIENT_BLUE:mCobraAmbientTint,mode);\n','    mCobraEffects.backdrop(mCobraBrowseBackground,cobraThemeColor("background",mTheme.background),mCobraAmbientTint,backdropMode);\n    mCobraEffects.backdrop(mCobraGuideShell,cobraModeColor("background"),live?COBRA_LIVE_AMBIENT_BLUE:mCobraAmbientTint,backdropMode);\n','backdrop')
    s=once(s,'    cobraRefreshLiveAmbientSurfaces(mode,live,mCobraAmbientTint);\n','    cobraRefreshLiveAmbientSurfaces(staticMode,live,mCobraAmbientTint);\n','ambient surfaces')
    s=once(s,'    cobraRefreshGlassTree(mCobraGuideShell,mode,false);\n','    cobraRefreshGlassTree(mCobraGuideShell,staticMode,false);\n','guide glass')
    s=once(s,'    if(mCobraModeToolbar!=null){View visuals=mCobraModeToolbar.findViewWithTag("cobra_mode_visuals");\n','    cobraRefreshImmersiveAmbient();\n    if(mCobraModeToolbar!=null){View visuals=mCobraModeToolbar.findViewWithTag("cobra_mode_visuals");\n','renderer refresh')
    s=once(s,'        i==0?"Use the current Cobra appearance":i==1?"Restrained contextual tint and lighting":"Richer contextual tint and lighting",\n','        i==0?"Use the current Cobra appearance":i==1?"Restrained contextual tint and lighting":"Live edge colours from the mini-player across the Cobra interface",\n','settings')
    s=once(s,'    for(int i=0;i<keys.length;i++){final String value=keys[i];cobraAddDetail(rows,"visuals",CobraPresentationEffects.ambientLabel(i),null,"cobra-visual-ambient:"+value,i==selected,()->{\n','    for(int i=0;i<keys.length;i++){final String value=keys[i];String detail=i==2?"Live mini-player edge colours • suspended in fullscreen, PiP and background":null;cobraAddDetail(rows,"visuals",CobraPresentationEffects.ambientLabel(i),detail,"cobra-visual-ambient:"+value,i==selected,()->{\n','visual menu')
    s=once(s,'    glass.effects(mCobraAmbientTint,cobraAmbientMode(),cobraNightCinemaActive()&&!light);return glass;\n','    glass.effects(mCobraAmbientTint,cobraStaticAmbientMode(),cobraNightCinemaActive()&&!light);return glass;\n','glass factory')
    return s

def patch_renderer(s):
    s=once(s,'if(view==null||CobraProUi.owns(view)||(view.getTag() instanceof String&&((String)view.getTag()).startsWith("cobra-visual-theme-controls"))||view instanceof TextureView||view instanceof SurfaceView||view instanceof android.webkit.WebView)return view;','if(view==null||CobraProUi.owns(view)||view instanceof CobraImmersiveAmbient||(view.getTag() instanceof String&&((String)view.getTag()).startsWith("cobra-visual-theme-controls"))||view instanceof TextureView||view instanceof SurfaceView||view instanceof android.webkit.WebView)return view;','renderer paint')
    s=once(s,'if(view==null||CobraProUi.owns(view)||depth>24||++count[0]>512||view instanceof TextureView||view instanceof SurfaceView||view instanceof android.webkit.WebView)return;','if(view==null||CobraProUi.owns(view)||view instanceof CobraImmersiveAmbient||depth>24||++count[0]>512||view instanceof TextureView||view instanceof SurfaceView||view instanceof android.webkit.WebView)return;','renderer tree')
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    shell=a.root/'shell-kodi';a.out.mkdir(parents=True,exist_ok=True)
    activity=shell/ACTIVITY;renderer=shell/RENDERER;pro=shell/PROUI;cmake=shell/CMAKE
    assert sha(activity.read_bytes())==PARENT_ACTIVITY_SHA,'Not exact locked 2103274 Activity'
    assert sha(renderer.read_bytes())==PARENT_RENDERER_SHA,'Not exact locked 2103274 renderer'
    assert sha(pro.read_bytes())==PARENT_PROUI_SHA,'Not exact locked 2103274 Pro UI'\n    install=shell/INSTALL;assert sha(install.read_bytes())==PARENT_INSTALL_SHA,'Not exact locked 2103274 Java registration'
    assert sha(cmake.read_bytes())==PARENT_CMAKE_SHA,'Not exact locked 2103274 Android source registration'
    activity.write_text(patch_activity(activity.read_text()))
    renderer.write_text(patch_renderer(renderer.read_text()))
    immersive_source=a.root/'repairs/immersive-edge-ambient-2103275/CobraImmersiveAmbient.java.in'
    shutil.copy2(immersive_source,shell/IMMERSIVE)
    c=cmake.read_text()
    c=once(c,'                  src/CobraProUi.java\n','                  src/CobraProUi.java\n                  src/CobraImmersiveAmbient.java\n','CMake source list')
    c=once(c,'configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraVisualRenderer.java.in\n               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraVisualRenderer.java @ONLY)\n','configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraVisualRenderer.java.in\n               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraVisualRenderer.java @ONLY)\n\nconfigure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java.in\n               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java @ONLY)\n','CMake configure_file')
    cmake.write_text(c)
    assert sha(activity.read_bytes())==AFTER_ACTIVITY_SHA,'Unexpected Activity result'
    assert sha(renderer.read_bytes())==AFTER_RENDERER_SHA,'Unexpected renderer result'
    assert (shell/IMMERSIVE).read_bytes()==immersive_source.read_bytes(),'Unexpected immersive renderer payload'
    assert sha(cmake.read_bytes())==AFTER_CMAKE_SHA,'Unexpected Android source registration result'
    gradle=shell/GRADLE;g=gradle.read_text();g=once(g,'versionCode 2103274','versionCode 2103275','version code');g=once(g,'versionName "1.0.9-Sports-Hub-Soccer-RC1"','versionName "1.0.9-Immersive-Edge-Ambient-RC1"','version name');gradle.write_text(g)
    script=a.root/'scripts/infinity_background_resume.py';v=script.read_text();v=once(v,'VERSION_CODE = 2103274','VERSION_CODE = 2103275');v=once(v,"RELEASE = '1.0.9-Sports-Hub-Soccer-RC1'",f"RELEASE = '{RELEASE}'");v=once(v,"BASE_COMMIT = '6a89688f3e61b8f2f66d9d4cef942cc506befffd'",f"BASE_COMMIT = '{PARENT_COMMIT}'");v=once(v,"BASE_APK_SHA256 = '0f35b65e3eb8c92e1966c8116bbccb3a55d09e368d1b59db02e9c8828d15dc3f'",f"BASE_APK_SHA256 = '{PARENT_APK}'");script.write_text(v)
    package=a.root/'scripts/package_background_resume.py';v=package.read_text();v=v.replace('Infinity-2103274-Sports-Hub-Soccer-RC1','Infinity-2103275-Immersive-Edge-Ambient-RC1');v=once(v,"'base_run':36770912528",f"'base_run':{PARENT_RUN}");v=once(v,"ROOT/'repairs/sports-hub-soccer-2103274/DEVICE-TEST.md'","ROOT/'repairs/immersive-edge-ambient-2103275/DEVICE-TEST.md'");package.write_text(v)
    receipt=a.root/'engine/background-resume-source.json';r=json.loads(receipt.read_text());r.update(base_source_commit=PARENT_COMMIT,base_apk_sha256=PARENT_APK,version_code=VERSION_CODE,release=RELEASE,candidate_locked=False,physical_device_verified=False,complete_product_audit=False,cobra_immersive_edge_ambient=True,cobra_immersive_sample_width=144,cobra_immersive_frame_interval_ms=83,cobra_immersive_directional_edges=True,cobra_immersive_all_view_modes=True,cobra_immersive_fullscreen_suspended=True,cobra_immersive_pip_suspended=True,cobra_immersive_background_suspended=True,cobra_off_preserved=True,cobra_subtle_preserved=True,x_ambient_mit_attribution=True,pro_sports_preserved=True,sports_repository_preserved=True,sports_channel_resolver_preserved=True,manual_multiview_preserved=True)
    for n in [ACTIVITY,RENDERER,IMMERSIVE,GRADLE,CMAKE]:r['files'].setdefault(n,{})['after']=sha((shell/n).read_bytes())
    receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print('Applied 2103275 native x-ambient-style edge projection to Cobra Immersive mini-player only; locked 2103274 playback/data owners preserved.')

if __name__=='__main__':main()
