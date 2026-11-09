"""Selected original-signed69 -> experimental74 -> forward-recovery75 install.

New test tooling only. No signing, production mutation, uninstall/data clear,
retry, module-fixture activation or global baseline-guard overrides.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import traceback
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

import qualify_android_baseline as base
import verify_tracking_android as core

HERE = Path(__file__).resolve().parent
REQUEST = HERE / 'POST-SIGN-INSTALL-REQUEST.json'  # Root supplies the disabled/officially pinned request.
OPERATION = 'verify-experimental-tracking-signed-pair-install'
BRANCH = 'work/infinity-tracking-integration-20261108'
VERSIONS = (2103469, 2103474, 2103475)
DECLARED = ('guisettings.xml', 'sources.xml', 'addon_data/skin.infinity.diggz/settings.xml',
            'addon_data/script.infinity.commandcenter/continue-watching.json')


def require(value, label):
    if not value:
        raise RuntimeError(label)


def check_pair(rows):
    require([row['versionCode'] for row in rows] == list(VERSIONS), 'EXACT_69_74_75_INCREASING_ORDER')
    require([row['role'] for row in rows] == ['baseline', 'candidate', 'recovery'], 'EXACT_BASE_CANDIDATE_FORWARD_RECOVERY')
    require(rows[0]['sha256'] == base.APK_SHA, 'PROTECTED_ORIGINAL69')
    for row in rows:
        require(re.fullmatch(r'[0-9a-f]{64}', row['sha256']) and type(row['size']) is int and row['size'] > 0,
                'IMMUTABLE_APK_HASH_AND_SIZE')
        require(re.fullmatch(r'[A-Za-z0-9._-]+\.apk', row['filename']) and row['certificate_sha256'] == base.CERT,
                'PINNED_BASENAME_AND_ORIGINAL_CERT')
        require(len(row['module_sources']) == 80 and re.fullmatch(r'[0-9a-f]{64}', row['manifest_sha256']), 'EXACT_FULL80_EXPECTATION')


def checked_request():
    request = base.load(REQUEST)
    require(request['operation'] == OPERATION and request['application_tests'] is True and
            request['shutdown_tests'] is False and request['build_sign'] is False and request['publication'] is False,
            'EXPLICIT_POST_SIGN_TEST_SELECTION_ONLY')
    require(request['authorized_branch'] == BRANCH and request['maximum_intentional_starts_per_version'] == 1 and
            request['automatic_retries'] == 0 and request['transport_scaffold'] == 'HARNESS_BOOTSTRAP', 'FIXED_ONE_START_NO_RETRY_SCOPE')
    signing = request['official_signing']
    require(signing['workflow_id'] == 397702717 and signing['workflow_path'] == '.github/workflows/infinity-combined-release.yml' and
            signing['conclusion'] == 'success' and re.fullmatch(r'[0-9a-f]{40}', signing['source']) and
            type(signing['run_id']) is int and type(signing['artifact']['id']) is int and
            re.fullmatch(r'[0-9a-f]{64}', signing['artifact']['sha256']) and signing['artifact']['size'] > 0,
            'OFFICIAL_COMPLETED_ORIGINAL_SIGNING_PROVENANCE')
    needed = {'verify_tracking_install.py', 'verify_tracking_android.py', 'tracking_android_observer.py',
              'qualify_android_baseline.py', 'TRACKING-DEPENDENCY-PINS.json', 'POST-SIGN-INSTALL-PLAN.md',
              'POST-SIGN-INSTALL-SELECTION.json'}
    require(needed <= set(request['source_bindings']), 'REQUIRED_FROZEN_TOOL_BINDINGS')
    for relative, wanted in request['source_bindings'].items():
        path = HERE / relative
        require(path.resolve().is_relative_to(HERE.resolve()) and base.sha(path) == wanted, 'EXACT_SELECTED_SOURCE:' + relative)
    check_pair(request['apks'])
    return request


def verify_host_apk(path, expected, sdk, out):
    require(path.stat().st_size == expected['size'] and base.sha(path) == expected['sha256'], 'EXACT_OFFICIAL_SIGNED_APK_BYTES')
    signature = base.command([sdk / 'build-tools/35.0.0/apksigner', 'verify', '--verbose', '--print-certs', path], timeout=60)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [base.CERT], 'ONE_ORIGINAL_PERMANENT_CERTIFICATE')
    (out / 'SIGNATURE.txt').write_text(signature)
    bundle, parser = base.original_module_tools()
    with tempfile.TemporaryDirectory() as temporary, ZipFile(path) as archive:
        names = base.safe_zip(archive)
        meta = base.axml_metadata(archive.read('AndroidManifest.xml'), parser)
        require(meta['manifest']['package'] == base.PACKAGE and meta['manifest']['versionCode'] == expected['versionCode'] and
                meta['uses-sdk']['minSdkVersion'] == 21 and meta['uses-sdk']['targetSdkVersion'] == 35, 'EXACT_PACKAGE_VERSION_SDK')
        require(hashlib.sha256(archive.read('lib/arm64-v8a/libkodi.so')).hexdigest() == base.NATIVE_SHA, 'ORIGINAL_NATIVE466_UNCHANGED')
        modules = Path(temporary) / 'modules'; modules.mkdir()
        for name in names:
            if not name.endswith('/') and any(name.startswith('assets/addons/' + aid + '/') for aid in bundle.IDS):
                destination = modules / name.removeprefix('assets/addons/')
                destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(archive.read(name))
        payload, files = bundle.build(modules)
        manifest = modules / base.CC / bundle.MANIFEST
        require(len(files) == 80 and manifest.read_bytes() == payload, 'CANONICAL_COMPLETE80_ACTUAL_APK_MANIFEST')
        base.command(['openssl', 'dgst', '-sha256', '-verify', base.FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem',
            '-signature', str(manifest) + '.sig', manifest], timeout=30)
        actual = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
        cc = ET.fromstring((modules / base.CC / 'addon.xml').read_bytes()).get('version')
        require(actual == expected['module_sources'] and base.sha(manifest) == expected['manifest_sha256'] and cc == expected['CC'],
                'EXACT_EXPECTED_GENERATION_AND_AUTHENTICATED80_SOURCE_MAP')
    proof = dict(status='PASS_HOST_APK_ORIGINAL_CERT_FULL80_ONLY', sha256=expected['sha256'], metadata=meta,
                 module_sources=actual, manifest_sha256=expected['manifest_sha256'], CC=cc, native_sha256=base.NATIVE_SHA)
    base.save(out / 'HOST-APK.json', proof)
    return proof


def admit_inputs(inputs, sdk, out):
    request, staged = checked_request(), base.load(inputs / 'INSTALL-INPUTS.json')
    require(staged['status'] == 'OFFICIAL_SIGNED_APK_INPUTS_ADMITTED' and staged['request_sha256'] == base.sha(REQUEST) and
            staged['official_signing'] == request['official_signing'], 'ROOT_ADMITTED_OFFICIAL_INPUT_PROVENANCE')
    require(staged['apks'] == request['apks'], 'EXACT_REQUEST_APK_EXPECTATIONS')
    for row in request['apks']:
        target = out / str(row['versionCode']); target.mkdir()
        verify_host_apk(inputs / row['filename'], row, sdk, target)
    pins = base.load(HERE / 'TRACKING-DEPENDENCY-PINS.json')
    by_id = {row['addon']: row for row in pins['archives']}
    require(len(staged['dependencies']) == len(pins['installation_order']) and
            [row['addon'] for row in staged['dependencies']] == pins['installation_order'], 'EXACT_UNMODIFIED_DEPENDENCY_CLOSURE')
    providers = {}
    for row in staged['dependencies']:
        pin = by_id[row['addon']]
        require(re.fullmatch(r'[A-Za-z0-9._-]+\.zip', row['archive']) and row['sha256'] == pin['sha256'] and
                row['version'] == pin['version'] and base.sha(inputs / 'zips' / row['archive']) == pin['sha256'], 'EXACT_PUBLISHER_ZIP')
        with ZipFile(inputs / 'zips' / row['archive']) as archive:
            names = [name for name in base.safe_zip(archive) if not name.endswith('/')]
            require(all(name.startswith(row['addon'] + '/') for name in names), 'SINGLE_PUBLISHER_ADDON_ROOT')
            if row['addon'] == core.WNT:
                providers[core.WNT] = {name.removeprefix(core.WNT + '/'): hashlib.sha256(archive.read(name)).hexdigest() for name in names}
    zips = out / 'zips'; zips.mkdir()
    for row in staged['dependencies']:
        (zips / row['archive']).write_bytes((inputs / 'zips' / row['archive']).read_bytes())
    qa = {}
    for row in request['apks']:
        version = '1.1.' + str(row['versionCode'])
        name = core.QA + '-' + version + '.zip'
        expected = dict(cc_version=row['CC'], manifest_sha256=row['manifest_sha256'], module_sources=row['module_sources'], provider_sources=providers)
        addon = ('<addon id="' + core.QA + '" name="Tracking installation observer" version="' + version + '" provider-name="Infinity engineering">'
                 '<requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/></addon>')
        with ZipFile(zips / name, 'x', compression=ZIP_DEFLATED) as archive:
            archive.writestr(core.QA + '/addon.xml', addon)
            archive.writestr(core.QA + '/default.py', (HERE / 'tracking_android_observer.py').read_bytes())
            archive.writestr(core.QA + '/expected.json', json.dumps(expected, sort_keys=True))
        qa[row['versionCode']] = dict(addon=core.QA, version=version, archive=name, sha256=base.sha(zips / name))
    return request, staged, qa


def check_installed_observation(observed, expected, uid=None):
    require(observed['versionCode'] == expected['versionCode'] and observed['sha256'] == expected['sha256'], 'ACTUAL_INSTALLED_VERSION_AND_SHA')
    require(type(observed['uid']) is int and observed['uid'] >= 10000 and (uid is None or observed['uid'] == uid), 'SAME_REAL_APPLICATION_UID')
    return dict(status='PASS_ACTUAL_PACKAGEMANAGER_IDENTITY', **observed)


def installed_package(device, expected, uid=None):
    paths = device.shell('pm', 'path', base.PACKAGE).splitlines()
    require(len(paths) == 1 and re.fullmatch(r'package:/data/app/[^\r\n]+/base\.apk', paths[0]), 'ONE_ACTUAL_INSTALLED_BASE_APK')
    path = paths[0].removeprefix('package:')
    dump = device.shell('dumpsys', 'package', base.PACKAGE)
    versions = re.findall(r'^\s*versionCode=(\d+)\b', dump, re.M)
    require(len(versions) == 1, 'ONE_PACKAGEMANAGER_VERSION_CODE')
    digest = device.shell('sha256sum', path).split()
    require(len(digest) == 2 and digest[1] == path and re.fullmatch(r'[0-9a-f]{64}', digest[0]), 'ACTUAL_INSTALLED_DIGEST_QUERY')
    actual_uid = device.shell('stat', '-c', '%u', '/data/user/0/' + base.PACKAGE).strip()
    require(actual_uid.isdigit(), 'ACTUAL_APPLICATION_UID_QUERY')
    return check_installed_observation(dict(versionCode=int(versions[0]), sha256=digest[0], uid=int(actual_uid), path=path), expected, uid)


def reserve_start(attempts, version):
    require(version in VERSIONS and version not in attempts, 'ONE_INTENTIONAL_START_PER_DECLARED_VERSION_NO_RETRY')
    attempts.append(version)


def new_package_crash(before, after, epoch):
    previous = Counter(before.splitlines())
    package = re.compile(r'(?<![A-Za-z0-9_.])' + re.escape(base.PACKAGE) + r'(?=$|[^A-Za-z0-9_.])')
    new = []
    for line in after.splitlines():
        if previous[line]: previous[line] -= 1; continue
        match = re.match(r'^\s*(\d+\.\d+)\s+', line)
        if match and float(match[1]) >= epoch and package.search(line): new.append(line)
    return new


class InstallDevice(core.FeatureDevice):
    phase_epoch = None
    phase_crashes_before = ''
    operation_deadline = None
    phase_out = None

    def phase_crash_check(self):
        if self.phase_epoch is not None:
            current = self.shell('logcat', '-b', 'crash', '-v', 'epoch', '-d', timeout=5)
            require(len(current.encode()) <= 4 * 1024 * 1024, 'BOUNDED_PRESERVED_CRASH_BUFFER')
            (self.phase_out / 'crash-buffer-after.txt').write_text(current)
            lines = new_package_crash(self.phase_crashes_before, current, self.phase_epoch)
            if lines:
                base.save(self.phase_out / 'NEW-PHASE-NATIVE-CRASH.json', dict(epoch=self.phase_epoch, package_lines=lines))
                raise RuntimeError('NEW_PHASE_PACKAGE_CRASH_NO_RETRY')

    def alive(self):
        if self.operation_deadline is not None and time.monotonic() >= self.operation_deadline:
            raise TimeoutError('SELECTED_PHASE_OPERATION_BUDGET_EXHAUSTED')
        super().alive()  # Original actual PID + process-start guard remains.
        self.phase_crash_check()


def start_version_once(device, version, attempts, out):
    reserve_start(attempts, version)
    require(not device.pids(), 'NO_PREEXISTING_OR_AUTORESTARTED_NATIVE_PROCESS')
    device.pid, device.start_time = 0, None
    device.phase_out = out
    device.phase_crashes_before = device.shell('logcat', '-b', 'crash', '-v', 'epoch', '-d', timeout=5)
    (out / 'crash-buffer-before.txt').write_text(device.phase_crashes_before)
    device.phase_epoch = float(device.shell('date', '+%s').strip())
    started = subprocess.run([str(device.adb_bin), '-s', device.serial, 'shell', 'am', 'start', '-W', '-n', base.PACKAGE + '/.Splash'],
                             check=False, capture_output=True, text=True, timeout=30)
    base.save(out / 'am-start.json', dict(returncode=started.returncode, stdout=started.stdout, stderr=started.stderr, device_epoch=device.phase_epoch))
    require(started.returncode == 0, 'ORIGINAL_SPLASH_START_COMMAND_FAILED')
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        device.phase_crash_check()  # Before accepting any PID, reject constructor crash/OS restart.
        pids = device.pids()
        if device.pid: device.alive()
        elif pids:
            require(len(pids) == 1 and pids[0].isdigit(), 'ONE_GENUINE_NATIVE_PROCESS')
            device.pid = int(pids[0])
            device.start_time = device.shell('cat', '/proc/' + pids[0] + '/stat').rsplit(') ', 1)[1].split()[19]
        tree = device.nodes('start-' + str(version))
        if tree is not None: device.handle_ui(tree)
        if device.pid:
            try:
                ping = device.rpc('JSONRPC.Ping', timeout=3)
                home = device.rpc('GUI.GetProperties', dict(properties=['currentwindow', 'currentcontrol', 'skin']), timeout=3)
            except (ConnectionError, TimeoutError, OSError):
                time.sleep(.5); continue
            if ping == 'pong' and home.get('currentwindow', {}).get('id') == 10000 and home.get('skin', {}).get('id') == 'skin.infinity.diggz':
                raw = device.shell('dumpsys', 'activity', 'activities', timeout=3)
                require(len(raw.encode()) <= 2 * 1024 * 1024, 'BOUNDED_ACTUAL_FOREGROUND_QUERY')
                component = base.resumed_component(raw)
                if component and component.startswith(base.PACKAGE + '/'):
                    device.alive()
                    return dict(status='PASS_ONE_OBSERVED_HOME_START', versionCode=version, pid=device.pid, process_start=device.start_time,
                                foreground=component, home=home, phase_epoch=device.phase_epoch, retries=0)
        time.sleep(.5)
    raise TimeoutError('ONE_VERSION_NORMAL_SPLASH_STARTUP_DEADLINE')


def declared_inventory(device, fixture):
    result = {}
    root = device.shell('readlink', '-f', base.PROFILE).strip()
    require(root.startswith('/storage/') or root.startswith('/mnt/'), 'REAL_SHARED_USERDATA_ROOT')
    for relative in DECLARED:
        remote = base.PROFILE + '/' + relative
        # Fixed declared paths only; no user-controlled shell fragments.
        marker = device.shell('sh', '-c', "'if [ -e " + remote + " ]; then echo PRESENT; else echo ABSENT; fi'").strip()
        if marker == 'ABSENT': result[relative] = dict(exists=False, domain=fixture.get(relative, 'NO_USER_FIXTURE_OBSERVED')); continue
        require(marker == 'PRESENT', 'EXACT_DECLARED_FILE_EXISTENCE')
        actual = device.shell('readlink', '-f', remote).strip()
        require(actual.startswith(root + '/') and device.shell('stat', '-c', '%F', remote).strip() == 'regular file', 'DECLARED_REGULAR_USERDATA_FILE')
        length, digest = device.shell('stat', '-c', '%s', remote).strip(), device.shell('sha256sum', remote).split()
        require(length.isdigit() and len(digest) == 2 and digest[1] == remote and re.fullmatch(r'[0-9a-f]{64}', digest[0]), 'ACTUAL_DECLARED_FILE_BYTES_QUERY')
        result[relative] = dict(exists=True, size=int(length), sha256=digest[0], domain=fixture.get(relative, 'NO_USER_FIXTURE_OBSERVED'))
    return result


def compare_inventory(before, after):
    require(set(before) == set(after) == set(DECLARED), 'SAME_FINITE_DECLARED_USERDATA_SET')
    rows, observed_user = {}, 0
    for path, original in before.items():
        current = after[path]
        if not original['exists']:
            rows[path] = dict(status='NOT_OBSERVED' if not current['exists'] else 'CREATED_NOT_RETENTION', before=original, after=current)
            continue
        require(current['exists'] and (original['size'], original['sha256']) == (current['size'], current['sha256']), 'DECLARED_EXISTING_FILE_BYTES_NOT_RETAINED:' + path)
        rows[path] = dict(status='PASS_EXISTING_FILE_BYTES_ONLY', domain=original['domain'], sha256=original['sha256'])
        if original['domain'].startswith('LEGITIMATE_UI_'): observed_user += 1
    return dict(status='PASS_OBSERVED_USER_FIXTURE_BYTES_ONLY' if observed_user else 'NOT_OBSERVED_USER_FIXTURE', files=rows,
                observed_user_fixture_files=observed_user, absent_progress_claimed_preserved=False)


def outcome(error):
    if str(error) in ('NEW_PHASE_PACKAGE_CRASH_NO_RETRY', 'NATIVE_ENGINE_DIED_OR_RESTARTED', 'NATIVE_PID_REUSED'):
        return 'FAIL_NATIVE_STARTUP_OR_PROCESS'
    if str(error).startswith(('ACTUAL_INSTALLED_', 'SAME_REAL_APPLICATION_UID', 'DECLARED_EXISTING_FILE_BYTES_NOT_RETAINED',
                             'OBSERVED_PACKAGEMANAGER_REJECTED', 'RECOVERY_AUTHENTICATED_AVAILABLE_STATE_NOT_RETAINED')):
        return 'FAIL_OBSERVED_INSTALL_OR_DATA_MISMATCH'
    return 'BLOCKED_PREREQUISITE'


def failure_status(error, fallback='BLOCKED'):
    observed = outcome(error)
    return observed if observed.startswith('FAIL') else fallback


def result_statuses(value):
    if isinstance(value, dict):
        if isinstance(value.get('status'), str): yield value['status']
        for child in value.values(): yield from result_statuses(child)
    elif isinstance(value, list):
        for child in value: yield from result_statuses(child)


def final_liveness(device):
    # The expired work budget remains in its recorded case. This bounded
    # read-only terminal observation must still run original PID/crash checks.
    device.operation_deadline = None
    device.alive()
    return dict(status='PASS_CURRENT_PROCESS_AND_NEW_CRASH_OBSERVATION_ONLY')


def initialize_report():
    return dict(status='NOT_RUN', experimental=True, release_acceptance=False, Fold='NOT_RUN', shutdown='NOT_SELECTED',
        versions={str(v): {key: dict(status='NOT_RUN') for key in ('install', 'retention', 'startup', 'native_authentication', 'fixture', 'runtime')} for v in VERSIONS},
        intentional_starts=[], functional_recovery='NOT_RUN', retained_failure_run=42604600259)


def stopped_for_transition(device):
    device.phase_epoch = None
    device.operation_deadline = None
    device.shell('am', 'force-stop', base.PACKAGE)
    require(not device.pids(), 'PACKAGE_TRANSITION_PROCESS_STOPPED_NO_START_RETRY')
    device.pid, device.start_time = 0, None


def phase_authentication(device, expected, qa, staged, out):
    for row in staged['dependencies']:
        existing = core.addon_details(device, row['addon'])
        if not existing or existing.get('version') != row['version'] or existing.get('enabled') is not True:
            core.install_zip(device, row, staged, out, 'dependency-' + row['addon'])
    core.install_zip(device, qa, staged, out, 'phase-observer')
    observer_out = out / 'observer'; observer_out.mkdir()
    observer = core.Observer(device, observer_out)
    identity = observer.call('identity')
    require(identity['cc_version'] == expected['CC'] and identity['manifest_sha256'] == expected['manifest_sha256'] and
            identity['module_files'] == expected['module_sources'] and identity['module_count'] == 80, 'ACTUAL_NATIVE_AUTHENTICATED_EXPECTED_GENERATION80')
    device.alive()
    return observer, identity


def run(inputs, sdk, out):
    require(not out.exists(), 'FRESH_POST_SIGN_EVIDENCE_DIRECTORY'); out.mkdir(parents=True)
    report, device, reader, disposer = initialize_report(), None, None, None
    def persist(): base.save(out / 'INSTALL-VERIFICATION.json', report)
    persist()
    try:
        request, staged, qa = admit_inputs(inputs, sdk, out)
        require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
                os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'EXPLICIT_SELECTED_DISPOSABLE_FEATURE_WORKFLOW_ONLY')
        report['host_admission'] = dict(status='PASS_ORIGINAL_CERT_SOURCE_FULL80_APKS_ONLY', provenance=request['official_signing'])
        device = InstallDevice(out, sdk)
        disposer, report['host_disposal'] = base.retained_disposal(out)
        report['environment'] = base.environment(device, out)
        require(not device.shell('pm', 'list', 'packages', base.PACKAGE).strip(), 'FRESH_VM_PACKAGE_ABSENT')
        report['root_handshake'] = base.root_reconnect(device, out)
        reader = base.start_lifecycle_log(device, out)
        remote = '/sdcard/Download/infinity-install-zips/'
        staged = dict(staged, remote_zip_directory=remote)
        uid, previous_installed, fixture, semantic_before = None, None, {'guisettings.xml': 'HARNESS_BOOTSTRAP', 'sources.xml': 'HARNESS_BOOTSTRAP'}, None
        for expected in request['apks']:
            version, phase = expected['versionCode'], report['versions'][str(expected['versionCode'])]
            phase_out = out / str(version)
            observer = None
            try:
                before = None
                if version != VERSIONS[0] and previous_installed != VERSIONS[VERSIONS.index(version) - 1]:
                    phase['install'] = dict(status='BLOCKED_PREDECESSOR_INSTALL_IDENTITY')
                    persist(); continue
                if uid is not None:
                    installed_package(device, request['apks'][VERSIONS.index(version) - 1], uid)
                    stopped_for_transition(device)
                    before = declared_inventory(device, fixture)
                    base.save(phase_out / 'userdata-before-install.json', before)
                args = ['install', '--no-streaming'] + (['-r'] if version != VERSIONS[0] else [])
                installed = subprocess.run([str(device.adb_bin), '-s', device.serial, *args, str(inputs / expected['filename'])],
                    check=False, capture_output=True, text=True, timeout=300)
                phase['install'].update(returncode=installed.returncode, stdout=installed.stdout, stderr=installed.stderr)
                base.save(phase_out / 'PackageManager-install.json', phase['install'])
                require(installed.returncode == 0 and installed.stdout.strip().endswith('Success'), 'OBSERVED_PACKAGEMANAGER_REJECTED')
                phase['install'] = installed_package(device, expected, uid)
                uid = phase['install']['uid']
                previous_installed = version
                if before is not None:
                    after = declared_inventory(device, fixture)
                    base.save(phase_out / 'userdata-immediately-after-install-before-start.json', after)
                    phase['retention'] = compare_inventory(before, after)
                if version == VERSIONS[0]:
                    device.shell('mkdir', '-p', base.PROFILE, remote)
                    guisettings = out / 'HARNESS-BOOTSTRAP-guisettings.xml'
                    guisettings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting><setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>')
                    sources = out / 'HARNESS-BOOTSTRAP-sources.xml'
                    sources.write_text('<sources><files><source><name>Tracking engineering ZIPs</name><path pathversion="1">' + remote + '</path><allowsharing>false</allowsharing></source></files></sources>')
                    device.adb('push', guisettings, base.PROFILE + '/guisettings.xml'); device.adb('push', sources, base.PROFILE + '/sources.xml')
                    device.adb('push', str(out / 'zips') + '/.', remote, timeout=180)
                    device.shell('chown', '-R', str(uid) + ':' + str(uid), '/data/media/0/Android/data/' + base.PACKAGE)
                    device.shell('restorecon', '-RF', '/data/media/0/Android/data/' + base.PACKAGE)
                    device.adb('forward', 'tcp:19090', 'tcp:9090')
                    report['scaffold'] = dict(status='HARNESS_BOOTSTRAP_NOT_USER_FIXTURE', user_created_settings=False, progress_seeded=False)
                require(not device.pids(), 'UNEXPECTED_NATIVE_PROCESS_AFTER_INSTALL_NO_ADOPTION')
                try:
                    phase['startup'] = start_version_once(device, version, report['intentional_starts'], phase_out)
                except Exception as error:
                    phase['startup'] = dict(status=outcome(error), error=repr(error), traceback=traceback.format_exc())
                    base.capture_failure(device, phase_out); persist(); continue
                try:
                    device.operation_deadline = time.monotonic() + 180
                    observer, identity = phase_authentication(device, expected, qa[version], staged, phase_out)
                    phase['native_authentication'] = dict(status='PASS_ACTUAL_NATIVE_FULL80', identity=identity)
                    device.operation_deadline = None
                except Exception as error:
                    phase['native_authentication'] = dict(status=outcome(error), error=repr(error)); persist(); continue
                if version == VERSIONS[0]:
                    device.operation_deadline = time.monotonic() + 180
                    phase['fixture'] = dict(status='RUNNING', progress_seeded=False)
                    try:
                        saved = core.prepare_saved_title(device, observer, 'movie')
                        fixture['addon_data/script.infinity.commandcenter/continue-watching.json'] = 'LEGITIMATE_UI_WATCHLIST'
                        phase['fixture']['watchlist'] = dict(status='PASS_GENUINE_SAVE_ONLY', key=saved['key'], source=saved['source'])
                    except Exception as error:
                        phase['fixture']['watchlist'] = dict(status=failure_status(error, 'FAIL' if isinstance(error, core.FunctionalFailure) else 'BLOCKED'), error=repr(error))
                    try:
                        device.rpc('Input.Home')
                        core.until(device, lambda: observer.call('snapshot')['window'] == 10000, 'Home for real public fixture setting', 25)
                        observer.call('public-view-mode', mode='compact')
                        view = core.until(device, lambda: (value if core.mode_ready(value := observer.call('view-snapshot'), 'compact') else None), 'Real public view-mode fixture', 25)
                        fixture['addon_data/skin.infinity.diggz/settings.xml'] = 'OBSERVED_SKIN_SETTINGS_BYTES_UI_READBACK_ONLY'
                        phase['fixture']['setting'] = dict(status='PASS_PUBLIC_UI_READBACK_ONLY_PERSISTED_FILE_VALUE_UNVERIFIED', actual=view)
                    except Exception as error:
                        phase['fixture']['setting'] = dict(status=failure_status(error), error=repr(error))
                    phase['fixture']['status'] = ('FAIL' if any(status.startswith('FAIL') for status in result_statuses(phase['fixture'])) else 'AVAILABLE_CASES_RECORDED_NO_PROGRESS_SEEDING')
                    device.operation_deadline = None
                elif version == VERSIONS[1]:
                    scenario = dict(status='RUNNING', steps={name: dict(status='NOT_RUN') for name in core.initial_report()['scenarios']['movie']['steps']}, origin_trace=[], integration_started=False)
                    phase['runtime'] = scenario; persist()
                    device.operation_deadline = time.monotonic() + 10 * 60
                    try:
                        core.run_origin_scenario(device, observer, phase_out, 'movie', scenario, persist)
                        fixture['addon_data/script.infinity.commandcenter/continue-watching.json'] = 'LEGITIMATE_UI_WATCHLIST_AND_ACTUAL_MOVIE'
                    except Exception as error:
                        scenario.update(status=failure_status(error, core.classify_scenario(error, scenario)), error=repr(error), traceback=traceback.format_exc())
                    try:
                        core.stop_video(device, observer)
                        semantic_before = observer.call('state')
                        base.save(phase_out / 'actual-pre-recovery-state.json', semantic_before)
                    except Exception as error: phase['runtime']['state_capture'] = dict(status=failure_status(error), error=repr(error))
                    device.operation_deadline = None
                else:
                    if semantic_before is not None:
                        after = observer.call('state')
                        require(core.playback_domain(semantic_before) == core.playback_domain(after) and
                                all(semantic_before['data'].get(bucket) == after['data'].get(bucket) for bucket in ('watchlist', 'collection', 'later', 'lists')),
                                'RECOVERY_AUTHENTICATED_AVAILABLE_STATE_NOT_RETAINED')
                        device.alive()
                        phase['runtime'] = dict(status='PASS_AVAILABLE_AUTHENTICATED_STATE_ONLY', playback_record_available=bool(semantic_before['data'].get('items')))
                        report['functional_recovery'] = 'NOT_RUN_PLAYBACK_RECOVERY; AUTHENTICATED_AVAILABLE_STATE_ONLY'
            except Exception as error:
                phase['phase_error'] = dict(status=outcome(error), error=repr(error), traceback=traceback.format_exc())
                try: base.capture_failure(device, phase_out)
                except Exception as capture_error: phase['phase_error']['capture_error'] = repr(capture_error)
            finally:
                if device:
                    if device.phase_epoch is not None and device.pid:
                        try:
                            phase['phase_end_liveness'] = final_liveness(device)
                        except Exception as error:
                            phase['phase_end_liveness'] = dict(status=outcome(error), error=repr(error))
                    try: phase['final_package_identity'] = installed_package(device, expected, uid)
                    except Exception as error: phase['final_package_identity'] = dict(status=outcome(error), error=repr(error))
                persist()
        all_results = list(result_statuses(report['versions']))
        report['status'] = 'FAIL_SELECTED_POST_SIGN_CASE' if any(value.startswith('FAIL') for value in all_results) else 'COMPLETED_EXPERIMENTAL_CASES_WITH_EXPLICIT_RUNTIME_LIMITS'
        report['unverified_runtime_disclosure'] = 'PackageManager/file byte retention does not prove functional recovery, all-provider tracking, native stability or physical Fold acceptance.'
    except Exception as error:
        report.update(status='BLOCKED_HOST_OR_ENVIRONMENT', error=repr(error), traceback=traceback.format_exc())
    finally:
        if reader:
            try: report['lifecycle'] = base.stop_lifecycle_log(reader, out)
            except Exception as error: report['lifecycle_error'] = repr(error)
        persist()
        if device and disposer: disposer['arm_host_disposal'](device, out)
    return 1 if report['status'].startswith(('FAIL', 'BLOCKED')) else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'sdk', 'out'): parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.inputs, args.sdk, args.out))
