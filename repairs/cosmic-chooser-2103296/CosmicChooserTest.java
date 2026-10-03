package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.os.Looper;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.android.controller.ActivityController;
import java.io.File;
import java.io.FileOutputStream;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CosmicChooserTest {
  static class Calls implements InfinityGlassChooser.Actions {
    final ArrayList<String> entered=new ArrayList<>(),settings=new ArrayList<>();
    String mode;int changed,themes;
    Calls(String mode){this.mode=mode;}
    public void enter(String value){entered.add(value);}
    public void settings(String value){settings.add(value);}
    public void themes(){themes++;}
    public String appearance(){return mode;}
    public void appearanceChanged(){changed++;}
  }
  static final int[][] SIZES={{240,400},{320,640},{420,936},{658,1536},{768,1024},{1840,1536},{1024,768},{900,400},{360,240}};
  static void layout(InfinityGlassChooser ui,int w,int h){
    ui.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));ui.layout(0,0,w,h);
  }
  static Map<String,String> tree(View v,ViewGroup root){
    Map<String,String> out=new LinkedHashMap<>();walk(v,root,out);return out;
  }
  static void walk(View v,ViewGroup root,Map<String,String> out){
    if(v.getTag()!=null){Rect rect=new Rect();v.getDrawingRect(rect);root.offsetDescendantRectToMyCoords(v,rect);
      String key=v.getTag().toString();if(key.startsWith("infinity_cosmic"))key="root";
      out.put(key,v.getClass().getSimpleName()+":"+rect+":"+v.getVisibility()+":"+v.getId()+":"+v.isClickable()+":"+v.isFocusable());
    }
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)walk(g.getChildAt(i),root,out);}
  }
  static void cleanup(ActivityController<Activity> ctl){ctl.pause().stop().destroy();}

  @Test public void exactDarkLightControlAndGeometryParityAtEveryWindow(){
    RuntimeEnvironment.setQualifiers("mdpi");
    for(int[] size:SIZES){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();
      InfinityGlassChooser dark=new InfinityGlassChooser(a,new Calls("dark"));a.setContentView(dark);layout(dark,size[0],size[1]);Map<String,String> expected=tree(dark,dark);
      InfinityGlassChooser light=new InfinityGlassChooser(a,new Calls("light"));a.setContentView(light);layout(light,size[0],size[1]);
      assertEquals(size[0]+"x"+size[1],expected,tree(light,light));
      assertNull(light.findViewById(InfinityGlassChooser.PILL_INFINITY));assertNull(dark.findViewById(InfinityGlassChooser.PILL_INFINITY));
      cleanup(ctl);
    }
  }
  @Test public void routedCardsAndGearsNeverCrossLaunch(){
    for(String theme:new String[]{"dark","light","oled"}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Calls c=new Calls(theme);
      InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),c);ctl.get().setContentView(ui);layout(ui,420,936);
      ui.findViewById(InfinityGlassChooser.SETTINGS_INFINITY).performClick();ui.findViewById(InfinityGlassChooser.SETTINGS_COBRA).performClick();
      assertEquals(java.util.Arrays.asList("infinity","live"),c.settings);assertTrue(c.entered.isEmpty());
      ui.stage.infinity.performClick();ui.stage.cobra.performClick();assertEquals(java.util.Arrays.asList("infinity","live"),c.entered);
      assertFalse(ui.stage.performLongClick());assertEquals(0,c.themes);cleanup(ctl);
    }
  }
  @Test public void foldReflowRetainsSameInstancesFocusAndUsableTargets(){
    RuntimeEnvironment.setQualifiers("mdpi");ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();
    InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),new Calls("dark"));ctl.get().setContentView(ui);
    View focus=ui.stage.cobra.gear;InfinityGlassChooser.Stage stage=ui.stage;
    layout(ui,658,1536);assertTrue("Initial gear focus",focus.requestFocus());
    for(int[] size:new int[][]{{658,1536},{1840,1536},{658,1536},{900,400},{360,240}}){
      layout(ui,size[0],size[1]);assertSame(stage,ui.stage);assertTrue("Retained gear focus at "+size[0]+"x"+size[1],focus.isFocused());
      Rect left=new Rect(),right=new Rect();ui.stage.infinity.getHitRect(left);ui.stage.cobra.getHitRect(right);
      assertFalse(Rect.intersects(left,right));assertTrue(left.left>=0);assertTrue(right.right<=size[0]);
      assertEquals(left.height(),right.height());
      for(View gear:new View[]{ui.stage.infinity.gear,ui.stage.cobra.gear}){assertTrue(gear.getWidth()>=48);assertTrue(gear.getHeight()>=48);}
      assertEquals(ui.stage.infinity.mark.getWidth(),ui.stage.cobra.mark.getWidth());
    }
    cleanup(ctl);
  }
  @Test public void actualTouchAfterWindowTranslationHitsOnlyGear(){
    RuntimeEnvironment.setQualifiers("mdpi");ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Calls c=new Calls("light");
    FrameHost host=new FrameHost(ctl.get());InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),c);host.addView(ui,new ViewGroup.LayoutParams(420,936));ctl.get().setContentView(host);
    host.measure(View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(1600,View.MeasureSpec.EXACTLY));host.layout(0,0,800,1600);ui.layout(130,300,550,1236);layoutChildren(ui,420,936);
    Rect rect=new Rect();ui.stage.cobra.gear.getDrawingRect(rect);host.offsetDescendantRectToMyCoords(ui.stage.cobra.gear,rect);
    long now=android.os.SystemClock.uptimeMillis();MotionEvent down=MotionEvent.obtain(now,now,0,rect.exactCenterX(),rect.exactCenterY(),0),up=MotionEvent.obtain(now,now+30,1,rect.exactCenterX(),rect.exactCenterY(),0);
    assertTrue(host.dispatchTouchEvent(down));assertTrue(host.dispatchTouchEvent(up));down.recycle();up.recycle();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(50));
    assertEquals(java.util.Arrays.asList("live"),c.settings);assertTrue(c.entered.isEmpty());cleanup(ctl);
  }
  static void layoutChildren(InfinityGlassChooser ui,int w,int h){
    ui.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));ui.layout(ui.getLeft(),ui.getTop(),ui.getLeft()+w,ui.getTop()+h);
  }
  static class FrameHost extends android.widget.FrameLayout {FrameHost(Context c){super(c);}}

  @Test public void staticFallbackAndMotionLifecycleReleaseWithoutTouchOwnership(){
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),new Calls("dark"));ctl.get().setContentView(ui);layout(ui,420,936);
    assertFalse(ui.backdrop.isClickable());assertFalse(ui.backdrop.isFocusable());assertNotNull(ui.backdrop.plate);
    ui.backdrop.setMotionDisabled(true);assertFalse(ui.backdrop.framePending);long phase=ui.backdrop.phaseMillis;
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(1));assertEquals(phase,ui.backdrop.phaseMillis);
    ui.backdrop.onWindowFocusChanged(false);assertFalse(ui.backdrop.framePending);
    ctl.get().setContentView(new View(ctl.get()));assertFalse(ui.backdrop.attached);assertFalse(ui.backdrop.framePending);assertNull(ui.backdrop.plate);
    assertFalse(ui.stage.weatherData.started);assertNull(ui.stage.weatherData.worker);cleanup(ctl);
  }
  @Test public void realClockFullDateAndWeatherUnavailableAreNotBakedArtwork(){
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),new Calls("dark"));ctl.get().setContentView(ui);layout(ui,420,936);
    assertFalse(ui.stage.time.getText().toString().isEmpty());assertFalse(ui.stage.date.getText().toString().isEmpty());
    assertEquals(android.text.format.DateFormat.getTimeFormat(ctl.get()).format(new java.util.Date()),ui.stage.time.getText().toString());
    ui.stage.weatherData.stop();ui.stage.weatherData.cache.edit().clear().commit();ui.stage.weatherData.renderCached();assertEquals("Weather unavailable",ui.stage.weather.getText().toString());cleanup(ctl);
  }
  @Test public void fullFoldPixelSizesRespectDensityWithoutForcedPortraitScrolling(){
    for(String qualifier:new String[]{"mdpi","xhdpi","xxhdpi"}){
      RuntimeEnvironment.setQualifiers(qualifier);
      for(int[] size:new int[][]{{658,1536},{1840,1536}}){
        ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),new Calls("dark"));ctl.get().setContentView(ui);layout(ui,size[0],size[1]);
        assertEquals("Full Fold composition height "+qualifier,ui.content.getHeight(),ui.stage.getHeight());
        assertTrue("Heading above cards",ui.stage.subtitle.getBottom()<ui.stage.infinity.getTop());
        assertTrue("Cards above footer",ui.stage.infinity.getBottom()<ui.stage.footer.getTop());
        assertTrue("Gear above card edge",ui.stage.cobra.gear.getBottom()<=ui.stage.cobra.getHeight());
        float density=ui.getResources().getDisplayMetrics().density;assertTrue(ui.stage.cobra.gear.getWidth()>=48*density);
        cleanup(ctl);
      }
    }
  }
  @Test public void weatherCacheAcceptsOnlyRealResponseAndMarksColdReadingLastKnown(){
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();TextView label=new TextView(ctl.get());InfinityChooserWeather w=new InfinityChooserWeather(ctl.get(),label,()->null);
    w.cache.edit().clear().commit();assertFalse(w.accept("{}"));assertFalse(w.accept("{\"result\":{\"Weather.Location\":\"Somewhere\"}}"));
    assertTrue(w.accept("{\"result\":{\"Weather.Location\":\"Location from Kodi\",\"Weather.Temperature\":\"15°C\",\"Weather.Conditions\":\"Cloudy\"}}"));
    w.renderCached();assertTrue(label.getText().toString().contains("15°C"));assertTrue(label.getText().toString().contains("last known"));assertFalse(w.accept("malformed"));
    w.cache.edit().putLong("timestamp",System.currentTimeMillis()-25*60*60*1000L).commit();w.renderCached();assertEquals("Weather unavailable",label.getText().toString());w.stop();cleanup(ctl);
  }
  @Test public void renderBothThemesAndAllRelevantAspectsForVisualInspection() throws Exception {
    RuntimeEnvironment.setQualifiers("mdpi");File evidence=new File(System.getProperty("chooser.evidence","build/chooser-evidence"));evidence.mkdirs();
    for(String theme:new String[]{"dark","light"})for(int[] size:new int[][]{{420,936},{900,768},{900,400},{360,240}}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),new Calls(theme));ctl.get().setContentView(ui);layout(ui,size[0],size[1]);ui.backdrop.setMotionDisabled(true);
      Bitmap bitmap=Bitmap.createBitmap(size[0],size[1],Bitmap.Config.ARGB_8888);ui.draw(new Canvas(bitmap));
      try(FileOutputStream out=new FileOutputStream(new File(evidence,"chooser-"+theme+"-"+size[0]+"x"+size[1]+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}bitmap.recycle();cleanup(ctl);
    }
  }
}
