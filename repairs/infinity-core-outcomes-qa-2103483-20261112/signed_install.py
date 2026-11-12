#!/usr/bin/env python3
"""Selected ordinary signed83 -> signed84 install-over, synthetic data only.

No application launch, native injection, functional/Close/shutdown test, signer,
APK mutation, uninstall, downgrade, data clear, owner device or Fold acceptance.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
import traceback
import uuid
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SELECTION = HERE / 'SIGNED-INSTALL-SELECTION.json'
FEATURE = 'core-outcomes-signed-install'
BRANCH = 'work/infinity-core-outcomes-qa-20261112'
PACKAGE = 'com.projectinfinity.kodi'
APK83 = '0c597a2976d9667796a4baac18ed9b624960e22399c94c9f62b1a52393d43236'
NATIVE83 = 'f14ff78865158337eb6fd19dfe549912d57f2a6a912e5b3440ed28880ee0cb0c'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
PROBE = HERE / 'android_probe.py'
BASE = ROOT / 'repairs/infinity-tracking-integration-2103469-20261108/qualify_android_baseline.py'
WORKFLOW = ROOT / '.github/workflows/infinity-saved-navigation-android.yml'
TOOLING = HERE / 'prepare_ci_tooling.sh'
LIB = 'lib/arm64-v8a/libkodi.so'
CHANGES = {LIB, 'AndroidManifest.xml', 'assets/experience-component-updates.properties'}
BASELINE = dict(run_id=43119348510, artifact_id=13899912993, workflow_id=397702717,
                workflow_path='.github/workflows/infinity-combined-release.yml',
                source='3d9709bb1226a2ffa3a474cf04b3d3842b084611',
                name='Infinity2103483-OriginalSigned-Startup-Internal-QA-43119348510-FOLD-PENDING',
                sha256='df8aa2cd1ba52a83d0da60927bbd51e6fbc5de3808d4a9e2279e9eb759f820e7',
                size_in_bytes=328376479)


def require(value, label):
    if not value:
        raise RuntimeError(label)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def selected():
    row = json.loads(SELECTION.read_text())
    # This first check precedes helper imports, API calls, downloads and ADB.
    require(row.get('enabled') is True, 'SIGNED_INSTALL_DISABLED_PENDING_ACTUAL_ORIGINAL_SIGNED_PRODUCER')
    require(row['feature'] == FEATURE and row['branch'] == BRANCH and
            row['install_only'] is True and row['synthetic_data_only'] is True and
            all(row[k] is False for k in ('application_tests', 'shutdown_tests', 'native_injection', 'owner_device')),
            'EXACT_INSTALL_ONLY_SELECTION')
    require(row['baseline'] == BASELINE and row['baseline_APK_sha256'] == APK83 and
            row['baseline_native_sha256'] == NATIVE83 and row['candidate_versionCode'] == 2103484,
            'EXACT83_TO_PROVISIONAL84_ONLY')
    pin = row['candidate']
    require(set(pin) == set(BASELINE) and all(pin[k] is not None for k in pin) and
            pin['workflow_id'] == 397702717 and pin['workflow_path'] == BASELINE['workflow_path'] and
            re.fullmatch('[0-9a-f]{40}', pin['source']) and re.fullmatch('[0-9a-f]{64}', pin['sha256']) and
            all(type(pin[k]) is int and pin[k] > 0 for k in ('run_id', 'artifact_id', 'size_in_bytes')) and
            isinstance(pin['name'], str) and bool(pin['name']), 'ACTUAL_ORIGINAL397_SIGNED84_PRODUCER_REQUIRED')
    require(all(re.fullmatch('[0-9a-f]{64}', row[k] or '') for k in
                ('candidate_APK_sha256', 'candidate_native_sha256')) and
            row['candidate_APK_sha256'] != APK83 and row['candidate_native_sha256'] != NATIVE83,
            'EXACT_NEW_SIGNED_APK_AND_ENGINE')
    expected = {str(p.relative_to(ROOT)) for p in (Path(__file__), PROBE, BASE, WORKFLOW, TOOLING)}
    require(set(row['source_bindings']) == expected, 'EXACT_FIVE_SOURCE_BINDINGS')
    for name, digest in row['source_bindings'].items():
        path = ROOT / name
        require(path.resolve().is_relative_to(ROOT) and sha(path) == digest, 'SOURCE_BINDING:' + name)
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and
            os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
            os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH and
            os.environ.get('SELECTED_FEATURE') == FEATURE and bool(os.environ.get('AUTHORIZED_SCOPE', '').strip()),
            'EXPLICIT_MANUAL_CI_ONLY')
    require(re.fullmatch('[0-9a-f]{40}', os.environ.get('SELECTED_SOURCE', '')) and
            subprocess.check_output(['git', '-C', ROOT, 'rev-parse', 'HEAD'], text=True).strip() ==
            os.environ['SELECTED_SOURCE'] == os.environ.get('GITHUB_SHA'), 'EXACT_CHECKED_OUT_SOURCE')
    return row


def helpers():
    """Import base definitions and four read-only probe functions, never runners."""
    spec = importlib.util.spec_from_file_location('signed_install_retained_base', BASE)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    names = {'api', 'artifact', 'one', 'native_package_layout'}
    nodes = [n for n in ast.parse(PROBE.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes} == names, 'EXACT_REUSED_READONLY_HELPERS')
    scope = dict(base=base, require=require, sha=sha, subprocess=subprocess, json=json,
                 Path=Path, re=re, stat=stat, ZipFile=ZipFile)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(PROBE), 'exec'), scope)
    return base, scope


def fetch(out):
    row = selected()
    base, tools = helpers()
    require(not out.exists(), 'FRESH_INTAKE_REQUIRED')
    for role in ('baseline', 'candidate'):
        tools['artifact'](row[role], out / role)
    save(out / 'FETCH.json', dict(selection_sha256=sha(SELECTION), source=os.environ['SELECTED_SOURCE'],
                                  baseline=row['baseline'], candidate=row['candidate']))


def payload(archive):
    names = archive.namelist()
    require(len(names) == len(set(names)), 'UNIQUE_APK_MEMBERS')
    signatures = {'META-INF/MANIFEST.MF', 'META-INF/INFINITY.SF', 'META-INF/INFINITY.RSA'}
    hashes = {}
    for name in names:
        if name not in signatures:
            with archive.open(name) as stream:
                hashes[name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return hashes


def sdk_contract(badging):
    fields = {}
    for name in ('sdkVersion', 'targetSdkVersion'):
        lines = [line for line in badging.splitlines() if line.startswith(name + ':')]
        require(len(lines) == 1 and re.fullmatch(name + r":'[1-9][0-9]*'", lines[0]),
                'VALID_UNIQUE_ANDROID_SDK_BADGING_FIELD:' + name)
        fields[name] = lines[0]
    return fields


def stage(inputs, sdk):
    row = selected()
    base, tools = helpers()
    fetched = json.loads((inputs / 'FETCH.json').read_text())
    require(fetched['selection_sha256'] == sha(SELECTION) and fetched['source'] == os.environ['SELECTED_SOURCE'] and
            all(fetched[k] == row[k] for k in ('baseline', 'candidate')), 'UNCHANGED_AUTHENTICATED_INTAKE')
    paths, manifests, sdk_contracts = {}, {}, {}
    for role, version, apk_sha, native_sha in (
            ('baseline', 2103483, APK83, NATIVE83),
            ('candidate', row['candidate_versionCode'], row['candidate_APK_sha256'], row['candidate_native_sha256'])):
        require(sha(inputs / role / 'artifact.zip') == row[role]['sha256'] and
                (inputs / role / 'artifact.zip').stat().st_size == row[role]['size_in_bytes'], 'RETAINED_WHOLE_ZIP')
        apk = tools['one'](inputs / role / 'files', 'Infinity-' + str(version) + '-Combined-Original-Signer.apk')
        require(sha(apk) == apk_sha, 'EXACT_SIGNED_APK:' + role)
        signature = base.command([sdk / 'build-tools/35.0.0/apksigner', 'verify', '--verbose', '--print-certs', apk], timeout=60)
        (inputs / (role + '-ORIGINAL-SIGNATURE.txt')).write_text(signature)
        require(re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]+)', signature) == [CERT], 'SOLE_ORIGINAL_CERT')
        for scheme in ('v1', 'v2', 'v3'):
            require(any(line.startswith('Verified using ' + scheme + ' scheme') and line.endswith(': true')
                        for line in signature.splitlines()), 'ORIGINAL_SIGNATURE_' + scheme)
        badging = base.command([sdk / 'build-tools/35.0.0/aapt', 'dump', 'badging', apk], timeout=60)
        (inputs / (role + '-BADGING.txt')).write_text(badging)
        require(re.search(r"^package: name='" + re.escape(PACKAGE) + r"' versionCode='" + str(version) + "'", badging, re.M),
                'EXACT_PACKAGE_VERSION')
        sdk_contracts[role] = sdk_contract(badging)
        with ZipFile(apk) as archive:
            manifests[role] = payload(archive)
            require(manifests[role][LIB] == native_sha, 'SIGNED_NATIVE_PAYLOAD')
            require(archive.read('assets/experience-component-updates.properties') ==
                    ('infinity.last_updated_in=' + str(version) + '\ncobra.last_updated_in=2103445\n').encode(),
                    'EXACT_INFINITY_VERSION_AND_RETAINED_COBRA_LABEL')
        paths[role] = str(apk.resolve())
    require(sdk_contracts['candidate'] == sdk_contracts['baseline'], 'UNCHANGED_ACTUAL_BASELINE_ANDROID_SDK_CONTRACT')
    require(set(manifests['baseline']) == set(manifests['candidate']), 'COMPLETE_SAME_APK_PAYLOAD_MEMBER_SET')
    delta = {n for n in manifests['baseline'] if manifests['baseline'][n] != manifests['candidate'][n]}
    require(delta == CHANGES, 'ONLY_ENGINE_AND_REQUIRED_VERSION_INFINITY_LABEL_MEMBERS')
    proof = dict(status='PASS_EXACT_ORIGINAL_SIGNED_INSTALL_INPUTS_ONLY', selection_sha256=sha(SELECTION),
                 APK_paths=paths, certificate_sha256=CERT, signature_schemes=['v1', 'v2', 'v3'],
                 changed_members=sorted(delta), Android_SDK_contract=sdk_contracts, baseline_APK_sha256=APK83,
                 candidate_APK_sha256=row['candidate_APK_sha256'], candidate_native_sha256=row['candidate_native_sha256'])
    save(inputs / 'INTAKE.json', proof)
    return row, base, tools, proof


def no_application(device):
    # PID reads only. Package installation must not turn this into an app test.
    processes = device.shell('ps', '-A', '-o', 'PID,NAME')
    matches = [line for line in processes.splitlines() if line.split() and
               (line.split()[-1] == PACKAGE or line.split()[-1].startswith(PACKAGE + ':'))]
    require(not matches, 'APPLICATION_PROCESS_MUST_NEVER_START')


def installed(device, tools, version, apk_sha, native_sha):
    lines = device.shell('pm', 'path', PACKAGE).splitlines()
    require(len(lines) == 1 and lines[0].startswith('package:'), 'SINGLE_INSTALLED_APK')
    path = lines[0].removeprefix('package:')
    dump = device.shell('dumpsys', 'package', PACKAGE)
    layout = tools['native_package_layout'](path, dump)
    versions = set(re.findall(r'^\s*versionCode=(\d+)\b', dump, re.M))
    require(versions == {str(version)}, 'ACTUAL_INSTALLED_VERSION')
    uid_query = device.shell('pm', 'list', 'packages', '-U', '--user', '0', PACKAGE)
    uid_rows = [re.fullmatch(r'package:([^\s]+) uid:([0-9]+)', line) for line in uid_query.splitlines()]
    require(all(uid_rows), 'VALID_PM_PACKAGE_UID_QUERY')
    uids = [match[2] for match in uid_rows if match[1] == PACKAGE]
    require(len(uids) == 1, 'EXACT_PM_PACKAGE_UID')
    uid = uids[0]
    require(int(uid) >= 10000, 'NORMAL_APPLICATION_UID')
    require(device.shell('sha256sum', path).split() == [apk_sha, path], 'EXACT_ACTUAL_INSTALLED_APK_BYTES')
    root = layout['library_root']
    require(device.shell('readlink', '-f', root).strip() == root, 'CANONICAL_PM_NATIVE_ROOT')
    candidates = device.shell('find', root, '-maxdepth', '2', '-name', 'libkodi.so', '-print').splitlines()
    require(len(candidates) == 1, 'UNIQUE_EXTRACTED_ENGINE')
    native = candidates[0]
    require(native.endswith('/libkodi.so') and
            (str(Path(native).parent) == root or str(Path(native).parent.parent) == root) and
            device.shell('readlink', '-f', native).strip() == native and
            device.shell('stat', '-c', '%F', native).strip() == 'regular file', 'OWNED_REGULAR_EXTRACTED_ENGINE')
    require(device.shell('sha256sum', native).split() == [native_sha, native], 'ACTUAL_EXTRACTED_ENGINE_SHA')
    # Android's user0 CE aliases may canonicalize in either direction. Keep
    # the package identity closed and verify its actual PM-issued UID.
    data = device.shell('readlink', '-f', '/data/user/0/' + PACKAGE).strip()
    require(data in ('/data/user/0/' + PACKAGE, '/data/data/' + PACKAGE) and
            device.shell('stat', '-c', '%u', data).strip() == uid, 'PM_DATA_DIRECTORY_UID')
    no_application(device)
    return dict(versionCode=version, UID=uid, package_UID_query=uid_query, APK_path=path, APK_sha256=apk_sha,
                extracted_native_path=native, extracted_native_sha256=native_sha, data_directory=data)


def snapshot(device, paths):
    result = {}
    for path in paths:
        fields = device.shell('stat', '-c', '%u:%g:%a:%s', path).strip()
        require(re.fullmatch(r'\d+:\d+:[0-7]{3,4}:\d+', fields), 'EXACT_FIXTURE_STAT')
        require(device.shell('readlink', '-f', path).strip() == path.replace('/sdcard/', '/storage/emulated/0/'),
                'CANONICAL_FIXTURE_PATH')
        digest = device.shell('sha256sum', path).split()
        require(len(digest) == 2 and digest[1] == path and re.fullmatch('[0-9a-f]{64}', digest[0]), 'FIXTURE_SHA')
        result[path] = dict(uid_gid_mode_size=fields, sha256=digest[0])
    return result


def seed(device, before, out):
    token = uuid.uuid4().hex
    private = before['data_directory'] + '/files/infinity-signed-install-qa/' + token
    external = '/sdcard/Android/data/' + PACKAGE + '/files/.kodi/userdata/infinity-signed-install-qa/' + token
    paths = []
    for role, directory in (('private', private), ('external_profile', external)):
        require(not device.shell('ls', '-d', directory, check=False).strip(), 'FRESH_SYNTHETIC_FIXTURE_DIRECTORY')
        device.shell('mkdir', '-p', directory)
        local = out / (role + '-synthetic-sentinel.bin')
        local.write_bytes(('INFINITY-INSTALL-ONLY-SYNTHETIC-NOT-USERDATA\n' + role + '\n' + token + '\n').encode())
        remote = directory + '/sentinel.bin'
        device.adb('push', local, remote)
        if role == 'private':
            # Only new synthetic nodes and the fresh package files directory.
            for path in (before['data_directory'] + '/files', str(Path(directory).parent), directory, remote):
                device.shell('chown', before['UID'] + ':' + before['UID'], path)
                device.shell('chmod', '600' if path == remote else '700', path)
        # External emulated storage has its stock FUSE ownership/modes; measure
        # them without attempting permission overrides or changing the mount.
        paths.append(remote)
    measured = snapshot(device, paths)
    require(measured[paths[0]]['uid_gid_mode_size'].split(':')[:3] == [before['UID'], before['UID'], '600'],
            'PRIVATE_SYNTHETIC_SENTINEL_APP_OWNED')
    return paths, measured


def run(inputs, sdk, out):
    require(not out.exists(), 'FRESH_RESULT_DIRECTORY')
    row, base, tools, proof = stage(inputs, sdk)
    out.mkdir(parents=True)
    report = dict(status='NOT_RUN', scope='SIGNED83_TO_SIGNED84_ORDINARY_INSTALL_OVER_SYNTHETIC_DATA_ONLY',
                  selection_sha256=sha(SELECTION), source=os.environ['SELECTED_SOURCE'],
                  application_launched=False, application_tests='NOT_RUN', real_userdata='NOT_RUN',
                  Fold='NOT_RUN', Core='NOT_RUN', providers='NOT_RUN', Close='NOT_RUN', shutdown='NOT_RUN',
                  native_injection=False, native_runtime='NOT_RUN', fixture_kind='SYNTHETIC_SENTINELS_ONLY')
    device, disposer = None, None
    code = 1
    try:
        device = base.Device(out, sdk)
        disposer, report['retained_host_disposal'] = base.retained_disposal(out)
        port = int(device.serial.removeprefix('emulator-'))
        targets = [p for entry in Path('/proc').iterdir() if entry.name.isdigit() and
                   disposer['_emulator_target'](p := disposer['_host_process'](int(entry.name)), str(device.sdk_root), port)]
        require(targets, 'EXACT_PINNED_SDK_EMULATOR_HOST_PROCESS_REQUIRED')
        report['environment'] = base.environment(device, out)
        require(not device.shell('pm', 'list', 'packages', PACKAGE).strip(), 'FRESH_VM_NO_PRIOR_INFINITY')
        report['root_handshake'] = base.root_reconnect(device, out)
        result = device.adb('install', '--no-streaming', proof['APK_paths']['baseline'], timeout=300)
        report['baseline_install_result'] = result
        require(result.strip().endswith('Success'), 'ORDINARY_SIGNED83_INSTALL_SUCCESS')
        before = installed(device, tools, 2103483, APK83, NATIVE83)
        report['baseline'] = before
        paths, original = seed(device, before, out)
        report['synthetic_before'] = original
        save(out / 'SIGNED-INSTALL.json', report)
        no_application(device)
        result = device.adb('install', '-r', '--no-streaming', proof['APK_paths']['candidate'], timeout=300)
        report['install_over_result'] = result
        require(result.strip().endswith('Success'), 'ORDINARY_SIGNED84_INSTALL_OVER_SUCCESS')
        after = installed(device, tools, row['candidate_versionCode'], row['candidate_APK_sha256'], row['candidate_native_sha256'])
        report['candidate'] = after
        report['synthetic_after'] = snapshot(device, paths)
        require(after['UID'] == before['UID'], 'APP_UID_RETAINED')
        require(report['synthetic_after'] == original, 'SYNTHETIC_BYTES_UID_GID_MODE_SIZE_RETAINED')
        no_application(device)
        report.update(status='PASS_SELECTED_SIGNED_INSTALL_OVER_SYNTHETIC_RETENTION_ONLY',
                      certificate_sha256=CERT, signature_schemes=['v1', 'v2', 'v3'],
                      changed_APK_members=proof['changed_members'], application_launched=False)
        code = 0
    except Exception:
        report['status'] = 'FAIL_SELECTED_SIGNED_INSTALL_OVER'
        report['error'] = traceback.format_exc()
    finally:
        save(out / 'SIGNED-INSTALL.json', report)
        if device and disposer:
            # CI host VM disposal only; never an application Close assertion.
            disposer['arm_host_disposal'](device, out)
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    sub.add_parser('gate')
    p = sub.add_parser('fetch'); p.add_argument('--out', type=Path, required=True)
    for name in ('stage', 'run'):
        p = sub.add_parser(name)
        p.add_argument('--inputs', type=Path, required=True)
        p.add_argument('--sdk', type=Path, required=True)
        if name == 'run': p.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'gate': selected()
    elif args.mode == 'fetch': fetch(args.out)
    elif args.mode == 'stage': stage(args.inputs, args.sdk)
    else: raise SystemExit(run(args.inputs, args.sdk, args.out))
