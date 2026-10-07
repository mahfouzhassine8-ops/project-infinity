"""Prove D8 helper relocation by exact, recursively resolved method bodies."""
import difflib
import hashlib
import json
import re
from pathlib import Path

ALLOWED = re.compile(r'com/projectinfinity/kodi/(?:InfinityKodiShutdown|Splash|BuildConfig)(?:\$[^/]*)?\.smali$')
# These are the helper containers observed in the locked APK and candidate.
OWNER = r'com/projectinfinity/kodi/(?:Main\$\$ExternalSyntheticApiModelOutline0|CobraProUi\$Hero\$\$ExternalSyntheticApiModelOutline[01]|InfinityExitDiagnostics\$\$ExternalSyntheticBackport2)'
HELPER = re.compile(OWNER + r'\.smali$')
CALL = re.compile(r'L' + OWNER + r';->m(?:\$\d+)?\([^\s]+')
METHOD = re.compile(r'^\.method (public static(?: bridge)? synthetic) (m(?:\$\d+)?\([^\n ]+)\n(.*?)^\.end method\n', re.M | re.S)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def resolve(classes):
    methods = {}
    helpers = set()
    for name, text in classes.items():
        if not HELPER.fullmatch(name):
            continue
        helpers.add(name)
        owner = name[:-6]
        header = '\n'.join(line for line in METHOD.sub('', text).splitlines() if line.strip())
        expected = ('.class public final synthetic L' + owner + ';\n'
                    '.super Ljava/lang/Object;\n.source "D8$$SyntheticClass"\n# direct methods')
        require(header == expected, 'Unexpected helper state, metadata or methods: ' + name)
        found = list(METHOD.finditer(text))
        require(bool(found), 'Empty helper: ' + name)
        for m in found:
            signature = m[2]
            key = 'L' + owner + ';->' + signature
            require(key not in methods, 'Duplicate helper method: ' + key)
            methods[key] = m[1] + ' ' + signature[signature.index('('):] + '\n' + m[3]
    digests = {}
    active = set()
    def digest(key):
        require(key in methods, 'Unresolved synthetic call: ' + key)
        if key in digests:
            return digests[key]
        require(key not in active, 'Unexpected helper recursion: ' + key)
        active.add(key)
        body = CALL.sub(lambda m: 'EXACT_HELPER_BODY_' + digest(m[0]), methods[key])
        active.remove(key)
        digests[key] = hashlib.sha256(body.encode()).hexdigest()
        return digests[key]
    for key in methods:
        digest(key)
    checked = {name: CALL.sub(lambda m: 'EXACT_HELPER_BODY_' + digest(m[0]), text)
               for name, text in classes.items() if name not in helpers}
    return checked, set(digests.values()), helpers


def verify(old, new, out):
    left, before, old_helpers = resolve(old)
    right, after, new_helpers = resolve(new)
    protected = sorted(n for n in left.keys() | right.keys() if not ALLOWED.fullmatch(n))
    changed = [n for n in protected if left.get(n) != right.get(n)]
    details = Path(out) / 'compiler-diffs'
    details.mkdir(exist_ok=True)
    for name in changed:
        (details / (Path(name).name + '.diff')).write_text(''.join(difflib.unified_diff(
            left.get(name, '').splitlines(True), right.get(name, '').splitlines(True),
            fromfile='base/' + name, tofile='candidate/' + name)))
    report = {
        'exact_api_bodies_before': len(before), 'exact_api_bodies_after': len(after),
        'protected_classes_checked': len(protected), 'protected_class_differences': changed,
        'helper_containers_before': sorted(old_helpers), 'helper_containers_after': sorted(new_helpers),
        'added_bodies': sorted(after - before), 'removed_bodies': sorted(before - after),
        'method': 'Resolve observed stateless D8 helper calls recursively to hashes of exact flags, signatures, registers and instructions; require every protected class and call site to remain identical.'}
    (Path(out) / 'API-BRIDGE-PRESERVATION.json').write_text(json.dumps(report, indent=2) + '\n')
    require(not changed, 'Protected instructions or referenced helper bodies changed: ' + repr(changed))
    return left, right, report

