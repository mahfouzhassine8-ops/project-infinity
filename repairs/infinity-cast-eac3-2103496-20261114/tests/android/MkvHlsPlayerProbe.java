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
  if(failure.get()!=null)throw new Exception("HLS_UI_"+failure.get().getClass().getSimpleName());return value.get();
 }
 static JSONObject play(Context context,String url,long expected)throws Exception {
  final Class<?> api=Class.forName("androidx.media3.common.Player"),item=Class.forName("androidx.media3.common.MediaItem");
  final Object player=main(()->{
   Class<?> builder=Class.forName("androidx.media3.exoplayer.ExoPlayer$Builder");Object b=builder.getConstructor(Context.class).newInstance(context);Object p=builder.getMethod("build").invoke(b);
   try {
    Class<?> mb=Class.forName("androidx.media3.common.MediaItem$Builder");Object m=mb.getConstructor().newInstance();mb.getMethod("setUri",String.class).invoke(m,url);mb.getMethod("setMimeType",String.class).invoke(m,"application/x-mpegURL");
    api.getMethod("setVolume",float.class).invoke(p,0f);api.getMethod("setMediaItem",item).invoke(p,mb.getMethod("build").invoke(m));api.getMethod("prepare").invoke(p);api.getMethod("play").invoke(p);return p;
   }catch(Throwable failure){api.getMethod("release").invoke(p);throw failure;}
  });
  try {
   long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(18);boolean ready=false;
   while(System.nanoTime()<end){
    Object error=main(()->api.getMethod("getPlayerError").invoke(player));InfinityCastProbeActivity.check(error==null,"actual_HLS_receiver_compatible_player_error");
    if((Integer)main(()->api.getMethod("getPlaybackState").invoke(player))==3 && (Boolean)main(()->api.getMethod("isPlaying").invoke(player))){ready=true;break;}Thread.sleep(50);
   }
   InfinityCastProbeActivity.check(ready,"actual_HLS_player_ready_and_playing");long duration=(Long)main(()->api.getMethod("getDuration").invoke(player));InfinityCastProbeActivity.check(Math.abs(duration-expected)<200,"actual_zero_based_HLS_duration");
   main(()->{api.getMethod("seekTo",long.class).invoke(player,2500L);return null;});
   end=System.nanoTime()+TimeUnit.SECONDS.toNanos(8);long position=0;boolean seek=false;
   while(System.nanoTime()<end){position=(Long)main(()->api.getMethod("getCurrentPosition").invoke(player));if(position>=2300 && position<3500 && (Integer)main(()->api.getMethod("getPlaybackState").invoke(player))==3){seek=true;break;}Thread.sleep(50);}
   InfinityCastProbeActivity.check(seek,"actual_zero_based_HLS_seek_position");return new JSONObject().put("duration_ms",duration).put("seek_position_ms",position).put("actual_Android_HLS_playback",true).put("player","immutable baseline Media3 APIs; CI package only, no Cobra entry point or production dependency");
  }finally{main(()->{api.getMethod("release").invoke(player);return null;});}
 }
}
