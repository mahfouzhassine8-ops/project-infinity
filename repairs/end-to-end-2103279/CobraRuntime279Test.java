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
 long startupMs;final JSONArray results=new JSONArray();final List<String> errors=new ArrayList<>();
 interface Action {void run()throws Exception;}
 static Field field(Object o,String n)throws Exception{Class<?> c=o instanceof Class?(Class<?>)o:o.getClass();while(c!=null){try{Field f=c.getDeclaredField(n);f.setAccessible(true);return f;}catch(NoSuchFieldException e){c=c.getSuperclass();}}throw new NoSuchFieldException(n);}
 static Object get(Object o,String n)throws Exception{return field(o,n).get(o instanceof Class?null:o);}
 static void put(Object o,String n,Object v)throws Exception{field(o,n).set(o,v);}
 static Object call(Object o,String n,Object...args)throws Exception{Class<?> c=o.getClass();while(c!=null){for(Method m:c.getDeclaredMethods())if(m.getName().equals(n)&&m.getParameterTypes().length==args.length){m.setAccessible(true);try{return m.invoke(o,args);}catch(IllegalArgumentException mismatch){}}c=c.getSuperclass();}throw new NoSuchMethodException(n);}
 <T>T ui(Callable<T> c)throws Exception{final Object[] r=new Object[2];ins.runOnMainSync(()->{try{r[0]=c.call();}catch(Throwable e){r[1]=e;}});if(r[1]!=null)throw new Exception((Throwable)r[1]);return (T)r[0];}
 void runUi(Action c)throws Exception{ui(()->{c.run();return null;});}
 void await(String label,Callable<Boolean> condition,long ms)throws Exception{long end=SystemClock.uptimeMillis()+ms;while(SystemClock.uptimeMillis()<end){if(ui(condition))return;SystemClock.sleep(150);}throw new AssertionError("Timeout: "+label);}
 void check(String name,Action action){long start=SystemClock.elapsedRealtime();JSONObject record=new JSONObject();try{action.run();record.put("passed",true);}catch(Throwable e){errors.add(name+": "+e);try{screenshot("failure-"+name.replaceAll("[^A-Za-z0-9]+","-"));}catch(Exception ignored){}try{record.put("passed",false).put("error",android.util.Log.getStackTraceString(e));}catch(Exception ignored){}}try{Debug.MemoryInfo memory=new Debug.MemoryInfo();Debug.getMemoryInfo(memory);record.put("pss_kb",memory.getTotalPss()).put("java_heap_bytes",Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory()).put("native_heap_bytes",Debug.getNativeHeapAllocatedSize());record.put("name",name).put("elapsed_ms",SystemClock.elapsedRealtime()-start);results.put(record);android.util.Log.i("CobraAudit279",record.toString());saveResults();}catch(Exception e){throw new RuntimeException(e);}}
 void saveResults()throws Exception{try(FileWriter w=new FileWriter(new File(out,"runtime-results.json"))){w.write(new JSONObject().put("kind","signed APK / real Android runtime / generated HTTP provider content").put("device",Build.MODEL).put("api",Build.VERSION.SDK_INT).put("tests",results).put("physical_fold",false).put("cobra_activity_startup_ms",startupMs).toString(2));}}
 void screenshot(String name)throws Exception{Bitmap b=ins.getUiAutomation().takeScreenshot();assertNotNull(b);try(FileOutputStream f=new FileOutputStream(new File(out,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,f);}finally{b.recycle();}}
 ExoPlayer player()throws Exception{return ui(()->(ExoPlayer)get(a,"mCobraPreviewPlayer"));}
 List<?> channels()throws Exception{return ui(()->new ArrayList<>((List<?>)get(a,"mChannels")));}
 Object channel(String name)throws Exception{for(Object c:channels())if(name.equals(get(c,"name")))return c;throw new AssertionError("Missing HTTP/M3U channel "+name);}
 void start(String name)throws Exception{Object c=channel(name);runUi(()->{call(a,"closeCobraActionSheet");if(get(a,"mMultiOverlay")!=null)call(a,"releaseMulti");if(get(a,"mPlayerOverlay")!=null)call(a,"closeFullscreenToCobraView");if(Boolean.TRUE.equals(get(a,"mCobraProActive"))){call(a,"cobraProSelectChannel",c,"FROM CHANNELS");call(a,"cobraProPreview");}else call(a,"startCobraPreview",c);});await("decoded "+name,()->{ExoPlayer p=(ExoPlayer)get(a,"mCobraPreviewPlayer");return p!=null&&p.getPlaybackState()==Player.STATE_READY&&p.getVideoSize().width>0&&p.isPlaying();},15000);runUi(()->((ExoPlayer)get(a,"mCobraPreviewPlayer")).setRepeatMode(Player.REPEAT_MODE_ALL));SystemClock.sleep(600);}
 void assertFilled(String name)throws Exception{
  // Validate the composed display, not getBitmap(), which omits TextureView's transform.
  final Rect bounds=new Rect();JSONObject diagnostic=ui(()->{
   TextureView t=(TextureView)get(a,"mCobraPreviewTexture");assertTrue(t.isAvailable());assertTrue(t.getGlobalVisibleRect(bounds));
   float[] matrix=new float[9];t.getTransform(new Matrix()).getValues(matrix);JSONObject d=new JSONObject().put("bounds",bounds.toShortString()).put("matrix",Arrays.toString(matrix));
   Object binding=((Map<?,?>)get(a,"mCobraPlayerBindings")).get(get(a,"mCobraPreviewPlayer"));Object crop=get(binding,"embeddedCrop");
   for(String f:new String[]{"zoom","contentX","contentY","consistent","probes","active","failed"})d.put(f,get(crop,f));return d;
  });
  Bitmap screen=ins.getUiAutomation().takeScreenshot();assertNotNull(screen);
  try{
   try(FileOutputStream f=new FileOutputStream(new File(out,name+"-screen.png"))){screen.compress(Bitmap.CompressFormat.PNG,100,f);}
   assertTrue(bounds.left>=0&&bounds.top>=0&&bounds.right<=screen.getWidth()&&bounds.bottom<=screen.getHeight());
   int black=0,total=0;
   // Central edge segments avoid approved rounded corners and overlaid controls.
   for(int n=30;n<60;n++){int y=bounds.top+bounds.height()*n/100;for(int side:new int[]{2,97}){int x=bounds.left+bounds.width()*side/100;int c=screen.getPixel(x,y);if(Color.red(c)<16&&Color.green(c)<16&&Color.blue(c)<16)black++;total++;}}
   for(int n=35;n<65;n++){int x=bounds.left+bounds.width()*n/100;int y=bounds.top+Math.max(3,bounds.height()/30);int c=screen.getPixel(x,y);if(Color.red(c)<16&&Color.green(c)<16&&Color.blue(c)<16)black++;total++;}
   diagnostic.put("black_edge_fraction",(float)black/total);
   try(FileWriter f=new FileWriter(new File(out,name+"-surface.json"))){f.write(diagnostic.toString(2));}
   assertTrue(name+" visible black edge fraction="+((float)black/total)+" "+diagnostic,black<total*.12f);
  }finally{screen.recycle();}
 }
 void assertPeekDisplayed(Object session)throws Exception{
  await("Quick Peek live state is published",()->{TextView state=a.getWindow().getDecorView().findViewWithTag("cobra_quick_peek_state");return state!=null&&state.getText().toString().startsWith("Live preview");},4000);
  Rect bounds=ui(()->{Rect r=new Rect();assertTrue(((TextureView)get(session,"texture")).getGlobalVisibleRect(r));return r;});
  int white=0,black=0,total=0;long until=SystemClock.uptimeMillis()+4000;
  // A decoder first-frame callback precedes compositor presentation. Require
  // the fixture's light grid on the actual screen, not just decoder state.
  do{
   SystemClock.sleep(150);ins.waitForIdleSync();Bitmap screen=ins.getUiAutomation().takeScreenshot();white=black=total=0;
   try{
    for(int y=10;y<90;y+=4)for(int x=10;x<90;x+=4){int c=screen.getPixel(bounds.left+bounds.width()*x/100,bounds.top+bounds.height()*y/100);if(Color.red(c)>140&&Color.green(c)>140&&Color.blue(c)>140)white++;}
    for(int y=20;y<80;y+=2)for(int x:new int[]{2,97}){int c=screen.getPixel(bounds.left+bounds.width()*x/100,bounds.top+bounds.height()*y/100);if(Color.red(c)<16&&Color.green(c)<16&&Color.blue(c)<16)black++;total++;}
    try(FileOutputStream f=new FileOutputStream(new File(out,"quick-peek.png"))){screen.compress(Bitmap.CompressFormat.PNG,100,f);}
   }finally{screen.recycle();}
   if(white>3)break;
  }while(SystemClock.uptimeMillis()<until);
  JSONObject d=new JSONObject().put("bounds",bounds.toShortString()).put("visible_grid_pixels",white).put("black_edge_fraction",black/(float)total);
  try(FileWriter f=new FileWriter(new File(out,"quick-peek-display.json"))){f.write(d.toString(2));}
  assertTrue("Quick Peek must display decoded picture: "+d,white>3);assertTrue("Quick Peek must fill its visible edges: "+d,black<total*.12f);
 }
 EditText inputIn(View v){if(v instanceof EditText)return (EditText)v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){EditText edit=inputIn(((ViewGroup)v).getChildAt(i));if(edit!=null)return edit;}return null;}
 View described(View v,String text){if(text.contentEquals(v.getContentDescription()==null?"":v.getContentDescription()))return v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){View found=described(((ViewGroup)v).getChildAt(i),text);if(found!=null)return found;}return null;}
 void press(String label)throws Exception{runUi(()->{View v=described(a.getWindow().getDecorView(),label);assertNotNull("Control "+label,v);assertTrue("Control reachable "+label,v.isShown());assertTrue("Control callback "+label,v.performClick());});}
 void foreground()throws Exception{Intent i=new Intent(ins.getTargetContext(),InfinityLiveActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);ins.getTargetContext().startActivity(i);await("foreground",()->(Boolean)get(a,"mCobraRotationResumed")&&!a.isInPictureInPictureMode(),8000);}
 void shell(String command)throws Exception{try(ParcelFileDescriptor fd=ins.getUiAutomation().executeShellCommand(command);InputStream in=new ParcelFileDescriptor.AutoCloseInputStream(fd)){byte[] b=new byte[1024];while(in.read(b)!=-1){}}}
 void swipe(float x,float from,float to)throws Exception{long down=SystemClock.uptimeMillis();for(int i=0;i<=12;i++){int action=i==0?MotionEvent.ACTION_DOWN:i==12?MotionEvent.ACTION_UP:MotionEvent.ACTION_MOVE;MotionEvent e=MotionEvent.obtain(down,SystemClock.uptimeMillis(),action,x,from+(to-from)*i/12f,0);try{ins.sendPointerSync(e);}finally{e.recycle();}SystemClock.sleep(18);}}
 @Test public void fullRuntimeJourney()throws Exception{
  out=new File(ins.getTargetContext().getExternalFilesDir(null),"audit279");out.mkdirs();
  Context ctx=ins.getTargetContext();JSONObject source=new JSONObject().put("id","audit").put("type","m3u").put("name","Generated audit provider").put("playlist_url","http://10.0.2.2:8765/audit.m3u").put("epg_url","");
  ctx.getSharedPreferences("infinity_cobra_live",0).edit().clear().putString("sources_json",new JSONArray().put(source).put(new JSONObject().put("id","peek").put("type","m3u").put("name","Independent preview audit source").put("playlist_url","http://10.0.2.2:8765/peek.m3u").put("epg_url","" )).put(new JSONObject().put("id","vod").put("type","xtream").put("name","Generated VOD audit provider").put("server","http://10.0.2.2:8765").put("username","audit").put("password","audit")).toString()).putString("active_source","audit").putBoolean("cobra_live_rewind_enabled",false).putString("cobra_appearance_mode","dark").putString("cobra_ambient_mode","immersive").commit();
  Intent launch=new Intent(ctx,InfinityLiveActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);long launchAt=SystemClock.elapsedRealtime();a=(InfinityLiveActivity)ins.startActivitySync(launch);startupMs=SystemClock.elapsedRealtime()-launchAt;
  check("Cobra launch and real HTTP M3U provider load",()->{await("provider channels",()->((List<?>)get(a,"mChannels")).size()>=5,20000);screenshot("01-live-launch");});
  for(String mode:new String[]{"mobile","grid","compact","cards","focus"})check("Decoded crop / "+mode,()->{
   runUi(()->{put(a,"mCobraGuideStyle",mode);call(a,"cobraShowGuideShell");});
   for(String clip:new String[]{"Wide","Classic","Portrait","Odd"}){start(clip);assertFilled(mode+"-"+clip);}
   screenshot("mode-"+mode);
  });
  runUi(()->{put(a,"mCobraGuideStyle","mobile");call(a,"cobraShowGuideShell");});
  check("Encoded black bars diagnostic",()->{start("Baked");SystemClock.sleep(1800);assertFilled("baked-bars");});
  check("Pause resume and fullscreen handoff preserve player",()->{
   start("Classic");ExoPlayer same=player();
   JSONArray pauses=new JSONArray();
   for(int cycle=0;cycle<3;cycle++){
    runUi(()->{View v=((View)get(a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_play_pause");assertNotNull(v);assertTrue(v.performClick());});
    assertFalse("Pause must immediately clear requested playback",ui(same::getPlayWhenReady));
    long requestedPosition=ui(same::getCurrentPosition),pauseAt=SystemClock.elapsedRealtime();
    // setPlayWhenReady updates application state before the playback thread has
    // processed the command. A bounded message acknowledgement observes that
    // thread without mutating the player or weakening the stationary check.
    androidx.media3.exoplayer.PlayerMessage ack=ui(()->same.createMessage((type,payload)->{}).send());
    assertTrue("Playback thread must acknowledge pause",ack.blockUntilDelivered(2000));
    long position=ui(same::getCurrentPosition),ackMs=SystemClock.elapsedRealtime()-pauseAt;
    SystemClock.sleep(600);long end=ui(same::getCurrentPosition);
    JSONObject sample=new JSONObject().put("cycle",cycle).put("requested_position_ms",requestedPosition).put("acknowledged_position_ms",position).put("after_600_ms",end).put("ack_ms",ackMs).put("play_when_ready",ui(same::getPlayWhenReady)).put("is_playing",ui(same::isPlaying));
    pauses.put(sample);try(FileWriter f=new FileWriter(new File(out,"pause-acknowledgement.json"))){f.write(pauses.toString(2));}
    assertFalse("Pause remains requested",ui(same::getPlayWhenReady));assertFalse("Paused renderer cannot report playing",ui(same::isPlaying));
    assertTrue("Paused position must remain stationary: "+sample,Math.abs(end-position)<100);
    runUi(()->{View v=((View)get(a,"mCobraPreviewHost")).findViewWithTag("cobra_preview_play_pause");assertNotNull(v);assertTrue(v.performClick());});
    assertTrue("Resume must request playback",ui(same::getPlayWhenReady));await("resume advances position",()->same.isPlaying()&&same.getCurrentPosition()>end+200,5000);assertSame(same,player());
   }
   runUi(()->call(a,"promoteCobraPreviewToFullscreen",get(a,"mGuidePreviewChannel")));await("fullscreen first frame",()->get(a,"mPlayer")==same&&((TextureView)get(a,"mPlayerTexture")).isAvailable(),10000);screenshot("watch-fullscreen");
   for(String menu:new String[]{"Channels","Display","More"}){runUi(()->call(a,"showPlayerChromeTemporarily"));press(menu);await(menu+" is visible",()->{View panel=(View)get(a,menu.equals("Channels")?"mCobraPlayerDrawer":"mCobraSheetPanel");return panel!=null&&panel.isShown()&&panel.getAlpha()>.95f&&panel.getHeight()>20;},8000);SystemClock.sleep(300);screenshot(menu);runUi(()->{call(a,"closeCobraActionSheet");call(a,"closeCobraPlayerDrawer");});}
   runUi(()->call(a,"closeFullscreenToCobraView"));await("preview return",()->get(a,"mCobraPreviewPlayer")==same,8000);assertFilled("fullscreen-return");
  });
  check("Quick Peek uses real independent decoder and clean release",()->{
   start("Wide");ExoPlayer main=player();Object other=channel("Peek");runUi(()->call(a,"cobraShowQuickPeek",other,get(a,"mCobraPreviewHost")));
   // M3U capacity policy may intentionally deny another connection; expose that accurately.
   await("Quick Peek session",()->get(a,"mCobraQuickPeek")!=null,6000);Object session=ui(()->get(a,"mCobraQuickPeek"));await("Quick Peek decode",()->((ExoPlayer)get(session,"player")).getVideoSize().width>0&&Boolean.TRUE.equals(get(session,"firstFrame")),12000);assertPeekDisplayed(session);runUi(()->call(a,"closeCobraActionSheet"));assertSame(main,player());assertTrue("Quick Peek must preserve requested main playback",ui(main::getPlayWhenReady));
  });
  check("Multi-View 2/3/4 real decoders and fullscreen return",()->{
   runUi(()->{call(a,"closeCobraActionSheet");call(a,"promoteCobraPreviewToFullscreen",get(a,"mGuidePreviewChannel"));});
   List<Object> selected=new ArrayList<>();for(String n:new String[]{"Wide","Classic","Portrait","Odd"})selected.add(channel(n));
   runUi(()->call(a,"cobraSetMultiFillScreen",true));
   for(int count=2;count<=4;count++){final int c=count;runUi(()->call(a,"openMultiView",new ArrayList<>(selected.subList(0,c))));await("multi "+c,()->{ExoPlayer[] ps=(ExoPlayer[])get(a,"mMultiPlayers");if(ps==null||ps.length!=c)return false;for(ExoPlayer p:ps)if(p==null||p.getVideoSize().width==0||!p.isPlaying()||((Number)get(get(((Map<?,?>)get(a,"mCobraPlayerBindings")).get(p),"vitals"),"firstFrameAt")).longValue()<0)return false;return true;},20000);SystemClock.sleep(600);screenshot("multi-"+c);}
   ExoPlayer[] prior=ui(()->((ExoPlayer[])get(a,"mMultiPlayers")).clone());String key=(String)get(selected.get(1),"id");runUi(()->call(a,"cobraPromoteMultiTileFullscreen",key));SystemClock.sleep(500);runUi(()->call(a,"cobraReturnToMultiFromFullscreen"));ExoPlayer[] after=ui(()->(ExoPlayer[])get(a,"mMultiPlayers"));assertArrayEquals(prior,after);runUi(()->call(a,"setMultiAudio",2));assertEquals(2,ui(()->get(a,"mAudioTile")));
   Object replacement=channel("Baked");runUi(()->call(a,"replaceCobraMultiTileClean",3,replacement));await("replacement pane",()->{ExoPlayer[] ps=(ExoPlayer[])get(a,"mMultiPlayers");return ps.length==4&&ps[3].isPlaying()&&((Number)get(get(((Map<?,?>)get(a,"mCobraPlayerBindings")).get(ps[3]),"vitals"),"firstFrameAt")).longValue()>=0;},15000);
   ExoPlayer[] replaced=ui(()->(ExoPlayer[])get(a,"mMultiPlayers"));for(int i=0;i<3;i++)assertSame("Replacement preserves peer "+i,prior[i],replaced[i]);assertNotSame(prior[3],replaced[3]);SystemClock.sleep(600);screenshot("multi-replacement");runUi(()->{call(a,"releaseMulti");call(a,"showCobraPrimaryView");});
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
   for(String size:new String[]{"720x1280","1280x720","600x1000","1000x600"}){
    shell("wm size "+size);SystemClock.sleep(800);runUi(()->((View)get(a,"mCobraGuideShell")).scrollTo(0,0));SystemClock.sleep(300);assertFilled("resize-"+size);screenshot("resize-"+size);
    if(ui(()->((Number)call(get(a,"mCobraGuideShell"),"range")).intValue())>0){
     Rect bounds=ui(()->{Rect r=new Rect();((View)get(a,"mCobraGuideShell")).getGlobalVisibleRect(r);return r;});
     for(int i=0;i<4;i++)swipe(bounds.left+bounds.width()*.2f,bounds.top+bounds.height()*.85f,bounds.top+bounds.height()*.15f);
     await("short-window channel browser reachable",()->{View list=(View)get(a,"mCobraGuideList");Rect r=new Rect();return list!=null&&list.getGlobalVisibleRect(r)&&r.height()>=Math.min(90,bounds.height()/3);},5000);
     screenshot("short-window-browser-"+size);runUi(()->((View)get(a,"mCobraGuideShell")).scrollTo(0,0));
    }
   }
   shell("wm size reset");SystemClock.sleep(1800);for(String theme:new String[]{"light","oled","dark"}){runUi(()->{((SharedPreferences)get(a,"mPrefs")).edit().putString("cobra_appearance_mode",theme).commit();call(a,"cobraApplyAppearanceSettings");});SystemClock.sleep(400);assertEquals("System bar contrast "+theme,theme.equals("light"),ui(()->(a.getWindow().getDecorView().getSystemUiVisibility()&View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR)!=0));Bitmap screen=ins.getUiAutomation().takeScreenshot();try{int pixel=screen.getPixel(screen.getWidth()/2,Math.max(1,ui(()->((View)get(a,"mRoot")).getPaddingTop())/2));float luminance=.2126f*Color.red(pixel)+.7152f*Color.green(pixel)+.0722f*Color.blue(pixel);assertEquals("Visible status backdrop "+theme,theme.equals("light"),luminance>158);}finally{screen.recycle();}screenshot("theme-"+theme);}
  });
  check("Rapid channel switching and repeated mode changes release stale bindings",()->{
   List<Object> clips=new ArrayList<>();for(String n:new String[]{"Wide","Classic","Portrait","Odd","Baked"})clips.add(channel(n));
   for(int i=0;i<15;i++){final Object c=clips.get(i%clips.size());runUi(()->call(a,"startCobraPreview",c));SystemClock.sleep(90);}
   await("final rapid retune",()->{ExoPlayer p=(ExoPlayer)get(a,"mCobraPreviewPlayer");return p!=null&&p.isPlaying()&&p.getVideoSize().width>0;},15000);SystemClock.sleep(2200);assertFilled("rapid-final");
   ExoPlayer same=player();for(String mode:new String[]{"grid","compact","cards","focus","mobile","cards","mobile"}){
    runUi(()->call(a,"cobraSwitchMode",mode));SystemClock.sleep(250);
    if(mode.equals("focus")){
     // Approved Pro entry restores its saved hero in the resting state. That
     // intentional selection may retune; all peer bindings must still be released.
     Object saved=ui(()->call(a,"findChannel",((SharedPreferences)get(a,"mPrefs")).getString("cobra_pro_hero_channel","")));
     assertNotNull(saved);assertEquals(ui(()->call(a,"cobraChannelKey",saved)),ui(()->get(a,"mCobraPreviewSessionKey")));
     assertFalse("Pro keeps its approved resting entry",ui(()->((ExoPlayer)get(a,"mCobraPreviewPlayer")).getPlayWhenReady()));same=player();
    }else assertSame("Unchanged preview owner in "+mode,same,player());
    assertEquals("No stale bindings in "+mode,1,ui(()->((Map<?,?>)get(a,"mCobraPlayerBindings")).size()).intValue());
   }
   assertEquals("Only the active player may retain a binding",1,ui(()->((Map<?,?>)get(a,"mCobraPlayerBindings")).size()).intValue());
   assertFilled("rapid-modes-final");
  });
  check("Favorites / Recents / Search produce real results without interrupting playback",()->{
   start("Wide");ExoPlayer same=player();Object selected=channel("Wide");String id=String.valueOf(get(selected,"id"));
   runUi(()->{View favorite=a.getWindow().getDecorView().findViewWithTag("cobra_preview_favorite");assertNotNull(favorite);favorite.performClick();});assertTrue(ui(()->((Set<?>)get(a,"mFavorites")).contains(id)));
   runUi(()->call(a,"selectCobraCategory","FAVORITES"));await("favorite result",()->((android.widget.BaseAdapter)get(a,"mCobraGuideAdapter")).getCount()==1,8000);
   assertTrue(ui(()->((List<?>)get(a,"mRecents")).contains(id)));runUi(()->call(a,"selectCobraCategory","RECENT"));assertTrue(ui(()->((android.widget.BaseAdapter)get(a,"mCobraGuideAdapter")).getCount()>0));
   runUi(()->{call(a,"cobraShowChannelSearch");EditText input=inputIn((View)get(a,"mCobraActionSheet"));assertNotNull(input);input.setText("Classic");});
   runUi(()->{View row=described((View)get(a,"mCobraActionSheet"),"Search");assertNotNull(row);assertTrue(row.performClick());});
   await("filtered search result",()->{android.widget.BaseAdapter adapter=(android.widget.BaseAdapter)get(a,"mCobraGuideAdapter");return adapter.getCount()==1&&String.valueOf(get(adapter.getItem(0),"name")).equals("Classic");},8000);assertSame(same,player());assertTrue(ui(same::isPlaying));screenshot("favorite-recent-search");
   runUi(()->{put(a,"mSearch","");call(a,"selectCobraCategory","ALL");});
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
   await("direct movie Watch ambient",()->{Object engine=get(a,"mCobraImmersiveAmbient");return engine!=null&&Boolean.TRUE.equals(call(engine,"isAmbientActive"))&&((Number)get(engine,"captures")).intValue()>0;},8000);
   ExoPlayer p=ui(()->(ExoPlayer)get(a,"mPlayer"));runUi(()->{call(a,"showPlayerChromeTemporarily");call(a,"cobraSetCaptionsEnabled",p,true);});
   await("movie timeline visible",()->{View seek=(View)get(a,"mCobraTimeshiftSeek");return seek!=null&&seek.isShown()&&seek.getWidth()>50;},8000);
   Rect seekBounds=ui(()->{Rect r=new Rect();((View)get(a,"mCobraTimeshiftSeek")).getGlobalVisibleRect(r);return r;});long down=SystemClock.uptimeMillis();
   for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_MOVE,MotionEvent.ACTION_UP}){MotionEvent e=MotionEvent.obtain(down,SystemClock.uptimeMillis(),action,seekBounds.left+seekBounds.width()*.4f,seekBounds.exactCenterY(),0);try{ins.sendPointerSync(e);}finally{e.recycle();}SystemClock.sleep(60);}
   await("movie touch seek",()->p.getCurrentPosition()>60000&&p.getCurrentPosition()<90000,8000);
   press("Rewind 30 seconds");await("movie rewind control",()->p.getCurrentPosition()<55000,8000);press("Forward 30 seconds");await("movie forward control",()->p.getCurrentPosition()>60000,8000);assertEquals(true,ui(()->call(a,"cobraCaptionsRequested",p)));
   await("actual selected subtitle track",()->{for(androidx.media3.common.Tracks.Group g:p.getCurrentTracks().getGroups())if(g.getType()==androidx.media3.common.C.TRACK_TYPE_TEXT)for(int i=0;i<g.length;i++)if(g.isTrackSelected(i))return true;return false;},5000);await("rendered subtitle cue",()->{Object binding=((Map<?,?>)get(a,"mCobraPlayerBindings")).get(p);return !((List<?>)get(get(binding,"captions"),"cues")).isEmpty();},8000);SystemClock.sleep(2500);runUi(()->call(a,"showPlayerChromeTemporarily"));SystemClock.sleep(300);
   await("visible Watch illumination after controls return",()->{Object engine=get(a,"mCobraImmersiveAmbient");return engine!=null&&Boolean.TRUE.equals(call(engine,"isAmbientActive"))&&((View)engine).getAlpha()>.95f&&get(engine,"watchPalette")!=null&&((List<?>)get(engine,"glass")).size()>0;},3000);
   JSONObject watch=ui(()->{Object engine=get(a,"mCobraImmersiveAmbient");View control=described((View)get(a,"mPlayerChrome"),"Channels");JSONObject d=new JSONObject().put("alpha",((View)engine).getAlpha()).put("background",control.getBackground().getClass().getName());for(String field:new String[]{"enabled","haveFrame","captures","captureFailed","controlsOnly","sourceRect"})d.put(field,String.valueOf(get(engine,field)));d.put("glass_count",((List<?>)get(engine,"glass")).size());for(String key:new String[]{"raw","smoothed","watchPalette"}){Bitmap b=(Bitmap)get(engine,key);d.put(key,b==null?"null":String.format(java.util.Locale.US,"%08x",b.getPixel(b.getWidth()/2,b.getHeight()/2)));}return d;});try(FileWriter f=new FileWriter(new File(out,"movie-watch-ambient.json"))){f.write(watch.toString(2));}
   screenshot("movie-captions");
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
