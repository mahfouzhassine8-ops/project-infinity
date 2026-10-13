#!/usr/bin/env python3
"""Launch prebuilt Kodi21.3 under Xvfb; collect actual renderer PNGs and logs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
CASES = [
    ('cover-like-dark', 'dark', 1080, 2400, 360, 800),
    ('cover-like-light', 'light', 1080, 2400, 360, 800),
    ('cover-like-oled', 'OLED', 1080, 2400, 360, 800),
    ('cover-like-cinema', 'cinema', 1080, 2400, 360, 800),
    ('inner-like-dark', 'dark', 2160, 2400, 720, 800),
    ('landscape-dark', 'dark', 2400, 1080, 800, 360),
    ('split-dark', 'dark', 1080, 1500, 360, 500),
    ('floating-light', 'light', 840, 1080, 280, 360),
]


def run_case(root, label, theme, width, height, dpw, dph, overlay):
    output = root / label
    profile = root / ('profile-' + label)
    command = [sys.executable, str(HERE / 'prepare.py'), '--profile', str(profile), '--output', str(output),
               '--width', str(width), '--height', str(height), '--dp-width', str(dpw), '--dp-height', str(dph),
               '--theme', theme, '--label', label]
    if overlay:
        command.extend(['--overlay', str(overlay)])
    subprocess.run(command, check=True)
    env = dict(os.environ, KODI_DATA=str(profile.resolve()), LIBGL_ALWAYS_SOFTWARE='1',
               GALLIUM_DRIVER='llvmpipe', SDL_AUDIODRIVER='dummy', KODI_AE_SINK='NULL')
    command = ['dbus-run-session', '--', 'xvfb-run', '-a', '-s',
               f'-screen 0 {width}x{height}x24 -nolisten tcp +extension GLX +render -noreset',
               'kodi', '--standalone', '--fullscreen', '--windowing=x11']
    # First-start Kodi disables newly discovered non-system add-ons. Bootstrap
    # only this disposable profile, then enable the test skin offline before
    # measuring the real dialog. No candidate file or user profile is changed.
    import sqlite3
    import signal
    import xml.etree.ElementTree as ET
    boot_started = time.monotonic()
    with (output / 'bootstrap-process.log').open('w') as bootlog:
        boot = subprocess.Popen(command, env=env, stdout=bootlog, stderr=subprocess.STDOUT, start_new_session=True)
        database = None
        while time.monotonic() - boot_started < 25:
            for file in (profile / 'userdata/Database').glob('Addons*.db'):
                try:
                    with sqlite3.connect(file, timeout=1) as db:
                        row = db.execute('SELECT enabled FROM installed WHERE addonID=?', ('skin.infinity.diggz',)).fetchone()
                        if row is not None:
                            database = file
                            break
                except sqlite3.DatabaseError:
                    pass
            if database is not None or boot.poll() is not None:
                break
            time.sleep(0.2)
        time.sleep(2)
        if boot.poll() is None:
            os.killpg(boot.pid, signal.SIGTERM)
            try:
                boot.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(boot.pid, signal.SIGKILL); boot.wait()
    if database is None:
        raise RuntimeError('Disposable Kodi bootstrap did not register the skin')
    for source in (profile / 'temp/kodi.log', profile / 'kodi.log'):
        if source.exists():
            shutil.copyfile(source, output / 'bootstrap-kodi.log')
    with sqlite3.connect(database) as db:
        previous = db.execute('SELECT enabled FROM installed WHERE addonID=?', ('skin.infinity.diggz',)).fetchone()
        db.execute('UPDATE installed SET enabled=1 WHERE addonID=?', ('skin.infinity.diggz',))
        enabled = db.execute('SELECT enabled FROM installed WHERE addonID=?', ('skin.infinity.diggz',)).fetchone()
        assert enabled == (1,)
    settings = profile / 'userdata/guisettings.xml'
    settings_root = ET.parse(settings).getroot()
    setting = settings_root.find("setting[@id='lookandfeel.skin']")
    if setting is None:
        setting = ET.SubElement(settings_root, 'setting', {'id': 'lookandfeel.skin'})
    setting.text = 'skin.infinity.diggz'
    if settings_root.find('resolutions') is None:
        ET.SubElement(settings_root, 'resolutions')
    ET.ElementTree(settings_root).write(settings, encoding='UTF-8', xml_declaration=True)
    (output / 'bootstrap-receipt.json').write_text(json.dumps({
        'test_only': True, 'database': database.name, 'previous_enabled': previous,
        'enabled_after': enabled, 'changed_addon': 'skin.infinity.diggz',
        'reason': 'Fresh-profile untrusted add-on admission; exact preview payload not modified.',
        'user_profile_touched': False}, indent=2))
    started = time.monotonic()
    with (output / 'process.log').open('w') as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        timed_out = False
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            timed_out = True
            import signal
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    for source in (profile / 'temp/kodi.log', profile / 'kodi.log'):
        if source.exists():
            shutil.copyfile(source, output / 'kodi.log')
    eventfile = output / 'events.json'
    events = json.loads(eventfile.read_text()) if eventfile.exists() else []
    opened = any(e['event'] == 'dialog-initialized' for e in events)
    captured = any(e['event'] == 'screenshot' and e['file'].startswith('preview-') for e in events)
    preview_active = any(e['event'] == 'capture-state' and 13000 <= e['current_dialog'] <= 13099
                         and e['properties'].get('Preview.Title') == 'Infinity Preview Test'
                         and (not overlay or e['properties'].get('Preview.LayoutReady') == 'true') for e in events)
    released = any(e['event'] == 'preview-returned' and not e['active'] and not e['nonce'] and not e['workers'] for e in events)
    result = {'case': label, 'duration_seconds': round(time.monotonic() - started, 2), 'process_exit': process.returncode,
              'timed_out': timed_out, 'dialog_initialized': opened, 'preview_captured': captured,
              'preview_active_with_real_metadata_at_capture': preview_active,
              'request_and_workers_released': released, 'physical_device_verified': False,
              'passed': opened and captured and preview_active and released and not timed_out,
              'errors': [e for e in events if e['event'] in ('exception', 'browser-exception', 'screenshot-missing')]}
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    # Profiles are disposable scratch, but retain all evidence above.
    shutil.rmtree(profile)
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--overlay', type=Path)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=True)
    version = subprocess.check_output(['kodi', '--version'], text=True, stderr=subprocess.STDOUT)
    (root / 'kodi-version.txt').write_text(version)
    assert '21.3' in version, 'Renderer must be the matching Kodi21.3 release: ' + version
    results = [run_case(root, 'before-210-dark', 'dark', 1080, 2400, 360, 800, None)]
    if args.overlay:
        assert (args.overlay / 'unified/InfinityFilePreview.xml').is_file()
        for name, theme, width, height, dpw, dph in (CASES[:3] if args.quick else CASES):
            result = run_case(root, 'after-211-' + name, theme, width, height, dpw, dph, args.overlay)
            results.append(result)
            if not result['passed']:
                break  # Retain failing evidence; do not repeat identical startup failure eight times.
    (root / 'renderer-results.json').write_text(json.dumps({'renderer': version.strip(), 'results': results,
          'physical_device_verified': False, 'native_android_dispatch_verified': False}, indent=2) + '\n')
    # Parent is an observational negative control; candidate must fully initialize
    # and dismiss. Failure cannot be converted to a green simulated screenshot.
    tested = results[1:] if args.overlay else results
    raise SystemExit(0 if all(r['passed'] for r in tested) else 1)
