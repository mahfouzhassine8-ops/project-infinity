/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

// This is a shutdown capability fence, not an interpreter retirement receipt.
// Unknown capabilities and shared-data writers remain essential. Optional
// private data is deliberately not certified durable by this fence.
#include <algorithm>
#include <cerrno>
#include <climits>
#include <cstdint>
#include <cstdlib>
#include <fcntl.h>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace InfinityEssentialScriptFence
{
struct Writer
{
  std::string name;
  bool observed{false};
  bool retired{false};
  bool failed{false};
  std::set<std::string> paths;
};
struct Proof
{
  uint64_t generation{0};
  bool admissionClosed{false};
  bool sealed{false};
  bool durable{false};
  std::size_t optionalUnfinished{0};
  std::vector<std::string> blockers;
};
struct Registry
{
  std::mutex mutex;
  std::map<int, Writer> writers;
  std::set<std::string> opaque;
  std::vector<std::string> profiles;
  std::vector<std::string> caches;
  uint64_t generation{0};
  bool closed{false};
  bool sealed{false};
  bool durable{false};
  std::string failure;
  // Deliberately false in production until all raw-file, SQLite ATTACH,
  // namespace/VFS and excluded-interpreter routes are wired and verified.
  bool hookCoverageComplete{false};
};
inline Registry& Get() { static auto* r = new Registry; return *r; }
inline bool Under(const std::string& path, const std::string& root)
{ return !root.empty() && (path == root || path.rfind(root + "/", 0) == 0); }

// Resolve the nearest existing ancestor, retaining missing leaf components.
// A linked or multiply-linked leaf is never accepted as optional private data.
inline std::string Canonical(const std::string& input)
{
  if (input.empty() || input.front() != '/' || input.find('\0') != std::string::npos)
    return {};
  std::string path = input, tail;
  for (unsigned depth = 0; depth < 256; ++depth)
  {
    struct stat st{};
    if (::lstat(path.c_str(), &st) == 0)
    {
      if (S_ISLNK(st.st_mode) || (S_ISREG(st.st_mode) && st.st_nlink != 1))
        return {};
      char resolved[PATH_MAX]{};
      if (!::realpath(path.c_str(), resolved)) return {};
      return std::string(resolved) + tail;
    }
    if (errno != ENOENT) return {};
    const auto slash = path.rfind('/');
    if (slash == std::string::npos || slash == 0) return {};
    const auto leaf = path.substr(slash + 1);
    if (leaf.empty() || leaf == "." || leaf == "..") return {};
    tail = "/" + leaf + tail;
    path.resize(slash);
  }
  return {};
}
inline bool OptionalLocked(const Registry& r, const std::string& raw)
{
  const auto path = Canonical(raw);
  if (path.empty()) return false;
  for (const auto& cache : r.caches)
    if (Under(path, cache)) return true;
  for (const auto& profile : r.profiles)
  {
    const auto prefix = profile + "/addon_data/";
    if (path.rfind(prefix, 0) != 0) continue;
    const auto end = path.find('/', prefix.size());
    if (end == std::string::npos) return false; // Never waive the directory itself.
    const auto addon = path.substr(prefix.size(), end - prefix.size());
    if (addon.empty() || addon == "." || addon == "..") return false;
    // First-party settings, Resume Hub, watched history and skin data stay
    // protected even if another add-on was the writer.
    if (addon.find("infinity") != std::string::npos ||
        addon.find("arctic") != std::string::npos || addon.rfind("skin.", 0) == 0)
      return false;
    return true;
  }
  return false;
}
inline void Admit(int id, const std::string& name)
{
  auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex);
  if (r.closed || r.writers.size() >= 8192)
  { r.failure = "script_admission_after_close_or_inventory_limit"; return; }
  auto& w = r.writers[id];
  // Reused invokers retain earlier path obligations until the final seal.
  w.retired = false;
  w.name = name;
}
inline void Observed(int id)
{
  auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex);
  auto it = r.writers.find(id);
  if (it != r.writers.end()) it->second.observed = true;
}
inline bool Observe(int id, const std::string& path)
{
  auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex);
  if (r.closed) return false; // Denial must be propagated before the mutation.
  auto it = r.writers.find(id);
  if (it == r.writers.end() || path.empty() || path.front() != '/' ||
      it->second.paths.size() >= 65536)
  { r.failure = "protected_write_identity_or_inventory_unconfirmed"; return true; }
  it->second.paths.insert(path);
  return true;
}
inline bool Closed()
{ auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex); return r.closed; }
inline void Failure(int id, const std::string& reason)
{
  auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex);
  auto it = r.writers.find(id);
  if (it != r.writers.end()) it->second.failed = true;
  // These operations remain inside previously inventoried file/DB handles.
  // Every unclassified capability remains a global essential blocker.
  static const std::set<std::string> bounded = {
    "uncaught_script_failure_before_persistence_receipt",
    "sqlite_write_failed", "sqlite_script_failed", "sqlite_commit_failed",
    "sqlite_pending_transaction_at_retirement", "sqlite_closed_with_pending_transaction",
    "sqlite_collected_with_pending_transaction", "buffer_flush_before_retirement_failed",
    "buffered_write_failed", "buffer_flush_failed", "buffer_close_failed",
    "raw_buffer_write_failed", "raw_buffer_close_failed", "layered_buffer_write_failed",
    "layered_buffer_flush_failed", "layered_buffer_close_failed"
  };
  if (!bounded.count(reason))
  {
    if (r.opaque.size() < 128) r.opaque.insert(std::to_string(id) + ":" + reason);
    else r.failure = "opaque_capability_inventory_overflow";
  }
}
inline void Retired(int id, bool success)
{
  auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex);
  auto it = r.writers.find(id);
  if (it != r.writers.end())
  { it->second.retired = true; it->second.failed = it->second.failed || !success; }
}
inline bool CloseAdmission(uint64_t generation, const std::vector<std::string>& profiles,
                           const std::vector<std::string>& caches)
{
  auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex);
  if (!r.hookCoverageComplete)
  { r.failure = "essential_write_hook_coverage_unverified"; return false; }
  if (r.closed) return r.generation == generation;
  if (!generation || profiles.empty()) return false;
  for (const auto& value : profiles)
  {
    const auto path = Canonical(value);
    if (path.empty()) { r.failure = "protected_profile_root_unconfirmed"; return false; }
    r.profiles.push_back(path);
  }
  for (const auto& value : caches)
  {
    const auto path = Canonical(value);
    if (path.empty()) continue; // Unknown cache stays protected.
    for (const auto& profile : r.profiles)
      if (Under(profile, path)) { r.failure = "cache_root_overlaps_protected_profile"; return false; }
    r.caches.push_back(path);
  }
  r.generation = generation;
  r.closed = true;
  return true;
}
inline Proof SnapshotLocked(const Registry& r)
{
  Proof p; p.generation = r.generation; p.admissionClosed = r.closed;
  p.sealed = r.sealed; p.durable = r.durable;
  if (!r.failure.empty()) p.blockers.push_back(r.failure);
  for (const auto& why : r.opaque) p.blockers.push_back("unverified_capability:" + why);
  for (const auto& entry : r.writers)
  {
    const auto& w = entry.second;
    if (!w.observed) { p.blockers.push_back("observer_unverified:" + w.name); continue; }
    bool protectedPath = false;
    for (const auto& path : w.paths)
      if (!OptionalLocked(r, path))
      {
        protectedPath = true;
        if (!w.retired || w.failed)
          p.blockers.push_back("protected_writer:" + w.name + ":" + path);
      }
    if (!w.retired && !protectedPath) ++p.optionalUnfinished;
  }
  return p;
}
inline Proof Snapshot()
{ auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex); return SnapshotLocked(r); }
inline bool Sync(const std::string& path, bool directory)
{
  const int fd = ::open(path.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW |
                                      (directory ? O_DIRECTORY : 0));
  if (fd < 0) return false;
  int rc; do { rc = ::fsync(fd); } while (rc != 0 && errno == EINTR);
  const int closed = ::close(fd);
  return rc == 0 && closed == 0;
}
inline bool Seal(uint64_t generation)
{
  auto& r = Get(); std::lock_guard<std::mutex> lock(r.mutex);
  if (!r.closed || r.generation != generation || !SnapshotLocked(r).blockers.empty()) return false;
  if (r.sealed) return r.durable;
  std::set<std::string> protectedPaths;
  for (const auto& entry : r.writers)
    for (const auto& path : entry.second.paths)
      if (!OptionalLocked(r, path)) protectedPaths.insert(path);
  for (const auto& path : protectedPaths)
  {
    struct stat st{};
    const bool present = ::lstat(path.c_str(), &st) == 0;
    if ((!present && errno != ENOENT) || (present &&
        (S_ISLNK(st.st_mode) || (!S_ISREG(st.st_mode) && !S_ISDIR(st.st_mode)) ||
         !Sync(path, S_ISDIR(st.st_mode)))))
    { r.failure = "protected_file_sync_failed:" + path; return false; }
    const auto slash = path.rfind('/');
    if (slash == std::string::npos || !Sync(slash ? path.substr(0, slash) : "/", true))
    { r.failure = "protected_namespace_sync_failed:" + path; return false; }
  }
  r.sealed = r.durable = true;
  return true;
}
inline bool Authorized(uint64_t generation)
{
  const auto p = Snapshot();
  return p.generation == generation && p.admissionClosed && p.sealed && p.durable && p.blockers.empty();
}
} // namespace InfinityEssentialScriptFence
