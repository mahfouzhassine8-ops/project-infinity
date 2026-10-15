package com.projectinfinity.kodi;

import android.app.Activity;
import android.view.View;
import android.widget.TextView;
import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@LooperMode(LooperMode.Mode.PAUSED)
public class MobileRepairTest {
  @Test public void eightMinuteChooserWaitDoesNotBecomeSlowKodiStartup() {
    InfinityStartupTiming t=new InfinityStartupTiming(1000);
    t.observe("chooser.firstFrame",1050);
    t.observe("handoff.requested",481000);
    assertEquals(479950,t.chooserMillis(481068));
    assertEquals(68,t.handoffMillis(481068));
    assertFalse(t.slow("main.afterSuper",481068));
  }
  @Test public void chooserRedrawAfterSettingsIsNotAnotherStartup() {
    InfinityStartupTiming t=new InfinityStartupTiming(1000);
    t.observe("chooser.firstFrame",1050);
    t.observe("chooser.firstFrame",481000);
    assertFalse(t.slow("chooser.firstFrame",481000));
    assertEquals(-1,t.handoffMillis(481000));
  }
  @Test public void actualSlowPreparationAfterSelectionRemainsVisible() {
    InfinityStartupTiming t=new InfinityStartupTiming(1000);
    t.observe("handoff.requested",481000);
    assertFalse(t.slow("main.afterSuper",485999));
    assertTrue(t.slow("main.afterSuper",486000));
  }
  @Test public void closingOwnerClearsTimingUntilUserSelectsAgain() {
    InfinityStartupTiming t=new InfinityStartupTiming(1000);
    t.observe("handoff.requested",2000);
    t.observe("handoff.waitClosingOwner",2010);
    assertEquals(-1,t.handoffMillis(600000));
    assertFalse(t.slow("main.afterSuper",600000));
    t.observe("handoff.requested",700000);
    assertEquals(40,t.handoffMillis(700040));
  }
  @Test public void repeatedTapDoesNotResetRealStartupClock() {
    InfinityStartupTiming t=new InfinityStartupTiming(1000);
    t.observe("handoff.requested",2000);
    t.observe("handoff.requested",6500);
    assertTrue(t.slow("main.afterSuper",7000));
  }
  @Test public void slowInitialFirstFrameStillRecorded() {
    InfinityStartupTiming t=new InfinityStartupTiming(1000);
    t.observe("chooser.firstFrame",6100);
    assertTrue(t.slow("chooser.firstFrame",6100));
    assertFalse(t.slow("main.afterSuper",6100));
  }
  @Test public void nativeTraceBytesSurviveIncludingInvalidUtf8() throws Exception {
    byte[] original=new byte[65539];new Random(20261003).nextBytes(original);
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    assertFalse(InfinityHealthExport.copyBounded(new ByteArrayInputStream(original),out,InfinityHealthExport.TRACE_LIMIT));
    assertArrayEquals(original,out.toByteArray());
  }
  @Test public void traceTruncationIsExplicitAndExact() throws Exception {
    byte[] original=new byte[InfinityHealthExport.TRACE_LIMIT+1];Arrays.fill(original,(byte)0xff);
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    assertTrue(InfinityHealthExport.copyBounded(new ByteArrayInputStream(original),out,InfinityHealthExport.TRACE_LIMIT));
    assertEquals(InfinityHealthExport.TRACE_LIMIT,out.size());
    assertArrayEquals(Arrays.copyOf(original,InfinityHealthExport.TRACE_LIMIT),out.toByteArray());
  }
  @Test public void exactlyLimitSizedTraceIsNotFlaggedTruncated() throws Exception {
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    assertFalse(InfinityHealthExport.copyBounded(new ByteArrayInputStream(new byte[8192]),out,8192));
    assertEquals(8192,out.size());
  }
  @Test public void emptyTraceAndZeroLengthReadCannotSpinForever() throws Exception {
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    assertFalse(InfinityHealthExport.copyBounded(new ByteArrayInputStream(new byte[0]),out,8192));
    InputStream unusual=new ByteArrayInputStream(new byte[]{(byte)0xf5,0,1}) {
      public synchronized int read(byte[] b,int offset,int count){return 0;}
    };
    assertFalse(InfinityHealthExport.copyBounded(unusual,out,8192));
    assertArrayEquals(new byte[]{(byte)0xf5,0,1},out.toByteArray());
  }
  @Test public void zipRemainsUsableWhenAndroidHasNoTrace() throws Exception {
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    InfinityHealthExport.write(RuntimeEnvironment.getApplication(),out,"Fixture report\n");
    Map<String,String> entries=new HashMap<>();
    try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(out.toByteArray()))) {
      ZipEntry entry;while((entry=zip.getNextEntry())!=null) {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        InfinityHealthExport.copyBounded(zip,bytes,100000);
        entries.put(entry.getName(),bytes.toString("UTF-8"));
      }
    }
    assertEquals("Fixture report\n",entries.get("report.txt"));
    assertTrue(entries.get("exit-manifest.json").contains("producer") || entries.get("exit-manifest.json").contains("Historical exits"));
    assertEquals(2,entries.size());
  }
  @Test public void requestedCopyIsExactAcrossExistingChooserLayouts() {
    for(String mode:new String[]{"light","dark","oled"}) {
      org.robolectric.android.controller.ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();
      InfinityGlassChooser ui=new InfinityGlassChooser(c.get(),new CosmicChooserTest.Calls(mode));
      c.get().setContentView(ui);
      for(int[] size:CosmicChooserTest.SIZES) {
        CosmicChooserTest.layout(ui,size[0],size[1]);
        for(String tag:new String[]{"hm-copy","infinity-tagline","cobra-tagline"}) {
          TextView v=ui.findViewWithTag(tag);assertNotNull(v);
          assertEquals(View.GONE,v.getVisibility());assertEquals("",v.getText().toString());
        }
        assertEquals("TWO UNIVERSES.",ui.stage.subtitle.getText().toString());
      }
      CosmicChooserTest.cleanup(c);
    }
  }
}
