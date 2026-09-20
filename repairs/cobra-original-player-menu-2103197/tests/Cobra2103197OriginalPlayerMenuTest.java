package com.projectinfinity.kodi;

import android.app.Application;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import java.lang.reflect.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103197OriginalPlayerMenuTest {
  CobraNavigationUiTest ui;
  @Before public void before(){ui=new CobraNavigationUiTest();ui.clock();}
  InfinityLiveActivity fixture()throws Exception{return ui.fixture(24);}
  Object call(Object owner,String name,Object...args)throws Exception{
    Method found=null;
    for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){found=m;break;}
    if(found==null)throw new NoSuchMethodException(name);found.setAccessible(true);return found.invoke(owner,args);
  }
  void set(Object owner,String name,Object value)throws Exception{Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}
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
    o.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));o.layout(0,0,w,h);return o;
  }
  Object firstChannel(InfinityLiveActivity a)throws Exception{
    java.util.List<?> channels=(java.util.List<?>)CobraNavigationUiTest.get(a,"mChannels");assertFalse(channels.isEmpty());return channels.get(0);
  }
  String channelId(Object c)throws Exception{Field f=c.getClass().getDeclaredField("id");f.setAccessible(true);return (String)f.get(c);}
  View root(InfinityLiveActivity a){return a.getWindow().getDecorView();}

  @Test public void originalTopLevelMenuIsBackAndNothingExtra()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      for(String label:new String[]{"Player settings","Channel playback","Health Center","Record now","Audio & subtitles","Aspect / Display","Cast / Route","Manage sources","Close player"})
        assertNotNull(label,findText(root(a),label));
      for(String banned:new String[]{"Player options","RECENT CHANNELS","Video & display","Player settings settings"})
        assertNull(banned,findText(root(a),banned));
    }finally{ui.clean(a);}
  }

  @Test public void topLevelMenuDoesNotRepeatOptions()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      for(String label:new String[]{"Channel playback","Health Center","Audio & subtitles","Aspect / Display","Cast / Route","Manage sources","Close player"})
        assertEquals(label,1,countText(root(a),label));
      assertTrue(countText(root(a),"Restart current program")<=1);
    }finally{ui.clean(a);}
  }

  @Test public void channelPlaybackRouteStillWorks()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Channel playback"));assertNotNull(row);assertTrue(row.performClick());ui.measure(a,412,915);
      for(String label:new String[]{"Channel playback","Aspect / display","Preferred audio language","Subtitles","Configured stream fallback","Automatic video-surface recovery","Reset this channel"})
        assertNotNull(label,findText(root(a),label));
    }finally{ui.clean(a);}
  }

  @Test public void healthCenterRouteStillExposesPlaybackDefaults()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Health Center"));assertNotNull(row);assertTrue(row.performClick());ui.measure(a,412,915);
      assertNotNull(findText(root(a),"Cobra Health Center"));assertNotNull(findText(root(a),"Playback defaults"));
    }finally{ui.clean(a);}
  }

  @Test public void audioAndSubtitleRouteStillWorks()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Audio & subtitles"));assertNotNull(row);assertTrue(row.performClick());ui.measure(a,412,915);
      assertNotNull(findText(root(a),"Audio & subtitles"));assertNotNull(findText(root(a),"Subtitles off"));
    }finally{ui.clean(a);}
  }

  @Test public void aspectRouteKeepsFoldAdaptiveInsideTheOldMenu()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Aspect / Display"));assertNotNull(row);assertTrue(row.performClick());ui.measure(a,412,915);
      assertNotNull(findText(root(a),"Channel display"));assertNotNull(findText(root(a),"Fold Adaptive"));
    }finally{ui.clean(a);}
  }

  @Test public void foldAdaptivePersistsForLiveChannel()throws Exception{
    InfinityLiveActivity a=fixture();try{
      Object channel=firstChannel(a);call(a,"cobraShowChannelAspect",channel);ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Fold Adaptive"));assertNotNull(row);assertTrue(row.performClick());
      String key=(String)call(a,"cobraPreferenceKey",channel);
      android.content.SharedPreferences prefs=(android.content.SharedPreferences)CobraNavigationUiTest.get(a,"mPrefs");
      assertTrue(prefs.getString(key,"").contains("\"aspect\":12"));
      assertEquals(12,((Integer)call(a,"cobraChannelAspect",channel)).intValue());
    }finally{ui.clean(a);}
  }

  @Test public void foldAdaptiveCanBeGlobalDefault()throws Exception{
    InfinityLiveActivity a=fixture();try{
      Object channel=firstChannel(a);String key=(String)call(a,"cobraPreferenceKey",channel);
      android.content.SharedPreferences prefs=(android.content.SharedPreferences)CobraNavigationUiTest.get(a,"mPrefs");
      prefs.edit().remove(key).putInt("cobra_player_aspect_mode",12).apply();
      assertEquals(12,((Integer)call(a,"cobraChannelAspect",channel)).intValue());
      call(a,"cobraShowPlaybackDefaults");ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Default fullscreen aspect"));assertNotNull(row);assertTrue(row.performClick());ui.measure(a,412,915);
      assertNotNull(findText(root(a),"Fold Adaptive"));
    }finally{ui.clean(a);}
  }

  @Test public void originalFourButtonPlayerToolbarIsRestored()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,900,700);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"cobraBuildPlayerChrome");
      for(String label:new String[]{"Channels","Display","Multi-View","More"})assertNotNull(label,findDescription(o,label));
      assertNull(findDescription(o,"Audio"));assertNull(findDescription(o,"Options"));
    }finally{ui.clean(a);}
  }

  @Test public void manageSourcesRouteStillWorksAndPlaybackGuardStaysLocked()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"showPlayerSettingsDrawer");ui.measure(a,412,915);
      View row=clickableAncestor(findText(root(a),"Manage sources"));assertNotNull(row);assertTrue(row.performClick());ui.measure(a,412,915);
      assertNotNull(findText(root(a),"+  ADD TV SOURCE"));
      assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.REWRITE_ENABLED);
      assertTrue(InfinityLiveActivity.CobraProviderPacePolicy.limited(30000L,900L,180L,560L,560L,560L,10L,500L,0L,0L,0L));
    }finally{ui.clean(a);}
  }
}
