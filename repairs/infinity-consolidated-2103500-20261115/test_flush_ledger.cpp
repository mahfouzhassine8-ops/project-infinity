// Focused production-ledger replay of the Python observer's actual callbacks.
// No Android process/shutdown acceptance is claimed by this host executable.
#include "InfinityProtectedWrites.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sys/syscall.h>

// Test-only durability fault at the real syscall boundary, for one temp file.
static std::string failingPath;
extern "C" int fsync(int fd)
{
  char path[PATH_MAX]{};
  const auto descriptor = "/proc/self/fd/" + std::to_string(fd);
  const auto size = ::readlink(descriptor.c_str(), path, sizeof(path) - 1);
  if (!failingPath.empty() && size > 0 && std::string(path, size) == failingPath)
  { errno = EIO; return -1; }
  return static_cast<int>(::syscall(SYS_fsync, fd));
}

int main(int argc, char** argv)
{
  assert(argc == 3);
  namespace fs = std::filesystem;
  using namespace InfinityScriptPersistence;
  const std::string scenario = argv[1], root = argv[2];
  const bool optional = scenario == "optional_failure";
  const std::string file = root + (optional ? "/cache/state" : "/profile/state");
  fs::create_directories(root + "/profile");
  fs::create_directories(root + "/cache");
  { std::ofstream out(file); out << "preserved"; }
  Admit(1, "fixture.provider:service.py");
  Observed(1);
  Touch(1, file);
  // Callback reasons are taken from CLOSED-FLUSH-HOST.json, not synthesized
  // substitutes for the guard itself. The exact guard headers are unchanged.
  if (scenario == "baseline_closed" || optional || scenario == "real_failure")
    Fail(1, "buffer_flush_failed");
  if (scenario == "prior_failure") Fail(1, "buffer_close_failed");
  if (scenario == "dirty") SetProtectedBuffer(1, "file", {file}, true);
  if (scenario == "transaction") SetProtectedTransaction("database", file, true);
  if (scenario == "unobserved") Admit(2, "unknown:service.py");
  if (scenario == "fsync_failure") failingPath = file;
  assert(BeginWriteProtection(23, {root + "/profile"}, {root + "/cache"}));
  assert(CloseParticipantWrites(23));
  const bool expected = scenario == "candidate_closed" || optional;
  const bool sealed = SealEssentialWrites(23);
  assert(sealed == expected);
  assert(EssentialWritesAuthorized(23) == expected);
  const auto proof = EssentialWrites();
  assert(proof.blockers.empty() == expected);
  if (expected)
  {
    assert(!BeginProtectedOperation(1, {root + "/profile/state"}, "late_write"));
    if (!optional)
    {
      std::ifstream in(file); std::string value; in >> value;
      assert(value == "preserved");
    }
  }
  std::cout << "PASS " << scenario << " sealed=" << sealed
            << " blockers=" << proof.blockers.size() << '\n';
}
