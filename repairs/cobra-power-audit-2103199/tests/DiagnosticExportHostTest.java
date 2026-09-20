
package com.projectinfinity.kodi;
import android.app.*;import android.content.*;import android.net.Uri;import android.widget.Toast;import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;import java.util.concurrent.*;import java.util.zip.*;
public class DiagnosticExportHostTest {
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
  check(new File(kodi,"kodi.log").setLastModified(1577836800000L),"fixture old log time set");
  save(app);Map<String,String> bundle=exported(app.resolver);check(bundle.containsKey("snapshot.txt")&&bundle.containsKey("manifest.txt")&&bundle.containsKey("kodi.log.txt"),"Production helper creates complete ZIP");
  check(bundle.get("manifest.txt").contains("\"event_queue_flushed\":true"),"Event flush status reported explicitly");
  String manifest=bundle.get("manifest.txt");
  check(manifest.contains("\"event_history_retained_limit\":47")&&manifest.contains("older entries may be evicted")&&manifest.contains("excludes normal history eviction"),"Retention and queue loss meanings truthful");
  check(manifest.contains("\"attachment_metadata\"")&&manifest.contains("\"file_modified_at_ms\":1577836800000")&&manifest.contains("does not establish event freshness"),"Stale log mtime exposed without claiming current-session content");
  check(manifest.contains("\"file_state\":\"unavailable\""),"Missing attachment status explicit");
  Files.write(Paths.get(args[0]),manifest.getBytes(StandardCharsets.UTF_8));

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

  java.lang.reflect.Method observed=InfinityCobraDiagnostics.class.getDeclaredMethod("addObservedFile",Map.class,String.class,File.class,String.class,int.class,org.json.JSONObject.class);observed.setAccessible(true);
  org.json.JSONObject metadata=new org.json.JSONObject();Map<String,String> checked=new HashMap<>();
  observed.invoke(null,checked,"linked",alias.toFile(),"linked.log",1024,metadata);check(metadata.toString().contains("omitted_noncanonical")&&!metadata.toString().contains("source_file_bytes"),"Symlink metadata does not stat private target");
  Files.write(real.resolve("future.log"),"future log".getBytes(StandardCharsets.UTF_8));check(real.resolve("future.log").toFile().setLastModified(System.currentTimeMillis()+86400000L),"future fixture time set");metadata=new org.json.JSONObject();
  observed.invoke(null,checked,"future",real.toFile(),"future.log",1024,metadata);check(metadata.toString().contains("\"file_age_ms\":-1"),"Future mtime is unknown age rather than fresh");
  metadata=new org.json.JSONObject();observed.invoke(null,checked,"small",real.toFile(),"good.log",3,metadata);check(metadata.toString().contains("\"text_may_be_truncated\":true"),"Read limit disclosure reflects source bytes");
  System.out.println("SUMMARY: "+count+" runtime checks passed using disclosed Android/JSON/SAF doubles");
 }
}
