package com.projectinfinity.kodi;

import android.app.Application;
import androidx.media3.exoplayer.DefaultLoadControl;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103174BufferRegressionTest {
  @Test public void media3DefaultStreamingBufferMatchesRestoredSingleViewContract(){
    assertEquals(50000,DefaultLoadControl.DEFAULT_MIN_BUFFER_MS);
    assertEquals(50000,DefaultLoadControl.DEFAULT_MAX_BUFFER_MS);
    assertTrue(InfinityLiveActivity.CobraBufferRegressionProfile.singleUsesMedia3Defaults());
  }

  @Test public void multiViewKeepsBoundedProfile(){
    assertEquals(6000,InfinityLiveActivity.CobraBufferRegressionProfile.multiMinMs());
    assertEquals(30000,InfinityLiveActivity.CobraBufferRegressionProfile.multiMaxMs());
    assertEquals(1500,InfinityLiveActivity.CobraBufferRegressionProfile.multiStartMs());
    assertEquals(3000,InfinityLiveActivity.CobraBufferRegressionProfile.multiRebufferMs());
    assertEquals(12*1024*1024,InfinityLiveActivity.CobraBufferRegressionProfile.multiTargetBytes());
  }

  @Test public void stallThresholdIsObservationOnlyBoundary(){
    assertEquals(12000L,InfinityLiveActivity.CobraBufferRegressionProfile.stallObservationMs());
  }
}
