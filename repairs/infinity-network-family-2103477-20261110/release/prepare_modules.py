"""Exact signed77 network/recovery module staging; no keys, APK or registry writes."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
ROOT = TASK.parents[1]
CC = 'script.infinity.commandcenter'
SKIN = 'skin.infinity.diggz'
BASE_APK = '93eb081cd6a86ff9cf1cb9aa75bc6d9087cd9c982fb46e0a9baa12c12aa9af22'
BASE_MANIFEST = '63110023bf70f4ec32b0ab4750b3c1293a4976aa58cdfd1afbcd55027758b371'
PAIRS = [('candidate', '0.3.5.76', '1.0.5.271', 81),
         ('recovery', '0.3.5.77', '1.0.5.272', 80)]
HUB = 'unified/Custom_1191_InfinitySystemHub.xml'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def hashes(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in sorted(root.rglob('*')) if p.is_file()}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def tools():
    path = ROOT/'repairs/infinity-tracking-integration-2103469-20261108/prepare_tracking_release.py'
    assert sha(path.read_bytes()) == '49c4d49bd679b2dd2ae2819ab45b8a673d4b362f80fc30090223553d3abc9e0b'
    spec = importlib.util.spec_from_file_location('retained_original_release_tools', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_tools()


def scalar(raw, key, before, after):
    old = ('"'+key+'": '+json.dumps(before)).encode()
    new = ('"'+key+'": '+json.dumps(after)).encode()
    assert raw.count(old) == 1, ('EXACT_METADATA_PREIMAGE', key)
    return raw.replace(old, new, 1)


def skin_metadata(baseline, version, hub):
    addon = baseline['addon.xml']
    assert addon.count(b'version="1.0.5.270"') == 1
    addon = addon.replace(b'version="1.0.5.270"', ('version="'+version+'"').encode(), 1)
    skin = baseline['infinity-skin.json']
    for key, old, new in [('candidate', 270, int(version.rsplit('.', 1)[1])),
                          ('skin_version', '1.0.5.270', version),
                          ('version', '1.0.5.270', version)]:
        skin = scalar(skin, key, old, new)
    manifest = baseline['Infinity-Protected-Manifest.json']
    original = json.loads(manifest)
    assert len(original['protected_files']) == 948
    updated = {HUB: hub, 'addon.xml': addon, 'infinity-skin.json': skin}
    for name, raw in updated.items():
        old = ('"'+name+'": "'+original['protected_files'][name]+'"').encode()
        new = ('"'+name+'": "'+sha(raw)+'"').encode()
        assert manifest.count(old) == 1
        manifest = manifest.replace(old, new, 1)
    for key, old, new in [('candidate', 270, int(version.rsplit('.', 1)[1])),
                          ('skin_version', '1.0.5.270', version),
                          ('candidate_version', '1.0.5.270', version)]:
        manifest = scalar(manifest, key, old, new)
    after = json.loads(manifest)
    assert set(after['protected_files']) == set(original['protected_files'])
    assert {k for k in original['protected_files']
            if after['protected_files'][k] != original['protected_files'][k]} <= set(updated)
    for name, raw in updated.items():
        assert after['protected_files'][name] == sha(raw)
    original_copy, after_copy = dict(original), dict(after)
    for key in ('candidate', 'skin_version', 'candidate_version', 'protected_files'):
        original_copy.pop(key); after_copy.pop(key)
    assert original_copy == after_copy, 'UNRELATED_SKIN_METADATA_CHANGED'
    updated['Infinity-Protected-Manifest.json'] = manifest
    return updated


def stage(apk, out):
    assert not out.exists(), 'FRESH_STAGING_ONLY'
    assert sha(apk.read_bytes()) == BASE_APK, 'EXACT_SIGNED77_INPUT'
    t = tools()
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    pins = json.loads((TASK/'SOURCE-PINS.json').read_text())
    for group, entries in pins.items():
        for name, digest in entries.items():
            assert sha((TASK/group/name).read_bytes()) == digest, name
    baseline = out/'baseline-modules'
    skin = {}
    with ZipFile(apk) as z:
        t.validate_names(z)
        for name in z.namelist():
            if any(name.startswith('assets/addons/'+aid+'/') for aid in t.module_bundle.IDS):
                relative = name[len('assets/addons/'):]
                if name.endswith('/'):
                    continue
                assert t.module_bundle.safe(relative), relative
                dest = baseline/relative; dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(name))
        for name in ('addon.xml', 'infinity-skin.json', 'Infinity-Protected-Manifest.json', HUB):
            skin[name] = z.read('assets/addons/'+SKIN+'/'+name)
    raw, before = t.module_bundle.build(baseline)
    assert len(before) == 80 and sha(raw) == BASE_MANIFEST
    assert raw == (baseline/CC/t.module_bundle.MANIFEST).read_bytes()
    subprocess.run(['openssl', 'dgst', '-sha256', '-verify',
                    str(ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
                    '-signature', str(baseline/CC/(t.module_bundle.MANIFEST+'.sig')),
                    str(baseline/CC/t.module_bundle.MANIFEST)], check=True, capture_output=True)
    module_records = {}
    for label, cc_version, skin_version, count in PAIRS:
        work = out/label; modules = work/'modules'
        shutil.copytree(baseline, modules)
        if label == 'candidate':
            for name in ('default.py', 'resources/settings.xml', 'network_connections.py'):
                target = modules/CC/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((TASK/'overlay'/CC/name).read_bytes())
        addon = modules/CC/'addon.xml'
        original = addon.read_bytes()
        assert original.count(b'version="0.3.5.75"') == 1
        addon.write_bytes(original.replace(b'version="0.3.5.75"', ('version="'+cc_version+'"').encode(), 1))
        (modules/CC/(t.module_bundle.MANIFEST+'.sig')).unlink()
        manifest, files = t.module_bundle.build(modules)
        assert len(files) == count
        modified = {name for name in before if before[name] != files.get(name)}
        expected = {CC+'/addon.xml'}
        if label == 'candidate':
            expected |= {CC+'/default.py', CC+'/resources/settings.xml'}
        assert modified == expected
        assert set(files)-set(before) == ({CC+'/network_connections.py'} if label == 'candidate' else set())
        assert not set(before)-set(files)
        (modules/CC/t.module_bundle.MANIFEST).write_bytes(manifest)
        hub = (TASK/'overlay'/SKIN/HUB).read_bytes() if label == 'candidate' else skin[HUB]
        skin_files = skin_metadata(skin, skin_version, hub)
        for name, raw in skin_files.items():
            target = work/'skin'/name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        record = dict(label=label, baseline=2103477, baseline_APK_sha256=BASE_APK,
                      source_commit=source, CC=cc_version, skin=skin_version,
                      authenticated_source_count=count, modules=hashes(modules),
                      skin_files=hashes(work/'skin'), manifest_sha256=sha(manifest),
                      functional_recovery_to_2103477=label == 'recovery',
                      resolver_replacement=False, Cobra_changes=False,
                      APK=False, APK_version_reserved=False, signature='PENDING_ORIGINAL_SIGNER')
        save(work/'INPUTS.json', record); module_records[label] = sha((work/'INPUTS.json').read_bytes())
    save(out/'PREPARATION.json', dict(baseline=2103477, original_tools=t.pins,
         source_commit=source, inputs=module_records, source_pins=pins,
         original_signer='UNCHANGED_SignInfinityModules.java', APK=False,
         registry_mutated=False, Cobra_changes=False, production_resolver='ORIGINAL_KODI',
         DNS_acceptance='OWNER_APPROVED_BASELINE_COMPARISON_CONTRACT',
         helper_experiments='PARKED_EXCLUDED_FROM_RELEASE'))
    print('PASS exact signed77 baseline; candidate81/recovery80; only approved network source and required version/integrity metadata staged')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    stage(args.apk, args.out)
