#!/usr/bin/env python3
"""Reproduce G0 branding inputs with the protected Ubuntu renderer, by exact hash.

This generates candidate assets in a disposable output directory. A candidate
is recovered only when its entire byte sequence equals the compiled parent.
The existing timestamp-only recovery never changes pixels/compressed IDAT.
There is no native compilation, APK creation, signing or installation here.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

from source_gate import compiled_manifest, relative_path

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
IMAGEMAGICK = '8:6.9.11.60+dfsg-1.3ubuntu0.22.04.5'
FONT_PACKAGE = '2.37-2build1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def package_version(name):
    return subprocess.check_output(
        ['dpkg-query', '-W', '-f=${Version}', name], text=True).strip()


def environment():
    image = package_version('imagemagick')
    font = package_version('fonts-dejavu-core')
    if image != IMAGEMAGICK or font != FONT_PACKAGE:
        raise ValueError('Protected renderer packages unavailable: ' + repr((image, font)))
    return {'imagemagick': image, 'fonts-dejavu-core': font,
            'convert': subprocess.check_output(['convert', '-version'], text=True),
            'font_sha256': sha(Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf').read_bytes())}


def recover_batch(expected, raw, recovery):
    payload, evidence, errors = {}, [], []
    for name, digest in sorted(expected.items()):
        path = raw / relative_path(name)
        # The protected source maps identify this TVOS copy as exactly the same
        # byte sequence as the main light splash. No generic TVOS image is used.
        if not path.is_file() and name.startswith('xbmc/platform/darwin/tvos/'):
            original = 'media/applaunch_screen.png'
            if expected.get(original) != digest:
                raise ValueError('Unknown TVOS splash source identity')
            path = raw / original
        row = {'path': name, 'expected_sha256': digest}
        try:
            data = path.read_bytes()
            row['generated_sha256'] = sha(data)
            moment = None
            if sha(data) != digest:
                if not name.endswith('.png'):
                    raise ValueError('Non-PNG candidate differs from compiled bytes')
                data, moment = recovery.recover(data, digest)
            if sha(data) != digest:
                raise ValueError('Full recovered hash mismatch')
            row.update(recovered_sha256=sha(data), timestamp_recovery=moment,
                       non_timestamp_bytes_preserved=True)
            payload[name] = data
        except (OSError, ValueError) as failure:
            row['error'] = str(failure)
            errors.append(name)
        evidence.append(row)
    return payload, evidence, errors


def write_verified_payload(expected, payload, output):
    if set(payload) != set(expected) or any(sha(data) != expected[name]
                                          for name, data in payload.items()):
        raise ValueError('Incomplete or mismatched assets: nothing admitted as recovered')
    if output.exists():
        raise ValueError('Recovered output must be fresh')
    output.mkdir(parents=True)
    for name, data in payload.items():
        path = output / relative_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if sha(path.read_bytes()) != expected[name]:
            raise ValueError('Source asset readback mismatch: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Recovery workspace must be fresh')
    env = environment()
    compiled, parent = compiled_manifest('native')
    missing = json.loads((HERE / 'evidence/missing-native-inputs.json').read_text())['files']
    if len(missing) != 37 or any(compiled.get(name) != digest for name, digest in missing.items()):
        raise ValueError('Protected missing-asset inventory changed')
    renderer_path = REPOSITORY / 'scripts/infinity_1_0_8_deep_rebrand.py'
    recovery_path = REPOSITORY / 'repairs/provider-windows-2103306/restore_assets.py'
    # Both scripts are pinned through the exact parent Git object. Do not quietly
    # render with a later script or weaken its timestamp/whole-file acceptance.
    for path in (renderer_path, recovery_path):
        original = subprocess.check_output(['git', 'show', parent['compiled_parent_commit'] + ':' +
                                            path.relative_to(REPOSITORY).as_posix()], cwd=REPOSITORY)
        if path.read_bytes() != original:
            raise ValueError('Renderer/recovery recipe differs from compiled parent')
    renderer = module('protected_branding_renderer', renderer_path)
    recovery = module('protected_png_recovery', recovery_path)
    args.output.mkdir(parents=True)
    raw = args.output / 'generated'
    renderer.art(raw)
    payload, evidence, errors = recover_batch(missing, raw, recovery)
    receipt = {'schema': 1, 'purpose': 'G0 exact assets only',
               'compiled_parent_commit': parent['compiled_parent_commit'],
               'renderer_sha256': sha(renderer_path.read_bytes()),
               'recovery_recipe_sha256': sha(recovery_path.read_bytes()),
               'environment': env, 'expected_files': len(missing),
               'verified_files': len(payload), 'errors': errors, 'files': evidence,
               'native_compiled': False, 'apk_created': False, 'device_pass': False,
               'complete': not errors}
    (args.output / 'ASSET-RECOVERY.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if errors:
        print(json.dumps({'recovered': len(payload), 'expected': len(missing), 'errors': errors}))
        return 2
    recovered = args.output / 'recovered'
    write_verified_payload(missing, payload, recovered)
    archive = args.output / 'exact-parent-assets.tar.gz'
    with tarfile.open(archive, 'w:gz') as pack:
        for name in sorted(payload):
            pack.add(recovered / name, arcname=name, recursive=False)
    (args.output / 'SHA256SUMS').write_text(sha(archive.read_bytes()) + '  exact-parent-assets.tar.gz\n')
    print('PASS: all 37 original source assets match full compiled SHA-256 hashes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
