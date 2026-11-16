"""Run only the reviewed disposable Android lock component instrumentation; never Infinity."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import uuid


def completed_result(output, run_id, returncode, timed_out):
    """A receipt is not success unless the Android instrumentation actually completed."""
    receipts = []
    for line in output.splitlines():
        prefix = 'INSTRUMENTATION_RESULT: lock_result='
        if line.startswith(prefix):
            try:
                receipts.append(json.loads(line[len(prefix):]))
            except ValueError:
                receipts.append(None)
    terminal = re.findall(r'^INSTRUMENTATION_CODE: (-?\d+)\s*$', output, re.MULTILINE)
    result = receipts[0] if len(receipts) == 1 and isinstance(receipts[0], dict) else None
    failures = []
    if timed_out: failures.append('Instrumentation process timed out')
    if returncode != 0: failures.append('Instrumentation command did not exit successfully')
    if terminal != ['-1']: failures.append('Missing or unsuccessful instrumentation terminal code')
    if result is None:
        result = {'runId': run_id}
        failures.append('Expected exactly one complete instrumentation receipt')
    elif result.get('runId') != run_id:
        failures.append('Stale instrumentation receipt')
    if result.get('pass') is not True: failures.append('Component checks did not pass')
    if failures:
        result['reported_pass_before_process_gate'] = result.get('pass')
        result['pass'] = False
        result['execution_failures'] = failures
    result['command_returncode'] = returncode
    result['command_timed_out'] = timed_out
    result['terminal_codes'] = terminal
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--adb', default='adb')
    parser.add_argument('--aapt2', type=Path, required=True)
    parser.add_argument('--theme', choices=['light', 'dark'], required=True)
    parser.add_argument('--selection', choices=['full', 'pip_tail', 'retirement_pip_tail'], required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    package = 'com.projectinfinity.lockqa'
    badging = subprocess.check_output([str(args.aapt2), 'dump', 'badging', str(args.apk)], text=True)
    assert "package: name='" + package + "'" in badging, 'Only the disposable lock package may be installed'
    run_id = uuid.uuid4().hex
    install = subprocess.run([args.adb, 'install', '-r', str(args.apk)], capture_output=True, text=True, timeout=60)
    install_output = install.stdout + install.stderr
    (args.output / 'install.txt').write_text(install_output)
    if install.returncode != 0:
        failure = {'pass': False, 'runId': run_id, 'phase': 'install',
                   'returncode': install.returncode, 'error': install_output,
                   'apk_sha256': hashlib.sha256(args.apk.read_bytes()).hexdigest(),
                   'instrumentation': 'NOT_RUN', 'package': package, 'owner_installer': False}
        (args.output / 'ANDROID-LOCK-COMPONENT.json').write_text(json.dumps(failure, indent=2) + '\n')
        print(json.dumps(failure, indent=2))
        raise SystemExit(1)
    command = [args.adb, 'shell', 'am', 'instrument', '-w', '-r', '-e', 'runId', run_id,
               '-e', 'expectedTheme', args.theme, '-e', 'selection', args.selection,
               package + '/com.projectinfinity.kodi.InfinityLockProbeInstrumentation']
    returncode = None
    timed_out = False
    try:
        run = subprocess.run(command, text=True, capture_output=True, timeout=180)
        output = run.stdout + run.stderr
        returncode = run.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        def decoded(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else (value or '')
        output = decoded(error.stdout) + '\n' + decoded(error.stderr)
    (args.output / 'instrumentation.txt').write_text(output)
    result = completed_result(output, run_id, returncode, timed_out)
    if result.get('selection') != args.selection:
        result['pass'] = False
        result.setdefault('execution_failures', []).append('Executed component selection mismatch')
    result.update(apk_sha256=hashlib.sha256(args.apk.read_bytes()).hexdigest(), package=package,
                  owner_installer=False, Infinity_shutdown='NOT_RUN', native_bridge='NOT_INCLUDED', Kodi_playback='NOT_RUN')
    receipt = args.output / 'ANDROID-LOCK-COMPONENT.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    capture_errors = []
    if result['pass'] is not True:
        for name in ('lock-failure-' + run_id + '.png', 'lock-failure-' + run_id + '-window.txt'):
            try:
                capture = subprocess.run([args.adb, 'exec-out', 'run-as', package, 'cat', 'files/' + name],
                                         capture_output=True, timeout=15)
                if capture.returncode == 0:
                    (args.output / name).write_bytes(capture.stdout)
                else: capture_errors.append(name + ': unavailable for this run')
            except subprocess.TimeoutExpired:
                capture_errors.append(name + ': retrieval deadline')
    try:
        logs = subprocess.run([args.adb, 'logcat', '-d', '-v', 'threadtime', 'AndroidRuntime:E',
                               'InputDispatcher:W', 'InputManager:W', 'WindowManager:W',
                               'InfinityLockProbe:I', 'InfinityVideoLock:E', '*:S'],
                              text=True, capture_output=True, timeout=15)
        (args.output / 'android-errors.txt').write_text(logs.stdout)
        if logs.returncode != 0: capture_errors.append('logcat retrieval failed')
    except subprocess.TimeoutExpired:
        capture_errors.append('logcat retrieval deadline')
    result['capture_errors'] = capture_errors
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
