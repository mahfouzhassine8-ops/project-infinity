"""Build a shell-run, public-UiAutomator QA DEX JAR; never builds/installs an APK.

SDK stubs come only from Google's exact official platform-34 archive, whose
size/SHA1 are published in repository2-3.xml. All extracted/used bytes get SHA256
records. Runtime implementation remains the emulator's own uiautomator classes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import urllib.request
import zipfile

SDK_URL = "https://dl.google.com/android/repository/platform-34-ext7_r03.zip"
SDK_BYTES = 63180081
SDK_SHA1 = "1f2e9478d6a7601425ceaa553311dc43191f103d"
SDK_SHA256 = "16fdb74c55e59ae3ef52def135aec713508467bd56d7dabcd8c9be31fa8b20f3"
SDK_MEMBERS = (
    "android-34/android.jar",
    "android-34/uiautomator.jar",
    "android-34/optional/android.test.base.jar",
    "android-34/optional/android.test.runner.jar",
)


def digest(path, algorithm="sha256"):
    result = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def build(out, d8, android=None, sdk_archive=None):
    out.mkdir(parents=True, exist_ok=True)
    d8 = d8.resolve()
    assert d8.is_file(), "Existing trusted D8 JAR required"
    archive = sdk_archive or out / "platform-34-ext7_r03.zip"
    if not archive.exists():
        assert sdk_archive is None, "Specified cached SDK archive missing"
        partial = archive.with_suffix(".download")
        with urllib.request.urlopen(SDK_URL, timeout=30) as response, partial.open("wb") as target:
            shutil.copyfileobj(response, target, 1024 * 1024)
        partial.replace(archive)
    assert archive.stat().st_size == SDK_BYTES, "Official SDK archive size mismatch"
    assert digest(archive, "sha1") == SDK_SHA1, "Official SDK archive checksum mismatch"
    assert digest(archive) == SDK_SHA256, "Official SDK archive SHA256 mismatch"
    sdk = out / "sdk-stubs"
    sdk.mkdir(exist_ok=True)
    dependencies = []
    with zipfile.ZipFile(archive) as source:
        for member in SDK_MEMBERS:
            target = sdk / Path(member).name
            target.write_bytes(source.read(member))
            if not member.endswith("/android.jar"):
                dependencies.append(target)
    android = android.resolve() if android is not None else (sdk / "android.jar").resolve()
    assert android.is_file(), "Android compiler API JAR missing"
    java = shutil.which("java")
    assert java, "Java required"
    javac = shutil.which("javac")
    compiler = [javac] if javac else [java, "-m", "jdk.compiler/com.sun.tools.javac.Main"]
    source = Path(__file__).resolve().parent / "qa/android/CobraNativeButtonProbe.java"
    classes = out / "classes"
    classes.mkdir(exist_ok=True)
    classpath = ":".join(map(str, (android, *dependencies)))
    compile_command = compiler + ["-source", "8", "-target", "8", "-cp", classpath,
                                  "-d", str(classes), str(source)]
    subprocess.run(compile_command, check=True)
    class_files = sorted(classes.rglob("*.class"))
    assert {str(p.relative_to(classes)) for p in class_files} == {
        "qa/CobraNativeButtonProbe.class", "qa/CobraNativeButtonProbe$Hit.class"}, "Unexpected QA classes"
    program = out / "qa-classes.jar"
    with zipfile.ZipFile(program, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for item in class_files:
            target.write(item, item.relative_to(classes))
    dex = out / "dex"
    dex.mkdir(exist_ok=True)
    command = [java, "-cp", str(d8), "com.android.tools.r8.D8", "--min-api", "23",
               "--lib", str(android)]
    for dependency in dependencies:
        command += ["--lib", str(dependency)]
    command += ["--output", str(dex), str(program)]
    subprocess.run(command, check=True)
    assert sorted(p.name for p in dex.iterdir()) == ["classes.dex"], "Unexpected DEX output"
    dex_bytes = (dex / "classes.dex").read_bytes()
    assert dex_bytes.startswith(b"dex\n"), "Not a DEX file"
    strings_count, strings_offset = struct.unpack_from("<II", dex_bytes, 56)
    types_count, types_offset = struct.unpack_from("<II", dex_bytes, 64)
    class_count, classes_offset = struct.unpack_from("<II", dex_bytes, 96)
    def descriptor(class_index):
        type_index = struct.unpack_from("<I", dex_bytes, classes_offset + class_index * 32)[0]
        assert type_index < types_count
        string_index = struct.unpack_from("<I", dex_bytes, types_offset + type_index * 4)[0]
        assert string_index < strings_count
        offset = struct.unpack_from("<I", dex_bytes, strings_offset + string_index * 4)[0]
        while dex_bytes[offset] & 0x80:
            offset += 1
        offset += 1
        return dex_bytes[offset:dex_bytes.index(0, offset)].decode("ascii")
    dex_classes = sorted(descriptor(i) for i in range(class_count))
    assert dex_classes == ["Lqa/CobraNativeButtonProbe$Hit;", "Lqa/CobraNativeButtonProbe;"], "Unexpected DEX classes"
    result = out / "CobraNativeButtonProbe.jar"
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as target:
        target.write(dex / "classes.dex", "classes.dex")
    record = {
        "scope": "QA_ONLY_PUBLIC_UIAUTOMATOR_DEX_JAR_NO_APK",
        "official_sdk_url": SDK_URL,
        "official_sdk_bytes": SDK_BYTES,
        "official_sdk_sha1": SDK_SHA1,
        "official_sdk_sha256": digest(archive),
        "SDK_members": {name: digest(sdk / Path(name).name) for name in SDK_MEMBERS},
        "android_jar_sha256": digest(android), "D8_jar_sha256": digest(d8),
        "source_sha256": digest(source), "class_files": [str(p.relative_to(classes)) for p in class_files],
        "inspected_DEX_classes": dex_classes,
        "DEX_sha256": digest(dex / "classes.dex"), "QA_JAR_sha256": digest(result),
        "runtime_classes": "OS /system/framework/uiautomator.jar and android.test.runner.jar; not bundled",
        "application_APK": "UNCHANGED_NOT_BUILT_OR_INSTALLED",
        "shutdown": "NOT_RUN", "CI_runtime": "NOT_RUN",
    }
    (out / "BUILD-RECEIPT.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("out", "d8"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--android", type=Path)
    parser.add_argument("--sdk-archive", type=Path)
    build(**vars(parser.parse_args()))
