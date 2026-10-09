#pragma once
// Native-owned admission, interpreter retirement and file durability are distinct
// proofs. Finishing an unknown script is NEVER itself a persistence receipt.
#include <algorithm>
#include <cerrno>
#include <climits>
#include <fcntl.h>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <sys/stat.h>
#include <thread>
#include <unistd.h>
#include <vector>

namespace InfinityScriptPersistence
{
struct Writer
{
  std::map<std::string, unsigned> admissions;
  bool observed{false};
  std::string failure;
};
struct Namespace
{
  bool present{true};
  bool directory{false};
  bool optional{false};
};
struct State
{
  std::mutex mutex;
  std::map<int, Writer> writers;
  std::map<std::string, std::pair<unsigned,unsigned>> totals;
  std::map<std::string, Namespace> paths;
  std::string failure;
  bool commitStarted{false};
  int failureWriterId{-1};
  std::string failureWriter;
  bool commitFinished{false};
  bool committed{false};
  unsigned retired{0};
};
inline State& Get() { static State* state = new State; return *state; }
inline void Admit(int id, const std::string& name)
{
  auto& s=Get(); std::lock_guard<std::mutex> lock(s.mutex);
  if(s.commitStarted || s.totals.size()>=8192 || s.writers.size()>=512)
  {s.failure="script_writer_admission_after_seal_or_limit";return;}
  ++s.writers[id].admissions[name]; ++s.totals[name].first;
}
inline bool Pending(int id)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);return s.writers.count(id)!=0;
}
inline void Observed(int id)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  const auto found=s.writers.find(id);if(found!=s.writers.end())found->second.observed=true;
}
inline void Fail(int id, const std::string& reason)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  auto found=s.writers.find(id);
  if(found!=s.writers.end() && found->second.failure.empty()) found->second.failure=reason;
  if(s.failure.empty()) {
    s.failure="python_writer:"+reason;
    s.failureWriterId=id;
    if(found!=s.writers.end() && !found->second.admissions.empty())
      s.failureWriter=found->second.admissions.begin()->first.substr(0,512);
  }
}
inline std::string Absolute(const std::string& input)
{
  if(input.empty() || input.find('\0')!=std::string::npos || input.find("://")!=std::string::npos)return {};
  std::string path=input;
  if(path.front()!='/') {char cwd[PATH_MAX];if(!::getcwd(cwd,sizeof(cwd)))return {};path=std::string(cwd)+"/"+path;}
  std::vector<std::string> parts;
  for(std::size_t start=1;start<=path.size();) {
    auto end=path.find('/',start);if(end==std::string::npos)end=path.size();
    auto part=path.substr(start,end-start);
    if(part=="..") {if(parts.empty())return {};parts.pop_back();}
    else if(!part.empty() && part!=".") parts.push_back(part);
    start=end+1;
  }
  std::string result;for(const auto& part:parts)result+="/"+part;return result.empty()?"/":result;
}
inline void Touch(int id,const std::string& path,bool present=true,bool directory=false)
{
  const auto absolute=Absolute(path);if(absolute.empty()){Fail(id,"unsupported_persistence_path");return;}
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  if(s.commitStarted || s.paths.size()>=65536){s.failure="file_mutation_after_seal_or_limit";return;}
  if(!s.writers.count(id)){s.failure="file_mutation_without_admitted_writer";return;}
  s.paths[absolute]={present,directory};
}
inline void SQLiteCompanions(int id,const std::string& path)
{
  const auto absolute=Absolute(path);
  if(absolute.empty()){Fail(id,"unsupported_sqlite_companion_path");return;}
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  if(s.commitStarted || s.paths.size()>65534 || !s.writers.count(id))
  {s.failure="sqlite_companion_after_seal_or_limit_or_without_writer";return;}
  for(const char* suffix:{"-wal","-journal"}) {
    const auto name=absolute+suffix;
    if(!s.paths.count(name))s.paths[name]={true,false,true};
  }
}
inline void Retired(int id)
{
  // Called ONLY after successful observer finalization, child-thread retirement
  // and actual Py_EndInterpreter. No Python callable can invoke this operation.
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  const auto found=s.writers.find(id);if(found==s.writers.end())return;
  if(!found->second.observed || !found->second.failure.empty())return;
  for(const auto& item:found->second.admissions)s.totals[item.first].second+=item.second;
  ++s.retired;s.writers.erase(found);
}
inline bool DurableRetirement(const std::string& name)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  const auto found=s.totals.find(name);
  return s.failure.empty() && found!=s.totals.end() && found->second.first==found->second.second;
}
inline std::string Failure()
{auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);return s.failure;}
struct Evidence
{
  std::size_t active{0}, observed{0}, retired{0}, paths{0};
  bool syncStarted{false}, syncFinished{false}, durable{false};
  std::string failure;
  int failureWriterId{-1};
  std::string failureWriter;
  std::vector<std::string> pending;
};
inline Evidence Snapshot()
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);Evidence result;
  result.active=s.writers.size();result.retired=s.retired;result.paths=s.paths.size();
  result.syncStarted=s.commitStarted;result.syncFinished=s.commitFinished;
  result.durable=s.committed && s.failure.empty();result.failure=s.failure;
  result.failureWriterId=s.failureWriterId;result.failureWriter=s.failureWriter;
  for(const auto& item:s.writers) {
    if(item.second.observed)++result.observed;
    for(const auto& admission:item.second.admissions)
      if(result.pending.size()<8)result.pending.push_back(admission.first);
  }
  return result;
}
inline bool SyncOne(const std::string& path, bool directory, std::string& error)
{
  // Parent directory aliases (e.g. Android external-files mounts) may resolve,
  // but a linked leaf never substitutes some other persistent file.
  struct stat info{};
  if(::lstat(path.c_str(),&info)!=0 || S_ISLNK(info.st_mode) ||
     (directory ? !S_ISDIR(info.st_mode) : !S_ISREG(info.st_mode)))
  {error="script_file_identity_or_type_unconfirmed";return false;}
  const int fd=::open(path.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW|(directory?O_DIRECTORY:0));
  if(fd<0){error="script_file_open_for_durability_failed";return false;}
  struct stat opened{};
  bool ok=::fstat(fd,&opened)==0 && opened.st_dev==info.st_dev && opened.st_ino==info.st_ino;
  if(ok) {int result;do {result=::fsync(fd);}while(result!=0 && errno==EINTR);ok=result==0;}
  if(::close(fd)!=0)ok=false;
  if(!ok)error="script_file_sync_or_identity_failed";
  return ok;
}
inline void CommitWorker(std::map<std::string,Namespace> paths)
{
  std::string error;std::set<std::string> directories;
  for(const auto& item:paths) {
    if(item.second.optional) {
      struct stat info{};
      if(::lstat(item.first.c_str(),&info)!=0 && errno==ENOENT)continue;
    }
    if(item.second.present && !SyncOne(item.first,item.second.directory,error))break;
    auto parent=item.first.substr(0,item.first.rfind('/'));if(parent.empty())parent="/";
    // Persist every changed namespace parent. New nested directories themselves
    // have separate mkdir audit entries, including their own parents.
    while(parent!="/") {
      struct stat info{};
      if(::lstat(parent.c_str(),&info)==0)break;
      const auto known=paths.find(parent);
      if(errno!=ENOENT || known==paths.end() || known->second.present)
      {error="script_namespace_parent_unconfirmed";break;}
      parent=parent.substr(0,parent.rfind('/'));if(parent.empty())parent="/";
    }
    if(!error.empty())break;
    directories.insert(parent);
  }
  if(error.empty())for(const auto& directory:directories)
    if(!SyncOne(directory,true,error))break;
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  if(!error.empty() && s.failure.empty())s.failure=error;
  s.committed=s.failure.empty();s.commitFinished=true;
}
inline bool PollCommit()
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  if(!s.failure.empty() || !s.writers.empty())return false;
  if(!s.commitStarted) {
    s.commitStarted=true;
    if(s.paths.empty()) {s.commitFinished=true;s.committed=true;return true;}
    const auto paths=s.paths;
    try {std::thread([paths]{CommitWorker(paths);}).detach();}
    catch(...) {s.failure="script_durability_worker_start_failed";s.commitFinished=true;}
  }
  return s.commitFinished && s.committed;
}
} // namespace InfinityScriptPersistence
