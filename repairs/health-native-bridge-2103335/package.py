#!/usr/bin/env python3
"""Package-only 2103335 diagnostic bridge over exact passed 2103334; libkodi stays byte-identical."""
import argparse, copy, difflib, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, tarfile, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VERSION = 2103335
RELEASE = "1.0.9-Native-Trace-Bridge-RC1"
PACKAGE = "com.projectinfinity.kodi"
ENGINE = "lib/arm64-v8a/libkodi.so"
PARENT_RUN = "37732755842"
PARENT_COMMIT = "5fe46bf82bdab4e3a0f08af8aac9a8db64171810"
PARENT_NATIVE_RUN = "37730777127"

sys.path.insert(0, str(HERE.parent / "mobile-regressions-2103304"))
sys.path.insert(0, str(HERE.parent / "chooser-close-owner-2103324"))
from packaging_checks import DEX, SIGNATURE, dex_contract, require, resource_ids, run, sha, verify_manifest_pair
import bridge_preservation

spec = importlib.util.spec_from_file_location(
    "factory335", HERE.parent / "mobile-regressions-2103304/package_candidate.py")
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)

spec = importlib.util.spec_from_file_location(
    "dex_equivalence335", HERE.parent / "cooperative-close-2103326/dex_equivalence.py")
dex_equivalence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dex_equivalence)

spec = importlib.util.spec_from_file_location("bridge335", HERE / "bridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}

def parent_guard(source, proof_path, base):
    report = json.loads((proof_path.parent / "APK-VERIFICATION.json").read_text())
    proof = json.loads(proof_path.read_text())
    require(report["candidate"] == 2103334 and report["version_name"] == "1.0.9-Script-Exit-RC1",
            "Wrong 2103334 parent identity")
    require(str(report["validation_run"]) == PARENT_RUN and report["source_commit"] == PARENT_COMMIT,
            "Wrong 2103334 packaging run/source")
    require(str(report["native_validation_run"]) == PARENT_NATIVE_RUN and report["native_recompiled"] is True,
            "Wrong 2103334 native association")
    require(report["skin_changed"] is False and report["data_reset"] is False,
            "Unexpected 2103334 parent mutation")
    require(sha(base.read_bytes()) == report["apk_sha256"], "2103334 APK bytes do not match green receipt")
    require(snapshot(source) == proof["after"], "Extracted source is not exact packaged 2103334 source")
    with zipfile.ZipFile(base) as apk:
        require(sha(apk.read(ENGINE)) == report["native_sha256"], "2103334 native payload/receipt mismatch")
    return report, proof

def append_test_support(build):
    tests = build / "xbmc/src/test/java/com/projectinfinity/kodi"
    tests.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "NativeTraceBridge335Test.java", tests / "NativeTraceBridge335Test.java")
    with (build / "xbmc/build.gradle").open("a") as f:
        f.write("""
android { testOptions { unitTests.includeAndroidResources = true; unitTests.all { maxHeapSize = "2g"; testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" } } } }
configurations { preservationTools }
dependencies { testImplementation 'junit:junit:4.13.2'; testImplementation 'org.robolectric:robolectric:4.14.1'; preservationTools 'org.smali:baksmali:2.5.2' }
tasks.register('exportPreservationTools') { doLast { rootProject.file('preservation-classpath.txt').text = configurations.preservationTools.asPath } }
""")

def merge(base, donor, out, native_sha):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(donor) as b, zipfile.ZipFile(out, "w") as z:
        require(a.testzip() is None and b.testzip() is None, "Parent or donor APK CRC failure")
        require(len(a.namelist()) == len(set(a.namelist())) and len(b.namelist()) == len(set(b.namelist())),
                "Duplicate APK entries")
        require(sha(a.read(ENGINE)) == native_sha, "Parent 2103334 engine changed")
        require(not any(n.startswith(("lib/", "assets/")) and not n.endswith("/") for n in b.namelist()),
                "Unexpected native/assets in Android-only donor")
        require(dex_contract(a)[0] == dex_contract(b)[0], "JNI/native method contract changed")
        for info in a.infolist():
            name = info.filename
            if name == "AndroidManifest.xml" or DEX.fullmatch(name) or SIGNATURE.fullmatch(name):
                continue
            z.writestr(copy.copy(info), a.read(name))
        for info in b.infolist():
            if info.filename == "AndroidManifest.xml" or DEX.fullmatch(info.filename):
                z.writestr(copy.copy(info), b.read(info.filename))

def verify_payload(base, candidate, native_sha):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(candidate) as b:
        kept = {n for n in a.namelist()
                if n != "AndroidManifest.xml" and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected = kept | {"AndroidManifest.xml"} | {
            n for n in b.namelist() if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(set(b.namelist()) == expected and len(b.namelist()) == len(expected),
                "Unexpected APK payload delta")
        for name in kept:
            require(a.read(name) == b.read(name), "Protected APK entry changed: " + name)
        require(sha(b.read(ENGINE)) == native_sha and a.read(ENGINE) == b.read(ENGINE),
                "2103334 libkodi.so is not byte-identical")
        require(dex_contract(a)[0] == dex_contract(b)[0], "JNI contract changed")
        require(b.testzip() is None, "Final APK CRC failure")
        return {
            "preserved_entries": len(kept),
            "assets_resources_skin_and_native_byte_identical": True,
            "native_engine_byte_identical_to_2103334": True,
        }

def compare_dex(base, final, build, out):
    recording = dex_equivalence.verify(base, final, build, out, DEX, require)
    classpath = (build / "preservation-classpath.txt").read_text()
    roots = {}
    for label, apk in (("base", base), ("final", final)):
        dexroot = out / ("dex-" + label)
        smali = out / ("smali-" + label)
        dexroot.mkdir()
        with zipfile.ZipFile(apk) as archive:
            for name in archive.namelist():
                if DEX.fullmatch(name):
                    target = dexroot / name
                    target.write_bytes(archive.read(name))
                    subprocess.run(["java", "-cp", classpath, "org.jf.baksmali.Main",
                                    "disassemble", str(target), "-o", str(smali)], check=True)
        roots[label] = smali
    old_all = {p.relative_to(roots["base"]).as_posix(): p.read_text()
               for p in roots["base"].rglob("*.smali")}
    new_all = {p.relative_to(roots["final"]).as_posix(): p.read_text()
               for p in roots["final"].rglob("*.smali")}
    health_prefix = "com/projectinfinity/kodi/InfinityHealthExport"
    protected_old = {name:text for name,text in old_all.items() if not name.startswith(health_prefix)}
    protected_new = {name:text for name,text in new_all.items() if not name.startswith(health_prefix)}
    protected_old, protected_new, bridge_report = bridge_preservation.verify(protected_old, protected_new, out)
    old = dict(protected_old); new = dict(protected_new)
    for name in old_all.keys() | new_all.keys():
        if name.startswith(health_prefix):
            if name in old_all: old[name] = old_all[name]
            if name in new_all: new[name] = new_all[name]
    changed = sorted(name for name in old.keys() | new.keys() if old.get(name) != new.get(name))
    allowed = re.compile(
        r"com/projectinfinity/kodi/(?:InfinityHealthExport|BuildConfig)(?:\$[^/]*)?\.smali$|"
        r"com/projectinfinity/kodi/InfinityCobraRecordingService(?:\$\$ExternalSyntheticLambda\d+)?\.smali$")
    unexpected = [name for name in changed if not allowed.fullmatch(name)]
    if unexpected:
        diag = out / "compiler-diffs"; diag.mkdir(exist_ok=True)
        for name in unexpected:
            (diag / (Path(name).name + ".diff")).write_text("".join(difflib.unified_diff(
                old.get(name, "").splitlines(True), new.get(name, "").splitlines(True),
                fromfile="base/" + name, tofile="candidate/" + name)))
    require(not unexpected, "Behavior changed outside Health exporter/version metadata: " + repr(unexpected))
    for path in (out / "dex-base", out / "dex-final", out / "smali-base", out / "smali-final"):
        shutil.rmtree(path)
    result = {
        "changed_dex_classes": changed,
        "all_other_classes_behavior_identical": True,
        "api_bridge_renumbering_verified": True,
        "cobra_recording_compiler_equivalence": recording,
        "bridge_preservation": bridge_report,
    }
    (out / "DEX-PRESERVATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result

def prepare(source, proof, base, build, out):
    parent, source_proof = parent_guard(source, proof, base)
    modified = out / "android-source"
    shutil.copytree(source, modified)
    receipt = out / "ANDROID-SOURCE-DELTA.json"
    bridge.apply(modified, proof, receipt)
    bridge.verify(modified, receipt)
    factory.BASE_APK_SHA256 = parent["apk_sha256"]
    factory.VERSION_CODE = VERSION
    factory.RELEASE = RELEASE
    factory.prepare(modified.resolve(), base.resolve(), build.resolve(), out.resolve())
    append_test_support(build)
    print("PASS: exact 2103334 source staged; only Health exporter changed; native not rebuilt")

def package(source, proof, base, build, out):
    parent, source_proof = parent_guard(source, proof, base)
    bridge.verify(out / "android-source", out / "ANDROID-SOURCE-DELTA.json")
    donor = build / "xbmc/build/outputs/apk/release/xbmc-release.apk"
    bt = Path(os.environ["ANDROID_HOME"]) / "build-tools/34.0.0"
    require(resource_ids(bt / "aapt2", base, out / "base-resources.txt") ==
            resource_ids(bt / "aapt2", donor, out / "donor-resources.txt"),
            "Android resource IDs changed")
    unsigned = out / "candidate-unsigned.apk"
    merge(base, donor, unsigned, parent["native_sha256"])
    verify_manifest_pair(
        run(bt / "aapt", "dump", "xmltree", base, "AndroidManifest.xml", output=out / "base-manifest.txt"),
        run(bt / "aapt", "dump", "xmltree", unsigned, "AndroidManifest.xml", output=out / "candidate-manifest.txt"))
    final = out / "Infinity-2103335-Native-Trace-Bridge-RC1.apk"
    run("bash", ROOT / "scripts/sign-infinity71.sh", unsigned, final)
    cert = run(bt / "apksigner", "verify", "--verbose", "--print-certs", final,
               output=out / "signing-verification.txt")
    require(parent["signer_certificate_sha256"] in cert.lower(), "Permanent install-over signer changed")
    badging = run(bt / "aapt", "dump", "badging", final, output=out / "badging.txt")
    require(f"package: name='{PACKAGE}' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,
            "Wrong 2103335 release identity")
    require("application-debuggable" not in badging, "Diagnostic candidate is debuggable")
    payload = verify_payload(base, final, parent["native_sha256"])
    dex = compare_dex(base, final, build, out)

    results = []
    for path in sorted((build / "xbmc/build/test-results/testReleaseUnitTest").glob("TEST-*.xml")):
        attrs = ET.parse(path).getroot().attrib
        results.append({key: (attrs[key] if key == "name" else int(attrs.get(key, 0)))
                        for key in ("name", "tests", "failures", "errors", "skipped")})
    target = [row for row in results if row["name"].endswith(".NativeTraceBridge335Test")]
    require(len(target) == 1 and target[0]["tests"] >= 2 and
            target[0]["failures"] == target[0]["errors"] == target[0]["skipped"] == 0,
            "NativeTraceBridge335Test missing or failed")

    source_delta = json.loads((out / "ANDROID-SOURCE-DELTA.json").read_text())
    report = {
        "candidate": VERSION,
        "version_name": RELEASE,
        "apk_parent": 2103334,
        "base_apk_sha256": parent["apk_sha256"],
        "apk_sha256": sha(final.read_bytes()),
        "source_commit": os.environ["GITHUB_SHA"],
        "validation_run": os.environ["GITHUB_RUN_ID"],
        "signer_certificate_sha256": parent["signer_certificate_sha256"],
        "native_sha256": parent["native_sha256"],
        "native_validation_run": parent["native_validation_run"],
        "native_recompiled": False,
        "native_engine_byte_identical_to_2103334": True,
        "shutdown_behavior_changed": False,
        "diagnostics_only": True,
        "shutdown_hang_resolved": False,
        "skin_parent": parent.get("installed_skin_pairing", parent.get("skin_parent", "1.0.5.201")),
        "skin_changed": False,
        "data_reset": False,
        "physical_device_verified": False,
        "locked": False,
        "android_source_delta": source_delta["changed"],
        "test_suites": results,
        **payload,
        **dex,
    }
    (out / "APK-VERIFICATION.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with tarfile.open(out / "repaired-shell-source.tar.gz", "w:gz") as archive:
        archive.add(out / "android-source", arcname="shell-kodi")
    unsigned.unlink()
    print("PASS: 2103335 diagnostic bridge signed; exact 2103334 native/UI/assets preserved")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["prepare", "package"])
    for name in ("source", "proof", "base", "build", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    fn = prepare if a.mode == "prepare" else package
    fn(a.source, a.proof, a.base, a.build, a.out)
