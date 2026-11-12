/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
#include "InfinityScriptPersistence.h"
#include <cstdint>
#include <cstdlib>
#include <signal.h>
#include <sstream>
#include <sys/sysmacros.h>

// Enforcement and durability for the existing native-owned persistence ledger.
// No process termination, Python finalization, join or escalation occurs here.
namespace InfinityScriptPersistence
{
inline thread_local int protectedWriteOwner{-1};
inline thread_local uint64_t protectedWriteToken{0};
inline int CurrentWriteOwner() { return protectedWriteOwner; }
// A NUL cannot name a POSIX file. A printable marker can: treating that
// filename as nonpersistent lets open(O_TRUNC) change it after sealing.
inline const std::string& NonPersistentTarget()
{ static const std::string target(1, '\0'); return target; }
inline bool Within(const std::string& path, const std::string& root)
{ return !root.empty() && (path == root || path.rfind(root + "/", 0) == 0); }

inline std::string ProtectedCanonical(const std::string& input)
{
  std::string path = Absolute(input), tail;
  if (path.empty()) return {};
  for (unsigned depth = 0; depth < 256; ++depth)
  {
    struct stat st{};
    if (::lstat(path.c_str(), &st) == 0)
    {
      if (S_ISLNK(st.st_mode) || (S_ISREG(st.st_mode) && st.st_nlink != 1)) return {};
      char resolved[PATH_MAX]{};
      if (!::realpath(path.c_str(), resolved)) return {};
      return std::string(resolved) + tail;
    }
    if (errno != ENOENT) return {};
    const auto slash = path.rfind('/');
    if (slash == std::string::npos || slash == 0) return {};
    tail = path.substr(slash) + tail;
    path.resize(slash);
  }
  return {};
}

// A VFS write error is path-scoped only when the native ledger holds the
// matching, live, same-thread writer lease. Python-supplied paths and add-on IDs
// alone NEVER establish optionality. This check works before Close is requested:
// the optionality decision occurs later under the actual protected profile map.
inline std::string VerifiedVfsWriteFailureTarget(int writer,
                                                  const std::string& operation,
                                                  const std::string& raw)
{
  if (operation != "vfs.write" || raw.empty() || raw.front() != '/')
    return {};
  const auto canonical = ProtectedCanonical(raw);
  if (canonical.empty()) return {};
  auto& state = Get();
  std::lock_guard<std::mutex> lock(state.mutex);
  if (!state.writers.count(writer)) return {};
  for (const auto& entry : state.protection.operations)
  {
    const auto& live = entry.second;
    if (live.writer != writer || live.operation != operation ||
        live.thread != std::this_thread::get_id() ||
        live.paths.size() != 1) continue;
    const auto leasePath = ProtectedCanonical(live.paths.front());
    if (leasePath == canonical) return canonical;
  }
  return {};
}

inline bool OptionalBasePathLocked(const WriteProtection& p, const std::string& raw)
{
  if (raw == NonPersistentTarget()) return true;
  const auto path = ProtectedCanonical(raw);
  if (path.empty()) return false;
  for (const auto& cache : p.caches) if (Within(path, cache)) return true;
  // An add-on identity or private profile folder does not prove that
  // databases/history/provider state are recoverable. Only the
  // coordinator's explicit cache roots may be optional.
  return false;
}
inline bool OptionalPathLocked(const WriteProtection& p, const std::string& raw)
{
  if (!OptionalBasePathLocked(p, raw)) return false;
  std::set<std::string> visited;
  std::vector<std::string> pending{raw};
  while (!pending.empty())
  {
    const auto path = pending.back(); pending.pop_back();
    if (!visited.insert(path).second) continue;
    if (visited.size() > 4096 || !OptionalBasePathLocked(p, path)) return false;
    for (const auto& pair : p.aliases)
    {
      if (Within(path, pair.first)) pending.push_back(pair.second + path.substr(pair.first.size()));
      if (Within(path, pair.second)) pending.push_back(pair.first + path.substr(pair.second.size()));
    }
  }
  return true;
}
inline bool ProtectedLocked(const WriteProtection& p, const ProtectedResource& resource)
{
  if (resource.paths.empty()) return true;
  for (const auto& path : resource.paths) if (!OptionalPathLocked(p, path)) return true;
  return false;
}
inline void ProtectionFailureLocked(WriteProtection& p, const std::string& reason)
{
  if (p.failures.size() < 128 && std::find(p.failures.begin(), p.failures.end(), reason) == p.failures.end())
    p.failures.push_back(reason.substr(0, 2048));
}
inline void ProtectionFailure(const std::string& reason)
{ auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); ProtectionFailureLocked(s.protection, reason); }
inline void RegisterParticipant(int id)
{ auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); s.protection.participants.insert(id); }
inline bool WriteProtectionActive()
{ auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); return s.protection.phase != 0; }

// Audit-only capabilities have no bounded completion callback. They may run
// normally before Close, but cannot be admitted during a checkpoint. A prior
// capability is retained as a real blocker by the existing writer ledger.
inline bool RejectOpaqueMutation(const std::string& operation)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  if (!s.protection.phase) return false;
  ++s.protection.denied;
  if (s.protection.denials.size() < 128) s.protection.denials.push_back(operation);
  return true;
}
inline void InvalidateDescriptor(int descriptor, uint64_t except = 0)
{
  if (descriptor < 0) return;
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  // A lease resolved before dup2/close cannot keep its old optional identity.
  // It becomes an essential uncertainty until the actual operation returns.
  for (auto& item : s.protection.operations)
    if (item.first != except && item.second.descriptor == descriptor) item.second.paths.clear();
}
inline void InvalidateDescriptorRange(int first, int last)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  for (auto& item : s.protection.operations)
    if (item.second.descriptor >= first && item.second.descriptor < last) item.second.paths.clear();
}
inline void RememberAlias(const std::string& from, const std::string& to)
{
  if (from == NonPersistentTarget() || to == NonPersistentTarget()) return;
  const auto source = Absolute(from), target = Absolute(to);
  if (source.empty() || target.empty() || source == target) return;
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); auto& p = s.protection;
  if (p.aliases.size() >= 65536)
  { ProtectionFailureLocked(p,"protected_namespace_alias_inventory_exhausted"); return; }
  p.aliases.emplace(source, target);
  p.paths.insert(source); p.paths.insert(target);
}

// Bounded provenance for absence evidence. Diagnostics cannot grant permission,
// manufacture removal proof, or change the native operation's result.
inline std::string NamespaceLease(const State& state, const ProtectedResource& resource)
{
  std::ostringstream out;
  out << "operation=" << resource.operation << ";writer_id=" << resource.writer
      << ";thread=" << resource.thread;
  const auto writer=state.writers.find(resource.writer);
  if(writer!=state.writers.end())
    for(const auto& invocation:writer->second.admissions)
      out << ";invocation=" << invocation.first;
  return out.str().substr(0,768);
}
inline void NamespaceEvidenceLocked(WriteProtection& protection,
                                    const std::string& path, const std::string& detail)
{
  if(protection.namespaceEvidence.size()>=65536 && !protection.namespaceEvidence.count(path))
  { ProtectionFailureLocked(protection,"namespace_evidence_inventory_exhausted");return; }
  protection.namespaceEvidence[path]=detail.substr(0,1024);
}
inline std::string NamespaceFailureEvidence(const std::string& path,int error)
{
  auto& state=Get();std::lock_guard<std::mutex> lock(state.mutex);
  std::ostringstream out;out << ";errno=" << error;
  std::string current=path;
  for(unsigned depth=0;depth<256 && out.str().size()<1400;++depth)
  {
    const auto evidence=state.protection.namespaceEvidence.find(current);
    if(evidence!=state.protection.namespaceEvidence.end())
      out << ";namespace=" << current << ";absence_verified="
          << state.protection.removedNamespaces.count(current) << ";" << evidence->second;
    const auto slash=current.rfind('/');if(slash==std::string::npos || !slash)break;
    current.resize(slash);
  }
  return out.str().substr(0,1700);
}

inline uint64_t BeginProtectedOperation(int id, const std::vector<std::string>& paths,
                                       const std::string& operation, bool nativeSave = false,
                                       bool existingTransaction = false, int descriptor = -1,
                                       NamespaceEffect effect = NamespaceEffect::MAY_MUTATE)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  auto& p = s.protection;
  ProtectedResource resource{id, paths, operation};
  resource.descriptor = descriptor;
  resource.namespaceEffect = effect;
  bool bufferDrain = false;
  const bool flushing = operation == "flush" || operation == "close" ||
      (operation.size() >= 6 && operation.compare(operation.size()-6, 6, ".flush") == 0) ||
      (operation.size() >= 6 && operation.compare(operation.size()-6, 6, ".close") == 0);
  for (const auto& item : p.buffers)
    if (flushing && item.second.writer == id && item.second.paths == paths) bufferDrain = true;
  for (const auto& item : p.operations)
    if (item.second.writer == id && item.second.thread == std::this_thread::get_id() &&
        item.second.paths == paths && (item.second.operation == "flush" || item.second.operation == "close" ||
        item.second.operation.find(".flush") != std::string::npos || item.second.operation.find(".close") != std::string::npos))
      bufferDrain = true;
  const bool persistent = paths.empty() || std::any_of(paths.begin(), paths.end(),
      [](const std::string& path) { return path != NonPersistentTarget(); });
  if (p.phase && (ProtectedLocked(p, resource) || (p.phase == 3 && persistent)))
  {
    const bool permitted = p.phase < 3 &&
        (existingTransaction || bufferDrain || nativeSave ||
         (p.phase == 1 && (id < 0 || p.participants.count(id))));
    if (!permitted)
    {
      ++p.denied;
      if (p.denials.size() < 128) p.denials.push_back(operation + ":" + (paths.empty() ? "unknown" : paths.front()));
      errno = EROFS; return 0;
    }
  }
  if (p.operations.size() >= 65536 || p.paths.size() >= 65536)
  {
    ProtectionFailureLocked(p, "protected_operation_inventory_exhausted");
    // Never silently grant an untracked mutation, even while running.
    errno = ENOSPC; return 0;
  }
  // Coordination barriers retain admission and pending-owner protection.
  // Their actual effects are observed by nested native leases and audit
  // contracts; the barrier itself cannot invalidate a removed name.
  // Unclassified operations still use MAY_MUTATE and fail closed.
  if (effect == NamespaceEffect::MAY_MUTATE) {
  // Any later admitted operation that overlaps a removed name revokes
  // its earlier absence evidence, even when the new operation fails.
  if (paths.empty()) {
    for(const auto& removed:p.removedNamespaces)
      NamespaceEvidenceLocked(p,removed,"revoked_unknown_target;"+NamespaceLease(s,resource));
    p.removedNamespaces.clear();
  }
  // mkdir creates an empty directory (or fails without adding descendants);
  // rmdir removes an empty directory. Neither can recreate an absent child.
  // Exact/ancestor identities are still invalidated below.
  bool preservesRemovedDescendants = operation == "rmdir" || operation == "namespace.rmdir" ||
      operation == "mkdir" || operation == "namespace.mkdir";
  if (operation == "converted_native_write_target") {
    const auto parent=p.operations.find(protectedWriteToken);
    preservesRemovedDescendants=parent!=p.operations.end() && parent->second.writer==id &&
        parent->second.thread==std::this_thread::get_id() &&
        (parent->second.operation=="rmdir" || parent->second.operation=="namespace.rmdir" ||
         parent->second.operation=="mkdir" || parent->second.operation=="namespace.mkdir");
  }
  for (const auto& raw : paths) {
    if (raw == NonPersistentTarget()) continue;
    const auto path = Absolute(raw);
    for (auto it=p.removedNamespaces.begin(); it!=p.removedNamespaces.end();)
      if (path.empty() || Within(path,*it) || (!preservesRemovedDescendants && Within(*it,path))) {
        NamespaceEvidenceLocked(p,*it,"revoked_overlap;target="+path+";"+NamespaceLease(s,resource));
        it=p.removedNamespaces.erase(it);
      }
      else ++it;
  }
  }
  const auto token = ++p.nextOperation;
  p.operations.emplace(token, resource);
  for (const auto& path : paths)
  {
    if (path == NonPersistentTarget()) continue;
    const auto absolute = Absolute(path);
    if (absolute.empty()) ProtectionFailureLocked(p, "protected_path_identity_unconfirmed:" + operation);
    else { p.paths.insert(absolute); p.writerPaths[id].insert(absolute); }
  }
  return token;
}
inline void EndProtectedOperation(uint64_t token)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  if (!token || s.protection.operations.erase(token) != 1)
    ProtectionFailureLocked(s.protection, "protected_operation_ownership_mismatch");
}
enum class ChildState { LIVE, DEAD, UNKNOWN };
inline ChildState ProtectedChildState(int pid, uint64_t& identity)
{
  if (pid <= 0) return ChildState::UNKNOWN;
  const auto path = "/proc/" + std::to_string(pid) + "/stat";
  const int fd = ::open(path.c_str(), O_RDONLY | O_CLOEXEC);
  if (fd < 0)
    return ::kill(pid, 0) < 0 && errno == ESRCH ? ChildState::DEAD : ChildState::UNKNOWN;
  char bytes[4096]{};
  const auto count = ::read(fd, bytes, sizeof(bytes)-1);
  ::close(fd);
  if (count <= 0) return ChildState::UNKNOWN;
  const std::string stat(bytes, static_cast<size_t>(count));
  const auto end = stat.rfind(')');
  if (end == std::string::npos) return ChildState::UNKNOWN;
  std::istringstream fields(stat.substr(end+1));
  std::string field;
  char state = 0;
  uint64_t started = 0;
  for (unsigned index = 3; index <= 22; ++index)
  {
    if (!(fields >> field)) return ChildState::UNKNOWN;
    if (index == 3 && field.size() == 1) state = field[0];
    if (index == 22)
    {
      if (field.empty() || field.find_first_not_of("0123456789") != std::string::npos)
        return ChildState::UNKNOWN;
      errno = 0; started = std::strtoull(field.c_str(), nullptr, 10);
      if (errno || !started) return ChildState::UNKNOWN;
    }
  }
  if (identity && identity != started) return ChildState::DEAD;
  identity = started;
  if (state == 'Z' || state == 'X') return ChildState::DEAD;
  return state ? ChildState::LIVE : ChildState::UNKNOWN;
}
inline void RefreshProtectedChildrenLocked(State& s);
inline void BindProtectedChild(uint64_t token, int pid)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  RefreshProtectedChildrenLocked(s);
  auto& p = s.protection;
  const auto resource = p.operations.find(token);
  if (resource == p.operations.end() || pid <= 0)
  { ProtectionFailureLocked(p, "native_child_output_ownership_unconfirmed"); return; }
  // fork has copied the descriptor table. Parent closes/dup2 must no longer
  // retarget a child's operation; earlier invalidations remain conservative.
  resource->second.descriptor = -1;
  resource->second.operation = "native_child_output:pid=" + std::to_string(pid);
  uint64_t identity = 0;
  if (ProtectedChildState(pid, identity) == ChildState::DEAD)
    p.operations.erase(resource);
  else p.childOperations.emplace(token, std::make_pair(pid, identity));
}
inline void RefreshProtectedChildrenLocked(State& s)
{
  // Observation inside the existing barrier only: no worker, watchdog, join,
  // waitpid reaping, timeout extension, or optional-retirement dependency.
  auto& p = s.protection;
  for (auto child = p.childOperations.begin(); child != p.childOperations.end();)
  {
    if (ProtectedChildState(child->second.first, child->second.second) == ChildState::DEAD)
    { p.operations.erase(child->first); child = p.childOperations.erase(child); }
    else ++child;
  }
}
inline void RecordProtectedResult(uint64_t token, const std::string& path)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  const auto found = s.protection.operations.find(token);
  if (found == s.protection.operations.end() || path.empty())
  { ProtectionFailureLocked(s.protection, "completed_native_write_target_unconfirmed"); return; }
  found->second.paths.push_back(path);
  if (path != NonPersistentTarget())
  {
    s.protection.paths.insert(path);
    s.protection.writerPaths[found->second.writer].insert(path);
  }
}
inline void RequireProtectedIdentity(uint64_t token)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  const auto found = s.protection.operations.find(token);
  if (found == s.protection.operations.end() || found->second.paths.empty())
    ProtectionFailureLocked(s.protection, "completed_native_write_target_unconfirmed");
}
inline bool ProtectActualTargets(uint64_t owner, const std::vector<std::string>& paths)
{
  int writer = -1;
  {
    auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
    const auto found = s.protection.operations.find(owner);
    if (found == s.protection.operations.end()) return false;
    writer = found->second.writer;
  }
  // The audit event supplies CPython's converted arguments, immediately before
  // the syscall. Keep this child lease live until its identities are attached
  // to the original operation, so a changing PathLike cannot hide the target.
  const auto child = BeginProtectedOperation(writer, paths, "converted_native_write_target");
  if (!child) return false;
  {
    auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
    auto& resource = s.protection.operations.at(owner);
    resource.paths.insert(resource.paths.end(), paths.begin(), paths.end());
    resource.actualPaths=paths; // Converted arguments from the real native audit event.
  }
  EndProtectedOperation(child);
  return true;
}
class ProtectedOperation
{
public:
  ProtectedOperation(int writer, const std::vector<std::string>& paths, const char* operation,
                     bool nativeSave = false, bool existingTransaction = false, int descriptor = -1,
                     NamespaceEffect effect = NamespaceEffect::MAY_MUTATE)
    : m_token(BeginProtectedOperation(writer, paths, operation, nativeSave, existingTransaction, descriptor, effect)) {}
  ~ProtectedOperation() { if (m_token) EndProtectedOperation(m_token); }
  explicit operator bool() const { return m_token != 0; }
  ProtectedOperation(const ProtectedOperation&) = delete;
  ProtectedOperation& operator=(const ProtectedOperation&) = delete;
private:
  uint64_t m_token;
};

// A procfs " (deleted)" annotation is not itself namespace evidence. FUSE can
// retain it on a live descriptor whose original named file still has one link.
// Resolve it only by proving the live descriptor and a no-follow opened name
// identify the same object. Never guess from the spelling or an add-on name.
inline bool SameDescriptorObject(const struct stat& a,const struct stat& b)
{
  return a.st_dev==b.st_dev && a.st_ino==b.st_ino && a.st_mode==b.st_mode &&
      a.st_uid==b.st_uid && a.st_gid==b.st_gid && a.st_nlink==b.st_nlink;
}
inline bool VerifiedDescriptorName(int descriptor,const struct stat& original,
                                   const std::string& path)
{
  if(path.empty() || path.front()!='/' || ProtectedCanonical(path)!=path)return false;
  struct stat named{},opened{},current{};
  if(::lstat(path.c_str(),&named)!=0 || S_ISLNK(named.st_mode) ||
     !SameDescriptorObject(original,named))return false;
  if((S_ISREG(named.st_mode) && named.st_nlink!=1) ||
     (!S_ISREG(named.st_mode) && !S_ISDIR(named.st_mode)))return false;
  // A second ordinary descriptor's close would release this process's POSIX
  // record locks on the inode. O_PATH inspects identity without that effect.
  // It still requires the same no-follow metadata and live-fd checks below.
  const int probe=::open(path.c_str(),O_PATH|O_CLOEXEC|O_NOFOLLOW|
      (S_ISDIR(named.st_mode)?O_DIRECTORY:0));
  if(probe<0)return false;
  const bool matched=::fstat(probe,&opened)==0 && SameDescriptorObject(original,opened) &&
      ::fstat(descriptor,&current)==0 && SameDescriptorObject(original,current);
  const int closed=::close(probe);
  return matched && closed==0;
}
inline std::string VerifiedDescriptorLink(int descriptor,const std::string& reported)
{
  static const std::string suffix=" (deleted)";
  if(reported.size()<=suffix.size() ||
      reported.compare(reported.size()-suffix.size(),suffix.size(),suffix)!=0)return reported;
  const int savedErrno=errno;
  std::string result=reported;
  struct stat original{};
  if(::fstat(descriptor,&original)==0 && original.st_nlink>0 &&
      (S_ISREG(original.st_mode) || S_ISDIR(original.st_mode)))
  {
    // A real filename can end in this suffix. Preserve it when it names the fd.
    const auto candidate=reported.substr(0,reported.size()-suffix.size());
    if(!VerifiedDescriptorName(descriptor,original,reported) &&
        VerifiedDescriptorName(descriptor,original,candidate))result=candidate;
  }
  errno=savedErrno;
  return result;
}

inline bool VerifiedBufferNamespaceTransition(int writer,const std::string& key,
    int descriptor,const std::vector<std::string>& paths,std::string& unresolved)
{
  if(paths.size()!=1 || paths.front()!=NonPersistentTarget())return true;
  auto& state=Get();std::lock_guard<std::mutex> lock(state.mutex);
  const auto found=state.protection.buffers.find(std::to_string(writer)+":"+key);
  if(found==state.protection.buffers.end())return true;
  const int savedErrno=errno;
  struct stat actual{};
  const bool unlinked=descriptor>=0 && ::fstat(descriptor,&actual)==0 &&
      S_ISREG(actual.st_mode) && actual.st_nlink==0;
  errno=savedErrno;
  if(found->second.paths.empty()){unresolved="<unresolved>";return false;}
  for(const auto& previous:found->second.paths)
    if(previous!=NonPersistentTarget() &&
        (!unlinked || !state.protection.removedNamespaces.count(Absolute(previous))))
    {unresolved=previous;return false;}
  return true;
}

inline std::string DescriptorPath(int fd)
{
  struct stat st{};
  if (::fstat(fd, &st) != 0) return {};
  if (!S_ISREG(st.st_mode) && !S_ISDIR(st.st_mode)) return NonPersistentTarget();
  if (!st.st_nlink) return NonPersistentTarget();
  char target[PATH_MAX]{};
  const auto name = "/proc/self/fd/" + std::to_string(fd);
  const auto size = ::readlink(name.c_str(), target, sizeof(target) - 1);
  if (size <= 0 || size >= static_cast<ssize_t>(sizeof(target) - 1)) return {};
  target[size] = '\0'; return VerifiedDescriptorLink(fd,target);
}
inline void SetProtectedBuffer(int writer, const std::string& key,
                               const std::vector<std::string>& paths, bool dirty)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); auto& p = s.protection;
  const auto identity = std::to_string(writer) + ":" + key;
  if (!dirty) { p.buffers.erase(identity); return; }
  if (p.buffers.size() >= 65536) { ProtectionFailureLocked(p, "protected_buffer_inventory_exhausted"); return; }
  p.buffers[identity] = {writer, paths, "buffered_write"};
}
inline void SetProtectedTransaction(const std::string& key, const std::string& path, bool active,
                                    const char* operation = "sqlite_write_transaction")
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); auto& p = s.protection;
  if (!active) { p.transactions.erase(key); return; }
  if (p.transactions.size() >= 65536) { ProtectionFailureLocked(p, "protected_transaction_inventory_exhausted"); return; }
  // Capture the actual native lease owner, including Python child threads.
  p.transactions[key] = {CurrentWriteOwner(), {path}, operation};
}
inline bool HasProtectedTransaction(const std::string& path)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  for (const auto& item : s.protection.transactions)
    for (const auto& target : item.second.paths) if (target == path) return true;
  return false;
}
inline bool BeginWriteProtection(uint64_t generation, const std::vector<std::string>& profiles,
                                 const std::vector<std::string>& caches)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); auto& p = s.protection;
  if (!generation || p.generation || profiles.empty()) return false;
  for (const auto& root : profiles)
  {
    const auto path = ProtectedCanonical(root);
    if (path.empty()) { ProtectionFailureLocked(p, "protected_profile_root_unconfirmed"); return false; }
    p.profiles.push_back(path);
  }
  for (const auto& root : caches)
  {
    const auto path = ProtectedCanonical(root);
    if (path.empty()) continue;
    for (const auto& profile : p.profiles)
      if (Within(profile, path)) { ProtectionFailureLocked(p, "cache_overlaps_protected_profile"); return false; }
    p.caches.push_back(path);
  }
  p.generation = generation; p.phase = 1; return true;
}
inline bool CloseParticipantWrites(uint64_t generation)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); auto& p = s.protection;
  if (p.generation != generation || p.phase != 1) return false;
  p.phase = 2; return true;
}
struct EssentialWriteProof
{
  uint64_t generation{0}, denied{0};
  unsigned phase{0};
  bool durable{false};
  std::vector<std::string> blockers;
};
inline std::string ResourceOwnerLocked(const State& s, const ProtectedResource& r)
{
  std::ostringstream out;
  out << ";writer_id=" << r.writer << ";thread=" << r.thread
      << ";checkpoint_generation=" << s.protection.generation << ";phase=" << s.protection.phase;
  for(const auto& path:r.paths)out << ";target=" << (path.empty()?"<unresolved>":path.substr(0,768));
  const auto writer=s.writers.find(r.writer);
  if (writer!=s.writers.end()) {
    out << ";interpreter=" << writer->second.initialization.interpreterIdentity;
    for (const auto& name:writer->second.admissions) out << ";invocation=" << name.first;
  }
  return out.str();
}
inline EssentialWriteProof EssentialWritesLocked(State& s)
{
  RefreshProtectedChildrenLocked(s);
  const auto& p = s.protection;
  EssentialWriteProof proof{p.generation, p.denied, p.phase, p.durable, p.failures};
  for (const auto& writer : s.writers)
    if (!writer.second.observed) proof.blockers.push_back("unobserved_python_writer:" + std::to_string(writer.first));
  for (const auto& blocker : s.blockers)
  {
    if (!blocker.blocking) continue;
    // Only failures with bounded, inventoried file/transaction effects can be
    // waived as optional private data. Opaque/native capabilities remain fatal.
    const auto& reason = blocker.reason;
    const bool bounded = reason == "sqlite_pending_transaction_at_retirement" ||
        reason == "sqlite_closed_with_pending_transaction" ||
        reason == "sqlite_collected_with_pending_transaction" ||
        reason == "buffer_flush_before_retirement_failed" ||
        reason == "buffered_write_failed" || reason == "buffer_flush_failed" ||
        reason == "buffer_close_failed" || reason == "raw_buffer_write_failed" ||
        reason == "raw_buffer_close_failed" || reason == "layered_buffer_write_failed" ||
        reason == "layered_buffer_flush_failed" || reason == "layered_buffer_close_failed";
    bool privateOnly = bounded;
    const auto paths = p.writerPaths.find(blocker.writerId);
    if (paths == p.writerPaths.end() || paths->second.empty()) privateOnly = false;
    else for (const auto& path : paths->second) if (!OptionalPathLocked(p, path)) privateOnly = false;
    // Only exact VFS WRITE outcomes can inherit their own verified target.
    // A failed optional write is not an essential save receipt. Recheck
    // canonical path, aliases, required-participant classification and genuine
    // tracked mutation under the FINAL trusted profile roots. Every other
    // failure remains unchanged, and the independently tracked operations,
    // unflushed buffers, and SQLite transactions below still block Close.
    if (!privateOnly &&
        (reason == "vfs_write_exception" || reason == "vfs_write_failed") &&
        !blocker.verifiedWriteTarget.empty() &&
        !p.participants.count(blocker.writerId) &&
        OptionalPathLocked(p, blocker.verifiedWriteTarget) &&
        paths != p.writerPaths.end())
    {
      bool allWriterPathsOptional = true;
      bool targetWasInventoried = false;
      for (const auto& written : paths->second)
      {
        // A writer that ALSO touched an essential/unknown path must not
        // assert the failed native VFS handle could affect optional data
        // only. This protects against mutable Python handle attributes.
        if (!OptionalPathLocked(p, written))
        {
          allWriterPathsOptional = false;
          break;
        }
        if (ProtectedCanonical(written) == blocker.verifiedWriteTarget)
          targetWasInventoried = true;
      }
      privateOnly = allWriterPathsOptional && targetWasInventoried;
    }
    if (!privateOnly) proof.blockers.push_back("unverified_protected_writer:" + blocker.writer + ":" + reason);
  }
  if (s.blockingOverflow) proof.blockers.push_back("protected_writer_failure_inventory_overflow");
  for (const auto& entry : p.operations)
    if (ProtectedLocked(p, entry.second)) proof.blockers.push_back("active_protected_operation:" + entry.second.operation + ";operation_id=" + std::to_string(entry.first) + ResourceOwnerLocked(s,entry.second));
  for (const auto& entry : p.buffers)
    if (ProtectedLocked(p, entry.second)) proof.blockers.push_back("unflushed_protected_buffer:" + entry.first + ResourceOwnerLocked(s,entry.second));
  for (const auto& entry : p.transactions)
    if (ProtectedLocked(p, entry.second)) proof.blockers.push_back("pending_protected_" + entry.second.operation + ":" + entry.first + ResourceOwnerLocked(s,entry.second));
  return proof;
}
inline EssentialWriteProof EssentialWrites()
{ auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); return EssentialWritesLocked(s); }

inline size_t ActiveProtectedResources()
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  RefreshProtectedChildrenLocked(s);
  size_t count = 0;
  for (const auto* resources : {&s.protection.buffers, &s.protection.transactions})
    for (const auto& entry : *resources) if (ProtectedLocked(s.protection,entry.second)) ++count;
  for (const auto& entry : s.protection.operations)
    if (ProtectedLocked(s.protection,entry.second)) ++count;
  return count;
}

inline size_t OptionalUnfinishedWriters()
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  size_t count = 0;
  for (const auto& writer : s.writers) if (!s.protection.participants.count(writer.first)) ++count;
  return count;
}

// A completed/rolled-back add-on installation can remove the entire UUID
// staging tree before final Close. The original proof fsyncs its *immediate*
// parent, which fails ENOENT if the installer removed that UUID parent too.
// Only resolve that specific case; do NOT allow a missing database/profile or
// arbitrary add-on path to inherit a missing-ancestor waiver.
inline bool InstallerStageRoot(const std::string& path,
                               const std::vector<std::string>& profiles,
                               std::string& stageRoot)
{
  for (const auto& profile : profiles)
  {
    const std::string marker = "/.kodi/userdata";
    const auto markerAt = profile.find(marker);
    if (markerAt == std::string::npos) continue;
    if (profile.size() > markerAt + marker.size() &&
        profile[markerAt + marker.size()] != '/') continue;
    const auto root = profile.substr(0, markerAt) + "/.kodi/addons/temp";
    if (!Within(path, root) || path.size() <= root.size() + 1) continue;
    const auto tail = path.substr(root.size() + 1);
    // The native Kodi installer uses a UUID-named scratch directory.
    // Do not classify arbitrary "addons/temp" or active named add-ons.
    if (tail.size() <= 37 || tail[36] != '/') continue;
    bool validUuid = true;
    for (size_t i = 0; i < 36; ++i)
    {
      const char c = tail[i];
      const bool hyphen = i == 8 || i == 13 || i == 18 || i == 23;
      const bool hex = (c >= '0' && c <= '9') ||
                       (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
      if ((hyphen && c != '-') || (!hyphen && !hex))
        { validUuid = false; break; }
    }
    if (!validUuid) continue;
    const auto remaining = tail.substr(37);
    if (remaining.empty()) continue;
    bool validComponents = true;
    size_t at = 0;
    while (at < remaining.size())
    {
      const auto slash = remaining.find('/', at);
      const auto part = remaining.substr(at, slash == std::string::npos ?
                                             std::string::npos : slash - at);
      if (part.empty() || part == "." || part == "..")
        { validComponents = false; break; }
      if (slash == std::string::npos) break;
      at = slash + 1;
    }
    if (!validComponents || remaining.back() == '/') continue;
    stageRoot = root;
    return true;
  }
  return false;
}

// There is nothing left to fsync at the vanished staging leaf. Prove the
// namespace deletion by fsync of the first surviving directory, without
// crossing above the trusted installer staging root. Existing files, link
// attacks, permission errors and all essential data paths remain fail-closed.
inline bool SyncRemovedInstallerStage(const std::string& missingParent,
                                      const std::string& path,
                                      const std::vector<std::string>& profiles)
{
  std::string stageRoot;
  if (!InstallerStageRoot(path, profiles, stageRoot)) return false;
  std::string current = missingParent;
  for (unsigned depth = 0; depth < 256; ++depth)
  {
    if (!Within(current, stageRoot)) return false;
    struct stat observed{};
    if (::lstat(current.c_str(), &observed) == 0)
    {
      if (!S_ISDIR(observed.st_mode) || S_ISLNK(observed.st_mode)) return false;
      const int fd = ::open(current.c_str(),
                            O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
      if (fd < 0) return false;
      struct stat verified{};
      const bool sameDirectory = ::fstat(fd, &verified) == 0 &&
          S_ISDIR(verified.st_mode) &&
          observed.st_dev == verified.st_dev && observed.st_ino == verified.st_ino;
      int rc = -1;
      if (sameDirectory)
        do { rc = ::fsync(fd); } while (rc < 0 && errno == EINTR);
      const int closed = ::close(fd);
      return sameDirectory && rc == 0 && closed == 0;
    }
    if (errno != ENOENT || current == stageRoot) return false;
    const auto slash = current.rfind('/');
    if (slash == std::string::npos || slash == 0) return false;
    current.resize(slash);
  }
  return false;
}

// Called only after a successful native namespace operation, while its exact
// writer/thread lease is still active. This is absence evidence, not fsync proof.
inline void RecordRemovedNamespace(uint64_t token)
{
  auto& state = Get();
  std::lock_guard<std::mutex> lock(state.mutex);
  const auto found = state.protection.operations.find(token);
  if (found == state.protection.operations.end() ||
      found->second.thread != std::this_thread::get_id() ||
      found->second.actualPaths.empty()) return;
  const auto& raw=found->second.actualPaths.front();
  const auto path=Absolute(raw);
  const auto& operation = found->second.operation;
  if (operation != "rename" && operation != "replace" && operation != "remove" &&
      operation != "unlink" && operation != "rmdir") return;
  // Inspect and record under the admission mutex. A new mutator cannot finish
  // between the absence check and insertion; an already admitted overlapping
  // mutator remains visible below until it ends under the same mutex.
  const auto canonical=ProtectedCanonical(path);
  std::string rejection;
  if (path.empty() || path != raw || canonical != path)
    rejection="removal_identity_unverified;canonical="+canonical;
  struct stat st{};
  if(rejection.empty())
  {
    const int result=::lstat(path.c_str(),&st),error=errno;
    if(result==0 || error!=ENOENT)
      rejection="removal_absence_unverified;lstat="+std::to_string(result)+";errno="+std::to_string(error);
  }
  if(!rejection.empty())
  { NamespaceEvidenceLocked(state.protection,path,rejection+";"+NamespaceLease(state,found->second));return; }
  for (const auto& live : state.protection.operations)
    if (live.second.thread != found->second.thread &&
        live.second.namespaceEffect == NamespaceEffect::MAY_MUTATE)
    {
      if (live.second.paths.empty())
      { NamespaceEvidenceLocked(state.protection,path,"concurrent_unknown_target;"+NamespaceLease(state,live.second));return; }
      for (const auto& target : live.second.paths)
        if (target.empty() || Within(target,path) || Within(path,target))
        { NamespaceEvidenceLocked(state.protection,path,"concurrent_overlap;target="+target+";"+NamespaceLease(state,live.second));return; }
    }
  if (state.protection.removedNamespaces.size() >= 65536)
  { ProtectionFailureLocked(state.protection,"removed_namespace_inventory_exhausted"); return; }
  state.protection.removedNamespaces.insert(path);
  NamespaceEvidenceLocked(state.protection,path,"observed_absent;"+NamespaceLease(state,found->second));
}

// A vanished parent may be traversed only when every absent component has its
// own completed native removal/rename evidence. The first surviving directory
// is opened without following a final symlink, identity checked and fsynced.
// Unknown disappearance, a changed alias or an I/O failure remains a blocker.
inline bool SyncRemovedNamespace(const std::string& path,
                                 const std::set<std::string>& removed)
{
  std::string current = path;
  for (unsigned depth = 0; depth < 256; ++depth)
  {
    if (ProtectedCanonical(current) != current) return false;
    struct stat observed{};
    if (::lstat(current.c_str(), &observed) == 0)
    {
      if (!S_ISDIR(observed.st_mode) || S_ISLNK(observed.st_mode)) return false;
      const int fd = ::open(current.c_str(), O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
      if (fd < 0) return false;
      struct stat verified{};
      const bool same = ::fstat(fd,&verified) == 0 && S_ISDIR(verified.st_mode) &&
          observed.st_dev == verified.st_dev && observed.st_ino == verified.st_ino;
      int rc = -1;
      if (same) do { rc = ::fsync(fd); } while (rc < 0 && errno == EINTR);
      const int closed = ::close(fd);
      return same && rc == 0 && closed == 0;
    }
    if (errno != ENOENT || !removed.count(current)) return false;
    const auto slash = current.rfind('/');
    if (slash == std::string::npos || slash == 0) return false;
    current.resize(slash);
  }
  return false;
}

inline bool SyncProtectedPath(const std::string& path,
                              const std::vector<std::string>& profiles,
                              const std::set<std::string>& removed = {})
{
  struct stat st{};
  if (::lstat(path.c_str(), &st) == 0)
  {
    // A real Linux null device has no durable bytes. Opening it for output
    // still records the operation; only this exact checked device is exempt
    // from file fsync. A regular file, symlink or other device is not a waiver.
    if (path == "/dev/null" && S_ISCHR(st.st_mode) &&
        major(st.st_rdev) == 1 && minor(st.st_rdev) == 3)
    {
      const int fd = ::open(path.c_str(), O_WRONLY | O_CLOEXEC | O_NOFOLLOW);
      if (fd < 0) return false;
      struct stat actual{};
      const bool matched = ::fstat(fd, &actual) == 0 && S_ISCHR(actual.st_mode) &&
          actual.st_rdev == st.st_rdev && actual.st_dev == st.st_dev && actual.st_ino == st.st_ino;
      const int closed = ::close(fd);
      return matched && closed == 0;
    }
    if ((!S_ISREG(st.st_mode) && !S_ISDIR(st.st_mode)) || S_ISLNK(st.st_mode)) return false;
    const int fd = ::open(path.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW |
                                     (S_ISDIR(st.st_mode) ? O_DIRECTORY : 0));
    if (fd < 0) return false;
    int rc; do { rc = ::fsync(fd); } while (rc < 0 && errno == EINTR);
    const int closed = ::close(fd);
    if (rc || closed) return false;
  }
  else if (errno != ENOENT) return false;
  const auto slash = path.rfind('/');
  if (slash == std::string::npos) return false;
  const auto parent = slash ? path.substr(0, slash) : "/";
  const int fd = ::open(parent.c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0)
  {
    // A vanished UUID staging parent is not a vanished essential database.
    // Fsync its surviving staging ancestor only when the installer path
    // exactly matches a verified profile-bound UUID scratch hierarchy.
    return errno == ENOENT && (SyncRemovedNamespace(path, removed) ||
                               SyncRemovedInstallerStage(parent, path, profiles));
  }
  int rc; do { rc = ::fsync(fd); } while (rc < 0 && errno == EINTR);
  const int closed = ::close(fd);
  return rc == 0 && closed == 0;
}
inline bool SealEssentialWrites(uint64_t generation)
{
  std::vector<std::string> paths, profiles;
  std::set<std::string> removed;
  auto& s = Get();
  {
    std::lock_guard<std::mutex> lock(s.mutex); auto& p = s.protection;
    if (p.generation != generation || p.phase != 2 || !EssentialWritesLocked(s).blockers.empty()) return false;
    // Close permission atomically with the zero-in-flight test, BEFORE fsync.
    p.phase = 3;
    removed = p.removedNamespaces;
    profiles = p.profiles; // Already canonical, captured under the admission mutex.
    for (const auto& path : p.paths)
      if (!OptionalPathLocked(p, path)) paths.push_back(path);
  }
  for (const auto& path : paths)
  {
    const auto canonical = ProtectedCanonical(path);
    if (canonical.empty() || !SyncProtectedPath(canonical, profiles, removed))
    { const int error=errno; ProtectionFailure("protected_durability_failed:" + path);
      ProtectionFailure("protected_durability_context:" + path + NamespaceFailureEvidence(path,error)); return false; }
  }
  std::lock_guard<std::mutex> lock(s.mutex);
  if (!EssentialWritesLocked(s).blockers.empty()) return false;
  s.protection.durable = true; return true;
}
inline bool EssentialWritesAuthorized(uint64_t generation)
{
  const auto proof = EssentialWrites();
  return generation && proof.generation == generation && proof.phase == 3 &&
         proof.durable && proof.blockers.empty();
}
} // namespace InfinityScriptPersistence
