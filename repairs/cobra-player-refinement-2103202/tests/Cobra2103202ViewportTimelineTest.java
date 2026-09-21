package com.projectinfinity.kodi;
import android.app.Application;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real TextureView transforms and UI drawing, not decoded GPU frames or physical Fold acceptance. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103202ViewportTimelineTest {
  Cobra2103201ScrubberTest f;InfinityLiveActivity a;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  Object call(String n,Object...v)throws Exception{return CobraNavigationUiTest.call(a,n,v);}
  @Before public void before()throws Exception{f=new Cobra2103201ScrubberTest();f.before();a=f.a;}
  @After public void after()throws Exception{if(f!=null)f.after();}
  ProgressBar line()throws Exception{return (ProgressBar)get(a,"mCobraPlayerProgramProgress");}
  @Test public void rewoundProgressAndLiveEdgeUseDistinctPartsOfTheSameTimeline()throws Exception{f.state.position=30000;f.state.duration=120000;call("cobraUpdateTimeshiftSeek");assertEquals(250,line().getProgress());assertEquals(1000,line().getSecondaryProgress());assertEquals(250,f.seek().getProgress());assertTrue(f.seek().getContentDescription().toString().contains("live edge"));assertNotEquals(line().getProgressTintList().getDefaultColor(),line().getSecondaryProgressTintList().getDefaultColor());}
  @Test public void returningToLiveSynchronizesThumbWithoutRemovingLiveEnd()throws Exception{f.state.position=120000;call("cobraUpdateTimeshiftSeek");assertEquals(1000,line().getProgress());assertEquals(1000,line().getSecondaryProgress());assertEquals(1000,f.seek().getProgress());}
  @Test public void providerCatchupEndpointIsNeverPresentedAsCurrentLiveEdge()throws Exception{put(a,"mCobraProviderCatchupActive",true);call("cobraUpdateTimeshiftSeek");assertEquals(0,line().getSecondaryProgress());assertFalse(f.seek().getContentDescription().toString().contains("live edge"));}
  @Test public void unavailableTimelineClearsOldLiveShading()throws Exception{call("cobraUpdateTimeshiftSeek");f.state.seekable=false;call("cobraUpdateTimeshiftSeek");assertEquals(0,line().getSecondaryProgress());assertEquals(View.GONE,f.seek().getVisibility());}
  @Test public void dragPreviewKeepsItsPositionWhileLiveEndStaysVisible()throws Exception{call("cobraUpdateTimeshiftSeek");put(a,"mCobraTimeshiftDragging",true);f.seek().setProgress(300);line().setProgress(300);f.state.position=70000;call("cobraUpdateTimeshiftSeek");assertEquals(300,line().getProgress());assertEquals(300,f.seek().getProgress());assertEquals(1000,line().getSecondaryProgress());}
  @Test public void allAppearanceModesRenderDifferentPlayedAndLiveWindowPixels()throws Exception{
    for(String mode:new String[]{"light","dark","oled","system"}){f.prefs.edit().putString("cobra_appearance_mode",mode).commit();call("cobraBuildPlayerChrome");f.settle();f.state.position=30000;call("cobraUpdateTimeshiftSeek");ProgressBar bar=line();bar.measure(View.MeasureSpec.makeMeasureSpec(400,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(8,View.MeasureSpec.EXACTLY));bar.layout(0,0,400,8);Bitmap b=Bitmap.createBitmap(400,8,Bitmap.Config.ARGB_8888);bar.draw(new Canvas(b));assertNotEquals(mode,b.getPixel(50,4),b.getPixel(300,4));b.recycle();}
  }
  @Test public void openSheetRecomputesHeightAfterWindowResize()throws Exception{
    f.ui.measure(a,1500,436);call("cobraShowChannelPreferences",get(a,"mPlaying"));f.ui.measure(a,1500,436);View panel=a.getWindow().getDecorView().findViewWithTag("cobra_sheet_panel");int shortHeight=panel.getHeight();assertTrue(shortHeight<=436);
    f.ui.measure(a,412,915);f.ui.frames(20);f.ui.measure(a,412,915);assertTrue("Open sheet must gain space after leaving short split-screen",panel.getHeight()>shortHeight);assertTrue(panel.getHeight()<=915);
  }
  @Test public void foldAdaptiveUsesActualSplitWindowWithoutCroppingOrRetuning()throws Exception{
    Cobra2103199DisplayRegressionTest g=new Cobra2103199DisplayRegressionTest();g.before();try{Cobra2103199DisplayRegressionTest.Controlled c=g.new Controlled();TextureView t=g.texture(1500,436);g.bind(c,g.channel(0),t,true);g.mode(g.channel(0),12);
      for(int[] size:new int[][]{{1500,436},{412,915},{1812,2176},{2176,1812},{904,2316},{1500,436}}){g.resize((View)t.getParent(),size[0],size[1]);CobraNavigationUiTest.call(g.a,"applyCobraAspectTransform");RectF r=g.rendered(t);assertEquals(16f/9f,r.width()/r.height(),.001f);assertTrue(r.width()<=size[0]+.01f);assertTrue(r.height()<=size[1]+.01f);assertTrue(Math.abs(r.width()-size[0])<.02f||Math.abs(r.height()-size[1])<.02f);assertFalse(c.writes.contains("prepare"));assertFalse(c.writes.contains("release"));}
    }finally{g.after();}
  }
}
