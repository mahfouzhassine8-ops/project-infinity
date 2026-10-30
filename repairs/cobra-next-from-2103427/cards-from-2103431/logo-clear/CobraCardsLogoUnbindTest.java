package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Bitmap;
import android.graphics.drawable.ColorDrawable;
import android.widget.ImageView;
import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.util.Map;
import org.junit.Test;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.annotation.*;

/** Actual accepted coordinator plus only the add-only Cards unbind method.
 * Controlled completions exercise stale publications without external HTTP. */
@RunWith(org.robolectric.RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraCardsLogoUnbindTest {
  static final String A="https://example.invalid/cards-a.png", B="https://example.invalid/cards-b.png";
  static Object service(CobraLogoWorkTest.Fixture f)throws Exception {
    Field field=CobraLogoRequests.class.getDeclaredField("OWNERS");field.setAccessible(true);
    WeakReference<?> reference=(WeakReference<?>)((Map<?,?>)field.get(null)).get(f.a);
    return reference==null?null:reference.get();
  }
  static Map<?,?> map(Object owner,String name)throws Exception {return (Map<?,?>)CobraLogoWorkTest.get(owner,name);}
  @Test public void clearWithoutOwnerCreatesNoServiceOrWork()throws Exception {
    CobraLogoWorkTest.Fixture f=new CobraLogoWorkTest.Fixture();ImageView v=f.view();
    v.setImageDrawable(new ColorDrawable(0xff00ff00));assertNull(service(f));
    CobraLogoRequests.clear(f.a,v);CobraLogoRequests.clear(f.a,null);f.idle();
    assertNull(v.getDrawable());assertNull(service(f));assertEquals(0,f.io.jobs.size());
  }
  @Test public void clearedBlankViewRejectsOldCompletionAndDoesNotRequeueOnAttach()throws Exception {
    CobraLogoWorkTest.Fixture f=new CobraLogoWorkTest.Fixture();ImageView v=f.view();f.request(A,v);f.idle();
    assertEquals(1,f.io.jobs.size());Object owner=service(f);Object binding=map(owner,"bindings").get(v);assertNotNull(binding);
    CobraLogoRequests.clear(f.a,v);assertFalse(map(owner,"waiting").containsKey(v));assertFalse(map(owner,"bindings").containsKey(v));
    assertEquals("",CobraLogoWorkTest.get(binding,"url"));
    f.root.removeView(v);f.root.addView(v);f.idle();
    assertFalse(map(owner,"bindings").containsKey(v));assertFalse(map(owner,"waiting").containsKey(v));
    Bitmap old=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);f.deliver(A,old,v);f.idle();
    assertNull(v.getDrawable());assertEquals(1,f.io.jobs.size());
  }
  @Test public void clearThenRebindPublishesOnlyTheCurrentLogo()throws Exception {
    CobraLogoWorkTest.Fixture f=new CobraLogoWorkTest.Fixture();ImageView v=f.view();f.request(A,v);f.idle();
    CobraLogoRequests.clear(f.a,v);f.request(B,v);f.idle();assertEquals(2,f.io.jobs.size());
    Bitmap old=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888),current=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);
    f.deliver(A,old,v);f.idle();assertNull(v.getDrawable());
    f.deliver(B,current,v);f.idle();assertSame(current,CobraLogoWorkTest.bitmap(v));
    f.root.removeView(v);f.root.addView(v);f.idle();assertSame(current,CobraLogoWorkTest.bitmap(v));assertEquals(2,f.io.jobs.size());
  }
  @Test public void clearingOneViewPreservesSharedFlightAndOtherWaiter()throws Exception {
    CobraLogoWorkTest.Fixture f=new CobraLogoWorkTest.Fixture();ImageView cleared=f.view(),retained=f.view();
    f.request(A,cleared);f.request(A,retained);f.idle();assertEquals(1,f.io.jobs.size());
    Object owner=service(f),flight=map(owner,"active").get(A);assertNotNull(flight);
    CobraLogoRequests.clear(f.a,cleared);assertSame(flight,map(owner,"active").get(A));assertTrue(map(owner,"waiting").containsKey(retained));
    Bitmap image=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);f.deliver(A,image,cleared);f.idle();
    assertNull(cleared.getDrawable());assertSame(image,CobraLogoWorkTest.bitmap(retained));assertEquals(1,f.io.jobs.size());
  }
}
