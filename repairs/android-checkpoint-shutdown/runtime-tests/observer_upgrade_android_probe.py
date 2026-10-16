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
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('production_probe', HERE/'essential_android_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
TEST3_SHA = '4ec1e3b2cabb595d228bc07bae2c6b3073c5af12822c8e40b1ec505b00865bf8'
IDS = ['service.observerprobe.writer'+str(i).zfill(2) for i in range(1, 38)]
DATA = probe.PROFILE+'/addon_data/'
DIRECTORY_FIXTURE = 'script.infinity.directoryprobe.test'
DIRECTORY_SETTINGS = '<settings><setting id="retained-proof">native-mkdirs</setting></settings>\n'
DIRECTORY_RESULT = DATA+DIRECTORY_FIXTURE+'/observation.json'
# Kodi may compile add-ons with optimization enabled. Every fixture operation
# and retained-data check must execute independently of Python assert removal.
SERVICE = r'''import json, os, xbmc, xbmcaddon, xbmcvfs
addon = xbmcaddon.Addon()
identity = addon.getAddonInfo('id')
root = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
if not os.path.isdir(root):
 created = xbmcvfs.mkdirs(root)
 if created is not True or not os.path.isdir(root):
  raise RuntimeError('Service fixture profile directory was not created')
expected = '<settings><setting id="retained-proof">'+identity+'</setting></settings>\n'
state = os.path.join(root, 'settings.xml')
if not os.path.exists(state):
 with open(state, 'w') as saved: saved.write(expected)
else:
 with open(state) as saved: retained = saved.read()
 if retained != expected: raise RuntimeError('Retained service state changed')
with open(os.path.join(root, 'ready.json'), 'w') as saved:
 json.dump(dict(addon=identity, pid=os.getpid(), observer_initialized=True, retained_settings_verified=True), saved)
monitor = xbmc.Monitor()
while not monitor.abortRequested(): monitor.waitForAbort(0.25)
'''
DIRECTORY_SCRIPT = r'''import json, os, sys, traceback, xbmc, xbmcaddon, xbmcvfs
stage = 'addon.identity'
try:
 addon = xbmcaddon.Addon()
 root = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
 stage = 'directory.missing'
 if os.path.exists(root): raise RuntimeError('Directory creation control must start missing')
 stage = 'directory.mkdirs'
 created = xbmcvfs.mkdirs(root)
 if created is not True: raise RuntimeError('xbmcvfs.mkdirs did not confirm creation')
 if not os.path.isdir(root): raise RuntimeError('Created profile is not a directory')
 state = os.path.join(root, 'settings.xml')
 stage = 'settings.open.w'
 with open(state, 'w') as saved:
  stage = 'settings.write'
  saved.write('<settings><setting id="retained-proof">native-mkdirs</setting></settings>\n')
  info = os.fstat(saved.fileno())
  with open('/proc/self/fdinfo/'+str(saved.fileno())) as fdinfo: descriptor_info = fdinfo.read()
  flags = int(next(line.split(':', 1)[1].strip() for line in descriptor_info.splitlines() if line.startswith('flags:')), 8)
  if flags & os.O_ACCMODE != os.O_WRONLY: raise RuntimeError('Settings descriptor is not writable as requested')
  descriptor = dict(target=os.readlink('/proc/self/fd/'+str(saved.fileno())), device=info.st_dev, inode=info.st_ino, mode=info.st_mode, status_flags=flags, access_mode=flags & os.O_ACCMODE, requested_mode='w', requested_flags=os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
 stage = 'observation.write'
 with open(os.path.join(root, 'observation.json'), 'w') as saved:
  json.dump(dict(addon=addon.getAddonInfo('id'), pid=os.getpid(), destination=root, mkdirs_succeeded=True, essential_settings_written=True, settings_descriptor=descriptor, python_optimization=sys.flags.optimize), saved)
except Exception:
 xbmc.log('Infinity directory control stage='+stage+'\n'+traceback.format_exc(), xbmc.LOGERROR)
 raise
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
        if item.get('pid') == pid and item.get('addon') in IDS and item.get('observer_initialized') is True and item.get('retained_settings_verified') is True:
            result[item['addon']] = item
    return result


def wait_services(owner):
    deadline = time.monotonic()+180
    while time.monotonic() < deadline:
        ready = ready_services(owner['pid'])
        if len(ready) == len(IDS): return ready
        time.sleep(.5)
    raise RuntimeError('Not all 37 production observers reached their service entry points')


def capture_failed_close(owner, output):
    """Read-only evidence after a refused Close on a verified disposable AVD.

    Never retries Close, clears application data or converts the refusal into
    acceptance. debuggerd requests a backtrace; it does not terminate the app.
    """
    evidence = dict(scope='after failed Close; diagnostics only, not an extended shutdown deadline',
                    captured=False, processes=probe.processes())
    if probe.shell('getprop', 'ro.kernel.qemu', check=False).strip() != '1':
        evidence['skipped'] = 'Native stack capture requires the disposable emulator'
        return evidence
    current = probe.read_json(probe.PRIVATE+'/files/infinity-kodi-process.json')
    pid = int(owner['pid'])
    if (current.get('owner') != owner['owner'] or current.get('pid') != pid or
            not any(row['pid'] == pid and str(row['uid']) == probe.APP_UID for row in evidence['processes'])):
        evidence['skipped'] = 'Failed engine identity is no longer live'
        return evidence
    evidence['ready_before_stack'] = ready_services(pid)
    (output/'failed-engine-maps.txt').write_text(probe.shell('cat', '/proc/'+str(pid)+'/maps', check=False))
    command = 'for t in /proc/'+str(pid)+'/task/*; do echo "$t"; cat "$t/comm" "$t/wchan" "$t/stat" 2>/dev/null; echo; done'
    (output/'failed-engine-threads.txt').write_text(probe.adb('shell', command, check=False))
    try:
        result = subprocess.run(['adb', 'shell', 'debuggerd', '-b', str(pid)],
                                capture_output=True, text=True, timeout=15)
        (output/'failed-engine-backtrace.txt').write_text(result.stdout+'\nSTDERR:\n'+result.stderr)
        evidence['debuggerd_returncode'] = result.returncode
    except subprocess.TimeoutExpired as error:
        (output/'failed-engine-backtrace.txt').write_text(str(error))
        evidence['debuggerd_timed_out'] = True
    evidence['ready_after_stack'] = ready_services(pid)
    evidence['captured'] = True
    return evidence


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
        if not report['passed']:
            try:
                report['failure_evidence'] = capture_failed_close(owner, output)
            except Exception as error:
                report['failure_evidence_error'] = type(error).__name__+': '+str(error)
        save()
        probe.adb('pull', probe.PROFILE+'/../temp/kodi.log', output/'kodi.log', check=False)
    return report


def saved_state_boundary(previous_close=None, *, evidence_path=None):
    """Close requires zero UID processes; install -r is a separate event.

    Android explicitly starts our preserved MY_PACKAGE_REPLACED receiver after
    an upgrade. Only that identified new Java process can coexist with the
    post-install byte comparison. This never grants a Close/death receipt.
    """
    live = probe.processes()
    proof = dict(processes=live, scope='after Close: whole UID absent', passed=False)
    try:
        return _saved_state_boundary(previous_close, live, proof)
    except Exception as error:
        proof['failure'] = type(error).__name__+': '+str(error)
        raise
    finally:
        if evidence_path is not None:
            evidence_path.write_text(json.dumps(proof, indent=2)+'\n')


def _saved_state_boundary(previous_close, live, proof):
    if previous_close is None:
        assert not live, 'Verify backup only after real whole-UID death'
    else:
        assert previous_close.get('passed') is True
        assert previous_close.get('whole_package_death_verified') is True
        assert previous_close.get('both_java_seals_verified') is True
        baseline = previous_close['receipt']
        final = probe.read_json(probe.PRIVATE+'/files/infinity-checkpoint-close.json')
        assert final.get('phase') == baseline.get('phase') == 'COMPLETE'
        assert final.get('session') == baseline.get('session')
        assert final.get('owner') == baseline.get('owner') and final.get('pid') == baseline.get('pid')
        assert final.get('checkpoint_saved') and final.get('authorization_consumed') and final.get('process_death_confirmed')
        proof.update(scope='after explicit APK upgrade, before engine launch; not a new shutdown/death proof',
                     previous_close_session=baseline['session'], receiver_starts=[], native_maps_absent=[], naturally_finished_receivers=[], process_samples=[], process_details=[])
        logs = probe.adb('logcat', '-d', '-v', 'threadtime', check=False)
        # install -r returns while Android is starting its receiver. Re-observe
        # an ambiguous ps name only after proving that exact PID's broadcast
        # origin and excluding native engines. This is outside the Close clock.
        deadline = time.monotonic()+3
        while True:
            proof['process_samples'].append(live)
            ambiguous = []
            for process in live:
                pid = process['pid']
                assert pid != baseline['pid'], 'Closed engine PID is still alive'
                if process['name'] != probe.PACKAGE:
                    proof['process_details'].append(dict(process=process,
                        cmdline=probe.shell('cat', '/proc/'+str(pid)+'/cmdline', check=False),
                        status=probe.shell('cat', '/proc/'+str(pid)+'/status', check=False)))
                assert process['name'] != probe.PACKAGE+':kodi', 'Unexpected package process before candidate launch: '+json.dumps(process)
                needle = 'Start proc '+str(pid)+':'+probe.PACKAGE+'/'
                component = 'for broadcast {'+probe.PACKAGE+'/'+probe.PACKAGE+'.InfinityCobraBootReceiver}'
                matches = [line for line in logs.splitlines() if needle in line and component in line]
                assert matches, 'New Java process has no observed package-update receiver origin: '+json.dumps(process)
                maps = probe.shell('cat', '/proc/'+str(pid)+'/maps', check=False)
                if not maps.strip() and not any(row['pid'] == pid for row in probe.processes()):
                    proof['naturally_finished_receivers'].append(pid)
                    continue
                assert maps.strip(), 'Cannot establish new receiver process image identity: '+json.dumps(process)
                assert 'libkodi.so' not in maps and 'libpython3.' not in maps, 'Native engine loaded before candidate launch: '+json.dumps(process)
                for match in matches:
                    if match not in proof['receiver_starts']: proof['receiver_starts'].append(match)
                if pid not in proof['native_maps_absent']: proof['native_maps_absent'].append(pid)
                if process['name'] != probe.PACKAGE: ambiguous.append(process)
            if not ambiguous:
                break
            assert time.monotonic() < deadline, 'Unexpected package process before candidate launch: '+json.dumps(ambiguous)
            time.sleep(.1)
            live = probe.processes()
    proof['passed'] = True
    return proof


def verify_saved_state(output, require_directory=False, previous_close=None):
    output.mkdir(parents=True, exist_ok=True)
    saved_state_boundary(previous_close, evidence_path=output.parent/(output.name+'-boundary-before.json'))
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
    if require_directory:
        assert probe.shell('cat', DATA+DIRECTORY_FIXTURE+'/settings.xml') == DIRECTORY_SETTINGS
        (output/'directory-settings.xml').write_text(DIRECTORY_SETTINGS)
    hashes = {p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()}
    # SQLite may update a WAL shared-memory sidecar even for a read-only
    # connection. Inspect a second copy so the verified backup stays exact.
    with tempfile.TemporaryDirectory(prefix='infinity-upgrade-integrity-') as tmp:
        inspection = Path(tmp)/'Database'
        shutil.copytree(output/'Database', inspection)
        for original in databases:
            path = inspection/original.name
            with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as conn:
                assert conn.execute('PRAGMA integrity_check').fetchone() == ('ok',), path.name
    assert hashes == {p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()}, 'Backup inspection modified original bytes'
    saved_state_boundary(previous_close, evidence_path=output.parent/(output.name+'-boundary-after.json'))
    return hashes


def install_fixtures(output):
    assert not probe.processes(), 'Fixture installation requires verified stopped disposable app'
    fixture = output/'service-fixtures'; fixture.mkdir()
    state = output/'seeded-service-state'; state.mkdir()
    hashes = {}
    for identity in IDS:
        root = fixture/identity; root.mkdir()
        (root/'addon.xml').write_text('<addon id="'+identity+'" name="Disposable observer service" version="1.0.0" provider-name="Infinity internal test"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.service" library="service.py" start="startup"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable observer shutdown regression</summary><description lang="en_GB">Synthetic test service, not a Diggz provider</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        (root/'service.py').write_text(SERVICE)
        for path in root.iterdir(): hashes[path.relative_to(fixture).as_posix()] = sha(path)
        probe.adb('push', root, probe.PROFILE+'/../addons/'+identity)
        # This comparison models an installation with existing user data.
        # Seed each essential setting while the disposable baseline is dead;
        # retain the independent candidate mkdirs regression below.
        saved = state/identity; saved.mkdir()
        (saved/'settings.xml').write_text('<settings><setting id="retained-proof">'+identity+'</setting></settings>\n')
        probe.adb('push', saved, DATA+identity)
    directory = fixture/DIRECTORY_FIXTURE; directory.mkdir()
    (directory/'addon.xml').write_text('<addon id="'+DIRECTORY_FIXTURE+'" name="Missing directory durability control" version="1.0.0" provider-name="Infinity internal test"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable actual mkdirs and essential settings regression</summary><description lang="en_GB">Not a Diggz provider</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    (directory/'default.py').write_text(DIRECTORY_SCRIPT)
    for path in directory.iterdir(): hashes[path.relative_to(fixture).as_posix()] = sha(path)
    probe.adb('push', directory, probe.PROFILE+'/../addons/'+DIRECTORY_FIXTURE)
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


def create_missing_directory(owner):
    details = probe.rpc('Addons.GetAddonDetails', {'addonid':DIRECTORY_FIXTURE, 'properties':['enabled']})['addon']
    if not details['enabled']:
        assert probe.rpc('Addons.SetAddonEnabled', {'addonid':DIRECTORY_FIXTURE, 'enabled':True}) == 'OK'
    assert probe.rpc('Addons.ExecuteAddon', {'addonid':DIRECTORY_FIXTURE, 'wait':True}) == 'OK'
    deadline = time.monotonic()+30
    while time.monotonic() < deadline:
        observation = probe.read_json(DIRECTORY_RESULT)
        if observation.get('pid') == owner['pid'] and observation.get('addon') == DIRECTORY_FIXTURE:
            assert observation.get('mkdirs_succeeded') is True and observation.get('essential_settings_written') is True
            descriptor = observation['settings_descriptor']
            assert descriptor['requested_mode'] == 'w' and descriptor['access_mode'] == 1
            assert isinstance(descriptor['status_flags'], int) and descriptor['status_flags'] & 3 == 1
            assert descriptor['inode'] > 0 and descriptor['device'] >= 0 and descriptor['target']
            assert probe.shell('cat', DATA+DIRECTORY_FIXTURE+'/settings.xml') == DIRECTORY_SETTINGS
            return observation
        time.sleep(.25)
    raise RuntimeError('Production missing-directory/essential-settings control did not complete')



def run_candidate_scenario(scenario, previous_owner, output, report, save):
    """Exercise one independently seeded upgrade, or the retained combined mode.

    Callers supply a fresh disposable AVD for each acceptance scenario. A failed
    early Close is never converted into cleanup or a loaded success.
    """
    assert scenario in ('early', 'loaded', 'combined')
    if scenario in ('early', 'combined'):
        started = time.monotonic()
        report['candidate_early_launch'] = probe.shell('am', 'start', '-n', probe.PACKAGE+'/.Splash')
        early_owner = wait_owner(previous_owner['owner'])
        report['candidate_early_close'] = close(early_owner, output/'candidate-early-close')
        report['candidate_launch_to_close_seconds'] = report['candidate_early_close']['requested_monotonic']-started
        report['early_ready_count'] = len(report['candidate_early_close']['ready_at_close'])
        assert report['early_ready_count'] < len(IDS), 'Early timing control missed startup; do not label loaded Close an early test'
        verify_saved_state(output/'after-early-close')
        previous_owner = early_owner
        save()
    if scenario in ('loaded', 'combined'):
        report['candidate_loaded_launch'] = probe.shell('am', 'start', '-n', probe.PACKAGE+'/.Splash')
        probe.enable_first_party(output)
        loaded_owner = probe.wait_ready(previous_owner['owner'])
        report['candidate_ready_services'] = wait_services(loaded_owner)
        report['candidate_directory_creation'] = create_missing_directory(loaded_owner)
        save()
        report['candidate_loaded_close'] = close(loaded_owner, output/'candidate-loaded-close')
        verify_saved_state(output/'after-loaded-close', require_directory=True)
        previous_owner = loaded_owner
        save()
    report['reopen'] = probe.shell('am', 'start', '-n', probe.PACKAGE+'/.Splash')
    probe.enable_first_party(output)
    reopened = probe.wait_ready(previous_owner['owner'])
    report['reopen_ready_services'] = wait_services(reopened)
    if scenario in ('loaded', 'combined'):
        assert probe.shell('cat', DATA+DIRECTORY_FIXTURE+'/settings.xml') == DIRECTORY_SETTINGS
    for identity in IDS:
        assert probe.shell('cat', DATA+identity+'/settings.xml') == '<settings><setting id="retained-proof">'+identity+'</setting></settings>\n'
    report['saved_data_reopen_verified'] = True
    save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-apk', type=Path, required=True)
    parser.add_argument('--candidate-apk', type=Path, required=True)
    parser.add_argument('--installed-addons', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--scenario', choices=('early', 'loaded', 'combined'), default='combined',
                        help='Use separate disposable AVDs for early and loaded acceptance; combined retains the original probe')
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    report = dict(scope='Disposable real Android in-place upgrade with 37 synthetic services and approved first-party add-ons; not full Diggz/Fold clone', scenario=args.scenario, passed=False, physical_fold_accepted=False, full_fold_backup_used=False, actual_diggz_ecosystem_tested=False)
    def save(): (args.out/'OBSERVER-UPGRADE-PROBE.json').write_text(json.dumps(report, indent=2)+'\n')
    try:
        report['baseline_apk_sha256'] = sha(args.baseline_apk)
        report['candidate_apk_sha256'] = sha(args.candidate_apk)
        assert report['baseline_apk_sha256'] == TEST3_SHA
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
        report['upgrade_receiver_before_comparison'] = saved_state_boundary(report['baseline_loaded_close'], evidence_path=args.out/'update-receiver-before-comparison.json'); save()
        after = verify_saved_state(args.out/'after-install-before-launch', previous_close=report['baseline_loaded_close'])
        assert before == after, 'APK upgrade changed saved fixture/database/preference bytes'
        report['upgrade_receiver_after_comparison'] = saved_state_boundary(report['baseline_loaded_close'], evidence_path=args.out/'update-receiver-after-comparison.json')
        report['upgrade_bytes_preserved'] = True; save()
        run_candidate_scenario(args.scenario, owner, args.out, report, save)
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
