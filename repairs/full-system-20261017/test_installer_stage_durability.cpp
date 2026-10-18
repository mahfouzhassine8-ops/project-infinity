// Compile the real protected-write implementation; no mocked fsync receipts.
#include "InfinityProtectedWrites.stagefix.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <unistd.h>

namespace fs = std::filesystem;
using InfinityScriptPersistence::InstallerStageRoot;
using InfinityScriptPersistence::SyncProtectedPath;
using InfinityScriptPersistence::SyncRemovedInstallerStage;

int main()
{
  const auto root = fs::temp_directory_path() /
                    ("infinity-durability-" + std::to_string(getpid()));
  fs::remove_all(root);
  const auto profile = root / ".kodi" / "userdata";
  const auto scratch = root / ".kodi" / "addons" / "temp";
  fs::create_directories(profile);
  fs::create_directories(scratch);
  const auto uuid = "1c160b3d-5630-4c50-a1cc-d6d1c995312f";
  const auto staged = scratch / uuid / "16x9";
  const std::vector<std::string> profiles{profile.string()};
  std::string trusted;
  assert(InstallerStageRoot(staged.string(), profiles, trusted));
  assert(trusted == scratch.string());
  // The Fold's verified failed add-on update removes UUID/16x9 entirely.
  // Persist the remaining real staging directory rather than opening the
  // removed UUID parent and falsely rejecting the whole essential checkpoint.
  assert(SyncProtectedPath(staged.string(), profiles));
  // Existing installer data is *not* skipped; both its inode and parent sync.
  fs::create_directories(staged);
  assert(SyncProtectedPath(staged.string(), profiles));
  fs::remove_all(scratch / uuid);
  assert(SyncProtectedPath(staged.string(), profiles));
  // Never extend the exception to missing essential watched / DB state.
  assert(!SyncProtectedPath((root / ".kodi/userdata/Database/gone/Movies.db").string(), profiles));
  assert(!SyncProtectedPath((root / ".kodi/userdata/addon_data/script.infinity.commandcenter/gone.json").string(), profiles));
  // A malformed UUID is not proof of a managed installer scratch tree.
  assert(!SyncProtectedPath((scratch / "not-a-uuid" / "16x9").string(), profiles));
  // No canonical root supplied -> absolutely no exception.
  assert(!SyncProtectedPath(staged.string(), {}));
  // Never traverse a staging symlink toward another tree.
  const auto foreign = root / "foreign";
  fs::create_directories(foreign);
  fs::create_directory_symlink(foreign, scratch / uuid);
  assert(!SyncProtectedPath(staged.string(), profiles));
  fs::remove(scratch / uuid);
  // If even the trusted scratch root is absent, fail: no durable anchor.
  fs::remove(scratch);
  assert(!SyncProtectedPath(staged.string(), profiles));

  // "Independent shutdown" must mean existing essential saves are retained,
  // future optional producers cannot open new protected writes, and a dirty
  // transaction/buffer NEVER becomes a manufactured save receipt.
  const auto dbdir = profile / "Database";
  fs::create_directories(dbdir);
  const auto database = dbdir / "ResumeHub.db";
  {
    std::ofstream stored(database);
    stored << "original-data-preserved";
  }
  constexpr uint64_t closeGeneration = 2103383;
  assert(InfinityScriptPersistence::BeginWriteProtection(closeGeneration, profiles, {}));
  InfinityScriptPersistence::RegisterParticipant(41);
  // Only the verified canonical participant may begin an essential save after
  // Close requests admission freeze. Unknown new addon writes are refused.
  const auto unauthorized = InfinityScriptPersistence::BeginProtectedOperation(
      500, {database.string()}, "new_optional_provider_write");
  assert(unauthorized == 0);
  const auto essential = InfinityScriptPersistence::BeginProtectedOperation(
      41, {database.string()}, "existing_essential_save");
  assert(essential != 0);
  assert(InfinityScriptPersistence::CloseParticipantWrites(closeGeneration));
  assert(!InfinityScriptPersistence::SealEssentialWrites(closeGeneration));
  InfinityScriptPersistence::EndProtectedOperation(essential);

  // A real uncommitted database transaction must keep authorization blocked,
  // even if optional interpreter retirement has already finished.
  InfinityScriptPersistence::SetProtectedTransaction(
      "resume-txn", database.string(), true);
  assert(!InfinityScriptPersistence::SealEssentialWrites(closeGeneration));
  InfinityScriptPersistence::SetProtectedTransaction(
      "resume-txn", database.string(), false);
  InfinityScriptPersistence::SetProtectedBuffer(
      41, "resume-buffer", {database.string()}, true);
  assert(!InfinityScriptPersistence::SealEssentialWrites(closeGeneration));
  InfinityScriptPersistence::SetProtectedBuffer(
      41, "resume-buffer", {database.string()}, false);

  assert(InfinityScriptPersistence::SealEssentialWrites(closeGeneration));
  assert(InfinityScriptPersistence::EssentialWritesAuthorized(closeGeneration));
  assert(!InfinityScriptPersistence::BeginProtectedOperation(
      41, {database.string()}, "post_seal_essential_write"));
  assert(InfinityScriptPersistence::EssentialWritesAuthorized(closeGeneration));
  assert(fs::exists(database));
  std::ifstream saved(database);
  std::string persisted;
  std::getline(saved, persisted);
  assert(persisted == "original-data-preserved");

  fs::remove_all(root);
  std::cout << "PASS: installer UUID stage durability and independent Essential-First admission/transaction/seal negatives\n";
}
