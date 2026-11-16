"""Selected host test of the actual production restored() method, not an Android run."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / 'java/com/projectinfinity/kodi/InfinityVideoLockBridge.java'


def extract_method(source):
    start = source.index('  public static void restored(')
    opening = source.index('{', start)
    depth = 0
    mode = 'code'
    escaped = False
    index = opening
    while index < len(source):
        char = source[index]
        following = source[index:index + 2]
        if mode == 'line':
            if char == '\n':
                mode = 'code'
        elif mode == 'block':
            if following == '*/':
                mode = 'code'
                index += 1
        elif mode in ('"', "'"):
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == mode:
                mode = 'code'
        elif following in ('//', '/*'):
            mode = 'line' if following == '//' else 'block'
            index += 1
        elif char in ('"', "'"):
            mode = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
        index += 1
    raise AssertionError('Unterminated actual restored method')


HARNESS = r'''
package com.projectinfinity.kodi;

/** Compile-only test adapters for production restored(), copied verbatim below. */
public final class InfinityVideoLockBridge {
  static final Queue UI = new Queue();
  static InfinityVideoLockBridge current;
  static int nativeCalls, checks;
  static boolean commitResult = true;
  final long session;
  final DialogAdapter dialog;
  boolean disposed;
  Object timeout = new Object();
  int cancelled, rejectedMessage, disposedCount;

  InfinityVideoLockBridge(long session, long epoch, long request) {
    this.session = session;
    dialog = new DialogAdapter(session, epoch, request);
  }
  void cancelTimeout() { cancelled++; timeout = null; }
  void unavailable() { rejectedMessage++; }
  void dispose(boolean notifyNative) {
    disposed = true; disposedCount++;
    if (current == this) current = null;
  }
  static boolean nativeCommit(long session, long grant) {
    nativeCalls++;
    return commitResult;
  }

__ACTUAL_RESTORED_METHOD__

  static final class Queue {
    final java.util.ArrayDeque<Runnable> pending = new java.util.ArrayDeque<>();
    boolean post(Runnable action) { pending.add(action); return true; }
    void drain() { while (!pending.isEmpty()) pending.remove().run(); }
  }
  static final class DialogAdapter {
    final long session;
    long epoch, request;
    boolean pending = true, locked = true;
    int confirmed, rejected;
    DialogAdapter(long session, long epoch, long request) {
      this.session = session; this.epoch = epoch; this.request = request;
    }
    boolean canConfirmUnlocked(long s, long e, long r) {
      return locked && pending && s == session && e == epoch && r == request;
    }
    boolean confirmUnlocked(long s, long e, long r) {
      if (!canConfirmUnlocked(s, e, r)) return false;
      confirmed++; locked = false; pending = false; return true;
    }
    void rejectUnlock(long s, long e, long r) {
      if (!canConfirmUnlocked(s, e, r)) throw new AssertionError("Reject must match current tuple");
      rejected++; pending = false;
    }
  }
  static InfinityVideoLockBridge fresh() {
    if (!UI.pending.isEmpty()) throw new AssertionError("Previous queue not drained");
    nativeCalls = 0; commitResult = true;
    return current = new InfinityVideoLockBridge(100, 10, 20);
  }
  static void check(boolean condition, String label) {
    checks++;
    if (!condition) throw new AssertionError(label);
  }
  public static void main(String[] args) {
    InfinityVideoLockBridge bridge = fresh();
    restored(100, 10, 20, 33); // old callback already queued before the user retries
    bridge.dialog.epoch = 11; bridge.dialog.request = 21;
    Object newTimer = bridge.timeout = new Object();
    UI.drain();
    check(bridge.timeout == newTimer && bridge.cancelled == 0,
        "Stale epoch ACK cannot cancel the newer hold's retry timer");
    check(nativeCalls == 0 && bridge.dialog.locked && current == bridge,
        "Stale epoch ACK cannot commit or dispose the current session");

    bridge = fresh(); newTimer = bridge.timeout;
    restored(100, 10, 19, 33); UI.drain();
    check(bridge.timeout == newTimer && bridge.cancelled == 0,
        "Stale request in the current epoch cannot cancel its timer");
    check(nativeCalls == 0 && bridge.dialog.pending, "Stale request leaves current unlock pending");

    bridge = fresh(); newTimer = bridge.timeout;
    restored(99, 10, 20, 33); UI.drain();
    check(bridge.timeout == newTimer && bridge.cancelled == 0 && nativeCalls == 0,
        "Stale session ACK has no timer or commit effects");

    bridge = fresh();
    restored(100, 10, 20, 33); UI.drain();
    check(nativeCalls == 1 && bridge.dialog.confirmed == 1 && !bridge.dialog.locked,
        "Matching positive ACK commits and confirms once");
    check(bridge.cancelled == 1 && bridge.timeout == null && bridge.disposedCount == 1 && current == null,
        "Matching positive ACK retires only its own timer and bridge");
    check(bridge.rejectedMessage == 0 && bridge.dialog.rejected == 0, "Successful ACK does not claim failure");

    bridge = fresh();
    restored(100, 10, 20, 0); UI.drain();
    check(nativeCalls == 0 && bridge.dialog.locked && !bridge.dialog.pending,
        "Negative ACK keeps input locked and rejects its pending request");
    check(bridge.cancelled == 1 && bridge.dialog.rejected == 1 && bridge.rejectedMessage == 1 && current == bridge,
        "Negative ACK offers retry without disposing the lock owner");
    bridge.dialog.epoch = 11; bridge.dialog.request = 21; bridge.dialog.pending = true;
    newTimer = bridge.timeout = new Object();
    restored(100, 10, 20, 0); UI.drain();
    check(bridge.timeout == newTimer && bridge.cancelled == 1,
        "Late duplicate negative ACK does not cancel retry timer");
    restored(100, 11, 21, 34); UI.drain();
    check(!bridge.dialog.locked && bridge.dialog.confirmed == 1 && current == null,
        "Fresh matching ACK can complete an explicit retry");

    bridge = fresh(); commitResult = false;
    restored(100, 10, 20, 33); UI.drain();
    check(nativeCalls == 1 && bridge.dialog.locked && bridge.dialog.confirmed == 0,
        "Native COMMIT rejection cannot dismiss the input barrier");
    check(bridge.dialog.rejected == 1 && bridge.rejectedMessage == 1 && current == bridge,
        "Native COMMIT rejection leaves retry available");

    bridge = fresh(); bridge.disposed = true; newTimer = bridge.timeout;
    restored(100, 10, 20, 33); UI.drain();
    check(bridge.timeout == newTimer && bridge.cancelled == 0 && nativeCalls == 0,
        "Disposed owner ignores delayed acknowledgement");
    current = null;
    restored(100, 10, 20, 33); UI.drain();
    check(nativeCalls == 0, "Missing owner does not invoke native COMMIT");
    System.out.println("PASS actual Bridge.restored " + checks + " assertions");
  }
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', type=Path, default=Path('/workspace/scratch/network-baseline-2103477/ecj-3.37.0.jar'))
    parser.add_argument('--output', type=Path, default=Path('/tmp/infinity502-lock-ack-host'))
    parser.add_argument('--receipt', type=Path, default=ROOT / 'BRIDGE-ACK-TEST.json')
    args = parser.parse_args()
    source = BRIDGE.read_text()
    method = extract_method(source)
    args.output.mkdir(parents=True, exist_ok=True)
    harness = args.output / 'InfinityVideoLockBridge.java'
    harness.write_text(HARNESS.replace('__ACTUAL_RESTORED_METHOD__', method))
    compiled = subprocess.run(['java', '-jar', str(args.compiler), '-17', '-d', str(args.output / 'classes'), str(harness)], text=True, capture_output=True)
    executed = None
    if compiled.returncode == 0:
        executed = subprocess.run(['java', '-cp', str(args.output / 'classes'), 'com.projectinfinity.kodi.InfinityVideoLockBridge'], text=True, capture_output=True)
    passed = compiled.returncode == 0 and executed is not None and executed.returncode == 0
    report = {
        'status': 'PASS_EXACT_RESTORED_METHOD_HOST_CHECKS' if passed else 'FAIL',
        'scope': 'Exact actual production Bridge.restored method with serial UI queue, timer and native-commit adapters; no actual Dialog, JNI, engine, or Android execution',
        'bridge_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'restored_method_sha256': hashlib.sha256(method.encode()).hexdigest(),
        'harness_sha256': hashlib.sha256(harness.read_bytes()).hexdigest(),
        'compiler_sha256': hashlib.sha256(args.compiler.read_bytes()).hexdigest(),
        'compile_exit_code': compiled.returncode,
        'compile_output': compiled.stdout + compiled.stderr,
        'test_exit_code': None if executed is None else executed.returncode,
        'test_output': '' if executed is None else executed.stdout + executed.stderr,
        'unchanged_128_state_assertions': 'NOT_RERUN',
        'Android': 'NOT_RUN',
        'shutdown': 'NOT_RUN'
    }
    args.receipt.write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'])
    print(report['compile_output'], end='')
    print(report['test_output'], end='')
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
