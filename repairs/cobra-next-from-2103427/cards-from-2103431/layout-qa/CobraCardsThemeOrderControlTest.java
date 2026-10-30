package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.drawable.Drawable;
import android.os.Looper;
import android.widget.TextView;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;

/** One baseline-only control of the ORIGINAL one-time renderer publication.
 * No native field reset, production stub, lifecycle teardown or signing. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 qualifiers="w358dp-h637dp-port-420dpi",instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraCardsLayoutTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraCardsThemeOrderControlTest {
  static Object get(Object o,String n)throws Exception{return CobraCardsLayoutTest.get(o,n);}
  static Object global(Class<?> type,String n)throws Exception{Field f=type.getDeclaredField(n);f.setAccessible(true);return f.get(null);}
  static JSONObject values(CobraCardsLayoutTest.Fixture f,String phase)throws Exception{
    Object renderer=get(f.a,"mVisualTheme");Class<?> type=renderer.getClass();Map bindings=(Map)get(renderer,"bindings");
    JSONObject result=new JSONObject().put("phase",phase).put("load_status",String.valueOf(global(type,"loadStatus"))).put("active_identity",System.identityHashCode(global(type,"active")))
      .put("loading_once",((AtomicBoolean)global(type,"loading")).get()).put("renderer_main_is_current",((android.os.Handler)global(type,"MAIN")).getLooper()==Looper.getMainLooper());
    TextView eyebrow=(TextView)get(f.a,"mCobraModeEyebrow"),label=((android.view.View)get(f.a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_label");
    for(Object[] pair:new Object[][]{{"eyebrow",eyebrow},{"legacy_status",label}}){TextView view=(TextView)pair[1];Object binding=bindings.get(view);JSONObject j=new JSONObject().put("attached",view.isAttachedToWindow()).put("current_spacing",view.getLetterSpacing()).put("current_padding",CobraCardsLayoutTest.padding(view)).put("current_background",view.getBackground()==null?"null":view.getBackground().getClass().getName());
      if(binding!=null)j.put("binding_original_spacing",get(binding,"spacing")).put("binding_original_padding",new JSONArray(Arrays.asList(get(binding,"l"),get(binding,"t"),get(binding,"r"),get(binding,"b")))).put("binding_original_background",get(binding,"background")==null?"null":get(binding,"background").getClass().getName()).put("slot",get(binding,"slot")).put("aliases",new JSONArray((Collection)get(binding,"aliases"))).put("waiting_for_attach",get(binding,"waitingForAttach")).put("current_native_styles",CobraCardsLayoutTest.call(renderer,"stylesFor",binding,view));
      result.put((String)pair[0],j);
    }
    return result;
  }
  static void write(JSONObject result)throws Exception{Path out=Paths.get(System.getProperty("cards.layout.output"));Files.createDirectories(out);Files.write(out.resolve(Boolean.getBoolean("cards.candidate")?"CANDIDATE-COLD-WARM-THEME.json":"NATIVE431-COLD-WARM-THEME.json"),(result.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));System.out.println("NATIVE431_THEME_CONTROL="+result);}
  @Test public void native431ColdAndWarmThemeCardsMobileControl()throws Exception{
    assertFalse(Boolean.getBoolean("cards.candidate"));control(false);
  }
  @Test public void nativeCandidateColdAndWarmThemeCardsMobileControl()throws Exception{assertTrue(Boolean.getBoolean("cards.candidate"));control(true);}
  void control(boolean candidate)throws Exception{
    new CobraCardsLayoutTest().frames();Class<?> type=Class.forName("com.projectinfinity.kodi.CobraVisualRenderer");
    assertFalse("fresh one-time native loading precondition, never reset by QA",((AtomicBoolean)global(type,"loading")).get());
    ExecutorService io=(ExecutorService)global(type,"IO");CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);
    Future<?> gate=io.submit(()->{entered.countDown();try{if(!release.await(30,TimeUnit.SECONDS))throw new AssertionError("QA ordering gate not released");}catch(InterruptedException e){Thread.currentThread().interrupt();throw new AssertionError(e);}});
    assertTrue("original native executor admitted ordering gate",entered.await(5,TimeUnit.SECONDS));
    JSONArray phases=new JSONArray();JSONObject result=new JSONObject().put("runtime",candidate?"actual current owner candidate":"exact signed431 native host baseline").put("native_global_fields_reset",false).put("phases",phases);
    CobraCardsLayoutTest.Fixture cold;
    try{cold=new CobraCardsLayoutTest.Fixture("cards");phases.put(values(cold,"cold_constructed_before_native_publication"));write(result);}finally{release.countDown();}
    gate.get(5,TimeUnit.SECONDS);io.submit(()->{}).get(5,TimeUnit.SECONDS);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));cold.layout();phases.put(values(cold,"cold_after_actual_native_IO_and_MAIN_publication"));
    cold.mode("mobile");phases.put(values(cold,"cold_cards_to_mobile_after_publication"));write(result);
    CobraCardsLayoutTest.Fixture warm=new CobraCardsLayoutTest.Fixture("cards");phases.put(values(warm,"warm_cards_constructed_after_one_time_publication"));warm.mode("mobile");phases.put(values(warm,"warm_cards_to_mobile"));write(result);
    assertTrue(((AtomicBoolean)global(type,"loading")).get());assertNotEquals("actual native publication completed",phases.getJSONObject(0).getInt("active_identity"),phases.getJSONObject(1).getInt("active_identity"));
    if(candidate){JSONObject baseline=new JSONObject(new String(Files.readAllBytes(Paths.get(System.getProperty("cards.theme.baseline"))),StandardCharsets.UTF_8));JSONArray original=baseline.getJSONArray("phases"),differences=new JSONArray();for(int phase:new int[]{2,4})for(String role:new String[]{"eyebrow","legacy_status"})for(String key:new String[]{"current_spacing","current_padding","current_background"}){Object expected=original.getJSONObject(phase).getJSONObject(role).get(key),actual=phases.getJSONObject(phase).getJSONObject(role).get(key);String difference=CobraCardsLayoutTest.diff(expected,actual,phases.getJSONObject(phase).getString("phase")+"."+role+"."+key);if(difference!=null)differences.put(difference);}result.put("independent_431_differences",differences);write(result);assertEquals("same cold/warm source-owned styles as independent signed431",0,differences.length());}
  }
}
