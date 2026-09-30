package com.projectinfinity.kodi;
import android.app.Activity;
import android.content.res.Configuration;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.lang.reflect.Method;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import static org.junit.Assert.*;

/** Product acceptance: actual bounds, readable independent choices, real reachable
 * targets, proportional brand art, no navigation/launch side effects during resize.
 * WindowHarness reports multi-window only; normal production View measurement/layout
 * and Canvas rendering run unchanged. Native Kodi decoding is NOT exercised. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w800dp-h1000dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class ResponsiveWindowTest {
 public static class WindowHarness extends Activity {boolean multi;@Override public boolean isInMultiWindowMode(){return multi;}}
 static final int[][] PANES={{320,800},{320,480},{360,360},{720,320},{480,280},{600,400},{240,360},{900,240}};
 static void layout(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
 static void window(CobraNavigationUiTest f,InfinityLiveActivity a,int w,int h)throws Exception{
  RuntimeEnvironment.setQualifiers("w"+w+"dp-h"+h+"dp-"+(w>h?"land":"port")+"-mdpi");org.robolectric.shadows.ShadowDisplay display=Shadows.shadowOf(a.getWindowManager().getDefaultDisplay());display.setWidth(w);display.setHeight(h);display.setRealWidth(w);display.setRealHeight(h);a.getWindow().setLayout(w,h);f.frames(2);View decor=a.getWindow().getDecorView();Object root=org.robolectric.util.ReflectionHelpers.callInstanceMethod(decor,"getViewRootImpl");assertNotNull(root);((org.robolectric.shadows.ShadowViewRootImpl)org.robolectric.shadow.api.Shadow.extract(root)).callDispatchResized();f.measure(a,w,h);assertEquals("Actual rendered window width",w,decor.getWidth());assertEquals("Actual rendered window height",h,decor.getHeight());
 }
 static Rect bounds(ViewGroup root,View v){Rect r=new Rect(0,0,v.getWidth(),v.getHeight());root.offsetDescendantRectToMyCoords(v,r);return r;}
 static void visible(ViewGroup root,View v){assertTrue(v.isShown());Rect r=bounds(root,v);assertTrue("Control escapes actual window: "+r+" in "+root.getWidth()+"x"+root.getHeight(),r.left>=0&&r.top>=0&&r.right<=root.getWidth()&&r.bottom<=root.getHeight());}
 static ArrayList<TextView> text(View v){ArrayList<TextView> out=new ArrayList<>();if(v instanceof TextView&&v.getVisibility()==View.VISIBLE)out.add((TextView)v);if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)out.addAll(text(((ViewGroup)v).getChildAt(i)));return out;}
 static Bitmap render(View v){Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(b));return b;}
 static void save(View v,String name)throws Exception{File dir=new File(System.getProperty("responsive.evidence"));dir.mkdirs();Bitmap b=render(v);try(FileOutputStream stream=new FileOutputStream(new File(dir,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,stream);}b.recycle();}
 @Test public void constrainedChooserIsReadableAndUsesTheActualWindowInsteadOfShrinkingPortraitArt()throws Exception{
  for(String mode:new String[]{"dark","light"})for(int[] pane:PANES){
   ActivityController<WindowHarness> ctl=Robolectric.buildActivity(WindowHarness.class).setup();WindowHarness a=ctl.get();a.multi=true;GlassChooserTest.Calls calls=new GlassChooserTest.Calls(mode);InfinityGlassChooser ui=new InfinityGlassChooser(a,calls);a.setContentView(ui);layout(ui,pane[0],pane[1]);
   save(ui,"observed-chooser-"+mode+"-"+pane[0]+"x"+pane[1]);Rect first=bounds(ui,ui.stage.infinity),second=bounds(ui,ui.stage.cobra);assertFalse(Rect.intersects(first,second));visible(ui,ui.stage.infinity);visible(ui,ui.stage.cobra);
   assertTrue("Choices must use at least 55% of constrained window, rather than miniature portrait composition",(first.width()*first.height()+second.width()*second.height())/(float)(pane[0]*pane[1])>=.55f);
   for(int id:new int[]{InfinityGlassChooser.SETTINGS_INFINITY,InfinityGlassChooser.SETTINGS_COBRA}){View gear=ui.findViewById(id);visible(ui,gear);assertTrue(gear.getWidth()>=48&&gear.getHeight()>=48);}
   for(InfinityGlassChooser.Card card:new InfinityGlassChooser.Card[]{ui.stage.infinity,ui.stage.cobra}){boolean named=false;for(TextView label:text(card))if(label.getText().toString().equals(card.cobra?"COBRA":"INFINITY")){named=true;visible(ui,label);assertTrue("Experience names must remain readable",label.getTextSize()>=15.5f);assertTrue("Entire experience name must fit",label.getPaint().measureText(label.getText().toString())<=label.getWidth());}assertTrue(named);
    if(card.pill!=null){visible(ui,card.pill);assertTrue(card.pill.getHeight()>=48);assertFalse("Settings and Enter touch targets remain independent",Rect.intersects(bounds(ui,card.gear),bounds(ui,card.pill)));}
   }
   assertTrue(calls.entered.isEmpty());assertTrue(calls.settings.isEmpty());save(ui,"chooser-"+mode+"-"+pane[0]+"x"+pane[1]);ctl.pause().stop().destroy();
  }
 }
 @Test public void resizeUsesSameControlsRoutesRealTouchesAndRestoresExactFullscreenPixels()throws Exception{
  for(String mode:new String[]{"dark","light"}){
   ActivityController<WindowHarness> ctl=Robolectric.buildActivity(WindowHarness.class).setup();WindowHarness a=ctl.get();GlassChooserTest.Calls calls=new GlassChooserTest.Calls(mode);InfinityGlassChooser ui=new InfinityGlassChooser(a,calls);a.setContentView(ui);layout(ui,800,1000);ui.clearFocus();Bitmap before=render(ui);View infinity=ui.stage.infinity,cobra=ui.stage.cobra;
   a.multi=true;for(int[] pane:PANES){layout(ui,pane[0],pane[1]);assertSame(infinity,ui.stage.infinity);assertSame(cobra,ui.stage.cobra);assertTrue(calls.entered.isEmpty());assertTrue(calls.settings.isEmpty());}
   layout(ui,320,800);View gear=ui.findViewById(InfinityGlassChooser.SETTINGS_COBRA);Rect r=bounds(ui,gear);long time=SystemClock.uptimeMillis();for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_UP}){MotionEvent event=MotionEvent.obtain(time,time+20,action,r.centerX(),r.centerY(),0);assertTrue(ui.dispatchTouchEvent(event));event.recycle();}assertEquals(Arrays.asList("live"),calls.settings);assertTrue(calls.entered.isEmpty());ui.stage.infinity.performClick();assertEquals(Arrays.asList("infinity"),calls.entered);
   a.multi=false;layout(ui,800,1000);ui.clearFocus();ui.stage.infinity.clearFocus();ui.stage.cobra.clearFocus();Bitmap after=render(ui);assertTrue("Fullscreen restoration must recover identical approved composition",before.sameAs(after));before.recycle();after.recycle();save(ui,"restored-"+mode);ctl.pause().stop().destroy();
  }
 }
 @Test public void largeTextAndInsetConstrainedWindowsKeepSettingsAndChoicesSeparate()throws Exception{
  for(String mode:new String[]{"dark","light"}){ActivityController<WindowHarness> ctl=Robolectric.buildActivity(WindowHarness.class).setup();WindowHarness a=ctl.get();a.multi=true;Configuration c=new Configuration(a.getResources().getConfiguration());c.fontScale=1.6f;a.getResources().updateConfiguration(c,a.getResources().getDisplayMetrics());InfinityGlassChooser ui=new InfinityGlassChooser(a,new GlassChooserTest.Calls(mode));a.setContentView(ui);ui.content.setPadding(12,24,12,28);for(int[] pane:new int[][]{{320,800},{720,320},{336,220}}){layout(ui,pane[0],pane[1]);for(int id:new int[]{InfinityGlassChooser.SETTINGS_INFINITY,InfinityGlassChooser.SETTINGS_COBRA}){visible(ui,ui.findViewById(id));assertTrue(bounds(ui,ui.findViewById(id)).top>=24);}save(ui,"insets-large-font-"+mode+"-"+pane[0]+"x"+pane[1]);}ctl.pause().stop().destroy();}
 }
 @Test public void cobraResponsiveHelpersUseActualDecorWhenPhysicalDisplayAndOrientationDisagree()throws Exception{
  CobraNavigationUiTest fixture=new CobraNavigationUiTest();fixture.clock();InfinityLiveActivity a=fixture.fixture(12);View decor=a.getWindow().getDecorView();layout(decor,320,720);
  // Display metrics and configuration deliberately remain an inner portrait Fold.
  a.getResources().getDisplayMetrics().widthPixels=1200;a.getResources().getDisplayMetrics().heightPixels=1800;
  assertEquals(320,CobraNavigationUiTest.call(a,"cobraWidthDp"));assertEquals(720,CobraNavigationUiTest.call(a,"cobraHeightDp"));assertEquals(true,CobraNavigationUiTest.call(a,"isCompact"));
  layout(decor,720,320);assertEquals(false,CobraNavigationUiTest.call(a,"isPortrait"));assertEquals(true,CobraNavigationUiTest.call(a,"isMedium"));
  ((Handler)CobraNavigationUiTest.get(a,"mMain")).removeCallbacksAndMessages(null);a.finish();
 }
 @Test public void liveTvModesAndDrawerRemainReachableDuringLiveResizeWithoutProviderRebuild()throws Exception{
  CobraNavigationUiTest f=new CobraNavigationUiTest();f.clock();InfinityLiveActivity a=f.fixture(24);Object provider=CobraNavigationUiTest.get(a,"mIo"),channels=CobraNavigationUiTest.get(a,"mChannels");
  for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
   CobraNavigationUiTest.put(a,"mCobraGuideStyle",mode);CobraNavigationUiTest.put(a,"mCobraGuideRoute","channels");CobraNavigationUiTest.call(a,"cobraShowGuideShell");View shell=(View)CobraNavigationUiTest.get(a,"mCobraGuideShell");
   for(int[] pane:new int[][]{{320,800},{600,400},{720,320},{360,480},{800,1000}}){window(f,a,pane[0],pane[1]);assertSame("Persistent shell survives resize",shell,CobraNavigationUiTest.get(a,"mCobraGuideShell"));assertSame(provider,CobraNavigationUiTest.get(a,"mIo"));assertSame(channels,CobraNavigationUiTest.get(a,"mChannels"));assertEquals("channels",CobraNavigationUiTest.get(a,"mCobraGuideRoute"));ViewGroup browser=(ViewGroup)CobraNavigationUiTest.get(a,"mCobraGuideBrowser");assertTrue("Channel browser must retain a usable viewport",browser.getWidth()>=160&&browser.getHeight()>=48);assertNotNull(CobraNavigationUiTest.get(a,"mCobraGuideList"));save(a.getWindow().getDecorView(),"live-"+mode+"-"+pane[0]+"x"+pane[1]);}
  }
  CobraNavigationUiTest.call(a,"toggleCobraDrawer");window(f,a,800,1000);ViewGroup drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");assertNotNull(drawer);window(f,a,320,800);View panel=drawer.getChildAt(0);panel.animate().cancel();panel.setTranslationX(0);panel.setAlpha(1);assertTrue("Open drawer must resize within actual narrow window",panel.getWidth()<=320);View power=drawer.findViewWithTag("cobra_drawer_power");visible(drawer,power);save(a.getWindow().getDecorView(),"drawer-resized");CobraNavigationUiTest.call(a,"closeCobraExperienceDrawer");((Handler)CobraNavigationUiTest.get(a,"mMain")).removeCallbacksAndMessages(null);a.finish();
 }
 @Test public void moviesShowsAndSettingsKeepTheirActualPageAndScrollDuringWindowReflow()throws Exception{
  CobraNavigationUiTest f=new CobraNavigationUiTest();f.clock();InfinityLiveActivity a=f.fixture(12);Object providers=CobraNavigationUiTest.get(a,"mIo");
  for(boolean series:new boolean[]{false,true}){
   CobraNavigationUiTest.put(a,"mCobraInternalScreen","internal");ArrayList<Object> items=new ArrayList<>();for(int i=0;i<12;i++)items.add(CobraNavigationUiTest.construct("VodItem","fixture","item"+i,"Sample title "+i,"Drama","","mp4",series,1750000000000L+i,8.0,"2026"));
   CobraNavigationUiTest.call(a,"renderVodBrowse",items,series,new ArrayList<String>());ViewGroup stage=(ViewGroup)CobraNavigationUiTest.get(a,"mStage");ScrollView scroll=null;for(int i=0;i<stage.getChildCount();i++)if(stage.getChildAt(i) instanceof ScrollView)scroll=(ScrollView)stage.getChildAt(i);assertNotNull(scroll);Object page=scroll.getChildAt(0);String title=(String)CobraNavigationUiTest.get(a,"mCobraStageTitle");
   window(f,a,320,800);scroll.scrollTo(0,140);int retained=scroll.getScrollY();assertTrue("Catalog can actually scroll",retained>0);
   for(int[] pane:new int[][]{{720,320},{360,480},{800,1000},{320,800}}){window(f,a,pane[0],pane[1]);a.onConfigurationChanged(new Configuration(a.getResources().getConfiguration()));window(f,a,pane[0],pane[1]);assertSame(page,scroll.getChildAt(0));assertTrue(scroll.isAttachedToWindow());assertEquals(title,CobraNavigationUiTest.get(a,"mCobraStageTitle"));assertEquals(retained,scroll.getScrollY());assertSame(providers,CobraNavigationUiTest.get(a,"mIo"));assertTrue(scroll.getHeight()>=48&&scroll.getWidth()>=160);save(a.getWindow().getDecorView(),(series?"shows":"movies")+"-"+pane[0]+"x"+pane[1]);}
  }
  CobraNavigationUiTest.call(a,"showSettings");ViewGroup stage=(ViewGroup)CobraNavigationUiTest.get(a,"mStage");View original=stage.getChildAt(stage.getChildCount()-1);for(int[] pane:new int[][]{{320,800},{720,320},{360,480}}){window(f,a,pane[0],pane[1]);a.onConfigurationChanged(new Configuration(a.getResources().getConfiguration()));window(f,a,pane[0],pane[1]);assertTrue(original.isAttachedToWindow());assertEquals("COBRA • SETTINGS",CobraNavigationUiTest.get(a,"mCobraStageTitle"));View header=a.getWindow().getDecorView().findViewWithTag("cobra_settings_drawer_header");assertNotNull(header);visible((ViewGroup)a.getWindow().getDecorView(),header);save(a.getWindow().getDecorView(),"settings-"+pane[0]+"x"+pane[1]);}f.clean(a);
 }
 @Test public void fullscreenResizePreservesPlaybackOwnerDisplayAndPositionWithoutSecondSession()throws Exception{
  Cobra2103268ProductAuditTest p=new Cobra2103268ProductAuditTest();p.before();try{final long[] position={123456};final int[] seeks={0};p.s=p.f.new State(){@Override public Object invoke(Object proxy,Method method,Object[] args){if(method.getName().equals("getCurrentPosition"))return position[0];if(method.getName().equals("seekTo")){seeks[0]++;return null;}return super.invoke(proxy,method,args);}};p.f.states.add(p.s);p.put(p.a,"mPlayer",p.s.player);p.put(p.a,"mPlaying",p.channel);p.call("openPlayerOverlay",p.channel);p.texture=(TextureView)p.get(p.a,"mPlayerTexture");p.f.bind(p.s,p.channel,p.texture);p.measure(800,600);p.mode(10);Object owner=p.s.player,surface=p.texture,source=p.channel;
   for(int[] pane:new int[][]{{320,800},{720,320},{480,280},{600,400},{800,600}}){p.a.onMultiWindowModeChanged(pane[0]!=800,new Configuration(p.a.getResources().getConfiguration()));p.measure(pane[0],pane[1]);assertSame(owner,p.get(p.a,"mPlayer"));assertSame(surface,p.get(p.a,"mPlayerTexture"));assertSame(source,p.get(p.a,"mPlaying"));assertEquals(123456L,position[0]);assertEquals("Resize must not reset the player position",0,seeks[0]);assertEquals(0,p.s.prepares);assertEquals(0,p.s.releases);Object prefs=p.call("cobraReadPreferences",p.call("cobraPreferenceKey",source));assertEquals(10,p.get(prefs,"aspect"));p.call("showCobraAspectPicker");p.f.ui.measure(p.a,pane[0],pane[1]);p.f.ui.frames(15);View close=p.row("cobra_display_close");assertNotNull(close);visible((ViewGroup)p.a.getWindow().getDecorView(),close);save(p.a.getWindow().getDecorView(),"player-display-"+pane[0]+"x"+pane[1]);p.call("closeCobraActionSheet");}
  }finally{p.after();}
 }
}
