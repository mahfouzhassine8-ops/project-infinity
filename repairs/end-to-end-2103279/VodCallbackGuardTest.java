package com.projectinfinity.kodi;
import android.app.Application;import android.view.*;import android.widget.*;
import java.util.*;import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class VodCallbackGuardTest {
 CobraNavigationUiTest ui;InfinityLiveActivity a;CobraNavigationUiTest.PendingIo io;
 Object get(String n)throws Exception{return CobraNavigationUiTest.get(a,n);}
 Object call(String n,Object...args)throws Exception{return CobraNavigationUiTest.call(a,n,args);}
 @Before public void setup()throws Exception{CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(3);io=(CobraNavigationUiTest.PendingIo)get("mIo");((List)get("mSources")).add(CobraNavigationUiTest.construct("LiveSource","audit","xtream","Fixture","invalid://fixture","","","",""));}
 @After public void cleanup()throws Exception{ui.clean(a);CobraVisualRenderer.clients.clear();}
 Runnable request(String name)throws Exception{Object item=CobraNavigationUiTest.construct("VodItem","audit",name,name,"Test","","mp4",false);call("cobraShowVodDetails",item);return io.tasks.remove(io.tasks.size()-1);}
 void finish(Runnable r){r.run();ui.frames(2);}
 boolean hasText(View v,String text){if(v instanceof TextView&&text.contentEquals(((TextView)v).getText()))return true;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)if(hasText(((ViewGroup)v).getChildAt(i),text))return true;return false;}
 @Test public void lateMovieResponseCannotReplaceRecordings()throws Exception{Runnable pending=request("Old movie");call("cobraSelectDrawerOwner","RECORDINGS");call("showCobraPrimaryView");Object stage=get("mCobraStageTitle");finish(pending);assertEquals(stage,get("mCobraStageTitle"));assertEquals("recordings",call("cobraDrawerOwner"));}
 @Test public void newerMovieDetailsWinWhenResponsesArriveOutOfOrder()throws Exception{Runnable old=request("Old movie"),newest=request("Latest movie");finish(newest);assertTrue(hasText(a.getWindow().getDecorView(),"Latest movie"));finish(old);assertTrue(hasText(a.getWindow().getDecorView(),"Latest movie"));assertFalse(hasText(a.getWindow().getDecorView(),"Old movie"));}
 @Test public void currentRequestStillOpensDetailsWhenMetadataFails()throws Exception{finish(request("Available movie"));assertEquals("COBRA • MOVIE DETAILS",get("mCobraStageTitle"));assertTrue(hasText(a.getWindow().getDecorView(),"Available movie"));}
}
