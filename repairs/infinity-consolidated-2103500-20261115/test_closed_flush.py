#!/usr/bin/env python3
"""Focused real-file/observer check. Never reads an installed user profile.

Run each case in a fresh process because the shipped observer instruments Python
I/O. Baseline is extracted from the source-map-authenticated signed500 header.
"""
import argparse
import hashlib
import io
import json
import platform
from pathlib import Path
import subprocess
import sys
import tempfile

BASELINE = 'd81736cf62fb3406649065558f7ec28a7be243f32c3d7afae33fac78b6c207f3'


CASES = ('closed_text', 'closed_binary', 'closed_writer', 'closed_random',
         'closed_layered_text', 'prior_failure_and_dirty', 'open_oserror',
         'open_valueerror', 'lying_file_closed', 'lying_buffer_closed',
         'custom_raw_closed', 'throwing_closed_getter', 'custom_native_flush',
         'closes_during_real_flush', 'normal_file', 'pending_transaction')


def child(header, scenario):
    source = Path(header).read_bytes().split(b'R"infinity_source(', 1)[1].rsplit(b')infinity_source";', 1)[0]
    scope = {'__name__': 'exact_shipped_persistence'}
    exec(compile(source, '<exact_shipped_persistence>', 'exec'), scope)
    failures, touches, leases = [], [], []
    dirty = {123: 'existing_protected_buffer'} if scenario == 'prior_failure_and_dirty' else {}
    if scenario == 'prior_failure_and_dirty':
        failures.append('preexisting_unresolved_write')
    def protect(operation, token, targets):
        leases.append(operation)
        if operation == 'dirty': dirty[token] = 'tracked'
        if operation == 'clean': dirty.pop(token, None)
        return 1
    with tempfile.TemporaryDirectory(prefix='infinity500-flush-') as folder:
        target = Path(folder) / 'disposable.txt'
        observer = scope['Observer'](
            lambda reason, *detail: failures.append(reason),
            lambda path, kind: touches.append(kind),
            protect=protect)
        try:
            if scenario.startswith('closed_') or scenario == 'prior_failure_and_dirty':
                data = b'preserved'
                if scenario == 'closed_writer':
                    handle = io.BufferedWriter(io.FileIO(target, 'w'))
                elif scenario == 'closed_random':
                    handle = io.BufferedRandom(io.FileIO(target, 'w+'))
                elif scenario == 'closed_layered_text':
                    handle = io.TextIOWrapper(io.BufferedWriter(io.FileIO(target, 'w')))
                    data = data.decode()
                else:
                    handle = open(target, 'wb' if scenario == 'closed_binary' else 'w')
                    if scenario != 'closed_binary': data = data.decode()
                handle.write(data)
                handle.close()
                assert handle.closed
                before = list(failures), list(leases), dict(dirty)
                try:
                    handle.flush()
                except ValueError:
                    outcome = 'ValueError'
                else:
                    raise AssertionError('Original closed-stream exception was swallowed')
                assert target.read_text() == 'preserved'
                assert dirty == before[2], (dirty, before[2])
                assert failures[:len(before[0])] == before[0]
                return dict(scenario=scenario, exception=outcome, bytes_preserved=True,
                            new_failures=failures[len(before[0]):], new_leases=leases[len(before[1]):],
                            previous_failures_and_dirty_state_unchanged=True)
            if scenario in ('open_oserror', 'open_valueerror'):
                error_type = OSError if scenario == 'open_oserror' else ValueError
                # Deliberate open-stream fault injection, not a provider mock.
                class Broken(io.BytesIO):
                    def flush(self):
                        raise error_type('injected real open-stream failure')
                raw = Broken()
                handle = scope['File'](raw, observer)
                handle.write(b'not yet persisted')
                before = dict(dirty)
                try: handle.flush()
                except error_type: pass
                else: raise AssertionError('Open-stream error suppressed')
                assert not raw.closed and dirty == before and dirty
                assert failures == ['buffer_flush_failed'], failures
                raw.close()
                return dict(scenario=scenario, exception=error_type.__name__,
                            real_failure_retained=True, dirty_state_retained=True)
            if scenario == 'lying_file_closed':
                class Lying(io.BytesIO):
                    @property
                    def closed(self): return True
                    def flush(self): raise OSError('actual open-stream failure')
                raw = Lying()
                assert io.BytesIO.closed.__get__(raw) is False
                handle = scope['File'](raw, observer)
                try: handle.flush()
                except OSError: pass
                else: raise AssertionError('Actual flush error suppressed')
                assert failures == ['buffer_flush_failed'], failures
                raw.close()
                return dict(scenario=scenario, real_failure_retained=True)
            if scenario == 'lying_buffer_closed':
                class BrokenRaw(io.RawIOBase):
                    fail_write = True
                    def writable(self): return True
                    def write(self, value):
                        if self.fail_write: raise OSError('actual raw-write failure')
                        return len(value)
                class LyingBuffer(io.BufferedWriter):
                    @property
                    def closed(self): return True
                raw = BrokenRaw()
                handle = LyingBuffer(raw)
                handle.write(b'pending')
                try: handle.flush()
                except OSError: pass
                else: raise AssertionError('Actual raw-write error suppressed')
                assert failures == ['layered_buffer_flush_failed'], failures
                raw.fail_write = False
                handle.flush()
                raw.close()
                return dict(scenario=scenario, real_failure_retained=True)
            if scenario == 'custom_raw_closed':
                class CustomRaw(io.RawIOBase):
                    pretend_closed = False
                    @property
                    def closed(self): return self.pretend_closed
                    def writable(self): return True
                    def write(self, value): return len(value)
                raw = CustomRaw()
                handle = io.BufferedWriter(raw)
                handle.write(b'pending')
                raw.pretend_closed = True
                try: handle.flush()
                except ValueError: pass
                else: raise AssertionError('Custom closed-state error swallowed')
                assert failures == ['layered_buffer_flush_failed'], failures
                raw.pretend_closed = False
                handle.close()
                return dict(scenario=scenario, ambiguous_state_failure_retained=True)
            if scenario == 'throwing_closed_getter':
                class Throwing(io.BytesIO):
                    @property
                    def closed(self): raise RuntimeError('closed unavailable')
                raw = Throwing()
                if hasattr(observer, 'native_file_closed'):
                    assert observer.native_file_closed(raw, raw.flush) is False
                handle = scope['File'](raw, observer)
                try: handle.flush()
                except RuntimeError: pass
                else: raise AssertionError('Existing property exception swallowed')
                raw.close()
                return dict(scenario=scenario, original_exception_preserved=True,
                            no_new_waiver=True)
            if scenario == 'custom_native_flush':
                handle = open(target, 'wb')
                handle.close()
                raw = handle._infinity_handle
                def custom_flush(): raise ValueError('custom flush still owns work')
                raw.flush = custom_flush
                try: handle.flush()
                except ValueError: pass
                else: raise AssertionError('Custom native-instance method exception swallowed')
                assert failures == ['buffer_flush_failed'], failures
                del raw.flush
                return dict(scenario=scenario, custom_method_failure_retained=True)
            if scenario == 'closes_during_real_flush':
                raw = io.FileIO(target, 'wb')
                handle = io.BufferedWriter(raw)
                def broken_write(value):
                    raw.close()
                    raise ValueError('actual write failed and closed its raw stream')
                raw.write = broken_write
                handle.write(b'pending')
                before = dict(dirty)
                try: handle.flush()
                except ValueError: pass
                else: raise AssertionError('Actual write failure swallowed')
                assert failures == ['layered_buffer_flush_failed'], failures
                assert dirty == before and dirty
                return dict(scenario=scenario, real_failure_retained=True,
                            dirty_state_retained=True)
            if scenario == 'normal_file':
                handle = open(target, 'w')
                handle.write('ordinary')
                handle.flush()
                handle.close()
                assert not failures and not dirty
                assert target.read_text() == 'ordinary'
                return dict(scenario=scenario, original_file_behavior=True)
            if scenario == 'pending_transaction':
                import sqlite3
                connection = sqlite3.connect(Path(folder) / 'temporary.db')
                connection.execute('CREATE TABLE record(position)')
                connection.commit()
                connection.execute('INSERT INTO record VALUES(231)')
                assert connection.in_transaction
                assert observer.finish() is False
                assert connection.in_transaction
                assert 'sqlite_pending_transaction_at_retirement' in failures
                connection.rollback()
                assert connection.execute('SELECT position FROM record').fetchall() == []
                connection.close()
                return dict(scenario=scenario, no_automatic_commit_or_rollback=True,
                            pending_transaction_blocked_retirement=True)
            raise AssertionError(scenario)
        finally:
            for owner, name, original, replacement in reversed(observer.originals):
                setattr(owner, name, original)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('header', type=Path)
    parser.add_argument('--child')
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    if args.child:
        print(json.dumps(child(args.header, args.child), sort_keys=True))
        return
    assert hashlib.sha256(args.header.read_bytes()).hexdigest() == BASELINE
    results = {}
    for label, header in [('baseline', args.header)] + ([('candidate', args.candidate)] if args.candidate else []):
        rows = []
        for case in CASES:
            result = json.loads(subprocess.check_output(
                [sys.executable, __file__, str(header), '--child', case], text=True))
            if case.startswith('closed_') or case == 'prior_failure_and_dirty':
                expected = [] if label == 'candidate' else [
                    'layered_buffer_flush_failed' if case in ('closed_writer','closed_random','closed_layered_text') else 'buffer_flush_failed']
                assert result['new_failures'] == expected, result
                assert result['new_leases'] == [], result
            rows.append(result)
        results[label] = rows
    print(json.dumps(dict(status='REPRODUCED_CLOSED_STREAM_FALSE_FAILURE_CALLBACK',
                          baseline_header_sha256=BASELINE, results=results,
                          candidate_header_sha256=hashlib.sha256(args.candidate.read_bytes()).hexdigest() if args.candidate else None,
                          interpreter=dict(implementation=platform.python_implementation(), version=platform.python_version()),
                          correction='PASS_HOST_ONLY' if args.candidate else 'NOT_TESTED',
                          physical_incident_causality='NOT_ESTABLISHED',
                          native_shutdown_impact='NOT_YET_TESTED'), indent=2))


if __name__ == '__main__':
    main()
