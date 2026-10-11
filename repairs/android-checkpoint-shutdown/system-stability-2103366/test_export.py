"""Actual bounded Java code-identity/timing collector with a filesystem Context."""
import argparse
from pathlib import Path
import subprocess
import tempfile

CONTEXT = '''package android.content;
public class Context {
 private final java.io.File root;
 public Context(java.io.File root){this.root=root;}
 public java.io.File getExternalFilesDir(String unused){return new java.io.File(root,"external");}
 public java.io.File getFilesDir(){return new java.io.File(root,"private");}
}
'''
MAIN = r'''
package com.projectinfinity.kodi;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import org.json.*;
public class EvidenceTest {
 static void require(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args)throws Exception {
  File root=new File(args[0]);android.content.Context context=new android.content.Context(root);
  File addon=new File(root,"external/.kodi/addons/script.kodihealthcenter");addon.mkdirs();
  Files.write(new File(addon,"addon.xml").toPath(),"<addon id='script.kodihealthcenter' version='2.5.18'/>".getBytes(StandardCharsets.UTF_8));
  Files.write(new File(addon,"default.py").toPath(),"reviewed code".getBytes(StandardCharsets.UTF_8));
  Files.write(new File(addon,"settings.xml").toPath(),"PRIVATE AUTHORIZATION DATA".getBytes(StandardCharsets.UTF_8));
  JSONObject observed=InfinityInstalledCodeEvidence.collect(context);
  JSONObject health=observed.getJSONArray("addons").getJSONObject(1);
  require(health.getString("state").equals("OBSERVED_CODE"));require(health.getString("version").equals("2.5.18"));
  require(health.getJSONObject("code_sha256").getString("default.py").length()==64);
  require(!observed.toString().contains("PRIVATE"));require(!observed.toString().contains("settings.xml"));
  require(!observed.getBoolean("proves_shutdown_or_health"));
  File log=new File(root,"external/.kodi/temp/kodi.log");log.getParentFile().mkdirs();
  String line="INFINITY_RESUME_TIMING {\"schema\":1,\"stage\":\"plugin_complete\",\"request\":\"n123\",\"media\":\"tv\",\"monotonic_ms\":1234,\"elapsed_ms\":8,\"items\":2,\"route\":\"SECRET_TOKEN\"}\n";
  Files.write(log.toPath(),("private unrelated log\n"+line+"INFINITY_RESUME_TIMING malformed\n").getBytes(StandardCharsets.UTF_8));
  String timing=InfinityInstalledCodeEvidence.timings(context,false);
  JSONObject row=new JSONObject(timing.trim());require(row.getInt("items")==2);require(!timing.contains("SECRET"));require(!timing.contains("private"));
  require(InfinityInstalledCodeEvidence.timings(context,true).isEmpty());
  Files.delete(new File(addon,"default.py").toPath());
  Files.createSymbolicLink(new File(addon,"default.py").toPath(),new File(addon,"settings.xml").toPath());
  require(InfinityInstalledCodeEvidence.collect(context).getJSONArray("addons").getJSONObject(1).getString("state").equals("UNVERIFIED"));
  System.out.println("PASS actual code identity, version/digests, missing-package distinction, symlink refusal and numeric-only timing export");
 }
}
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--json-jar', type=Path, required=True)
    a = p.parse_args()
    source = Path(__file__).parents[1] / 'runtime/android/overlay/tools/android/packaging/xbmc/src/InfinityInstalledCodeEvidence.java.in'
    with tempfile.TemporaryDirectory(prefix='integration-export-') as tmp:
        tmp = Path(tmp)
        files = {'android/content/Context.java': CONTEXT,
                 'com/projectinfinity/kodi/EvidenceTest.java': MAIN,
                 'com/projectinfinity/kodi/InfinityInstalledCodeEvidence.java': source.read_text().replace('@APP_PACKAGE@', 'com.projectinfinity.kodi')}
        for name, content in files.items():
            target = tmp / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        classes = tmp / 'classes'
        subprocess.run(['java', 'com.sun.tools.javac.Main', '--release', '8', '-Xlint:all', '-Werror',
                        '-cp', str(a.json_jar), '-d', str(classes), *[str(tmp / n) for n in files]], check=True)
        subprocess.run(['java', '-cp', str(classes) + ':' + str(a.json_jar),
                        'com.projectinfinity.kodi.EvidenceTest', str(tmp / 'files')], check=True, timeout=15)


if __name__ == '__main__':
    main()
