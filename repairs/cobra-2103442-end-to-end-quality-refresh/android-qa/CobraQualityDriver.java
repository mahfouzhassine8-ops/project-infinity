package qa;

import android.app.UiAutomation;
import android.graphics.Rect;
import android.os.SystemClock;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.*;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import org.json.*;
import static qa.CobraDrawerDriver.*;

/** Finite public-input journey on the exact signed APK, no application instrumentation. */
public final class CobraQualityDriver {
 static JSONArray cases=new JSONArray();
 static void preflight()throws Exception{
  String density=shell("wm density"),size=shell("wm size"),sdk=shell("getprop ro.build.version.sdk");
  raw("preflight-density.txt",density);raw("preflight-size.txt",size);raw("preflight-sdk.txt",sdk);
  require(density.contains("Override density: 320"),"Exact320dpi OS command preflight required: "+density);
  require(size.contains("Override size: 1080x2520"),"Exact front window OS command preflight required: "+size);
  require(sdk.trim().equals("37"),"Selected API37 OS command preflight required: "+sdk);
 }
 static void capture(String name)throws Exception {
  screenshot(name); // Preserve the actual foreground even if ownership assertion fails.
  Tree t=new Tree();try{write(name+"-nodes.json",new JSONObject().put("labels",t.labels()).put("nodes",nodes(t)).put("query_ms",SystemClock.uptimeMillis()-t.started));}finally{t.close();}
 }
 static void mode(String label)throws Exception {
  tap("(?m)^Choose one of five view modes$|^Choose view mode$|^Views$");await("(?m)^View$",true);
  String pattern="(?m)^"+java.util.regex.Pattern.quote(label)+"(?:,.*)?$";
  for(int i=0;i<5;i++){
   Tree t=new Tree();boolean ready;try{ready=t.find(pattern,true)!=null;}finally{t.close();}
   if(ready){long started=SystemClock.uptimeMillis();tap(pattern);await("(?m)^View$",false);await("Cards QA",true);
    cases.put(new JSONObject().put("mode",label).put("tap_to_observed_guide_ms",SystemClock.uptimeMillis()-started).put("includes_observer_overhead",true));write("MATRIX.json",new JSONObject().put("cases",cases).put("status","IN_PROGRESS_PARTIAL"));return;}
   scrollVisibleSheet();
  }throw new IllegalStateException("Original mode choice not visible: "+label);
 }
 static void swipeList()throws Exception {
  Tree tree=new Tree();Rect target=null,window=new Rect();
  try{require(tree.root!=null,"Current Cobra window required");tree.root.getBoundsInScreen(window);for(AccessibilityNodeInfo node:tree.nodes)if(node.isVisibleToUser()&&node.isScrollable()&&("android.widget.GridView".contentEquals(node.getClassName())||"android.widget.ListView".contentEquals(node.getClassName()))){Rect r=new Rect();node.getBoundsInScreen(r);if(r.intersect(window)&&r.height()>160&&r.width()>160){require(target==null,"One channel-list scroll owner");target=r;}}}finally{tree.close();}
  require(target!=null,"Actual scrollable channel list required");
  // Use the list interior: TV Grid reaches the bottom system-gesture region.
  // The former bottom-30 start invoked Android Home, not an application scroll.
  int x=target.centerX(),y=target.top+target.height()*3/4,end=target.top+target.height()/4;long stamp=SystemClock.uptimeMillis();
  steps.put(new JSONObject().put("channel_list_swipe",box(target)).put("window",box(window)).put("start",new JSONArray(new int[]{x,y})).put("end",new JSONArray(new int[]{x,end})));
  for(int i=0;i<=12;i++){int action=i==0?0:i==12?1:2;android.view.MotionEvent e=android.view.MotionEvent.obtain(stamp,SystemClock.uptimeMillis(),action,x,y+(end-y)*Math.min(i,11)/11f,0);e.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);try{require(ui.injectInputEvent(e,true),"Uncertain scroll input; no retry");}finally{e.recycle();}SystemClock.sleep(24);}syncInputs();
 }
 static void journey(boolean setup)throws Exception {
  if(setup)enterSource();else await("Cards QA",true);
  raw("gfx-before.txt",shell("dumpsys gfxinfo "+PKG+" reset"));
  for(String label:new String[]{"Mobile","TV Grid","Compact","Cards","Pro"}){
   mode(label);capture("front-"+label.replace(' ','-'));swipeList();
  }
  mode("Cards");resize(1600,1800,320);capture("inner-cards");openDrawer();capture("inner-drawer-open");back();await("(?m)^My List$",false);
  for(String label:new String[]{"Mobile","TV Grid","Compact","Cards","Pro"}){mode(label);capture("inner-"+label.replace(' ','-'));swipeList();}
  mode("Cards");resize(1080,2520,320);capture("cover-return");
  raw("gfx-after.txt",shell("dumpsys gfxinfo "+PKG+" framestats"));
  raw("memory-after.txt",shell("dumpsys meminfo "+PKG));raw("cpu-after.txt",shell("dumpsys cpuinfo"));
  write("MATRIX.json",new JSONObject().put("cases",cases).put("state","PUBLIC_INPUT_MODE_SCROLL_RESIZE_JOURNEY").put("physical_Fold","NOT_TESTED"));
 }
 public static void main(String[] args)throws Exception {
  require(args.length==3,"Phase, fresh public output directory and exact QA JAR digest required");
  require(args[0].equals("baseline")||args[0].equals("candidate")||args[0].equals("preflight"),"Selected baseline/candidate/preflight only");
  require(args[1].matches("/sdcard/cobra-quality-(baseline|candidate|preflight)-[0-9]+"),"Fresh selected output only");
  dir=new File(args[1]);require(!dir.exists()&&dir.mkdir(),"Fresh evidence directory required");
  JSONObject result=new JSONObject().put("phase",args[0]).put("shutdown","NOT_RUN").put("Infinity","NOT_LAUNCHED").put("steps",steps);Object wrapper=null;Method disconnect=null;
  try{
   File jar=new File("/data/local/tmp/CobraQualityDriver.jar");ByteArrayOutputStream bytes=new ByteArrayOutputStream();try(InputStream in=new FileInputStream(jar)){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)bytes.write(b,0,n);}require(hash(bytes.toByteArray()).equals(args[2]),"Exact QA driver SHA required");
   require(System.getProperty("java.class.path").equals("/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:"+jar),"OS-only classpath required");
   if(args[0].equals("preflight")){preflight();result.put("status","PASS_EXACT_OS_COMMAND_PREFLIGHT");return;}
   Class<?> c=Class.forName("com.android.uiautomator.core.UiAutomationShellWrapper");wrapper=c.getConstructor().newInstance();c.getMethod("connect").invoke(wrapper);disconnect=c.getMethod("disconnect");c.getMethod("setCompressedLayoutHierarchy",boolean.class).invoke(wrapper,false);ui=(UiAutomation)c.getMethod("getUiAutomation").invoke(wrapper);
   android.accessibilityservice.AccessibilityServiceInfo info=ui.getServiceInfo();info.flags|=android.accessibilityservice.AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;ui.setServiceInfo(info);
   journey(args[0].equals("baseline"));result.put("status","PASS_SELECTED_PUBLIC_INPUT_MODE_SCROLL_RESIZE");
  }catch(Throwable error){result.put("status","FAILED_CLOSED").put("error",error.toString());if(ui!=null)try{capture("failure");}catch(Throwable capture){result.put("capture_error",capture.toString());}if(error instanceof Exception)throw (Exception)error;throw (Error)error;}
  finally{write("OUTCOME.json",result);if(disconnect!=null)disconnect.invoke(wrapper);}
 }
}
