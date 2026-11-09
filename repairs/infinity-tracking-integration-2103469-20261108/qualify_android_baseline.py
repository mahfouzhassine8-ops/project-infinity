"""Unchanged signed69 / stock API36 baseline startup qualification only.

One installation; three explicit process starts with retained data. No playback,
provider/fixture addon, Close journey, shutdown acceptance, build or signing.
The old API37 transport and its guards are never imported or overridden.
"""
import argparse
import codecs
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import runpy
import shutil
import socket
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time
import traceback
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIRST = ROOT / 'repairs/infinity-final-closure-2103407'
REQUEST = HERE / 'ANDROID-BASELINE-REQUEST.json'
RECEIPT = HERE / 'ANDROID-BASELINE-HOST-GUARDS.json'
PACKAGE = 'com.projectinfinity.kodi'
CC = 'script.infinity.commandcenter'
HOME = '/sdcard/Android/data/' + PACKAGE + '/files/.kodi'
PROFILE = HOME + '/userdata'
AVD = 'infinity-tracking-baseline-api36'
IMAGE = 'system-images;android-36;google_apis;x86_64'
SOURCE = 'a76e29b84996304241e6b309d56a31e6659ad190'
APK_SHA = '804eebc57af2e4ef4e5418b56994bda64eb7fd7e7f2c0653b5c6e2a9f7833058'
NATIVE_SHA = 'ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ARTIFACT = dict(id=13631340281, name='Infinity-Watchlist-Original-Signed-2103469-42514440156-INTERNAL-QA',
                digest='sha256:f9d054ee500326b77ee2bf4ce8673af2bd54c54115831899d374d931a98dff43', size_in_bytes=329126132)
RETAINED = 'a4a89977f085480c720a7b6e73489374d01395dc'
COMMON = 'repairs/infinity-watchlist-playback-2103466-20261108/android_watchlist_common.py'
COMMON_SHA = 'f8d5b4cec4db192ffa096e683f1f95d1b48cf3a62ba9acebc5ee7cff65dfa712'


def require(value, label):
    if not value:
        raise RuntimeError(label)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def load(path):
    return json.loads(Path(path).read_text())


def command(args, timeout=30, check=True, binary=False):
    result = subprocess.run(list(map(str, args)), capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(map(str, args[:4])) + ': ' + result.stderr.decode(errors='replace')[-1200:])
    return result.stdout if binary else result.stdout.decode(errors='replace')


def git_source(commit, path):
    return command(['git', '-C', ROOT, 'show', commit + ':' + path], binary=True)


def gh(path):
    return json.loads(command(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/' + path]))


def checked_request(path):
    request = load(path)
    expected = dict(schema=1, operation='qualify-unchanged69-stock-api36-startup', selected_before_execution=True,
                    baseline_only=True, application_startup_only=True, application_feature_tests=False,
                    shutdown_tests=False, startup_attempts=3, stable_seconds=45, avd_name=AVD, image=IMAGE,
                    image_revision=7, apk_sha256=APK_SHA, certificate_sha256=CERT, package=PACKAGE,
                    version_code=2103469, min_sdk=21, target_sdk=35)
    require(all(type(request.get(k)) is type(v) and request[k] == v for k, v in expected.items()), 'EXACT_SELECTED_BASELINE_ONLY_REQUEST')
    require(request['harness_sha256'] == sha(__file__) and request['host_guard_receipt_sha256'] == sha(RECEIPT), 'COMMITTED_HARNESS_AND_HOST_GUARD_BINDING')
    require(load(RECEIPT)['harness_sha256'] == sha(__file__), 'EXACT_HOST_GUARD_RECEIPT_SOURCE')
    return request


def safe_zip(z):
    names = z.namelist()
    require(len(names) == len(set(names)) and len(names) <= 15000, 'BOUNDED_UNIQUE_ZIP_MEMBERS')
    require(sum(i.file_size for i in z.infolist()) < 2 * 1024 ** 3, 'BOUNDED_ZIP_BYTES')
    for item in z.infolist():
        p = Path(item.filename)
        require(not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename and
                '\0' not in item.filename and not stat.S_ISLNK(item.external_attr >> 16), 'SAFE_ZIP_MEMBER')
    return names


def original_module_tools():
    for name in ('module_bundle.py', 'FIRSTPARTY-COMPOSITION-PLAN.json', 'ORIGINAL-INFINITY-PUBLIC-KEY.pem', 'p0/manifest.py'):
        path = FIRST / name
        require(path.read_bytes() == git_source(SOURCE, path.relative_to(ROOT).as_posix()), 'UNCHANGED_ORIGINAL_MODULE_OR_AXML_TOOL:' + name)
    sys.path.insert(0, str(FIRST))
    import module_bundle
    spec = importlib.util.spec_from_file_location('original_baseline_axml', FIRST / 'p0/manifest.py')
    axml = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(axml)
    return module_bundle, axml


def axml_metadata(raw, parser):
    parts = list(parser.chunks(raw))
    strings = parser.string_pool(next(p for _, kind, p in parts if kind == 1))
    result = {}
    for _, kind, part in parts:
        if kind != 0x102:
            continue
        node = strings[struct.unpack_from('<I', part, 20)[0]]
        if node not in ('manifest', 'uses-sdk'):
            continue
        first, step, count = struct.unpack_from('<3H', part, 24)
        values = {}
        for i in range(count):
            at = 16 + first + i * step
            key = strings[struct.unpack_from('<I', part, at + 4)[0]]
            typ, value = part[at + 15], struct.unpack_from('<I', part, at + 16)[0]
            values[key] = strings[value] if typ == 3 else value
        result[node] = values
    return result


def verify_apk(apk, sdk, out):
    require(sha(apk) == APK_SHA, 'EXACT_UNCHANGED_ORIGINAL69_APK')
    signature = command([sdk / 'apksigner', 'verify', '--verbose', '--print-certs', apk], timeout=60)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [CERT], 'ONE_ORIGINAL_PERMANENT_CERTIFICATE')
    (out / 'SIGNATURE.txt').write_text(signature)
    bundle, axml = original_module_tools()
    with tempfile.TemporaryDirectory() as temporary, ZipFile(apk) as z:
        names = safe_zip(z)
        metadata = axml_metadata(z.read('AndroidManifest.xml'), axml)
        require(metadata['manifest']['package'] == PACKAGE and metadata['manifest']['versionCode'] == 2103469 and
                metadata['uses-sdk']['minSdkVersion'] == 21 and metadata['uses-sdk']['targetSdkVersion'] == 35, 'EXACT_PACKAGE_VERSION_MIN21_TARGET35')
        require(hashlib.sha256(z.read('lib/arm64-v8a/libkodi.so')).hexdigest() == NATIVE_SHA, 'EXACT_NATIVE466_FOUNDATION')
        modules = Path(temporary) / 'modules'
        modules.mkdir()
        for name in names:
            if not name.endswith('/') and any(name.startswith('assets/addons/' + aid + '/') for aid in bundle.IDS):
                p = modules / name.removeprefix('assets/addons/')
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(z.read(name))
        payload, files = bundle.build(modules)
        manifest = modules / CC / bundle.MANIFEST
        require(len(files) == 80 and manifest.read_bytes() == payload, 'COMPLETE_CANONICAL80_MODULE_MANIFEST')
        command(['openssl', 'dgst', '-sha256', '-verify', FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem', '-signature',
                 str(manifest) + '.sig', manifest])
        module_hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
        extra = {CC + '/' + name: sha(modules / CC / name) for name in (bundle.MANIFEST, bundle.MANIFEST + '.sig')}
    return dict(apk_sha256=APK_SHA, certificate_sha256=CERT, metadata=metadata, native_sha256=NATIVE_SHA,
                module_sources=module_hashes, module_metadata=extra, authenticated_source_count=80)


def admit(request, sdk, out):
    selected = checked_request(request)
    require(not out.exists(), 'FRESH_ADMISSION_DIRECTORY')
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
            os.environ.get('GITHUB_REF') == 'refs/heads/work/infinity-tracking-integration-20261108', 'AUTHORIZED_CI_BRANCH_ONLY')
    head = command(['git', '-C', ROOT, 'rev-parse', 'HEAD']).strip()
    require(head == os.environ['GITHUB_SHA'] and not command(['git', '-C', ROOT, 'status', '--porcelain', '--untracked-files=no']).strip(), 'EXACT_CLEAN_COMMITTED_HARNESS_SOURCE')
    this = gh('actions/runs/' + os.environ['GITHUB_RUN_ID'])
    require(this['head_sha'] == head and this['workflow_id'] == 393886994 and this['path'] == '.github/workflows/infinity-saved-navigation-android.yml', 'EXISTING_SELECTED_FEATURE_WORKFLOW')
    run = gh('actions/runs/42514440156')
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == SOURCE and
            run['workflow_id'] == 397702717 and run['path'] == '.github/workflows/infinity-combined-release.yml' and
            run['head_branch'] == 'work/infinity-watchlist-phase-b-20261108', 'EXACT_ORIGINAL69_SIGNING_PRODUCER')
    artifact = gh('actions/artifacts/' + str(ARTIFACT['id']))
    require(not artifact['expired'] and artifact['workflow_run']['id'] == 42514440156 and
            all(artifact[k] == v for k, v in ARTIFACT.items()), 'EXACT_LIVE_ORIGINAL69_ARTIFACT')
    out.mkdir(parents=True)
    archive = out / 'original69.zip'
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/' + str(ARTIFACT['id']) + '/zip'],
                       stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
    require(archive.stat().st_size == ARTIFACT['size_in_bytes'] and 'sha256:' + sha(archive) == ARTIFACT['digest'], 'EXACT_DOWNLOADED_ARTIFACT_DIGEST')
    with ZipFile(archive) as z:
        safe_zip(z)
        name = 'Infinity-2103469-Combined-Original-Signer.apk'
        require(name in z.namelist(), 'EXACT_ORIGINAL69_ARTIFACT_APK_PATH')
        apk = out / name
        with z.open(name) as source, apk.open('xb') as target:
            shutil.copyfileobj(source, target)
    proof = verify_apk(apk, sdk, out)
    proof.update(status='PASS_ORIGINAL69_INPUT_ADMISSION_ONLY', source=head, request_sha256=sha(request),
                 harness_sha256=sha(__file__), host_guard_receipt_sha256=sha(RECEIPT), signing_run=42514440156,
                 signing_source=SOURCE, artifact=ARTIFACT, APK_path=str(apk.resolve()), SDK=str(sdk.resolve()),
                 application_started=False, shutdown='NOT_SELECTED', full_twelve_checks='NOT_RUN', release_acceptance=False)
    save(out / 'ADMISSION.json', proof)
    save(out / 'GITHUB-PROVENANCE.json', dict(original_signing_run=run, original_artifact=artifact, current_run=this))
    save(out / 'SELECTED-REQUEST.json', selected)


def retained_disposal(admission):
    original = git_source(RETAINED, COMMON)
    require(hashlib.sha256(original).hexdigest() == COMMON_SHA, 'EXACT_RETAINED_HOST_DISPOSAL_SOURCE')
    old = b"DISPOSABLE_AVD='infinity-four-repair-api37'"
    require(original.count(old) == 1, 'ONE_HOST_AVD_SCOPE_ANCHOR')
    adapted = original.replace(old, ("DISPOSABLE_AVD='" + AVD + "'").encode(), 1)
    p = admission / '_retained_host_disposal.py'
    if p.exists():
        require(p.read_bytes() == adapted, 'RETAINED_HOST_DISPOSAL_ARTIFACT_UNCHANGED')
    else:
        p.write_bytes(adapted)
    functions = runpy.run_path(str(p))
    return functions, dict(source=RETAINED, source_sha256=COMMON_SHA, adapted_sha256=hashlib.sha256(adapted).hexdigest(),
                           adaptation='Only DISPOSABLE_AVD literal; original PID/start/exe/SDK/action/pidfd/report gates unchanged')


def properties(raw):
    return dict(re.findall(r'^\[([^\]]+)\]: \[(.*)\]$', raw, re.M))


def measured_center(node):
    match = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', node.get('bounds', ''))
    require(match is not None and node.get('clickable') == 'true' and node.get('enabled') == 'true', 'MEASURED_ENABLED_CLICKABLE_UI_NODE')
    x1, y1, x2, y2 = map(int, match.groups())
    require(x2 > x1 and y2 > y1, 'NONEMPTY_MEASURED_UI_BOUNDS')
    return (x1 + x2) // 2, (y1 + y2) // 2


class Device:
    def __init__(self, out, sdk_root):
        self.out, self.sdk_root = out, sdk_root.resolve()
        self.adb_bin = self.sdk_root / 'platform-tools/adb'
        devices = command([self.adb_bin, 'devices']).splitlines()[1:]
        connected = [line.split()[0] for line in devices if line.strip()]
        require(len(connected) == 1 and re.fullmatch(r'emulator-\d+', connected[0]), 'ONE_DISPOSABLE_EMULATOR_ONLY')
        require(any(line.split() == [connected[0], 'device'] for line in devices), 'EMULATOR_ADB_READY')
        self.serial, self.pid, self.start_time = connected[0], 0, None
        self.actions = []
        self.ui_sequence, self.last_ui_capture = 0, None

    def adb(self, *args, timeout=20, check=True, binary=False):
        return command([self.adb_bin, '-s', self.serial, *args], timeout=timeout, check=check, binary=binary)

    def shell(self, *args, timeout=12, check=True):
        return self.adb('shell', *args, timeout=timeout, check=check)

    def nodes(self, label):
        self.ui_sequence += 1
        sequence = self.ui_sequence
        remote = '/sdcard/Download/infinity-baseline-ui-' + str(os.getpid()) + '-' + str(sequence) + '.xml'
        detail = dict(sequence=sequence, started_epoch=time.time(), remote_file=remote, label=label, accepted=False,
                      returncode=None, stdout='', stderr='')
        self.last_ui_capture = None
        try:
            result = subprocess.run([str(self.adb_bin), '-s', self.serial, 'shell', 'uiautomator', 'dump', remote],
                                    check=False, capture_output=True, text=True, timeout=15)
            detail.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
            marker = 'UI hierchary dumped to: ' + remote
            require(result.returncode == 0 and result.stdout.strip() == marker and 'ERROR:' not in result.stderr, 'FRESH_UI_DUMP_SUCCESS_MARKER_REQUIRED')
            raw = self.shell('cat', remote)
            require(0 < len(raw.encode()) <= 4 * 1024 * 1024, 'BOUNDED_FRESH_UI_XML')
            tree = ET.fromstring(raw)
            require(tree.tag == 'hierarchy', 'FRESH_UI_HIERARCHY_REQUIRED')
            versioned = label + '-dump-' + str(sequence).zfill(5) + '.xml'
            (self.out / versioned).write_text(raw)
            (self.out / (label + '.xml')).write_text(raw)
            detail.update(accepted=True, XML_file=versioned, XML_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                          packages=sorted({n.get('package', '') for n in tree.iter('node')}))
            self.last_ui_capture = dict(sequence=sequence, captured_epoch=time.time(), XML_file=versioned)
            return tree
        except (RuntimeError, OSError, ET.ParseError, subprocess.SubprocessError) as error:
            detail['error'] = repr(error)
            if isinstance(error, subprocess.TimeoutExpired):
                detail['stdout'] = (error.stdout or b'').decode(errors='replace') if isinstance(error.stdout, bytes) else (error.stdout or '')
                detail['stderr'] = (error.stderr or b'').decode(errors='replace') if isinstance(error.stderr, bytes) else (error.stderr or '')
            return None  # No fresh tree means no action; the existing startup deadline still applies.
        finally:
            detail['finished_epoch'] = time.time()
            save(self.out / ('ui-dump-' + str(sequence).zfill(5) + '.json'), detail)

    def permission_snapshot(self, label):
        detail = dict(captured_epoch=time.time(), UI_capture=self.last_ui_capture, read_only=True)
        commands = dict(package_permissions=['dumpsys', 'package', PACKAGE],
                        all_files_appop=['cmd', 'appops', 'get', PACKAGE, 'MANAGE_EXTERNAL_STORAGE'],
                        foreground_tasks=['dumpsys', 'activity', 'activities'],
                        Java_pids=['pidof', PACKAGE], native_pids=['pidof', PACKAGE + ':kodi'])
        for name, args in commands.items():
            try:
                result = subprocess.run([str(self.adb_bin), '-s', self.serial, 'shell', *args],
                                        check=False, capture_output=True, text=True, timeout=3)
                detail[name] = dict(returncode=result.returncode, stdout=result.stdout[:2 * 1024 * 1024],
                                    stderr=result.stderr[:4096], stdout_truncated=len(result.stdout) > 2 * 1024 * 1024)
            except (OSError, subprocess.SubprocessError) as error:
                detail[name] = dict(error=repr(error))
        save(self.out / (label + '.json'), detail)

    def screenshot(self, label):
        data = self.adb('exec-out', 'screencap', '-p', timeout=15, binary=True)
        require(data.startswith(b'\x89PNG\r\n\x1a\n'), 'REAL_ANDROID_SCREENSHOT')
        (self.out / (label + '.png')).write_bytes(data)

    def pids(self):
        return self.shell('pidof', PACKAGE + ':kodi', check=False).strip().split()

    def alive(self):
        require(self.pids() == [str(self.pid)], 'NATIVE_ENGINE_DIED_OR_RESTARTED')
        raw = self.shell('cat', '/proc/' + str(self.pid) + '/stat')
        started = raw.rsplit(') ', 1)[1].split()[19]
        require(started == self.start_time, 'NATIVE_PID_REUSED')

    def tap(self, node, purpose):
        require(self.last_ui_capture is not None, 'FRESH_CAPTURE_REQUIRED_BEFORE_MEASURED_TAP')
        center = measured_center(node)
        self.shell('input', 'tap', *center)
        self.actions.append(dict(purpose=purpose, package=node.get('package'), resource_id=node.get('resource-id'),
                                 description=node.get('content-desc'), text=node.get('text'), bounds=node.get('bounds'), center=center,
                                 UI_capture=self.last_ui_capture, action_epoch=time.time()))

    def handle_ui(self, tree):
        nodes = list(tree.iter('node'))
        rationale = 'Infinity requires access to your device media and files to function. Please allow this via the following dialogue box or Infinity will exit.'
        titles = [n for n in nodes if n.get('package') == PACKAGE and n.get('resource-id') == 'android:id/alertTitle' and n.get('text') == 'Infinity']
        messages = [n for n in nodes if n.get('package') == PACKAGE and n.get('resource-id') == 'android:id/message' and n.get('text') == rationale]
        buttons = [n for n in nodes if n.get('class') == 'android.widget.Button' and n.get('clickable') == 'true' and n.get('enabled') == 'true']
        if len(titles) == len(messages) == len(buttons) == 1 and buttons[0].get('package') == PACKAGE and buttons[0].get('resource-id') == 'android:id/button3' and buttons[0].get('text') == 'Continue':
            self.tap(buttons[0], 'Measured exact Infinity initial media/files permission rationale Continue')
            return True
        card = [n for n in nodes if n.get('package') == PACKAGE and n.get('content-desc') == 'Infinity. Open Infinity.' and n.get('clickable') == 'true']
        require(len(card) <= 1, 'UNAMBIGUOUS_ORIGINAL_INFINITY_CARD')
        if card:
            self.tap(card[0], 'Original measured Infinity experience card')
            return True
        permissions = [n for n in nodes if n.get('package') == 'com.google.android.permissioncontroller' or n.get('package') == 'com.android.permissioncontroller']
        allow = [n for n in permissions if n.get('resource-id', '').rsplit('/', 1)[-1] in
                 ('permission_allow_button', 'permission_allow_foreground_only_button', 'permission_allow_all_button') and n.get('clickable') == 'true']
        if allow:
            require(len(allow) == 1 and any('Infinity' in n.get('text', '') for n in permissions), 'EXACT_APP_OWNED_OS_PERMISSION_DIALOG')
            self.tap(allow[0], 'Measured stock OS runtime permission for Infinity')
            return True
        settings = [n for n in nodes if n.get('package') == 'com.android.settings']
        compose = [n for n in settings if n.get('class') == 'android.view.View' and n.get('checkable') == 'true' and n.get('clickable') == 'true' and n.get('enabled') == 'true' and
                   any(child.get('package') == 'com.android.settings' and child.get('text') == 'Allow access to manage all files' for child in n.iter('node') if child is not n)]
        if len([n for n in settings if n.get('text') == 'Infinity']) == 1 and len([n for n in settings if n.get('text') == 'All files access']) == 1 and compose:
            require(len(compose) == 1 and compose[0].get('checked') in ('false', 'true'), 'ONE_EXACT_STOCK_COMPOSE_ALL_FILES_ROW')
            if compose[0].get('checked') == 'false':
                self.tap(compose[0], 'Measured exact stock Settings Compose all-files row for Infinity')
                return True
            self.shell('input', 'keyevent', 'KEYCODE_BACK')
            self.actions.append(dict(purpose='Back after fresh checked=true stock all-files permission', keycode='KEYCODE_BACK', UI_capture=self.last_ui_capture, action_epoch=time.time()))
            self.permission_snapshot('all-files-after-back-ui-' + str(self.ui_sequence))
            return True
        texts = ' '.join(n.get('text', '') for n in settings)
        if 'Infinity' in texts and ('Allow access to manage all files' in texts or 'Allow access to all files' in texts):
            switches = [n for n in settings if n.get('class') in ('android.widget.Switch', 'android.widget.CompoundButton') and n.get('clickable') == 'true']
            require(len(switches) == 1, 'ONE_EXACT_STOCK_ALL_FILES_SWITCH')
            if switches[0].get('checked') != 'true':
                self.tap(switches[0], 'Measured stock Settings all-files permission for Infinity')
                return True
            self.shell('input', 'keyevent', 'KEYCODE_BACK')
            self.actions.append(dict(purpose='Back after fresh checked=true stock all-files permission', keycode='KEYCODE_BACK', UI_capture=self.last_ui_capture, action_epoch=time.time()))
            self.permission_snapshot('all-files-after-back-ui-' + str(self.ui_sequence))
            return True
        tutorials = [n for n in nodes if n.get('package') == 'com.android.systemui' and n.get('text') in ('Got it', 'GOT IT') and n.get('clickable') == 'true']
        if tutorials:
            require(len(tutorials) == 1, 'ONE_MEASURED_STOCK_IMMERSIVE_TUTORIAL')
            self.tap(tutorials[0], 'Measured stock OS immersive tutorial acknowledgement')
            return True
        return False

    def rpc(self, method, params=None, timeout=5):
        require(method in ('JSONRPC.Ping', 'GUI.GetProperties', 'Input.Home', 'Input.Right', 'Input.Left'), 'STARTUP_ONLY_RPC_METHOD')
        deadline, received = time.monotonic() + timeout, 0
        def remaining():
            value = deadline - time.monotonic()
            if value <= 0:
                raise TimeoutError('Absolute startup JSONRPC deadline: ' + method)
            return value
        request = dict(jsonrpc='2.0', id=69, method=method)
        if params is not None:
            request['params'] = params
        with socket.create_connection(('127.0.0.1', 19090), timeout=remaining()) as conn:
            conn.settimeout(remaining())
            conn.sendall(json.dumps(request).encode())
            utf8, decoder, pending = codecs.getincrementaldecoder('utf-8')(), json.JSONDecoder(), ''
            while received < 1024 * 1024:
                conn.settimeout(remaining())
                chunk = conn.recv(min(65536, 1024 * 1024 - received))
                if not chunk:
                    break
                received += len(chunk)
                pending += utf8.decode(chunk)
                while pending.strip():
                    remaining()
                    pending = pending.lstrip()
                    try:
                        reply, end = decoder.raw_decode(pending)
                    except ValueError:
                        break
                    pending = pending[end:]
                    if reply.get('id') != 69:
                        continue
                    require('error' not in reply and reply.get('jsonrpc') == '2.0', 'REAL_STARTUP_RPC_ERROR:' + method)
                    remaining()
                    return reply['result']
        raise ConnectionError('Incomplete bounded startup JSONRPC reply: ' + method)


def environment(device, out):
    raw = device.shell('getprop')
    p = properties(raw)
    (out / 'runtime-properties.txt').write_text(raw)
    require(p.get('ro.kernel.qemu') == '1' and p.get('ro.build.version.sdk') == '36' and
            p.get('ro.product.cpu.abi') == 'x86_64' and 'arm64-v8a' in p.get('ro.product.cpu.abilist', '').split(',') and
            p.get('ro.dalvik.vm.native.bridge') == 'libndk_translation.so' and p.get('sys.boot_completed') == '1', 'STOCK_API36_QEMU_X86_64_ARM64_BRIDGE_REQUIRED')
    require(device.shell('getconf', 'PAGESIZE').strip() == '4096', 'STOCK_4K_PAGES_REQUIRED')
    require(device.adb('emu', 'avd', 'name').splitlines()[0].strip() == AVD, 'EXACT_DISPOSABLE_API36_AVD')
    sdk_image = device.sdk_root / 'system-images/android-36/google_apis/x86_64'
    package_properties = dict(line.split('=', 1) for line in (sdk_image / 'source.properties').read_text().splitlines() if '=' in line and not line.startswith('#'))
    require(package_properties.get('Pkg.Revision') == '7' and package_properties.get('AndroidVersion.ApiLevel') == '36' and
            package_properties.get('SystemImage.Abi') == 'x86_64' and package_properties.get('SystemImage.TagId') == 'google_apis', 'EXACT_STOCK_SDK_API36_R7_IMAGE')
    avd_root = Path(os.environ.get('ANDROID_AVD_HOME', str(Path(os.environ.get('ANDROID_USER_HOME', str(Path.home() / '.android'))) / 'avd')))
    config = (avd_root / (AVD + '.avd') / 'config.ini').read_text()
    config_values = dict(line.split('=', 1) for line in config.splitlines() if '=' in line)
    require((device.sdk_root / config_values['image.sysdir.1']).resolve() == sdk_image.resolve(), 'EXACT_RUNNING_AVD_IMAGE_BINDING')
    (out / 'avd-config.ini').write_text(config)
    (out / 'image-source.properties').write_text((sdk_image / 'source.properties').read_text())
    bridge = out / 'stock-libndk_translation.so'
    device.adb('pull', '/system/lib64/libndk_translation.so', bridge, timeout=30)
    actual = device.shell('sha256sum', '/system/lib64/libndk_translation.so').split()[0]
    require(sha(bridge) == actual, 'ACTUAL_STOCK_BRIDGE_HASH')
    notes = command(['readelf', '-n', bridge])
    (out / 'stock-bridge-notes.txt').write_text(notes)
    build_ids = re.findall(r'Build ID: ([0-9a-f]+)', notes)
    require(len(build_ids) == 1, 'STOCK_BRIDGE_BUILD_ID_REQUIRED')
    result = dict(status='PASS_STOCK_API36_ENVIRONMENT_INTAKE_ONLY', sdk=36, image=IMAGE, revision=7,
                  fingerprint=p.get('ro.build.fingerprint'), page_size=4096, serial=device.serial,
                  stock_bridge_sha256=actual, stock_bridge_build_id=build_ids[0], compatibility_overrides=False,
                  application_installed=False, application_started=False)
    save(out / 'ENVIRONMENT.json', result)
    return result


def installed_hashes(device, proof):
    expected = dict(proof['module_sources'], **proof['module_metadata'])
    names = sorted(expected)
    actual = {}
    for start in range(0, len(names), 16):
        batch = names[start:start + 16]
        paths = [HOME + '/addons/' + n for n in batch]
        text = device.shell('sha256sum', *paths, timeout=15)
        for line in text.splitlines():
            match = re.fullmatch(r'([0-9a-f]{64})\s+(.+)', line)
            require(match is not None and match[2].startswith(HOME + '/addons/'), 'INSTALLED_MODULE_HASH_ROW')
            name = match[2].removeprefix(HOME + '/addons/')
            require(name in batch and name not in actual, 'EXACT_INSTALLED_MODULE_HASH_SET')
            actual[name] = match[1]
    require(actual == expected, 'COMPLETE_INSTALLED80_SOURCES_AND_ORIGINAL_METADATA_UNCHANGED')
    return actual


def installed_apk(device):
    paths = device.shell('pm', 'path', PACKAGE).splitlines()
    require(len(paths) == 1 and paths[0].startswith('package:/data/app/') and paths[0].endswith('/base.apk'), 'ONE_INSTALLED_ORIGINAL_APK')
    require(device.shell('sha256sum', paths[0].removeprefix('package:')).split()[0] == APK_SHA, 'INSTALLED_APK_STILL_EXACT_ORIGINAL69')


def root_reconnect(device, out):
    detail = dict(status='ROOT_HANDSHAKE_STARTED', root_requests=1, application_installed=False)
    started = time.monotonic()
    try:
        result = subprocess.run([str(device.adb_bin), '-s', device.serial, 'root'],
                                check=False, capture_output=True, text=True, timeout=20)
        detail['root_command'] = dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        save(out / 'ADB-ROOT-HANDSHAKE.json', detail)
        device.adb('wait-for-device', timeout=25)
        detail['verified_uid'] = device.shell('id', '-u', timeout=8).strip()
        require(detail['verified_uid'] == '0', 'ACTUAL_ROOT_RECONNECTION_REQUIRED_BEFORE_INSTALL')
        detail['status'] = 'PASS_VERIFIED_ROOT_RECONNECTION_ONLY'
        return detail
    except Exception as error:
        detail.update(status='FAIL_ROOT_RECONNECTION_NO_INSTALL', error=repr(error))
        raise
    finally:
        detail['elapsed_seconds'] = time.monotonic() - started
        save(out / 'ADB-ROOT-HANDSHAKE.json', detail)


def crash_free_alive(device):
    device.alive()
    crash = device.shell('logcat', '-b', 'crash', '-d', '-t', '2000', timeout=5)
    package = re.escape(PACKAGE)
    require(not re.search(r'(?<![A-Za-z0-9_.])' + package + r'(?=$|[^A-Za-z0-9_.])', crash), 'BASELINE_PACKAGE_OR_CHILD_CRASH_NO_RETRY')
    device.alive()


def _lifecycle_file_limit():
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))


def start_lifecycle_log(device, out):
    timeout = shutil.which('timeout')
    require(timeout is not None, 'BOUNDED_LIFECYCLE_READER_REQUIRES_HOST_TIMEOUT')
    tags = ['ActivityTaskManager:I', 'ActivityManager:I', 'WindowManager:I', 'PermissionController:I', 'PermissionManager:I',
            'AndroidRuntime:E', 'libc:F', 'DEBUG:F', 'linker:W', 'Kodi:V', 'kodi:V', 'XBMC:V', 'Infinity:V', 'Splash:V',
            'am_proc_start:I', 'am_proc_died:I', 'am_crash:I', 'am_kill:I', 'am_finish_activity:I', 'am_create_activity:I',
            'am_resume_activity:I', 'am_pause_activity:I', 'am_destroy_activity:I', 'am_force_stop:I', '*:S']
    args = [timeout, '--signal=TERM', '--kill-after=2', '900', str(device.adb_bin), '-s', device.serial, 'logcat',
            '-v', 'threadtime', '-b', 'main', '-b', 'system', '-b', 'crash', '-b', 'events', *tags]
    with (out / 'lifecycle-filtered.log').open('wb') as stdout, (out / 'lifecycle-filtered.stderr').open('wb') as stderr:
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                   close_fds=True, start_new_session=True, preexec_fn=_lifecycle_file_limit)
    save(out / 'LIFECYCLE-CAPTURE.json', dict(status='STARTED_BEFORE_FIRST_SPLASH', host_pid=process.pid, command=args,
                                           started_epoch=time.time(), duration_limit_seconds=900, per_file_limit_bytes=8 * 1024 * 1024,
                                           logcat_cleared=False, application_state_changed=False))
    return process


def stop_lifecycle_log(process, out):
    detail = load(out / 'LIFECYCLE-CAPTURE.json')
    try:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)  # Only the session created for this reader and its adb child.
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=2)
        detail.update(status='OWN_READER_STOP_REQUESTED_LEADER_EXITED', returncode=process.poll(),
                      observation_scope='Owned reader leader exit only; adb descendant retirement not independently audited')
    except (OSError, subprocess.SubprocessError) as error:
        detail.update(status='OWN_READER_STOP_BOUNDED_OR_UNAVAILABLE', error=repr(error))
    detail.update(finished_epoch=time.time(), stdout_bytes=(out / 'lifecycle-filtered.log').stat().st_size,
                  stderr_bytes=(out / 'lifecycle-filtered.stderr').stat().st_size)
    detail['size_cap_reached'] = max(detail['stdout_bytes'], detail['stderr_bytes']) >= detail['per_file_limit_bytes']
    save(out / 'LIFECYCLE-CAPTURE.json', detail)
    return detail


def capture_failure(device, out):
    detail = dict(status='READ_ONLY_BOUNDED_CAPTURE', application_restarted=False, target_pid=device.pid)
    deadline = time.monotonic() + 25
    try:
        while time.monotonic() < deadline - 8:
            if not device.shell('pidof', 'crash_dump64', check=False, timeout=3).strip():
                break
            time.sleep(.25)
        running = bool(device.shell('pidof', 'crash_dump64', check=False, timeout=3).strip())
        detail['debuggerd_still_running'] = running
        (out / 'failure-crash-buffer.txt').write_text(device.shell('logcat', '-b', 'crash', '-d', '-t', '1000', timeout=4)[-2 * 1024 * 1024:])
        if not running:
            for name in device.shell('ls', '-t', '/data/tombstones', timeout=3).splitlines()[:4]:
                if not re.fullmatch(r'tombstone_[0-9]+', name):
                    continue
                source_bytes = device.shell('stat', '-c', '%s', '/data/tombstones/' + name, timeout=3).strip()
                require(source_bytes.isdigit(), 'TOMBSTONE_SOURCE_SIZE_REQUIRED')
                text = device.shell('head', '-c', '2097152', '/data/tombstones/' + name, timeout=4)
                if PACKAGE in text and (not device.pid or re.search(r'\bpid:\s*' + str(device.pid) + r'\b', text)):
                    (out / 'failure-final-tombstone.txt').write_text(text)
                    detail.update(matching_tombstone=name, tombstone_source_bytes=int(source_bytes),
                                  tombstone_capture_limit_bytes=2097152, tombstone_truncated=int(source_bytes) > 2097152,
                                  debuggerd_finished=True, full_tombstone_captured=int(source_bytes) <= 2097152)
                    break
        else:
            detail['status'] = 'DEBUGGERD_NOT_FINISHED_NO_FINAL_TOMBSTONE_CLAIM'
    except Exception as error:
        detail['capture_error'] = repr(error)
    finally:
        save(out / 'failure-native-capture.json', detail)
    device.permission_snapshot('failure-permission-state')
    for name, args in (('failure-logcat.txt', ('logcat', '-d', '-t', '2000')),
                       ('failure-pids.txt', ('shell', 'ps', '-A'))):
        try:
            (out / name).write_text(device.adb(*args, timeout=8)[-4 * 1024 * 1024:])
        except Exception as error:
            (out / (name + '.error')).write_text(repr(error))
    try:
        device.screenshot('failure')
    except Exception as error:
        (out / 'failure-screenshot.error').write_text(repr(error))


def resumed_component(raw):
    markers = [line for line in raw.splitlines() if re.match(r'^\s*(?:topResumedActivity|mResumedActivity)\s*[=:]', line)]
    components = set()
    for line in markers:
        match = re.match(r'^\s*(?:topResumedActivity|mResumedActivity)\s*[=:]\s*ActivityRecord\{[^}\n]*?\s([A-Za-z0-9_.]+/[A-Za-z0-9_.$]+)(?:\s|\})', line)
        if match is None:
            return None
        components.add(match[1])
    return next(iter(components)) if len(components) == 1 else None


def start_once(device, cycle, out):
    device.pid, device.start_time = 0, None
    started = subprocess.run([str(device.adb_bin), '-s', device.serial, 'shell', 'am', 'start', '-W', '-n', PACKAGE + '/.Splash'],
                             check=False, capture_output=True, text=True, timeout=30)
    save(out / ('start-' + str(cycle) + '-am-start.json'), dict(returncode=started.returncode, stdout=started.stdout,
                                                            stderr=started.stderr, captured_epoch=time.time()))
    require(started.returncode == 0, 'ORIGINAL_SPLASH_START_COMMAND_FAILED')
    deadline = time.monotonic() + 180
    ping, home, foreground = None, None, None
    app_ui_seen, launcher_captures = False, 0
    while time.monotonic() < deadline:
        pids = device.pids()
        if device.pid:
            device.alive()
        elif pids:
            require(len(pids) == 1 and pids[0].isdigit(), 'ONE_GENUINE_NATIVE_PROCESS')
            device.pid = int(pids[0])
            device.start_time = device.shell('cat', '/proc/' + pids[0] + '/stat').rsplit(') ', 1)[1].split()[19]
        crash = device.shell('logcat', '-b', 'crash', '-d', '-t', '80', timeout=5)
        require(PACKAGE not in crash, 'BASELINE_NATIVE_OR_JAVA_CRASH_NO_RETRY')
        tree = device.nodes('start-' + str(cycle) + '-latest-ui')
        if tree is not None:
            packages = {n.get('package', '') for n in tree.iter('node')}
            app_ui_seen = app_ui_seen or PACKAGE in packages
            launcher = bool(packages & {'com.google.android.apps.nexuslauncher', 'com.android.launcher3'})
            launcher_captures = launcher_captures + 1 if app_ui_seen and launcher and PACKAGE not in packages else 0
            require(launcher_captures < 3, 'APP_EXITED_TO_LAUNCHER_AFTER_APP_UI_NO_RELAUNCH')
            device.handle_ui(tree)
        if device.pid:
            try:
                ping = device.rpc('JSONRPC.Ping', timeout=3)
                home = device.rpc('GUI.GetProperties', dict(properties=['currentwindow', 'currentcontrol', 'skin']), timeout=3)
            except (ConnectionError, TimeoutError, OSError):
                time.sleep(.5)
                continue
            if ping == 'pong' and home.get('currentwindow', {}).get('id') == 10000 and home.get('skin', {}).get('id') == 'skin.infinity.diggz':
                raw, error = '', None
                try:
                    raw = device.shell('dumpsys', 'activity', 'activities', timeout=3)
                except (RuntimeError, OSError, subprocess.SubprocessError) as caught:
                    error = repr(caught)
                component = resumed_component(raw) if len(raw.encode()) <= 2 * 1024 * 1024 else None
                foreground = dict(component=component, captured_epoch=time.time(), raw_query=raw[:2 * 1024 * 1024],
                                  query_truncated=len(raw.encode()) > 2 * 1024 * 1024, error=error)
                save(out / ('start-' + str(cycle) + '-foreground.json'), foreground)
                if component and component.startswith(PACKAGE + '/'):
                    break
        time.sleep(.5)
    else:
        raise TimeoutError('NORMAL_SPLASH_INFINITY_HOME_STARTUP_DEADLINE')
    device.alive()
    return dict(cycle=cycle, pid=device.pid, process_start=device.start_time, entry='Original Splash and measured original Infinity card or retained original admission',
                ping=ping, home=home, foreground=foreground)


def run(request, admission, out, avd):
    checked_request(request)
    require(avd == AVD and os.environ.get('GITHUB_ACTIONS') == 'true' and
            os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
            os.environ.get('GITHUB_REF') == 'refs/heads/work/infinity-tracking-integration-20261108', 'EXACT_SELECTED_DISPOSABLE_CI_RUN')
    proof = load(admission / 'ADMISSION.json')
    require(proof['status'] == 'PASS_ORIGINAL69_INPUT_ADMISSION_ONLY' and proof['harness_sha256'] == sha(__file__) and
            proof['request_sha256'] == sha(request) and proof['host_guard_receipt_sha256'] == sha(RECEIPT) and
            proof['source'] == os.environ['GITHUB_SHA'], 'EXACT_ADMITTED_UNCHANGED_INPUTS')
    apk = Path(proof['APK_path'])
    require(sha(apk) == APK_SHA and not out.exists(), 'FRESH_RESULTS_AND_UNCHANGED69_APK')
    out.mkdir(parents=True)
    report = dict(status='RUNNING_BASELINE_ONLY_API36_STARTUP_QUALIFICATION', starts=[], APK_sha256=APK_SHA,
                  feature_checks='NOT_RUN', full_twelve_checks='NOT_RUN', shutdown='NOT_SELECTED', Fold='NOT_RUN', release_acceptance=False,
                  force_stop_scope='Only the two explicitly selected startup-reliability resets; no data clear or Close/shutdown coverage')
    device, disposer, reader = None, None, None
    code = 1
    try:
        device = Device(out, Path(os.environ['ANDROID_HOME']))
        disposer, report['retained_host_disposal'] = retained_disposal(admission)
        port = int(device.serial.removeprefix('emulator-'))
        targets = [p for entry in Path('/proc').iterdir() if entry.name.isdigit() and
                   disposer['_emulator_target'](p := disposer['_host_process'](int(entry.name)), str(device.sdk_root), port)]
        require(targets, 'EXACT_PINNED_SDK_EMULATOR_HOST_PROCESS_REQUIRED')
        report['environment'] = environment(device, out)
        require(not device.shell('pm', 'list', 'packages', PACKAGE).strip(), 'FRESH_VM_NO_PRIOR_INFINITY_INSTALLATION')
        report['adb_root_handshake'] = root_reconnect(device, out)
        device.adb('install', '--no-streaming', apk, timeout=300)
        installed_apk(device)
        report.update(application_installed=True, installed_APK_sha256=APK_SHA)
        save(out / 'ANDROID-VERIFICATION.json', report)
        # Minimal disposable settings only. No addon, provider, observer or tracking seed.
        settings = '<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting><setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>'
        local = out / 'disposable-guisettings.xml'
        local.write_text(settings)
        device.shell('mkdir', '-p', PROFILE)
        device.adb('push', local, PROFILE + '/guisettings.xml')
        uid = device.shell('stat', '-c', '%u', '/data/user/0/' + PACKAGE).strip()
        require(uid.isdigit() and int(uid) >= 10000, 'NORMAL_APPLICATION_UID')
        device.shell('chown', '-R', uid + ':' + uid, '/data/media/0/Android/data/' + PACKAGE)
        device.shell('restorecon', '-RF', '/data/media/0/Android/data/' + PACKAGE)
        device.adb('forward', 'tcp:19090', 'tcp:9090')
        reader = start_lifecycle_log(device, out)
        seen = set()
        whole_deadline = time.monotonic() + 850
        for cycle in (1, 2, 3):
            require(time.monotonic() < whole_deadline, 'TOTAL_STARTUP_QUALIFICATION_DEADLINE')
            if cycle > 1:
                save(out / ('installed80-before-start-' + str(cycle) + '.json'), installed_hashes(device, proof))
                crash_free_alive(device)
                old = (device.pid, device.start_time)
                device.shell('am', 'force-stop', PACKAGE)
                require(not device.pids(), 'EXPLICIT_STARTUP_RESET_STOPPED_PREVIOUS_NATIVE_PROCESS')
                report['starts'][-1]['explicit_next_start_reset'] = dict(previous_pid=old[0], previous_start=old[1], data_cleared=False)
            started = time.monotonic()
            record = start_once(device, cycle, out)
            identity = (record['pid'], record['process_start'])
            require(identity not in seen, 'THREE_GENUINE_DISTINCT_PROCESS_STARTS')
            seen.add(identity)
            save(out / ('installed80-after-start-' + str(cycle) + '.json'), installed_hashes(device, proof))
            device.screenshot('start-' + str(cycle) + '-home')
            require(device.rpc('Input.Home') == 'OK', 'REAL_GUI_HOME_INPUT_ACKNOWLEDGED')
            stable_started = time.monotonic()
            observations = []
            while time.monotonic() - stable_started < 45:
                crash_free_alive(device)
                require(device.rpc('JSONRPC.Ping') == 'pong', 'REAL_BOUNDED_PING_DURING_STABILITY')
                gui = device.rpc('GUI.GetProperties', dict(properties=['currentwindow', 'currentcontrol', 'skin']))
                require(gui.get('currentwindow', {}).get('id') == 10000 and gui.get('skin', {}).get('id') == 'skin.infinity.diggz', 'UNCHANGED_INFINITY_HOME_REMAINS_RESPONSIVE')
                crash_free_alive(device)
                observations.append(dict(elapsed=time.monotonic() - stable_started, gui=gui))
                time.sleep(2)
            device.alive()
            installed_apk(device)
            save(out / ('installed80-after-stability-' + str(cycle) + '.json'), installed_hashes(device, proof))
            crash_free_alive(device)
            record.update(stable_seconds=time.monotonic() - stable_started, startup_seconds=stable_started - started,
                          observations=observations, installed80_source_hashes_unchanged=True, actual_GUI_RPC_responsive=True)
            report['starts'].append(record)
            save(out / 'ANDROID-VERIFICATION.json', report)
        crash_free_alive(device)
        report['status'] = 'PASS_UNCHANGED69_STOCK_API36_THREE_STARTS_ONLY'
        code = 0
    except Exception as error:
        report.update(status='FAIL_UNCHANGED69_STOCK_API36_STARTUP_QUALIFICATION', error=repr(error), traceback=traceback.format_exc())
        if device:
            capture_failure(device, out)
    finally:
        if reader:
            report['lifecycle_capture'] = stop_lifecycle_log(reader, out)
        if device:
            report['measured_UI_actions'] = device.actions
        save(out / 'ANDROID-VERIFICATION.json', report)
        if device and disposer:
            disposer['arm_host_disposal'](device, out)
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    p = modes.add_parser('admit')
    p.add_argument('--request', type=Path, default=REQUEST)
    p.add_argument('--sdk', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p = modes.add_parser('run')
    p.add_argument('--request', type=Path, default=REQUEST)
    p.add_argument('--admission', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--avd', default=AVD)
    args = vars(parser.parse_args())
    mode = args.pop('mode')
    if mode == 'admit':
        args['sdk'] = args['sdk'] or Path(os.environ['ANDROID_HOME']) / 'build-tools/35.0.0'
        admit(**args)
    else:
        raise SystemExit(run(**args))
