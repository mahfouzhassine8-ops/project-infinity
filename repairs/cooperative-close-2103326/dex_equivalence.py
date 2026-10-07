"""Prove InfinityCobraRecordingService D8 lambda-number churn is behavior-identical."""
import hashlib
import re
import shutil
import subprocess
import zipfile
from collections import Counter

MAIN = 'com/projectinfinity/kodi/InfinityCobraRecordingService.smali'
LAMBDA = re.compile(r'^com/projectinfinity/kodi/InfinityCobraRecordingService\$\$ExternalSyntheticLambda\d+\.smali$')
REF = re.compile(r'L(com/projectinfinity/kodi/InfinityCobraRecordingService\$\$ExternalSyntheticLambda\d+);')


def verify(base, final, build, out, dex_pattern, require):
    classpath = (build / 'preservation-classpath.txt').read_text()
    roots = {}
    for label, apk in [('base', base), ('final', final)]:
        dexroot = out / ('recording-dex-' + label)
        smali = out / ('recording-smali-' + label)
        for target in (dexroot, smali):
            if target.exists():
                shutil.rmtree(target)
        dexroot.mkdir()
        with zipfile.ZipFile(apk) as archive:
            for name in archive.namelist():
                if dex_pattern.fullmatch(name):
                    target = dexroot / name
                    target.write_bytes(archive.read(name))
                    subprocess.run(
                        ['java', '-cp', classpath, 'org.jf.baksmali.Main',
                         'disassemble', str(target), '-o', str(smali)],
                        check=True)
        roots[label] = smali

    def relevant(root):
        folder = root / 'com/projectinfinity/kodi'
        return {p.relative_to(root).as_posix(): p.read_text()
                for p in folder.glob('InfinityCobraRecordingService*.smali')}

    def semantic_lambda(text):
        normalized = REF.sub(
            'Lcom/projectinfinity/kodi/InfinityCobraRecordingService$$ExternalSyntheticLambda#;',
            text)
        return hashlib.sha256(normalized.encode()).hexdigest()

    old, new = relevant(roots['base']), relevant(roots['final'])
    require(MAIN in old and MAIN in new, 'Cobra recording service missing')
    old_map = {name: semantic_lambda(text) for name, text in old.items() if LAMBDA.fullmatch(name)}
    new_map = {name: semantic_lambda(text) for name, text in new.items() if LAMBDA.fullmatch(name)}
    require(Counter(old_map.values()) == Counter(new_map.values()),
            'Cobra recording lambda bodies changed, not merely renumbered')

    def canonical_main(text, mapping):
        def repl(match):
            key = match.group(1) + '.smali'
            require(key in mapping, 'Unresolved Cobra recording lambda reference: ' + key)
            return ('Lcom/projectinfinity/kodi/InfinityCobraRecordingService$$SyntheticBody_'
                    + mapping[key] + ';')
        return REF.sub(repl, text)

    require(canonical_main(old[MAIN], old_map) == canonical_main(new[MAIN], new_map),
            'Cobra recording instructions changed beyond lambda renumbering')
    nested = (set(old) | set(new)) - {MAIN} - set(old_map) - set(new_map)
    changed_nested = sorted(name for name in nested if old.get(name) != new.get(name))
    require(not changed_nested, 'Cobra recording nested behavior changed: ' + repr(changed_nested))

    report = {
        'compiler_only_lambda_renumbering': True,
        'lambda_body_multiset_identical': True,
        'main_call_sites_identical_after_semantic_mapping': True,
        'other_nested_classes_identical': True,
        'lambda_bodies': len(old_map),
    }
    import json
    (out / 'COBRA-RECORDING-DEX-PRESERVATION.json').write_text(json.dumps(report, indent=2) + '\n')
    for root in [out / 'recording-dex-base', out / 'recording-dex-final',
                 out / 'recording-smali-base', out / 'recording-smali-final']:
        if root.exists():
            shutil.rmtree(root)
    return report
