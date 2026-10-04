package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.Context;
import android.content.res.Configuration;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import android.widget.TextView;
import java.io.*;
import java.util.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class GlassOptionsTest {
  static String[] options(boolean cobra) {
    String label=cobra?"Cobra":"Infinity";
    ArrayList<String> names=new ArrayList<>(Arrays.asList("Remember & launch "+label,"Launch "+label+" just this time","Ask every time","Infinity Health Center"));
    if(cobra)names.add("Cobra Recovery");return names.toArray(new String[0]);
  }
  static InfinityGlassOptions open(Activity a,boolean light,boolean cobra,ArrayList<Integer> calls){
    InfinityGlassOptions d=new InfinityGlassOptions(a,cobra,cobra?"Cobra options":"Infinity options",options(cobra),()->light,(ignored,i)->calls.add(i));d.show();return d;
  }
  static void panelLayout(InfinityGlassOptions d,int w,int h){
    d.panel.maxHeight=h;
    d.panel.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.AT_MOST));
    d.panel.layout(0,0,w,d.panel.getMeasuredHeight());
  }
  @Test public void bothExperiencesBothThemesKeepExactLabelsAndEveryAction(){
    for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true})for(int index=0;index<options(cobra).length;index++){
      ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();ArrayList<Integer> calls=new ArrayList<>();
      InfinityGlassOptions d=open(c.get(),light,cobra,calls);panelLayout(d,840,1600);
      assertEquals(cobra?3:2,d.panel.rows.getChildCount());assertEquals(light,d.panel.light);
      assertEquals(cobra?"Cobra options":"Infinity options",d.panel.title.getText().toString());
      assertEquals(3,d.panel.launchChoices.getChildCount());
      for(int j=0;j<3;j++)assertEquals(options(cobra)[j],((TextView)d.panel.launchChoices.getChildAt(j)).getText().toString());
      for(int j=3;j<options(cobra).length;j++)assertEquals(options(cobra)[j],d.panel.findViewById(InfinityGlassOptions.ROW_ID+j).getContentDescription());
      View row=d.panel.findViewById(InfinityGlassOptions.ROW_ID+index);assertTrue(row.performClick());
      if(index<3) {
        assertTrue(calls.isEmpty());assertTrue(d.isShowing());
        row=d.panel.findViewWithTag("experience_launch_apply");assertTrue(row.performClick());
      }
      assertEquals(Arrays.asList(index),calls);assertFalse(d.isShowing());row.performClick();assertEquals(1,calls.size());c.pause().stop().destroy();
    }
  }
  @Test public void originalSplashCallbackPreservesDefaultsLaunchHealthAndRecovery(){
    for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true})for(int index=0;index<options(cobra).length;index++){
      ActivityController<OptionsActionHarness> ctl=Robolectric.buildActivity(OptionsActionHarness.class).setup();OptionsActionHarness a=ctl.get();
      a.getSharedPreferences(OptionsActionHarness.INFINITY_EXPERIENCE_PREFS,Context.MODE_PRIVATE).edit().putString(OptionsActionHarness.INFINITY_EXPERIENCE_DEFAULT,"sentinel").commit();
      String experience=cobra?"live":"infinity";
      InfinityGlassOptions d=new InfinityGlassOptions(a,cobra,cobra?"Cobra options":"Infinity options",options(cobra),()->light,a.listener(experience));d.show();
      d.panel.findViewById(InfinityGlassOptions.ROW_ID+index).performClick();
      if(index<3)d.panel.findViewWithTag("experience_launch_apply").performClick();
      String stored=a.getSharedPreferences(OptionsActionHarness.INFINITY_EXPERIENCE_PREFS,Context.MODE_PRIVATE).getString(OptionsActionHarness.INFINITY_EXPERIENCE_DEFAULT,null);
      assertEquals(index==0?experience:index==2?null:"sentinel",stored);
      assertEquals(index<=1?experience:null,a.launched);assertEquals(index==3?1:0,a.health);assertEquals(index==4?1:0,a.recovery);
      ctl.pause().stop().destroy();
    }
  }
  @Test public void choicesAreMutuallyExclusiveAndResizeKeepsThePendingSelection(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");
    for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true}){
      ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();
      ArrayList<Integer> calls=new ArrayList<>();InfinityGlassOptions d=open(c.get(),light,cobra,calls);
      for(int choice:new int[]{0,2,1}){
        d.panel.findViewById(InfinityGlassOptions.ROW_ID+choice).performClick();
        assertTrue(calls.isEmpty());assertTrue(d.isShowing());
        for(int[] size:new int[][]{{396,900},{900,396},{700,700},{336,220}}){
          panelLayout(d,size[0],size[1]);
          assertEquals(InfinityGlassOptions.ROW_ID+choice,d.panel.launchChoices.getCheckedRadioButtonId());
          int checked=0;for(int i=0;i<3;i++)if(((android.widget.RadioButton)d.panel.launchChoices.getChildAt(i)).isChecked())checked++;
          assertEquals(1,checked);
        }
      }
      d.panel.findViewWithTag("experience_launch_apply").performClick();
      assertEquals(Arrays.asList(1),calls);assertFalse(d.isShowing());
      c.pause().stop().destroy();
    }
  }
  @Test public void cancelAndBackNeverDispatchAnOption(){
    for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true})for(boolean back:new boolean[]{false,true}){
      ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();ArrayList<Integer> calls=new ArrayList<>();InfinityGlassOptions d=open(c.get(),light,cobra,calls);
      if(back)d.onBackPressed();else d.panel.cancel.performClick();
      assertFalse(d.isShowing());assertTrue(calls.isEmpty());assertFalse(d.subscribed);c.pause().stop().destroy();
    }
  }
  @Test public void actualTouchTargetsDoNotLeakToChooserOrDoubleDispatch(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");
    for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();ArrayList<Integer> calls=new ArrayList<>();int[] underneath={0};
      View chooser=new View(ctl.get());chooser.setOnClickListener(v->underneath[0]++);ctl.get().setContentView(chooser);
      InfinityGlassOptions d=open(ctl.get(),light,cobra,calls);panelLayout(d,396,900);
      View row=d.panel.findViewById(InfinityGlassOptions.ROW_ID+3);Rect r=new Rect();row.getDrawingRect(r);d.panel.offsetDescendantRectToMyCoords(row,r);
      long now=android.os.SystemClock.uptimeMillis();MotionEvent down=MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,r.exactCenterX(),r.exactCenterY(),0);MotionEvent up=MotionEvent.obtain(now,now+30,MotionEvent.ACTION_UP,r.exactCenterX(),r.exactCenterY(),0);
      assertTrue(d.panel.dispatchTouchEvent(down));assertTrue(d.panel.dispatchTouchEvent(up));down.recycle();up.recycle();Shadows.shadowOf(Looper.getMainLooper()).idle();
      assertEquals(Arrays.asList(3),calls);assertEquals(0,underneath[0]);ctl.pause().stop().destroy();
    }
  }
  @Test public void shortWindowsAndLargeTextKeepCancelAndAllRowsReachable(){
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-mdpi");
    for(float font:new float[]{1f,1.6f})for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true})for(int[] size:new int[][]{{296,600},{396,900},{436,296},{336,220}}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();
      Configuration conf=new Configuration(a.getResources().getConfiguration());conf.fontScale=font;a.getResources().updateConfiguration(conf,a.getResources().getDisplayMetrics());
      InfinityGlassOptions d=new InfinityGlassOptions(a,cobra,"Options",options(cobra),()->light,(x,y)->{});
      // Directional focus requires a shown window, not merely a detached measured panel.
      d.show();Shadows.shadowOf(Looper.getMainLooper()).idle();panelLayout(d,size[0],size[1]);
      InfinityGlassOptions.Panel p=d.panel;assertTrue(p.getMeasuredHeight()<=size[1]);assertTrue(p.header.getBottom()<p.scroll.getTop());assertTrue(p.scroll.getBottom()<=p.footer.getTop());
      assertTrue(p.cancel.getMeasuredHeight()>=48);assertTrue(p.scroll.getHeight()>0);
      for(int i=0;i<3;i++){
        TextView choice=(TextView)p.launchChoices.getChildAt(i);
        assertTrue(choice.isFocusable());assertTrue(choice.getHeight()>=48);
        assertNotNull(choice.getLayout());
        assertTrue(choice.getMeasuredHeight()>=choice.getLayout().getHeight());
        assertTrue(choice.getRight()<=p.launchChoices.getWidth());
      }
      View apply=p.findViewWithTag("experience_launch_apply");
      assertTrue(apply.isFocusable());assertTrue(apply.getHeight()>=48);
      for(int i=1;i<p.rows.getChildCount();i++){
        View row=p.rows.getChildAt(i);assertTrue(row.getHeight()>=48);assertTrue(row.isFocusable());assertTrue(row.getRight()<=p.rows.getWidth());
        TextView label=(TextView)((android.view.ViewGroup)row).getChildAt(1);assertNotNull(label.getLayout());
        assertTrue(label.getMeasuredHeight()>=label.getLayout().getHeight());
      }
      p.scroll.scrollTo(0,p.rows.getHeight());assertTrue(p.scroll.getScrollY()>=0);assertTrue("shown Cancel requests focus: "+font+" "+light+" "+cobra+" "+size[0]+"x"+size[1],p.cancel.requestFocusFromTouch());assertTrue("Cancel owns directional focus",p.cancel.isFocused());
      d.dismiss();ctl.pause().stop().destroy();
    }
  }
  @Test public void liveThemeRefreshAndDismissReleaseListeners(){
    for(boolean cobra:new boolean[]{false,true}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();boolean[] light={false};
      InfinityGlassOptions d=new InfinityGlassOptions(a,cobra,"Options",options(cobra),()->light[0],(x,i)->{});d.show();Shadows.shadowOf(Looper.getMainLooper()).idle();
      d.panel.launchChoices.check(InfinityGlassOptions.ROW_ID+2);
      InfinityGlassOptions.Panel old=d.panel;light[0]=true;
      a.getSharedPreferences("infinity_cobra_live",Context.MODE_PRIVATE).edit().putString("cobra_appearance_mode","light").commit();
      Shadows.shadowOf(Looper.getMainLooper()).idle();assertNotSame(old,d.panel);assertTrue(d.panel.light);assertEquals(cobra?3:2,d.panel.rows.getChildCount());
      assertEquals(InfinityGlassOptions.ROW_ID+2,d.panel.launchChoices.getCheckedRadioButtonId());
      assertEquals("Save choice",((TextView)d.panel.findViewWithTag("experience_launch_apply")).getText().toString());
      d.dismiss();assertFalse(d.subscribed);InfinityGlassOptions.Panel stopped=d.panel;light[0]=false;
      a.getSharedPreferences("infinity_cobra_live",Context.MODE_PRIVATE).edit().putString("cobra_appearance_mode","dark").commit();Shadows.shadowOf(Looper.getMainLooper()).idle();assertSame(stopped,d.panel);ctl.pause().stop().destroy();
    }
  }
  @Test public void nativeRendersAllFourSettingsPanelsOnUnchangedChooser() throws Exception {
    RuntimeEnvironment.setQualifiers("w420dp-h936dp-xhdpi");
    for(boolean light:new boolean[]{false,true})for(boolean cobra:new boolean[]{false,true}){
      ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();
      InfinityGlassChooser chooser=new InfinityGlassChooser(a,new InfinityGlassChooser.Actions(){
        public void enter(String s){}public void settings(String s){}public void themes(){}public String appearance(){return light?"light":"dark";}public void appearanceChanged(){}
      });a.setContentView(chooser);CosmicChooserTest.layout(chooser,840,1873);
      chooser.setFocusableInTouchMode(true);chooser.requestFocus();
      InfinityGlassOptions d=open(a,light,cobra,new ArrayList<>());panelLayout(d,792,1780);
      Bitmap b=Bitmap.createBitmap(840,1873,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(b);chooser.draw(canvas);
      canvas.drawARGB(Math.round(d.getWindow().getAttributes().dimAmount*255),0,0,0);
      canvas.save();canvas.translate(24,(1873-d.panel.getHeight())/2f);d.panel.draw(canvas);canvas.restore();
      File out=new File(System.getProperty("glass.evidence","build/glass-evidence"));assertTrue(out.isDirectory()||out.mkdirs());
      try(FileOutputStream f=new FileOutputStream(new File(out,(cobra?"cobra":"infinity")+"-settings-"+(light?"light":"dark")+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,f));}
      b.recycle();d.dismiss();ctl.pause().stop().destroy();
    }
  }
}
