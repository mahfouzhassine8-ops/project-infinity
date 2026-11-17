package com.projectinfinity.kodi;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import java.lang.reflect.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import org.json.JSONObject;

/** CI package only. Uses immutable baseline Media3 APIs, never Cobra entry points.
 * Android's legacy MediaPlayer HLS implementation cannot parse EXT-X-MAP/fMP4.
 * No dependency or this helper is added to the owner APK/component DEX.
 */
final class MkvHlsPlayerProbe {
 interface Task {Object run() throws Exception;}
 static Object main(Task task)throws Exception {
  CountDownLatch done=new CountDownLatch(1);AtomicReference<Object> value=new AtomicReference<>();AtomicReference<Throwable> failure=new AtomicReference<>();
  new Handler(Looper.getMainLooper()).post(()->{try{value.set(task.run());}catch(Throwable e){failure.set(e);}finally{done.countDown();}});
  InfinityCastProbeActivity.check(done.await(4,TimeUnit.SECONDS),"HLS_UI_call_deadline");
  if(failure.get()!=null)throw new Exception("HLS_UI_"+failure.get().getClass().getSimpleName(),failure.get());return value.get();
 }
 static final AtomicReference<JSONObject> lastEvidence=new AtomicReference<>();
 static int count(Object player,String kind)throws Exception {
  return (Integer)main(()->{Object c=Class.forName("androidx.media3.exoplayer.ExoPlayer").getMethod("get"+kind+"DecoderCounters").invoke(player);if(c==null)return 0;c.getClass().getMethod("ensureUpdated").invoke(c);return c.getClass().getField("renderedOutputBufferCount").get(c);});
 }
 static JSONObject play(Context context,String url,long expected)throws Exception {
  final AtomicInteger firstFrames=new AtomicInteger();final JSONObject evidence=new JSONObject();lastEvidence.set(evidence);
  final Class<?> api=Class.forName("androidx.media3.common.Player"),item=Class.forName("androidx.media3.common.MediaItem");
  final Object player=main(()->{
   Class<?> builder=Class.forName("androidx.media3.exoplayer.ExoPlayer$Builder");Object b=builder.getConstructor(Context.class).newInstance(context);Object p=builder.getMethod("build").invoke(b);
   try {
    Class<?> mb=Class.forName("androidx.media3.common.MediaItem$Builder");Object m=mb.getConstructor().newInstance();mb.getMethod("setUri",String.class).invoke(m,url);mb.getMethod("setMimeType",String.class).invoke(m,"application/x-mpegURL");
    Class<?> listener=Class.forName("androidx.media3.common.Player$Listener");Object events=java.lang.reflect.Proxy.newProxyInstance(listener.getClassLoader(),new Class[]{listener},(proxy,method,args)->{if(method.getName().equals("onRenderedFirstFrame"))firstFrames.incrementAndGet();if(method.getName().equals("hashCode"))return System.identityHashCode(proxy);if(method.getName().equals("equals"))return proxy==args[0];if(method.getName().equals("toString"))return "CI rendered-first-frame observer";return null;});api.getMethod("addListener",listener).invoke(p,events);
    InfinityCastProbeActivity.check(((InfinityCastProbeActivity)context).outputSurface!=null && ((InfinityCastProbeActivity)context).outputSurface.isValid(),"actual_video_surface_valid");
    api.getMethod("setVideoSurface",android.view.Surface.class).invoke(p,((InfinityCastProbeActivity)context).outputSurface);api.getMethod("setVolume",float.class).invoke(p,0f);api.getMethod("setMediaItem",item).invoke(p,mb.getMethod("build").invoke(m));api.getMethod("prepare").invoke(p);api.getMethod("play").invoke(p);return p;
   }catch(Throwable failure){api.getMethod("release").invoke(p);throw failure;}
  });
  try {
   long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(18);boolean ready=false;
   while(System.nanoTime()<end){
    Object error=main(()->api.getMethod("getPlayerError").invoke(player));InfinityCastProbeActivity.check(error==null,"actual_HLS_receiver_compatible_player_error");
    if((Integer)main(()->api.getMethod("getPlaybackState").invoke(player))==3 && (Boolean)main(()->api.getMethod("isPlaying").invoke(player))){ready=true;break;}Thread.sleep(50);
   }
   InfinityCastProbeActivity.check(ready,"actual_HLS_player_ready_and_playing");long duration=(Long)main(()->api.getMethod("getDuration").invoke(player));InfinityCastProbeActivity.check(Math.abs(duration-expected)<200,"actual_zero_based_HLS_duration");
   int beforeRendered=count(player,"Audio"),beforeVideo=count(player,"Video");
   main(()->{api.getMethod("seekTo",long.class).invoke(player,2500L);return null;});
   long mapped=(Long)main(()->api.getMethod("getCurrentPosition").invoke(player));InfinityCastProbeActivity.check(Math.abs(mapped-2500)<200,"HLS_seek_target_mapping");long seekStarted=android.os.SystemClock.elapsedRealtime();
   end=System.nanoTime()+TimeUnit.SECONDS.toNanos(8);long position=0;boolean seek=false;
   int rendered=0,videoRendered=0;
   while(System.nanoTime()<end){
    Object error=main(()->api.getMethod("getPlayerError").invoke(player));InfinityCastProbeActivity.check(error==null,"actual_HLS_error_after_seek");
    position=(Long)main(()->api.getMethod("getCurrentPosition").invoke(player));rendered=count(player,"Audio");videoRendered=count(player,"Video");
    boolean playing=(Integer)main(()->api.getMethod("getPlaybackState").invoke(player))==3 && (Boolean)main(()->api.getMethod("isPlaying").invoke(player));
    evidence.put("video_rendered_frames_before_seek",beforeVideo).put("video_rendered_frames",videoRendered).put("rendered_first_frame_events",firstFrames.get()).put("audio_rendered_buffers_before_seek",beforeRendered).put("audio_rendered_buffers",rendered).put("duration_ms",duration).put("seek_mapped_ms",mapped).put("seek_elapsed_ms",android.os.SystemClock.elapsedRealtime()-seekStarted).put("seek_position_ms",position).put("isPlaying",playing);
    if(position>=2650 && position<duration-100 && position<=2500+(android.os.SystemClock.elapsedRealtime()-seekStarted)+500 && playing && rendered>beforeRendered && videoRendered>beforeVideo && firstFrames.get()>0){seek=true;break;}Thread.sleep(50);
   }
   InfinityCastProbeActivity.check(rendered>beforeRendered,"actual_AAC_audio_resumed_after_seek");InfinityCastProbeActivity.check(videoRendered>beforeVideo && firstFrames.get()>0,"actual_H264_video_rendered");InfinityCastProbeActivity.check(seek,"actual_zero_based_HLS_seek_position");
   return evidence.put("actual_Android_HLS_playback",true).put("player","immutable baseline Media3 APIs; CI package only, no Cobra entry point or production dependency");
  }finally{main(()->{api.getMethod("release").invoke(player);return null;});}
 }
}
