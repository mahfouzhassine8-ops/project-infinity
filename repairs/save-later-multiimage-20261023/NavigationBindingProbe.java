package infinity.qa;

import java.io.File;
import java.lang.reflect.Method;

/** Disposable API37 ART probe. Never packaged in the application. */
public final class NavigationBindingProbe {
  public static void main(String[] args) throws Exception {
    if (args.length != 3) throw new IllegalArgumentException("method, directory, expected required");
    Class<?> owner = Class.forName("com.projectinfinity.kodi.InfinityInstalledCheckpointInstaller");
    Method method = owner.getDeclaredMethod(args[0], File.class);
    method.setAccessible(true);
    Object result = method.invoke(null, new File(args[1]));
    boolean expected = Boolean.parseBoolean(args[2]);
    if (!(result instanceof Boolean) || ((Boolean) result).booleanValue() != expected)
      throw new AssertionError("Production source verifier result mismatch");
    System.out.println("VERIFIED_PRODUCTION_BINDING=" + args[0] + ":" + result);
  }
}
