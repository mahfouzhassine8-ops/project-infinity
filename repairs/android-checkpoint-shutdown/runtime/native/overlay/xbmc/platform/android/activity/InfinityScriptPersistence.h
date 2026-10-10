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
  bool blockingFailure{false};
  std::string failure;
};
struct Blocker
{
  int writerId{-1};
  std::string writer;
  std::string reason;
  std::string detail;
  unsigned count{1};
  bool blocking{true};
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
  std::vector<Blocker> blockers;
  bool blockerOverflow{false};
  bool blockingOverflow{false};
  unsigned failedSettled{0};
  unsigned advisoryRetired{0};
  bool commitStarted{false};
  int failureWriterId{-1};
  std::string failureWriter;
  std::string failureDetail;
  bool commitFinished{false};
  bool committed{false};
  unsigned retired{0};
  std::set<int> retiredInvokers;
};
inline State& Get() { static State* state = new State; return *state; }
inline bool AdvisoryFailureReason(const std::string& reason)
{
  // These are runtime/operation diagnostics, not proof that state remains
  // dirty at checkpoint retirement. Finalization still must prove no pending
  // transaction, no unflushed handle and no unobserved persistence path.
  return reason=="uncaught_script_failure_before_persistence_receipt" ||
         reason=="sqlite_write_failed" ||
         reason=="sqlite_script_failed" ||
         reason=="sqlite_commit_failed" ||
         reason=="unraisable_python_cleanup_or_write_failure";
}
inline void AddBlockerLocked(State& s,int id,const std::string& writer,
                             const std::string& reason,const std::string& detail,
                             bool blocking=true)
{
  const auto safeWriter=writer.substr(0,512),safeReason=reason.substr(0,384),safeDetail=detail.substr(0,2048);
  for(auto& blocker:s.blockers)
    if(blocker.writerId==id && blocker.writer==safeWriter &&
       blocker.reason==safeReason && blocker.detail==safeDetail && blocker.blocking==blocking) {
      if(blocker.count<UINT_MAX)++blocker.count;
      return;
    }
  if(s.blockers.size()>=128){s.blockerOverflow=true;if(blocking)s.blockingOverflow=true;return;}
  s.blockers.push_back({id,safeWriter,safeReason,safeDetail,1,blocking});
}
inline bool HasBlockingBlockerLocked(const State& s)
{
  if(s.blockingOverflow)return true;
  for(const auto& blocker:s.blockers)if(blocker.blocking)return true;
  return false;
}
inline void Admit(int id, const std::string& name)
{
  auto& s=Get(); std::lock_guard<std::mutex> lock(s.mutex);
  if(s.commitStarted || s.totals.size()>=8192 || s.writers.size()>=512) {
    AddBlockerLocked(s,id,name,"script_writer_admission_after_seal_or_limit",{});
    if(s.failure.empty()){s.failure="python_writer:script_writer_admission_after_seal_or_limit";s.failureWriterId=id;s.failureWriter=name.substr(0,512);}
    return;
  }
  s.retiredInvokers.erase(id); // Reusing an ID starts a new retirement obligation.
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
inline void Fail(int id, const std::string& reason, const std::string& detail={})
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  auto found=s.writers.find(id);
  const bool blocking=!AdvisoryFailureReason(reason);
  if(found!=s.writers.end() && blocking) {
    found->second.blockingFailure=true;
    if(found->second.failure.empty())found->second.failure=reason;
  }
  std::string writer;
  if(found!=s.writers.end() && !found->second.admissions.empty())
    writer=found->second.admissions.begin()->first.substr(0,512);
  AddBlockerLocked(s,id,writer,reason,detail,blocking);
  if(blocking && s.failure.empty()) {
    s.failure="python_writer:"+reason;
    s.failureWriterId=id;
    s.failureDetail=detail.substr(0,2048);
    s.failureWriter=writer;
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
  if(s.commitStarted || s.paths.size()>=65536) {
    std::string writer;const auto found=s.writers.find(id);
    if(found!=s.writers.end()&&!found->second.admissions.empty())writer=found->second.admissions.begin()->first;
    AddBlockerLocked(s,id,writer,"file_mutation_after_seal_or_limit",absolute);
    if(s.failure.empty()){s.failure="python_writer:file_mutation_after_seal_or_limit";s.failureWriterId=id;s.failureWriter=writer;s.failureDetail=absolute.substr(0,2048);}
    return;
  }
  if(!s.writers.count(id)) {
    AddBlockerLocked(s,id,{},"file_mutation_without_admitted_writer",absolute);
    if(s.failure.empty()){s.failure="python_writer:file_mutation_without_admitted_writer";s.failureWriterId=id;s.failureDetail=absolute.substr(0,2048);}
    return;
  }
  s.paths[absolute]={present,directory};
}
inline void SQLiteCompanions(int id,const std::string& path)
{
  const auto absolute=Absolute(path);
  if(absolute.empty()){Fail(id,"unsupported_sqlite_companion_path");return;}
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  if(s.commitStarted || s.paths.size()>65534 || !s.writers.count(id)) {
    std::string writer;const auto found=s.writers.find(id);
    if(found!=s.writers.end()&&!found->second.admissions.empty())writer=found->second.admissions.begin()->first;
    AddBlockerLocked(s,id,writer,"sqlite_companion_after_seal_or_limit_or_without_writer",absolute);
    if(s.failure.empty()){s.failure="python_writer:sqlite_companion_after_seal_or_limit_or_without_writer";s.failureWriterId=id;s.failureWriter=writer;s.failureDetail=absolute.substr(0,2048);}
    return;
  }
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
  if(!found->second.observed)return;
  if(found->second.blockingFailure) {
    ++s.failedSettled;
    s.writers.erase(found); // Hard persistence uncertainty never receives a durable receipt.
    return;
  }
  bool hadAdvisory=false;
  for(const auto& blocker:s.blockers)
    if(!blocker.blocking && blocker.writerId==id){hadAdvisory=true;break;}
  if(hadAdvisory)++s.advisoryRetired;
  for(const auto& item:found->second.admissions)s.totals[item.first].second+=item.second;
  if(s.retiredInvokers.size()>=512){
    std::string writer;
    if(!found->second.admissions.empty())writer=found->second.admissions.begin()->first.substr(0,512);
    AddBlockerLocked(s,id,writer,"interpreter_retirement_receipt_limit",{});
    if(s.failure.empty()){s.failure="python_writer:interpreter_retirement_receipt_limit";s.failureWriterId=id;s.failureWriter=writer;}
    return;
  }
  s.retiredInvokers.insert(id);
  ++s.retired;s.writers.erase(found);
}
// Completion is per invocation. Another active invocation of the same script,
// or another writer's failure, cannot revoke THIS interpreter's actual proof.
// Global checkpoint acceptance still requires Failure(), all names and PollCommit.
inline bool AdvisoryInterpreterRetirement(int id, const std::string& reason)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  if(!s.retiredInvokers.count(id))return false;
  for(const auto& blocker:s.blockers)
    if(!blocker.blocking && blocker.writerId==id && blocker.reason==reason)return true;
  return false;
}
inline bool TakeInterpreterRetirement(int id)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  return s.retiredInvokers.erase(id)!=0;
}
inline bool DurableRetirement(const std::string& name)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  const auto found=s.totals.find(name);
  return found!=s.totals.end() && found->second.first==found->second.second;
}
inline bool BlockedRetirement(const std::string& name)
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  for(const auto& blocker:s.blockers)if(blocker.blocking && blocker.writer==name)return true;
  return false;
}
inline std::string Failure()
{auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);return s.failure;}
struct Evidence
{
  std::size_t active{0}, observed{0}, retired{0}, failedSettled{0}, advisoryRetired{0}, paths{0};
  std::size_t blockingCount{0}, advisoryCount{0};
  bool syncStarted{false}, syncFinished{false}, durable{false}, blockerOverflow{false}, blockingOverflow{false};
  std::string failure;
  int failureWriterId{-1};
  std::string failureWriter;
  std::string failureDetail;
  std::vector<std::string> pending;
  std::vector<Blocker> blockers;
};
inline Evidence Snapshot()
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);Evidence result;
  result.active=s.writers.size();result.retired=s.retired;result.failedSettled=s.failedSettled;
  result.advisoryRetired=s.advisoryRetired;result.paths=s.paths.size();
  result.syncStarted=s.commitStarted;result.syncFinished=s.commitFinished;
  result.failure=s.failure;result.failureWriterId=s.failureWriterId;result.failureWriter=s.failureWriter;
  result.failureDetail=s.failureDetail;result.blockers=s.blockers;result.blockerOverflow=s.blockerOverflow;
  result.blockingOverflow=s.blockingOverflow;
  for(const auto& blocker:s.blockers) {
    if(blocker.blocking)++result.blockingCount;else ++result.advisoryCount;
  }
  result.durable=s.committed && s.failure.empty() && result.blockingCount==0 && !result.blockingOverflow;
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
  if(!error.empty()) {
    AddBlockerLocked(s,-1,"python_services",error,{});
    if(s.failure.empty()) {
      s.failure=error;s.failureWriterId=-1;s.failureWriter="python_services";s.failureDetail.clear();
    }
  }
  s.committed=error.empty();s.commitFinished=true;
}
inline bool PollInventory()
{
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  if(!s.writers.empty())return false;
  if(!s.commitStarted) {
    s.commitStarted=true;
    if(s.paths.empty()) {s.commitFinished=true;s.committed=true;return true;}
    const auto paths=s.paths;
    try {std::thread([paths]{CommitWorker(paths);}).detach();}
    catch(...) {
      AddBlockerLocked(s,-1,"python_services","script_durability_worker_start_failed",{});
      if(s.failure.empty()) {s.failure="script_durability_worker_start_failed";s.failureWriter="python_services";}
      s.committed=false;s.commitFinished=true;
    }
  }
  return s.commitFinished;
}
inline bool PollCommit()
{
  if(!PollInventory())return false;
  auto& s=Get();std::lock_guard<std::mutex> lock(s.mutex);
  return s.committed && s.failure.empty() && !HasBlockingBlockerLocked(s);
}
} // namespace InfinityScriptPersistence
