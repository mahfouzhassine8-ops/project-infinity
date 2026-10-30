package qa;

import android.app.UiAutomation;
import android.graphics.Bitmap;
import android.graphics.Rect;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.InputDevice;
import android.view.MotionEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.*;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.regex.Pattern;
import org.json.*;

/** QA shell main, existing OS UiAutomation wrapper, one persistent connection.
 * No app classes, callbacks, private storage, compatibility setting or lifecycle
 * operations. The only player target is Cards FULLSCREEN More. */
public final class CobraFoldMoreDriver {
 static final String PKG="com.projectinfinity.kodi";
 static final long PLAYER_PRESS_LIMIT=3500;
 static UiAutomation ui;static File dir;static JSONArray steps=new JSONArray();static int sequence;
 static void require(boolean b,String why){if(!b)throw new IllegalStateException(why);}
 static String hash(byte[] raw)throws Exception{byte[] b=MessageDigest.getInstance("SHA-256").digest(raw);StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format(Locale.US,"%02x",v));return s.toString();}
 static JSONArray box(Rect r){return new JSONArray().put(r.left).put(r.top).put(r.right).put(r.bottom);}
 static void write(String name,JSONObject value)throws Exception{try(FileOutputStream out=new FileOutputStream(new File(dir,name))){out.write((value.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));}}
 static String text(AccessibilityNodeInfo n){CharSequence t=n.getText(),d=n.getContentDescription();return (t==null?"":t.toString())+"\n"+(d==null?"":d.toString());}
 static final class Tree {
  final long started=SystemClock.uptimeMillis();final AccessibilityNodeInfo root;final ArrayList<AccessibilityNodeInfo> nodes=new ArrayList<>();
  Tree(){root=ui.getRootInActiveWindow();if(root==null)return;require(PKG.contentEquals(root.getPackageName()),"Unexpected active package");nodes.add(root);for(int i=0;i<nodes.size();i++){require(nodes.size()<1600,"Bounded public UI tree exceeded");AccessibilityNodeInfo n=nodes.get(i);for(int c=0;c<n.getChildCount();c++){AccessibilityNodeInfo child=n.getChild(c);if(child!=null)nodes.add(child);}}}
  AccessibilityNodeInfo find(String regex,boolean clickable){Pattern p=Pattern.compile(regex,Pattern.CASE_INSENSITIVE);for(AccessibilityNodeInfo n:nodes){Rect r=new Rect();n.getBoundsInScreen(r);if(n.isVisibleToUser()&&n.isEnabled()&&(!clickable||n.isClickable())&&r.width()>12&&r.height()>12&&p.matcher(text(n)).find())return n;}return null;}
  JSONArray labels()throws Exception{JSONArray a=new JSONArray();for(AccessibilityNodeInfo n:nodes){String t=text(n).trim();if(!t.isEmpty())a.put(new JSONObject().put("label",t).put("visible",n.isVisibleToUser()).put("class",String.valueOf(n.getClassName())).put("resource_id",String.valueOf(n.getViewIdResourceName())).put("clickable",n.isClickable()).put("enabled",n.isEnabled()));}return a;}
  void close(){for(AccessibilityNodeInfo n:nodes)n.recycle();}
 }
 static void screenshot(String name)throws Exception{Bitmap b=ui.takeScreenshot();require(b!=null,"Native screenshot unavailable");try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){require(b.compress(Bitmap.CompressFormat.PNG,100,out),"Screenshot failed");}finally{b.recycle();}}
 static Rect waitBounds(String pattern,long budget)throws Exception{
  long started=SystemClock.uptimeMillis();JSONArray observations=new JSONArray();
  for(int i=0;i<20&&SystemClock.uptimeMillis()-started<budget;i++){
   Tree t=new Tree();try{AccessibilityNodeInfo n=t.find(pattern,true);if(n!=null){Rect r=new Rect();n.getBoundsInScreen(r);steps.put(new JSONObject().put("observed",pattern).put("bounds",box(r)).put("root_query_ms",SystemClock.uptimeMillis()-t.started));return r;}observations=t.labels();}finally{t.close();}SystemClock.sleep(150);
  }write("missing-target.json",new JSONObject().put("pattern",pattern).put("labels",observations));throw new IllegalStateException("Current public target not observed: "+pattern);
 }
 static void tap(Rect r,String purpose)throws Exception{long stamp=SystemClock.uptimeMillis();MotionEvent d=MotionEvent.obtain(stamp,stamp,MotionEvent.ACTION_DOWN,r.exactCenterX(),r.exactCenterY(),0);MotionEvent u=MotionEvent.obtain(stamp,stamp+32,MotionEvent.ACTION_UP,r.exactCenterX(),r.exactCenterY(),0);d.setSource(InputDevice.SOURCE_TOUCHSCREEN);u.setSource(InputDevice.SOURCE_TOUCHSCREEN);boolean down=false,up=false;try{down=ui.injectInputEvent(d,true);SystemClock.sleep(32);up=ui.injectInputEvent(u,true);}finally{d.recycle();u.recycle();steps.put(new JSONObject().put("coordinate_press",purpose).put("bounds",box(r)).put("down_injected",down).put("up_injected",up));}require(down&&up,"Input outcome uncertain; no retry");}
 static void tap(String pattern)throws Exception{tap(waitBounds(pattern,12000),pattern);}
 static boolean has(String pattern)throws Exception{Tree t=new Tree();try{return t.find(pattern,false)!=null;}finally{t.close();}}
 static void back()throws Exception{long t=SystemClock.uptimeMillis();for(int action:new int[]{android.view.KeyEvent.ACTION_DOWN,android.view.KeyEvent.ACTION_UP})require(ui.injectInputEvent(new android.view.KeyEvent(t,t+32,action,android.view.KeyEvent.KEYCODE_BACK,0),true),"Back injection failed");steps.put(new JSONObject().put("input","Back"));}
 static void nativeList(String pattern)throws Exception{
  long start=SystemClock.uptimeMillis();for(int i=0;i<16&&SystemClock.uptimeMillis()-start<12000;i++){
   Tree t=new Tree();try{AccessibilityNodeInfo n=t.find(pattern,false);boolean list=false;for(AccessibilityNodeInfo v:t.nodes)list|="android:id/select_dialog_listview".equals(v.getViewIdResourceName())&&v.isVisibleToUser();
    if(n!=null&&list&&"android:id/text1".equals(n.getViewIdResourceName())&&"android.widget.TextView".contentEquals(n.getClassName())){Rect r=new Rect();n.getBoundsInScreen(r);tap(r,"Original Android dialog item "+pattern);return;}
   }finally{t.close();}SystemClock.sleep(150);
  }throw new IllegalStateException("Original native dialog item not observed");
 }
 static void enterSource()throws Exception{
  tap("(?m)^\\+?\\s*ADD TV SOURCE$");nativeList("(?m)^M3U / M3U8 playlist$");
  String[] values={"CobraFoldMoreQA","http://10.0.2.2:8765/fold-more.m3u","http://10.0.2.2:8765/cards-epg.xml"};
  for(int index=0;index<3;index++){
   Tree t=new Tree();try{ArrayList<AccessibilityNodeInfo> fields=new ArrayList<>();for(AccessibilityNodeInfo n:t.nodes)if("android.widget.EditText".contentEquals(n.getClassName())&&n.isVisibleToUser())fields.add(n);require(fields.size()==3,"Original M3U form must expose three fields");Bundle a=new Bundle();a.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,values[index]);require(fields.get(index).performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,a),"Public input text failed");steps.put(new JSONObject().put("normal_source_form_field",index));}finally{t.close();}
  }tap("(?m)^TEST & SAVE$");
  for(int i=0;i<24;i++){if(has("(?m)^Return to preview$")){back();break;}if(has("Cards QA 00001"))break;SystemClock.sleep(250);}
  tap("(?m)^Choose one of five view modes$|^Choose view mode$|^Views$");tap("(?m)^Cards(?:,.*)?$");
  require(has("(?m)^CARDS.*"),"Cards public heading not observed");require(!has("(?m)^Previous Pro source$"),"Pro is not the target");screenshot("cards-before-fullscreen");
 }
 static Rect preview()throws Exception{Tree t=new Tree();try{for(AccessibilityNodeInfo n:t.nodes)if("android.view.TextureView".contentEquals(n.getClassName())&&n.isVisibleToUser()){Rect r=new Rect();n.getBoundsInScreen(r);if(r.width()>120&&r.height()>100)return r;}throw new IllegalStateException("Current Cards video texture not observed");}finally{t.close();}}
 static void fullscreen()throws Exception{
  if(has("(?m)^Return to preview$"))return;
  // Cards uses its original preview's real visible coordinate, never a callback.
  Rect r=preview();tap(r,"Current Cards preview");
  if(has("(?m)^Return to preview$"))return;
  long started=SystemClock.uptimeMillis();Rect full=waitBounds("(?m)^Fullscreen$",PLAYER_PRESS_LIMIT);
  require(SystemClock.uptimeMillis()-started<PLAYER_PRESS_LIMIT,"Inline target observation expired; no press");tap(full,"Cards inline Fullscreen");require(SystemClock.uptimeMillis()-started<PLAYER_PRESS_LIMIT,"Inline press completed after valid interval");
  require(has("(?m)^Return to preview$"),"Fullscreen destination not observed");
 }
 static void more(int iteration)throws Exception{
  require(has("(?m)^Channels$")&&has("(?m)^Display$"),"Actual fullscreen bottom strip required");
  // Observe the actual original hide transition, then renew it through a real
  // background tap. This avoids guessing how much of its 4-second life is left.
  long hiddenStart=SystemClock.uptimeMillis();boolean hidden=iteration>1;
  for(int i=0;!hidden&&i<16&&SystemClock.uptimeMillis()-hiddenStart<10000;i++){if(!has("(?m)^More$")){hidden=true;break;}SystemClock.sleep(250);}require(hidden,"Original fullscreen chrome did not hide within observation limit");
  Bitmap display=ui.takeScreenshot();require(display!=null,"Display bounds unavailable");int w=display.getWidth(),h=display.getHeight();display.recycle();
  Rect reveal=new Rect(w/2-2,h/4-2,w/2+2,h/4+2);long changed=SystemClock.uptimeMillis();if(iteration==1)tap(reveal,"Reveal existing fullscreen chrome");
  Rect first=waitBounds("(?m)^More$",PLAYER_PRESS_LIMIT);Rect second=waitBounds("(?m)^More$",PLAYER_PRESS_LIMIT);
  require(first.equals(second),"Fullscreen More changed bounds; no press");require(SystemClock.uptimeMillis()-changed<PLAYER_PRESS_LIMIT,"Fresh fullscreen More exceeded3.5-second visibility interval; no press");
  tap(second,"Cards FULLSCREEN More "+iteration);require(SystemClock.uptimeMillis()-changed<PLAYER_PRESS_LIMIT,"More injection uncertain after visibility deadline; no retry");
  long tapped=SystemClock.uptimeMillis();SystemClock.sleep(250);screenshot("fullscreen-more-"+iteration+"-250ms");
  Tree after=new Tree();try{write("fullscreen-more-"+iteration+"-nodes.json",new JSONObject().put("labels",after.labels()).put("elapsed_after_press_ms",SystemClock.uptimeMillis()-tapped));require(after.find("(?m)^Player settings$",false)!=null,"Original fullscreen More menu heading not visible");require(after.find("(?m)^Channel playback$",false)!=null&&after.find("(?m)^Health Center$",false)!=null,"Original More menu actions not visible");}finally{after.close();}
  SystemClock.sleep(300);screenshot("fullscreen-more-"+iteration+"-settled");back();require(!has("(?m)^Player settings$"),"Back did not close original menu");
 }
 public static void main(String[] args)throws Exception{
  require(args.length==2,"QA output path and exact JAR digest required");require(args[0].matches("/sdcard/cobra-fold-more-[0-9]+"),"Unsafe public QA output path");dir=new File(args[0]);require(!dir.exists()&&dir.mkdir(),"Fresh public output directory required");
  JSONObject report=new JSONObject().put("scope","EXACT_SIGNED433_CARDS_FULLSCREEN_MORE_ONLY").put("steps",steps).put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN").put("application_classpath",System.getProperty("java.class.path")).put("BOOTCLASSPATH","INHERITED_UNCHANGED");Object wrapper=null;Method disconnect=null;
  try{
   File jar=new File("/data/local/tmp/CobraFoldMoreDriver.jar");try(FileInputStream in=new FileInputStream(jar);ByteArrayOutputStream bytes=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)bytes.write(b,0,n);require(hash(bytes.toByteArray()).equals(args[1]),"QA JAR differs from compiled receipt");}
   require(System.getProperty("java.class.path").equals("/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:"+jar),"Original OS wrapper application classpath required");
   Class<?> c=Class.forName("com.android.uiautomator.core.UiAutomationShellWrapper");wrapper=c.getConstructor().newInstance();c.getMethod("connect").invoke(wrapper);disconnect=c.getMethod("disconnect");c.getMethod("setCompressedLayoutHierarchy",boolean.class).invoke(wrapper,true);ui=(UiAutomation)c.getMethod("getUiAutomation").invoke(wrapper);
   android.accessibilityservice.AccessibilityServiceInfo info=ui.getServiceInfo();info.flags|=android.accessibilityservice.AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;ui.setServiceInfo(info);
   enterSource();fullscreen();more(1);more(2);report.put("status","SIGNED433_BASELINE_MORE_REPRODUCED_AS_WORKING; NOT_A_FIX_CLAIM");
  }catch(Throwable e){report.put("status","FAILED_CLOSED").put("error",e.toString());if(ui!=null)try{screenshot("failure");}catch(Throwable ignored){}if(e instanceof Exception)throw (Exception)e;throw (Error)e;}
  finally{write("OUTCOME.json",report);if(disconnect!=null)disconnect.invoke(wrapper);}
 }
}
