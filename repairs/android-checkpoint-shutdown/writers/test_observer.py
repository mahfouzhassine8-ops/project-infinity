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
    read_connection = sqlite3.connect
    with tempfile.TemporaryDirectory(prefix='infinity-save-') as folder:
        root = Path(folder)
        failures, mutations = [], []
        observer = module.Observer(failures.append, lambda path, kind: mutations.append((path, kind)))
        database = root / 'state.db'
        connection = sqlite3.connect(database)
        connection.execute('create table state (value)')
        connection.commit()
        if name == 'committed':
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
                write = os.write
            cached = Accessor()
            cached.mkdir(root / 'cached')
            descriptor = cached.opened(root / 'cached' / 'state', os.O_WRONLY | os.O_CREAT, 0o600)
            cached.write(descriptor, b'saved')
            os.close(descriptor)
            assert observer.finish()
            assert not failures, failures
            assert (root / 'cached' / 'state').read_bytes() == b'saved'
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
                 'binding_replaced', 'sql_failure', 'rollback', 'nested_directories', 'descriptor_cache'):
        subprocess.run([sys.executable, __file__, '--scenario', name], check=True)
    print('PASS: checked saves, pending-data retention, swallowed failures and explicit rollback')


if __name__ == '__main__':
    main()
