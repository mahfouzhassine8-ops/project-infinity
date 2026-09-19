#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json

ROOT=Path("tools/android/packaging/xbmc/src")
BRIDGE=Path("repairs/infinity-experience-2103159")
FILES={
 "Splash.java.in": None,
}
def sha(b): return hashlib.sha256(b).hexdigest()
def require(v,m):
 if not v: raise RuntimeError(m)

def insert_once(text,anchor,addition,label):
 require(text.count(anchor)==1,label+" anchor mismatch")
 return text.replace(anchor,addition+anchor,1)

def main():
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 splash=a.source/ROOT/"Splash.java.in"; before=splash.read_text()
 require("restoreBuiltInVisualThemeFromChooser" not in before,"Recovery already present")
 load_anchor="  private ExperienceTheme loadExperienceTheme()\n  {"
 recovery='''  private void restoreBuiltInVisualThemeFromChooser()
  {
    File root = getExternalFilesDir(null);
    if (root == null)
    {
      android.widget.Toast.makeText(this, "Theme recovery unavailable", android.widget.Toast.LENGTH_LONG).show();
      return;
    }
    File visualRoot = new File(root, ".kodi/addons/script.infinity.cobra.theme/resources/visual");
    File pointer = new File(visualRoot, "active.json");
    boolean reset = false;
    try
    {
      if (pointer.isFile())
      {
        File backup = new File(visualRoot, "active.recovery-backup.json");
        try { java.nio.file.Files.copy(pointer.toPath(), backup.toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING); }
        catch (Exception ignored) {}
        if (!pointer.delete())
        {
          try (java.io.FileOutputStream out = new java.io.FileOutputStream(pointer, false))
          { out.write("{\\\"active\\\":\\\"\\\",\\\"previous\\\":\\\"\\\"}\\n".getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
        }
        reset = true;
      }
      File legacy = new File(root, ".kodi/addons/script.infinity.cobra.theme/resources/visual-theme.json");
      if (legacy.isFile())
      {
        File disabled = new File(legacy.getParentFile(), "visual-theme.disabled-by-recovery.json");
        if (disabled.exists()) disabled.delete();
        if (!legacy.renameTo(disabled) && !legacy.delete()) throw new java.io.IOException("Could not disable legacy visual theme");
        reset = true;
      }
      android.widget.Toast.makeText(this, reset ? "Built-in Cobra theme restored" : "Cobra is already using the built-in theme", android.widget.Toast.LENGTH_LONG).show();
    }
    catch (Exception failure)
    {
      android.util.Log.e(TAG, "Emergency theme recovery failed", failure);
      android.widget.Toast.makeText(this, "Theme recovery failed", android.widget.Toast.LENGTH_LONG).show();
    }
  }

'''
 after=insert_once(before,load_anchor,recovery,"recovery method")
 old='''    gear.setBackground(chooserSurface((top & 0x00ffffff) | 0xdd000000, border, 16));
    gear.setOnClickListener(v -> settings.run());'''
 new='''    gear.setBackground(chooserSurface((top & 0x00ffffff) | 0xdd000000, border, 16));
    gear.setOnClickListener(v -> {
      if (!infinity)
      {
        final String[] choices = new String[]{"Cobra settings", "Restore Built-in Theme", "Cancel"};
        new android.app.AlertDialog.Builder(this)
            .setTitle("Cobra recovery")
            .setItems(choices, (dialog, which) -> {
              if (which == 0) settings.run();
              else if (which == 1)
              {
                new android.app.AlertDialog.Builder(this)
                    .setTitle("Restore Built-in Theme?")
                    .setMessage("Disables the installed Cobra visual theme and returns Cobra to its built-in appearance. Playback, timeshift and app data are not cleared.")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Restore", (confirm, button) -> restoreBuiltInVisualThemeFromChooser())
                    .show();
              }
            }).show();
      }
      else settings.run();
    });'''
 require(after.count(old)==1,"chooser gear anchor mismatch")
 after=after.replace(old,new,1)
 for token in ("Restore Built-in Theme","Cobra recovery","active.recovery-backup.json","visual-theme.disabled-by-recovery.json"):
  require(token in after,"missing recovery token "+token)
 splash.write_text(after)
 a.out.mkdir(parents=True,exist_ok=True)
 report={"before":sha(before.encode()),"after":sha(after.encode()),"changed_file":str(ROOT/"Splash.java.in"),"native_changed":False,"playback_changed":False,"timeshift_changed":False}
 (a.out/"patch.json").write_text(json.dumps(report,indent=2)+"\n")
 print("PASS: chooser-independent emergency theme recovery applied")
if __name__=="__main__":main()

# reconstruction-pipeline-trigger
