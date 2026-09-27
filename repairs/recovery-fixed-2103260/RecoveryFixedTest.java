package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.content.res.Configuration;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowDialog;
import org.robolectric.android.controller.ActivityController;
import java.io.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class RecoveryFixedTest {
  static final String RESTORE_TEXT="Restore Cobra's built-in presentation. Your themes, sources, settings and playback data are kept.";
  static void layout(InfinityGlassRecovery dialog,int w,int h){
    dialog.panel.maxHeight=h;dialog.panel.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.AT_MOST));
    dialog.panel.layout(0,0,w,dialog.panel.getMeasuredHeight());
  }
  static InfinityGlassRecovery latest(){assertTrue(ShadowDialog.getLatestDialog() instanceof InfinityGlassRecovery);return (InfinityGlassRecovery)ShadowDialog.getLatestDialog();}
  static void swipe(View target,float x0,float y0,float x1,float y1){
    long time=android.os.SystemClock.uptimeMillis();
    for(int i=0;i<=12;i++){
      int action=i==0?MotionEvent.ACTION_DOWN:i==12?MotionEvent.ACTION_UP:MotionEvent.ACTION_MOVE;
      float q=i/12f;MotionEvent event=MotionEvent.obtain(time,time+i*12,action,x0+(x1-x0)*q,y0+(y1-y0)*q,0);
      target.dispatchTouchEvent(event);event.recycle();
    }
    Shadows.shadowOf(Looper.getMainLooper()).idle();
  }
  static void fixed(InfinityGlassChooser ui){
    assertEquals(0,ui.content.getScrollX());assertEquals(0,ui.content.getScrollY());assertFalse(ui.content.canScrollVertically(1));assertFalse(ui.content.canScrollVertically(-1));
    assertEquals(0f,ui.content.getTranslationX(),0f);assertEquals(0f,ui.content.getTranslationY(),0f);
    assertEquals(1f,ui.content.getScaleX(),0f);assertEquals(1f,ui.content.getScaleY(),0f);
    assertEquals(ui.content.getHeight()-ui.content.getPaddingTop()-ui.content.getPaddingBottom(),ui.stage.getHeight());
  }
  @Test public void chooserDoesNotMoveForDragsFlingsOrFocusAtAllWindowSizes(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");
    for(String mode:new String[]{"light","dark"})for(int[] size:new int[][]{{320,640},{420,936},{768,1024},{1024,768},{600,400},{336,220}}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();
      InfinityGlassChooser ui=new InfinityGlassChooser(a,new GlassChooserTest.Calls(mode));a.setContentView(ui);ui.content.setPadding(0,24,0,28);GlassChooserTest.layout(ui,size[0],size[1]);
      int x=ui.stage.infinity.getLeft(),y=ui.stage.infinity.getTop();
      assertFalse(ui.content instanceof android.widget.ScrollView);assertEquals(View.OVER_SCROLL_NEVER,ui.content.getOverScrollMode());fixed(ui);
      swipe(ui,size[0]/2f,size[1]*.8f,size[0]/2f,size[1]*.2f);swipe(ui,size[0]/2f,size[1]*.2f,size[0]/2f,size[1]*.8f);
      swipe(ui,size[0]*.2f,size[1]*.25f,size[0]*.8f,size[1]*.25f);ui.content.scrollTo(90,120);fixed(ui);
      for(int id:new int[]{InfinityGlassChooser.SETTINGS_INFINITY,InfinityGlassChooser.SETTINGS_COBRA}){
        View gear=ui.findViewById(id);assertTrue(gear.requestFocusFromTouch());fixed(ui);
        Rect r=new Rect();gear.getDrawingRect(r);ui.offsetDescendantRectToMyCoords(gear,r);
        assertTrue(mode+" visible gear at "+size[0]+"x"+size[1],r.top>=24&&r.bottom<=size[1]-28&&r.left>=0&&r.right<=size[0]);
      }
      assertEquals(x,ui.stage.infinity.getLeft());assertEquals(y,ui.stage.infinity.getTop());ctl.pause().stop().destroy();
    }
  }
  @Test public void repeatedMeasureAndWindowResizeReturnToSameAnchors(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");
    for(String mode:new String[]{"light","dark"}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();InfinityGlassChooser ui=new InfinityGlassChooser(a,new GlassChooserTest.Calls(mode));a.setContentView(ui);
      ui.content.setPadding(12,24,12,28);GlassChooserTest.layout(ui,420,936);Rect start=new Rect();ui.stage.infinity.getHitRect(start);
      for(int i=0;i<10;i++){ui.requestLayout();GlassChooserTest.layout(ui,420,936);Rect now=new Rect();ui.stage.infinity.getHitRect(now);assertEquals(start,now);fixed(ui);}
      GlassChooserTest.layout(ui,936,420);fixed(ui);GlassChooserTest.layout(ui,420,936);Rect restored=new Rect();ui.stage.infinity.getHitRect(restored);assertEquals(start,restored);fixed(ui);ctl.pause().stop().destroy();
    }
  }
  @Test public void originalRecoveryCallbackLaunchesSafeModeOnceWithExactFlags(){
    for(boolean light:new boolean[]{false,true}){
      ActivityController<RecoveryActionHarness> ctl=Robolectric.buildActivity(RecoveryActionHarness.class).setup();RecoveryActionHarness a=ctl.get();a.light=light;a.openRecovery();InfinityGlassRecovery d=latest();
      assertEquals("Cobra Recovery",d.panel.title.getText().toString());assertEquals("Close",d.panel.close.getText().toString());assertEquals(2,d.panel.rows.getChildCount());
      assertEquals("Start Cobra in Safe Mode",d.panel.rows.getChildAt(0).getContentDescription());assertEquals("Restore Built-in Theme",d.panel.rows.getChildAt(1).getContentDescription());
      View row=d.panel.rows.getChildAt(0);row.performClick();row.performClick();assertEquals(1,a.launches);assertEquals("live",a.launched);assertTrue(a.safe);assertTrue(a.once);assertEquals(0,a.restored);assertFalse(d.isShowing());assertFalse(d.subscribed);ctl.pause().stop().destroy();
    }
  }
  @Test public void restoreStillRequiresTheOriginalConfirmationAndCancelNeverRestores(){
    for(boolean light:new boolean[]{false,true})for(boolean confirm:new boolean[]{false,true}){
      ActivityController<RecoveryActionHarness> ctl=Robolectric.buildActivity(RecoveryActionHarness.class).setup();RecoveryActionHarness a=ctl.get();a.light=light;a.openRecovery();InfinityGlassRecovery menu=latest();
      menu.panel.rows.getChildAt(1).performClick();InfinityGlassRecovery dialog=latest();assertNotSame(menu,dialog);assertFalse(menu.isShowing());assertEquals(0,a.restored);
      assertEquals("Restore Built-in Theme?",dialog.panel.title.getText().toString());assertEquals(RESTORE_TEXT,dialog.panel.description.getText().toString());
      assertEquals("Restore",dialog.panel.restore.getText().toString());assertEquals("Cancel",dialog.panel.close.getText().toString());
      View action=confirm?dialog.panel.restore:dialog.panel.close;action.performClick();action.performClick();assertEquals(confirm?1:0,a.restored);assertEquals(0,a.launches);assertFalse(dialog.isShowing());assertFalse(dialog.subscribed);ctl.pause().stop().destroy();
    }
  }
  @Test public void recoveryCloseBackAndActualTouchPreserveSingleDispatch(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");
    for(int action=0;action<3;action++){
      ActivityController<RecoveryActionHarness> ctl=Robolectric.buildActivity(RecoveryActionHarness.class).setup();RecoveryActionHarness a=ctl.get();a.openRecovery();InfinityGlassRecovery d=latest();layout(d,396,700);
      if(action==0)d.panel.close.performClick();else if(action==1)d.onBackPressed();else{
        View row=d.panel.rows.getChildAt(0);Rect r=new Rect();row.getDrawingRect(r);d.panel.offsetDescendantRectToMyCoords(row,r);
        long time=android.os.SystemClock.uptimeMillis();MotionEvent down=MotionEvent.obtain(time,time,MotionEvent.ACTION_DOWN,r.centerX(),r.centerY(),0),up=MotionEvent.obtain(time,time+30,MotionEvent.ACTION_UP,r.centerX(),r.centerY(),0);
        assertTrue(d.panel.dispatchTouchEvent(down));assertTrue(d.panel.dispatchTouchEvent(up));down.recycle();up.recycle();Shadows.shadowOf(Looper.getMainLooper()).idle();
      }
      assertEquals(action==2?1:0,a.launches);assertEquals(0,a.restored);assertFalse(d.isShowing());assertFalse(d.subscribed);ctl.pause().stop().destroy();
    }
  }
  @Test public void recoveryAndConfirmationRemainReachableInShortWindowsAndLargeText(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");
    for(boolean light:new boolean[]{false,true})for(boolean confirm:new boolean[]{false,true})for(float font:new float[]{1f,1.6f})for(int[] size:new int[][]{{296,600},{396,900},{436,296},{336,220}}){
      ActivityController<RecoveryActionHarness> ctl=Robolectric.buildActivity(RecoveryActionHarness.class).setup();RecoveryActionHarness a=ctl.get();a.light=light;
      Configuration conf=new Configuration(a.getResources().getConfiguration());conf.fontScale=font;a.getResources().updateConfiguration(conf,a.getResources().getDisplayMetrics());
      a.openRecovery();if(confirm)latest().panel.rows.getChildAt(1).performClick();InfinityGlassRecovery d=latest();Shadows.shadowOf(Looper.getMainLooper()).idle();layout(d,size[0],size[1]);
      assertTrue(d.panel.getHeight()<=size[1]);assertTrue(d.panel.scroll.getHeight()>0);assertTrue(d.panel.scroll.getBottom()<=d.panel.footer.getTop());assertTrue(d.panel.header.getBottom()<d.panel.scroll.getTop());
      assertTrue(d.panel.close.getHeight()>=48);assertTrue(d.panel.close.requestFocusFromTouch());assertTrue(d.panel.close.isFocused());
      if(confirm){assertTrue(d.panel.restore.getHeight()>=48);assertTrue(d.panel.restore.getRight()<=d.panel.footer.getWidth());assertTrue(d.panel.restore.requestFocusFromTouch());}
      d.dismiss();ctl.pause().stop().destroy();
    }
  }
  @Test public void themeChangesRefreshBothRecoveryScreensAndStopAfterDismiss(){
    for(boolean confirm:new boolean[]{false,true}){
      ActivityController<RecoveryActionHarness> ctl=Robolectric.buildActivity(RecoveryActionHarness.class).setup();RecoveryActionHarness a=ctl.get();a.light=false;a.openRecovery();if(confirm)latest().panel.rows.getChildAt(1).performClick();InfinityGlassRecovery d=latest();Shadows.shadowOf(Looper.getMainLooper()).idle();
      InfinityGlassRecovery.Panel old=d.panel;a.light=true;a.getSharedPreferences("infinity_cobra_live",Context.MODE_PRIVATE).edit().putString("cobra_appearance_mode","light").commit();Shadows.shadowOf(Looper.getMainLooper()).idle();
      assertNotSame(old,d.panel);assertTrue(d.panel.light);assertTrue(d.panel.getBackground() instanceof InfinityGlassOptions.GlassSurface);
      if(confirm)assertEquals(RESTORE_TEXT,d.panel.description.getText().toString());
      d.dismiss();assertFalse(d.subscribed);InfinityGlassRecovery.Panel stopped=d.panel;a.light=false;a.getSharedPreferences("infinity_cobra_live",Context.MODE_PRIVATE).edit().putString("cobra_appearance_mode","dark").commit();Shadows.shadowOf(Looper.getMainLooper()).idle();assertSame(stopped,d.panel);ctl.pause().stop().destroy();
    }
  }
  @Test public void renderBothRecoveryScreensInBothThemes() throws Exception {
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-xhdpi");
    for(boolean light:new boolean[]{false,true})for(boolean confirm:new boolean[]{false,true}){
      ActivityController<RecoveryActionHarness> ctl=Robolectric.buildActivity(RecoveryActionHarness.class).setup();RecoveryActionHarness a=ctl.get();a.light=light;
      InfinityGlassChooser ui=new InfinityGlassChooser(a,new GlassChooserTest.Calls(light?"light":"dark"));a.setContentView(ui);GlassChooserTest.layout(ui,840,1873);ui.setFocusableInTouchMode(true);ui.requestFocus();
      a.openRecovery();if(confirm)latest().panel.rows.getChildAt(1).performClick();InfinityGlassRecovery dialog=latest();layout(dialog,792,1780);
      Bitmap image=Bitmap.createBitmap(840,1873,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(image);ui.draw(c);c.drawARGB(Math.round(dialog.getWindow().getAttributes().dimAmount*255),0,0,0);c.save();c.translate(24,(1873-dialog.panel.getHeight())/2f);dialog.panel.draw(c);c.restore();
      File dir=new File(System.getProperty("glass.evidence","build/glass-evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());
      try(FileOutputStream file=new FileOutputStream(new File(dir,"recovery-"+(confirm?"confirm-":"menu-")+(light?"light":"dark")+".png"))){assertTrue(image.compress(Bitmap.CompressFormat.PNG,100,file));}
      image.recycle();dialog.dismiss();ctl.pause().stop().destroy();
    }
  }
}
