package com.projectinfinity.kodi;
import android.app.Application;
import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class) @Config(sdk=34,application=Application.class,manifest=Config.NONE)
public class Cobra2103194FoldAdaptiveAspectTest {
 @Test public void foldAdaptiveIsDedicatedMode(){assertEquals(12,InfinityLiveActivity.CobraFoldAspectPolicy.MODE);}
 @Test public void innerLikeViewportPreservesSourceWithoutWildStretch(){float[] s=InfinityLiveActivity.CobraFoldAspectPolicy.scale(1920,1080,1f,1812,2176);assertTrue(s[0]>0f&&s[0]<=1.06f);assertTrue(s[1]>0f&&s[1]<=1.06f);}
 @Test public void coverLikeViewportFitsEntireFrame(){float[] s=InfinityLiveActivity.CobraFoldAspectPolicy.scale(1920,1080,1f,904,2316);assertTrue(s[0]<1f);assertEquals(1f,s[1],.001f);}
 @Test public void landscapeNearMatchUsesOnlyTinyCrop(){float[] s=InfinityLiveActivity.CobraFoldAspectPolicy.scale(1920,1080,1f,2176,1812);assertTrue(s[0]<=1.06f&&s[1]<=1.06f);}
 @Test public void invalidGeometryIsSafe(){assertArrayEquals(new float[]{1f,1f},InfinityLiveActivity.CobraFoldAspectPolicy.scale(0,1080,1f,1000,1000),.001f);}
 @Test public void lockedPlaybackGuardRemains(){assertFalse(InfinityLiveActivity.CobraTimelineNormalizerPolicy.REWRITE_ENABLED);assertTrue(InfinityLiveActivity.CobraProviderPacePolicy.limited(30000L,900L,180L,560L,560L,560L,10L,500L,0L,0L,0L));}
}
