"""Authenticate this owner's fixed source evidence; no provider execution.

Local staging only. Account settings/databases are neither inputs nor outputs.
"""
import argparse
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import unittest
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CC = 'script.infinity.commandcenter'
TRAKT = 'script.module.tmdbhelper.sync.trakt'
ARCHIVE = 'e14b1e9c8441e78ce5c930dea8c7a5885053011d531df9ec51377fcb18298b65'
API = Path('resources/lib/tmdbhelper_sync_trakt/api')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_members(z):
    rows = z.infolist()
    assert 0 < len(rows) <= 10000 and sum(i.file_size for i in rows) <= 64 * 1024 * 1024
    assert len({i.filename.casefold() for i in rows}) == len(rows)
    for i in rows:
        assert i.file_size <= 8 * 1024 * 1024 and not i.flag_bits & 1
        assert (not i.filename.startswith('/') and '\\' not in i.filename and ':' not in i.filename
                and not any(p in ('', '.', '..') for p in i.filename.split('/')))
        assert not stat.S_ISLNK(i.external_attr >> 16)
        assert not any(p.casefold() in ('addon_data', 'userdata', 'database', 'profile') for p in i.filename.split('/'))
        assert not i.filename.lower().endswith(('.db', '.sqlite', '.sqlite3', '-wal', '-shm', '-journal', '.pyc', '.pyo'))
    assert z.testzip() is None
    return [i.filename for i in rows]


def audit(archive, out, host=False):
    raw = archive.read_bytes()
    assert sha(raw) == ARCHIVE
    out.mkdir(parents=True, exist_ok=False)
    exported = out / 'installed'
    exported.mkdir()
    archives, receipts = {}, {}
    with ZipFile(io.BytesIO(raw)) as outer:
        safe_members(outer)
        for row in json.loads(outer.read('SHA256-MANIFEST.json'))['entries']:
            matches = [n for n in outer.namelist() if n.rsplit('/', 1)[-1] == row['filename']]
            assert len(matches) == 1
            data = outer.read(matches[0])
            assert len(data) == row['bytes'] and sha(data) == row['sha256']
        for name in outer.namelist():
            if not name.startswith('device-exports/') or not name.endswith('.zip'):
                continue
            data = outer.read(name)
            archives[name] = sha(data)
            with ZipFile(io.BytesIO(data)) as z:
                names = safe_members(z)
                manifests = [n for n in names if n == 'KHC_ADDON_EXPORT_MANIFEST.json']
                if manifests:
                    receipt = json.loads(z.read(manifests[0]))
                    assert receipt['includes_saved_data'] is False
                    assert set(names) == set(receipt['files']) | set(manifests)
                    records = [(n, m['size'], m['sha256']) for n, m in receipt['files'].items()]
                else:
                    receipt = json.loads(z.read('UMB-SEARCH-SOURCE-REPORT.json'))
                    assert receipt['file_count'] == 5 and receipt['app_modified'] is False
                    records = [('plugin.video.umbrella/' + m['path'], m['bytes'], m['sha256']) for m in receipt['files']]
                    assert set(names) == {n for n, _, _ in records} | {'UMB-SEARCH-SOURCE-REPORT.json'}
                aid = receipt['addon_id']
                assert aid in (CC, TRAKT, 'plugin.video.umbrella', 'plugin.video.pov') and aid not in receipts
                for path, size, digest in records:
                    assert path.startswith(aid + '/')
                    contents = z.read(path)
                    assert len(contents) == size and sha(contents) == digest
                    target = exported / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(contents)
                receipts[aid] = dict(files=len(records), globally_atomic=False)
    assert len(receipts) == 4
    controller = exported / CC
    manifest = controller / 'INFINITY-MODULES.v1'
    assert sha(manifest.read_bytes()) == '166c994d66503cfe3b3c70b7c4d4a10ce9778cea5e01a9838c9ce83a1a4b34bc'
    subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(ROOT / 'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
                    '-signature', str(controller / 'INFINITY-MODULES.v1.sig'), str(manifest)], check=True, capture_output=True)
    records = {f[2]: f[1] for line in manifest.read_text().splitlines() if (f := line.split('\t'))[0] == 'file'}
    declared = {n: h for n, h in records.items() if n.startswith(CC + '/')}
    assert len(records) == 78 and len(declared) == 62
    assert all(sha((exported / n).read_bytes()) == h for n, h in declared.items())
    files = {p.relative_to(exported).as_posix() for p in controller.rglob('*') if p.is_file()}
    assert files - set(declared) - {CC + '/INFINITY-MODULES.v1', CC + '/INFINITY-MODULES.v1.sig'} == {CC + '/native_search_compatibility.py'}
    overlay = ROOT / 'repairs/infinity-only-performance-2103425/overlay' / CC
    assert (controller / 'native_search_compatibility.py').read_bytes() == (overlay / 'native_search_compatibility.py').read_bytes()
    pins = json.loads((HERE / 'trakt/SOURCE-PINS.json').read_text())
    trakt = exported / TRAKT
    actual = {p.relative_to(trakt).as_posix(): sha(p.read_bytes()) for p in trakt.rglob('*') if p.is_file()}
    expected = pins['upstream_file_pins']
    changed = {n for n in actual if actual[n] != expected.get(n)}
    assert len(actual) == 145 and set(expected) - set(actual) == {'.gitignore'}
    assert changed == {str(API / 'keys.py'), str(API / 'recovery.py')}
    original = (HERE / 'trakt/reference' / API / 'recovery.py').read_text()
    before = 'return bool(self.token.refresh_token and not self.force_login)'
    after = "return bool(self.token.refresh_token and self.token.refresh_token != '1' and not self.force_login)  # AM Lite sentinel guard"
    assert original.count(before) == 1 and (trakt / API / 'recovery.py').read_text() == original.replace(before, after, 1)
    key_tree = ast.parse((trakt / API / 'keys.py').read_bytes())
    assert len(key_tree.body) == 1 and isinstance(key_tree.body[0], ast.Assign)
    assignment = key_tree.body[0]
    assert len(assignment.targets) == 1 and isinstance(assignment.targets[0], ast.Name) and assignment.targets[0].id == 'CLIENT_ID'
    assert isinstance(assignment.value, ast.Constant) and isinstance(assignment.value.value, str) and len(assignment.value.value) == 64
    # Never print the installed application identifier or account credentials.
    staged = out / 'trakt'
    shutil.copytree(trakt, staged / 'reference')
    shutil.copytree(trakt, staged / 'candidate')
    (staged / 'SOURCE-PINS.json').write_text(json.dumps(pins))
    for path, change in pins['changed'].items():
        assert actual[path] == change['before_sha256']
        shutil.copyfile(HERE / 'trakt/candidate' / path, staged / 'candidate' / path)
    proposed = {p.relative_to(staged / 'candidate').as_posix(): sha(p.read_bytes()) for p in (staged / 'candidate').rglob('*') if p.is_file()}
    assert {n for n in actual if actual[n] != proposed[n]} == set(pins['changed'])
    patched = out / 'controller' / CC
    shutil.copytree(controller, patched)
    for name in ('provider_inventory.py', 'native_search_compatibility.py'):
        shutil.copyfile(overlay / name, patched / name)
    report = dict(status='PASS_ACTUAL_INSTALLED_SOURCE_AUTHENTICATION_AND_SCOPED_INTEGRATION', archive_sha256=ARCHIVE,
                  archives=archives, receipts=receipts, signed_CC_records=78, exported_CC_records_verified=62,
                  other_shim_source_records=16, CC_signature='ORIGINAL_RSA_PASS', loose_helper='EXACT_APPROVED_BYTES_INACTIVE',
                  installed_Trakt_source_hashes=actual, reference_differences_preserved=sorted(changed),
                  Trakt_candidate_changed=sorted(pins['changed']), Trakt_candidate_unchanged=143,
                  account_or_token_data_read=False, provider_code_executed=False, Android='NOT_RUN', Fold='NOT_RUN')
    if host:
        scan = HERE / 'test_cc62_inventory.py'
        results = {}
        for name, path in [('installed_CC62', controller), ('approved_two_file_overlay', patched)]:
            result = subprocess.run([sys.executable, str(scan), '--worker', '--cc', str(path), '--fixtures', str(exported)], capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            results[name] = json.loads(result.stdout)
        assert all(v['status'] == 'unsupported' for v in results['installed_CC62'].values())
        assert all(v == dict(status='verified', operations=['movie/search', 'tv/search']) for v in results['approved_two_file_overlay'].values())
        report['actual_provider_inventory'] = results
        spec = importlib.util.spec_from_file_location('installed_Trakt_selected_tests', HERE / 'test_trakt_silent_failure.py')
        tests = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tests)
        tests.TRAKT = staged
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(tests.TraktSilentFailure)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert result.wasSuccessful() and result.testsRun == 13
        for candidate in (False, True):
            with tests.environment(candidate=candidate) as state:
                state.api.user_token.value = json.dumps(dict(access_token='synthetic-access', refresh_token='1', created_at=0, expires_in=1))
                account = state.api.user_token.value
                assert state.stored.get_authorization() is None and state.http_calls == 0
                assert state.properties['TraktRefreshTimeStamp'] == 1300 and state.api.user_token.value == account
                assert bool(state.dialogs) is (not candidate)
        report['actual_Trakt_host'] = dict(existing_cases=13, preserved_AM_Lite_sentinel_case=1, passed=14, real_SDK_or_accounts=False)
    (out / 'DEVICE-SOURCE-VERIFICATION.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS source evidence and original CC signature; Trakt installed customizations preserved; Android NOT RUN')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--host', action='store_true')
    a = p.parse_args()
    audit(a.archive, a.out, a.host)
