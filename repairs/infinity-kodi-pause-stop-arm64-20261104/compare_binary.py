"""Read-only exact ELF inventories and selected ARM64 disassembly. No execution."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import mmap
import subprocess
import shutil
from collections import defaultdict
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN

PARENT = 'f89a40b5653c0091a06edd44f6ac5cdf056a649301b6751ee638c8ba88db9674'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def wanted(name):
    return ('CApplicationMessenger' in name and any(part in name for part in
            ('ProcessCheckpointDisplayMessages', 'ProcessMessage', 'SendMsg', 'Cleanup'))) or \
           'IsCheckpointPlaybackControl' in name or 'CApplication8OnAction' in name or \
           'CGUIWindowManager20OnApplicationMessage' in name or \
           ('CXBMCApp' in name and any(part in name for part in ('onPause', 'onStop', 'onResume', 'onAudioFocusChange'))) or \
           ('InfinityAndroidCheckpoint' in name and any(part in name for part in
            ('AllowNativeWrite', 'CheckpointWriteGuard', 'AuthorizeTermination', 'IsActive', '4Pump')))


def inventory(path, output, mode):
    with path.open('rb') as handle:
        whole = hashlib.file_digest(handle, 'sha256').hexdigest()
        handle.seek(0)
        elf = ELFFile(handle)
        assert elf['e_machine'] == 'EM_AARCH64' and elf.elfclass == 64
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as raw:
            sections = {}
            for section in elf.iter_sections():
                data = b'' if section['sh_type'] == 'SHT_NOBITS' else raw[section['sh_offset']:section['sh_offset'] + section['sh_size']]
                sections[section.name] = {'type': section['sh_type'], 'address': section['sh_addr'],
                    'offset': section['sh_offset'], 'size': section['sh_size'], 'flags': section['sh_flags'],
                    'alignment': section['sh_addralign'], 'file_data_sha256': digest(data)}
            exports = []
            for symbol in elf.get_section_by_name('.dynsym').iter_symbols():
                if symbol.name:
                    exports.append({'name': symbol.name, 'type': symbol['st_info']['type'],
                        'bind': symbol['st_info']['bind'], 'visibility': symbol['st_other']['visibility'],
                        'defined': symbol['st_shndx'] != 'SHN_UNDEF'})
            exports.sort(key=lambda row: row['name'])
            functions, selected, addresses = defaultdict(list), [], defaultdict(list)
            for symbol in elf.get_section_by_name('.symtab').iter_symbols():
                if symbol['st_info']['type'] != 'STT_FUNC' or not isinstance(symbol['st_shndx'], int):
                    continue
                section = elf.get_section(symbol['st_shndx'])
                size, address = symbol['st_size'], symbol['st_value']
                offset = section['sh_offset'] + address - section['sh_addr']
                code = raw[offset:offset + size]
                record = {'name': symbol.name, 'address': address, 'size': size,
                          'section': section.name, 'bind': symbol['st_info']['bind'], 'sha256': digest(code)}
                functions[symbol.name].append(record)
                addresses[address].append(symbol.name)
                if wanted(symbol.name) and size:
                    selected.append((record, code))
            disassembler = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
            disassembly = []
            immediate_report = {}
            for record, code in sorted(selected, key=lambda row: row[0]['address']):
                name = record['name']
                demangled = subprocess.check_output(['c++filt', name], text=True).strip()
                disassembly.append('\n' + demangled + '\n' + json.dumps(record, sort_keys=True))
                instructions = []
                for insn in disassembler.disasm(code, record['address']):
                    note = ''
                    if insn.mnemonic in ('bl', 'b') and insn.op_str.startswith('#0x'):
                        target = int(insn.op_str[1:], 16)
                        if target in addresses:
                            note = ' ; ' + ','.join(addresses[target])
                    disassembly.append(f'{insn.address:016x} {insn.bytes.hex():8s} {insn.mnemonic:8s} {insn.op_str}{note}')
                    instructions.append({'offset': insn.address - record['address'], 'mnemonic': insn.mnemonic, 'operands': insn.op_str})
                immediate_report[name] = instructions
            (output / (mode + '-SELECTED-DISASSEMBLY.txt')).write_text('\n'.join(disassembly) + '\n')
            (output / (mode + '-SELECTED-INSTRUCTIONS.json')).write_text(json.dumps(immediate_report, indent=2) + '\n')
            result = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': whole,
                      'machine': elf['e_machine'], 'elfclass': elf.elfclass,
                      'sections': sections, 'exports': exports, 'functions': dict(functions)}
            (output / (mode + '-ELF-INVENTORY.json')).write_text(json.dumps(result, sort_keys=True) + '\n')
            return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--parent-inventory', type=Path, help='Reuse the already measured exact452 inventory directory')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    if args.parent_inventory:
        with args.before.open('rb') as handle:
            assert hashlib.file_digest(handle, 'sha256').hexdigest() == PARENT
        before = json.loads((args.parent_inventory / 'before-ELF-INVENTORY.json').read_text())
        assert before['sha256'] == PARENT and before['bytes'] == args.before.stat().st_size
        for name in ('before-ELF-INVENTORY.json', 'before-SELECTED-DISASSEMBLY.txt', 'before-SELECTED-INSTRUCTIONS.json'):
            shutil.copyfile(args.parent_inventory / name, args.out / name)
    else:
        before = inventory(args.before, args.out, 'before')
    after = inventory(args.after, args.out, 'after')
    assert before['sha256'] == PARENT
    sections = {}
    for name in sorted(set(before['sections']) | set(after['sections'])):
        old, new = before['sections'].get(name), after['sections'].get(name)
        sections[name] = {'before': old, 'after': new, 'metadata_equal': old == new,
                         'file_bytes_equal': old is not None and new is not None and old['file_data_sha256'] == new['file_data_sha256']}
    counts = defaultdict(int)
    selected_comparison = []
    with (args.out / 'ALL-FUNCTION-BYTE-COMPARISON.csv').open('w') as handle:
        writer = csv.writer(handle)
        writer.writerow(['symbol', 'duplicate_ordinal', 'before_address', 'after_address',
                         'before_size', 'after_size', 'before_sha256', 'after_sha256', 'raw_equal'])
        for name in sorted(set(before['functions']) | set(after['functions'])):
            old = sorted(before['functions'].get(name, []), key=lambda row: row['address'])
            new = sorted(after['functions'].get(name, []), key=lambda row: row['address'])
            if len(old) > 1 or len(new) > 1:
                counts['duplicate_symbol_names'] += 1
            for index in range(max(len(old), len(new))):
                a = old[index] if index < len(old) else None
                b = new[index] if index < len(new) else None
                same = a is not None and b is not None and a['sha256'] == b['sha256']
                counts['equal' if same else 'changed_or_added_removed'] += 1
                writer.writerow([name, index, hex(a['address']) if a else '', hex(b['address']) if b else '',
                                 a['size'] if a else '', b['size'] if b else '', a['sha256'] if a else '', b['sha256'] if b else '', same])
                if wanted(name):
                    selected_comparison.append({'name': name, 'before': a, 'after': b, 'raw_equal': same})
    summary = {'before_sha256': before['sha256'], 'after_sha256': after['sha256'],
        'before_bytes': before['bytes'], 'after_bytes': after['bytes'],
        'dynamic_symbol_contract_equal': before['exports'] == after['exports'],
        'section_comparison': sections, 'function_raw_byte_counts': dict(counts),
        'selected_function_comparison': selected_comparison,
        'interpretation': 'Raw equality is exact. Changed bytes include link-address relocations and debug/build metadata; this inventory alone does not prove semantic equivalence. Duplicate local names are paired by address order and explicitly counted.',
        'android_executed': False}
    (args.out / 'BINARY-COMPARISON.json').write_text(json.dumps(summary, indent=2) + '\n')
    assert summary['dynamic_symbol_contract_equal'], 'Native dynamic symbol contract changed'
    assert any('ProcessCheckpointDisplayMessages' in row['name'] and not row['raw_equal'] for row in selected_comparison), 'Candidate compiled admission absent/unchanged'
    print(json.dumps({key: summary[key] for key in ('before_sha256', 'after_sha256', 'before_bytes', 'after_bytes', 'dynamic_symbol_contract_equal', 'function_raw_byte_counts')}, indent=2))


if __name__ == '__main__':
    main()
