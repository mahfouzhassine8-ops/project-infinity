#!/usr/bin/env python3
"""Apply only the terminal-Activity async fix after the exact RC2 reconstruction.

No native, skin, provider-format, Main, service, or background-control changes.
The original RC2 generation and its preservation gates still run first.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
GRADLE = Path('tools/android/packaging/xbmc/build.gradle.in')
PREIMAGE = '1e5f769e7f71e82d20506b891f818e7b32d4289d07e6c37be4252724ac6149b1'
RC2 = '1.0.9-Infinity-Background-Control-RC2'
RELEASE = '1.0.9-Infinity-Lifecycle-Repair-RC3'
VERSION_CODE = 2103138
FIELDS = '''  // Terminal per-Activity state. Pausing, PiP and Fold reflow do not close it.
  private final Object mCobraAsyncLock = new Object();
  private volatile boolean mCobraAsyncDestroyed = false;
'''
METHODS = '''  private boolean isCobraAsyncAlive() {
    return !mCobraAsyncDestroyed && !isFinishing() && !isDestroyed();
  }

  private boolean submitCobraIo(Runnable task) {
    synchronized (mCobraAsyncLock) {
      if (!isCobraAsyncAlive() || mIo.isShutdown()) return false;
      try {
        mIo.execute(() -> {
          // shutdownNow is best effort; an already-dequeued task also checks here.
          if (!isCobraAsyncAlive() || Thread.currentThread().isInterrupted()) return;
          task.run();
        });
        return true;
      } catch (java.util.concurrent.RejectedExecutionException rejected) {
        // Contain the shutdown race only. Do not hide unrelated live-executor errors,
        // run network work on the UI thread, or recreate an executor after teardown.
        if (!isCobraAsyncAlive() || mIo.isShutdown()) return false;
        throw rejected;
      }
    }
  }

  private void publishCobraUi(Runnable task) {
    if (!isCobraAsyncAlive()) return;
    if (Looper.myLooper() == Looper.getMainLooper()) {
      if (isCobraAsyncAlive()) task.run();
      return;
    }
    synchronized (mCobraAsyncLock) {
      if (!isCobraAsyncAlive()) return;
      // Use this Activity's own Handler so teardown can remove queued publications.
      mMain.post(() -> {
        if (isCobraAsyncAlive()) task.run();
      });
    }
  }

  private void closeCobraAsyncWork() {
    synchronized (mCobraAsyncLock) {
      // Publish closure BEFORE releasing players, cancelling callbacks or shutdown.
      mCobraAsyncDestroyed = true;
      mMain.removeCallbacksAndMessages(null);
      mIo.shutdownNow();
    }
  }

'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace(text: str, old: str, new: str, count: int = 1) -> str:
    if text.count(old) != count:
        raise RuntimeError('Source contract changed: ' + repr(old[:90]))
    return text.replace(old, new)


def transform(java: str) -> str:
    if sha(java.encode()) != PREIMAGE:
        raise RuntimeError('Not the exact RC2 InfinityLiveActivity source')
    # Cover every source, guide, catalog, validation and episode task/callback.
    java = replace(java, 'mIo.execute(', 'submitCobraIo(', 6)
    java = replace(java, 'runOnUiThread(', 'publishCobraUi(', 10)
    java = replace(java, '  private final Handler mMain = new Handler(Looper.getMainLooper());\n',
                   '  private final Handler mMain = new Handler(Looper.getMainLooper());\n' + FIELDS)
    java = replace(java, '  protected void onDestroy() {\n',
                   '  protected void onDestroy() {\n    closeCobraAsyncWork();\n')
    java = replace(java, '    mIo.shutdownNow();\n', '')
    java = replace(java, '  private int dp(int value) {', METHODS + '  private int dp(int value) {')
    # Refuse direct calls before they touch a screen belonging to a finished Activity.
    for signature in (
        '  private void validateAndSave(\n      LiveSource candidate, LiveSource editing, AlertDialog dialog) {',
        '  private void loadAllEnabledSources(boolean showBusy) {',
        '  private void loadActiveSource(boolean showBusy) {',
        '  private void loadGuideAsync(LiveSource source) {',
        '  private void showVodLibrary(boolean series) {',
        '  private void openSeries(VodItem item) {',
    ):
        java = replace(java, signature, signature + '\n    if (!isCobraAsyncAlive()) return;')
    # Stop follow-on requests after teardown. Existing in-flight I/O is still bounded
    # by the unchanged transport timeouts; no promise that interruption cancels HTTP.
    java = replace(java, '  private String httpGet(String url) throws LiveException {\n',
                   '  private String httpGet(String url) throws LiveException {\n'
                   '    if (!isCobraAsyncAlive() || Thread.currentThread().isInterrupted())\n'
                   '      throw new LiveException("Request cancelled because Cobra closed.");\n')
    java = replace(java, '      while ((count = input.read(buffer)) != -1) {\n',
                   '      while ((count = input.read(buffer)) != -1) {\n'
                   '        if (mCobraAsyncDestroyed || Thread.currentThread().isInterrupted())\n'
                   '          throw new java.io.InterruptedIOException("Cobra closed");\n')
    # Player listeners are delivered by a separate queue; they must not re-arm timers
    # during/after release. Playback, PiP, audio ownership and resume policy are unchanged.
    java = replace(java, '        public void onPlaybackStateChanged(int playbackState) {\n',
                   '        public void onPlaybackStateChanged(int playbackState) {\n'
                   '          if (!isCobraAsyncAlive()) return;\n')
    java = replace(java, '        public void onPlayerError(PlaybackException error) {\n',
                   '        public void onPlayerError(PlaybackException error) {\n'
                   '          if (!isCobraAsyncAlive()) return;\n')
    java = replace(java, '@Override public void onPlayerError(PlaybackException error) { label.setText(',
                   '@Override public void onPlayerError(PlaybackException error) { if (!isCobraAsyncAlive()) return; label.setText(')
    java = replace(java, '  private final Runnable mAutoRefresh = new Runnable() {\n    @Override public void run() {\n',
                   '  private final Runnable mAutoRefresh = new Runnable() {\n    @Override public void run() {\n'
                   '      if (!isCobraAsyncAlive()) return;\n')
    java = replace(java, '  private final Runnable mProgressTicker = new Runnable() {\n    @Override public void run() {\n',
                   '  private final Runnable mProgressTicker = new Runnable() {\n    @Override public void run() {\n'
                   '      if (!isCobraAsyncAlive()) return;\n')
    for signature in ('  private void startSinglePlayer(String url) {', '  private void playNextEpisode() {'):
        java = replace(java, signature, signature + '\n    if (!isCobraAsyncAlive()) return;')
    return java


def apply(source: Path, receipt: Path, packager: Path) -> None:
    before = (source/LIVE).read_bytes()
    after = transform(before.decode())
    gradle = (source/GRADLE).read_text()
    gradle = replace(gradle, 'versionCode 2103137', f'versionCode {VERSION_CODE}')
    gradle = replace(gradle, f'versionName "{RC2}"', f'versionName "{RELEASE}"')
    row = json.loads(receipt.read_text())
    if row['files'][str(LIVE)]['after'] != sha(before):
        raise RuntimeError('RC2 source receipt mismatch')
    (source/LIVE).write_text(after)
    (source/GRADLE).write_text(gradle)
    for rel in (LIVE, GRADLE):
        row['files'][str(rel)]['after'] = sha((source/rel).read_bytes())
    row.update(version_code=VERSION_CODE, version_name=RELEASE,
               lifecycle_repair_base_commit='90d4efd2796828795f5e6d4e436d8cd4e43a6a6b',
               lifecycle_repair_preimage=PREIMAGE, terminal_async_guard=True,
               runtime_device_tested=False)
    receipt.write_text(json.dumps(row, indent=2, sort_keys=True)+'\n')
    # RC2's original packager is already configured by its bridge script. Preserve
    # all its engine/resource/manifest/signing gates, changing release identity only.
    constants = ROOT/'scripts/infinity_background_resume.py'
    text = constants.read_text()
    text = replace(text, 'VERSION_CODE = 2103137', f'VERSION_CODE = {VERSION_CODE}')
    text = replace(text, f"RELEASE = '{RC2}'", f"RELEASE = '{RELEASE}'")
    constants.write_text(text)
    text = packager.read_text()
    if text.count('Infinity-1.0.9-Infinity-Background-Control-RC2') != 2:
        raise RuntimeError('Unexpected RC2 packaging filenames')
    text = text.replace('Infinity-1.0.9-Infinity-Background-Control-RC2', 'Infinity-'+RELEASE)
    text = replace(text, 'docs/infinity-background-control-rc2.md', 'docs/infinity-lifecycle-repair-rc3.md')
    packager.write_text(text)
    print('PASS: exact RC2 Activity lifecycle guard; version 2103138; original packaging gates retained')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--packager',type=Path,required=True)
    a=p.parse_args();apply(a.source,a.receipt,a.packager)
