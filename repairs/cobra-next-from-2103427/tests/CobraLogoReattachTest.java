package com.projectinfinity.kodi;
import android.app.Application;
import android.graphics.Bitmap;
import android.widget.ImageView;
import org.junit.Test;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.annotation.*;
@RunWith(org.robolectric.RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraLogoReattachTest {
 @Test public void pendingOriginalCompletionStillReachesSameReattachedView()throws Exception{
  CobraLogoWorkTest.Fixture f=new CobraLogoWorkTest.Fixture();ImageView v=f.view();String url="https://example.invalid/retained.png";
  f.request(url,v);f.idle();assertEquals(1,f.io.jobs.size());
  f.root.removeView(v);assertFalse(v.isAttachedToWindow());f.root.addView(v);assertTrue(v.isAttachedToWindow());f.idle();
  Bitmap bitmap=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);f.deliver(url,bitmap,v);f.idle();
  assertSame("Original same-view completion must survive temporary reparent",bitmap,CobraLogoWorkTest.bitmap(v));
 }
}
