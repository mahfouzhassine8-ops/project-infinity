package com.projectinfinity.kodi;
import android.app.Application;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadow.api.Shadow;
import org.robolectric.util.ReflectionHelpers;

/** Signed435 owner, original drawer input and native views. Host trace only. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,instrumentedPackages={"com.projectinfinity.kodi"},shadows={CobraCardsLayoutTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraDrawerGeometry435Test {
 static Object get(Object o,String n)throws Exception{return CobraCardsLayoutTest.get(o,n);}
 static void pulses(CobraCardsLayoutTest.Fixture f,int count){
  for(int i=0;i<count;i++){
   Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));
   Object receiver=ReflectionHelpers.getField(Choreographer.getInstance(),"mDisplayEventReceiver");
   ReflectionHelpers.callInstanceMethod(Shadow.extract(receiver),"onVsync");
   Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));f.layout();
  }
 }
 static JSONObject metrics(CobraCardsLayoutTest.Fixture f)throws Exception{
  View shell=(View)get(f.a,"mCobraGuideShell"),stage=(View)get(f.a,"mStage"),decor=f.a.getWindow().getDecorView();int[] pos=new int[2];shell.getLocationInWindow(pos);
  WindowInsets insets=shell.getRootWindowInsets();
  JSONObject x=new JSONObject().put("shell_raw_width",shell.getWidth()).put("shell_raw_height",shell.getHeight()).put("shell_window_x",pos[0]).put("shell_window_y",pos[1]).put("stage_translation_x",stage.getTranslationX()).put("stage_scale_x",stage.getScaleX()).put("decor_width",decor.getWidth()).put("decor_height",decor.getHeight()).put("root_insets_nonnull",insets!=null);
  if(insets!=null)x.put("insets_ltrb",new JSONArray(new int[]{insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom()})).put("computed_cards_right_loss",Math.max(0,pos[0]+shell.getWidth()-decor.getWidth()+insets.getSystemWindowInsetRight()));
  for(String field:new String[]{"mCobraModeToolbar","mCobraGuideVideo","mCobraGuideDetails","mCobraGuideBrowser","mCobraGuideList"}){View v=(View)get(f.a,field);x.put(field,new JSONArray(new int[]{v.getLeft(),v.getTop(),v.getWidth(),v.getHeight()}));}
  return x.put("columns",((GridView)get(f.a,"mCobraGuideList")).getNumColumns()).put("IO_admitted",f.io.admitted.size());
 }
 @Test public void signed435DrawerTranslationAndInsetGeometry()throws Exception{
  new CobraCardsLayoutTest().frames();CobraCardsLayoutTest.nativeWarmThemeSetup();
  CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1600,1680,320);f.a.getWindow().setLayout(1600,1680);pulses(f,3);
  JSONObject result=new JSONObject().put("signed435_before",metrics(f));
  View button=((ViewGroup)get(f.a,"mCobraModeToolbar")).getChildAt(0);assertTrue(button.hasOnClickListeners());f.press(button);pulses(f,12);
  assertNotNull("Actual experience drawer is a Decor overlay",f.a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer"));
  result.put("signed435_after_open",metrics(f));
  // Re-run only the ORIGINAL existing restyle path while drawer is open, as
  // happens on legitimate style/layout refreshes. No substitute sizing method.
  CobraCardsLayoutTest.call(f.a,"cobraRestyleGuide");pulses(f,3);result.put("signed435_after_native_restyle",metrics(f));
  CobraCardsLayoutTest.call(f.a,"closeCobraExperienceDrawer");pulses(f,12);result.put("signed435_after_close",metrics(f));
  result.put("kind","HOST_ONLY_REAL_NATIVE_DRAWER_POINTER_AND_FRAME_TRACE").put("physical_Fold","NOT_RUN").put("decoder","NOT_RUN").put("shutdown","NOT_RUN");
  Path out=Paths.get(System.getProperty("drawer.output"));Files.createDirectories(out);Files.write(out.resolve("SIGNED435-DRAWER-GEOMETRY.json"),(result.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
 }
}
