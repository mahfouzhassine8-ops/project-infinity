package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103185LiveDiagnosticsFreezeTest {
  @Test public void activeEvidenceIncludesEitherPlayerOrTimeshift(){
    assertFalse(InfinityLiveActivity.CobraDiagnosticFreezePolicy.hasActiveEvidence(0,false));
    assertTrue(InfinityLiveActivity.CobraDiagnosticFreezePolicy.hasActiveEvidence(1,false));
    assertTrue(InfinityLiveActivity.CobraDiagnosticFreezePolicy.hasActiveEvidence(0,true));
  }

  @Test public void frozenSnapshotIsUsedOnlyWhenCurrentPlaybackIsInactive(){
    long now=1_000_000L;
    assertTrue(InfinityLiveActivity.CobraDiagnosticFreezePolicy.useFrozen(false,"{}",now-1000L,now));
    assertFalse(InfinityLiveActivity.CobraDiagnosticFreezePolicy.useFrozen(true,"{}",now-1000L,now));
  }

  @Test public void staleFrozenSnapshotExpires(){
    long now=2_000_000L;
    long max=InfinityLiveActivity.CobraDiagnosticFreezePolicy.MAX_FROZEN_AGE_MS;
    assertTrue(InfinityLiveActivity.CobraDiagnosticFreezePolicy.useFrozen(false,"{}",now-max,now));
    assertFalse(InfinityLiveActivity.CobraDiagnosticFreezePolicy.useFrozen(false,"{}",now-max-1L,now));
  }

  @Test public void missingFrozenSnapshotNeverSubstitutes(){
    assertFalse(InfinityLiveActivity.CobraDiagnosticFreezePolicy.useFrozen(false,null,10L,20L));
    assertFalse(InfinityLiveActivity.CobraDiagnosticFreezePolicy.useFrozen(false,"",10L,20L));
    assertFalse(InfinityLiveActivity.CobraDiagnosticFreezePolicy.useFrozen(false,"{}",0L,20L));
  }

  @Test public void tenMinuteRetentionWindowIsExplicit(){
    assertEquals(600000L,InfinityLiveActivity.CobraDiagnosticFreezePolicy.MAX_FROZEN_AGE_MS);
  }
}
