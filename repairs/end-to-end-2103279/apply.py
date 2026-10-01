from pathlib import Path
import argparse,hashlib,json,re
HERE=Path(__file__).parent
BASE='41f08774a8b908d60c0f9e6647497e40d6bbe081'
APK_SHA='473eed44dbe8bb6152ec895a96d034361c4fc8fb3217edb9b26cc753e0f631f7'
RELEASE='1.0.9-End-to-End-Repair-RC1'
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
PEEK='tools/android/packaging/xbmc/src/CobraQuickPeekSession.java.in'
CMAKE='cmake/scripts/android/Install.cmake'
CROP='tools/android/packaging/xbmc/src/CobraEmbeddedCrop.java.in'
AMBIENT='tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
def once(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
def activity(s):
 s=once(s,'    TextureView texture;View.OnLayoutChangeListener layoutListener;','    TextureView texture;View.OnLayoutChangeListener layoutListener;\n    VideoSize lastVideoSize=VideoSize.UNKNOWN;')
 s=once(s,'@Override public void onVideoSizeChanged(VideoSize size){if(current()){cobraFitBinding(this);','@Override public void onVideoSizeChanged(VideoSize size){if(current()){if(size.width>0&&size.height>0)lastVideoSize=size;cobraFitBinding(this);')
 s=once(s,'@Override public void onRenderedFirstFrame(){if(current()){lastFrameMs=','@Override public void onSurfaceSizeChanged(int width,int height){if(current())cobraFitBinding(this);}\n    @Override public void onRenderedFirstFrame(){if(current()){cobraFitBinding(this);lastFrameMs=')
 s=once(s,'    if(binding.texture==texture)return;','    if(binding.texture==texture){cobraFitBinding(binding);return;}')
 s=once(s,'    texture.addOnLayoutChangeListener(binding.layoutListener);','    texture.addOnLayoutChangeListener(binding.layoutListener);\n    cobraFitBinding(binding);')
 s=once(s,'    VideoSize size=player.getVideoSize();\n    CobraPlayerBinding b=mCobraPlayerBindings.get(player);CobraChannelPreferences saved=', '''    VideoSize size=player.getVideoSize();
    CobraPlayerBinding b=mCobraPlayerBindings.get(player);
    if(b!=null){if(size.width>0&&size.height>0)b.lastVideoSize=size;else size=b.lastVideoSize;}
    CobraChannelPreferences saved=''')
 s=once(s,'    final CobraSessionVitals vitals;CobraCaptionOverlay captions;','    final CobraSessionVitals vitals;CobraCaptionOverlay captions;final CobraEmbeddedCrop embeddedCrop;')
 s=once(s,'CobraPlayerBinding(ExoPlayer p,Channel c){player=p;channel=c;vitals=new CobraSessionVitals(p,c);}','''CobraPlayerBinding(ExoPlayer p,Channel c){player=p;channel=c;vitals=new CobraSessionVitals(p,c);
      embeddedCrop=new CobraEmbeddedCrop(()->current()&&texture==mCobraPreviewTexture&&mPlayerOverlay==null&&!mInPictureInPicture&&!mBackgroundStopped&&mCobraRotationResumed,
          ()->{if(mCobraImmersiveAmbient!=null)mCobraImmersiveAmbient.geometryChanged();});}''')
 s=once(s,'@Override public void onIsPlayingChanged(boolean playing){if(current()){if(player==mPlayer)', '@Override public void onIsPlayingChanged(boolean playing){if(current()){embeddedCrop.refresh();if(player==mPlayer)')
 s=once(s,'if(binding!=null){binding.closed=true;player.removeListener(binding);','if(binding!=null){binding.closed=true;binding.embeddedCrop.close();player.removeListener(binding);')
 s=once(s,'mCobraRotationResumed=true;cobraApplyPlayerRotation("resume");','mCobraRotationResumed=true;for(CobraPlayerBinding binding:mCobraPlayerBindings.values())binding.embeddedCrop.refresh();cobraApplyPlayerRotation("resume");')
 s=once(s,'mCobraPlaybackPolicy.pause();cobraSuspendImmersiveAmbient();','mCobraPlaybackPolicy.pause();for(CobraPlayerBinding binding:mCobraPlayerBindings.values())binding.embeddedCrop.refresh();cobraSuspendImmersiveAmbient();')
 s=once(s,'  private void cobraStartPresentationTicker() {','  private void cobraStartPresentationTicker() {\n    for(CobraPlayerBinding binding:mCobraPlayerBindings.values())binding.embeddedCrop.refresh();')
 s=once(s,'    if((embedded||(texture==mPlayerTexture&&mPlayerOverlay!=null))&&mCobraImmersiveAmbient!=null)', '    if(b!=null)b.embeddedCrop.apply(texture,player,matrix,embedded);\n    if((embedded||(texture==mPlayerTexture&&mPlayerOverlay!=null))&&mCobraImmersiveAmbient!=null)')
 s=once(s,'texture.setTransform(matrix);}'+'\n    }else cobraFitVideo','texture.setTransform(matrix);binding.embeddedCrop.apply(texture,binding.player,matrix,false);}'+'\n    }else cobraFitVideo')
 s=once(s,'LiveSource source=sourceById(item.sourceId);if(source==null)return;status("Loading details…");','LiveSource source=sourceById(item.sourceId);if(source==null)return;status("Loading details…");final long ticket=mCobraNavigation.advance();final String profile=mFeatures.activeProfileId();')
 s=once(s,'final JSONObject ready=info;runOnUiThread(()->{status("Ready");cobraRenderVodDetails(item,ready);});','final JSONObject ready=info;cobraPublishNavigation(ticket,()->{if(!profile.equals(mFeatures.activeProfileId()))return;status("Ready");cobraRenderVodDetails(item,ready);});')
 s=once(s,'Fullscreen fitting follows the actual pane. Preview and PiP keep the complete picture.','Fullscreen fitting follows the actual pane. Previews fill their frame; PiP keeps the complete picture.')
 s=once(s,'Inherited in fullscreen. Previews keep the complete picture. Multi-View tiles inherit Fold Fit / Fold Fill unless a channel overrides them.','Inherited in fullscreen. Previews use center crop. Multi-View tiles inherit Fold Fit / Fold Fill unless a channel overrides them.')
 return short_window_ui(playback_ui(s))

def short_window_ui(s):
 s=once(s,'  private void cobraShowGuideShell(){',(HERE/'guide_viewport.java.fragment').read_text()+'  private void cobraShowGuideShell(){')
 s=once(s,'mCobraGuideShell=new FrameLayout(this){','mCobraGuideShell=new CobraGuideViewport(){')
 s=once(s,'Math.max(1,Math.round((h-top-bottom)/density)),getResources().getConfiguration().fontScale,mCobraModeGroupsExpanded)', 'cobraGuideWorkingHeight(Math.max(1,Math.round((h-top-bottom)/density))),getResources().getConfiguration().fontScale,mCobraModeGroupsExpanded)')
 s=once(s,'  private void cobraLayoutGuide(){','  private int cobraGuideWorkingHeight(int measured){return measured<240?360:measured;}\n  private void cobraLayoutGuide(){')
 s=once(s,'    View controls=mCobraGuideVideo.findViewWithTag("cobra_preview_controls");','    mCobraGuideShell.scrollTo(0,mCobraGuideShell.getScrollY());\n    View controls=mCobraGuideVideo.findViewWithTag("cobra_preview_controls");')
 s=once(s,'    }else{buildShell();showSettings();}\n  }\n  private void showCobraSystemDarkPicker(){','    }else{buildShell();showSettings();}\n    cobraApplySystemBarsForSurface();\n  }\n  private void showCobraSystemDarkPicker(){')
 return s

def playback_ui(s):
 s=once(s,'    CobraImmersiveAmbient ambient=mCobraImmersiveAmbient;if(ambient==null)return;','''    CobraImmersiveAmbient ambient=mCobraImmersiveAmbient;
    // Entering Movies/Shows releases the guide's renderer. Direct Watch playback
    // must be able to restore the same shared engine behind the browse content.
    if(ambient==null&&cobraWatchAmbientEligible()&&mCobraBrowseBackground!=null
        &&mCobraBrowseBackground.getParent() instanceof FrameLayout){
      FrameLayout parent=(FrameLayout)mCobraBrowseBackground.getParent();
      ambient=new CobraImmersiveAmbient(this);mCobraImmersiveAmbient=ambient;
      parent.addView(ambient,parent.indexOfChild(mCobraBrowseBackground)+1,new FrameLayout.LayoutParams(-1,-1));
    }
    if(ambient==null)return;''')
 s=once(s,'  private boolean cobraTimeshiftTimelineAvailable(){','''  private boolean cobraVodSeekable(){
    if(mPlayingVodKey==null||mPlayingVodKey.isEmpty()||mPlayer==null)return false;
    try{return mPlayer.isCurrentMediaItemSeekable()&&mPlayer.getDuration()>0L&&mPlayer.getDuration()!=C.TIME_UNSET;}
    catch(RuntimeException unavailable){return false;}
  }
  private void cobraSeekVodBy(long delta){
    if(!cobraVodSeekable())return;
    try{mPlayer.seekTo(Math.max(0L,Math.min(mPlayer.getDuration(),mPlayer.getCurrentPosition()+delta)));}
    catch(RuntimeException unavailable){return;}
    cobraUpdateTimeshiftSeek();cobraUpdateLiveRewindControls();showPlayerChromeTemporarily();
  }
  private boolean cobraTimeshiftTimelineAvailable(){
    if(cobraVodSeekable())return true;''')
 s=once(s,'boolean liveWindow=available&&!mCobraProviderCatchupActive;','boolean liveWindow=available&&!mCobraProviderCatchupActive&&mPlayingVodKey.isEmpty();')
 s=once(s,'  private void cobraRewindLive(long amountMs){','  private void cobraRewindLive(long amountMs){\n    if(!mPlayingVodKey.isEmpty()){cobraSeekVodBy(-amountMs);return;}')
 s=once(s,'  private void cobraGoLive(){','  private void cobraGoLive(){\n    if(!mPlayingVodKey.isEmpty()){cobraSeekVodBy(30000L);return;}')
 s=once(s,'  private void cobraUpdateLiveRewindControls(){','''  private void cobraUpdateLiveRewindControls(){
    if(!mPlayingVodKey.isEmpty()){
      boolean enabled=cobraVodSeekable();
      if(mCobraLiveRewindButton!=null){mCobraLiveRewindButton.setEnabled(enabled);mCobraLiveRewindButton.setAlpha(enabled?1f:.35f);mCobraLiveRewindButton.setContentDescription("Rewind 30 seconds");}
      if(mCobraGoLiveButton!=null){mCobraGoLiveButton.setEnabled(enabled);mCobraGoLiveButton.setAlpha(enabled?1f:.35f);mCobraGoLiveButton.setSelected(false);mCobraGoLiveButton.caption("+30s");mCobraGoLiveButton.setContentDescription("Forward 30 seconds");}return;
    }
    if(mCobraGoLiveButton!=null)mCobraGoLiveButton.caption("LIVE");''')
 s=once(s,'    if(mCobraPlayerUpcoming!=null)mCobraPlayerUpcoming.setText(next==null?"":"Next  "+next.title);','''    if(mCobraPlayerUpcoming!=null)mCobraPlayerUpcoming.setText(next==null?"":"Next  "+next.title);
    if(!mPlayingVodKey.isEmpty()&&mPlayer!=null&&mCobraPlayerSchedule!=null){
      long duration=mPlayer.getDuration(),position=Math.max(0L,mPlayer.getCurrentPosition());
      mCobraPlayerSchedule.setText(duration>0L&&duration!=C.TIME_UNSET?android.text.format.DateUtils.formatElapsedTime(position/1000L)+" / "+android.text.format.DateUtils.formatElapsedTime(duration/1000L):"Loading playback…");
    }''')
 s=once(s,'  private final class CobraCaptionOverlay extends View {','''  private int cobraCaptionBottom(View captions){
    int bottom=captions.getHeight();if(!cobraSubtitleAdaptive())return bottom;
    View obstruction=null;
    if(captions.getParent()==mPlayerOverlay&&mPlayerChrome!=null&&mPlayerChrome.isShown()&&mPlayerChrome.getChildCount()>0)
      obstruction=mPlayerChrome.getChildAt(mPlayerChrome.getChildCount()-1);
    else if(captions.getParent()==mCobraPreviewHost&&mCobraPreviewHost!=null)
      obstruction=mCobraPreviewHost.findViewWithTag("cobra_preview_controls");
    if(obstruction!=null&&obstruction.isShown()&&obstruction.getHeight()>0){
      int top=obstruction.getTop()-captions.getTop();if(obstruction.getParent()==mPlayerChrome)top+=mPlayerChrome.getTop();
      if(top>dp(36))bottom=Math.min(bottom,Math.max(1,top-dp(8)));
    }return bottom;
  }
  private final class CobraCaptionOverlay extends View {''')
 s=once(s,'int save=canvas.save();canvas.clipRect(0,0,w,h);\n      for(androidx.media3.common.text.Cue cue:cues){','int save=canvas.save();canvas.clipRect(0,0,w,h);int contentBottom=cobraCaptionBottom(this);\n      for(androidx.media3.common.text.Cue cue:cues){')
 s=once(s,'Math.max(1,h-dp(12))/(float)Math.max(1,height)','Math.max(1,contentBottom-dp(12))/(float)Math.max(1,height)')
 s=once(s,'y=Math.max(0,Math.min(h-drawHeight,y));','y=Math.max(0,Math.min(contentBottom-drawHeight,y));')
 s=once(s,'    cobraResetMotion(chrome);chrome.setVisibility(View.VISIBLE);','    cobraResetMotion(chrome);chrome.setVisibility(View.VISIBLE);cobraRefreshCaptionStyle();cobraRefreshImmersiveAmbient();')
 s=once(s,'cobraResetMotion(mPlayerChrome);mPlayerChrome.setVisibility(View.GONE);}','cobraResetMotion(mPlayerChrome);mPlayerChrome.setVisibility(View.GONE);cobraRefreshCaptionStyle();cobraRefreshImmersiveAmbient();}')
 s=once(s,'if(!cobraMotionEnabled()){target.setVisibility(View.GONE);return;}','if(!cobraMotionEnabled()){target.setVisibility(View.GONE);cobraRefreshCaptionStyle();cobraRefreshImmersiveAmbient();return;}')
 s=once(s,'if(cobraChromeCanHide(target))target.setVisibility(View.GONE);','if(cobraChromeCanHide(target)){target.setVisibility(View.GONE);cobraRefreshCaptionStyle();cobraRefreshImmersiveAmbient();}')
 s=once(s,'mPlayerChrome.setVisibility(View.GONE);ensureCobraPlayerLockOverlay();','mPlayerChrome.setVisibility(View.GONE);cobraRefreshCaptionStyle();cobraRefreshImmersiveAmbient();ensureCobraPlayerLockOverlay();')
 s=once(s,'mPlayerChrome=chrome;chrome.setTag("cobra_player_refined_chrome");','mPlayerChrome=chrome;chrome.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->cobraRefreshCaptionStyle());chrome.setTag("cobra_player_refined_chrome");')
 return s

def peek(s):
 s=once(s,'  private Listener listener;','  private Listener listener;\n  private final CobraEmbeddedCrop crop=new CobraEmbeddedCrop(()->!this.closed,null);')
 s=once(s,'    @Override public void onVideoSizeChanged(VideoSize size){fit();}','    @Override public void onIsPlayingChanged(boolean playing){crop.refresh();}\n    @Override public void onVideoSizeChanged(VideoSize size){fit();}')
 s=once(s,'    if(closed)return;closed=true;handler.removeCallbacksAndMessages(null);listener=null;','    if(closed)return;closed=true;crop.close();handler.removeCallbacksAndMessages(null);listener=null;')
 s=once(s,'firstFrame=true;handler.removeCallbacks(startupTimeout);','firstFrame=true;fit();handler.removeCallbacks(startupTimeout);')
 s=once(s,'    @Override public void onVideoSizeChanged(VideoSize size){fit();}','    @Override public void onVideoSizeChanged(VideoSize size){fit();}\n    @Override public void onSurfaceSizeChanged(int width,int height){fit();}')
 s=once(s,'''    float aspect=size.width*Math.max(.01f,size.pixelWidthHeightRatio)/size.height;float viewport=(float)w/h;
    Matrix matrix=new Matrix();matrix.setScale(aspect<viewport?aspect/viewport:1f,aspect>viewport?viewport/aspect:1f,w/2f,h/2f);texture.setTransform(matrix);''','''    float[] scale=InfinityLiveActivity.CobraFoldAspectPolicy.fill(size.width,size.height,size.pixelWidthHeightRatio,w,h);
    Matrix matrix=new Matrix();matrix.setScale(scale[0],scale[1],w/2f,h/2f);texture.setTransform(matrix);crop.apply(texture,player,matrix,true);''')
 return s

def cmake(s):
 s=once(s,'                  src/CobraImmersiveAmbient.java','                  src/CobraImmersiveAmbient.java\n                  src/CobraEmbeddedCrop.java')
 return s+'\nconfigure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraEmbeddedCrop.java.in\n               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraEmbeddedCrop.java @ONLY)\n'

def ambient(s):
 s=once(s,'private final android.graphics.Matrix watchMatrix=new android.graphics.Matrix();','private final android.graphics.Matrix watchMatrix=new android.graphics.Matrix(),captureInverse=new android.graphics.Matrix();')
 s=once(s,'controlsOnly ? captureWatch(texture,width,height) : texture.getBitmap(raw)','captureWatch(texture,width,height)')
 s=once(s,'    visiblePicture(texture,watchPicture,watchMatrix);','    visibleSource(texture,watchPicture,watchMatrix,captureInverse);')
 marker='  static void visiblePicture(TextureView texture,RectF out,android.graphics.Matrix matrix){'
 s=once(s,marker,'''  // Hardware TextureView readback omits the layer transform. Map the viewport
  // back to source coordinates so ambient edges match the picture on screen.
  static void visibleSource(TextureView texture,RectF out,android.graphics.Matrix matrix,android.graphics.Matrix inverse){
    out.set(0,0,texture.getWidth(),texture.getHeight());texture.getTransform(matrix);
    if(!matrix.invert(inverse)){out.setEmpty();return;}inverse.mapRect(out);
    if(!out.intersect(0,0,texture.getWidth(),texture.getHeight()))out.setEmpty();
  }
'''+marker)
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.root;shell=root/'shell-kodi'
 for path,fn in [(ACTIVITY,activity),(PEEK,peek),(CMAKE,cmake),(AMBIENT,ambient)]:
  f=shell/path;f.write_text(fn(f.read_text()))
 f=shell/'tools/android/packaging/xbmc/src/CobraEmbeddedCrop.java.in';f.write_text((HERE/'CobraEmbeddedCrop.java.in').read_text())
 f=shell/GRADLE;f.write_text(once(once(f.read_text(),'versionCode 2103278','versionCode 2103279'),'1.0.9-Watch-Ambient-RC1',RELEASE))
 f=root/'scripts/infinity_background_resume.py';s=f.read_text()
 for key,value in [('VERSION_CODE','2103279'),('RELEASE',repr(RELEASE)),('BASE_COMMIT',repr(BASE)),('BASE_APK_SHA256',repr(APK_SHA))]:
  s,n=re.subn(r'^'+key+r' = .*$',key+' = '+value,s,flags=re.M);assert n==1
 f.write_text(s)
 f=root/'scripts/package_background_resume.py';f.write_text(f.read_text().replace('Infinity-2103278-Watch-Ambient-RC1','Infinity-2103279-End-to-End-Repair-RC1').replace("'base_run':36790711206","'base_run':36794611568").replace('repairs/watch-ambient-2103278/DEVICE-TEST.md','repairs/end-to-end-2103279/DEVICE-TEST.md'))
 f=root/'engine/background-resume-source.json';r=json.loads(f.read_text());r.update(base_source_commit=BASE,base_apk_sha256=APK_SHA,version_code=2103279,release=RELEASE,candidate_locked=False,physical_device_verified=False)
 for path in [ACTIVITY,PEEK,GRADLE,CROP,CMAKE,AMBIENT]:r['files'].setdefault(path,{})['after']=hashlib.sha256((shell/path).read_bytes()).hexdigest()
 f.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');a.out.mkdir(parents=True,exist_ok=True)
 print('Applied bounded surface lifecycle and Quick Peek fill repairs.')
if __name__=='__main__':main()
