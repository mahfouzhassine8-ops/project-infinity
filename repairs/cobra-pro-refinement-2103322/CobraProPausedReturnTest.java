package com.projectinfinity.kodi;

import java.util.ArrayList;
import java.util.List;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.LooperMode;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Production mode handoff with a controlled player; no real-decoder claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35, application=android.app.Application.class, manifest=Config.NONE,
        qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraProPausedReturnTest {
  CobraProHandoffTest h;
  @Before public void setup() throws Exception { h=new CobraProHandoffTest(); h.setup(); }
  @After public void cleanup() throws Exception { h.cleanup(); }

  private void pausedReturn(String owner, boolean muted) throws Exception {
    h.pro(); h.activeMini(2); Object main=h.channel(2);
    if ("sports".equals(owner)) {
      Object game=h.addLiveGameForChannel(0);
      call(h.a,"cobraProFilter",4); h.freshPlayer(); h.sportsMini(0,game);
    } else if ("preview".equals(owner)) {
      call(h.a,"cobraProStep",1); Object channel=get(h.a,"mGuidePreviewChannel");
      h.freshPlayer(); put(h.a,"mCobraPreviewPlayer",h.player);
      put(h.a,"mCobraPreviewSessionKey",call(h.a,"cobraChannelKey",channel));
      call(h.a,"cobraProPreview"); call(h.a,"cobraProUnmute");
    }
    if(muted) call(h.a,"cobraProMuteSession",h.player);
    h.state.playing=false; h.state.position=63000L;
    Object channel=get(h.a,"mGuidePreviewChannel");
    int prepares=h.state.prepares, changes=h.state.changes;

    call(h.a,"cobraExitProMode");
    call(h.a,"cobraEnterProMode",new ArrayList((List)get(h.a,"mChannels")));

    assertSame("Mode return must keep the paused session",h.player,get(h.a,"mCobraPreviewPlayer"));
    assertFalse("Mode return must not release the decoder",h.state.released);
    assertFalse("Mode return must not resume playback",h.state.playing);
    assertEquals(63000L,h.state.position);
    assertEquals(muted?0f:1f,h.state.volume,0f);
    assertEquals(muted,get(h.a,"mCobraPreviewMuted"));
    assertEquals(CobraProUi.WATCHING,get(h.a,"mCobraProState"));
    assertSame(main,get(h.a,"mCobraProMainChannel"));
    assertSame(channel,get(h.a,"mGuidePreviewChannel"));
    assertEquals("sports".equals(owner),call(h.a,"cobraProSportsHeroActive"));
    assertEquals(!"preview".equals(owner),get(h.a,"mCobraProPlaybackOwned"));
    if("preview".equals(owner)) assertFalse((Boolean)get(call(h.a,"cobraProCurrentSlot"),"main"));
    assertEquals(prepares,h.state.prepares); assertEquals(changes,h.state.changes);

    // Restoring a paused session must not weaken the universal pane-leave rule.
    call(h.a,"cobraProStep",1);
    assertTrue(h.state.released); assertNull(get(h.a,"mCobraPreviewPlayer"));
    assertEquals(CobraProUi.RESTING,get(h.a,"mCobraProState"));
  }

  @Test public void pausedMainMutedSurvivesModeReturn() throws Exception { pausedReturn("main",true); }
  @Test public void pausedMainUnmutedSurvivesModeReturn() throws Exception { pausedReturn("main",false); }
  @Test public void pausedSportsMutedSurvivesModeReturn() throws Exception { pausedReturn("sports",true); }
  @Test public void pausedSportsUnmutedSurvivesModeReturn() throws Exception { pausedReturn("sports",false); }
  @Test public void pausedPreviewMutedSurvivesModeReturn() throws Exception { pausedReturn("preview",true); }
  @Test public void pausedPreviewUnmutedSurvivesModeReturn() throws Exception { pausedReturn("preview",false); }

  @Test public void stoppedPaneDoesNotAcquirePlaybackOnModeReturn() throws Exception {
    h.pro(); h.activeMini(2); call(h.a,"cobraProStep",1);
    assertNull(get(h.a,"mCobraPreviewPlayer"));
    call(h.a,"cobraExitProMode");
    call(h.a,"cobraEnterProMode",new ArrayList((List)get(h.a,"mChannels")));
    assertNull(get(h.a,"mCobraPreviewPlayer"));
    assertFalse((Boolean)get(h.a,"mCobraProPlaybackOwned"));
    assertEquals(CobraProUi.RESTING,get(h.a,"mCobraProState"));
  }

  @Test public void rejectedSportsLookupReportsFailureAndKeepsCurrentSession() throws Exception {
    h.pro(); h.activeMini(2); Object main=h.channel(2);
    Object game=h.addLiveGameForChannel(0);
    ((java.util.concurrent.ExecutorService)get(h.a,"mIo")).shutdownNow();
    call(h.a,"cobraSportsWatch",game);
    assertEquals("Broadcast lookup unavailable. Reopen Sports and try again.",
        org.robolectric.shadows.ShadowToast.getTextOfLatestToast());
    assertSame(h.player,get(h.a,"mCobraPreviewPlayer"));
    assertSame(main,get(h.a,"mGuidePreviewChannel"));
    assertSame(main,get(h.a,"mCobraProMainChannel"));
    assertTrue(h.state.playing); assertFalse(h.state.released);
    assertEquals(0,h.state.prepares); assertEquals(0,h.state.changes);
    assertNull(get(h.a,"mPlayerOverlay")); assertNull(get(h.a,"mMultiOverlay"));
  }
}
