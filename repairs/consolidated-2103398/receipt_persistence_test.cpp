// Actual durable helper: per-attempt names cannot use the two-message shortcut.
#include "platform/android/activity/InfinityCheckpointFile.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
using namespace infinity::checkpoint::files;
std::string read(const std::string& name)
{
  std::ifstream f(name);return {std::istreambuf_iterator<char>(f),{}};
}
int main(int argc,char** argv)
{
  assert(argc==2);const std::string root=std::string(argv[1])+"/.android-checkpoint";
  assert(mkdir(root.c_str(),0700)==0);
  const std::string failed=root+"/attempt-failed-one-CHECKPOINT_FAILED.json";
  const std::string safe=root+"/attempt-passed-two-SAFE_TO_TERMINATE.json";
  const auto old=SaveProtocolRecord(failed,"failed receipt");
  assert(!old.ok && old.error==EINVAL && old.stage==Stage::ValidatePath);
  const auto a=SaveDirty(failed,"failed receipt");
  const auto b=SaveDirty(safe,"safe receipt");
  assert(a.ok && b.ok && a.dataAndDirectorySynced && b.dataAndDirectorySynced);
  assert(read(failed)=="failed receipt" && read(safe)=="safe receipt");
  struct stat st{};assert(stat(failed.c_str(),&st)==0 && (st.st_mode&0777)==0600);
  const auto again=SaveDirty(failed,"failed receipt");assert(again.ok && again.dataAndDirectorySynced);
  const std::string link=root+"/attempt-symlink-CHECKPOINT_FAILED.json";
  assert(symlink(safe.c_str(),link.c_str())==0);
  assert(!SaveDirty(link,"must not replace protected target").ok);
  assert(read(safe)=="safe receipt" && read(failed)=="failed receipt");
  std::cout<<"original protocol shortcut rejected; both receipts durable and separate; symlink denied\n";
}
