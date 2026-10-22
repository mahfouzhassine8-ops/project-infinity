"""Source-backed native observer tests; host outcomes are not Fold acceptance."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import tempfile
import patch

HERE = Path(__file__).resolve().parent
PROVIDERS = ('plugin.video.thecrew', 'plugin.video.umbrella', 'plugin.video.seren',
             'plugin.video.pov', 'plugin.video.future_provider_7fa29')
CASES = ('normal', 'invalid', 'partial', 'foreign', 'subclass', 'buffered',
         'transaction', 'sqlite', 'sqlite-busy-recovered', 'sqlite-busy-pending', 'namespace', 'child-thread', 'late',
         'pending-native', 'opaque', 'namespace-unobserved', 'namespace-recreated',
         'namespace-symlink', 'namespace-fsync', 'namespace-parent-recreated', 'namespace-barrier',
         'namespace-concurrent-unknown', 'namespace-unknown-later', 'namespace-nested-mutation', 'profile-transaction',
         'buffered-finalize','buffered-phase2','child-drain','clean-io-late-write',
         'clean-io-override','clean-io-retarget','empty-io-close','layered-drain','cached-drain','multi-interpreter-drain','composite-drain','descriptor-stale-drain','descriptor-stale-replaced','descriptor-stale-symlink','descriptor-literal-deleted','descriptor-stale-unlinked','descriptor-observed-unlinked')


def readback(root, case):
    """Read independently after the test process exits; never infer saved bytes from a seal."""
    profile = root/'profile'
    expected = {'normal': b'textbytesarray', 'partial': b'ab'}
    preserved = {'invalid', 'buffered', 'transaction', 'sqlite', 'namespace', 'child-thread', 'late'}
    io_cases={'sqlite-busy-recovered','sqlite-busy-pending','composite-drain','multi-interpreter-drain','buffered-finalize','buffered-phase2','child-drain','clean-io-late-write','clean-io-override','clean-io-retarget','empty-io-close','layered-drain','cached-drain'}
    preserved |= io_cases
    if case.startswith('descriptor-'):preserved.add(case)
    data = (profile/'provider-settings.json').read_bytes()
    assert data == expected.get(case, b'preserved' if case in preserved else b''), (case, data)
    if case in ('descriptor-stale-unlinked','descriptor-observed-unlinked'):assert not (profile/'resume.json').exists()
    if case=='descriptor-stale-drain':assert (profile/'resume.json').read_bytes()==b'resume preserved'
    if case=='descriptor-literal-deleted':assert (profile/'resume.json (deleted)').read_bytes()==b'resume preserved'
    if case=='descriptor-stale-replaced':assert (profile/'resume.json').read_bytes()==b'sentinel'
    if case in ('descriptor-stale-replaced','descriptor-stale-symlink'):assert (profile/'moved-buffer').read_bytes()==b''
    if case=='buffered' or case in io_cases:
        assert (profile/'resume.json').read_bytes()==(b'' if case=='empty-io-close' else b'resume preserved')
    if case in ('child-drain','composite-drain'):assert (profile/'worker').read_bytes()==b'worker state'
    if case=='clean-io-retarget':assert (profile/'retarget-target').read_bytes()==b'sentinel'
    if case in ('namespace','composite-drain'): assert (profile/'state').read_bytes() == b'state'
    if case == 'child-thread': assert (profile/'child').read_bytes() == b'owned'
    if case in ('foreign', 'subclass'): assert (profile/case).read_bytes() == b'changed'
    if case == 'sqlite':
        for leaf, table, expected in [('history.db', 'history', [(7,)]), ('watched.db', 'watched', [(8,)])]:
            with sqlite3.connect(profile/leaf) as db:
                assert db.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
                assert db.execute('SELECT v FROM '+table).fetchall() == expected
    if case.startswith('sqlite-busy-'):
        with sqlite3.connect((profile/'commit.db').resolve().as_uri()+'?mode=ro',uri=True) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
            assert db.execute('SELECT v FROM history').fetchall()==[(1,)]
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--overlay', type=Path, required=True)
    parser.add_argument('--python-source', type=Path)
    parser.add_argument('--python-prefix', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=CASES)
    args = parser.parse_args()
    source, overlay = (p.resolve() for p in (args.source, args.overlay))
    prefix = args.python_prefix.resolve()
    python = args.python_source.resolve() if args.python_source else prefix/'lib'
    xbmc = source / 'xbmc'
    pins = json.loads((source.parent / 'NATIVE-SOURCE-MAP.json').read_text())
    exact = ('xbmc/interfaces/python/typemaps/python.buffer.intm',
             'xbmc/interfaces/legacy/File.cpp', 'xbmc/commons/Buffer.h')
    for path in exact:
        assert patch.sha((source/path).read_bytes()) == pins[path], path
    conversion = (source/exact[0]).read_text().split('%>', 1)[1]
    conversion = conversion.replace('${slarg}', 'value').replace('${api}', 'buffer').replace('${method.@name}', 'write')
    raw = (source/exact[1]).read_text()
    loop = raw.split('bool File::write(XbmcCommons::Buffer& buffer)', 1)[1]
    loop = loop[loop.index('{')+1:loop.rindex('return true;')+len('return true;')]
    # Host has no Kodi language hook. Conversion and every backend/write result
    # branch remain the production implementation, not a Python VFS simulation.
    assert loop.count('DelayedCallGuard dg(languageHook);') == 1
    loop = loop.replace('DelayedCallGuard dg(languageHook);', '')
    code = (HERE/'vfs_harness.cpp.in').read_text().replace('@@WRITE_LOOP@@', loop).replace('@@BUFFER_CONVERSION@@', conversion)
    python_includes = [python/'Include',python] if args.python_source else [prefix/'include/python3.11']
    includes = [overlay/'xbmc/interfaces/python', overlay/'xbmc', xbmc/'interfaces/python',
                xbmc, *python_includes, Path('/usr/local/include')]
    env = dict(os.environ, LD_LIBRARY_PATH=str(python), PYTHONHOME=str(prefix),
               PYTHONPATH=str(prefix/'lib/python3.11')+':'+str(prefix/'lib/python3.11/lib-dynload'),
               PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([str(prefix/'bin/python3.11'), '-c',
        'import ctypes, sqlite3, ssl; assert sqlite3.sqlite_version'], env=env, check=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='universal-persistence-') as tmp:
        tmp = Path(tmp)
        cpp = tmp/'test.cpp'
        cpp.write_text(code)
        common = ['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-Wno-cast-function-type',
                  '-pthread', *['-I'+str(p) for p in includes], str(cpp), '-L'+str(python),
                  '-lpython3.11', '-l:libsqlite3.so.0', '-ldl', '-lm', '-lcrypto', '-Wl,--export-dynamic']
        for label in ('candidate', 'baseline'):
            binary = tmp/(label+'-test')
            command = common+['-DINFINITY_UNIVERSAL_CANDIDATE'] if label == 'candidate' else [v for v in common if v not in ('-I'+str(overlay/'xbmc/interfaces/python'), '-I'+str(overlay/'xbmc'))]
            subprocess.run(command+['-o', str(binary)], check=True)
            for provider in PROVIDERS:
                for case in ((args.case,) if args.case else CASES) if label == 'candidate' else ('invalid',):
                    root = tmp/label/provider/case
                    (root/'profile').mkdir(parents=True)
                    (root/'cache').mkdir()
                    sentinel = root/'profile/existing-user-data.json'
                    sentinel.write_bytes(b'{"resume":37,"watched":["movie-1"],"settings":{"enabled":true}}')
                    sentinel_hash = patch.sha(sentinel.read_bytes())
                    process = subprocess.run([str(binary), case, str(root), provider, label],
                        env=env, capture_output=True, text=True, timeout=30)
                    record = dict(source=label, provider_identity=provider, case=case,
                        exit_code=process.returncode, stdout=process.stdout, stderr=process.stderr)
                    results.append(record)
                    if process.returncode == 0:
                        record['independent_readback_passed'] = readback(root, case)
                        assert patch.sha(sentinel.read_bytes()) == sentinel_hash
                        record['existing_user_data_unchanged'] = True
                    print(label, provider, case, process.returncode, flush=True)
                    if process.returncode:
                        print(process.stderr, flush=True)
            if label == 'candidate' and not args.case:
                root = tmp/'reopen-cycles'
                (root/'profile').mkdir(parents=True); (root/'cache').mkdir()
                marker = root/'profile/untouched'; marker.write_bytes(b'keep across process lifetimes')
                for cycle in range(3):
                    process = subprocess.run([str(binary), 'invalid', str(root), PROVIDERS[-1], label],
                        env=env, capture_output=True, text=True, timeout=30)
                    result = dict(source=label, case='process-reopen-cycle', cycle=cycle,
                        exit_code=process.returncode, stdout=process.stdout, stderr=process.stderr)
                    if process.returncode == 0:
                        result['independent_readback_passed'] = readback(root, 'invalid')
                        assert marker.read_bytes() == b'keep across process lifetimes'
                    results.append(result)
    report = dict(scope='production observer + production Kodi buffer conversion/write loop; host POSIX backend adapter',
        provider_code_executed=False, provider_identities=list(PROVIDERS), results=results,
        passed=all(r['exit_code']==0 for r in results),
        input_hashes={p:pins[p] for p in exact}, source_delta=json.loads((overlay/'SOURCE-DELTA.json').read_text()),
        android_validated=False, physical_fold_verified=False, final_lock=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
