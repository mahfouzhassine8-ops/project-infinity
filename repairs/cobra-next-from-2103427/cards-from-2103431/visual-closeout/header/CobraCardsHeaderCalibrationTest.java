package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowChoreographer;

/** Selected native Canvas calibration only. Actual owner/native shell header,
 * four declared font cases, no fake core UI, inputs, decoder, or private asset. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 qualifiers="w358dp-h637dp-port-420dpi",instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraCardsLayoutTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraCardsHeaderCalibrationTest {
  static TextView header(View root){
    if(root instanceof TextView && "Cobra".contentEquals(((TextView)root).getText()))return (TextView)root;
    if(root instanceof ViewGroup){ViewGroup parent=(ViewGroup)root;for(int i=0;i<parent.getChildCount();i++){TextView result=header(parent.getChildAt(i));if(result!=null)return result;}}
    return null;
  }
  static JSONObject metrics(Bitmap bitmap)throws Exception{
    int left=bitmap.getWidth(),top=bitmap.getHeight(),right=0,bottom=0,peak=0,count=0;double ink=0;
    for(int y=15;y<65;y++)for(int x=125;x<300;x++){
      int rgb=bitmap.getPixel(x,y),low=Math.min(Color.red(rgb),Math.min(Color.green(rgb),Color.blue(rgb))),high=Math.max(Color.red(rgb),Math.max(Color.green(rgb),Color.blue(rgb)));
      if(low>70 && high-low<40){left=Math.min(left,x);right=Math.max(right,x+1);top=Math.min(top,y);bottom=Math.max(bottom,y+1);peak=Math.max(peak,low);count++;ink+=(low-20)/235d;}
    }
    assertTrue("Actual header glyph pixels required",count>0 && peak>20);
    double normalized=ink*235d/(peak-20),score=Math.abs((right-left)-114)/114d+Math.abs((bottom-top)-33)/33d+Math.abs(normalized-1332.911)/1332.911;
    return new JSONObject().put("bbox",new JSONArray().put(left).put(top).put(right).put(bottom)).put("width",right-left).put("height",bottom-top)
      .put("threshold_pixels",count).put("minRGB_peak",peak).put("weighted_ink",ink).put("color_normalized_ink",normalized).put("relative_geometry_ink_error",score);
  }

  @Test public void refineApprovedHeaderMetrics()throws Exception{
    ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));Locale.setDefault(Locale.US);TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
    assertTrue(SystemClock.setCurrentTimeMillis(1735732800000L));CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards");
    View toolbar=(View)CobraCardsLayoutTest.get(f.a,"mCobraModeToolbar");TextView name=header(toolbar);assertNotNull(name);assertEquals(42f,name.getTextSize(),.001f);assertEquals(941,toolbar.getWidth());assertEquals(104,toolbar.getHeight());
    Typeface original=name.getTypeface();int color=name.getCurrentTextColor();int originalLeft=name.getLeft(),originalTop=name.getTop();JSONArray cases=new JSONArray();Path out=Paths.get(System.getProperty("header.output"));Files.createDirectories(out);
    float[][] variants={{42f,.03f},{42.25f,.025f},{42.5f,.02f}};
    for(int index=0;index<variants.length;index++){
      float size=variants[index][0],tracking=variants[index][1];name.setTypeface(Typeface.create(Typeface.create("sans-serif",Typeface.NORMAL),500,false));name.setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,size);name.setLetterSpacing(tracking);
      toolbar.measure(View.MeasureSpec.makeMeasureSpec(941,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(104,View.MeasureSpec.EXACTLY));toolbar.layout(0,0,941,104);
      assertEquals(color,name.getCurrentTextColor());assertEquals(originalLeft,name.getLeft());assertEquals(originalTop,name.getTop());
      Bitmap bitmap=Bitmap.createBitmap(941,104,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(bitmap);canvas.drawColor(Color.BLACK);toolbar.draw(canvas);
      String file="native-header-refine-"+(index+1)+".png";try(OutputStream stream=Files.newOutputStream(out.resolve(file))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,stream));}
      cases.put(metrics(bitmap).put("requested_weight",500).put("actual_weight",name.getTypeface().getWeight()).put("tracking_em",tracking).put("size_px",size).put("text_color",color).put("native_Canvas_PNG",file));bitmap.recycle();
    }
    name.setTypeface(original);name.setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,42);name.setLetterSpacing(0);
    JSONObject report=new JSONObject().put("status","PASS_SELECTED_THREE_NATIVE_HEADER_REFINEMENT_CASES").put("cases",cases).put("reference_bbox",new JSONArray().put(136).put(24).put(250).put(57)).put("reference_color_normalized_ink",1332.911)
      .put("criteria","Preserve33pxheight/anchor first, then minimize width and normalized ink error; no exact-font claim").put("Android","NOT_RUN").put("shutdown","NOT_RUN");
    Files.write(out.resolve("HEADER-REFINEMENT.json"),(report.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
  }

  @Test public void compareApprovedHeaderWeights()throws Exception{
    ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));Locale.setDefault(Locale.US);TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
    assertTrue(SystemClock.setCurrentTimeMillis(1735732800000L));
    CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards");
    View toolbar=(View)CobraCardsLayoutTest.get(f.a,"mCobraModeToolbar");TextView name=header(toolbar);assertNotNull(name);assertEquals(42f,name.getTextSize(),.001f);assertEquals(0f,name.getLetterSpacing(),.0001f);
    assertEquals(941,toolbar.getWidth());assertEquals(104,toolbar.getHeight());
    Typeface original=name.getTypeface();assertEquals(700,original.getWeight());int color=name.getCurrentTextColor();
    JSONArray cases=new JSONArray();Path out=Paths.get(System.getProperty("header.output"));Files.createDirectories(out);
    for(int weight:new int[]{700,500,550,600}){
      float tracking=weight==700?0:.02f;name.setTypeface(weight==700?original:Typeface.create(Typeface.create("sans-serif",Typeface.NORMAL),weight,false));name.setLetterSpacing(tracking);
      toolbar.measure(View.MeasureSpec.makeMeasureSpec(941,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(104,View.MeasureSpec.EXACTLY));toolbar.layout(0,0,941,104);
      assertEquals(42f,name.getTextSize(),.001f);assertEquals(color,name.getCurrentTextColor());
      Bitmap bitmap=Bitmap.createBitmap(941,104,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(bitmap);canvas.drawColor(Color.BLACK);toolbar.draw(canvas);
      String file="native-header-weight-"+weight+".png";try(OutputStream stream=Files.newOutputStream(out.resolve(file))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,stream));}
      JSONObject row=metrics(bitmap).put("requested_weight",weight).put("actual_weight",name.getTypeface().getWeight()).put("tracking_em",tracking).put("size_px",name.getTextSize())
        .put("text_color",color).put("native_TextView_class",name.getClass().getName()).put("native_Canvas_PNG",file).put("font_same_as_reference","NOT_CLAIMED");cases.put(row);bitmap.recycle();
    }
    name.setTypeface(original);name.setLetterSpacing(0);
    JSONObject report=new JSONObject().put("status","PASS_SELECTED_FOUR_NATIVE_HEADER_CALIBRATION_CASES").put("cases",cases)
      .put("reference_bbox",new JSONArray().put(136).put(24).put(250).put(57)).put("reference_color_normalized_ink",1332.911)
      .put("criteria","Minimize relative width/height/normalized ink error; area/bbox do not establish exact font or pixel-perfect identity")
      .put("fixture","Actual current owner native buildShell/ShowGuideShell header TextView; existing Layout fixture compiled only")
      .put("provider_workers","ADMISSIONS_ONLY; BODIES_NOT_EXECUTED").put("Android","NOT_RUN").put("shutdown","NOT_RUN");
    Files.write(out.resolve("HEADER-CALIBRATION.json"),(report.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
  }
}
