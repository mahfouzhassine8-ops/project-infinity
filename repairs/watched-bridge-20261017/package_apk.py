#!/usr/bin/env python3
"""New-code experimental APK plus an in-place TEST4 compatibility rollback.

The completed deadlock repair plus read-only watched presentation and scoped touch preparation are the only native deltas. Only the ARM64 engine and the two version attributes may differ. Every DEX,
resource, asset, Android component and other library is byte preserved.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ENGINE = "lib/arm64-v8a/libkodi.so"
PARENT_SHA = "bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286"
PARENT_ENGINE_SHA = "2f1597ecc4f8a0ee09f24e399aa738b96a876c7760eaec0ee0ad1a18bafd6929"
CERT = "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
NATIVE_RUN = 39002607563
NATIVE_SOURCE = "c4f0e315f4595b9f7cb3446ed5ad04a6f490b07b"
CODE = 2103381
NAME = "1.0.9-Watched-Touch-Bridge-TEST2"
OLD_NAME = "1.0.9-Essential-First-TEST4-RC05"
SIGNATURE = re.compile(r"META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))", re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True, stderr=subprocess.STDOUT)


def load(path):
    return json.loads(path.read_text())


def package(parent, native, out):
    if sha(parent.read_bytes()) != PARENT_SHA:
        raise ValueError("Not the exact user-locked Fold TEST4 APK")
    for key in ("INFINITY_KEYSTORE_B64", "INFINITY_STORE_PASSWORD", "INFINITY_KEY_PASSWORD", "INFINITY_KEY_ALIAS"):
        if not os.environ.get(key):
            raise ValueError("Permanent signing configuration unavailable; no fallback certificate permitted")
    proof = load(native / "ENGINE-PROOF.json")
    delta = load(native / "FOLD-DEADLOCK-SOURCE-DELTA.json")
    host = load(native / "fold-lock-host/LOCK-RETIREMENT-HOST.json")
    assert proof["complete_native_engine_compiled"] and proof["fold_callback_retirement_compiled"]
    assert proof["fold_correction_source_commit"] == delta["source_commit"] == NATIVE_SOURCE
    assert delta["changed"] == ["xbmc/guilib/listproviders/DirectoryProvider.cpp"]
    assert not delta["all_other_native_sources_byte_identical"] and delta["shutdown_coordinator_unchanged"]
    watched = load(native / "WATCHED-TOUCH-SOURCE-DELTA.json")
    expected = {"xbmc/GUIInfoManager.cpp", "xbmc/interfaces/builtins/GUIBuiltins.cpp", "xbmc/profiles/ProfileManager.cpp",
                "xbmc/guilib/InfinityWatchedIndex.h", "xbmc/guilib/InfinityWatchedPresentation.h",
                "xbmc/input/InputManager.cpp", "xbmc/guilib/GUIBaseContainer.cpp", "xbmc/guilib/GUIBaseContainer.h"}
    assert set(watched["changed"]) == expected
    assert watched["source_commit"] == NATIVE_SOURCE
    assert watched["completed_deadlock_callback_sha256"] == "496d7b61c8425050e9f707cd28fa41f1e792abcf8892f49d7259bd71cee3506f"
    assert watched["all_other_native_sources_byte_identical"] and watched["native_shutdown_and_write_admission_unchanged"]
    assert watched["original_home_rail_hold_unchanged"] and not watched["provider_code_changed"]
    assert not watched["command_center_code_changed"] and not watched["rails_helper_code_changed"]
    assert proof["watched_presentation_bridge_compiled"] and proof["browse_touch_preselection_compiled"]
    for report in ("WATCHED-INDEX-HOST.json", "BROWSE-TOUCH-PRODUCTION-HOST.json"):
        assert load(native / report)["passed"]
    assert delta["protected_write_admission_unchanged"] and delta["rails_stale_request_gate_preserved"]
    assert host["status"] == "passed" and host["baseline_cycle_reproduced"]
    assert host["candidate_directory_unlocked_during_graphics_cleanup"]
    library = native / "libkodi.so"
    assert sha(library.read_bytes()) == proof["native_sha256"]
    out.mkdir(parents=True, exist_ok=True)
    android = Path(os.environ["ANDROID_HOME"])
    bt = android / "build-tools/34.0.0"
    ndk = android / "ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin"
    engine = out / "candidate-engine.so"
    shutil.copyfile(library, engine)
    run(ndk / "llvm-strip", "--strip-unneeded", engine)
    spec = importlib.util.spec_from_file_location("fold_manifest", ROOT / "repairs/critical-preview-2103376/manifest_patch.py")
    manifest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manifest)
    manifest.PARENT_CODE = 2103377
    manifest.CODE = CODE
    manifest.PARENT_NAME = OLD_NAME
    assert len(NAME) == len(OLD_NAME)
    records = []
    with zipfile.ZipFile(parent) as old:
        assert old.testzip() is None and len(old.namelist()) == len(set(old.namelist()))
        assert sha(old.read(ENGINE)) == PARENT_ENGINE_SHA
        parent_engine = out / "test4-engine.so"
        parent_engine.write_bytes(old.read(ENGINE))
        def exports(p):
            return {a[-1].split('@')[0] for line in run('readelf', '--dyn-syms', '--wide', p).splitlines()
                    if len(a := line.split()) >= 8 and a[4:6] == ['GLOBAL', 'DEFAULT'] and a[6] != 'UND'}
        assert not (exports(parent_engine) - exports(engine)), "Existing exported ABI removed"
        needed = lambda p: sorted(re.findall(r'\(NEEDED\).*?\[(.*?)\]', run('readelf', '-d', '-W', p)))
        assert needed(parent_engine) == needed(engine), "Native dependency set changed"
        for rollback in (False, True):
            filename = (f"Infinity-{CODE}-TEST4-Compatibility-Rollback.apk" if rollback else
                        f"Infinity-{CODE}-Watched-Touch-TEST2.apk")
            unsigned = out / ("unsigned-" + filename)
            manifest.NAME = OLD_NAME if rollback else NAME
            patched, edits = manifest.patch(old.read("AndroidManifest.xml"))
            assert {e["field"] for e in edits} == {"versionCode", "versionName"}
            with zipfile.ZipFile(unsigned, "w") as target:
                for info in old.infolist():
                    if SIGNATURE.fullmatch(info.filename):
                        continue
                    data = old.read(info.filename)
                    if info.filename == "AndroidManifest.xml":
                        data = patched
                    elif info.filename == ENGINE and not rollback:
                        data = engine.read_bytes()
                    target.writestr(copy.copy(info), data)
            final = out / filename
            subprocess.run(["bash", str(ROOT / "scripts/sign-infinity71.sh"), str(unsigned), str(final)], check=True)
            certificate = run(bt / "apksigner", "verify", "--verbose", "--print-certs", final)
            assert CERT in certificate.lower()
            for scheme in (1, 2, 3):
                assert re.search(r"Verified using v" + str(scheme) + r" scheme[^\n]+true", certificate)
            run(bt / "zipalign", "-c", "-p", "4", final)
            badging = run(bt / "aapt", "dump", "badging", final)
            assert f"package: name='com.projectinfinity.kodi' versionCode='{CODE}'" in badging
            assert f"versionName='{manifest.NAME}'" in badging
            assert "application-label:'Infinity'" in badging and "application-debuggable" not in badging
            with zipfile.ZipFile(final) as new:
                assert set(old.namelist()) == set(new.namelist()) and new.testzip() is None
                changed = sorted(n for n in old.namelist() if not SIGNATURE.fullmatch(n) and old.read(n) != new.read(n))
                assert changed == (["AndroidManifest.xml"] if rollback else ["AndroidManifest.xml", ENGINE])
                dex = {n: sha(new.read(n)) for n in new.namelist() if re.fullmatch(r"classes(?:[0-9]+)?\.dex", n)}
                records.append(dict(file=filename, sha256=sha(final.read_bytes()), bytes=final.stat().st_size,
                    version_code=CODE, version_name=manifest.NAME, signer_sha256=CERT,
                    apk_signing_schemes=[1, 2, 3], changed_payload_entries=changed, java_dex_sha256=dex,
                    native_packaged_sha256=sha(new.read(ENGINE)), rollback=rollback))
            unsigned.unlink()
    engine.unlink()
    parent_engine.unlink()
    receipt = dict(schema=1, status="EXPERIMENTAL; PHYSICAL FOLD VALIDATION REQUIRED",
        packaging_source_commit=os.environ.get("GITHUB_SHA"), native_source_commit=NATIVE_SOURCE,
        native_run=NATIVE_RUN, protected_test4_apk_sha256=PARENT_SHA, artifacts=records,
        all_dex_resources_assets_other_libraries_byte_identical=True,
        native_dependency_set_unchanged=True, exported_native_abi_preserved=True,
        skins_rails_command_center_modified=False, user_data_modified=False,
        completed_deadlock_correction_retained=True, watched_readonly_bridge=True, scoped_android_grid_preselection=True,
        physical_fold_verified=False, final_lock_authorized=False,
        rollback_note="The same-code compatibility APK restores TEST4 payloads without an Android version downgrade. Original TEST4 remains immutable.")
    (out / "WATCHED-TOUCH-APK-PRESERVATION.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (out / "SHA256SUMS").write_text("".join(f"{r['sha256']}  {r['file']}\n" for r in records))
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("parent", "native", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    package(args.parent, args.native, args.out)
