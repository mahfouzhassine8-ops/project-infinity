#!/usr/bin/env python3
"""Stage a disposable emulator only; use public Kodi API and production launcher."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import time

HERE = Path(__file__).resolve().parent
p = HERE.parent / 'android-checkpoint-shutdown/runtime-tests/essential_android_probe.py'
spec = importlib.util.spec_from_file_location('preserved_android_probe', p)
probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
ADDON = 'script.infinity.watchednative.test'


def main(args):
    args.out.mkdir(parents=True, exist_ok=True)
    report = dict(passed=False, scope='Actual signed ARM64 candidate on disposable API30 emulator',
                  physical_fold_verified=False, apk_sha256=hashlib.sha256(args.apk.read_bytes()).hexdigest())
    try:
        assert report['apk_sha256'] == args.expected_sha256
        probe.adb('root'); probe.adb('wait-for-device')
        assert probe.shell('getprop', 'ro.kernel.qemu').strip() == '1', 'Disposable emulator required'
        assert probe.PACKAGE not in probe.shell('pm', 'list', 'packages', probe.PACKAGE), 'Fresh emulator required'
        assert 'arm64-v8a' in probe.shell('getprop', 'ro.product.cpu.abilist')
        assert 'Success' in probe.adb('install', '--no-incremental', args.apk)
        probe.shell('input', 'keyevent', '82')
        for permission in ('android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE'):
            probe.shell('pm', 'grant', probe.PACKAGE, permission, check=False)
        probe.shell('appops', 'set', probe.PACKAGE, 'MANAGE_EXTERNAL_STORAGE', 'allow', check=False)
        probe.shell('mkdir', '-p', probe.PRIVATE + '/shared_prefs', probe.PROFILE + '/../addons')
        uid = probe.shell('stat', '-c', '%u', probe.PRIVATE).strip(); assert uid.isdigit(); probe.APP_UID = uid
        prefs = args.out / 'test-preference.xml'; prefs.write_text('<map><string name="default">infinity</string></map>\n')
        probe.adb('push', prefs, probe.PRIVATE + '/shared_prefs/infinity_experience.xml')
        fixture = args.out / 'first-party-fixture'; fixture.mkdir()
        manifest = {}
        for addon_id in probe.FIRST_PARTY:
            shutil.copytree(args.installed_addons / addon_id, fixture / addon_id, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            for path in sorted((fixture / addon_id).rglob('*')):
                if path.is_file(): manifest[path.relative_to(fixture).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        assert hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == 'eb61ddf66a01f434978c9ea070131311360ad76c536dd704355738db9179c1a5'
        for addon_id in probe.FIRST_PARTY: probe.adb('push', fixture / addon_id, probe.PROFILE + '/../addons/' + addon_id)
        extra = fixture / ADDON; xml = extra / 'resources/skins/Default/1080i'; xml.mkdir(parents=True)
        (extra / 'addon.xml').write_text('<addon id="' + ADDON + '" name="Native Watched Fixture" version="1.0.0" provider-name="Infinity CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Offline native row checks</summary><description lang="en_GB">Disposable emulator only</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        shutil.copyfile(HERE / 'android_native_fixture.py', extra / 'default.py')
        (xml / 'NativeWatchedFixture.xml').write_text('<window><defaultcontrol>50</defaultcontrol><controls><control type="list" id="50"><left>50</left><top>50</top><width>900</width><height>800</height><itemlayout height="80" width="900"><control type="label"><width>850</width><height>70</height><font>font13</font><label>$INFO[ListItem.Label]</label></control></itemlayout><focusedlayout height="80" width="900"><control type="label"><width>850</width><height>70</height><font>font13</font><label>$INFO[ListItem.Label]</label></control></focusedlayout></control></controls></window>')
        probe.adb('push', extra, probe.PROFILE + '/../addons/' + ADDON)
        helper = fixture / 'script.infinity.watchedbridge'
        shutil.copytree(HERE / 'addon', helper, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        probe.adb('push', helper, probe.PROFILE + '/../addons/' + helper.name)
        backing = '/data/media/0/Android/data/' + probe.PACKAGE
        probe.shell('chown', '-R', uid + ':' + uid, backing, probe.PRIVATE + '/shared_prefs')
        probe.shell('restorecon', '-RF', backing, probe.PRIVATE + '/shared_prefs')
        assert probe.shell('getenforce').strip() == 'Enforcing'
        probe.adb('logcat', '-c'); probe.shell('am', 'start', '-W', '-n', probe.PACKAGE + '/.Splash')
        report['first_party'] = probe.enable_first_party(args.out)
        report['owner'] = probe.wait_ready()
        assert probe.rpc('Addons.SetAddonEnabled', dict(addonid=ADDON, enabled=True)) == 'OK'
        assert probe.rpc('Addons.ExecuteAddon', dict(addonid=ADDON, wait=False)) == 'OK'
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            result = probe.read_json(probe.PROFILE + '/watched-native-runtime-result.json')
            if result: break
            time.sleep(.5)
        else: raise RuntimeError('Native row fixture did not return a result')
        report['native_row_result'] = result
        assert result.get('passed') is True, result.get('failure')
        assert len(result.get('tests', [])) == 14, 'All native index cases are required'
        assert result.get('helper_pipeline_verified') is True, 'Existing writer -> read-only publisher -> native row pipeline required'
        spec = importlib.util.spec_from_file_location('preserved_loaded_close', HERE.parent / 'android-checkpoint-shutdown/runtime-tests/observer_upgrade_android_probe.py')
        close_probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(close_probe)
        close_probe.probe = probe
        report['integrated_close'] = close_probe.close(report['owner'], args.out / 'integrated-close')
        assert report['integrated_close']['passed'], 'Integrated helper Close failed'
        probe.shell('am', 'start', '-W', '-n', probe.PACKAGE + '/.Splash')
        report['reopened_owner'] = probe.wait_ready(report['owner']['owner'])
        retained = probe.read_json(probe.PROFILE + '/addon_data/script.infinity.commandcenter/continue-watching.json')
        key = result['helper_pipeline_key']
        assert key in retained.get('watchlist', {}) and key in retained.get('collection', {})
        assert retained.get('infinity_watched_overrides', {}).get(key, {}).get('watched') is False
        assert key not in retained.get('items', {}) and key not in retained.get('watched', {})
        report['helper_state_retained_after_safe_close_reopen'] = True
        report['passed'] = True
    finally:
        (args.out / 'ANDROID-WATCHED-NATIVE-PROBE.json').write_text(json.dumps(report, indent=2) + '\n')
        (args.out / 'kodi.log').write_text(probe.shell('cat', probe.PROFILE + '/../temp/kodi.log', check=False))
        (args.out / 'logcat.txt').write_text(probe.adb('logcat', '-d'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('apk', 'installed-addons', 'out'): parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--expected-sha256', required=True)
    main(parser.parse_args())
