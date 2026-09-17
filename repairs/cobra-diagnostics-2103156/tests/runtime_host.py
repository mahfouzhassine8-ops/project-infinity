#!/usr/bin/env python3
"""Run exact diagnostics helper with explicit Android/JSON/SAF doubles. Not device or OS crash acceptance."""
from pathlib import Path
import argparse,subprocess,json
ROOT=Path(__file__).resolve().parents[1]
STUBS={
'android/net/Uri.java':'''package android.net; public class Uri {String raw;private Uri(String s){raw=s;}public static Uri parse(String s){return new Uri(s);}public String getScheme(){int i=raw.indexOf(':');return i<0?null:raw.substring(0,i);}public String toString(){return raw;}}''',
'android/content/Intent.java':'''package android.content;import java.util.*;public class Intent {public static final String ACTION_CREATE_DOCUMENT="create",CATEGORY_OPENABLE="openable",EXTRA_TITLE="title";public static final int FLAG_GRANT_READ_URI_PERMISSION=1,FLAG_GRANT_WRITE_URI_PERMISSION=2;public String action,type;public int flags;public Set<String> categories=new HashSet<>();public Map<String,String> extras=new HashMap<>();public Intent(String s){action=s;}public Intent addCategory(String s){categories.add(s);return this;}public Intent setType(String s){type=s;return this;}public Intent putExtra(String k,String v){extras.put(k,v);return this;}public Intent addFlags(int f){flags|=f;return this;}}''',
'android/content/pm/PackageInfo.java':'''package android.content.pm;public class PackageInfo {public String versionName="fixture-2103156";public int versionCode=2103156;}''',
'android/content/pm/PackageManager.java':'''package android.content.pm;public class PackageManager {public PackageInfo getPackageInfo(String s,int n){return new PackageInfo();}}''',
'android/content/ContentResolver.java':'''package android.content;import java.io.*;import android.net.Uri;public class ContentResolver {public ByteArrayOutputStream bytes=new ByteArrayOutputStream();public volatile String mode="ok";public volatile boolean deleted=false,opened=false;public OutputStream openOutputStream(Uri u,String m)throws IOException{opened=true;if(mode.equals("null"))return null;if(mode.equals("deny"))throw new SecurityException("denied");return new OutputStream(){public void write(int b)throws IOException{if(mode.equals("full"))throw new IOException("full");bytes.write(b);}public void close()throws IOException{if(mode.equals("close"))throw new IOException("close");}};}public boolean delete(Uri u){deleted=true;return true;}}''',
'android/content/Context.java':'''package android.content;import java.io.*;import android.app.*;import android.content.pm.*;public class Context {public static final String ACTIVITY_SERVICE="activity";public File root;public ContentResolver resolver=new ContentResolver();public ActivityManager manager=new ActivityManager();public Context getApplicationContext(){return this;}public ContentResolver getContentResolver(){return resolver;}public File getFilesDir(){File f=new File(root,"files");f.mkdirs();return f;}public File getCacheDir(){File f=new File(root,"cache");f.mkdirs();return f;}public File getExternalFilesDir(String n){File f=new File(root,"external");f.mkdirs();return f;}public String getPackageName(){return "com.projectinfinity.kodi";}public PackageManager getPackageManager(){return new PackageManager();}public Object getSystemService(String s){return manager;}}''',
'android/app/Activity.java':'package android.app;public class Activity extends android.content.Context {}',
'android/app/Application.java':'''package android.app;import android.os.Bundle;public class Application extends android.content.Context {public ActivityLifecycleCallbacks callbacks;public boolean rejectCallbacks;public void registerActivityLifecycleCallbacks(ActivityLifecycleCallbacks c){if(rejectCallbacks)throw new IllegalStateException("fixture registration failure");callbacks=c;}public interface ActivityLifecycleCallbacks {void onActivityCreated(Activity a,Bundle b);void onActivityStarted(Activity a);void onActivityResumed(Activity a);void onActivityPaused(Activity a);void onActivityStopped(Activity a);void onActivityDestroyed(Activity a);void onActivitySaveInstanceState(Activity a,Bundle b);}}''',
'android/app/ActivityManager.java':'''package android.app;import java.util.*;public class ActivityManager {public List<ApplicationExitInfo> exits=new ArrayList<>();public String queried;public List<ApplicationExitInfo> getHistoricalProcessExitReasons(String p,int pid,int max){queried=p;return exits;}}''',
'android/app/ApplicationExitInfo.java':'''package android.app;import java.io.*;public class ApplicationExitInfo {public static final int REASON_ANR=6;public int reason;public byte[] trace;public int getReason(){return reason;}public long getTimestamp(){return 1234;}public int getPid(){return 17;}public int getStatus(){return 11;}public long getPss(){return 20;}public long getRss(){return 30;}public InputStream getTraceInputStream(){return trace==null?null:new ByteArrayInputStream(trace);}}''',
'android/os/Bundle.java':'package android.os;public class Bundle {}',
'android/os/Build.java':'package android.os;public class Build {public static class VERSION {public static int SDK_INT=31;}}',
'android/os/Process.java':'package android.os;public class Process {public static final int THREAD_PRIORITY_BACKGROUND=10;public static void setThreadPriority(int n){}}',
'android/os/Looper.java':'package android.os;public class Looper {public static Looper getMainLooper(){return new Looper();}}',
'android/os/Handler.java':'package android.os;public class Handler {public Handler(Looper l){}public boolean post(Runnable r){r.run();return true;}}',
'android/provider/DocumentsContract.java':'''package android.provider;import android.content.ContentResolver;import android.net.Uri;public class DocumentsContract {public static boolean deleteDocument(ContentResolver r,Uri u){return r.delete(u);}}''',
'android/widget/Toast.java':'''package android.widget;import android.content.Context;import java.util.*;public class Toast {public static final int LENGTH_LONG=1;public static final List<String> messages=Collections.synchronizedList(new ArrayList<>());String m;public static Toast makeText(Context c,String s,int n){Toast t=new Toast();t.m=s;return t;}public void show(){messages.add(m);}}''',
'org/json/JSONException.java':'package org.json;public class JSONException extends Exception {public JSONException(String m){super(m);}}',
'org/json/JSONObject.java':'''package org.json;import java.util.*;public class JSONObject {Map<String,Object> m=new LinkedHashMap<>();public JSONObject put(String k,Object v)throws JSONException{m.put(k,v);return this;}public String toString(int n)throws JSONException{return toString();}static String val(Object o){if(o instanceof String)return "\\\""+o.toString().replace("\\\\","\\\\\\\\").replace("\\\"","\\\\\\\"").replace("\\n","\\\\n")+"\\\"";return o.toString();}public String toString(){StringBuilder s=new StringBuilder("{");for(Map.Entry<String,Object> e:m.entrySet()){if(s.length()>1)s.append(',');s.append(val(e.getKey())).append(':').append(val(e.getValue()));}return s.append('}').toString();}}''',
'org/json/JSONArray.java':'''package org.json;import java.util.*;public class JSONArray {List<Object> items=new ArrayList<>();public JSONArray put(Object o){items.add(o);return this;}public int length(){return items.size();}public String toString(){StringBuilder s=new StringBuilder("[");for(Object o:items){if(s.length()>1)s.append(',');s.append(JSONObject.val(o));}return s.append(']').toString();}}''',
'com/projectinfinity/kodi/InfinityLiveActivity.java':'package com.projectinfinity.kodi;public class InfinityLiveActivity extends android.app.Activity {}',
}
HARNESS=r'''
package com.projectinfinity.kodi;
import android.app.*;import android.content.*;import android.net.Uri;import android.widget.Toast;import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;import java.util.concurrent.*;import java.util.zip.*;
public class RuntimeTest {
 static int count;static void check(boolean ok,String text){if(!ok)throw new AssertionError(text);count++;System.out.println("PASS: "+text);}
 static void drain()throws Exception{java.lang.reflect.Field f=InfinityCobraDiagnostics.class.getDeclaredField("EVENTS");f.setAccessible(true);((ThreadPoolExecutor)f.get(null)).submit(()->{}).get(5,TimeUnit.SECONDS);}
 static Map<String,String> exported(ContentResolver r)throws Exception{Map<String,String> out=new HashMap<>();try(ZipInputStream z=new ZipInputStream(new ByteArrayInputStream(r.bytes.toByteArray()))){ZipEntry e;while((e=z.getNextEntry())!=null){ByteArrayOutputStream b=new ByteArrayOutputStream();CobraDiagnosticArchive.copy(z,b);out.put(e.getName(),b.toString("UTF-8"));}}return out;}
 static void save(Application app)throws Exception{Toast.messages.clear();InfinityCobraDiagnostics.export(app,Uri.parse("content://fixture/new.zip"),"live snapshot");long until=System.currentTimeMillis()+10000;while(InfinityCobraDiagnostics.exporting()&&System.currentTimeMillis()<until)Thread.sleep(10);if(InfinityCobraDiagnostics.exporting())throw new AssertionError("export never completed");}
 public static void main(String[] args)throws Exception{
  Application app=new Application();app.root=Files.createTempDirectory("cobra-runtime-test-").toFile();
  app.rejectCallbacks=true;InfinityCobraDiagnostics.start(app);check(app.callbacks==null,"Diagnostic observer registration failure cannot abort app startup");app.rejectCallbacks=false;
  InfinityCobraDiagnostics.start(app);check(app.callbacks!=null,"Lifecycle observer registered");
  org.json.JSONObject identity=new org.json.JSONObject();InfinityCobraDiagnostics.addIdentity(app,identity);check(identity.toString().contains("2103156")&&!identity.toString().contains("candidate-2"),"Actual installed package version reported");
  Intent intent=InfinityCobraDiagnostics.createDocumentIntent();check(intent.action.equals(Intent.ACTION_CREATE_DOCUMENT)&&intent.type.equals("application/zip")&&intent.categories.contains(Intent.CATEGORY_OPENABLE)&&intent.extras.get(Intent.EXTRA_TITLE).endsWith(".zip"),"Actual picker intent action/MIME/category/name");
  InfinityCobraDiagnostics.setSecrets(Arrays.asList("privateUser","SecretPassword"));
  InfinityCobraDiagnostics.failure(app,"playback",new IOException("https://host/privateUser?token=SecretPassword"));drain();
  File error=new File(app.getFilesDir(),"health/cobra-diagnostics/last-error.json");String saved=new String(Files.readAllBytes(error.toPath()),StandardCharsets.UTF_8);check(saved.contains("IOException")&&!saved.contains("SecretPassword")&&!saved.contains("host/"),"Captured bounded exception redacted");
  InfinityCobraDiagnostics.record(app,"lifecycle","resumed","");drain();check(new String(Files.readAllBytes(error.toPath()),StandardCharsets.UTF_8).equals(saved),"Success/lifecycle does not erase prior error");
  InfinityCobraDiagnostics.saveHealth(app,"{\"state\":\"ready\"}","");drain();check(new File(app.getFilesDir(),"health/cobra-health.json").isFile(),"Async atomic health persistence");
  File kodi=new File(app.getExternalFilesDir(null),".kodi/temp");kodi.mkdirs();Files.write(new File(kodi,"kodi.log").toPath(),"token=SecretPassword\nhealthy\n".getBytes(StandardCharsets.UTF_8));
  ApplicationExitInfo nativeExit=new ApplicationExitInfo();nativeExit.reason=5;nativeExit.trace="SECRETNATIVEMEMORY".getBytes(StandardCharsets.UTF_8);app.manager.exits.add(nativeExit);
  ApplicationExitInfo anr=new ApplicationExitInfo();anr.reason=6;anr.trace="ANR at Thread.run\nAuthorization: Bearer SecretPassword\n".getBytes(StandardCharsets.UTF_8);app.manager.exits.add(anr);
  save(app);Map<String,String> bundle=exported(app.resolver);check(bundle.containsKey("snapshot.txt")&&bundle.containsKey("manifest.txt")&&bundle.containsKey("kodi.log.txt"),"Production helper creates complete ZIP");
  check(bundle.get("manifest.txt").contains("\"event_queue_flushed\":true"),"Event flush status reported explicitly");
  check(bundle.get("android-exits.txt").contains("not proof Cobra alone"),"Whole-process crash history not falsely attributed to Cobra");
  check(bundle.get("kodi.old.log.txt").contains("missing"),"Unavailable previous log explicit");
  check(bundle.get("android-exits.txt").contains("native_binary_omitted_for_privacy")&&!bundle.toString().contains("SECRETNATIVEMEMORY"),"Native binary metadata kept but raw memory omitted");
  check(bundle.get("android-anr-1.txt").contains("ANR")&&!bundle.toString().contains("SecretPassword"),"Available ANR text redacted and retained");
  check(app.manager.queried.equals(app.getPackageName()),"OS history query confined to app");
  check(Toast.messages.toString().contains("saved to your chosen location"),"Success notified after destination closed");
  File cache=new File(app.getCacheDir(),"cobra-diagnostic-export");check(cache.listFiles().length==0,"Staged ZIP removed after export");
  java.lang.reflect.Method addFile=InfinityCobraDiagnostics.class.getDeclaredMethod("addFile",Map.class,String.class,File.class,String.class,int.class);addFile.setAccessible(true);
  Path real=Files.createTempDirectory("cobra-trusted-root-");Files.write(real.resolve("good.log"),"real log".getBytes(StandardCharsets.UTF_8));Path alias=app.root.toPath().resolve("root-alias");Files.createSymbolicLink(alias,real);
  Map<String,String> safe=new HashMap<>();addFile.invoke(null,safe,"alias",alias.toFile(),"good.log",1024);check(safe.get("alias").equals("real log"),"Android-style app storage root alias does not hide logs");
  Files.createSymbolicLink(real.resolve("linked.log"),error.toPath());addFile.invoke(null,safe,"linked",alias.toFile(),"linked.log",1024);check(safe.get("linked").contains("omitted"),"Descendant diagnostic symlink cannot export unrelated private data");
  for(String mode:Arrays.asList("null","deny","full","close")){app.resolver=new ContentResolver();app.resolver.mode=mode;save(app);check(app.resolver.deleted&&!Toast.messages.toString().contains("saved to your chosen location")&&Toast.messages.toString().contains("Export failed"),"Provider failure "+mode+" does not report success and cleans partial document");}
  app.resolver=new ContentResolver();InfinityCobraDiagnostics.export(app,Uri.parse("file:///not-authorized"),"x");check(!app.resolver.opened,"Non-document destination refused");
  app.resolver=new ContentResolver();android.os.Build.VERSION.SDK_INT=29;save(app);check(exported(app.resolver).get("android-exits.txt").contains("unavailable_before_android_11"),"Pre-API30 reports unavailable rather than inventing history");
  app.resolver=new ContentResolver();android.os.Build.VERSION.SDK_INT=31;app.manager.exits.clear();save(app);check(exported(app.resolver).get("android-exits.txt").contains("no_retained_exit_records"),"Empty history not classified as no crash");
  for(int i=0;i<60;i++){InfinityCobraDiagnostics.record(app,"lifecycle","sample","");drain();}String events=new String(Files.readAllBytes(new File(app.getFilesDir(),"health/cobra-diagnostics/events.jsonl").toPath()),StandardCharsets.UTF_8);check(events.split("\n").length<=48,"Event history bounded");
  System.out.println("SUMMARY: "+count+" runtime checks passed using disclosed Android/JSON/SAF doubles");
 }
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();src=out/'src';src.mkdir(parents=True,exist_ok=True)
 for name,text in STUBS.items():f=src/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
 for name in ('InfinityCobraDiagnostics','CobraDiagnosticArchive'):(src/'com/projectinfinity/kodi'/f'{name}.java').write_text((ROOT/f'{name}.java.in').read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi'))
 (src/'com/projectinfinity/kodi/RuntimeTest.java').write_text(HARNESS)
 subprocess.run(['javac','--release','8','-d',str(out/'classes')]+[str(f) for f in src.rglob('*.java')],check=True)
 r=subprocess.run(['java','-cp',str(out/'classes'),'com.projectinfinity.kodi.RuntimeTest'],capture_output=True,text=True,timeout=30)
 print(r.stdout);print(r.stderr);(out/'output.txt').write_text(r.stdout+r.stderr)
 (out/'results.json').write_text(json.dumps({'exit_code':r.returncode,'stdout':r.stdout,'adapters':'Android lifecycle, PackageManager, own-exit history, JSON serializer, and SAF provider doubles; real production exporter executes','real_device_tested':False},indent=2)+'\n')
 raise SystemExit(r.returncode)
if __name__=='__main__':main()
