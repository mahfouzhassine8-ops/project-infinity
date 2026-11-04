"""Read-only classification of the already inventoried, selected ARM64 methods.

This is not an emulator or proof of whole-engine semantic equivalence. Preserve
the raw comparisons; never normalize arbitrary data or instruction constants.
"""
from pathlib import Path
import argparse
import collections
import json
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True, type=Path)
    args = parser.parse_args()
    root = args.evidence
    inventories = [json.loads((root / (side + '-ELF-INVENTORY.json')).read_text())
                   for side in ('before', 'after')]
    code = [json.loads((root / (side + '-SELECTED-INSTRUCTIONS.json')).read_text())
            for side in ('before', 'after')]
    addresses = []
    for inv in inventories:
        index = collections.defaultdict(set)
        for name, records in inv['functions'].items():
            for record in records:
                index[record['address']].add(name)
        addresses.append(index)

    def section_position(inv, value, page=False):
        for name, section in inv['sections'].items():
            if not (section['flags'] & 2):
                continue
            start = section['address'] & ~4095 if page else section['address']
            if start <= value < section['address'] + section['size']:
                return name, value - start
        return None

    results = []
    for name, before in sorted(code[0].items()):
        if 'ProcessCheckpointDisplayMessages' in name:
            continue  # Authorized semantic delta, separately inspected verbatim.
        after = code[1].get(name)
        records = [inv['functions'][name] for inv in inventories]
        assert len(records[0]) == len(records[1]) == 1, 'Ambiguous selected symbol'
        bases = [r[0]['address'] for r in records]
        sizes = [r[0]['size'] for r in records]
        assert after is not None and len(before) == len(after) and sizes[0] == sizes[1]
        changes = collections.Counter()
        unresolved = []
        for old, new in zip(before, after):
            if old == new:
                changes['exact_instruction'] += 1
                continue
            mnemonic = old['mnemonic']
            if old['offset'] != new['offset'] or mnemonic != new['mnemonic']:
                unresolved.append({'before': old, 'after': new})
                continue
            accepted = mnemonic in ('bl', 'b', 'adr', 'adrp', 'cbz', 'cbnz', 'tbz', 'tbnz') or mnemonic.startswith('b.')
            matches = [re.search(r'#(0x[0-9a-f]+)$', insn['operands']) for insn in (old, new)]
            if not accepted or not all(matches):
                unresolved.append({'before': old, 'after': new})
                continue
            operands = [insn['operands'][:m.start()] for insn, m in zip((old, new), matches)]
            targets = [int(m.group(1), 16) for m in matches]
            if operands[0] != operands[1]:
                unresolved.append({'before': old, 'after': new})
            elif mnemonic != 'adrp' and all(base <= target < base + size for base, target, size in zip(bases, targets, sizes)) and targets[0] - bases[0] == targets[1] - bases[1]:
                changes['same_intrafunction_target_offset'] += 1
            elif mnemonic in ('bl', 'b') and addresses[0][targets[0]] & addresses[1][targets[1]]:
                changes['same_named_function_target'] += 1
            else:
                positions = [section_position(inv, target, mnemonic == 'adrp') for inv, target in zip(inventories, targets)]
                if positions[0] is not None and positions[0] == positions[1]:
                    changes['same_allocated_section_page_offset' if mnemonic == 'adrp' else 'same_allocated_section_offset'] += 1
                else:
                    unresolved.append({'before': old, 'after': new, 'section_positions': positions})
        results.append({'symbol': name, 'instruction_count': len(before), 'classification': dict(changes), 'unresolved': unresolved})

    report = {'native_before': inventories[0]['sha256'], 'native_after': inventories[1]['sha256'],
              'selected_methods': len(results), 'methods': results,
              'all_selected_changes_classified': all(not r['unresolved'] for r in results),
              'limits': 'Selected unchanged methods only. PC-relative operands must retain intra-method offsets, named targets, or allocated-section offsets. This does not compare every code/data relocation or establish Android execution.'}
    (root / 'SELECTED-LINK-CHANGE-REVIEW.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'selected_methods': len(results), 'all_selected_changes_classified': report['all_selected_changes_classified'],
                      'unresolved_count': sum(len(r['unresolved']) for r in results)}, indent=2))
    assert report['all_selected_changes_classified'], 'Inspect unclassified selected machine-code differences'


if __name__ == '__main__':
    main()
