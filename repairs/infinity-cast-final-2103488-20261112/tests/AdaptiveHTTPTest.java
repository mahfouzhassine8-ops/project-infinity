package com.projectinfinity.kodi;

import com.sun.net.httpserver.HttpServer;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.regex.*;

public final class AdaptiveHTTPTest {
    static int checks;
    static final AtomicInteger authenticated=new AtomicInteger(),denied=new AtomicInteger();
    static void check(boolean condition,String label){if(!condition)throw new AssertionError(label);checks++;}
    static String text(String uri) throws Exception {
        HttpURLConnection c=(HttpURLConnection)new URL(uri).openConnection();c.setConnectTimeout(3000);c.setReadTimeout(7000);
        try(InputStream in=c.getInputStream()){return new String(in.readAllBytes(),StandardCharsets.UTF_8);}finally{c.disconnect();}
    }
    static InfinityCastRelay relay(String uri) throws Exception {return relay(InfinityCastSource.parse(uri+"|Authorization=Bearer%20private&Cookie=fixture%3Dsecret"));}
    static InfinityCastRelay relay(InfinityCastSource source) throws Exception {
        CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> error=new AtomicReference<>();
        InfinityCastRelay r=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),source,(o,m,f)->{error.set(f);ready.countDown();});
        check(ready.await(10,TimeUnit.SECONDS),"bounded preparation");check(error.get()==null,"supported adaptive media prepared: "+error.get());return r;
    }
    static void retire(InfinityCastRelay r) throws Exception {
        r.close();long until=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(InfinityCastRelay.busy() && System.nanoTime()<until)Thread.sleep(10);check(!InfinityCastRelay.busy(),"relay, clients and upstream work drained");
    }
    static void decode(String url,boolean seek) throws Exception {
        List<String> args=new ArrayList<>(Arrays.asList("ffmpeg","-hide_banner","-loglevel","error"));if(seek)args.addAll(Arrays.asList("-ss","3"));
        args.addAll(Arrays.asList("-i",url,"-t","1","-f","null","-"));
        Process process=new ProcessBuilder(args).redirectErrorStream(true).start();boolean done=process.waitFor(25,TimeUnit.SECONDS);
        if(!done)process.destroyForcibly();String output=new String(process.getInputStream().readAllBytes(),StandardCharsets.UTF_8);
        check(done && process.exitValue()==0,"actual FFmpeg adaptive decode/seek: "+output); 
    }
    static void refused(String uri) throws Exception {
        CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> error=new AtomicReference<>();
        InfinityCastRelay r=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse(uri),(o,m,f)->{error.set(f);ready.countDown();});
        check(ready.await(10,TimeUnit.SECONDS) && error.get()!=null,"DRM/XXE/malformed source is refused before receiver load");retire(r);
    }
    public static void main(String[] args) throws Exception {
        Path root=Paths.get(args[0]);HttpServer server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),12);
        server.setExecutor(Executors.newFixedThreadPool(8,r->{Thread t=new Thread(r,"AdaptiveFixture");t.setDaemon(true);return t;}));
        server.createContext("/",e->{
            String path=e.getRequestURI().getPath();Path file=root.resolve(path.substring(1)).normalize();
            if(!file.startsWith(root) || !Files.isRegularFile(file)){e.sendResponseHeaders(404,-1);e.close();return;}
            if(!path.contains("drm") && !path.contains("entity") && !("Bearer private".equals(e.getRequestHeaders().getFirst("Authorization")) && "fixture=secret".equals(e.getRequestHeaders().getFirst("Cookie")))){denied.incrementAndGet();e.sendResponseHeaders(403,-1);e.close();return;}
            String fixtureHeader=e.getRequestHeaders().getFirst("X-Cast-Fixture");
            if(fixtureHeader!=null && !(path.endsWith(".m3u8")?"manifest":"stream").equals(fixtureHeader)){denied.incrementAndGet();e.sendResponseHeaders(403,-1);e.close();return;}
            authenticated.incrementAndGet();byte[] data=Files.readAllBytes(file);String type=path.endsWith(".m3u8")?"application/vnd.apple.mpegurl":path.endsWith(".mpd")?"application/dash+xml":path.endsWith(".ts")?"video/mp2t":path.endsWith(".m4s") || path.endsWith(".mp4")?"video/mp4":"application/octet-stream";
            e.getResponseHeaders().set("Content-Type",type);String range=e.getRequestHeaders().getFirst("Range");int from=0,to=data.length-1,status=200;
            if(range!=null){Matcher m=Pattern.compile("bytes=([0-9]+)-([0-9]*)").matcher(range);if(!m.matches()){e.sendResponseHeaders(416,-1);e.close();return;}from=Integer.parseInt(m.group(1));if(!m.group(2).isEmpty())to=Math.min(to,Integer.parseInt(m.group(2)));if(from>to){e.sendResponseHeaders(416,-1);e.close();return;}status=206;e.getResponseHeaders().set("Content-Range","bytes "+from+"-"+to+"/"+data.length);}
            e.getResponseHeaders().set("Content-Length",String.valueOf(to-from+1));
            if(e.getRequestMethod().equals("HEAD")){e.sendResponseHeaders(status,-1);e.close();return;}
            e.sendResponseHeaders(status,to-from+1);try(OutputStream body=e.getResponseBody()){body.write(data,from,to-from+1);}
        });server.start();String base="http://127.0.0.1:"+server.getAddress().getPort();
        try {
            for(String path:new String[]{"hls/master.m3u8","fmp4/movie.m3u8","dash/stream.mpd","multi/master.m3u8","single/stream.mpd"}) {
                InfinityCastRelay r=relay(base+"/private/"+path+"?secret=root-token");String manifest=text(r.address());
                check(!manifest.contains("root-token") && !manifest.contains("fixture-token") && !manifest.contains("/private/") && !manifest.contains("Authorization") && !manifest.contains("Cookie"),"rewritten manifest never exposes source or credentials");
                decode(r.address(),false);decode(r.address(),true);retire(r);
            }
            check(InfinityCastSource.parse(base+"/private/hls/movie.m3u8", "Authorization=Bearer%20private", "Authorization=Bearer%20private",true)==null,"declared inputstream DRM refused");
            InfinityCastRelay properties=relay(InfinityCastSource.parse(base+"/private/hls/movie.m3u8", "Authorization=Bearer%20private&Cookie=fixture%3Dsecret&X-Cast-Fixture=manifest", "Authorization=Bearer%20private&Cookie=fixture%3Dsecret&X-Cast-Fixture=stream",false));
            decode(properties.address(),false);check(text(properties.address()+"?_HLS_msn=1&_HLS_part=0").startsWith("#EXTM3U"),"bounded HLS reload query preserved through private sender URI");retire(properties);
            InfinityCastRelay r=relay(base+"/private/encrypted/movie.m3u8");String manifest=text(r.address());
            check(!manifest.contains("key-token") && !manifest.contains("segment-token") && !manifest.contains("private label"),"key/segment URIs and labels remain private");
            Matcher key=Pattern.compile("URI=\"([^\"]*)\"").matcher(manifest);check(key.find(),"AES-128 identity key rewritten");
            byte[] keyBytes=new URL(key.group(1)).openStream().readAllBytes();check(keyBytes.length==16,"legitimate HLS key delivered only over selected-peer capability");decode(r.address(),false);decode(r.address(),true);retire(r);
            refused(base+"/private/drm.m3u8");refused(base+"/private/drm.mpd");refused(base+"/private/entity.mpd");
            check(authenticated.get()>20 && denied.get()==0,"all actual manifest/init/audio/video/key requests preserve legitimate sender auth");
            System.out.println("PASS_ADAPTIVE_ACTUAL_AUTHENTICATED_HTTP_DECODE_SEEK_AND_CLEANUP checks="+checks+"; NOT_A_REAL_CAST_RECEIVER_TEST");
        } finally{server.stop(0);}
    }
}
