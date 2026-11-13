package com.projectinfinity.kodi;
import com.sun.net.httpserver.HttpServer;
import java.net.*;import java.io.*;import java.nio.charset.StandardCharsets;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
/** Actual production relay with two distinct HTTP origins. No receiver claim. */
public final class RelayBoundaryTest {
 static int checks;static void check(boolean x,String m){checks++;if(!x)throw new AssertionError(m);}
 static void retire(InfinityCastRelay r)throws Exception{r.close();long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(5);while(InfinityCastRelay.busy()&&System.nanoTime()<end)Thread.sleep(10);check(!InfinityCastRelay.busy(),"retired");}
 public static void main(String[] args)throws Exception {
  HttpServer a=HttpServer.create(new InetSocketAddress("127.0.0.1",0),4),b=HttpServer.create(new InetSocketAddress("127.0.0.1",0),4);
  AtomicBoolean secret=new AtomicBoolean(),portable=new AtomicBoolean();AtomicInteger calls=new AtomicInteger();
  String target="http://127.0.0.1:"+b.getAddress().getPort()+"/video.mp4";
  a.createContext("/video.mp4",e->{e.getResponseHeaders().set("Location",target);e.sendResponseHeaders(302,-1);e.close();});
  b.createContext("/video.mp4",e->{calls.incrementAndGet();boolean valid="ExistingPlayer/1".equals(e.getRequestHeaders().getFirst("User-Agent"))&&"video/*".equals(e.getRequestHeaders().getFirst("Accept"));portable.set(valid);for(String n:new String[]{"Authorization","Cookie","X-Secret","Referer","Origin"})if(e.getRequestHeaders().getFirst(n)!=null)secret.set(true);
   e.getResponseHeaders().set("Content-Type","video/mp4");if(!valid){e.sendResponseHeaders(403,-1);e.close();return;}byte[] data=new byte[32];data[4]='f';data[5]='t';data[6]='y';data[7]='p';if(e.getRequestMethod().equals("HEAD")){e.getResponseHeaders().set("Content-Length","32");e.sendResponseHeaders(200,-1);}else{e.sendResponseHeaders(200,32);e.getResponseBody().write(data);}e.close();});
  a.start();b.start();InfinityCastRelay r=null;
  try {
   String source="http://127.0.0.1:"+a.getAddress().getPort()+"/video.mp4|User-Agent=ExistingPlayer%2F1&Accept=video%2F*&Accept-Language=en&Authorization=Bearer%20secret&Cookie=session%3Dsecret&X-Secret=private&Referer=https%3A%2F%2Fprivate.invalid&Origin=https%3A%2F%2Fprivate.invalid";
   CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> failure=new AtomicReference<>();
   r=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse(source),(owner,mime,error)->{failure.set(error);ready.countDown();});
   check(ready.await(6,TimeUnit.SECONDS),"bounded relay preparation");check(!secret.get(),"cross-origin credentials remain isolated");check(calls.get()>0,"actual second origin reached");check(portable.get()&&failure.get()==null,"original public User-Agent/Accept must survive redirect; current error="+failure.get());
   URL url=new URL(r.address());HttpURLConnection c=(HttpURLConnection)url.openConnection();c.setConnectTimeout(2000);c.setReadTimeout(2000);check(c.getResponseCode()==200,"receiver receives redirected media");try(InputStream input=c.getInputStream()){check(input.read()>=0,"actual media bytes delivered");}finally{c.disconnect();}
   check(!secret.get(),"no credentials after real receiver request");
   System.out.println("PASS_CAST_CROSS_ORIGIN_PUBLIC_HEADERS checks="+checks);
  }finally{if(r!=null)retire(r);a.stop(0);b.stop(0);}
 }
}
