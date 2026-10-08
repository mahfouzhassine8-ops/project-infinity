#pragma once
// Generated from writers/observer.py; verified by the source gate.
inline constexpr const char* INFINITY_PYTHON_PERSISTENCE_SOURCE = R"infinity_source(# SPDX-License-Identifier: GPL-2.0-or-later
"""Native-owned Python persistence observer; never grants termination itself.

Installed before add-on module initialization in each interpreter. Original
save/commit semantics are retained. Finalization refuses pending transactions,
records swallowed write failures and closes tracked buffers before interpreter
teardown. Native admission, thread retirement and filesystem durability are
separate required proofs.
"""
import builtins
from functools import partial
import io
import os
import sqlite3
import threading
import weakref
from urllib.parse import unquote, urlsplit, parse_qs


class Observer:
    def __init__(self, fail, touch, vfs=None):
        self.fail = fail
        self.touch = touch
        self.lock = threading.RLock()
        self.handles = weakref.WeakSet()
        self.connections = weakref.WeakSet()
        self.held_connections = set()
        self.held_handles = set()
        self.originals = []
        self.retired = False
        self.vfs = vfs
        self.install()

    def error(self, operation):
        self.fail(operation)

    def patch(self, module, name, replacement):
        original = getattr(module, name)
        setattr(module, name, replacement)
        self.originals.append((module, name, original, replacement))
        return original

    def check_live(self):
        if self.retired:
            self.error('write_after_observer_retirement')
            raise RuntimeError('Persistence observer is retired')

    def file(self, original, path, mode='r', *args, **kwargs):
        writable = isinstance(mode, str) and any(c in mode for c in 'wax+')
        if not writable:
            return original(path, mode, *args, **kwargs)
        self.check_live()
        self.touch(path, 'checked-open-begin')
        try:
            handle = original(path, mode, *args, **kwargs)
        except Exception:
            # Exclusive temporary allocation can legitimately retry a collision.
            if not ('x' in mode and os.path.exists(path)):
                self.error('file_open_for_write_failed')
            raise
        finally:
            self.touch(path, 'checked-open-end')
        self.touch(path, 'write')
        proxy = File(handle, self)
        self.handles.add(proxy)
        return proxy

    def install(self):
        for module in (builtins, io):
            original = module.open
            def opened(path, mode='r', *args, _original=original, **kwargs):
                return self.file(_original, path, mode, *args, **kwargs)
            self.patch(module, 'open', opened)
        observer = self
        original_connection = sqlite3.Connection
        original_cursor = sqlite3.Cursor

        class Cursor(original_cursor):
            def execute(self, sql, *args, **kwargs):
                try:
                    return super().execute(sql, *args, **kwargs)
                except Exception:
                    if _writes(sql): observer.error('sqlite_write_failed')
                    raise
            def executemany(self, sql, *args, **kwargs):
                try:
                    return super().executemany(sql, *args, **kwargs)
                except Exception:
                    if _writes(sql): observer.error('sqlite_write_failed')
                    raise
            def executescript(self, sql):
                try: return super().executescript(sql)
                except Exception:
                    observer.error('sqlite_script_failed')
                    raise

        class Connection(original_connection):
            def __init__(self, database, *args, **kwargs):
                super().__init__(database, *args, **kwargs)
                self._infinity_closed = False
                observer.connections.add(self)
                value = os.fsdecode(database)
                if value.startswith('file:'):
                    uri = urlsplit(value)
                    query = parse_qs(uri.query)
                    if query.get('mode') in (['memory'], ['ro']): value = ':memory:'
                    elif uri.netloc not in ('', 'localhost'):
                        observer.error('unsupported_sqlite_uri_host')
                    else: value = unquote(uri.path)
                if value != ':memory:': observer.touch(value, 'sqlite')
            def cursor(self, factory=None):
                if factory not in (None, original_cursor, Cursor):
                    observer.error('unobserved_sqlite_cursor_factory')
                return super().cursor(factory or Cursor)
            def execute(self, sql, *args, **kwargs):
                return self.cursor().execute(sql, *args, **kwargs)
            def executemany(self, sql, *args, **kwargs):
                return self.cursor().executemany(sql, *args, **kwargs)
            def executescript(self, sql):
                return self.cursor().executescript(sql)
            def commit(self):
                observer.check_live()
                try: return super().commit()
                except Exception:
                    observer.error('sqlite_commit_failed')
                    raise
            def close(self):
                if not self._infinity_closed and self.in_transaction:
                    observer.held_connections.add(self)
                    observer.error('sqlite_closed_with_pending_transaction')
                    raise sqlite3.ProgrammingError('Pending transaction requires explicit commit or rollback')
                try: return super().close()
                except Exception:
                    observer.error('sqlite_close_failed')
                    raise
                finally: self._infinity_closed = True
            def __exit__(self, exc_type, exc, tb):
                # Preserve SQLite's commit-on-success / rollback-on-exception.
                try: return super().__exit__(exc_type, exc, tb)
                except Exception:
                    observer.error('sqlite_context_commit_or_rollback_failed')
                    raise
            def __del__(self):
                if not getattr(self, '_infinity_closed', True):
                    try:
                        if self.in_transaction:
                            observer.held_connections.add(self)
                            observer.error('sqlite_collected_with_pending_transaction')
                    except Exception:
                        observer.error('sqlite_transaction_inspection_failed')

        original_connect = sqlite3.connect
        def connect(database, *args, **kwargs):
            observer.check_live()
            positional = list(args)
            factory = positional[4] if len(positional) > 4 else kwargs.get('factory', Connection)
            if factory not in (Connection, original_connection):
                observer.error('unobserved_sqlite_connection_factory')
            if len(positional) > 4: positional[4] = Connection if factory is original_connection else factory
            else: kwargs['factory'] = Connection if factory is original_connection else factory
            return original_connect(database, *positional, **kwargs)
        self.connection_type = Connection
        self.patch(sqlite3, 'Connection', Connection)
        self.patch(sqlite3, 'connect', connect)
        for name in ('write', 'pwrite', 'ftruncate'):
            if not hasattr(os, name): continue
            original = getattr(os, name)
            def operated(*args, _original=original, _name=name, **kwargs):
                observer.check_live()
                observer.touch(args[0], 'write')
                try:
                    result = _original(*args, **kwargs)
                    if _name in ('write', 'pwrite') and result != len(args[1]):
                        observer.error('short_raw_file_write')
                    return result
                except Exception:
                    observer.error('raw_file_'+_name+'_failed')
                    raise
            self.patch(os, name, partial(operated))
        for name in ('open', 'rename', 'replace', 'remove', 'unlink', 'mkdir', 'rmdir', 'truncate'):
            original = getattr(os, name)
            def namespace_op(*args, _original=original, _name=name, **kwargs):
                if _name == 'open':
                    flags = args[1] if len(args) > 1 else kwargs.get('flags', 0)
                    if not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                        return _original(*args, **kwargs)
                    if kwargs.get('dir_fd') is not None:
                        self.error('unobserved_directory_relative_file_open')
                self.check_live()
                if _name == 'open': self.touch(args[0], 'checked-open-begin')
                try:
                    return _original(*args, **kwargs)
                except FileExistsError:
                    if _name not in ('open', 'mkdir'): self.error('namespace_'+_name+'_failed')
                    raise
                except FileNotFoundError:
                    # pathlib creates missing parents after an initial mkdir miss.
                    # Native namespace proof still requires the final directories.
                    if _name not in ('remove', 'unlink', 'rmdir', 'mkdir'): self.error('namespace_'+_name+'_failed')
                    raise
                except Exception:
                    self.error('namespace_'+_name+'_failed')
                    raise
                finally:
                    if _name == 'open': self.touch(args[0], 'checked-open-end')
            # Builtin os functions do not bind when cached on an accessor class.
            # Preserve that behavior for Python 3.10 pathlib and addon helpers.
            self.patch(os, name, partial(namespace_op))
        if self.vfs is not None:
            original = self.vfs.File
            def vfs_file(path, mode=None):
                if mode is None or not str(mode).startswith('w'):
                    return original(path) if mode is None else original(path, mode)
                observer.check_live()
                observer.touch(self.vfs.translatePath(path), 'write')
                handle = VFSFile(original(path, mode), observer)
                observer.handles.add(handle)
                return handle
            self.patch(self.vfs, 'File', vfs_file)
            for name, target in [('copy', 1), ('rename', 1), ('delete', 0), ('mkdir', 0), ('mkdirs', 0), ('rmdir', 0)]:
                if not hasattr(self.vfs, name): continue
                original = getattr(self.vfs, name)
                def vfs_op(*args, _original=original, _name=name, _target=target, **kwargs):
                    observer.check_live()
                    try:
                        result = _original(*args, **kwargs)
                        if result is not True:
                            observer.error('vfs_'+_name+'_failed')
                        else:
                            observer.touch(self.vfs.translatePath(args[_target]),
                                           'delete' if _name in ('delete','rmdir') else 'directory' if _name in ('mkdir','mkdirs') else 'write')
                            if _name == 'rename': observer.touch(self.vfs.translatePath(args[0]), 'delete')
                        return result
                    except Exception:
                        observer.error('vfs_'+_name+'_exception')
                        raise
                self.patch(self.vfs, name, vfs_op)

    def finish(self):
        # Called with the GIL after all interpreter child threads have retired.
        # Native code separately checks the thread list and actual destruction.
        with self.lock:
            for module, name, original, replacement in self.originals:
                if getattr(module, name) is not replacement:
                    self.error('persistence_observer_binding_replaced:'+name)
            safe = True
            for connection in set(self.connections) | self.held_connections:
                if not connection._infinity_closed:
                    if connection.in_transaction:
                        self.held_connections.add(connection)
                        self.error('sqlite_pending_transaction_at_retirement')
                        safe = False
                        continue
                    try: connection.close()
                    except Exception: safe = False
            for handle in set(self.handles) | self.held_handles:
                try: handle.close()
                except Exception: safe = False
            if safe: self.retired = True
            return safe


class File:
    def __init__(self, handle, observer):
        self.handle, self.observer = handle, observer
    def __getattr__(self, name):
        if name in ('buffer', 'raw', 'detach'):
            self.observer.error('unobserved_raw_buffer_access')
        return getattr(self.handle, name)
    def __iter__(self): return iter(self.handle)
    def __next__(self): return next(self.handle)
    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
    def write(self, value):
        self.observer.check_live()
        try:
            result = self.handle.write(value)
            if result != len(value): self.observer.error('short_buffered_write')
            return result
        except Exception:
            self.observer.error('buffered_write_failed')
            raise
    def writelines(self, values):
        for value in values: self.write(value)
    def truncate(self, size=None):
        self.observer.check_live()
        try: return self.handle.truncate(size)
        except Exception:
            self.observer.error('buffer_truncate_failed')
            raise
    def flush(self):
        try: return self.handle.flush()
        except Exception:
            self.observer.error('buffer_flush_failed')
            raise
    def close(self):
        if self.handle.closed: return
        try:
            self.flush()
            return self.handle.close()
        except Exception:
            self.observer.held_handles.add(self)
            self.observer.error('buffer_close_failed')
            raise
    def __del__(self):
        try: self.close()
        except Exception: pass  # Failure remains sticky in the native ledger.


class VFSFile(File):
    def __init__(self, handle, observer):
        super().__init__(handle, observer)
        self.closed = False
    def write(self, value):
        self.observer.check_live()
        try:
            result = self.handle.write(value)
            if result is not True: self.observer.error('vfs_write_failed')
            return result
        except Exception:
            self.observer.error('vfs_write_exception')
            raise
    def flush(self): return None  # The native VFS close flushes; native durability is separate.
    def close(self):
        if self.closed: return
        try: return self.handle.close()
        except Exception:
            self.observer.error('vfs_close_failed')
            raise
        finally: self.closed = True


def _writes(sql):
    if not isinstance(sql, str) or not sql.strip(): return False
    return sql.lstrip().split(None, 1)[0].upper() not in ('SELECT', 'EXPLAIN')
)infinity_source";
