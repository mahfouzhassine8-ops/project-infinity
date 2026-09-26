#!/usr/bin/env python3
"""Exercise the actual APK merge against the exact parent with its real DEX.

The donor contains the parent's unchanged Java bytecode solely as a packaging
fixture. Nothing built here is a replacement APK or a runtime gesture test.
Temporary APK fixtures are deleted; only a small evidence receipt is retained.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import tempfile
import zipfile

PARENT_SHA = '273c7d0a88196cd9f00121b51fe5ac54a4328558c34d5c3c79a74e85a29176be'


def run(root: Path, parent: Path, evidence: Path) -> dict:
    original_hash = hashlib.sha256(parent.read_bytes()).hexdigest()
    if original_hash != PARENT_SHA:
        raise AssertionError('Packaging fixture must use the exact preserved 2103255 APK')
    sys.path.insert(0, str(root/'scripts'))
    spec = importlib.util.spec_from_file_location('reviewed_packager', root/'scripts/package_background_resume.py')
    if spec is None or spec.loader is None:
        raise RuntimeError('Reviewed packager unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks = []
    with tempfile.TemporaryDirectory(prefix='cobra-apk-merge-') as directory:
        work = Path(directory)
        (work/'engine').mkdir()
        module.ROOT = work
        recorder = work/'engine/libinfinitycrash.so'
        donor = work/'fixture-java-only.apk'
        with zipfile.ZipFile(parent) as a, zipfile.ZipFile(donor, 'w', zipfile.ZIP_DEFLATED) as z:
            recorder.write_bytes(a.read(module.CRASH_RECORDER_APK_PATH))
            for info in a.infolist():
                if info.filename == 'AndroidManifest.xml' or module.DEX.fullmatch(info.filename):
                    z.writestr(copy.copy(info), a.read(info.filename))
        expected_recorder = recorder.read_bytes()
        # Deliberately recreate ONLY the previous aliasing error, not a mock merge.
        broken_source = inspect.getsource(module.merge).replace('copy.copy(info)', 'info')
        if broken_source == inspect.getsource(module.merge):
            raise AssertionError('Missing ZipInfo copy correction')
        broken = dict(vars(module))
        exec(compile(broken_source, 'prior-zipinfo-alias-regression', 'exec'), broken)
        try:
            broken['merge'](parent, donor, work/'reproduced-failure.apk')
        except zipfile.BadZipFile as exc:
            if 'Bad magic number' not in str(exc):
                raise
            checks.append('prior mutable-ZipInfo failure reproduced on the valid parent')
        else:
            raise AssertionError('Expected old packaging failure was not reproduced')
        output = work/'fixture-merged.apk'
        native_count, core_count = module.merge(parent, donor, output)
        if not native_count or not core_count:
            raise AssertionError('Real DEX/JNI contract was not checked')
        checks.append('corrected actual merge and real DEX/JNI contract pass')
        with zipfile.ZipFile(parent) as a, zipfile.ZipFile(output) as b:
            if a.testzip() is not None or b.testzip() is not None:
                raise AssertionError('Fixture ZIP integrity failure')
            checks.append('parent and merged fixture CRC checks pass')
            if b.namelist().count(module.CRASH_RECORDER_APK_PATH) != 1 or len(b.namelist()) != len(set(b.namelist())):
                raise AssertionError('Recorder or other ZIP member duplicated')
            checks.append('recorder appears exactly once; no duplicate ZIP entries')
            kept = {n for n in a.namelist() if n != 'AndroidManifest.xml' and not module.DEX.fullmatch(n) and not module.SIGNATURE.fullmatch(n)}
            protected_new = {n for n in b.namelist() if n != 'AndroidManifest.xml' and not module.DEX.fullmatch(n) and not module.SIGNATURE.fullmatch(n)}
            if kept != protected_new or any(a.read(n) != b.read(n) for n in kept):
                raise AssertionError('Protected payload changed')
            checks.append('all protected parent APK members are byte-identical')
        actual_verify = module.verify_bytes(parent, output)
        if not actual_verify['android_resources_byte_identical']:
            raise AssertionError('Existing post-merge audit failed')
        checks.append('existing full verify_bytes audit remains intact and passes')
        recorder.write_bytes(expected_recorder + b'INVALID-FIXTURE')
        try:
            module.merge(parent, donor, work/'must-reject.apk')
        except RuntimeError as exc:
            if str(exc) != 'Recorder differs from exact parent':
                raise
            checks.append('different recorder refused; integrity gate not bypassed')
        else:
            raise AssertionError('Recorder mismatch wrongly accepted')
    if hashlib.sha256(parent.read_bytes()).hexdigest() != original_hash:
        raise AssertionError('Parent APK changed during tests')
    checks.append('original signed parent hash unchanged; temporary fixtures deleted')
    receipt = {'packaging_regressions': len(checks), 'checks': checks,
               'parent_sha256': original_hash, 'protected_members_verified': len(kept),
               'uses_real_dex_parser': True, 'native_methods': native_count, 'core_classes': core_count,
               'android_touch_or_device_test': False, 'new_runtime_apk_built': False}
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence/'packaging-tests.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('PASS: '+str(len(checks))+' actual-APK packaging regressions; prior aliasing failure reproduced then corrected')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.parent.resolve(), args.evidence.resolve())
