#!/usr/bin/env python3
"""2103253: crash-forensics RC4 delta over exact locked 2103229 source."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

VERSION = 2103253
OLD_VERSION = 2103229
OLD_NAME = "1.0.9-Cobra-MultiView-Stability-Fill-RC1"
NEW_NAME = "1.0.9-Native-Crash-Forensics-RC4"
NATIVE_ENGINE_SHA = "db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375"
PARENT_APK_SHA = "3a80480e300bafc6071aed7f494cc6b3a96a79f7e1e4dcb9ae87fe36c9a707f5"
PACKAGING_BASE_SHA = "9bda7a49c38dcfd7c67b548ed38c661ddb44ca7434fbb2c69ce48dd7554dab7f"

MAIN = Path("tools/android/packaging/xbmc/src/Main.java.in")
EXIT = Path("tools/android/packaging/xbmc/src/InfinityExitDiagnostics.java.in")
GRADLE = Path("tools/android/packaging/xbmc/build.gradle.in")
EXPECTED_MAIN = "ddf18d30c4040369b30e861ded588a53846ff3de319a89a219344771f8db9318"
EXPECTED_EXIT = "9ad267b3f5e1a9c1c9adbdc120146cc1d93848f4e50e7d0a9953c20f26d1ff94"
EXPECTED_GRADLE = "3d4d5c84a810104d8b532caa2a09598b4019ed526e22d0ba7b5c85af9678895b"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def req(value, msg):
    if not value:
        raise RuntimeError(msg)


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    req(count == 1, f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_main(path: Path) -> None:
    text = path.read_text()
    req(sha(path) == EXPECTED_MAIN, "Main.java preimage is not exact locked 2103229")
    old = '''    // Collect previous-process evidence off the UI thread. No player access.
    InfinityExitDiagnostics.start(getApplicationContext());
    System.loadLibrary("@APP_NAME_LC@");

    super.onCreate(savedInstanceState);
'''
    new = '''    // Preserve previous-process evidence before native initialization can truncate
    // its new-process crash slot. Let Kodi and NativeActivity finish onCreate
    // first, then install the diagnostic fatal-signal recorder LAST so startup
    // cannot overwrite our SIGSEGV/SIGABRT/SIGBUS/SIGILL/SIGFPE handlers.
    InfinityExitDiagnostics.start(getApplicationContext());
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onCreate.beforeNative");
    System.loadLibrary("@APP_NAME_LC@");
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.kodiNative.loaded");

    super.onCreate(savedInstanceState);
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onCreate.afterSuper");
    try
    {
      System.loadLibrary("infinitycrash");
      InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "nativeCrashRecorder.loaded.afterKodiOnCreateOnCreate");
    }
    catch (LinkageError recorderUnavailable)
    {
      android.util.Log.w("InfinityDiagnostics", "Native crash recorder unavailable: " +
          recorderUnavailable.getClass().getSimpleName());
      InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "nativeCrashRecorder.unavailable.afterKodiOnCreate");
    }
    InfinityExitDiagnostics.snapshotNativeMaps(getApplicationContext());
'''
    text = once(text, old, new, "onCreate native diagnostics")

    anchors = {
        '''  public void onStart()
  {
    super.onStart();
''': '''  public void onStart()
  {
    super.onStart();
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onStart");
''',
        '''  public void onResume()
  {
    super.onResume();
''': '''  public void onResume()
  {
    super.onResume();
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onResume");
''',
        '''  public void onPause()
  {
    super.onPause();
''': '''  public void onPause()
  {
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onPause");
    super.onPause();
''',
        '''  public void onDestroy()
  {
    if (isFinishing()) InfinityExtendedBackgroundService.stopForExit(this);
''': '''  public void onDestroy()
  {
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onDestroy");
    if (isFinishing()) InfinityExtendedBackgroundService.stopForExit(this);
''',
        '''  public void onConfigurationChanged(Configuration configuration)
  {
    super.onConfigurationChanged(configuration);
''': '''  public void onConfigurationChanged(Configuration configuration)
  {
    super.onConfigurationChanged(configuration);
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onConfigurationChanged");
''',
        '''  public void onStop()
  {
    infinityRequestPlayerOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED, "stop");
''': '''  public void onStop()
  {
    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onStop");
    infinityRequestPlayerOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED, "stop");
''',
    }
    for old_anchor, new_anchor in anchors.items():
        text = once(text, old_anchor, new_anchor, old_anchor.splitlines()[0].strip())
    path.write_text(text)


def patch_identity(root: Path, shell: Path) -> None:
    gradle = shell / GRADLE
    req(sha(gradle) == EXPECTED_GRADLE, "build.gradle preimage is not exact locked 2103229")
    g = gradle.read_text()
    g = once(g, f"versionCode {OLD_VERSION}", f"versionCode {VERSION}", "versionCode")
    g = once(g, f'versionName "{OLD_NAME}"', f'versionName "{NEW_NAME}"', "versionName")
    gradle.write_text(g)

    runtime = root / "scripts/infinity_background_resume.py"
    r = runtime.read_text()
    r = once(r, f"VERSION_CODE = {OLD_VERSION}", f"VERSION_CODE = {VERSION}", "runtime version")
    r = once(r, f"RELEASE = '{OLD_NAME}'", f"RELEASE = '{NEW_NAME}'", "runtime release")
    runtime.write_text(r)

    pack = root / "scripts/package_background_resume.py"
    p = pack.read_text()
    p = once(
        p,
        "def merge(base: Path, donor: Path, output: Path):",
        "CRASH_RECORDER_APK_PATH = 'lib/arm64-v8a/libinfinitycrash.so'\n\n\ndef merge(base: Path, donor: Path, output: Path):",
        "crash recorder constant",
    )
    p = once(
        p,
        '''        for info in b.infolist():
            n=info.filename
            if n=='AndroidManifest.xml' or DEX.fullmatch(n):
                z.writestr(info,b.read(n))
    return len(original_native),len(core)
''',
        '''        for info in b.infolist():
            n=info.filename
            if n=='AndroidManifest.xml' or DEX.fullmatch(n):
                z.writestr(info,b.read(n))
        recorder = ROOT/'engine/libinfinitycrash.so'
        require(recorder.is_file(), 'Missing compiled Infinity crash recorder')
        z.write(recorder, CRASH_RECORDER_APK_PATH, compress_type=zipfile.ZIP_STORED)
    return len(original_native),len(core)
''',
        "merge recorder",
    )
    p = once(
        p,
        '''        expected=kept|{'AndroidManifest.xml'}|{n for n in bn if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(bn==expected,'Unexpected final APK member inventory')
        for name in sorted(kept): require(a.read(name)==b.read(name),'Protected APK payload changed: '+name)
        require(sha(b.read('lib/arm64-v8a/libkodi.so'))==BASE_ENGINE_SHA256,'Native engine changed')
''',
        '''        expected=kept|{'AndroidManifest.xml',CRASH_RECORDER_APK_PATH}|{n for n in bn if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(bn==expected,'Unexpected final APK member inventory')
        for name in sorted(kept): require(a.read(name)==b.read(name),'Protected APK payload changed: '+name)
        require(sha(b.read('lib/arm64-v8a/libkodi.so'))==BASE_ENGINE_SHA256,'Native engine changed')
        recorder = ROOT/'engine/libinfinitycrash.so'
        require(sha(b.read(CRASH_RECORDER_APK_PATH))==sha(recorder.read_bytes()),'Crash recorder payload mismatch')
''',
        "verify recorder",
    )
    old_runtime = "        for token in (b'InfinityExtendedBackgroundService',b'InfinityBackgroundControlActivity',b'BACKGROUND_MODE_NORMAL',b'BACKGROUND_MODE_EXTENDED',b'InfinityCoreBridge',b'InfinityCobraDeviceBridge',b'getPlayWhenReady',b'Turn off'):\n            require(token in joined,'Missing source-built runtime: '+repr(token))\n        return {'native_files_byte_identical':sum(n.startswith('lib/') and not n.endswith('/') for n in kept),\n"
    new_runtime = "        for token in (b'InfinityExtendedBackgroundService',b'InfinityBackgroundControlActivity',b'BACKGROUND_MODE_NORMAL',b'BACKGROUND_MODE_EXTENDED',b'InfinityCoreBridge',b'InfinityCobraDeviceBridge',b'getPlayWhenReady',b'Turn off',b'nativeCrashRecorder.loaded.afterKodiOnCreate',b'trace_request_attempted',b'process_state_summary'):\n            require(token in joined,'Missing source-built runtime: '+repr(token))\n        return {'native_files_byte_identical':sum(n.startswith('lib/') and not n.endswith('/') for n in kept),\n                'diagnostic_native_library_added':CRASH_RECORDER_APK_PATH,\n"
    p = once(p, old_runtime, new_runtime, "runtime proof")
    p = p.replace(
        "Infinity-1.0.9-Cobra-MultiView-Stability-Fill-RC1-unsigned.apk",
        "Infinity-1.0.9-Native-Crash-Forensics-RC4-unsigned.apk",
    )
    p = p.replace(
        "Infinity-1.0.9-Cobra-MultiView-Stability-Fill-RC1.apk",
        "Infinity-1.0.9-Native-Crash-Forensics-RC4.apk",
    )
    req(
        "Infinity-1.0.9-Cobra-MultiView-Stability-Fill-RC1" not in p,
        "old APK output identity remained in packager",
    )
    pack.write_text(p)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--shell", type=Path, default=Path("shell-kodi"))
    parser.add_argument("--collector", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    shell = args.shell.resolve()

    main_java = shell / MAIN
    exit_java = shell / EXIT
    req(sha(main_java) == EXPECTED_MAIN, "locked Main.java hash mismatch")
    req(sha(exit_java) == EXPECTED_EXIT, "locked InfinityExitDiagnostics hash mismatch")

    receipt_path = root / "engine/background-resume-source.json"
    receipt = json.loads(receipt_path.read_text())
    req(receipt.get("version_code") == OLD_VERSION, "receipt is not locked 2103229")
    req(receipt.get("version_name") == OLD_NAME, "receipt version name drift")
    req(receipt.get("native_engine_sha256") == NATIVE_ENGINE_SHA, "locked native engine drift")

    patch_main(main_java)
    enhanced = args.collector.read_text()
    req('collector_version", "2"' in enhanced and "process_state_summary" in enhanced,
        "collector v2 source contract missing")
    exit_java.write_text(enhanced)
    patch_identity(root, shell)

    # The historical source receipt tracks a curated subset of generated files.
    # Main + Gradle are tracked there; InfinityExitDiagnostics is present in the
    # exact locked shell but was not part of that older curated receipt. Preserve
    # receipt semantics and record its before/after identity explicitly below.
    for rel in (str(MAIN), str(GRADLE)):
        req(rel in receipt["files"], "receipt missing " + rel)
        receipt["files"][rel]["after"] = sha(shell / rel)
    receipt["native_diagnostics_source"] = {
        "path": str(EXIT),
        "before_sha256": EXPECTED_EXIT,
        "after_sha256": sha(exit_java),
    }
    receipt.update(
        version_code=VERSION,
        version_name=NEW_NAME,
        source_parent=OLD_VERSION,
        candidate_locked=False,
        physical_device_verified=False,
        native_engine_rebuilt=False,
        native_engine_reused_from_2103209=True,
        native_engine_sha256=NATIVE_ENGINE_SHA,
        native_crash_forensics=True,
        crash_collector_version=2,
        app_owned_fatal_signal_register_capture=True,
        process_state_summary=True,
        lifecycle_breadcrumbs=True,
        application_exit_trace_attempt_for_fatal_signaled_exit=True,
        home_skin_unchanged=True,
        playback_core_unchanged=True,
        providers_unchanged=True,
        timeshift_core_unchanged=True,
        multiview_behavior_unchanged=True,
    )
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    for rel, row in receipt["files"].items():
        req(sha(shell / rel) == row["after"], "receipt drift " + rel)

    audit = root / "audit250"
    audit.mkdir(exist_ok=True)
    scope = {
        "schema": 1,
        "build": VERSION,
        "parent": OLD_VERSION,
        "protected_parent_branch": "locked-infinity-cobra-2103229-multiview-stability-fill-passed",
        "protected_parent_apk_sha256": PARENT_APK_SHA,
        "packaging_base_sha256": PACKAGING_BASE_SHA,
        "native_engine_sha256": NATIVE_ENGINE_SHA,
        "native_engine_rebuilt": False,
        "authorized_delta": [
            "APK-side bounded fatal-signal register recorder companion library",
            "ApplicationExitInfo collector v2",
            "privacy-safe Activity lifecycle breadcrumbs/process-state summary",
            "native module-map snapshot",
            "version identity",
        ],
        "explicitly_unchanged": [
            "libkodi.so",
            "Cobra playback",
            "providers",
            "timeshift",
            "Multi-View behavior",
            "Infinity skin",
            "Command Center",
            "Health Center package",
        ],
        "status": "TEST CANDIDATE",
    }
    (audit / "scope.json").write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n")
    print("PASS: crash-forensics delta applied to exact locked 2103229 source")


if __name__ == "__main__":
    main()
