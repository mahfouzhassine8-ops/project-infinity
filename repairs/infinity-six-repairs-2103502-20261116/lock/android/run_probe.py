"""Run only the reviewed disposable Android lock component instrumentation; never Infinity."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--adb', default='adb')
    parser.add_argument('--aapt2', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    package = 'com.projectinfinity.lockqa'
    badging = subprocess.check_output([str(args.aapt2), 'dump', 'badging', str(args.apk)], text=True)
    assert "package: name='" + package + "'" in badging, 'Only the disposable lock package may be installed'
    run_id = uuid.uuid4().hex
    subprocess.run([args.adb, 'install', '-r', str(args.apk)], check=True, capture_output=True, text=True, timeout=60)
    command = [args.adb, 'shell', 'am', 'instrument', '-w', '-r', '-e', 'runId', run_id,
               package + '/com.projectinfinity.kodi.InfinityLockProbeInstrumentation']
    try:
        run = subprocess.run(command, text=True, capture_output=True, timeout=180)
        output = run.stdout + run.stderr
    except subprocess.TimeoutExpired as error:
        output = str(error.stdout or '') + '\n' + str(error.stderr or '')
    (args.output / 'instrumentation.txt').write_text(output)
    result = None
    for line in output.splitlines():
        prefix = 'INSTRUMENTATION_RESULT: lock_result='
        if line.startswith(prefix): result = json.loads(line[len(prefix):])
    if result is None:
        result = {'pass': False, 'runId': run_id, 'error': 'No complete instrumentation receipt before deadline'}
    assert result.get('runId') == run_id, 'Stale instrumentation receipt'
    result.update(apk_sha256=hashlib.sha256(args.apk.read_bytes()).hexdigest(), package=package,
                  owner_installer=False, Infinity_shutdown='NOT_RUN', native_bridge='NOT_INCLUDED', Kodi_playback='NOT_RUN')
    (args.output / 'ANDROID-LOCK-COMPONENT.json').write_text(json.dumps(result, indent=2) + '\n')
    logs = subprocess.run([args.adb, 'logcat', '-d', '-v', 'threadtime', 'AndroidRuntime:E', '*:S'], text=True, capture_output=True, timeout=15)
    (args.output / 'android-errors.txt').write_text(logs.stdout)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
