package com.projectinfinity.kodi;
import android.app.*;import android.content.*;import android.os.*;import android.view.*;import android.widget.*;import org.json.*;import java.io.*;
public final class Infinity95Test extends Instrumentation {
 int passed=0;long token=100;Activity activity;
 static final String T="0123456789abcdef0123456789abcdef";
 static final class Capture implements InfinityAndroidKeyboard.Sink {
  int completed;boolean accepted;String text;
  public void change(long id,String value,boolean done,boolean keep){if(done){completed++;accepted=keep;text=value;}}
 }
 void check(boolean b,String message){if(!b)throw new AssertionError(message);passed++;}
 String request(String theme)throws Exception {
  JSONArray rows=new JSONArray();rows.put(new JSONObject().put("id","plugin.video.umbrella").put("name","Umbrella").put("description","Search movies").put("available",true).put("icon",""));
  rows.put(new JSONObject().put("id","plugin.video.pov").put("name","POV").put("description","Unavailable").put("available",false).put("icon",""));
  return "Infinity.Search.2103395:"+new JSONObject().put("token",T).put("theme",theme).put("media","Movies").put("providers",rows).toString();
 }
 void suite()throws Exception{
  for(String theme:new String[]{"light","dark","oled"}){
   Capture sink=new Capture();InfinityAndroidKeyboard.Editor e=InfinityAndroidKeyboard.show(activity,++token,"","",false,true,0,sink);
   // Ordinary keyboard remains intact, then the actual private request uses the exact production hook.
   check(e.input.getParent() instanceof LinearLayout,"original keyboard layout");e.finish(false);
   e=InfinityAndroidKeyboard.show(activity,++token,"été العربية 🎬",request(theme),false,true,0,sink=new Capture());
   LinearLayout panel=(LinearLayout)e.input.getParent();
   check(panel.getChildCount()==6,"one integrated header/query/providers/footer");
   check(e.dialog.isShowing() && e.input.isShown(),"real dialog displayed "+theme);
   check(e.input.getText().toString().equals("été العربية 🎬"),"unicode query preserved");
   View all=panel.findViewById(0x00950001);check(all!=null,"prominent Search All present");
   all.performClick();check(sink.completed==1 && sink.accepted,"one submit");
   JSONObject result=new JSONObject(sink.text);check(result.getString("provider").equals("all")&&result.getString("query").equals("été العربية 🎬"),"real result envelope");
   check(T.equals(result.getString("token")),"request token preserved");
  }
  Capture sink=new Capture();InfinityAndroidKeyboard.Editor e=InfinityAndroidKeyboard.show(activity,++token,"",request("dark"),false,true,0,sink);
  LinearLayout panel=(LinearLayout)e.input.getParent();panel.findViewById(0x00950001).performClick();check(e.dialog.isShowing()&&sink.completed==0&&e.input.getError()!=null,"empty query stays open");
  View provider=panel.findViewWithTag("plugin.video.umbrella");check(provider!=null,"provider row integrated");
  provider.performLongClick();JSONObject result=new JSONObject(sink.text);check(result.getBoolean("history")&&result.getString("provider").equals("plugin.video.umbrella"),"verified provider history selection");
  e=InfinityAndroidKeyboard.show(activity,++token,"query",request("light"),false,true,0,sink=new Capture());
  panel=(LinearLayout)e.input.getParent();panel.findViewWithTag("plugin.video.pov").performClick();check(e.dialog.isShowing()&&sink.completed==0,"unavailable provider inert");
  panel.findViewWithTag("plugin.video.umbrella").performClick();check(new JSONObject(sink.text).getString("provider").equals("plugin.video.umbrella"),"individual provider selection");
  e=InfinityAndroidKeyboard.show(activity,++token,"query",request("oled"),false,true,0,sink=new Capture());
  e.input.onEditorAction(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);check(sink.completed==1&&new JSONObject(sink.text).getString("provider").equals("all"),"IME Search uses integrated request");
  e=InfinityAndroidKeyboard.show(activity,++token,"",request("dark"),false,true,0,sink=new Capture());e.finish(false);check(!sink.accepted&&sink.completed==1,"cancel inert");
  e=InfinityAndroidKeyboard.show(activity,++token,"secret","Password",true,false,0,sink=new Capture());check(e.input.getTransformationMethod() instanceof android.text.method.PasswordTransformationMethod,"unrelated password preserved");e.finish(false);
  e=InfinityAndroidKeyboard.show(activity,++token,"text","Original heading",false,false,0,sink=new Capture());e.finish(true);check("text".equals(sink.text)&&sink.completed==1,"unrelated text entry preserved");
 }
 void screenshots()throws Exception {
  for(String theme:new String[]{"light","dark","oled"}) {
   final InfinityAndroidKeyboard.Editor[] editor={null};final Throwable[] error={null};
   runOnMainSync(()->{try{editor[0]=InfinityAndroidKeyboard.show(activity,++token,"Dune",request(theme),false,true,0,new Capture());}catch(Throwable e){error[0]=e;}});
   if(error[0]!=null)throw new AssertionError(error[0]);
   waitForIdleSync();android.os.SystemClock.sleep(600);
   android.graphics.Bitmap frame=getUiAutomation().takeScreenshot();
   if(frame==null)throw new AssertionError("Screenshot unavailable");
   try(FileOutputStream out=new FileOutputStream(new File(getTargetContext().getFilesDir(),"search-"+theme+".png"))){if(!frame.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out))throw new AssertionError("Screenshot failed");}
   frame.recycle();runOnMainSync(()->editor[0].finish(false));waitForIdleSync();
  }
 }
 public void onCreate(Bundle args){super.onCreate(args);start();}
 public void onStart(){
  Bundle result=new Bundle();
  try{
   if(Build.VERSION.SDK_INT!=37)throw new AssertionError("Android 17 required");
   Intent intent=new Intent(getTargetContext(),Infinity95TestActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
   activity=startActivitySync(intent);waitForIdleSync();final Throwable[] error={null};
   runOnMainSync(()->{try{suite();}catch(Throwable e){error[0]=e;}});if(error[0]!=null)throw new AssertionError(error[0]);
   screenshots();
   result.putString("stream","INFINITY95_UI_PASS="+passed+"\n");result.putInt("passed",passed);finish(Activity.RESULT_OK,result);
  }catch(Throwable error){result.putString("stream","INFINITY95_UI_FAILED="+error.toString()+"\n");finish(Activity.RESULT_CANCELED,result);}
 }
}
