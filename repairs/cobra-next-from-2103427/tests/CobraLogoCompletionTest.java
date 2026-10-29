package com.projectinfinity.kodi;
import android.app.Application;
import android.graphics.Bitmap;
import android.widget.ImageView;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.annotation.*;
/** Real unchanged downloader over loopback PNG, existing executor wrappers,
 * actual publish/finish ordering. Host only; no external feed/physical claim. */
@RunWith(org.robolectric.RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraLogoCompletionTest {
 @Test public void originalDownloaderCompletesCoalescedAndDeferredRequestsWithoutRetryLoop()throws Exception{
  byte[] png=Base64.getDecoder().decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jHHsAAAAASUVORK5CYII=");
  AtomicInteger requests=new AtomicInteger();HttpServer server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
  server.createContext("/",e->{requests.incrementAndGet();boolean fail=e.getRequestURI().getPath().contains("fail");e.sendResponseHeaders(fail?500:200,fail?-1:png.length);if(!fail)e.getResponseBody().write(png);e.close();});server.start();
  try{
   CobraLogoWorkTest.Fixture f=new CobraLogoWorkTest.Fixture();String base="http://127.0.0.1:"+server.getAddress().getPort();
   ArrayList<ImageView> views=new ArrayList<>();
   for(int i=0;i<9;i++){ImageView view=f.view();views.add(view);f.request(base+"/logo"+i+".png",view);}
   ImageView duplicate=f.view();f.request(base+"/logo0.png",duplicate);f.idle();assertEquals(4,f.io.jobs.size());
   int done=0;
   while(done<f.io.jobs.size()){
    Thread worker=new Thread(f.io.jobs.get(done++));worker.start();worker.join(5000);assertFalse("loopback worker must finish",worker.isAlive());f.idle();
    assertTrue("at most4 admitted unfinished jobs",f.io.jobs.size()-done<=4);
   }
   assertEquals(9,done);assertEquals(9,requests.get());for(ImageView view:views)assertNotNull(CobraLogoWorkTest.bitmap(view));assertSame(CobraLogoWorkTest.bitmap(views.get(0)),CobraLogoWorkTest.bitmap(duplicate));
   ImageView failed=f.view();f.request(base+"/fail.png",failed);f.idle();assertEquals(10,f.io.jobs.size());
   Thread worker=new Thread(f.io.jobs.get(9));worker.start();worker.join(5000);assertFalse(worker.isAlive());f.idle();f.idle();
   assertEquals("no automatic failure retry",10,requests.get());assertEquals(10,f.io.jobs.size());assertNull(CobraLogoWorkTest.bitmap(failed));
   ImageView detached=new ImageView(f.a);f.request(base+"/attach.png",detached);f.idle();assertEquals(10,f.io.jobs.size());
   f.root.addView(detached);f.idle();assertEquals(11,f.io.jobs.size());
  }finally{server.stop(0);}
 }
}
