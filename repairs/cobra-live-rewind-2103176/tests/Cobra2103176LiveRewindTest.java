package com.projectinfinity.kodi;

import android.app.Application;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103176LiveRewindTest {
  @Test public void providerArchiveFlagsAreStrict(){
    assertTrue(InfinityLiveActivity.CobraLiveRewindPolicy.archiveFlag("1"));
    assertTrue(InfinityLiveActivity.CobraLiveRewindPolicy.archiveFlag("true"));
    assertFalse(InfinityLiveActivity.CobraLiveRewindPolicy.archiveFlag("0"));
    assertFalse(InfinityLiveActivity.CobraLiveRewindPolicy.archiveFlag(""));
  }

  @Test public void archiveDaysAreBounded(){
    assertEquals(0,InfinityLiveActivity.CobraLiveRewindPolicy.archiveDays(-2));
    assertEquals(7,InfinityLiveActivity.CobraLiveRewindPolicy.archiveDays(7));
    assertEquals(365,InfinityLiveActivity.CobraLiveRewindPolicy.archiveDays(900));
  }

  @Test public void archiveWindowRejectsExpiredPrograms(){
    long now=10L*86400000L;
    assertTrue(InfinityLiveActivity.CobraLiveRewindPolicy.withinArchive(now,now-2L*86400000L,3));
    assertFalse(InfinityLiveActivity.CobraLiveRewindPolicy.withinArchive(now,now-4L*86400000L,3));
    assertFalse(InfinityLiveActivity.CobraLiveRewindPolicy.withinArchive(now,now+1000L,3));
  }

  @Test public void rewindNeverCrossesProgramStart(){
    long now=1_000_000L,start=950_000L;
    assertEquals(970_000L,InfinityLiveActivity.CobraLiveRewindPolicy.rewindTarget(now,start,30_000L));
    assertEquals(start,InfinityLiveActivity.CobraLiveRewindPolicy.rewindTarget(now,start,90_000L));
  }

  @Test public void catchupDurationIsMinuteBounded(){
    assertEquals(1,InfinityLiveActivity.CobraLiveRewindPolicy.durationMinutes(1000L,1000L));
    assertEquals(2,InfinityLiveActivity.CobraLiveRewindPolicy.durationMinutes(0L,61_000L));
    assertEquals(1440,InfinityLiveActivity.CobraLiveRewindPolicy.durationMinutes(0L,3L*86400000L));
  }
}
