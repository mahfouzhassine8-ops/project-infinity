"""Two selected synthetic viewport/theme checks; no Infinity app, reset, or shutdown."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def adb(*args):
    return subprocess.check_output(['adb', *args], text=True, timeout=30).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    args = parser.parse_args()
    output = args.work / 'results'
    output.mkdir(parents=True, exist_ok=True)
    selected = [
        ('narrow-dark', '720x1680', '320', 'yes'),
        ('wide-light', '1472x1344', '320', 'no'),
    ]
    report = {'selected': selected, 'physical_Fold': 'NOT_RUN',
              'scope': 'Synthetic narrow/wide Android windows; both orientations exercised by instrumentation',
              'Infinity_shutdown': 'NOT_SELECTED', 'owner_installer': False, 'results': []}
    success = True
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
                                 '--theme', 'dark' if night == 'yes' else 'light'],
                                timeout=220)
        entry = {'profile': name, 'returncode': result.returncode,
                 'display': adb('shell', 'wm', 'size'),
                 'density': adb('shell', 'wm', 'density'),
                 'night_mode': adb('shell', 'cmd', 'uimode', 'night')}
        report['results'].append(entry)
        success &= result.returncode == 0
        # A failure is retained; the second geometry is independent and remains selected.
    report['pass'] = success
    (output / 'SELECTED-WINDOWS.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
