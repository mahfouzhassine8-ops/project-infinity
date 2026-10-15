"""Execute the actual Java mirror using real files and host Android file adapters."""
from pathlib import Path
import argparse
import runpy
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(); p.add_argument('--json-jar', type=Path, required=True); a = p.parse_args()
    peers = runpy.run_path(str(ROOT / 'test_checkpoint_installer.py'))['STUBS'].copy()
    del peers['com/projectinfinity/kodi/InstallerMain.java']
    peers['android/os/Process.java'] = 'package android.os; public class Process {public static int myPid(){return 123;}}'
    peers['android/os/SystemClock.java'] = 'package android.os; public class SystemClock {public static long elapsedRealtime(){return 123456;}}'
    peers['android/util/AtomicFile.java'] = '''package android.util;
import java.io.*;import java.nio.file.*;
public class AtomicFile {
 private final File path;public AtomicFile(File file){path=file;}
 public byte[] readFully()throws Exception{return Files.readAllBytes(path.toPath());}
 public FileOutputStream startWrite()throws Exception{return new FileOutputStream(path+".new");}
 public void finishWrite(FileOutputStream out)throws Exception{out.close();android.system.Os.rename(path+".new",path.toString());}
 public void failWrite(FileOutputStream out)throws Exception{out.close();Files.deleteIfExists(Paths.get(path+".new"));}
}'''
    peers['com/projectinfinity/kodi/InfinityCheckpointProtocol.java'] = '''package com.projectinfinity.kodi;
import java.io.*;import java.nio.file.*;import java.nio.charset.*;import org.json.*;
final class InfinityCheckpointProtocol {
 static final String RECEIPT="infinity-checkpoint-close.json";
 static JSONObject read(File root)throws Exception{return new JSONObject(new String(Files.readAllBytes(new File(root,RECEIPT).toPath()),StandardCharsets.UTF_8));}
 static String proof(String raw)throws Exception {StringBuilder text=new StringBuilder();for(byte b:java.security.MessageDigest.getInstance("SHA-256").digest(raw.getBytes(StandardCharsets.UTF_8)))text.append(String.format("%02x",b&255));return text.toString();}
}'''
    peers['com/projectinfinity/kodi/MirrorMain.java'] = '''package com.projectinfinity.kodi;
import java.io.*;import java.nio.file.*;import java.nio.charset.*;import org.json.*;
final class MirrorMain {
 public static void main(String[] args)throws Exception {
  File root=new File(args[0]),priv=new File(root,"private"),external=new File(root,"external");priv.mkdirs();external.mkdirs();
  android.content.Context context=new android.content.Context(root);
  File source=new File(priv,InfinityCheckpointProtocol.RECEIPT),destination=new File(external,InfinityCheckpointProtocol.RECEIPT);
  JSONObject row=new JSONObject().put("schema",1).put("pid",77).put("session","session").put("phase","COMPLETE");
  Files.write(source.toPath(),row.toString().getBytes(StandardCharsets.UTF_8));
  InfinityCheckpointEvidence.register(context);
  JSONObject metadata=read(new File(external,"infinity-checkpoint-mirror.json"));
  check(metadata.getString("publication").equals("startup_snapshot"));check(metadata.getString("current_process_health").equals("UNVERIFIED"));
  check(java.util.Arrays.equals(Files.readAllBytes(source.toPath()),Files.readAllBytes(destination.toPath())));
  row.put("phase","CHECKPOINT_FAILED");Files.write(source.toPath(),row.toString().getBytes(StandardCharsets.UTF_8));
  InfinityCheckpointEvidence.mirror(source,row);metadata=read(new File(external,"infinity-checkpoint-mirror.json"));
  check(metadata.getString("publication").equals("coordinator_write"));check(metadata.getString("phase").equals("CHECKPOINT_FAILED"));
  check(metadata.getString("receipt_sha256").equals(InfinityCheckpointProtocol.proof(row.toString())));
  byte[] before=Files.readAllBytes(destination.toPath());row.put("phase","COMPLETE");
  InfinityCheckpointEvidence.mirror(source,row);check(java.util.Arrays.equals(before,Files.readAllBytes(destination.toPath())));
  Files.delete(destination.toPath());File victim=new File(root,"victim");Files.write(victim.toPath(),before);Files.createSymbolicLink(destination.toPath(),victim.toPath());
  Files.write(source.toPath(),row.toString().getBytes(StandardCharsets.UTF_8));InfinityCheckpointEvidence.mirror(source,row);
  check(java.util.Arrays.equals(before,Files.readAllBytes(victim.toPath())));
  System.out.println("PASS actual atomic Java receipt mirror: exact source bytes, startup/current provenance, failed-close update, mismatch and symlink refusal");
 }
 static JSONObject read(File file)throws Exception{return new JSONObject(new String(Files.readAllBytes(file.toPath()),StandardCharsets.UTF_8));}
 static void check(boolean value){if(!value)throw new AssertionError();}
}'''
    with tempfile.TemporaryDirectory(prefix='mirror-host-') as tmp:
        root = Path(tmp)
        for name, content in peers.items():
            path = root / 'src' / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
        source = ROOT / 'runtime/android/overlay/tools/android/packaging/xbmc/src/InfinityCheckpointEvidence.java.in'
        (root / 'src/com/projectinfinity/kodi/InfinityCheckpointEvidence.java').write_text(source.read_text().replace('@APP_PACKAGE@', 'com.projectinfinity.kodi'))
        subprocess.run(['java', 'com.sun.tools.javac.Main', '--release', '8', '-cp', str(a.json_jar), '-d', str(root / 'classes'),
                        *map(str, (root / 'src').rglob('*.java'))], check=True)
        subprocess.run(['java', '-cp', str(root / 'classes') + ':' + str(a.json_jar), 'com.projectinfinity.kodi.MirrorMain', str(root / 'files')], check=True)


if __name__ == '__main__': main()
