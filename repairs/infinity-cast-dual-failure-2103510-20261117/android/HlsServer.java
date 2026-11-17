package com.projectinfinity.kodi;
import java.io.*;import java.net.*;import java.nio.charset.StandardCharsets;import java.util.concurrent.atomic.*;

/** CI-only real HLS HTTP transport around the actual native/MediaCodec converter. */
final class HlsServer implements AutoCloseable {
 final InfinityCastRemux remux;final ServerSocket listener;final Thread thread;final AtomicInteger resources=new AtomicInteger();final AtomicLong bytes=new AtomicLong();volatile boolean closed;volatile Socket client;
 HlsServer(InfinityCastRemux r)throws Exception{remux=r;listener=new ServerSocket(0,8,InetAddress.getByName("127.0.0.1"));thread=new Thread(()->serve(),"CastPipelineHlsHTTP");thread.start();}
 String base(){return "http://127.0.0.1:"+listener.getLocalPort();}String address(){return base()+"/master.m3u8";}
 void serve(){while(!closed)try(Socket c=listener.accept()){client=c;c.setSoTimeout(5000);ByteArrayOutputStream h=new ByteArrayOutputStream();int value,tail=0;while(h.size()<8192&&(value=c.getInputStream().read())!=-1){h.write(value);tail=(tail<<8)|value;if(tail==0x0d0a0d0a)break;}String line=h.toString("US-ASCII").split("\r\n")[0];String[] request=line.split(" ");if(request.length!=3||!(request[0].equals("GET")||request[0].equals("HEAD")))continue;String path=request[1];byte[] body;String mime;
  if(path.equals("/master.m3u8")){body=remux.playlist(base());mime="application/vnd.apple.mpegurl";}else if(path.equals("/mkv/media.m3u8")){body=remux.mediaPlaylist(base());mime="application/vnd.apple.mpegurl";}else if(path.matches("/mkv/(init\\.mp4|[0-9]{1,4}\\.m4s)")){body=remux.resource(path.substring(5));mime="video/mp4";}else continue;
  // A complete generated fragment is the resource. Range may be ignored with
  // HTTP200; this fixture never splices separately regenerated encoded bytes.
  OutputStream out=c.getOutputStream();out.write(("HTTP/1.1 200 OK\r\nConnection: close\r\nCache-Control: no-store\r\nAccept-Ranges: none\r\nContent-Type: "+mime+"\r\nContent-Length: "+body.length+"\r\n\r\n").getBytes(StandardCharsets.US_ASCII));if(request[0].equals("GET")){out.write(body);out.flush();bytes.addAndGet(body.length);}resources.incrementAndGet();
 }catch(Throwable failure){if(!closed)android.util.Log.e("InfinityPipelineProbe","CI HLS server failure",failure);}finally{client=null;}}
 public void close()throws Exception{closed=true;listener.close();Socket c=client;if(c!=null)c.close();thread.join(5000);InfinityCastProbeActivity.check(!thread.isAlive(),"HLS_HTTP_worker_retired");}
}
