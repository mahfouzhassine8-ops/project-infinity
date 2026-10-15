/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "InfinityEssentialScriptFence.h"
#define INFINITY_DATABASE_BARRIER_TEST
#include "dbwrappers/InfinityDatabaseBarrier.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>
#include <atomic>
using namespace InfinityEssentialScriptFence;
namespace fs = std::filesystem;

int main(int argc, char** argv)
{
  assert(argc == 3);
  const std::string mode = argv[1], root = argv[2];
  const auto privatePath = root + "/addon_data/plugin.video.optional/cache.db";
  const auto sharedPath = root + "/Database/MyVideos.db";
  fs::create_directories(fs::path(privatePath).parent_path());
  fs::create_directories(fs::path(sharedPath).parent_path());
  std::ofstream(privatePath) << "optional";
  std::ofstream(root + "/favourites.xml") << "essential";
  if (mode == "unwired-runtime-refused")
  {
    assert(!CloseAdmission(1, {root}, {}));
    assert(!Authorized(1));
    assert(Snapshot().blockers.front() == "essential_write_hook_coverage_unverified");
    std::cout << "PASS unwired-runtime-refused\n";
    return 0;
  }
  // Controlled test boundary ONLY. No production hook-coverage claim.
  Get().hookCoverageComplete = true;
  if (mode == "native-barrier-raw-file-gap")
  {
    const int fd = ::open((root + "/favourites.xml").c_str(), O_WRONLY);
    assert(fd >= 0);
    assert(InfinityDatabaseBarrier::Begin(1));
    assert(InfinityDatabaseBarrier::Seal(1));
    assert(::write(fd, "CHANGED!!", 9) == 9);
    assert(::fsync(fd) == 0); ::close(fd);
    std::ifstream file(root + "/favourites.xml"); std::string value; file >> value;
    assert(value == "CHANGED!!");
    std::cout << "REPRODUCED: already-open raw file changes after native seal\n";
    return 0;
  }
  Admit(1, "plugin.video.optional:service.py"); Observed(1);
  assert(Observe(1, privatePath));
  if (mode == "shared-writer" || mode == "shared-failure" || mode == "retired-shared" || mode == "reuse-shared")
  {
    std::ofstream(sharedPath) << "committed";
    assert(Observe(1, sharedPath));
    if (mode != "shared-writer") Retired(1, mode != "shared-failure");
    if (mode == "reuse-shared") { Admit(1, "plugin.video.optional:service.py"); Observed(1); }
  }
  if (mode == "opaque") Failure(1, "unclassified_addon_native_extension");
  if (mode == "optional-failure") Failure(1, "sqlite_write_failed");
  if (mode == "observer-missing") Admit(2, "unknown:service.py");
  if (mode == "symlink")
  {
    fs::remove(privatePath); fs::create_symlink(root + "/favourites.xml", privatePath);
  }
  if (mode == "hardlink")
  {
    fs::remove(privatePath); fs::create_hard_link(root + "/favourites.xml", privatePath);
  }
  if (mode == "cache-overlap")
  {
    assert(!CloseAdmission(1, {root}, {fs::path(root).parent_path()}));
    assert(!Authorized(1)); return 0;
  }
  std::atomic<bool> run{true};
  std::thread worker;
  if (mode == "blocked-optional")
    worker = std::thread([&] { while (run) std::this_thread::yield(); });
  if (mode == "concurrent-admission")
  {
    std::ofstream(sharedPath) << "committed";
    worker = std::thread([&] { while (run) Observe(1, sharedPath); });
  }
  assert(CloseAdmission(1, {root}, {}));
  assert(!Observe(1, sharedPath)); // Admission denied under same lock as close.
  const bool ok = Seal(1);
  if (worker.joinable()) { run = false; worker.join(); }
  if (mode == "shared-writer" || mode == "shared-failure" || mode == "reuse-shared" ||
      mode == "opaque" || mode == "observer-missing" || mode == "symlink" || mode == "hardlink")
  { assert(!ok); assert(!Authorized(1)); assert(!Snapshot().blockers.empty()); }
  else if (mode == "concurrent-admission")
  { assert(ok ? Snapshot().blockers.empty() : !Snapshot().blockers.empty()); }
  else
  {
    assert(ok); assert(Authorized(1)); assert(!Authorized(2));
    if (mode == "late-admission") { Admit(2, "late:service.py"); assert(!Authorized(1)); }
  }
  std::cout << "PASS " << mode << '\n';
}

extern "C" bool infinity_test_begin() { return InfinityDatabaseBarrier::Begin(1); }
extern "C" bool infinity_test_ready() { return InfinityDatabaseBarrier::GetSnapshot().Ready(); }
extern "C" bool infinity_test_seal() { return InfinityDatabaseBarrier::Seal(1); }
extern "C" bool infinity_test_sealed() { return InfinityDatabaseBarrier::GetSnapshot().sealed; }
