package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Insets;
import android.view.*;
import android.widget.*;
import java.lang.reflect.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103198CompleteProductAuditTest {
  CobraNavigationUiTest ui;

  @Before public void before(){ui=new CobraNavigationUiTest();ui.clock();}
  InfinityLiveActivity fixture()throws Exception{return ui.fixture(24);}

  Object call(Object owner,String name,Object...args)throws Exception{
    Method found=null;
    for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){found=m;break;}
    if(found==null)throw new NoSuchMethodException(name);
    found.setAccessible(true);
    try{return found.invoke(owner,args);}catch(InvocationTargetException e){throw new AssertionError(name,e.getCause());}
  }
  void set(Object owner,String name,Object value)throws Exception{
    Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);
  }
  Object get(Object owner,String name)throws Exception{
    Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(owner);
  }
  View tag(android.app.Activity a,String value){return a.getWindow().getDecorView().findViewWithTag(value);}
  TextView findText(View v,String text){
    if(v instanceof TextView&&text.contentEquals(((TextView)v).getText()))return (TextView)v;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){TextView r=findText(g.getChildAt(i),text);if(r!=null)return r;}}
    return null;
  }
  int countText(View v,String text){
    int n=v instanceof TextView&&text.contentEquals(((TextView)v).getText())?1:0;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)n+=countText(g.getChildAt(i),text);}
    return n;
  }
  View findDescription(View v,String text){
    CharSequence d=v.getContentDescription();if(d!=null&&text.contentEquals(d))return v;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){View r=findDescription(g.getChildAt(i),text);if(r!=null)return r;}}
    return null;
  }
  View clickableAncestor(View v){
    View p=v;while(p!=null&&!p.isClickable()){android.view.ViewParent parent=p.getParent();p=parent instanceof View?(View)parent:null;}return p;
  }
  FrameLayout overlay(InfinityLiveActivity a,int w,int h){
    FrameLayout o=new FrameLayout(a);a.setContentView(o);
    o.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));o.layout(0,0,w,h);
    return o;
  }
  Object firstChannel(InfinityLiveActivity a)throws Exception{
    java.util.List<?> channels=(java.util.List<?>)CobraNavigationUiTest.get(a,"mChannels");assertFalse(channels.isEmpty());return channels.get(0);
  }
  View root(InfinityLiveActivity a){return a.getWindow().getDecorView();}

  @Test public void settingsExposeOneCanonicalProductControlSet()throws Exception{
    InfinityLiveActivity a=fixture();try{
      call(a,"showSettings");ui.measure(a,412,915);
      assertNotNull(tag(a,"cobra_theme_management"));
      assertNotNull(tag(a,"cobra_background_mode"));
      assertNotNull(tag(a,"cobra_tv_sources"));
      assertEquals(1,countText(root(a),"TV SOURCES"));
      assertNotNull(findText(root(a),"REFRESH CURRENT SOURCE"));
      assertNotNull(findText(root(a),"REFRESH ALL ENABLED SOURCES"));
      assertNull(tag(a,"cobra_theme_install"));
      assertNull(tag(a,"cobra_visual_theme_state"));
    }finally{ui.clean(a);}
  }

  @Test public void tvSourcesRouteStillOpensExistingSourceManager()throws Exception{
    InfinityLiveActivity a=fixture();try{
      call(a,"showSettings");ui.measure(a,412,915);
      View sources=tag(a,"cobra_tv_sources");assertNotNull(sources);assertTrue(sources.performClick());ui.measure(a,412,915);
      TextView add=findText(root(a),"+  ADD TV SOURCE");assertNotNull(add);assertTrue(add.isClickable());
    }finally{ui.clean(a);}
  }

  @Test public void playerMenuIsOriginalAndNotDuplicated()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));
      call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      for(String label:new String[]{"Channel playback","Health Center","Audio & subtitles","Aspect / Display","Cast / Route","Manage sources","Close player"})
        assertEquals(label,1,countText(root(a),label));
      for(String banned:new String[]{"Player options","RECENT CHANNELS","Video & display","Player settings settings"})
        assertNull(banned,findText(root(a),banned));
    }finally{ui.clean(a);}
  }

  @Test public void playerToolbarIsApprovedFourActionLayout()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,900,700);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"cobraBuildPlayerChrome");
      for(String label:new String[]{"Channels","Display","Multi-View","More"})assertNotNull(label,findDescription(o,label));
      assertNull(findDescription(o,"Options"));assertNull(findDescription(o,"Audio"));
    }finally{ui.clean(a);}
  }

  @Test public void healthCenterStillRoutesToPlaybackDefaults()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));
      call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Health Center"));assertNotNull(row);assertTrue(row.performClick());ui.measure(a,412,915);
      assertNotNull(findText(root(a),"Cobra Health Center"));assertNotNull(findText(root(a),"Playback defaults"));
    }finally{ui.clean(a);}
  }

  @Test public void channelPlaybackRouteStillHasRecoveryAndReset()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));
      call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Channel playback"));assertNotNull(row);assertTrue(row.performClick());ui.measure(a,412,915);
      for(String label:new String[]{"Aspect / display","Preferred audio language","Subtitles","Configured stream fallback","Automatic video-surface recovery","Reset this channel"})
        assertNotNull(label,findText(root(a),label));
    }finally{ui.clean(a);}
  }

  @Test public void backgroundModeSheetKeepsNormalAndExtendedChoices()throws Exception{
    InfinityLiveActivity a=fixture();try{
      call(a,"showSettings");ui.measure(a,412,915);
      View background=tag(a,"cobra_background_mode");assertNotNull(background);assertTrue(background.performClick());ui.measure(a,412,915);
      assertNotNull(tag(a,"cobra-background-mode:normal"));assertNotNull(tag(a,"cobra-background-mode:extended"));
    }finally{InfinityExtendedBackgroundService.setEnabled(a,false);ui.clean(a);}
  }

  @Test public void foldAdaptiveRemainsAvailableInsideOriginalDisplayRoute()throws Exception{
    InfinityLiveActivity a=fixture();try{
      Object channel=firstChannel(a);call(a,"cobraShowChannelAspect",channel);ui.measure(a,412,915);
      assertNotNull(findText(root(a),"Fold Adaptive"));
      assertEquals(12,InfinityLiveActivity.CobraFoldAspectPolicy.MODE);
    }finally{ui.clean(a);}
  }

  @Test public void highRefreshPolicyKeeps120AndSafetyCaps(){
    assertEquals(120f,InfinityLiveActivity.CobraRefreshPolicy.choose("120",new float[]{60f,90f,120f},false,false),.01f);
    assertEquals(60f,InfinityLiveActivity.CobraRefreshPolicy.choose("120",new float[]{60f,90f,120f},true,false),.01f);
    assertEquals(60f,InfinityLiveActivity.CobraRefreshPolicy.choose("max",new float[]{60f,120f},false,true),.01f);
  }

  @Test public void fullscreenExitRestoresBrowseSystemBarOwnership()throws Exception{
    InfinityLiveActivity a=fixture();try{
      View safe=(View)get(a,"mRoot");
      WindowInsets insets=new WindowInsets.Builder().setInsets(WindowInsets.Type.systemBars(),Insets.of(0,36,0,22)).build();
      safe.dispatchApplyWindowInsets(insets);
      FrameLayout o=new FrameLayout(a);set(a,"mPlayerOverlay",o);set(a,"mInPictureInPicture",false);call(a,"cobraApplySystemBarsForSurface");
      assertTrue((a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN)!=0);
      set(a,"mPlayerOverlay",null);call(a,"cobraApplySystemBarsForSurface");safe.dispatchApplyWindowInsets(insets);
      assertEquals(0,a.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_FULLSCREEN);
      assertEquals(36,safe.getPaddingTop());assertEquals(22,safe.getPaddingBottom());
    }finally{ui.clean(a);}
  }

  @Test public void allFiveLiveViewsRemainReachableWithoutReplacingPreview()throws Exception{
    InfinityLiveActivity a=fixture();try{
      call(a,"cobraOpenLiveTv");ui.measure(a,412,915);
      Object texture=get(a,"mCobraPreviewTexture");assertNotNull(texture);
      for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
        call(a,"cobraSwitchMode",mode);ui.measure(a,412,915);
        assertSame("View mode replaced preview texture: "+mode,texture,get(a,"mCobraPreviewTexture"));
        assertNotNull("Missing list in "+mode,get(a,"mCobraGuideList"));
      }
    }finally{ui.clean(a);}
  }

  @Test public void playbackTimeshiftAndProviderGuardsRemainFrozen(){
    assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.REWRITE_ENABLED);
    assertTrue(InfinityLiveActivity.CobraProviderPacePolicy.limited(30000L,900L,180L,560L,560L,560L,10L,500L,0L,0L,0L));
    assertTrue(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("https://tv.example/live/1.ts","ts"));
    assertFalse(InfinityLiveActivity.CobraFinalFeaturePolicy.localTsEligible("https://tv.example/live/1.m3u8","m3u8"));
  }
}
