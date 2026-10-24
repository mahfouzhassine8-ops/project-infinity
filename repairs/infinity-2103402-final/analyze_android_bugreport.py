"""Read-only, allowlisted summary of supplied Android crash evidence.

Never exports raw memory, user paths, provider data or unrelated process logs.
Tombstone protobuf field numbers follow AOSP debuggerd/proto/tombstone.proto.
Raw inputs stay outside the repository; a missing trace is not a clean bill.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile

PROCESS = 'com.projectinfinity.kodi:kodi'
PACKAGE = 'com.projectinfinity.kodi'
TARGET_TIME = '2026-10-24 15:22:18.390'
TARGET_PID = 9097
MAX_MEMBER = 24 * 1024 * 1024
MAX_DUMPSTATE = 512 * 1024 * 1024


def varint(data, offset):
    value = 0
    for shift in range(0, 70, 7):
        if offset >= len(data): raise ValueError('Truncated protobuf varint')
        byte = data[offset]; offset += 1
        value |= (byte & 127) << shift
        if not byte & 128: return value, offset
    raise ValueError('Oversized protobuf varint')


def fields(data):
    at = 0
    while at < len(data):
        key, at = varint(data, at)
        number, wire = key >> 3, key & 7
        if not number: raise ValueError('Invalid protobuf field')
        if wire == 0:
            value, at = varint(data, at)
        elif wire in (1, 2, 5):
            if wire == 2: size, at = varint(data, at)
            else: size = 8 if wire == 1 else 4
            if size > len(data) - at: raise ValueError('Truncated protobuf field')
            value = data[at:at + size]; at += size
        else: raise ValueError('Unsupported protobuf wire type')
        yield number, value


def proto_header(data):
    result = {}
    names = {4: 'timestamp', 5: 'pid', 6: 'tid', 9: 'process', 20: 'uptime_seconds'}
    for key, value in fields(data):
        if key in names:
            result[names[key]] = value.decode('utf-8', 'replace') if isinstance(value, bytes) else value
    return result


def recovered_registers(text):
    # Only the crashing thread's displayed memory; do not concatenate across gaps.
    memory = {}
    for address, a, b in re.findall(r'^\s*([0-9a-f]{16}) ([0-9a-f]{16}) ([0-9a-f]{16})  ',
                                     text.split('memory map (', 1)[0], re.M):
        for i, value in enumerate(struct.pack('<QQ', int(a, 16), int(b, 16))):
            address_i = int(address, 16) + i
            if address_i in memory and memory[address_i] != value:
                raise ValueError('Conflicting displayed memory')
            memory[address_i] = value
    chunks = []; last = -2
    for address in sorted(memory):
        if address != last + 1: chunks.append(bytearray())
        chunks[-1].append(memory[address]); last = address
    allowed = ('schema', 'timestamp_ms', 'pid', 'tid', 'signal', 'si_code', 'pc', 'sp', 'fp', 'lr', 'pstate')
    candidates = []
    for data in chunks:
        start = data.find(b'schema=1\n')
        if start < 0: continue
        result = {}
        for line in data[start:].split(b'\n')[:-1]:
            match = re.fullmatch(rb'([a-z_]+)=(-?(?:0x[0-9a-f]+|[0-9]+))', line)
            if match and match[1].decode() in allowed:
                result[match[1].decode()] = int(match[2], 16 if b'0x' in match[2] else 10)
        if result.get('schema') == 1: candidates.append(result)
    # si_addr is a union: SIGABRT's sender bytes are NOT a fault address.
    return candidates


def summarize_tombstone(raw):
    text = raw.decode('utf-8', 'replace')
    head = text[:5000]
    def match(pattern):
        value = re.search(pattern, head, re.M)
        return value.group(1) if value else None
    process = match(r'^Cmdline: (.+)$')
    if process != PROCESS: return None
    result = {'process': process, 'timestamp': match(r'^Timestamp: (.+)$'),
              'pid': int(match(r'^pid: (\d+)') or 0),
              'tid': int(match(r'^pid: .*?tid: (\d+)') or 0),
              'signal': int(match(r'^signal (\d+)') or 0),
              'sha256': hashlib.sha256(raw).hexdigest()}
    abort = match(r"^Abort message: '(.*)'$")
    known = {'Pure virtual function called!', 'Scudo ERROR: internal map failure (error desc=Out of memory)'}
    result['abort_kind'] = abort if abort in known else 'not_in_allowlist_or_absent'
    result['crashing_frames'] = []
    # Only symbols/relative PCs/binary basenames/build IDs, never private paths.
    for line in head.split('backtrace:', 1)[-1].split('\n\n', 1)[0].splitlines():
        m = re.search(r'#\d+ pc ([0-9a-f]+)\s+\S*/([^/\s]+) \(([^)]+)\)(?: \(BuildId: ([0-9a-f]+)\))?', line)
        if m:
            result['crashing_frames'].append(dict(zip(('relative_pc', 'binary', 'symbol', 'build_id'), m.groups())))
    records = recovered_registers(text)
    result['recovered_prehandler_records'] = [r for r in records if
        r.get('pid') == result['pid'] and r.get('tid') == result['tid'] and r.get('signal') == result['signal']]
    result['original_call_stack_available'] = False if any(
        'restore_and_reraise' in f['symbol'] for f in result['crashing_frames']) else None
    counts = Counter(); sizes = Counter(); page_counts = Counter()
    region = text.split('memory map (', 1)
    if len(region) == 2:
        header, body = region[1].split('\n', 1)
        result['reported_mapping_count'] = int(header.split()[0])
        for line in body.split('\n\n', 1)[0].splitlines():
            m = re.match(r"\s*([0-9a-f']+)-([0-9a-f']+)\s+([rwxps-]+)\s+[0-9a-f]+\s+([0-9a-f]+)(?:\s+(.*))?", line)
            if not m: continue
            start, end, perms, size, name = m.groups()
            allowed = {'[anon:scudo:primary]', '[anon:scudo:primary_reserve]', '[anon:scudo:secondary]', '[anon:thread signal stack]'}
            label = name if name in allowed else ('unnamed' if not name else 'other')
            counts[label] += 1; sizes[label] += int(size, 16)
            if label == '[anon:scudo:secondary]': page_counts[str(int(size, 16))] += 1
        result.update(mapping_counts=dict(counts), mapping_virtual_bytes=dict(sizes),
                      scudo_secondary_size_counts=dict(page_counts))
    result['threads'] = len(re.findall(r'^pid: .*?tid: \d+', text, re.M))
    result['root_cause_confirmed'] = False
    return result


def exit_records(lines):
    active = False; row = None; rows = []; consumed = 0
    for line in lines:
        consumed += len(line.encode('utf-8'))
        if consumed > MAX_DUMPSTATE: raise ValueError('Dumpstate exceeds bounded input')
        if line.startswith('  package: '):
            if row: rows.append(row); row = None
            active = line.strip() == 'package: ' + PACKAGE
        if not active: continue
        m = re.search(r'timestamp=(\d{4}-\d\d-\d\d [\d:.]+) pid=(\d+) ', line)
        if m:
            if row: rows.append(row)
            row = {'timestamp_local': m[1], 'pid': int(m[2])}
        if not row: continue
        m = re.search(r'process=(\S+) reason=(\d+) .*?subreason=(\d+) .*?status=(\d+)', line)
        if m: row.update(process=m[1], reason=int(m[2]), subreason=int(m[3]), exit_status=int(m[4]))
        m = re.search(r'importance=(\d+) pss=(\S+) rss=(\S+) .*?trace=(\S+)', line)
        if m: row.update(importance=int(m[1]), pss_display=m[2], rss_display=m[3], trace_available=m[4] != 'null')
        m = re.search(r'description=excessive cpu (\d+) during (\d+) dur=(\d+) limit=(\d+)', line)
        if m: row['os_cpu_description_numbers'] = dict(zip(('cpu_ms', 'window_ms', 'duration_ms', 'limit'), map(int, m.groups())))
    if row: rows.append(row)
    return [r for r in rows if r.get('process') in (PACKAGE, PROCESS)]


def analyze(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''): digest.update(block)
    result = {'schema': 1, 'bugreport_sha256': digest.hexdigest(), 'read_only': True,
              'timezone': 'America/Detroit', 'raw_data_included': False}
    headers = []; text_headers = []; details = []
    with ZipFile(path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())): raise ValueError('Duplicate archive names')
        for member in archive.infolist():
            if member.filename == 'dumpstate.txt':
                if member.file_size > MAX_DUMPSTATE: raise ValueError('Dumpstate too large')
                with archive.open(member) as stream:
                    result['exit_records'] = exit_records(io.TextIOWrapper(stream, encoding='utf-8', errors='replace'))
            elif re.fullmatch(r'FS/data/tombstones/tombstone_\d+(\.pb)?', member.filename):
                if member.file_size > MAX_MEMBER: raise ValueError('Tombstone too large')
                raw = archive.read(member)
                if member.filename.endswith('.pb'):
                    header = proto_header(raw)
                    # Coverage includes all protobufs; only own identity retained.
                    if header.get('process') == PROCESS:
                        headers.append(dict(header, member=member.filename, sha256=hashlib.sha256(raw).hexdigest()))
                else:
                    summary = summarize_tombstone(raw)
                    if summary:
                        text_headers.append({key: summary[key] for key in ('timestamp', 'pid', 'tid', 'signal', 'process', 'sha256')})
                        if summary['timestamp'].startswith('2026-10-23 '):
                            details.append(dict(summary, member=member.filename))
        result['tombstone_text_members_checked'] = sum(bool(re.fullmatch(r'FS/data/tombstones/tombstone_\d+', n)) for n in archive.namelist())
        result['tombstone_proto_members_checked'] = sum(n.endswith('.pb') and '/tombstones/' in n for n in archive.namelist())
    result['own_proto_headers'] = headers
    result['own_text_headers'] = text_headers
    result['oct23_incidents'] = details
    result['search'] = {'exit': next((r for r in result.get('exit_records', []) if
        r['timestamp_local'] == TARGET_TIME and r['pid'] == TARGET_PID and r['process'] == PROCESS), None),
        'matching_proto_tombstones': [h for h in headers if h['pid'] == TARGET_PID and h['timestamp'].startswith('2026-10-24 ')],
        'matching_text_tombstones': [h for h in text_headers if h['pid'] == TARGET_PID and h['timestamp'].startswith('2026-10-24 ')],
        'root_cause_confirmed': False, 'fix_claimed': False}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bugreport', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(analyze(args.bugreport), indent=2) + '\n')
