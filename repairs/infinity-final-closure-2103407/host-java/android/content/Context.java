// Build-only host fixture. Never packaged or reported as Android execution.
package android.content;
import java.io.File;
import android.content.res.AssetManager;
public abstract class Context {
  public abstract File getExternalFilesDir(String type);
  public abstract File getFilesDir();
  public abstract AssetManager getAssets();
}
