#!/usr/bin/env python3
"""Disposable TEST3->TEST4 retained-data and early/loaded Close comparison.

Uses the production launcher, Power Close, first-party add-ons and native
observers. Extra service fixtures are synthetic, not the user's Diggz build.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sqlite3
import time
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('production_probe', HERE/'essential_android_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
TEST3_SHA = '4ec1e3b2cabb595d228bc07bae2c6b3073c5af12822c8e40b1ec505b00865bf8'
IDS = ['service.observerprobe.writer'+str(i).zfill(2) for i in range(1, 38)]
DATA = probe.PROFILE+'/addon_data/'
SERVICE = '''import json, os, xbmc, xbmcaddon, xbmcvfs
addon = xbmcaddon.Addon()
identity = addon.getAddonInfo('id')
root = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
if not os.path.isdir(root): xbmcvfs.mkdirs(root)
expected = '<settings><setting id="retained-proof">'+identity+'</setting></settings>\\n'
state = os.path.join(root, 'settings.xml')
if not os.path.exists(state):
 with open(state, 'w') as saved: saved.write(expected)
else:
 with open(state) as saved: assert saved.read() == expected, 'Retained service state changed'
with open(os.path.join(root, 'ready.json'), 'w') as saved:
 json.dump(dict(addon=identity, pid=os.getpid(), observer_initialized=True), saved)
monitor = xbmc.Monitor()
while not monitor.abortRequested(): monitor.waitForAbort(0.25)
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait_owner(previous):
    deadline = time.monotonic()+180
    while time.monotonic() < deadline:
        owner = probe.read_json(probe.PRIVATE+'/files/infinity-kodi-process.json')
        native = probe.read_json(probe.CONTROL+'/engine.json')
        if (owner.get('phase') == 'RUNNING' and owner.get('owner') != previous and
                native.get('owner') == owner.get('owner') and native.get('pid') == owner.get('pid') and
                any(p['pid'] == owner.get('pid') for p in probe.processes())):
            return owner
        time.sleep(.1)
    raise RuntimeError('New native process owner did not appear')


def ready_services(pid):
    # One shell read avoids delaying early Close with 37 separate adb calls.
    paths = ' '.join(DATA+identity+'/ready.json' for identity in IDS)
    text = probe.adb('shell', 'for f in '+paths+'; do [ ! -f "$f" ] || { cat "$f"; echo; }; done', check=False)
    result = {}
    for line in text.splitlines():
        try: item = json.loads(line)
        except ValueError: continue
        if item.get('pid') == pid and item.get('addon') in IDS and item.get('observer_initialized') is True:
            result[item['addon']] = item
    return result


def wait_services(owner):
    deadline = time.monotonic()+180
    while time.monotonic() < deadline:
        ready = ready_services(owner['pid'])
        if len(ready) == len(IDS): return ready
        time.sleep(.5)
    raise RuntimeError('Not all 37 production observers reached their service entry points')


def close(owner, output):
    output.mkdir(parents=True, exist_ok=True)
    report = {'owner':owner, 'passed':False}
    def save(): (output/'close.json').write_text(json.dumps(report, indent=2)+'\n')
    try:
        report['ready_at_close'] = ready_services(owner['pid'])
        report['requested_monotonic'] = time.monotonic()
        report['request'] = probe.shell('am', 'start', '-n', probe.PACKAGE+'/.InfinityPowerControlActivity', '-a', probe.PACKAGE+'.action.CLOSE_KODI')
        deadline = time.monotonic()+35
        receipt = {}
        while time.monotonic() < deadline:
            receipt = probe.read_json(probe.PRIVATE+'/files/infinity-checkpoint-close.json')
            if receipt.get('owner') == owner['owner'] and receipt.get('phase') in ('COMPLETE', 'CHECKPOINT_FAILED'): break
            time.sleep(.25)
        report['receipt'] = receipt; save()
        assert receipt.get('phase') == 'COMPLETE', receipt.get('error', 'Missing terminal receipt')
        assert receipt.get('owner') == owner['owner'] and receipt.get('pid') == owner['pid']
        assert all(receipt.get(key) is True for key in ('checkpoint_saved', 'authorization_consumed', 'process_death_confirmed'))
        native = receipt['native_receipt']
        assert native['essential_writes_sealed'] and native['essential_writes_durable'] and not native['essential_write_blockers']
        assert len(native['essential_owners']) == 16 and len(native['owners']) == 17
        for _ in range(15):
            if not probe.processes(): break
            time.sleep(.2)
        report['remaining_processes'] = probe.processes()
        assert not report['remaining_processes'], 'Package UID remains alive'
        final = probe.read_json(probe.PRIVATE+'/files/infinity-checkpoint-close.json')
        assert final.get('session') == receipt['session'] and final.get('phase') == 'COMPLETE'
        assert final.get('coordinator_termination_authorized') is True
        assert all(re.fullmatch(r'[0-9a-f-]{36}', final.get(key, '')) for key in ('engine_java_save_seal', 'coordinator_java_save_seal'))
        assert not final.get('engine_java_pending') and not final.get('coordinator_java_pending')
        report['receipt'] = final
        report.update(passed=True, whole_package_death_verified=True, both_java_seals_verified=True)
    finally:
        save()
        probe.adb('pull', probe.PROFILE+'/../temp/kodi.log', output/'kodi.log', check=False)
    return report


def verify_saved_state(output):
    output.mkdir(parents=True, exist_ok=True)
    assert not probe.processes(), 'Verify backup only after real whole-UID death'
    favourites = probe.shell('cat', probe.PROFILE+'/favourites.xml')
    assert any(row.get('name') == probe.FAVOURITE for row in ET.fromstring(favourites))
    (output/'favourites.xml').write_text(favourites)
    preference = probe.shell('cat', probe.PRIVATE+'/shared_prefs/infinity_experience.xml')
    assert '<string name="default">infinity</string>' in preference
    (output/'infinity_experience.xml').write_text(preference)
    for identity in IDS:
        text = probe.shell('cat', DATA+identity+'/settings.xml')
        assert text == '<settings><setting id="retained-proof">'+identity+'</setting></settings>\n'
        (output/(identity+'.xml')).write_text(text)
    probe.adb('pull', probe.PROFILE+'/Database', output/'Database')
    databases = sorted((output/'Database').glob('*.db'))
    assert len(databases) >= 7
    for path in databases:
        with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as conn:
            assert conn.execute('PRAGMA integrity_check').fetchone() == ('ok',), path.name
    return {p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()}


def install_fixtures(output):
    assert not probe.processes(), 'Fixture installation requires verified stopped disposable app'
    fixture = output/'service-fixtures'; fixture.mkdir()
    hashes = {}
    for identity in IDS:
        root = fixture/identity; root.mkdir()
        (root/'addon.xml').write_text('<addon id="'+identity+'" name="Disposable observer service" version="1.0.0" provider-name="Infinity internal test"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.service" library="service.py" start="startup"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable observer shutdown regression</summary><description lang="en_GB">Synthetic test service, not a Diggz provider</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        (root/'service.py').write_text(SERVICE)
        for path in root.iterdir(): hashes[path.relative_to(fixture).as_posix()] = sha(path)
        probe.adb('push', root, probe.PROFILE+'/../addons/'+identity)
    backing = '/data/media/0/Android/data/'+probe.PACKAGE
    probe.shell('chown', '-R', probe.APP_UID+':'+probe.APP_UID, backing)
    probe.shell('restorecon', '-RF', backing)
    assert probe.shell('getenforce').strip() == 'Enforcing'
    return hashes


def enable_fixtures():
    inventory = probe.rpc('Addons.GetAddons', {'properties':['version', 'enabled']})
    installed = {row['addonid']:row for row in inventory.get('addons', [])}
    for identity in IDS:
        assert identity in installed, identity
        if not installed[identity]['enabled']:
            assert probe.rpc('Addons.SetAddonEnabled', {'addonid':identity, 'enabled':True}) == 'OK'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-apk', type=Path, required=True)
    parser.add_argument('--candidate-apk', type=Path, required=True)
    parser.add_argument('--installed-addons', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    report = dict(scope='Disposable real Android in-place upgrade with 37 synthetic services and approved first-party add-ons; not full Diggz/Fold clone', passed=False, physical_fold_accepted=False, full_fold_backup_used=False, actual_diggz_ecosystem_tested=False)
    def save(): (args.out/'OBSERVER-UPGRADE-PROBE.json').write_text(json.dumps(report, indent=2)+'\n')
    try:
        assert sha(args.baseline_apk) == TEST3_SHA
        # Existing probe refuses physical devices/existing installations and
        # requires its original full save/death/integrity/reopen checks.
        import sys
        sys.argv = [str(HERE/'essential_android_probe.py'), '--apk', str(args.baseline_apk), '--installed-addons', str(args.installed_addons), '--require-java-save-proof', '--out', str(args.out/'baseline-control')]
        probe.main()
        report['baseline_control'] = json.loads((args.out/'baseline-control/ANDROID-PROCESS-PROBE.json').read_text())
        assert report['baseline_control']['passed']
        previous = probe.wait_ready()
        report['baseline_setup_close'] = close(previous, args.out/'baseline-setup-close')
        report['fixture_sha256'] = install_fixtures(args.out)
        report['baseline_fixture_launch'] = probe.shell('am', 'start', '-n', probe.PACKAGE+'/.Splash')
        probe.enable_first_party(args.out)
        enable_fixtures()
        owner = probe.wait_ready(previous['owner'])
        report['baseline_ready_services'] = wait_services(owner); save()
        report['baseline_loaded_close'] = close(owner, args.out/'baseline-loaded-close')
        before = verify_saved_state(args.out/'verified-backup-before-upgrade')
        report['verified_backup_sha256'] = before; save()
        assert not probe.processes()
        report['upgrade_install'] = probe.adb('install', '-r', '--no-incremental', args.candidate_apk)
        assert 'Success' in report['upgrade_install']
        assert probe.shell('stat', '-c', '%u', probe.PRIVATE).strip() == probe.APP_UID
        after = verify_saved_state(args.out/'after-install-before-launch')
        assert before == after, 'APK upgrade changed saved fixture/database/preference bytes'
        report['upgrade_bytes_preserved'] = True; save()
        started = time.monotonic()
        report['candidate_early_launch'] = probe.shell('am', 'start', '-n', probe.PACKAGE+'/.Splash')
        early_owner = wait_owner(owner['owner'])
        report['candidate_early_close'] = close(early_owner, args.out/'candidate-early-close')
        report['candidate_launch_to_close_seconds'] = report['candidate_early_close']['requested_monotonic']-started
        report['early_ready_count'] = len(report['candidate_early_close']['ready_at_close'])
        assert report['early_ready_count'] < len(IDS), 'Early timing control missed startup; do not label loaded Close an early test'
        verify_saved_state(args.out/'after-early-close')
        report['candidate_loaded_launch'] = probe.shell('am', 'start', '-n', probe.PACKAGE+'/.Splash')
        probe.enable_first_party(args.out)
        loaded_owner = probe.wait_ready(early_owner['owner'])
        report['candidate_ready_services'] = wait_services(loaded_owner)
        report['candidate_loaded_close'] = close(loaded_owner, args.out/'candidate-loaded-close')
        verify_saved_state(args.out/'after-loaded-close')
        report['reopen'] = probe.shell('am', 'start', '-n', probe.PACKAGE+'/.Splash')
        probe.enable_first_party(args.out)
        reopened = probe.wait_ready(loaded_owner['owner'])
        report['reopen_ready_services'] = wait_services(reopened)
        report['saved_data_reopen_verified'] = True
        report['passed'] = True
    except Exception as error:
        report['failure'] = type(error).__name__+': '+str(error)
    finally:
        save()
        probe.adb('pull', probe.PROFILE+'/../temp/kodi.log', args.out/'last-kodi.log', check=False)
        (args.out/'logcat.txt').write_text(probe.adb('logcat', '-d', '-v', 'threadtime', check=False))
    print(json.dumps({k:report.get(k) for k in ('passed', 'upgrade_bytes_preserved', 'early_ready_count', 'candidate_launch_to_close_seconds', 'saved_data_reopen_verified', 'failure')}, indent=2))
    if not report['passed']: raise SystemExit(report['failure'])


if __name__ == '__main__':
    main()
