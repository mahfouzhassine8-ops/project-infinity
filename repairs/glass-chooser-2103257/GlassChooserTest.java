package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.os.Looper;
import android.view.MotionEvent;
import android.view.View;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.Shadows;
import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class GlassChooserTest {
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
  static void layout(InfinityGlassChooser ui,int w,int h) {
    ui.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));
    ui.layout(0,0,w,h);
  }
  @Test public void bothThemesRouteEveryVisibleControlWithoutCrossLaunching() {
    for(String mode:new String[]{"dark","light","oled"}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();Calls c=new Calls(mode);
      InfinityGlassChooser ui=new InfinityGlassChooser(a,c);a.setContentView(ui);layout(ui,1080,2400);
      ui.findViewById(InfinityGlassChooser.SETTINGS_INFINITY).performClick();
      ui.findViewById(InfinityGlassChooser.SETTINGS_COBRA).performClick();
      assertEquals(java.util.Arrays.asList("infinity","live"),c.settings);assertTrue(c.entered.isEmpty());
      ui.findViewById(InfinityGlassChooser.ENTER_INFINITY).performClick();ui.findViewById(InfinityGlassChooser.ENTER_COBRA).performClick();
      assertEquals(java.util.Arrays.asList("infinity","live"),c.entered);
      if("light".equals(mode)){
        ui.findViewById(InfinityGlassChooser.PILL_INFINITY).performClick();ui.findViewById(InfinityGlassChooser.PILL_COBRA).performClick();assertEquals(4,c.entered.size());
      }else{assertNull(ui.findViewById(InfinityGlassChooser.PILL_INFINITY));assertNull(ui.findViewById(InfinityGlassChooser.PILL_COBRA));}
      ui.stage.performLongClick();assertEquals(1,c.themes);ctl.pause().stop().destroy();
    }
  }
  @Test public void actualGearTouchDoesNotSelectParentCard() {
    RuntimeEnvironment.setQualifiers("w420dp-h900dp-mdpi");
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();Calls c=new Calls("light");
    InfinityGlassChooser ui=new InfinityGlassChooser(a,c);a.setContentView(ui);layout(ui,420,936);
    View gear=ui.findViewById(InfinityGlassChooser.SETTINGS_COBRA);Rect rect=new Rect();gear.getDrawingRect(rect);ui.offsetDescendantRectToMyCoords(gear,rect);
    long now=android.os.SystemClock.uptimeMillis();
    MotionEvent down=MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,rect.exactCenterX(),rect.exactCenterY(),0);
    MotionEvent up=MotionEvent.obtain(now,now+30,MotionEvent.ACTION_UP,rect.exactCenterX(),rect.exactCenterY(),0);
    assertTrue(ui.dispatchTouchEvent(down));assertTrue(ui.dispatchTouchEvent(up));down.recycle();up.recycle();
    Shadows.shadowOf(Looper.getMainLooper()).idle();
    assertEquals(java.util.Arrays.asList("live"),c.settings);assertTrue(c.entered.isEmpty());ctl.pause().stop().destroy();
  }
  @Test public void minimumTargetsAndIndependentCardBoundsAtWindowSizes() {
    RuntimeEnvironment.setQualifiers("w420dp-h900dp-mdpi");
    for(String mode:new String[]{"dark","light"})for(int[] size:new int[][]{{320,640},{420,936},{768,1024},{1024,768},{600,400}}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Calls c=new Calls(mode);InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),c);ctl.get().setContentView(ui);layout(ui,size[0],size[1]);
      Rect l=new Rect(),r=new Rect();ui.stage.infinity.getHitRect(l);ui.stage.cobra.getHitRect(r);assertFalse(Rect.intersects(l,r));assertTrue(l.left>=0&&r.right<=size[0]);
      int minimum=Math.round(48*ui.getResources().getDisplayMetrics().density);
      for(int id:new int[]{InfinityGlassChooser.SETTINGS_INFINITY,InfinityGlassChooser.SETTINGS_COBRA}){
        View v=ui.findViewById(id);assertTrue(v.getMeasuredWidth()>=minimum);assertTrue(v.getMeasuredHeight()>=minimum);assertTrue(v.isFocusable());assertNotNull(v.getContentDescription());
      }
      assertTrue(ui.stage.infinity.requestFocus());assertTrue(ui.stage.infinity.isFocused());assertEquals(InfinityGlassChooser.ENTER_COBRA,ui.stage.infinity.getNextFocusRightId());
      ctl.pause().stop().destroy();
    }
  }
  @Test public void preferenceListenerIsCoalescedAndReleased() {
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();Calls c=new Calls("dark");InfinityGlassChooser ui=new InfinityGlassChooser(a,c);a.setContentView(ui);layout(ui,1080,2400);
    Shadows.shadowOf(Looper.getMainLooper()).idle();
    c.mode="light";SharedPreferences prefs=a.getSharedPreferences("infinity_cobra_live",Context.MODE_PRIVATE);
    prefs.edit().putString("cobra_appearance_mode","light").commit();Shadows.shadowOf(Looper.getMainLooper()).idle();assertEquals(1,c.changed);
    a.setContentView(new View(a));c.mode="dark";prefs.edit().putString("cobra_appearance_mode","dark").commit();Shadows.shadowOf(Looper.getMainLooper()).idle();assertEquals(1,c.changed);ctl.pause().stop().destroy();
  }
  @Test public void nativeCanvasScreenshotsBothGoldenSizesAndFoldWindows() throws Exception {
    RuntimeEnvironment.setQualifiers("w470dp-h836dp-xhdpi");
    for(String mode:new String[]{"dark","light"}){
      for(int[] size:new int[][]{("light".equals(mode)?new int[]{840,1873}:new int[]{941,1672}),new int[]{420,936},new int[]{768,1024},new int[]{1024,768}}){
        ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();Calls calls=new Calls(mode);InfinityGlassChooser ui=new InfinityGlassChooser(a,calls);a.setContentView(ui);layout(ui,size[0],size[1]);
        ui.clearFocus();ui.stage.infinity.clearFocus();
        Bitmap image=Bitmap.createBitmap(size[0],size[1],Bitmap.Config.ARGB_8888);ui.draw(new Canvas(image));
        File dir=new File(System.getProperty("glass.evidence","build/glass-evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());
        try(FileOutputStream out=new FileOutputStream(new File(dir,mode+"-"+size[0]+"x"+size[1]+".png"))){assertTrue(image.compress(Bitmap.CompressFormat.PNG,100,out));}
        image.recycle();ctl.pause().stop().destroy();
      }
    }
  }
  @Test public void allMaterialPlatesDecodeAndUnknownKeyFailsClosed() {
    for(String mode:new String[]{"light","dark"})for(String key:new String[]{"background","orb","gold","cyan"}){
      Bitmap b=InfinityGlassArt.decode(mode+"_"+key);assertNotNull(b);assertTrue(b.getByteCount()<700000);b.recycle();
    }
    try{InfinityGlassArt.decode("missing");fail("unknown material must trigger chooser fallback");}catch(IllegalArgumentException expected){}
  }
}
