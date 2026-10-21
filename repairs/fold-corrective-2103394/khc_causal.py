"""Bounded, read-only causal view of existing Infinity diagnostic evidence.

No service, persistence ownership, account data, repair, or shutdown authority.
The exporter owns its existing output ZIP; this module returns plain data only.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

CATEGORIES = (
    ('shutdown', 'Shutdown and Essential-First'),
    ('native', 'Native crashes and SIGSEGV'),
    ('anr', 'ANRs and thread waits'),
    ('storage', 'SQLite, VFS and protected writes'),
    ('python', 'Python and add-on services'),
    ('playback', 'Playback, surfaces, audio and PiP'),
    ('ui', 'Skin, focus and navigation'),
    ('android', 'Android tasks, startup and return'),
)
MAX_INPUT = 1024 * 1024
MAX_EVENTS = 240
MAX_FILES = 24
HASH = re.compile(r'[0-9a-f]{64}\Z')
OWNER = re.compile(r'(?:plugin|script|service|skin)\.[a-zA-Z0-9_.-]+\Z')


def identifier(value, limit=120):
    value = str(value or '')
    return value[:limit] if re.fullmatch(r'[A-Za-z0-9_.:<>()-]*', value) else '<redacted>'


def _integer(value):
    return value if type(value) is int and value >= 0 else None


def _detail(value):
    """Allow exception types, numeric codes and bounded basename-only stacks."""
    text = str(value or '')[:4096]
    parts = []
    for key in ('exception', 'errno', 'sqlite_code', 'sqlite_errorcode', 'verb', 'native_errno',
                'signal', 'si_code', 'pc', 'fault_address', 'arch'):
        match = re.search(r'(?:^|[; ,])' + key + r'=([A-Za-z0-9_.-]{1,90})', text)
        if match:
            parts.append(key + '=' + match[1])
    match = re.search(r'(?:^|;)stack=([^;]+)', text)
    if match:
        frames = []
        for frame in match[1].split('>')[-8:]:
            if re.fullmatch(r'(?:[A-Za-z0-9_.-]+\.py|<observer>):\d{1,8}:[A-Za-z0-9_<>]{1,80}', frame):
                frames.append(frame)
        parts.append('stack=' + ('>'.join(frames) if frames else '<missing>'))
    return ';'.join(parts)[:1600]


def _category(text):
    text = text.lower()
    for words, category in (
        (('sqlite', 'vfs', 'protected_write', 'persistence'), 'storage'),
        (('segv', 'fatal_signal', 'native_crash'), 'native'),
        (('anr', 'deadlock', 'futex', 'gil_acquire'), 'anr'),
        (('surface', 'playback', 'audio', 'subtitle', 'pip'), 'playback'),
        (('touch', 'focus', 'skin', 'navigation', 'theme'), 'ui'),
        (('python', 'script', 'invoker'), 'python'),
        (('checkpoint', 'close', 'shutdown', 'barrier', 'terminate'), 'shutdown'),
    ):
        if any(word in text for word in words):
            return category
    return 'android'


def event(row, source):
    operation = str(row.get('operation_kind') or row.get('reason') or row.get('phase') or row.get('event') or '')
    outcome = str(row.get('outcome') or row.get('error') or row.get('reason') or row.get('detail') or '')
    owner = str(row.get('addon_id') or '')
    if not owner and isinstance(row.get('writer'), str):
        owner = row['writer'].split(':', 1)[0]
    # Only the native admission error's explicit writer field may name an owner.
    owner_match = re.search(r'unverified_protected_writer:((?:plugin|script|service)\.[\w.-]+):', outcome)
    if not owner and owner_match:
        owner = owner_match[1]
    failed = operation.startswith('native_crash.') or any(word in (operation + ' ' + outcome).lower()
                 for word in ('failed', 'failure', 'exception', 'denied', 'unverified_protected_writer'))
    details = _detail(row.get('error_detail') or row.get('detail') or outcome)
    sha = str(row.get('native_engine_sha256') or row.get('engine_sha256') or '')
    gaps = []
    if failed and not details:
        gaps.append('Original exception type, operation stack or code was not captured.')
    if not HASH.fullmatch(sha):
        sha = None
        gaps.append('Matching native engine hash is absent from this event.')
    category='shutdown' if operation in ('CHECKPOINT_FAILED','checkpoint.failed') else _category(operation + ' ' + str(row.get('event') or '') + ' ' + outcome)
    public_outcome=outcome.split(';',1)[0]
    # This native admission prefix is a known structural separator, rather
    # than permission to copy arbitrary exception messages or private paths.
    if re.fullmatch(r'native_admission: unverified_protected_writer:(?:plugin|script|service)\.[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+',public_outcome):
        public_outcome=public_outcome.replace('native_admission: ','native_admission:')
    return dict(category=category,
                operation=identifier(operation), outcome=identifier(public_outcome,240),
                error_context=details, pid=_integer(row.get('pid')), tid=_integer(row.get('tid')),
                epoch_ns=_integer(row.get('epoch_ns')) or (
                    row['epoch_ms'] * 1000000 if type(row.get('epoch_ms')) is int else None),
                monotonic_ns=_integer(row.get('monotonic_ns') or row.get('elapsed_ns')),
                observed_epoch_ms=_integer(row.get('observed_epoch_ms')),
                session=identifier(row.get('session') or row.get('session_start_ns')),
                build_version_code=_integer(row.get('build_version_code') or row.get('version_code') or row.get('versionCode')),
                component=owner if OWNER.fullmatch(owner) else None,
                owner_verified=bool(OWNER.fullmatch(owner)) and row.get('owner_verified') is True, engine_sha256=sha,
                source=source, consequence=('Protected save remains blocked.' if
                    'unverified_protected_writer' in outcome else 'See observed operation.'),
                role=('advisory' if row.get('blocking') is False else 'failure') if failed else 'observation',
                confidence='observed', gaps=gaps)


def anr_waits(text):
    """Keep explicit thread/symbol relationships; do not invent mutex owners."""
    threads = []
    for block in re.split(r'\n(?="[^\n]+" (?:daemon )?prio=)', text[:MAX_INPUT]):
        tid = re.search(r'\| sysTid=(\d+)', block)
        if not tid:
            continue
        symbols = [symbol for symbol in (
            'CXBMCApp::surfaceDestroyed', 'CApplicationMessenger::SendMsg',
            'CPythonInvoker::stop', 'take_gil', 'PyEval_RestoreThread',
            'CApplication::LockFrameMoveGuard', 'xbmc::getCondVisibility',
            'ControlList::getSelectedItem',
            'CDirectoryProvider::OnJobComplete') if symbol in block]
        if symbols:
            threads.append({'tid': int(tid[1]), 'wait_symbols': symbols})
    display = next((x for x in threads if 'CXBMCApp::surfaceDestroyed' in x['wait_symbols']), None)
    stopping = next((x for x in threads if 'CPythonInvoker::stop' in x['wait_symbols'] and
                     'PyEval_RestoreThread' in x['wait_symbols']), None)
    children = [x for x in threads if 'CApplication::LockFrameMoveGuard' in x['wait_symbols'] and
                'ControlList::getSelectedItem' in x['wait_symbols']]
    chain = []
    if display and stopping and children:
        chain = [dict(from_tid=display['tid'], to_tid=stopping['tid'], resource='Kodi message completion'),
                 dict(from_tid=stopping['tid'], to_tid=None, resource='Python GIL'),
                 dict(from_tid=children[0]['tid'], to_tid=None, resource='frame/graphics guard')]
    return {'threads': threads[:64], 'wait_chain': chain,
            'confidence': 'source_correlation_required' if chain else 'incomplete',
            'gaps': ['A stack sample does not itself identify every mutex owner or the GIL owner.',
                     'Physical lifecycle retest is required; this report does not certify a fix.']}


def build(inputs, environment=None):
    """Build a bounded report from already collected text/JSON byte snapshots."""
    timeline, waits, gaps = [], [], []
    for source, raw in list(inputs.items())[:MAX_FILES]:
        if isinstance(raw, bytes):
            raw = raw[-MAX_INPUT:].decode('utf-8', 'replace')
        elif not isinstance(raw, str):
            raw = json.dumps(raw)
        raw = raw[-MAX_INPUT:]
        name = Path(source).name
        if name.startswith('native-crash-'):
            fields={key:value for key,value in re.findall(r'(?m)^([a-z_][a-z0-9_]*)=([A-Za-z0-9_.-]{1,90})$',raw)
                    if key in ('schema','timestamp_ms','pid','tid','signal','si_code','fault_address','pc','arch','native_engine_sha256')}
            if fields.get('signal','').isdecimal() and fields.get('pid','').isdecimal():
                record=dict(event='native_crash.original_signal',outcome='signal_'+fields['signal'],
                    pid=int(fields['pid']),tid=int(fields['tid']) if fields.get('tid','').isdecimal() else None,
                    native_engine_sha256=fields.get('native_engine_sha256'),
                    epoch_ms=int(fields['timestamp_ms']) if fields.get('timestamp_ms','').isdecimal() else None,
                    detail=';'.join(k+'='+fields[k] for k in ('signal','si_code','pc','fault_address','arch') if k in fields))
                fact=event(record,name)
                fact['gaps'].append('Raw original-handler registers require symbolication with the exact matching engine; no faulting instruction or repair is proved here.')
                timeline.append(fact)
            elif raw.strip():gaps.append(name+': original signal fields unavailable')
            continue
        if name.endswith('.anr.txt') or ('Input dispatching timed out' in raw and 'sysTid=' in raw):
            waits.append(anr_waits(raw))
            timeline.append(event({'event': 'anr.input_timeout', 'outcome': 'Android input timeout'}, name))
            continue
        rows = []
        if name.endswith('.json'):
            try:
                row = json.loads(raw)
                if isinstance(row, dict):
                    rows.append(row)
            except (ValueError, TypeError):
                gaps.append(name + ': invalid or truncated JSON snapshot')
        else:
            for line in raw.splitlines()[-6000:]:
                try:
                    if line.startswith('{'):
                        row = json.loads(line)
                    elif '[InfinityTouch]' in line:
                        row = json.loads(line.split('[InfinityTouch]', 1)[1].strip())
                    else:
                        continue
                    if isinstance(row, dict):
                        rows.append(row)
                except (ValueError, TypeError):
                    continue
        for row in rows:
            if any(k in row for k in ('phase', 'event', 'operation_kind', 'error')):
                timeline.append(event(row, name))
            native = row.get('last_native_status', {})
            if isinstance(native, dict):
                persistence = native.get('script_persistence', {})
                if isinstance(persistence, dict):
                    for blocker in persistence.get('blockers', [])[:64]:
                        if isinstance(blocker, dict):
                            fact=event(dict(blocker,pid=row.get('pid'),session=row.get('session'),
                                observed_epoch_ms=row.get('updated_epoch_ms')),name)
                            fact['gaps'].append('Failure occurrence time is unavailable; this receipt only proves when the sticky failure was observed.')
                            timeline.append(fact)
    # Failures are retained first; repetitive wait observations cannot evict them.
    failures = [x for x in timeline if x['role'] == 'failure']
    observations = [x for x in timeline if x['role'] != 'failure']
    timeline = failures[-MAX_EVENTS:] + observations[-max(0, MAX_EVENTS-len(failures)):]
    timeline = sorted(timeline, key=lambda x: (x['epoch_ns'] or 0, x['monotonic_ns'] or 0))[-MAX_EVENTS:]
    for i, row in enumerate(timeline):
        row['id'] = 'event-' + str(i)
    relations = []
    for current in timeline:
        if current['operation'] not in ('CHECKPOINT_FAILED', 'checkpoint.failed'):
            continue
        candidates = [x for x in failures if x['category'] == 'storage' and
                      x['pid'] == current['pid'] and x['session'] == current['session'] and
                      x['pid'] is not None and x['session'] and x['epoch_ns'] is not None and
                      current['epoch_ns'] is not None and x['epoch_ns'] <= current['epoch_ns']]
        if candidates:
            primary = max(candidates, key=lambda x:x['epoch_ns'])
            if 'id' in primary:
                relations.append({'cause': primary['id'], 'consequence': current['id'],
                                  'confidence': 'same_process_session_order',
                                  'detail': 'Inspect the original operation; temporal order alone is not root-cause proof.'})
    groups = [{'id': key, 'label': label,
               'events': [x['id'] for x in timeline if x['category'] == key],
               'status': 'observed' if any(x['category'] == key for x in timeline) else 'needs_evidence'}
              for key, label in CATEGORIES]
    if not timeline:
        gaps.append('No supported causal events were available in the supplied snapshot.')
    return {'schema': 1, 'read_only': True, 'termination_authority': False,
            'categories': groups, 'timeline': timeline, 'relations': relations,
            'anr_waits': waits, 'gaps': gaps, 'physical_acceptance': 'needs_evidence',
            'build': re.sub(r'[^A-Za-z0-9_. ():+-]','?',str((environment or {}).get('kodi_build') or ''))[:160],
            'original_sigsegv': 'needs_evidence'}


def collect(roots, environment=None):
    inputs = {}
    folders=[]
    for root in list(roots)[:8]:
        root=Path(root);folders.extend((root,root/'traces'))
    for root in folders:
        root = Path(root)
        if root.is_symlink() or not root.is_dir():
            continue
        for path in sorted(root.iterdir()):
            if len(inputs) >= MAX_FILES:
                break
            if path.is_symlink() or not path.is_file() or path.suffix not in ('.json', '.jsonl', '.txt', '.log', '.trace'):
                continue
            if any(word in path.name for word in ('settings', 'account', 'token', 'source')):
                continue
            try:
                with path.open('rb') as stream:
                    stream.seek(0, 2)
                    stream.seek(max(0, stream.tell()-MAX_INPUT))
                    inputs[path.name] = stream.read(MAX_INPUT)
            except OSError:
                pass
    return build(inputs, environment)


def text(report):
    out = ['Infinity Health Center — diagnostic tree',
           'Observed evidence only. Missing evidence never authorizes shutdown.']
    for group in report['categories']:
        out.append(group['label'] + ' — ' + group['status']+' ('+str(len(group['events']))+')')
    out.append('\nCentral event timeline — build '+report['build'])
    for row in report['timeline']:
        out.append('%s | %s | epoch_ns=%s | pid=%s tid=%s | %s | %s' %
                   (row['id'],row['role'],row['epoch_ns'],row['pid'],row['tid'],row['operation'],row['outcome']))
        out.append('Component=%s | session=%s | build=%s | engine=%s | confidence=%s' %
                   (row['component'] or 'unverified',row['session'],row['build_version_code'],
                    row['engine_sha256'] or 'missing',row['confidence']))
        if row['error_context']:out.append(row['error_context'])
        out.extend('Gap: ' + x for x in row['gaps'])
    out.extend('\nGap: ' + x for x in report['gaps'])
    return '\n'.join(out)[:96000]
