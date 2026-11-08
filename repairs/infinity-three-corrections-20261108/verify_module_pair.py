"""Real unchanged Java module installer, new79-file upgrade/recovery pair only.

Local filesystem and Android API transport adapters; no device/profile access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIRST = ROOT / 'repairs/infinity-final-closure-2103407'
sys.path.insert(0, str(FIRST))
import module_dex
import module_bundle
CC = 'script.infinity.commandcenter'


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def audit(prepared, out):
    out.mkdir(parents=True, exist_ok=False)
    reference = json.loads((ROOT / 'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/CC-AUDIT-REFERENCE.json').read_text())
    source = module_dex.source()
    assert hashlib.sha256(source.encode()).hexdigest() == reference['java_source_sha256']
    host = {p.relative_to(FIRST).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (FIRST / 'host-java').rglob('*.java')}
    assert host == reference['host_java_sha256']
    rows = []
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        temp = Path(temporary)
        assets = {}
        for version in (64, 65):
            path = temp / str(version) / 'assets/addons'
            shutil.copytree(prepared / str({64: 2103466, 65: 2103467}[version]) / 'modules', path)
            payload, files = module_bundle.build(path)
            assert len(files) == 79 and payload == (path / CC / module_bundle.MANIFEST).read_bytes()
            subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem'), '-signature', str(path / CC / (module_bundle.MANIFEST + '.sig')), str(path / CC / module_bundle.MANIFEST)], capture_output=True, check=True)
            assets[version] = path.parent
        java = temp / 'InfinityInstalledCheckpointInstaller.java'
        java.write_text(source)
        classes = temp / 'classes'
        classes.mkdir()
        subprocess.run(['javac', '--release', '8', '-g:none', '-d', str(classes), str(java), *map(str, (FIRST / 'host-java').rglob('*.java'))], check=True)

        def fixture(name):
            storage = temp / name
            shutil.copytree(prepared / 'baseline-modules', storage / '.kodi/addons')
            # Exactly the additional inactive approved helper observed on Fold.
            shutil.copyfile(prepared / 'device-audit/installed' / CC / 'native_search_compatibility.py', storage / '.kodi/addons' / CC / 'native_search_compatibility.py')
            for path, raw in [('.kodi/userdata/addon_data/plugin.video.sentinel/settings.xml', b'<settings>retain user data</settings>'),
                              ('.kodi/addons/plugin.video.sentinel/source.py', b'# unrelated provider\n'),
                              ('.kodi/addons/' + CC + '/user-retained-file.txt', b'unknown unlisted retained file')]:
                p = storage / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(raw)
            return storage

        def call(storage, version, other_assets=None):
            return subprocess.run(['java', '-cp', str(classes), 'com.projectinfinity.kodi.Main', str(storage), str(other_assets or assets[version])], capture_output=True, text=True)

        def passed(name, storage, version):
            result = call(storage, version)
            assert result.returncode == 0 and 'VERIFIED_VERSION=0.3.5.' + str(version) in result.stdout, (name, result.stderr)
            for relative in hashes(assets[version] / 'addons'):
                assert (storage / '.kodi/addons' / relative).read_bytes() == (assets[version] / 'addons' / relative).read_bytes()
            assert (storage / '.kodi/userdata/addon_data/plugin.video.sentinel/settings.xml').read_bytes() == b'<settings>retain user data</settings>'
            assert (storage / '.kodi/addons/plugin.video.sentinel/source.py').read_bytes() == b'# unrelated provider\n'
            assert (storage / '.kodi/addons' / CC / 'user-retained-file.txt').read_bytes() == b'unknown unlisted retained file'
            rows.append(dict(case=name, status='PASS_REAL_UNCHANGED_JAVA', version=version))

        storage = fixture('owner62_loose_helper_to64')
        passed('actual62_generation_plus_exact_loose_helper_to79_file64', storage, 64)
        before = hashes(storage)
        passed('same64_idempotent_noop', storage, 64)
        assert hashes(storage) == before
        passed('forward65_recovery_original_inventory_inactive_helper_and_data', storage, 65)
        before = hashes(storage)
        result = call(storage, 64)
        assert result.returncode == 0 and 'VERIFIED_VERSION=0.3.5.65' in result.stdout and hashes(storage) == before
        rows.append(dict(case='older64_retains_authenticated65_no_downgrade', status='PASS_NO_WRITE'))
        for name, change in (
                ('unknown_inventory_source', lambda root: (root / CC / 'provider_inventory.py').write_bytes(b'unknown generation')),
                ('unknown_loose_helper', lambda root: (root / CC / 'native_search_compatibility.py').write_bytes(b'unknown helper')),
                ('missing_installed_signature', lambda root: (root / CC / (module_bundle.MANIFEST + '.sig')).unlink()),
                ('unmatched_partial_signature', lambda root: shutil.copyfile(assets[64] / 'addons' / CC / (module_bundle.MANIFEST + '.sig'), root / CC / (module_bundle.MANIFEST + '.sig')))):
            storage = fixture(name)
            change(storage / '.kodi/addons')
            before = hashes(storage)
            result = call(storage, 64)
            assert result.returncode != 0 and hashes(storage) == before, name
            rows.append(dict(case=name, status='REFUSED_AS_REQUIRED_ALL_BYTES_RETAINED'))
        storage = fixture('known_partial_inventory')
        shutil.copyfile(assets[64] / 'addons' / CC / 'provider_inventory.py', storage / '.kodi/addons' / CC / 'provider_inventory.py')
        passed('known_signed64_partial_inventory_resumes_from62', storage, 64)
        storage = fixture('tampered_candidate_helper')
        damaged = temp / 'damaged-assets'
        shutil.copytree(assets[64], damaged)
        (damaged / 'addons' / CC / 'native_search_compatibility.py').write_bytes(b'tampered APK source')
        before = hashes(storage)
        result = call(storage, 64, damaged)
        assert result.returncode != 0 and hashes(storage) == before
        rows.append(dict(case='tampered_candidate_helper', status='REFUSED_AS_REQUIRED_ALL_BYTES_RETAINED'))
    assert len(rows) == 10
    report = dict(status='PASS_TEN_REAL_JAVA79_FILE_UPGRADE_AND_FORWARD_RECOVERY_CASES', cases=rows,
                  java_source_sha256=reference['java_source_sha256'], host_transport_sha256=host,
                  original_installer_changed=False, user_data_and_unknown_files_preserved=True,
                  original_signatures_verified=True, Android='NOT_RUN_BY_HOST_TEST', Fold='NOT_RUN', shutdown='NOT_SELECTED')
    (out / 'MODULE-UPGRADE-RECOVERY.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--prepared', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    audit(a.prepared, a.out)
