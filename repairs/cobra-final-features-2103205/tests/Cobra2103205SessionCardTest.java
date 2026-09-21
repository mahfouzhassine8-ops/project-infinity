package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowDisplay;
import static org.junit.Assert.*;

/** Production Health Center, synthetic guide/player/format counters. No device, decoder or network proof. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205SessionCardTest {
  final CobraNavigationUiTest ui=new CobraNavigationUiTest();
  final CobraHealthUiTest health=new CobraHealthUiTest();
  @Before public void clock(){ui.clock();}
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object call(Object o,String n,Object... args)throws Exception{return CobraNavigationUiTest.call(o,n,args);}
  View tag(InfinityLiveActivity a,String name){return a.getWindow().getDecorView().findViewWithTag(name);}
  JSONObject card(InfinityLiveActivity a)throws Exception{return (JSONObject)call(a,"cobraPlaybackSessionCardSnapshot");}
  String summary(InfinityLiveActivity a){return ((TextView)tag(a,"cobra-health-summary")).getText().toString();}
  static final class CardPlayer implements InvocationHandler {
    final CobraHealthUiTest.PlayerDouble base;Format format=new Format.Builder().setWidth(1920).setHeight(1080)
        .setSampleMimeType("video/avc").setCodecs("avc1.640028").setFrameRate(29.97f).build();
    long buffered=5000L,live=12000L;
    CardPlayer(InfinityLiveActivity a){base=new CobraHealthUiTest.PlayerDouble(a);
      base.player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);}
    public Object invoke(Object proxy,Method method,Object[] args){
      if("getVideoFormat".equals(method.getName()))return format;
      if("getTotalBufferedDuration".equals(method.getName()))return buffered;
      if("getCurrentLiveOffset".equals(method.getName()))return live;
      return base.invoke(proxy,method,args);
    }
  }
  void attach(InfinityLiveActivity a,CardPlayer p)throws Exception{call(a,"cobraOpenLiveTv");ui.measure(a,412,915);health.attach(a,p.base);p.base.writes.clear();}
  void shot(InfinityLiveActivity a,String name)throws Exception{
    View v=a.getWindow().getDecorView();Bitmap bitmap=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(bitmap));
    File root=new File(System.getProperty("cobra.evidence"));assertTrue(root.isDirectory()||root.mkdirs());
    try(FileOutputStream out=new FileOutputStream(new File(root,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}bitmap.recycle();
  }

  @Test public void cardLivesOnlyInsideHealthCenterAndPreservesExistingActions()throws Exception{
    InfinityLiveActivity a=ui.fixture(16);try{
      assertNull(tag(a,"cobra-health-session-card"));call(a,"showCobraHealthCenter");ui.measure(a,412,915);
      View card=tag(a,"cobra-health-session-card"),sheet=(View)get(a,"mCobraActionSheet");assertNotNull(card);
      ViewParent parent=card.getParent();boolean inside=false;while(parent instanceof View){if(parent==sheet){inside=true;break;}parent=parent.getParent();}assertTrue(inside);
      for(String action:new String[]{"cobra-health-refresh","cobra-health-export","cobra-health-snapshot","cobra-health-defaults"})assertNotNull(tag(a,action));
      assertTrue(summary(a).contains("No active playback"));call(a,"closeCobraActionSheet");assertNull(tag(a,"cobra-health-session-card"));assertNull(get(a,"mCobraHealthSummary"));
    }finally{ui.clean(a);}
  }
  @Test public void sourceMetadataIsExplicitAndReadFromCurrentPlayer()throws Exception{
    InfinityLiveActivity a=ui.fixture(16);try{
      CardPlayer p=new CardPlayer(a);attach(a,p);call(a,"showCobraHealthCenter");ui.measure(a,412,915);
      assertTrue(summary(a).contains("1920 × 1080"));assertTrue(summary(a).contains("Source FPS: 29.97"));assertTrue(summary(a).contains("not measured output FPS"));
      JSONObject row=card(a).getJSONArray("sessions").getJSONObject(0);assertEquals(29.97,row.getDouble("source_fps"),0.01);assertEquals("avc1.640028",row.getString("video_codec"));
      assertEquals(5000,row.getLong("buffered_ahead_ms"));assertEquals(12000,row.getLong("live_edge_ms"));
      p.format=new Format.Builder().setWidth(1280).setHeight(720).setSampleMimeType("video/hevc").setFrameRate(50).build();
      call(a,"cobraRefreshHealthSummary");assertTrue(summary(a).contains("1280 × 720"));assertTrue(summary(a).contains("Source FPS: 50.00"));
      assertTrue(p.base.writes.isEmpty());
    }finally{ui.clean(a);}
  }
  @Test public void unknownFormatsBufferAndCountersRemainUnknownInsteadOfZeroSuccess()throws Exception{
    InfinityLiveActivity a=ui.fixture(16);try{
      CardPlayer p=new CardPlayer(a);attach(a,p);p.format=null;p.buffered=C.TIME_UNSET;p.live=C.TIME_UNSET;
      call(a,"showCobraHealthCenter");ui.measure(a,412,915);String value=summary(a);
      assertTrue(value.contains("Video Not reported"));assertTrue(value.contains("Source FPS: Not reported"));assertTrue(value.contains("Buffered ahead: Not reported"));
      JSONObject row=card(a).getJSONArray("sessions").getJSONObject(0);
      for(String field:new String[]{"video_width","video_height","source_fps","buffered_ahead_ms","live_edge_ms","observed_frames","dropped_frames"})assertTrue(field,row.isNull(field));
      assertFalse(value.contains(Long.toString(C.TIME_UNSET)));assertTrue(p.base.writes.isEmpty());
    }finally{ui.clean(a);}
  }
  @Implements(Display.class) public static class ReportedRefreshDisplay extends ShadowDisplay {
    static float reported;
    @Implementation protected float getRefreshRate(){return reported;}
  }
  @Config(shadows=ReportedRefreshDisplay.class) @Test public void currentDisplayIsObservedWithoutChangingRefreshPolicyOrEnablingOverlay()throws Exception{
    InfinityLiveActivity a=ui.fixture(16);try{
      Display display=(Display)call(a,"cobraCurrentDisplay");assertNotNull(display);ReportedRefreshDisplay.reported=90f;put(a,"mCobraActiveHz",17f);
      int requested=a.getWindow().getAttributes().preferredDisplayModeId;assertEquals(90,card(a).getDouble("display_refresh_hz"),0.01);
      ReportedRefreshDisplay.reported=120f;assertEquals(120,card(a).getDouble("display_refresh_hz"),0.01);
      assertEquals(17f,(Float)get(a,"mCobraActiveHz"),0f);assertEquals(requested,a.getWindow().getAttributes().preferredDisplayModeId);assertNull(get(a,"mCobraPerformanceOverlayView"));
    }finally{ui.clean(a);}
  }
  @Test public void repeatedCardRefreshAndExportCannotMutatePlaybackOrPreferences()throws Exception{
    InfinityLiveActivity a=ui.fixture(16);try{
      CardPlayer p=new CardPlayer(a);attach(a,p);Object texture=get(a,"mCobraPreviewTexture"),timeshift=get(a,"mCobraTimeshiftSession");
      Map<String,?> prefs=new HashMap<>(((SharedPreferences)get(a,"mPrefs")).getAll());
      CobraNavigationUiTest.PendingIo io=(CobraNavigationUiTest.PendingIo)get(a,"mIo");int queued=io.tasks.size();
      call(a,"showCobraHealthCenter");ui.measure(a,412,915);p.base.writes.clear();
      for(int i=0;i<100;i++){call(a,"cobraRefreshHealthSummary");JSONObject snapshot=new JSONObject((String)call(a,"cobraFreshHealthSnapshot"));assertNotNull(snapshot.getJSONObject("playback_session_card"));assertNotNull(snapshot.getJSONObject("network_intelligence"));}
      assertTrue(p.base.writes.isEmpty());assertSame(p.base.player,get(a,"mCobraPreviewPlayer"));assertSame(texture,get(a,"mCobraPreviewTexture"));assertSame(timeshift,get(a,"mCobraTimeshiftSession"));
      assertEquals(30000,p.base.position);assertEquals(queued,io.tasks.size());assertEquals(prefs,((SharedPreferences)get(a,"mPrefs")).getAll());
      assertEquals("not_observable_by_app",card(a).getString("call_time_audibility"));
    }finally{ui.clean(a);}
  }
  @Test public void cardSnapshotsExcludeNonCurrentBindingsAndDoNotIncludeProviderIdentity()throws Exception{
    InfinityLiveActivity a=ui.fixture(16);try{
      CardPlayer p=new CardPlayer(a);attach(a,p);Object binding=((Map<?,?>)get(a,"mCobraPlayerBindings")).get(p.base.player);
      String json=card(a).toString();assertTrue(json.contains("channel_hash"));assertFalse(json.contains("Nature One"));assertFalse(json.contains("primaryUrl"));
      put(binding,"closed",true);assertEquals(0,card(a).getInt("session_count"));assertEquals(0,card(a).getJSONArray("sessions").length());
    }finally{ui.clean(a);}
  }
  @Test(timeout=120000) public void sessionCardWrapsAndScrollsInExistingSheetAcrossThemesAndWindows()throws Exception{
    for(int[] size:new int[][]{{320,720},{720,900},{960,360}})for(String theme:new String[]{"light","dark","oled"})for(float font:new float[]{1f,2f}){
      RuntimeEnvironment.setQualifiers("w"+size[0]+"dp-h"+size[1]+"dp-"+(size[0]>size[1]?"land":"port")+"-mdpi");
      RuntimeEnvironment.setFontScale(font);
      InfinityLiveActivity a=ui.fixture(16);try{
        ((SharedPreferences)get(a,"mPrefs")).edit().putString("cobra_appearance_mode",theme).commit();
        call(a,"showCobraHealthCenter");ui.measure(a,size[0],size[1]);ui.frames(20);ui.measure(a,size[0],size[1]);
        View card=tag(a,"cobra-health-session-card"),panel=(View)get(a,"mCobraSheetPanel");TextView text=(TextView)tag(a,"cobra-health-summary");
        assertTrue(card.getWidth()>0);assertTrue(panel.getWidth()<=size[0]);assertTrue(panel.getHeight()<=size[1]);assertNotNull(text.getLayout());
        for(int line=0;line<text.getLineCount();line++)assertEquals("Health text must wrap, not ellipsize",0,text.getLayout().getEllipsisCount(line));
        shot(a,"cobra205-session-card-"+theme+"-"+size[0]+"x"+size[1]+"-font"+Math.round(font*100));
      }finally{ui.clean(a);RuntimeEnvironment.setFontScale(1f);}
    }
  }
}
