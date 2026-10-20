#!/usr/bin/env python3
"""Execute only the already verified CC22 startup class on disposable Android ART.

No native workflow submission, libkodi build/load, APK signing/installation,
app startup, shutdown certification, or physical Fold claim is performed.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
APK_SHA = '47609f2ada1d6bbc7cdbddb791d11815bdbf1100a083bd8205d60ac21c882151'
CANDIDATE = '2b54ba6ede1461cfcd0e1788de8c35a7cf63df582d9c8e03bb3c583890b8de54'
BASELINE = '67e556c37a534be95789b3d88a9468219ecc5ea47d81dd5aab9b5911ba1c6573'
SHARD2 = 'd4df6604044e7cb66584229562186bf2ed8f0031d2d3efba03bba8ebe38934ca'
PRODUCER = '0308452b1a6164e659630076d6d0908c37c00789'
CLASS = 'com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.smali'
FALSE_FLAGS = ('native_engine_loaded', 'installed_app_started',
               'whole_process_shutdown_tested', 'physical_fold_verified')


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def component_proof(proof: dict, dex: Path) -> None:
    require(proof.get('source_commit') == PRODUCER and proof.get('run_id') == '39376264712',
            'Wrong startup component producer')
    require(proof.get('source_apk_sha256') == APK_SHA, 'Wrong original APK lineage')
    require(proof.get('component_dex_name') == 'classes.dex' and
            proof.get('component_dex_sha256') == CANDIDATE and sha(dex) == CANDIDATE,
            'Wrong actual component bytes')
    require(proof.get('only_runtime_class_changed') == CLASS and
            proof.get('protected_classes_in_changed_shard') == 7854 and
            proof.get('decoded_protected_instructions_identical') is True,
            'Missing original DEX preservation proof')
    require(proof.get('fields', {}).get('exact_field_definitions_verified') == 25870 and
            proof.get('fields', {}).get('encoded_values_and_presence_preserved') is True,
            'Missing field-preservation proof')
    require(proof.get('original_dex_sha256') == BASELINE and
            proof.get('other_dex_shards') == {'classes2.dex': SHARD2}, 'DEX baseline differs')
    require(proof.get('new_signed_apk') is False and proof.get('physical_fold_verified') is False,
            'Component proof cannot represent a delivered app')


def expected_cases(pins: dict[str, str]) -> list[str]:
    require(len(pins) == 13, 'Exactly thirteen complete controller fingerprints required')
    result = ['component_fingerprint', 'fixture_fingerprints', 'reviewed_cc22_accepted']
    for name in sorted(pins):
        part = PurePosixPath(name)
        require(bool(re.fullmatch(r'[a-z0-9_./-]+', name)) and not part.is_absolute() and
                all(p not in ('', '.', '..') for p in name.split('/')) and
                bool(re.fullmatch(r'[0-9a-f]{64}', pins[name])), 'Invalid controller fingerprint')
        result += ['changed:' + name, 'missing:' + name]
    return result + ['symlinked_file_rejected', 'symlinked_controller_root_rejected',
                     'oversized_file_rejected', 'missing_controller_root_rejected',
                     'legacy_cc21_rejected', 'restored_cc22_accepted',
                     'fixture_and_sentinel_unchanged', 'component_still_identical']


def prepare(apk: Path, component: Path, out: Path, tools: Path | None, android: Path | None) -> dict:
    require(not out.exists(), 'Refusing to overwrite test inputs')
    require(sha(apk) == APK_SHA, 'Wrong original signed APK')
    proof = json.loads((component / 'STARTUP-DEX-INTEGRATION.json').read_text())
    dex = component / 'component/classes.dex'
    component_proof(proof, dex)
    release_path = ROOT / 'repairs/2103390-bugfixes/group7/finish92/release.py'
    sys.path.insert(0, str(release_path.parent))
    spec = importlib.util.spec_from_file_location('art_cc22_reviewed_release', release_path)
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    originals = release.read_original(apk)
    final = release.components(originals)
    pins = json.loads(final[release.UI + '/CONTROLLER-PREIMAGES.json'])
    cases = expected_cases(pins)
    require(len(cases) == 37, 'Incomplete candidate case matrix')
    inputs = out / 'inputs'; inputs.mkdir(parents=True)
    for name, digest in sorted(pins.items()):
        body = final[release.CC + '/' + name]
        require(hashlib.sha256(body).hexdigest() == digest, 'Wrong reviewed controller source')
        path = inputs / 'controller-input' / name
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(body)
    (inputs / 'pins.tsv').write_text(''.join(n + '\t' + h + '\n' for n, h in sorted(pins.items())))
    shutil.copyfile(dex, inputs / 'candidate.dex')
    with ZipFile(apk) as archive:
        (inputs / 'baseline.dex').write_bytes(archive.read('classes.dex'))
        (inputs / 'classes2.dex').write_bytes(archive.read('classes2.dex'))
    require(sha(inputs / 'baseline.dex') == BASELINE and sha(inputs / 'classes2.dex') == SHARD2,
            'Original APK bytecode shards do not match component proof')
    runner_built = False
    if tools is not None:
        require(android is not None and android.is_file() and (tools / 'd8').is_file(),
                'Android compiler input missing')
        classes = out / 'probe-classes'; classes.mkdir()
        subprocess.run(['javac', '--release', '8', '-g:none', '-Xlint:all,-options', '-Werror',
                        '-d', str(classes), str(HERE / 'Controller22ArtProbe.java')], check=True)
        produced = list(classes.rglob('*.class'))
        require([p.relative_to(classes).as_posix() for p in produced] == ['Controller22ArtProbe.class'],
                'Test compiler emitted unexpected classes')
        output = out / 'probe-dex'; output.mkdir()
        subprocess.run([str(tools / 'd8'), '--release', '--min-api', '26', '--lib', str(android),
                        '--output', str(output), str(produced[0])], check=True)
        require(len(list(output.glob('*.dex'))) == 1, 'Unexpected test DEX shards')
        shutil.copyfile(output / 'classes.dex', inputs / 'probe.dex'); runner_built = True
    report = dict(schema=1, state='DISPOSABLE_ART_INPUTS_ONLY', component_producer=PRODUCER,
                  source_apk_sha256=APK_SHA, component_sha256=CANDIDATE,
                  controller_pins=pins, expected_candidate_cases=cases,
                  expected_baseline_cases=['baseline_has_no_cc22_verifier'],
                  runner_compiled=runner_built, requested_android_api=37,
                  tested_component_recompiled=False, native_build_started=False,
                  installed_app_started=False, whole_process_shutdown_tested=False,
                  physical_fold_verified=False, final_lock=False,
                  release_generator_sha256=sha(release_path),
                  harness_source_sha256=sha(HERE / 'Controller22ArtProbe.java'),
                  input_hashes={p.relative_to(inputs).as_posix(): sha(p) for p in inputs.rglob('*') if p.is_file()})
    require(sha(apk) == APK_SHA and sha(dex) == CANDIDATE, 'Original input was modified')
    save(out / 'ART-INPUTS.json', report)
    return report


def parse_result(output: str, variant: str, expected: list[str], api: int) -> dict:
    rows = [line[len('ART_RESULT '):] for line in output.splitlines() if line.startswith('ART_RESULT ')]
    require(len(rows) == 1, 'Missing or duplicated Android result')
    result = json.loads(rows[0])
    require(result.get('passed') is True and result.get('variant') == variant, 'Wrong/failed result')
    require(result.get('api') == api and str(result.get('android_release')).split('.')[0] == '17',
            'The actual runtime is not Android17/API37')
    require(result.get('cases') == expected and len(set(expected)) == len(expected),
            'Missing/duplicate/reordered Android cases')
    case_lines = [line[len('ART_CASE_PASS '):] for line in output.splitlines() if line.startswith('ART_CASE_PASS ')]
    require(case_lines == expected, 'Summary disagrees with executed case output')
    require(all(result.get(key) is False for key in FALSE_FLAGS), 'Component test scope overstated')
    return result


def art_command(device: str, variant: str) -> str:
    """Use AndroidRuntime initialization, not bare ART lacking framework JNI.

    app_process takes VM options, a command directory, then the Java main class.
    This starts only the disposable probe; it does not start the installed app.
    """
    require(bool(re.fullmatch(r'/data/local/tmp/infinity-cc22-art-[0-9]+-[0-9]+', device)),
            'Invalid disposable ART path')
    require(variant in ('baseline', 'candidate'), 'Invalid ART variant')
    cp = ':'.join(device + '/' + n for n in ('probe.dex', variant + '.dex', 'classes2.dex'))
    return ('CLASSPATH=' + shlex.quote(cp) +
            ' /system/bin/app_process -Xverify:all /system/bin Controller22ArtProbe ' +
            variant + ' ' + shlex.quote(device) + ' 37')


def android_test(out: Path, adb: str = 'adb') -> dict:
    proof = json.loads((out / 'ART-INPUTS.json').read_text()); inputs = out / 'inputs'
    require(proof.get('runner_compiled') is True, 'No compiled test entrypoint')
    hashes = {p.relative_to(inputs).as_posix(): sha(p) for p in inputs.rglob('*') if p.is_file()}
    require(hashes == proof['input_hashes'], 'Test inputs changed before Android execution')
    require(hashes['candidate.dex'] == CANDIDATE and hashes['baseline.dex'] == BASELINE and
            hashes['classes2.dex'] == SHARD2, 'Production DEX fingerprint mismatch')
    expected = expected_cases(proof['controller_pins'])
    require(proof['expected_candidate_cases'] == expected, 'Case manifest drift')
    token = os.environ.get('GITHUB_RUN_ID', str(os.getpid()))
    attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '1')
    require(token.isdecimal() and attempt.isdecimal(), 'Invalid disposable directory token')
    device = '/data/local/tmp/infinity-cc22-art-' + token + '-' + attempt
    report = dict(schema=1, passed=False, component_sha256=CANDIDATE, source_apk_sha256=APK_SHA,
                  component_producer=PRODUCER, workflow_source=os.environ.get('GITHUB_SHA', ''),
                  workflow_run=token, scope='Exact startup verifier on Android ART; NOT full Infinity',
                  tested_component_recompiled=False, native_engine_compiled=False,
                  android_runtime_launcher='/system/bin/app_process -Xverify:all',
                  installed_app_started=False, whole_process_shutdown_tested=False,
                  new_signed_apk=False, physical_fold_verified=False, final_lock=False, cases=[])
    try:
        listing = subprocess.check_output([adb, 'devices'], text=True)
        devices = [s.split()[0] for s in listing.splitlines()[1:] if s.strip().endswith('\tdevice')]
        require(len(devices) == 1 and devices[0].startswith('emulator-'), 'Only one disposable emulator is permitted')
        def shell(command: str) -> str:
            return subprocess.check_output([adb, '-s', devices[0], 'shell', command], text=True, stderr=subprocess.STDOUT)
        api = int(shell('getprop ro.build.version.sdk').strip())
        version = shell('getprop ro.build.version.release').strip()
        require(api == 37 and version.split('.')[0] == '17', 'Wrong actual Android platform')
        report['platform'] = dict(api=api, release=version, abi=shell('getprop ro.product.cpu.abi').strip(),
                                  build_fingerprint=shell('getprop ro.build.fingerprint').strip(),
                                  samsung_one_ui_emulated=False)
        shell('test ! -e ' + shlex.quote(device) + ' && mkdir ' + shlex.quote(device))
        subprocess.run([adb, '-s', devices[0], 'push', str(inputs) + '/.', device], check=True)
        shell('chmod 444 ' + ' '.join(shlex.quote(device + '/' + n) for n in ('candidate.dex', 'baseline.dex', 'classes2.dex', 'probe.dex')))
        for variant, cases in [('baseline', ['baseline_has_no_cc22_verifier']), ('candidate', expected)]:
            command = art_command(device, variant)
            result = subprocess.run([adb, '-s', devices[0], 'shell', command], text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
            (out / (variant + '-art.log')).write_text(result.stdout)
            print(result.stdout, flush=True)
            require(result.returncode == 0, 'ART ' + variant + ' failed; original output retained')
            report['cases'].append(parse_result(result.stdout, variant, cases, api))
        report.update(passed=True, android_art_component_executed=True,
                      candidate_cases_passed=37, baseline_control_cases_passed=1,
                      actual_startup_apply_before_native_invoked=False)
        return report
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        save(out / 'ART-COMPONENT-VERIFICATION.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'android'])
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--apk', type=Path); parser.add_argument('--component', type=Path)
    parser.add_argument('--build-tools', type=Path); parser.add_argument('--android-jar', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        require(args.apk is not None and args.component is not None, 'Original APK and component are required')
        value = prepare(args.apk, args.component, args.out, args.build_tools, args.android_jar)
    else:
        value = android_test(args.out)
    print(json.dumps(value, indent=2, sort_keys=True))
