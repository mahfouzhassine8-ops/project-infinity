package com.projectinfinity.kodi;
import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Matrix;
import android.os.Looper;
import android.view.TextureView;
import android.widget.FrameLayout;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowSystemClock;
import static org.junit.Assert.*;

/** Runs unchanged against 2103229 and 2103230. Controlled Media3 doubles are NOT real provider/decoder proof. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103230RegressionProofTest {
  CobraNavigationUiTest ui;InfinityLiveActivity a;Object[] channels=new Object[2],bindings=new Object[2],tiles=new Object[2];Fake[] players=new Fake[2];
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object call(Object o,String n,Object...args)throws Exception{return CobraNavigationUiTest.call(o,n,args);}
  static class Fake implements InvocationHandler {
    final ExoPlayer player;final TrackSelectionParameters tracks;int state=Player.STATE_READY,prepares,seeks,releases,writes,plays,pauses;boolean requested=true,loading=false;float volume=0f;
    Fake(Context c){tracks=new TrackSelectionParameters.Builder(c).build();player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},this);}
    public Object invoke(Object p,Method method,Object[] args){String n=method.getName();
      if(n.equals("hashCode"))return System.identityHashCode(p);if(n.equals("equals"))return p==args[0];if(n.equals("toString"))return "AuditControlledPlayer";
      if(n.equals("getTrackSelectionParameters"))return tracks;if(n.equals("getCurrentTracks"))return Tracks.EMPTY;
      if(n.equals("getCurrentTimeline"))return Timeline.EMPTY;if(n.equals("getMediaItemCount"))return 1;
      if(n.equals("getVideoSize"))return new VideoSize(1920,1080);
      if(n.equals("getAudioAttributes"))return new AudioAttributes.Builder().setUsage(C.USAGE_MEDIA).setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build();
      if(n.equals("getApplicationLooper"))return Looper.getMainLooper();
      if(n.equals("getPlaybackState"))return state;if(n.equals("getPlayWhenReady"))return requested;
      if(n.equals("isPlaying"))return requested&&state==Player.STATE_READY;if(n.equals("isLoading"))return loading;
      if(n.equals("getVolume"))return volume;if(n.equals("setVolume")){volume=(Float)args[0];return null;}
      if(n.equals("prepare")){prepares++;state=Player.STATE_BUFFERING;return null;}
      if(n.startsWith("seekTo")){seeks++;return null;}if(n.equals("release")){releases++;return null;}
      if(n.equals("setMediaItem")){writes++;return null;}if(n.equals("play")){plays++;requested=true;return null;}if(n.equals("pause")){pauses++;requested=false;return null;}
      Class<?> type=method.getReturnType();if(type==boolean.class)return false;if(type==int.class)return 0;if(type==long.class)return 0L;if(type==float.class)return 0f;if(type==double.class)return 0d;return null;
    }
  }
  @Before @SuppressWarnings("unchecked") public void before()throws Exception{
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(2);
    List<Object> list=(List<Object>)get(a,"mChannels");list.clear();
    for(int i=0;i<2;i++){
      channels[i]=CobraNavigationUiTest.construct("Channel","audit:"+i,"Audit "+i,"Test","epg"+i,"","https://example.invalid/live/primary"+i,"https://example.invalid/live/fallback"+i,Collections.emptyMap());list.add(channels[i]);
      players[i]=new Fake(a);bindings[i]=CobraNavigationUiTest.construct("CobraPlayerBinding",a,players[i].player,channels[i]);
      ((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(players[i].player,bindings[i]);
    }
    put(a,"mMultiPlayers",new ExoPlayer[]{players[0].player,players[1].player});
    Object array=Array.newInstance(channels[0].getClass(),2);Array.set(array,0,channels[0]);Array.set(array,1,channels[1]);put(a,"mMultiChannels",array);
    put(a,"mPlayer",null);put(a,"mPlaying",null);put(a,"mCobraHealthForeground",false);
  }
  @After public void after()throws Exception{if(a!=null)ui.clean(a);CobraVisualRenderer.clients.clear();}
  void idle(long ms){Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(ms));}
  void state(int i,int state)throws Exception{players[i].state=state;call(bindings[i],"onPlaybackStateChanged",state);}
  void pause(int i)throws Exception{players[i].requested=false;call(bindings[i],"onPlayWhenReadyChanged",false,Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST);}
  void error(int i)throws Exception{players[i].state=Player.STATE_IDLE;call(bindings[i],"onPlayerError",new PlaybackException("Controlled error",null,PlaybackException.ERROR_CODE_IO_UNSPECIFIED));}
  @SuppressWarnings("unchecked") void grid()throws Exception{
    FrameLayout overlay=new FrameLayout(a),canvas=new FrameLayout(a);overlay.addView(canvas,new FrameLayout.LayoutParams(-1,-1));((FrameLayout)a.getWindow().getDecorView()).addView(overlay,new FrameLayout.LayoutParams(-1,-1));put(a,"mMultiOverlay",overlay);put(a,"mCobraMultiCanvas",canvas);
    Map<String,Object> entries=(Map<String,Object>)get(get(a,"mCobraTiles"),"entries");
    for(int i=0;i<2;i++){tiles[i]=CobraNavigationUiTest.construct("CobraVideoTile",a,channels[i]);put(tiles[i],"player",players[i].player);entries.put("audit:"+i,tiles[i]);canvas.addView((android.view.View)get(tiles[i],"view"),new FrameLayout.LayoutParams(1000,1000));put(bindings[i],"texture",get(tiles[i],"texture"));}
  }
  @Test public void peerPauseDoesNotCancelAnotherPlayersFallback()throws Exception{
    error(0);pause(1);idle(300);assertEquals("A peer pause must not cancel this player's configured fallback",1,players[0].prepares);assertEquals(0,players[1].prepares);assertEquals(0,players[1].releases);
  }
  @Test public void pausingFailedPlayerStillCancelsItsFallback()throws Exception{
    error(0);pause(0);idle(300);assertEquals(0,players[0].prepares);assertEquals(0,players[0].writes);
  }
  @Test public void endedBufferingEndedUsesSecondAttemptWithoutRequiringReady()throws Exception{
    grid();state(0,Player.STATE_ENDED);idle(450);assertEquals(1,players[0].prepares);
    state(0,Player.STATE_BUFFERING);state(0,Player.STATE_ENDED);idle(450);
    assertEquals("A missing READY event must not latch liveEndedRecovering forever",2,players[0].prepares);
    state(0,Player.STATE_BUFFERING);state(0,Player.STATE_ENDED);idle(450);assertEquals("No third automatic attempt",2,players[0].prepares);assertEquals(0,players[1].prepares);assertEquals(0,players[1].releases);
  }
  @Test public void multiEndedErrorCannotBypassLiveEndedRecoveryBudget(){
    assertEquals("",InfinityLiveActivity.CobraMultiRecoveryPolicy.reason(true,true,Player.PLAYBACK_SUPPRESSION_REASON_NONE,Player.STATE_ENDED,true,60000,60000,false));
  }
  @Test public void activeLoaderIsNotAbortedByEighteenSecondMultiWatchdog()throws Exception{
    grid();players[0].state=Player.STATE_BUFFERING;players[0].loading=true;call(a,"cobraInspectMultiHealth");
    ShadowSystemClock.advanceBy(Duration.ofMillis(18001));call(a,"cobraInspectMultiHealth");assertEquals(0,players[0].prepares);assertEquals(0,players[1].prepares);
  }
  @Test public void promotedFullscreenHonorsItsOwnNormalAspectWithFillSaved()throws Exception{
    grid();((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_multiview_layout_fill_screen",true).putInt("cobra_player_aspect_mode",0).commit();
    put(a,"mCobraMultiFullscreenActive",true);put(a,"mPlayer",players[0].player);put(a,"mPlaying",channels[0]);
    TextureView full=new TextureView(a);full.layout(0,0,1000,1000);put(bindings[0],"texture",full);call(a,"cobraFitBinding",bindings[0]);
    float[] actual=new float[9];full.getTransform(new Matrix()).getValues(actual);Method fit=Class.forName(InfinityLiveActivity.class.getName()+"$CobraLayoutMath").getDeclaredMethod("fit",int.class,int.class,float.class,int.class,int.class,int.class,float.class,float.class);fit.setAccessible(true);float[] expected=(float[])fit.invoke(null,1920,1080,1f,1000,1000,0,1f,1f);
    assertEquals(expected[0],actual[Matrix.MSCALE_X],.001f);assertEquals(expected[1],actual[Matrix.MSCALE_Y],.001f);assertEquals(0,players[0].prepares);assertEquals(0,players[1].releases);
  }
  @Test public void previewUnexpectedEndIsNotSilentlyExcluded()throws Exception{
    put(a,"mMultiPlayers",null);put(a,"mMultiChannels",null);put(a,"mCobraPreviewPlayer",players[0].player);put(a,"mGuidePreviewChannel",channels[0]);state(0,Player.STATE_ENDED);idle(450);assertEquals(1,players[0].prepares);
  }
}
