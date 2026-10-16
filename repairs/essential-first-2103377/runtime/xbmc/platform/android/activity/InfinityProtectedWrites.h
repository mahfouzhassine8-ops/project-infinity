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

inline bool OptionalBasePathLocked(const WriteProtection& p, const std::string& raw)
{
  if (raw == ":nonpersistent:") return true;
  const auto path = ProtectedCanonical(raw);
  if (path.empty()) return false;
  for (const auto& cache : p.caches) if (Within(path, cache)) return true;
  for (const auto& root : p.profiles)
  {
    const auto prefix = root + "/addon_data/";
    if (path.rfind(prefix, 0) != 0) continue;
    const auto slash = path.find('/', prefix.size());
    if (slash == std::string::npos) return false;
    const auto addon = path.substr(prefix.size(), slash - prefix.size());
    if (addon.empty() || addon == "." || addon == ".." ||
        addon.find("infinity") != std::string::npos ||
        addon.find("arctic") != std::string::npos || addon.rfind("skin.", 0) == 0)
      return false;
    // Add-on settings are user state even when other private cache is optional.
    if (path.substr(slash + 1) == "settings.xml") return false;
    return true;
  }
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
  if (from == ":nonpersistent:" || to == ":nonpersistent:") return;
  const auto source = Absolute(from), target = Absolute(to);
  if (source.empty() || target.empty() || source == target) return;
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex); auto& p = s.protection;
  if (p.aliases.size() >= 65536)
  { ProtectionFailureLocked(p,"protected_namespace_alias_inventory_exhausted"); return; }
  p.aliases.emplace(source, target);
  p.paths.insert(source); p.paths.insert(target);
}

inline uint64_t BeginProtectedOperation(int id, const std::vector<std::string>& paths,
                                       const std::string& operation, bool nativeSave = false,
                                       bool existingTransaction = false, int descriptor = -1)
{
  auto& s = Get(); std::lock_guard<std::mutex> lock(s.mutex);
  auto& p = s.protection;
  ProtectedResource resource{id, paths, operation};
  resource.descriptor = descriptor;
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
      [](const std::string& path) { return path != ":nonpersistent:"; });
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
  const auto token = ++p.nextOperation;
  p.operations.emplace(token, resource);
  for (const auto& path : paths)
  {
    if (path == ":nonpersistent:") continue;
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
  if (path != ":nonpersistent:")
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
  }
  EndProtectedOperation(child);
  return true;
}
class ProtectedOperation
{
public:
  ProtectedOperation(int writer, const std::vector<std::string>& paths, const char* operation,
                     bool nativeSave = false, bool existingTransaction = false, int descriptor = -1)
    : m_token(BeginProtectedOperation(writer, paths, operation, nativeSave, existingTransaction, descriptor)) {}
  ~ProtectedOperation() { if (m_token) EndProtectedOperation(m_token); }
  explicit operator bool() const { return m_token != 0; }
  ProtectedOperation(const ProtectedOperation&) = delete;
  ProtectedOperation& operator=(const ProtectedOperation&) = delete;
private:
  uint64_t m_token;
};

inline std::string DescriptorPath(int fd)
{
  struct stat st{};
  if (::fstat(fd, &st) != 0) return {};
  if (!S_ISREG(st.st_mode) && !S_ISDIR(st.st_mode)) return ":nonpersistent:";
  if (!st.st_nlink) return ":nonpersistent:";
  char target[PATH_MAX]{};
  const auto name = "/proc/self/fd/" + std::to_string(fd);
  const auto size = ::readlink(name.c_str(), target, sizeof(target) - 1);
  if (size <= 0 || size >= static_cast<ssize_t>(sizeof(target) - 1)) return {};
  target[size] = '\0'; return target;
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
  p.transactions[key] = {-1, {path}, operation};
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
    if (!privateOnly) proof.blockers.push_back("unverified_protected_writer:" + blocker.writer + ":" + reason);
  }
  if (s.blockingOverflow) proof.blockers.push_back("protected_writer_failure_inventory_overflow");
  for (const auto& entry : p.operations)
    if (ProtectedLocked(p, entry.second)) proof.blockers.push_back("active_protected_operation:" + entry.second.operation);
  for (const auto& entry : p.buffers)
    if (ProtectedLocked(p, entry.second)) proof.blockers.push_back("unflushed_protected_buffer:" + entry.first);
  for (const auto& entry : p.transactions)
    if (ProtectedLocked(p, entry.second)) proof.blockers.push_back("pending_protected_" + entry.second.operation + ":" + entry.first);
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

inline bool SyncProtectedPath(const std::string& path)
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
  if (fd < 0) return false;
  int rc; do { rc = ::fsync(fd); } while (rc < 0 && errno == EINTR);
  const int closed = ::close(fd);
  return rc == 0 && closed == 0;
}
inline bool SealEssentialWrites(uint64_t generation)
{
  std::vector<std::string> paths;
  auto& s = Get();
  {
    std::lock_guard<std::mutex> lock(s.mutex); auto& p = s.protection;
    if (p.generation != generation || p.phase != 2 || !EssentialWritesLocked(s).blockers.empty()) return false;
    // Close permission atomically with the zero-in-flight test, BEFORE fsync.
    p.phase = 3;
    for (const auto& path : p.paths)
      if (!OptionalPathLocked(p, path)) paths.push_back(path);
  }
  for (const auto& path : paths)
  {
    const auto canonical = ProtectedCanonical(path);
    if (canonical.empty() || !SyncProtectedPath(canonical))
    { ProtectionFailure("protected_durability_failed:" + path); return false; }
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
