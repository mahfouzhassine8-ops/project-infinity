#!/usr/bin/env python3
"""Reuse the actual XML/owner-ledger tests with production virtual owner routing."""
from pathlib import Path
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("original_file_save_tests",
    ROOT/"repairs/android-checkpoint-shutdown/native/test_runtime_file_saves.py")
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
RUNTIME = original.RUNTIME
function = original.function

class RuntimeFileSavesTest(unittest.TestCase):
    def test_checked_xml_and_actual_loaded_owner_ledger(self):
        addon = (RUNTIME / "xbmc/addons/Addon.cpp").read_text()
        self.assertIn('CheckpointExistingFile("special://profile/infinity-audio-policy.json", "audio_policy")', addon)
        start = addon.rfind("namespace\n{", 0, addon.index("struct CheckpointAddonTree"))
        registry = addon[start:addon.index("\n#endif\n\nnamespace ADDON", start)]
        callback_start = addon.index('[checkpointOwner, id]')
        callback_end = addon.index('});', callback_start) + 1
        serializer = ('\nnamespace ADDON { auto CheckpointSerializer(std::weak_ptr<CAddon> checkpointOwner, int id) { return '
                      + addon[callback_start:callback_end] + '; } }\n')
        xml1 = function((RUNTIME / "xbmc/utils/XBMCTinyXML.cpp").read_text(),
                        "bool CXBMCTinyXML::SaveFile(const std::string& filename) const")
        xml2 = function((RUNTIME / "xbmc/utils/XBMCTinyXML2.cpp").read_text(),
                        "bool CXBMCTinyXML2::SaveFile(const std::string& filename) const")
        with tempfile.TemporaryDirectory(prefix="infinity-runtime-file-tests-") as work:
            root = Path(work)
            (root / "filesystem").mkdir()
            (root / "utils").mkdir()
            (root / "filesystem/SpecialProtocol.h").write_text(
                '#pragma once\n#include <string>\nstruct CSpecialProtocol { static std::string TranslatePath(const std::string& path) { return path; } };\n')
            (root / "utils/log.h").write_text(
                '#pragma once\nconstexpr int LOGERROR = 1;\nstruct CLog { template<class... T> static void Log(int, const char*, T...) {} };\n')
            cpp = root / "runtime.cpp"
            cpp.write_text(PRELUDE + serializer + xml1 + "\n" + xml2 + "\n" + registry + TESTS)
            binary = root / "runtime-tests"
            command = [shutil.which("c++") or "c++", "-std=c++17", "-DTARGET_ANDROID",
                       "-Wall", "-Wextra", "-Werror", "-pedantic", "-O2", "-pthread",
                       "-I", str(root), "-I", str(RUNTIME / "xbmc/platform/android/activity"),
                       str(cpp), "-o", str(binary)]
            compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(binary), str(root)], capture_output=True, text=True, timeout=30)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertIn("PASS", tested.stdout)


PRELUDE = original.PRELUDE.replace('#include <fstream>', '#include <fstream>\n#include <functional>')
PRELUDE += r'''namespace ADDON { struct CAddon {
  std::shared_ptr<CAddonSettings> current;
  std::string ownerBytes;
  bool serializable = true;
  std::shared_ptr<CAddonSettings> FindInstanceSettings(int) const { return current; }
  bool SettingsToXML(CXBMCTinyXML& doc, int) const {
    doc.bytes = ownerBytes; return serializable;
  }
};
}
'''
TESTS = original.TESTS.replace('    Reset(); TrackAddonDeletion(path);', r'''    // A derived owner keeps its actual values outside the generic settings
    // placeholder. The production ledger must serialize that existing owner,
    // while retaining checked failures and conflict detection.
    Reset(); Seed(path, "skin-before");
    owner = std::make_shared<ADDON::CAddonSettings>(); owner->serializable = false;
    auto actualOwner = std::make_shared<ADDON::CAddon>();
    actualOwner->current = owner; actualOwner->ownerBytes = "skin-before";
    TrackCreatedAddonTree(owner, path, ADDON::CheckpointSerializer(actualOwner, 0));
    TrackLoadedAddonTree(owner, path);
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "skin-before");
    actualOwner->ownerBytes = "skin-after";
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "skin-after");
    actualOwner->serializable = false;
    CHECK(!InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "skin-after");
    CHECK(InfinityAndroidCheckpoint::failures.back().find("loaded_owner_not_serializable") != std::string::npos);
    // Reloading an owner must not redirect a retained old tree to a new tree.
    actualOwner->serializable = true;
    actualOwner->current = std::make_shared<ADDON::CAddonSettings>();
    actualOwner->ownerBytes = "different-current-tree";
    CHECK(!InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "skin-after");
    owner->serializable = true; owner->bytes = "retained-old-tree-edit";
    InfinityAndroidCheckpoint::MarkAddonSettingsManagerDirty(owner.get());
    const std::weak_ptr<ADDON::CAddon> lifetime = actualOwner;
    actualOwner.reset(); CHECK(lifetime.expired()); // Diagnostics do not retain clean owners.
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "retained-old-tree-edit");
    Reset(); owner = std::make_shared<ADDON::CAddonSettings>(); owner->serializable = false;
    TrackCreatedAddonTree(owner, path); TrackLoadedAddonTree(owner, path);
    CHECK(!InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "retained-old-tree-edit"); // No generic serialization failure waiver.

''' + '    Reset(); TrackAddonDeletion(path);')

if __name__ == '__main__':
    unittest.main()
