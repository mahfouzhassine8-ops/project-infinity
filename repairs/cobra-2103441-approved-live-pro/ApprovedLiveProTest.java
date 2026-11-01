package com.projectinfinity.kodi;

import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.lang.ref.WeakReference;
import java.time.Duration;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.robolectric.Shadows;
import static org.junit.Assert.*;

/** Exact compiled Cobra owner; real views/touch, controlled ExoPlayer, no hardware claims. */
public class ApprovedLiveProTest extends PlayingRowAndProViewportTest {
 static Object holder(View row)throws Exception {
  java.lang.reflect.Field field=CobraCardsTiles.class.getDeclaredField("HOLDERS");field.setAccessible(true);
  return ((WeakReference)((Map)field.get(null)).get(row)).get();
 }
 static TextView live(View row)throws Exception{return (TextView)get(holder(row),"live");}
 static Drawable indicator(View row)throws Exception{return live(row).getCompoundDrawables()[0];}
 static boolean pulse(View row)throws Exception {
  Class<?> type=Class.forName("com.projectinfinity.kodi.CobraCardsTiles$LivePlayback");
  java.lang.reflect.Field field=type.getDeclaredField("STATES");field.setAccessible(true);
  return (Boolean)get(((Map)field.get(null)).get(indicator(row)),"pulse");
 }
 static String dotPixels(View row)throws Exception {
  Drawable d=indicator(row);Rect r=d.getBounds();assertTrue(r.width()>0&&r.height()>0);
  Bitmap b=Bitmap.createBitmap(r.width(),r.height(),Bitmap.Config.ARGB_8888);d.draw(new Canvas(b));
  int[] colors=new int[b.getWidth()*b.getHeight()];b.getPixels(colors,0,b.getWidth(),0,0,b.getWidth(),b.getHeight());b.recycle();
  java.nio.ByteBuffer raw=java.nio.ByteBuffer.allocate(colors.length*4);for(int color:colors)raw.putInt(color);return CobraCardsLayoutTest.hash(raw.array());
 }
 static void publish(CobraCardsLayoutTest.Fixture f)throws Exception{call(f.a,"cobraRefreshPlayingIndicators");frames();}
 static void staticDot(View row)throws Exception{
  assertFalse(pulse(row));String first=dotPixels(row);
  for(int i=0;i<4;i++){Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(330));assertEquals("Nonplaying LIVE is static",first,dotPixels(row));}
 }
 @Test public void cardsLiveDotPlaybackStatesAndIdentity()throws Exception{
  JSONArray results=new JSONArray();
  for(int[] size:new int[][]{{1080,2520,480},{1600,1800,240}})for(String theme:new String[]{"light","dark","oled"}){
   CobraCardsLayoutTest.Fixture f=fixture("cards",size[0],size[1],size[2],theme);
   View a=grid(f).getChildAt(0),b=grid(f).getChildAt(1);Object player=f.player,texture=get(f.a,"mCobraPreviewTexture");
   assertTrue(pulse(a));staticDot(b);assertNull("No duplicate separate playing indicator",dot(a).getParent());assertFalse(dot(a).isAttachedToWindow());
   put(f.a,"mGuidePreviewChannel",f.channels.get(1));publish(f);assertTrue("Selection is not playback identity",pulse(a));staticDot(b);
   f.input.ready=false;publish(f);staticDot(a);
   f.input.ready=true;f.input.state=androidx.media3.common.Player.STATE_BUFFERING;publish(f);staticDot(a);
   f.input.state=androidx.media3.common.Player.STATE_READY;publish(f);assertTrue(pulse(a));
   put(f.binding,"channel",f.channels.get(1));publish(f);staticDot(a);assertTrue(pulse(b));
   CobraCardsTiles.bind(f.a,(LinearLayout)b,f.channels.get(8),8);frames();staticDot(b);
   CobraCardsTiles.bind(f.a,(LinearLayout)b,f.channels.get(1),1);frames();assertTrue(pulse(b));
   f.input.state=androidx.media3.common.Player.STATE_ENDED;publish(f);staticDot(b);
   f.input.state=androidx.media3.common.Player.STATE_IDLE;publish(f);staticDot(b);
   f.input.state=androidx.media3.common.Player.STATE_READY;publish(f);assertTrue(pulse(b));
   assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertEquals(0,requests);
   results.put(new JSONObject().put("viewport",new JSONArray(size)).put("theme",theme).put("ready_pause_buffer_resume_switch_recycle_end_stop",true).put("separate_dot_attached",false));
  }
  save("LIVE-STATES",new JSONObject().put("cases",results).put("physical_Fold","NOT_TESTED"));
 }
 @Test public void cardsLiveDotCyclesAndOriginalGeometry()throws Exception{
  JSONArray results=new JSONArray();
  for(int[] size:new int[][]{{1080,2520,480},{1600,1800,240}})for(String theme:new String[]{"light","dark","oled"})for(boolean cinema:new boolean[]{false,true}){
   CobraCardsLayoutTest.Fixture f=fixture("cards",size[0],size[1],size[2],theme);View row=grid(f).getChildAt(0);TextView label=live(row);Drawable d=indicator(row);
   Rect before=bounds(label),icon=new Rect(d.getBounds());int spacing=label.getCompoundDrawablePadding();
   f.prefs.edit().putBoolean("cobra_night_cinema",cinema).commit();dotPixels(row);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(2000));
   long period=InfinityLiveActivity.CobraPlayingIndicatorPolicy.pulsePeriodMs(cinema);long now=SystemClock.uptimeMillis();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(period-now%period));
   List<String> phases=new ArrayList<>();for(int i=0;i<12;i++){phases.add(dotPixels(row));Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(period/4));}
   for(int cycle=0;cycle<3;cycle++)assertTrue("LIVE visibly pulses each complete cycle",new HashSet<>(phases.subList(cycle*4,cycle*4+4)).size()>=3);
   for(int i=0;i<4;i++){assertEquals(phases.get(i),phases.get(i+4));assertEquals(phases.get(i),phases.get(i+8));}
   f.input.ready=false;publish(f);assertEquals(before,bounds(label));assertEquals(icon,d.getBounds());assertEquals(spacing,label.getCompoundDrawablePadding());assertEquals("LIVE",label.getText().toString());
   assertNull(dot(row).getParent());staticDot(row);
   results.put(new JSONObject().put("viewport",new JSONArray(size)).put("theme",theme).put("night_cinema",cinema).put("period_ms",period).put("complete_cycles",3).put("phase_pixels",new JSONArray(phases)).put("label_bounds",before.toShortString()).put("dot_bounds",icon.toShortString()));
  }
  save("LIVE-CYCLES-GEOMETRY",new JSONObject().put("cases",results).put("mockup_visual_match","PENDING_IMAGE_ACCESS"));
 }
 @Test public void cardsPreviewAndContextRealPresses()throws Exception{
  JSONArray cases=new JSONArray();
  for(int[] size:new int[][]{{1080,2520,480},{1600,1800,240}})for(String theme:new String[]{"light","dark"}){
   CobraCardsLayoutTest.Fixture f=fixture("cards",size[0],size[1],size[2],theme);Object player=f.player,texture=get(f.a,"mCobraPreviewTexture");int first=grid(f).getFirstVisiblePosition();
   for(int mode=0;mode<14;mode++){
    String key=(String)call(f.a,"cobraPreferenceKey",f.channels.get(0));Object prefs=call(f.a,"cobraReadPreferences",key);put(prefs,"aspect",mode);call(f.a,"cobraSavePreferences",f.channels.get(0),key,prefs,false);
    f.press((View)get(f.a,"mCobraPreviewHost"));frames();CobraActualFullscreenMoreTest.assertSheetVisible(f,"preview-actions");
    assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertEquals(first,grid(f).getFirstVisiblePosition());
    f.a.onBackPressed();frames();assertNull(get(f.a,"mCobraActionSheet"));
   }
   View row=grid(f).getChildAt(0);f.press((View)get(holder(row),"more"));frames();
   assertNotNull("Actual Cards channel menu press opens its existing sheet",get(f.a,"mCobraActionSheet"));assertTrue(((View)get(f.a,"mCobraSheetPanel")).isShown());
   cases.put(new JSONObject().put("viewport",new JSONArray(size)).put("theme",theme).put("preview_real_presses",14).put("channel_menu",String.valueOf(get(f.a,"mCobraSheetKind"))));
   f.a.onBackPressed();frames();assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertTrue(pulse(row));
  }
  save("LIVE-PREVIEW-CONTEXT-TOUCH",new JSONObject().put("cases",cases).put("input","Actual decor DOWN/UP; no direct click callbacks"));
 }
 @Test public void cardsNativePlaybackEventsAndRenderedRows()throws Exception{
  JSONArray cases=new JSONArray();
  for(int[] size:new int[][]{{1080,2520,480},{1600,1800,240}})for(String theme:new String[]{"light","dark"}){
   CobraCardsLayoutTest.Fixture f=fixture("cards",size[0],size[1],size[2],theme);View row=grid(f).getChildAt(0);
   f.input.ready=false;call(f.binding,"onIsPlayingChanged",false);frames();staticDot(row);
   f.input.ready=true;f.input.state=androidx.media3.common.Player.STATE_BUFFERING;call(f.binding,"onIsPlayingChanged",false);frames();staticDot(row);
   f.input.state=androidx.media3.common.Player.STATE_READY;call(f.binding,"onIsPlayingChanged",true);frames();assertTrue(pulse(row));
   dotPixels(row);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(2000));
   String name="live-render-"+size[0]+"-"+theme;
   image((View)get(f.a,"mCobraGuideShell"),name);
   image(row,name+"-playing-row");
   image(grid(f).getChildAt(1),name+"-static-row");
   cases.put(new JSONObject().put("viewport",new JSONArray(size)).put("theme",theme).put("native_callback","CobraPlayerBinding.onIsPlayingChanged -> cobraUpdatePlaybackLabels -> existing indicator refresh").put("render",name+".png"));
  }
  save("LIVE-NATIVE-CALLBACKS-RENDER",new JSONObject().put("cases",cases).put("mockup_match","PENDING_ACCESS").put("physical_Fold","NOT_TESTED"));
 }
}
