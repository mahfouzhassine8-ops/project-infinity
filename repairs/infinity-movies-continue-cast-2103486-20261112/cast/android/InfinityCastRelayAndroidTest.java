package com.projectinfinity.kodi;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import org.json.JSONObject;

/** CI-only local simulated receiver/source; never an owner APK class. */
final class InfinityCastRelayAndroidTest {
    static JSONObject run() {
        InfinityCastRelay relay=null;ServerSocket origin=null;
        try {
            origin=new ServerSocket(0,2,InetAddress.getByName("127.0.0.1"));origin.setSoTimeout(7000);
            final ServerSocket server=origin;AtomicReference<Throwable> serverError=new AtomicReference<>();
            Thread source=new Thread(()->{
                try {
                    for(int n=0;n<2;n++)try(Socket client=server.accept()) {
                        client.setSoTimeout(2000);InputStream input=client.getInputStream();ByteArrayOutputStream data=new ByteArrayOutputStream();int tail=0,value;
                        while(data.size()<4096 && (value=input.read())!=-1){data.write(value);tail=(tail<<8)|value;if(tail==0x0d0a0d0a)break;}
                        String request=data.toString("US-ASCII");
                        if(!request.contains("/private-token.mp4?key=private") || !request.contains("authorization: Bearer private"))
                            throw new IOException("Private source metadata lost");
                        boolean head=request.startsWith("HEAD ");
                        String headers="HTTP/1.1 "+(head?"200 OK":"206 Partial Content")+"\r\nContent-Type: video/mp4\r\nContent-Length: "+(head?"100":"8")+
                            (head?"":"\r\nContent-Range: bytes 4-11/100")+"\r\nSet-Cookie: private=not-forwarded\r\nConnection: close\r\n\r\n";
                        client.getOutputStream().write(headers.getBytes(StandardCharsets.US_ASCII));
                        if(!head)client.getOutputStream().write("abcdefgh".getBytes(StandardCharsets.US_ASCII));
                    }
                }catch(Throwable failure){serverError.set(failure);}
            },"CIOnlyCastOrigin");source.setDaemon(true);source.start();
            CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> failure=new AtomicReference<>();
            relay=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse(
                "http://127.0.0.1:"+origin.getLocalPort()+"/private-token.mp4?key=private|Authorization=Bearer%20private"),
                (owner,mime,error)->{failure.set(error);ready.countDown();});
            if(!ready.await(7,TimeUnit.SECONDS) || failure.get()!=null)throw new IOException("Relay preparation failed");
            URI endpoint=new URI(relay.address());String response;
            try(Socket client=new Socket(endpoint.getHost(),endpoint.getPort())) {
                client.setSoTimeout(4000);client.getOutputStream().write(("GET "+endpoint.getRawPath()+" HTTP/1.1\r\nHost: local\r\nRange: bytes=4-11\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
                ByteArrayOutputStream data=new ByteArrayOutputStream();byte[] buffer=new byte[1024];int count;
                while((count=client.getInputStream().read(buffer))!=-1){data.write(buffer,0,count);if(data.size()>4096)throw new IOException("Relay response limit");}
                response=data.toString("US-ASCII");
            }
            source.join(1000);
            if(source.isAlive() || serverError.get()!=null || !response.startsWith("HTTP/1.1 206") ||
                !response.endsWith("abcdefgh") || response.contains("private") || response.contains("Set-Cookie"))throw new IOException("Range/privacy contract failed");
            relay.close();long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
            while(InfinityCastRelay.busy() && System.nanoTime()<deadline)Thread.sleep(10);
            if(InfinityCastRelay.busy())throw new IOException("Relay did not retire");
            return new JSONObject().put("pass",true).put("actual_private_HTTP_runtime",true).put("range_body",true)
                .put("private_source_not_returned",true).put("retired",true).put("real_Cast_receiver",false);
        } catch(Exception | LinkageError failure) {
            try{return new JSONObject().put("pass",false).put("reason",failure.getClass().getSimpleName());}catch(Exception ignored){return new JSONObject();}
        } finally {
            if(relay!=null)relay.close();if(origin!=null)try{origin.close();}catch(IOException ignored){}
        }
    }
}
