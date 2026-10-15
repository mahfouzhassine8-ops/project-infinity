#!/usr/bin/env python3
"""Fast retry for 2103334 using the exact completed dependency/ccache snapshot from failed native run 37724566406.

The previous run compiled Kodi/libkodi to 100% and then failed only because its verifier
compared the post-build tree against a pre-build snapshot, thereby treating generated
build files under kodi/tools/depends as source mutations. This retry keeps the reviewed
2103334 native source unchanged, restores the exact completed dependency cache, skips
rebuilding those dependencies, recompiles Kodi through the preserved toolchain/ccache,
and verifies every pre-existing source file by hash.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess

OUT=Path("engine3334")
SOURCE=Path("kodi")

def run(cmd):
    subprocess.run(cmd,check=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    receipt=json.loads((OUT/"source-manifest.json").read_text())
    expected=receipt["after"]

    # Every file that existed in the reviewed source snapshot must still exist byte-for-byte.
    # Build-generated files may be added under the build/dependency tree; they are not source edits.
    missing=[name for name in expected if not (SOURCE/name).is_file()]
    changed=[name for name,digest in expected.items()
             if (SOURCE/name).is_file() and sha(SOURCE/name)!=digest]
    if missing or changed:
        raise AssertionError(f"Reviewed source changed before fast compile: missing={missing[:8]} changed={changed[:8]}")

    stage=Path("scripts/infinity_live_app_ci_2.sh").read_text()
    old_apply='python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json'
    assert stage.count(old_apply)==1
    stage=stage.replace(old_apply,'python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi')

    old_dep='''rm -f "$TARBALLS/fontconfig-2.14.0.tar.xz" "$TARBALLS/fontconfig-2.14.0.tar.xz.sha512"
make -C target/fontconfig FULL_URL=https://gstreamer.freedesktop.org/data/src/mirror/fontconfig-2.14.0.tar.xz download
make -j"$(nproc)"
make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"'''
    fast_dep='''# Reuse the exact dependency prefix saved after run 37724566406 reached a full 100% Kodi build.
# The workflow requires an exact-key cache hit before this script is invoked.
test -x "$DEPENDS/x86_64-linux-gnu-native/bin/cmake"
test -x "$DEPENDS/x86_64-linux-gnu-native/bin/pkg-config"
test -d "$DEPENDS/aarch64-linux-android-21-debug/include"
test -d "$DEPENDS/aarch64-linux-android-21-debug/lib"
test -d "$DEPENDS/aarch64-linux-android-21-debug/lib/pkgconfig"
test -n "$(find "$DEPENDS/aarch64-linux-android-21-debug/lib" -maxdepth 1 -type f -print -quit)"
make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"'''
    assert stage.count(old_dep)==1
    stage=stage.replace(old_dep,fast_dep)

    marker='make -C "$BUILD_DIR" apk -j"$(nproc)"'
    assert stage.count(marker)==1
    fast_script=OUT/"compile-fast.sh"
    fast_script.write_text(stage[:stage.index(marker)])
    run(["bash",str(fast_script)])

    # Correct preservation rule: protect every reviewed pre-existing source file.
    # Ignore only newly generated build files, exactly as the successful 3330 verifier did.
    missing=[name for name in expected if not (SOURCE/name).is_file()]
    changed=[name for name,digest in expected.items()
             if (SOURCE/name).is_file() and sha(SOURCE/name)!=digest]
    if missing or changed:
        raise AssertionError(f"Reviewed source changed during compile: missing={missing[:8]} changed={changed[:8]}")

    libs=list(Path(os.environ["BUILD_DIR"]).rglob("libkodi.so"))
    assert len(libs)==1,libs
    data=libs[0].read_bytes()
    for token in (b"infinity-shutdown-2103334-v1",b"python.exit_frame",
                  b"scripts.late_message_rejected",b"directory.result_wait_cancelled",
                  b"thread.std_join_fallback"):
        assert token in data,token

    shutil.copy2(libs[0],OUT/"libkodi.so")
    proof=dict(candidate=2103334,apk_parent=2103333,native_parent=2103330,
               locked_rollback=2103327,source_commit=os.environ["GITHUB_SHA"],
               native_sha256=hashlib.sha256(data).hexdigest(),
               baseline_kodi_commit="a3a448d26b8d560a65655dab2cd122994dc4e146",
               parent_packaged_native_sha256="22f56ef1836c53930f7b2c9fa89d1a3658482db9444c088bdc175c5a641b477d",
               late_message_gate_fixed=True,python_abort_policy_unchanged=True,
               script_finalizers_unchanged=True,directory_repair_preserved=True,
               final_joins_preserved=True,timeouts_unchanged=True,
               exact_dependency_cache_run=37724566406,
               preservation_rule="all reviewed pre-existing source files byte-identical; generated build outputs ignored",
               physical_device_verified=False,locked=False)
    (OUT/"ENGINE-PROOF.json").write_text(json.dumps(proof,indent=2)+"\n")
    with (OUT/"elf-identity.txt").open("w") as fh:
        subprocess.run(["readelf","-h","-n","-W",str(OUT/"libkodi.so")],stdout=fh,check=True)
    print("PASS: 2103334 fast retry compiled with exact completed dependency cache and preserved reviewed source")

if __name__=="__main__":
    main()
