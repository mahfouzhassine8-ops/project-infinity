// Uses the production InfinityScriptPersistence/InfinityProtectedWrites headers.
// Each scenario runs in a fresh process: never reset or fake native ledger state.
#include "InfinityProtectedWrites.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>

namespace fs = std::filesystem;
namespace IP = InfinityScriptPersistence;

int main(int argc, char** argv)
{
  assert(argc == 2);
  const std::string scenario = argv[1];
  const auto root = fs::temp_directory_path() /
                    ("infinity-optional-io-" + scenario + "-" + std::to_string(getpid()));
  fs::remove_all(root);
  const auto profile = root / ".kodi/userdata";
  const auto addon = profile / "addon_data/plugin.video.thecrew/cache";
  const auto otherAddon = profile / "addon_data/plugin.video.thecrew";
  const auto database = profile / "Database";
  const auto commandCenter = profile / "addon_data/script.infinity.commandcenter";
  fs::create_directories(addon);
  fs::create_directories(database);
  fs::create_directories(commandCenter);
  const auto optional = (addon / "service.log").string();
  const auto essential = (database / "ResumeHub.db").string();
  const auto userSettings = (otherAddon / "settings.xml").string();
  const auto cc = (commandCenter / "progress.json").string();
  IP::Admit(8,"plugin.video.thecrew:service.py");
  IP::Observed(8);
  constexpr uint64_t generation = 2103384;

  if(scenario == "optional_vfs_error" || scenario == "optional_vfs_false" ||
     scenario == "optional_buffer_error" || scenario == "essential_pending" ||
     scenario == "optional_sqlite_pending" || scenario == "optional_corrupt_path" ||
     scenario == "native_ambiguous" || scenario == "essential_participant")
  {
    const std::string reason =
      scenario == "optional_vfs_false" ? "vfs_write_failed" :
      scenario == "optional_buffer_error" ? "buffered_write_failed" : "vfs_write_exception";
    const std::string nativeOperation =
      scenario == "optional_buffer_error" ? "file.write" : "vfs.write";
    const auto lease=IP::BeginProtectedOperation(8,{optional},nativeOperation);
    assert(lease);
    uint64_t extra=0;
    if(scenario == "native_ambiguous")
    {
      extra=IP::BeginProtectedOperation(8,{optional},nativeOperation);
      assert(extra);
    }
    assert(IP::BeginWriteProtection(generation,{profile.string()},{}));
    if(scenario == "essential_participant") IP::RegisterParticipant(8);
    if(scenario == "optional_corrupt_path")
      IP::RecordProtectedResult(lease,essential); // one native lease, two destinations
    IP::Fail(8,reason,"untrusted Python detail cannot prove a file path");
    const auto& blocker=IP::Get().blockers.back();
    if(scenario == "native_ambiguous")
      assert(!blocker.nativeFailureTargetVerified);
    else {
      assert(blocker.nativeFailureTargetVerified);
      assert(blocker.nativeFailureTargets.size() == (scenario=="optional_corrupt_path" ? 2 : 1));
      assert(blocker.nativeFailureTargets[0]==optional);
    }
    if(extra) IP::EndProtectedOperation(extra);
    IP::EndProtectedOperation(lease);
    if(scenario == "essential_pending")
    {
      const auto essentialLease=IP::BeginProtectedOperation(-1,{essential},"native_essential_save",true);
      assert(essentialLease);
      assert(!IP::EssentialWrites().blockers.empty());
      IP::EndProtectedOperation(essentialLease);
    }
    if(scenario == "optional_sqlite_pending")
      IP::SetProtectedTransaction("required-trakt-progress",essential,true);
    assert(IP::CloseParticipantWrites(generation));
    const bool shouldPass=scenario=="optional_vfs_error" ||
                          scenario=="optional_vfs_false" ||
                          scenario=="optional_buffer_error" ||
                          scenario=="essential_pending";
    // Once the accepted required save has ended, its separate proof clears.
    // The optional error itself must not hold the checkpoint hostage.
    const auto actual=IP::EssentialWrites();
    assert(actual.blockers.empty()==shouldPass);
    assert(IP::SealEssentialWrites(generation)==shouldPass);
    assert(IP::EssentialWritesAuthorized(generation)==shouldPass);
  }
  else if(scenario=="essential_vfs" || scenario=="settings_vfs" ||
          scenario=="command_center_vfs" || scenario=="symlink_vfs")
  {
    std::string target=scenario=="essential_vfs"?essential:
                       scenario=="settings_vfs"?userSettings:
                       scenario=="command_center_vfs"?cc:(addon/"leak").string();
    if(scenario=="symlink_vfs")
    {
      const auto foreign=root/"outside";
      fs::create_directories(foreign);
      fs::create_directory_symlink(foreign, addon/"leak");
      target=(addon/"leak/secret").string();
    }
    const auto lease=IP::BeginProtectedOperation(8,{target},"vfs.write");
    assert(lease);
    assert(IP::BeginWriteProtection(generation,{profile.string()},{}));
    IP::Fail(8,"vfs_write_exception");
    IP::EndProtectedOperation(lease);
    assert(IP::CloseParticipantWrites(generation));
    assert(!IP::EssentialWrites().blockers.empty());
    assert(!IP::SealEssentialWrites(generation));
  }
  else if(scenario=="spoofed_path" || scenario=="wrong_operation" ||
          scenario=="unknown_error" || scenario=="no_native_path")
  {
    uint64_t lease=0;
    if(scenario!="spoofed_path")
      lease=IP::BeginProtectedOperation(8,
        scenario=="no_native_path"?std::vector<std::string>{}:std::vector<std::string>{optional},
        scenario=="wrong_operation"?"vfs.copy":"vfs.write");
    assert(scenario=="spoofed_path"||lease);
    assert(IP::BeginWriteProtection(generation,{profile.string()},{}));
    IP::Fail(8,scenario=="unknown_error"?"unclassified_native_persistence_operation":
               "vfs_write_exception", "claimed_optional_path="+optional);
    if(lease) IP::EndProtectedOperation(lease);
    assert(IP::CloseParticipantWrites(generation));
    assert(!IP::EssentialWrites().blockers.empty());
    assert(!IP::SealEssentialWrites(generation));
  }
  else
  {
    std::cerr << "Unknown scenario " << scenario << "\n";
    return 2;
  }
  fs::remove_all(root);
  std::cout << "PASS " << scenario << "\n";
  return 0;
}
