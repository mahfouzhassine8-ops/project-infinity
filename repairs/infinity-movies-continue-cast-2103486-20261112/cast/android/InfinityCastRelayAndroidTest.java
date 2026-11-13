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
        InfinityCastRelay relay=null;ServerSocket origin=null;String stage="fixture_start";
        AtomicReference<String> sourceFailure=new AtomicReference<>();
        try {
            origin=new ServerSocket(0,2,InetAddress.getByName("127.0.0.1"));origin.setSoTimeout(7000);
            final ServerSocket server=origin;AtomicReference<Throwable> serverError=new AtomicReference<>();
            Thread source=new Thread(()->{
                try {
                    for(int n=0;n<2;n++)try(Socket client=server.accept()) {
                        client.setSoTimeout(2000);InputStream input=client.getInputStream();ByteArrayOutputStream data=new ByteArrayOutputStream();int tail=0,value;
                        while(data.size()<4096 && (value=input.read())!=-1){data.write(value);tail=(tail<<8)|value;if(tail==0x0d0a0d0a)break;}
                        String request=data.toString("US-ASCII");
                        boolean authorization=false;for(String field:request.split("\r\n"))if(field.regionMatches(true,0,"Authorization:",0,14) && field.substring(14).trim().equals("Bearer private"))authorization=true;
                        if(!request.contains("/private-token.mp4?key=private") || !authorization){
                            sourceFailure.set("source_metadata_missing");throw new IOException("Private source metadata lost");}
                        boolean head=request.startsWith("HEAD ");
                        String headers="HTTP/1.1 "+(head?"200 OK":"206 Partial Content")+"\r\nContent-Type: video/mp4\r\nContent-Length: "+(head?"100":"8")+
                            (head?"":"\r\nContent-Range: bytes 4-11/100")+"\r\nSet-Cookie: private=not-forwarded\r\nConnection: close\r\n\r\n";
                        client.getOutputStream().write(headers.getBytes(StandardCharsets.US_ASCII));
                        if(!head)client.getOutputStream().write("abcdefgh".getBytes(StandardCharsets.US_ASCII));
                    }
                }catch(Throwable failure){serverError.set(failure);}
            },"CIOnlyCastOrigin");source.setDaemon(true);source.start();
            stage="prepare";CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> failure=new AtomicReference<>();
            relay=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),InfinityCastSource.parse(
                "http://127.0.0.1:"+origin.getLocalPort()+"/private-token.mp4?key=private|Authorization=Bearer%20private"),
                (owner,mime,error)->{failure.set(error);ready.countDown();});
            if(!ready.await(7,TimeUnit.SECONDS) || failure.get()!=null)throw new IOException("Relay preparation failed");
            stage="range_delivery";URI endpoint=new URI(relay.address());String response;
            try(Socket client=new Socket(endpoint.getHost(),endpoint.getPort())) {
                client.setSoTimeout(4000);client.getOutputStream().write(("GET "+endpoint.getRawPath()+" HTTP/1.1\r\nHost: local\r\nRange: bytes=4-11\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
                ByteArrayOutputStream data=new ByteArrayOutputStream();byte[] buffer=new byte[1024];int count;
                while((count=client.getInputStream().read(buffer))!=-1){data.write(buffer,0,count);if(data.size()>4096)throw new IOException("Relay response limit");}
                response=data.toString("US-ASCII");
            }
            stage="range_privacy";source.join(1000);
            if(source.isAlive() || serverError.get()!=null || !response.startsWith("HTTP/1.1 206") ||
                !response.endsWith("abcdefgh") || response.contains("private") || response.contains("Set-Cookie"))throw new IOException("Range/privacy contract failed");
            stage="drain";CountDownLatch retirement=new CountDownLatch(1);relay.closeWhenRetired(retirement::countDown);long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
            while(InfinityCastRelay.busy() && System.nanoTime()<deadline)Thread.sleep(10);
            if(InfinityCastRelay.busy() || !retirement.await(1,TimeUnit.SECONDS))throw new IOException("Relay did not retire");
            stage="cross_origin_headers";crossOrigin();
            return new JSONObject().put("pass",true).put("actual_private_HTTP_runtime",true).put("range_body",true)
                .put("private_source_not_returned",true).put("retired",true).put("retirement_callback",true).put("cross_origin_public_headers",true).put("real_Cast_receiver",false);
        } catch(Exception | LinkageError failure) {
            try{return new JSONObject().put("pass",false).put("reason",failure.getClass().getSimpleName()).put("stage",stage).put("source_failure",sourceFailure.get()==null?"none":sourceFailure.get());}catch(Exception ignored){return new JSONObject();}
        } finally {
            if(relay!=null)relay.close();if(origin!=null)try{origin.close();}catch(IOException ignored){}
        }
    }
    /** Two real localhost origins; preserves public negotiation, isolates auth. */
    private static void crossOrigin() throws Exception {
        InetAddress local=InetAddress.getByName("127.0.0.1");
        try(ServerSocket origin=new ServerSocket(0,4,local);ServerSocket cdn=new ServerSocket(0,4,local)) {
            origin.setSoTimeout(6000);cdn.setSoTimeout(6000);AtomicReference<Throwable> error=new AtomicReference<>();
            Thread redirect=new Thread(()->{try {for(int n=0;n<2;n++)try(Socket c=origin.accept()){
                readRequest(c);String response="HTTP/1.1 302 Found\r\nLocation: http://127.0.0.1:"+cdn.getLocalPort()+"/video.mp4\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";c.getOutputStream().write(response.getBytes(StandardCharsets.US_ASCII));
            }}catch(Throwable failure){error.set(failure);}},"CIOnlyCastRedirect");redirect.setDaemon(true);
            Thread destination=new Thread(()->{try {for(int n=0;n<2;n++)try(Socket c=cdn.accept()){
                String request=readRequest(c).toLowerCase(java.util.Locale.ROOT);
                if(!request.contains("user-agent: existingplayer/1\r\n") || !request.contains("accept: video/*\r\n"))throw new IOException("Public media headers lost");
                for(String key:new String[]{"authorization:","cookie:","x-secret:","referer:","origin:"})if(request.contains("\r\n"+key))throw new IOException("Cross-origin private header");
                c.getOutputStream().write("HTTP/1.1 200 OK\r\nContent-Type: video/mp4\r\nContent-Length: 8\r\nConnection: close\r\n\r\n".getBytes(StandardCharsets.US_ASCII));
                if(!request.startsWith("head "))c.getOutputStream().write("abcdefgh".getBytes(StandardCharsets.US_ASCII));
            }}catch(Throwable failure){error.set(failure);}},"CIOnlyCastCDN");destination.setDaemon(true);redirect.start();destination.start();
            InfinityCastRelay relay=null;
            try {
                CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> failure=new AtomicReference<>();
                relay=InfinityCastRelay.start(local,InfinityCastSource.parse("http://127.0.0.1:"+origin.getLocalPort()+"/video.mp4|User-Agent=ExistingPlayer%2F1&Accept=video%2F*&Authorization=Bearer%20secret&Cookie=secret%3Dprivate&X-Secret=private&Referer=https%3A%2F%2Fprivate.invalid&Origin=https%3A%2F%2Fprivate.invalid"),(r,m,f)->{failure.set(f);ready.countDown();});
                if(!ready.await(6,TimeUnit.SECONDS) || failure.get()!=null)throw new IOException("Cross-origin preparation failed");
                HttpURLConnection client=(HttpURLConnection)new URL(relay.address()).openConnection();client.setConnectTimeout(2000);client.setReadTimeout(3000);
                try {if(client.getResponseCode()!=200)throw new IOException("Cross-origin receiver status");try(InputStream input=client.getInputStream()){if(input.read()!='a')throw new IOException("Cross-origin receiver bytes");}}finally{client.disconnect();}
                redirect.join(1000);destination.join(1000);if(error.get()!=null || redirect.isAlive() || destination.isAlive())throw new IOException("Cross-origin fixture contract");
            }finally{if(relay!=null){CountDownLatch done=new CountDownLatch(1);relay.closeWhenRetired(done::countDown);if(!done.await(3,TimeUnit.SECONDS))throw new IOException("Cross-origin retirement timeout");}}
        }
    }
    private static String readRequest(Socket client) throws IOException {
        client.setSoTimeout(3000);ByteArrayOutputStream data=new ByteArrayOutputStream();int value,tail=0;
        while(data.size()<8192 && (value=client.getInputStream().read())!=-1){data.write(value);tail=(tail<<8)|value;if(tail==0x0d0a0d0a)break;}
        return data.toString("US-ASCII");
    }

}
