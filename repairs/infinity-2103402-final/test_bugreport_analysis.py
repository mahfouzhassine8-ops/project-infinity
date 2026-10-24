import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile

import analyze_android_bugreport as a


def encode_varint(number):
    out = bytearray()
    while number > 127:
        out.append((number & 127) | 128); number >>= 7
    out.append(number)
    return bytes(out)


def proto(**kwargs):
    out = bytearray()
    for number, value in ((4, kwargs['timestamp']), (5, kwargs['pid']), (9, kwargs['process'])):
        if isinstance(value, str):
            data = value.encode(); out += encode_varint(number << 3 | 2) + encode_varint(len(data)) + data
        else: out += encode_varint(number << 3) + encode_varint(value)
    return bytes(out)


class BugreportTests(unittest.TestCase):
    def test_exit_and_proto_scope_do_not_mix_pid_reuse_or_other_processes(self):
        own = ('  package: com.projectinfinity.kodi\n'
               ' timestamp=2026-10-24 15:22:18.390 pid=9097 realUid=123\n'
               ' process=com.projectinfinity.kodi:kodi reason=2 (SIGNALED) subreason=0 (UNKNOWN) status=7\n'
               ' importance=100 pss=0.00 rss=719MB state=73 bytes trace=null\n')
        other = own.replace('com.projectinfinity.kodi', 'private.other.app')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bugreport.zip'
            with ZipFile(path, 'w') as z:
                z.writestr('dumpstate.txt', other + own)
                z.writestr('FS/data/tombstones/tombstone_27.pb', proto(timestamp='2026-10-23 12:00:00-0400', pid=9097, process=a.PROCESS))
                z.writestr('FS/data/tombstones/tombstone_28.pb', proto(timestamp='2026-10-24 15:22:18-0400', pid=9097, process='private.other.app'))
            result = a.analyze(path)
        self.assertEqual(result['search']['exit']['exit_status'], 7)
        self.assertFalse(result['search']['exit']['trace_available'])
        self.assertEqual(result['search']['matching_proto_tombstones'], [])
        self.assertEqual(len(result['exit_records']), 1)
        self.assertNotIn('private.other', json.dumps(result))

    def test_original_registers_recovered_only_from_contiguous_complete_fields(self):
        text = b'schema=1\npid=3071\ntid=3071\nsignal=6\nsi_code=-1\npc=0x716c9129f0\nfault_address=0x1234\nlr=0xabc\n'
        text += b'\x00' * ((-len(text)) % 16)
        lines = []
        for i in range(0, len(text), 16):
            x, y = struct.unpack('<QQ', text[i:i+16])
            lines.append(f'    {4096+i:016x} {x:016x} {y:016x}  displayed memory')
        recovered = a.recovered_registers('\n'.join(lines))
        self.assertEqual(recovered[0]['pc'], 0x716c9129f0)
        self.assertEqual(recovered[0]['si_code'], -1)
        self.assertNotIn('fault_address', recovered[0])
        # Remove the block with the PC; bytes either side cannot create a record.
        broken = '\n'.join(line for line in lines if not line.startswith('    0000000000001030'))
        self.assertNotIn('pc', a.recovered_registers(broken)[0])

    def test_map_summary_preserves_counts_without_exporting_private_paths(self):
        raw = b'''Timestamp: 2026-10-23 22:00:06-0400
Cmdline: com.projectinfinity.kodi:kodi
pid: 3485, ppid: 123, tid: 18800, name: Thread-48
signal 6 (SIGABRT), code -6
Abort message: 'Scudo ERROR: internal map failure (error desc=Out of memory)'
backtrace:
 #00 pc 00002158 /private/path/libinfinitycrash.so (restore_and_reraise+168) (BuildId: abcd)

memory map (3 entries):
    00001000-00001fff rw- 0 1000 [anon:scudo:secondary]
    00002000-00003fff --- 0 2000
    00004000-00004fff r-- 0 1000 /private/account/token

'''
        row = a.summarize_tombstone(raw)
        self.assertEqual(row['mapping_counts'], {'[anon:scudo:secondary]': 1, 'unnamed': 1, 'other': 1})
        self.assertEqual(row['mapping_virtual_bytes']['[anon:scudo:secondary]'], 4096)
        self.assertFalse(row['original_call_stack_available'])
        self.assertNotIn('/private', json.dumps(row))

    def test_malformed_and_oversized_proto_fields_fail_closed(self):
        for data in (b'\x22\xff', b'\x22\x08abc', b'\x00', b'\xff'*12):
            with self.subTest(data=data), self.assertRaises(ValueError):
                list(a.fields(data))


if __name__ == '__main__': unittest.main(verbosity=2)
