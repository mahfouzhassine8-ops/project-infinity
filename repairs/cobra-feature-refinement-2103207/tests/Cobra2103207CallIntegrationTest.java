package com.projectinfinity.kodi;
import android.app.Application;
import android.media.AudioManager;
import android.view.TextureView;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103207CallIntegrationTest {
  Cobra2103206MediaCallsTest f;
  Cobra2103202LifecycleTest.State s;
  int transport,audioRenewals;long position=42000L;
  @Before public void before()throws Exception{
    f=new Cobra2103206MediaCallsTest();f.before();f.manual();
    s=f.f.new State(){
      @Override public Object invoke(Object p,java.lang.reflect.Method m,Object[] v){
        String n=m.getName();if(n.equals("getCurrentPosition")||n.equals("getContentPosition"))return position;
        if(n.equals("setAudioSessionId"))audioRenewals++;
        if(n.startsWith("seek")||n.equals("play")||n.equals("pause")||n.equals("setPlayWhenReady")||n.equals("stop")||n.equals("prepare")||n.startsWith("setMedia")||n.equals("release"))transport++;
        return super.invoke(p,m,v);
      }
    };
    f.f.states.add(s);f.put(f.a,"mPlayer",s.player);f.put(f.a,"mPlaying",f.f.channels.get(0));f.call("openPlayerOverlay",f.f.channels.get(0));f.f.bind(s,f.f.channels.get(0),(TextureView)f.get(f.a,"mPlayerTexture"));f.put(f.a,"mCobraTimeshiftPlayer",s.player);f.call("cobraUserPlay",s.player);transport=0;
  }
  @After public void after()throws Exception{if(f!=null)f.after();}
  @Test public void unmuteAndCallEndNeverIssueTransportCommands()throws Exception{
    f.interrupt();f.call("cobraUserUnmute",s.player);f.mode(AudioManager.MODE_NORMAL);f.listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);
    assertEquals(0,transport);assertEquals(42000L,s.player.getCurrentPosition());assertTrue(s.requested);assertSame(s.player,f.get(f.a,"mCobraTimeshiftPlayer"));assertEquals(1f,s.volume,0f);
  }
  @Test public void mutedBeforeCallIsMutedAgainAfterCall()throws Exception{
    f.call("cobraToggleMediaMute",s.player);assertEquals(0f,s.volume,0f);f.interrupt();f.call("cobraUserUnmute",s.player);assertEquals(1f,s.volume,0f);f.mode(AudioManager.MODE_NORMAL);assertEquals(0f,s.volume,0f);assertEquals(0,transport);
  }
  @Test public void fullPlayerSpeakerRowFollowsCallMuteAndResumesAudioOnly()throws Exception{
    f.call("showTrackChooser");f.interrupt();assertNotNull(f.row("cobra-track-media-mute"));f.row("cobra-track-media-mute").performClick();assertEquals(1f,s.volume,0f);assertEquals(0,transport);assertTrue(s.requested);
  }
  @Test public void explicitMuteDuringCallSurvivesFocusGainAndCallEnd()throws Exception{
    f.interrupt();f.call("cobraUserUnmute",s.player);f.call("cobraToggleMediaMute",s.player);f.listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);f.mode(AudioManager.MODE_NORMAL);assertEquals(0f,s.volume,0f);assertEquals(0,transport);
  }
  @Test public void existingMultiAudioActionUnmutesOnlySelectedPaneDuringCall()throws Exception{
    f.call("releaseSinglePlayer");f.f.states.clear();f.f.multi(3);f.interrupt();
    String key=(String)f.get(f.f.channels.get(1),"id");f.call("cobraUseMultiAudioHere",key);
    assertEquals(0f,f.f.states.get(0).volume,0f);assertEquals(1f,f.f.states.get(1).volume,0f);assertEquals(0f,f.f.states.get(2).volume,0f);
    for(Cobra2103202LifecycleTest.State tile:f.f.states){assertEquals(0,tile.prepares);assertEquals(0,tile.releases);assertTrue(tile.requested);}
  }
}
