package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.LayerDrawable;
import android.os.Bundle;
import android.os.Looper;
import android.view.KeyEvent;
import android.view.TextureView;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.io.File;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.json.JSONObject;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Activity factories/listeners/lifecycle methods with a controlled player.
 * Verifies source wiring and native Android output, not decoding or physical devices. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w960dp-h540dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205PresentationUiTest {
  CobraNavigationUiTest ui; InfinityLiveActivity a; SharedPreferences prefs;Object channel,binding;
  ObservedPlayer player;TextureView texture;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object value)throws Exception{CobraNavigationUiTest.put(o,n,value);}
  Object call(String n,Object...args)throws Exception{return CobraNavigationUiTest.call(a,n,args);}
  View tag(String n){return a.getWindow().getDecorView().findViewWithTag(n);}
  void layout()throws Exception{ui.measure(a,960,540);}
  @Before public void before()throws Exception{
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.loading.set(true);CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(8);prefs=(SharedPreferences)get(a,"mPrefs");
    a.setIntent(new Intent());call("cobraInitPresentationEffects",(Bundle)null);channel=((List<?>)get(a,"mChannels")).get(0);layout();
  }
  @After public void after()throws Exception{
    CobraPresentationEffects effects=(CobraPresentationEffects)get(a,"mCobraEffects");if(effects!=null)effects.close();
    call("cobraReleasePipMediaSession");ui.clean(a);CobraVisualRenderer.clients.clear();
  }
  class ObservedPlayer implements InvocationHandler {
    boolean requested=true;int state=Player.STATE_READY,suppression=Player.PLAYBACK_SUPPRESSION_REASON_NONE;
    long position=60000L,duration=120000L;final List<String>writes=new ArrayList<>();
    final TrackSelectionParameters tracks=new TrackSelectionParameters.Builder(a).build();
    final ExoPlayer instance=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);
    public Object invoke(Object p,Method m,Object[] values){String n=m.getName();
      if(n.equals("hashCode"))return System.identityHashCode(p);if(n.equals("equals"))return p==values[0];if(n.equals("toString"))return "Presentation controlled player";
      if(n.equals("getPlaybackState"))return state;if(n.equals("getPlaybackSuppressionReason"))return suppression;
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return requested;
      if(n.equals("getVideoSize"))return new VideoSize(1920,1080);if(n.equals("getTrackSelectionParameters"))return tracks;
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;if(n.equals("getCurrentTimeline"))return Timeline.EMPTY;
      if(n.equals("getCurrentPosition"))return position;if(n.equals("getDuration"))return duration;
      if(n.equals("isCurrentMediaItemSeekable"))return true;if(n.equals("getCurrentLiveOffset"))return C.TIME_UNSET;
      if(n.equals("getTotalBufferedDuration"))return 20000L;if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;if(n.equals("getApplicationLooper"))return Looper.getMainLooper();
      if(n.equals("seekTo")){position=((Number)values[values.length-1]).longValue();writes.add(n);return null;}
      if(n.equals("pause")){requested=false;writes.add(n);return null;}if(n.equals("play")){requested=true;writes.add(n);return null;}
      if(n.startsWith("set")||n.startsWith("clear")||n.equals("prepare")||n.equals("release")||n.equals("stop"))writes.add(n);
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @SuppressWarnings("unchecked") void single()throws Exception{
    player=new ObservedPlayer();put(a,"mPlayer",player.instance);put(a,"mPlaying",channel);call("openPlayerOverlay",channel);
    texture=(TextureView)get(a,"mPlayerTexture");binding=CobraNavigationUiTest.construct("CobraPlayerBinding",a,player.instance,channel);
    ((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(player.instance,binding);call("cobraAttachVideo",player.instance,texture);
    call("cobraBuildPlayerChrome");layout();player.writes.clear();
  }
  void toggleNight()throws Exception{
    call("showPlayerSettingsDrawer");layout();View row=tag("cobra_night_cinema");assertNotNull(row);assertTrue(row.performClick());layout();
  }
  void unchangedVideo(Matrix before)throws Exception{
    assertSame(player.instance,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));
    assertEquals(before,texture.getTransform(new Matrix()));assertTrue("Presentation must not write to playback: "+player.writes,player.writes.isEmpty());
  }
  void controls()throws Exception{
    for(String name:new String[]{"cobra_player_play_pause","cobra_live_rewind_30","cobra_live_edge","cobra_player_rotation","cobra_player_aspect_anchor","cobra_player_options_anchor"}){
      View control=tag(name);assertNotNull(name,control);assertTrue(name,control.isClickable());
    }
    assertNotNull(tag("cobra_unified_live_timeline"));assertNotNull(tag("cobra_live_timeshift_seek"));
  }
  @Test public void nightMenuPersistsAppliesBlackChromeAndRetainsAllControlsAndTransport()throws Exception{
    single();Matrix matrix=texture.getTransform(new Matrix());controls();assertFalse(prefs.getBoolean(CobraPresentationEffects.NIGHT,false));
    toggleNight();assertTrue(prefs.getBoolean(CobraPresentationEffects.NIGHT,false));assertEquals(true,call("cobraNightCinemaActive"));controls();
    assertFalse("Night Cinema must preserve disabled rewind",prefs.getBoolean("cobra_live_rewind_enabled",false));
    assertEquals(View.GONE,tag("cobra_live_timeshift_seek").getVisibility());
    assertEquals(View.GONE,((View)get(a,"mCobraPlayerSchedule")).getVisibility());assertEquals(View.GONE,((View)get(a,"mCobraPlayerUpcoming")).getVisibility());
    call("cobraRefreshProgrammeLabels");assertEquals(View.GONE,((View)get(a,"mCobraPlayerSchedule")).getVisibility());
    LinearLayout chrome=(LinearLayout)get(a,"mPlayerChrome");View footer=chrome.getChildAt(chrome.getChildCount()-1);
    Bitmap pixels=Cobra2103204PresentationTest.background(footer,Color.MAGENTA);
    try{int bottom=pixels.getPixel(pixels.getWidth()/2,pixels.getHeight()-1);assertTrue(Color.red(bottom)<=2&&Color.green(bottom)<=2&&Color.blue(bottom)<=2);}finally{pixels.recycle();}
    unchangedVideo(matrix);Cobra2103201MenuPolishTest.capture(a,ui,"cobra205-night-cinema-960x540",960,540);
    call("cobraBuildPlayerChrome");layout();assertEquals(View.GONE,((View)get(a,"mCobraPlayerSchedule")).getVisibility());unchangedVideo(matrix);
    toggleNight();assertFalse(prefs.getBoolean(CobraPresentationEffects.NIGHT,false));assertEquals(View.VISIBLE,((View)get(a,"mCobraPlayerSchedule")).getVisibility());controls();unchangedVideo(matrix);
  }
  @Test public void nightTimelineStillSeeksThroughExistingUserListenerOnly()throws Exception{
    // The protected rewind preference is Off by default. Night Cinema must not enable it.
    prefs.edit().putBoolean("cobra_live_rewind_enabled",true).commit();
    single();assertEquals(true,call("cobraTimeshiftTimelineAvailable"));toggleNight();player.writes.clear();SeekBar seek=(SeekBar)tag("cobra_live_timeshift_seek");assertEquals(View.VISIBLE,seek.getVisibility());
    seek.setProgress(250,true); // Programmatic/animated progress must not seek.
    assertTrue(player.writes.isEmpty());
    assertTrue(seek.onKeyDown(KeyEvent.KEYCODE_DPAD_LEFT,new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_LEFT)));
    assertEquals(player.duration*seek.getProgress()/1000L,player.position);assertTrue(player.position<30000L);assertEquals(Collections.singletonList("seekTo"),player.writes);
    assertSame(player.instance,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));
  }
  @Test public void nightShortHideIsRenewedByInteractionAndBlockedByScrubbingOrMenus()throws Exception{
    single();toggleNight();call("showPlayerChromeTemporarily");View chrome=(View)get(a,"mPlayerChrome");
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(1800));assertEquals(View.VISIBLE,chrome.getVisibility());a.onUserInteraction();
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(600));assertEquals(View.VISIBLE,chrome.getVisibility());
    put(a,"mCobraTimeshiftDragging",true);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(2000));assertEquals(View.VISIBLE,chrome.getVisibility());
    put(a,"mCobraTimeshiftDragging",false);call("showPlayerSettingsDrawer");Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(2400));assertNotNull(get(a,"mCobraActionSheet"));
    call("closeCobraActionSheet");call("showPlayerChromeTemporarily");
    assertEquals(true,call("cobraNightCinemaActive"));assertEquals(true,call("cobraChromeCanHide",chrome));
    // This fixture pauses Choreographer: a bulk idle advances time without delivering
    // the 150ms fade frames. Drive real frame steps and check both sides of the deadline.
    ui.frames(129);assertEquals("Before the 2100ms deadline",View.VISIBLE,chrome.getVisibility());assertEquals(1f,chrome.getAlpha(),.001f);
    ui.frames(6);assertEquals("During the existing fade",View.VISIBLE,chrome.getVisibility());assertTrue("Hide starts after 2100ms",chrome.getAlpha()<1f);
    ui.frames(10);assertEquals("Fade completes without another interaction",View.GONE,chrome.getVisibility());
  }
  @Test public void nightIsFullscreenOnlyAndSafeModeKeepsStoredPreferenceRecoverable()throws Exception{
    single();toggleNight();assertEquals(true,call("cobraNightCinemaActive"));
    put(a,"mInPictureInPicture",true);assertEquals(false,call("cobraNightCinemaActive"));put(a,"mInPictureInPicture",false);
    put(a,"mMultiOverlay",new FrameLayout(a));assertEquals(false,call("cobraNightCinemaActive"));put(a,"mMultiOverlay",null);
    a.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));assertEquals(false,call("cobraNightCinemaActive"));assertTrue(prefs.getBoolean(CobraPresentationEffects.NIGHT,false));
  }
  @Test public void actualAmbientControlsPersistAndChangeGuidePixelsWithoutReplacingPreview()throws Exception{
    call("cobraOpenLiveTv");layout();TextureView preview=(TextureView)get(a,"mCobraPreviewTexture");View shell=(View)get(a,"mCobraGuideShell");
    Bitmap original=Cobra2103204PresentationTest.background(shell,Color.MAGENTA);
    for(String mode:new String[]{"subtle","immersive","off"}){
      call("cobraShowAmbientMode");layout();assertTrue(tag("cobra-ambient:"+mode).performClick());layout();ui.frames(20);
      assertEquals(mode,prefs.getString(CobraPresentationEffects.AMBIENT,""));assertSame(preview,get(a,"mCobraPreviewTexture"));assertSame(shell,get(a,"mCobraGuideShell"));
      Bitmap current=Cobra2103204PresentationTest.background(shell,Color.MAGENTA);
      try{if(mode.equals("off"))assertTrue(original.sameAs(current));else assertFalse(original.sameAs(current));}finally{current.recycle();}
      Cobra2103201MenuPolishTest.capture(a,ui,"cobra205-ambient-"+mode+"-960x540",960,540);
    }
    original.recycle();
  }
  @Test public void actualEntryOwnerAndOnNewIntentConsumeGreetingButOrdinaryResumeNeverReplaysIt()throws Exception{
    prefs.edit().putString(CobraPresentationEffects.GREETING,"Welcome back, Hassine").commit();
    a.onNewIntent(new Intent().putExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN,"explicit-chooser-1"));ui.frames(2);layout();
    assertNotNull(tag("cobra_personalized_welcome"));assertEquals("Welcome back, Hassine",((TextView)tag("cobra_welcome_text")).getText().toString());
    assertFalse(a.getIntent().hasExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN));Bundle saved=new Bundle();a.onSaveInstanceState(saved);
    a.onPause();assertNull(tag("cobra_personalized_welcome"));a.onResume();ui.frames(2);assertNull(tag("cobra_personalized_welcome"));
    a.onNewIntent(new Intent());ui.frames(2);assertNull(tag("cobra_personalized_welcome"));
    a.onNewIntent(new Intent().putExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN,"explicit-chooser-1"));ui.frames(2);assertNull(tag("cobra_personalized_welcome"));
    a.onNewIntent(new Intent().putExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN,"explicit-chooser-2"));ui.frames(2);assertNotNull(tag("cobra_personalized_welcome"));
  }
  @Test public void installedArtworkThemeRetainsArtAndExplicitColorsWhileAmbientRemainsActive()throws Exception{
    Bitmap art=Bitmap.createBitmap(32,32,Bitmap.Config.ARGB_8888);
    for(int x=0;x<32;x++)for(int y=0;y<32;y++)art.setPixel(x,y,(x/8+y/8)%2==0?0xffab7021:0xff284625);
    JSONObject json=new JSONObject("{\"id\":\"installed-art-fixture\",\"base\":{\"colors\":{\"fixture_accent\":\"#DD9955\"},\"styles\":{\"screen\":{\"image\":\"art\",\"image_fit\":\"stretch\",\"radius_dp\":0}}}}");
    Constructor<CobraVisualTheme> constructor=CobraVisualTheme.class.getDeclaredConstructor(JSONObject.class,File.class,Map.class,long.class);constructor.setAccessible(true);
    Map<String,Bitmap> images=new HashMap<>();images.put("art",art);CobraVisualRenderer.active=constructor.newInstance(json,null,images,4096L);
    CobraVisualRenderer renderer=(CobraVisualRenderer)call("vtheme");assertTrue(renderer.installed());
    View background=(View)get(a,"mCobraBrowseBackground");renderer.paint(background,"screen");layout();Drawable original=background.getBackground();
    assertTrue(original instanceof CobraVisualRenderer.ArtworkDrawable);Bitmap baseline=Cobra2103204PresentationTest.background(background,Color.MAGENTA);
    prefs.edit().putString(CobraPresentationEffects.AMBIENT,"immersive").commit();call("cobraRefreshAmbient");ui.frames(20);layout();
    assertEquals(CobraPresentationEffects.IMMERSIVE,call("cobraAmbientMode"));assertTrue(background.getBackground() instanceof LayerDrawable);
    assertSame(original,((LayerDrawable)background.getBackground()).getDrawable(0));assertEquals(0xffdd9955,renderer.color("fixture_accent",Color.RED));
    Bitmap ambient=Cobra2103204PresentationTest.background(background,Color.MAGENTA);assertFalse(baseline.sameAs(ambient));
    prefs.edit().putString(CobraPresentationEffects.AMBIENT,"off").commit();call("cobraRefreshAmbient");assertSame(original,background.getBackground());
    Bitmap restored=Cobra2103204PresentationTest.background(background,Color.MAGENTA);assertTrue(baseline.sameAs(restored));baseline.recycle();ambient.recycle();restored.recycle();
  }
  @Test public void safeEntryConsumesExplicitWelcomeTokenWithoutDisplayingOrDeletingGreeting()throws Exception{
    prefs.edit().putString(CobraPresentationEffects.GREETING,"My saved greeting").commit();
    a.onNewIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true).putExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN,"safe-explicit"));ui.frames(2);
    assertNull(tag("cobra_personalized_welcome"));assertFalse(a.getIntent().hasExtra(CobraPresentationEffects.EXTRA_ENTRY_TOKEN));assertEquals("My saved greeting",prefs.getString(CobraPresentationEffects.GREETING,""));
  }
  @Test public void actualPulseBridgeNeverClaimsHealthyPlaybackForDecoderFailurePauseOrSuppression()throws Exception{
    single();assertEquals(CobraPresentationEffects.PulseState.NORMAL,call("cobraVisualPulseState",player.instance));
    put(binding,"error","ERROR_CODE_DECODING_FAILED");player.state=Player.STATE_IDLE;call("cobraUpdatePlaybackLabels");
    assertEquals(CobraPresentationEffects.PulseState.NONE,call("cobraVisualPulseState",player.instance));assertEquals(View.VISIBLE,tag("player_state").getVisibility());assertEquals("Stream unavailable",((TextView)tag("player_state")).getText().toString());
    put(binding,"error","");player.state=Player.STATE_READY;player.requested=false;call("cobraUpdatePlaybackLabels");assertEquals(CobraPresentationEffects.PulseState.NONE,call("cobraVisualPulseState",player.instance));assertEquals("Paused",((TextView)tag("player_state")).getText().toString());
    player.requested=true;player.suppression=Player.PLAYBACK_SUPPRESSION_REASON_TRANSIENT_AUDIO_FOCUS_LOSS;assertEquals(CobraPresentationEffects.PulseState.NONE,call("cobraVisualPulseState",player.instance));
    player.suppression=Player.PLAYBACK_SUPPRESSION_REASON_NONE;player.state=Player.STATE_BUFFERING;call("cobraUpdatePlaybackLabels");assertEquals(CobraPresentationEffects.PulseState.BUFFERING,call("cobraVisualPulseState",player.instance));
    assertEquals(View.INVISIBLE,tag("player_state").getVisibility());assertEquals(View.VISIBLE,tag("cobra_pulse_emblem").getVisibility());assertTrue(player.writes.isEmpty());
  }
}
