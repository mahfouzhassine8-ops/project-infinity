package com.projectinfinity.kodi;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.regex.*;
import org.json.JSONObject;

/** Disposable Android transport/XML test, not remote playback or shutdown. */
final class InfinityCastAdaptiveAndroidTest {
    static String get(String address) throws Exception {
        URI uri=new URI(address);try(Socket client=new Socket(uri.getHost(),uri.getPort())) {
            client.setSoTimeout(5000);client.getOutputStream().write(("GET "+uri.getRawPath()+" HTTP/1.1\r\nHost: local\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] b=new byte[4096];int n;
            while((n=client.getInputStream().read(b))!=-1){bytes.write(b,0,n);if(bytes.size()>65536)throw new IOException("test response bound");}
            String result=bytes.toString("UTF-8");if(!result.startsWith("HTTP/1.1 200"))throw new IOException("actual delivery failed");return result.substring(result.indexOf("\r\n\r\n")+4);
        }
    }
    static void drain(InfinityCastRelay relay) throws Exception {
        relay.close();long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(InfinityCastRelay.busy() && System.nanoTime()<deadline)Thread.sleep(10);
        if(InfinityCastRelay.busy())throw new IOException("owned adaptive work did not drain");
    }
    static JSONObject run() {
        InfinityCastRelay relay=null;ServerSocket origin=null;AtomicBoolean closing=new AtomicBoolean();AtomicInteger authenticated=new AtomicInteger();
        try {
            origin=new ServerSocket(0,8,InetAddress.getByName("127.0.0.1"));final ServerSocket server=origin;
            Thread worker=new Thread(()->{
                while(!closing.get())try(Socket socket=server.accept()) {
                    socket.setSoTimeout(2000);ByteArrayOutputStream header=new ByteArrayOutputStream();int value,tail=0;
                    while(header.size()<8192 && (value=socket.getInputStream().read())!=-1){header.write(value);tail=(tail<<8)|value;if(tail==0x0d0a0d0a)break;}
                    String request=header.toString("US-ASCII");boolean head=request.startsWith("HEAD ");String target=request.split(" ")[1];String body,type;
                    if(!request.contains("authorization: Bearer private"))throw new IOException("sender authentication lost");authenticated.incrementAndGet();
                    if(target.startsWith("/private/movie.mpd")) {
                        type="application/dash+xml";body="<MPD xmlns=\"urn:mpeg:dash:schema:mpd:2011\"><Period><AdaptationSet><Representation id=\"video\" bandwidth=\"100\"><SegmentTemplate initialization=\"init.mp4?secret=init\" media=\"segment-$Number%05d$.m4s?secret=segment\" duration=\"2\"/></Representation></AdaptationSet></Period></MPD>";
                    } else if(target.startsWith("/private/movie.m3u8")) {
                        type="application/vnd.apple.mpegurl";body="#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXT-X-MAP:URI=\"init.mp4?secret=init\"\n#EXTINF:2,\nsegment.m4s?secret=segment\n#EXT-X-ENDLIST\n";
                    } else {type="video/mp4";body="fixture-media";}
                    byte[] data=body.getBytes(StandardCharsets.UTF_8);
                    socket.getOutputStream().write(("HTTP/1.1 200 OK\r\nContent-Type: "+type+"\r\nContent-Length: "+data.length+"\r\nConnection: close\r\n\r\n").getBytes(StandardCharsets.US_ASCII));if(!head)socket.getOutputStream().write(data);
                } catch(Exception stopped){if(!closing.get())return;}
            },"CIOnlyAdaptiveSource");worker.setDaemon(true);worker.start();
            for(String name:new String[]{"movie.m3u8","movie.mpd"}) {
                CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> error=new AtomicReference<>();
                relay=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse("http://127.0.0.1:"+origin.getLocalPort()+"/private/"+name+"?secret=root", "Authorization=Bearer%20private", "Authorization=Bearer%20private",false),(r,m,f)->{error.set(f);ready.countDown();});
                if(!ready.await(8,TimeUnit.SECONDS) || error.get()!=null)throw new IOException("adaptive source preparation failed");
                String manifest=get(relay.address());if(manifest.contains("/private/") || manifest.contains("secret") || manifest.contains("Bearer"))throw new IOException("manifest privacy failed");
                Matcher link=Pattern.compile("http://[^<\\\"\\s]+").matcher(manifest);boolean fetched=false;
                while(link.find())if(!link.group().contains("$")){if(!get(link.group()).equals("fixture-media"))throw new IOException("segment delivery failed");fetched=true;break;}
                if(!fetched)throw new IOException("no rewritten init/segment endpoint");drain(relay);relay=null;
            }
            return new JSONObject().put("pass",true).put("actual_Android_HLS_DASH_rewrite_and_segment_HTTP",true).put("property_auth_headers_preserved",authenticated.get()>4).put("drained",true).put("real_receiver",false).put("decoder",false);
        } catch(Exception | LinkageError failure) {
            try{return new JSONObject().put("pass",false).put("reason",failure.getClass().getSimpleName());}catch(Exception ignored){return new JSONObject();}
        } finally{closing.set(true);if(relay!=null)relay.close();if(origin!=null)try{origin.close();}catch(IOException ignored){}}
    }
}
