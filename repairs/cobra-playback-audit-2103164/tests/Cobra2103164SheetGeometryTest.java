package com.projectinfinity.kodi;
import android.app.*;
import android.content.*;
import android.content.res.Configuration;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.Cobra2103164RegressionTest.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103164SheetGeometryTest {
 final Cobra2103164RegressionTest f=new Cobra2103164RegressionTest();
 @Before public void before(){f.before();}
 int px(InfinityLiveActivity a,int dp){return Math.round(dp*a.getResources().getDisplayMetrics().density);}
 void bounds(InfinityLiveActivity a,int w,int h,int top,int bottom)throws Exception{
  FrameLayout scrim=(FrameLayout)get(a,"mCobraActionSheet");assertNotNull(scrim);
  View panel=scrim.getChildAt(0);assertEquals("Bottom-center placement "+scrim.getWidth()+"x"+scrim.getHeight()+" parent "+((View)scrim.getParent()).getWidth()+" root "+a.getWindow().getDecorView().getWidth(),w/2f,(panel.getLeft()+panel.getRight())/2f,1f);
  assertTrue("Header must remain inside top safe area",panel.getTop()>=top+px(a,12));
  assertEquals("Bottom anchor must remain inside navigation area",h-bottom-px(a,12),panel.getBottom(),1f);
  assertTrue(panel.getLeft()>=px(a,12));assertTrue(panel.getRight()<=w-px(a,12));
  View close=f.ui.description(panel,"Close menu");assertNotNull(close);assertTrue(close.getHeight()>=px(a,48));
 }
 @Test public void moreAndEveryVideoSettingsSubmenuUseSameAnchorAcrossSizes()throws Exception{
  int[][] sizes={{412,915},{915,412},{600,340},{840,700},{320,720}};
  for(int[] size:sizes){int w=size[0],h=size[1];RuntimeEnvironment.setQualifiers("w"+w+"dp-h"+h+"dp-"+(w>h?"land":"port")+"-mdpi");
   InfinityLiveActivity a=f.activity();try{
    Cobra2103164RegressionTest.Video v=f.fullscreen(a,w,h);Object texture=get(a,"mPlayerTexture");
    for(String item:new String[]{"Aspect / Display","Channel playback","Audio & subtitles","Health Center"}){
      call(a,"closeCobraActionSheet");View more=f.ui.description(a.getWindow().getDecorView(),"More");assertNotNull(more);more.performClick();f.ui.measure(a,w,h);bounds(a,w,h,0,0);
      FrameLayout scrim=(FrameLayout)get(a,"mCobraActionSheet");View row=f.clickable(f.text(scrim,item));assertNotNull(item,row);row.performClick();f.ui.measure(a,w,h);bounds(a,w,h,0,0);
      assertSame(v.player,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));assertFalse(v.commands.contains("release"));assertFalse(v.commands.contains("prepare"));
    }
   }finally{f.clean(a);}
  }
 }
 @Test public void systemBarsAndSideCutoutInsetsAreRespected()throws Exception{
  RuntimeEnvironment.setQualifiers("w915dp-h412dp-land-mdpi");InfinityLiveActivity a=f.activity();try{
   f.fullscreen(a,915,412);call(a,"showPlayerSettingsDrawer");f.ui.measure(a,915,412);
   FrameLayout scrim=(FrameLayout)get(a,"mCobraActionSheet");
   WindowInsets insets=new WindowInsets.Builder().setSystemWindowInsets(Insets.of(0,24,0,30)).build();scrim.dispatchApplyWindowInsets(insets);f.ui.measure(a,915,412);bounds(a,915,412,24,30);
   WindowInsets side=new WindowInsets.Builder().setSystemWindowInsets(Insets.of(40,0,28,0)).build();scrim.dispatchApplyWindowInsets(side);f.ui.measure(a,915,412);View panel=scrim.getChildAt(0);
   assertTrue(panel.getLeft()>=52);assertTrue(panel.getRight()<=915-40);assertEquals((40+915-28)/2f,(panel.getLeft()+panel.getRight())/2f,1f);
  }finally{f.clean(a);}
 }
 @Test public void rotatingWithMenuOpenReflowsWithoutReplacingVideoOrPanel()throws Exception{
  InfinityLiveActivity a=f.activity();try{
   Cobra2103164RegressionTest.Video v=f.fullscreen(a,412,915);call(a,"showPlayerSettingsDrawer");f.ui.measure(a,412,915);Object sheet=get(a,"mCobraActionSheet"),texture=get(a,"mPlayerTexture");
   RuntimeEnvironment.setQualifiers("w915dp-h412dp-land-mdpi");org.robolectric.shadows.ShadowDisplayManager.changeDisplay(android.view.Display.DEFAULT_DISPLAY,"w915dp-h412dp-land-mdpi");a.onConfigurationChanged(a.getResources().getConfiguration());
   // A resource qualifier change alone does not resize an already attached test window.
   // Deliver the framework window-resize event, then measure the real views normally.
   Object root=call(a.getWindow().getDecorView(),"getViewRootImpl");
   ((org.robolectric.shadows.ShadowViewRootImpl)org.robolectric.shadow.api.Shadow.extract(root)).callDispatchResized();
   f.ui.measure(a,915,412);
   assertSame(sheet,get(a,"mCobraActionSheet"));assertSame(texture,get(a,"mPlayerTexture"));assertSame(v.player,get(a,"mPlayer"));bounds(a,915,412,0,0);
  }finally{f.clean(a);}
 }
 @Test public void highDensitySheetControlsStayReachable()throws Exception{
  RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-xxhdpi");InfinityLiveActivity a=f.activity();try{
   f.fullscreen(a,1236,2745);call(a,"showPlayerSettingsDrawer");f.ui.measure(a,1236,2745);bounds(a,1236,2745,0,0);
  }finally{f.clean(a);}
 }
 @Test public void paletteStylesCannotReturnVideoSubmenusToMiddleScreen()throws Exception{
  RuntimeEnvironment.setQualifiers("w915dp-h412dp-land-mdpi");
  for(String mode:new String[]{"light","dark","oled"}){
   CobraVisualRuntimeTest theme=new CobraVisualRuntimeTest();theme.context=RuntimeEnvironment.getApplication();
   JSONObject root=theme.root("sheet-"+mode);root.getJSONObject("base").put("styles",new JSONObject().put("sheet.channel-aspect",new JSONObject().put("fill",mode.equals("light")?"#F0F5FA":mode.equals("oled")?"#000000":"#0A1522").put("radius_dp",20).put("stroke_width_dp",1).put("stroke","#60B7ED")));
   theme.activate(theme.install(root));InfinityLiveActivity a=f.activity();try{
    ((SharedPreferences)get(a,"mPrefs")).edit().putString("cobra_appearance_mode",mode).commit();call(a,"cobraApplyAppearanceSettings");
    f.fullscreen(a,915,412);call(a,"showCobraAspectPicker");f.ui.measure(a,915,412);bounds(a,915,412,0,0);f.ui.frames(15);
    FrameLayout scrim=(FrameLayout)get(a,"mCobraActionSheet");TextView text=(TextView)f.text(scrim,"Best Fit");assertNotNull(text);
    int ink=text.getCurrentTextColor();boolean bright=Color.red(ink)+Color.green(ink)+Color.blue(ink)>384;
    assertEquals("Palette text contrast must match the actual sheet surface",!"light".equals(mode),bright);
    f.shot(a,"video-display-"+mode);
   }finally{f.clean(a);theme.cleanup();}
  }
 }
}
