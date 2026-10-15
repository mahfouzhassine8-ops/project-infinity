#!/usr/bin/env python3
"""Exercise extracted production XML routing and loaded-owner ledger on real files.

This deliberately compiles the changed function bodies, not a second copy of
their algorithm. Kodi UI/serialization classes are minimal fixtures; POSIX
durability, paths, xattrs, atomic replacement and the registry are production.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


RUNTIME = Path(os.environ.get("INFINITY_RUNTIME_NATIVE", "/workspace/scratch/a86210039ee8/runtime-native"))


def function(source, signature):
    start = source.index(signature)
    end = source.index("\n}\n", start) + 3
    return source[start:end]


class RuntimeFileSavesTest(unittest.TestCase):
    def test_checked_xml_and_actual_loaded_owner_ledger(self):
        addon = (RUNTIME / "xbmc/addons/Addon.cpp").read_text()
        self.assertIn('CheckpointExistingFile("special://profile/infinity-audio-policy.json", "audio_policy")', addon)
        start = addon.index("namespace\n{\nstruct CheckpointAddonTree")
        registry = addon[start:addon.index("\n#endif\n\nnamespace ADDON", start)]
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
            cpp.write_text(PRELUDE + xml1 + "\n" + xml2 + "\n" + registry + TESTS)
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


PRELUDE = r'''
#include "InfinityCheckpointXml.h"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <mutex>
#include <set>
#include <stdexcept>
#include <vector>

namespace fs = std::filesystem;
#define CHECK(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while(false)
namespace InfinityAndroidCheckpoint {
bool persist = true;
bool admit = true;
std::vector<std::string> failures;
bool IsActive() { return persist; }
bool IsPersistingOnThisThread() { return persist; }
void RecordPersistenceFailure(const char* owner, const char* detail) {
  failures.push_back(std::string(owner) + ":" + detail);
}
CheckpointWriteGuard::CheckpointWriteGuard(const char*) : m_admitted(admit) {}
CheckpointWriteGuard::~CheckpointWriteGuard() = default;
}

struct TiXmlPrinter {
  std::string bytes;
  const char* CStr() const { return bytes.c_str(); }
  size_t Size() const { return bytes.size(); }
};
namespace tinyxml2 {
struct XMLPrinter {
  std::string bytes;
  const char* CStr() const { return bytes.c_str(); }
  int CStrSize() const { return static_cast<int>(bytes.size()) + 1; }
};
}
struct CXBMCTinyXML {
  std::string bytes;
  bool serialize = true;
  bool Accept(TiXmlPrinter* printer) const { printer->bytes = bytes; return serialize; }
  bool SaveFile(const std::string& filename) const;
};
struct CXBMCTinyXML2 {
  std::string bytes;
  bool serialize = true;
  bool Accept(tinyxml2::XMLPrinter* printer) const { printer->bytes = bytes; return serialize; }
  bool SaveFile(const std::string& filename) const;
};
namespace XFILE {
struct CFile {
  static int legacyOpens;
  static int legacyFlushes;
  bool OpenForWrite(const std::string&, bool) { ++legacyOpens; return true; }
  ssize_t Write(const char*, size_t n) { return static_cast<ssize_t>(n); }
  void Flush() { ++legacyFlushes; }
  static bool Exists(const std::string& path) { return fs::exists(path); }
};
int CFile::legacyOpens = 0;
int CFile::legacyFlushes = 0;
struct CDirectory {
  static bool Exists(const std::string& path) { return fs::is_directory(path); }
  static bool Create(const std::string& path) { return fs::create_directories(path); }
};
}
using XFILE::CFile;
using XFILE::CDirectory;
struct URIUtils {
  static std::string GetDirectory(const std::string& path) { return path.substr(0, path.rfind('/') + 1); }
  static std::string GetParentPath(std::string path) {
    while (path.size() > 1 && path.back() == '/') path.pop_back();
    return fs::path(path).parent_path().string() + "/";
  }
};
namespace ADDON {
struct CAddonSettings {
  std::string bytes;
  bool loaded = true;
  bool serializable = true;
  bool IsLoaded() const { return loaded; }
  bool Save(CXBMCTinyXML& doc) const { doc.bytes = bytes; return serializable; }
  const void* GetSettingsManager() const { return this; }
};
}
'''

TESTS = r'''
std::string Read(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  return std::string(std::istreambuf_iterator<char>(in), {});
}
void Seed(const std::string& path, const std::string& value) {
  std::ofstream out(path, std::ios::binary); out << value;
}
ino_t Inode(const std::string& path) { struct stat st{}; CHECK(::stat(path.c_str(), &st) == 0); return st.st_ino; }
void Reset() {
  g_checkpointAddonTrees.clear(); g_checkpointAddonSaves.clear(); g_checkpointAddonSaveGenerations.clear(); g_checkpointAddonDeletions.clear();
  InfinityAndroidCheckpoint::failures.clear(); InfinityAndroidCheckpoint::persist = true;
  InfinityAndroidCheckpoint::admit = true;
}
struct ExistingFileIo : infinity::checkpoint::files::PosixIo {
  std::map<int, bool> descriptors;
  int filesSynced = 0, directoriesSynced = 0, writes = 0, renames = 0;
  bool failFileSync = false, failDirectorySync = false, failFileClose = false;
  int OpenAt(int directory, const char* path, int flags, mode_t mode) override {
    const int fd = PosixIo::OpenAt(directory, path, flags, mode);
    if (fd >= 0) descriptors[fd] = (flags & O_DIRECTORY) != 0;
    return fd;
  }
  int Sync(int fd) override {
    const bool directory = descriptors.at(fd);
    if (directory) ++directoriesSynced; else ++filesSynced;
    if ((directory && failDirectorySync) || (!directory && failFileSync)) { errno = EIO; return -1; }
    return PosixIo::Sync(fd);
  }
  int Close(int fd) override {
    const bool file = !descriptors.at(fd);
    descriptors.erase(fd);
    const int result = PosixIo::Close(fd);
    if (file && failFileClose) { errno = EINTR; return -1; }
    return result;
  }
  ssize_t Write(int fd, const void* data, size_t size) override {
    ++writes; return PosixIo::Write(fd, data, size);
  }
  int RenameAt(int from, const char* oldName, int to, const char* newName) override {
    ++renames; return PosixIo::RenameAt(from, oldName, to, newName);
  }
};
int main(int argc, char** argv) {
  try {
    CHECK(argc == 2);
    const std::string root = argv[1];
    const std::string control = root + "/.android-checkpoint";
    fs::create_directory(control);
    const std::string engine = control + "/engine.json";
    CHECK(InfinityAndroidCheckpoint::SaveCheckpointProtocol(engine, "current-owner"));
    InfinityAndroidCheckpoint::persist = false;
    CHECK(!InfinityAndroidCheckpoint::SaveCheckpointProtocol(engine, "unauthorized-owner"));
    CHECK(Read(engine) == "current-owner");
    InfinityAndroidCheckpoint::persist = true;
    CHECK(!InfinityAndroidCheckpoint::SaveCheckpointProtocol(control + "/settings.xml", "bad"));
    CHECK(!fs::exists(control + "/settings.xml"));
    const std::string path = root + "/settings.xml";
    const std::string policy = root + "/infinity-audio-policy.json";
    ExistingFileIo missing;
    CHECK(InfinityAndroidCheckpoint::CheckpointExistingFile(policy, "audio_policy", missing));
    CHECK(!fs::exists(policy) && missing.filesSynced == 0 && missing.descriptors.empty());
    Seed(policy, "{\"schema\":1,\"video\":\"movie\"}\n");
    const std::string policyBytes = Read(policy); const auto policyInode = Inode(policy);
    ExistingFileIo completed;
    CHECK(InfinityAndroidCheckpoint::CheckpointExistingFile(policy, "audio_policy", completed));
    CHECK(completed.filesSynced == 1 && completed.directoriesSynced == 1);
    CHECK(completed.writes == 0 && completed.renames == 0 && completed.descriptors.empty());
    CHECK(Read(policy) == policyBytes && Inode(policy) == policyInode);
    for (int fault = 0; fault < 3; ++fault) {
      ExistingFileIo failed;
      failed.failFileSync = fault == 0; failed.failDirectorySync = fault == 1; failed.failFileClose = fault == 2;
      CHECK(!InfinityAndroidCheckpoint::CheckpointExistingFile(policy, "audio_policy", failed));
      CHECK(failed.descriptors.empty()); CHECK(Read(policy) == policyBytes && Inode(policy) == policyInode);
    }
    const std::string policyLink = root + "/policy-link";
    CHECK(::symlink(policy.c_str(), policyLink.c_str()) == 0);
    CHECK(!InfinityAndroidCheckpoint::CheckpointExistingFile(policyLink, "audio_policy"));
    CHECK(!InfinityAndroidCheckpoint::CheckpointExistingFile(root, "audio_policy"));
    CHECK(!InfinityAndroidCheckpoint::CheckpointExistingFile(root + "/missing-parent/policy.json", "audio_policy"));
    CXBMCTinyXML doc; doc.bytes = "<settings>state</settings>";
    CHECK(doc.SaveFile(path)); CHECK(Read(path) == doc.bytes);
    const auto inode = Inode(path); CHECK(doc.SaveFile(path)); CHECK(Inode(path) == inode);
    CXBMCTinyXML2 doc2; doc2.bytes = "<favourites/>";
    CHECK(doc2.SaveFile(path)); CHECK(Read(path) == doc2.bytes); // no trailing NUL
    doc.serialize = false; CHECK(!doc.SaveFile(path)); CHECK(Read(path) == doc2.bytes);
    CHECK(!InfinityAndroidCheckpoint::failures.empty()); doc.serialize = true;
    InfinityAndroidCheckpoint::admit = false; CHECK(!doc.SaveFile(path));
    CHECK(Read(path) == doc2.bytes); InfinityAndroidCheckpoint::admit = true;
    CHECK(!doc.SaveFile("smb://host/settings.xml"));
    const std::string link = root + "/leaf-link";
    CHECK(::symlink(path.c_str(), link.c_str()) == 0); CHECK(!doc.SaveFile(link));
    const std::string parentLink = root + "/parent-link";
    CHECK(::symlink(root.c_str(), parentLink.c_str()) == 0);
    CHECK(doc.SaveFile(parentLink + "/resolved.xml")); CHECK(Read(root + "/resolved.xml") == doc.bytes);
    InfinityAndroidCheckpoint::persist = false;
    CHECK(doc.SaveFile(path)); CHECK(CFile::legacyOpens == 1 && CFile::legacyFlushes == 1);
    CHECK(Read(path) == doc2.bytes); // legacy fixture has no side effect

    Reset(); Seed(path, "baseline");
    auto owner = std::make_shared<ADDON::CAddonSettings>(); owner->bytes = "baseline";
    TrackCreatedAddonTree(owner, path); TrackLoadedAddonTree(owner, path);
    const auto untouched = Inode(path);
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()); CHECK(Inode(path) == untouched);
    owner->bytes = "unsaved-current-value";
    InfinityAndroidCheckpoint::MarkAddonSettingsManagerDirty(owner.get());
    const std::weak_ptr<ADDON::CAddonSettings> dirtyLifetime = owner;
    owner.reset(); CHECK(!dirtyLifetime.expired());
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "unsaved-current-value"); CHECK(dirtyLifetime.expired());

    Reset(); owner = std::make_shared<ADDON::CAddonSettings>(); owner->bytes = Read(path);
    TrackCreatedAddonTree(owner, path); TrackLoadedAddonTree(owner, path);
    const std::weak_ptr<ADDON::CAddonSettings> cleanLifetime = owner;
    owner.reset(); CHECK(cleanLifetime.expired());
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());

    Reset(); Seed(path, "baseline");
    auto left = std::make_shared<ADDON::CAddonSettings>(); left->bytes = "baseline";
    auto right = std::make_shared<ADDON::CAddonSettings>(); right->bytes = "baseline";
    TrackCreatedAddonTree(left, path); TrackLoadedAddonTree(left, path);
    TrackCreatedAddonTree(right, path); TrackLoadedAddonTree(right, path);
    left->bytes = "left-unsaved"; right->bytes = "right-unsaved";
    InfinityAndroidCheckpoint::MarkAddonSettingsManagerDirty(left.get());
    InfinityAndroidCheckpoint::MarkAddonSettingsManagerDirty(right.get());
    CHECK(!InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()); CHECK(Read(path) == "baseline");
    CHECK(InfinityAndroidCheckpoint::failures.back().find("conflicting_loaded_owners") != std::string::npos);

    // A checked real settings SaveFile may rebase only the exact writer. A second
    // loaded owner still retains its own baseline; an unsaved conflicting edit
    // must not be lost or silently declared durable at shutdown.
    Reset(); Seed(path, "baseline");
    left = std::make_shared<ADDON::CAddonSettings>(); left->bytes = "baseline";
    right = std::make_shared<ADDON::CAddonSettings>(); right->bytes = "baseline";
    TrackCreatedAddonTree(left, path); TrackLoadedAddonTree(left, path);
    TrackCreatedAddonTree(right, path); TrackLoadedAddonTree(right, path);
    CXBMCTinyXML committed; committed.bytes = "left-committed";
    left->bytes = committed.bytes;
    CHECK(committed.SaveFile(path)); // actual checked synchronous settings file write
    CHECK(ConfirmAddonSave(left, path, committed));
    CHECK(g_checkpointAddonSaveGenerations.at(path) == 1);
    CHECK(g_checkpointAddonSaves.at(path).bytes == committed.bytes);
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "left-committed");
    CHECK(g_checkpointAddonSaves.empty());
    // Save evidence must be rechecked; only the matching writer's baseline advanced.
    Reset(); Seed(path, "baseline");
    left = std::make_shared<ADDON::CAddonSettings>(); left->bytes = "baseline";
    right = std::make_shared<ADDON::CAddonSettings>(); right->bytes = "baseline";
    TrackCreatedAddonTree(left, path); TrackLoadedAddonTree(left, path);
    TrackCreatedAddonTree(right, path); TrackLoadedAddonTree(right, path);
    committed.bytes = "committed-value"; left->bytes = committed.bytes;
    CHECK(committed.SaveFile(path));
    CHECK(ConfirmAddonSave(left, path, committed));
    right->bytes = "other-unsaved-change";
    InfinityAndroidCheckpoint::MarkAddonSettingsManagerDirty(right.get());
    CHECK(!InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings());
    CHECK(Read(path) == "committed-value"); // conflict remains fail-closed
    CHECK(InfinityAndroidCheckpoint::failures.back().find("conflicting_loaded_owners") != std::string::npos);
    Seed(path, "baseline"); // Restore the next inherited fixture after conflict verification.

    Reset(); owner = std::make_shared<ADDON::CAddonSettings>(); owner->bytes = "unproven";
    TrackCreatedAddonTree(owner, path);
    CHECK(!InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()); CHECK(Read(path) == "baseline");

    Reset(); owner = std::make_shared<ADDON::CAddonSettings>(); owner->bytes = "baseline";
    TrackCreatedAddonTree(owner, path); TrackLoadedAddonTree(owner, path);
    CXBMCTinyXML queued; queued.bytes = "earlier-save"; TrackAddonSave(owner, path, queued);
    owner->bytes = "newer-unsaved"; InfinityAndroidCheckpoint::MarkAddonSettingsManagerDirty(owner.get());
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()); CHECK(Read(path) == "newer-unsaved");

    Reset(); queued.bytes = "retry-save"; TrackAddonSave(nullptr, link, queued);
    CHECK(!InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()); CHECK(!g_checkpointAddonSaves.empty());
    CHECK(::unlink(link.c_str()) == 0);
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()); CHECK(Read(link) == "retry-save");
    CHECK(g_checkpointAddonSaves.empty());

    Reset(); TrackAddonDeletion(path); CHECK(::unlink(path.c_str()) == 0);
    CHECK(InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()); CHECK(!fs::exists(path));
    std::cout << "PASS production XML routing and loaded owner persistence/lifetime/failure scenarios\n";
    return 0;
  } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
'''


if __name__ == "__main__":
    unittest.main()
