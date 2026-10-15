#!/usr/bin/env python3
"""Exercise the production VFS/ledger with real Python SQLite connections.

Use a Python linked to the same SQLite shared library as the small C ABI bridge.
The bridge invokes production code; it does not simulate transactions or seals.
"""
import argparse
import ctypes
import json
import shutil
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
BRIDGE = r'''
#define INFINITY_DATABASE_BARRIER_TEST
#include "dbwrappers/InfinitySQLiteVFS.h"
#include "dbwrappers/InfinityDatabaseBarrier.h"
extern "C" {
int install() { return InfinitySQLiteVFS::Install(); }
const char* version() { return sqlite3_libversion(); }
int begin(const char* profile, const char* cache) {
  return InfinityScriptPersistence::BeginWriteProtection(17, {profile}, {cache}) &&
         InfinityScriptPersistence::CloseParticipantWrites(17) && InfinityDatabaseBarrier::Begin(17);
}
int ready() { return InfinityDatabaseBarrier::GetSnapshot().Ready(); }
int seal() { return InfinityDatabaseBarrier::Seal(17) && InfinityScriptPersistence::SealEssentialWrites(17); }
int authorized() { return InfinityScriptPersistence::EssentialWritesAuthorized(17); }
const char* blockers() {
  static std::string result; result.clear();
  for (const auto& why : InfinityScriptPersistence::EssentialWrites().blockers) result += why + "\n";
  return result.c_str();
}
const char* denials() {
  static std::string result; result.clear();
  auto& s = InfinityScriptPersistence::Get(); std::lock_guard<std::mutex> lock(s.mutex);
  for (const auto& why : s.protection.denials) result += why + "\n";
  return result.c_str();
}
int tracked(const char* path) {
  auto& s = InfinityScriptPersistence::Get(); std::lock_guard<std::mutex> lock(s.mutex);
  return s.protection.paths.count(path);
}
}
'''

def child(library, case):
    lib = ctypes.CDLL(str(library))
    lib.begin.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    lib.tracked.argtypes = [ctypes.c_char_p]
    lib.version.restype = lib.blockers.restype = lib.denials.restype = ctypes.c_char_p
    assert lib.version().decode() == sqlite3.sqlite_version
    assert lib.install()
    with tempfile.TemporaryDirectory(prefix='essential-sqlite-') as folder:
        root = Path(folder)
        profile, cache = root/'profile', root/'cache'
        profile.mkdir(); cache.mkdir()
        shared, private = profile/'history.db', cache/'private.db'
        protected = sqlite3.connect(shared, timeout=0)
        if 'wal' in case:
            assert protected.execute('PRAGMA journal_mode=WAL').fetchone()[0] == 'wal'
        protected.execute('CREATE TABLE history(position)')
        protected.commit()
        if case.startswith('attach'):
            conn = sqlite3.connect(private, timeout=0)
            conn.execute('ATTACH DATABASE ? AS shared', (str(shared),))
            conn.execute('INSERT INTO shared.history VALUES(321)')
            assert lib.tracked(str(shared).encode())
        elif case.startswith('optional'):
            conn = sqlite3.connect(private, timeout=0)
            conn.execute('CREATE TABLE cache(value)')
            conn.execute('INSERT INTO cache VALUES(99)')
        else:
            conn = protected
            conn.execute('INSERT INTO history VALUES(321)')
        if case in ('late-write', 'late-write-wal', 'uri-vfs'):
            conn.commit()
        assert lib.begin(str(profile).encode(), str(cache).encode())
        if case.startswith('optional'):
            assert conn.in_transaction
            assert lib.ready(), lib.blockers()
            assert lib.seal(), lib.blockers()
            # Optional transaction may remain unfinished through authorization.
            assert lib.authorized() and conn.in_transaction
            conn.commit()  # Test cleanup; not a shutdown requirement.
        elif case in ('late-write', 'late-write-wal', 'uri-vfs'):
            assert lib.ready(), lib.blockers()
            assert lib.seal(), lib.blockers()
            try:
                if case == 'uri-vfs':
                    conn = sqlite3.connect(shared.as_uri()+'?vfs=unix-excl', uri=True, timeout=0)
                conn.execute('INSERT INTO history VALUES(999)')
                conn.commit()
                raise AssertionError('protected SQLite write crossed seal')
            except sqlite3.DatabaseError:
                pass
            assert lib.authorized(), lib.blockers()
        else:
            assert conn.in_transaction
            assert not lib.ready(), 'native barrier ignored Python/ATTACH transaction'
            assert not lib.seal(), 'seal accepted active protected transaction'
            assert b'pending_protected_sqlite_transaction' in lib.blockers()
            try: conn.commit()
            except sqlite3.DatabaseError:
                print(lib.denials(), file=sys.stderr)
                raise
            assert lib.ready(), lib.blockers()
            assert lib.seal(), lib.blockers()
            assert lib.authorized()
        # Read independently after the original connection's write attempt.
        # mode=ro prevents new write-open admission during the seal.
        readback = sqlite3.connect(shared.as_uri()+'?mode=ro&immutable=1', uri=True)
        if 'wal' not in case:
            rows = readback.execute('SELECT position FROM history').fetchall()
            assert rows == ([] if case.startswith('optional') else [(321,)]), rows
        readback.close()
        # Connection close may attempt a WAL checkpoint. No interpreter teardown
        # is part of the authorization. The child process exits after evidence.
        print(json.dumps({'case': case, 'result':'PASS', 'sqlite':sqlite3.sqlite_version,
                          'actual_python_sqlite':True, 'actual_runtime_vfs':True,
                          'folder':folder, 'expected':[] if case.startswith('optional') else [[321]]}))
        sys.stdout.flush()
        import os
        os._exit(0)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sqlite-include', type=Path)
    p.add_argument('--library', type=Path)
    p.add_argument('--case')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if args.library:
        child(args.library, args.case)
        return
    cases = ['pending', 'pending-wal', 'attach', 'attach-wal',
             'optional-pending', 'late-write', 'late-write-wal', 'uri-vfs']
    with tempfile.TemporaryDirectory(prefix='runtime-sqlite-build-') as folder:
        root = Path(folder); source = root/'bridge.cpp'; library=root/'bridge.so'
        source.write_text(BRIDGE)
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-fPIC','-shared','-pthread',
                        '-I'+str(HERE/'runtime/xbmc'), '-I'+str(args.sqlite_include),
                        str(source), '-l:libsqlite3.so.0','-o',str(library)],check=True)
        results=[]
        for case in cases:
            process=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--library',str(library),'--case',case],
                                   capture_output=True,text=True,timeout=15)
            results.append({'case':case,'exit_code':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
            if process.returncode == 0:
                receipt=json.loads(process.stdout)
                folder=Path(receipt['folder'])
                with sqlite3.connect(folder/'profile/history.db') as reopened:
                    assert [list(row) for row in reopened.execute('SELECT position FROM history')] == receipt['expected']
                    assert reopened.execute('PRAGMA integrity_check').fetchone() == ('ok',)
                results[-1]['essential_rows_verified_after_host_process_death']=True
                shutil.rmtree(folder)
            print(case, process.returncode, process.stderr, flush=True)
        report={'scope':'production native VFS and ledger with real Python SQLite',
                'cases':results,'all_passed':all(r['exit_code']==0 for r in results),
                'android_verified':False,'apk_deliverable':False}
        if args.out: args.out.write_text(json.dumps(report,indent=2)+'\n')
        if not report['all_passed']: raise SystemExit(1)

if __name__ == '__main__': main()
