package com.projectinfinity.kodi;
import android.app.Application;
import android.content.*;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.common.text.*;
import androidx.media3.exoplayer.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Production views and recovery adapters; synthetic guide/cues and explicit ExoPlayer double.
 * Not network, codec, GPU, audio hardware, install or full Activity lifecycle acceptance.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraHealthUiTest {
  final CobraNavigationUiTest ui=new CobraNavigationUiTest();
  @Before public void clock(){ui.clock();}
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object call(Object o,String n,Object... args)throws Exception{return CobraNavigationUiTest.call(o,n,args);}
  View tag(InfinityLiveActivity a,String name){return a.getWindow().getDecorView().findViewWithTag(name);}
  void click(InfinityLiveActivity a,String name)throws Exception{View v=tag(a,name);assertNotNull(name,v);assertTrue(name,v.performClick());ui.measure(a,412,915);}
  void shot(InfinityLiveActivity a,String name)throws Exception{
    View view=a.getWindow().getDecorView();Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));
    File root=new File(System.getProperty("cobra.evidence"));assertTrue(root.isDirectory()||root.mkdirs());
    try(FileOutputStream out=new FileOutputStream(new File(root,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}bitmap.recycle();
  }
  @Test(timeout=90000) public void drawerOnlyRevealsModesAfterViewAndPreservesTexture()throws Exception{
    InfinityLiveActivity a=ui.fixture(192);try{
      call(a,"cobraOpenLiveTv");ui.measure(a,412,915);ui.guide(a);Object texture=get(a,"mCobraPreviewTexture");
      for(String theme:new String[]{"dark","light","oled"}){
        ((SharedPreferences)get(a,"mPrefs")).edit().putString("cobra_appearance_mode",theme).commit();
        call(a,"toggleCobraDrawer");ui.measure(a,412,915);assertNotNull(tag(a,"cobra-drawer-view"));
        for(String mode:new String[]{"mobile","grid","compact","cards","focus"})assertNull(tag(a,"cobra-view-mode:"+mode));
        shot(a,"cobra-drawer-"+theme);click(a,"cobra-drawer-view");assertNull(tag(a,"cobra_experience_drawer"));
        assertEquals("view-mode",get(a,"mCobraSheetKind"));shot(a,"cobra-view-chooser-"+theme);
        for(String mode:new String[]{"mobile","grid","compact","cards","focus"})assertNotNull(tag(a,"cobra-view-mode:"+mode));
        click(a,"cobra-view-mode:compact");assertEquals("compact",get(a,"mCobraGuideStyle"));assertSame(texture,get(a,"mCobraPreviewTexture"));
      }
    }finally{ui.clean(a);}
  }
  @Test(timeout=90000) public void healthCenterReadsWithoutDestroyingGuideOrStartingProviderWork()throws Exception{
    InfinityLiveActivity a=ui.fixture(192);try{
      call(a,"cobraOpenLiveTv");ui.measure(a,412,915);Object shell=get(a,"mCobraGuideShell"),texture=get(a,"mCobraPreviewTexture");
      CobraNavigationUiTest.PendingIo io=(CobraNavigationUiTest.PendingIo)get(a,"mIo");int queued=io.tasks.size();
      call(a,"toggleCobraDrawer");click(a,"cobra-drawer-health");
      assertSame(shell,get(a,"mCobraGuideShell"));assertSame(texture,get(a,"mCobraPreviewTexture"));assertEquals(queued,io.tasks.size());
      assertTrue(((TextView)tag(a,"cobra-health-summary")).getText().toString().contains("No active playback"));
      assertNotNull(tag(a,"cobra-health-export"));shot(a,"cobra-health-idle");
      a.onBackPressed();assertNull(get(a,"mCobraActionSheet"));assertSame(texture,get(a,"mCobraPreviewTexture"));
    }finally{ui.clean(a);}
  }
  @Test(timeout=90000) public void channelPreferencesPersistWithSourceAndProfileIsolationAndScopedReset()throws Exception{
    InfinityLiveActivity a=ui.fixture(192);try{
      Object c=((List<?>)get(a,"mChannels")).get(0),other=((List<?>)get(a,"mChannels")).get(1);
      String key=(String)call(a,"cobraPreferenceKey",c),otherKey=(String)call(a,"cobraPreferenceKey",other);assertNotEquals(key,otherKey);
      call(a,"cobraShowChannelPreferences",c);ui.measure(a,412,915);shot(a,"cobra-channel-playback");click(a,"cobra-channel-aspect");click(a,"cobra-channel-aspect:2");
      SharedPreferences prefs=(SharedPreferences)get(a,"mPrefs");assertEquals(2,new JSONObject(prefs.getString(key,"")).getInt("aspect"));assertFalse(prefs.contains(otherKey));
      click(a,"cobra-channel-audio");click(a,"cobra-channel-language:ar");assertEquals("ar",new JSONObject(prefs.getString(key,"")).getString("audio"));
      click(a,"cobra-channel-recovery");click(a,"cobra-channel-recovery:off");assertEquals("off",new JSONObject(prefs.getString(key,"")).getString("recovery"));
      Object reloaded=call(a,"cobraReadPreferences",key);assertEquals(2,get(reloaded,"aspect"));assertEquals("ar",get(reloaded,"audio"));
      prefs.edit().putString("unrelated-test","keep").commit();click(a,"cobra-channel-reset");assertTrue(prefs.contains(key));click(a,"cobra-channel-reset-confirm");assertFalse(prefs.contains(key));assertEquals("keep",prefs.getString("unrelated-test",""));
      InfinityCobraFeatureRuntime features=(InfinityCobraFeatureRuntime)get(a,"mFeatures");String id=features.createProfile("Playback test","",false);assertTrue(features.unlockAndSelectProfile(id,""));assertNotEquals(key,call(a,"cobraPreferenceKey",c));
    }finally{ui.clean(a);}
  }
  static final class PlayerDouble implements InvocationHandler {
    ExoPlayer player;TrackSelectionParameters params;final DecoderCounters video=new DecoderCounters(),audio=new DecoderCounters();
    final List<String> writes=new ArrayList<>();boolean requested=true,playing=true,released;int state=Player.STATE_READY;long position=30000;
    PlayerDouble(Context c){params=new TrackSelectionParameters.Builder(c).build();player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);}
    public Object invoke(Object proxy,Method method,Object[] args){String n=method.getName();
      if(n.equals("toString"))return "Explicit ExoPlayer test double";if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("equals"))return proxy==args[0];
      if(n.equals("getTrackSelectionParameters"))return params;if(n.equals("getCurrentTracks"))return Tracks.EMPTY;
      if(n.equals("getVideoSize"))return new VideoSize(1920,1080);if(n.equals("getVideoFormat"))return new Format.Builder().setWidth(1920).setHeight(1080).setSampleMimeType("video/avc").build();
      if(n.equals("getAudioFormat"))return new Format.Builder().setSampleMimeType("audio/mp4a-latm").build();
      if(n.equals("getVideoDecoderCounters"))return video;if(n.equals("getAudioDecoderCounters"))return audio;
      if(n.equals("getPlaybackState"))return state;if(n.equals("getPlayWhenReady"))return requested;if(n.equals("isPlaying"))return playing;if(n.equals("isReleased"))return released;
      if(n.equals("getCurrentPosition"))return position;if(n.equals("getTotalBufferedDuration"))return 5000L;
      if(n.equals("setTrackSelectionParameters")){params=(TrackSelectionParameters)args[0];writes.add(n);return null;}
      if(n.startsWith("set")||n.startsWith("clear")||n.startsWith("remove")||n.equals("release")||n.equals("prepare")||n.equals("play")||n.equals("stop")||n.startsWith("seek"))writes.add(n);
      if(n.equals("release"))released=true;
      Class<?> type=method.getReturnType();if(type==boolean.class)return false;if(type==int.class)return 0;if(type==long.class)return 0L;if(type==float.class)return 0f;if(type==double.class)return 0d;return null;
    }
  }
  @SuppressWarnings("unchecked") Object attach(InfinityLiveActivity a,PlayerDouble fake)throws Exception{
    Object c=((List<?>)get(a,"mChannels")).get(0);Object binding=CobraNavigationUiTest.construct("CobraPlayerBinding",a,fake.player,c);
    ((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(fake.player,binding);put(a,"mCobraPreviewPlayer",fake.player);
    TextureView texture=(TextureView)get(a,"mCobraPreviewTexture");texture.setSurfaceTexture(new SurfaceTexture(0));
    call(a,"cobraAttachVideo",fake.player,texture);ui.measure(a,412,915);assertTrue(texture.isAvailable());return binding;
  }
  @Test(timeout=90000) public void recoveryAdapterOnlyReattachesCurrentSurfaceAndNeverRestartsPlayer()throws Exception{
    InfinityLiveActivity a=ui.fixture(192);try{
      call(a,"cobraOpenLiveTv");ui.measure(a,412,915);PlayerDouble fake=new PlayerDouble(a);Object binding=attach(a,fake);Object original=get(a,"mCobraPreviewTexture");
      put(a,"mCobraHealthForeground",true);fake.writes.clear();call(a,"cobraReattachObservedSurface",binding);
      assertEquals(Arrays.asList("clearVideoTextureView","setVideoTextureView"),fake.writes);assertSame(fake.player,get(a,"mCobraPreviewPlayer"));assertSame(original,get(a,"mCobraPreviewTexture"));assertEquals(30000,fake.position);
      fake.writes.clear();put(a,"mBackgroundStopped",true);call(a,"cobraReattachObservedSurface",binding);assertTrue(fake.writes.isEmpty());
      put(a,"mBackgroundStopped",false);fake.requested=false;call(a,"cobraReattachObservedSurface",binding);assertTrue(fake.writes.isEmpty());
      fake.requested=true;put(a,"mInPictureInPicture",true);call(a,"cobraReattachObservedSurface",binding);assertTrue(fake.writes.isEmpty());
      put(a,"mInPictureInPicture",false);fake.state=Player.STATE_BUFFERING;call(a,"cobraReattachObservedSurface",binding);assertTrue(fake.writes.isEmpty());
    }finally{ui.clean(a);}
  }
  @Test(timeout=90000) public void bufferingBudgetAndDisposalCannotLoopOrLeaveSessionObserver()throws Exception{
    InfinityLiveActivity a=ui.fixture(192);try{
      call(a,"cobraOpenLiveTv");ui.measure(a,412,915);PlayerDouble fake=new PlayerDouble(a);attach(a,fake);
      Object channel=((List<?>)get(a,"mChannels")).get(0);String key=(String)call(a,"cobraPreferenceKey",channel);Object prefs=call(a,"cobraReadPreferences",key);put(prefs,"aspect",2);fake.writes.clear();
      assertEquals(true,call(a,"cobraSavePreferences",channel,key,prefs,false));assertFalse("Display changes must not reset manual track selection",fake.writes.contains("setTrackSelectionParameters"));
      assertEquals(true,call(a,"cobraPermitBufferRetry",fake.player));assertEquals(true,call(a,"cobraPermitBufferRetry",fake.player));assertEquals(false,call(a,"cobraPermitBufferRetry",fake.player));
      call(a,"cobraSuspendHealth");assertEquals(false,get(a,"mCobraHealthForeground"));fake.writes.clear();call(a,"cobraDisposePlayer",fake.player);
      assertTrue(fake.released);assertTrue(fake.writes.contains("removeAnalyticsListener"));assertTrue(((Map<?,?>)get(a,"mCobraPlayerBindings")).isEmpty());
    }finally{ui.clean(a);}
  }
  @Test(timeout=90000) public void captionCuesActuallyRenderAndOffPreferenceClearsThem()throws Exception{
    InfinityLiveActivity a=ui.fixture(192);try{
      call(a,"cobraOpenLiveTv");ui.measure(a,412,915);PlayerDouble fake=new PlayerDouble(a);Object binding=attach(a,fake);
      Cue cue=new Cue.Builder().setText("Cobra caption presentation fixture").build();call(binding,"onCues",new CueGroup(Arrays.asList(cue),0));
      View overlay=(View)get(binding,"captions");assertTrue(overlay.isAttachedToWindow());assertEquals(View.VISIBLE,overlay.getVisibility());ui.measure(a,412,915);shot(a,"cobra-captions-fixture");
      Object c=((List<?>)get(a,"mChannels")).get(0);String key=(String)call(a,"cobraPreferenceKey",c);Object prefs=call(a,"cobraReadPreferences",key);put(prefs,"subtitles","off");
      assertEquals(true,call(a,"cobraSavePreferences",c,key,prefs,false));assertTrue(fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertEquals(View.GONE,overlay.getVisibility());
    }finally{ui.clean(a);}
  }
  @Test(timeout=90000) public void errorEvidenceSurvivesReadyAndIsIncludedInExportSnapshot()throws Exception{
    InfinityLiveActivity a=ui.fixture(192);try{
      call(a,"cobraOpenLiveTv");ui.measure(a,412,915);PlayerDouble fake=new PlayerDouble(a);Object binding=attach(a,fake);
      call(binding,"onPlayerError",new PlaybackException("Fixture error",null,PlaybackException.ERROR_CODE_IO_NETWORK_CONNECTION_FAILED));call(binding,"onPlaybackStateChanged",Player.STATE_READY);
      assertEquals("",get(binding,"error"));assertFalse(((String)get(get(binding,"vitals"),"lastError")).isEmpty());
      JSONObject snapshot=new JSONObject((String)call(a,"cobraFreshHealthSnapshot"));JSONArray sessions=snapshot.getJSONArray("session_health");assertEquals(1,sessions.length());assertTrue(sessions.getJSONObject(0).getString("last_error_code").contains("NETWORK"));
      call(a,"showCobraHealthCenter");ui.measure(a,412,915);shot(a,"cobra-health-observed-session");
    }finally{ui.clean(a);}
  }
}
