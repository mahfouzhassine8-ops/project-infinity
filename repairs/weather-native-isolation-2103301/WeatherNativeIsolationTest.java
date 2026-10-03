package com.projectinfinity.kodi;
import android.content.Context;
import android.widget.TextView;
import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import com.sun.net.httpserver.HttpServer;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(sdk=35) @LooperMode(LooperMode.Mode.PAUSED)
public class WeatherNativeIsolationTest {
  private Context app;
  private HttpServer server;
  private ExecutorService executor;
  private final AtomicInteger calls=new AtomicInteger();
  private final AtomicReference<String> body=new AtomicReference<>(),auth=new AtomicReference<>();
  private static final String REAL="{\"result\":{\"Weather.Location\":\"Configured city\",\"Weather.Temperature\":\"15°C\",\"Weather.Conditions\":\"Cloudy\"}}";
  @Before public void setup() throws Exception {
    app=RuntimeEnvironment.getApplication();Main.MainActivity=null;
    app.getSharedPreferences("infinity_chooser_weather",0).edit().clear().commit();
    server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
    executor=Executors.newCachedThreadPool();server.setExecutor(executor);
  }
  @After public void teardown(){server.stop(0);executor.shutdownNow();Main.MainActivity=null;}
  private InfinityChooserWeather.Settings settings(){
    InfinityChooserWeather.Settings s=new InfinityChooserWeather.Settings();s.enabled=true;s.port=server.getAddress().getPort();return s;
  }
  private void serve(int status,String payload){
    server.createContext("/jsonrpc",e->{
      calls.incrementAndGet();auth.set(e.getRequestHeaders().getFirst("Authorization"));
      body.set(new String(e.getRequestBody().readAllBytes(),StandardCharsets.UTF_8));
      if(status==302)e.getResponseHeaders().set("Location","http://127.0.0.1:"+server.getAddress().getPort()+"/forbidden");
      byte[] data=payload.getBytes(StandardCharsets.UTF_8);e.sendResponseHeaders(status,data.length);
      e.getResponseBody().write(data);e.close();
    });server.start();
  }
  @Test public void readOnlyLoopbackWorksWithoutLoadingKodiAndPreservesValidCache(){
    serve(200,REAL);InfinityChooserWeather.LocalReader reader=new InfinityChooserWeather.LocalReader(app);
    String result=reader.request(settings());assertEquals(REAL,result);
    assertEquals(InfinityChooserWeather.REQUEST,body.get());assertNull(auth.get());assertNull(Main.MainActivity);
    TextView label=new TextView(app);InfinityChooserWeather weather=new InfinityChooserWeather(app,label,reader);
    assertTrue(weather.accept(result));weather.renderCached();assertTrue(label.getText().toString().contains("last known"));
  }
  @Test public void configuredBasicAuthenticationIsUsedOnlyForLoopback(){
    serve(200,REAL);InfinityChooserWeather.Settings s=settings();s.authenticated=true;s.user="local-user";s.password="test-only";
    assertEquals(REAL,new InfinityChooserWeather.LocalReader(app).request(s));
    assertEquals("Basic "+java.util.Base64.getEncoder().encodeToString("local-user:test-only".getBytes(StandardCharsets.UTF_8)),auth.get());
  }
  @Test public void disabledOrHttpsOnlyServiceIsNotContacted(){
    serve(200,REAL);InfinityChooserWeather.LocalReader reader=new InfinityChooserWeather.LocalReader(app);
    InfinityChooserWeather.Settings s=settings();s.enabled=false;assertNull(reader.request(s));
    s.enabled=true;s.ssl=true;assertNull(reader.request(s));assertEquals(0,calls.get());
  }
  @Test public void redirectsAndOversizedResponsesCannotEscapeBoundary(){
    AtomicInteger redirected=new AtomicInteger();server.createContext("/forbidden",e->{redirected.incrementAndGet();e.close();});
    serve(302,"redirect");assertNull(new InfinityChooserWeather.LocalReader(app).request(settings()));assertEquals(0,redirected.get());
    server.removeContext("/jsonrpc");server.createContext("/jsonrpc",e->{byte[] data=new byte[17000];e.sendResponseHeaders(200,data.length);e.getResponseBody().write(data);e.close();});
    assertNull(new InfinityChooserWeather.LocalReader(app).request(settings()));
  }
  @Test public void unavailableEndpointDoesNotEraseCachedWeather(){
    serve(401,"unauthorized");TextView label=new TextView(app);InfinityChooserWeather weather=new InfinityChooserWeather(app,label);
    assertTrue(weather.accept(REAL));assertFalse(weather.accept(new InfinityChooserWeather.LocalReader(app).request(settings())));
    weather.renderCached();assertTrue(label.getText().toString().contains("Configured city"));
  }
  @Test public void settingsAreReadWithoutWritingAndInvalidPortIsRefused() throws Exception {
    String xml="<settings><setting id=\"services.webserver\">true</setting><setting id=\"services.webserverport\">9876</setting><setting id=\"services.webserverauthentication\">true</setting><setting id=\"services.webserverusername\">local</setting><setting id=\"services.webserverpassword\">test-only</setting></settings>";
    InfinityChooserWeather.Settings s=InfinityChooserWeather.Settings.parse(new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)));
    assertTrue(s.enabled);assertTrue(s.authenticated);assertEquals(9876,s.port);assertEquals("local",s.user);
    try{InfinityChooserWeather.Settings.parse(new ByteArrayInputStream(xml.replace("9876","70000").getBytes(StandardCharsets.UTF_8)));fail();}catch(IOException expected){}
  }
  @Test public void lateWorkerResultAfterStopCannotUpdateCache() throws Exception {
    CountDownLatch began=new CountDownLatch(1),release=new CountDownLatch(1),done=new CountDownLatch(1);
    AtomicInteger cancelled=new AtomicInteger();
    InfinityChooserWeather.Reader reader=new InfinityChooserWeather.Reader(){
      public String read(){began.countDown();try{release.await();}catch(InterruptedException ignored){}done.countDown();return REAL;}
      public void cancel(){cancelled.incrementAndGet();release.countDown();}
    };
    InfinityChooserWeather weather=new InfinityChooserWeather(app,null,reader);weather.start();assertTrue(began.await(2,TimeUnit.SECONDS));
    weather.stop();assertTrue(done.await(2,TimeUnit.SECONDS));
    org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
    assertEquals(0,weather.cache.getLong("timestamp",0));assertEquals(1,cancelled.get());assertFalse(weather.started);assertNull(weather.worker);
  }
  @Test public void unresponsiveServerHasFiniteReadTimeout() throws Exception {
    CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);
    server.createContext("/jsonrpc",e->{entered.countDown();try{release.await(4,TimeUnit.SECONDS);}catch(InterruptedException ignored){}e.close();});server.start();
    Future<String> result=executor.submit(()->new InfinityChooserWeather.LocalReader(app).request(settings()));
    try{assertTrue(entered.await(2,TimeUnit.SECONDS));assertNull(result.get(3,TimeUnit.SECONDS));}finally{release.countDown();}
  }
}
