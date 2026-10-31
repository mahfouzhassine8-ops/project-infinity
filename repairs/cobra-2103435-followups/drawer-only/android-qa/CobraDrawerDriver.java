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
 * operations. Only selected targets are Cards drawer interactions and real window configuration changes. */
public final class CobraDrawerDriver {
 static final String PKG="com.projectinfinity.kodi";
 static UiAutomation ui;static File dir,baselineReference;static JSONArray steps=new JSONArray();static int sequence,windowWidth=1080,windowHeight=2520;
 static void require(boolean b,String why){if(!b)throw new IllegalStateException(why);}
 static String hash(byte[] raw)throws Exception{byte[] b=MessageDigest.getInstance("SHA-256").digest(raw);StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format(Locale.US,"%02x",v));return s.toString();}
 static JSONArray box(Rect r){return new JSONArray().put(r.left).put(r.top).put(r.right).put(r.bottom);}
 static void write(String name,JSONObject value)throws Exception{try(FileOutputStream out=new FileOutputStream(new File(dir,name))){out.write((value.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));}}
 static String text(AccessibilityNodeInfo n){CharSequence t=n.getText(),d=n.getContentDescription();return (t==null?"":t.toString())+"\n"+(d==null?"":d.toString());}
 static final class Tree {
  final long started=SystemClock.uptimeMillis();final AccessibilityNodeInfo root;final ArrayList<AccessibilityNodeInfo> nodes=new ArrayList<>();final Map<Integer,Integer> parents=new HashMap<>();
  Tree(){root=ui.getRootInActiveWindow();if(root==null)return;require(PKG.contentEquals(root.getPackageName()),"Unexpected active package");nodes.add(root);for(int i=0;i<nodes.size();i++){require(nodes.size()<1600,"Bounded public UI tree exceeded");AccessibilityNodeInfo n=nodes.get(i);for(int c=0;c<n.getChildCount();c++){AccessibilityNodeInfo child=n.getChild(c);if(child!=null){parents.put(child.hashCode(),n.hashCode());nodes.add(child);}}}}
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
  String[] values={"CobraDrawerQA","http://10.0.2.2:8765/fold-more.m3u","http://10.0.2.2:8765/cards-epg.xml"};
  for(int index=0;index<3;index++){
   Tree t=new Tree();try{ArrayList<AccessibilityNodeInfo> fields=new ArrayList<>();for(AccessibilityNodeInfo n:t.nodes)if("android.widget.EditText".contentEquals(n.getClassName())&&n.isVisibleToUser())fields.add(n);require(fields.size()==3,"Original M3U form must expose three fields");Bundle a=new Bundle();a.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,values[index]);require(fields.get(index).performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,a),"Public input text failed");steps.put(new JSONObject().put("normal_source_form_field",index));}finally{t.close();}
  }tap("(?m)^TEST & SAVE$");
  for(int i=0;i<24;i++){if(has("(?m)^Return to preview$")){back();break;}if(has("Cards QA 00001"))break;SystemClock.sleep(250);}
  tap("(?m)^Choose one of five view modes$|^Choose view mode$|^Views$");cardsChoice();
  await("(?m)^CARDS.*",true);require(!has("(?m)^Previous Pro source$"),"Pro is not the target");screenshot("cards-source-configured");
 }
 static Rect preview()throws Exception{
  Tree t=new Tree();AccessibilityNodeInfo parent=null;JSONArray chain=new JSONArray();
  try{
   AccessibilityNodeInfo pip=t.find("(?m)^Picture-in-Picture$",true);require(pip!=null,"Actual current Cards small PiP anchor required");Rect child=new Rect();pip.getBoundsInScreen(child);parent=pip.getParent();
   for(int depth=0;parent!=null&&depth<6;depth++){
    Rect r=new Rect();parent.getBoundsInScreen(r);chain.put(new JSONObject().put("class",String.valueOf(parent.getClassName())).put("bounds",box(r)).put("visible",parent.isVisibleToUser()).put("clickable",parent.isClickable()));
    if(parent.isVisibleToUser()&&parent.isClickable()&&r.contains(child)&&r.width()>child.width()*2&&r.height()>child.height()){
     require(!child.contains(r.centerX(),r.centerY()),"Preview center must not overlap small PiP button");write("actual-preview-public-ancestry-"+(sequence++)+".json",new JSONObject().put("PiP_anchor",box(child)).put("original_clickable_host",box(r)).put("chain",chain));return r;
    }
    AccessibilityNodeInfo next=parent.getParent();parent.recycle();parent=next;
   }
   write("missing-preview-public-ancestry.json",new JSONObject().put("chain",chain).put("labels",t.labels()));throw new IllegalStateException("Original clickable Cards preview host not exposed through actual PiP ancestry");
  }finally{if(parent!=null)parent.recycle();t.close();}
 }
 static String shell(String command)throws Exception{
  try(InputStream in=new android.os.ParcelFileDescriptor.AutoCloseInputStream(ui.executeShellCommand(command));ByteArrayOutputStream out=new ByteArrayOutputStream()){
   byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1){require(out.size()+n<8*1024*1024,"Bounded public OS dump exceeded");out.write(buffer,0,n);}return new String(out.toByteArray(),StandardCharsets.UTF_8);
  }
 }
 static void raw(String name,String value)throws Exception{try(FileOutputStream out=new FileOutputStream(new File(dir,name))){out.write(value.getBytes(StandardCharsets.UTF_8));}}
 static JSONArray nodes(Tree t)throws Exception{
  JSONArray out=new JSONArray();for(AccessibilityNodeInfo n:t.nodes){
   Rect drawing=new Rect();n.getBoundsInParent(drawing);
   JSONObject v=new JSONObject().put("id",n.hashCode()).put("parent",t.parents.containsKey(n.hashCode())?t.parents.get(n.hashCode()):JSONObject.NULL).put("label",text(n).trim()).put("class",String.valueOf(n.getClassName())).put("visible",n.isVisibleToUser()).put("focused",n.isFocused()).put("selected",n.isSelected()).put("bounds",nodeBox(n)).put("drawing_bounds",box(drawing));
   AccessibilityNodeInfo.CollectionInfo collection=n.getCollectionInfo();if(collection!=null)v.put("columns",collection.getColumnCount()).put("rows",collection.getRowCount());out.put(v);
  }return out;
 }
 static JSONObject measured(AccessibilityNodeInfo n)throws Exception{
  require(n!=null,"Original structural view node required");
  require(n.getAvailableExtraData().contains(AccessibilityNodeInfo.EXTRA_DATA_RENDERING_INFO_KEY),"Native ViewGroup rendering-info capability required");
  require(n.refreshWithExtraData(AccessibilityNodeInfo.EXTRA_DATA_RENDERING_INFO_KEY,new Bundle()),"Native rendering-info refresh failed");
  AccessibilityNodeInfo.ExtraRenderingInfo extra=n.getExtraRenderingInfo();require(extra!=null&&extra.getLayoutSize()!=null,"Actual native layout parameters required");
  Rect drawing=new Rect();n.getBoundsInParent(drawing);android.util.Size lp=extra.getLayoutSize();
  JSONObject result=new JSONObject().put("identity",n.hashCode()).put("class",String.valueOf(n.getClassName())).put("drawing_bounds",box(drawing)).put("width",drawing.width()).put("height",drawing.height()).put("layout_width",lp.getWidth()).put("layout_height",lp.getHeight()).put("screen_bounds",nodeBox(n));
  AccessibilityNodeInfo.CollectionInfo collection=n.getCollectionInfo();if(collection!=null)result.put("columns",collection.getColumnCount());return result;
 }
 static JSONObject structure(Tree tree)throws Exception{
  AccessibilityNodeInfo grid=null;
  for(AccessibilityNodeInfo n:tree.nodes)if("android.widget.GridView".contentEquals(n.getClassName())&&n.isVisibleToUser()){Rect r=new Rect();n.getBoundsInParent(r);if(r.width()>200&&r.height()>100){require(grid==null,"One actual Cards grid required");grid=n;}}
  require(grid!=null,"Actual native Cards GridView required");AccessibilityNodeInfo browser=grid.getParent(),nav=tree.find("(?m)^Open Cobra navigation$",true),toolbar=nav==null?null:nav.getParent();
  AccessibilityNodeInfo pip=tree.find("(?m)^Picture-in-Picture$",true),preview=pip==null?null:pip.getParent();
  try{
   require(nav!=null&&toolbar!=null&&"android.widget.LinearLayout".contentEquals(toolbar.getClassName()),"Original mode-toolbar parent required");
   while(preview!=null&&!preview.isClickable()){AccessibilityNodeInfo next=preview.getParent();preview.recycle();preview=next;}
   JSONObject g=measured(grid),b=measured(browser),h=measured(toolbar),p=measured(preview);
   require(h.getInt("height")>0&&h.getInt("height")<400,"Native mode toolbar must not be confused with the page root");
   for(JSONObject v:new JSONObject[]{b,h,p})require(v.getInt("layout_width")==v.getInt("width")&&v.getInt("layout_height")==v.getInt("height"),"Actual drawn group size must agree with committed native layout parameters");
   return new JSONObject().put("grid",g).put("browser",b).put("toolbar",h).put("preview",p).put("nav_screen_bounds",nodeBox(nav));
  }finally{if(browser!=null)browser.recycle();if(toolbar!=null)toolbar.recycle();if(preview!=null)preview.recycle();}
 }
 static void snapshot(String phase,boolean drawer)throws Exception{
  syncInputs();String dump=shell("dumpsys activity top");raw(phase+"-activity.txt",dump);
  raw(phase+"-display.txt",shell("wm size; wm density"));
  boolean observedDrawer=nativeTextBounds("My List")!=null;require(observedDrawer==drawer,"Actual drawer state differs from selected scenario; no assumed state or further Back input");
  Tree t=new Tree();try{JSONObject state=new JSONObject().put("phase",phase).put("expected_drawer",drawer).put("actual_drawer_observed",observedDrawer).put("nodes",nodes(t)).put("structure",structure(t)).put("at_ms",SystemClock.uptimeMillis());
   if(!drawer)state.put("preview_frame",box(preview()));write(phase+"-nodes.json",state);
  }finally{t.close();}screenshot(phase);steps.put(new JSONObject().put("snapshot",phase).put("drawer",drawer));
 }
 static void awaitDecodedPreview()throws Exception{
  long start=SystemClock.uptimeMillis();int last=0;
  for(int attempt=0;attempt<24&&SystemClock.uptimeMillis()-start<12000;attempt++){
   Rect r=preview();Bitmap b=ui.takeScreenshot();require(b!=null,"Actual preview readiness screenshot required");int matches=0;
   try{for(int y=1;y<=8;y++)for(int x=1;x<=8;x++){
    int pixel=b.getPixel(Math.min(b.getWidth()-1,r.left+r.width()*x/10),Math.min(b.getHeight()-1,r.top+r.height()*y/10));int red=(pixel>>16)&255,green=(pixel>>8)&255,blue=pixel&255;
    if(blue>8&&blue>green*1.6f&&green>red*1.3f)matches++;
   }}finally{b.recycle();}last=matches;if(matches>=24){steps.put(new JSONObject().put("decoded_loopback_QA1_preview_blue_samples",matches));return;}SystemClock.sleep(150);
  }throw new IllegalStateException("Known loopback QA1 decoded preview was not observed; matches="+last);
 }
 static void openDrawer()throws Exception{tap("(?m)^Open Cobra navigation$");await("(?m)^My List$",true);}
 static void closeDrawer()throws Exception{requireOpenDrawerBeforeBack();back();syncInputs();await("(?m)^My List$",false);awaitMeasuredClosedNav();}
 static String referencePhase(){return windowWidth==1080?"435-cover-closed":windowWidth==1600?"435-inner-closed":"435-rotated-inner-closed";}
 static void awaitMeasuredClosedNav()throws Exception{
  require(baselineReference!=null,"Actual original435 closed-layout reference required");File file=new File(baselineReference,referencePhase()+"-nodes.json");
  JSONObject reference;try(FileInputStream in=new FileInputStream(file);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);reference=new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));}
  JSONArray target=reference.getJSONObject("structure").getJSONArray("nav_screen_bounds");long start=SystemClock.uptimeMillis();
  for(int i=0;i<40&&SystemClock.uptimeMillis()-start<12000;i++){Rect observed=nativeTextBounds("Open Cobra navigation");if(observed!=null&&observed.left==target.getInt(0)&&observed.width()==target.getInt(2)-target.getInt(0))return;SystemClock.sleep(16);}
  throw new IllegalStateException("Original measured closed navigation X was not restored; no assumed settled geometry");
 }
 static Rect nativeTextBounds(String label)throws Exception{
  AccessibilityNodeInfo root=ui.getRootInActiveWindow();require(root!=null&&PKG.contentEquals(root.getPackageName()),"Current Cobra window required");
  List<AccessibilityNodeInfo> matches=root.findAccessibilityNodeInfosByText(label);Rect found=null;Pattern pattern=Pattern.compile("(?im)^"+Pattern.quote(label)+"$");
  try{for(AccessibilityNodeInfo n:matches)if(n.isVisibleToUser()&&n.isEnabled()&&pattern.matcher(text(n).trim()).find()){Rect r=new Rect();n.getBoundsInScreen(r);if(r.width()>12&&r.height()>12){if(found==null)found=r;else if(r.contains(found))found=r;else require(found.contains(r),"Duplicate nonoverlapping native targets refused");}}}finally{for(AccessibilityNodeInfo n:matches)n.recycle();root.recycle();}return found;
 }
 static void requireOpenDrawerBeforeBack()throws Exception{
  long start=SystemClock.uptimeMillis();for(int i=0;i<30&&SystemClock.uptimeMillis()-start<12000;i++){if(nativeTextBounds("My List")!=null)return;SystemClock.sleep(16);}
  throw new IllegalStateException("Drawer opening was not observed; Back was NOT injected into an unknown surface");
 }
 static void resize(int width,int height,int density)throws Exception{
  // Density is fixed once before app installation. A window-size transition
  // must not add a separate, potentially recreating density change to the
  // selected fold-size scenario.
  require(shell("wm density").contains("Override density: "+density),"Expected stable test display density required");
  raw("resize-"+width+".txt",shell("wm size "+width+"x"+height));syncInputs();
  long start=SystemClock.uptimeMillis();boolean observed=false;
  for(int i=0;i<30&&SystemClock.uptimeMillis()-start<12000;i++){
   AccessibilityNodeInfo root=ui.getRootInActiveWindow();if(root!=null){Rect r=new Rect();root.getBoundsInScreen(r);boolean own=PKG.contentEquals(root.getPackageName());root.recycle();if(own&&r.width()==width){observed=true;break;}}SystemClock.sleep(100);
  }require(observed,"Actual new Android window width was not observed; no inferred configuration success");
  windowWidth=width;windowHeight=height;
 }
 static void swipeGrid()throws Exception{
  Tree t=new Tree();Rect r=null;try{for(AccessibilityNodeInfo n:t.nodes)if("android.widget.GridView".contentEquals(n.getClassName())&&n.isVisibleToUser()){Rect b=new Rect();n.getBoundsInScreen(b);if(b.width()>300&&b.height()>250){require(r==null,"One visible Cards grid required");r=b;}}}finally{t.close();}
  require(r!=null,"Current Cards grid bounds required for touch scroll");int x=r.centerX(),from=r.bottom-80,to=r.top+80;long stamp=SystemClock.uptimeMillis();
  for(int i=0;i<=11;i++){
   // Finish this selected drag at rest so the anchor check does not confuse
   // legitimate inertial scrolling with drawer-induced movement.
   if(i==11)SystemClock.sleep(160);
   int action=i==0?MotionEvent.ACTION_DOWN:i==11?MotionEvent.ACTION_UP:MotionEvent.ACTION_MOVE;MotionEvent e=MotionEvent.obtain(stamp,SystemClock.uptimeMillis(),action,x,from+(to-from)*Math.min(10,i)/10f,0);e.setSource(InputDevice.SOURCE_TOUCHSCREEN);try{require(ui.injectInputEvent(e,true),"Grid swipe outcome uncertain; no retry");}finally{e.recycle();}SystemClock.sleep(24);
  }syncInputs();
 }
 static void journey()throws Exception{
  await("(?m)^CARDS.*",true);require(!has("(?m)^\\+?\\s*ADD TV SOURCE$"),"Original configured source must survive install-over");
  tap("(?m)^Cards QA 00001(?:,|\\n|$)");if(has("(?m)^Return to preview$")){back();syncInputs();}
  awaitDecodedPreview();
  snapshot("01-cover-closed",false);openDrawer();snapshot("02-cover-open",true);
  resize(1600,1680,320);snapshot("03-inner-open-from-cover",true);closeDrawer();snapshot("04-inner-closed",false);
  swipeGrid();snapshot("05-inner-scroll-anchor",false);
  int fullOpenNavLeft=-1;
  for(int i=0;i<3;i++){openDrawer();snapshot("06-inner-open-"+i,true);if(i==0)fullOpenNavLeft=waitBounds("(?m)^Open Cobra navigation$",12000).left;closeDrawer();snapshot("07-inner-closed-"+i,false);}
  // Interrupted motion uses actual nav/Back events, with the original210ms
  // production animation untouched. Record the real event interval; offline
  // validation requires at least one genuinely interrupted attempt.
  for(int i=0;i<3;i++){
   syncInputs();Rect r=waitBounds("(?m)^Open Cobra navigation$",12000);long before=SystemClock.uptimeMillis();tap(r,"Interruptible original drawer open");requireOpenDrawerBeforeBack();Rect moving=nativeTextBounds("Open Cobra navigation");require(moving!=null,"Actual drawer-stage position required before interruption");long backStart=SystemClock.uptimeMillis();back();steps.put(new JSONObject().put("interruption",i).put("open_to_Back_start_ms",backStart-before).put("closed_nav_left",r.left).put("fully_open_nav_left",fullOpenNavLeft).put("observed_before_Back_nav_left",moving.left));syncInputs();await("(?m)^My List$",false);awaitMeasuredClosedNav();snapshot("08-interrupted-"+i,false);
  }
  openDrawer();resize(1680,1600,320);snapshot("09-rotated-inner-open",true);closeDrawer();snapshot("10-rotated-inner-closed",false);
  openDrawer();resize(1080,2520,320);snapshot("11-cover-open-from-inner",true);closeDrawer();snapshot("12-cover-return-closed",false);
 }
 public static void main(String[] args)throws Exception{
  require(args.length==4,"Phase, fresh QA output, exact JAR SHA256 and original closed-layout reference required");String phase=args[0];require(phase.equals("setup")||phase.equals("verify"),"Only selected phases allowed");
  require(args[1].matches("/sdcard/cobra-drawer-(setup|verify)-[0-9]+"),"Fresh public QA output only");dir=new File(args[1]);require(!dir.exists()&&dir.mkdir(),"Fresh QA output directory required");
  JSONObject report=new JSONObject().put("scope","CARDS_DRAWER_ONLY_ORIGINAL_EVENTS_AND_WINDOWMANAGER_CONFIGURATION").put("phase",phase).put("steps",steps).put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN").put("Infinity","NOT_LAUNCHED");Object wrapper=null;Method disconnect=null;
  try{
   File jar=new File("/data/local/tmp/CobraDrawerDriver.jar");try(FileInputStream in=new FileInputStream(jar);ByteArrayOutputStream data=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)data.write(b,0,n);require(hash(data.toByteArray()).equals(args[2]),"Exact compiled QA JAR required");}
   require(System.getProperty("java.class.path").equals("/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:"+jar),"Original OS wrapper classpath required");
   Class<?> c=Class.forName("com.android.uiautomator.core.UiAutomationShellWrapper");wrapper=c.getConstructor().newInstance();c.getMethod("connect").invoke(wrapper);disconnect=c.getMethod("disconnect");c.getMethod("setCompressedLayoutHierarchy",boolean.class).invoke(wrapper,false);ui=(UiAutomation)c.getMethod("getUiAutomation").invoke(wrapper);
   android.accessibilityservice.AccessibilityServiceInfo info=ui.getServiceInfo();info.flags|=android.accessibilityservice.AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;ui.setServiceInfo(info);
   if(phase.equals("setup")){
    require(args[3].equals("none"),"Setup cannot consume an unobserved reference");enterSource();snapshot("435-cover-closed",false);
    resize(1600,1680,320);snapshot("435-inner-closed",false);resize(1680,1600,320);snapshot("435-rotated-inner-closed",false);resize(1080,2520,320);snapshot("435-cover-return-closed",false);
   }else{require(args[3].matches("/sdcard/cobra-drawer-setup-[0-9]+"),"Only this run's original435 public reference is allowed");baselineReference=new File(args[3]);require(baselineReference.isDirectory(),"Original435 reference not present");journey();}report.put("status","NATIVE_EVENTS_CAPTURED; OFFLINE_GEOMETRY_AND_CONTINUITY_VALIDATION_REQUIRED");
  }catch(Throwable e){report.put("status","FAILED_CLOSED").put("error",e.toString());if(ui!=null)try{screenshot("failure");}catch(Throwable capture){report.put("capture_error",capture.toString());}if(e instanceof Exception)throw (Exception)e;throw (Error)e;}
  finally{write("OUTCOME.json",report);if(disconnect!=null)disconnect.invoke(wrapper);}
 }
}
