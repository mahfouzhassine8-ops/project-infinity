package com.projectinfinity.kodi;

import android.animation.ValueAnimator;
import android.app.Application;
import android.graphics.RectF;
import android.view.TextureView;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import androidx.media3.common.VideoSize;
import java.lang.reflect.Method;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Android view/matrix and animation scheduling tests. No GPU/decoder/Fold device claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w1600dp-h900dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103201FoldMotionTest {
  Cobra2103199DisplayRegressionTest d;InfinityLiveActivity a;CobraNavigationUiTest ui;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object call(Object o,String n,Object...v)throws Exception{return CobraNavigationUiTest.call(o,n,v);}
  static void durationScale(float scale)throws Exception{
    Method m=ValueAnimator.class.getDeclaredMethod("setDurationScale",float.class);m.setAccessible(true);m.invoke(null,scale);
  }
  @Before public void before()throws Exception{durationScale(1f);d=new Cobra2103199DisplayRegressionTest();d.before();a=d.a;ui=d.ui;}
  @After public void after()throws Exception{durationScale(1f);if(d!=null)d.after();}
  LinearLayout chrome()throws Exception{
    FrameLayout root=new FrameLayout(a);a.setContentView(root);LinearLayout chrome=new LinearLayout(a);
    root.addView(chrome,new FrameLayout.LayoutParams(-1,-1));put(a,"mPlayerOverlay",root);put(a,"mPlayerChrome",chrome);
    d.resize(root,1600,900);ui.frames(2);assertTrue(root.isAttachedToWindow());return chrome;
  }
  void settled(View view){assertEquals(1f,view.getAlpha(),.001f);assertEquals(0f,view.getTranslationX(),.001f);assertEquals(0f,view.getTranslationY(),.001f);assertEquals(1f,view.getScaleX(),.001f);assertEquals(1f,view.getScaleY(),.001f);assertEquals(0L,view.animate().getStartDelay());}
  @Test public void adaptiveActualMatrixAlwaysFitsWholeFrameIncludingPreviousCropWindow()throws Exception{
    Cobra2103199DisplayRegressionTest.Controlled c=d.new Controlled();TextureView t=d.texture(2000,1200);Object ch=d.channel(0);d.mode(ch,12);d.bind(c,ch,t,true);c.writes.clear();
    int[][] bounds={{2000,1200},{2000,1100},{1200,2000},{1812,2176},{2176,1812},{904,2316},{2316,904},{320,240},{601,601}};
    for(int[] box:bounds)for(VideoSize size:new VideoSize[]{new VideoSize(1920,1080),new VideoSize(1080,1920),new VideoSize(720,576,0,16f/15f)}){
      c.size=size;d.resize((View)t.getParent(),box[0],box[1]);call(a,"applyCobraAspectTransform");RectF r=d.rendered(t);
      assertTrue("Whole frame left",r.left>=-.02);assertTrue("Whole frame top",r.top>=-.02);assertTrue("Whole frame right",r.right<=box[0]+.02);assertTrue("Whole frame bottom",r.bottom<=box[1]+.02);
      assertEquals(box[0]/2f,r.centerX(),.02);assertEquals(box[1]/2f,r.centerY(),.02);
      assertTrue("Largest proportional fit must meet one pair of edges",Math.abs(r.width()-box[0])<.02||Math.abs(r.height()-box[1])<.02);
      assertEquals(size.width*(double)size.pixelWidthHeightRatio/size.height,r.width()/(double)r.height(),.0001);
    }
    assertTrue("Display fitting cannot mutate transport or surface ownership",c.writes.isEmpty());
  }
  @Test public void oldTextureResizeCannotTransformReplacementPane()throws Exception{
    Cobra2103199DisplayRegressionTest.Controlled c=d.new Controlled();TextureView old=d.texture(2000,1200);Object ch=d.channel(0);d.mode(ch,12);d.bind(c,ch,old,true);
    FrameLayout root=(FrameLayout)old.getParent();TextureView replacement=new TextureView(a);root.addView(replacement,new FrameLayout.LayoutParams(800,600));
    put(a,"mPlayerTexture",replacement);call(a,"cobraAttachVideo",c.player,replacement);d.resize(root,2000,1200);call(a,"applyCobraAspectTransform");
    RectF before=d.rendered(replacement);old.layout(0,0,904,2316);ui.frames(2);assertEquals(before,d.rendered(replacement));
    assertEquals(800,replacement.getWidth());assertEquals(600,replacement.getHeight());
  }
  @Test public void revealInterruptingEntryImmediatelyRestoresStableTouchGeometry()throws Exception{
    LinearLayout chrome=chrome();chrome.setAlpha(.2f);chrome.setTranslationY(8f);chrome.setScaleX(.99f);
    chrome.animate().alpha(1f).translationY(0f).setDuration(150L).start();ui.frames(2);
    assertTrue(chrome.getTranslationY()>0f);call(a,"showPlayerChromeTemporarily");settled(chrome);ui.frames(15);settled(chrome);assertEquals(View.VISIBLE,chrome.getVisibility());
  }
  @Test public void revealCancelsHideCompletionAndStaleEndAction()throws Exception{
    LinearLayout chrome=chrome();((Runnable)get(a,"mHideChrome")).run();ui.frames(3);assertTrue(chrome.getAlpha()<1f);
    call(a,"showPlayerChromeTemporarily");ui.frames(15);assertEquals(View.VISIBLE,chrome.getVisibility());settled(chrome);
  }
  @Test public void menuOpenedDuringHideKeepsControlsStableAfterCompletion()throws Exception{
    LinearLayout chrome=chrome();((Runnable)get(a,"mHideChrome")).run();ui.frames(3);
    put(a,"mCobraActionSheet",new FrameLayout(a));ui.frames(15);assertEquals(View.VISIBLE,chrome.getVisibility());settled(chrome);
    ((Runnable)get(a,"mHideChrome")).run();ui.frames(15);assertEquals(View.VISIBLE,chrome.getVisibility());put(a,"mCobraActionSheet",null);
  }
  @Test public void panelEntryResetsOrthogonalTranslationAndInheritedDelay()throws Exception{
    LinearLayout chrome=chrome();FrameLayout root=(FrameLayout)chrome.getParent();View panel=new View(a);root.addView(panel,new FrameLayout.LayoutParams(300,300));
    panel.setTranslationX(27);panel.setTranslationY(31);panel.animate().setStartDelay(999L);
    call(a,"cobraAnimatePanelIn",panel,false);assertEquals(0f,panel.getTranslationX(),.001f);assertEquals(0L,panel.animate().getStartDelay());
    ui.frames(20);settled(panel);root.removeView(panel);call(a,"cobraAnimatePanelIn",panel,true);settled(panel);
  }
  @Test public void systemAnimatorOffSettlesExistingPanelRowsAndFocusImmediately()throws Exception{
    LinearLayout chrome=chrome();LinearLayout group=new LinearLayout(a);((FrameLayout)chrome.getParent()).addView(group);Button child=new Button(a);group.addView(child);
    durationScale(0f);assertFalse(ValueAnimator.areAnimatorsEnabled());
    child.setAlpha(0);child.setTranslationY(8);child.animate().setStartDelay(220L);call(a,"cobraAnimateChildrenIn",group);settled(child);
    chrome.setTranslationX(9);call(a,"cobraAnimatePanelIn",chrome,false);settled(chrome);
    call(a,"cobraPolishFocusable",child);child.getOnFocusChangeListener().onFocusChange(child,true);
    assertEquals(1f,child.getAlpha(),.001f);assertEquals(1.018f,child.getScaleX(),.001f);assertEquals(0f,child.getTranslationY(),.001f);
    ((Runnable)get(a,"mHideChrome")).run();assertEquals(View.GONE,chrome.getVisibility());call(a,"showPlayerChromeTemporarily");assertEquals(View.VISIBLE,chrome.getVisibility());settled(chrome);
  }
  @Test public void existingIconFocusFeedbackPreservesImmediateActionAndSettles()throws Exception{
    final int[] clicks={0};View button=(View)call(a,"cobraIcon","pause","Pause",true,(View.OnClickListener)v->clicks[0]++);
    LinearLayout chrome=chrome();chrome.addView(button);assertNotNull(button.getOnFocusChangeListener());button.getOnFocusChangeListener().onFocusChange(button,true);
    assertTrue(button.performClick());assertEquals(1,clicks[0]);ui.frames(12);assertEquals(1.018f,button.getScaleX(),.002f);
    button.getOnFocusChangeListener().onFocusChange(button,false);ui.frames(12);assertEquals(1f,button.getScaleX(),.002f);assertEquals(0f,button.getTranslationY(),.001f);
  }
  @Test public void draggingChromeNeverEntersOrHidesThroughAnimation()throws Exception{
    LinearLayout chrome=chrome();put(a,"mCobraTimeshiftDragging",true);call(a,"cobraAnimatePlayerChromeIn",chrome);settled(chrome);
    ((Runnable)get(a,"mHideChrome")).run();ui.frames(20);assertEquals(View.VISIBLE,chrome.getVisibility());settled(chrome);put(a,"mCobraTimeshiftDragging",false);
  }
  @Test public void runtimeDisabledIconCancelsFocusMotionAndKeepsItsDimmedState()throws Exception{
    View button=(View)call(a,"cobraIcon","recent","Last channel",true,(View.OnClickListener)v->{});LinearLayout chrome=chrome();
    // Match the real Last-channel slot; empty icon text has no intrinsic width.
    Button focusAnchor=new Button(a);focusAnchor.setText("Anchor");chrome.addView(focusAnchor,new LinearLayout.LayoutParams(80,46));
    chrome.addView(button,new LinearLayout.LayoutParams(46,46));d.resize((View)chrome.getParent(),1600,900);
    assertEquals("Measured Last-channel width",46,button.getWidth());assertEquals("Measured Last-channel height",46,button.getHeight());
    org.robolectric.shadows.ShadowInstrumentation.getInstrumentation().setInTouchMode(false);
    assertFalse("D-pad fixture must leave touch mode",button.isInTouchMode());
    assertTrue("Establish a different real focus owner",focusAnchor.requestFocus());ui.frames(12);
    assertFalse("Icon must not already own focus",button.hasFocus());assertEquals("Prior focus motion settled",1f,button.getScaleX(),.001f);
    boolean requested=button.requestFocus();
    System.out.println("Disabled-icon focus fixture: requested="+requested+" focused="+button.hasFocus()+" bounds="+button.getWidth()+"x"+button.getHeight()+" alpha="+button.getAlpha()+" scale="+button.getScaleX());
    assertTrue("Measured icon must accept real focus",requested);assertTrue("Measured icon owns real focus",button.hasFocus());
    ui.frames(2);
    System.out.println("Disabled-icon before runtime disable: focused="+button.hasFocus()+" scale="+button.getScaleX());
    assertTrue("Focus animation must have started",button.getScaleX()>1f);
    assertTrue("Disable must interrupt unfinished focus motion",button.getScaleX()<1.018f);
    // Real availability owner: no previous channel means disable, then alpha .35.
    put(a,"mCobraLastChannelButton",button);call(a,"cobraUpdateLastChannelButton");assertFalse(button.isEnabled());assertEquals(.35f,button.getAlpha(),.001f);
    ui.frames(12);assertEquals(.35f,button.getAlpha(),.001f);assertEquals(1f,button.getScaleX(),.001f);
    button.getOnFocusChangeListener().onFocusChange(button,false);ui.frames(12);assertEquals(.35f,button.getAlpha(),.001f);assertEquals(1f,button.getScaleX(),.001f);
  }
}
