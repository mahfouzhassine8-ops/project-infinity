package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.Context;
import android.content.res.Configuration;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import java.io.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class GlassHealthFinishTest {
  static final String REPORT="Infinity diagnostic environment\n\nExample capture only\nBuild: 2103259\n\nNo device data collected by this test.\n\n";
  static void layout(InfinityGlassHealth d,int width,int height){
    d.panel.maxHeight=height;
    d.panel.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.AT_MOST));
    d.panel.layout(0,0,width,d.panel.getMeasuredHeight());
  }
  @Test public void glassInteriorIsOpaqueAndRoundedCornersStayTransparent(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");Context c=RuntimeEnvironment.getApplication();
    for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true}){
      InfinityGlassOptions.GlassSurface surface=new InfinityGlassOptions.GlassSurface(c,new InfinityGlassOptions.Palette(light,cobra));
      Bitmap b=Bitmap.createBitmap(400,600,Bitmap.Config.ARGB_8888);surface.setBounds(0,0,400,600);surface.draw(new Canvas(b));
      assertEquals("rounded corner",0,Color.alpha(b.getPixel(0,0)));
      for(int y=30;y<570;y+=7)for(int x=30;x<370;x+=7)assertEquals("No chooser lettering may bleed through",255,Color.alpha(b.getPixel(x,y)));
      // A single continuous surface must not contain hard horizontal/vertical plate joins.
      for(int y=40;y<560;y++)for(int x=40;x<360;x++){
        int here=b.getPixel(x,y),right=b.getPixel(x+1,y),below=b.getPixel(x,y+1);
        assertTrue(Math.abs(Color.red(here)-Color.red(right))<5);assertTrue(Math.abs(Color.blue(here)-Color.blue(below))<5);
      }
      b.recycle();
    }
  }
  @Test public void backgroundContrastCannotChangeTheMenuInterior(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");Context c=RuntimeEnvironment.getApplication();
    for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true}){
      InfinityGlassOptions.GlassSurface surface=new InfinityGlassOptions.GlassSurface(c,new InfinityGlassOptions.Palette(light,cobra));surface.setBounds(0,0,400,600);
      Bitmap a=Bitmap.createBitmap(400,600,Bitmap.Config.ARGB_8888),b=Bitmap.createBitmap(400,600,Bitmap.Config.ARGB_8888);
      Canvas ca=new Canvas(a),cb=new Canvas(b);ca.drawColor(Color.BLACK);cb.drawColor(Color.WHITE);surface.draw(ca);surface.draw(cb);
      for(int y=30;y<570;y+=9)for(int x=30;x<370;x+=9)assertEquals(a.getPixel(x,y),b.getPixel(x,y));a.recycle();b.recycle();
    }
  }
  @Test public void originalHealthActionsKeepTheirDismissalAndCopySemantics(){
    for(boolean light:new boolean[]{false,true})for(int i=0;i<4;i++){
      ActivityController<HealthActionHarness> ctl=Robolectric.buildActivity(HealthActionHarness.class).setup();HealthActionHarness a=ctl.get();
      InfinityGlassHealth d=a.openHealth(light);assertEquals(4,d.panel.rows.getChildCount());
      assertTrue(d.panel.getBackground() instanceof InfinityGlassOptions.GlassSurface);
      assertTrue(d.panel.findViewById(InfinityGlassHealth.ROW_ID+i).performClick());
      assertEquals(i==0?"Recent crashes & exits":i==3?"Build & device info":null,a.textTitle);
      assertEquals(i==1?1:0,a.exports);assertEquals(i==2?1:0,a.copies);
      assertEquals(i==2,d.isShowing());
      if(i==2){d.panel.findViewById(InfinityGlassHealth.ROW_ID+i).performClick();assertEquals(2,a.copies);d.dismiss();}
      assertFalse(d.subscribed);ctl.pause().stop().destroy();
    }
  }
  @Test public void diagnosticTextAndCloseRemainFunctional(){
    for(boolean light:new boolean[]{false,true}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();
      InfinityGlassHealth d=new InfinityGlassHealth(ctl.get(),"Build & device info","INFINITY DIAGNOSTICS",()->light);
      d.report(REPORT);d.show();layout(d,792,1500);
      assertEquals(REPORT,d.panel.output.getText().toString());assertTrue(d.panel.output.isTextSelectable());
      assertEquals("Close",d.panel.close.getText().toString());d.panel.close.performClick();assertFalse(d.isShowing());assertFalse(d.subscribed);
      ctl.pause().stop().destroy();
    }
  }
  @Test public void shortHealthWindowsAndLargeTextKeepCloseReachable(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");
    for(float font:new float[]{1f,1.6f})for(boolean light:new boolean[]{false,true})for(int[] size:new int[][]{{296,600},{396,900},{436,296},{336,320}}){
      ActivityController<HealthActionHarness> ctl=Robolectric.buildActivity(HealthActionHarness.class).setup();HealthActionHarness a=ctl.get();
      Configuration conf=new Configuration(a.getResources().getConfiguration());conf.fontScale=font;a.getResources().updateConfiguration(conf,a.getResources().getDisplayMetrics());
      InfinityGlassHealth d=a.openHealth(light);Shadows.shadowOf(Looper.getMainLooper()).idle();layout(d,size[0],size[1]);
      assertTrue(d.panel.getHeight()<=size[1]);assertTrue(d.panel.scroll.getHeight()>0);
      assertTrue(d.panel.scroll.getBottom()<=d.panel.footer.getTop());assertTrue(d.panel.header.getBottom()<d.panel.scroll.getTop());
      assertTrue(d.panel.close.getMeasuredHeight()>=48);assertTrue(d.panel.close.requestFocusFromTouch());assertTrue(d.panel.close.isFocused());
      for(int i=0;i<4;i++){View row=d.panel.rows.getChildAt(i);assertTrue(row.getHeight()>=48);assertNotNull(row.getContentDescription());}
      d.dismiss();ctl.pause().stop().destroy();
    }
  }
  @Test public void healthThemeRefreshAndBackReleaseListeners(){
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();boolean[] light={false};
    a.getSharedPreferences("infinity_cobra_live",Context.MODE_PRIVATE).edit().clear().commit();
    InfinityGlassHealth d=new InfinityGlassHealth(a,"Build & device info","INFINITY DIAGNOSTICS",()->light[0]);d.report(REPORT);d.show();Shadows.shadowOf(Looper.getMainLooper()).idle();
    InfinityGlassHealth.HealthPanel old=d.panel;light[0]=true;
    a.getSharedPreferences("infinity_cobra_live",Context.MODE_PRIVATE).edit().putString("cobra_appearance_mode","light").commit();Shadows.shadowOf(Looper.getMainLooper()).idle();
    assertNotSame(old,d.panel);assertTrue(d.panel.light);assertEquals(REPORT,d.panel.output.getText().toString());
    d.onBackPressed();assertFalse(d.isShowing());assertFalse(d.subscribed);InfinityGlassHealth.HealthPanel stopped=d.panel;
    a.getSharedPreferences("infinity_cobra_live",Context.MODE_PRIVATE).edit().putString("cobra_appearance_mode","dark").commit();Shadows.shadowOf(Looper.getMainLooper()).idle();assertSame(stopped,d.panel);ctl.pause().stop().destroy();
  }
  @Test public void nativeHealthMenuAndReportRenders() throws Exception {
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-xhdpi");
    for(boolean light:new boolean[]{false,true})for(boolean report:new boolean[]{false,true}){
      ActivityController<HealthActionHarness> ctl=Robolectric.buildActivity(HealthActionHarness.class).setup();HealthActionHarness a=ctl.get();
      InfinityGlassChooser chooser=new InfinityGlassChooser(a,new InfinityGlassChooser.Actions(){
        public void enter(String s){}public void settings(String s){}public void themes(){}public String appearance(){return light?"light":"dark";}public void appearanceChanged(){}
      });a.setContentView(chooser);GlassChooserTest.layout(chooser,840,1873);chooser.setFocusableInTouchMode(true);chooser.requestFocus();
      InfinityGlassHealth d;
      if(report){d=new InfinityGlassHealth(a,"Build & device info","INFINITY DIAGNOSTICS",()->light);d.report(REPORT+REPORT+REPORT);d.show();}
      else d=a.openHealth(light);
      layout(d,792,1780);Bitmap b=Bitmap.createBitmap(840,1873,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(b);chooser.draw(canvas);
      canvas.drawARGB(Math.round(d.getWindow().getAttributes().dimAmount*255),0,0,0);canvas.save();canvas.translate(24,(1873-d.panel.getHeight())/2f);d.panel.draw(canvas);canvas.restore();
      File dir=new File(System.getProperty("glass.evidence","build/glass-evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());
      try(FileOutputStream out=new FileOutputStream(new File(dir,"health-"+(report?"report-":"menu-")+(light?"light":"dark")+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));}
      b.recycle();d.dismiss();ctl.pause().stop().destroy();
    }
  }
}
