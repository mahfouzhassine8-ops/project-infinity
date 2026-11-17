package com.projectinfinity.kodi;
import com.sun.net.httpserver.HttpServer;
import java.io.*;import java.net.*;import java.lang.reflect.*;import java.nio.charset.StandardCharsets;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public class RelayFailureProbe {
 static void need(boolean x,String m){if(!x)throw new AssertionError(m);}
 static class Client extends Socket {final byte[] request;final boolean fail;Client(String address,boolean fail){this.fail=fail;request=("GET "+URI.create(address).getRawPath()+" HTTP/1.1\r\nHost: fixture\r\n\r\n").getBytes(StandardCharsets.US_ASCII);}public void setSoTimeout(int n){}public InputStream getInputStream()throws IOException{return new ByteArrayInputStream(request);}public OutputStream getOutputStream(){return fail?new OutputStream(){public void write(int value)throws IOException{throw new SocketException("fixture_receiver_reset");}}:new ByteArrayOutputStream();}}
 public static void main(String[] args)throws Exception {
  boolean original=args.length>0&&args[0].equals("original");AtomicBoolean refused=new AtomicBoolean();HttpServer origin=HttpServer.create(new InetSocketAddress("127.0.0.1",0),2);origin.setExecutor(Executors.newCachedThreadPool(r->{Thread t=new Thread(r);t.setDaemon(true);return t;}));
  origin.createContext("/movie.mp4",e->{byte[] bytes=new byte[8192];e.getResponseHeaders().set("Content-Type","video/mp4");e.sendResponseHeaders(refused.get()?503:200,bytes.length);e.getResponseBody().write(bytes);e.close();});origin.start();InfinityCastRelay relay=null;
  try{CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> failure=new AtomicReference<>();relay=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse("http://127.0.0.1:"+origin.getAddress().getPort()+"/movie.mp4"),(r,m,f)->{failure.set(f);ready.countDown();});need(ready.await(6,TimeUnit.SECONDS)&&failure.get()==null,"prepare");Method serve=InfinityCastRelay.class.getDeclaredMethod("serve",Socket.class);serve.setAccessible(true);InfinityCastDiagnostics.begin();serve.invoke(relay,new Client(relay.address(),false){public InputStream getInputStream()throws IOException{throw new SocketTimeoutException("fixture_request_timeout");}});
   if(!original){need(relay.failure().isEmpty(),"receiver_request_not_source_failure");need(InfinityCastDiagnostics.summary().contains("receiver_request_failed"),"request_failure_outcome");}
   serve.invoke(relay,new Client(relay.address(),true));
   if(original)need(!relay.failure().isEmpty(),"baseline_misattributes_receiver_write");
   else {need(relay.failure().isEmpty(),"downstream_not_source_failure");need(InfinityCastDiagnostics.summary().contains("receiver_write_failed"),"downstream_outcome");refused.set(true);serve.invoke(relay,new Client(relay.address(),false));need(relay.failure().equals("source_http_503"),"genuine_source_error_retained");
    Method code=InfinityCastSession.class.getDeclaredMethod("mediaErrorCode",String.class);code.setAccessible(true);need(code.invoke(null,(Object)null).equals("absent"),"null_error_reason");need(code.invoke(null,"LOAD_FAILED").equals("load_failed"),"known_reason");need(code.invoke(null,"https://private.invalid/?token=secret").equals("other"),"private_error_not_logged");}
   System.out.println(original?"REPRODUCED_BASELINE_DOWNSTREAM_ERROR_ATTRIBUTION":"PASS_ACTUAL_RELAY_DELIVERY_SOURCE_AND_SAFE_ERROR_SPLIT");
  }finally{if(relay!=null){relay.close();long until=System.nanoTime()+TimeUnit.SECONDS.toNanos(6);while(InfinityCastRelay.busy()&&System.nanoTime()<until)Thread.sleep(5);need(!InfinityCastRelay.busy(),"owned_jobs_retired");}origin.stop(0);}
 }
}
