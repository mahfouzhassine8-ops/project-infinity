"""Focused corrected-source lifetime verification; no device or user-data access."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
from test_baseline_observer_lifetime import definition

HERE = Path(__file__).resolve().parent
ACTIVITY = 'xbmc/platform/android/activity/'
METHODS = ('jboolean CJNIMainActivity::_infinityHasActiveVideo(',
           'void CJNIMainActivity::_infinitySyncDisplayState(',
           'jint CJNIMainActivity::_infinityWindowWidth(',
           'jint CJNIMainActivity::_infinityWindowHeight(',
           'jboolean CJNIMainActivity::_infinityCanEnterPictureInPicture(',
           'jfloat CJNIMainActivity::_infinityVideoAspectRatio(',
           'jlongArray CJNIMainActivity::_infinityGetState(')
HOOKS = ('void CJNIMainActivity::PublishInfinityObservers(', 'void CJNIMainActivity::RetireInfinityObservers(')
FACTORY = ('static CXBMCApp& Create(', 'static void Destroy()')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    scope = json.loads((HERE / 'OBSERVER-SCOPE.json').read_bytes())
    sources = json.loads((HERE / 'OBSERVER-SOURCE.json').read_bytes())
    for name, row in sources.items():
        assert sha((HERE / 'native' / name).read_bytes()) == row['after'], name
    for name, expected in scope['existing'].items():
        assert sha((args.baseline / name).read_bytes()) == expected, name
    source = (HERE / 'native' / ACTIVITY / 'JNIMainActivity.cpp').read_text()
    base = (args.baseline / ACTIVITY / 'JNIMainActivity.cpp').read_text()
    normal = source
    for method in METHODS:
        normal = normal.replace(definition(normal, method), definition(base, method), 1)
    for method in HOOKS:
        normal = normal.replace(definition(normal, method) + '\n\n', '', 1)
    normal = normal.replace('#include "InfinityActivityObserver.h"\n#include <android/log.h>\n', '', 1)
    normal = normal.replace('InfinityActivityObserver<CJNIMainActivity> g_infinityObservers;\n\n', '', 1)
    assert normal == base, 'Unrelated JNI source changed'
    header = (HERE / 'native' / ACTIVITY / 'JNIMainActivity.h').read_text()
    addition = '''  // Private factory hooks: no JNI or exported ABI additions.
  static void PublishInfinityObservers(CJNIMainActivity* owner) __attribute__((visibility("hidden")));
  static void RetireInfinityObservers(CJNIMainActivity* owner) __attribute__((visibility("hidden")));

'''
    assert header.replace(addition, '', 1) == (args.baseline / ACTIVITY / 'JNIMainActivity.h').read_text()
    factory = (HERE / 'native' / ACTIVITY / 'XBMCApp.h').read_text()
    original_factory = (args.baseline / ACTIVITY / 'XBMCApp.h').read_text()
    normal = factory
    for method in FACTORY:
        normal = normal.replace(definition(normal, method), definition(original_factory, method), 1)
    assert normal == original_factory, 'Unrelated native owner changed'
    inherited = ('CJNIMainActivity::CJNIMainActivity(', 'CJNIMainActivity::~CJNIMainActivity()')
    for method in inherited:
        assert definition(source, method) == definition(base, method)
    methods = '\n\n'.join(definition(source, method) for method in (*inherited, *HOOKS, *METHODS))
    factories = '\n'.join(definition(factory, method) for method in FACTORY)
    fixture = (HERE / 'observer_lifetime_fixture.cpp.in').read_text()
    assert fixture.count('// @EXACT_JNI_METHODS@') == fixture.count('// @EXACT_FACTORY_METHODS@') == 1
    harness = fixture.replace('// @EXACT_JNI_METHODS@', methods).replace('// @EXACT_FACTORY_METHODS@', factories)
    assert not args.work.exists()
    args.work.mkdir(parents=True)
    cpp = args.work / 'observer.cpp'
    cpp.write_text(harness)
    binary = args.work / 'observer'
    command = ['g++', '-std=c++17', '-O1', '-g', '-pthread', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I', str(HERE / 'native' / ACTIVITY), str(cpp), '-o', str(binary)]
    compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
    receipt = {'status': 'PASS_CORRECTED_SOURCE_HOST' if result.returncode == 0 else 'FAIL', 'source': sources,
               'outside_reviewed_delta': 'BYTE_IDENTICAL', 'harness_sha256': sha(harness.encode()),
               'extracted_methods_sha256': sha(methods.encode()), 'extracted_factory_sha256': sha(factories.encode()),
               'sanitizers': ['address', 'undefined'], 'returncode': result.returncode,
               'stdout': result.stdout, 'stderr': result.stderr,
               'limits': ['Minimal JNI carrier', 'Actual virtual owners use test-only barriers and return values', 'No Android/Stop/watched/owner-incident execution claim']}
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    assert result.returncode == 0, (result.stdout, result.stderr)
    print(receipt['status'], result.stdout.strip())


if __name__ == '__main__':
    main()
