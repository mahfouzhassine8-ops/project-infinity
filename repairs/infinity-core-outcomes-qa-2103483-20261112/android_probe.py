#!/usr/bin/env python3
"""Pre-sign diagnostic: unchanged signed83 APK, replaced engine on disposable VM.

This is not APK installation acceptance. No Core path repair, success activation,
shutdown, service disablement, owner-device access, or substitute signer.
"""
import argparse
import ast
import codecs
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import sys
import time
import traceback
import uuid
from urllib.parse import parse_qs, urlsplit
from zipfile import ZipFile, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BRANCH = 'work/infinity-core-outcomes-qa-20261112'
FEATURE = 'core-outcomes-native-qa'
CONTROL_FEATURE = 'core-outcomes-baseline-startup'
SELECTION = HERE / 'ANDROID-SELECTION.json'
APK_SHA = '0c597a2976d9667796a4baac18ed9b624960e22399c94c9f62b1a52393d43236'
OLD_NATIVE = 'f14ff78865158337eb6fd19dfe549912d57f2a6a912e5b3440ed28880ee0cb0c'
CORE = 'service.adulthideout.core'
CORE_SOURCE = '2e1b79adc352129696ccfa48a3b5b16f85ebf812026fdd26c3e55d67f34b43b3'
CORE_BINARY = 'c4a8a8d1e046cab6a42934b8fba31246efb21a002a90beb2bffa555623a383a9'
PUBLISHER = '6d38cce274bb45e2b658a63dd44a01e94c8ae990'
QA = 'script.infinity.coreoutcomesqa'
sys.path.insert(0, str(ROOT / 'repairs/infinity-tracking-integration-2103469-20261108'))
import qualify_android_baseline as base
import verify_tracking_android as gui
QP = base.PROFILE + '/addon_data/' + QA
REMOTE = '/sdcard/Download/infinity-core-outcomes-qa/'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def selected():
    row = base.load(SELECTION)
    require(row.get('enabled') is True and row.get('application_tests') is True,
            'ANDROID_SELECTION_DISABLED_PENDING_COMPLETED_NATIVE_PROOF')
    require(row['feature'] == FEATURE and row['branch'] == BRANCH and
            row['baseline_APK_sha256'] == APK_SHA and row['baseline_native_sha256'] == OLD_NATIVE,
            'EXACT_ORIGINAL83_SCOPE')
    require(row['native_injection'] is True and row['APK_modified'] is False and
            row['before_first_launch'] is True and row['owner_device'] is False and
            row['shutdown_tests'] is False and row['Core_path_correction'] is False,
            'DISPOSABLE_PRELAUNCH_DIAGNOSTIC_ONLY')
    require(re.fullmatch('[0-9a-f]{64}', row['native']['native_sha256'] or '') and
            row['native']['native_sha256'] != OLD_NATIVE, 'FROZEN_NEW_NATIVE_REQUIRED')
    require(row['source_bindings'], 'SOURCE_BOUND_SELECTION_REQUIRED')
    for name, wanted in row['source_bindings'].items():
        path = ROOT / name
        require(path.resolve().is_relative_to(ROOT) and sha(path) == wanted, 'SOURCE_BINDING:' + name)
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        require(os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
                os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH and
                (os.environ.get('SELECTED_FEATURE') == FEATURE or
                 (os.environ.get('SELECTED_FEATURE') == CONTROL_FEATURE and
                  row.get('allow_matched_baseline_control') is True)), 'EXACT_MANUAL_CI_ROUTE')
        require(re.fullmatch('[0-9a-f]{40}', os.environ.get('SELECTED_SOURCE', '')) and
                subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() ==
                os.environ['SELECTED_SOURCE'], 'EXACT_CHECKED_OUT_TEST_SOURCE')
    return row


# Reuse only the frozen bounded Device class, never the performance runner.
transport = ROOT / 'repairs/infinity-performance-ui-2103477-20261110/baseline.py'
tree = ast.parse(transport.read_text())
node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Device')
exec(compile(ast.Module(body=[node], type_ignores=[]), str(transport), 'exec'), globals())
RetainedDevice = Device


class Device(RetainedDevice):
    METHODS = RetainedDevice.METHODS | {'Addons.SetAddonEnabled', 'Files.GetDirectory'}

    def rpc(self, method, params=None, timeout=5):
        if method == 'Addons.SetAddonEnabled':
            require(params in [dict(addonid=n, enabled=True) for n in
                               (CORE, 'script.kodihealthcenter')], 'ONLY_NORMAL_SELECTED_ENABLE')
        if method == 'Files.GetDirectory':
            require(params == dict(directory='plugin://script.infinity.commandcenter/?action=commands',
                                   media='files'), 'ONLY_EXISTING_LOCAL_CC_COMMANDS')
        return super().rpc(method, params, timeout)

    def alive(self):
        super().alive()
        reader = getattr(self, 'core_reader', None)
        if reader is not None:
            require(reader.poll() is None, 'DIRECT_NATIVE_DIAGNOSTIC_READER_STOPPED')
        path = getattr(self, 'core_log', None)
        if path:
            rows = events(path, self.pid)
            reject_success(rows)


def api(path):
    return json.loads(subprocess.check_output(
        ['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/' + path], text=True, timeout=45))


def artifact(pin, out):
    require(all(pin.get(k) is not None for k in ('run_id', 'artifact_id', 'workflow_id',
            'workflow_path', 'source', 'name', 'sha256', 'size_in_bytes')), 'UNBOUND_ARTIFACT')
    run = api('actions/runs/' + str(pin['run_id']))
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and
            run['workflow_id'] == pin['workflow_id'] and run['path'] == pin['workflow_path'] and
            run['head_sha'] == pin['source'], 'COMPLETED_EXACT_PRODUCER_REQUIRED')
    row = api('actions/artifacts/' + str(pin['artifact_id']))
    require(not row['expired'] and row['workflow_run']['id'] == pin['run_id'] and
            row['name'] == pin['name'] and row['digest'] == 'sha256:' + pin['sha256'] and
            row['size_in_bytes'] == pin['size_in_bytes'], 'EXACT_ARTIFACT_API_IDENTITY')
    out.mkdir(parents=True, exist_ok=False)
    archive = out / 'artifact.zip'
    with archive.open('wb') as stream:
        subprocess.run(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/' +
                        str(pin['artifact_id']) + '/zip'], stdout=stream, check=True, timeout=300)
    require(sha(archive) == pin['sha256'] and archive.stat().st_size == pin['size_in_bytes'],
            'WHOLE_ARTIFACT_ZIP_DIGEST_AND_SIZE')
    with ZipFile(archive) as zip:
        names = zip.namelist()
        require(len(names) == len(set(names)) and len(names) <= 20000 and
                sum(i.file_size for i in zip.infolist()) <= 2 * 1024**3, 'BOUNDED_UNIQUE_ARTIFACT')
        for item in zip.infolist():
            p = Path(item.filename)
            require(not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename and
                    '\0' not in item.filename and not stat.S_ISLNK(item.external_attr >> 16), 'SAFE_ARTIFACT_PATH')
        zip.extractall(out / 'files')
    base.save(out / 'API-PROVENANCE.json', dict(run=run, artifact=row, zip_sha256=sha(archive)))
    return out / 'files'


def one(root, name):
    matches = list(root.rglob(name))
    require(len(matches) == 1, 'UNIQUE_INPUT:' + name)
    return matches[0]


def fetch(out):
    row = selected()
    require(not out.exists(), 'FRESH_INTAKE')
    baseline = artifact(row['baseline'], out / 'baseline')
    native = artifact(row['native'], out / 'native')
    apk = one(baseline, 'Infinity-2103483-Combined-Original-Signer.apk')
    library = one(native, 'libkodi.so')
    proof = base.load(one(native, 'CORE-OUTCOMES-ARM64.json'))
    require(sha(apk) == APK_SHA and sha(library) == row['native']['native_sha256'], 'EXACT_APK_AND_ENGINE')
    require(proof['status'] == 'PASS_FULL_ARM64_CORE_OUTCOMES_LINK_AND_BASELINE_ABI' and
            proof['source_commit'] == row['native']['source'] and proof['native_sha256'] == sha(library) and
            proof['baseline83_native_sha256'] == OLD_NATIVE and proof['diagnostic_only'] is True and
            proof['Core_path_correction_activated'] is False and proof['signed'] is False,
            'ACTUAL_COMPLETED_ARM64_SOURCE_ABI_PROOF')
    protected = ['observer.py', 'native', 'make_overlay.py', 'build_native.py', 'NATIVE-BINDINGS.json']
    require(not subprocess.check_output(['git', 'diff', '--name-only', row['native']['source'], 'HEAD', '--',
            *[str(HERE.relative_to(ROOT) / n) for n in protected]], text=True).strip(),
            'CURRENT_DIAGNOSTIC_SOURCE_DIFFERS_FROM_COMPLETED_NATIVE_PRODUCER')
    with ZipFile(apk) as zip:
        require(hashlib.sha256(zip.read('lib/arm64-v8a/libkodi.so')).hexdigest() == OLD_NATIVE,
                'ORIGINAL83_NATIVE_PREIMAGE')
        require(not any(n.startswith('assets/addons/' + CORE + '/') for n in zip.namelist()),
                'CORE_NOT_PACKAGED_IN_BASE83')
    fixture = out / 'publisher'; fixture.mkdir()
    require(row['publisher']['commit'] == PUBLISHER, 'EXACT_REVIEWED_PUBLISHER_COMMIT')
    for item in row['publisher']['files']:
        require(item['url'].startswith('https://raw.githubusercontent.com/Vashiel/repository.adulthideout/' +
                row['publisher']['commit'] + '/'), 'PINNED_PUBLISHER_URL')
        target = fixture / item['name']
        require(target.parent == fixture, 'FLAT_PUBLISHER_INPUT')
        import urllib.request
        with urllib.request.urlopen(item['url'], timeout=45) as response:
            data = response.read(item['size'] + 1)
        require(len(data) == item['size'] and hashlib.sha256(data).hexdigest() == item['sha256'],
                'UNMODIFIED_PUBLISHER_BYTES:' + item['name'])
        target.write_bytes(data)
    require(sha(fixture / 'service.py') == CORE_SOURCE and
            sha(fixture / 'libadulthideout_core.so') == CORE_BINARY, 'EXACT_CORE_SOURCE_AND_BINARY')
    base.save(out / 'FETCH.json', dict(status='PASS_AUTHENTICATED_PRE_SIGN_INPUTS_NOT_APPLICATION_TEST',
        apk=str(apk.resolve()), native=str(library.resolve()), publisher=str(fixture.resolve()),
        selection_sha256=sha(SELECTION), native_source=row['native']['source']))


OBSERVER = r'''
import hashlib,json,os,time
import xbmc,xbmcaddon,xbmcgui,xbmcvfs
def require(v,m):
    if not v:raise RuntimeError(m)
root=xbmcvfs.translatePath('special://profile/addon_data/script.infinity.coreoutcomesqa/')
with open(root+'request.json') as stream:r=json.load(stream)
with open('/proc/self/stat') as stream:started=stream.read().rsplit(') ',1)[1].split()[19]
require(r['pid']==os.getpid() and r['process_start']==started,'ACTUAL_PROCESS_REQUEST')
out=dict(pid=os.getpid(),process_start=started,nonce=r['nonce'],sequence=r['sequence'],action=r['action'],passed=False)
if r['action']=='local-python':
    out.update(passed=True,arithmetic=sum([1,2,3]))
elif r['action']=='health-center':
    path=xbmcvfs.translatePath(xbmcaddon.Addon('script.kodihealthcenter').getAddonInfo('path'))
    for name,wanted in r['health_sources'].items():
        with open(os.path.join(path,name),'rb') as stream:actual=hashlib.sha256(stream.read()).hexdigest()
        require(actual==wanted,'EXACT_HEALTH_CENTER_SOURCE')
    require(not xbmc.getCondVisibility('Window.IsVisible(1188)'),'HEALTH_INITIAL_ABSENT')
    xbmc.executebuiltin('RunScript(script.kodihealthcenter)')
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
        if xbmcgui.getCurrentWindowDialogId()==11188 and xbmcgui.Window(10000).getProperty('KHC.Version')=='2.5.26':
            owner=xbmcgui.Window(11188);control=owner.getControl(1188101)
            require(isinstance(control,xbmcgui.ControlButton),'HEALTH_BUTTON_TYPE')
            label=control.getLabel()
            require(label=='Scan Kodi' and xbmcgui.getCurrentWindowDialogId()==11188,'REAL_HEALTH_CONTROL')
            out.update(passed=True,label=label,dialog=11188);break
        xbmc.sleep(100)
else:raise RuntimeError('UNSELECTED_ACTION')
with open(root+'reply.pending','w') as stream:json.dump(out,stream)
os.replace(root+'reply.pending',root+'reply.json')
'''


def stage(inputs, sdk):
    row = selected(); proof = base.load(inputs / 'FETCH.json')
    require(proof['selection_sha256'] == sha(SELECTION), 'CURRENT_INPUT_SELECTION')
    apk = Path(proof['apk'])
    require(sha(apk) == APK_SHA and sha(Path(proof['native'])) == row['native']['native_sha256'], 'INPUTS_UNCHANGED')
    signature = base.command([sdk / 'build-tools/35.0.0/apksigner', 'verify', '--verbose', '--print-certs', apk], timeout=60)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [base.CERT], 'ORIGINAL_CERTIFICATE')
    for scheme in ('v1', 'v2', 'v3'):
        require(any(line.startswith('Verified using ' + scheme + ' scheme') and line.endswith(': true')
                    for line in signature.splitlines()), 'ORIGINAL_SIGNATURE_' + scheme)
    (inputs / 'ORIGINAL-SIGNATURE.txt').write_text(signature)
    qa = inputs / 'core-outcomes-observer.zip'
    with ZipFile(qa, 'x', ZIP_DEFLATED) as zip:
        zip.writestr(QA + '/addon.xml', '<addon id="' + QA + '" name="Internal Core outcomes observer" version="1.0.0" provider-name="Infinity QA"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/></addon>')
        zip.writestr(QA + '/default.py', OBSERVER)
    core = inputs / 'service.adulthideout.core-1.0.2.zip'
    with ZipFile(core, 'x', ZIP_DEFLATED) as zip:
        for name in ('addon.xml', 'service.py'):
            zip.write(Path(proof['publisher']) / name, CORE + '/' + name)
        zip.write(Path(proof['publisher']) / 'libadulthideout_core.so', CORE + '/bin/android-arm64-v8a/libadulthideout_core.so')
        zip.writestr(CORE + '/bin/android-arm64-v8a/version.txt', '1.0.1\n')
    if os.environ.get('SELECTED_FEATURE') == CONTROL_FEATURE:
        control = inputs / 'exact83-control-libkodi.so'
        with ZipFile(apk) as archive, archive.open('lib/arm64-v8a/libkodi.so') as src, control.open('xb') as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
        require(sha(control) == OLD_NATIVE, 'EXACT_ORIGINAL83_CONTROL_ENGINE')
        proof['control_native'] = str(control.resolve())
    health = {}
    with ZipFile(apk) as zip:
        for name in ('default.py', 'khc_contracts.py'):
            health[name] = hashlib.sha256(zip.read('assets/addons/script.kodihealthcenter/' + name)).hexdigest()
    proof.update(status='PASS_STAGED_PRE_SIGN_DIAGNOSTIC_INPUTS', health_sources=health,
        qa=dict(addon=QA, version='1.0.0', archive=qa.name, sha256=sha(qa)),
        core=dict(addon=CORE, version='1.0.2', archive=core.name, sha256=sha(core)))
    base.save(inputs / 'INTAKE.json', proof)


def events(path, pid):
    if not path.exists():
        return []
    require(path.stat().st_size <= 8 * 1024**2, 'BOUNDED_NATIVE_DIAGNOSTIC_LOG')
    rows = []
    for line in path.read_text(errors='replace').splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue  # logcat headers/partial last line are retained raw.
        if row.get('native_pid') == pid and isinstance(row.get('data'), dict):
            rows.append(row)
    return rows


def reject_success(rows):
    require(not any(r['data'].get('event') == 'core.load.returned' or
            (r['data'].get('event') == 'core.maps' and
             (r['data'].get('map_entries', 0) > 0 or r['data'].get('executable_mapping') is True)) or
            (r['data'].get('event', '').startswith('native_call.') and
             r['data'].get('symbol') == 'start_core_service') for r in rows),
            'UNEXPECTED_CORE_SUCCESS_OR_REAL_NATIVE_START_ABORT_REMAINING_DIAGNOSTIC')


def outcome(rows):
    reject_success(rows)
    for first in rows:
        data = first['data']; invoker = first.get('invoker')
        if data.get('event') != 'coverage.begin' or data.get('actor') != 'core_service' or data.get('source_sha') != CORE_SOURCE:
            continue
        require(type(invoker) is int and invoker >= 0, 'ACTUAL_CORE_INVOKER_ID')
        owned = [r['data'] for r in rows if r.get('invoker') == invoker]
        if not any(r.get('event') == 'coverage.installed' and r.get('actor') == 'core_service' for r in owned):
            continue
        require(not any(r.get('event') in ('coverage.disabled', 'coverage.limit', 'coverage.code_mismatch',
                    'coverage.trace_error', 'coverage.trace_unavailable', 'coverage.inspect_failed',
                    'coverage.record_too_large') for r in owned), 'CORE_OBSERVER_COVERAGE_INCOMPLETE')
        begins = [r for r in owned if r.get('actor') == 'core_service' and r.get('event') == 'operation.begin']
        terminals = [r for r in owned if r.get('actor') == 'core_service' and
                     r.get('event') in ('operation.return', 'operation.error')]
        paired = [dict(begin=b, end=t) for b in begins for t in terminals
                  if b.get('ticket') == t.get('ticket') and b.get('operation') == t.get('operation')]
        if not any(p['begin']['operation'] == 'copy2' for p in paired) or not any(
                p['begin']['operation'] in ('chmod', 'utime', 'setxattr') for p in paired):
            continue
        for i, begin in enumerate(owned):
            if begin.get('event') != 'core.load.begin':
                continue
            target = begin.get('target', '')
            require(target.endswith('/.kodi/temp/libadulthideout_core.so') and
                    target.startswith(('/storage/emulated/0/Android/data/' + base.PACKAGE + '/',
                                       '/sdcard/Android/data/' + base.PACKAGE + '/')),
                    'ORIGINAL_EXTERNAL_TEMP_CORE_LOAD_PATH_REQUIRED')
            for j in range(i + 1, len(owned)):
                failed = owned[j]
                if failed.get('event') == 'core.load.error' and failed.get('ticket') == begin['ticket']:
                    require(failed.get('namespace_rejected') is True, 'EXPECTED_NAMESPACE_REJECTION_REQUIRED')
                    maps = next((r for r in owned[j + 1:] if r.get('event') == 'core.maps' and
                                 r.get('moment') == 'load_error'), None)
                    if maps is None:
                        continue
                    require(type(maps.get('complete')) is bool and maps.get('map_entries') == 0 and
                            maps.get('executable_mapping') is False and maps.get('chunk_limit') == 4096 and
                            type(maps.get('buffer_chunks_scanned')) is int and
                            0 <= maps['buffer_chunks_scanned'] <= 4096 and
                            all(type(maps.get(key)) is bool for key in
                                ('limit_reached', 'line_truncated', 'open_succeeded', 'read_failed')),
                            'BOUNDED_EXPLICIT_OWN_PROCESS_MAP_OBSERVATION_REQUIRED')
                    unavailable = (not maps['open_succeeded'] or maps['limit_reached'] or
                                   maps['line_truncated'] or maps['read_failed'])
                    require(maps['complete'] is not unavailable, 'INCONSISTENT_MAP_VISIBILITY')
                    return dict(status='PASS_OBSERVED_ORIGINAL_CORE_NAMESPACE_FAILURE_NOT_CORE_SUCCESS',
                                invoker=invoker, coverage=first, operations=paired,
                                load_begin=begin, load_error=failed, own_process_maps=maps,
                                own_process_maps_visibility=('COMPLETE_BOUNDED_SNAPSHOT_NOT_WORKER_PROOF'
                                    if maps['complete'] else 'NOT_VERIFIED_INCOMPLETE_SNAPSHOT'),
                                native_worker_absence='NOT_ESTABLISHED', native_drain='UNVERIFIED')
    return None


def enable(device, addon):
    before = device.rpc('Addons.GetAddonDetails', dict(addonid=addon, properties=['version', 'enabled']))['addon']
    if before['enabled'] is False:
        require(device.rpc('Addons.SetAddonEnabled', dict(addonid=addon, enabled=True)) == 'OK', 'NORMAL_ENABLE')
    after = device.rpc('Addons.GetAddonDetails', dict(addonid=addon, properties=['version', 'enabled']))['addon']
    require(after['enabled'] is True, 'SELECTED_SERVICE_NOT_ENABLED')
    return dict(before=before, after=after)


def invoke(device, inputs, out, action, sequence, nonce):
    request = dict(pid=device.pid, process_start=device.start_time, nonce=nonce, sequence=sequence,
                   action=action, health_sources=inputs['health_sources'])
    path = out / 'request.json'; base.save(path, request)
    device.adb('push', path, QP + '/request.pending'); device.shell('mv', QP + '/request.pending', QP + '/request.json')
    device.rpc('Addons.ExecuteAddon', dict(addonid=QA))
    deadline = time.monotonic() + 50
    while time.monotonic() < deadline:
        device.alive()
        try:
            reply = json.loads(device.shell('head', '-c', '65536', QP + '/reply.json', check=False))
        except ValueError:
            reply = {}
        if all(reply.get(k) == request[k] for k in ('pid', 'process_start', 'nonce', 'sequence', 'action')):
            base.save(out / ('case-%d-%s.json' % (sequence, action)), reply)
            require(reply.get('passed') is True, 'ACTUAL_LOCAL_FUNCTIONAL_CASE:' + action)
            if action == 'local-python':
                require(reply.get('arithmetic') == 6, 'ACTUAL_LOCAL_PYTHON_RESULT')
            return reply
        time.sleep(.2)
    raise TimeoutError('ACTUAL_OBSERVER_REPLY:' + action)


def native_package_layout(installed, dump):
    """Parse only credential-free native fields; PM's APK owns the search root.

    API36 AOSP Settings.dumpPackageLPr prints legacyNativeLibraryDir. For a
    cluster install PackageAbiHelperImpl derives codePath/lib/<instruction-set>.
    A printed directory may therefore be the root or the ISA leaf, not a file.
    """
    require(re.fullmatch(r'/data/app/[A-Za-z0-9_./+=~-]+/base\.apk', installed) and
            all(part not in ('.', '..', '') for part in installed.split('/')[1:]),
            'EXACT_PM_OWNED_BASE_APK_PATH')
    package_root = str(Path(installed).parent)
    require(Path(package_root).name.startswith(base.PACKAGE + '-'), 'PM_PACKAGE_DIRECTORY_IDENTITY')
    library_root = package_root + '/lib'
    names = ('nativeLibraryDir', 'legacyNativeLibraryDir', 'nativeLibraryRootDir',
             'secondaryNativeLibraryDir', 'primaryCpuAbi', 'secondaryCpuAbi', 'extractNativeLibs')
    fields = []
    for name, value in re.findall(r'^\s*(' + '|'.join(names) + r')=([^\r\n]*)$', dump, re.M):
        value = value.strip()
        if name.endswith('Dir') and value != 'null':
            require(re.fullmatch(r'/data/app/[A-Za-z0-9_./+=~-]+', value) and
                    all(part not in ('.', '..', '') for part in value.split('/')[1:]) and
                    (value == library_root or str(Path(value).parent) == library_root),
                    'NATIVE_DIRECTORY_OUTSIDE_EXACT_PACKAGE_LIB_ROOT')
        elif name in ('primaryCpuAbi', 'secondaryCpuAbi'):
            require(value in ('null', 'arm64-v8a', 'armeabi-v7a', 'x86_64', 'x86'), 'UNRECOGNIZED_PACKAGE_ABI')
        elif name == 'extractNativeLibs':
            require(value in ('true', 'false'), 'UNRECOGNIZED_EXTRACTION_FIELD')
        fields.append(dict(name=name, value=value))
    return dict(package_root=package_root, library_root=library_root, fields=fields)


def discover_native(device, installed, out):
    evidence = dict(status='NATIVE_DISCOVERY_PENDING', pm_apk_path=installed,
                    package=base.PACKAGE, full_package_dump_saved=False,
                    contract='API36 codePath/lib root or ISA leaf; no global native-directory search',
                    native_fields=[], candidates=[])
    try:
        dump = device.shell('dumpsys', 'package', base.PACKAGE)
        # Save only these safe PM fields even if layout validation subsequently
        # rejects them; exclude permissions, account names, URLs and other dump.
        for match in re.finditer(r'^\s*(nativeLibraryDir|legacyNativeLibraryDir|nativeLibraryRootDir|secondaryNativeLibraryDir|primaryCpuAbi|secondaryCpuAbi|extractNativeLibs)=([^\r\n]*)$', dump, re.M):
            value = match.group(2).strip()
            safe = bool(re.fullmatch(r'[A-Za-z0-9_./+=~:-]{1,512}', value))
            evidence['native_fields'].append(dict(name=match.group(1), value=value if safe else '<unsafe-value-rejected>'))
        base.save(out / 'PACKAGE-NATIVE-DISCOVERY.json', evidence)
        layout = native_package_layout(installed, dump)
        evidence.update(package_root=layout['package_root'], library_root=layout['library_root'])
        for path in (installed, layout['package_root'], layout['library_root']):
            actual = device.shell('readlink', '-f', path).strip()
            require(actual == path, 'CANONICAL_PM_PACKAGE_PATH_ONLY')
        for field in layout['fields']:
            if field['name'].endswith('Dir') and field['value'] != 'null':
                require(device.shell('readlink', '-f', field['value']).strip() == field['value'],
                        'CANONICAL_PRINTED_NATIVE_DIRECTORY_ONLY')
        # No -L: never follow directory symlinks. Depth2 includes lib itself and
        # actual ISA child directories. The preimage hash selects no foreign ABI.
        raw = device.shell('find', layout['library_root'], '-maxdepth', '2', '-name', 'libkodi.so', '-print')
        require(len(raw.encode()) <= 4096, 'BOUNDED_PACKAGE_NATIVE_CANDIDATES')
        candidates = [line for line in raw.splitlines() if line]
        evidence['candidates'] = candidates
        require(len(candidates) == 1, 'UNIQUE_PACKAGE_NATIVE_LIBRARY_FILE')
        target = candidates[0]
        require(target.endswith('/libkodi.so') and
                (str(Path(target).parent) == layout['library_root'] or
                 str(Path(target).parent.parent) == layout['library_root']), 'NATIVE_CANDIDATE_SCOPE')
        info = dict(path=target, kind=device.shell('stat', '-c', '%F', target).strip(),
                    canonical=device.shell('readlink', '-f', target).strip())
        evidence['candidate_identity'] = info
        require(info['kind'] == 'regular file' and info['canonical'] == target, 'REGULAR_OWNED_NATIVE_FILE_ONLY')
        digest = device.shell('sha256sum', target).split()
        require(len(digest) == 2 and digest[1] == target and digest[0] == OLD_NATIVE,
                'EXACT_INSTALLED_ORIGINAL_ENGINE')
        info['sha256'] = digest[0]
        evidence['status'] = 'PASS_UNIQUE_CANONICAL_ORIGINAL83_NATIVE_DISCOVERY'
        return target
    except Exception as error:
        evidence.update(status='BLOCKED_NATIVE_DISCOVERY_NO_INJECTION', error=str(error))
        raise
    finally:
        base.save(out / 'PACKAGE-NATIVE-DISCOVERY.json', evidence)


def matching_crash(text, pid, uid):
    """Strict identity from the Android tombstone, never a log substring."""
    commands = re.findall(r'^Cmdline:\s*([^\r\n]+)$', text, re.M)
    identities = re.findall(r'^pid:\s*(\d+),\s*tid:\s*\d+,.*?>>>\s*([^<>\r\n]+?)\s*<<<', text, re.M)
    users = re.findall(r'^uid:\s*(\d+)\s*$', text, re.M)
    return (bool(commands and identities and users) and
            all(command.strip() == base.PACKAGE + ':kodi' for command in commands) and
            all(int(number) == pid and name.strip() == base.PACKAGE + ':kodi'
                for number, name in identities) and all(int(number) == uid for number in users))


def symbolize_crash(text, library, expected_sha, sdk, destination, deadline):
    result = dict(status='NOT_RUN_NO_AVAILABLE_LLVM_ADDR2LINE', diagnostic_only=True,
                  native_sha256=expected_sha)
    tools = [sdk / 'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-addr2line']
    available = shutil.which('llvm-addr2line')
    if available:
        tools.append(Path(available))
    tool = next((path for path in tools if path.is_file() and os.access(path, os.X_OK)), None)
    if tool is None:
        return result
    if not library.is_file() or sha(library) != expected_sha:
        return dict(status='REFUSED_NATIVE_BINARY_IDENTITY_MISMATCH', diagnostic_only=True)
    frames = []
    for line in text.splitlines():
        match = re.match(r'^\s*#(\d+)\s+pc\s+([0-9a-fA-F]{1,16})\s+(\S*libkodi\.so)(?:\s|$)', line)
        if match and match.group(3) == destination:
            frames.append(dict(frame=int(match.group(1)), relative_pc='0x' + match.group(2),
                               module=match.group(3), original_line=line))
    if not frames:
        return dict(status='NOT_RUN_NO_FRAMES_FOR_EXACT_INJECTED_KODI_PATH', diagnostic_only=True,
                    native_sha256=expected_sha)
    if time.monotonic() >= deadline:
        return dict(status='NOT_RUN_DIAGNOSTIC_BUDGET_EXHAUSTED', diagnostic_only=True)
    result.update(tool=str(tool), tool_sha256=sha(tool), frames=frames[:64], frame_limit=64)
    try:
        version = subprocess.run([str(tool), '--version'], capture_output=True, text=True,
                                 timeout=min(2, max(.1, deadline - time.monotonic())))
        result['tool_version'] = version.stdout[:2048]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            result['status'] = 'NOT_RUN_DIAGNOSTIC_BUDGET_EXHAUSTED'
            return result
        command = [str(tool), '-C', '-f', '-i', '-e', str(library)]
        command.extend(frame['relative_pc'] for frame in frames[:64])
        symbols = subprocess.run(command, capture_output=True, text=True, timeout=min(5, remaining))
        result.update(status='SYMBOLIZATION_COMPLETED' if symbols.returncode == 0 else 'SYMBOLIZER_ERROR',
                      returncode=symbols.returncode, symbols=symbols.stdout[:262144],
                      stderr=symbols.stderr[:2048], output_truncated=len(symbols.stdout) > 262144)
    except (OSError, subprocess.TimeoutExpired) as error:
        result.update(status='SYMBOLIZER_UNAVAILABLE_OR_TIMEOUT', error=type(error).__name__)
    return result


def collect_failure(device, out, environment, uid, library, expected_sha, sdk, destination):
    """Failure-only readback on the already-rooted, admitted disposable CI VM.

    No escalation, permission changes, app action, signal, restart or log clear.
    API36 tombstoned publishes tombstone_NN via linkat only after kCompletedDump
    (AOSP android-16.0.0_r1 debuggerd/tombstoned/tombstoned.cpp:431–466).
    """
    result = dict(status='NOT_RUN_ENVIRONMENT_OR_IDENTITY_NOT_ADMITTED', failure_only=True,
                  original_failure_unchanged=True, wait_budget_seconds=40,
                  tombstone_read_limit_bytes=4194304, retained_foreign_crashes=False)
    if not (os.environ.get('GITHUB_ACTIONS') == 'true' and
            os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
            os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH and
            environment.get('status') == 'PASS_STOCK_API36_ENVIRONMENT_INTAKE_ONLY' and
            environment.get('sdk') == 36 and environment.get('serial') == device.serial and
            re.fullmatch(r'emulator-\d+', device.serial) and
            type(device.pid) is int and device.pid > 0 and
            str(uid).isdigit() and 10000 <= int(uid) < 100000):
        return result
    began = time.monotonic(); deadline = began + 40
    result.update(status='WAITING_FOR_COMPLETED_MATCHING_NATIVE_TOMBSTONE', pid=device.pid, uid=int(uid),
                  cmdline=base.PACKAGE + ':kodi', candidates=[], captured_at_utc=time.time())
    names = ['/data/tombstones/tombstone_%02d' % i for i in range(32)]
    seen = set()

    def command(arguments, limit=4):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            return subprocess.run([str(device.adb_bin), '-s', device.serial, *arguments],
                                  capture_output=True, timeout=min(limit, remaining))
        except (OSError, subprocess.TimeoutExpired) as error:
            result['last_query_error'] = type(error).__name__
            return None

    # Capture all Android buffers for this app UID only; debuggerd's completed
    # text below supplies frames emitted under the system crash-dumper UID.
    logs = command(['logcat', '-b', 'all', '-d', '--uid=' + str(uid), '-v', 'threadtime', '-t', '4000'], 5)
    if logs is not None:
        result['uid_logcat'] = dict(returncode=logs.returncode, bytes=len(logs.stdout),
            retained_bytes=min(len(logs.stdout), 8 * 1024**2), truncated=len(logs.stdout) > 8 * 1024**2,
            stderr=logs.stderr.decode(errors='replace')[:2048])
        if logs.returncode == 0:
            (out / 'failure-app-uid-logcat.txt').write_bytes(logs.stdout[:8 * 1024**2])
    else:
        result['uid_logcat'] = dict(status='UNAVAILABLE_OR_TIMEOUT')
    while time.monotonic() < deadline:
        metadata = command(['shell', 'stat', '-c', '%n|%f|%s|%Y|%i', *names])
        if metadata is None:
            break
        error = metadata.stderr.decode(errors='replace')
        if 'Permission denied' in error or 'Operation not permitted' in error:
            result['tombstone_access_denied'] = True
        candidates = []
        for line in metadata.stdout.decode(errors='replace').splitlines():
            parts = line.split('|')
            if len(parts) != 5 or parts[0] not in names or not re.fullmatch(r'[0-9a-fA-F]+', parts[1]) or not all(p.isdigit() for p in parts[2:]):
                continue
            path, mode, size, mtime, inode = parts
            signature = tuple(parts)
            if signature in seen:
                continue
            seen.add(signature)
            observation = dict(path=path, size=int(size), mtime=int(mtime), inode=int(inode))
            result['candidates'].append(observation)
            if not stat.S_ISREG(int(mode, 16)):
                observation['status'] = 'NON_REGULAR_NOT_READ'
            elif int(size) == 0:
                observation['status'] = 'EMPTY_PUBLISHED_FILE'
            else:
                candidates.append((parts, observation))
        # Read only fixed, published text filenames; never .pb, temp files, or
        # a directory traversal. Foreign contents are inspected then discarded.
        for parts, observation in sorted(candidates, key=lambda item: int(item[0][3]), reverse=True):
            content = command(['exec-out', 'head', '-c', '4194304', parts[0]])
            if content is None:
                observation['status'] = 'READ_UNAVAILABLE_OR_TIMEOUT'
                break
            if content.returncode:
                observation['status'] = 'READ_FAILED'
                continue
            raw = content.stdout
            if len(raw) != min(int(parts[2]), 4194304) or len(raw) > 4194304:
                observation['status'] = 'SIZE_CHANGED_OR_TRUNCATED_NOT_RETAINED'
                continue
            text = raw.decode('utf-8', errors='replace')
            if not matching_crash(text, device.pid, int(uid)):
                observation['status'] = 'FOREIGN_OR_UNMATCHED_IDENTITY_NOT_RETAINED'
                continue
            confirm = command(['shell', 'stat', '-c', '%n|%f|%s|%Y|%i', parts[0]])
            if confirm is None or confirm.returncode or confirm.stdout.decode(errors='replace').strip() != '|'.join(parts):
                observation['status'] = 'FILE_REPLACED_DURING_READ_NOT_RETAINED'
                continue
            target = out / ('failure-own-' + Path(parts[0]).name + '.txt')
            target.write_bytes(raw)
            observation.update(status='MATCHED_OWN_COMPLETED_PUBLISHED_TOMBSTONE', local_file=target.name,
                               sha256=hashlib.sha256(raw).hexdigest(),
                               full_tombstone_captured=int(parts[2]) <= 4194304,
                               truncated=int(parts[2]) > 4194304)
            result.update(status='CAPTURED_MATCHING_COMPLETED_NATIVE_TOMBSTONE_TEXT',
                          tombstone=observation, publication_completion='API36_TOMBSTONED_KCOMPLETEDDUMP_THEN_LINKAT',
                          elapsed_seconds=time.monotonic() - began,
                          backtrace_lines=len(re.findall(r'^\s*#\d+\s+pc\s+', text, re.M)))
            result['symbolization'] = symbolize_crash(text, library, expected_sha, sdk, destination, deadline)
            result['elapsed_seconds'] = time.monotonic() - began
            return result
        if time.monotonic() < deadline:
            time.sleep(min(1, max(0, deadline - time.monotonic())))
    result.update(status='TOMBSTONE_ACCESS_DENIED' if result.get('tombstone_access_denied') else
                  'TIMED_OUT_NO_COMPLETED_MATCHING_TOMBSTONE', elapsed_seconds=time.monotonic() - began)
    return result


def run(inputs, sdk, out):
    control = os.environ.get('SELECTED_FEATURE') == CONTROL_FEATURE
    row = selected(); proof = base.load(inputs / 'INTAKE.json')
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and not out.exists(), 'CI_FRESH_OUTPUT_ONLY')
    require(proof['selection_sha256'] == sha(SELECTION) and sha(Path(proof['apk'])) == APK_SHA and
            sha(Path(proof['native'])) == row['native']['native_sha256'], 'EXACT_CURRENT_ADMITTED_INPUTS')
    for key in ('qa', 'core'):
        require(sha(inputs / proof[key]['archive']) == proof[key]['sha256'], 'STAGED_ZIP_UNCHANGED')
    expected_engine = OLD_NATIVE if control else row['native']['native_sha256']
    engine_path = Path(proof['control_native'] if control else proof['native'])
    require(sha(engine_path) == expected_engine, 'EXACT_SELECTED_ENGINE_BYTES')
    out.mkdir(parents=True)
    report = dict(status='RUNNING', native_injection=True, APK_modified=False, before_first_launch=True,
        owner_device=False, baseline_APK_sha256=APK_SHA, native_sha256=expected_engine,
        matched_baseline_control=control, original83_engine=control,
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), native_producer_source=proof['native_source'],
        APK_install_acceptance=False, Core_success_activated=False, shutdown='NOT_RUN', cases=[])
    device = reader = None
    uid = None
    destination = None
    def checkpoint(): base.save(out / 'ANDROID-CORE-OUTCOMES.json', report)
    try:
        device = Device(out, sdk); report['environment'] = base.environment(device, out)
        require(not device.shell('pm', 'list', 'packages', base.PACKAGE).strip(), 'NEW_DISPOSABLE_VM_ONLY')
        base.root_reconnect(device, out)
        require(device.adb('install', '--no-streaming', proof['apk'], timeout=300).strip().endswith('Success'), 'EXACT_ORIGINAL83_INSTALL')
        require(not device.pids() and not device.shell('pidof', base.PACKAGE, check=False).strip(), 'NO_FIRST_LAUNCH_YET')
        package_paths = device.shell('pm', 'path', base.PACKAGE).splitlines()
        require(len(package_paths) == 1 and package_paths[0].startswith('package:'), 'ONE_PM_BASE_APK')
        installed = package_paths[0].removeprefix('package:')
        require(device.shell('sha256sum', installed).split()[0] == APK_SHA, 'ACTUAL_UNCHANGED_APK_BYTES')
        destination = discover_native(device, installed, out)
        before = device.shell('stat', '-c', '%u:%g:%a:%C', destination).strip()
        staged = '/data/local/tmp/infinity-core-outcomes-libkodi.so'
        device.adb('push', engine_path, staged, timeout=300)
        require(device.shell('sha256sum', staged).split()[0] == expected_engine, 'PUSHED_ENGINE_SHA')
        device.shell('cp', staged, destination, timeout=120)
        require(device.shell('stat', '-c', '%u:%g:%a:%C', destination).strip() == before, 'NATIVE_FILE_OWNER_MODE_LABEL_PRESERVED')
        require(device.shell('sha256sum', destination).split()[0] == expected_engine, 'INJECTED_ENGINE_READBACK')
        require(device.shell('sha256sum', installed).split()[0] == APK_SHA and not device.pids(), 'APK_UNCHANGED_BEFORE_FIRST_LAUNCH')
        report['injection'] = dict(status='PASS_PRELAUNCH_NATIVE_INJECTION_NOT_APK_INSTALL_ACCEPTANCE',
                                   destination=destination, before=OLD_NATIVE, after=expected_engine)
        device.shell('mkdir', '-p', base.PROFILE, REMOTE, QP)
        settings = out / 'HARNESS_BOOTSTRAP-guisettings.xml'
        settings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting><setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>')
        sources = out / 'HARNESS_BOOTSTRAP-sources.xml'
        sources.write_text('<sources><files><source><name>Internal Core outcomes QA</name><path pathversion="1">' + REMOTE + '</path><allowsharing>false</allowsharing></source></files></sources>')
        device.adb('push', settings, base.PROFILE + '/guisettings.xml'); device.adb('push', sources, base.PROFILE + '/sources.xml')
        for key in ('qa', 'core'):
            device.adb('push', inputs / proof[key]['archive'], REMOTE + proof[key]['archive'])
        binary_dir = base.PROFILE + '/addon_data/' + CORE + '/bin/android-arm64-v8a'
        device.shell('mkdir', '-p', binary_dir)
        device.adb('push', Path(proof['publisher']) / 'libadulthideout_core.so', binary_dir + '/libadulthideout_core.so')
        version = out / 'FRESH-FIXTURE-version.txt'; version.write_text('1.0.1\n')
        device.adb('push', version, binary_dir + '/version.txt')
        require(device.shell('sha256sum', binary_dir + '/libadulthideout_core.so').split()[0] == CORE_BINARY,
                'SYNTHETIC_PRELAUNCH_CORE_BINARY_EXACT')
        uid = device.shell('stat', '-c', '%u', '/data/user/0/' + base.PACKAGE).strip()
        require(uid.isdigit(), 'ACTUAL_FRESH_VM_UID')
        device.shell('chown', '-R', uid + ':' + uid, '/data/media/0/Android/data/' + base.PACKAGE)
        device.shell('restorecon', '-RF', '/data/media/0/Android/data/' + base.PACKAGE)
        device.adb('forward', 'tcp:19090', 'tcp:9090')
        device.core_log = out / 'InfinityCoreQA.raw.log'
        with device.core_log.open('wb') as stream, (out / 'logcat.stderr').open('wb') as error:
            reader = subprocess.Popen(['timeout', '--signal=TERM', '--kill-after=2', '1200',
                str(device.adb_bin), '-s', device.serial, 'logcat', '-v', 'raw', '-s', 'InfinityCoreQA:I', '*:S'],
                stdout=stream, stderr=error, stdin=subprocess.DEVNULL, close_fds=True, start_new_session=True)
        device.core_reader = reader
        base.save(out / 'STAGING-IDENTITY.json', dict(status='PASS_PRELAUNCH_NATIVE_INJECTION_ONLY_NOT_APK_INSTALL_ACCEPTANCE',
            native_sha256=expected_engine, baseline_APK_sha256=APK_SHA,
            matched_baseline_control=control, native_injection=True, APK_modified=False, before_first_launch=True, owner_device=False,
            source_commit=report['source_commit'], native_producer_source=proof['native_source'],
            installed_native_path=destination, package_preservation_acceptance=False))
        report['startup'] = base.start_once(device, 1, out); checkpoint()
        require(device.shell('sha256sum', destination).split()[0] == expected_engine, 'RUNTIME_ENGINE_FILE_UNCHANGED')
        gui.install_zip(device, proof['qa'], dict(remote_zip_directory=REMOTE), out, 'local-observer')
        nonce = uuid.uuid4().hex
        report['cases'].append(invoke(device, proof, out, 'local-python', 1, nonce)); checkpoint()
        if control:
            require(not events(device.core_log, device.pid), 'ORIGINAL83_HAS_NO_CORE_DIAGNOSTIC_EVENTS')
            base.crash_free_alive(device)
            report['status'] = 'PASS_MATCHED_ORIGINAL83_STARTUP_CONTROL_ONLY_NOT_DIAGNOSTIC_ACCEPTANCE'
            checkpoint()
            return
        gui.install_zip(device, proof['core'], dict(remote_zip_directory=REMOTE), out, 'original-core-source')
        report['core_enable'] = enable(device, CORE); checkpoint()
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            device.alive(); observed = outcome(events(device.core_log, device.pid))
            if observed:
                report['core_outcome'] = observed; checkpoint(); break
            time.sleep(.2)
        else: raise TimeoutError('ORIGINAL_CORE_OUTCOME_COVERAGE_NOT_OBSERVED')
        report['health_enable'] = enable(device, 'script.kodihealthcenter')
        report['cases'].append(invoke(device, proof, out, 'health-center', 2, nonce)); checkpoint()
        device.screenshot('real-health-center'); device.rpc('Input.Back'); device.rpc('Input.Home')
        report['cases'].append(invoke(device, proof, out, 'local-python', 3, nonce)); checkpoint()
        listing = device.rpc('Files.GetDirectory', dict(directory='plugin://script.infinity.commandcenter/?action=commands', media='files'), timeout=25)
        files = listing.get('files', [])
        for label, key in [('Health Center', 'health-center'), ('Resume Hub', 'resume-hub')]:
            matches = [f for f in files if f.get('label') == label]
            require(len(matches) == 1, 'EXISTING_CC_COMMAND:' + key)
            route = urlsplit(matches[0]['file'])
            require(route.scheme == 'plugin' and route.netloc == base.CC and route.path == '/' and
                    parse_qs(route.query) == {'action': ['command'], 'command': [key]}, 'UNCHANGED_CC_ROUTE')
        report['command_center'] = dict(status='PASS_REAL_LOCAL_PLUGIN_EXECUTION', rows=files, activated=False)
        base.crash_free_alive(device)
        reject_success(events(device.core_log, device.pid))
        require(device.shell('sha256sum', installed).split()[0] == APK_SHA, 'FINAL_APK_BYTES_UNCHANGED')
        report['status'] = 'PASS_SELECTED_PRE_SIGN_ANDROID_CORE_OUTCOME_DIAGNOSTIC_ONLY'
    except Exception:
        report.update(status='BLOCKED_OR_FAILED_PRE_SIGN_DIAGNOSTIC', error=traceback.format_exc())
        raise
    finally:
        # Stop ONLY the host log reader. No application Quit/Close/force-stop.
        if reader:
            import signal
            try: os.killpg(reader.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: reader.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(reader.pid, signal.SIGKILL); reader.wait(timeout=3)
        if device:
            if report['status'] not in ('PASS_SELECTED_PRE_SIGN_ANDROID_CORE_OUTCOME_DIAGNOSTIC_ONLY',
                                       'PASS_MATCHED_ORIGINAL83_STARTUP_CONTROL_ONLY_NOT_DIAGNOSTIC_ACCEPTANCE'):
                try:
                    report['failure_diagnostics'] = collect_failure(device, out, report.get('environment', {}),
                        uid, engine_path, expected_engine, sdk, destination)
                    base.save(out / 'FAILURE-ONLY-DIAGNOSTICS.json', report['failure_diagnostics'])
                except Exception as error:
                    # Collection must never replace the original exception/status.
                    report['failure_collection_error'] = type(error).__name__ + ': ' + str(error)
            for name in ('kodi.log', 'kodi.old.log'):
                try: device.adb('pull', base.HOME + '/temp/' + name, out / name, check=False)
                except Exception: pass
            try: (out / 'crash.log').write_text(device.shell('logcat', '-b', 'crash', '-d', timeout=5))
            except Exception: pass
        checkpoint()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['gate', 'fetch', 'stage', 'run'])
    parser.add_argument('--inputs', type=Path); parser.add_argument('--sdk', type=Path); parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.operation == 'gate': selected()
    elif args.operation == 'fetch': fetch(args.out)
    elif args.operation == 'stage': stage(args.inputs, args.sdk)
    else: run(args.inputs, args.sdk, args.out)
