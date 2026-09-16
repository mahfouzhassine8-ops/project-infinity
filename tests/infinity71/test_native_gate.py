"""Real host CMake fixtures reproduce a cold-prefix gate defect, not Android runtime.

The fixture mirrors Kodi 21.3: JNIMainActivity belongs to platform_android_activity,
WinSystemAndroid to windowing_android, and CORE_MAIN_SOURCE XBMCApp to kodi. Custom-command dependencies create otherwise absent
AndroidJNI/fmt/spdlog headers. No downloaded SDK or host package fills those gaps.
"""
from pathlib import Path
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts'))
import infinity71


class NativeGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='infinity-native-gate-')
        self.root = Path(self.temp.name)
        self.source = self.root / 'source with spaces'
        self.build = self.root / 'build with spaces'
        self.source.mkdir()
        self.cmake = shutil.which('cmake')
        if not self.cmake or not shutil.which('c++'):
            self.fail('Real CMake and a host C++ compiler are required')
        files = {
            'xbmc/platform/android/activity/JNIMainActivity.cpp':
                '#include <androidjni/Activity.h>\nint jni_value() { return JNI_FIXTURE; }\n',
            'xbmc/platform/android/activity/XBMCApp.cpp':
                '#include <fmt/format.h>\n#include <spdlog/spdlog.h>\nint app_value() { return FMT_FIXTURE + SPDLOG_FIXTURE; }\n',
            'xbmc/windowing/android/WinSystemAndroid.cpp':
                '#include <fmt/format.h>\nint window_value() { return FMT_FIXTURE; }\n',
        }
        for name, text in files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        (self.source / 'GenerateHeaders.cmake').write_text('''
file(MAKE_DIRECTORY "${DEST}/androidjni" "${DEST}/fmt" "${DEST}/spdlog")
file(WRITE "${DEST}/androidjni/Activity.h" "#define JNI_FIXTURE 1\\n")
file(WRITE "${DEST}/fmt/format.h" "#define FMT_FIXTURE 2\\n")
file(WRITE "${DEST}/spdlog/spdlog.h" "#define SPDLOG_FIXTURE 3\\n")
''')
        (self.source / 'CMakeLists.txt').write_text('''
cmake_minimum_required(VERSION 3.18)
project(InfinityNativeGateFixture LANGUAGES CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(headers "${CMAKE_BINARY_DIR}/generated/include")
add_custom_command(
  OUTPUT "${headers}/androidjni/Activity.h" "${headers}/fmt/format.h" "${headers}/spdlog/spdlog.h"
  COMMAND "${CMAKE_COMMAND}" "-DDEST=${headers}" -P "${CMAKE_SOURCE_DIR}/GenerateHeaders.cmake"
  DEPENDS "${CMAKE_SOURCE_DIR}/GenerateHeaders.cmake"
  VERBATIM)
add_custom_target(native_fixture_prerequisites
  DEPENDS "${headers}/androidjni/Activity.h" "${headers}/fmt/format.h" "${headers}/spdlog/spdlog.h")
add_library(platform_android_activity STATIC
  xbmc/platform/android/activity/JNIMainActivity.cpp)
add_library(windowing_android STATIC xbmc/windowing/android/WinSystemAndroid.cpp)
# Kodi Android ArchSetup.cmake assigns XBMCApp.cpp to CORE_MAIN_SOURCE;
# the root CMakeLists.txt adds that source to the main shared kodi target.
add_library(kodi SHARED xbmc/platform/android/activity/XBMCApp.cpp)
target_link_libraries(kodi PRIVATE platform_android_activity windowing_android)
foreach(t platform_android_activity windowing_android kodi)
  set_target_properties(${t} PROPERTIES POSITION_INDEPENDENT_CODE ON)
  add_dependencies(${t} native_fixture_prerequisites)
  target_include_directories(${t} PRIVATE "${headers}")
endforeach()
''')
        subprocess.run([self.cmake, '-S', str(self.source), '-B', str(self.build),
                        '-G', 'Unix Makefiles'], check=True, capture_output=True, text=True)
        self.env = patch.dict(os.environ, {'CMAKE_BUILD_PARALLEL_LEVEL': '2'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def status(self):
        return json.loads((self.build / 'infinity-native-gate/status.json').read_text())

    def old_replay(self, suffix):
        entries = json.loads((self.build / 'compile_commands.json').read_text())
        entry = next(e for e in entries if e['file'].endswith(suffix))
        args = entry.get('arguments') or shlex.split(entry['command'])
        filtered = []
        i = 0
        while i < len(args):
            if args[i] in ('-o', '-MF', '-MT', '-MQ'):
                i += 2
                continue
            if args[i] in ('-c', '-MD', '-MMD', '-MP'):
                i += 1
                continue
            filtered.append(args[i])
            i += 1
        return subprocess.run(filtered + ['-fsyntax-only'], cwd=entry['directory'],
                              text=True, capture_output=True)

    def test_rc1_cold_prefix_fails_old_replay_but_target_gate_builds_dependencies(self):
        old = self.old_replay('/JNIMainActivity.cpp')
        self.assertNotEqual(old.returncode, 0)
        self.assertIn('androidjni/Activity.h', old.stderr)
        infinity71.native_compile_check(self.build)
        self.assertEqual(self.status()['status'], 'passed')
        for name in ('androidjni/Activity.h', 'fmt/format.h', 'spdlog/spdlog.h'):
            self.assertTrue((self.build / 'generated/include' / name).is_file())
        self.assertEqual(len(list(self.build.rglob('*.cpp.o'))), 3)

    def test_rc2_one_header_fix_does_not_supply_other_dependencies(self):
        header = self.build / 'generated/include/androidjni/Activity.h'
        header.parent.mkdir(parents=True)
        header.write_text('#define JNI_FIXTURE 1\n')
        self.assertEqual(self.old_replay('/JNIMainActivity.cpp').returncode, 0)
        old = self.old_replay('/XBMCApp.cpp')
        self.assertNotEqual(old.returncode, 0)
        self.assertIn('fmt/format.h', old.stderr)
        infinity71.native_compile_check(self.build)
        self.assertEqual(self.status()['status'], 'passed')

    def test_warm_build_reuses_compiled_objects(self):
        infinity71.native_compile_check(self.build)
        before = {str(p): p.stat().st_mtime_ns for p in self.build.rglob('*.cpp.o')}
        infinity71.native_compile_check(self.build)
        self.assertEqual(before, {str(p): p.stat().st_mtime_ns for p in self.build.rglob('*.cpp.o')})

    def test_real_compile_error_is_not_hidden(self):
        bad = self.source / 'xbmc/windowing/android/WinSystemAndroid.cpp'
        bad.write_text('#error DELIBERATE_COMPILER_FIXTURE_FAILURE\n')
        with self.assertRaises(subprocess.CalledProcessError):
            infinity71.native_compile_check(self.build)
        self.assertEqual(self.status()['status'], 'failed')
        self.assertEqual(self.status()['failed_target'], 'windowing_android')
        self.assertEqual(self.status()['completed_targets'], ['platform_android_activity'])

    def test_dependency_failure_stops_without_success_receipt(self):
        (self.source / 'GenerateHeaders.cmake').write_text('message(FATAL_ERROR "DELIBERATE_DEPENDENCY_FIXTURE_FAILURE")\n')
        with self.assertRaises(subprocess.CalledProcessError):
            infinity71.native_compile_check(self.build)
        self.assertEqual(self.status()['status'], 'failed')
        self.assertEqual(self.status()['completed_targets'], [])

    def test_wrong_target_mapping_is_rejected_before_build(self):
        path = self.build / 'compile_commands.json'
        path.write_text(path.read_text().replace('platform_android_activity.dir', 'unrelated.dir'))
        with self.assertRaisesRegex(ValueError, 'Unexpected native target'):
            infinity71.native_compile_check(self.build)
        self.assertFalse((self.build / 'generated').exists())

    def test_missing_source_is_rejected_before_build(self):
        path = self.build / 'compile_commands.json'
        entries = json.loads(path.read_text())
        path.write_text(json.dumps(entries[1:]))
        with self.assertRaisesRegex(ValueError, 'Missing/ambiguous'):
            infinity71.native_compile_check(self.build)

    def test_kodi_21_3_main_source_is_built_by_its_real_owner(self):
        entries = json.loads((self.build / 'compile_commands.json').read_text())
        app = next(e for e in entries if e['file'].endswith('/XBMCApp.cpp'))
        args = app.get('arguments') or shlex.split(app['command'])
        output = app.get('output') or args[args.index('-o') + 1]
        self.assertIn('CMakeFiles/kodi.dir/', output)
        infinity71.native_compile_check(self.build)
        receipt = self.status()
        self.assertEqual(receipt['sources']['xbmc/platform/android/activity/XBMCApp.cpp'], 'kodi')
        self.assertEqual(receipt['completed_targets'],
                         ['platform_android_activity', 'windowing_android', 'kodi'])
        self.assertFalse(receipt['device_accepted'])
        self.assertTrue((self.build / 'libkodi.so').is_file())

    def test_main_source_compile_error_is_not_hidden(self):
        bad = self.source / 'xbmc/platform/android/activity/XBMCApp.cpp'
        bad.write_text('#error DELIBERATE_MAIN_SOURCE_FIXTURE_FAILURE\n')
        with self.assertRaises(subprocess.CalledProcessError):
            infinity71.native_compile_check(self.build)
        self.assertEqual(self.status()['status'], 'failed')
        self.assertEqual(self.status()['failed_target'], 'kodi')
        self.assertEqual(self.status()['completed_targets'],
                         ['platform_android_activity', 'windowing_android'])

    def test_incorrect_activity_owner_for_main_source_is_rejected(self):
        path = self.build / 'compile_commands.json'
        path.write_text(path.read_text().replace('CMakeFiles/kodi.dir/',
                                                'CMakeFiles/platform_android_activity.dir/'))
        with self.assertRaisesRegex(ValueError, 'Unexpected native target.*XBMCApp'):
            infinity71.native_compile_check(self.build)
        self.assertFalse((self.build / 'generated').exists())

    def test_invalid_parallelism_is_rejected(self):
        with patch.dict(os.environ, {'CMAKE_BUILD_PARALLEL_LEVEL': '0'}):
            with self.assertRaisesRegex(ValueError, 'parallelism'):
                infinity71.native_compile_check(self.build)


if __name__ == '__main__':
    unittest.main(verbosity=2)
