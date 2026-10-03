package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.os.Looper;
import android.view.View;
import java.io.File;
import java.io.FileOutputStream;
import java.time.Duration;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class MotionFrameTest {
  static Bitmap render(InfinityGlassChooser ui) {
    Bitmap b=Bitmap.createBitmap(ui.getWidth(),ui.getHeight(),Bitmap.Config.ARGB_8888);
    // Background-only comparison excludes genuine live clock changes from the evidence.
    ui.backdrop.draw(new Canvas(b));return b;
  }
  static void save(Bitmap b,String name) throws Exception {
    File dir=new File(System.getProperty("chooser.evidence"));dir.mkdirs();
    try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));}
  }
  @Test public void softwareScheduledFramesChangePixelsAndNeverControls() throws Exception {
    RuntimeEnvironment.setQualifiers("mdpi");
    StringBuilder report=new StringBuilder("Actual scheduled software-view motion; native Canvas raster comparison\n");
    for(String theme:new String[]{"dark","light"})for(int[] size:new int[][]{{420,936},{900,768},{900,400},{360,240}}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();
      InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),new CosmicChooserTest.Calls(theme));
      ctl.get().setContentView(ui);CosmicChooserTest.layout(ui,size[0],size[1]);
      // Robolectric native graphics defaults AttachInfo to accelerated even for bitmap draws.
      // Explicitly simulate the real software-window attachment; rasterization stays native Canvas.
      Object attach=org.robolectric.util.ReflectionHelpers.getField(ui.backdrop,"mAttachInfo");
      org.robolectric.util.ReflectionHelpers.setField(attach,"mHardwareAccelerated",false);
      assertFalse("Software View must be eligible",ui.backdrop.isHardwareAccelerated());
      ui.backdrop.onWindowFocusChanged(true);assertTrue(ui.backdrop.eligible());assertTrue(ui.backdrop.framePending);
      Map<String,String> bounds=CosmicChooserTest.tree(ui,ui);
      long before=ui.backdrop.phaseMillis;Bitmap a=render(ui);
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(1500));
      assertTrue("Real callback clock advanced",ui.backdrop.phaseMillis>before+1000);
      Bitmap b=render(ui);assertEquals("Every card/control bound unchanged",bounds,CosmicChooserTest.tree(ui,ui));
      boolean[] protectedPixels=new boolean[size[0]*size[1]];
      for(int i=0;i<ui.stage.getChildCount();i++){
        View v=ui.stage.getChildAt(i);Rect r=new Rect();v.getDrawingRect(r);ui.offsetDescendantRectToMyCoords(v,r);
        for(int y=Math.max(0,r.top);y<Math.min(size[1],r.bottom);y++)
          for(int x=Math.max(0,r.left);x<Math.min(size[0],r.right);x++)protectedPixels[y*size[0]+x]=true;
      }
      int moving=0,protectedChanged=0;
      for(int y=0;y<size[1];y++)for(int x=0;x<size[0];x++)if(a.getPixel(x,y)!=b.getPixel(x,y)){
        if(protectedPixels[y*size[0]+x])protectedChanged++;else moving++;
      }
      assertTrue("Visible raster changes "+theme+" "+size[0],moving>100);
      assertEquals("No animated pixels in controls/cards",0,protectedChanged);
      String id=theme+"-"+size[0]+"x"+size[1];save(a,"motion-"+id+"-t0");save(b,"motion-"+id+"-t1500");
      report.append(id+": changed background pixels="+moving+", protected changes=0, bounds unchanged\n");
      a.recycle();b.recycle();CosmicChooserTest.cleanup(ctl);
    }
    java.nio.file.Files.write(new File(System.getProperty("chooser.evidence"),"FRAME-DIFFERENCE.txt").toPath(),report.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
  }
  @Test public void focusVisibilityDetachAndResizeControlTheSameLoop() {
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();
    InfinityGlassChooser ui=new InfinityGlassChooser(ctl.get(),new CosmicChooserTest.Calls("dark"));ctl.get().setContentView(ui);
    CosmicChooserTest.layout(ui,420,936);ui.backdrop.onWindowFocusChanged(true);
    for(int[] size:new int[][]{{420,936},{900,768},{420,936},{360,240},{900,400}}){
      CosmicChooserTest.layout(ui,size[0],size[1]);assertTrue(ui.backdrop.framePending);
      ui.backdrop.onWindowFocusChanged(false);long phase=ui.backdrop.phaseMillis;
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(500));assertEquals(phase,ui.backdrop.phaseMillis);
      ui.backdrop.onWindowFocusChanged(true);assertTrue(ui.backdrop.framePending);
    }
    ui.setVisibility(View.GONE);assertFalse(ui.backdrop.framePending);
    ui.setVisibility(View.VISIBLE);assertTrue(ui.backdrop.framePending);
    ctl.get().setContentView(new View(ctl.get()));assertFalse(ui.backdrop.framePending);assertNull(ui.backdrop.plate);
    long phase=ui.backdrop.phaseMillis;Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(2));assertEquals(phase,ui.backdrop.phaseMillis);
    CosmicChooserTest.cleanup(ctl);
  }
}
