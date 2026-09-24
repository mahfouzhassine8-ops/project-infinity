package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Looper;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.ExecutorService;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual production Android views/dispatch with controlled media and data. No decoder/device claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w960dp-h540dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103243TvAuditTest {
  CobraNavigationUiTest ui; InfinityLiveActivity a;
  @Before public void before() throws Exception {
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);measure();idle(350);
  }
  @After public void after() throws Exception {if(a!=null)ui.clean(a);CobraVisualRenderer.clients.clear();}
  Object get(String n)throws Exception{return CobraNavigationUiTest.get(a,n);}
  void put(String n,Object value)throws Exception{CobraNavigationUiTest.put(a,n,value);}
  Object call(String n,Object...v)throws Exception{return CobraNavigationUiTest.call(a,n,v);}
  void idle(long ms){Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(ms));}
  View root(){return a.getWindow().getDecorView();}
  View tag(String n){return root().findViewWithTag(n);}
  void measure(){View d=root();for(int i=0;i<3;i++){d.measure(View.MeasureSpec.makeMeasureSpec(960,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(540,View.MeasureSpec.EXACTLY));d.layout(0,0,960,540);idle(16);}}
  boolean inside(View parent,View child){for(View cur=child;cur!=null;cur=cur.getParent() instanceof View?(View)cur.getParent():null)if(cur==parent)return true;return false;}
  Object channel()throws Exception{return ((List<?>)get("mChannels")).get(0);}
  @SuppressWarnings("unchecked") ArrayList<Object> catalog(boolean series)throws Exception {
    List<Object> sources=(List<Object>)get("mSources");
    if(sources.isEmpty())sources.add(CobraNavigationUiTest.construct("LiveSource","fixture","m3u","Fixture Provider","","","","",""));
    ArrayList<Object> items=new ArrayList<>();
    String[] titles={"Target","Target sequel","A Target story","Other"};
    for(int i=0;i<titles.length;i++)items.add(CobraNavigationUiTest.construct("VodItem","fixture","id"+i,titles[i],i==3?"Target genre":"Drama","","mp4",series,100L,8.0,"2025"));
    ArrayList<Object> store=(ArrayList<Object>)get(series?"mCobraVodShowsCatalog":"mCobraVodMoviesCatalog");store.clear();store.addAll(items);return items;
  }
  EditText landing(boolean series)throws Exception {
    ArrayList<Object> items=catalog(series);call("cobraSetSectionOwner",series?"SHOWS":"MOVIES");call("renderVodBrowse",items,series,new ArrayList<String>());measure();
    EditText input=(EditText)tag(series?"cobra_tv_shows_landing_search_2103240":"cobra_tv_movies_landing_search_2103240");assertNotNull(input);return input;
  }
  FrameLayout modal()throws Exception {FrameLayout m=new FrameLayout(a);((FrameLayout)root()).addView(m,new FrameLayout.LayoutParams(-1,-1));put("mCobraActionSheet",m);return m;}
  ListView simpleList(int count){ListView list=new ListView(a);list.setFocusable(true);list.setAdapter(adapter(count));return list;}
  BaseAdapter adapter(final int count){return new BaseAdapter(){public int getCount(){return count;}public Object getItem(int p){return "item"+p;}public long getItemId(int p){return p;}public View getView(int p,View old,ViewGroup parent){Button b=new Button(a);b.setText("Item "+p);b.setFocusable(true);return b;}};}
  final class Media implements InvocationHandler {
    boolean requested=true;int state=Player.STATE_READY,suppression=0;int plays=0,pauses=0;final List<String> writes=new ArrayList<>();
    final ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);
    public Object invoke(Object proxy,Method m,Object[] args){String n=m.getName();
      if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("equals"))return proxy==args[0];if(n.equals("toString"))return "Controlled TV media, not a decoder";
      if(n.equals("getPlayWhenReady"))return requested;if(n.equals("isPlaying"))return requested&&state==Player.STATE_READY&&suppression==0;
      if(n.equals("getPlaybackState"))return state;if(n.equals("getPlaybackSuppressionReason"))return suppression;
      if(n.equals("getVideoSize"))return new VideoSize(1920,1080);if(n.equals("getTrackSelectionParameters"))return new TrackSelectionParameters.Builder(a).build();
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;if(n.equals("getCurrentTimeline"))return Timeline.EMPTY;
      if(n.equals("getAvailableCommands"))return new Player.Commands.Builder().build();if(n.equals("getVolume"))return 1f;
      if(n.equals("play")){plays++;requested=true;}if(n.equals("pause")){pauses++;requested=false;}
      if(n.startsWith("set")||n.startsWith("clear")||n.equals("prepare")||n.equals("release")||n.equals("stop")||n.startsWith("seek"))writes.add(n);
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  Media player()throws Exception {Media m=new Media();put("mPlayer",m.player);put("mPlaying",channel());call("openPlayerOverlay",channel());measure();call("showPlayerChromeTemporarily");measure();return m;}
  @Test public void powerKeepsFocusAgainstDelayedDirectoryRestore()throws Exception {
    call("cobraOpenLiveTv");measure();LinearLayout directory=(LinearLayout)get("mCobraGuideDirectory");ListView list=simpleList(4);directory.addView(list,new LinearLayout.LayoutParams(-1,200));measure();
    call("cobraTvPostDirectoryFocus",list,0);call("showCobraPowerMenu");measure();idle(80);measure();
    assertTrue("DELAYED_DIRECTORY_STOLE_MODAL_FOCUS",inside(tag("cobra_power_menu"),a.getCurrentFocus()));
  }
  @Test public void powerRestoreCannotStealFromNewModal()throws Exception {
    call("cobraOpenLiveTv");measure();call("showCobraPowerMenu");measure();call("cobraTvClosePowerMenuRestoreFocus");
    FrameLayout newer=modal();Button button=new Button(a);button.setText("New modal");newer.addView(button);measure();button.requestFocus();idle(80);
    assertTrue("STALE_POWER_RESTORE_STOLE_NEW_MODAL",inside(newer,a.getCurrentFocus()));
  }
  @Test public void explicitChannelMenuLinksOverrideGeometry()throws Exception {
    FrameLayout m=modal();LinearLayout rows=new LinearLayout(a);rows.setOrientation(LinearLayout.VERTICAL);m.addView(rows);
    Button first=new Button(a),geometric=new Button(a),linked=new Button(a);first.setText("First");geometric.setText("Not next");linked.setText("Explicit next");
    for(Button b:new Button[]{first,geometric,linked}){b.setId(View.generateViewId());rows.addView(b,new LinearLayout.LayoutParams(300,60));}
    first.setNextFocusDownId(linked.getId());measure();first.requestFocus();call("cobraTvMoveTransientFocus",KeyEvent.KEYCODE_DPAD_DOWN);
    assertSame("EXPLICIT_LINK_IGNORED",linked,a.getCurrentFocus());
  }
  @Test public void separateFastDirectionalPressesAreNotDiscarded()throws Exception {
    long t=SystemClock.uptimeMillis();assertEquals(true,call("cobraTvBeginRemoteEdgeAction",new KeyEvent(t,t,KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_RIGHT,0)));
    assertEquals("DISTINCT_FAST_PRESS_DROPPED",true,call("cobraTvBeginRemoteEdgeAction",new KeyEvent(t+30,t+30,KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_LEFT,0)));
  }
  @Test public void heldTransportKeyTogglesOnce()throws Exception {
    Media m=player();long down=SystemClock.uptimeMillis();a.dispatchKeyEvent(new KeyEvent(down,down,KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,0));
    idle(300);a.dispatchKeyEvent(new KeyEvent(down,SystemClock.uptimeMillis(),KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,1));
    a.dispatchKeyEvent(new KeyEvent(down,SystemClock.uptimeMillis(),KeyEvent.ACTION_UP,KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,0));
    assertEquals("HELD_KEY_DOUBLE_TOGGLE",1,m.plays+m.pauses);assertFalse(m.requested);
  }
  @Test public void systemRequestedPauseIsNotAutomaticallyUndone()throws Exception {
    Media m=player();m.requested=false;call("cobraTvRecoverUnexpectedPause",m.player,Player.PLAY_WHEN_READY_CHANGE_REASON_AUDIO_FOCUS_LOSS);idle(400);
    assertEquals("SYSTEM_PAUSE_OVERRIDDEN",0,m.plays);assertFalse(m.requested);
  }
  @Test public void dotDoesNotClaimBufferingOrSuppressionIsPlaying()throws Exception {
    Media m=player();assertEquals(true,call("cobraTvChannelPlaying",channel()));m.state=Player.STATE_BUFFERING;
    assertEquals("BUFFERING_MARKED_PLAYING",false,call("cobraTvChannelPlaying",channel()));m.state=Player.STATE_READY;m.suppression=1;
    assertEquals(false,call("cobraTvChannelPlaying",channel()));m.suppression=0;m.state=Player.STATE_ENDED;assertEquals(false,call("cobraTvChannelPlaying",channel()));
  }
  @Test public void searchSubmitHandsFocusToCurrentResults()throws Exception {
    EditText input=landing(false);input.requestFocus();input.setText("Target");input.onEditorAction(EditorInfo.IME_ACTION_SEARCH);measure();idle(200);measure();
    View first=tag("cobra_vod_landing_search_result_0");assertNotNull(first);assertSame("IME_SUBMIT_LOST_RESULT_FOCUS",first,a.getCurrentFocus());
  }
  @Test public void searchCardMetadataFitsInsideCard()throws Exception {
    EditText input=landing(false);input.setText("Target");idle(180);measure();ViewGroup card=(ViewGroup)tag("cobra_vod_landing_search_result_0");assertNotNull(card);
    View last=card.getChildAt(card.getChildCount()-1);assertTrue("SEARCH_CARD_CONTENT_CLIPPED",last.getBottom()+card.getPaddingBottom()<=card.getHeight());
  }
  @Test public void repeatedQueriesReleaseOldTrimReferences()throws Exception {
    EditText input=landing(false);input.setText("Target");idle(180);measure();int start=((Map<?,?>)get("mCobraVodTrimRoles")).size();
    for(int i=0;i<12;i++){input.setText(i%2==0?"Target ":"Target");idle(180);measure();}
    assertTrue("DISCARDED_SEARCH_VIEWS_RETAINED",((Map<?,?>)get("mCobraVodTrimRoles")).size()<=start+4);
  }
  @Test public void delayedDetailsCannotReplaceNewSection()throws Exception {
    ArrayList<Object> items=catalog(false);call("cobraShowVodDetails",items.get(0));call("clearStage","COBRA • SETTINGS");
    ((CobraNavigationUiTest.PendingIo)get("mIo")).drain();idle(50);measure();
    assertNull("STALE_DETAILS_OPENED_AFTER_NAVIGATION",get("mCobraActionSheet"));assertEquals("COBRA • SETTINGS",get("mCobraStageTitle"));
  }
  @Test public void staleMultiFocusCannotSelectFromReplacedAdapter()throws Exception {
    FrameLayout picker=new FrameLayout(a);put("mCobraMultiPicker",picker);((FrameLayout)root()).addView(picker);ListView list=simpleList(8);list.setTag("cobra_multi_picker_list");picker.addView(list,new FrameLayout.LayoutParams(400,300));measure();
    call("cobraTvFocusMultiRow",5);list.setAdapter(adapter(1));put("mCobraTvMultiRow",0);list.setSelection(0);idle(100);measure();
    assertTrue("STALE_MULTI_SELECTION",list.getSelectedItemPosition()<=0);
  }
  @Test public void playingControlsResetInactivityDeadline()throws Exception {
    player();long delay=CobraPresentationEffects.chromeDelay(false);call("scheduleChromeHide");idle(delay-300);
    long now=SystemClock.uptimeMillis();a.dispatchKeyEvent(new KeyEvent(now,now,KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_LEFT,0));idle(500);
    assertEquals("ACTIVE_INPUT_DID_NOT_RESET_TIMEOUT",View.VISIBLE,((View)get("mPlayerChrome")).getVisibility());
  }
  @Test public void intentionalUserPauseRemainsPaused()throws Exception {Media m=player();call("toggleCobraPlayerPlayPause");idle(600);assertFalse(m.requested);assertEquals(0,m.plays);}
  @Test public void bufferingWatchdogNeverRestartsMedia()throws Exception {Media m=player();m.state=Player.STATE_BUFFERING;((Runnable)get("mStallWatchdog")).run();idle(13000);assertFalse(m.writes.contains("prepare"));assertFalse(m.writes.contains("release"));assertFalse(m.writes.contains("setMediaItem"));}
  @Test public void backHidesChromeBeforeLeavingFullscreen()throws Exception {Media m=player();Object overlay=get("mPlayerOverlay");a.onBackPressed();assertSame(overlay,get("mPlayerOverlay"));assertEquals(View.GONE,((View)get("mPlayerChrome")).getVisibility());a.onBackPressed();assertNull(get("mPlayerOverlay"));assertSame(m.player,get("mCobraPreviewPlayer"));assertFalse(m.writes.contains("release"));}
  @Test public void exactPrefixContainsMetadataSearchOrderPreserved()throws Exception {catalog(false);Object result=call("cobraTvVodSearchMatches",false,"tArGeT","",35);List<?> values=(List<?>)CobraNavigationUiTest.get(result,"items");assertEquals(4,values.size());String[] expected={"Target","Target sequel","A Target story","Other"};for(int i=0;i<4;i++)assertEquals(expected[i],CobraNavigationUiTest.get(values.get(i),"title"));}
  @Test public void moviesAndShowsKeepSingleNativeInputAndSectionOwner()throws Exception {for(boolean shows:new boolean[]{false,true}){EditText input=landing(shows);assertEquals("Type a title or narrow by genre",input.getHint().toString());input.setText("Target");idle(180);measure();input.setText("");idle(180);measure();assertEquals(shows?"SHOWS":"MOVIES",get("mCobraSectionOwner"));assertNull(tag("cobra_vod_landing_search_result_0"));}}
  @Test public void guideRowsRemainVirtualized()throws Exception {ui.clean(a);a=ui.fixture(12000);call("cobraOpenLiveTv");measure();AbsListView list=(AbsListView)get("mCobraGuideList");assertNotNull(list);assertTrue(list.getChildCount()<100);assertTrue(ui.nodes(root())<1200);}
  @Test public void powerActionsRemainPresentAndCancelWorks()throws Exception {call("showCobraPowerMenu");measure();for(String t:new String[]{"cobra_power_switch_infinity","cobra_power_exit","cobra_power_cancel"})assertNotNull(tag(t));assertTrue(tag("cobra_power_cancel").performClick());idle(100);assertNull(tag("cobra_power_menu"));}
}
