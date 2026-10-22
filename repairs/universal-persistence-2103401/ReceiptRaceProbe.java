import android.util.AtomicFile;
import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import org.json.JSONObject;

/** Disposable ART replay; invokes the original signed APK methods unchanged. */
public final class ReceiptRaceProbe {
  static void check(boolean value,String detail){if(!value)throw new AssertionError(detail);}
  public static void main(String[] args)throws Exception{
    check(android.os.Build.VERSION.SDK_INT==37,"Android 17 required");
    File root=new File(args[0]);check(root.mkdir(),"fresh isolated fixture required");
    Class<?> protocol=Class.forName("com.projectinfinity.kodi.InfinityCheckpointProtocol");
    Method read=protocol.getDeclaredMethod("read",File.class);read.setAccessible(true);
    Method atomic=protocol.getDeclaredMethod("atomic",File.class,JSONObject.class);atomic.setAccessible(true);
    File receipt=new File(root,"infinity-checkpoint-close.json");
    JSONObject previous=new JSONObject().put("marker","previous");
    atomic.invoke(null,receipt,previous);
    AtomicFile platform=new AtomicFile(receipt);
    FileOutputStream out=platform.startWrite();
    out.write("{\"marker\":\"pending\"}".getBytes(StandardCharsets.UTF_8));out.getFD().sync();
    File staged=new File(receipt.getPath()+".new");check(staged.isFile(),"platform stage missing");
    Object observed=read.invoke(null,root);
    check(previous.toString().equals(observed.toString()),"reader must see prior receipt");
    boolean deleted=!staged.exists();check(deleted,"original reader did not reproduce stage deletion");
    platform.finishWrite(out);
    check(previous.toString().equals(read.invoke(null,root).toString()),"failed rename must retain prior receipt");
    AtomicBoolean stop=new AtomicBoolean();AtomicInteger reads=new AtomicInteger();
    Thread reader=new Thread(()->{while(!stop.get()){try{read.invoke(null,root);reads.incrementAndGet();}catch(Exception ignored){}}},"ActualReceiptReader");
    reader.start();int failed=0,succeeded=0;String failure="";
    try{
      StringBuilder payload=new StringBuilder();for(int n=0;n<32000;n++)payload.append('x');
      for(int i=0;i<100;i++){
        JSONObject value=new JSONObject().put("marker",i).put("payload",payload.toString());
        try{atomic.invoke(null,receipt,value);succeeded++;}
        catch(InvocationTargetException error){Throwable cause=error.getCause();check(cause instanceof IOException,"unexpected exception "+cause);failed++;failure=cause.toString();}
      }
    }finally{stop.set(true);reader.join(10000);check(!reader.isAlive(),"reader failed retirement");}
    check(failed>0&&reads.get()>0,"production-method race not reproduced");
    JSONObject report=new JSONObject().put("passed",true).put("sdk",37)
      .put("original_reader_deleted_in_progress_stage",deleted).put("actual_atomic_failures",failed)
      .put("actual_atomic_successes",succeeded).put("concurrent_reads",reads.get()).put("failure",failure)
      .put("installed_app_modified",false).put("physical_fold_verified",false);
    System.out.println("RECEIPT_RACE_RESULT="+report);
  }
}
