package com.projectinfinity.kodi;

import com.sun.net.httpserver.HttpServer;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

/** Actual local HTTP/OkHttp tests. No Android, receiver, Kodi or profile claim. */
public final class InfinityCastRelayTest {
    static int checks;
    static void check(boolean condition,String label){if(!condition)throw new AssertionError(label);checks++;}
    static final byte[] media=new byte[8192];
    static final List<String> observed=Collections.synchronizedList(new ArrayList<>());
    static final AtomicInteger upstreamCalls=new AtomicInteger();
    static HttpServer server(int port) throws Exception {
        HttpServer result=HttpServer.create(new InetSocketAddress("127.0.0.1",port),4);
        result.setExecutor(Executors.newFixedThreadPool(4,r->{Thread t=new Thread(r,"FixtureHTTP");t.setDaemon(true);return t;}));return result;
    }
    static InfinityCastRelay start(String source) throws Exception {
        CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> error=new AtomicReference<>();
        InfinityCastRelay value=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse(source),
            (owner,mime,failure)->{error.set(failure);ready.countDown();});
        check(ready.await(6,TimeUnit.SECONDS),"bounded prepare");
        check(error.get()==null,"supported media prepared");return value;
    }
    static void retired(InfinityCastRelay relay) throws Exception {
        relay.close();long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(6);
        while(InfinityCastRelay.busy() && System.nanoTime()<deadline)Thread.sleep(10);
        check(!InfinityCastRelay.busy(),"all owned work retired");
    }
    static byte[] request(String address,String method,String suffix,String headers,String bind) throws Exception {
        URI uri=new URI(address);
        try(Socket client=new Socket()) {
            client.bind(new InetSocketAddress(bind,0));client.connect(new InetSocketAddress(uri.getHost(),uri.getPort()),1000);client.setSoTimeout(5000);
            client.getOutputStream().write((method+" "+uri.getRawPath()+suffix+" HTTP/1.1\r\nHost: local\r\n"+headers+"\r\n").getBytes(StandardCharsets.US_ASCII));
            ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int count;
            try{while((count=client.getInputStream().read(buffer))!=-1)out.write(buffer,0,count);}catch(SocketException closed){}
            return out.toByteArray();
        }
    }
    public static void main(String[] args) throws Exception {
        Arrays.fill(media,(byte)42);
        HttpServer origin=server(0),other=server(0);String base="http://127.0.0.1:"+origin.getAddress().getPort();
        String destination="http://127.0.0.1:"+other.getAddress().getPort();
        com.sun.net.httpserver.HttpHandler serve=exchange->{
            upstreamCalls.incrementAndGet();
            observed.add(exchange.getRequestHeaders().getFirst("Authorization")+"|"+exchange.getRequestHeaders().getFirst("Cookie")+"|"+exchange.getRequestURI());
            exchange.getResponseHeaders().set("Content-Type","video/mp4");
            exchange.getResponseHeaders().set("Set-Cookie","private=do-not-forward");
            exchange.getResponseHeaders().set("Location","https://do-not-forward.invalid/token");
            String range=exchange.getRequestHeaders().getFirst("Range");int from=0,to=media.length-1,code=200;
            if(range!=null){String[] pair=range.substring(6).split("-",-1);from=Integer.parseInt(pair[0]);to=Integer.parseInt(pair[1]);code=206;exchange.getResponseHeaders().set("Content-Range","bytes "+from+"-"+to+"/"+media.length);}
            exchange.getResponseHeaders().set("Content-Length",Integer.toString(to-from+1));
            if(exchange.getRequestMethod().equals("HEAD")){exchange.sendResponseHeaders(code,-1);exchange.close();}
            else {exchange.sendResponseHeaders(code,to-from+1);try(OutputStream body=exchange.getResponseBody()){body.write(media,from,to-from+1);}}
        };
        origin.createContext("/private/",serve);other.createContext("/private/",serve);
        origin.createContext("/redirect.mp4",e->{e.getResponseHeaders().set("Location",destination+"/private/other.mp4");e.sendResponseHeaders(302,-1);e.close();});
        origin.createContext("/unsupported.mp4",e->{e.getResponseHeaders().set("Content-Type","application/vnd.apple.mpegurl");e.sendResponseHeaders(200,-1);e.close();});
        CountDownLatch stalled=new CountDownLatch(1),release=new CountDownLatch(1);
        origin.createContext("/stall.mp4",e->{stalled.countDown();try{release.await(8,TimeUnit.SECONDS);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();}e.close();});
        origin.start();other.start();
        try {
            check(InfinityCastSource.parse("plugin://provider/action")==null,"no independent provider invocation");
            check(InfinityCastSource.parse(base+"/a.m3u8")==null,"no adaptive rewrite");
            check(InfinityCastSource.parse(base+"/a.mp4|verifypeer=false")==null,"no TLS override");
            check(InfinityCastSource.parse(base+"/a.mp4|Cookie=a%0D%0Ab")==null,"no header injection");
            check(InfinityCastSource.parse("http://user:secret@127.0.0.1/a.mp4")==null,"no ambiguous URL userinfo");
            check(InfinityCastSource.receiverTitle("https://secret.invalid/a").equals("Infinity video"),"no URL title");
            InfinityCastRelay relay=start(base+"/private/opaque-token.mp4?api_key=secret|Authorization=Bearer%20private&Cookie=session%3Dprivate&Referer=https%3A%2F%2Fprivate.invalid");
            check(!relay.address().contains("secret") && !relay.address().contains("private"),"receiver URL contains only local capability");
            byte[] response=request(relay.address(),"GET","","Range: bytes=10-29\r\n","127.0.0.1");
            String text=new String(response,StandardCharsets.ISO_8859_1);
            check(text.startsWith("HTTP/1.1 206"),"actual range status");
            check(text.contains("Content-Range: bytes 10-29/8192"),"actual range preserved");
            check(response.length-text.indexOf("\r\n\r\n")-4==20,"actual range body");
            check(!text.contains("secret") && !text.contains("Set-Cookie") && !text.contains("Location:") && !text.contains("private"),"credentials/upstream headers never returned");
            check(observed.get(0).contains("Bearer private|session=private|/private/opaque-token.mp4?api_key=secret"),"original URL and headers reach source only");
            int count=upstreamCalls.get();
            check(request(relay.address(),"GET","/wrong","","127.0.0.1").length==0,"wrong capability rejected");
            check(request(relay.address(),"GET","","","127.0.0.2").length==0,"different peer rejected");
            check(request(relay.address(),"GET","","Range: bytes=0-1,3-4\r\n","127.0.0.1").length==0,"multiple ranges rejected");
            check(upstreamCalls.get()==count,"rejected requests do not reach source");
            text=new String(request(relay.address(),"HEAD","","","127.0.0.1"),StandardCharsets.US_ASCII);
            check(text.startsWith("HTTP/1.1 200") && text.endsWith("\r\n\r\n"),"HEAD returns metadata only");
            URI endpoint=new URI(relay.address());
            Socket slow=new Socket(endpoint.getHost(),endpoint.getPort());slow.setSoTimeout(3500);
            slow.getOutputStream().write("G".getBytes(StandardCharsets.US_ASCII));
            check(slow.getInputStream().read()==-1,"incomplete request has total deadline");slow.close();
            retired(relay);
            observed.clear();relay=start(base+"/redirect.mp4|Authorization=Bearer%20private&Cookie=session%3Dprivate");
            request(relay.address(),"GET","","","127.0.0.1");
            check(observed.size()==2 && observed.stream().allMatch(v->v.startsWith("null|null|")),"cross-origin redirect permanently strips private headers");retired(relay);
            CountDownLatch failed=new CountDownLatch(1);AtomicReference<String> reason=new AtomicReference<>();
            relay=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse(base+"/unsupported.mp4"),(r,m,f)->{reason.set(f);failed.countDown();});
            check(failed.await(6,TimeUnit.SECONDS) && reason.get()!=null,"unsupported MIME reports failure");retired(relay);
            CountDownLatch cancelled=new CountDownLatch(1);
            relay=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse(base+"/stall.mp4"),(r,m,f)->cancelled.countDown());
            check(stalled.await(2,TimeUnit.SECONDS),"actual pending source request");
            long at=System.nanoTime();retired(relay);check(TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-at)<2500,"cancel closes pending HTTP promptly");
            release.countDown();
            System.out.println("PASS_CAST_RELAY_HTTP_AND_OWNERSHIP checks="+checks+" (host only; no real Cast receiver)");
        } finally {release.countDown();origin.stop(0);other.stop(0);}
    }
}
