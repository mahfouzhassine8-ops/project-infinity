package com.projectinfinity.kodi;
import android.app.*;
import android.content.*;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.*;
import java.io.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real Android layout/lifecycle methods with explicit controlled playback doubles.
 * These tests do not claim a real device, provider, codec or hardware GPU test. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103164RegressionTest {
  final CobraNavigationUiTest ui=new CobraNavigationUiTest();
  @Before public void before(){
    ui.clock();CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    Context app=RuntimeEnvironment.getApplication();
    app.getSharedPreferences("infinity_runtime",0).edit().clear().commit();
    app.getSharedPreferences("infinity_player_rotation",0).edit().clear().commit();
    Shadows.shadowOf((Application)app).grantPermissions("android.permission.POST_NOTIFICATIONS");
  }
  static Object get(Object a,String n)throws Exception{return CobraNavigationUiTest.get(a,n);}
  static void put(Object a,String n,Object v)throws Exception{CobraNavigationUiTest.put(a,n,v);}
  static Object call(Object o,String n,Object...args)throws Exception{
    for(Class<?> type=o.getClass();type!=null;type=type.getSuperclass())for(Method m:type.getDeclaredMethods())if(m.getName().equals(n)&&m.getParameterCount()==args.length){m.setAccessible(true);try{return m.invoke(o,args);}catch(InvocationTargetException e){Throwable c=e.getCause();if(c instanceof Exception)throw (Exception)c;throw new AssertionError(c);}}
    throw new NoSuchMethodException(n);
  }
  InfinityLiveActivity activity()throws Exception{
    InfinityLiveActivity a=ui.fixture(24);
    put(a,"mDeviceBridge",new InfinityCobraDeviceBridge(a,()->{try{return (Boolean)call(a,"hasCobraVideo");}catch(Exception e){throw new AssertionError(e);}}));
    call(a,"onResume");return a;
  }
  void clean(InfinityLiveActivity a)throws Exception{
    call(a,"cobraEndMiniBackgroundPlayback");call(a,"closePlayer");
    InfinityCobraDeviceBridge d=(InfinityCobraDeviceBridge)get(a,"mDeviceBridge");if(d!=null)d.close();
    ui.clean(a);
  }
  static final class Video implements InvocationHandler {
    final ExoPlayer player;final List<String> commands=new ArrayList<>();final List<Player.Listener> listeners=new ArrayList<>();
    final TrackSelectionParameters tracks; boolean ready=true,released=false;int state=Player.STATE_READY;float volume=1f;long position=12345L;
    Video(Context c){tracks=new TrackSelectionParameters.Builder(c).build();player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);}
    public Object invoke(Object proxy,Method m,Object[] args){String n=m.getName();
      if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("equals"))return args[0]==proxy;if(n.equals("toString"))return "ControlledVideo";
      if(n.equals("getPlaybackState"))return state;if(n.equals("getPlayWhenReady"))return ready;if(n.equals("isPlaying"))return ready&&state==Player.STATE_READY&&!released;
      if(n.equals("getVideoSize"))return new VideoSize(1920,1080);if(n.equals("getVideoFormat"))return new Format.Builder().setWidth(1920).setHeight(1080).setSampleMimeType("video/avc").build();
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;if(n.equals("getTrackSelectionParameters"))return tracks;
      if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;if(n.equals("getCurrentPosition"))return position;if(n.equals("getDuration"))return 120000L;
      if(n.equals("getVolume"))return volume;
      if(n.equals("addListener")){listeners.add((Player.Listener)args[0]);return null;}if(n.equals("removeListener")){listeners.remove(args[0]);return null;}
      if(n.equals("play")){commands.add(n);ready=true;notifyPlaying();return null;}
      if(n.equals("pause")){commands.add(n);ready=false;notifyPlaying();return null;}
      if(n.equals("stop")||n.equals("release")){commands.add(n);ready=false;state=Player.STATE_IDLE;released=n.equals("release")||released;notifyPlaying();return null;}
      if(n.equals("setVolume")){volume=(Float)args[0];return null;}
      if(n.equals("setPlayWhenReady")){commands.add(n);ready=(Boolean)args[0];notifyPlaying();return null;}
      if(n.equals("prepare")||n.equals("setMediaItem"))commands.add(n);
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
    void notifyPlaying(){for(Player.Listener l:new ArrayList<>(listeners))l.onIsPlayingChanged(ready&&state==Player.STATE_READY&&!released);}
  }
  Video fullscreen(InfinityLiveActivity a,int w,int h)throws Exception{
    call(a,"cobraOpenLiveTv");ui.measure(a,w,h);
    Object channel=((List<?>)get(a,"mChannels")).get(0);Video v=new Video(a);put(a,"mPlayer",v.player);put(a,"mPlaying",channel);
    call(a,"openPlayerOverlay",channel);ui.measure(a,w,h);return v;
  }
  View text(View v,String value){if(v instanceof TextView&&value.contentEquals(((TextView)v).getText()))return v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){View r=text(((ViewGroup)v).getChildAt(i),value);if(r!=null)return r;}return null;}
  View clickable(View v){while(v!=null&&!v.isClickable())v=v.getParent() instanceof View?(View)v.getParent():null;return v;}
  void shot(InfinityLiveActivity a,String name)throws Exception{View d=a.getWindow().getDecorView();Bitmap b=Bitmap.createBitmap(d.getWidth(),d.getHeight(),Bitmap.Config.ARGB_8888);d.draw(new Canvas(b));File f=new File(System.getProperty("cobra.evidence"),name+".png");try(FileOutputStream o=new FileOutputStream(f)){b.compress(Bitmap.CompressFormat.PNG,100,o);}b.recycle();}

  @Test public void closingPipStopsAudioEvenBeforeAndroidClearsThePipFlag()throws Exception{
    InfinityLiveActivity a=activity();try{
      Video v=fullscreen(a,412,915);
      a.onPictureInPictureModeChanged(true,a.getResources().getConfiguration());call(a,"onPause");call(a,"onStop");
      assertFalse("Closing the PiP window must silence the existing player even if the mode flag is still true",v.ready);
      assertFalse("PiP dismissal must never start mini-player background playback",(Boolean)get(a,"mCobraMiniBackgroundActive"));
      assertTrue("Explicitly dismissed playback must not be queued to auto-resume",((Map<?,?>)get(a,"mBackgroundResumePlayers")).isEmpty());
      a.onPictureInPictureModeChanged(false,a.getResources().getConfiguration());call(a,"onResume");
      assertNull("Returning after PiP dismissal must not reopen fullscreen",get(a,"mPlayerOverlay"));assertFalse(v.ready);
    }finally{clean(a);}
  }
  @Test public void closingPipIsAlsoTerminalWhenModeCallbackComesBeforeOnStop()throws Exception{
    InfinityLiveActivity a=activity();try{
      Video v=fullscreen(a,412,915);a.onPictureInPictureModeChanged(true,a.getResources().getConfiguration());call(a,"onPause");
      a.onPictureInPictureModeChanged(false,a.getResources().getConfiguration());call(a,"onStop");call(a,"onResume");
      assertFalse("Dismissed video must not restart through the background resume map",v.ready);assertNull(get(a,"mPlayerOverlay"));
    }finally{clean(a);}
  }
  @Test public void explicitCobraSelectionReturnsToPreviewRatherThanForcingFullscreen()throws Exception{
    InfinityLiveActivity a=activity();try{
      Video v=fullscreen(a,412,915);Object texture=get(a,"mCobraPreviewTexture");
      call(a,"onNewIntent",new Intent(a,InfinityLiveActivity.class).putExtra("cobra_open_browse",true));call(a,"onResume");
      assertNull("Selecting Cobra should show browsing, not the previous fullscreen overlay",get(a,"mPlayerOverlay"));
      assertSame("Live reentry should retain the same session",v.player,get(a,"mCobraPreviewPlayer"));assertSame(texture,get(a,"mCobraPreviewTexture"));
      assertFalse(v.commands.contains("release"));assertFalse(v.commands.contains("prepare"));
    }finally{clean(a);}
  }
  @Test public void videoSubmenusStayBottomCenteredNotMiddleRight()throws Exception{
    RuntimeEnvironment.setQualifiers("w915dp-h412dp-land-mdpi");InfinityLiveActivity a=activity();try{
      fullscreen(a,915,412);View more=ui.description(a.getWindow().getDecorView(),"More");assertNotNull(more);more.performClick();ui.measure(a,915,412);
      View display=clickable(text((View)get(a,"mCobraActionSheet"),"Aspect / Display"));assertNotNull(display);display.performClick();ui.measure(a,915,412);
      FrameLayout scrim=(FrameLayout)get(a,"mCobraActionSheet");View panel=scrim.getChildAt(0);shot(a,"display-menu-landscape");
      assertEquals("Display submenu must be centered horizontally like More",scrim.getWidth()/2f,(panel.getLeft()+panel.getRight())/2f,1f);
      assertTrue("Video submenu must remain at the bottom safe edge",scrim.getHeight()-panel.getBottom()<=24);
    }finally{clean(a);}
  }
}
