package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import androidx.media3.common.AudioAttributes;
import androidx.media3.common.PlaybackParameters;
import androidx.media3.common.Player;
import androidx.media3.common.TrackSelectionParameters;
import androidx.media3.common.Tracks;
import androidx.media3.common.VideoSize;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowActivity;
import org.robolectric.shadows.ShadowChoreographer;

/** Real production buttons, scroll and dispatcher. Only terminal fullscreen,
 * menu and OS PiP boundaries are host spies. No decoder/OS PiP claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
  qualifiers="w412dp-h915dp-port-mdpi",instrumentedPackages={"com.projectinfinity.kodi"},
  shadows={CobraPlayerButtonDispatchTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraPlayerButtonDispatchTest {
  static final List<String> ENDPOINTS=new ArrayList<>();
  @Before public void controlledFrames(){
    ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));
  }
  static final class Playback implements InvocationHandler {
    float volume=1;boolean playing=true;
    public Object invoke(Object p,Method m,Object[] args){
      String n=m.getName();
      if(n.equals("equals"))return p==args[0];if(n.equals("hashCode"))return System.identityHashCode(p);
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return playing;
      if(n.equals("getPlaybackState"))return Player.STATE_READY;
      if(n.equals("getVolume"))return volume;if(n.equals("setVolume")){volume=(Float)args[0];return null;}
      if(n.equals("getTrackSelectionParameters"))return TrackSelectionParameters.DEFAULT_WITHOUT_CONTEXT;
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;if(n.equals("getVideoSize"))return VideoSize.UNKNOWN;
      if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;
      if(n.equals("getAvailableCommands"))return Player.Commands.EMPTY;
      if(n.equals("getApplicationLooper"))return Looper.getMainLooper();
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;
      if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true,looseSignatures=true)
  public static class TerminalActions extends ShadowActivity {
    @RealObject InfinityLiveActivity owner;
    @Implementation protected void promoteCobraPreviewToFullscreen(Object channel)throws Exception {
      ENDPOINTS.add("fullscreen");
      CobraArrangeIntegrationTest.set(owner,"mPlayer",CobraArrangeIntegrationTest.get(owner,"mCobraPreviewPlayer"));
      CobraArrangeIntegrationTest.set(owner,"mPlayerOverlay",new FrameLayout(owner));
    }
    @Implementation protected void showCobraChannelActions(Object channel){ENDPOINTS.add("more");}
    @Implementation protected void enterCobraPictureInPicture(){ENDPOINTS.add("pip");}
  }
  static final class Fixture {
    final CobraArrangeIntegrationTest.Fixture base;
    final InfinityLiveActivity a;final ViewGroup root;final Object channel,player;
    final FrameLayout preview;final LinearLayout nativeRow;CobraProUi.Hero hero;
    CobraProUi.Program visualProgram;
    Fixture(String initialMode)throws Exception {
      base=new CobraArrangeIntegrationTest.Fixture(0,"mobile",412,915);a=base.a;root=base.root;
      CobraArrangeIntegrationTest.set(a,"mMultiOverlay",null);
      CobraArrangeIntegrationTest.set(a,"mFeatures",new InfinityCobraFeatureRuntime(a));
      CobraArrangeIntegrationTest.set(a,"mCobraPreviewAutoplayAllowed",false);
      base.prefs.edit().putString("guide_view_mode",initialMode).commit();
      CobraArrangeIntegrationTest.set(a,"mCobraGuideStyle",initialMode);
      CobraArrangeIntegrationTest.set(a,"mCobraProActive",false);
      CobraArrangeIntegrationTest.set(a,"mCobraGuideDetails",new LinearLayout(a));
      channel=CobraArrangeIntegrationTest.construct("Channel","buttons-qa","Synthetic QA","Group","epg","","https://example.invalid/qa","source",Collections.emptyMap());
      CobraArrangeIntegrationTest.set(a,"mGuidePreviewChannel",channel);
      ((List)CobraArrangeIntegrationTest.get(a,"mChannels")).add(channel);
      // The real entry sequence constructs/restores the native preview before
      // cobraEnterProMode sets active=true. Do not pre-set the active flag.
      preview=(FrameLayout)CobraArrangeIntegrationTest.call(a,"cobraPreviewPanel",channel,false);
      nativeRow=preview.findViewWithTag("cobra_preview_controls");
      root.removeAllViews();root.addView(preview,new FrameLayout.LayoutParams(-1,-1));
      CobraArrangeIntegrationTest.set(a,"mCobraGuideStyle","focus");
      CobraArrangeIntegrationTest.call(a,"cobraEnterProMode",new ArrayList((List)CobraArrangeIntegrationTest.get(a,"mChannels")));
      hero=(CobraProUi.Hero)CobraArrangeIntegrationTest.get(a,"mCobraProHeroUi");
      player=Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},new Playback());
      ready();layout(412,915);
    }
    void ready()throws Exception {
      CobraArrangeIntegrationTest.set(a,"mPlayerOverlay",null);
      CobraArrangeIntegrationTest.set(a,"mPlayer",null);
      CobraArrangeIntegrationTest.set(a,"mGuidePreviewChannel",channel);
      CobraArrangeIntegrationTest.set(a,"mCobraPreviewPlayer",player);
      CobraArrangeIntegrationTest.set(a,"mCobraPreviewSessionKey",CobraArrangeIntegrationTest.call(a,"cobraChannelKey",channel));
      CobraArrangeIntegrationTest.set(a,"mCobraPlayerLocked",false);
      CobraArrangeIntegrationTest.set(a,"mCobraProState",CobraProUi.WATCHING);
      CobraArrangeIntegrationTest.set(a,"mCobraProPlaybackOwned",true);
      CobraArrangeIntegrationTest.call(a,"cobraProSelectPlayingSlot",channel);
      CobraArrangeIntegrationTest.call(a,"cobraRefreshProHero");
      CobraArrangeIntegrationTest.call(a,"cobraSetProState",CobraProUi.WATCHING,false);
      ENDPOINTS.clear();
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(400));
      // Sports presentation uses explicitly synthetic Program data. The native
      // button dispatcher and callbacks are unchanged; no live Sports feed is
      // simulated or accepted by this host fixture.
      if(visualProgram!=null)hero.bind(visualProgram,visualProgram.sports?1:0,2);
      hero.revealControls();
      hero.setState(CobraProUi.WATCHING,null,false);hero.playback(true,false,false,true);
    }
    void layout(int w,int h){
      CobraArrangeIntegrationTest.measure(a.getWindow().getDecorView(),w,h);
      CobraArrangeIntegrationTest.measure(root,w,h);
    }
    void pointer(int action,float x,float y,long start,long time){
      MotionEvent e=MotionEvent.obtain(start,time,action,x,y,0);
      try{assertTrue(root.dispatchTouchEvent(e));}finally{e.recycle();}
    }
    String press(int index,int scroll,boolean remote)throws Exception {
      ready();layout(root.getWidth(),root.getHeight());
      hero.controlScroll.scrollTo(scroll<0?centeredScroll(index):scroll,0);layout(root.getWidth(),root.getHeight());
      View target=hero.player[index];assertEquals(View.VISIBLE,target.getVisibility());assertTrue(target.isEnabled());
      assertEquals("the pressed production view draws the expected icon",
        index==4?"fullscreen":index==8?"pip":"more",CobraArrangeIntegrationTest.get(target,"glyph"));
      Rect visible=new Rect();assertTrue("target has actual visible hit rectangle",target.getGlobalVisibleRect(visible));
      if(remote){
        target.setFocusableInTouchMode(true);assertTrue(target.requestFocus());
        long t=SystemClock.uptimeMillis();
        assertTrue(root.dispatchKeyEvent(new KeyEvent(t,t,KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_CENTER,0)));
        assertTrue(root.dispatchKeyEvent(new KeyEvent(t,t+16,KeyEvent.ACTION_UP,KeyEvent.KEYCODE_DPAD_CENTER,0)));
      } else {
        int[] at=new int[2];root.getLocationOnScreen(at);
        float x=visible.exactCenterX()-at[0],y=visible.exactCenterY()-at[1];
        long t=SystemClock.uptimeMillis();
        pointer(MotionEvent.ACTION_DOWN,x,y,t,t);pointer(MotionEvent.ACTION_UP,x,y,t,t+32);
      }
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(32));
      assertTrue("one press cannot double dispatch: "+ENDPOINTS,
        ENDPOINTS.equals(Arrays.asList("fullscreen")) || ENDPOINTS.equals(Arrays.asList("fullscreen","pip")) || ENDPOINTS.equals(Arrays.asList("more")));
      if(ENDPOINTS.contains("pip")){
        assertSame(player,CobraArrangeIntegrationTest.get(a,"mPlayer"));return "pip";
      }
      if(ENDPOINTS.contains("more")){
        assertSame(player,CobraArrangeIntegrationTest.get(a,"mCobraPreviewPlayer"));return "more";
      }
      assertNotNull("one visual press reaches original fullscreen or menu/PiP",CobraArrangeIntegrationTest.get(a,"mPlayerOverlay"));
      assertSame(player,CobraArrangeIntegrationTest.get(a,"mPlayer"));return "fullscreen";
    }
    int centeredScroll(int index){return Math.max(0,hero.player[index].getLeft()-hero.controlScroll.getWidth()/2+hero.player[index].getWidth()/2);}
    int moreIndex(){return nativeRow.indexOfChild(nativeRow.findViewWithTag("cobra_preview_options_anchor"));}
  }
  @Test public void initialProEntryActualVisualButtonsHaveSeparateActions()throws Exception {
    List<String> actual=new ArrayList<>();
    for(int index:new int[]{4,8,5}){Fixture f=new Fixture("focus");actual.add(f.press(index,f.centeredScroll(index),false));}
    System.out.println("COBRA_VISUAL_BUTTON_ROUTES "+actual);
    assertEquals(Arrays.asList("fullscreen","pip","more"),actual);
  }
  @Test public void retainedNonProEntryAndRemoteClicksKeepTargetsAndMoreLast()throws Exception {
    for(String mode:new String[]{"mobile","compact","cards","grid"}){
      Fixture f=new Fixture(mode);assertEquals(7,f.nativeRow.getChildCount());
      assertEquals(6,f.moreIndex());
      List<String> actual=new ArrayList<>();
      for(int index:new int[]{4,8,5}){
        actual.add(f.press(index,f.centeredScroll(index),true));
        assertEquals("semantic dispatch must not reorder the retained native row",6,f.moreIndex());
      }
      assertEquals(mode,Arrays.asList("fullscreen","pip","more"),actual);
      CobraArrangeIntegrationTest.call(f.a,"cobraExitProMode");
      CobraArrangeIntegrationTest.set(f.a,"mCobraGuideStyle",mode);
      assertEquals("non-Pro More-last survives actual Pro exit",6,f.moreIndex());
    }
  }
  @Test public void clippedVisibleFragmentsAndResizesKeepCorrectHitTargets()throws Exception {
    Fixture f=new Fixture("focus");boolean clipped=false;
    for(int[] size:new int[][]{{280,500},{720,420},{360,800}}){
      f.layout(size[0],size[1]);
      for(int index:new int[]{4,8,5}){
        int offset=Math.max(0,f.hero.player[index].getLeft()-f.hero.controlScroll.getWidth()+12);
        String actual=f.press(index,offset,false);
        assertEquals(index==4?"fullscreen":index==8?"pip":"more",actual);
        Rect visible=new Rect();assertTrue(f.hero.player[index].getGlobalVisibleRect(visible));
        clipped|=visible.width()<f.hero.player[index].getWidth();
      }
    }
    assertTrue("at least one actual partially clipped button was pressed",clipped);
  }
  @Test public void horizontalDragsAtBothEdgesDoNotClickOrPageHero()throws Exception {
    Fixture f=new Fixture("focus");
    for(int edge:new int[]{0,f.hero.controlStrip.getWidth()}){
      f.ready();f.hero.controlScroll.scrollTo(edge,0);f.layout(280,500);
      int before=(Integer)CobraArrangeIntegrationTest.get(f.a,"mCobraProHeroIndex");
      int[] at=new int[2];f.hero.controlScroll.getLocationInWindow(at);
      int[] rootAt=new int[2];f.root.getLocationInWindow(rootAt);
      float y=at[1]-rootAt[1]+20,x=at[0]-rootAt[0]+f.hero.controlScroll.getWidth()/2f;
      long t=SystemClock.uptimeMillis();
      f.pointer(MotionEvent.ACTION_DOWN,x,y,t,t);
      f.pointer(MotionEvent.ACTION_MOVE,x-50,y,t,t+32);
      f.pointer(MotionEvent.ACTION_MOVE,x+50,y,t,t+64);
      f.pointer(MotionEvent.ACTION_CANCEL,x+50,y,t,t+80);
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(100));
      assertTrue(ENDPOINTS.isEmpty());assertEquals(before,CobraArrangeIntegrationTest.get(f.a,"mCobraProHeroIndex"));
      assertFalse(f.hero.controlGesture);
    }
  }
  @Test public void nativeSixControlPreviewAlsoBindsFullscreenAndMoreByIdentity()throws Exception {
    android.content.pm.PackageManager pm=RuntimeEnvironment.getApplication().getPackageManager();
    Shadows.shadowOf(pm).setSystemFeature("android.software.leanback",true);
    try{
      Fixture f=new Fixture("focus");assertEquals(6,f.nativeRow.getChildCount());
      assertEquals("fullscreen",f.press(4,f.centeredScroll(4),false));
      assertEquals("more",f.press(5,f.centeredScroll(5),false));
      assertEquals(5,f.moreIndex());
    }finally{Shadows.shadowOf(pm).setSystemFeature("android.software.leanback",false);}
  }
  @Test public void sportsAndRegularHeroButtonsKeepOrderAndSameThreeDestinations()throws Exception {
    for(boolean sports:new boolean[]{false,true}){
      Fixture f=new Fixture("focus");CobraProUi.Program p=new CobraProUi.Program();
      p.channel="Synthetic QA";p.title="Synthetic program";p.live=true;p.sports=sports;
      p.sportsAvailable=sports;p.sportsMultiAvailable=sports;f.visualProgram=p;
      List<String> actual=new ArrayList<>();
      for(int index:new int[]{4,8,5})actual.add(f.press(index,-1,false));
      assertEquals(Arrays.asList("fullscreen","pip","more"),actual);
      f.ready();f.layout(412,915);
      List<Integer> visible=new ArrayList<>();
      for(int i=0;i<f.hero.controlStrip.getChildCount();i++){
        View v=f.hero.controlStrip.getChildAt(i);if(v.getVisibility()==View.VISIBLE)
          for(int j=0;j<f.hero.player.length;j++)if(f.hero.player[j]==v)visible.add(j);
      }
      assertEquals(sports?Arrays.asList(0,1,2,3,4,8,6,7,5):Arrays.asList(0,1,2,3,4,8,5),visible);
    }
  }
}
