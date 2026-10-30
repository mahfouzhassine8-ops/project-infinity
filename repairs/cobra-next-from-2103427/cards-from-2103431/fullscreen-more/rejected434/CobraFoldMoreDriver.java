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
 * operations. Targets are Cards original sun menu, fullscreen entry and FULLSCREEN More. */
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
  JSONArray labels()throws Exception{JSONArray a=new JSONArray();for(AccessibilityNodeInfo n:nodes){String t=text(n).trim();if(!t.isEmpty())a.put(new JSONObject().put("label",t).put("visible",n.isVisibleToUser()).put("class",String.valueOf(n.getClassName())).put("resource_id",String.valueOf(n.getViewIdResourceName())).put("clickable",n.isClickable()).put("enabled",n.isEnabled()).put("selected",n.isSelected()).put("bounds",nodeBox(n)));}return a;}
  void close(){for(AccessibilityNodeInfo n:nodes)n.recycle();}
 }
 static JSONArray nodeBox(AccessibilityNodeInfo n){Rect r=new Rect();n.getBoundsInScreen(r);return box(r);}
 static void syncInputs()throws Exception{
  Method method=UiAutomation.class.getMethod("syncInputTransactions",boolean.class);require(java.lang.reflect.Modifier.isPublic(method.getModifiers()),"Public OS input synchronizer required");long started=SystemClock.uptimeMillis();method.invoke(ui,true);steps.put(new JSONObject().put("OS_window_input_sync_ms",SystemClock.uptimeMillis()-started));
 }
 static void await(String pattern,boolean present)throws Exception{
  long started=SystemClock.uptimeMillis();for(int i=0;i<40&&SystemClock.uptimeMillis()-started<12000;i++){if(has(pattern)==present)return;SystemClock.sleep(100);}throw new IllegalStateException("Expected current UI state not observed: "+pattern+" present="+present);
 }
 static void awaitForm()throws Exception{
  syncInputs();long started=SystemClock.uptimeMillis();JSONArray last=new JSONArray();for(int i=0;i<40&&SystemClock.uptimeMillis()-started<12000;i++){Tree t=new Tree();try{int fields=0;for(AccessibilityNodeInfo n:t.nodes)if("android.widget.EditText".contentEquals(n.getClassName())&&n.isVisibleToUser())fields++;if(fields==3)return;last=t.labels();}finally{t.close();}SystemClock.sleep(100);}write("form-readiness.json",new JSONObject().put("labels",last));throw new IllegalStateException("Native three-field source form was not ready");
 }
 static void screenshot(String name)throws Exception{Bitmap b=ui.takeScreenshot();require(b!=null,"Native screenshot unavailable");try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){require(b.compress(Bitmap.CompressFormat.PNG,100,out),"Screenshot failed");}finally{b.recycle();}}
 static Rect waitBounds(String pattern,long budget)throws Exception{
  long started=SystemClock.uptimeMillis();JSONArray observations=new JSONArray();
  for(int i=0;i<20&&SystemClock.uptimeMillis()-started<budget;i++){
   Tree t=new Tree();try{AccessibilityNodeInfo n=t.find(pattern,true);if(n!=null){Rect r=new Rect();n.getBoundsInScreen(r);steps.put(new JSONObject().put("observed",pattern).put("bounds",box(r)).put("root_query_ms",SystemClock.uptimeMillis()-t.started));return r;}observations=t.labels();}finally{t.close();}SystemClock.sleep(150);
  }write("missing-target.json",new JSONObject().put("pattern",pattern).put("labels",observations));throw new IllegalStateException("Current public target not observed: "+pattern);
 }
 static void tap(Rect r,String purpose)throws Exception{long stamp=SystemClock.uptimeMillis();MotionEvent d=MotionEvent.obtain(stamp,stamp,MotionEvent.ACTION_DOWN,r.exactCenterX(),r.exactCenterY(),0);MotionEvent u=MotionEvent.obtain(stamp,stamp+32,MotionEvent.ACTION_UP,r.exactCenterX(),r.exactCenterY(),0);d.setSource(InputDevice.SOURCE_TOUCHSCREEN);u.setSource(InputDevice.SOURCE_TOUCHSCREEN);boolean down=false,up=false;try{down=ui.injectInputEvent(d,true);SystemClock.sleep(32);up=ui.injectInputEvent(u,true);}finally{d.recycle();u.recycle();steps.put(new JSONObject().put("coordinate_press",purpose).put("bounds",box(r)).put("down_injected",down).put("up_injected",up));}require(down&&up,"Input outcome uncertain; no retry");}
 static void tap(String pattern)throws Exception{
  syncInputs();Rect first=waitBounds(pattern,12000);SystemClock.sleep(32);Rect second=waitBounds(pattern,12000);require(first.equals(second),"Setup target moved; no press");tap(second,pattern);syncInputs();
 }
 static boolean has(String pattern)throws Exception{Tree t=new Tree();try{return t.find(pattern,false)!=null;}finally{t.close();}}
 static void back()throws Exception{long t=SystemClock.uptimeMillis();for(int action:new int[]{android.view.KeyEvent.ACTION_DOWN,android.view.KeyEvent.ACTION_UP})require(ui.injectInputEvent(new android.view.KeyEvent(t,t+32,action,android.view.KeyEvent.KEYCODE_BACK,0),true),"Back injection failed");steps.put(new JSONObject().put("input","Back"));}
 static void nativeList(String pattern)throws Exception{
  syncInputs();long start=SystemClock.uptimeMillis();for(int i=0;i<16&&SystemClock.uptimeMillis()-start<12000;i++){
   Tree t=new Tree();try{AccessibilityNodeInfo n=t.find(pattern,false);boolean list=false;for(AccessibilityNodeInfo v:t.nodes)list|="android:id/select_dialog_listview".equals(v.getViewIdResourceName())&&v.isVisibleToUser();
    if(n!=null&&list&&"android:id/text1".equals(n.getViewIdResourceName())&&"android.widget.TextView".contentEquals(n.getClassName())){Rect r=new Rect();n.getBoundsInScreen(r);tap(r,"Original Android dialog item "+pattern);syncInputs();return;}
   }finally{t.close();}SystemClock.sleep(150);
  }throw new IllegalStateException("Original native dialog item not observed");
 }
 static void scrollVisibleSheet()throws Exception{
  syncInputs();Tree tree=new Tree();Rect r=null;
  try{int matches=0;for(AccessibilityNodeInfo n:tree.nodes)if(n.isVisibleToUser()&&n.isScrollable()&&"android.widget.ScrollView".contentEquals(n.getClassName())){Rect b=new Rect();n.getBoundsInScreen(b);if(b.width()>100&&b.height()>100){r=b;matches++;}}require(matches==1,"Exactly one current visible sheet scroller required");}finally{tree.close();}
  int x=r.centerX(),from=r.top+r.height()*4/5,to=r.top+r.height()/5;long stamp=SystemClock.uptimeMillis();
  for(int i=0;i<=11;i++){int action=i==0?MotionEvent.ACTION_DOWN:i==11?MotionEvent.ACTION_UP:MotionEvent.ACTION_MOVE;float y=from+(to-from)*Math.min(i,10)/10f;MotionEvent event=MotionEvent.obtain(stamp,SystemClock.uptimeMillis(),action,x,y,0);event.setSource(InputDevice.SOURCE_TOUCHSCREEN);try{require(ui.injectInputEvent(event,true),"Sheet scroll injection uncertain; no retry");}finally{event.recycle();}SystemClock.sleep(24);}
  steps.put(new JSONObject().put("real_sheet_swipe",box(r)));syncInputs();
 }
 static void cardsChoice()throws Exception{
  await("(?m)^View$",true);
  for(int i=0;i<3;i++){Tree t=new Tree();boolean ready;try{ready=t.find("(?m)^Cards(?:,.*)?$",true)!=null;}finally{t.close();}if(ready){tap("(?m)^Cards(?:,.*)?$");return;}scrollVisibleSheet();}
  throw new IllegalStateException("Cards choice not visible after bounded actual sheet swipes");
 }
 static void enterSource()throws Exception{
  tap("(?m)^\\+?\\s*ADD TV SOURCE$");nativeList("(?m)^M3U / M3U8 playlist$");awaitForm();
  String[] values={"CobraFoldMoreQA","http://10.0.2.2:8765/fold-more.m3u","http://10.0.2.2:8765/cards-epg.xml"};
  for(int index=0;index<3;index++){
   Tree t=new Tree();try{ArrayList<AccessibilityNodeInfo> fields=new ArrayList<>();for(AccessibilityNodeInfo n:t.nodes)if("android.widget.EditText".contentEquals(n.getClassName())&&n.isVisibleToUser())fields.add(n);require(fields.size()==3,"Original M3U form must expose three fields");Bundle a=new Bundle();a.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,values[index]);require(fields.get(index).performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,a),"Public input text failed");steps.put(new JSONObject().put("normal_source_form_field",index));}finally{t.close();}
  }tap("(?m)^TEST & SAVE$");
  for(int i=0;i<24;i++){if(has("(?m)^Return to preview$")){back();break;}if(has("Cards QA 00001"))break;SystemClock.sleep(250);}
  tap("(?m)^Choose one of five view modes$|^Choose view mode$|^Views$");cardsChoice();
  await("(?m)^CARDS.*",true);require(!has("(?m)^Previous Pro source$"),"Pro is not the target");screenshot("cards-before-fullscreen");
 }
 static void visualSettings()throws Exception{
  tap("(?m)^Visual settings(?:,|:).*");
  await("(?m)^Visual settings$",true);await("(?m)^Ambient Mode$",true);await("(?m)^Night Cinema$",true);
  screenshot("cards-sun-menu-before");
  Tree t=new Tree();Rect off=null;
  try{
   write("cards-sun-menu-nodes.json",new JSONObject().put("labels",t.labels()));
   AccessibilityNodeInfo header=t.find("(?m)^Night Cinema$",false);require(header!=null,"Original Night Cinema section required");Rect h=new Rect();header.getBoundsInScreen(h);
   for(AccessibilityNodeInfo n:t.nodes){Rect r=new Rect();n.getBoundsInScreen(r);if(!n.isVisibleToUser()||!n.isEnabled()||r.top<h.bottom||!Pattern.compile("(?m)^Off(?:,.*)?$",Pattern.CASE_INSENSITIVE).matcher(text(n)).find())continue;
    AccessibilityNodeInfo row=n;boolean owned=false;
    try{for(int depth=0;depth<5&&!row.isClickable();depth++){AccessibilityNodeInfo parent=row.getParent();if(owned)row.recycle();row=parent;owned=true;if(row==null)break;}if(row!=null&&row.isClickable()&&row.isVisibleToUser()){Rect b=new Rect();row.getBoundsInScreen(b);if(off==null||b.top<off.top)off=b;}}finally{if(owned&&row!=null)row.recycle();}
   }
  }finally{t.close();}
  require(off!=null,"Original Night Cinema Off row must have current visible touch bounds");tap(off,"Original Night Cinema Off row");syncInputs();await("(?m)^Visual settings$",false);
  tap("(?m)^Visual settings(?:,|:).*");await("(?m)^Night Cinema$",true);screenshot("cards-sun-menu-reopened");back();syncInputs();await("(?m)^Visual settings$",false);
 }
 static Rect preview()throws Exception{
  Tree t=new Tree();AccessibilityNodeInfo parent=null;JSONArray chain=new JSONArray();
  try{
   AccessibilityNodeInfo pip=t.find("(?m)^Picture-in-Picture$",true);require(pip!=null,"Actual current Cards small PiP anchor required");Rect child=new Rect();pip.getBoundsInScreen(child);parent=pip.getParent();
   for(int depth=0;parent!=null&&depth<6;depth++){
    Rect r=new Rect();parent.getBoundsInScreen(r);chain.put(new JSONObject().put("class",String.valueOf(parent.getClassName())).put("bounds",box(r)).put("visible",parent.isVisibleToUser()).put("clickable",parent.isClickable()));
    if(parent.isVisibleToUser()&&parent.isClickable()&&r.contains(child)&&r.width()>child.width()*2&&r.height()>child.height()){
     require(!child.contains(r.centerX(),r.centerY()),"Preview center must not overlap small PiP button");write("actual-preview-public-ancestry.json",new JSONObject().put("PiP_anchor",box(child)).put("original_clickable_host",box(r)).put("chain",chain));return r;
    }
    AccessibilityNodeInfo next=parent.getParent();parent.recycle();parent=next;
   }
   write("missing-preview-public-ancestry.json",new JSONObject().put("chain",chain).put("labels",t.labels()));throw new IllegalStateException("Original clickable Cards preview host not exposed through actual PiP ancestry");
  }finally{if(parent!=null)parent.recycle();t.close();}
 }
 static void fullscreen()throws Exception{
  if(has("(?m)^Return to preview$"))return;
  // Cards uses its original preview's real visible coordinate, never a callback.
  Rect r=preview();long changed=SystemClock.uptimeMillis();tap(r,"Current Cards preview");syncInputs();
  if(has("(?m)^Return to preview$"))return;
  long started=changed;Rect full=waitBounds("(?m)^Fullscreen$",PLAYER_PRESS_LIMIT);
  require(SystemClock.uptimeMillis()-started<PLAYER_PRESS_LIMIT,"Inline target observation expired; no press");tap(full,"Cards inline Fullscreen");require(SystemClock.uptimeMillis()-started<PLAYER_PRESS_LIMIT,"Inline press completed after valid interval");
  syncInputs();await("(?m)^Return to preview$",true);
 }
 static void more(int iteration)throws Exception{
  await("(?m)^Channels$",true);await("(?m)^Display$",true);
  // Observe the actual original hide transition, then renew it through a real
  // background tap. This avoids guessing how much of its 4-second life is left.
  long hiddenStart=SystemClock.uptimeMillis();boolean hidden=iteration>1;
  for(int i=0;!hidden&&i<16&&SystemClock.uptimeMillis()-hiddenStart<10000;i++){if(!has("(?m)^More$")){hidden=true;break;}SystemClock.sleep(250);}require(hidden,"Original fullscreen chrome did not hide within observation limit");
  Bitmap display=ui.takeScreenshot();require(display!=null,"Display bounds unavailable");int w=display.getWidth(),h=display.getHeight();display.recycle();
  Rect reveal=new Rect(w/2-2,h/4-2,w/2+2,h/4+2);long changed=SystemClock.uptimeMillis();if(iteration==1||!has("(?m)^More$"))tap(reveal,"Reveal existing fullscreen chrome");
  Rect first=waitBounds("(?m)^More$",PLAYER_PRESS_LIMIT);Rect second=waitBounds("(?m)^More$",PLAYER_PRESS_LIMIT);
  require(first.equals(second),"Fullscreen More changed bounds; no press");require(SystemClock.uptimeMillis()-changed<PLAYER_PRESS_LIMIT,"Fresh fullscreen More exceeded3.5-second visibility interval; no press");
  tap(second,"Cards FULLSCREEN More "+iteration);require(SystemClock.uptimeMillis()-changed<PLAYER_PRESS_LIMIT,"More injection uncertain after visibility deadline; no retry");
  long tapped=SystemClock.uptimeMillis();SystemClock.sleep(250);screenshot("fullscreen-more-"+iteration+"-250ms");
  Tree after=new Tree();try{write("fullscreen-more-"+iteration+"-nodes.json",new JSONObject().put("labels",after.labels()).put("elapsed_after_press_ms",SystemClock.uptimeMillis()-tapped));require(after.find("(?m)^Player settings$",false)!=null,"Original fullscreen More menu heading not visible");require(after.find("(?m)^Channel playback$",false)!=null&&after.find("(?m)^Health Center$",false)!=null,"Original More menu actions not visible");}finally{after.close();}
  SystemClock.sleep(300);screenshot("fullscreen-more-"+iteration+"-settled");back();syncInputs();await("(?m)^Player settings$",false);
 }
 public static void main(String[] args)throws Exception{
  require(args.length==2,"QA output path and exact JAR digest required");require(args[0].matches("/sdcard/cobra-fold-more-[0-9]+"),"Unsafe public QA output path");dir=new File(args[0]);require(!dir.exists()&&dir.mkdir(),"Fresh public output directory required");
  JSONObject report=new JSONObject().put("scope","EXACT_REJECTED434_CARDS_SUN_FULLSCREEN_MORE").put("steps",steps).put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN").put("application_classpath",System.getProperty("java.class.path")).put("BOOTCLASSPATH","INHERITED_UNCHANGED");Object wrapper=null;Method disconnect=null;
  try{
   File jar=new File("/data/local/tmp/CobraFoldMoreDriver.jar");try(FileInputStream in=new FileInputStream(jar);ByteArrayOutputStream bytes=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)bytes.write(b,0,n);require(hash(bytes.toByteArray()).equals(args[1]),"QA JAR differs from compiled receipt");}
   require(System.getProperty("java.class.path").equals("/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:"+jar),"Original OS wrapper application classpath required");
   Class<?> c=Class.forName("com.android.uiautomator.core.UiAutomationShellWrapper");wrapper=c.getConstructor().newInstance();c.getMethod("connect").invoke(wrapper);disconnect=c.getMethod("disconnect");c.getMethod("setCompressedLayoutHierarchy",boolean.class).invoke(wrapper,true);ui=(UiAutomation)c.getMethod("getUiAutomation").invoke(wrapper);
   android.accessibilityservice.AccessibilityServiceInfo info=ui.getServiceInfo();info.flags|=android.accessibilityservice.AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;ui.setServiceInfo(info);
   require(java.lang.reflect.Modifier.isPublic(UiAutomation.class.getMethod("syncInputTransactions",boolean.class).getModifiers()),"Current OS public transaction synchronization unavailable");
   enterSource();fullscreen();more(1);more(2);report.put("status","EXACT_REJECTED434_FULLSCREEN_MORE_OBSERVED; SUN_RETAINED41116655432; EMULATOR_ONLY_NOT_PHYSICAL_ACCEPTANCE");
  }catch(Throwable e){report.put("status","FAILED_CLOSED").put("error",e.toString());if(ui!=null)try{screenshot("failure");}catch(Throwable ignored){}if(e instanceof Exception)throw (Exception)e;throw (Error)e;}
  finally{write("OUTCOME.json",report);if(disconnect!=null)disconnect.invoke(wrapper);}
 }
}
