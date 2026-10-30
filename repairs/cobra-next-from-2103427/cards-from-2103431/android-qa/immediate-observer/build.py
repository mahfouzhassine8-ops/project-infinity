"""Build only the standalone QA observer DEX JAR, using existing pinned tools.

No downloads, APK generation, installation, device execution or test runner.
The platform wrapper/dumper implementations remain in the device OS archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile


HERE = Path(__file__).resolve().parent
ANDROID_SHA256 = "6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad"
D8_SHA256 = "305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5"
OWN_CLASS = "qa/CobraImmediateHierarchy.class"
OWN_DESCRIPTOR = "Lqa/CobraImmediateHierarchy;"
OWN_CLASSES = {
    OWN_CLASS,
    "qa/CobraImmediateHierarchy$ReadinessSignal.class",
    "qa/CobraImmediateHierarchy$RootReadiness.class",
}
OWN_DESCRIPTORS = sorted([
    OWN_DESCRIPTOR,
    "Lqa/CobraImmediateHierarchy$ReadinessSignal;",
    "Lqa/CobraImmediateHierarchy$RootReadiness;",
])
PLATFORM_CLASS_PATH = (
    "/system/framework/android.test.runner.jar:"
    "/system/framework/uiautomator.jar"
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_inputs(android: Path, d8: Path, source: Path) -> None:
    assert android.is_file() and digest(android) == ANDROID_SHA256, "Pinned official Android34 JAR required"
    assert d8.is_file() and digest(d8) == D8_SHA256, "Pinned official SDK35 D8 JAR required"
    code = source.read_text()
    assert re.search(r"\bpackage\s+qa\s*;", code), "QA-only package required"
    assert re.search(r"\bpublic\s+final\s+class\s+CobraImmediateHierarchy\b", code), "Exact QA main class required"
    # Comments may explain why these APIs are omitted; invocations/reflection
    # literals are forbidden. No platform implementation is compiled here.
    executable = re.sub(r"/\*.*?\*/|//[^\n]*", "", code, flags=re.S)
    forbidden = (
        "waitForIdle", "injectInputEvent", "executeShellCommand", "setRunAsMonkey",
        "adoptShellPermissionIdentity", "setHiddenApiExemptions", "reboot",
    )
    for name in forbidden:
        assert not re.search(r"\b" + re.escape(name) + r"\s*\(|[\"']" + re.escape(name) + r"[\"']", executable), "Forbidden observer API: " + name
    assert not re.search(r"\bimport\s+(?:junit\.|org\.junit\.|com\.android\.uiautomator\.testrunner\.)", executable), "No legacy/JUnit runner allowed"
    assert "UiAutomatorTestCase" not in executable and "UiAutomatorTestRunner" not in executable, "No legacy test entry allowed"
    assert "Runtime.getRuntime" not in executable and "ProcessBuilder" not in executable, "Observer must not execute arbitrary commands"


def dex_descriptors(raw: bytes) -> list[str]:
    """Read actual class definitions, refusing malformed/foreign DEX classes."""
    assert len(raw) >= 112 and raw[:4] == b"dex\n" and raw[7] == 0, "DEX header required"
    declared_size, header_size, endian = struct.unpack_from("<III", raw, 32)
    assert declared_size == len(raw) and header_size == 112 and endian == 0x12345678, "Unexpected DEX layout"
    strings_count, strings_offset = struct.unpack_from("<II", raw, 56)
    types_count, types_offset = struct.unpack_from("<II", raw, 64)
    class_count, classes_offset = struct.unpack_from("<II", raw, 96)
    for count, offset, width in ((strings_count, strings_offset, 4), (types_count, types_offset, 4), (class_count, classes_offset, 32)):
        assert count > 0 and 0 <= offset <= len(raw) and count <= (len(raw) - offset) // width, "Truncated DEX table"
    result = []
    for index in range(class_count):
        type_index = struct.unpack_from("<I", raw, classes_offset + index * 32)[0]
        assert type_index < types_count, "Invalid DEX class type"
        string_index = struct.unpack_from("<I", raw, types_offset + type_index * 4)[0]
        assert string_index < strings_count, "Invalid DEX descriptor string"
        offset = struct.unpack_from("<I", raw, strings_offset + string_index * 4)[0]
        assert offset < len(raw), "Invalid DEX string offset"
        # Descriptor names are ASCII and short; skip a valid bounded ULEB128.
        for byte in range(5):
            assert offset < len(raw), "Truncated DEX UTF length"
            value = raw[offset]
            offset += 1
            if value & 0x80 == 0:
                break
        else:
            raise AssertionError("Invalid DEX UTF length")
        end = raw.find(b"\0", offset)
        assert end >= offset, "Unterminated DEX descriptor"
        result.append(raw[offset:end].decode("ascii"))
    assert len(result) == len(set(result)), "Duplicate DEX class definitions"
    return sorted(result)


def write_jar(path: Path, members: dict[str, bytes]) -> None:
    """Stable ZIP metadata keeps transport hashes independent of file mtimes."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)


def build(android: Path, d8: Path, out: Path) -> dict:
    android, d8, out = android.resolve(), d8.resolve(), out.resolve()
    source = HERE / "CobraImmediateHierarchy.java"
    source_sha256 = digest(source)
    verify_inputs(android, d8, source)
    assert not out.exists(), "Fresh QA output folder required; prior evidence must not be overwritten"
    out.mkdir(parents=True)
    java = shutil.which("java")
    assert java, "Existing Java required"
    javac = shutil.which("javac")
    compiler = [javac] if javac else [java, "-m", "jdk.compiler/com.sun.tools.javac.Main"]
    snapshot = out / "source/qa/CobraImmediateHierarchy.java"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(source.read_bytes())
    assert digest(snapshot) == source_sha256, "Reviewed Java source changed before compilation"
    classes = out / "classes"
    classes.mkdir()
    compile_command = compiler + ["-source", "8", "-target", "8", "-cp", str(android), "-d", str(classes), str(snapshot)]
    subprocess.run(compile_command, check=True)
    class_files = {str(path.relative_to(classes)): path for path in classes.rglob("*.class")}
    assert set(class_files) == OWN_CLASSES, "Only the three explicitly approved QA observer classes may be compiled"
    program = out / "observer-classes.jar"
    write_jar(program, {name: path.read_bytes() for name, path in class_files.items()})
    dex = out / "dex"
    dex.mkdir()
    d8_command = [java, "-cp", str(d8), "com.android.tools.r8.D8", "--min-api", "23", "--lib", str(android), "--output", str(dex), str(program)]
    subprocess.run(d8_command, check=True)
    assert sorted(path.name for path in dex.iterdir()) == ["classes.dex"], "Single observer DEX required"
    raw = (dex / "classes.dex").read_bytes()
    descriptors = dex_descriptors(raw)
    assert descriptors == OWN_DESCRIPTORS, "Foreign or extra classes must not be bundled"
    result = out / "CobraImmediateHierarchy.jar"
    write_jar(result, {"classes.dex": raw})
    assert digest(source) == source_sha256, "Reviewed Java source changed during compilation"
    provenance = HERE / "SOURCE-PROVENANCE.json"
    record = {
        "scope": "QA_ONLY_IMMEDIATE_PLATFORM_ROOT_OBSERVER_NO_APK",
        "source_sha256": source_sha256,
        "compiled_source_snapshot_sha256": digest(snapshot),
        "build_script_sha256": digest(Path(__file__).resolve()),
        "android_jar_sha256": digest(android),
        "D8_jar_sha256": digest(d8),
        "compiler_command": compile_command,
        "D8_command": d8_command,
        "class_files_sha256": {name: digest(path) for name, path in class_files.items()},
        "inspected_DEX_classes": descriptors,
        "DEX_sha256": digest(dex / "classes.dex"),
        "QA_JAR_sha256": digest(result),
        "QA_JAR_bytes": result.stat().st_size,
        "platform_source_provenance_sha256": digest(provenance),
        "runtime_application_classpath_prefix": PLATFORM_CLASS_PATH,
        "runtime_BOOTCLASSPATH": "INHERITED_OS_UNCHANGED",
        "platform_classes": "REFLECT_EXISTING_SYSTEM_ARCHIVE_ONLY; NOT_BUNDLED",
        "API_surface": "FAIL_CLOSED_DEVICE_PREFLIGHT_REQUIRED_BEFORE_OBSERVATION",
        "APK_build_or_install": "NONE",
        "application_or_device_execution": "NOT_RUN",
        "CI": "NOT_DISPATCHED",
        "shutdown": "NOT_RUN",
    }
    (out / "BUILD-RECEIPT.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("android", "d8", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    print(json.dumps(build(**vars(parser.parse_args())), indent=2))
