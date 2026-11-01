package com.projectinfinity.kodi;
import android.app.*;import android.content.*;import android.content.res.Configuration;import android.view.*;import android.widget.*;import java.lang.reflect.*;import java.util.*;
import org.junit.*;import static org.junit.Assert.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;import androidx.media3.exoplayer.ExoPlayer;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w360dp-h840dp-port-480dpi",instrumentedPackages={"com.projectinfinity.kodi"},shadows={CobraActualFullscreenMoreTest.Trace.class})
@LooperMode(LooperMode.Mode.PAUSED) @GraphicsMode(GraphicsMode.Mode.NATIVE)
public class RotationAudioTest {
 static Object get(Object a,String n)throws Exception{return CobraCardsLayoutTest.get(a,n);}
 static Object call(Object a,String n,Object...v)throws Exception{return CobraCardsLayoutTest.call(a,n,v);}
 static void set(Object a,String n,Object v)throws Exception{CobraCardsLayoutTest.set(a,n,v);}
 @Before public void frames(){new CobraCardsLayoutTest().frames();}
 @Test public void allPhysicalOrientationMappingsAndTwoStatePolicy(){
  int[][] configs={{1,2,1,2},{2,1,2,1}};int[][] expected={{1,0,9,8},{0,9,8,1}};
  for(int natural=0;natural<2;natural++)for(int r=0;r<4;r++)assertEquals(expected[natural][r],CobraRotationPolicy.displayedOrientation(configs[natural][r],r));
  Activity a=Robolectric.buildActivity(Activity.class).setup().get();SharedPreferences p=CobraJavaPersistence.preferences(a,"cobra_player_rotation",0);p.edit().clear().commit();
  assertFalse(CobraRotationPolicy.apply(a,false));CobraRotationPolicy.toggle(a);assertTrue(CobraRotationPolicy.apply(a,false));assertEquals(10,a.getRequestedOrientation());
  CobraRotationPolicy.toggle(a);assertTrue(CobraRotationPolicy.apply(a,false));int locked=a.getRequestedOrientation();assertTrue(locked==1||locked==9);
  assertTrue(CobraRotationPolicy.apply(a,true));assertEquals(-1,a.getRequestedOrientation());CobraRotationPolicy.apply(a,false);assertEquals(locked,a.getRequestedOrientation());
  CobraRotationPolicy.toggle(a);CobraRotationPolicy.apply(a,false);assertEquals(10,a.getRequestedOrientation());
 }
 @Test public void nativeFullscreenActualRotationAndAudioPresses()throws Exception{
  CobraCardsLayoutTest.Fixture f=CobraActualFullscreenMoreTest.fixture();CobraActualFullscreenMoreTest.actualPreviewPress(f);
  // The host cannot execute Android directory fsync in the bridge constructor.
  // Supply only its activity state; execute the actual compiled orientation methods.
  java.lang.reflect.Field uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);
  Object bridge=((sun.misc.Unsafe)uf.get(null)).allocateInstance(InfinityCobraDeviceBridge.class);
  set(bridge,"activity",f.a);set(bridge,"paused",false);set(f.a,"mDeviceBridge",bridge);
  View chrome=(View)get(f.a,"mPlayerChrome");View rotate=chrome.findViewWithTag("cobra_player_rotation");assertNotNull(rotate);
  Object player=get(f.a,"mPlayer");f.press(rotate);assertEquals(1,CobraJavaPersistence.preferences(f.a,"cobra_player_rotation",0).getInt("mode",0));assertEquals(10,f.a.getRequestedOrientation());
  f.press(rotate);assertEquals(0,CobraJavaPersistence.preferences(f.a,"cobra_player_rotation",0).getInt("mode",1));assertTrue(f.a.getRequestedOrientation()==1||f.a.getRequestedOrientation()==9);assertSame(player,get(f.a,"mPlayer"));
  View button=chrome.findViewWithTag("cobra_fullscreen_audio");assertNotNull(button);assertEquals("Mute",button.getContentDescription());
  f.press(button);assertTrue((Boolean)call(f.a,"cobraMediaMuted",player));assertEquals("Unmute",button.getContentDescription());assertSame(player,get(f.a,"mPlayer"));
  f.press(button);assertFalse((Boolean)call(f.a,"cobraMediaMuted",player));assertEquals("Mute",button.getContentDescription());assertSame(player,get(f.a,"mPlayer"));
 }
 @Test public void selectedAudioVolumeRestoredWithoutStreamRestart()throws Exception{
  CobraCardsLayoutTest.Fixture f=CobraActualFullscreenMoreTest.fixture();CobraActualFullscreenMoreTest.actualPreviewPress(f);
  final float[] volume={.37f};final int[] starts={0};CobraCardsLayoutTest.Playback input=new CobraCardsLayoutTest.Playback();
  Object player=Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},(o,m,args)->{
   if(m.getName().equals("getVolume"))return volume[0];if(m.getName().equals("setVolume")){volume[0]=(Float)args[0];return null;}
   if(m.getName().equals("prepare")||m.getName().equals("setMediaItem")||m.getName().equals("setMediaSource"))starts[0]++;
   return input.invoke(o,m,args);
  });
  Object binding=CobraCardsLayoutTest.construct("CobraPlayerBinding",f.a,player,f.channels.get(0));((Map)get(f.a,"mCobraPlayerBindings")).put(player,binding);set(f.a,"mPlayer",player);
  View button=((View)get(f.a,"mPlayerChrome")).findViewWithTag("cobra_fullscreen_audio");CobraFullscreenAudio.refresh(f.a);f.press(button);assertEquals(0f,volume[0],0f);f.press(button);assertEquals(.37f,volume[0],.00001f);assertEquals(0,starts[0]);volume[0]=0f;call(binding,"onVolumeChanged",0f);assertEquals("Unmute",button.getContentDescription());volume[0]=.24f;call(binding,"onVolumeChanged",.24f);assertEquals("Mute",button.getContentDescription());assertEquals(0,starts[0]);
 }
 @Test public void fullscreenControlsAcrossModesPanesAndThemes()throws Exception{
  for(int[] pane:new int[][]{{1080,2520,480},{1600,1800,320}}){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",pane[0],pane[1],pane[2]);f.a.getWindow().setLayout(pane[0],pane[1]);CobraActualFullscreenMoreTest.pulses(3);CobraActualFullscreenMoreTest.actualPreviewPress(f);Object player=get(f.a,"mPlayer");
   for(String mode:new String[]{"mobile","compact","grid","cards","focus"})for(String theme:new String[]{"light","dark","oled"}){
    f.prefs.edit().putString("cobra_appearance_mode",theme).commit();f.mode(mode);call(f.a,"cobraBuildPlayerChrome");CobraActualFullscreenMoreTest.pulses(3);
    View chrome=(View)get(f.a,"mPlayerChrome"),audio=chrome.findViewWithTag("cobra_fullscreen_audio");assertNotNull(mode+" "+theme,audio);
    LinearLayout tools=(LinearLayout)audio.getParent();assertSame(audio,tools.getChildAt(1));assertEquals("Display",tools.getChildAt(2).getContentDescription());assertEquals("PiP",tools.getChildAt(4).getContentDescription());
    assertTrue(audio.getWidth()>=Math.round(44*f.a.getResources().getDisplayMetrics().density));f.press(audio);assertTrue((Boolean)call(f.a,"cobraMediaMuted",player));f.press(audio);assertFalse((Boolean)call(f.a,"cobraMediaMuted",player));
    assertSame(player,get(f.a,"mPlayer"));assertNotNull(chrome.findViewWithTag("cobra_player_rotation"));
   }
  }
 }

 @Test public void multiviewMuteTargetsSelectedAudioTileOnly()throws Exception{
  CobraCardsLayoutTest.Fixture f=CobraActualFullscreenMoreTest.fixture();CobraActualFullscreenMoreTest.actualPreviewPress(f);
  final float[][] levels={{.21f},{.63f}};Object[] players=new Object[2];
  for(int i=0;i<2;i++){final int index=i;CobraCardsLayoutTest.Playback input=new CobraCardsLayoutTest.Playback();
   players[i]=Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},(o,m,args)->{
    if(m.getName().equals("getVolume"))return levels[index][0];if(m.getName().equals("setVolume")){levels[index][0]=(Float)args[0];return null;}return input.invoke(o,m,args);});
   Object binding=CobraCardsLayoutTest.construct("CobraPlayerBinding",f.a,players[i],f.channels.get(i));((Map)get(f.a,"mCobraPlayerBindings")).put(players[i],binding);
  }
  ExoPlayer[] typed={(ExoPlayer)players[0],(ExoPlayer)players[1]};set(f.a,"mMultiPlayers",typed);set(f.a,"mAudioTile",1);set(f.a,"mCobraMultiFullscreenActive",true);set(f.a,"mMultiOverlay",new FrameLayout(f.a));
  View button=((View)get(f.a,"mPlayerChrome")).findViewWithTag("cobra_fullscreen_audio");CobraFullscreenAudio.refresh(f.a);f.press(button);assertEquals(.21f,levels[0][0],0);assertEquals(0f,levels[1][0],0);f.press(button);assertEquals(.63f,levels[1][0],.00001f);assertEquals(1,get(f.a,"mAudioTile"));
 }

}
