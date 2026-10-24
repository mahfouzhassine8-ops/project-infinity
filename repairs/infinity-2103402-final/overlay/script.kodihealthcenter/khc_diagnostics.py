"""Health Center 2.3: bounded incident storage and export (no Kodi calls).

Unclean observer termination is NOT proof of a process crash. No network access,
no player control, no original-log deletion and no account settings collection.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone

VERSION = '2.5.26'
SCHEMA = 3
MAX_EVENTS = 160
MAX_SESSIONS = 10
TAIL_BYTES = 512 * 1024
MAX_FILE = 2 * 1024 * 1024
MAX_BUNDLE = 16 * 1024 * 1024
MAX_FILES = 800
MAX_SKIN_FILES = 600
MAX_STATE = 256 * 1024


def utc(epoch=None):
    return datetime.fromtimestamp(time.time() if epoch is None else epoch, timezone.utc).isoformat(timespec='milliseconds')


def stamp():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]


def redact(text):
    """Best-effort sharing filter; titles and other personal text may remain."""
    text = str(text)
    text = re.sub(r'(?i)plugin://([a-z0-9_.-]+)[^\s<>"\']*', r'plugin://\1/[REDACTED]', text)
    text = re.sub(r'(?i)\b(?:https?|ftp|smb|nfs|rtsp|rtmp|dav|davs|file)://[^\s<>"\']+', '[URL REDACTED]', text)
    text = re.sub(r'(?i)\b(?:magnet):\?[^\s<>"\']+', '[URL REDACTED]', text)
    text = re.sub(r'(?i)\b(?:authorization|cookie|set-cookie)\s*[:=][^\r\n]+', '[AUTH HEADER REDACTED]', text)
    text = re.sub(r'(?i)\b(?:bearer|basic)\s+[a-z0-9._~+/=-]+', '[AUTH REDACTED]', text)
    keys = r'(?:password|passwd|passphrase|access_token|refresh_token|token|api[_-]?key|client_secret|secret|username|user_name)'
    # Quoted JSON/Python/key-value fields, then unquoted values.
    text = re.sub(r'(?i)(["\']?' + keys + r'["\']?\s*[:=]\s*)(["\'])(.*?)\2', r'\1"[REDACTED]"', text)
    text = re.sub(r'(?i)(\b' + keys + r'\s*[:=]\s*)(?!["\'])([^\s,;&}\]]+)', r'\1[REDACTED]', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[EMAIL REDACTED]', text)
    # Preserve semantic dotted-quad versions when nearby text identifies them as versions.
    ip_re = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
    source = text
    def _ip_or_version(match):
        before = source[max(0, match.start()-32):match.start()].lower()
        if re.search(r'(?:version|ver(?:sion)?|release|build|skin|addon)[\s:=#-]*$', before):
            return match.group(0)
        return '[IP REDACTED]'
    text = ip_re.sub(_ip_or_version, text)
    # Common desktop user home directories, not Android package/module paths.
    text = re.sub(r'(?i)(?:/Users/|/home/)[^/\s]+', '/[USER]', text)
    text = re.sub(r'(?i)[A-Z]:\\Users\\[^\\\s]+', r'[USER]', text)
    return text


def safe_json(value):
    if isinstance(value, dict):
        sensitive = {'password', 'passwd', 'passphrase', 'access_token', 'refresh_token',
                     'token', 'api_key', 'apikey', 'client_secret', 'secret',
                     'authorization', 'cookie', 'username', 'user_name'}
        version_keys={'version','version_name','versionname','addon_version','skin_version','build_version'}
        out={}
        for k,v in value.items():
            key=str(k); low=key.lower()
            if low in sensitive: out[key]='[REDACTED]'
            elif low in version_keys and isinstance(v,str): out[key]=v
            else: out[key]=safe_json(v)
        return out
    if isinstance(value, (tuple, list)):
        return [safe_json(x) for x in value]
    return redact(value) if isinstance(value, str) else value


def read_json(path, default=None):
    try:
        path = Path(path)
        if path.is_symlink():
            return default
        with path.open('rb') as handle:
            data = handle.read(MAX_STATE + 1)
        if len(data) > MAX_STATE:
            return default
        return json.loads(data.decode('utf-8'))
    except (OSError, ValueError, UnicodeError):
        return default


def atomic_json(path, value, durable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex[:8] + '.tmp')
    data = json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False).encode('utf-8')
    if len(data) > MAX_STATE:
        raise ValueError('Diagnostic metadata exceeds its limit')
    try:
        with temp.open('xb') as handle:
            handle.write(data)
            handle.flush()
            if durable:
                os.fsync(handle.fileno())
        os.replace(str(temp), str(path))
    finally:
        if temp.exists():
            temp.unlink()


def baseline(root):
    """Return the active Refresh Codes baseline owned by Health Center."""
    data = read_json(Path(root) / 'baseline.json', {})
    try:
        epoch = float(data.get('epoch', 0) or 0) if isinstance(data, dict) else 0.0
    except (ValueError, TypeError):
        epoch = 0.0
    if not math.isfinite(epoch) or epoch < 0:
        epoch = 0.0
    return {'epoch': epoch, 'utc': data.get('utc', '') if isinstance(data, dict) else '',
            'token': data.get('token', '') if isinstance(data, dict) else '',
            'incident_id': data.get('incident_id', '') if isinstance(data, dict) else ''}


def read_tail(path, cap=TAIL_BYTES):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refusing symbolic-link log')
    with path.open('rb') as handle:
        end = handle.seek(0, os.SEEK_END)
        handle.seek(max(0, end - cap))
        data = handle.read(cap)
    # The first tail line may be partial; retain it and explicitly label truncation.
    return data.decode('utf-8', 'replace'), {'input_bytes': end, 'read_bytes': len(data), 'truncated': end > cap}


def process_identity():
    pid = os.getpid()
    try:
        data = Path('/proc/self/stat').read_text()
        start = data[data.rfind(')') + 2:].split()[19]  # Linux field 22
        return {'pid': pid, 'start_ticks': start, 'strength': 'pid_and_start_time'}
    except (OSError, IndexError):
        return {'pid': pid, 'start_ticks': None, 'strength': 'pid_only'}


def same_process(left, right):
    return bool(isinstance(left, dict) and isinstance(right, dict) and
                left.get('start_ticks') and right.get('start_ticks') and
                left.get('pid') == right.get('pid') and left['start_ticks'] == right['start_ticks'])


def session_path(root, name):
    if not isinstance(name, str) or not re.fullmatch(r'session-[0-9TZ]+-[0-9a-f]{8}', name):
        raise ValueError('Invalid diagnostic session ID')
    root = Path(root).resolve()
    path = root / 'sessions' / name
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Symbolic-link session directory')
    return path


def snapshot_log(folder, source, filename, session_id=None):
    """Retain a bounded *copy*, never modify or rotate Kodi's original log."""
    folder = Path(folder)
    if not re.fullmatch(r'[a-z0-9_.-]+\.log', filename):
        raise ValueError('Invalid snapshot name')
    result = {'file': filename, 'captured_utc': utc(), 'source': Path(source).name,
              'same_session_marker_in_tail': False, 'redaction': 'best_effort'}
    try:
        text, info = read_tail(source)
        result.update(info)
        result['same_session_marker_in_tail'] = bool(session_id and session_id in text)
        text = redact(text)
        data = text.encode('utf-8')[-TAIL_BYTES:]
        result['bytes'] = len(data)
        result['sha256'] = hashlib.sha256(data).hexdigest()
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / filename
        temp = target.with_name(target.name + '.tmp')
        temp.write_bytes(data)
        os.replace(str(temp), str(target))
        result['status'] = 'copied_tail_not_crash_proof'
    except (OSError, ValueError) as error:
        result.update(status='unavailable', error_type=type(error).__name__)
    return result


class SessionStore:
    """One service writer; callbacks share a lock and perform no Kodi queries."""
    def __init__(self, root, identity, old_log, metadata=None):
        self.root = Path(root)
        (self.root / 'sessions').mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.closed = False
        self.recovered = None
        self.io_error = None
        pointer = read_json(self.root / 'current.json', {})
        old_name = pointer.get('session_id') if isinstance(pointer, dict) else None
        if old_name:
            try:
                old_folder = session_path(self.root, old_name)
                previous = read_json(old_folder / 'state.json', {})
                if previous.get('status') == 'active':
                    previous['detection_utc'] = utc()
                    if same_process(previous.get('process'), identity):
                        previous['status'] = 'observer_restarted_same_process'
                        previous['reason'] = 'Service restarted in the same Kodi process; not a process crash.'
                    else:
                        previous['status'] = 'unclean_exit_detected'
                        previous['reason'] = ('Previous observer ended without a shutdown marker. '
                                              'Crash, force-stop, OS kill, power loss or observer failure are possible.')
                        previous['crash_cause_confirmed'] = False
                        snap = snapshot_log(old_folder, old_log, 'previous-kodi.tail.log', old_name)
                        previous.setdefault('snapshots', {})['previous-kodi.tail.log'] = snap
                        previous['previous_log_association'] = 'marker_seen' if snap['same_session_marker_in_tail'] else 'unverified_or_marker_outside_tail'
                        self.recovered = old_folder
                    atomic_json(old_folder / 'state.json', previous)
            except (OSError, ValueError, TypeError, AttributeError):
                self.io_error = 'previous_session_read_or_archive_failed'
        self.name = 'session-' + stamp()
        self.folder = session_path(self.root, self.name)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.start_mono = time.monotonic()
        self.state = {'schema': SCHEMA, 'health_center_version': VERSION, 'session_id': self.name,
                      'process': identity, 'started_utc': utc(), 'started_epoch': time.time(),
                      'status': 'active', 'crash_cause_confirmed': False, 'events': [],
                      'last_event': 'observer_started', 'snapshots': {}, 'metadata': safe_json(metadata or {}),
                      'timing_note': 'Callback timestamps are observation times, not exact button-press or process-death times.'}
        self.event('observer_started', durable=False)
        atomic_json(self.root / 'current.json', {'session_id': self.name})
        self.prune()

    def _save(self, durable=False):
        try:
            self.state['heartbeat_epoch'] = time.time()
            self.state['heartbeat_utc'] = utc()
            atomic_json(self.folder / 'state.json', self.state, durable)
            self.io_error = None
        except (OSError, ValueError) as error:
            self.io_error = type(error).__name__

    def event(self, name, details=None, durable=False):
        with self.lock:
            if self.closed:
                return
            event = {'event': str(name)[:80], 'utc': utc(), 'epoch': time.time(),
                     'elapsed_ms': round((time.monotonic() - self.start_mono) * 1000)}
            if details:
                event['details'] = safe_json(details)
            self.state['events'] = (self.state['events'] + [event])[-MAX_EVENTS:]
            self.state['last_event'] = event['event']
            if name in ('playback_stopped', 'playback_ended', 'playback_error'):
                self.state['last_stop_epoch'] = event['epoch']
            self._save(durable)

    def heartbeat(self, observations=None):
        with self.lock:
            if self.closed:
                return
            if observations:
                self.state['observations'] = safe_json(observations)
            self._save()

    def metadata(self, metadata):
        with self.lock:
            self.state['metadata'] = safe_json(metadata)
            self._save()

    def snapshot(self, source, name):
        # Heavy log reading is done in the monitor loop, never inside a player callback.
        result = snapshot_log(self.folder, source, name, self.name)
        with self.lock:
            if not self.closed:
                self.state['snapshots'][name] = result
                self._save()
        return result

    def finish(self, reason='observer_abort_requested'):
        with self.lock:
            self.event(reason)
            self.state['status'] = 'observer_stopped'
            self.state['observer_stop_utc'] = utc()
            self.state['reason'] = 'The service observed a stop request. This alone does not certify final process shutdown.'
            self._save()
            self.closed = True

    def prune(self):
        folders = sorted((self.root / 'sessions').glob('session-*'), key=lambda p: p.name, reverse=True)
        keep = {self.name}
        if self.recovered:
            keep.add(self.recovered.name)
        for p in folders:
            if len(keep) < MAX_SESSIONS and not p.is_symlink():
                keep.add(p.name)
        for p in folders:
            if p.name not in keep and not p.is_symlink() and p.is_dir():
                shutil.rmtree(str(p), ignore_errors=True)


def records(root, legacy_dir=None):
    result = []
    cut = baseline(root).get('epoch', 0) or 0
    for p in sorted((Path(root) / 'sessions').glob('session-*'), reverse=True):
        if p.is_symlink() or not p.is_dir():
            continue
        data = read_json(p / 'state.json', {})
        if not isinstance(data, dict) or not data.get('session_id'):
            continue
        try:
            started = float(data.get('started_epoch', 0) or 0)
        except (ValueError, TypeError):
            started = 0
        if cut and started < cut:
            continue
        data['_folder'] = str(p)
        data['_path'] = str(p / 'state.json')
        result.append(data)
    result.sort(key=lambda r: r.get('started_epoch', 0) if isinstance(r.get('started_epoch'), (int, float)) else 0, reverse=True)
    # Legacy v2.2 reports predate the Refresh Codes baseline. Keep them on disk,
    # but do not mix them into the current clean test session after a refresh.
    if legacy_dir and not cut:
        for p in sorted(Path(legacy_dir).glob('crash_*.json'), reverse=True)[:30]:
            data = read_json(p, {})
            if not isinstance(data, dict) or not data:
                continue
            data = dict(data)
            data.update(_path=str(p), _legacy=True, status='legacy_unclean_session', crash_cause_confirmed=False)
            result.append(data)
    return result


def current(root):
    p = read_json(Path(root) / 'current.json', {})
    try:
        state = read_json(session_path(root, p['session_id']) / 'state.json', {})
        cut = baseline(root).get('epoch', 0) or 0
        if cut and isinstance(state, dict):
            try:
                if float(state.get('started_epoch', 0) or 0) < cut:
                    return {}
            except (ValueError, TypeError):
                return {}
        return state
    except (ValueError, KeyError, TypeError):
        return {}


def collect_memory():
    result = {}
    try:
        # procfs is a stream; SEEK_END can fail even when its contents are readable.
        with open('/proc/self/status', 'rb') as handle:
            text = handle.read(16384).decode('utf-8', 'replace')
        for line in text.splitlines():
            if line.startswith(('VmRSS:', 'VmHWM:', 'Threads:')):
                key, value = line.split(':', 1)
                result[key] = value.strip()
    except (OSError, ValueError):
        result['status'] = 'process_memory_unavailable'
    try:
        # Numeric counts only: never export unrelated apps' files or account paths.
        fds = []
        with os.scandir('/proc/self/fd') as entries:
            for entry in entries:
                if entry.name.isdecimal():
                    fds.append(int(entry.name))
                if len(fds) >= 16384:
                    result['fd_count_capped'] = True
                    break
        result.update(open_fd_count=len(fds), max_fd=max(fds, default=None),
                      fd_sample_note='approximate; includes the transient enumeration descriptor')
    except OSError:
        result['fd_status'] = 'unavailable'
    return result


def log_clues(text):
    """Counts are search aids, never assigned causes or proof of native death."""
    patterns = {
        'codec_messages': r'MediaCodec|ReleaseOutputBuffer|timeout waiting for buffer',
        'no_media_exceptions': r'not playing any media',
        'python_tracebacks': r'Traceback \(most recent call last\)',
        'fatal_signal_markers': r'Fatal signal \d+|SIGSEGV|SIGABRT',
        'java_fatal_markers': r'FATAL EXCEPTION',
    }
    hits = {k: len(re.findall(p, text, re.I)) for k, p in patterns.items()}
    hits['interpretation'] = 'Text matches only; not a diagnosis or attribution to an add-on.'
    return hits



def crash_signatures(text):
    """Recognize a few high-value native signatures without assigning blame."""
    text = str(text or '')
    out = []
    checks = [
        ('fortify_fd_set_overflow',
         r'FORTIFY:\s*FD_SET:\s*file descriptor \d+ >= FD_SETSIZE \d+',
         'FD_SET exceeded its descriptor bound; the caller and resource lifetime still require evidence.'),
        ('pythoninvoker_refcount_abort',
         r'PythonInvoker\.cpp:704.*Py_REFCNT\(p\)\s*==\s*2|PyObjectDeleter.*Py_REFCNT\(p\)\s*==\s*2',
         'Kodi PythonInvoker native assertion during Python object cleanup/module initialization.'),
        ('pythoninvoker_threadstate_abort',
         r'PythonInvoker\.cpp:412.*m_threadState\s*!=\s*nullptr',
         'Kodi PythonInvoker native assertion involving a missing Python thread state.'),
        ('native_sigabrt', r'Fatal signal\s+6\s*\(SIGABRT\)|signal\s+6\s*\(SIGABRT\)',
         'Android native abort marker.'),
        ('native_sigsegv', r'Fatal signal\s+11\s*\(SIGSEGV\)|signal\s+11\s*\(SIGSEGV\)',
         'Android native segmentation-fault marker.'),
        ('zeroconf_unknownhost_abort', r'UnknownHostException.*localhost|CZeroconfAndroid::doPublishService',
         'Android/Zeroconf localhost failure appears in this evidence.'),
    ]
    for key, pattern, description in checks:
        matches = list(re.finditer(pattern, text, re.I | re.S))
        if matches:
            out.append({'id': key, 'count': len(matches), 'description': description})
    return out


def addon_id_clues(text, limit=30):
    """Return only add-on IDs seen in logs; these are correlation clues, never causation."""
    ids = []
    seen = set()
    pattern = re.compile(r'\b(?:plugin|script|service|skin|resource)\.[A-Za-z0-9_.-]+\b', re.I)
    for match in pattern.finditer(str(text or '')):
        addon = match.group(0)
        key = addon.lower()
        if key not in seen:
            seen.add(key)
            ids.append(addon)
            if len(ids) >= limit:
                break
    return ids


def analyze_incident_texts(sources):
    """Combine bounded archived text into a conservative incident summary."""
    sources = sources or {}
    result = {'classification': 'no_confirmed_native_signature', 'signatures': [],
              'addon_id_clues': [], 'playback_stop_markers': 0,
              'interpretation': 'Correlation only. Add-on IDs near an incident are not proof of causation.'}
    sig_by_id = {}
    addon_seen = set()
    for name, text in sources.items():
        for sig in crash_signatures(text):
            cur = sig_by_id.setdefault(sig['id'], dict(sig, count=0, sources=[]))
            cur['count'] = cur.get('count', 0) + sig.get('count', 0)
            if name not in cur['sources']:
                cur['sources'].append(name)
        result['playback_stop_markers'] += len(re.findall(r'playback_stopped|Player\.OnStop|OnPlayBackStopped|Playback stopped', str(text), re.I))
        for addon in addon_id_clues(text):
            key = addon.lower()
            if key not in addon_seen:
                addon_seen.add(key)
                result['addon_id_clues'].append(addon)
    result['signatures'] = list(sig_by_id.values())
    ids = {x['id'] for x in result['signatures']}
    if 'pythoninvoker_refcount_abort' in ids:
        result['classification'] = 'pythoninvoker_refcount_native_abort'
        result['recommended_focus'] = 'Python add-on/script lifecycle around module initialization or shutdown; do not disable assertions blindly.'
    elif 'pythoninvoker_threadstate_abort' in ids:
        result['classification'] = 'pythoninvoker_threadstate_native_abort'
        result['recommended_focus'] = 'Python invoker thread-state lifecycle; correlate with the script running immediately before the abort.'
    elif 'native_sigabrt' in ids:
        result['classification'] = 'native_sigabrt_unclassified'
    elif 'native_sigsegv' in ids:
        result['classification'] = 'native_sigsegv_unclassified'
    return result


class Bundle:
    def __init__(self, target, max_total=MAX_BUNDLE):
        self.target = Path(target)
        self.partial = self.target.with_name(self.target.name + '.partial')
        self.limit = max_total
        self.total = 0
        self.entries = []
        self.omitted = []
        self.names = set()
        self.target.parent.mkdir(parents=True, exist_ok=True)
        if self.target.exists() or self.partial.exists():
            raise ValueError('Refusing to overwrite a diagnostic ZIP')
        self.archive = zipfile.ZipFile(self.partial, 'x', zipfile.ZIP_DEFLATED)

    def add(self, name, data, role, scrub=True):
        if name in self.names or name.startswith('/') or '..' in name.split('/') or '\\' in name:
            raise ValueError('Unsafe or duplicate archive member')
        if isinstance(data, str):
            data = data.encode('utf-8')
        if len(data) > MAX_FILE:
            self.omitted.append({'file': name, 'reason': 'per_file_limit'})
            return False
        if scrub:
            data = redact(data.decode('utf-8', 'replace')).encode('utf-8')
        if len(data) > MAX_FILE or self.total + len(data) > self.limit or len(self.entries) >= MAX_FILES:
            self.omitted.append({'file': name, 'reason': 'bundle_size_or_count_limit'})
            return False
        self.archive.writestr(name, data)
        self.names.add(name)
        self.total += len(data)
        self.entries.append({'file': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                             'role': role, 'redaction': 'best_effort' if scrub else 'not_applied'})
        return True

    def json(self, name, value, role):
        return self.add(name, json.dumps(safe_json(value), indent=2), role, scrub=False)

    def file(self, path, name, role, scrub=True, tail=False):
        path = Path(path)
        try:
            if path.is_symlink():
                raise ValueError('symbolic_link')
            if tail:
                text, info = read_tail(path, MAX_FILE)
                if not text:
                    self.omitted.append({'file': name, 'reason': 'empty_source', 'available': False})
                    return False
                ok = self.add(name, text, role, scrub)
                if ok:
                    self.entries[-1].update(info)
                return ok
            with path.open('rb') as handle:
                data = handle.read(MAX_FILE + 1)
            if not data:
                self.omitted.append({'file': name, 'reason': 'empty_source', 'available': False})
                return False
            return self.add(name, data, role, scrub)
        except (OSError, ValueError) as error:
            self.omitted.append({'file': name, 'reason': type(error).__name__})
            return False

    def close(self, metadata):
        receipt = {'schema': SCHEMA, 'health_center_version': VERSION, 'exported_utc': utc(),
                   'files': self.entries, 'omitted': self.omitted, 'input_bytes': self.total,
                   'limits': {'file_bytes': MAX_FILE, 'total_bytes': self.limit, 'files': MAX_FILES},
                   'metadata': safe_json(metadata), 'crash_cause_confirmed': False,
                   'network_upload': False, 'original_logs_modified': False,
                   'privacy_note': 'URLs/known credentials are filtered in text. Titles or other private data may remain. Native binary traces are not redacted.'}
        try:
            self.archive.writestr('manifest.json', json.dumps(receipt, indent=2))
            self.archive.close()
            with zipfile.ZipFile(self.partial) as check:
                if check.testzip() is not None or len(check.namelist()) < 2:
                    raise ValueError('Diagnostic ZIP validation failed')
                if set(check.namelist()) != self.names | {'manifest.json'}:
                    raise ValueError('Diagnostic ZIP inventory mismatch')
                for entry in self.entries:
                    data = check.read(entry['file'])
                    if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                        raise ValueError('Diagnostic ZIP hash mismatch')
            os.replace(str(self.partial), str(self.target))
            return receipt
        except Exception:
            self.abort()
            raise

    def abort(self):
        self.archive.close()
        if self.partial.exists():
            self.partial.unlink()


def add_skin_xml(bundle, skin_root):
    """Read definition XML only, not data folders, artwork or font binaries."""
    root = Path(skin_root)
    if root.is_symlink() or not root.is_dir():
        bundle.omitted.append({'file': 'active-skin/', 'reason': 'skin_source_unavailable'})
        return
    count = 0
    for folder, dirs, names in os.walk(str(root), followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in
                         ('userdata', 'addon_data', 'cache', 'packages') and
                         not (Path(folder) / d).is_symlink())
        for name in sorted(names):
            if not name.lower().endswith('.xml') or name.startswith('.'):
                continue
            path = Path(folder) / name
            if path.is_symlink():
                continue
            if count >= MAX_SKIN_FILES or bundle.total >= bundle.limit:
                bundle.omitted.append({'file': 'active-skin/', 'reason': 'skin_export_limit'})
                return
            bundle.file(path, 'active-skin/' + path.relative_to(root).as_posix(), 'active_skin_definition_not_user_settings')
            count += 1


def _native_kv(path):
    """Read bounded key=value native crash record; never treats it as root-cause proof."""
    result = {}
    try:
        path = Path(path)
        if path.is_symlink() or not path.is_file():
            return result
        data = path.read_bytes()[:64 * 1024].decode('utf-8', 'replace')
        for line in data.splitlines():
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if re.fullmatch(r'[a-zA-Z0-9_]+', key):
                result[key] = value[:512]
    except OSError:
        pass
    return result


def correlate_native_incident(native_dirs, active_baseline, selected_record=None, environment=None):
    """Keep compatibility while attributing event history separately from sessions."""
    from khc_native import correlate
    return safe_json(correlate(native_dirs, active_baseline, VERSION, selected_record, environment))


def build_report(target, record, environment, current_log, old_log, skin_root=None,
                 native_dirs=(), native_status=None, health_text=None, include_saved_android=False, scan_results=None, scan_details=None, authorization_health=None, authorization_details=None):
    bundle = Bundle(target)
    selected = {k: v for k, v in (record or {}).items() if not k.startswith('_')}
    try:
        bundle.json('incident.json', selected or {'status': 'manual_snapshot'}, 'selected_session')
        bundle.json('environment-now.json', environment, 'environment_at_export_not_at_crash')
        try:
            from infinity_runtime_identity import collect as runtime_identity
            identity = runtime_identity()
        except Exception as error:
            identity = {'status': 'unavailable', 'available': False,
                        'error_type': type(error).__name__, 'runtime_resolved': False}
        bundle.json('runtime-component-identity.json', identity, 'actual_resolved_kodi_addons')
        try:
            from khc_causal import collect as causal_collect
            causal_roots = [entry[1] for entry in native_dirs]
            causal_roots += [Path(entry[1]).parent for entry in native_dirs]
            causal = causal_collect(causal_roots, environment)
        except Exception as error:
            causal = {'status': 'unavailable', 'available': False,
                      'error_type': type(error).__name__, 'root_cause_confirmed': False}
        bundle.json('causal-tree.json', causal, 'bounded_causal_diagnostic_tree')
        events = selected.get('events', [])
        timeline = '\n'.join(json.dumps(safe_json(e)) for e in events)
        if not events:
            timeline = '\n'.join(selected.get('breadcrumbs', []))
        bundle.add('timeline.txt', timeline + '\n', 'callback_observations_not_exact_button_times')
        # ALWAYS prefer the immutable incident snapshot over later rotating logs.
        if record and record.get('_legacy'):
            source = Path(record['_path'])
            snapshot = source.with_name(source.stem + '_kodi.old.log')
            if snapshot.is_file():
                bundle.file(snapshot, 'incident-logs/kodi.saved.old.log', 'legacy_saved_incident_log', tail=True)
            else:
                bundle.omitted.append({'file': 'incident-logs/kodi.saved.old.log', 'reason': 'legacy_snapshot_missing'})
        elif record and record.get('_folder'):
            folder = Path(record['_folder'])
            for p in sorted(folder.glob('*.log')):
                bundle.file(p, 'incident-logs/' + p.name, 'saved_with_selected_session', tail=True)
            for p in (sorted(folder.glob('android-*')) if include_saved_android else []):
                if p.is_file() and p.suffix in ('.json', '.txt'):
                    bundle.file(p, 'incident-native/' + p.name, 'saved_optional_same_uid_evidence')
        active_baseline = environment.get('diagnostic_baseline', {}) if isinstance(environment, dict) else {}
        baseline_epoch = active_baseline.get('epoch', 0) if isinstance(active_baseline, dict) else 0
        baseline_token = active_baseline.get('token', '') if isinstance(active_baseline, dict) else ''
        bundle.json('diagnostic-baseline.json', active_baseline or {'epoch': 0, 'utc': '', 'status': 'not_set'},
                    'diagnostic_zero_point_prebaseline_evidence_is_historical')
        old_role = ('historical_rotating_old_log_not_used_for_new_crash_attribution' if baseline_epoch
                    else 'rotating_old_log_at_export_may_be_unrelated')
        current_role = ('full_current_log_for_reference_postbaseline_analysis_uses_marker_boundary' if baseline_epoch
                        else 'current_log_at_export_not_crash_log')
        bundle.file(old_log, 'export-time/kodi.old.tail.log', old_role, tail=True)
        bundle.file(current_log, 'export-time/kodi.current.tail.log', current_role, tail=True)
        # When a fresh baseline is active, automatic signature analysis MUST NOT
        # re-surface old crashes simply because Kodi still retains rotating logs.
        # Start Fresh/Refresh Codes writes a unique token into kodi.log. If that
        # token is still present, archive a post-baseline slice and use only that
        # slice (plus saved post-baseline incident logs) for automatic analysis.
        if baseline_epoch and baseline_token:
            try:
                current_text, _info = read_tail(current_log, MAX_FILE)
                marker_text = 'diagnostic_baseline token=' + str(baseline_token)
                marker_at = current_text.rfind(marker_text)
                if marker_at >= 0:
                    post_text = current_text[marker_at:]
                    bundle.add('export-time/kodi.current.post-baseline.log', post_text,
                               'post_baseline_current_log_used_for_new_crash_analysis')
                else:
                    bundle.json('baseline-log-boundary-status.json',
                                {'status':'marker_not_in_current_tail',
                                 'note':'Full rotating logs remain reference-only and are excluded from automatic new-crash attribution.'},
                                'baseline_boundary_safety_status')
            except Exception:
                bundle.json('baseline-log-boundary-status.json',
                            {'status':'current_log_boundary_unavailable',
                             'note':'Full rotating logs remain reference-only and are excluded from automatic new-crash attribution.'},
                            'baseline_boundary_safety_status')
        if health_text:
            bundle.add('health-summary.txt', health_text, 'legacy_health_scan_not_crash_attribution')
        if scan_results is not None:
            bundle.add('scan-results.json', json.dumps(safe_json(scan_results), indent=2),
                       'scan_kodi_structured_results_same_read_only_collector', scrub=True)
        if scan_details is not None:
            bundle.add('scan-details.txt', scan_details,
                       'scan_kodi_human_readable_full_detail', scrub=True)
        if authorization_health is not None:
            bundle.add('authorization-health.json', json.dumps(safe_json(authorization_health), indent=2),
                       'privacy_safe_authorization_state_no_credential_values', scrub=True)
        if authorization_details is not None:
            bundle.add('authorization-health.txt', authorization_details,
                       'human_readable_authorization_state_no_credential_values', scrub=True)
        bundle.json('android-capture-status.json', native_status or {'status': 'not_requested'}, 'capture_availability_not_diagnosis')
        for prefix, folder in native_dirs:
            folder = Path(folder)
            try:
                if folder.is_symlink() or not folder.is_dir():
                    bundle.omitted.append({'file': 'android-optional/' + prefix,
                                           'reason': 'directory_missing_or_unverified'})
                    continue
                candidates = sorted(folder.iterdir())
            except OSError as error:
                bundle.omitted.append({'file': 'android-optional/' + prefix,
                                       'reason': 'directory_unavailable',
                                       'error_type': type(error).__name__})
                continue
            for p in candidates:
                if p.is_symlink() or not p.is_file():
                    continue
                native_name = (
                    p.name in ('android-exit-info.json', 'same-uid-crash-logcat.txt', 'android-status.json',
                               'runtime-identity.json', 'incident-boundary.json') or
                    p.name.startswith('native-crash-') or p.name.startswith('native-maps-') or
                    p.name.startswith('lifecycle-breadcrumbs') or
                    re.fullmatch(r'exit-\d+-\d+-\d+\.trace', p.name)
                )
                if native_name:
                    bundle.file(p, 'android-optional/' + prefix + '/' + p.name,
                                'optional_native_evidence_time_pid_and_incident_must_be_correlated',
                                scrub=p.suffix not in ('.trace',))
                    if p.suffix == '.trace':
                        # A privacy-minimized summary supplements—not replaces—the
                        # raw evidence already covered by the existing explicit consent.
                        from khc_native import trace_summary, MAX_TRACE
                        try:
                            with p.open('rb') as handle:
                                trace_data = handle.read(MAX_TRACE + 1)
                            trace_info = trace_summary(trace_data)
                        except (OSError, ValueError, TypeError, OverflowError) as error:
                            trace_info = {'status': 'summary_unavailable', 'error_type': type(error).__name__,
                                          'original_fault_stack_confirmed': False}
                        bundle.json('native-trace-summaries/' + prefix + '/' + p.name + '.json', trace_info,
                                    'bounded_summary_no_memory_or_installed_application_paths')
        try:
            correlation = correlate_native_incident(native_dirs, active_baseline, selected, environment)
            if not isinstance(correlation, dict) or not isinstance(correlation.get('session_exit', {}), dict):
                raise ValueError('Invalid native correlation result')
        except Exception as error:
            correlation = {'status': 'unavailable', 'available': False,
                           'error_type': type(error).__name__,
                           'temporal_scope': 'unverified',
                           'attributable_to_selected_session': False,
                           'session_exit': {'status': 'UNVERIFIED',
                               'summary': 'Session exit evidence unavailable; no crash or clean-exit conclusion.'}}
        session_exit=correlation.get('session_exit',{})
        bundle.json('SESSION-EXIT-STATUS.json',session_exit,'session_bound_os_reason_not_raw_observer_rewrite')
        bundle.add('SESSION-EXIT-STATUS.txt',session_exit.get('summary','Unverified session exit')+'\n','session_bound_os_reason')
        bundle.add('NATIVE-EVENT-STATUS.txt',
                   'Event: %s\nEvent UTC: %s\nRelation: %s\nSelected session: %s\n'
                   'Matches selected session: %s\nExport UTC: %s\n'
                   'A repeated event ID is retained history, not another crash.\n'
                   'The collector version is not the historical exit version.\n'
                   'Trace availability does not prove the original caller.\n' % (
                       correlation.get('event_id', 'none'), correlation.get('event_utc', 'unknown'),
                       correlation.get('temporal_scope'), selected.get('session_id', 'manual'),
                       correlation.get('attributable_to_selected_session'), environment.get('captured_utc', 'unknown')),
                   'read_first_event_history_not_new_crash_claim')
        bundle.json('native-incident-correlation.json', correlation,
                    'post_start_fresh_pid_timestamp_native_evidence_correlation_not_root_cause_proof')
        if skin_root:
            add_skin_xml(bundle, skin_root)
        # Clues/automatic analysis are baseline-aware. Full rotating logs can still
        # be archived for manual reference, but they are not allowed to make a
        # pre-baseline crash look new after Start Fresh.
        clue_sources = {}
        incident_texts = {}
        for e in list(bundle.entries):
            name = e['file']
            if not name.endswith(('.log', '.txt')):
                continue
            text = bundle.archive.read(name).decode('utf-8', 'replace')
            # Android buffers/maps/crash records contain retained cross-session history.
            # They remain exported and separately correlated, never promoted by text matching.
            allow_analysis = not name.startswith(('android-optional/', 'incident-native/'))
            if baseline_epoch and name in ('export-time/kodi.old.tail.log', 'export-time/kodi.current.tail.log'):
                allow_analysis = False
            if allow_analysis:
                incident_texts[name] = text
                if name.endswith('.log'):
                    clue_sources[name] = log_clues(text)
        bundle.json('log-clues.json', clue_sources,
                    'post_baseline_text_search_aids_only' if baseline_epoch else 'text_search_aids_only')
        analysis = analyze_incident_texts(incident_texts)
        if baseline_epoch:
            analysis['diagnostic_baseline'] = safe_json(active_baseline)
            analysis['prebaseline_rotating_logs_excluded'] = True
            analysis['attribution_scope'] = 'baseline_filtered_logs; Android_history_is_separately_correlated'
        analysis['session_exit'] = session_exit
        analysis['native_event_scope'] = correlation.get('temporal_scope')
        analysis['native_event_matches_selected_session'] = correlation.get('attributable_to_selected_session')
        bundle.json('incident-analysis.json', analysis, 'automatic_signature_and_correlation_analysis_not_cause_attribution')
        status = selected.get('status', 'manual_snapshot')
        summary = ('KODI HEALTH CENTER ' + VERSION + ' DIAGNOSTIC PACKAGE\n'
                   'Session explanation: '+session_exit.get('summary','Unverified')+'\n'
                   'Raw observer record: ' + status + '\n'
                   'No component has been confirmed as the crash cause.\n'
                   'An unfinished session can mean a crash, force-stop, OS kill, power loss or observer failure.\n'
                   'Python no-media exceptions and MediaCodec timeouts are clues, not proof of process death.\n'
                   'incident-analysis.json recognizes known native signatures and lists add-on IDs only as correlation clues, never blame.\n' +
                   ('With Start Fresh active, pre-baseline rotating logs are reference-only and excluded from automatic new-crash attribution.\n' if baseline_epoch else '') +
                   'incident-logs belong to the selected session; export-time logs may be from another launch.\n'
                   'A heartbeat/last event is not the exact death time. Callbacks can be delayed or never delivered.\n'
                   'Android evidence can be absent or restricted; no root, adb, privileged access or signal handler is used.\n'
                   'This add-on cannot call ApplicationExitInfo unless an APK-side collector provides its output.\n'
                   'Read NATIVE-EVENT-STATUS.txt first: post-baseline history may not be this session.\n'
                   'Optional native traces require explicit export consent; raw memory cannot be redacted.\n'
                   'native-trace-summaries/ omits raw memory and installed application paths.\n'
                   'Text redaction is best-effort. Review the ZIP before sharing. Nothing uploads automatically.\n'
                   'manifest.json records file hashes, truncation, limits and omissions.\n')
        bundle.add('READ-ME-FIRST.txt', summary, 'interpretation_and_limits')
        return bundle.close({'selected_session_id': selected.get('session_id'), 'selected_status': status,
                             'active_skin_xml_included': bool(skin_root)})
    except Exception:
        bundle.abort()
        raise
