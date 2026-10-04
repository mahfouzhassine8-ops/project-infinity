#!/usr/bin/env python3
"""Compile the production route installer with minimal host Android stand-ins.

These checks exercise XML preservation and real temporary-file installation.
They do not simulate Android lifecycle, native cleanup, or device touch input.
"""
import argparse
from pathlib import Path
import subprocess
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "InfinityPowerMenuRoutes.java.in"
FIXTURE = HERE.parent / "e2e-mobile-2103303/fixtures/unified-DialogButtonMenu.xml"
STUBS = {
    "android/content/Context.java": """
package android.content;
import java.io.File;
import java.util.*;
public class Context {
  public static final int MODE_PRIVATE=0;
  private final File root;
  private final Map<String,SharedPreferences> prefs=new HashMap<>();
  public Context(File root){this.root=root;root.mkdirs();}
  public Context getApplicationContext(){return this;}
  public File getExternalFilesDir(String type){return new File(root,"external");}
  public File getFilesDir(){File p=new File(root,"files");p.mkdirs();return p;}
  public String getPackageName(){return "com.projectinfinity.kodi";}
  public File getDir(String name,int mode){File p=new File(root,name);p.mkdirs();return p;}
  public SharedPreferences getSharedPreferences(String name,int mode){
    return prefs.computeIfAbsent(name,k->new SharedPreferences());
  }
}
""",
    "android/content/SharedPreferences.java": """
package android.content;
public class SharedPreferences {
  private String value="";
  public String getString(String key,String fallback){return value.isEmpty()?fallback:value;}
  public Editor edit(){return new Editor();}
  public class Editor {
    private String pending;
    public Editor putString(String key,String value){pending=value;return this;}
    public boolean commit(){value=pending;return true;}
  }
}
""",
    "android/util/AtomicFile.java": """
package android.util;
import java.io.*;
import java.nio.file.*;
public class AtomicFile {
  private final File file,temporary;
  public AtomicFile(File file){this.file=file;temporary=new File(file+".new");}
  public FileOutputStream startWrite()throws IOException{return new FileOutputStream(temporary);}
  public void finishWrite(FileOutputStream out)throws IOException{
    out.close();Files.move(temporary.toPath(),file.toPath(),StandardCopyOption.REPLACE_EXISTING);
  }
  public void failWrite(FileOutputStream out)throws IOException{out.close();temporary.delete();}
}
""",
    "com/projectinfinity/kodi/InfinityExitCompletion.java": """
package com.projectinfinity.kodi;
final class InfinityExitCompletion {
  static final String NORMAL="com.projectinfinity.kodi.action.CLOSE_KODI";
  static final String FORCE="com.projectinfinity.kodi.action.FORCE_CLOSE_KODI";
}
""",
    "com/projectinfinity/kodi/XBMCProperties.java": """
package com.projectinfinity.kodi;
final class XBMCProperties {
  static String getStringProperty(String key,String fallback){return System.getProperty(key,fallback);}
}
""",
}

HARNESS = r"""
package com.projectinfinity.kodi;
import android.content.Context;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;

public class PowerRouteHostTest {
  static int checks;
  static void check(boolean ok,String why){
    if(!ok)throw new AssertionError(why);checks++;
  }
  static void rejected(String xml,String why)throws Exception{
    try{InfinityPowerMenuRoutes.patch(xml);throw new AssertionError("Accepted "+why);}
    catch(IOException expected){checks++;}
  }
  static String button(String id,String label,String commands){
    return "<control type=\"button\" id=\""+id+"\"><label>"+label+"</label>"+commands+"</control>";
  }
  static String click(String condition,String command){
    return "<onclick"+(condition==null?"":" condition=\""+condition+"\"")+">"+command+"</onclick>";
  }
  static final String FORCE_LEGACY="ActivateWindow(10001,\"plugin://plugin.program.chef21/?mode=18&amp;name=Force%20Close\",return)";
  static String paired(boolean reverse){
    String normal=click("!System.Platform.Android","Quit()"),android=click("System.Platform.Android",InfinityPowerMenuRoutes.command(false));
    String force=click("!System.Platform.Android",FORCE_LEGACY),androidForce=click("System.Platform.Android",InfinityPowerMenuRoutes.command(true));
    return "<window>"+button("200","CLOSE KODI",reverse?android+normal:normal+android)
      +button("300","FORCE CLOSE KODI",reverse?androidForce+force:force+androidForce)+"</window>";
  }
  static String maskPower(String xml){
    for(String id:new String[]{"200","300"}){
      Matcher m=Pattern.compile("<control[^>]*id=\""+id+"\"[^>]*>.*?</control>",Pattern.DOTALL).matcher(xml);
      check(m.find(),"missing mask button");
      String body=m.group().replaceAll("(?s)<onclick>.*?</onclick>","<onclick>POWER_COMMAND</onclick>");
      xml=xml.substring(0,m.start())+body+xml.substring(m.end());
    }
    return xml;
  }
  static void put(File file,String text)throws Exception{
    file.getParentFile().mkdirs();Files.writeString(file.toPath(),text,StandardCharsets.UTF_8);
  }
  static String read(File file)throws Exception{return Files.readString(file.toPath(),StandardCharsets.UTF_8);}
  public static void main(String[] args)throws Exception{
    String legacy=Files.readString(Path.of(args[0]),StandardCharsets.UTF_8);
    String conditionalFixture=Files.readString(Path.of(args[1]),StandardCharsets.UTF_8);
    String patched=InfinityPowerMenuRoutes.patch(legacy);
    check(!legacy.equals(patched),"legacy routes unchanged");
    check(maskPower(legacy).equals(maskPower(patched)),"non-command legacy bytes changed");
    check(patched.equals(InfinityPowerMenuRoutes.patch(patched)),"legacy patch not idempotent");
    check(conditionalFixture.equals(InfinityPowerMenuRoutes.patch(conditionalFixture)),
      "195 conditional-route fixture bytes changed");
    for(boolean reverse:new boolean[]{false,true})
      check(paired(reverse).equals(InfinityPowerMenuRoutes.patch(paired(reverse))),"conditional route ordering");
    for(boolean force:new boolean[]{false,true}){
      String command=InfinityPowerMenuRoutes.command(force);
      String[] parts=command.substring(command.indexOf('(')+1,command.length()-1).split(",",-1);
      check(parts.length==9,"wrong Android argument count");
      check(parts[8].equals("com.projectinfinity.kodi.InfinityPowerControlActivity"),"wrong component");
    }
    rejected(paired(false).replace("System.Platform.Android\"","System.Platform.Android + true\""),"unknown condition");
    rejected(paired(false).replace(InfinityPowerMenuRoutes.command(false),"CustomClose()"),"unknown Android route");
    rejected(paired(false).replace("!System.Platform.Android","System.Platform.Android"),"duplicate conditions");
    rejected(paired(false).replace("Quit()","UnknownQuit()"),"unknown desktop fallback");
    rejected(paired(false).replace("<onclick condition=","<onclick extra=\"true\" condition="),"unknown attribute");
    rejected(paired(false).replace("</window>",button("200","CLOSE KODI",click(null,"Quit()"))+"</window>"),"duplicate button");
    rejected(paired(false).replace("</label>","</label>"+click(null,"Quit()")),"extra actions");
    rejected(legacy.replace("<onclick>Quit()</onclick>",click("System.Platform.Android","Quit()")),"single conditional action");
    rejected("<window>","malformed XML");
    rejected("<!DOCTYPE window [<!ENTITY x SYSTEM 'file:///private'>]><window/>","DTD");

    File root=new File(args[2]);Context app=new Context(root);
    File data=new File(root,"data");File skin=new File(data,".kodi/addons/skin.infinity.diggz");
    File unified=new File(skin,"unified/DialogButtonMenu.xml");
    File valid=new File(skin,"16x9/DialogButtonMenu.xml");
    File invalid=new File(skin,"20x9/DialogButtonMenu.xml");
    File later=new File(skin,"6x5/DialogButtonMenu.xml");
    String bad=paired(false).replace(InfinityPowerMenuRoutes.command(false),"Unknown()");
    put(unified,conditionalFixture);put(valid,legacy);put(invalid,bad);put(later,legacy);
    System.setProperty("xbmc.data",data.getAbsolutePath());
    InfinityPowerMenuRoutes.apply(app);
    check(read(unified).equals(conditionalFixture),"approved unified file modified");
    check(read(valid).equals(patched),"valid legacy file not installed");
    check(read(invalid).equals(bad),"unknown file overwritten");
    check(read(later).equals(patched),"rejected profile aborted later valid profile");
    String audit=InfinityPowerMenuRoutes.report(app);
    check(audit.contains("Validated profiles: 3; commands updated: 2; rejected profiles: 1"),"wrong audit counts: "+audit);
    File[] backups=new File(app.getFilesDir(),"infinity-power-route-originals-2103299").listFiles();
    check(backups!=null && backups.length==1,"original backup not deduplicated");
    check(read(backups[0]).equals(legacy),"backup differs from original");
    InfinityPowerMenuRoutes.apply(app);
    check(read(valid).equals(patched) && read(unified).equals(conditionalFixture),"repeat install changed bytes");
    check(InfinityPowerMenuRoutes.report(app).contains("commands updated: 0"),"repeat installer changed commands");
    System.clearProperty("xbmc.data");
    System.out.println("PASS "+checks+" host route/preservation checks; Android/native/device acceptance not simulated.");
  }
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    # Replay just the established 195 Power XML delta on the inherited fixture.
    # It is a regression fixture, not a claim of the complete skin file's hash.
    patch = HERE.parent / "mobile-regressions-2103304/skin-194-repair.patch"
    with tempfile.TemporaryDirectory(prefix="infinity-power-routes-") as directory:
        root = Path(directory)
        fixture = root / "addons/skin.infinity.diggz/unified/DialogButtonMenu.xml"
        fixture.parent.mkdir(parents=True)
        fixture.write_bytes(FIXTURE.read_bytes())
        subprocess.run(["git", "apply", "--include=addons/skin.infinity.diggz/unified/DialogButtonMenu.xml",
                        str(patch.resolve())], cwd=root, check=True)
        sources = root / "src"
        files = dict(STUBS)
        files["com/projectinfinity/kodi/InfinityPowerMenuRoutes.java"] = args.source.read_text().replace(
            "@APP_PACKAGE@", "com.projectinfinity.kodi")
        files["com/projectinfinity/kodi/PowerRouteHostTest.java"] = HARNESS
        for name, content in files.items():
            target = sources / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        classes = root / "classes"
        compiler = ["javac"] if shutil.which("javac") else ["java", "-m", "jdk.compiler/com.sun.tools.javac.Main"]
        subprocess.run([*compiler, "-d", str(classes), *map(str, sources.rglob("*.java"))], check=True)
        subprocess.run(["java", "-cp", str(classes), "com.projectinfinity/kodi/PowerRouteHostTest",
                        str(FIXTURE.resolve()), str(fixture), str(root / "install")], check=True)


if __name__ == "__main__":
    main()
