"""Compare closeout owner DEX directly with protected signed432, without APK production."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile

APK_SHA = '55671707e7acc8b1c329e5b87bdbe47706607418aa152b11b8889c3081a447c3'
DEX = {'classes4.dex': '47c9635ce03485013d19200db15ee7a703d5e4368197f35f084d0cc9a8afcde6',
       'classes5.dex': '3360d86366c77771c21af868db10dabe95503fd876977c5ecf201a32af2c384e'}
APP = 'Lcom/projectinfinity/kodi/'
CHANGED = {APP + name + ';' for name in ('CobraCardsLayout', 'CobraCardsLayout$State',
    'CobraCardsLayout$PreviewBadge', 'CobraCardsTiles', 'CobraCardsTiles$Holder',
    'InfinityLiveActivity$CobraPosterChannelCard')}
METHOD = re.compile(r'^\.method ([^\n]+)\n.*?^\.end method', re.M | re.S)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def classes(folder):
    result = {}
    for path in folder.rglob('*.smali'):
        raw = path.read_text(); name = raw.splitlines()[0].split()[-1]
        assert name not in result
        result[name] = raw
    return result


def methods(raw):
    return {m[1]: m[0] + '\n' for m in METHOD.finditer(raw)}


def resolved_preview(preview, layout):
    # Javac may renumber synthetic accessors when a field is introduced.
    # Resolve each accessor to its exact body; reject any real preview change.
    mapping = {}
    for signature, raw in methods(layout).items():
        if ' synthetic access$' in signature:
            body = raw.split('\n', 1)[1]
            mapping[signature.split()[-1]] = hashlib.sha256(body.encode()).hexdigest()
    pattern = re.compile(r'(Lcom/projectinfinity/kodi/CobraCardsLayout;->)(access\$\d+\([^\n ]+\)[^\n ]+)')
    return pattern.sub(lambda match: match[1] + 'resolved:' + mapping[match[2]], preview)


def verify(apk, prototype, jars, out):
    assert not out.exists(), 'Preserve previous proof; require fresh output'
    assert sha(apk) == APK_SHA, 'Exact protected signed432 bytes required'
    pins = json.loads((Path(__file__).resolve().parents[4] /
        'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
    assert {p.name: sha(p) for p in jars.glob('*.jar')} == pins
    out.mkdir(parents=True)
    with ZipFile(apk) as archive:
        for leaf, pin in DEX.items():
            raw = archive.read(leaf)
            assert hashlib.sha256(raw).hexdigest() == pin
            dex = out / leaf; dex.write_bytes(raw)
            subprocess.run(['java', '-cp', str(jars / '*'), 'org.jf.baksmali.Main',
                'disassemble', '--sequential-labels', str(dex), '-o', str(out / 'signed432' / dex.stem)], check=True)
    old, new = classes(out / 'signed432'), classes(prototype / 'independent-canonical')
    assert set(old) == set(new) and len(old) == 7165
    changed = {name for name in old if old[name] != new[name]}
    assert changed == CHANGED, sorted(changed)
    card = APP + 'InfinityLiveActivity$CobraPosterChannelCard;'
    before, after = methods(old[card]), methods(new[card])
    assert set(before) == set(after)
    delta = sorted(key for key in before if before[key] != after[key])
    assert delta == ['bind(Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;I)V']
    assert METHOD.sub('', old[card]) == METHOD.sub('', new[card])
    preview, layout = APP + 'CobraCardsLayout$PreviewBadge;', APP + 'CobraCardsLayout;'
    assert resolved_preview(old[preview], old[layout]) == resolved_preview(new[preview], new[layout])
    proof = dict(status='PASS_EXACT_CLOSEOUT_DELTA_FROM_ACTUAL_SIGNED432',
        protected432_source='b53d4286759cee6707c8c2915cc5a0c9a3260336', protected432_APK_SHA256=APK_SHA,
        protected432_owner_DEX=DEX, prototype_existing_classes=len(old), unchanged_classes=len(old)-len(changed),
        changed_classes=sorted(changed), existing_native_method_changes={card: delta}, new_or_removed_classes=[],
        prototype_DEX={p.name: sha(p) for p in (prototype/'owner-dex/COBRA').glob('*.dex')},
        compiler_source_files=json.loads((prototype/'BUILD.json').read_text())['compiler_source_files'],
        prototype_canonical_receipt_sha256=sha(prototype/'INDEPENDENT-CANONICAL-RESULT.json'),
        PreviewBadge_change='Compiler synthetic-accessor renumbering only; resolved bodies and remaining class text exact',
        verifier_sha256=sha(Path(__file__)), APK='NOT_BUILT', signing='NOT_RUN', shutdown='NOT_RUN')
    (out/'PRESERVATION-FROM-SIGNED432.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({key: proof[key] for key in ('status','unchanged_classes','changed_classes','prototype_DEX')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('apk', 'prototype', 'jars', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    verify(**vars(parser.parse_args()))
