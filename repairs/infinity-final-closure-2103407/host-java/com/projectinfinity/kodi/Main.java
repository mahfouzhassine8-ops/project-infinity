// Disposable Java-process entry. Never included in the Android DEX or APK.
package com.projectinfinity.kodi;
import android.content.Context;
import android.content.res.AssetManager;
import java.io.*;
import java.lang.reflect.*;
public final class Main extends Context {
  private final File storage;
  private final AssetManager assets;
  Main(File storage,File assets) {this.storage=storage;this.assets=new AssetManager(assets);}
  public File getExternalFilesDir(String type) {return storage;}
  public File getFilesDir() {return new File(storage,"private");}
  public AssetManager getAssets() {return assets;}
  public static void main(String[] args)throws Exception {
    final Main main=new Main(new File(args[0]),new File(args[1]));
    Context context=main;
    if(args.length>2 && args[2].equals("other"))context=new Context() {
      public File getExternalFilesDir(String type) {return main.storage;}
      public File getFilesDir() {return main.getFilesDir();}
      public AssetManager getAssets() {return main.assets;}
    };
    File root=new File(new File(main.storage,".kodi"),"addons");
    if(args.length>2 && args[2].equals("wrong-root"))root=new File(main.storage,"unowned");
    Method call=InfinityInstalledCheckpointInstaller.class.getDeclaredMethod("verify",Context.class,File.class);
    call.setAccessible(true);
    try {System.out.println("VERIFIED_VERSION="+call.invoke(null,context,root));}
    catch(InvocationTargetException failure) {
      Throwable cause=failure.getCause();System.err.println(cause.getClass().getSimpleName()+": "+cause.getMessage());System.exit(42);
    }
  }
}
