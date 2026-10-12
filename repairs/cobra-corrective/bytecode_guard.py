"""Compare protected decoded instructions with exact resolved D8 helper bodies.

Baksmali sequential labels remove address-only label changes. Only const-string
encoding width and provably unreachable payload alignment padding are normalized.
No register, string value, branch target, exception range, or instruction is ignored.
"""
import difflib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ALLOWED = re.compile(r'com/projectinfinity/kodi/(?:InfinityLiveActivity|CobraProUi|BuildConfig)(?:\$[^/]*)?\.smali$')
METHOD = re.compile(r'^\.method[^\n]*\n.*?^\.end method\s*$', re.M | re.S)
PAYLOAD = re.compile(r'^:(?:pswitch|sswitch|array)_data_\d+$')
TERMINAL = re.compile(r'^(?:return(?:-void|-object|-wide)?(?:\s|$)|throw\s|goto(?:/16|/32)?\s)')


def normalize(text):
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == 'nop':
            before = i - 1
            while before >= 0 and (not lines[before].strip() or lines[before].lstrip().startswith('#')):
                before -= 1
            after = i + 1
            while after < len(lines) and (not lines[after].strip() or lines[after].lstrip().startswith('#')):
                after += 1
            payload = after + 1
            while payload < len(lines) and not lines[payload].strip():
                payload += 1
            if before >= 0 and TERMINAL.match(lines[before].strip()) and after < len(lines) and PAYLOAD.fullmatch(lines[after].strip()) and payload < len(lines) and lines[payload].strip().startswith(('.packed-switch', '.sparse-switch', '.array-data')):
                # No label or debug directive may precede this nop: it cannot be
                # targeted and the immediately previous instruction cannot fall through.
                continue
        line = re.sub(r'^(\s*)const-string/jumbo(?=\s)', r'\1const-string', line)
        if line.strip():
            result.append(line)
    return '\n'.join(result)


def compare(base, candidate, classpath, out):
    spec = importlib.util.spec_from_file_location('approved_bridge_guard', HERE.parent / 'chooser-close-owner-2103324/bridge_preservation.py')
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    reports = []
    with tempfile.TemporaryDirectory(prefix='cobra-corrective-dex-') as directory:
        maps = []
        for label, apk in (('base', base), ('candidate', candidate)):
            root = Path(directory) / label
            root.mkdir()
            with zipfile.ZipFile(apk) as archive:
                for name in archive.namelist():
                    if re.fullmatch(r'classes\d*\.dex', name):
                        dex = root / name
                        dex.write_bytes(archive.read(name))
                        subprocess.run(['java', '-cp', classpath, 'org.jf.baksmali.Main', 'disassemble', '--sequential-labels', str(dex), '-o', str(root / 'smali')], check=True)
            raw = {p.relative_to(root / 'smali').as_posix(): p.read_text() for p in (root / 'smali').rglob('*.smali')}
            normalized = {name: normalize(text) + '\n' for name, text in raw.items()}
            resolved, bodies, helpers = bridge.resolve(normalized)
            maps.append((raw, resolved))
            reports.append({'side': label, 'classes': len(raw), 'exact_helper_bodies': sorted(bodies), 'helper_containers': sorted(helpers)})
        (oldraw, old), (newraw, new) = maps
        protected = sorted(n for n in old.keys() | new.keys() if not ALLOWED.fullmatch(n))
        changed = [n for n in protected if old.get(n) != new.get(n)]
        diagnostics = out / 'compiler-differences'
        diagnostics.mkdir(exist_ok=True)
        for name in changed:
            (diagnostics / (name.replace('/', '_') + '.diff')).write_text(''.join(difflib.unified_diff(old.get(name, '').splitlines(True), new.get(name, '').splitlines(True), fromfile='approved/' + name, tofile='candidate/' + name)))
        report = {'protected_classes_checked': len(protected), 'unexpected_differences': changed,
                  'encoding_only_differences': [n for n in protected if oldraw.get(n) != newraw.get(n) and old.get(n) == new.get(n)],
                  'allowed_class_families': ALLOWED.pattern, 'helper_proofs': reports,
                  'decoded_protected_instructions_identical': not changed,
                  'method': 'Sequential labels, exact const-string value and register operands, unreachable payload-padding check; exact recursive synthetic helper body resolution.'}
        (out / 'DEX-PRESERVATION.json').write_text(json.dumps(report, indent=2) + '\n')
        if changed:
            raise RuntimeError('Protected bytecode changed: ' + repr(changed))
        return report
