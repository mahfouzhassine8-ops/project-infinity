package com.projectinfinity.kodi;
import android.app.Activity;import android.os.*;import android.media.*;import java.io.*;import java.net.*;import java.nio.*;import java.nio.charset.StandardCharsets;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;import org.json.*;

/** Separate CI package. Actual original94 FFmpeg/ARM64 JNI; no Kodi startup/shutdown. */
public final class InfinityCastProbeActivity extends Activity {
 static native boolean loadExistingEngine();
 static final AtomicBoolean admitted=new AtomicBoolean();
 public void onCreate(Bundle state){super.onCreate(state);if(!admitted.compareAndSet(false,true))return;new Thread(()->runProbe(),"CastMkvAndroidProbe").start();}
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
 static JSONObject extracted(byte[] all,JSONObject expected)throws Exception{
  MediaExtractor e=new MediaExtractor();try{e.setDataSource(new MediaDataSource(){public int readAt(long p,byte[] b,int offset,int size){if(p>=all.length)return -1;int n=(int)Math.min(size,all.length-p);System.arraycopy(all,(int)p,b,offset,n);return n;}public long getSize(){return all.length;}public void close(){}});
   int video=-1,audio=-1;for(int n=0;n<e.getTrackCount();n++){String type=e.getTrackFormat(n).getString(MediaFormat.KEY_MIME);if("video/avc".equals(type))video=n;if("audio/mp4a-latm".equals(type))audio=n;}
   check(video>=0 && audio>=0,"actual_fMP4_video_audio_tracks");e.selectTrack(video);e.selectTrack(audio);ByteBuffer data=ByteBuffer.allocate(1048576);int v=0,a=0;long firstVideo=Long.MAX_VALUE,firstAudio=Long.MAX_VALUE,last=0;
   while(e.getSampleTrackIndex()>=0){check(e.readSampleData(data,0)>0,"actual_media_samples");int track=e.getSampleTrackIndex();long at=e.getSampleTime();if(track==video){v++;firstVideo=Math.min(firstVideo,at);}else{a++;firstAudio=Math.min(firstAudio,at);}last=Math.max(last,at);check(e.advance() || e.getSampleTrackIndex()<0,"extractor_progress");}
   check(v==expected.getJSONObject("source_packets").getInt("video") && a==expected.getJSONObject("source_packets").getInt("audio"),"all_video_and_audio_packets_delivered");check(Math.abs((firstVideo-firstAudio)-expected.getLong("relative_video_start_us"))<=2000,"actual_A_V_relative_start");check(last-firstAudio>7900000,"complete_movie_timeline");return new JSONObject().put("video_samples",v).put("audio_samples",a).put("relative_video_start_us",firstVideo-firstAudio);
  }finally{e.release();}
 }
 static JSONObject clock(String url,long expectedDuration)throws Exception{
  MediaPlayer player=new MediaPlayer();CountDownLatch prepared=new CountDownLatch(1),seek=new CountDownLatch(1);AtomicInteger failure=new AtomicInteger();Handler ui=new Handler(Looper.getMainLooper());
  CountDownLatch created=new CountDownLatch(1);ui.post(()->{try{player.setVolume(0,0);player.setOnErrorListener((p,w,x)->{failure.set(w);prepared.countDown();seek.countDown();return true;});player.setOnPreparedListener(p->prepared.countDown());player.setOnSeekCompleteListener(p->seek.countDown());player.setDataSource(url);player.prepareAsync();}catch(Exception e){failure.set(-1);prepared.countDown();}finally{created.countDown();}});
  try{check(created.await(2,TimeUnit.SECONDS)&&prepared.await(20,TimeUnit.SECONDS)&&failure.get()==0,"actual_HLS_player_prepare");int duration=player.getDuration();check(Math.abs(duration-expectedDuration)<200,"actual_zero_based_HLS_duration");player.start();Thread.sleep(350);player.seekTo(4500,MediaPlayer.SEEK_CLOSEST);check(seek.await(12,TimeUnit.SECONDS)&&failure.get()==0,"actual_HLS_seek_complete");int position=player.getCurrentPosition();check(position>=4300&&position<5500,"actual_zero_based_HLS_seek_position");return new JSONObject().put("duration_ms",duration).put("seek_position_ms",position).put("actual_Android_HLS_playback",true);}finally{player.release();}
 }
 void runProbe(){InfinityCastRelay relay=null;Origin origin=null;String stage="engine_load";JSONObject result=new JSONObject();try{
  System.loadLibrary("infinitycastqaloader");check(loadExistingEngine(),"original94_engine_load");origin=new Origin(asset("mkv-fixtures/h264-aac.mkv"));stage="native_inspection";relay=start(origin);check(InfinityCastRemuxNative.active()==1,"one_native_context");
  String playlist=new String(body(relay.address()),StandardCharsets.UTF_8);check(playlist.contains("#EXT-X-ENDLIST")&&!playlist.contains("fixture")&&!playlist.contains("private.mkv"),"private_full_VOD_playlist");List<String> segments=new ArrayList<>();String init=null;for(String line:playlist.split("\n")){if(line.startsWith("#EXT-X-MAP:")){init=line.substring(line.indexOf('"')+1,line.lastIndexOf('"'));}else if(line.startsWith("http"))segments.add(line);}
  check(segments.size()==4&&init!=null,"verified_source_cue_boundaries");stage="random_seek_copy";byte[][] pieces=new byte[4][];for(int n:new int[]{2,0,3,1})pieces[n]=body(segments.get(n));ByteArrayOutputStream combined=new ByteArrayOutputStream();combined.write(body(init));for(byte[] part:pieces)combined.write(part);JSONObject expected=new JSONObject(new String(asset("mkv-fixtures/expected.json"),StandardCharsets.UTF_8));result.put("fMP4",extracted(combined.toByteArray(),expected));
  stage="real_HLS_clock";result.put("HLS",clock(relay.address(),relay.durationMs()));check(!origin.privateFailure,"provider_auth_preserved_only_phone_side");retire(relay);relay=null;
  stage="conversion_cancellation";relay=start(origin);origin.stallRanges=true;
  // New transfer has a fresh capability. Derive its own first segment URL.
  String next=new String(body(relay.address()),StandardCharsets.UTF_8);String target=null;for(String l:next.split("\n"))if(l.startsWith("http")){target=l;break;}
  final String fetch=target;Thread requester=new Thread(()->{try{body(fetch);}catch(Exception cancelledFetch){}},"CancelledReceiver");requester.start();check(origin.stalled.await(5,TimeUnit.SECONDS),"actual_pending_native_HTTP_read");retire(relay);relay=null;origin.release.countDown();requester.join(3000);check(!requester.isAlive(),"receiver_request_retired");
  result.put("pass",true).put("baseline_versionCode",2103494).put("existing_original_engine",true).put("new_ARM64_JNI",true).put("stream_copy_not_transcode",true).put("authenticated_ranges",true).put("random_segment_seeking",true).put("native_contexts_after_close",InfinityCastRemuxNative.active()).put("cancellation",true).put("TV_receiver","NOT_TESTED").put("Kodi_player_handback","NOT_TESTED").put("shutdown","NOT_SELECTED");
 }catch(Throwable failure){try{result.put("pass",false).put("stage",stage).put("reason",failure.getMessage()==null?failure.getClass().getSimpleName():failure.getMessage());}catch(Exception ignored){}}
 finally{if(relay!=null)relay.close();if(origin!=null)origin.close();try{result.put("API",Build.VERSION.SDK_INT);}catch(Exception ignored){}android.util.Log.i("InfinityCastProbe",result.toString());}}
}
