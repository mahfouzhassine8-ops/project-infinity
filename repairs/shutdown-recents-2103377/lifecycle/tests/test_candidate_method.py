#!/usr/bin/env python3
"""Run the transformed guard method and real gate with controlled Java peers.

The historical counterexample harness is copied unchanged and hash-pinned.
This adapter makes its replacement peer obey the proposed entry lease. This
is a scoped mechanism test, NOT an Android/NativeActivity lifecycle test.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
SAVED_SHA = 'e30366a06c6c51b4f5b2525393afacf90e4d48c66add6b413aac7a8c3d610fff'
GUARD_SHA = 'fa53fecd9eb9436d3cd64b77f1e88ac83496cda606be75850cae79fe7c264459'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Historical harness anchor changed')
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guard', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    historical = HERE / 'saved_recents_harness.py'
    if sha(historical) != SAVED_SHA or sha(args.guard) != GUARD_SHA:
        raise ValueError('Not the exact historical harness and staged guard candidate')
    spec = importlib.util.spec_from_file_location('saved_harness', historical)
    saved = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(saved)
    gate = HERE.parent / 'InfinityTaskLifecycleGate.java.in'
    fragment = saved.method(args.guard.read_text())
    peers = 'package com.projectinfinity.kodi;\n' + saved.PEERS
    peers = once(peers,
        'if(injectAfterLastObservation&&retirementChecks==2) replacement();',
        'if(injectAfterLastObservation&&retirementChecks==2 && InfinityTaskLifecycleGate.retainEntry(d)) replacement();')
    peers = once(peers, 'File getFilesDir(){return new File(".");}',
                 'File getFilesDir(){return new File(System.getProperty("gate.directory"));}')
    peers = once(peers,
        'require(h.manager.task.removedWhileReplacementLive,"expected saved-source race did not reproduce");',
        'require(h.manager.task.removed&&!h.manager.task.removedWhileReplacementLive,"retirement must exclude replacement entry");\n'
        '    require(InfinityTaskLifecycleGate.retainEntry(h.getFilesDir()),"new entry must work after removal returns");\n'
        '    InfinityKodiShutdown.replacement();\n'
        '    require(InfinityKodiShutdown.current.alive,"replacement may now become live");')
    peers = once(peers, 'COUNTEREXAMPLE=replacement_after_last_snapshot_removed',
                 'TARGETED_CASE=entry_excluded_until_removal_returns')
    peers = once(peers, 'RELEASE_GATE=FAIL',
                 'RELEASE_GATE=BLOCKED_pending_full_native_Android_and_shutdown_validation')
    source = once(peers, '  static void require(', '  ' + fragment + '\n  static void require(')
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        package = folder / 'com/projectinfinity/kodi'
        package.mkdir(parents=True)
        harness = package / 'RecentsRaceHarness.java'
        helper = package / 'InfinityTaskLifecycleGate.java'
        harness.write_text(source)
        helper.write_text(gate.read_text().replace('@APP_PACKAGE@', 'com.projectinfinity.kodi'))
        compile_result = subprocess.run(['javac', '--release', '11', '-Xlint:all', '-Werror',
            '-d', str(folder), str(harness), str(helper)], capture_output=True, text=True, timeout=30)
        (args.out / 'candidate-method-compile.log').write_text(compile_result.stdout + compile_result.stderr)
        compile_result.check_returncode()
        result = subprocess.run(['java', '-ea', '-Dgate.directory=' + str(folder), '-cp', str(folder),
            'com.projectinfinity.kodi.RecentsRaceHarness'], capture_output=True, text=True, timeout=30)
        (args.out / 'candidate-method.log').write_text(result.stdout + result.stderr)
        result.check_returncode()
    report = {
        'cases': 6, 'controls': 5, 'targeted_entry_exclusion_case_passed': True,
        'guard_sha256': sha(args.guard),
        'compiled_method_sha256': hashlib.sha256(fragment.encode()).hexdigest(),
        'gate_sha256': sha(gate), 'historical_harness_sha256': sha(historical),
        'scope': 'Actual transformed guard method and gate with controlled task/owner peers. '
                 'The replacement peer now obeys the proposed admission gate; this does not '
                 'prove all Android entry paths are coordinated.',
        'full_release_gate': 'BLOCKED',
    }
    (args.out / 'candidate-method.json').write_text(json.dumps(report, indent=2) + '\n')
    (args.out / 'candidate-method-harness.java').write_text(source)
    print(result.stdout)


if __name__ == '__main__':
    main()
