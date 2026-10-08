#!/usr/bin/env python3
"""Exercise the actual installer on real files, including hard process-death recovery.

Android Context/Os/Log are host adapters; org.json is the real Android library.
Os rename uses an atomic filesystem move and fsync uses real FileChannel.force.
The production APK asset is not built here: a deterministic synthetic exact-parent
code fixture is used to test transaction semantics without user data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

FILES = ["common.py", "default.py", "experience.py", "plugin.py", "resume_hub.py", "service.py",
         "checkpoint_runtime.py", "persistence_participant.py"]
OLD = {name: ("print('old " + name + "')\n").encode() for name in FILES[:6]}
NEW = {name: ("print('new " + name + "')\n").encode() for name in FILES}
MARKER = b'<addon id="script.infinity.commandcenter" version="0.3.5.19"/>\n'
STUBS = {
"android/content/Context.java": """package android.content;
import java.io.*;
public class Context {
 private final File root;
 public Context(File root){this.root=root;}
 public Context getApplicationContext(){return this;}
 public File getFilesDir(){return new File(root,"private");}
 public File getExternalFilesDir(String ignored){return new File(root,"external");}
 public android.content.res.AssetManager getAssets(){return new android.content.res.AssetManager(new File(root,"assets"));}
}
""",
"android/content/res/AssetManager.java": """package android.content.res;
import java.io.*;
public class AssetManager {
 private final File root; public AssetManager(File root){this.root=root;}
 public InputStream open(String name)throws Exception{return new FileInputStream(new File(root,name));}
}
""",
"android/util/Log.java": """package android.util;
public class Log {public static int e(String a,String b){System.out.println(b);return 0;}
 public static int w(String a,String b){System.out.println(b);return 0;}
 public static int i(String a,String b){System.out.println(b);return 0;}}
""",
"android/system/OsConstants.java": """package android.system;
public class OsConstants {public static final int O_RDONLY=0; public static boolean S_ISDIR(int mode){return mode==0040000;}}
""",
"android/system/StructStat.java": """package android.system;
public class StructStat {public final int st_mode;public StructStat(int mode){st_mode=mode;}}
""",
"android/system/Os.java": """package android.system;
import java.io.*;import java.nio.channels.*;import java.nio.file.*;import java.util.*;
public class Os {
 private static final Map<FileDescriptor,FileChannel> channels=new IdentityHashMap<>();
 private static final Map<FileDescriptor,Path> paths=new IdentityHashMap<>();
 private static int codeRenames=0;private static boolean injected=false;
 public static FileDescriptor open(String path,int flags,int mode)throws Exception {
  FileDescriptor fd=new FileDescriptor();Path p=Paths.get(path);
  channels.put(fd,FileChannel.open(p,StandardOpenOption.READ));paths.put(fd,p);return fd;
 }
 public static StructStat fstat(FileDescriptor fd){return new StructStat(Files.isDirectory(paths.get(fd))?0040000:0100000);}
 public static void fsync(FileDescriptor fd)throws Exception{channels.get(fd).force(true);}
 public static void close(FileDescriptor fd)throws Exception{channels.remove(fd).close();paths.remove(fd);}
 public static void rename(String oldPath,String newPath)throws Exception {
  Files.move(Paths.get(oldPath),Paths.get(newPath),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
  if(newPath.endsWith(".py")) {
   ++codeRenames;String mode=System.getProperty("infinity.test.mode","");
   if(mode.equals("crash") && codeRenames==3)Runtime.getRuntime().halt(73);
   if(mode.equals("fail") && !injected){injected=true;throw new IOException("injected rename followup failure");}
  }
 }
}
""",
"com/projectinfinity/kodi/InstallerMain.java": """package com.projectinfinity.kodi;
public class InstallerMain {public static void main(String[] args){
 boolean result=InfinityCheckpointAddonInstaller.applyBeforeNative(new android.content.Context(new java.io.File(args[0])));
 System.out.println("INSTALL_RESULT="+result);System.exit(result?0:10);
}}
""",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_asset(root):
    manifest = {"schema": 1, "addon_id": "script.infinity.commandcenter", "addon_version": "0.3.5.19",
                "addon_xml_sha256": sha(MARKER), "files": [
                    {"path": name, "before": sha(OLD[name]) if name in OLD else None, "after": sha(NEW[name])}
                    for name in FILES]}
    path = root / "fixture.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, separators=(",", ":")))
        for name in FILES:
            archive.writestr("payload/" + name, NEW[name])
    return path.read_bytes()


def initialize(root, asset):
    addon = root / "external/.kodi/addons/script.infinity.commandcenter"
    addon.mkdir(parents=True)
    (root / "private").mkdir()
    assets = root / "assets/infinity"
    assets.mkdir(parents=True)
    (assets / "checkpoint-controller.zip").write_bytes(asset)
    (addon / "addon.xml").write_bytes(MARKER)
    for name, data in OLD.items():
        (addon / name).write_bytes(data)
    (addon / "skin_upgrade.py").write_bytes(b"PRESERVED unrelated code\n")
    user = root / "external/.kodi/userdata/addon_data/script.infinity.commandcenter"
    user.mkdir(parents=True)
    (user / "resume_hub.json").write_bytes(b"PRESERVED resume state\n")
    return addon


def contents(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--android-jar", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="infinity-installer-test-") as temporary:
        work = Path(temporary)
        asset = make_asset(work)
        sources = work / "src"
        for relative, text in STUBS.items():
            path = sources / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        production = args.source / "tools/android/packaging/xbmc/src/InfinityCheckpointAddonInstaller.java.in"
        code = production.read_text().replace("@APP_PACKAGE@", "com.projectinfinity.kodi")
        # Test the actual algorithm with this synthetic fixture's trusted asset digest.
        import re
        code, count = re.subn(r'ASSET_SHA256 = "[^"]+";', 'ASSET_SHA256 = "' + sha(asset) + '";', code)
        assert count == 1
        (sources / "com/projectinfinity/kodi/InfinityCheckpointAddonInstaller.java").write_text(code)
        classes = work / "classes"
        subprocess.run(["java", "com.sun.tools.javac.Main", "--release", "8", "-Xlint:all", "-Werror",
                        "-cp", str(args.android_jar), "-d", str(classes),
                        *[str(path) for path in sorted(sources.rglob("*.java"))]], check=True)

        def run(root, mode="", expected=0):
            result = subprocess.run(["java", "-Dinfinity.test.mode=" + mode,
                                     "-cp", str(classes) + ":" + str(args.android_jar),
                                     "com.projectinfinity.kodi.InstallerMain", str(root)],
                                    text=True, capture_output=True, timeout=20)
            assert result.returncode == expected, result.stdout + result.stderr
            return result

        def check_installed(addon):
            for name, data in NEW.items():
                assert (addon / name).read_bytes() == data
            assert (addon / "addon.xml").read_bytes() == MARKER
            assert (addon / "skin_upgrade.py").read_bytes() == b"PRESERVED unrelated code\n"

        root = work / "success"
        addon = initialize(root, asset)
        run(root)
        check_installed(addon)
        before = contents(root / "external")
        run(root)
        assert contents(root / "external") == before
        print("PASS successful exact overlay and idempotent retry preserve marker/unrelated files/data")

        root = work / "unknown"
        addon = initialize(root, asset)
        (addon / "experience.py").write_bytes(b"user-customized code\n")
        before = contents(root / "external")
        run(root, expected=10)
        assert contents(root / "external") == before
        print("PASS unknown installed preimage refuses all mutations")

        root = work / "bad-asset"
        addon = initialize(root, asset + b"corruption")
        before = contents(root / "external")
        run(root, expected=10)
        assert contents(root / "external") == before
        print("PASS corrupt trusted asset refuses all mutations")

        root = work / "rollback"
        addon = initialize(root, asset)
        before = contents(root / "external")
        run(root, mode="fail", expected=10)
        assert contents(root / "external") == before
        run(root)
        check_installed(addon)
        print("PASS real atomic-write failure rolls back all code before retry")

        root = work / "crash"
        addon = initialize(root, asset)
        run(root, mode="crash", expected=73)
        assert (root / "private/infinity-checkpoint-code-transaction/journal.json").is_file()
        run(root)
        check_installed(addon)
        print("PASS hard process death mid-overlay recovers and installs on next startup")

        root = work / "recovery-unknown"
        addon = initialize(root, asset)
        run(root, mode="crash", expected=73)
        (addon / "common.py").write_bytes(b"new user edit after interrupted install\n")
        before = contents(root / "external")
        run(root, expected=10)
        assert contents(root / "external") == before
        print("PASS interrupted recovery never overwrites an unknown user edit")

        root = work / "recovery-corrupt"
        addon = initialize(root, asset)
        run(root, mode="crash", expected=73)
        (root / "private/infinity-checkpoint-code-transaction/backup-0").write_bytes(b"damaged backup")
        before = contents(root / "external")
        run(root, expected=10)
        assert contents(root / "external") == before
        print("PASS corrupt backup blocks recovery before any installed-file mutation")


if __name__ == "__main__":
    main()
