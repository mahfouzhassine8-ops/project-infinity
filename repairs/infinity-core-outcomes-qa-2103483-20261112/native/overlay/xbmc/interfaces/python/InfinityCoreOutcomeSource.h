#pragma once
inline constexpr const char* INFINITY_CORE_OUTCOME_SOURCE=R"coreoutcome("""Core-only internal QA observation. No persistence or admission authority."""
import ast
import hashlib
import json
import marshal
import os
import shutil
import stat
import sys
import threading
import time
import types
import ctypes
import _ctypes

CORE_SOURCE = '2e1b79adc352129696ccfa48a3b5b16f85ebf812026fdd26c3e55d67f34b43b3'
CORE_LIBRARY = 'libadulthideout_core.so'


class State:
    def __init__(self, emit, source_path, source_sha, actor, observe_loads=True):
        self.emit = emit
        self.source = source_path
        self.actor = actor
        self.observe_loads = observe_loads
        self.local = threading.local()
        self.bindings = []
        self.serial = 0
        self.events = 0
        self.started = time.monotonic()
        self.overflow = False
        self.closed = False
        self.loads = 0
        self.start_returns = 0
        self.pending = {}
        self.codes = set()
        self.checked_codes = {}
        self.calls = {}
        self.return_locals = {}
        self.trace_owned = False
        self.tracer = self.trace
        self.record('coverage.begin', source_sha=source_sha)
        with open(source_path, 'rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != source_sha:
            self.record('coverage.disabled', reason='source_hash_mismatch')
            return
        if actor != 'qa_fixture' and source_sha != CORE_SOURCE:
            self.record('coverage.disabled', reason='unrecognized_source')
            return
        compiled = compile(raw, source_path, 'exec', dont_inherit=True)
        def collect(code):
            self.codes.add(hashlib.sha256(marshal.dumps(code)).digest())
            for child in code.co_consts:
                if type(child) is types.CodeType:
                    collect(child)
        collect(compiled)
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                symbol = node.func.attr
                if symbol in ('start_core_service', 'stop_core_service', 'is_core_service_running'):
                    self.calls.setdefault(node.lineno, []).append(symbol)
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                call = node.value
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'start_core_service':
                    self.return_locals[(call.lineno, call.func.attr)] = node.targets[0].id
        try:
            self.wrap_metadata()
            self.wrap(shutil, 'copy2', 'copy2')
            # Preserve the existing Infinity crypto-loader wrapper as the delegate.
            if observe_loads:
                delegate = _ctypes.dlopen
                wrapper = self.wrapper(delegate, 'dlopen')
                for module, name in ((_ctypes, 'dlopen'), (ctypes, '_dlopen')):
                    if getattr(module, name) is delegate:
                        self.bindings.append((module, name, delegate, wrapper))
                        setattr(module, name, wrapper)
                    else:
                        self.wrap(module, name, 'dlopen')
            if sys.gettrace() is None:
                self.trace_owned = True
                sys.settrace(self.tracer)
                self.record('coverage.trace_installed')
            else:
                self.record('coverage.trace_unavailable', reason='existing_trace_preserved')
            self.record('coverage.installed', unchanged_core_path=True, universal_native_load_events=not observe_loads)
        except BaseException:
            self.uninstall()
            raise

    def record(self, event, **facts):
        # Diagnostic failures never replace the observed call's result/error.
        if getattr(self.local, 'diagnosing', False) or self.closed:
            return
        self.local.diagnosing = True
        try:
            if self.events >= 4096 or time.monotonic()-self.started >= 1800:
                if self.overflow:
                    return
                self.overflow = True
                event, facts = 'coverage.limit', dict(reason='record_or_time_limit')
            self.events += 1
            row = dict(v=1, actor=self.actor, event=event, seq=self.events,
                       tid=threading.get_native_id(), us=time.monotonic_ns()//1000,
                       completion_proof=False, **facts)
            encoded = json.dumps(row, ensure_ascii=True, separators=(',', ':'))
            if len(encoded) > 3000:
                row = dict(v=1, actor=self.actor, event='coverage.record_too_large', seq=self.events,
                           completion_proof=False)
                encoded = json.dumps(row, separators=(',', ':'))
            # Native sink consumes only this bounded, one-line JSON string.
            row['line'] = encoded
            self.emit(row)
        except BaseException:
            pass
        finally:
            self.local.diagnosing = False

    def target(self, value, directory=None):
        if type(value) is int:
            try:
                path = os.readlink('/proc/self/fd/'+str(value))
            except OSError:
                return dict(kind='fd', fd=value, resolved=False)
        elif type(value) in (str, bytes):
            path = os.fsdecode(value)
            if directory is not None and type(directory) is int and directory >= 0 and not os.path.isabs(path):
                try:
                    path = os.path.join(os.readlink('/proc/self/fd/'+str(directory)), path)
                except OSError:
                    return dict(kind='path', resolved=False, dir_fd=directory)
        else:
            return dict(kind='unsupported_path_type', resolved=False)
        # Only code/staging filenames are exposed. Other target text stays out
        # of logcat, including URLs, account names, credentials and xattr values.
        safe = path.startswith('/') and '\x00' not in path and '://' not in path and '?' not in path
        known = path.rsplit('/', 1)[-1] in (CORE_LIBRARY, 'libinfinity_coreqa_fixture.so')
        out = dict(kind='path', resolved=safe, target=path[:512] if safe and known else '<other-target>')
        out['target_id'] = hashlib.sha256((str(self.started)+'\0'+path).encode(errors='replace')).hexdigest()[:20]
        return out

    def snapshot(self, value, kwargs):
        if type(value) not in (str, bytes, int):
            return dict(status='unsupported_path_type')
        follow = kwargs.get('follow_symlinks', True)
        directory = kwargs.get('dir_fd')
        if type(follow) is not bool or directory is not None and type(directory) is not int:
            return dict(status='unsupported_stat_arguments')
        try:
            if type(value) is int:
                info = os.fstat(value)
            else:
                info = os.stat(value, dir_fd=directory, follow_symlinks=follow)
            return dict(status='observed', dev=info.st_dev, ino=info.st_ino,
                        mode=info.st_mode, size=info.st_size,
                        mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns,
                        follow_symlinks=follow)
        except OSError as error:
            return dict(status='unavailable', errno=error.errno)

    def wrap_metadata(self):
        native = __import__(os.name)
        for name in ('chmod', 'utime', 'setxattr'):
            if not hasattr(os, name):
                self.record('coverage.operation_unavailable', operation=name)
                continue
            original = getattr(os, name)
            wrapper = self.wrapper(original, name)
            for module in (os, native):
                value = getattr(module, name, None)
                if value is original:
                    self.bindings.append((module, name, original, wrapper))
                    setattr(module, name, wrapper)

    def wrap(self, module, name, operation):
        original = getattr(module, name)
        wrapper = self.wrapper(original, operation)
        self.bindings.append((module, name, original, wrapper))
        setattr(module, name, wrapper)

    def wrapper(self, original, operation):
        def observed(*args, **kwargs):
            if getattr(self.local, 'diagnosing', False) or self.closed:
                return original(*args, **kwargs)
            self.serial += 1
            ticket = self.serial
            parent = getattr(self.local, 'parent', 0)
            value = args[0] if args else kwargs.get('name' if operation == 'dlopen' else 'src' if operation == 'copy2' else 'path')
            if operation == 'dlopen' and self.actor != 'qa_fixture':
                if type(value) not in (str, bytes) or os.fsdecode(value).rsplit('/', 1)[-1] != CORE_LIBRARY:
                    return original(*args, **kwargs)
            facts = dict(operation=operation, ticket=ticket, parent=parent)
            try:
                facts['target'] = self.target(value, kwargs.get('dir_fd'))
                if operation == 'copy2':
                    destination = args[1] if len(args)>1 else kwargs.get('dst')
                    facts['destination'] = self.target(destination)
                    facts['destination_before'] = self.snapshot(destination, {})
                if operation != 'dlopen':
                    facts['before'] = self.snapshot(value, kwargs)
                self.record('operation.begin', **facts)
            except BaseException:
                self.record('coverage.inspect_failed', operation=operation, ticket=ticket)
            self.local.parent = ticket
            try:
                result = original(*args, **kwargs)
            except BaseException as error:
                try:
                    post_error = self.snapshot(value, kwargs) if operation != 'dlopen' else None
                except BaseException:
                    post_error = dict(status='inspection_failed')
                self.record('operation.error', operation=operation, ticket=ticket, parent=parent,
                            exception=type(error).__name__[:80],
                            after=post_error,
                            errno=error.errno if type(error).__module__ == 'builtins' and isinstance(error, OSError) else None)
                raise
            else:
                if operation == 'dlopen':
                    self.loads += 1
                extra = dict(result_kind=type(result).__name__[:40],
                             result=result if type(result) in (bool, type(None)) else None)
                if operation != 'dlopen':
                    try:
                        extra['after'] = self.snapshot(value, kwargs)
                    except BaseException:
                        extra['after'] = dict(status='inspection_failed')
                if operation == 'copy2':
                    try:
                        extra['destination_after'] = self.snapshot(destination, {})
                    except BaseException:
                        extra['destination_after'] = dict(status='inspection_failed')
                # Handles and arbitrary returned objects are never serialized.
                self.record('operation.return', operation=operation, ticket=ticket, parent=parent, **extra)
                return result
            finally:
                self.local.parent = parent
        return observed

    def trace(self, frame, event, arg):
        try:
            if frame.f_code.co_filename != self.source:
                return None
            if frame.f_code not in self.checked_codes:
                self.checked_codes[frame.f_code] = hashlib.sha256(marshal.dumps(frame.f_code)).digest() in self.codes
            if not self.checked_codes[frame.f_code]:
                self.record('coverage.code_mismatch')
                return None
            key = id(frame)
            pending = self.pending.get(key)
            if pending and event in ('line', 'return', 'exception'):
                symbol, line = pending
                if event != 'line' or frame.f_lineno != line:
                    self.pending.pop(key, None)
                    if event == 'exception':
                        self.record('native_call.exception', symbol=symbol, line=line,
                                    exception=arg[0].__name__[:80])
                    else:
                        local = self.return_locals.get((line, symbol))
                        value = frame.f_locals.get(local) if local is not None else None
                        observed = symbol == 'start_core_service' and local is not None and type(value) is int
                        if observed:
                            self.start_returns += 1
                        self.record('native_call.progressed', symbol=symbol, line=line,
                                    numeric_return_observed=observed, result=value if observed else None)
            if event == 'line' and frame.f_lineno in self.calls:
                symbols = self.calls[frame.f_lineno]
                if len(symbols) == 1:
                    self.pending[key] = (symbols[0], frame.f_lineno)
                    self.record('native_call.before', symbol=symbols[0], line=frame.f_lineno)
            return self.tracer
        except BaseException:
            self.record('coverage.trace_error')
            return self.tracer

    def uninstall(self):
        if self.closed:
            return
        if self.trace_owned:
            if sys.gettrace() is self.tracer:
                sys.settrace(None)
            else:
                self.record('coverage.trace_replaced')
        for module, name, original, wrapper in reversed(self.bindings):
            if getattr(module, name, None) is wrapper:
                setattr(module, name, original)
            else:
                self.record('coverage.binding_replaced', binding=name)
        self.record('coverage.retired', successful_load_calls=self.loads if self.observe_loads else None,
                    observed_start_returns=self.start_returns, native_drain='UNVERIFIED')
        self.bindings.clear()
        self.closed = True


def install(emit, source_path, source_sha, actor='core_service', observe_loads=True):
    return State(emit, source_path, source_sha, actor, observe_loads)
)coreoutcome";
