package com.projectinfinity.kodi;

import android.app.*;import android.content.*;import android.graphics.*;import android.os.*;import android.view.*;import android.widget.*;
import androidx.media3.common.Player;import androidx.media3.exoplayer.ExoPlayer;
import androidx.test.ext.junit.runners.AndroidJUnit4;import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.*;import org.junit.runner.RunWith;import org.json.*;
import java.io.*;import java.lang.reflect.*;import java.util.*;import java.util.concurrent.Callable;
import static org.junit.Assert.*;

/** Instrumentation against the exact signed product APK, actual MediaCodec/TextureView,
 * generated HTTP/M3U content, and Android lifecycle. No player mocks or app test hooks. */
@RunWith(AndroidJUnit4.class)
public class CobraRuntime279Test {
 final Instrumentation ins=InstrumentationRegistry.getInstrumentation();InfinityLiveActivity a;File out;
 final JSONArray results=new JSONArray();final List<String> errors=new ArrayList<>();
 interface Action {void run()throws Exception;}
 static Field field(Object o,String n)throws Exception{Class<?> c=o instanceof Class?(Class<?>)o:o.getClass();while(c!=null){try{Field f=c.getDeclaredField(n);f.setAccessible(true);return f;}catch(NoSuchFieldException e){c=c.getSuperclass();}}throw new NoSuchFieldException(n);}
 static Object get(Object o,String n)throws Exception{return field(o,n).get(o instanceof Class?null:o);}
 static void put(Object o,String n,Object v)throws Exception{field(o,n).set(o,v);}
 static Object call(Object o,String n,Object...args)throws Exception{Class<?> c=o.getClass();while(c!=null){for(Method m:c.getDeclaredMethods())if(m.getName().equals(n)&&m.getParameterTypes().length==args.length){m.setAccessible(true);try{return m.invoke(o,args);}catch(IllegalArgumentException mismatch){}}c=c.getSuperclass();}throw new NoSuchMethodException(n);}
 <T>T ui(Callable<T> c)throws Exception{final Object[] r=new Object[2];ins.runOnMainSync(()->{try{r[0]=c.call();}catch(Throwable e){r[1]=e;}});if(r[1]!=null)throw new Exception((Throwable)r[1]);return (T)r[0];}
 void runUi(Action c)throws Exception{ui(()->{c.run();return null;});}
 void await(String label,Callable<Boolean> condition,long ms)throws Exception{long end=SystemClock.uptimeMillis()+ms;while(SystemClock.uptimeMillis()<end){if(ui(condition))return;SystemClock.sleep(150);}throw new AssertionError("Timeout: "+label);}
 void check(String name,Action action){long start=SystemClock.elapsedRealtime();JSONObject record=new JSONObject();try{action.run();record.put("passed",true);}catch(Throwable e){errors.add(name+": "+e);try{record.put("passed",false).put("error",android.util.Log.getStackTraceString(e));}catch(Exception ignored){}}try{record.put("name",name).put("elapsed_ms",SystemClock.elapsedRealtime()-start);results.put(record);android.util.Log.i("CobraAudit279",record.toString());saveResults();}catch(Exception e){throw new RuntimeException(e);}}
 void saveResults()throws Exception{try(FileWriter w=new FileWriter(new File(out,"runtime-results.json"))){w.write(new JSONObject().put("kind","signed APK / real Android runtime / generated HTTP provider content").put("device",Build.MODEL).put("api",Build.VERSION.SDK_INT).put("tests",results).put("physical_fold",false).toString(2));}}
 void screenshot(String name)throws Exception{Bitmap b=ins.getUiAutomation().takeScreenshot();assertNotNull(b);try(FileOutputStream f=new FileOutputStream(new File(out,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,f);}finally{b.recycle();}}
 ExoPlayer player()throws Exception{return ui(()->(ExoPlayer)get(a,"mCobraPreviewPlayer"));}
 List<?> channels()throws Exception{return ui(()->new ArrayList<>((List<?>)get(a,"mChannels")));}
 Object channel(String name)throws Exception{for(Object c:channels())if(name.equals(get(c,"name")))return c;throw new AssertionError("Missing HTTP/M3U channel "+name);}
 void start(String name)throws Exception{Object c=channel(name);runUi(()->{call(a,"closeCobraActionSheet");if(get(a,"mMultiOverlay")!=null)call(a,"releaseMulti");if(get(a,"mPlayerOverlay")!=null)call(a,"closeFullscreenToCobraView");if(Boolean.TRUE.equals(get(a,"mCobraProActive"))){call(a,"cobraProSelectChannel",c,"FROM CHANNELS");call(a,"cobraProPreview");}else call(a,"startCobraPreview",c);});await("decoded "+name,()->{ExoPlayer p=(ExoPlayer)get(a,"mCobraPreviewPlayer");return p!=null&&p.getPlaybackState()==Player.STATE_READY&&p.getVideoSize().width>0&&p.isPlaying();},15000);runUi(()->((ExoPlayer)get(a,"mCobraPreviewPlayer")).setRepeatMode(Player.REPEAT_MODE_ALL));SystemClock.sleep(600);}
 void assertFilled(String name)throws Exception{Bitmap b=ui(()->{TextureView t=(TextureView)get(a,"mCobraPreviewTexture");assertTrue(t.isAvailable());return t.getBitmap(144,90);});assertNotNull(b);try{int black=0,total=0;for(int y=10;y<80;y++)for(int x:new int[]{1,2,141,142}){int c=b.getPixel(x,y);if(Color.red(c)<16&&Color.green(c)<16&&Color.blue(c)<16)black++;total++;}for(int x=8;x<136;x++)for(int y:new int[]{1,2,87,88}){int c=b.getPixel(x,y);if(Color.red(c)<16&&Color.green(c)<16&&Color.blue(c)<16)black++;total++;}try(FileOutputStream f=new FileOutputStream(new File(out,name+"-decoded.png"))){b.compress(Bitmap.CompressFormat.PNG,100,f);}assertTrue(name+" black edge fraction="+((float)black/total),black<total*.12f);}finally{b.recycle();}}
 View described(View v,String text){if(text.contentEquals(v.getContentDescription()==null?"":v.getContentDescription()))return v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){View found=described(((ViewGroup)v).getChildAt(i),text);if(found!=null)return found;}return null;}
 void press(String label)throws Exception{runUi(()->{View v=described(a.getWindow().getDecorView(),label);assertNotNull("Control "+label,v);assertTrue("Control reachable "+label,v.isShown());assertTrue("Control callback "+label,v.performClick());});}
 void foreground()throws Exception{Intent i=new Intent(ins.getTargetContext(),InfinityLiveActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);ins.getTargetContext().startActivity(i);await("foreground",()->(Boolean)get(a,"mCobraRotationResumed")&&!a.isInPictureInPictureMode(),8000);}
 void shell(String command)throws Exception{try(ParcelFileDescriptor fd=ins.getUiAutomation().executeShellCommand(command);InputStream in=new ParcelFileDescriptor.AutoCloseInputStream(fd)){byte[] b=new byte[1024];while(in.read(b)!=-1){}}}
 @Test public void fullRuntimeJourney()throws Exception{
  out=new File(ins.getTargetContext().getExternalFilesDir(null),"audit279");out.mkdirs();
  Context ctx=ins.getTargetContext();JSONObject source=new JSONObject().put("id","audit").put("type","m3u").put("name","Generated audit provider").put("playlist_url","http://10.0.2.2:8765/audit.m3u").put("epg_url","");
  ctx.getSharedPreferences("infinity_cobra_live",0).edit().clear().putString("sources_json",new JSONArray().put(source).put(new JSONObject().put("id","peek").put("type","m3u").put("name","Independent preview audit source").put("playlist_url","http://10.0.2.2:8765/peek.m3u").put("epg_url","" )).put(new JSONObject().put("id","vod").put("type","xtream").put("name","Generated VOD audit provider").put("server","http://10.0.2.2:8765").put("username","audit").put("password","audit")).toString()).putString("active_source","audit").putBoolean("cobra_live_rewind_enabled",false).putString("cobra_appearance_mode","dark").putString("cobra_ambient_mode","immersive").commit();
  Intent launch=new Intent(ctx,InfinityLiveActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);a=(InfinityLiveActivity)ins.startActivitySync(launch);
  check("Cobra launch and real HTTP M3U provider load",()->{await("provider channels",()->((List<?>)get(a,"mChannels")).size()>=5,20000);screenshot("01-live-launch");});
  for(String mode:new String[]{"mobile","grid","compact","cards","focus"})check("Decoded crop / "+mode,()->{
   runUi(()->{put(a,"mCobraGuideStyle",mode);call(a,"cobraShowGuideShell");});
   for(String clip:new String[]{"Wide","Classic","Portrait","Odd"}){start(clip);assertFilled(mode+"-"+clip);}
   screenshot("mode-"+mode);
  });
  runUi(()->{put(a,"mCobraGuideStyle","mobile");call(a,"cobraShowGuideShell");});
  check("Encoded black bars diagnostic",()->{start("Baked");SystemClock.sleep(1800);assertFilled("baked-bars");});
  check("Pause resume and fullscreen handoff preserve player",()->{
   start("Classic");ExoPlayer same=player();runUi(()->{View v=((View)get(a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_play_pause");assertNotNull(v);assertTrue(v.performClick());});assertFalse("Pause must clear requested playback",ui(same::getPlayWhenReady));long position=ui(same::getCurrentPosition);SystemClock.sleep(600);assertTrue(Math.abs(ui(same::getCurrentPosition)-position)<100);runUi(()->{View v=((View)get(a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_play_pause");assertNotNull(v);assertTrue(v.performClick());});assertTrue("Resume must request playback",ui(same::getPlayWhenReady));
   runUi(()->call(a,"promoteCobraPreviewToFullscreen",get(a,"mGuidePreviewChannel")));await("fullscreen first frame",()->get(a,"mPlayer")==same&&((TextureView)get(a,"mPlayerTexture")).isAvailable(),10000);screenshot("watch-fullscreen");
   for(String menu:new String[]{"Channels","Display","More"}){runUi(()->call(a,"showPlayerChromeTemporarily"));press(menu);SystemClock.sleep(250);screenshot(menu);runUi(()->{call(a,"closeCobraActionSheet");call(a,"closeCobraPlayerDrawer");});}
   runUi(()->call(a,"closeFullscreenToCobraView"));await("preview return",()->get(a,"mCobraPreviewPlayer")==same,8000);assertFilled("fullscreen-return");
  });
  check("Quick Peek uses real independent decoder and clean release",()->{
   start("Wide");ExoPlayer main=player();Object other=channel("Peek");runUi(()->call(a,"cobraShowQuickPeek",other,get(a,"mCobraPreviewHost")));
   // M3U capacity policy may intentionally deny another connection; expose that accurately.
   await("Quick Peek session",()->get(a,"mCobraQuickPeek")!=null,6000);Object session=ui(()->get(a,"mCobraQuickPeek"));await("Quick Peek decode",()->((ExoPlayer)get(session,"player")).getVideoSize().width>0&&Boolean.TRUE.equals(get(session,"firstFrame")),12000);screenshot("quick-peek");runUi(()->call(a,"closeCobraActionSheet"));assertSame(main,player());assertTrue("Quick Peek must preserve requested main playback",ui(main::getPlayWhenReady));
  });
  check("Multi-View 2/3/4 real decoders and fullscreen return",()->{
   runUi(()->{call(a,"closeCobraActionSheet");call(a,"promoteCobraPreviewToFullscreen",get(a,"mGuidePreviewChannel"));});
   List<Object> selected=new ArrayList<>();for(String n:new String[]{"Wide","Classic","Portrait","Odd"})selected.add(channel(n));
   runUi(()->call(a,"cobraSetMultiFillScreen",true));
   for(int count=2;count<=4;count++){final int c=count;runUi(()->call(a,"openMultiView",new ArrayList<>(selected.subList(0,c))));await("multi "+c,()->{ExoPlayer[] ps=(ExoPlayer[])get(a,"mMultiPlayers");if(ps==null||ps.length!=c)return false;for(ExoPlayer p:ps)if(p==null||p.getVideoSize().width==0||!p.isPlaying())return false;return true;},20000);screenshot("multi-"+c);}
   ExoPlayer[] prior=ui(()->((ExoPlayer[])get(a,"mMultiPlayers")).clone());String key=(String)get(selected.get(1),"id");runUi(()->call(a,"cobraPromoteMultiTileFullscreen",key));SystemClock.sleep(500);runUi(()->call(a,"cobraReturnToMultiFromFullscreen"));ExoPlayer[] after=ui(()->(ExoPlayer[])get(a,"mMultiPlayers"));assertArrayEquals(prior,after);runUi(()->call(a,"setMultiAudio",2));assertEquals(2,ui(()->get(a,"mAudioTile")));runUi(()->{call(a,"releaseMulti");call(a,"showCobraPrimaryView");});
  });
  check("Android PiP and foreground return preserve player",()->{
   start("Wide");ExoPlayer same=player();runUi(()->call(a,"promoteCobraPreviewToFullscreen",get(a,"mGuidePreviewChannel")));runUi(()->call(a,"enterCobraPictureInPicture"));await("actual PiP",a::isInPictureInPictureMode,8000);screenshot("pip");foreground();assertSame(same,ui(()->get(a,"mPlayer")));runUi(()->call(a,"closeFullscreenToCobraView"));assertSame(same,player());assertFilled("pip-return");
  });
  check("Actual Android background pause / audio / foreground",()->{
   start("Classic");ExoPlayer same=player();
   for(boolean enabled:new boolean[]{false,true}){
    runUi(()->((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_mini_background_playback",enabled).commit());
    shell("input keyevent KEYCODE_HOME");await("background",()->!Boolean.TRUE.equals(get(a,"mCobraRotationResumed")),8000);SystemClock.sleep(1300);
    assertSame(same,player());assertEquals("Requested background audio="+enabled,enabled,ui(same::getPlayWhenReady));
    foreground();await("foreground playback resumes",same::isPlaying,8000);assertSame(same,player());assertFilled("background-return-"+enabled);
   }
  });
  check("Android resize and both themes",()->{
   runUi(()->{call(a,"releaseMulti");if(get(a,"mPlayerOverlay")!=null)call(a,"closeFullscreenToCobraView");});start("Classic");
   for(String size:new String[]{"720x1280","1280x720","600x1000","1000x600"}){shell("wm size "+size);SystemClock.sleep(800);assertFilled("resize-"+size);screenshot("resize-"+size);}
   shell("wm size reset");SystemClock.sleep(1800);for(String theme:new String[]{"light","oled","dark"}){runUi(()->{((SharedPreferences)get(a,"mPrefs")).edit().putString("cobra_appearance_mode",theme).commit();call(a,"cobraApplyAppearanceSettings");});SystemClock.sleep(400);screenshot("theme-"+theme);}
  });
  check("Real-time TS rewind / live edge / interrupted provider recovery",()->{
   runUi(()->((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_live_rewind_enabled",true).commit());start("Rewind");
   Object session=ui(()->get(a,"mCobraTimeshiftSession"));assertNotNull("Live TS must create rewind history",session);
   await("real-time rewind history",()->Boolean.TRUE.equals(call(session,"ready")),40000);
   ExoPlayer same=player();runUi(()->call(a,"promoteCobraPreviewToFullscreen",get(a,"mGuidePreviewChannel")));runUi(()->call(a,"cobraRewindLive",10000L));
   await("rewind decoder",()->get(a,"mCobraTimeshiftPlayer")==same&&same.isCurrentMediaItemSeekable()&&same.getPlaybackState()==Player.STATE_READY,15000);assertSame(same,ui(()->get(a,"mPlayer")));screenshot("live-rewind");
   runUi(()->call(a,"cobraGoLive"));await("live edge plays",same::isPlaying,10000);
   int prior=((Number)ui(()->call(session,"reconnects"))).intValue();new java.net.URL("http://10.0.2.2:8765/audit-outage").openConnection().getInputStream().close();
   await("provider reconnect",()->((Number)call(session,"reconnects")).intValue()>prior,15000);
   await("recovered playback",()->same.getPlaybackState()==Player.STATE_READY&&same.getPlayWhenReady(),20000);assertSame(same,ui(()->get(a,"mPlayer")));screenshot("live-after-outage");
   runUi(()->{call(a,"closeFullscreenToCobraView");((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_live_rewind_enabled",false).commit();});start("Wide");
  });
  check("HTTP movie details / My List / playback / seek / subtitles / Smart Return",()->{
   runUi(()->{call(a,"cobraSelectDrawerOwner","MOVIES");call(a,"showCobraPrimaryView");});await("HTTP movie catalog",()->!((List<?>)get(a,"mCobraVodMoviesCatalog")).isEmpty(),12000);
   Object movie=ui(()->((List<?>)get(a,"mCobraVodMoviesCatalog")).get(0));runUi(()->call(a,"cobraShowVodDetails",movie));await("movie details",()->String.valueOf(get(a,"mCobraStageTitle")).contains("MOVIE DETAILS"),10000);screenshot("movie-details");
   runUi(()->call(a,"toggleWatchlist",movie));assertEquals(true,ui(()->call(a,"cobraVodWatchlistContains",movie)));runUi(()->call(a,"playMovie",movie));await("movie decoder",()->{ExoPlayer p=(ExoPlayer)get(a,"mPlayer");return p!=null&&p.getVideoSize().width>0&&p.getPlaybackState()==Player.STATE_READY;},15000);
   ExoPlayer p=ui(()->(ExoPlayer)get(a,"mPlayer"));runUi(()->{p.seekTo(14000);call(a,"cobraSetCaptionsEnabled",p,true);});await("movie seek",()->p.getCurrentPosition()>=14000,8000);assertEquals(true,ui(()->call(a,"cobraCaptionsRequested",p)));
   await("actual selected subtitle track",()->{for(androidx.media3.common.Tracks.Group g:p.getCurrentTracks().getGroups())if(g.getType()==androidx.media3.common.C.TRACK_TYPE_TEXT)for(int i=0;i<g.length;i++)if(g.isTrackSelected(i))return true;return false;},5000);screenshot("movie-captions");
   runUi(()->{call(a,"showTrackChooser");int group=0;boolean changed=false;for(androidx.media3.common.Tracks.Group g:p.getCurrentTracks().getGroups()){if(g.getType()==androidx.media3.common.C.TRACK_TYPE_AUDIO)for(int i=0;i<g.length;i++)if(g.isTrackSupported(i)&&!g.isTrackSelected(i)){View row=a.getWindow().getDecorView().findViewWithTag("cobra-track:"+group+":"+i);assertNotNull(row);assertTrue(row.performClick());changed=true;break;}group++;if(changed)break;}assertTrue("A second real audio track must be selectable",changed);});SystemClock.sleep(400);screenshot("audio-and-subtitles");runUi(()->call(a,"closeCobraActionSheet"));
   runUi(()->call(a,"closeFullscreenToCobraView"));assertEquals("movies",ui(()->call(a,"cobraDrawerOwner")));screenshot("movie-return");
  });
  check("Delayed movie metadata cannot replace a newer drawer destination",()->{
   runUi(()->{call(a,"cobraSelectDrawerOwner","MOVIES");call(a,"showCobraPrimaryView");});await("movie catalog",()->!((List<?>)get(a,"mCobraVodMoviesCatalog")).isEmpty(),12000);
   Object movie=ui(()->((List<?>)get(a,"mCobraVodMoviesCatalog")).get(0));runUi(()->call(a,"cobraShowVodDetails",movie));SystemClock.sleep(150);
   runUi(()->{call(a,"cobraSelectDrawerOwner","SHOWS");call(a,"showCobraPrimaryView");});SystemClock.sleep(2000);
   assertEquals("shows",ui(()->call(a,"cobraDrawerOwner")));assertFalse(String.valueOf(ui(()->get(a,"mCobraStageTitle"))).contains("MOVIE DETAILS"));screenshot("delayed-metadata-navigation");
  });
  check("HTTP show seasons / episode playback / return",()->{
   runUi(()->{call(a,"cobraSelectDrawerOwner","SHOWS");call(a,"showCobraPrimaryView");});await("HTTP show catalog",()->!((List<?>)get(a,"mCobraVodShowsCatalog")).isEmpty(),12000);
   Object show=ui(()->((List<?>)get(a,"mCobraVodShowsCatalog")).get(0));runUi(()->call(a,"openSeries",show));await("episode list",()->!((List<?>)get(a,"mEpisodeQueue")).isEmpty(),10000);screenshot("series-episodes");
   Object episode=ui(()->((List<?>)get(a,"mEpisodeQueue")).get(0));runUi(()->call(a,"cobraPlaySeriesEpisode",show,episode,new ArrayList<>((List<?>)get(a,"mEpisodeQueue"))));await("episode decoder",()->{ExoPlayer p=(ExoPlayer)get(a,"mPlayer");return p!=null&&p.getVideoSize().width>0;},15000);screenshot("episode-playing");runUi(()->call(a,"closeFullscreenToCobraView"));assertEquals("shows",ui(()->call(a,"cobraDrawerOwner")));
  });
  check("Drawer section memory and settings retain ownership",()->{
   for(String owner:new String[]{"MOVIES","SHOWS","RECORDINGS","MY LIST","SPORTS","TV"}){runUi(()->{call(a,"cobraSelectDrawerOwner",owner);call(a,"showCobraPrimaryView");});SystemClock.sleep(400);Object before=ui(()->call(a,"cobraDrawerOwner"));runUi(()->call(a,"showSettings"));SystemClock.sleep(200);runUi(()->call(a,"showCobraPrimaryView"));assertEquals(before,ui(()->call(a,"cobraDrawerOwner")));screenshot("section-"+owner.replace(' ','-'));}
  });
  check("Activity recreation preserves Movies and settings",()->{
   runUi(()->{call(a,"cobraSelectDrawerOwner","MOVIES");call(a,"showCobraPrimaryView");});SystemClock.sleep(500);
   InfinityLiveActivity old=a;runUi(old::recreate);
   await("recreated Cobra",()->{for(android.app.Activity current:androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(androidx.test.runner.lifecycle.Stage.RESUMED))if(current instanceof InfinityLiveActivity&&current!=old){a=(InfinityLiveActivity)current;return true;}return false;},15000);
   await("restored provider",()->((List<?>)get(a,"mChannels")).size()>=5,15000);assertEquals("movies",ui(()->call(a,"cobraDrawerOwner")));assertEquals("dark",ui(()->call(a,"cobraStoredAppearanceMode")));screenshot("recreated-movies");
  });
  saveResults();runUi(()->a.finish());assertTrue(errors.toString(),errors.isEmpty());
 }
}
