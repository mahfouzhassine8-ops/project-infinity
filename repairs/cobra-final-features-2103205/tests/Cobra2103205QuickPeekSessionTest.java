package com.projectinfinity.kodi;

import android.app.Application;
import android.os.Looper;
import android.view.TextureView;
import androidx.media3.common.*;
import androidx.media3.datasource.DefaultDataSource;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory;
import java.lang.reflect.Field;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real Media3 session construction/release with a missing local file and controlled callbacks.
 * No network, decoded video, physical device or simultaneous-decoder capacity claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205QuickPeekSessionTest {
  CobraQuickPeekSession session;ArrayList<String> updates;int cleanups;
  static Object get(Object object,String name)throws Exception{Field field=object.getClass().getDeclaredField(name);field.setAccessible(true);return field.get(object);}
  CobraQuickPeekSession create(){
    Application app=RuntimeEnvironment.getApplication();updates=new ArrayList<>();
    return new CobraQuickPeekSession(app,new TextureView(app),new DefaultMediaSourceFactory(new DefaultDataSource.Factory(app)),MediaItem.fromUri("file:///does-not-exist-cobra205-peek.ts"),(state,w,h,codec)->updates.add(state),()->cleanups++);
  }
  @Before public void before(){session=create();}
  @After public void after(){if(session!=null)session.close();}
  Player.Listener events()throws Exception{return (Player.Listener)get(session,"events");}
  @Test public void previewOwnsMutedVideoOnlyTracksWithoutAudioOrCaptions()throws Exception{
    ExoPlayer player=(ExoPlayer)get(session,"player");assertNotNull(player);assertEquals(0f,player.getVolume(),0f);assertTrue(player.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_AUDIO));assertTrue(player.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertEquals(1,player.getMediaItemCount());
  }
  @Test public void readyWithoutRenderedFrameDoesNotClaimVisibleVideo()throws Exception{events().onPlaybackStateChanged(Player.STATE_READY);assertEquals("Connecting preview…",updates.get(updates.size()-1));events().onRenderedFirstFrame();assertEquals("Live preview · muted",updates.get(updates.size()-1));}
  @Test public void closeIsIdempotentAndReleasesPlayerTextureAndDedicatedTransport()throws Exception{session.close();session.close();assertTrue(session.closed());assertNull(get(session,"player"));assertNull(get(session,"texture"));assertNull(get(session,"listener"));assertEquals(1,cleanups);}
  @Test public void callbacksCapturedBeforeDismissAreIgnoredAfterRelease()throws Exception{Player.Listener old=events();session.close();int count=updates.size();old.onRenderedFirstFrame();old.onPlaybackStateChanged(Player.STATE_READY);old.onVideoSizeChanged(new VideoSize(1920,1080));old.onPlayerError(new PlaybackException("controlled",null,PlaybackException.ERROR_CODE_IO_UNSPECIFIED));assertEquals(count,updates.size());assertEquals(1,cleanups);}
  @Test public void playerErrorClosesOnlyThisDisposableSessionAndReportsUnavailable()throws Exception{events().onPlayerError(new PlaybackException("controlled",null,PlaybackException.ERROR_CODE_IO_UNSPECIFIED));assertTrue(session.closed());assertEquals("Preview unavailable",updates.get(updates.size()-1));assertEquals(1,cleanups);}
  @Test public void queuedTimeoutCannotReopenOrUpdateClosedSession(){session.close();int count=updates.size();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(20));assertEquals(count,updates.size());assertEquals(1,cleanups);}
  @Test public void startupTimeoutReleasesUnavailablePreviewWithoutRetry()throws Exception{((Runnable)get(session,"startupTimeout")).run();assertTrue(session.closed());assertNull(get(session,"player"));assertEquals("Preview unavailable",updates.get(updates.size()-1));assertEquals(1,cleanups);}
  @Test public void firstFrameMakesStaleStartupTimeoutHarmless()throws Exception{events().onRenderedFirstFrame();((Runnable)get(session,"startupTimeout")).run();assertFalse(session.closed());assertEquals(0,cleanups);}
}
