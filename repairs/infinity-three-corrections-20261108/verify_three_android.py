"""Only selected Search/Trakt/install-over/recovery on a fresh API37 emulator.

No uninstall, data clear, shutdown, playback or unrelated behavioral tests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import traceback
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'repairs/infinity-final-release-462-20261107'
PACKAGE = 'com.projectinfinity.kodi'
CC = 'script.infinity.commandcenter'
QA = 'script.infinity.finalreleaseqa'
TRAKT = 'script.module.tmdbhelper.sync.trakt'
HOME = '/sdcard/Android/data/' + PACKAGE + '/files/.kodi'
PROFILE = HOME + '/userdata'
QAROOT = PROFILE + '/addon_data/script.infinity.finalreleaseqa'
PROVIDERS = {'plugin.video.umbrella', 'plugin.video.pov'}


def transport():
    # Retained passing, feature-only transport. Its main journey is not invoked.
    source = subprocess.check_output(['git', 'show', '2759febb:repairs/infinity-final-release-462-20261107/verify_android_release.py'])
    namespace = {'__name__': 'retained_feature_only_transport', '__file__': str(OLD / 'verify_android_release.py')}
    exec(compile(source, str(OLD / 'verify_android_release.py'), 'exec'), namespace)
    namespace['PROVIDERS'] = PROVIDERS
    class SelectedDevice(namespace['Device']):
        def start_qa(self):
            # The retained transport also enables an unrelated playback clip.
            # This selected fixture contains only the script observer.
            addon = self.rpc('Addons.GetAddonDetails', dict(addonid=QA, properties=['enabled']))['addon']
            if not addon['enabled']:
                assert self.rpc('Addons.SetAddonEnabled', dict(addonid=QA, enabled=True)) == 'OK'
            assert self.rpc('Addons.GetAddonDetails', dict(addonid=QA))['addon']['type'] == 'xbmc.python.script'
            assert self.rpc('Addons.ExecuteAddon', dict(addonid=QA)) == 'OK'
            self.until(lambda: self.read_json(QAROOT + '/ready.json').get('pid') == self.pid, 'fresh QA observer', 90)
            self.dismiss_immersive_education()

    return SelectedDevice


def expected(apk):
    with ZipFile(apk) as z:
        base = 'assets/addons/'
        manifest = z.read(base + CC + '/INFINITY-MODULES.v1').decode()
        modules = {f[2]: f[1] for row in manifest.splitlines() if (f := row.split('\t'))[0] == 'file'}
        trakt = {n.removeprefix(base + TRAKT + '/'): hashlib.sha256(z.read(n)).hexdigest()
                 for n in z.namelist() if n.startswith(base + TRAKT + '/') and not n.endswith('/')}
    return modules, trakt


def run(baseline, candidate, recovery, fixture, out):
    assert not out.exists()
    out.mkdir(parents=True)
    scope = json.loads((HERE / 'ANDROID-REQUEST.json').read_text())
    assert scope['application_tests'] is True and scope['shutdown_tests'] is False
    phase = scope.get('execution_phase', 'complete')
    assert phase in ('complete', 'Trakt-recovery-and-provider-timing', 'finish-native-heading-and-Trakt')
    report = dict(status='RUNNING_SELECTED_THREE_CORRECTION_ANDROID_GATES', cases=[], Fold='NOT_RUN',
                  shutdown='NOT_SELECTED', playback='NOT_SELECTED', observer_workaround=False, accepted_pointer_updated=False)
    device = None
    report['selected_phase'] = phase
    if phase == 'Trakt-recovery-and-provider-timing':
        report['Search_acceptance'] = 'FAIL_COLD_UMBRELLA_TIMEOUT_RUN42465125757_ATTEMPT2_RETAINED'
    if phase == 'finish-native-heading-and-Trakt':
        prior = json.loads((HERE / 'evidence/ANDROID-SEVEN-PASS-EIGHTH-ZERO-PENDING.json').read_text())
        assert prior['run'] == 42470383172 and prior['candidate_sha256'] == hashlib.file_digest(candidate.open('rb'), 'sha256').hexdigest()
        assert len(prior['accepted_cycles']) == 7 and prior['observed_same_PID_completed_requests'] == 8
        report['source_bound_reused_Search'] = prior

    def save():
        (out / 'ANDROID-VERIFICATION.json').write_text(json.dumps(report, indent=2) + '\n')

    def passed(name, **detail):
        report['cases'].append(dict(case=name, status='PASS', **detail))
        save()

    def identity(apk, cc_version, trakt_version):
        value = device.command('identity')
        assert value['components'][CC]['version'] == cc_version
        assert value['components'][TRAKT]['version'] == trakt_version
        assert value['components']['skin.infinity.diggz']['version'] == '1.0.5.270'
        modules, trakt = expected(apk)
        assert len(modules) == 79 and value['module_files'] == modules
        assert len(trakt) == 145 and value['trakt_files'] == trakt
        return value

    def begin(request):
        device.alive()
        device.sequence += 1
        seq = device.sequence
        path = out / 'request.json'
        path.write_text(json.dumps(dict(pid=device.pid, sequence=seq, **request)))
        device.adb('push', str(path), QAROOT + '/request.pending')
        device.shell('mv', QAROOT + '/request.pending', QAROOT + '/request.json')
        return seq

    def reply(seq):
        value = device.read_json(QAROOT + '/reply.json')
        if value.get('sequence') != seq or value.get('pid') != device.pid:
            return None
        assert value['passed'], value
        return value['result']

    def visible(wid):
        key = 'Window.IsVisible(' + str(wid) + ')'
        return device.rpc('XBMC.GetInfoBooleans', dict(booleans=[key]))[key]

    def confirm_failure(label):
        device.until(lambda: visible(12002), 'actual Trakt failure Dialog.ok', 35)
        labels = device.rpc('XBMC.GetInfoLabels', dict(labels=['Control.GetLabel(1)', 'Control.GetLabel(9)']))
        device.screenshot(label)
        assert 'Trakt Authentication' in labels['Control.GetLabel(1)'], labels
        assert 'five minutes' in labels['Control.GetLabel(9)'], labels
        device.rpc('Input.Select')
        device.until(lambda: not visible(12002), 'known Trakt failure dialog dismissed', 10)
        return labels

    try:
        Device = transport()
        device = Device(out)
        assert not device.shell('pm', 'list', 'packages', PACKAGE).strip(), 'FRESH_DISPOSABLE_EMULATOR_ONLY'
        report['platform'] = {n: device.shell('getprop', n).strip() for n in ('ro.build.fingerprint', 'ro.build.version.sdk', 'ro.product.cpu.abilist', 'ro.dalvik.vm.native.bridge')}
        device.shell('wm', 'size', '1080x2520')
        device.shell('wm', 'density', '420')
        device.install(baseline, 'baseline464')
        for args in [('appops', 'set', PACKAGE, 'MANAGE_EXTERNAL_STORAGE', 'allow'),
                     ('pm', 'grant', PACKAGE, 'android.permission.RECORD_AUDIO'),
                     ('pm', 'grant', PACKAGE, 'android.permission.POST_NOTIFICATIONS')]:
            device.shell(*args)
        device.shell('mkdir', '-p', HOME)
        device.adb('push', str(fixture / 'home') + '/.', HOME)
        device.adb('root')
        device.adb('wait-for-device')
        uid = device.shell('stat', '-c', '%u', '/data/user/0/' + PACKAGE).strip()
        assert uid.isdigit() and int(uid) >= 10000
        backing = '/data/media/0/Android/data/' + PACKAGE
        device.shell('chown', '-R', uid + ':' + uid, backing)
        device.shell('restorecon', '-RF', backing)
        report['fixture_ownership'] = dict(disposable_qemu_only=True, application_UID=int(uid), app_protections_unchanged=True)
        # Establish a real existing external1.2.8 registration before updating.
        device.enter('baseline464')
        pins = json.loads((fixture / 'ANDROID-INPUTS.json').read_text())
        for aid in [r['addon'] for r in pins['provider_inputs']] + ['plugin.video.pov', TRAKT, 'service.infinity.compat']:
            details = device.rpc('Addons.GetAddonDetails', dict(addonid=aid, properties=['enabled', 'version']))['addon']
            if not details['enabled']:
                assert device.rpc('Addons.SetAddonEnabled', dict(addonid=aid, enabled=True)) == 'OK'
        device.start_qa()
        baseline_identity = device.command('identity')
        assert baseline_identity['components'][CC]['version'] == '0.3.5.62'
        assert baseline_identity['components'][TRAKT]['version'] == '1.2.8'
        assert '/.kodi/addons/' in baseline_identity['components'][TRAKT]['path']
        passed('existing464_CC62_external_Trakt128_registered', identity=baseline_identity)
        sentinel = device.shell('cat', PROFILE + '/release-data-sentinel.txt')
        oldpid = device.pid
        device.install(candidate, 'candidate466')
        device.enter('candidate466')
        assert device.pid != oldpid
        device.start_qa()
        value = identity(candidate, '0.3.5.64', '1.2.8.1')
        assert device.shell('cat', PROFILE + '/release-data-sentinel.txt') == sentinel
        passed('signed464_to466_complete79_authentication_and_Trakt_source_selection', identity=value)
        init = device.command('first-use', seconds=420)
        assert init['status'] == 'PASS_UNMODIFIED_TWO_PROVIDER_INITIALIZATION'
        if phase in ('complete', 'finish-native-heading-and-Trakt'):
            queries = [('movie', 'The Matrix'), ('movie', 'Inception'), ('movie', 'Toy Story'), ('movie', 'Finding Nemo'),
                       ('tv', 'Breaking Bad'), ('tv', 'The Office'), ('tv', 'SpongeBob'), ('tv', 'Re:zero')]
            headings_open = {0: 'plugin.video.umbrella', 1: 'plugin.video.pov', 6: 'plugin.video.umbrella', 7: 'plugin.video.pov'}
            start = 0
            if phase == 'finish-native-heading-and-Trakt':
                queries, start = [('tv', 'Stranger Things')], 8
                headings_open[8] = 'plugin.video.pov'
            for cycle, (media, query) in enumerate(queries, start=start):
                device.command('home')
                device.command('search', media=media)
                device.submit_search_all(query, cycle)

                def results():
                    current = device.command('snapshot', seconds=55)
                    if current['window'] != 10025 or 'action=search-all' not in current['labels']['Container.FolderPath']:
                        return None
                    headings = [r for r in current.get('rows', []) if r.get('provider') in PROVIDERS and re.search(r' — \d+ results$', r.get('label', ''))]
                    good = [r for r in current.get('rows', []) if r.get('provider') in PROVIDERS and not re.search(r' — \d+ results$', r.get('label', '')) and r.get('file', '').startswith('plugin://' + r['provider'] + '/')]
                    if {r['provider'] for r in headings} == PROVIDERS and {r['provider'] for r in good} == PROVIDERS:
                        return current, headings, good
                    return None

                current, headings, good = device.until(results, 'real nonempty Umbrella and POV results cycle' + str(cycle + 1), 160)
                assert not any('state changed' in r.get('label', '').lower() for r in current['rows'])
                device.command('focus-result', index=good[0]['index'], file=good[0]['file'])
                device.shell('input', 'swipe', '820', '1650', '820', '750', '500')
                device.shell('input', 'swipe', '820', '750', '820', '1650', '500')
                opened = None
                if cycle in headings_open:
                    provider = headings_open[cycle]
                    heading = next(r for r in headings if r['provider'] == provider)
                    # Original live Container(50).ListItem read is deliberately used.
                    native = device.command('select-row', index=heading['index'], file=heading['file'], seconds=160)
                    opened = provider
                    if media == 'tv':
                        folders = [r for r in native.get('rows', []) if r.get('file', '').startswith('plugin://' + provider + '/') and 'season' in r['file'].lower()]
                        assert folders, 'ACTUAL_TV_RESULT_FOLDER_REQUIRED'
                        device.command('select-row', index=folders[0]['index'], file=folders[0]['file'], seconds=160)
                device.alive()
                passed('real_Search_All_cycle_' + str(cycle + 1), media=media, query=query, providers=sorted(PROVIDERS), results=len(good), heading_opened=opened, PID=device.pid, live_ListItem_read=True)
        device.command('home')
        try:
            for case in ('silent-on', 'silent-off', 'manual', 'success', 'other-skin'):
                if case == 'other-skin':
                    assert device.rpc('Settings.SetSettingValue', dict(setting='lookandfeel.skin', value='skin.estuary')) is True
                    device.until(lambda: device.rpc('XBMC.GetInfoLabels', dict(labels=['System.CurrentWindow'])), 'Estuary loaded', 20)
                    time.sleep(3)
                seq = begin(dict(action='trakt-case', case=case))
                if case == 'manual':
                    device.until(lambda: visible(10101), 'actual manual device-code progress dialog', 25)
                    device.screenshot('manual-Trakt-device-code')
                    time.sleep(2)
                    device.rpc('Input.Back')
                if case not in ('silent-on', 'success'):
                    labels = confirm_failure('Trakt-' + case)
                outcome = device.until(lambda: reply(seq), 'selected actual SDK Trakt case ' + case, 40)
                assert outcome['status'] == ('PASS_REAL_SDK_SUCCESSFUL_REFRESH' if case == 'success' else 'PASS_REAL_SDK_SCOPED_TRAKT_CASE')
                assert outcome['HTTP_boundary_calls'] == (0 if case == 'manual' else 1), 'ACTUAL_SDK_CALL_MUST_BE_OBSERVED'
                if case != 'success':
                    assert 299 <= outcome['timestamp_delta'] <= 335 and outcome['deadline'] > 0, 'ACTUAL_300_SECOND_COOLDOWN_REQUIRED'
                if case == 'manual':
                    assert outcome['device_code_polls'] > 0, 'ACTUAL_MANUAL_DEVICE_CODE_POLL_REQUIRED'
                if case in ('silent-on', 'success'):
                    assert not visible(12002)
                passed('real_SDK_Trakt_' + case, details=outcome)
        except Exception as error:
            report.setdefault('feature_failures', []).append(dict(feature='Trakt', error=repr(error), traceback=traceback.format_exc()))
            save()
        try:
            assert device.rpc('Settings.SetSettingValue', dict(setting='lookandfeel.skin', value='skin.infinity.diggz')) is True
            time.sleep(3)
            device.alive()
            device.command('home')
            if phase == 'Trakt-recovery-and-provider-timing':
                for media, query in (('movie', 'The Matrix'), ('tv', 'Breaking Bad')):
                    timing = device.command('provider-timing', provider='plugin.video.umbrella', media=media, query=query, seconds=180)
                    passed('diagnostic_normal_Umbrella_' + media + '_route_timing', details=timing, production_Search_acceptance=False)
            if phase == 'finish-native-heading-and-Trakt':
                control = device.command('provider-timing', provider='plugin.video.umbrella', media='tv', query='Re:zero', allow_empty=True, seconds=180)
                assert control['results'] == 0, 'RETAINED_INFINITY_ZERO_MUST_MATCH_ORDINARY_NATIVE_PROVIDER'
                passed('retained_eighth_zero_matches_ordinary_native_Umbrella', details=control, original_run=42470383172, original_PID=5361)
        except Exception as error:
            # Retain a failed feature and still exercise the selected forward
            # recovery. Never convert a failed SDK/diagnostic case into PASS.
            report.setdefault('feature_failures', []).append(dict(feature='native-route-diagnostic', error=repr(error), traceback=traceback.format_exc()))
            save()
        (out / 'CANDIDATE-LOGCAT.txt').write_text(device.adb('logcat', '-d', '-v', 'threadtime', timeout=60))
        oldpid = device.pid
        device.install(recovery, 'recovery467')
        device.enter('recovery467')
        assert device.pid != oldpid
        device.start_qa()
        restored = identity(recovery, '0.3.5.65', '1.2.8.2')
        assert device.shell('cat', PROFILE + '/release-data-sentinel.txt') == sentinel
        passed('signed466_to467_forward_recovery79_files_and_data', identity=restored, previous_functional_sources_restored=True)
        if report.get('feature_failures'):
            raise RuntimeError('Selected Trakt/provider diagnostic failed; forward recovery results retained')
        status = ('PASS_SELECTED_ANDROID_THREE_CORRECTION_GATES' if phase == 'complete' else
                  'PASS_REMAINING_ANDROID_GATES_WITH_SOURCE_BOUND_REUSED_SEARCH' if phase == 'finish-native-heading-and-Trakt' else
                  'PASS_ONLY_SELECTED_TRAKT_RECOVERY_AND_NATIVE_ROUTE_DIAGNOSTICS_SEARCH_REMAINS_BLOCKED')
        report.update(status=status, physical_Fold='PENDING_ONE_OWNER_TEST', public_release='ENGINEERING_CANDIDATE_ONLY')
    except BaseException as error:
        report.update(status='FAIL_SELECTED_ANDROID_THREE_CORRECTION_GATE', error=type(error).__name__ + ': ' + str(error), traceback=traceback.format_exc())
        raise
    finally:
        if device:
            for name, arguments in [('LOGCAT.txt', ['logcat', '-d', '-v', 'threadtime']), ('KODI-LOG.txt', ['shell', 'cat', HOME + '/temp/kodi.log'])]:
                try:
                    (out / name).write_text(device.adb(*arguments, timeout=60, check=False))
                except Exception as error:
                    report[name + '_read_error'] = str(error)
        save()
        print(report['status'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for n in ('baseline', 'candidate', 'recovery', 'fixture', 'out'):
        p.add_argument('--' + n, type=Path, required=True)
    run(**vars(p.parse_args()))
