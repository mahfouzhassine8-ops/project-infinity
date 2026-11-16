"""Exact502 lock-only DEX assembly and preservation; no APK writer or installer."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OWNER = "Lcom/projectinfinity/kodi/Main;"
BRIDGE = "Lcom/projectinfinity/kodi/InfinityVideoLockBridge;"
MAIN_PATH = "com/projectinfinity/kodi/Main.smali"
BASE_DEX = "5634f2376e5d0bf6176ebef6fa1ac16bb22fdecc1d018ac078f266bb757fe9b8"
BASE_MAIN = "484c40e499c3d1c2109297486b7c2bbde86bb6223279cad27d04070ee818f9dc"
DEX_READER = ROOT / "repairs/infinity-movies-continue-cast-2103486-20261112/cast/dex_contract.py"
DEX_READER_SHA = "c01cce69deacb207633bfd70f1d6d1f56aa3d21972fb3685b7e9a1d7e01739e4"
METHODS = re.compile(r"^\.method[^\n]*\n.*?^\.end method$", re.M | re.S)
NEW_CLASS = re.compile(r"Lcom/projectinfinity/kodi/InfinityVideoLock(?:State|Dialog|Bridge)(?:\$[^;]+)?;")
TOOLS = {
    "ST4-4.0.8.jar": "58caabc40c9f74b0b5993fd868e0f64a50c0759094e6a251aaafad98edfc7a3b",
    "animal-sniffer-annotations-1.17.jar": "92654f493ecfec52082e76354f0ebf87648dc3d5cec2e3c3cdb947c016747a53",
    "antlr-2.7.7.jar": "88fbda4b912596b9f56e8e12e580cc954bacfb51776ecfddd3e18fc1cf56dc4c",
    "antlr-3.5.2.jar": "5ac36c2acfb0a0f3d37dafe20b5b570f2643e2d000c648d44503c2738be643df",
    "antlr-runtime-3.5.2.jar": "ce3fc8ecb10f39e9a3cddcbb2ce350d272d9cd3d0b1e18e6fe73c3b9389c8734",
    "baksmali-2.5.2.jar": "1ed236266d7dc4907aade0b19a34f77efac25342b63c8ace52e579039941b389",
    "checker-compat-qual-2.5.2.jar": "d7291cebf5e158d169807ae49d4b16ff672986f0c6d803e5f207c40cb61ef982",
    "dexlib2-2.5.2.jar": "5a5c8982d8bd7d6e3bb1a0713049e3c78b719ec32b20f6b619885cec30a0dd61",
    "error_prone_annotations-2.2.0.jar": "6ebd22ca1b9d8ec06d41de8d64e0596981d9607b42035f9ed374f9de271a481a",
    "failureaccess-1.0.1.jar": "a171ee4c734dd2da837e4b16be9df4661afab72a41adaf31eb84dfdaf936ca26",
    "guava-27.1-android.jar": "686404f2d1d4d221911f96bd627ff60dac2226a5dfa6fb8ba517073eb97ec0ef",
    "j2objc-annotations-1.1.jar": "2994a7eb78f2710bd3d3bfb639b2c94e219cedac0d4d084d516e78c16dddecf6",
    "jcommander-1.64.jar": "156be736199c990321d9ff77090b199629cfc9865e2d6c13f7cd291bb1641817",
    "jsr305-3.0.2.jar": "766ad2a0783f2687962c8ad74ceecc38a28b9f72a2d085ee438b7813e928d0c7",
    "listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar": "b372a037d4230aa57fbeffdef30fd6123f9c0c2db85d0aced00c91b974f33f99",
    "smali-2.5.2.jar": "136c5c4653d6531bd7b6f10f35f8691cb96432e727d30b4d5579826ee01e9419",
    "stringtemplate-3.2.1.jar": "f66ce72e965e5301cb0f020e54d2ba6ad76feb91b3cbfc30dbbf00c06a6df6d7",
    "util-2.5.2.jar": "4f580a9cff3ebb83cb3fd20bec88e37e4f183796ca652732992611620282daea",
}
ECJ_SHA = "cde026ff966b48b5e5f148b6f041ceff3cf4f85cf75155f4ec0f40e4ee14b545"
ANDROID_SHA = "6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad"
D8_SHA = "305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def normalize(text):
    def method(match):
        block = match.group(0)
        # Baksmali definitions use four spaces. Packed-switch payload targets
        # use eight spaces and may legally repeat; they are references.
        labels = re.findall(r"^    (:[A-Za-z0-9_]+)[ \t]*$", block, re.M)
        require(len(labels) == len(set(labels)), "Duplicate method label")
        mapping = {label: ":label_" + str(i) for i, label in enumerate(labels)}
        # Labels inside quoted constants/annotations are data, not branch targets.
        return re.sub(r'"(?:\\.|[^"\\])*"|:[A-Za-z0-9_]+',
                      lambda found: mapping.get(found.group(0), found.group(0))
                      if not found.group(0).startswith('"') else found.group(0), block)
    text = METHODS.sub(method, text)
    return "\n".join(line.strip() for line in text.splitlines()
                     if line.strip() and not line.lstrip().startswith(("#", ".line ")))


def erase_calls(text, hooks):
    observed = Counter()
    def method(match):
        block = match.group(0)
        signature = block.splitlines()[0].split()[-1]
        if signature not in hooks:
            require(BRIDGE not in block, "Unexpected Bridge reference in original Main method")
            return block
        name, second, _ = hooks[signature]
        registers = "p0 .. p1" if second else "p0 .. p0"
        line = f"    invoke-static/range {{{registers}}}, {BRIDGE}->{name}({OWNER}{'Z' if second else ''})V"
        require(block.splitlines().count(line) == 1, "Missing or duplicate exact hook: " + signature)
        observed[signature] += 1
        return block.replace(line + "\n", "", 1)
    restored = METHODS.sub(method, text)
    require(set(observed) == set(hooks) and all(v == 1 for v in observed.values()), "Seven-hook inventory changed")
    require(BRIDGE not in restored, "Unexpected residual Bridge reference")
    return restored


def declared(definitions, owner, member, kind, seen=None):
    seen = set() if seen is None else seen
    if owner.startswith("["):
        owner = "Ljava/lang/Object;"
    if owner in seen or owner not in definitions:
        return False
    seen.add(owner)
    cls = definitions[owner]
    if member in cls[kind]:
        return True
    if member[0] == "<init>":
        return False
    return any(declared(definitions, parent, member, kind, seen)
               for parent in [cls["parent"], *cls["interfaces"]] if parent)


def jar_from(folder, target):
    files = sorted(folder.rglob("*.class"))
    require(bool(files), "Empty class output")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            name = path.relative_to(folder).as_posix()
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return [p.relative_to(folder).as_posix() for p in files]


def build(args, receipt):
    out = args.output.resolve()
    require(str(out).startswith("/dev/shm/"), "Build output must remain in /dev/shm")
    require(not out.exists(), "Refusing to overwrite an existing build/evidence directory")
    out.mkdir(parents=True)
    receipt["output"] = str(out)
    baseline = json.loads((HERE.parent / "BASELINE.json").read_text())
    receipt["baseline_apk_sha256"] = file_sha(args.apk)
    require(receipt["baseline_apk_sha256"] == baseline["APK_sha256"], "Signed502 APK hash mismatch")
    require(file_sha(DEX_READER) == DEX_READER_SHA, "DEX reader source changed")
    reader = {}
    exec(compile(DEX_READER.read_bytes(), str(DEX_READER), "exec"), reader)
    Dex, class_contract = reader["Dex"], reader["class_contract"]
    contract = {"__name__": "reviewed_main_patch"}
    exec(compile((HERE / "patch_main.py").read_bytes(), str(HERE / "patch_main.py"), "exec"), contract)
    hooks = contract["HOOKS"]
    require(len(hooks) == 7, "Expected seven original Main hook sites")
    source_files = sorted((HERE / "java/com/projectinfinity/kodi").glob("*.java"))
    require({p.name for p in source_files} == {"InfinityVideoLockState.java", "InfinityVideoLockDialog.java", "InfinityVideoLockBridge.java"}, "Unexpected Java input")
    inputs = [*source_files, HERE / "smali" / MAIN_PATH, HERE / "patch_main.py", HERE / "DEX-BUILD-SELECTION.json", Path(__file__)]
    source_hashes = {p.relative_to(HERE).as_posix(): file_sha(p) for p in inputs}
    receipt["input_sha256"] = source_hashes
    java_copy = out / "source/com/projectinfinity/kodi"
    java_copy.mkdir(parents=True)
    for source in source_files:
        shutil.copyfile(source, java_copy / source.name)

    tool_hashes = {p.name: file_sha(p) for p in args.smali_tools.glob("*.jar")}
    require(tool_hashes == TOOLS, "Pinned smali tool inventory changed")
    require(file_sha(args.ecj) == ECJ_SHA and file_sha(args.android) == ANDROID_SHA and file_sha(args.d8) == D8_SHA, "Pinned Java/Android tool changed")
    receipt["tool_sha256"] = dict(tool_hashes, ecj=ECJ_SHA, android_jar=ANDROID_SHA, d8=D8_SHA, dex_reader=DEX_READER_SHA)
    commands = []
    receipt["commands"] = commands
    def run(label, command):
        command = [str(x) for x in command]
        completed = subprocess.run(command, capture_output=True, text=True)
        raw = completed.stdout + completed.stderr
        log = out / (label + ".log")
        log.write_text(raw)
        commands.append(dict(label=label, argv=command, exit_code=completed.returncode,
                             log_sha256=sha(raw.encode()), log=str(log)))
        require(completed.returncode == 0, f"{label} failed with exit {completed.returncode}; see {log}")
    cp = ":".join(str(args.smali_tools / name) for name in sorted(TOOLS))
    baseline_defs, baseline_dex = {}, {}
    with zipfile.ZipFile(args.apk) as archive:
        names = sorted(n for n in archive.namelist() if re.fullmatch(r"classes\d*\.dex", n))
        require(names == ["classes.dex", *[f"classes{i}.dex" for i in range(2, 7)]], "Baseline DEX inventory is not exactly classes1 through6")
        for name in names:
            raw = archive.read(name)
            baseline_dex[name] = sha(raw)
            dex = Dex(raw)
            require(not set(baseline_defs) & set(dex.classes), "Baseline already has duplicate class definitions")
            baseline_defs.update(dex.classes)
            if name == "classes3.dex":
                require(sha(raw) == BASE_DEX, "Original classes3 digest mismatch")
                (out / "original-classes3.dex").write_bytes(raw)
    receipt["baseline_dex_sha256"] = baseline_dex
    require(not any(NEW_CLASS.fullmatch(name) for name in baseline_defs), "Lock class already exists in baseline")
    for field in (("MainActivity", OWNER), ("mMainView", "Lcom/projectinfinity/kodi/XBMCMainView;"),
                  ("mInfinityExitPlan", "Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;")):
        require(field in baseline_defs[OWNER]["fields"], "Exact Main field descriptor missing: " + repr(field))
    require(baseline_defs["Lcom/projectinfinity/kodi/XBMCMainView;"]["parent"] == "Landroid/view/SurfaceView;", "Main-view superclass changed")
    require(("pending", "()Z") in baseline_defs["Lcom/projectinfinity/kodi/InfinityExitCompletion$Plan;"]["methods"], "Exit Plan API changed")

    if args.reuse_classes3_receipt:
        previous = json.loads(args.reuse_classes3_receipt.read_text())
        require(previous.get("status") == "PASS_CLASSES3_ASSEMBLY_AND_PRESERVATION_JAVA_NOT_BUILT", "Reuse requires a completed classes3 audit")
        require(previous.get("baseline_apk_sha256") == receipt["baseline_apk_sha256"] and
                previous.get("baseline_dex_sha256") == baseline_dex, "Classes3 reuse baseline changed")
        for relative in ("smali/" + MAIN_PATH, "patch_main.py", "build_dex.py", "DEX-BUILD-SELECTION.json"):
            require(previous["input_sha256"].get(relative) == source_hashes[relative], "Classes3 auditor/hook input changed: " + relative)
        previous_out = Path(previous["output"])
        require(file_sha(previous_out / "classes3.dex") == previous["outputs_sha256"]["classes3.dex"], "Classes3 reuse artifact changed")
        require(file_sha(previous_out / "ORIGINAL-CLASS-PRESERVATION.json") == previous["classes3_preservation"]["canonical_class_inventory_sha256"], "Classes3 reuse inventory changed")
        shutil.copyfile(previous_out / "classes3.dex", out / "classes3.dex")
        shutil.copyfile(previous_out / "ORIGINAL-CLASS-PRESERVATION.json", out / "ORIGINAL-CLASS-PRESERVATION.json")
        receipt["classes3_preservation"] = previous["classes3_preservation"]
        receipt["classes3_reused_receipt_sha256"] = file_sha(args.reuse_classes3_receipt)
    else:
        base_smali, patch_smali, check_smali = (out / leaf for leaf in ("baseline-smali", "patched-smali", "assembled-smali"))
        run("disassemble-original", ["java", "-cp", cp, "org.jf.baksmali.Main", "d", "-a", "21", "-o", base_smali, out / "original-classes3.dex"])
        main_before = (base_smali / MAIN_PATH).read_bytes()
        require(sha(main_before) == BASE_MAIN, "Original Main disassembly is not the pinned preimage")
        expected, _, unchanged_methods = contract["patch"](main_before)
        main_input = (HERE / "smali" / MAIN_PATH).read_bytes()
        require(main_input == expected, "Main input differs from exact seven-hook transformation")
        shutil.copytree(base_smali, patch_smali)
        (patch_smali / MAIN_PATH).write_bytes(main_input)
        run("assemble-main", ["java", "-cp", cp, "org.jf.smali.Main", "a", "-a", "21", "-o", out / "classes3.dex", patch_smali])
        run("disassemble-assembled", ["java", "-cp", cp, "org.jf.baksmali.Main", "d", "-a", "21", "-o", check_smali, out / "classes3.dex"])
        before_files = {p.relative_to(base_smali).as_posix(): p for p in base_smali.rglob("*.smali")}
        after_files = {p.relative_to(check_smali).as_posix(): p for p in check_smali.rglob("*.smali")}
        require(set(before_files) == set(after_files), "Original DEX class inventory changed")
        untouched, normalized_only, preservation = [], [], {}
        for name in sorted(before_files):
            before, after = before_files[name].read_text(), after_files[name].read_text()
            restored = erase_calls(after, hooks) if name == MAIN_PATH else after
            require(normalize(before) == normalize(restored), "Original class code changed: " + name)
            preservation[name] = sha(normalize(before).encode())
            if name != MAIN_PATH:
                (untouched if before == after else normalized_only).append(name)
        (out / "ORIGINAL-CLASS-PRESERVATION.json").write_text(json.dumps(preservation, indent=2) + "\n")
        receipt["classes3_preservation"] = dict(original_classes=len(before_files),
            other_classes_raw_smali_identical=len(untouched), other_classes_normalization_required=normalized_only,
            Main_original_methods=len(METHODS.findall(main_before.decode())), Main_unchanged_methods=unchanged_methods,
            Main_hooked_methods=sorted(hooks), Main_equivalent_after_removing_exact_hooks=True,
            canonical_class_inventory_sha256=file_sha(out / "ORIGINAL-CLASS-PRESERVATION.json"),
            normalization=json.loads((HERE / "DEX-BUILD-SELECTION.json").read_text())["normalization"])
    if args.classes3_only:
        for relative in ("smali/" + MAIN_PATH, "patch_main.py", "build_dex.py", "DEX-BUILD-SELECTION.json"):
            require(file_sha(HERE / relative) == source_hashes[relative], "Classes3 input changed during assembly")
        receipt["status"] = "PASS_CLASSES3_ASSEMBLY_AND_PRESERVATION_JAVA_NOT_BUILT"
        receipt["outputs_sha256"] = {"classes3.dex": file_sha(out / "classes3.dex")}
        receipt["Java_compilation"] = "WAITING_FOR_ROOT_SOURCE_STABLE_MESSAGE"
        return

    stubs = out / "compile-only/com/projectinfinity/kodi"
    stubs.mkdir(parents=True)
    (stubs / "Main.java").write_text("package com.projectinfinity.kodi; public class Main extends android.app.NativeActivity { public static Main MainActivity; public XBMCMainView mMainView; final InfinityExitCompletion.Plan mInfinityExitPlan = null; }\n")
    (stubs / "InfinityExitCompletion.java").write_text("package com.projectinfinity.kodi; final class InfinityExitCompletion { static final class Plan { boolean pending() { throw new UnsupportedOperationException(\"compile only\"); } } }\n")
    (stubs / "XBMCMainView.java").write_text("package com.projectinfinity.kodi; public class XBMCMainView extends android.view.SurfaceView { public XBMCMainView(android.content.Context context) { super(context); } }\n")
    stub_classes, program_classes = out / "stub-classes", out / "program-classes"
    stub_classes.mkdir(); program_classes.mkdir()
    run("compile-only-api", ["java", "-jar", args.ecj, "-1.8", "-classpath", args.android,
                            "-d", stub_classes, *sorted(stubs.glob("*.java"))])
    stub_entries = jar_from(stub_classes, out / "compile-only.jar")
    require(set(stub_entries) == {"com/projectinfinity/kodi/" + name + ".class" for name in
            ("Main", "InfinityExitCompletion", "InfinityExitCompletion$Plan", "XBMCMainView")}, "Unexpected stub output")
    run("compile-lock-program", ["java", "-jar", args.ecj, "-1.8", "-classpath",
                                 str(args.android) + ":" + str(out / "compile-only.jar"),
                                 "-d", program_classes, *sorted(java_copy.glob("*.java"))])
    program_entries = jar_from(program_classes, out / "lock-program.jar")
    require(all(NEW_CLASS.fullmatch("L" + name[:-6] + ";") for name in program_entries), "Unrelated Java program class emitted")
    dex_out = out / "new-dex"
    dex_out.mkdir()
    run("d8-lock-only", ["java", "-cp", args.d8, "com.android.tools.r8.D8", "--release", "--min-api", "21",
                         "--lib", args.android, "--classpath", out / "compile-only.jar", "--output", dex_out, out / "lock-program.jar"])
    require(sorted(p.name for p in dex_out.iterdir()) == ["classes.dex"], "Unexpected new DEX outputs")
    shutil.copyfile(dex_out / "classes.dex", out / "classes7.dex")
    added = Dex((out / "classes7.dex").read_bytes())
    require(bool(added.classes) and all(NEW_CLASS.fullmatch(name) for name in added.classes), "New DEX includes unrelated/stub classes")
    require(not set(added.classes) & set(baseline_defs), "New DEX replaces an existing class")
    definitions = dict(baseline_defs)
    framework_count = 0
    with zipfile.ZipFile(args.android) as framework:
        for name in framework.namelist():
            if name.endswith(".class"):
                descriptor, definition = class_contract(framework.read(name))
                require(descriptor not in definitions, "Baseline/framework definition collision: " + descriptor)
                definitions[descriptor] = definition
                framework_count += 1
    definitions.update(added.classes)
    missing = []
    for kind, refs in (("fields", added.fields), ("methods", added.methods)):
        for owner, name, signature in refs:
            if not declared(definitions, owner, (name, signature), kind):
                missing.append([kind, owner, name, signature])
    require(not missing, "New DEX has unresolved exact502/framework references: " + json.dumps(missing))
    for name, second, _ in hooks.values():
        require((name, "(" + OWNER + ("Z" if second else "") + ")V") in added.classes[BRIDGE]["methods"], "New Bridge lacks exact Main hook target")
    receipt["new_dex"] = dict(member="classes7.dex", classes=sorted(added.classes),
        original_class_collisions=0, packaged_stubs=0, field_references=len(added.fields),
        method_references=len(added.methods), unresolved_references=[],
        framework_classes=framework_count, baseline_classes=len(baseline_defs),
        Main_mMainView_descriptor="Lcom/projectinfinity/kodi/XBMCMainView;",
        prior_SurfaceView_compile_stub="INSUFFICIENT_FOR_RUNTIME_LINKAGE_NOT_REUSED")
    require(all(file_sha(HERE / name) == digest for name, digest in source_hashes.items()), "Input source changed during build")
    receipt["input_sources_stable"] = True
    receipt["outputs_sha256"] = {name: file_sha(out / name) for name in ("classes3.dex", "classes7.dex", "lock-program.jar", "compile-only.jar")}
    receipt["status"] = "PASS_ISOLATED_DEX_ASSEMBLY_PRESERVATION_AND_DECLARED_REFERENCE_LINKAGE"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--classes3-only", action="store_true")
    parser.add_argument("--reuse-classes3-receipt", type=Path)
    parser.add_argument("--smali-tools", type=Path, default=Path("/dev/shm/infinity500-repair/pinned-dex-tools"))
    parser.add_argument("--ecj", type=Path, default=Path("/workspace/scratch/network-baseline-2103477/ecj-3.37.0.jar"))
    parser.add_argument("--android", type=Path, default=Path("/workspace/scratch/cast-sdk86/tools/android.jar"))
    parser.add_argument("--d8", type=Path, default=Path("/workspace/scratch/cast-sdk86/tools/d8.jar"))
    args = parser.parse_args()
    receipt = dict(status="NOT_COMPLETED", selected_checks="DEX-BUILD-SELECTION.json",
                   APK_created=False, APK_signed=False, installed=False, original_APK_modified=False,
                   Cobra_changed=False, provider_or_profile_access=False,
                   limitations=["Declared-reference verification is not Android ART execution", "No native engine integration or APK assembly", "No physical lock acceptance"])
    try:
        build(args, receipt)
    except Exception as error:
        receipt["status"] = "BLOCKED_BUILD_OR_PRESERVATION_GUARD"
        receipt["error"] = str(error)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps({"status": receipt["status"], "error": str(error), "receipt": str(args.receipt)}))
        return 1
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "outputs": receipt["outputs_sha256"], "receipt": str(args.receipt)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
