"""Release tooling only; never shipped. Use unchanged original module signer."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIRST = ROOT / 'repairs/infinity-final-closure-2103407'
sys.path.insert(0, str(FIRST))
import module_bundle
import module_dex

CC = module_bundle.CC
M = module_bundle.MANIFEST
SOURCE = '16af10e42265f9f5155efd54849b25871c50aa0f'
APK_SHA = 'a24ffafd056db23aa9d433552e17d4362cc9dbc9dd568b086d84cabadae8c619'
OLD_MANIFEST = '5a40c8a5492309625a010aeb2f86f7fc4a9392ca35170a4fe671065fe729440f'
NEW_MANIFEST = '01491c3ebf991ee8c0aeaab43dcf41abd0b9adfd4cf85c5c6c4245c40a19da80'
REVIEW_IDS = {410798135, 410795791, 410860075, 410843338}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(*args, env=None):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True, env=env)
    if result.returncode:
        raise RuntimeError(str(args[0]) + ': ' + result.stdout[-2500:] + result.stderr[-2500:])
    return result.stdout


def save(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def inventory(root):
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}


def scope():
    """Preserve old jobs and every old trust rule; catalog only audited no-key jobs."""
    changed = set(run('git', 'diff', '--name-only', SOURCE, 'HEAD').splitlines())
    allowed = {'.github/workflows/infinity-combined-release.yml',
               'repairs/dual-experience-isolation-2103420/signer-policy.json',
               *[str((HERE / n).relative_to(ROOT)) for n in
                 ('package_zip.py', 'WORKFLOW-REVIEW.json', 'SCOPE.md')]}
    assert changed == allowed, ('UNREVIEWED_PACKAGING_PATHS', sorted(changed ^ allowed))
    workflow = '.github/workflows/infinity-combined-release.yml'
    before = run('git', 'show', SOURCE + ':' + workflow)
    current = (ROOT / workflow).read_text()
    expected = before.replace('verify-nine-update-recovery, prepare-nine-native462-463]',
                              'verify-nine-update-recovery, prepare-nine-native462-463, package-umbrella-pov-462]')
    assert current.startswith(expected.rstrip() + '\n'), 'EXISTING_SIGNER_JOBS_CHANGED'
    policy_path = 'repairs/dual-experience-isolation-2103420/signer-policy.json'
    original = json.loads(run('git', 'show', SOURCE + ':' + policy_path))
    review = json.loads((HERE / 'WORKFLOW-REVIEW.json').read_text())
    assert {r['id'] for r in review} == REVIEW_IDS
    assert all(r['original_key_access'] is False for r in review)
    for item in review:
        raw = subprocess.check_output(['git', 'show', item['source'] + ':' + item['path']])
        assert sha(raw) == item['workflow_sha256']
        assert b'secrets.' not in raw and b'INFINITY_KEYSTORE' not in raw
    expected_policy = json.loads(json.dumps(original))
    expected_policy['reviewed_workflow_ids'] = sorted(set(original['reviewed_workflow_ids']) | REVIEW_IDS)
    expected_policy['additional_unsigned_owner_workflows'] += review
    assert json.loads((ROOT / policy_path).read_text()) == expected_policy
    assert original['sole_original_key_workflow_id'] == 397702717
    for name in ('SignInfinityModules.java', 'ORIGINAL-INFINITY-PUBLIC-KEY.pem',
                 'module_bundle.py', 'module_dex.py', 'InfinityInstalledModules.java.in',
                 'isolated-native/InfinityModuleManifest.cpp'):
        assert (FIRST / name).read_bytes() == subprocess.check_output(
            ['git', 'show', SOURCE + ':repairs/infinity-final-closure-2103407/' + name])
    sys.path.insert(0, str(ROOT / 'repairs/dual-experience-isolation-2103420'))
    from signer_policy import check
    return check(expected_policy)


def verify_native(root, verifier):
    return run(verifier, root, FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem')


def preflight(apk, out):
    assert not out.exists(), 'FRESH_OUTPUT_REQUIRED'
    out.mkdir(parents=True)
    policy = scope()
    assert hashlib.file_digest(apk.open('rb'), 'sha256').hexdigest() == APK_SHA
    baseline = out / 'baseline'
    baseline.mkdir()
    with ZipFile(apk) as z:
        for name in z.namelist():
            prefix = 'assets/addons/'
            if not name.startswith(prefix) or name.endswith('/'):
                continue
            relative = name[len(prefix):]
            if relative.split('/')[0] not in module_bundle.IDS:
                continue
            assert '..' not in Path(relative).parts
            dest = baseline / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(name))
    payload, old = module_bundle.build(baseline)
    assert len(old) == 78 and sha(payload) == OLD_MANIFEST
    assert payload == (baseline / CC / M).read_bytes()
    verifier = out / 'verify-modules'
    run('g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
        FIRST / 'verify_module_bundle.cpp', FIRST / 'isolated-native/InfinityModuleManifest.cpp',
        '-lcrypto', '-o', verifier)
    original_auth = verify_native(baseline, verifier)
    candidate = out / 'candidate'
    shutil.copytree(baseline, candidate)
    overlay = ROOT / 'repairs/infinity-only-performance-2103425/overlay' / CC
    for name in ('provider_inventory.py', 'native_search_compatibility.py'):
        raw = (overlay / name).read_bytes()
        assert raw == subprocess.check_output(['git', 'show', SOURCE + ':' + str((overlay / name).relative_to(ROOT))])
        (candidate / CC / name).write_bytes(raw)
    source = (candidate / CC / 'provider_inventory.py').read_bytes()
    start = source.index(b"    if not operations and addon_id in ('plugin.video.umbrella', 'plugin.video.pov'):\n")
    end = source.index(b"    if not operations:\n        operations = _automatic_search", start)
    assert source[:start] + source[end:] == old[CC + '/provider_inventory.py']
    new, files = module_bundle.build(candidate)
    assert len(files) == 79 and sha(new) == NEW_MANIFEST
    assert new.splitlines()[:3] == payload.splitlines()[:3]
    differences = {p for p in files if old.get(p) != files[p]}
    assert differences == {CC + '/provider_inventory.py', CC + '/native_search_compatibility.py'}
    (candidate / CC / M).write_bytes(new)
    (candidate / CC / (M + '.sig')).unlink()
    save(out / 'PREFLIGHT.json', dict(status='PASS_EXACT462_TWO_SOURCE_REBIND',
         source=run('git', 'rev-parse', 'HEAD').strip(), baseline_apk_sha256=APK_SHA,
         baseline=inventory(baseline), candidate=inventory(candidate), policy=policy,
         original_native_authentication=original_auth, unsigned_manifest_sha256=sha(new),
         allowed_source_changes=sorted(differences), original_records=78, new_records=79,
         preserved_original_source_records=77, version='0.3.5.61', apk_version=2103462,
         host_provider_verification_reused=42435806833, Android='NOT_RUN', Fold='NOT_RUN'))


def archive(root, target):
    with ZipFile(target, 'w', compression=ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted((root / CC).rglob('*')):
            if not p.is_file():
                continue
            info = ZipInfo(str(p.relative_to(root)), date_time=(2026, 11, 8, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, p.read_bytes())
    with ZipFile(target) as z:
        expected = {p: d for p, d in inventory(root).items() if p.startswith(CC + '/')}
        assert len(z.namelist()) == len(expected) and z.testzip() is None
        assert {n: sha(z.read(n)) for n in z.namelist()} == expected


def host_install_recovery(out):
    """Real unchanged Java verifier/installer; host ZIP transport, not Android GUI."""
    baseline, candidate = out / 'baseline', out / 'candidate'
    reference = json.loads((ROOT / 'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/CC-AUDIT-REFERENCE.json').read_text())
    source = module_dex.source()
    assert sha(source.encode()) == reference['java_source_sha256']
    assert {str(p.relative_to(FIRST)): sha(p.read_bytes()) for p in (FIRST / 'host-java').rglob('*.java')} == reference['host_java_sha256']
    rows = []
    with tempfile.TemporaryDirectory(prefix='zip-host-', dir=out) as temporary:
        temp = Path(temporary)
        java = temp / 'InfinityInstalledCheckpointInstaller.java'
        java.write_text(source)
        classes = temp / 'classes'
        classes.mkdir()
        run('javac', '--release', '8', '-g:none', '-d', classes, java,
            *sorted((FIRST / 'host-java').rglob('*.java')))
        def fixture(label):
            storage = temp / label
            root = storage / '.kodi/addons'
            shutil.copytree(baseline, root)
            sentinel = storage / '.kodi/userdata/addon_data/sentinel/settings.xml'
            sentinel.parent.mkdir(parents=True)
            sentinel.write_bytes(b'preserve user data')
            return storage, root, sentinel
        def call(storage):
            return subprocess.run(['java', '-cp', str(classes), 'com.projectinfinity.kodi.Main',
                                   str(storage), str(baseline.parent / 'apk-assets')], capture_output=True, text=True)
        assets = baseline.parent / 'apk-assets/addons'
        shutil.copytree(baseline, assets)
        storage, root, sentinel = fixture('complete')
        with ZipFile(out / 'internal-signed' / (CC + '-0.3.5.61-2103462-umbrella-pov.zip')) as z:
            z.extractall(root)
        result = call(storage)
        assert result.returncode == 0 and 'VERIFIED_VERSION=0.3.5.61' in result.stdout, result.stderr
        assert inventory(root) == inventory(candidate) and sentinel.read_bytes() == b'preserve user data'
        rows.append(dict(case='complete_same_version_ZIP_with_original462_APK_assets', result='PASS_REAL_JAVA_HOST'))
        for label, names in [('code_only', ['provider_inventory.py', 'native_search_compatibility.py']),
                             ('manifest_only', [M]), ('signature_only', [M + '.sig'])]:
            storage, root, sentinel = fixture(label)
            for name in names:
                shutil.copyfile(candidate / CC / name, root / CC / name)
            before = inventory(storage)
            result = call(storage)
            assert result.returncode != 0 and inventory(storage) == before
            # Exact signed original ZIP restores the old generation. Added unknown
            # helper may remain on disk; it is unreferenced by the original sources.
            with ZipFile(out / 'internal-signed' / (CC + '-0.3.5.61-2103462-original-recovery.zip')) as z:
                z.extractall(root)
            assert call(storage).returncode == 0
            assert all((root / p).read_bytes() == (baseline / p).read_bytes() for p in inventory(baseline))
            assert sentinel.read_bytes() == b'preserve user data'
            rows.append(dict(case=label, result='PASS_REFUSAL_THEN_ORIGINAL_SIGNED_ZIP_RECOVERY', refusal=result.stderr.strip()))
        storage, root, sentinel = fixture('unknown_source')
        (root / CC / 'provider_inventory.py').write_bytes(b'unknown source must remain')
        before = inventory(storage)
        assert call(storage).returncode != 0 and inventory(storage) == before
        rows.append(dict(case='unknown_installed_source', result='PASS_REFUSAL_PRESERVES_ALL_BYTES'))
    save(out / 'internal-signed/HOST-INSTALL-RECOVERY.json', dict(status='PASS_FIVE_FOCUSED_HOST_CASES',
         cases=rows, original_installer_source_sha256=sha(source.encode()),
         Android_GUI='NOT_RUN', physical_Fold='NOT_RUN', shutdown='NOT_SELECTED'))


def sign(out):
    proof = json.loads((out / 'PREFLIGHT.json').read_text())
    assert proof['source'] == run('git', 'rev-parse', 'HEAD').strip()
    scope()
    for name in ('baseline', 'candidate'):
        assert inventory(out / name) == proof[name], 'STAGED_SOURCE_CHANGED'
    marker = out / 'candidate' / CC / M
    assert module_bundle.build(out / 'candidate')[0] == marker.read_bytes()
    assert sha(marker.read_bytes()) == NEW_MANIFEST
    publish = out / 'internal-signed'
    publish.mkdir()
    with tempfile.TemporaryDirectory(prefix='infinity-original-module-sign-') as temporary:
        temp = Path(temporary)
        key = temp / 'original.jks'
        key.touch(mode=0o600)
        key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'], validate=True))
        classes = temp / 'classes'
        classes.mkdir()
        run('javac', '--release', '8', '-g:none', '-d', classes, FIRST / 'SignInfinityModules.java')
        env = {n: os.environ[n] for n in ('PATH', 'JAVA_HOME', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS')}
        signed = run('java', '-cp', classes, 'SignInfinityModules', key, marker, env=env)
    signed += verify_native(out / 'candidate', out / 'verify-modules')
    (publish / 'MODULE-AUTHENTICATION.txt').write_text(signed)
    for root, suffix in [('candidate', 'umbrella-pov'), ('baseline', 'original-recovery')]:
        archive(out / root, publish / (CC + '-0.3.5.61-2103462-' + suffix + '.zip'))
    host_install_recovery(out)
    checksums = {p.name: sha(p.read_bytes()) for p in publish.glob('*.zip')}
    (publish / 'SHA256SUMS').write_text(''.join(h + '  ' + n + '\n' for n, h in sorted(checksums.items())))
    proof.update(status='SIGNED_COMPLETE_ZIPS_HOST_VERIFIED_ANDROID_DELIVERY_BLOCKED',
                 artifacts=checksums, new_manifest_sha256=NEW_MANIFEST,
                 certificate_sha256='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7',
                 Android='NOT_RUN', Fold='NOT_RUN', public_release=False,
                 unchanged_APK_DEX_native_skin_Cobra_providers_userdata=True)
    save(publish / 'BUILD-RECEIPT.json', proof)
    (publish / 'DELIVERY-HOLD.txt').write_text('SIGNED INTERNAL CANDIDATE. Not cleared for installation: actual Android standalone ZIP install/recovery and fresh installed inventory are still required. No APK rebuild or crash repair is included.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['preflight', 'sign'])
    parser.add_argument('--apk', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.operation == 'preflight':
        preflight(args.apk.resolve(), args.out.resolve())
    else:
        sign(args.out.resolve())
