// Compile actual native header algorithms, without falsifying Close receipts.
// Each scenario runs a separate process, resetting all process-lifetime ledgers.
#include "InfinityProtectedWrites.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <unistd.h>
namespace fs=std::filesystem;
namespace IS=InfinityScriptPersistence;

static void makeFile(const fs::path& path) {
  fs::create_directories(path.parent_path());
  std::ofstream f(path);
  f<<"DATA PRESERVED";
  f.flush();
  assert(bool(f));
}
int main(int argc,char**argv) {
  assert(argc==2);
  std::string which=argv[1];
  fs::path root=fs::temp_directory_path() /
    ("infinity-vfs-integrity-"+std::to_string(getpid()));
  fs::remove_all(root);
  const auto profile=root/".kodi"/"userdata";
  const auto addon=profile/"addon_data"/"plugin.video.thecrew"/"artwork.cache";
  const auto essential=profile/"addon_data"/"script.infinity.commandcenter"/"progress.json";
  const auto settings=profile/"addon_data"/"plugin.video.thecrew"/"settings.xml";
  makeFile(addon);makeFile(essential);makeFile(settings);
  const auto addonPath=addon.string(), essentialPath=essential.string(),
             settingsPath=settings.string();
  const int id=8;
  IS::Admit(id,"plugin.video.thecrew:service.py");
  IS::Observed(id);
  // A prior essential write by the same Python service prevents us from
  // falsely classifying its later failed handle as optional-only.
  if(which=="mixed-profile-writes") {
    auto earlier=IS::BeginProtectedOperation(id,{essentialPath},"vfs.write");
    assert(earlier);
    IS::EndProtectedOperation(earlier);
  }
  // Simulate the exact failed VFS write that was logged by the physical Fold.
  const std::string leased = which=="essential" ? essentialPath :
                             which=="settings" ? settingsPath : addonPath;
  auto token=IS::BeginProtectedOperation(id,{leased},"vfs.write");
  assert(token!=0);
  std::string bound;
  if(which=="forged")bound=IS::VerifiedVfsWriteFailureTarget(id,"vfs.write",essentialPath);
  else if(which=="wrong-operation")
    bound=IS::VerifiedVfsWriteFailureTarget(id,"vfs.close",leased);
  else if(which!="unscoped")
    bound=IS::VerifiedVfsWriteFailureTarget(id,"vfs.write",leased);
  if(which=="forged" || which=="wrong-operation") assert(bound.empty());
  else if(which!="unscoped")assert(!bound.empty());
  IS::Fail(id,
      which=="unrelated" ? "vfs_close_failed" : "vfs_write_exception",
      "",bound);
  IS::EndProtectedOperation(token);
  IS::Retired(id); // Failed optional interpreter remains a failed receipt.
  assert(IS::BeginWriteProtection(2103384,{profile.string()},{}));
  if(which=="pending-essential-txn")
    IS::SetProtectedTransaction("main-profile-db",essentialPath,true);
  if(which=="unflushed-essential-buffer")
    IS::SetProtectedBuffer(8,"my-buffer",{essentialPath},true);
  if(which=="active-essential-operation") {
    const auto op=IS::BeginProtectedOperation(-1,{essentialPath},
                                              "already_accepted_native_db_save",true);
    assert(op!=0);
  }
  if(which=="alias-to-essential")
    IS::RememberAlias(addonPath,essentialPath);
  assert(IS::CloseParticipantWrites(2103384));
  const auto preSeal=IS::EssentialWrites();
  const bool shouldPass=which=="optional";
  if(shouldPass) {
    assert(preSeal.blockers.empty());
    assert(IS::SealEssentialWrites(2103384));
    assert(IS::EssentialWritesAuthorized(2103384));
  }else{
    assert(!preSeal.blockers.empty());
    assert(!IS::SealEssentialWrites(2103384));
    assert(!IS::EssentialWritesAuthorized(2103384));
  }
  {
    std::ifstream f(essential);
    std::string saved;
    std::getline(f,saved);
    assert(saved=="DATA PRESERVED");
  }
  fs::remove_all(root);
  std::cout << "PASS "<<which<<" bound_write="<<(!bound.empty())<<
     " essential_authorized="<<shouldPass<<'\n';
}
