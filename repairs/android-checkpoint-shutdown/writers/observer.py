# SPDX-License-Identifier: GPL-2.0-or-later
"""Native-owned Python persistence observer; never grants termination itself.

Installed before add-on module initialization in each interpreter. Original
save/commit semantics are retained. Finalization refuses pending transactions,
records swallowed write failures and closes tracked buffers before interpreter
teardown. Native admission, thread retirement and filesystem durability are
separate required proofs.
"""
import builtins
import importlib
import io
import _io
import os
import shutil
import sqlite3
# Marker is embedded into libkodi.so and checked by the native build gate.
DIRECT_SQLITE_CONNECT_OBSERVED = 'direct_sqlite_connect_observed'
try:
    import subprocess
except ImportError:
    subprocess = None
import threading
import types
import weakref
from urllib.parse import unquote, urlsplit, parse_qs


class Observer:
    def __init__(self, fail, touch, vfs=None, host_probe=False):
        self.fail = fail
        self.touch = touch
        self.lock = threading.RLock()
        self.handles = weakref.WeakSet()
        self.connections = weakref.WeakSet()
        self.held_connections = set()
        self.held_handles = set()
        self.children = set()
        self.host_probe = host_probe
        self.child_scope = threading.local()
        self.originals = []
        self.retired = False
        self.vfs = vfs
        self.install()

    def error(self, operation):
        self.fail(operation)

    def patch(self, module, name, replacement):
        original = getattr(module, name)
        if isinstance(replacement, types.FunctionType):
            replacement = Operation(replacement)
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
        self.touch(handle.fileno(), 'write')
        proxy = File(handle, self)
        self.handles.add(proxy)
        return proxy

    def install(self):
        for module in (builtins, io, _io):
            original = module.open
            def opened(path, mode='r', *args, _original=original, **kwargs):
                return self.file(_original, path, mode, *args, **kwargs)
            self.patch(module, 'open', opened)
        observer = self
        original_raw = _io.FileIO
        class RawFile(original_raw):
            _infinity_depth = 0
            def __init__(self, file, mode='r', closefd=True, opener=None):
                self._infinity_writable = isinstance(mode, str) and any(c in mode for c in 'wax+')
                if not self._infinity_writable:
                    super().__init__(file, mode, closefd, opener)
                    return
                observer.check_live()
                observer.touch(file, 'checked-open-begin')
                try:
                    super().__init__(file, mode, closefd, opener)
                except Exception:
                    if not ('x' in mode and os.path.exists(file)):
                        observer.error('raw_file_open_for_write_failed')
                    raise
                finally:
                    observer.touch(file, 'checked-open-end')
                observer.touch(self.fileno(), 'write')
                observer.handles.add(self)
            def write(self, value):
                observer.check_live()
                try:
                    result = super().write(value)
                    if result != len(value): observer.error('short_raw_buffer_write')
                    return result
                except Exception:
                    observer.error('raw_buffer_write_failed')
                    raise
            def writelines(self, values):
                for value in values: self.write(value)
            def truncate(self, size=None):
                observer.check_live()
                try: return super().truncate(size)
                except Exception:
                    observer.error('raw_buffer_truncate_failed')
                    raise
            def close(self):
                if self.closed: return
                try: return super().close()
                except Exception:
                    if getattr(self, '_infinity_writable', False):
                        observer.held_handles.add(self)
                        observer.error('raw_buffer_close_failed')
                    raise
        self.patch(_io, 'FileIO', RawFile)
        self.patch(io, 'FileIO', RawFile)
        for name in ('BufferedWriter', 'BufferedRandom', 'TextIOWrapper'):
            base = getattr(_io, name)
            class CheckedBuffer(base):
                _infinity_depth = 2 if name == 'TextIOWrapper' else 1
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    if self.writable(): observer.handles.add(self)
                def write(self, value):
                    observer.check_live()
                    try:
                        result = super().write(value)
                        if result != len(value): observer.error('short_layered_buffer_write')
                        return result
                    except Exception:
                        observer.error('layered_buffer_write_failed')
                        raise
                def writelines(self, values):
                    for value in values: self.write(value)
                def flush(self):
                    try: return super().flush()
                    except Exception:
                        observer.error('layered_buffer_flush_failed')
                        raise
                def truncate(self, size=None):
                    observer.check_live()
                    try: return super().truncate(size)
                    except Exception:
                        observer.error('layered_buffer_truncate_failed')
                        raise
                def close(self):
                    if self.closed: return
                    try: return super().close()
                    except Exception:
                        observer.held_handles.add(self)
                        observer.error('layered_buffer_close_failed')
                        raise
            self.patch(_io, name, CheckedBuffer)
            self.patch(io, name, CheckedBuffer)
        native_sqlite = importlib.import_module('_sqlite3')
        dbapi2 = importlib.import_module('sqlite3.dbapi2')
        original_connection = native_sqlite.Connection
        original_cursor = native_sqlite.Cursor

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
        original_dbapi_connect = dbapi2.connect
        original_native_connect = native_sqlite.connect

        def checked_connect(original, database, *args, **kwargs):
            observer.check_live()
            positional = list(args)
            factory = positional[4] if len(positional) > 4 else kwargs.get('factory', Connection)
            if factory not in (Connection, original_connection):
                observer.error('unobserved_sqlite_connection_factory')
            if len(positional) > 4: positional[4] = Connection if factory is original_connection else factory
            else: kwargs['factory'] = Connection if factory is original_connection else factory
            return original(database, *positional, **kwargs)

        def connect(database, *args, **kwargs):
            return checked_connect(original_connect, database, *args, **kwargs)
        def dbapi_connect(database, *args, **kwargs):
            return checked_connect(original_dbapi_connect, database, *args, **kwargs)
        def native_connect(database, *args, **kwargs):
            return checked_connect(original_native_connect, database, *args, **kwargs)

        self.connection_type = Connection
        # sqlite3, sqlite3.dbapi2 and _sqlite3 all expose the same native entry
        # points through different module attributes. Patch every standard route
        # before add-on module initialization so direct users still receive the
        # tracked Connection subclass and preserve their own commit/rollback logic.
        self.patch(sqlite3, 'Connection', Connection)
        self.patch(sqlite3, 'connect', connect)
        self.patch(dbapi2, 'Connection', Connection)
        self.patch(dbapi2, 'connect', dbapi_connect)
        self.patch(native_sqlite, 'Connection', Connection)
        self.patch(native_sqlite, 'connect', native_connect)
        native_os = importlib.import_module(os.name)
        for name in ('write', 'pwrite', 'ftruncate', 'sendfile', 'copy_file_range'):
            if not hasattr(os, name): continue
            original = getattr(os, name)
            def operated(*args, _original=original, _name=name, **kwargs):
                observer.check_live()
                observer.touch(args[1] if _name == 'copy_file_range' else args[0], 'write')
                try:
                    result = _original(*args, **kwargs)
                    if _name in ('write', 'pwrite') and result != len(args[1]):
                        observer.error('short_raw_file_write')
                    return result
                except Exception:
                    observer.error('raw_file_'+_name+'_failed')
                    raise
            self.patch(os, name, operated)
            if hasattr(native_os, name): self.patch(native_os, name, operated)
        for name in ('open', 'rename', 'replace', 'remove', 'unlink', 'mkdir', 'rmdir', 'truncate'):
            original = getattr(os, name)
            def namespace_op(*args, _original=original, _name=name, **kwargs):
                if _name == 'open':
                    flags = args[1] if len(args) > 1 else kwargs.get('flags', 0)
                    if not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                        return _original(*args, **kwargs)
                self.check_live()
                if _name == 'open': self.touch(args[0], 'checked-open-begin')
                try:
                    result = _original(*args, **kwargs)
                    if _name == 'open': self.touch(result, 'write')
                    return result
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
            self.patch(os, name, namespace_op)
            if hasattr(native_os, name): self.patch(native_os, name, namespace_op)
        if subprocess is not None:
            self.install_children()
        if self.vfs is not None:
            original = self.vfs.File
            def vfs_file(path, mode=None, _original=original):
                if mode is None or not str(mode).startswith('w'):
                    return _original(path) if mode is None else _original(path, mode)
                observer.check_live()
                observer.touch(self.vfs.translatePath(path), 'write')
                try:
                    handle = VFSFile(_original(path, mode), observer)
                except Exception:
                    observer.error('vfs_open_for_write_failed')
                    raise
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

    def install_children(self):
        observer = self
        original_popen = subprocess.Popen

        def readonly_command(command):
            if not isinstance(command, (list, tuple)):
                return False
            command = list(command)
            logcat = ['/system/bin/logcat', '--uid='+str(os.getuid()), '-b', 'crash', '-d', '-t', '200', '-v', 'threadtime']
            if command == logcat:
                return True
            if observer.host_probe and command == ['/bin/echo', 'infinity-diagnostic-fixture']:
                return True
            # Android property reads are a common capability probe and cannot
            # mutate persistent state. Resolve PATH-based spelling to the
            # immutable system binary before allowing it.
            if 1 <= len(command) <= 2 and command[0] in ('getprop', '/system/bin/getprop'):
                resolved = command[0] if command[0].startswith('/') else shutil.which(command[0])
                if resolved != '/system/bin/getprop':
                    return False
                if len(command) == 2:
                    key = command[1]
                    if not isinstance(key, str) or not key or len(key) > 128 or any(
                            not (ch.isalnum() or ch in '._-') for ch in key):
                        return False
                return True

            # SlyGuy probes Android network state with read-only system tools.
            # Keep this allowlist intentionally narrow: "ip" receives exactly
            # one display-only noun, while ifconfig receives at most one
            # interface/display argument. Mutation forms require additional
            # arguments and remain fail-closed.
            resolved = command[0] if command[0].startswith('/') else shutil.which(command[0])
            if resolved == '/system/bin/ip':
                return (len(command) == 2 and isinstance(command[1], str) and
                        command[1] in ('addr', 'address', 'link', 'route', 'neigh', 'rule'))
            if resolved == '/system/bin/ifconfig':
                if len(command) == 1:
                    return True
                return (len(command) == 2 and isinstance(command[1], str) and
                        0 < len(command[1]) <= 64 and '\x00' not in command[1])
            return False

        class Popen(original_popen):
            def __init__(child, command, *args, **kwargs):
                observer.check_live()
                readonly = (readonly_command(command) and not args and
                            not kwargs.get('shell', False) and kwargs.get('env') is None and
                            kwargs.get('cwd') is None and kwargs.get('preexec_fn') is None and
                            not kwargs.get('pass_fds', ()) and
                            (observer.host_probe or not any(name.startswith(('LD_', 'DYLD_')) for name in os.environ)) and
                            kwargs.get('executable') in (None, command[0]))
                if readonly:
                    for name, fallback in (('stdout', 1), ('stderr', 2)):
                        output = kwargs.get(name)
                        if isinstance(output, File): observer.touch(output.fileno(), 'write')
                        elif output is None: observer.touch(fallback, 'write')
                        elif output not in (subprocess.PIPE, subprocess.STDOUT):
                            observer.error('unobserved_diagnostic_child_output')
                    observer.touch(None, 'readonly-child-begin')
                    observer.child_scope.readonly = True
                try:
                    super().__init__(command, **kwargs) if not args else super().__init__(command, *args, **kwargs)
                    if readonly: observer.children.add(child)
                finally:
                    if readonly:
                        observer.child_scope.readonly = False
                        observer.touch(None, 'readonly-child-end')
        self.patch(subprocess, 'Popen', Popen)
        # subprocess captures the C fork function at import. Check both aliases
        # so importing the lower-level module cannot evade child ownership.
        try:
            native_process = importlib.import_module('_posixsubprocess')
        except ImportError:
            native_process = None
        if native_process is not None:
            fork_exec = native_process.fork_exec
            def checked_fork_exec(*args, **kwargs):
                if not getattr(observer.child_scope, 'readonly', False):
                    observer.error('unobserved_native_child_process')
                return fork_exec(*args, **kwargs)
            self.patch(native_process, 'fork_exec', checked_fork_exec)
            if hasattr(subprocess, '_fork_exec'):
                self.patch(subprocess, '_fork_exec', checked_fork_exec)

    def finish(self):
        # Called with the GIL after all interpreter child threads have retired.
        # Native code separately checks the thread list and actual destruction.
        with self.lock:
            for module, name, original, replacement in self.originals:
                if getattr(module, name) is not replacement:
                    self.error('persistence_observer_binding_replaced:'+name)
            safe = True
            for child in set(self.children):
                if child.poll() is None:
                    self.error('diagnostic_child_not_retired')
                    safe = False
                else:
                    self.children.discard(child)
            for connection in set(self.connections) | self.held_connections:
                if not connection._infinity_closed:
                    if connection.in_transaction:
                        self.held_connections.add(connection)
                        self.error('sqlite_pending_transaction_at_retirement')
                        safe = False
                        continue
                    try: connection.close()
                    except Exception: safe = False
            handles = sorted(set(self.handles) | self.held_handles,
                             key=lambda h: getattr(h, '_infinity_depth', 2), reverse=True)
            flushed = True
            for handle in handles:
                try:
                    if not handle.closed: handle.flush()
                except Exception:
                    self.held_handles.add(handle)
                    self.error('buffer_flush_before_retirement_failed')
                    flushed = False
            if flushed:
                for handle in handles:
                    try: handle.close()
                    except Exception: safe = False
            else:
                safe = False
            if safe: self.retired = True
            return safe


class File:
    def __init__(self, handle, observer):
        self.handle, self.observer = handle, observer
    def __getattr__(self, name):
        if name in ('buffer', 'raw', 'detach'):
            try:
                anonymous = os.fstat(self.handle.fileno()).st_nlink == 0
            except (OSError, ValueError):
                anonymous = False
            if not anonymous: self.observer.error('unobserved_raw_buffer_access')
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
        try:
            result = self.handle.close()
            self.closed = True
            return result
        except Exception:
            self.observer.held_handles.add(self)
            self.observer.error('vfs_close_failed')
            raise


def _writes(sql):
    if not isinstance(sql, str) or not sql.strip(): return False
    return sql.lstrip().split(None, 1)[0].upper() not in ('SELECT', 'EXPLAIN')


class Operation:
    """Match a native function's non-descriptor behavior in cached class aliases."""
    def __init__(self, function): self.function = function
    def __call__(self, *args, **kwargs): return self.function(*args, **kwargs)
    def __getattr__(self, name): return getattr(self.function, name)
