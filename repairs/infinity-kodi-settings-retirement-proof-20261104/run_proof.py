#!/usr/bin/env python3
"""Selected settings-retirement safety cases; host-only, no production patch."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NATIVE = Path('/tmp/kodi451-restored-native')
OUT = Path('/tmp/infinity-settings-retirement-proof-results-20261104')
OLD = Path('/workspace/project-infinity/repairs/android-checkpoint-shutdown/native/test_runtime_file_saves.py')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    plan = json.loads((HERE/'SELECTED-TESTS.json').read_text())
    OUT.mkdir(exist_ok=True)
    if (OUT/'STARTED.json').exists():
        raise RuntimeError('Selected run already started; preserve results, no automatic retry')
    expected = json.loads(Path('/tmp/kodi451-restored-proof/CANDIDATE-NATIVE-SOURCE-MAP.json').read_text())
    baseline = json.loads(Path('/tmp/kodi451-restored-proof/BASELINE-NATIVE-SOURCE-MAP.json').read_text())
    binding = {}

    def read(name):
        raw = (NATIVE/name).read_bytes()
        assert digest(raw) == expected[name], name
        binding[name] = {'sha256': digest(raw), 'identical_to451': digest(raw) == baseline[name]}
        return raw.decode()

    spec = importlib.util.spec_from_file_location('existing_extractor', OLD)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    addon = read('xbmc/addons/Addon.cpp')
    start = addon.rfind('namespace\n{', 0, addon.index('struct CheckpointAddonTree'))
    end = addon.index('\n#endif\n\nnamespace ADDON', start)
    registry = addon[start:end]
    xml = old.function(read('xbmc/utils/XBMCTinyXML.cpp'), 'bool CXBMCTinyXML::SaveFile(const std::string& filename) const')
    for name in ('xbmc/platform/android/activity/InfinityCheckpointFile.h',
                 'xbmc/platform/android/activity/InfinityCheckpointXml.h',
                 'xbmc/platform/android/activity/InfinityAndroidCheckpoint.h',
                 'xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp',
                 'xbmc/settings/lib/SettingsManager.cpp', 'xbmc/settings/lib/Setting.cpp',
                 'xbmc/addons/settings/AddonSettings.cpp', 'xbmc/addons/Addon.h', 'xbmc/addons/Skin.cpp'):
        read(name)
    unit = (HERE/'proof_peers.cpp.in').read_text()+'\n'+xml+'\n'+registry+'\n'+(HERE/'proof_cases.cpp.in').read_text()
    for signature in ('void TrackCreatedAddonTree(', 'void TrackLoadedAddonTree(', 'void TrackAddonSave(',
                      'bool ConfirmAddonSave(', 'void InfinityAndroidCheckpoint::MarkAddonSettingsManagerDirty(',
                      'bool InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()'):
        assert old.function(unit, signature) == old.function(addon, signature), signature
    (OUT/'proof.cpp').write_text(unit)
    (OUT/'include/filesystem').mkdir(parents=True, exist_ok=True)
    (OUT/'include/utils').mkdir(parents=True, exist_ok=True)
    (OUT/'include/filesystem/SpecialProtocol.h').write_text('#pragma once\n#include <string>\nstruct CSpecialProtocol { static std::string TranslatePath(const std::string& p){return p;} };\n')
    (OUT/'include/utils/log.h').write_text('#pragma once\nconstexpr int LOGERROR=1;\nstruct CLog {template<class... T> static void Log(int,const char*,T&&...){} };\n')
    (OUT/'SOURCE-BINDING.json').write_text(json.dumps({
        'files': binding, 'extractor_sha256': digest(OLD.read_bytes()),
        'generated_cpp_sha256': digest(unit.encode()),
        'actual_methods': ['owner registry', 'CheckpointLoadedAddonSettings', 'CXBMCTinyXML::SaveFile'],
        'actual_io': 'Protected InfinityCheckpointXml/File headers, host POSIX IO and read-back',
        'peers': ['synthetic opaque serialization payloads, not native settings trees',
                  'coordinator admission/phase supplied, not Android coordinator execution',
                  'ordinary CFile open/write/flush peer', 'fsync fault injection in host executable only'],
        'negative_controls': 'Two deliberately unsafe retirement predicates manipulate synthetic registry state only',
        'no_production_patch': True,
    }, indent=2)+'\n')
    command = ['g++', '-std=c++17', '-O2', '-pthread', '-DTARGET_ANDROID', '-Wall', '-Wextra',
               '-I', str(OUT/'include'), '-I', str(NATIVE/'xbmc/platform/android/activity'),
               str(OUT/'proof.cpp'), '-Wl,--wrap=fsync', '-o', str(OUT/'proof')]
    compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (OUT/'COMPILE.txt').write_text(compiled.stdout+compiled.stderr)
    (OUT/'COMPILE-COMMAND.json').write_text(json.dumps(command, indent=2)+'\n')
    if compiled.returncode:
        raise RuntimeError('Host fixture compile failed; see COMPILE.txt; no cases executed')
    (OUT/'STARTED.json').write_text(json.dumps({'cases': plan['cases'], 'binary_sha256': digest((OUT/'proof').read_bytes()), 'pid': os.getpid()}, indent=2)+'\n')
    results = []
    negative = {'confirmed_order_not_file_order', 'unsafe_generation_count_retirement_counterexample', 'revision_invalidation_only_counterexample'}
    for case in plan['cases']:
        ran = subprocess.run([str(OUT/'proof'), case, str(OUT/'synthetic-files'/case)], capture_output=True, text=True, timeout=30)
        (OUT/(case+'.stderr.txt')).write_text(ran.stderr)
        if ran.returncode:
            (OUT/(case+'.stdout.txt')).write_text(ran.stdout)
            raise RuntimeError('Selected case failed; no automatic retry: '+case)
        row = json.loads(ran.stdout)
        assert row['case'] == case and row['expected_result_observed'] is True
        row['classification'] = 'UNSAFE_RULE_OR_ORDERING_COUNTEREXAMPLE' if case in negative else 'PRESERVED_OBLIGATION_OBSERVED'
        results.append(row)
    result = {'status': 'COMPLETED_SELECTED_HOST_SAFETY_PROOF', 'cases': len(results),
              'preserved_obligation_cases': len(results)-len(negative), 'counterexamples': len(negative),
              'results': results, 'production_ready_retirement_patch': False,
              'why_not_ready': 'Existing generation/reference metadata does not establish snapshot revision, mutation coverage or actual same-path write ordering.',
              'android_tested': False, 'full_shutdown_tested': False,
              'checkpoint_component_tested': True, 'signed_or_built_apk': False}
    (OUT/'RESULTS.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('status','cases','preserved_obligation_cases','counterexamples','production_ready_retirement_patch')}, indent=2))


if __name__ == '__main__':
    main()
