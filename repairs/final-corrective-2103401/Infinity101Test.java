package com.projectinfinity.kodi;
import android.app.*;import android.content.*;import android.os.*;import android.view.*;import android.view.accessibility.*;import android.widget.*;import org.json.*;import java.io.*;import java.util.*;
public final class Infinity101Test extends Instrumentation {
 int passed=0;long token=100;Activity activity;InfinityAndroidKeyboard.Editor active;
 static final String T="0123456789abcdef0123456789abcdef";
 static final class Capture implements InfinityAndroidKeyboard.Sink {
  int completed;boolean accepted;String text;
  public void change(long id,String value,boolean done,boolean keep){if(done){completed++;accepted=keep;text=value;}}
 }
 void check(boolean b,String message){if(!b)throw new AssertionError(message);passed++;}
 String request(String theme,String media)throws Exception {
  JSONArray rows=new JSONArray();
  for(String id:new String[]{"umbrella","pov","seren","fenlight","themoviedb.helper"})rows.put(new JSONObject().put("id","plugin.video."+id).put("name",id.equals("umbrella")?"Umbrella":id.equals("pov")?"POV":id.equals("seren")?"Seren":id.equals("fenlight")?"Fen Light":"TMDb Helper").put("description",id.equals("fenlight")||id.equals("themoviedb.helper")?"Not installed or disabled":"Search "+media.toLowerCase()+" · select, then press Search").put("available",!id.equals("fenlight")&&!id.equals("themoviedb.helper")).put("icon",""));
  JSONArray history=new JSONArray().put(new JSONObject().put("query","Relationship Rehab").put("provider","all").put("name","Search All").put("media","tv").put("at",1792627200));
  return "Infinity.Search.2103395:"+new JSONObject().put("token",T).put("theme",theme).put("media",media).put("providers",rows).put("shared_history",history).toString();
 }
 LinearLayout panel(InfinityAndroidKeyboard.Editor e){return (LinearLayout)((View)e.input.getParent()).getParent();}
 void suite()throws Exception{
  for(String theme:new String[]{"light","dark","oled"})for(String media:new String[]{"Movies","TV Shows"}){
   Capture sink=new Capture();InfinityAndroidKeyboard.Editor e=InfinityAndroidKeyboard.show(activity,++token,"été العربية 🎬",request(theme,media),false,true,0,sink);
   LinearLayout p=panel(e);check(e.dialog.isShowing()&&e.input.isShown(),"displayed "+theme+media);check(e.input.getText().toString().equals("été العربية 🎬"),"unicode unchanged");
   for(String id:new String[]{"all","plugin.video.umbrella","plugin.video.pov","plugin.video.seren"}){
    View row=id.equals("all")?p.findViewById(0x00950001):p.findViewWithTag(id);check(row!=null,"provider present");row.performClick();check(sink.completed==0&&e.dialog.isShowing(),"tap never submits");check(row.isSelected(),"cyan selected row state");
    int selected=0;for(String other:new String[]{"all","plugin.video.umbrella","plugin.video.pov","plugin.video.seren"})if((other.equals("all")?p.findViewById(0x00950001):p.findViewWithTag(other)).isSelected())selected++;
    check(selected==1,"one selected provider");row.performLongClick();check(sink.completed==0,"hold never launches provider keyboard");
    LinearLayout r=(LinearLayout)row;check(((TextView)r.getChildAt(r.getChildCount()-1)).getText().toString().equals("✓"),"visible selected checkmark");
   }
   p.findViewWithTag("plugin.video.fenlight").performClick();check(sink.completed==0&&p.findViewWithTag("plugin.video.seren").isSelected(),"unverified inert");
   View submit=p.findViewById(0x01010001);check(((TextView)submit).getText().toString().equals("Search Seren"),"selected search label");submit.performClick();submit.performClick();
   JSONObject result=new JSONObject(sink.text);check(sink.completed==1&&sink.accepted,"single explicit submit");check(result.getString("provider").equals("plugin.video.seren")&&result.getString("query").equals("été العربية 🎬")&&result.getString("token").equals(T),"exact selection query token");
  }
  Capture sink=new Capture();InfinityAndroidKeyboard.Editor e=InfinityAndroidKeyboard.show(activity,++token,"",request("dark","Movies"),false,true,0,sink);
  panel(e).findViewById(0x01010001).performClick();check(sink.completed==0&&e.input.getError()!=null&&e.dialog.isShowing(),"empty query stays open");e.finish(false);
  e=InfinityAndroidKeyboard.show(activity,++token,"Dune",request("oled","TV Shows"),false,true,0,sink=new Capture());panel(e).findViewWithTag("plugin.video.pov").performClick();e.input.onEditorAction(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);check(sink.completed==1&&new JSONObject(sink.text).getString("provider").equals("plugin.video.pov"),"IME uses selected provider");
  e=InfinityAndroidKeyboard.show(activity,++token,"text","Original heading",false,false,0,sink=new Capture());e.finish(true);check(sink.completed==1&&sink.text.equals("text"),"unrelated text preserved");
  e=InfinityAndroidKeyboard.show(activity,++token,"secret","Password",true,false,0,sink=new Capture());check(e.input.getTransformationMethod() instanceof android.text.method.PasswordTransformationMethod,"password preserved");e.finish(false);
  e=InfinityAndroidKeyboard.show(activity,++token,"x",request("dark","Movies"),false,true,0,sink=new Capture());e.finish(false);check(sink.completed==1&&!sink.accepted,"cancel inert");
 }
 void clickText(String text)throws Exception {
  waitForIdleSync();AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();check(root!=null,"active accessibility window");
  List<AccessibilityNodeInfo> nodes=root.findAccessibilityNodeInfosByText(text);
  for(AccessibilityNodeInfo node:nodes)if(text.contentEquals(node.getText())){
   AccessibilityNodeInfo target=node;while(target!=null&&!target.isClickable())target=target.getParent();
   if(target!=null&&target.performAction(AccessibilityNodeInfo.ACTION_CLICK)){waitForIdleSync();return;}
  }
  throw new AssertionError("Missing clickable text: "+text);
 }
 void frame(String name)throws Exception {
  waitForIdleSync();android.os.SystemClock.sleep(200);android.graphics.Bitmap b=getUiAutomation().takeScreenshot();check(b!=null,"screenshot");
  try(FileOutputStream out=new FileOutputStream(new File(getTargetContext().getFilesDir(),name+".png"))){check(b.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out),"screenshot saved");}b.recycle();
 }
 void historyAndScreenshots()throws Exception {
  for(String theme:new String[]{"light","dark","oled"}){
   Capture sink=new Capture();final Throwable[] error={null};
   runOnMainSync(()->{try{active=InfinityAndroidKeyboard.show(activity,++token,"Dune",request(theme,"Movies"),false,true,0,sink);panel(active).findViewWithTag("plugin.video.seren").performClick();}catch(Throwable e){error[0]=e;}});if(error[0]!=null)throw new AssertionError(error[0]);
   frame("search-"+theme);
   runOnMainSync(()->panel(active).findViewById(0x01010002).performClick());frame("history-"+theme);check(sink.completed==0,"history opens without submit");
   clickText("Relationship Rehab");runOnMainSync(()->{check(active.input.getText().toString().equals("Relationship Rehab"),"history populates existing query");check(active.dialog.isShowing()&&sink.completed==0,"history reuse waits for Search");check(panel(active).findViewWithTag("plugin.video.seren").isSelected(),"provider selection retained");});frame("history-reused-"+theme);
   runOnMainSync(()->panel(active).findViewById(0x01010002).performClick());clickText("Clear History");frame("history-confirm-"+theme);check(sink.completed==0,"clear needs confirmation");clickText("Cancel");check(sink.completed==0,"cancel retains history");
   clickText("Clear History");clickText("Clear History");check(sink.completed==1&&sink.accepted,"confirmed clear returns once");JSONObject result=new JSONObject(sink.text);check(result.getString("operation").equals("clear-history")&&result.getBoolean("confirmed")&&result.getString("query").equals("Relationship Rehab"),"clear envelope retains query and selection");
  }
 }
 public void onCreate(Bundle args){super.onCreate(args);start();}
 public void onStart(){Bundle result=new Bundle();try{
  if(Build.VERSION.SDK_INT!=37)throw new AssertionError("Android17 required");activity=startActivitySync(new Intent(getTargetContext(),Infinity101TestActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));waitForIdleSync();final Throwable[] error={null};
  runOnMainSync(()->{try{suite();}catch(Throwable e){error[0]=e;}});if(error[0]!=null)throw new AssertionError(error[0]);historyAndScreenshots();
  result.putString("stream","INFINITY101_UI_PASS="+passed+"\n");result.putInt("passed",passed);finish(Activity.RESULT_OK,result);
 }catch(Throwable error){StringWriter trace=new StringWriter();error.printStackTrace(new PrintWriter(trace));result.putString("stream","INFINITY101_UI_FAILED="+trace+"\n");finish(Activity.RESULT_CANCELED,result);}}
}
