package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.view.TextureView;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual production views, selected-state semantics and controlled transport spy.
 * Screenshot evidence is software-rendered; physical Fold/OEM behavior remains a device check. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103208PresentationUiTest {
  Cobra2103199DisplayRegressionTest f;
  InfinityLiveActivity a;
  SharedPreferences prefs;
  @Before public void before()throws Exception{
    Cobra2103208BrandingTest.installApprovedArtwork();
    f=new Cobra2103199DisplayRegressionTest();f.before();a=f.a;prefs=f.prefs;
    prefs.edit().putString(CobraPresentationEffects.AMBIENT,"off").putBoolean(CobraPresentationEffects.NIGHT,false).commit();
    call("cobraOpenLiveTv");measure(412,915);
  }
  @After public void after()throws Exception{if(f!=null)f.after();}
  Object call(String n,Object...v)throws Exception{return CobraNavigationUiTest.call(a,n,v);}
  Object get(String n)throws Exception{return CobraNavigationUiTest.get(a,n);}
  void put(String n,Object v)throws Exception{CobraNavigationUiTest.put(a,n,v);}
  View root(){return a.getWindow().getDecorView();}
  View tag(String n){return root().findViewWithTag(n);}
  void measure(int w,int h)throws Exception{f.ui.measure(a,w,h);f.ui.frames(20);}
  void capture(String name,int w,int h)throws Exception{Cobra2103201MenuPolishTest.capture(a,f.ui,name,w,h);}
  TextView text(View root,String value){
    if(root instanceof TextView&&value.contentEquals(((TextView)root).getText()))return (TextView)root;
    if(root instanceof ViewGroup)for(int i=0;i<((ViewGroup)root).getChildCount();i++){TextView found=text(((ViewGroup)root).getChildAt(i),value);if(found!=null)return found;}
    return null;
  }
  List<View> tagged(View root,String prefix){
    List<View> out=new ArrayList<>();Object value=root.getTag();if(value instanceof String&&((String)value).startsWith(prefix))out.add(root);
    if(root instanceof ViewGroup)for(int i=0;i<((ViewGroup)root).getChildCount();i++)out.addAll(tagged(((ViewGroup)root).getChildAt(i),prefix));
    return out;
  }
  int checkmarks(View root){
    int n=root instanceof TextView&&"✓".contentEquals(((TextView)root).getText())?1:0;
    if(root instanceof ViewGroup)for(int i=0;i<((ViewGroup)root).getChildCount();i++)n+=checkmarks(((ViewGroup)root).getChildAt(i));
    return n;
  }
  Rect bounds(View v){return new Rect(v.getLeft(),v.getTop(),v.getRight(),v.getBottom());}
  View menu()throws Exception{View b=tag("cobra_mode_visuals");assertNotNull(b);assertTrue(b.performClick());measure(412,915);return tag("cobra_themed_sheet");}
  void selected(String row,boolean expected){View v=tag(row);assertNotNull(row,v);assertEquals(row,expected,v.isSelected());assertEquals(row,expected?1:0,checkmarks(v));}
  Map<String,Object> nonVisualPreferences(){Map<String,Object> all=new HashMap<>(prefs.getAll());all.remove(CobraPresentationEffects.AMBIENT);all.remove(CobraPresentationEffects.NIGHT);return all;}

  final class TransportSpy implements InvocationHandler {
    final List<String> writes=new ArrayList<>();
    final TrackSelectionParameters tracks=new TrackSelectionParameters.Builder(a).build();
    final ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);
    public Object invoke(Object proxy,Method m,Object[] args){
      String n=m.getName();if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("equals"))return proxy==args[0];if(n.equals("toString"))return "Presentation transport spy";
      if(n.equals("getCurrentTimeline"))return Timeline.EMPTY;if(n.equals("getVideoSize"))return new VideoSize(1920,1080);
      if(n.equals("getTrackSelectionParameters"))return tracks;if(n.equals("getCurrentTracks"))return Tracks.EMPTY;
      if(n.equals("getPlaybackState"))return Player.STATE_READY;if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return true;
      if(n.equals("getCurrentPosition"))return 37123L;if(n.equals("getVolume"))return .63f;if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getVideoFormat"))return new Format.Builder().setWidth(1920).setHeight(1080).setSampleMimeType("video/avc").build();
      if(n.startsWith("set")||n.startsWith("clear")||n.startsWith("seek")||Arrays.asList("prepare","release","play","pause","stop").contains(n))writes.add(n);
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @SuppressWarnings("unchecked") TransportSpy preview()throws Exception{
    TransportSpy spy=new TransportSpy();Object ch=f.channel(0);Object binding=CobraNavigationUiTest.construct("CobraPlayerBinding",a,spy.player,ch);
    ((Map<ExoPlayer,Object>)get("mCobraPlayerBindings")).put(spy.player,binding);put("mCobraPreviewPlayer",spy.player);
    call("cobraAttachVideo",spy.player,(TextureView)get("mCobraPreviewTexture"));spy.writes.clear();return spy;
  }

  @Test public void visualMenuReplacesOnlyToolbarTransportAndLeavesPreviewPauseReachable()throws Exception{
    ViewGroup toolbar=(ViewGroup)get("mCobraModeToolbar");View visual=tag("cobra_mode_visuals");
    assertNotNull(visual);assertSame(toolbar,visual.getParent());assertNull(toolbar.findViewWithTag("cobra_mode_play_pause"));
    View pause=tag("cobra_preview_play_pause");assertNotNull(pause);assertTrue(pause.isClickable());
    TransportSpy spy=preview();menu();assertTrue("Opening visual choices must not write player state",spy.writes.isEmpty());
    assertEquals(3,tagged(root(),"cobra-visual-ambient:").size());assertEquals(2,tagged(root(),"cobra-visual-night:").size());
    capture("cobra208-visual-menu-412x915",412,915);
  }

  @Test public void menuCheckmarksFollowSavedAmbientAndNightChoices()throws Exception{
    for(String mode:new String[]{"off","subtle","immersive"})for(boolean night:new boolean[]{false,true}){
      call("closeCobraActionSheet");prefs.edit().putString(CobraPresentationEffects.AMBIENT,mode).putBoolean(CobraPresentationEffects.NIGHT,night).commit();menu();
      for(String other:new String[]{"off","subtle","immersive"})selected("cobra-visual-ambient:"+other,mode.equals(other));
      selected("cobra-visual-night:off",!night);selected("cobra-visual-night:on",night);
    }
  }

  @Test public void ambientSelectionsPreservePreviewTransportProfileAndGuideGeometry()throws Exception{
    TransportSpy spy=preview();View shell=(View)get("mCobraGuideShell"),texture=(View)get("mCobraPreviewTexture");Rect geometry=bounds(texture);
    Object mode=get("mCobraGuideStyle"),channel=get("mGuidePreviewChannel"),timeshift=get("mCobraTimeshiftSession");
    String profile=((InfinityCobraFeatureRuntime)get("mFeatures")).activeProfileId();Map<String,Object> unchanged=nonVisualPreferences();
    CobraVisualTheme visualTheme=CobraVisualRenderer.active;String themePointer=CobraVisualTheme.readPointer(a).toString();
    for(String value:new String[]{"subtle","immersive","off"}){
      call("closeCobraActionSheet");menu();spy.writes.clear();assertTrue(tag("cobra-visual-ambient:"+value).performClick());measure(412,915);
      assertEquals(value,prefs.getString(CobraPresentationEffects.AMBIENT,""));assertTrue("Appearance cannot prepare, seek, pause or replace video: "+spy.writes,spy.writes.isEmpty());
      assertSame(spy.player,get("mCobraPreviewPlayer"));assertSame(channel,get("mGuidePreviewChannel"));assertSame(timeshift,get("mCobraTimeshiftSession"));
      assertSame(shell,get("mCobraGuideShell"));assertSame(texture,get("mCobraPreviewTexture"));assertEquals(geometry,bounds(texture));assertEquals(mode,get("mCobraGuideStyle"));
      assertEquals(profile,((InfinityCobraFeatureRuntime)get("mFeatures")).activeProfileId());assertEquals(unchanged,nonVisualPreferences());
      assertSame("Ambient selection must not replace theme runtime",visualTheme,CobraVisualRenderer.active);assertEquals(themePointer,CobraVisualTheme.readPointer(a).toString());
    }
  }

  @Test public void nightSelectionsPreservePreviewTransportAndUserAudioState()throws Exception{
    TransportSpy spy=preview();Object shell=get("mCobraGuideShell"),texture=get("mCobraPreviewTexture");Map<String,Object> unchanged=nonVisualPreferences();
    for(String value:new String[]{"on","off"}){
      call("closeCobraActionSheet");menu();spy.writes.clear();assertTrue(tag("cobra-visual-night:"+value).performClick());measure(412,915);
      assertEquals("on".equals(value),prefs.getBoolean(CobraPresentationEffects.NIGHT,false));assertTrue(spy.writes.toString(),spy.writes.isEmpty());
      assertSame(spy.player,get("mCobraPreviewPlayer"));assertSame(shell,get("mCobraGuideShell"));assertSame(texture,get("mCobraPreviewTexture"));assertEquals(unchanged,nonVisualPreferences());
      assertEquals(.63f,spy.player.getVolume(),0f);assertEquals(37123L,spy.player.getCurrentPosition());
    }
  }

  @Test @SuppressWarnings("unchecked") public void visualChoicesAlsoKeepFullscreenTransportAndPositionUntouched()throws Exception{
    TransportSpy spy=new TransportSpy();Object channel=f.channel(0);TextureView texture=f.texture(412,915);
    put("mPlayer",spy.player);put("mPlaying",channel);put("mPlayerTexture",texture);
    Object binding=CobraNavigationUiTest.construct("CobraPlayerBinding",a,spy.player,channel);
    ((Map<ExoPlayer,Object>)get("mCobraPlayerBindings")).put(spy.player,binding);call("cobraAttachVideo",spy.player,texture);call("cobraBuildPlayerChrome");measure(412,915);
    Object timeshift=get("mCobraTimeshiftSession"),overlay=get("mPlayerOverlay");Rect geometry=bounds(texture);Map<String,Object> unchanged=nonVisualPreferences();
    for(String row:new String[]{"cobra-visual-ambient:immersive","cobra-visual-night:on","cobra-visual-night:off","cobra-visual-ambient:off"}){
      call("closeCobraActionSheet");call("cobraShowVisualMenu",(View)texture);measure(412,915);spy.writes.clear();
      View choice=tag(row);assertNotNull(row,choice);assertTrue(choice.performClick());measure(412,915);
      assertTrue(row+" must not mutate transport: "+spy.writes,spy.writes.isEmpty());assertSame(spy.player,get("mPlayer"));assertSame(channel,get("mPlaying"));
      assertSame(timeshift,get("mCobraTimeshiftSession"));assertSame(overlay,get("mPlayerOverlay"));assertSame(texture,get("mPlayerTexture"));assertEquals(geometry,bounds(texture));
      assertEquals(unchanged,nonVisualPreferences());assertEquals(37123L,spy.player.getCurrentPosition());assertEquals(.63f,spy.player.getVolume(),0f);
    }
  }

  @Test public void drawerKeepsExactlyOriginalDestinationsWithoutStateChips()throws Exception{
    call("toggleCobraDrawer");measure(412,915);View drawer=tag("cobra_experience_drawer");assertNotNull(drawer);
    Set<String> actual=new HashSet<>();for(View row:tagged(drawer,"cobra-destination:")){actual.add((String)row.getTag());assertEquals("No appended chip in drawer navigation",2,((ViewGroup)row).getChildCount());}
    Set<String> expected=new HashSet<>(Arrays.asList("cobra-destination:SEARCH","cobra-destination:TV","cobra-destination:MOVIES","cobra-destination:SHOWS","cobra-destination:RECORDINGS","cobra-destination:MY LIST","cobra-destination:SETTINGS"));
    assertEquals(expected,actual);assertNotNull(drawer.findViewWithTag("cobra-drawer-view"));assertNotNull(drawer.findViewWithTag("cobra_drawer_brand"));
    assertNotNull(drawer.findViewWithTag("cobra_drawer_navigation_group"));assertNotNull(drawer.findViewWithTag("cobra_drawer_footer"));
    assertEquals(0,checkmarks(drawer));assertNull(text(drawer,"ON NOW"));assertNull(text(drawer,"CONNECTED"));
  }

  @Test public void compactFooterPowerOpensOriginalMenuAndCancelKeepsPlayback()throws Exception{
    TransportSpy spy=preview();call("toggleCobraDrawer");measure(412,915);
    View footer=tag("cobra_drawer_footer"),power=tag("cobra_drawer_power");assertNotNull(footer);assertNotNull(power);
    assertTrue("Power remains in the compact bottom footer",isDescendant(power,footer));assertTrue(power.getHeight()>=44);assertTrue(footer.getHeight()<=100);
    spy.writes.clear();assertTrue(power.performClick());measure(412,915);assertNull(tag("cobra_experience_drawer"));
    View powerMenu=tag("cobra_power_menu");assertNotNull(powerMenu);assertNotNull(text(powerMenu,"∞  Switch to Infinity"));assertNotNull(text(powerMenu,"⏻  Exit"));
    TextView cancel=text(powerMenu,"Cancel");assertNotNull(cancel);assertTrue(cancel.performClick());assertNull(tag("cobra_power_menu"));
    assertTrue(spy.writes.toString(),spy.writes.isEmpty());assertSame(spy.player,get("mCobraPreviewPlayer"));
  }
  boolean isDescendant(View child,View ancestor){for(android.view.ViewParent p=child.getParent();p!=null;p=p.getParent())if(p==ancestor)return true;return false;}

  @Test public void settingsHasOnlyHeaderBrandAndKeepsExistingPlainSettingRows()throws Exception{
    call("showSettings");measure(412,915);TextView header=(TextView)get("mHeader");Drawable[] drawables=header.getCompoundDrawables();
    assertNotNull("Approved brand occupies top-right header",drawables[2]);assertNull(drawables[0]);assertNull(drawables[1]);assertNull(drawables[3]);
    View stage=(View)get("mStage");
    for(String row:new String[]{"cobra_theme_management","cobra_ambient_mode","cobra_display_performance","cobra_background_mode","cobra_provider_network_family","cobra_mini_background","cobra_file_picker","cobra_live_rewind"}){
      View control=stage.findViewWithTag(row);assertNotNull(row,control);assertTrue("Settings stays its original button rather than a row with chips",control instanceof Button);
      for(Drawable d:((Button)control).getCompoundDrawables())assertNull("No brand repeated on setting rows",d);
    }
    assertEquals(0,checkmarks(stage));capture("cobra208-settings-header-brand-412x915",412,915);
    call("showWelcome");assertNull("Settings-only header adornment is cleared on another destination",header.getCompoundDrawables()[2]);
  }

  double luminance(int color){double total=0;int[] values={Color.red(color),Color.green(color),Color.blue(color)};double[] weights={.2126,.7152,.0722};for(int i=0;i<3;i++){double s=values[i]/255.;total+=weights[i]*(s<=.04045?s/12.92:Math.pow((s+.055)/1.055,2.4));}return total;}
  double contrast(int a,int b){double x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
  @Test public void drawerRespectsLightDarkAndTrueOledWithReadableOriginalPalette()throws Exception{
    for(String appearance:new String[]{"light","dark","oled"}){
      call("closeCobraExperienceDrawer");prefs.edit().putString("cobra_appearance_mode",appearance).commit();call("cobraApplyAppearanceSettings");call("toggleCobraDrawer");measure(412,915);
      View drawer=tag("cobra_experience_drawer");TextView label=text(drawer,"Live TV");assertNotNull(label);
      int panel=(Integer)call("cobraModeColor","panel"),rail=(Integer)call("cobraModeColor","rail");
      assertTrue(appearance+" navigation label contrast",contrast(label.getCurrentTextColor(),panel)>=4.5);
      if("light".equals(appearance)){assertTrue(luminance(rail)>.7);assertTrue(luminance(label.getCurrentTextColor())<.15);}
      if("oled".equals(appearance))assertEquals(Color.BLACK,rail);
      assertNotNull(tag("cobra_drawer_brand"));assertEquals(appearance,prefs.getString("cobra_appearance_mode",""));
      capture("cobra208-drawer-"+appearance+"-412x915",412,915);
    }
  }

  @Test public void narrowCoverAndInnerLandscapeKeepFooterAndBrandWithinWindow()throws Exception{
    for(int[] size:new int[][]{{320,720},{960,540}}){
      call("closeCobraExperienceDrawer");RuntimeEnvironment.setQualifiers("w"+size[0]+"dp-h"+size[1]+"dp-"+(size[0]>size[1]?"land":"port")+"-mdpi");measure(size[0],size[1]);
      call("toggleCobraDrawer");measure(size[0],size[1]);
      for(String name:new String[]{"cobra_drawer_brand","cobra_drawer_power"}){View v=tag(name);assertNotNull(name,v);Rect visible=new Rect();assertTrue(name,v.getGlobalVisibleRect(visible));assertTrue(name,visible.left>=0&&visible.top>=0&&visible.right<=size[0]&&visible.bottom<=size[1]);assertTrue(name,visible.height()>=v.getHeight()-1);}
      capture("cobra208-drawer-fit-"+size[0]+"x"+size[1],size[0],size[1]);
    }
  }
}
