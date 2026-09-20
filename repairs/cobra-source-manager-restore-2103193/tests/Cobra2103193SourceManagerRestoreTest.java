package com.projectinfinity.kodi;

import android.app.Application;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
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
public class Cobra2103193SourceManagerRestoreTest {
  CobraNavigationUiTest ui;
  @Before public void before(){ui=new CobraNavigationUiTest();ui.clock();}
  InfinityLiveActivity fixture()throws Exception{return ui.fixture(24);}
  Object call(Object owner,String name,Object...args)throws Exception{
    Method found=null;for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){found=m;break;}
    if(found==null)throw new NoSuchMethodException(name);found.setAccessible(true);return found.invoke(owner,args);
  }
  View tag(android.app.Activity a,String value){return a.getWindow().getDecorView().findViewWithTag(value);}
  TextView findText(View v,String text){
    if(v instanceof TextView&&text.contentEquals(((TextView)v).getText()))return (TextView)v;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){TextView r=findText(g.getChildAt(i),text);if(r!=null)return r;}}
    return null;
  }
  @Test public void settingsExposeTvSourcesButton()throws Exception{
    InfinityLiveActivity a=fixture();try{call(a,"showSettings");ui.measure(a,412,915);View v=tag(a,"cobra_tv_sources");assertNotNull(v);assertTrue(v instanceof TextView);assertEquals("TV SOURCES",((TextView)v).getText().toString());assertTrue(v.isClickable());}finally{ui.clean(a);}
  }
  @Test public void tvSourcesButtonOpensExistingSourceManager()throws Exception{
    InfinityLiveActivity a=fixture();try{call(a,"showSettings");ui.measure(a,412,915);assertTrue(tag(a,"cobra_tv_sources").performClick());ui.measure(a,412,915);assertNotNull(findText(a.getWindow().getDecorView(),"+  ADD TV SOURCE"));}finally{ui.clean(a);}
  }
  @Test public void existingRefreshControlsRemain()throws Exception{
    InfinityLiveActivity a=fixture();try{call(a,"showSettings");ui.measure(a,412,915);assertNotNull(findText(a.getWindow().getDecorView(),"REFRESH CURRENT SOURCE"));assertNotNull(findText(a.getWindow().getDecorView(),"REFRESH ALL ENABLED SOURCES"));}finally{ui.clean(a);}
  }
  @Test public void sourceManagerStillExposesAddSourceContract()throws Exception{
    InfinityLiveActivity a=fixture();try{call(a,"showSources");ui.measure(a,412,915);TextView add=findText(a.getWindow().getDecorView(),"+  ADD TV SOURCE");assertNotNull(add);assertTrue(add.isClickable());}finally{ui.clean(a);}
  }
  @Test public void playbackGuardRemainsUntouched(){
    assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.REWRITE_ENABLED);
    assertTrue(InfinityLiveActivity.CobraProviderPacePolicy.limited(30000L,900L,180L,560L,560L,560L,10L,500L,0L,0L,0L));
  }
}
