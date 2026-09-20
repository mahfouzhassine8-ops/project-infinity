package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import java.lang.reflect.*;
import java.time.Duration;
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
public class Cobra2103195PresentationPolishTest {
  CobraNavigationUiTest ui;
  @Before public void before(){ui=new CobraNavigationUiTest();ui.clock();}
  InfinityLiveActivity fixture()throws Exception{return ui.fixture(24);}
  Object call(Object owner,String name,Object...args)throws Exception{
    Method found=null;for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){found=m;break;}
    if(found==null)throw new NoSuchMethodException(name);found.setAccessible(true);return found.invoke(owner,args);
  }
  void set(Object owner,String name,Object value)throws Exception{Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}
  TextView findText(View v,String text){
    if(v instanceof TextView&&text.contentEquals(((TextView)v).getText()))return (TextView)v;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){TextView r=findText(g.getChildAt(i),text);if(r!=null)return r;}}
    return null;
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
    FrameLayout o=new FrameLayout(a);a.setContentView(o);o.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));o.layout(0,0,w,h);return o;
  }
  Object firstChannel(InfinityLiveActivity a)throws Exception{
    java.util.List<?> channels=(java.util.List<?>)CobraNavigationUiTest.get(a,"mChannels");assertFalse(channels.isEmpty());return channels.get(0);
  }
  String channelId(Object c)throws Exception{Field f=c.getClass().getDeclaredField("id");f.setAccessible(true);return (String)f.get(c);}

  @Test public void playerHubLooksLikeARealQuickOptionsLayer()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);Object channel=firstChannel(a);set(a,"mPlaying",channel);
      @SuppressWarnings("unchecked") Collection<String> recents=(Collection<String>)CobraNavigationUiTest.get(a,"mRecents");recents.add(channelId(channel));
      call(a,"showCobraPlayerOptionsHub");ui.measure(a,412,915);
      for(String label:new String[]{"Player options","RECENT CHANNELS","Channels","TV Guide","Audio & subtitles","Video & display","Multi-View","Picture in Picture","Health Center","Player settings"})
        assertNotNull(label,findText(a.getWindow().getDecorView(),label));
    }finally{ui.clean(a);}
  }

  @Test public void videoMenuCollectsFoldDisplayRotationAndPip()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));
      call(a,"showCobraVideoOptions");ui.measure(a,412,915);
      for(String label:new String[]{"Video & display","Display mode","Video details","Rotation","Display & performance","Picture in Picture","Channel playback"})
        assertNotNull(label,findText(a.getWindow().getDecorView(),label));
    }finally{ui.clean(a);}
  }

  @Test public void widePlayerChromeExposesExpandedQuickActions()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,900,700);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"cobraBuildPlayerChrome");
      for(String label:new String[]{"Channels","Favorite","Audio","Display","Multi-View","Options"})assertNotNull(label,findDescription(o,label));
    }finally{ui.clean(a);}
  }

  @Test public void shortPlayerChromeStaysCompact()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,300);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"cobraBuildPlayerChrome");
      assertNotNull(findDescription(o,"Channels"));assertNotNull(findDescription(o,"Display"));assertNotNull(findDescription(o,"Multi-View"));assertNotNull(findDescription(o,"Options"));
      assertNull(findDescription(o,"Favorite"));assertNull(findDescription(o,"Audio"));
    }finally{ui.clean(a);}
  }

  @Test public void focusMotionIsSubtleAndReturnsToRest()throws Exception{
    InfinityLiveActivity a=fixture();try{
      FrameLayout o=overlay(a,412,915);set(a,"mPlayerOverlay",o);set(a,"mPlaying",firstChannel(a));call(a,"showCobraVideoOptions");ui.measure(a,412,915);
      View row=clickableAncestor(findText(a.getWindow().getDecorView(),"Display mode"));assertNotNull(row);assertTrue(row.requestFocus());
      Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(Duration.ofMillis(160));assertTrue(row.getScaleX()>1f&&row.getScaleX()<1.03f);
      row.clearFocus();Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(Duration.ofMillis(140));assertEquals(1f,row.getScaleX(),.02f);
    }finally{ui.clean(a);}
  }

  @Test public void lockedSourceAndFoldContractsRemainVisible()throws Exception{
    InfinityLiveActivity a=fixture();try{
      call(a,"showSettings");ui.measure(a,412,915);assertNotNull(findText(a.getWindow().getDecorView(),"TV SOURCES"));
      assertEquals(12,InfinityLiveActivity.CobraFoldAspectPolicy.MODE);
    }finally{ui.clean(a);}
  }

  @Test public void lockedPlaybackGuardRemainsUntouched(){
    assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.REWRITE_ENABLED);
    assertTrue(InfinityLiveActivity.CobraProviderPacePolicy.limited(30000L,900L,180L,560L,560L,560L,10L,500L,0L,0L,0L));
  }
}
