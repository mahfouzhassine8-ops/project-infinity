package com.projectinfinity.kodi;
import java.io.*;import java.net.*;import java.util.*;import java.nio.charset.StandardCharsets;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
// Existing authenticated synthetic origin fixture; no provider or owner data.
 final class Origin implements AutoCloseable {
  final ServerSocket server;final byte[] data;final Set<Socket> clients=ConcurrentHashMap.newKeySet();final AtomicInteger reads=new AtomicInteger();
  final CountDownLatch stalled=new CountDownLatch(1),release=new CountDownLatch(1);volatile boolean closed,stallRanges,privateFailure;
  Origin(byte[] bytes)throws Exception {data=bytes;server=new ServerSocket(0,8,InetAddress.getByName("127.0.0.1"));Thread accept=new Thread(()->{while(!closed)try{Socket s=server.accept();clients.add(s);Thread t=new Thread(()->serve(s),"MkvFixtureHTTP");t.setDaemon(true);t.start();}catch(IOException done){break;}},"MkvFixtureAccept");accept.setDaemon(true);accept.start();}
  String address(){return "http://127.0.0.1:"+server.getLocalPort()+"/private.mkv?token=fixture";}
  void serve(Socket s){try(Socket c=s){c.setSoTimeout(3000);ByteArrayOutputStream h=new ByteArrayOutputStream();int value,tail=0;while(h.size()<8192 && (value=c.getInputStream().read())!=-1){h.write(value);tail=(tail<<8)|value;if(tail==0x0d0a0d0a)break;}
   String header=h.toString("US-ASCII"),lower=header.toLowerCase(Locale.ROOT);if(!lower.contains("authorization: bearer fixture\r\n") || !lower.contains("session=fixture")){privateFailure=true;return;}
   boolean head=header.startsWith("HEAD ");long from=0,to=data.length-1;boolean range=false;
   for(String line:header.split("\r\n"))if(line.toLowerCase(Locale.ROOT).startsWith("range: bytes=")){String[] pair=line.substring(13).trim().split("-",-1);from=Long.parseLong(pair[0]);if(pair.length>1 && !pair[1].isEmpty())to=Math.min(to,Long.parseLong(pair[1]));range=true;}
   if(range && stallRanges){stalled.countDown();release.await(12,TimeUnit.SECONDS);return;}
   if(from>to || from>=data.length){c.getOutputStream().write("HTTP/1.1 416 Range Not Satisfiable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".getBytes(StandardCharsets.US_ASCII));return;}
   reads.incrementAndGet();String response="HTTP/1.1 "+(range?"206 Partial Content":"200 OK")+"\r\nContent-Type: video/x-matroska\r\nContent-Length: "+(to-from+1)+"\r\nETag: \"fixed-mkv-fixture\"\r\nConnection: close\r\n"+(range?"Content-Range: bytes "+from+"-"+to+"/"+data.length+"\r\n":"")+"\r\n";
   c.getOutputStream().write(response.getBytes(StandardCharsets.US_ASCII));if(!head)c.getOutputStream().write(data,(int)from,(int)(to-from+1));
  }catch(Exception ignored){}finally{clients.remove(s);}}
  public void close(){closed=true;release.countDown();try{server.close();}catch(Exception ignored){}for(Socket c:clients)try{c.close();}catch(Exception ignored){}}
 }
