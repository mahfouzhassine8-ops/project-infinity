package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real Android views/drawables and Activity wiring. Controlled tracks/players;
 * not a claim of physical decoder concurrency, call audibility or device rendering. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103207RefinementUiTest {
  Cobra2103201SubtitleTest f;
  @Before public void before()throws Exception{f=new Cobra2103201SubtitleTest();f.before();}
  @After public void after()throws Exception{if(f!=null)f.after();}
  Object call(String n,Object...v)throws Exception{return CobraNavigationUiTest.call(f.a,n,v);}
  void preview()throws Exception{CobraNavigationUiTest.put(f.a,"mPlayer",null);CobraNavigationUiTest.put(f.a,"mCobraPreviewPlayer",f.fake.player);}
  View cc()throws Exception{call("cobraUpdatePreviewSubtitleState");return ((View)CobraNavigationUiTest.get(f.a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_captions");}
  @Test public void savedOnWithoutTrackIsNeutral()throws Exception{preview();call("cobraSetCaptionsEnabled",f.fake.player,true);assertFalse(cc().isSelected());assertEquals("No subtitle track available",cc().getContentDescription());}
  @Test public void supportedButUnselectedTrackIsNeutral()throws Exception{preview();call("cobraSetCaptionsEnabled",f.fake.player,true);f.tracks(Cobra2103201SubtitleTest.group("en","text/vtt","en",true,false));assertFalse(cc().isSelected());}
  @Test public void selectedSupportedTrackIsActiveThenOffClearsIt()throws Exception{preview();call("cobraSetCaptionsEnabled",f.fake.player,true);f.tracks(Cobra2103201SubtitleTest.group("en","text/vtt","en",true,true));assertTrue(cc().isSelected());call("cobraSetCaptionsEnabled",f.fake.player,false);assertFalse(cc().isSelected());}
  @Test public void unsupportedSelectedTrackCannotClaimEnabled()throws Exception{preview();f.tracks(Cobra2103201SubtitleTest.group("en","text/vtt","en",false,true));assertFalse(cc().isSelected());}
  Bitmap paint(Drawable d,int[] state){d.setState(state);d.jumpToCurrentState();d.setBounds(0,0,64,48);Bitmap b=Bitmap.createBitmap(64,48,Bitmap.Config.ARGB_8888);d.draw(new Canvas(b));return b;}
  void evidence(Bitmap b,String name)throws Exception{new Cobra2103205PresentationEffectsTest().evidence(b,name);}
  @Test public void focusedOffHasTransparentCenterButActiveHasBlueFill()throws Exception{
    Drawable d=(Drawable)call("cobraCaptionControlSurface",true);
    Bitmap off=paint(d,new int[]{android.R.attr.state_enabled,android.R.attr.state_focused});assertEquals(0,Color.alpha(off.getPixel(32,24)));
    Bitmap on=paint(d,new int[]{android.R.attr.state_enabled,android.R.attr.state_selected});assertTrue(Color.alpha(on.getPixel(32,24))>0);
    evidence(off,"cobra207-cc-focus-off");evidence(on,"cobra207-cc-active");
  }
  @Test public void videoEmblemHasNoBlackDisc()throws Exception{
    CobraPresentationEffects.PulseView mark=new CobraPresentationEffects.PulseView(f.a);mark.allowMotion(false);mark.layout(0,0,40,40);
    Bitmap b=Bitmap.createBitmap(40,40,Bitmap.Config.ARGB_8888);mark.draw(new Canvas(b));int opaque=0,black=0;
    for(int y=0;y<40;y++)for(int x=0;x<40;x++){int c=b.getPixel(x,y);if(Color.alpha(c)>0){opaque++;if((c&0xffffff)==0)black++;}}
    assertTrue(opaque>0);assertEquals(0,black);assertEquals(0,Color.alpha(b.getPixel(1,20)));
    evidence(b,"cobra207-transparent-emblem");
  }
  @Test public void greetingUsesHeaderBoundsAndRestoresTitleAfterHold()throws Exception{
    FrameLayout root=new FrameLayout(f.a);TextView title=new TextView(f.a);title.setText("TV Grid");FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(280,56);lp.leftMargin=48;root.addView(title,lp);
    ((FrameLayout)f.a.getWindow().getDecorView()).addView(root,new FrameLayout.LayoutParams(-1,-1));
    root.measure(View.MeasureSpec.makeMeasureSpec(412,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(915,View.MeasureSpec.EXACTLY));root.layout(0,0,412,915);
    CobraPresentationEffects effects=new CobraPresentationEffects(f.a);effects.showWelcome(root,"Welcome back, Hassine",false,false,title);
    View row=root.findViewWithTag("cobra_personalized_welcome");assertNotNull(row);assertNull(row.getBackground());assertEquals(280,row.getLayoutParams().width);assertEquals(56,row.getLayoutParams().height);assertEquals(0f,title.getAlpha(),0f);assertFalse(row.isClickable());
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(2400));assertTrue(effects.welcomeVisible());
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(800));assertFalse(effects.welcomeVisible());assertEquals(1f,title.getAlpha(),0f);effects.close();
  }
  @Test public void dismissGreetingAlwaysRestoresExistingTitleAlpha()throws Exception{
    FrameLayout root=new FrameLayout(f.a);View title=new View(f.a);root.addView(title);root.layout(0,0,412,915);title.layout(50,0,300,56);title.setAlpha(.7f);
    CobraPresentationEffects effects=new CobraPresentationEffects(f.a);effects.showWelcome(root,"Welcome back",true,false,title);effects.setForeground(false);assertEquals(.7f,title.getAlpha(),0f);assertFalse(effects.welcomeVisible());effects.close();
  }
  @Test public void freshCapacityAndStaleCapacityAreDistinct(){long now=500000L;assertTrue(CobraQuickPeekSession.capacityFresh(new CobraQuickPeekSession.Capacity(2,1,now),now));assertFalse(CobraQuickPeekSession.capacityFresh(new CobraQuickPeekSession.Capacity(2,1,now-120001),now));assertFalse(CobraQuickPeekSession.capacityFresh(null,now));}
}
