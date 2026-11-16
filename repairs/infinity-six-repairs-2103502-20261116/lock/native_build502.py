#!/usr/bin/env python3
"""Build the exact signed502 native source plus the explicitly reviewed lock delta.

The immutable c3 producer reconstructs provenance in a separate worktree. Its
historical ELF comparisons are retained there only; the sole candidate ABI
baseline is the exact ELF shipped in 502. No APK/signing/runtime entry exists.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import mmap
import os
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
ROOT = TASK.parents[1]
OUT = ROOT / 'native502-lock-output'
HISTORY = ROOT / 'native502-lock-provenance'
TOOLS = HISTORY / 'native500-frozen-tools'
NATIVE = TOOLS / 'kodi'
BASELINE = ROOT / 'baseline502-native'
HISTORICAL_BASELINE = ROOT / 'baseline500-native'
FROZEN = 'c3c1e920e17fbeee5b9977eadc9409a9806a06f9'
RECONSTRUCTION = '9ce852ebb044a82853ef93af24e34a07ed96daff'
PRODUCER_PATH = 'repairs/infinity-consolidated-2103500-20261115'
BRANCH = 'work/infinity-2103502-six-repairs-20261116'
REPOSITORY = 'mahfouzhassine8-ops/project-infinity'
ENGINE = 'ed2d955d1825bf838ea50a712782e54b69926d40605270a2f241efd913202ee7'
MAP = '4ef7607c83dc97291c088de701cfec2456e4cd53f256599151fd3d1b43ba507a'
APK = 'f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28'
WORKFLOW = '.github/workflows/infinity-502-lock-integration.yml'
REQUEST = HERE / 'CI-NATIVE.json'
SCOPE = HERE / 'NATIVE-BUILD-SCOPE.json'
SELECTION = HERE / 'NATIVE-TEST-SELECTION.json'
REVIEW = HERE / 'ASTRA-NATIVE-BUILD-REVIEW.json'
SELECTED_TEST = 'lock_and_observer_lifetime_full_arm64_compile_link_exact502_abi'
EXISTING = {
    'xbmc/application/Application.cpp',
    'xbmc/interfaces/builtins/AndroidBuiltins.cpp',
    'xbmc/platform/android/activity/CMakeLists.txt',
    'xbmc/platform/android/activity/JNIMainActivity.cpp',
    'xbmc/platform/android/activity/JNIMainActivity.h',
    'xbmc/platform/android/activity/XBMCApp.h',
}
NEW = {
    'xbmc/platform/android/activity/InfinityVideoLock.cpp',
    'xbmc/platform/android/activity/InfinityVideoLock.h',
    'xbmc/platform/android/activity/InfinityVideoLockGate.h',
    'xbmc/platform/android/activity/InfinityActivityObserver.h',
}
CRASH_NATIVE = {
    'xbmc/platform/android/activity/JNIMainActivity.cpp',
    'xbmc/platform/android/activity/JNIMainActivity.h',
    'xbmc/platform/android/activity/XBMCApp.h',
    'xbmc/platform/android/activity/InfinityActivityObserver.h',
}


def native_path(name):
    require(name in EXISTING | NEW, 'Unknown native overlay')
    return (TASK / 'crashes' if name in CRASH_NATIVE else HERE) / 'native' / name


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def blob(ref, name):
    return subprocess.check_output(['git', 'show', ref + ':' + name], cwd=ROOT)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def relative(path):
    return path.relative_to(ROOT).as_posix()


def source_hashes():
    paths = [native_path(name) for name in sorted(EXISTING | NEW)]
    paths += [Path(__file__).resolve(), ROOT / WORKFLOW, SCOPE, SELECTION]
    paths += [TASK / 'crashes' / name for name in
              ('OBSERVER-SCOPE.json', 'OBSERVER-SOURCE.json', 'ASTRA-OBSERVER-REVIEW.json',
               'OBSERVER-HOST-ATTEMPT1.json', 'OBSERVER-RETIREMENT-RACE.json')]
    for path in paths:
        require(path.is_file() and not path.is_symlink(), 'Missing or linked reviewed input: ' + relative(path))
    return {relative(path): sha(path) for path in paths}


def gate():
    """Current task authority replaces historical branch labels, never content pins."""
    require(not sys.flags.optimize and not os.environ.get('PYTHONOPTIMIZE'), 'Retained assertions must remain enabled')
    require(os.environ.get('GITHUB_ACTIONS') == 'true', 'GitHub Actions only')
    require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'Wrong repository')
    require(os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'Wrong branch')
    require(os.environ.get('GITHUB_EVENT_NAME') in ('push', 'workflow_dispatch'), 'Explicit request event required')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    require(head == os.environ.get('GITHUB_SHA'), 'Checkout does not match requested CI commit')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', relative(HERE),
                    relative(TASK / 'crashes'), WORKFLOW], cwd=ROOT, check=True)
    request = json.loads(REQUEST.read_bytes())
    require(request.get('schema') == 1 and request.get('operation') == 'exact502-lock-observer-full-arm64-compile-link', 'Wrong native operation')
    require(request.get('branch') == BRANCH and request.get('root_approved') is True, 'Explicit root-approved branch request required')
    require(request.get('baseline_version_code') == 2103502 and request.get('baseline_apk_sha256') == APK, 'Wrong application baseline')
    require(request.get('baseline_native_sha256') == ENGINE and request.get('baseline_source_map_sha256') == MAP, 'Wrong native baseline')
    require(request.get('selected_test') == SELECTED_TEST, 'Unselected native check')
    for flag in ('APK', 'signing', 'installation', 'application_execution', 'shutdown_testing'):
        require(request.get(flag) is False, 'Native request must exclude ' + flag)
    selected = json.loads(SELECTION.read_bytes())
    require('Full ARM64 compile/link and exact502 exportedABI preservation' in selected.get('selected_before_execution', []), 'Selected test document changed')
    pins = source_hashes()
    require(request.get('reviewed_files') == pins, 'Request source/build/selection hashes differ')
    native = {name: pins[relative(native_path(name))] for name in sorted(EXISTING | NEW)}
    require(request.get('native_sources') == native, 'Request must bind exactly ten native overlays')
    observed = {p.relative_to(HERE / 'native').as_posix() for p in (HERE / 'native').rglob('*') if p.is_file()}
    crash_files = {p.relative_to(TASK / 'crashes/native').as_posix()
                   for p in (TASK / 'crashes/native').rglob('*') if p.is_file()}
    require(observed == (EXISTING | NEW) - CRASH_NATIVE and crash_files == CRASH_NATIVE,
            'Unreviewed or overlapping native overlay file')
    host = json.loads((TASK / 'crashes/OBSERVER-HOST-ATTEMPT1.json').read_bytes())
    require(host['status'] == 'PASS_CORRECTED_SOURCE_HOST' and host['outside_reviewed_delta'] == 'BYTE_IDENTICAL',
            'Corrected observer source host/preservation gate missing')
    require({name: row['after'] for name, row in host['source'].items()} ==
            {name: native[name] for name in CRASH_NATIVE}, 'Observer host receipt differs from requested source')
    race = json.loads((TASK / 'crashes/OBSERVER-RETIREMENT-RACE.json').read_bytes())
    require(race['status'] == 'PASS' and race['header_sha256'] ==
            native['xbmc/platform/android/activity/InfinityActivityObserver.h'],
            'Observer retirement race receipt differs from requested source')
    require(request.get('astra_review_sha256') == sha(REVIEW), 'Independent review hash differs')
    review = json.loads(REVIEW.read_bytes())
    require(review.get('reviewer') == 'Astra' and review.get('status') == 'PASS_SOURCE_REVIEW', 'Independent source review required')
    require(review.get('files') == pins, 'Independent review must bind the complete native build inputs')
    reviewed_commit = request.get('reviewed_source_commit', '')
    require(re.fullmatch('[0-9a-f]{40}', reviewed_commit) is not None, 'Reviewed source commit required')
    subprocess.run(['git', 'merge-base', '--is-ancestor', reviewed_commit, head], cwd=ROOT, check=True)
    changes = set(subprocess.check_output(['git', 'diff', '--name-only', reviewed_commit, head], cwd=ROOT, text=True).splitlines())
    require(changes <= {relative(REQUEST)}, 'Only the explicit request may follow the reviewed source commit')
    if os.environ['GITHUB_EVENT_NAME'] == 'workflow_dispatch':
        require(os.environ.get('REQUEST_SHA256') == sha(REQUEST), 'Dispatch must name the exact checked-in request SHA-256')
    scope = json.loads(SCOPE.read_bytes())
    require(scope.get('baseline_source_count') == 9414 and scope.get('candidate_source_count') == 9418, 'Wrong source counts')
    require(scope.get('baseline_source_map_sha256') == MAP and scope.get('baseline_native_sha256') == ENGINE, 'Scope baseline differs')
    require(set(scope.get('existing_native_changes', {})) == EXISTING and set(scope.get('new_native_files', [])) == NEW, 'Scope native allowlist differs')
    base = json.loads((TASK / 'BASELINE.json').read_bytes())
    require(base.get('versionCode') == 2103502 and base.get('APK_sha256') == APK and base.get('native_sha256') == ENGINE, 'Task baseline differs')
    # Read blobs instead of sparse-worktree files; all older production tooling
    # remains byte-identical. New source authority is confined to this task.
    for name in ('build_native.py', 'verify_scope.py', 'prepare_ci_tooling.sh'):
        path = PRODUCER_PATH + '/' + name
        require(blob('HEAD', path) == blob(FROZEN, path), 'Historical preservation tool changed: ' + path)
    return request, scope


def authenticate_inputs():
    request, scope = gate()
    rows = []
    for expected in scope['input_artifacts']:
        actual = json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPOSITORY + '/actions/artifacts/' + str(expected['id'])], text=True))
        require(actual.get('expired') is False, 'Required retained artifact expired')
        for key in ('id', 'name', 'size_in_bytes', 'digest'):
            require(actual.get(key) == expected[key], 'Retained artifact metadata differs: ' + str(expected['id']) + ':' + key)
        require(actual['workflow_run']['id'] == expected['run_id'] and actual['workflow_run']['head_sha'] == expected['source_commit'], 'Retained artifact producer differs')
        rows.append(expected)
    save('INPUT-AUTHENTICATION.json', dict(status='AUTHENTICATED_METADATA_ONLY', request_sha256=sha(REQUEST), artifacts=rows, application_execution='NOT_RUN'))


def baseline_inputs():
    require(sha(BASELINE / 'libkodi.so') == ENGINE, 'Exact502 native ELF missing or mismatched')
    require(sha(BASELINE / 'NATIVE-SOURCE-MAP.json') == MAP, 'Exact502 native source map missing or mismatched')
    require(sha(BASELINE / 'ARM64.json') == 'c447b9832eb251b3cd724db6964a18125be3762ee9adc75d2fdb6b49150ccb2d', 'Exact502 producer receipt differs')
    proof = json.loads((BASELINE / 'ARM64.json').read_bytes())
    require(proof.get('native_sha256') == ENGINE and proof.get('source') == FROZEN, 'Exact502 native producer differs')
    expected = json.loads((BASELINE / 'NATIVE-SOURCE-MAP.json').read_bytes())
    require(len(expected) == 9414, 'Exact502 map must contain all 9414 source files')
    return expected


def provenance_gate():
    gate()
    baseline_inputs()
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=HISTORY, text=True).strip() == FROZEN, 'Wrong historical producer worktree')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD'], cwd=HISTORY, check=True)
    # Retain the frozen producer's content/scope checks and comparison inputs.
    # Only its obsolete task-specific branch authority is replaced by gate().
    load(HISTORY / PRODUCER_PATH / 'verify_scope.py', 'exact502_provenance_scope').main()
    base = json.loads((HISTORY / PRODUCER_PATH / 'BASELINE.json').read_bytes())
    old_engine = '3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75'
    old_map = '26525c76540cd62fbc483b4d4ec2eb2579ef595a64f2fe564859131139498f1c'
    require(base['versionCode'] == 2103500 and base['native_engine_sha256'] == old_engine, 'Historical reconstruction baseline differs')
    require(base['source_maps']['native_map_sha256'] == old_map, 'Historical reconstruction map pin differs')
    require(sha(HISTORICAL_BASELINE / 'libkodi.so') == old_engine and sha(HISTORICAL_BASELINE / 'NATIVE-SOURCE-MAP.json') == old_map, 'Historical comparison inputs differ')
    receipt = json.loads((HISTORICAL_BASELINE / 'CAST-ARM64.json').read_bytes())
    require(receipt['native_sha256'] == old_engine and receipt['source'] == '16df356f0acffbf9ca28ab7095f3a21233998d6d', 'Historical producer differs')


def producer():
    path = HISTORY / PRODUCER_PATH / 'build_native.py'
    require(path.read_bytes() == blob(FROZEN, PRODUCER_PATH + '/build_native.py'), 'Frozen reconstruction code differs')
    module = load(path, 'exact502_frozen_source_producer')
    module.OUT = OUT / 'provenance'
    module.gate = provenance_gate
    return module


def hasher():
    path = TOOLS / 'repairs/infinity-native-touch-2103451-20261105/compile_only.py'
    require(path.read_bytes() == blob(RECONSTRUCTION, 'repairs/infinity-native-touch-2103451-20261105/compile_only.py'), 'Retained source hasher differs')
    return load(path, 'exact502_full_source_hasher')


def candidate_map():
    request, scope = gate()
    before = baseline_inputs()
    for name, pin in scope['existing_native_changes'].items():
        require(before.get(name) == pin, 'Wrong exact502 source preimage: ' + name)
    require(not NEW.intersection(before), 'New lock path already belongs to baseline502')
    expected = dict(before)
    expected.update(request['native_sources'])
    require(len(expected) == 9418, 'Candidate source count differs')
    require({name for name in before if before[name] != expected[name]} == EXISTING, 'Existing-source delta differs')
    return before, expected


def prepare():
    gate()
    baseline_inputs()
    require(not HISTORY.exists(), 'Refuse reused provenance source worktree')
    require(not Path(os.environ['BUILD_DIR']).exists(), 'Refuse reused native build directory')
    OUT.mkdir(exist_ok=True)
    (OUT / 'provenance').mkdir(exist_ok=True)
    subprocess.run(['git', 'worktree', 'add', '--detach', '--no-checkout', str(HISTORY), FROZEN], cwd=ROOT, check=True)
    subprocess.run(['git', 'sparse-checkout', 'init', '--no-cone'], cwd=HISTORY, check=True)
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', FROZEN], cwd=ROOT, text=True).splitlines()
    suffixes = {'.py', '.sh', '.json', '.java', '.in', '.h', '.hpp', '.cpp', '.c', '.txt', '.patch', '.xml', '.pem', '.sig', '.v1', '.cmake', '.yml', '.md'}
    selected = [name for name in names if Path(name).suffix in suffixes or Path(name).name == 'CMakeLists.txt']
    subprocess.run(['git', 'sparse-checkout', 'set', '--no-cone', '--stdin'], input=''.join('/' + name + '\n' for name in selected), cwd=HISTORY, text=True, check=True)
    subprocess.run(['git', 'checkout'], cwd=HISTORY, check=True)
    for name in ('verified-inputs', 'previous-review', 'exact464', 'signed80', 'baseline500-native'):
        require((ROOT / name).is_dir(), 'Retained reconstruction artifact missing: ' + name)
        (HISTORY / name).symlink_to(ROOT / name, target_is_directory=True)
    producer().prepare()
    before, after = candidate_map()
    # Mandatory boundary: not one new lock byte is applied before full equality.
    require(hasher().hashes(NATIVE) == before, 'Reconstructed source is not exact signed502 across all 9414 files')
    require(json.loads((OUT / 'provenance/NATIVE-SOURCE-MAP.json').read_bytes()) == before, 'Frozen producer map does not equal signed502')
    save('BASE502-NATIVE-SOURCE-MAP.json', before)
    changed = {}
    for name in sorted(EXISTING | NEW):
        target = NATIVE / name
        if name in EXISTING:
            require(sha(target) == before[name], 'Existing native preimage changed')
        else:
            require(not target.exists(), 'Unexpected new native target')
        candidate = native_path(name)
        require(sha(candidate) == after[name], 'Overlay changed after request gate')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(candidate.read_bytes())
        changed[name] = dict(before=before.get(name), after=after[name])
    require(hasher().hashes(NATIVE) == after, 'Only the ten requested native sources may differ')
    unchanged = sum(before[name] == after[name] for name in before)
    require(unchanged == 9408, 'Unchanged native count differs')
    save('NATIVE-SOURCE-MAP.json', after)
    save('SOURCE-PRESERVATION.json', dict(status='PASS_EXACT502_PREIMAGE_AND_TEN_REVIEWED_LOCK_OBSERVER_FILES',
        source=os.environ['GITHUB_SHA'], request_sha256=sha(REQUEST), baseline_native_sha256=ENGINE,
        baseline_source_map_sha256=MAP, exact_baseline_source_count=len(before),
        candidate_source_count=len(after), unchanged_native_files=unchanged, changed=changed,
        historical_producer=FROZEN, historical_receipts='PROVENANCE_ONLY_NOT_NEW_ACCEPTANCE',
        historical_ELFs='SEGREGATED_PROVENANCE_COMPARISONS_ONLY', final_ABI_baseline='EXACT_SIGNED502',
        Android_execution='NOT_RUN', APK=False, signing=False, physical_acceptance=False))


def with_tools(action):
    previous = os.environ.get('GITHUB_WORKSPACE')
    os.environ['GITHUB_WORKSPACE'] = str(TOOLS)
    try:
        return action()
    finally:
        if previous is None:
            os.environ.pop('GITHUB_WORKSPACE', None)
        else:
            os.environ['GITHUB_WORKSPACE'] = previous


def tooling():
    gate()
    release = Path('/etc/os-release').read_text()
    require('ID=ubuntu' in release and 'VERSION_CODENAME=jammy' in release, 'Pinned Ubuntu 22.04 runner required')
    require(Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg').is_file(), 'Ubuntu signing keyring missing')
    OUT.mkdir(exist_ok=True)
    sources = OUT / 'official-ubuntu-sources.txt'
    sources.write_text(''.join('deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] ' + url + ' ' + suite + ' main restricted universe multiverse\n' for url, suite in (
        ('https://archive.ubuntu.com/ubuntu', 'jammy'),
        ('https://archive.ubuntu.com/ubuntu', 'jammy-updates'),
        ('https://security.ubuntu.com/ubuntu', 'jammy-security'))))
    args = ['timeout', '180', 'sudo', 'apt-get', '-o', 'Dir::Etc::sourcelist=' + str(sources),
            '-o', 'Dir::Etc::sourceparts=-', '-o', 'Acquire::Retries=1',
            '-o', 'Acquire::http::Timeout=20', '-o', 'Acquire::https::Timeout=20']
    subprocess.run(args + ['-o', 'APT::Update::Error-Mode=any', 'update', '-qq'], check=True)
    subprocess.run(args + ['install', '-y', 'python3-yaml', 'python3-dev', 'libsqlite3-dev', 'libssl-dev',
                          'libffi-dev', 'autoconf', 'automake', 'libtool', 'pkg-config', 'libcurl4-openssl-dev'], check=True)


def dependencies():
    gate()
    _, expected = candidate_map()
    require(hasher().hashes(NATIVE) == expected, 'Candidate changed before dependencies')
    historical = producer()
    with_tools(historical.retained().dependencies)


def private_link_fixture():
    """Selected NDK visibility check before the full engine build; no runtime substitute."""
    scope = json.loads(SCOPE.read_bytes())
    names = scope['private_link_symbols']
    require(len(names) == 28 and len(set(names)) == 28 and
            all(re.fullmatch(r'_Z[A-Za-z0-9_]+', name) for name in names), 'Unexpected private helper list')
    cmake = (NATIVE / 'xbmc/platform/android/activity/CMakeLists.txt').read_text()
    blocks = re.findall(r'file\(WRITE "\$\{infinity_lock_exports\}" \[=\[\n(.*?)\]=\]\)', cmake, re.S)
    expected = '{\n  local:\n' + ''.join('    ' + name + ';\n' for name in names) + '};\n'
    require(blocks == [expected], 'Anonymous map differs from reviewed exact-name list')
    tools = Path(os.environ['ANDROID_HOME']) / 'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin'
    readelf = tools / 'llvm-readelf'

    def exports(path):
        result = set()
        for line in subprocess.check_output([readelf, '--dyn-syms', '--wide', path], text=True).splitlines():
            row = line.split()
            if len(row) >= 8 and row[4] in ('GLOBAL', 'WEAK') and row[5] in ('DEFAULT', 'PROTECTED') and row[6] != 'UND':
                result.add(row[7])
        return result

    require(not set(names).intersection(exports(BASELINE / 'libkodi.so')), 'Private map intersects an original502 export')
    fixture = OUT / 'private-link-fixture'
    fixture.mkdir(exist_ok=True)
    script = fixture / 'InfinityVideoLock.exports.map'
    script.write_text(expected)
    old = fixture / 'old.cpp'
    new = fixture / 'new.cpp'
    old.write_text('extern "C" __attribute__((weak)) int retained_weak(int v) { return v+1; }\n'
                   'extern "C" int baseline_entry(int v) { return retained_weak(v); }\n')
    new.write_text('extern "C" __attribute__((weak)) int selected_internal(int) __asm__("' + names[0] + '");\n'
                   'extern "C" __attribute__((weak)) int selected_internal(int v) { return v+2; }\n'
                   'extern "C" __attribute__((weak)) int unlisted_new(int v) { return v+3; }\n')
    command = [str(tools / 'clang++'), '--target=aarch64-linux-android21', '-fPIC', '-O0', '-shared',
               '-nostdlib', '-fuse-ld=lld', '-Wl,--no-undefined']
    base, expanded, selective = (fixture / (name + '.so') for name in ('base', 'expanded', 'selective'))
    subprocess.run(command + [str(old), '-o', str(base)], check=True)
    subprocess.run(command + [str(old), str(new), '-o', str(expanded)], check=True)
    subprocess.run(command + [str(old), str(new), '-Wl,--version-script=' + str(script), '-o', str(selective)], check=True)
    original, all_symbols, private = exports(base), exports(expanded), exports(selective)
    require(original == {'retained_weak', 'baseline_entry'}, 'Fixture baseline differs')
    require(all_symbols == original | {names[0], 'unlisted_new'}, 'Fixture additions differ')
    require(private == original | {'unlisted_new'}, 'Map changed an unlisted/baseline symbol or retained private helper')
    require(private != original, 'Negative ABI case must still detect the unlisted new export')
    save('PRIVATE-LINK-FIXTURE.json', dict(status='PASS_PINNED_NDK_SELECTIVE_LOCAL_VISIBILITY',
        selected_before_full_engine=True, map_sha256=sha(script), exact_names=names,
        retained_weak_preserved=True, selected_new_helper_private=True,
        unlisted_new_export_still_detectable=True, baseline502_exports_excluded=True,
        clang_version=subprocess.check_output([tools / 'clang++', '--version'], text=True).splitlines()[0],
        Android_execution='NOT_RUN', fixture_only=True))
    return script


def compile_native():
    gate()
    _, expected = candidate_map()
    require(json.loads((OUT / 'NATIVE-SOURCE-MAP.json').read_bytes()) == expected, 'Staged map differs from reviewed request')
    path = TOOLS / 'repairs/universal-persistence-2103401/build.py'
    require(path.read_bytes() == blob(RECONSTRUCTION, 'repairs/universal-persistence-2103401/build.py'), 'Retained ARM64 compiler differs')
    compiler = load(path, 'exact502_retained_arm64_compiler')
    compiler.OUT = OUT
    original = compiler.checked_sources

    def checked(root, pins, allow_generated=False):
        extras = original(root, pins, allow_generated=True)
        require(Path(root) == NATIVE and pins == expected, 'Unexpected native compile input map')
        if not allow_generated:
            require(all(name.startswith('tools/depends/') for name in extras), 'Unreviewed precompile additions')
        return extras

    # Same generated-dependency exception as the frozen c3 full-engine build;
    # every reviewed source hash remains checked before and after compilation.
    compiler.checked_sources = checked
    private_map = private_link_fixture()
    proof = with_tools(compiler.compile_engine)
    require(proof['complete_native_engine_compiled'] and proof['reviewed_file_count'] == 9418, 'Full native engine compilation not established')
    library = OUT / 'libkodi.so'
    require(sha(library) == proof['native_sha256'], 'Compiled engine proof differs')
    objects = list(Path(os.environ['BUILD_DIR']).rglob('InfinityVideoLock.cpp.o'))
    require(len(objects) == 1, 'Exact lock translation unit object missing or ambiguous')
    maps = list(Path(os.environ['BUILD_DIR']).rglob('InfinityVideoLock.exports.map'))
    require(len(maps) == 1 and maps[0].read_bytes() == private_map.read_bytes(), 'Effective private linker map differs')
    links = [(path, path.read_text()) for path in Path(os.environ['BUILD_DIR']).rglob('link.txt')
             if str(maps[0]) in path.read_text()]
    flag = '-Wl,--version-script=' + str(maps[0])
    require(len(links) == 1 and links[0][1].count(flag) == 1 and 'libkodi.so' in links[0][1],
            'Private map must occur exactly once on final libkodi.so link')
    with library.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as binary:
        require(binary.find(b'com.projectinfinity.kodi.InfinityVideoLockBridge') >= 0, 'Lock bridge was not linked into the real engine')
        require(binary.find(b'Infinity activity observer publication refused') >= 0, 'Observer lifetime correction was not linked')
    readelf = Path(os.environ['ANDROID_HOME']) / 'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'

    def abi(path):
        header = subprocess.check_output([readelf, '-h', path], text=True)
        require(all(value in header for value in ('ELF64', 'AArch64', 'DYN')), 'Invalid ARM64 shared library')
        dynamic = subprocess.check_output([readelf, '-d', path], text=True)
        rows = subprocess.check_output([readelf, '--dyn-syms', '--wide', path], text=True).splitlines()
        symbols = set()
        for line in rows:
            fields = line.split()
            if len(fields) >= 8 and fields[4] in ('GLOBAL', 'WEAK') and fields[5] in ('DEFAULT', 'PROTECTED') and fields[6] != 'UND':
                symbols.add((fields[7], fields[3], fields[4], fields[5]))
        require(any(row[0] == 'InfinityCommandCenterIdentityV1' for row in symbols), 'Original trust ABI absent')
        versions = subprocess.check_output([readelf, '--version-info', path], text=True)
        definitions = tuple(re.findall(r'Rev:\s*\d+[^\n]*?Name:\s*(\S+)', versions))
        return symbols, set(re.findall(r'Shared library: \[([^\]]+)\]', dynamic)), definitions

    before, after = abi(BASELINE / 'libkodi.so'), abi(library)
    save('ABI-COMPARISON.json', dict(baseline_native_sha256=ENGINE,
        removed=sorted(before[0] - after[0]), added=sorted(after[0] - before[0]),
        dependencies_before=sorted(before[1]), dependencies_after=sorted(after[1]),
        version_definitions_before=before[2], version_definitions_after=after[2]))
    require(before == after, 'Exact502 exported ABI or shared dependencies changed')
    save('ARM64.json', dict(status='PASS_FULL_ARM64_LINK_AND_EXACT502_ABI',
        source=os.environ['GITHUB_SHA'], request_sha256=sha(REQUEST), selected_test=SELECTED_TEST,
        baseline_native_sha256=ENGINE, baseline_source_map_sha256=MAP, native_sha256=sha(library),
        reviewed_file_count=9418, unchanged_original_native_sources=9408,
        lock_object_sha256=sha(objects[0]), lock_bridge_linked=True,
        exported_interfaces_preserved=len(after[0]), dependencies=sorted(after[1]),
        private_map_sha256=sha(private_map), private_map_link_occurrences=1,
        version_definitions_preserved=before[2] == after[2],
        Android_execution='NOT_RUN', APK=False, signing=False,
        application_acceptance=False, physical_Fold_acceptance=False))


if __name__ == '__main__':
    require(len(sys.argv) == 2, 'Select one native build stage')
    stages = {'gate': authenticate_inputs, 'prepare': prepare, 'tooling': tooling,
              'dependencies': dependencies, 'compile': compile_native}
    require(sys.argv[1] in stages, 'Unknown native build stage')
    stages[sys.argv[1]]()
