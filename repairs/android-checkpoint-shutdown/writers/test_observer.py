#!/usr/bin/env python3
"""Exercise the real observer against real files/SQLite, one fresh process per case."""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def scenario(name):
    spec = importlib.util.spec_from_file_location('persistence', Path(__file__).with_name('observer.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import sqlite3
    import builtins
    import gc
    import types
    read_connection = sqlite3.connect
    with tempfile.TemporaryDirectory(prefix='infinity-save-') as folder:
        root = Path(folder)
        failures, failure_details, mutations = [], [], []
        def fail(reason, detail=None):
            failures.append(reason)
            if detail is not None:
                failure_details.append((reason, str(detail)))
        vfs = None
        if name.startswith('vfs_'):
            class NativeFile:
                def __init__(self, path, mode=None):
                    self.path, self.mode, self.closed = path, mode, False
                    if name == 'vfs_open_failure' and mode == 'w': raise OSError('native open failed')
                def write(self, value):
                    if name == 'vfs_write_failure': return False
                    self.value = value
                    return True
                def close(self):
                    if name == 'vfs_close_failure' and self.mode == 'w': raise OSError('native close failed')
                    self.closed = True
            def rmdir(path, force=False):
                if isinstance(force, str): raise TypeError("'str' object cannot be interpreted as an integer")
                return True
            vfs = types.SimpleNamespace(File=NativeFile, translatePath=lambda path: str(path),
                copy=lambda a,b: True, rename=lambda a,b: True, delete=lambda p: True,
                mkdir=lambda p: True, mkdirs=lambda p: False if name == 'vfs_mkdirs_failure' else True, rmdir=rmdir)
        observer = module.Observer(fail, lambda path, kind: mutations.append((path, kind)), vfs=vfs)
        database = root / 'state.db'
        connection = sqlite3.connect(database)
        connection.execute('create table state (value)')
        connection.commit()
        if name.startswith('vfs_'):
            connection.close()
            for mode in (None, 'r', 'a'):
                handle = vfs.File(str(root / 'read'), mode) if mode else vfs.File(str(root / 'read'))
                assert isinstance(handle, NativeFile) and handle.mode == mode
                handle.close()
            if name == 'vfs_open_failure':
                try: vfs.File(str(root / 'state'), 'w')
                except OSError: pass
                else: raise AssertionError('VFS open failure was swallowed')
                assert 'vfs_open_for_write_failed' in failures
                for target, attr, original, replacement in reversed(observer.originals):
                    setattr(target, attr, original)
                return
            if name == 'vfs_mkdirs_failure':
                target = str(root / 'missing-parent')
                assert vfs.mkdirs(target) is False
                assert 'vfs_mkdirs_failed' in failures
                assert ('vfs_mkdirs_failed', 'path='+target) in failure_details
                for target_obj, attr, original, replacement in reversed(observer.originals):
                    setattr(target_obj, attr, original)
                return
            handle = vfs.File(str(root / 'state'), 'w')
            assert isinstance(handle, module.VFSFile)
            assert handle.handle.mode == 'w'
            result = handle.write('saved')
            if name == 'vfs_write_failure':
                assert result is False and 'vfs_write_failed' in failures
                handle.close()
            elif name == 'vfs_close_failure':
                try: handle.close()
                except OSError: pass
                else: raise AssertionError('VFS close error was swallowed')
                assert not handle.closed and handle in observer.held_handles
                assert not observer.finish()
                assert 'vfs_close_failed' in failures
            else:
                assert result is True
                assert observer.finish()
                assert handle.closed and handle.handle.closed
                assert not failures, failures
                assert (str(root / 'state'), 'write') in mutations
        elif name == 'committed':
            connection.execute('insert into state values (42)')
            connection.commit()
            connection.close()
            handle = open(root / 'state.json', 'w')
            handle.write('saved')
            assert observer.finish()
            assert handle.closed
            assert not failures, failures
            assert (root / 'state.json').read_text() == 'saved'
            assert read_connection(database).execute('select value from state').fetchall() == [(42,)]
        elif name == 'pending':
            connection.execute('insert into state values (42)')
            try:
                connection.close()
            except sqlite3.ProgrammingError:
                pass
            else:
                raise AssertionError('pending close silently discarded data')
            assert connection.in_transaction
            assert not observer.finish()
            assert connection.execute('select value from state').fetchall() == [(42,)]
            assert read_connection(database).execute('select value from state').fetchall() == []
            connection.rollback()
            connection.close()
            assert any('pending_transaction' in reason for reason in failures)
        elif name == 'collected':
            connection.execute('insert into state values (42)')
            del connection
            gc.collect()
            assert observer.held_connections
            assert not observer.finish()
            retained = next(iter(observer.held_connections))
            assert retained.in_transaction
            assert retained.execute('select value from state').fetchall() == [(42,)]
            retained.rollback()
            retained.close()
        elif name == 'write_failure':
            connection.close()
            if not Path('/dev/full').exists():
                raise RuntimeError('/dev/full required for write failure proof')
            handle = open('/dev/full', 'w')
            handle.write('unsaved')
            try:
                handle.close()
            except OSError:
                pass
            assert failures
            assert not observer.finish()
            assert not handle.closed
            assert observer.held_handles
        elif name == 'binding_replaced':
            connection.close()
            builtins.open = observer.originals[0][2]
            observer.finish()
            assert 'persistence_observer_binding_replaced:open' in failures
        elif name == 'sql_failure':
            try:
                connection.execute('insert into missing_table values (42)')
            except sqlite3.OperationalError:
                pass
            connection.close()
            observer.finish()
            assert 'sqlite_write_failed' in failures
        elif name == 'rollback':
            connection.execute('insert into state values (42)')
            connection.rollback()
            connection.close()
            assert observer.finish()
            assert not failures
            assert read_connection(database).execute('select value from state').fetchall() == []
        elif name == 'nested_directories':
            connection.close()
            target = root / 'health' / 'sessions' / 'session' / 'state.json'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('saved')
            assert observer.finish()
            assert not failures, failures
            assert target.read_text() == 'saved'
        elif name == 'descriptor_cache':
            connection.close()
            class Accessor:
                mkdir = os.mkdir
                opened = os.open
            cached = Accessor()
            cached.mkdir(root / 'cached')
            descriptor = cached.opened(root / 'cached' / 'state', os.O_WRONLY | os.O_CREAT, 0o600)
            os.write(descriptor, b'saved')
            os.close(descriptor)
            assert observer.finish()
            assert not failures, failures
        else:
            raise AssertionError(name)
        # Restore only for test cleanup; production never restores retired bindings.
        for target, attr, original, replacement in reversed(observer.originals):
            setattr(target, attr, original)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario')
    args = parser.parse_args()
    if args.scenario:
        scenario(args.scenario)
        return
    for name in ('committed', 'pending', 'collected', 'write_failure',
                 'binding_replaced', 'sql_failure', 'rollback', 'nested_directories', 'descriptor_cache',
                 'vfs_normal', 'vfs_write_failure', 'vfs_close_failure', 'vfs_open_failure',
                 'vfs_mkdirs_failure'):
        subprocess.run([sys.executable, __file__, '--scenario', name], check=True)
    print('PASS: checked saves, pending-data retention, swallowed failures and explicit rollback')


if __name__ == '__main__':
    main()
