#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re,shutil
HERE=Path(__file__).resolve().parent
BASE='88b733f2a25eca1873673c27b75b51021e4ef56b'
SOURCE_SHA='1a2fd49c2b9b324814fe4734c174957024b1113818cb2a4be88444c5066aee96'
APK_SHA=''
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
AMBIENT='tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
RELEASE='1.0.9-Whole-UI-Ambient-RC1'
def sha(data):return hashlib.sha256(data).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a))
 return s.replace(a,b,1)
def patch_activity(s):
 s=once(s,'    mRoot = new LinearLayout(this);','''    if(mCobraImmersiveAmbient!=null)mCobraImmersiveAmbient.release();
    mCobraImmersiveAmbient=new CobraImmersiveAmbient(this);
    frame.addView(mCobraImmersiveAmbient,new FrameLayout.LayoutParams(-1,-1));
    mRoot = new LinearLayout(this);''')
 s=once(s,'      mCobraImmersiveAmbient=new CobraImmersiveAmbient(this);\n      mCobraGuideShell.addView(mCobraImmersiveAmbient,new FrameLayout.LayoutParams(-1,-1));\n','')
 s=once(s,'if(mCobraImmersiveAmbient!=null){mCobraImmersiveAmbient.release();mCobraImmersiveAmbient=null;}','if(mCobraImmersiveAmbient!=null){mCobraImmersiveAmbient.release();if(mCobraImmersiveAmbient.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)mCobraImmersiveAmbient.getParent()).removeView(mCobraImmersiveAmbient);mCobraImmersiveAmbient=null;}')
 s=once(s,'    boolean host=mCobraPreviewHost!=null&&mCobraPreviewHost.isAttachedToWindow()&&mCobraPreviewHost.isShown();','    boolean host=mCobraPreviewHost!=null&&mCobraPreviewHost.isAttachedToWindow()&&mCobraPreviewHost.isShown()&&mCobraPreviewHost.getGlobalVisibleRect(new android.graphics.Rect());')
 s=once(s,'eligible(mode,cobraVisualEffectsAllowed(),mPlayerOverlay!=null','eligible(mode,cobraVisualEffectsAllowed()&&mCobraRotationResumed,mPlayerOverlay!=null')
 s=once(s,'return mode==CobraPresentationEffects.IMMERSIVE&&cobraImmersiveAmbientEligible()?CobraPresentationEffects.SUBTLE:mode;','return mode==CobraPresentationEffects.IMMERSIVE&&cobraImmersiveAmbientEligible()?CobraPresentationEffects.OFF:mode;')
 s=once(s,'    int staticMode=reactive?CobraPresentationEffects.SUBTLE:mode;','    int staticMode=reactive?CobraPresentationEffects.OFF:mode;\n    if(mCobraImmersiveAmbient!=null)mCobraImmersiveAmbient.restoreGlass();')
 s=once(s,'ambient.bind(mCobraPreviewTexture,mCobraPreviewHost,!cobraModeDark());','ambient.bind(mCobraPreviewTexture,mCobraPreviewHost,!cobraModeDark(),mCobraPreviewSessionKey);')
 s=once(s,'moving=mCobraPreviewPlayer.isPlaying()||mCobraPreviewPlayer.getPlayWhenReady();','moving=mCobraPreviewPlayer.isPlaying();')
 s=once(s,'    ambient.state(active,moving);','''    ambient.state(active,moving);
    if(active)ambient.illuminate(getWindow().getDecorView());''')
 s=once(s,'    int raw=cobraVisualEffectsAllowed()?CobraPresentationEffects.ambientMode(mPrefs):CobraPresentationEffects.OFF;\n    cobraAmbientSurface(mCobraPlayerDrawer,playerTint,','    int raw=cobraVisualEffectsAllowed()?CobraPresentationEffects.ambientMode(mPrefs):CobraPresentationEffects.OFF;\n    if(raw==CobraPresentationEffects.IMMERSIVE&&cobraImmersiveAmbientEligible())raw=CobraPresentationEffects.OFF;\n    cobraAmbientSurface(mCobraPlayerDrawer,playerTint,')
 s=once(s,'    cobraRefreshGlassTree(drawer,mode,false);\n    cobraRefreshGlassTree(cobraCurrentSheetPanel(),mode,cobraNightCinemaActive());','    cobraRefreshGlassTree(drawer,staticMode,false);\n    cobraRefreshGlassTree(cobraCurrentSheetPanel(),staticMode,cobraNightCinemaActive());')
 s=once(s,'Live edge colours from the mini-player across the Cobra interface','Live colors from the embedded video extend naturally throughout the surrounding Cobra interface')
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--apk-sha',required=True);a=p.parse_args()
 shell=a.root/'shell-kodi';activity=shell/ACTIVITY
 assert sha(activity.read_bytes())=='0ed5f50992bf637bd31ff7c4c299fc4837f5ae0ed3169a687511eec8ed07643c'
 assert (shell/AMBIENT).read_bytes()==(a.root/'repairs/immersive-edge-ambient-2103275/CobraImmersiveAmbient.java.in').read_bytes()
 activity.write_text(patch_activity(activity.read_text()))
 shutil.copy2(HERE/'CobraImmersiveAmbient.java.in',shell/AMBIENT)
 g=shell/GRADLE;g.write_text(once(once(g.read_text(),'versionCode 2103275','versionCode 2103276'),'1.0.9-Immersive-Edge-Ambient-RC1',RELEASE))
 s=a.root/'scripts/infinity_background_resume.py';v=s.read_text()
 for key,value in [('VERSION_CODE','2103276'),('RELEASE',repr(RELEASE)),('BASE_COMMIT',repr(BASE)),('BASE_APK_SHA256',repr(a.apk_sha))]:
  v,n=re.subn(r'^'+key+r' = .*$',key+' = '+value,v,flags=re.M);assert n==1
 s.write_text(v)
 p=a.root/'scripts/package_background_resume.py';v=p.read_text().replace('Infinity-2103275-Immersive-Edge-Ambient-RC1','Infinity-2103276-Whole-UI-Ambient-RC1').replace("'base_run':36775670821","'base_run':36783367196").replace('repairs/immersive-edge-ambient-2103275/DEVICE-TEST.md','repairs/whole-ui-ambient-2103276/DEVICE-TEST.md');p.write_text(v)
 p=a.root/'engine/background-resume-source.json';r=json.loads(p.read_text());r.update(base_source_commit=BASE,base_apk_sha256=a.apk_sha,version_code=2103276,release=RELEASE,candidate_locked=False,physical_device_verified=False,whole_ui_directional_ambient=True)
 for n in [ACTIVITY,AMBIENT,GRADLE]:r['files'].setdefault(n,{})['after']=sha((shell/n).read_bytes())
 p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');a.out.mkdir(parents=True,exist_ok=True)
 print('Applied forward 2103276 whole-window projection and local glass transmission.')
if __name__=='__main__':main()
