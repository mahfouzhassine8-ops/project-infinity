#!/usr/bin/env python3
"""Exercise the actual installer on real files, including hard process-death recovery.

Android Context/Os/Log are host adapters; org.json is the real Android library.
Os rename uses an atomic filesystem move and fsync uses real FileChannel.force.
By default a synthetic exact-parent code fixture tests transaction semantics.
--production-asset/--parent-addon exercise the unmodified production hash pin and
reviewed payload against all preserved original add-on files, without user data.
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
PRESERVED = {"skin_upgrade.py": b"PRESERVED unrelated code\n"}
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
    for name, data in PRESERVED.items():
        target = addon / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    user = root / "external/.kodi/userdata/addon_data/script.infinity.commandcenter"
    user.mkdir(parents=True)
    (user / "resume_hub.json").write_bytes(b"PRESERVED resume state\n")
    return addon


def contents(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def main():
    global OLD, NEW, MARKER, PRESERVED
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--android-jar", type=Path, required=True)
    parser.add_argument("--production-asset", type=Path)
    parser.add_argument("--parent-addon", type=Path)
    parser.add_argument("--controller20", action="store_true")
    args = parser.parse_args()
    if bool(args.production_asset) != bool(args.parent_addon):
        parser.error("--production-asset and --parent-addon must be supplied together")
    with tempfile.TemporaryDirectory(prefix="infinity-installer-test-") as temporary:
        work = Path(temporary)
        if args.production_asset:
            import participant_asset
            asset = args.production_asset.read_bytes()
            if args.controller20:
                import android_ci
                assert asset == android_ci.installed_build.build('script.infinity.commandcenter')
            else:
                assert asset == participant_asset.build(), "Production asset differs from reviewed build"
            parent = contents(args.parent_addon)
            delta = json.loads((Path(__file__).parent / "runtime/commandcenter/manifest.json").read_text())
            if args.controller20:
                delta = json.loads((Path(__file__).parent / 'installed/manifest.json').read_text())['script.infinity.commandcenter']
            assert {name: sha(data) for name, data in parent.items()} == delta["before"], "Wrong original add-on preimages"
            OLD = {name: parent[name] for name in FILES if name in parent}
            MARKER = parent["addon.xml"]
            PRESERVED = {name: data for name, data in parent.items() if name not in FILES and name != "addon.xml"}
            with zipfile.ZipFile(args.production_asset) as archive:
                NEW = {name: archive.read("payload/" + name) for name in FILES}
        else:
            asset = make_asset(work)
        sources = work / "src"
        for relative, text in STUBS.items():
            path = sources / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        production = args.source / "tools/android/packaging/xbmc/src/InfinityCheckpointAddonInstaller.java.in"
        if args.controller20:
            production = production.with_name('InfinityCheckpointController20Installer.java.in')
        code = production.read_text().replace("@APP_PACKAGE@", "com.projectinfinity.kodi")
        if args.controller20:
            code = code.replace('InfinityCheckpointController20Installer', 'InfinityCheckpointAddonInstaller')
            code = code.replace('checkpoint-controller-20.zip', 'checkpoint-controller.zip')
            code = code.replace('infinity-infinitycheckpointcontroller20installer', 'infinity-checkpoint-code')
        import re
        if args.production_asset:
            assert 'ASSET_SHA256 = "' + sha(asset) + '";' in code, "Unmodified production installer hash mismatch"
        else:
            # The synthetic fixture changes only the trusted digest in the test copy.
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
            for name, data in PRESERVED.items():
                assert (addon / name).read_bytes() == data

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
        transaction = root / "private/infinity-checkpoint-code-transaction"
        journal = json.loads((transaction / "journal.json").read_text())
        backup_index = next(index for index, entry in enumerate(journal["files"]) if entry["existed"])
        (transaction / ("backup-" + str(backup_index))).write_bytes(b"damaged backup")
        before = contents(root / "external")
        run(root, expected=10)
        assert contents(root / "external") == before
        print("PASS corrupt backup blocks recovery before any installed-file mutation")
        if args.production_asset:
            print("PASS all installer recovery cases used the unchanged production hash pin, exact reviewed asset, and exact original add-on preimages")


if __name__ == "__main__":
    main()
