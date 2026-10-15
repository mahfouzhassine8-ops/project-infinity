#!/usr/bin/env python3
"""Switch Close Kodi from Kodi JSON-RPC quit to Android task removal."""
import argparse
import hashlib
import json
from pathlib import Path

TARGET = 'tools/android/packaging/xbmc/src/InfinityExitCompletion.java.in'
PARENT_MAP = '8c4786d60f02d67a860f923729b7556543319fe1e9311aa068571385d2b1ac42'
SOURCE_COUNT = 254


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in root.rglob('*') if p.is_file()}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unexpected 3312 preimage: ' + old[:100])
    return text.replace(old, new, 1)


def transform(text):
    text = replace_once(text,
        'enum Phase { RUNNING, WAITING_FOR_STOP, QUIT_QUEUED, DESTROYING, COMPLETE, FORCED }',
        'enum Phase { RUNNING, ANDROID_TASK_REMOVAL, WAITING_FOR_STOP, QUIT_QUEUED, DESTROYING, COMPLETE, FORCED }')
    text = replace_once(text,
        '(phase==Phase.WAITING_FOR_STOP || phase==Phase.QUIT_QUEUED || phase==Phase.DESTROYING);',
        '(phase==Phase.ANDROID_TASK_REMOVAL || phase==Phase.WAITING_FOR_STOP || phase==Phase.QUIT_QUEUED || phase==Phase.DESTROYING);')
    text = replace_once(text,
        '    synchronized boolean stopped(boolean configurationChange) {',
        '''    synchronized boolean requestAndroidTaskRemoval() {
      if (phase != Phase.RUNNING) return false;
      requestedAt=SystemClock.elapsedRealtime();phase=Phase.ANDROID_TASK_REMOVAL;observeClose(this);return true;
    }
    synchronized boolean cancelAndroidTaskRemoval() {
      if (phase != Phase.ANDROID_TASK_REMOVAL) return false;
      phase=Phase.RUNNING;forgetClose(this);return true;
    }
    synchronized boolean stopped(boolean configurationChange) {''')
    text = replace_once(text,
        '''    if (!owner.mInfinityExitPlan.requestNormal()) return owner.mInfinityExitPlan.pending();
    owner.infinityStopWeatherCapture();
    record(owner, "exit.normal.requested");
    final WeakReference<Main> observed=new WeakReference<>(owner);
    WATCH.schedule(() -> {
      Main current=observed.get();
      if(current!=null && current.mInfinityExitPlan.stalled(SystemClock.elapsedRealtime()))
        record(current,"exit.graceful.boundExceeded.userRecoveryAvailable");
    }, STALL_BOUND_MS, java.util.concurrent.TimeUnit.MILLISECONDS);
    // Kodi's Android pause/stop callbacks can synchronously contact its core.
    // Do not begin Quit until those callbacks have returned.
    if (owner.mInfinityStopped) { afterStop(owner); return true; }
    if (!owner.moveTaskToBack(true)) {
      owner.mInfinityExitPlan.cancelBeforeQuit();
      record(owner, "exit.normal.backgroundRejected.noQuit"); return false;
    }
    return true;''',
        '''    if (!owner.mInfinityExitPlan.requestAndroidTaskRemoval()) return owner.mInfinityExitPlan.pending();
    owner.infinityStopWeatherCapture();
    record(owner, "exit.androidTaskRemoval.requested");
    final WeakReference<Main> observed=new WeakReference<>(owner);
    WATCH.schedule(() -> {
      Main current=observed.get();
      if(current!=null && current.mInfinityExitPlan.stalled(SystemClock.elapsedRealtime()))
        record(current,"exit.androidTaskRemoval.boundExceeded.userRecoveryAvailable");
    }, STALL_BOUND_MS, java.util.concurrent.TimeUnit.MILLISECONDS);
    // Match Android Recents removal: remove the NativeActivity task and let
    // Android deliver its normal lifecycle destruction. Do not issue
    // Application.Quit; Main.onDestroy owns NativeActivity cleanup.
    try { owner.finishAndRemoveTask(); }
    catch (RuntimeException denied) {
      owner.mInfinityExitPlan.cancelAndroidTaskRemoval();
      record(owner, "exit.androidTaskRemoval.rejected." + denied.getClass().getSimpleName());
      return false;
    }
    return true;''')
    text = replace_once(text,
        '''  static void afterStop(Main owner) {
    if (!owner.mInfinityExitPlan.stopped(owner.isChangingConfigurations())) return;''',
        '''  static void afterStop(Main owner) {
    if(owner.mInfinityExitPlan.phase()==Plan.Phase.ANDROID_TASK_REMOVAL){
      record(owner,"exit.androidTaskRemoval.androidStopped.noKodiQuit");return;
    }
    if (!owner.mInfinityExitPlan.stopped(owner.isChangingConfigurations())) return;''')
    return text


def apply(source, proof, output):
    parent = json.loads(proof.read_text())['after']
    if len(parent) != SOURCE_COUNT or sha(json.dumps(parent, sort_keys=True, separators=(',', ':')).encode()) != PARENT_MAP:
        raise ValueError('Not the complete exact 2103312 source proof')
    before = snapshot(source)
    if before != parent:
        raise ValueError('Android source differs from locked 2103312')
    target = source / TARGET
    original = target.read_text()
    changed = transform(original)
    target.write_text(changed)
    after = snapshot(source)
    changed_files = sorted(n for n in before if before[n] != after[n])
    if changed_files != [TARGET] or before.keys() != after.keys():
        raise ValueError('Unexpected source files changed')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'base_source_map': PARENT_MAP, 'before': before,
        'after': after, 'changed': changed_files, 'native_engine_changed': False},
        indent=2, sort_keys=True) + '\n')


def verify(source, receipt):
    proof = json.loads(receipt.read_text())
    actual = snapshot(source)
    if actual != proof['after'] or proof['changed'] != [TARGET] or proof['native_engine_changed']:
        raise ValueError('Android close source changed after validation')
    text = (source / TARGET).read_text()
    if 'owner.finishAndRemoveTask();' not in text or 'request_string(QUIT)' in text[text.index('static boolean requestNormal'):text.index('static void afterStop')]:
        raise ValueError('Normal close is not the declared Android task-removal path')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['apply', 'verify'])
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--proof', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'apply':
        if not args.proof:
            parser.error('apply requires --proof')
        apply(args.source, args.proof, args.receipt)
    verify(args.source, args.receipt)
    print('PASS: Close Kodi uses Android task removal; exact 3312 native engine and remaining source preserved')


if __name__ == '__main__':
    main()
