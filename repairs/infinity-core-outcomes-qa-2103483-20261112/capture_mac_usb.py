#!/usr/bin/env python3
"""Read-only USB evidence for ONE owner-controlled Infinity Close attempt.

Only the owner operates Android. This program never starts/stops the app,
changes its state, clears logs, elevates privileges, or writes device files.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import threading
import time

PACKAGE = 'com.projectinfinity.kodi'
PROCESS = PACKAGE + ':kodi'
FILES = '/sdcard/Android/data/' + PACKAGE + '/files'
FRAMEWORK = {'close': FILES + '/infinity-checkpoint-close.json',
             'mirror': FILES + '/infinity-checkpoint-mirror.json'}
ATTEMPTS = FILES + '/.kodi/userdata/addon_data/script.infinity.commandcenter/.android-checkpoint/'
MAX_RECEIPT = 1024 * 1024
READ_SECONDS = 5
FINAL_RESERVE = 60
MAX_LOG_BYTES = 32 * 1024 * 1024
SESSION = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z')
TAGS = ('InfinityCoreQA', 'InfinityClose', 'InfinityPower', 'InfinityEvidence',
        'InfinityCheckpoint', 'InfinityCheckpointEvidence', 'InfinityCheckpointClose',
        'InfinityCheckpointMirror', 'InfinityShutdown', 'InfinityExit', 'InfinityExitDiagnostics')
SYSTEM_TAGS = ('ActivityManager', 'ActivityTaskManager', 'AndroidRuntime', 'libc', 'DEBUG',
               'am_proc_start', 'am_proc_died', 'am_kill', 'am_crash', 'am_anr')
LOG_LINE = re.compile(r'^\s*\d\d-\d\d\s+\d\d:\d\d:\d\d\.\d+\s+\d+\s+\d+\s+[VDIWEFAS]\s+([^:]+):\s?(.*)$')


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def select_usb(adb, serial):
    result = subprocess.run([adb, 'devices', '-l'], capture_output=True, timeout=10)
    if result.returncode:
        raise RuntimeError('adb devices failed; use the existing authorized USB connection.')
    devices = []
    for line in result.stdout.decode(errors='replace').splitlines():
        if not line.strip() or line.startswith(('List of devices', '*')):
            continue
        fields = line.split()
        if len(fields) >= 2:
            devices.append(dict(serial=fields[0], state=fields[1],
                                usb=any(f.startswith('usb:') for f in fields[2:])))
    if serial is None:
        if len(devices) != 1:
            raise RuntimeError('Select exactly one existing USB device with --serial; no automatic selection among multiple devices.')
        selected = devices[0]
    else:
        matches = [d for d in devices if d['serial'] == serial]
        if len(matches) != 1:
            raise RuntimeError('The requested USB serial is not uniquely listed by adb.')
        selected = matches[0]
    if selected['state'] == 'device' and not selected['usb']:
        # Some Mac platform-tools omit the usb: listing field. ADB's supported
        # -d selector still enforces a physical USB transport at the server.
        probe = subprocess.run([adb, '-d', 'get-serialno'], capture_output=True, timeout=10)
        selected['usb'] = (probe.returncode == 0 and
                           probe.stdout.decode(errors='replace').strip() == selected['serial'])
    if selected['state'] != 'device' or not selected['usb']:
        raise RuntimeError('An already authorized physical USB device is required; offline, wireless and emulator transports are refused.')
    return selected['serial']


class Reader:
    def __init__(self, adb, serial, deadline):
        self.prefix = [adb, '-s', serial]
        self.deadline = deadline

    def command(self, args):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            return dict(status='TIME_BUDGET_EXHAUSTED', returncode=None, stdout=b'', stderr='')
        try:
            result = subprocess.run(self.prefix + args, capture_output=True,
                                    timeout=min(READ_SECONDS, remaining))
            error = result.stderr.decode(errors='replace')[:2048]
            return dict(status='OK' if result.returncode == 0 else 'COMMAND_FAILED',
                        returncode=result.returncode, stdout=result.stdout, stderr=error)
        except subprocess.TimeoutExpired:
            return dict(status='READ_TIMEOUT', returncode=None, stdout=b'', stderr='')
        except OSError as error:
            return dict(status='HOST_ADB_EXECUTION_ERROR', returncode=None, stdout=b'',
                        stderr=type(error).__name__)


def read_error(result):
    if result['status'] != 'COMMAND_FAILED':
        return result['status']
    message = result['stderr'].lower()
    if ('device offline' in message or 'unauthorized' in message or
            'no devices/emulators found' in message or
            ('device' in message and 'not found' in message)):
        return 'USB_DEVICE_UNAVAILABLE'
    if 'permission denied' in message or 'operation not permitted' in message:
        return 'ACCESS_DENIED_NO_BYPASS_ATTEMPTED'
    if 'no such file' in message:
        return 'MISSING'
    return 'READ_FAILED'


def read_receipt(reader, remote, local):
    row = dict(path=remote, observed_utc=utc(), content_reads=0, max_bytes=MAX_RECEIPT)
    meta = reader.command(['shell', 'stat', '-c', '%s:%Y:%i:%F', remote])
    if meta['status'] != 'OK':
        row.update(status=read_error(meta), error=meta['stderr'])
        return row, None
    text = meta['stdout'].decode(errors='replace').strip()
    fields = re.fullmatch(r'(\d+):(\d+):(\d+):([^\r\n]+)', text)
    if not fields:
        row.update(status='UNRECOGNIZED_READ_ONLY_STAT_OUTPUT')
        return row, None
    size, mtime, inode = map(int, fields.groups()[:3])
    row.update(pre_read_size=size, device_mtime_seconds=mtime, pre_read_inode=inode)
    if fields.group(4) != 'regular file':
        row.update(status='NON_REGULAR_RECEIPT_NOT_READ')
        return row, None
    if size > MAX_RECEIPT:
        row.update(status='OVERSIZE_NOT_READ')
        return row, None
    result = reader.command(['exec-out', 'head', '-c', str(MAX_RECEIPT), remote])
    row['content_reads'] = 1
    if result['status'] != 'OK':
        row.update(status=read_error(result), error=result['stderr'])
        return row, None
    raw = result['stdout']
    if len(raw) > MAX_RECEIPT:
        row.update(status='READ_BOUND_VIOLATED_NOT_SAVED')
        return row, None
    local.write_bytes(raw)
    row.update(local_file=local.name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
               size_matches_pre_read_stat=len(raw) == size, stat_and_content_not_atomic=True)
    try:
        value = json.loads(raw.decode('utf-8'))
    except (UnicodeError, ValueError):
        row.update(status='INVALID_JSON_RAW_RETAINED')
        return row, None
    if not isinstance(value, dict):
        row.update(status='NON_OBJECT_JSON_RAW_RETAINED')
        return row, None
    row['status'] = 'READ_OK'
    # These are claims made by the Android receipt, not conclusions of this tool.
    row['android_receipt_fields'] = {k: value[k] for k in
        ('session', 'pid', 'native_pid', 'engine_pid', 'process_death_confirmed',
         'last_native_status', 'status', 'state', 'phase') if k in value}
    return row, value


def sessions(value):
    """Only the two source-confirmed session locations; no recursive search."""
    if not isinstance(value, dict):
        return set()
    candidates = [value.get('session')]
    native = value.get('last_native_status')
    if isinstance(native, str):
        try:
            native = json.loads(native)
        except ValueError:
            native = None
    if isinstance(native, dict):
        candidates.append(native.get('session'))
    return {s for s in candidates if isinstance(s, str) and SESSION.fullmatch(s)}


def receipt_phase(reader, out, phase):
    records, tokens = {}, set()
    for name, remote in FRAMEWORK.items():
        record, data = read_receipt(reader, remote, out / (phase + '-' + name + '.json'))
        records[remote] = record
        tokens.update(sessions(data))
    if len(tokens) > 2:
        return dict(records=records, native_attempts='REFUSED_MORE_THAN_TWO_SESSION_TOKENS')
    for session in sorted(tokens):
        remote = ATTEMPTS + 'attempt-' + session + '-CHECKPOINT_FAILED.json'
        record, data = read_receipt(reader, remote, out / (phase + '-native-' + session + '.json'))
        record['derived_safe_session'] = session
        record['session_matches_content'] = data is not None and data.get('session') == session
        records[remote] = record
    return dict(records=records, native_attempts='READ_ONLY_DERIVED_KNOWN_FILENAMES' if tokens else
                'NO_SAFE_SESSION_IN_CONFIRMED_FIELDS')


def process_snapshot(reader, elapsed):
    row = dict(observed_utc=utc(), host_elapsed_seconds=round(elapsed, 3), process=PROCESS)
    result = reader.command(['shell', 'pidof', PROCESS])
    raw = result['stdout'].decode(errors='replace').strip()
    if result['returncode'] == 1 and not raw and not result['stderr']:
        row.update(status='OBSERVED_ABSENT', pids=[])
        return row
    if result['status'] != 'OK' or not re.fullmatch(r'\d+(?:\s+\d+)*', raw):
        row.update(status='UNKNOWN_QUERY_OR_TRANSPORT_ERROR', query_status=result['status'],
                   error=result['stderr'])
        return row
    pids = list(map(int, raw.split()))
    if len(pids) > 4 or len(pids) != len(set(pids)) or any(p <= 0 for p in pids):
        row.update(status='AMBIGUOUS_PID_RESULT')
        return row
    result = reader.command(['shell', 'ps', '-w', '-p', ','.join(map(str, pids)), '-o', 'PID,NAME'])
    if result['status'] != 'OK':
        row.update(status='UNKNOWN_PS_QUERY_OR_PROCESS_TRANSITION', queried_pids=pids,
                   error=result['stderr'])
        return row
    matched = []
    for line in result['stdout'].decode(errors='replace').splitlines():
        fields = line.split()
        if fields == ['PID', 'NAME']:
            continue
        if len(fields) != 2 or not fields[0].isdigit() or int(fields[0]) not in pids or fields[1] != PROCESS:
            # Do not export another process's name if PID reuse occurred.
            row.update(status='PS_IDENTITY_MISMATCH_OR_UNSUPPORTED_COLUMNS', queried_pids=pids)
            return row
        matched.append(int(fields[0]))
    row.update(status='OBSERVED_PRESENT' if sorted(matched) == sorted(pids) else
               'PIDOF_PS_TRANSITION_UNVERIFIED', pids=sorted(matched))
    return row


class LogCapture:
    def __init__(self, reader, out, stop):
        self.stop = stop
        self.stats = dict(retained_lines=0, retained_bytes=0, ignored_system_lines=0,
                          oversized_lines=0, native_json_lines=0, status='RUNNING',
                          initial_one_buffered_line_may_precede_capture=True)
        args = reader.prefix + ['logcat', '-v', 'threadtime', '-T', '1', '-b', 'main', '-b', 'system',
                               '-b', 'crash', '-b', 'events', '-s']
        args += [tag + ':V' for tag in TAGS] + [tag + ':I' for tag in SYSTEM_TAGS] + ['*:S']
        self.stderr = (out / 'logcat-reader.stderr').open('wb')
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=self.stderr,
                                     stdin=subprocess.DEVNULL, close_fds=True)
        self.thread = threading.Thread(target=self.consume, args=(out,), daemon=True)
        self.thread.start()

    def consume(self, out):
        try:
            with (out / 'android-logcat.txt').open('wb') as log, (out / 'InfinityCoreQA-native.jsonl').open('w') as native:
                while True:
                    raw = self.proc.stdout.readline(16385)
                    if not raw:
                        break
                    if len(raw) > 16384 or not raw.endswith(b'\n'):
                        self.stats['oversized_lines'] += 1
                        while raw and not raw.endswith(b'\n'):
                            raw = self.proc.stdout.readline(16385)
                        continue
                    match = LOG_LINE.match(raw.decode(errors='replace').rstrip('\r\n'))
                    if not match:
                        continue
                    tag, message = match.groups(); tag = tag.strip()
                    if tag not in TAGS and not re.search(r'(?<![A-Za-z0-9_.])' + re.escape(PACKAGE) +
                                                        r'(?=$|[^A-Za-z0-9_.])', message):
                        self.stats['ignored_system_lines'] += 1
                        continue
                    if self.stats['retained_bytes'] + len(raw) > MAX_LOG_BYTES:
                        self.stats['status'] = 'LOG_SIZE_LIMIT_REACHED'
                        self.stop.set(); break
                    log.write(raw); log.flush()
                    self.stats['retained_lines'] += 1
                    self.stats['retained_bytes'] += len(raw)
                    if tag == 'InfinityCoreQA':
                        try:
                            row = json.loads(message)
                        except ValueError:
                            continue
                        if isinstance(row, dict) and isinstance(row.get('data'), dict) and type(row.get('native_pid')) is int:
                            # Preserve the actual Android message, not a host reconstruction.
                            native.write(message + '\n'); native.flush()
                            self.stats['native_json_lines'] += 1
            if self.stats['status'] == 'RUNNING':
                self.stats['status'] = 'READER_ENDED'
        except Exception as error:
            self.stats.update(status='READER_ERROR', error=type(error).__name__)
        finally:
            self.stop.set()

    def finish(self):
        if self.proc.poll() is None:
            self.proc.terminate()  # Host adb recording client only; no Android app signal.
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill(); self.proc.wait(timeout=2)
        self.thread.join(timeout=2)
        self.stderr.close()
        self.stats.update(host_reader_returncode=self.proc.returncode,
                          host_reader_thread_ended=not self.thread.is_alive())


def summarize(before, after, snapshots):
    freshness = []
    for path, record in after['records'].items():
        previous = before['records'].get(path, {})
        if record.get('sha256') and previous.get('sha256'):
            state = 'UNCHANGED_PREEXISTING_STALE_FOR_THIS_CAPTURE' if record['sha256'] == previous['sha256'] else 'CONTENT_CHANGED_DURING_CAPTURE'
        elif record.get('sha256'):
            state = 'FIRST_OBSERVED_AFTER_NO_CONTENT_BASELINE_FOR_THIS_PATH'
        else:
            state = 'FRESHNESS_UNVERIFIABLE'
        freshness.append(dict(path=path, freshness=state, status=record['status']))
    transitions, previous = [], None
    for snapshot in snapshots:
        if snapshot['status'] not in ('OBSERVED_PRESENT', 'OBSERVED_ABSENT'):
            continue
        current = snapshot['pids']
        if previous is not None and previous != current:
            transitions.append(dict(host_elapsed_seconds=snapshot['host_elapsed_seconds'],
                                    prior_pids=previous, observed_pids=current))
        previous = current
    return dict(receipt_freshness=freshness, observed_pid_set_transitions=transitions,
                process_death_or_replacement='DISCRETE_EXACT_NAME_OBSERVATIONS_ONLY; PID_REUSE_AND_GAPS_NOT_EXCLUDED',
                clean_persistence_proven=False, successful_Close_asserted=False,
                native_reason='Read android_receipt_fields.last_native_status and exact raw receipt files; denied/missing reads remain unavailable')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', help='Existing authorized physical USB serial; required if multiple transports are listed')
    parser.add_argument('--duration', type=int, default=900, help='Total bounded capture budget, 120–1800 seconds (default900)')
    parser.add_argument('--out', type=Path, default=Path('Infinity-Close-Capture-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--adb', default='adb', help='Existing adb executable (default: adb in PATH)')
    args = parser.parse_args()
    if not 120 <= args.duration <= 1800:
        parser.error('--duration must be120–1800 seconds')
    adb = shutil.which(args.adb)
    if not adb:
        parser.error('adb is unavailable; use your existing Android platform-tools installation')
    try:
        serial = select_usb(adb, args.serial)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        parser.error(str(error))
    if args.out.exists():
        parser.error('--out must be a new directory; existing captures are never overwritten')
    args.out.mkdir(parents=True)
    began = time.monotonic(); deadline = began + args.duration
    reader = Reader(adb, serial, deadline)
    stop = threading.Event(); user_stop = []
    def interrupt(signum, frame):
        user_stop.append(utc()); stop.set()
    original_signal = signal.signal(signal.SIGINT, interrupt)
    metadata = dict(status='CAPTURE_PREPARING', started_utc=utc(), usb_serial=serial,
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        duration_budget_seconds=args.duration, final_read_reserve_seconds=FINAL_RESERVE,
        app_commands_executed=False, device_writes=False, root_or_run_as=False,
        logs_cleared=False, maps_read=False, native_events_are_android_messages_only=True)
    before = after = dict(records={}, native_attempts='NOT_READ')
    snapshots = []; capture = None
    try:
        save(args.out / 'CAPTURE.json', metadata)
        capture = LogCapture(reader, args.out, stop)
        snapshots.append(process_snapshot(reader, time.monotonic() - began))
        before = receipt_phase(reader, args.out, 'before')
        for record in before['records'].values():
            record['freshness'] = 'PREEXISTING_UNCORRELATED_BASELINE'
        save(args.out / 'RECEIPTS-BEFORE.json', before)
        metadata['ready_announced'] = not stop.is_set() and time.monotonic() < deadline - FINAL_RESERVE
        if metadata['ready_announced']:
            print('READY — recording read-only USB evidence. Perform your ONE existing Infinity Close attempt on the phone.')
            print('Press Control-C here after the attempt. This stops only Mac recording. Output: ' + str(args.out.resolve()), flush=True)
        with (args.out / 'PROCESS-SNAPSHOTS.jsonl').open('w') as stream:
            for snapshot in snapshots:
                stream.write(json.dumps(snapshot) + '\n')
            stream.flush()
            while not stop.is_set() and time.monotonic() < deadline - FINAL_RESERVE:
                snapshot = process_snapshot(reader, time.monotonic() - began)
                snapshots.append(snapshot); stream.write(json.dumps(snapshot) + '\n'); stream.flush()
                stop.wait(min(2, max(0, deadline - FINAL_RESERVE - time.monotonic())))
        metadata['recording_stop_reason'] = 'OWNER_CONTROL_C' if user_stop else (
            capture.stats['status'] if stop.is_set() else 'BOUNDED_DURATION')
    except Exception as error:
        metadata.update(status='CAPTURE_TOOL_ERROR', error=type(error).__name__ + ': ' + str(error))
    finally:
        if capture:
            capture.finish(); metadata['log_reader'] = capture.stats
        print('Recording stopped. Taking final read-only receipts/process snapshot (at most the remaining budget).', flush=True)
        snapshots.append(process_snapshot(reader, time.monotonic() - began))
        after = receipt_phase(reader, args.out, 'after')
        save(args.out / 'RECEIPTS-AFTER.json', after)
        save(args.out / 'SUMMARY.json', summarize(before, after, snapshots))
        save(args.out / 'PROCESS-SUMMARY.json', dict(final_snapshot=snapshots[-1], sample_count=len(snapshots)))
        metadata.update(finished_utc=utc(), elapsed_seconds=round(time.monotonic() - began, 3),
                        owner_interrupts=len(user_stop))
        if metadata['status'] != 'CAPTURE_TOOL_ERROR':
            completed = metadata.get('ready_announced') and metadata.get('recording_stop_reason') in ('OWNER_CONTROL_C', 'BOUNDED_DURATION')
            metadata['status'] = 'CAPTURE_COMPLETE_NOT_CLOSE_ACCEPTANCE' if completed else 'CAPTURE_INCOMPLETE_NOT_CLOSE_ACCEPTANCE'
        save(args.out / 'CAPTURE.json', metadata)
        signal.signal(signal.SIGINT, original_signal)
    print('Saved read-only evidence to ' + str(args.out.resolve()) + '. The Android app was not controlled by this tool.')
    return 0 if metadata['status'] == 'CAPTURE_COMPLETE_NOT_CLOSE_ACCEPTANCE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
