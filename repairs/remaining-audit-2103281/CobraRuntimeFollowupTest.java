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
public class CobraRuntimeFollowupTest {
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
 void assertDrawerSafe()throws Exception{
  JSONObject d=ui(()->{
   View hint=a.getWindow().getDecorView().findViewWithTag("cobra_player_channel_hint");assertNotNull(hint);assertTrue(hint.isShown());
   View decor=a.getWindow().getDecorView();WindowInsets insets=decor.getRootWindowInsets();assertNotNull(insets);
   android.graphics.Insets nav=insets.getInsetsIgnoringVisibility(WindowInsets.Type.navigationBars());int[] h=new int[2],root=new int[2];hint.getLocationInWindow(h);decor.getLocationInWindow(root);
   int safeBottom=root[1]+decor.getHeight()-nav.bottom;
   JSONObject result=new JSONObject().put("hint_top",h[1]).put("hint_bottom",h[1]+hint.getHeight()).put("safe_bottom",safeBottom).put("navigation_bottom",nav.bottom);
   assertTrue("Drawer hint must remain above navigation: "+result,h[1]+hint.getHeight()<=safeBottom);return result;
  });try(FileWriter f=new FileWriter(new File(out,"channels-drawer-insets.json"))){f.write(d.toString(2));}
 }
 EditText inputIn(View v){if(v instanceof EditText)return (EditText)v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){EditText edit=inputIn(((ViewGroup)v).getChildAt(i));if(edit!=null)return edit;}return null;}
 View described(View v,String text){if(text.contentEquals(v.getContentDescription()==null?"":v.getContentDescription()))return v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){View found=described(((ViewGroup)v).getChildAt(i),text);if(found!=null)return found;}return null;}
 void press(String label)throws Exception{runUi(()->{View v=described(a.getWindow().getDecorView(),label);assertNotNull("Control "+label,v);assertTrue("Control reachable "+label,v.isShown());assertTrue("Control callback "+label,v.performClick());});}
 void foreground()throws Exception{Intent i=new Intent(ins.getTargetContext(),InfinityLiveActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);ins.getTargetContext().startActivity(i);await("foreground",()->(Boolean)get(a,"mCobraRotationResumed")&&!a.isInPictureInPictureMode(),8000);}
 void shell(String command)throws Exception{try(ParcelFileDescriptor fd=ins.getUiAutomation().executeShellCommand(command);InputStream in=new ParcelFileDescriptor.AutoCloseInputStream(fd)){byte[] b=new byte[1024];while(in.read(b)!=-1){}}}
 void swipe(float x,float from,float to)throws Exception{long down=SystemClock.uptimeMillis();for(int i=0;i<=12;i++){int action=i==0?MotionEvent.ACTION_DOWN:i==12?MotionEvent.ACTION_UP:MotionEvent.ACTION_MOVE;MotionEvent e=MotionEvent.obtain(down,SystemClock.uptimeMillis(),action,x,from+(to-from)*i/12f,0);try{ins.sendPointerSync(e);}finally{e.recycle();}SystemClock.sleep(18);}}
