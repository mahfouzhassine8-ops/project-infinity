from pathlib import Path
import argparse,hashlib,json,re
HERE=Path(__file__).parent
BASE='8e8b55b6e3c2bb731359e2d52aa11cdf07327729'
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
AMBIENT='tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
RELEASE='1.0.9-Watch-Ambient-RC1'
def sha(b):return hashlib.sha256(b).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
def patch_activity(s):
 start=s.index('  private boolean cobraImmersiveAmbientEligible(){')
 end=s.index('  private int cobraStaticAmbientMode()',start)
 old=s[start:end]
 s=s[:start]+'  private boolean cobraWatchAmbientEligible(){\n    int mode=mPrefs==null?CobraPresentationEffects.OFF:CobraPresentationEffects.ambientMode(mPrefs);\n    boolean host=mPlayerOverlay!=null&&mPlayerOverlay.isAttachedToWindow()&&mPlayerOverlay.isShown();\n    boolean texture=mPlayerTexture!=null&&mPlayerTexture.isAvailable()&&mPlayerTexture.isShown();\n    boolean controls=(mPlayerChrome!=null&&mPlayerChrome.isShown())||(mCobraPlayerDrawer!=null&&mCobraPlayerDrawer.isShown())\n        ||(mCobraActionSheet!=null&&mCobraActionSheet.isShown())||(mCobraMultiPicker!=null&&mCobraMultiPicker.isShown());\n    return CobraImmersiveAmbient.watchEligible(mode,cobraVisualEffectsAllowed()&&mCobraRotationResumed,mPlayerOverlay!=null,\n        mMultiOverlay!=null||mCobraMultiFullscreenActive||cobraMultiViewPlayer(mPlayer),mInPictureInPicture||isCobraInPictureInPicture(),\n        mCobraMiniBackgroundActive||mBackgroundStopped,host,texture,mPlayer!=null,controls);\n  }\n' +old.replace('    int mode=', '    if(cobraWatchAmbientEligible())return true;\n    int mode=',1)+s[end:]
 start=s.index('  private void cobraRefreshImmersiveAmbient(){')
 end=s.index('  private void cobraAmbientSurface(',start)
 s=s[:start]+'  private void cobraRefreshImmersiveAmbient(){\n    CobraImmersiveAmbient ambient=mCobraImmersiveAmbient;if(ambient==null)return;\n    boolean watch=mPlayerOverlay!=null;\n    boolean active=cobraImmersiveAmbientEligible();ambient.controlsOnly(watch);\n    if(active&&watch)cobraWatchBlackScrims();\n    ExoPlayer sourcePlayer=watch?mPlayer:mCobraPreviewPlayer;\n    if(watch){\n      if(mPlayerTexture!=null)ambient.bind(mPlayerTexture,mPlayerOverlay,!cobraModeDark(),\n          "watch:"+(mPlaying==null?"":mPlaying.id)+":"+mPlayingVodKey+":"+System.identityHashCode(sourcePlayer));\n      ambient.illuminateWatch(mCobraPlayerProgramProgress,mPlayerChrome,mCobraPlayerDrawer,mCobraActionSheet,mCobraMultiPicker,mCobraPlayerLockOverlay);\n    }else if(mCobraPreviewTexture!=null&&mCobraPreviewHost!=null)ambient.bind(mCobraPreviewTexture,mCobraPreviewHost,!cobraModeDark(),mCobraPreviewSessionKey);\n    boolean moving=false;if(active&&sourcePlayer!=null)try{moving=sourcePlayer.isPlaying();}catch(RuntimeException ignored){}\n    ambient.state(active,moving);\n    if(active){if(watch)ambient.illuminateWatch(mCobraPlayerProgramProgress,mPlayerChrome,mCobraPlayerDrawer,mCobraActionSheet,mCobraMultiPicker,mCobraPlayerLockOverlay);\n      else ambient.illuminate(getWindow().getDecorView());}\n  }\n\n' +s[end:]
 s=once(s,'      super.onDraw(canvas);if(!liveWindow)return;','      super.onDraw(canvas);if(mCobraImmersiveAmbient!=null)mCobraImmersiveAmbient.drawWatchProgress(canvas,this,getProgress()/(float)Math.max(1,getMax()));if(!liveWindow)return;')
 s=once(s,'    cobraRefreshGlassTree(mCobraPlayerDrawer,mode,cobraNightCinemaActive());\n    cobraRefreshGlassTree(mPlayerChrome,mode,cobraNightCinemaActive());','    cobraRefreshGlassTree(mCobraPlayerDrawer,staticMode,cobraNightCinemaActive());\n    cobraRefreshGlassTree(mPlayerChrome,staticMode,cobraNightCinemaActive());')
 s=once(s,'    if(raw==CobraPresentationEffects.OFF||!cobraVisualEffectsAllowed())return;', '    if(raw==CobraPresentationEffects.IMMERSIVE&&cobraWatchAmbientEligible()){\n      // Watch ambient is confined to controls. Restore the original black chrome scrims.\n      header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{vtheme().color("cobra.cobraBuildPlayerChrome.colors.1",0xcf000000),vtheme().color("cobra.cobraBuildPlayerChrome.colors.2",0x65000000),Color.TRANSPARENT}));\n      footer.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{Color.TRANSPARENT,vtheme().color("cobra.cobraBuildPlayerChrome.colors.8",0xba000000),vtheme().color("cobra.cobraBuildPlayerChrome.colors.9",0xe6000000)}));\n      cobraRefreshGlassTree(mPlayerChrome,CobraPresentationEffects.OFF,false);return;\n    }\n    if(raw==CobraPresentationEffects.OFF||!cobraVisualEffectsAllowed())return;')
 s=once(s,'  private void cobraApplyNightCinema(View header,View footer,View pause){',"  private View mCobraWatchBlackChrome;\n  private void cobraWatchBlackScrims(){\n    if(cobraNightCinemaActive()||mPlayerChrome==null||mCobraWatchBlackChrome==mPlayerChrome)return;\n    mCobraWatchBlackChrome=mPlayerChrome;\n    View header=mPlayerChrome.getChildAt(0),footer=mPlayerChrome.getChildAt(mPlayerChrome.getChildCount()-1);\n    header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{vtheme().color(\"cobra.cobraBuildPlayerChrome.colors.1\",0xcf000000),vtheme().color(\"cobra.cobraBuildPlayerChrome.colors.2\",0x65000000),Color.TRANSPARENT}));\n    footer.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{Color.TRANSPARENT,vtheme().color(\"cobra.cobraBuildPlayerChrome.colors.8\",0xba000000),vtheme().color(\"cobra.cobraBuildPlayerChrome.colors.9\",0xe6000000)}));\n  }\n  private void cobraApplyNightCinema(View header,View footer,View pause){\n    mCobraWatchBlackChrome=null;")
 s=once(s,'if(embedded&&mCobraImmersiveAmbient!=null)mCobraImmersiveAmbient.geometryChanged();','if((embedded||(texture==mPlayerTexture&&mPlayerOverlay!=null))&&mCobraImmersiveAmbient!=null)mCobraImmersiveAmbient.geometryChanged();')
 s=once(s,'configureCobraPip(cobraPlaybackRequested(player));}cobraUpdatePlaybackLabels();cobraPublishMiniState();}}','configureCobraPip(cobraPlaybackRequested(player));}cobraUpdatePlaybackLabels();cobraPublishMiniState();if(player==mPlayer)cobraRefreshImmersiveAmbient();}}')
 s=once(s,'Live colors from the embedded video extend naturally throughout the surrounding Cobra interface','Live video colors illuminate Cobra glass, Watch controls and menus. Video stays unchanged.')
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.root;shell=root/'shell-kodi'
 for path,fn in [(ACTIVITY,patch_activity)]:
  f=shell/path;f.write_text(fn(f.read_text()))
 import shutil
 shutil.copy2(HERE/'CobraImmersiveAmbient.java.in',shell/AMBIENT)
 f=shell/GRADLE;f.write_text(once(once(f.read_text(),'versionCode 2103277','versionCode 2103278'),'1.0.9-Mini-Player-Fill-RC1',RELEASE))
 f=root/'scripts/infinity_background_resume.py';s=f.read_text()
 for key,value in [('VERSION_CODE','2103278'),('RELEASE',repr(RELEASE)),('BASE_COMMIT',repr(BASE)),('BASE_APK_SHA256',repr('cd996d2f865f60ae79df3114b35c5d788b2f4177582ec1389d1a217a3f71051b'))]:
  s,n=re.subn(r'^'+key+r' = .*$',key+' = '+value,s,flags=re.M);assert n==1
 f.write_text(s)
 f=root/'scripts/package_background_resume.py';f.write_text(f.read_text().replace('Infinity-2103277-Mini-Player-Fill-RC1','Infinity-2103278-Watch-Ambient-RC1').replace("'base_run':36787860835","'base_run':36790711206").replace('repairs/mini-player-fill-2103277/DEVICE-TEST.md','repairs/watch-ambient-2103278/DEVICE-TEST.md'))
 f=root/'engine/background-resume-source.json';r=json.loads(f.read_text());r.update(base_source_commit=BASE,base_apk_sha256='cd996d2f865f60ae79df3114b35c5d788b2f4177582ec1389d1a217a3f71051b',version_code=2103278,release=RELEASE,candidate_locked=False,physical_device_verified=False,watch_control_ambient=True)
 for path in [ACTIVITY,AMBIENT,GRADLE]:r['files'].setdefault(path,{})['after']=sha((shell/path).read_bytes())
 f.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');a.out.mkdir(parents=True,exist_ok=True)
 print('Applied bounded 2103278 Watch control ambient.')
if __name__=='__main__':main()
