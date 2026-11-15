package com.projectinfinity.observerqa;

import android.app.Activity;
import android.os.Bundle;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Separate CI package/processes. Never installed on the owner's profile. */
public class ProbeActivity extends Activity {
  static { System.loadLibrary("infinityobserverqa"); }
  private static native String runNative(String directory, String pythonPath,
      String caseName, String pythonCode, boolean corrected);
  private void copyTree(String asset, File destination) throws Exception {
    String[] children=getAssets().list(asset);
    if (children != null && children.length>0) {
      destination.mkdirs();
      for(String child:children) copyTree(asset+"/"+child,new File(destination,child));
    } else {
      destination.getParentFile().mkdirs();
      try(InputStream input=getAssets().open(asset);FileOutputStream output=new FileOutputStream(destination)) {
        byte[] bytes=new byte[65536];int count;
        while((count=input.read(bytes))!=-1) output.write(bytes,0,count);
      }
    }
  }
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    final String scenario=getIntent().getStringExtra("case");
    new Thread(()->{
      String result;
      try {
        File root=new File(getFilesDir(),scenario);
        if(root.exists()) throw new IllegalStateException("fresh_case_directory_required");
        new File(root,"profile").mkdirs();new File(root,"cache").mkdirs();
        File python=new File(getFilesDir(),"python3.11");
        if(!new File(python,"encodings/__init__.py").isFile()) copyTree("python3.11",python);
        String code;
        try(InputStream input=getAssets().open("cases/"+scenario+".py")) {
          java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();
          byte[] buffer=new byte[8192];int count;
          while((count=input.read(buffer))!=-1) bytes.write(buffer,0,count);
          code=new String(bytes.toByteArray(),StandardCharsets.UTF_8);
        }
        result=runNative(root.getAbsolutePath(),python.getAbsolutePath(),scenario,code,
            getPackageName().endsWith("candidate"));
      } catch(Exception error) {
        result="{\"status\":\"FAIL\",\"stage\":\"java_fixture\",\"reason\":\""+
            error.getClass().getSimpleName()+"\"}";
      }
      try(FileOutputStream out=new FileOutputStream(new File(getExternalFilesDir(null),scenario+".json"))) {
        out.write(result.getBytes(StandardCharsets.UTF_8));
      } catch(Exception error) { android.util.Log.e("InfinityObserverQA","receipt write failed",error); }
      runOnUiThread(this::finishAndRemoveTask);
    },"observer-fixture").start();
  }
  public static class ClosedBinary extends ProbeActivity {}
  public static class ClosedText extends ProbeActivity {}
  public static class ClosedLayered extends ProbeActivity {}
  public static class FlushError extends ProbeActivity {}
  public static class DirtyBuffer extends ProbeActivity {}
  public static class SqlitePending extends ProbeActivity {}
  public static class DurabilityDenied extends ProbeActivity {}
  public static class LateWrite extends ProbeActivity {}
}
