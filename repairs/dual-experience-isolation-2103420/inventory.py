"""Inventory shipped code without loading it or running application tests.

DEX fingerprints use pinned baksmali with resolved symbolic references. They do
not depend on global DEX indices. Reachability is conservative evidence, not a
claim that reflection, JNI, dynamic paths or shared mutable state are isolated.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'repairs/infinity-final-closure-2103407/p0'))
from manifest import chunks, string_pool, NONE
import struct

APK_SHA = 'ae641e74bbe0b3360d103254d9bc5425fe1558f625466a99f1da9f16414fef26'
CERT_SHA = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
BASE_SOURCE = 'ddc054583c5e5f3cd04c328e131cb76af8d4728b'
PACKAGE = 'com.projectinfinity.kodi'
OWNERS = ('INFINITY', 'COBRA', 'CHOOSER_SHELL', 'MINIMAL_ANDROID_CONTRACT', 'UNRESOLVED')
SIGNATURE = {'META-INF/INFINITY.SF', 'META-INF/INFINITY.RSA', 'META-INF/MANIFEST.MF'}
APP = 'Lcom/projectinfinity/kodi/'
REFERENCE = re.compile(r'L[^\s"<>:(),{}]+;')
MEMBER = re.compile(r'(L[^\s,{}]+;)->([^\s,{}]+)')
STORAGE = re.compile(r'getSharedPreferences|InfinityJavaPersistence|InfinityJavaWriteBarrier|Ljava/io/File;|SharedPreferences\$Editor;|SQLite|AtomicFile;|openFileOutput|ContentResolver;')


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical(value)
    if path.suffix == '.gz':
        with path.open('wb') as f, gzip.GzipFile(filename='', mode='wb', fileobj=f, mtime=0) as z:
            z.write(raw)
    else:
        path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def load(path):
    path = Path(path)
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())


def validate_names(archive):
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise ValueError('Duplicate ZIP member')
    for name in names:
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name or '\x00' in name:
            raise ValueError('Unsafe ZIP member: ' + name)
    return names


def apk_members(apk):
    with ZipFile(apk) as archive:
        validate_names(archive)
        result = {}
        for info in archive.infolist():
            with archive.open(info) as stream:
                value = hashlib.file_digest(stream, 'sha256').hexdigest()
            result[info.filename] = {'sha256': value, 'size': info.file_size}
        return result


def manifest_tree(raw):
    parts = list(chunks(raw))
    strings = string_pool(next(p for _, k, p in parts if k == 1))
    stack, roots = [], []
    for _, kind, part in parts:
        if kind == 0x102:
            name = strings[struct.unpack_from('<I', part, 20)[0]]
            first, step, count = struct.unpack_from('<3H', part, 24)
            attributes = {}
            for i in range(count):
                at = 16 + first + i * step
                ns, key, _ = struct.unpack_from('<3I', part, at)
                typ, value = part[at + 15], struct.unpack_from('<I', part, at + 16)[0]
                key = (strings[ns] + ':' if ns != NONE else '') + strings[key]
                if key in attributes:
                    raise ValueError('Duplicate manifest attribute')
                attributes[key] = {'type': typ, 'value': strings[value] if typ == 3 else value}
            node = {'tag': name, 'attributes': attributes, 'children': []}
            (stack[-1]['children'] if stack else roots).append(node)
            stack.append(node)
        elif kind == 0x103:
            if not stack or stack.pop()['tag'] != strings[struct.unpack_from('<I', part, 20)[0]]:
                raise ValueError('Unbalanced manifest')
    if stack or len(roots) != 1 or roots[0]['tag'] != 'manifest':
        raise ValueError('Invalid manifest tree')
    return roots[0]


def disassemble(apk, jars, out):
    pins = load(ROOT / 'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
    if {p.name: file_sha(p) for p in Path(jars).glob('*.jar')} != pins:
        raise ValueError('Pinned DEX tools required')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    with ZipFile(apk) as archive:
        validate_names(archive)
        for name in archive.namelist():
            if re.fullmatch(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex', name):
                target = out / name
                target.write_bytes(archive.read(name))
                subprocess.run(['java', '-cp', str(Path(jars).resolve() / '*'),
                                'org.jf.baksmali.Main', 'disassemble', '--sequential-labels',
                                str(target), '-o', str(out / (target.stem + '-smali'))], check=True)


def parse_dex(smali):
    classes, calls, storage = {}, [], []
    for path in sorted(Path(smali).glob('*-smali/**/*.smali')):
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        descriptor = text.splitlines()[0].split()[-1]
        if not descriptor.startswith('L') or not descriptor.endswith(';') or descriptor in classes:
            raise ValueError('Invalid or duplicate DEX class: ' + descriptor)
        methods, fields = {}, []
        for match in re.finditer(r'^\.method ([^\n]+)\n.*?^\.end method\s*$', text, re.M | re.S):
            body = match[0]
            signature = match[1].split()[-1]
            if signature in methods:
                raise ValueError('Duplicate DEX method')
            methods[signature] = {'sha256': digest(body.encode()), 'declaration': match[1]}
            for line in body.splitlines():
                instruction = line.strip()
                if instruction.startswith(('invoke-', 'iget', 'iput', 'sget', 'sput')):
                    ref = MEMBER.search(instruction)
                    if ref:
                        calls.append({'from': descriptor, 'method': signature, 'opcode': instruction.split()[0],
                                      'to': ref[1], 'member': ref[2]})
            if STORAGE.search(body):
                storage.append({'class': descriptor, 'method': signature, 'sha256': methods[signature]['sha256'],
                                'literals': re.findall(r'^\s*const-string(?:/jumbo)? [^,]+, (".*")$', body, re.M),
                                'status': 'STATIC_CANDIDATES_NOT_PROVEN_PATH_OR_KEY_OWNERSHIP'})
        if len(methods) != text.count('\n.method '):
            raise ValueError('Incomplete method parsing: ' + descriptor)
        for line in text.splitlines():
            if line.startswith('.field '):
                fields.append(line)
        classes[descriptor] = {'dex': path.relative_to(smali).parts[0].replace('-smali', '.dex'),
                               'sha256': digest(raw), 'methods': methods, 'fields': fields,
                               'references': sorted(set(REFERENCE.findall(text)) - {descriptor})}
    if not classes:
        raise ValueError('No DEX definitions')
    return classes, calls, storage


def classify(classes, policy):
    seeds = {APP + name + ';': owner for owner, names in policy['entry_roots'].items() for name in names}
    blocked = set(policy['unresolved_families'])

    def boundary(name):
        family = name.removeprefix(APP).split('$')[0].removesuffix(';')
        if name.startswith(APP) and family in blocked:
            return 'UNRESOLVED'
        return seeds.get(name)

    reachable = defaultdict(set)
    for seed, owner in seeds.items():
        if seed not in classes:
            raise ValueError('Entry root absent: ' + seed)
        pending, seen = [seed], set()
        while pending:
            name = pending.pop()
            if name in seen or name not in classes:
                continue
            seen.add(name)
            other = boundary(name)
            if other and other != owner:
                continue
            reachable[name].add(owner)
            pending.extend(classes[name]['references'])
    for name, item in classes.items():
        candidates = sorted(reachable[name])
        owner = boundary(name) or (candidates[0] if len(candidates) == 1 else 'UNRESOLVED')
        item.update(owner=owner, reachable_from=candidates,
                    ownership_basis='EXPLICIT_ENTRY_OR_CONSERVATIVE_REFERENCE_GRAPH',
                    isolation_review='UNRESOLVED' if owner == 'UNRESOLVED' else 'STATIC_ONLY')


def verify_components(apk, components, receipt):
    expected = receipt['component_sha256']
    paths = {p.name: p for p in Path(components).glob('*.zip')}
    if set(paths) != set(expected) or len(paths) != 6:
        raise ValueError('Exact six baseline components required')
    with ZipFile(apk) as archive:
        for name, path in paths.items():
            if file_sha(path) != expected[name]:
                raise ValueError('Component archive digest mismatch: ' + name)
            with ZipFile(path) as component:
                for member in validate_names(component):
                    if not member.endswith('/') and component.read(member) != archive.read('assets/addons/' + member):
                        raise ValueError('Component/APK mismatch: ' + member)
    return expected


def build(apk, smali, components, receipt, out):
    apk, out = Path(apk), Path(out)
    if file_sha(apk) != APK_SHA:
        raise ValueError('Exact signed2103420 required')
    receipt = load(receipt)
    if (receipt['candidate_APK_sha256'] != APK_SHA or receipt['source_commit'] != BASE_SOURCE
            or receipt['original_certificate_sha256'] != CERT_SHA or str(receipt['build']) != '40413893227'):
        raise ValueError('Baseline source/artifact binding mismatch')
    members = apk_members(apk)
    # Bind disassembly input to actual APK, never trust a supplied report alone.
    dex_names = {n for n in members if re.fullmatch(r'classes[0-9]*\.dex', n)}
    if {p.name for p in Path(smali).glob('*.dex')} != dex_names:
        raise ValueError('DEX set mismatch')
    for name in dex_names:
        if file_sha(Path(smali) / name) != members[name]['sha256']:
            raise ValueError('DEX input mismatch')
    classes, calls, storage = parse_dex(smali)
    policy = load(HERE / 'ownership-policy.json')
    classify(classes, policy)
    with ZipFile(apk) as archive:
        manifest = manifest_tree(archive.read('AndroidManifest.xml'))
    components = verify_components(apk, components, receipt)
    for name, item in members.items():
        # Native and asset reachability is not proved by file names. Freeze the
        # actual bytes and mark unresolved instead of assigning invented owners.
        owner = 'UNRESOLVED'
        basis = 'OPAQUE_MEMBER_FROZEN_PENDING_CALL_AND_STATE_REVIEW'
        if name in SIGNATURE or name in ('AndroidManifest.xml', 'resources.arsc') or name.startswith('res/'):
            owner, basis = 'MINIMAL_ANDROID_CONTRACT', 'FROZEN_SHARED_CONTAINER_NOT_FEATURE_STATE'
        elif name.startswith('assets/addons/'):
            owner, basis = 'INFINITY', 'KODI_ADDON_RUNTIME_ASSET_PRESERVED_NO_MIGRATION'
        item.update(owner=owner, basis=basis)
    cross = []
    for edge in calls:
        if edge['to'] in classes:
            a, b = classes[edge['from']]['owner'], classes[edge['to']]['owner']
            if a != b or a == 'UNRESOLVED':
                cross.append(dict(edge, from_owner=a, to_owner=b, review='UNRESOLVED'))
    out.mkdir(parents=True, exist_ok=True)
    shards = {'DEX-MEMBERS.json.gz': classes, 'DEX-CALLS.json.gz': calls,
              'CROSS-OWNER-EDGES.json.gz': cross, 'PERSISTENCE-CANDIDATES.json.gz': storage,
              'MANIFEST.json': manifest}
    for name, value in shards.items():
        save(out / name, value)
    report = {'schema': 1, 'status': 'BLOCKED_BY_SHARED_PERSISTENCE_AND_BACKGROUND_LIFECYCLE',
              'provenance': {'apk_sha256': APK_SHA, 'source_commit': BASE_SOURCE, 'build_run': 40413893227,
                             'artifact_id': 12695160919, 'certificate_sha256': CERT_SHA},
              'members': members, 'component_zips': components,
              'shards': {n: file_sha(out / n) for n in shards},
              'counts': {'apk_members': len(members), 'dex_classes': len(classes),
                         'dex_methods': sum(len(c['methods']) for c in classes.values()),
                         'dex_call_and_field_edges': len(calls), 'cross_or_unresolved_edges': len(cross),
                         'class_owners': dict(Counter(c['owner'] for c in classes.values()))},
              'limitations': ['Static reference graph is not dynamic call resolution or dataflow proof',
                              'Native function/JNI and Python dynamic call ownership remains unresolved',
                              'Persistence candidates are method literals, not proven file/key partitions',
                              'No runtime, shutdown, install-over or physical device tests run'],
              'release_blockers': policy['release_blockers']}
    save(out / 'OWNERSHIP-MAP.json', report)
    return report['counts']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', required=True, type=Path)
    parser.add_argument('--jars', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--components', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    disassemble(args.apk, args.jars, args.work)
    print(json.dumps(build(args.apk, args.work, args.components, args.receipt, args.out), indent=2))
