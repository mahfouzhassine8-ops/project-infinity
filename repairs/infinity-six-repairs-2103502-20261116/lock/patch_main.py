"""Seven lock-only hooks in exact502 Main; no replacement Activity template."""
import argparse
import hashlib
import json
from pathlib import Path
import re

PREIMAGE = '484c40e499c3d1c2109297486b7c2bbde86bb6223279cad27d04070ee818f9dc'
OWNER = 'Lcom/projectinfinity/kodi/Main;'
BRIDGE = 'Lcom/projectinfinity/kodi/InfinityVideoLockBridge;'
HOOKS = {
    'onResume()V': ('onResume', False, True),
    'onPause()V': ('onPause', False, False),
    'onDestroy()V': ('onDestroy', False, False),
    'onConfigurationChanged(Landroid/content/res/Configuration;)V': ('onConfigurationChanged', False, False),
    'onPictureInPictureModeChanged(Z)V': ('onPictureInPictureChanged', True, False),
    'onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V': ('onPictureInPictureChanged', True, False),
    'infinityOnPlaybackStateChanged()V': ('onPlaybackChanged', False, False),
}
METHODS = re.compile(r'^\.method[^\n]*\n.*?^\.end method$', re.M | re.S)


def hook_text(name, second):
    registers = 'p0 .. p1' if second else 'p0 .. p0'
    args = OWNER + ('Z' if second else '')
    return ('\n    # Infinity Repair5: session-owned lock; original method retained.\n'
            f'    invoke-static/range {{{registers}}}, {BRIDGE}->{name}({args})V\n\n')


def patch(before):
    if hashlib.sha256(before).hexdigest() != PREIMAGE:
        raise ValueError('Main is not the authenticated signed502 disassembly')
    source = before.decode()
    changed = {}

    def replace(match):
        block = match.group(0)
        signature = block.splitlines()[0].split()[-1]
        if signature not in HOOKS:
            return block
        name, second, last = HOOKS[signature]
        text = hook_text(name, second)
        if last:
            # All existing denied-entry / pending-exit returns are before this final return.
            offset = block.rfind('    return-void')
        else:
            registers = re.search(r'^    \.registers \d+\n', block, re.M)
            if not registers:
                raise ValueError('Unexpected original method register declaration')
            offset = registers.end()
        if offset < 0:
            raise ValueError('Unexpected original method control flow')
        after = block[:offset] + text + block[offset:]
        if after.replace(text, '', 1) != block:
            raise ValueError('Non-hook method change')
        changed[signature] = {'before': hashlib.sha256(block.encode()).hexdigest(),
                              'after': hashlib.sha256(after.encode()).hexdigest()}
        return after

    after = METHODS.sub(replace, source)
    if set(changed) != set(HOOKS):
        raise ValueError('Unexpected Main method set')
    restored = after
    for signature, (name, second, last) in HOOKS.items():
        restored = restored.replace(hook_text(name, second), '', 1)
    if restored != source:
        raise ValueError('Main preservation failed')
    return after.encode(), changed, len(METHODS.findall(source)) - len(changed)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--receipt', required=True)
    args = p.parse_args()
    result, changed, unchanged = patch(Path(args.baseline).read_bytes())
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(result)
    receipt = {'status': 'PASS_SEVEN_HOOK_SOURCE_PRESERVATION_ONLY',
               'baseline_dex_member': 'classes3.dex',
               'baseline_dex_sha256': '5634f2376e5d0bf6176ebef6fa1ac16bb22fdecc1d018ac078f266bb757fe9b8',
               'before_smali_sha256': PREIMAGE, 'after_smali_sha256': hashlib.sha256(result).hexdigest(),
               'changed_methods': changed, 'unchanged_Main_methods': unchanged,
               'original_fields_and_method_bodies': 'BYTE_IDENTICAL_AFTER_REMOVING_ONLY_SEVEN_STATIC_CALLS',
               'manifest_or_other_class_changes': 'NONE_IN_THIS_STAGE',
               'not_verified': ['assembled DEX', 'Android runtime linkage', 'physical lock behavior']}
    Path(args.receipt).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'changed_methods': len(changed), 'unchanged_Main_methods': unchanged}))


if __name__ == '__main__':
    main()
