package com.projectinfinity.kodi;
import android.app.Activity;import android.os.*;import android.media.*;import java.io.*;import java.net.*;import java.nio.*;import java.nio.charset.StandardCharsets;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;import org.json.*;

/** Separate CI package. Actual signed504 FFmpeg/ARM64 JNI; no Kodi startup/shutdown. */
public final class InfinityCastProbeActivity extends Activity {
 static native boolean loadExistingEngine();
 static final AtomicBoolean admitted=new AtomicBoolean();
 volatile android.view.Surface outputSurface;
 public void onCreate(Bundle state){super.onCreate(state);android.view.SurfaceView screen=new android.view.SurfaceView(this);screen.getHolder().addCallback(new android.view.SurfaceHolder.Callback(){public void surfaceCreated(android.view.SurfaceHolder h){outputSurface=h.getSurface();if(admitted.compareAndSet(false,true))new Thread(()->runProbe(),"CastMkvAndroidProbe").start();}public void surfaceChanged(android.view.SurfaceHolder h,int f,int w,int height){}public void surfaceDestroyed(android.view.SurfaceHolder h){outputSurface=null;}});setContentView(screen);}
 static void check(boolean value,String reason)throws IOException{if(!value)throw new IOException(reason);}
 static byte[] body(String address)throws Exception{
  HttpURLConnection c=(HttpURLConnection)new URL(address).openConnection();c.setConnectTimeout(3000);c.setReadTimeout(15000);
  try{check(c.getResponseCode()==200,"receiver_HTTP_status");ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[16384];try(InputStream in=c.getInputStream()){int n;while((n=in.read(buffer))!=-1){check(bytes.size()+n<=16*1024*1024,"receiver_body_limit");bytes.write(buffer,0,n);}}return bytes.toByteArray();}finally{c.disconnect();}
 }
 static final class Origin implements AutoCloseable {
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
 byte[] asset(String path)throws Exception{try(InputStream in=getAssets().open(path)){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toByteArray();}}
 static InfinityCastRelay start(Origin o)throws Exception{
  CountDownLatch ready=new CountDownLatch(1);AtomicReference<String> failure=new AtomicReference<>();InfinityCastSource source=InfinityCastSource.parse(o.address()+"|Authorization=Bearer%20fixture&Cookie=session%3Dfixture&User-Agent=ExistingPlayer%2F1");
  InfinityCastRelay r=InfinityCastRelay.start(InetAddress.getByName("127.0.0.1"),source,(owner,mime,error)->{failure.set(error);ready.countDown();});
  check(ready.await(20,TimeUnit.SECONDS),"native_prepare_deadline");check(failure.get()==null,"native_prepare_"+failure.get());return r;
 }
 static void retire(InfinityCastRelay r)throws Exception{CountDownLatch done=new CountDownLatch(1);r.closeWhenRetired(done::countDown);check(done.await(4,TimeUnit.SECONDS),"native_and_transport_retirement");check(!InfinityCastRelay.busy() && InfinityCastRemuxNative.active()==0,"native_context_leak");}

 static JSONObject extracted(byte[] all,String name)throws Exception{
  MediaExtractor e=new MediaExtractor();try{e.setDataSource(new MediaDataSource(){public int readAt(long p,byte[] b,int offset,int size){if(p>=all.length)return -1;int n=(int)Math.min(size,all.length-p);System.arraycopy(all,(int)p,b,offset,n);return n;}public long getSize(){return all.length;}public void close(){}});
   int video=-1,audio=-1;for(int n=0;n<e.getTrackCount();n++){MediaFormat f=e.getTrackFormat(n);String type=f.getString(MediaFormat.KEY_MIME);if(type.startsWith("video/"))video=n;if("audio/mp4a-latm".equals(type)){audio=n;check(f.getInteger(MediaFormat.KEY_CHANNEL_COUNT)==2,"actual_AAC_stereo");}}
   check(video>=0 && audio>=0,"actual_AAC_fMP4_tracks");e.selectTrack(video);e.selectTrack(audio);ByteBuffer data=ByteBuffer.allocate(1048576);int v=0,a=0;long last=-1;
   while(e.getSampleTrackIndex()>=0){check(e.readSampleData(data,0)>0,"actual_media_sample");int track=e.getSampleTrackIndex();if(track==video)v++;else a++;last=Math.max(last,e.getSampleTime());e.advance();}
   check(v>30 && a>50 && last>1500000,"actual_complete_media");return new JSONObject().put("video_packets",v).put("AAC_packets",a).put("name",name);
  }finally{e.release();}
 }
 static String mediaAddress(String master)throws Exception{for(String line:master.split("\n"))if(line.startsWith("http"))return line;throw new IOException("media_playlist_missing");}
 static void ranges(String url,byte[] expected)throws Exception{
  HttpURLConnection c=(HttpURLConnection)new URL(url).openConnection();c.setConnectTimeout(3000);c.setReadTimeout(15000);c.setRequestProperty("Range","bytes=0-15");try{check(c.getResponseCode()==206,"converted_range_206");check(c.getHeaderField("Content-Range").equals("bytes 0-15/"+expected.length),"converted_content_range");byte[] b=new byte[16];try(DataInputStream in=new DataInputStream(c.getInputStream())){in.readFully(b);check(in.read()==-1,"range_length");}check(Arrays.equals(b,Arrays.copyOf(expected,16)),"range_bytes");}finally{c.disconnect();}
 }
 void runProbe(){InfinityCastRelay relay=null;Origin origin=null;String stage="engine_load";JSONObject result=new JSONObject();try{
  System.loadLibrary("infinitycastqaloader");check(loadExistingEngine(),"exact504_engine_load");JSONArray cases=new JSONArray();
  for(String name:new String[]{"transients51","44100-odd","32000","main10-eac3"}){
   long wall=SystemClock.elapsedRealtime(),cpu=android.os.Process.getElapsedCpuTime(),heap=android.os.Debug.getNativeHeapAllocatedSize();stage=name+"_prepare";origin=new Origin(asset("cast-fixtures/"+name+".mkv"));relay=start(origin);check(InfinityCastRemuxNative.active()==1,"one_owned_native_context");
   String master=new String(body(relay.address()),StandardCharsets.UTF_8);check(master.contains("mp4a.40.2")&&!master.contains("ec-3")&&!master.contains("fixture")&&!master.contains("private.mkv"),"truthful_private_AAC_master");
   String playlist=new String(body(mediaAddress(master)),StandardCharsets.UTF_8);check(playlist.contains("#EXT-X-ENDLIST"),"complete_VOD_playlist");List<String> segments=new ArrayList<>();String init=null;for(String line:playlist.split("\n")){if(line.startsWith("#EXT-X-MAP:"))init=line.substring(line.indexOf('"')+1,line.lastIndexOf('"'));else if(line.startsWith("http"))segments.add(line);}
   check(segments.size()>=2 && init!=null,"cue_playlists");byte[][] pieces=new byte[segments.size()][];
   stage=name+"_out_of_order";for(int step=0;step<segments.size();step++){int n=(step%2==0)?segments.size()-1-step/2:step/2;pieces[n]=body(segments.get(n));}
   check(Arrays.equals(pieces[0],body(segments.get(0))),"deterministic_evicted_fragment");byte[] actualInit=body(init);ranges(init,actualInit);
   ByteArrayOutputStream combined=new ByteArrayOutputStream();combined.write(actualInit);for(byte[] p:pieces)combined.write(p);try(FileOutputStream f=new FileOutputStream(new File(getExternalFilesDir(null),name+".mp4"))){f.write(combined.toByteArray());}
   JSONObject row=extracted(combined.toByteArray(),name);row.put("native_heap_before_bytes",heap).put("native_heap_after_conversion_bytes",android.os.Debug.getNativeHeapAllocatedSize()).put("Java_heap_after_conversion_bytes",Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory());
   if(name.equals("transients51")){stage="actual_H264_AAC_HLS_play_and_seek";row.put("HLS",MkvHlsPlayerProbe.play(this,relay.address(),relay.durationMs()));}
   check(!origin.privateFailure,"provider_authentication_preserved");retire(relay);relay=null;origin.close();origin=null;row.put("case_wall_ms",SystemClock.elapsedRealtime()-wall).put("case_process_CPU_ms",android.os.Process.getElapsedCpuTime()-cpu).put("native_heap_after_retirement_bytes",android.os.Debug.getNativeHeapAllocatedSize());cases.put(row);
  }
  stage="cancel_during_AAC_source_read";origin=new Origin(asset("cast-fixtures/transients51.mkv"));relay=start(origin);origin.stallRanges=true;
  final String address=relay.address();AtomicReference<Throwable> cancelled=new AtomicReference<>();Thread request=new Thread(()->{try{body(address);}catch(Throwable e){cancelled.set(e);}},"CastCancelledConversion");request.start();
  check(origin.stalled.await(5,TimeUnit.SECONDS),"actual_pending_AAC_JNI_source_read");retire(relay);relay=null;request.join(3000);check(!request.isAlive() && cancelled.get()!=null,"cancelled_conversion_retired");
  result.put("pass",true).put("baseline",2103504).put("actual_ARM64_encoder_JNI_relay",true).put("cases",cases).put("cancellation",true).put("native_contexts_after_close",InfinityCastRemuxNative.active()).put("TV_receiver","NOT_TESTED").put("Kodi_phone_handoff","UNCHANGED_NOT_TESTED").put("shutdown","NOT_SELECTED");
 }catch(Throwable e){try{result.put("pass",false).put("HLS_partial_evidence",MkvHlsPlayerProbe.lastEvidence.get()).put("stage",stage).put("reason",e.getMessage()==null?e.getClass().getSimpleName():e.getMessage());}catch(Exception ignored){}}
 finally{if(relay!=null)relay.close();if(origin!=null)origin.close();try{result.put("API",Build.VERSION.SDK_INT);}catch(Exception ignored){}android.util.Log.i("InfinityCastProbe",result.toString());}}
}
