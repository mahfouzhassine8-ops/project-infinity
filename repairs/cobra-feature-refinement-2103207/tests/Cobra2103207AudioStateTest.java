package com.projectinfinity.kodi;
import org.junit.*;
import static org.junit.Assert.*;

/** Pure mute intent transitions, independent of Android focus and routing. */
public class Cobra2103207AudioStateTest {
  InfinityLiveActivity.CobraMediaAudioState s;
  @Before public void before(){s=new InfinityLiveActivity.CobraMediaAudioState();}
  @Test public void initiallyAudibleRestoresAfterCall(){s.observe(true);s.observe(false);assertFalse(s.userMuted);}
  @Test public void initiallyMutedRestoresAfterExplicitCallUnmute(){s.mute();s.observe(true);s.unmute();s.observe(false);assertTrue(s.userMuted);}
  @Test public void explicitMuteDuringCallIsPreserved(){s.observe(true);s.unmute();s.mute();s.observe(false);assertTrue(s.userMuted);}
  @Test public void latestUnmuteDuringCallReplacesEarlierCallMute(){s.observe(true);s.mute();s.unmute();s.observe(false);assertFalse(s.userMuted);}
  @Test public void repeatedCallObservationsDoNotOverwritePriorIntent(){s.mute();s.observe(true);s.unmute();s.observe(true);s.observe(true);s.observe(false);assertTrue(s.userMuted);}
  @Test public void callEndRevokesPendingAudioRenewal(){s.observe(true);s.renewAudio=true;s.observe(false);assertFalse(s.renewAudio);}
  @Test public void explicitMuteRevokesPendingAudioRenewal(){s.observe(true);s.renewAudio=true;s.mute();assertFalse(s.renewAudio);}
  @Test public void repeatedCyclesDoNotLeakIntent(){for(int i=0;i<20;i++){s.observe(true);s.unmute();s.observe(false);assertFalse(s.userMuted);}}
}
