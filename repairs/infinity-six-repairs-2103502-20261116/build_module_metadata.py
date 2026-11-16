"""Four reviewed metadata overlays only, derived byte-for-byte from exact signed502."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
SKIN = 'skin.infinity.diggz/'
NAMES = ['script.kodihealthcenter/addon.xml', SKIN + 'addon.xml',
         SKIN + 'infinity-skin.json', SKIN + 'Infinity-Protected-Manifest.json']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def once(data, before, after):
    assert data.count(before) == 1, repr(before)
    return data.replace(before, after, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('apk', type=Path)
    args = parser.parse_args()
    with args.apk.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == json.loads((HERE / 'BASELINE.json').read_text())['APK_sha256']
    scope = json.loads((HERE / 'SCOPE.json').read_text())['production_allowlist']
    pins = {r.get('APK_member'): r.get('before_sha256') for r in scope}
    with ZipFile(args.apk) as apk:
        before = {n: apk.read('assets/addons/' + n) for n in NAMES}
        for name, data in before.items():
            assert sha(data) == pins['assets/addons/' + name], name
        candidate = dict(before)
        candidate[NAMES[0]] = once(before[NAMES[0]], b'version="2.5.27"', b'version="2.5.28"')
        candidate[NAMES[1]] = once(before[NAMES[1]], b'version="1.0.5.274"', b'version="1.0.5.275"')
        for key, old, new in [('version', '"1.0.5.274"', '"1.0.5.275"'),
                              ('skin_version', '"1.0.5.274"', '"1.0.5.275"'),
                              ('candidate', '274', '275')]:
            candidate[NAMES[2]] = once(candidate[NAMES[2]],
                ('\n  "' + key + '": ' + old + ',').encode(),
                ('\n  "' + key + '": ' + new + ',').encode())
        manifest = json.loads(before[NAMES[3]])
        for key, expected in manifest['protected_files'].items():
            assert sha(apk.read('assets/addons/' + SKIN + key)) == expected, 'Baseline protected hash: ' + key
        for key, old, new in [('candidate_version', '"1.0.5.274"', '"1.0.5.275"'),
                              ('skin_version', '"1.0.5.274"', '"1.0.5.275"'),
                              ('candidate', '274', '275')]:
            candidate[NAMES[3]] = once(candidate[NAMES[3]],
                ('\n  "' + key + '": ' + old + ',').encode(),
                ('\n  "' + key + '": ' + new + ',').encode())
        affected = ['addon.xml', 'infinity-skin.json', 'unified/VideoOSD.xml',
                    'unified/custom_1199_InfinityVideoLock.xml']
        for key in affected:
            source = candidate[SKIN + key] if SKIN + key in candidate else (HERE / 'overlay' / SKIN / key).read_bytes()
            old = manifest['protected_files'][key]
            candidate[NAMES[3]] = once(candidate[NAMES[3]],
                ('"' + key + '": "' + old + '"').encode(),
                ('"' + key + '": "' + sha(source) + '"').encode())
        # Semantic guards supplement the byte-preserving replacements.
        old_skin, new_skin = (json.loads(x) for x in (before[NAMES[2]], candidate[NAMES[2]]))
        assert {k for k in old_skin.keys() | new_skin.keys() if old_skin.get(k) != new_skin.get(k)} == {'version', 'skin_version', 'candidate'}
        new_manifest = json.loads(candidate[NAMES[3]])
        assert {k for k in manifest.keys() | new_manifest.keys() if manifest.get(k) != new_manifest.get(k)} == {'candidate', 'candidate_version', 'skin_version', 'protected_files'}
        assert manifest['protected_files'].keys() == new_manifest['protected_files'].keys()
        assert {k for k in manifest['protected_files'] if manifest['protected_files'][k] != new_manifest['protected_files'][k]} == set(affected)
        assert new_skin['candidate_locked'] is False and new_manifest['candidate_locked'] is False
        for key, expected in new_manifest['protected_files'].items():
            path = HERE / 'overlay' / SKIN / key
            data = candidate.get(SKIN + key)
            if data is None:
                data = path.read_bytes() if path.is_file() else apk.read('assets/addons/' + SKIN + key)
            assert sha(data) == expected, 'Candidate protected hash: ' + key
        for name, data in candidate.items():
            target = HERE / 'overlay' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        report = {'status': 'PASS_EXACT_METADATA_AND_PROTECTED_HASHES', 'baseline_apk_sha256': digest,
                  'files': {n: {'before': sha(before[n]), 'after': sha(candidate[n])} for n in NAMES},
                  'protected_files_verified': len(manifest['protected_files']),
                  'changed_protected_entries': affected,
                  'all_other_metadata_bytes': 'UNCHANGED', 'APK_assembly': 'NOT_RUN',
                  'runtime_profile_selection': 'NOT_VERIFIED; equal or higher profile version may take precedence',
                  'profile_mutation': 'NONE in this build; retained CC may refresh version-bound UI backup at runtime',
                  'acceptance': 'PENDING'}
        (HERE / 'METADATA-PRESERVATION.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
