#!/usr/bin/env python3
"""RC3: fence dead-Activity async work on the exact Background Control RC2 source.

Apply after both background transforms. No native, skin, service or manifest edits.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
GRADLE = Path('tools/android/packaging/xbmc/build.gradle.in')
RC2_SHA = '1e5f769e7f71e82d20506b891f818e7b32d4289d07e6c37be4252724ac6149b1'
RC2_GRADLE_SHA = '89e0b5532736496e338adc6f3b4f8523360d7686d3e39d112b1c098e3ca50cee'
RC2_APK_SHA = 'd709c9dbf7224a9cfe4198cffb3adf523449fdc34af8c373f1c4463cdb494930'
RELEASE = '1.0.9-Infinity-Lifecycle-Repair-RC3'
VERSION_CODE = 2103138

HELPERS = '''  // Activity-instance lifetime, not background/foreground policy. Never reset.
  private volatile boolean mAsyncDestroyed = false;
  private final Object mAsyncLock = new Object();

  private boolean isCobraAsyncAlive() {
    return !mAsyncDestroyed && !isFinishing() && !isDestroyed();
  }

  private boolean submitCobraIo(Runnable task) {
    if (!isCobraAsyncAlive() || mIo.isShutdown()) return false;
    try {
      mIo.execute(() -> {
        if (isCobraAsyncAlive() && !Thread.currentThread().isInterrupted()) task.run();
      });
      return true;
    } catch (java.util.concurrent.RejectedExecutionException error) {
      // shutdown can win between the check and execute. Never recreate the pool
      // or run rejected network work on the caller/UI thread.
      if (isCobraAsyncAlive() && !mIo.isShutdown()) {
        android.util.Log.w("InfinityCobraAsync", "Active executor rejected a task");
      }
      return false;
    }
  }

  private boolean postCobraUi(Runnable task) {
    if (Looper.myLooper() == mMain.getLooper()) {
      if (!isCobraAsyncAlive()) return false;
      task.run();
      return true;
    }
    synchronized (mAsyncLock) {
      if (!isCobraAsyncAlive()) return false;
      // Use our own Handler, not Activity.runOnUiThread's unowned queue.
      // Check again at execution: destroy/finish can follow a successful post.
      return mMain.post(() -> {
        if (isCobraAsyncAlive()) task.run();
      });
    }
  }

  private boolean postCobraDelayed(Runnable task, long delayMs) {
    synchronized (mAsyncLock) {
      if (!isCobraAsyncAlive()) return false;
      // Keep the original Runnable identity: existing removeCallbacks still works.
      return mMain.postDelayed(task, delayMs);
    }
  }

  private void stopCobraAsync() {
    synchronized (mAsyncLock) {
      mAsyncDestroyed = true;
      mMain.removeCallbacksAndMessages(null);
    }
    // Non-blocking cancellation. In-flight I/O may finish, but cannot publish
    // or enqueue successor work. Do not wait for workers on the Android UI thread.
    mIo.shutdownNow();
  }

'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError('Unexpected preimage: ' + old[:100])
    return text.replace(old, new, 1)


def transform(java: str) -> str:
    if digest(java.encode()) != RC2_SHA:
        raise RuntimeError('Not the exact compiled RC2 Activity source')
    for old, new, expected in (
        ('mIo.execute(', 'submitCobraIo(', 6),
        ('runOnUiThread(', 'postCobraUi(', 10),
        ('mMain.postDelayed(', 'postCobraDelayed(', 11),
    ):
        if java.count(old) != expected:
            raise RuntimeError('Async inventory drift: ' + old)
        java = java.replace(old, new)
    java = once(java, '  protected void onDestroy() {\n',
                '  protected void onDestroy() {\n    stopCobraAsync();\n')
    java = once(java, '    mIo.shutdownNow();\n', '')
    # Deny direct calls before they mutate any UI or enqueue work.
    for signature in (
        '  private void validateAndSave(\n      LiveSource candidate, LiveSource editing, AlertDialog dialog) {\n',
        '  private void loadAllEnabledSources(boolean showBusy) {\n',
        '  private void loadActiveSource(boolean showBusy) {\n',
        '  private void loadGuideAsync(LiveSource source) {\n',
        '  private void showVodLibrary(boolean series) {\n',
        '  private void openSeries(VodItem item) {\n',
        '  private void rebuildCobraShellIfNeeded() {\n',
    ):
        java = once(java, signature, signature + '    if (!isCobraAsyncAlive()) return;\n')
    # Android/Media3 can deliver queued listener events during/after release.
    for signature, expected in (
        ('public void onPlaybackStateChanged(int playbackState) {', 1),
        ('public void onPlayerError(PlaybackException error) {', 2),
    ):
        if java.count(signature) != expected:
            raise RuntimeError('Player callback inventory drift')
        java = java.replace(signature, signature + '\n          if (!isCobraAsyncAlive()) return;')
    return once(java, '  private InfinityCobraFeatureRuntime mFeatures;\n',
                HELPERS + '  private InfinityCobraFeatureRuntime mFeatures;\n')


def apply(source: Path, receipt: Path) -> None:
    original = (source / LIVE).read_bytes()
    gradle = (source / GRADLE).read_bytes()
    if digest(gradle) != RC2_GRADLE_SHA:
        raise RuntimeError('Not the exact RC2 Gradle source')
    java = transform(original.decode())
    changed_gradle = once(gradle.decode(), 'versionCode 2103137', f'versionCode {VERSION_CODE}')
    changed_gradle = once(changed_gradle, 'versionName "1.0.9-Infinity-Background-Control-RC2"',
                          f'versionName "{RELEASE}"')
    row = json.loads(receipt.read_text())
    if row['version_code'] != 2103137 or row['files'][str(LIVE)]['after'] != RC2_SHA:
        raise RuntimeError('Source receipt is not RC2')
    (source / LIVE).write_text(java)
    (source / GRADLE).write_text(changed_gradle)
    row.update(version_code=VERSION_CODE, version_name=RELEASE,
               lifecycle_repair=True, predecessor_apk_sha256=RC2_APK_SHA,
               predecessor_source_commit='90d4efd2796828795f5e6d4e436d8cd4e43a6a6b')
    for p in (LIVE, GRADLE):
        row['files'][str(p)]['after'] = digest((source / p).read_bytes())
    receipt.write_text(json.dumps(row, indent=2, sort_keys=True) + '\n')
    # These are build-time metadata changes only. Keep all existing packager gates.
    module = ROOT / 'scripts/infinity_background_resume.py'
    text = once(module.read_text(), 'VERSION_CODE = 2103137', f'VERSION_CODE = {VERSION_CODE}')
    text = once(text, "RELEASE = '1.0.9-Infinity-Background-Control-RC2'", f"RELEASE = '{RELEASE}'")
    module.write_text(text)
    packager = ROOT / 'scripts/package_background_resume.py'
    text = packager.read_text().replace('Infinity-1.0.9-Infinity-Background-Control-RC2', 'Infinity-' + RELEASE)
    text = text.replace('docs/infinity-background-control-rc2.md', 'docs/infinity-lifecycle-repair-rc3.md')
    packager.write_text(text)
    print('PASS: RC3 lifetime gate; six I/O routes, ten UI callbacks, eleven timers; native/skin untouched')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    a = p.parse_args()
    apply(a.source, a.receipt)
