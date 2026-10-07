package com.projectinfinity.kodi;

import android.app.Activity;
import android.os.Looper;
import android.os.SystemClock;
import android.view.InputDevice;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import androidx.media3.common.C;
import androidx.media3.common.Format;
import androidx.media3.common.TrackGroup;
import androidx.media3.common.TrackSelectionParameters;
import androidx.media3.common.Tracks;
import androidx.media3.exoplayer.ExoPlayer;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.Shadows;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.LooperMode;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Production Hero dispatch, layout and callback tests. No provider or decoding claims. */
@RunWith(org.robolectric.RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraProControlsRefinementTest {
  ActivityController<Activity> controller;
  Activity activity;
  InterceptingParent parent;
  CobraProUi.Hero hero;
  Calls calls;

  static final class Calls implements CobraProUi.Actions {
    final int[] control=new int[8];int steps;Runnable onControl;
    public void preview(){}public void unmute(){}public void step(int delta){steps+=delta;}
    public void control(int index){control[index]++;if(onControl!=null)onControl.run();}
  }
  static final class InterceptingParent extends FrameLayout {
    boolean disallow;int stolenMoves;
    InterceptingParent(Activity a){super(a);}
    @Override public void requestDisallowInterceptTouchEvent(boolean value){disallow=value;super.requestDisallowInterceptTouchEvent(value);}
    @Override public boolean onInterceptTouchEvent(MotionEvent e){if(e.getActionMasked()==MotionEvent.ACTION_MOVE){stolenMoves++;return true;}return false;}
    @Override public boolean onTouchEvent(MotionEvent e){return true;}
  }
  @Before public void setup(){
    controller=Robolectric.buildActivity(Activity.class).setup();activity=controller.get();calls=new Calls();parent=new InterceptingParent(activity);
    hero=new CobraProUi.Hero(activity,true,calls,null);parent.addView(hero,new FrameLayout.LayoutParams(-1,-1));activity.setContentView(parent);
    bind(true);layout(412,310);hero.clearFocus();
  }
  @After public void cleanup(){controller.pause().stop().destroy();}
  void bind(boolean sports){CobraProUi.Program p=new CobraProUi.Program();p.channel="Fixture channel";p.title="Fixture program";p.source=sports?"LIVE SPORTS":"FROM CHANNELS";p.sports=sports;p.live=true;p.sportsAvailable=true;p.sportsMultiAvailable=true;hero.bind(p,sports?6:0,7);hero.setState(CobraProUi.WATCHING,null,false);hero.playback(true,true,false,true);}
  void layout(int w,int h){parent.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));parent.layout(0,0,w,h);}
  void event(int action,float x,float y,long start){MotionEvent e=MotionEvent.obtain(start,SystemClock.uptimeMillis(),action,x,y,0);try{parent.dispatchTouchEvent(e);}finally{e.recycle();}}
  List<String> visibleLabels(){List<String> labels=new ArrayList<>();for(int i=0;i<hero.controlStrip.getChildCount();i++){View v=hero.controlStrip.getChildAt(i);if(v.getVisibility()==View.VISIBLE)labels.add(v.getContentDescription().toString());}return labels;}
  int totalCalls(){int count=0;for(int n:calls.control)count+=n;return count;}
  int[] bounds(View v){return new int[]{v.getLeft(),v.getTop(),v.getRight(),v.getBottom()};}
  void wheel(float x,float y,float scroll){MotionEvent.PointerProperties p=new MotionEvent.PointerProperties();p.id=0;p.toolType=MotionEvent.TOOL_TYPE_MOUSE;MotionEvent.PointerCoords c=new MotionEvent.PointerCoords();c.x=x;c.y=y;c.setAxisValue(MotionEvent.AXIS_HSCROLL,scroll);long now=SystemClock.uptimeMillis();MotionEvent e=MotionEvent.obtain(now,now,MotionEvent.ACTION_SCROLL,1,new MotionEvent.PointerProperties[]{p},new MotionEvent.PointerCoords[]{c},0,0,1,1,0,0,InputDevice.SOURCE_MOUSE,0);try{assertTrue(hero.dispatchGenericMotionEvent(e));}finally{e.recycle();}}

  @Test public void sportsOrderIsExactAndRegularModeRetainsSixActions(){
    assertEquals(Arrays.asList("Pause","Favorite","Subtitles","Unmute","Fullscreen","Stats","Multi-View","More"),visibleLabels());
    int[] indices={0,1,2,3,4,6,7,5};for(int i=0;i<indices.length;i++)assertSame(hero.player[indices[i]],hero.controlStrip.getChildAt(i));
    assertTrue(hero.controlStrip.getWidth()>hero.controlScroll.getWidth());hero.controlScroll.scrollTo(hero.controlStrip.getWidth(),0);
    View more=hero.player[5];assertTrue(more.getRight()-hero.controlScroll.getScrollX()<=hero.controlScroll.getWidth());
    bind(false);layout(412,310);assertEquals(Arrays.asList("Pause","Favorite","Subtitles","Unmute","Fullscreen","More"),visibleLabels());assertEquals(0,hero.controlScroll.getScrollX());
  }
  @Test public void eachVisualActionKeepsCorrectCallbackAndRapidRepeatsAreCoalesced(){
    for(int i=0;i<hero.controlStrip.getChildCount();i++){View action=hero.controlStrip.getChildAt(i);action.performClick();action.performClick();}
    for(int count:calls.control)assertEquals(1,count);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(351));for(CobraProUi.Action action:hero.player)action.performClick();
    for(int count:calls.control)assertEquals(2,count);
    hero.player[6].setEnabled(false);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(351));hero.player[6].performClick();assertEquals(2,calls.control[6]);
    bind(false);hero.player[7].performClick();assertEquals(2,calls.control[7]);
  }
  @Test public void callbackCannotReenterAndDispatchRecoversAfterException(){
    calls.onControl=()->hero.player[1].performClick();hero.player[0].performClick();assertEquals(1,calls.control[0]);assertEquals(0,calls.control[1]);
    calls.onControl=()->{throw new IllegalStateException("fixture callback");};try{hero.player[2].performClick();fail("Expected fixture failure");}catch(IllegalStateException expected){assertEquals("fixture callback",expected.getMessage());}
    calls.onControl=null;hero.player[1].performClick();assertEquals(1,calls.control[1]);assertFalse(hero.dispatchingControl);
  }
  @Test public void stripDragRetainsOwnershipOutsideBoundsAndAtBothScrollEdges(){
    for(int edge:new int[]{0,hero.controlStrip.getWidth()}){
      hero.controlScroll.scrollTo(edge,0);long start=SystemClock.uptimeMillis();float y=hero.controlScroll.getTop()+30;
      event(MotionEvent.ACTION_DOWN,300,y,start);assertTrue(hero.controlGesture);assertTrue(parent.disallow);
      // A child/edge cannot hand this already-owned gesture to the Hero or an ancestor.
      hero.requestDisallowInterceptTouchEvent(false);assertTrue(parent.disallow);
      event(MotionEvent.ACTION_MOVE,150,y,start);event(MotionEvent.ACTION_MOVE,40,40,start);event(MotionEvent.ACTION_UP,20,35,start);
      assertFalse(hero.controlGesture);assertFalse(parent.disallow);assertEquals(0,parent.stolenMoves);assertEquals(0,calls.steps);assertEquals(0,totalCalls());
    }
  }
  @Test public void holdingStripBeyondOldTimeoutKeepsControlsUntilGestureEnds(){
    long start=SystemClock.uptimeMillis();float y=hero.controlScroll.getTop()+30;event(MotionEvent.ACTION_DOWN,300,y,start);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(9));hero.collapseControls();assertTrue(hero.controlsVisible);assertEquals(View.VISIBLE,hero.controlScroll.getVisibility());
    event(MotionEvent.ACTION_CANCEL,300,y,start);assertFalse(hero.controlGesture);assertFalse(parent.disallow);hero.clearFocus();hero.collapseControls();assertFalse(hero.controlsVisible);
  }
  @Test public void cancellationReleasesStripAndNextHeroSwipeChangesPane(){
    long start=SystemClock.uptimeMillis();float y=hero.controlScroll.getTop()+30;event(MotionEvent.ACTION_DOWN,300,y,start);event(MotionEvent.ACTION_CANCEL,150,y,start);
    assertFalse(hero.controlGesture);assertFalse(parent.disallow);
    // Dispatch directly to Hero here: the synthetic ancestor intentionally steals non-control moves.
    for(int[] e:new int[][]{{MotionEvent.ACTION_DOWN,300,90},{MotionEvent.ACTION_MOVE,160,90},{MotionEvent.ACTION_UP,30,90}}){MotionEvent m=MotionEvent.obtain(start,SystemClock.uptimeMillis(),e[0],e[1],e[2],0);try{hero.dispatchTouchEvent(m);}finally{m.recycle();}}
    assertEquals(1,calls.steps);assertEquals(0,totalCalls());
  }
  @Test public void stripHitTestIncludesBothAxesAndWheelEdgesNeverPageHero(){
    float y=hero.controlScroll.getTop()+30;assertFalse(hero.insideControlStrip(hero.controlScroll.getLeft()-1,y));assertFalse(hero.insideControlStrip(hero.controlScroll.getRight(),y));assertFalse(hero.insideControlStrip(200,hero.controlScroll.getBottom()));
    for(int edge:new int[]{0,hero.controlStrip.getWidth()}){hero.controlScroll.scrollTo(edge,0);wheel(200,y,edge==0?1:-1);assertEquals(0,calls.steps);}
    wheel(200,90,-1);assertEquals(1,calls.steps);
  }
  @Test public void controlVisibilityAndScrollPreserveOverlayBoundsAcrossWindowSizes(){
    for(int[] size:new int[][]{{280,280},{412,310},{720,420},{915,300}}){
      hero.revealControls();layout(size[0],size[1]);int[] heroBounds=bounds(hero),shade=bounds(hero.shade),transport=bounds(hero.transport),strip=bounds(hero.controlScroll);
      hero.controlScroll.scrollTo(hero.controlStrip.getWidth(),0);layout(size[0],size[1]);assertArrayEquals(heroBounds,bounds(hero));assertArrayEquals(shade,bounds(hero.shade));assertArrayEquals(transport,bounds(hero.transport));assertArrayEquals(strip,bounds(hero.controlScroll));
      hero.clearFocus();hero.collapseControls();layout(size[0],size[1]);assertFalse(hero.controlsVisible);assertArrayEquals(heroBounds,bounds(hero));assertArrayEquals(shade,bounds(hero.shade));assertArrayEquals(transport,bounds(hero.transport));assertArrayEquals(strip,bounds(hero.controlScroll));
      hero.performClick();layout(size[0],size[1]);assertTrue(hero.controlsVisible);assertArrayEquals(heroBounds,bounds(hero));assertArrayEquals(shade,bounds(hero.shade));assertArrayEquals(transport,bounds(hero.transport));
    }
    assertEquals(0,calls.steps);assertEquals(0,totalCalls());
  }

  static final class TrackStub extends CobraProHandoffTest.Stub {
    TrackSelectionParameters params=TrackSelectionParameters.DEFAULT_WITHOUT_CONTEXT.buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_TEXT,false).setSelectUndeterminedTextLanguage(true).build();
    final Tracks tracks=new Tracks(Arrays.asList(new Tracks.Group(new TrackGroup("fixture-text",new Format.Builder().setSampleMimeType("text/vtt").setLanguage("en").build()),false,new int[]{C.FORMAT_HANDLED},new boolean[]{true})));
    int parameterWrites;
    @Override public Object invoke(Object proxy,Method method,Object[] args){
      if(method.getName().equals("getTrackSelectionParameters"))return params;
      if(method.getName().equals("setTrackSelectionParameters")){params=(TrackSelectionParameters)args[0];parameterWrites++;return null;}
      if(method.getName().equals("getCurrentTracks"))return tracks;
      return super.invoke(proxy,method,args);
    }
  }
  TrackStub installTrackPlayer(CobraProHandoffTest f)throws Exception{
    TrackStub state=new TrackStub();f.state=state;f.player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},state);return state;
  }
  void bindTrackPlayer(CobraProHandoffTest f)throws Exception{Object binding=construct("CobraPlayerBinding",f.a,f.player,f.channel(0));((Map)get(f.a,"mCobraPlayerBindings")).put(f.player,binding);}
  View sheetRow(CobraProHandoffTest f,String tag)throws Exception{View sheet=(View)get(f.a,"mCobraActionSheet");assertNotNull(sheet);View row=sheet.findViewWithTag(tag);assertNotNull(tag,row);return row;}
  @Test public void sportsSubtitlesOpenExistingSessionSheetAndNestedSettingsReturn()throws Exception{
    CobraProHandoffTest f=new CobraProHandoffTest();f.setup();try{
      f.pro();Object game=f.addLiveGameForChannel(0);call(f.a,"cobraProFilter",4);TrackStub state=installTrackPlayer(f);f.sportsMini(0,game);bindTrackPlayer(f);f.f.measure(f.a,412,915);
      int pane=(Integer)get(f.a,"mCobraProHeroIndex");long position=state.position;float volume=state.volume;ExoPlayer original=f.player;
      f.hero().player[2].performClick();assertEquals("tracks",get(f.a,"mCobraSheetKind"));assertSame(original,get(f.a,"mCobraTrackSheetPlayer"));assertEquals(0,state.parameterWrites);assertTrue(f.text((View)get(f.a,"mCobraActionSheet")).contains("Audio & subtitles"));
      sheetRow(f,"cobra-track-off").performClick();assertTrue(state.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertEquals(1,state.parameterWrites);
      call(f.a,"cobraProControl",2);assertEquals("tracks",get(f.a,"mCobraSheetKind"));sheetRow(f,"cobra-subtitle-size").performClick();assertEquals("subtitle-size",get(f.a,"mCobraSheetKind"));sheetRow(f,"cobra-subtitle-size:125").performClick();assertEquals("tracks",get(f.a,"mCobraSheetKind"));assertEquals(125,call(f.a,"cobraSubtitleSize"));assertSame(original,get(f.a,"mCobraTrackSheetPlayer"));
      sheetRow(f,"cobra-subtitle-adaptation").performClick();assertEquals("subtitle-adaptation",get(f.a,"mCobraSheetKind"));sheetRow(f,"cobra-subtitle-adaptation:false").performClick();assertEquals("tracks",get(f.a,"mCobraSheetKind"));assertEquals(false,call(f.a,"cobraSubtitleAdaptive"));
      sheetRow(f,"cobra-channel-subtitles").performClick();assertEquals("channel-language",get(f.a,"mCobraSheetKind"));sheetRow(f,"cobra-channel-language:off").performClick();assertEquals("tracks",get(f.a,"mCobraSheetKind"));assertSame(original,get(f.a,"mCobraTrackSheetPlayer"));
      assertSame(original,get(f.a,"mCobraPreviewPlayer"));assertEquals(pane,get(f.a,"mCobraProHeroIndex"));assertEquals(position,state.position);assertEquals(volume,state.volume,0);assertTrue(state.playing);assertFalse(state.released);assertEquals(0,state.prepares);assertEquals(0,state.changes);assertEquals(0,state.pauses);assertEquals(0,state.seeks);
    }finally{f.cleanup();}
  }
  @Test public void regularPreviewSubtitleControlKeepsExistingToggleBehavior()throws Exception{
    CobraProHandoffTest f=new CobraProHandoffTest();f.setup();try{
      f.pro();TrackStub state=installTrackPlayer(f);f.activeMini(0);bindTrackPlayer(f);f.hero().player[2].performClick();
      assertTrue(state.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertEquals(1,state.parameterWrites);assertNull(get(f.a,"mCobraActionSheet"));assertSame(f.player,get(f.a,"mCobraPreviewPlayer"));assertEquals(0,state.prepares);assertEquals(0,state.changes);
    }finally{f.cleanup();}
  }
  @Test public void sportsSubtitlesWithoutCurrentBindingDoNotOpenOrMutateSession()throws Exception{
    CobraProHandoffTest f=new CobraProHandoffTest();f.setup();try{
      f.pro();Object game=f.addLiveGameForChannel(0);call(f.a,"cobraProFilter",4);TrackStub state=installTrackPlayer(f);f.sportsMini(0,game);f.hero().player[2].performClick();
      assertNull(get(f.a,"mCobraActionSheet"));assertEquals(0,state.parameterWrites);assertEquals("Subtitles are unavailable. Start the live game and try again.",org.robolectric.shadows.ShadowToast.getTextOfLatestToast());assertEquals(0,state.prepares);assertEquals(0,state.changes);
    }finally{f.cleanup();}
  }
}
