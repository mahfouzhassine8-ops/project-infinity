"""Two selected synthetic viewport/theme checks; no Infinity app, reset, or shutdown."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def adb(*args):
    return subprocess.check_output(['adb', *args], text=True, timeout=30).strip()


def education_state():
    style = adb('shell', 'wm', 'get-letterbox-style')
    match = re.search(r'^Is education enabled: (true|false)\s*$', style, re.MULTILINE)
    if match is None:
        raise RuntimeError('Cannot read exact letterbox education setting')
    return {'immersive': adb('shell', 'settings', 'get', 'secure', 'immersive_mode_confirmations'),
            'letterbox': match.group(1)}


def prepare_education(report):
    # Only first-use tutorials in this disposable component emulator are excluded.
    # App input security, system focus loss, window bounds and all lock checks remain enabled.
    report['emulator'] = adb('shell', 'getprop', 'ro.kernel.qemu')
    report['packages'] = adb('shell', 'pm', 'list', 'packages', 'com.projectinfinity')
    if report['emulator'] != '1' or 'package:com.projectinfinity.kodi' in report['packages'].splitlines():
        raise RuntimeError('Education fixture requires disposable emulator without Infinity installed')
    # Android BasicShellCommandHandler returns -1 (adb 255) after normal onHelp().
    # Validate the actual help, not a zero exit status; mutations still require success.
    help_result = subprocess.run(['adb', 'shell', 'wm', 'help'], text=True,
                                 capture_output=True, timeout=30)
    help_text = help_result.stdout
    report['cli_help'] = {'returncode': help_result.returncode,
                          'stdout': help_text, 'stderr': help_result.stderr}
    if (help_result.returncode not in (0, 255) or help_result.stderr.strip() or
            not help_text.startswith('Window manager (window) commands:') or
            'set-letterbox-style' not in help_text or '--isEducationEnabled' not in help_text):
        raise RuntimeError('Exact selected letterbox education CLI unsupported')
    report['cli_supported'] = True
    report['before'] = education_state()
    adb('shell', 'settings', 'put', 'secure', 'immersive_mode_confirmations', 'confirmed')
    adb('shell', 'wm', 'set-letterbox-style', '--isEducationEnabled', 'false')
    report['applied'] = education_state()
    if report['applied'] != {'immersive': 'confirmed', 'letterbox': 'false'}:
        raise RuntimeError('Education setup readback mismatch')


def restore_education(report):
    before = report.get('before')
    if before is None:
        return
    failures = []
    commands = [
        ('shell', 'settings', 'delete', 'secure', 'immersive_mode_confirmations')
        if before['immersive'] == 'null' else
        ('shell', shlex.join(['settings', 'put', 'secure', 'immersive_mode_confirmations', before['immersive']])),
        ('shell', 'wm', 'set-letterbox-style', '--isEducationEnabled', before['letterbox']),
    ]
    for command in commands:
        try:
            adb(*command)
        except Exception as error:
            failures.append(type(error).__name__ + ': ' + str(error))
    try:
        report['restored'] = education_state()
        if report['restored'] != before:
            failures.append('Education restoration readback mismatch')
    except Exception as error:
        failures.append(type(error).__name__ + ': ' + str(error))
    report['restore_errors'] = failures
    if failures:
        raise RuntimeError('Education fixture restoration failed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--selection', choices=['full', 'pip_tail', 'retirement_pip_tail'], required=True)
    args = parser.parse_args()
    output = args.work / 'results'
    output.mkdir(parents=True, exist_ok=True)
    selected = [
        ('narrow-dark', '720x1680', '320', 'yes'),
        ('wide-light', '1472x1344', '320', 'no'),
    ]
    report = {'selected': selected, 'physical_Fold': 'NOT_RUN',
              'scope': ('Synthetic narrow/wide Android windows; selected retirement/PiP/lifecycle tail only'
                        if args.selection != 'full' else
                        'Synthetic narrow/wide Android windows; full input/rotation/lifecycle sequence'),
              'Infinity_shutdown': 'NOT_SELECTED', 'owner_installer': False, 'results': [],
              'education_fixture': {},
              'excluded': ['First-use immersive tutorial', 'First-use letterbox tutorial'],
              'selection': args.selection}
    if args.selection != 'full':
        retained = json.loads((HERE / 'ANDROID-ATTEMPT6.json').read_text())
        report['retained_prefix'] = {'run': retained['run'],
                                     'receipt_sha256': retained['passed_receipt_sha256'],
                                     'scope': 'Input/hold/ACK/rotation/Home prefix on previous Dialog bytes only; original run remains failed; no current full-pass claim'}
    success = True
    try:
        prepare_education(report['education_fixture'])
        for name, size, density, night in selected:
            # Only this disposable emulator's display and theme are selected; no owner settings.
            adb('shell', 'wm', 'size', size)
            adb('shell', 'wm', 'density', density)
            adb('shell', 'cmd', 'uimode', 'night', night)
            adb('shell', 'wm', 'dismiss-keyguard')
            destination = output / name
            result = subprocess.run([sys.executable, str(HERE / 'run_probe.py'),
                                     '--apk', str(args.work / 'build/CI-LOCK-PROBE-DEBUG-NOT-OWNER.apk'),
                                     '--output', str(destination), '--aapt2', str(args.sdk / 'aapt2'),
                                     '--theme', 'dark' if night == 'yes' else 'light',
                                     '--selection', args.selection],
                                    timeout=220)
            entry = {'profile': name, 'returncode': result.returncode,
                     'display': adb('shell', 'wm', 'size'),
                     'density': adb('shell', 'wm', 'density'),
                     'night_mode': adb('shell', 'cmd', 'uimode', 'night')}
            report['results'].append(entry)
            success &= result.returncode == 0
            receipt_path = destination / 'ANDROID-LOCK-COMPONENT.json'
            if receipt_path.exists() and json.loads(receipt_path.read_text()).get('phase') == 'install':
                report['not_run'] = [row[0] for row in selected[len(report['results']):]]
                break  # A shared package-install failure cannot be retested meaningfully at another size.
            # A failure is retained; the second geometry is independent and remains selected.
    except Exception as error:
        success = False
        report['setup_or_execution_error'] = type(error).__name__ + ': ' + str(error)
    finally:
        try:
            restore_education(report['education_fixture'])
        except Exception as error:
            success = False
            report['restoration_error'] = type(error).__name__ + ': ' + str(error)
    report['pass'] = success
    (output / 'SELECTED-WINDOWS.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
