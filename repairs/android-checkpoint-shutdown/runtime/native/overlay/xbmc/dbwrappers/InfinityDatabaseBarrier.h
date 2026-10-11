/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <cstddef>
#include <cstdint>
#include <mutex>
#include <unordered_map>

#if defined(TARGET_ANDROID) && !defined(INFINITY_DATABASE_BARRIER_TEST)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif

// Subordinate native-database participant. Android's checkpoint coordinator is
// the sole caller of Begin/Seal/End. This registry does not terminate a process,
// commit another owner's transaction, or cover Python/private SQLite handles.
namespace InfinityDatabaseBarrier
{
struct Snapshot
{
  uint64_t session{0};
  size_t activeOperations{0};
  size_t activeTransactions{0};
  size_t queuedOwners{0};
  size_t unsupportedOwners{0};
  uint64_t failures{0};
  uint64_t rejectedWrites{0};
  bool sealed{false};
  bool Ready() const
  {
    return session != 0 && activeOperations == 0 && activeTransactions == 0 &&
           queuedOwners == 0 && unsupportedOwners == 0 && failures == 0 && rejectedWrites == 0;
  }
};

namespace Detail
{
struct Owner
{
  size_t operations{0};
  bool transaction{false};
  bool queued{false};
  bool unsupported{false};
};
struct Registry
{
  std::mutex mutex;
  std::unordered_map<const void*, Owner> owners;
  uint64_t session{0};
  uint64_t lastSession{0};
  uint64_t failures{0};
  uint64_t rejectedWrites{0};
  size_t abandonedOwners{0};
  // Closing a remote connection is not a persistence acknowledgement. Its
  // unchecked/private commit path remains unsupported for this engine lifetime.
  bool unsupportedBackendEncountered{false};
  bool sealed{false};
};
inline Registry& State()
{
  // Process-lifetime state; do not depend on static destructor ordering at exit.
  static Registry* state = new Registry;
  return *state;
}
inline thread_local uint64_t failureSerial{0};
inline thread_local uint64_t permissionSession{0};
inline thread_local unsigned int drainDepth{0};
inline Snapshot ReadLocked(const Registry& state)
{
  Snapshot snapshot;
  snapshot.session = state.session;
  snapshot.failures = state.failures;
  snapshot.rejectedWrites = state.rejectedWrites;
  snapshot.sealed = state.sealed;
  snapshot.queuedOwners = state.abandonedOwners;
  for (const auto& entry : state.owners)
  {
    snapshot.activeOperations += entry.second.operations;
    snapshot.activeTransactions += entry.second.transaction ? 1U : 0U;
    snapshot.queuedOwners += entry.second.queued ? 1U : 0U;
    snapshot.unsupportedOwners += entry.second.unsupported ? 1U : 0U;
  }
  // Preserve the refusal after all live remote owners have closed, including
  // before Begin(), and across explicit failed-session recovery.
  if (state.unsupportedBackendEncountered && snapshot.unsupportedOwners == 0)
    snapshot.unsupportedOwners = 1;
  return snapshot;
}
inline bool PermittedLocked(const Registry& state)
{
  return !state.sealed && (state.session == 0 || permissionSession == state.session || drainDepth > 0);
}
inline void RejectLocked(Registry& state)
{
  if (state.session != 0)
  {
    ++state.failures;
    ++state.rejectedWrites;
  }
}
} // namespace Detail

inline bool Begin(uint64_t session)
{
  auto& state = Detail::State();
  std::lock_guard<std::mutex> lock(state.mutex);
  if (session == 0 || state.session != 0 || session <= state.lastSession)
    return false;
  state.session = session;
  state.lastSession = session;
  state.failures = 0;
  state.rejectedWrites = 0;
  state.sealed = false;
  return true;
}
inline Snapshot GetSnapshot()
{
  auto& state = Detail::State();
  std::lock_guard<std::mutex> lock(state.mutex);
  return Detail::ReadLocked(state);
}
inline bool Seal(uint64_t session)
{
  auto& state = Detail::State();
  std::lock_guard<std::mutex> lock(state.mutex);
  if (state.session != session || state.sealed || !Detail::ReadLocked(state).Ready())
    return false;
  state.sealed = true;
  return true;
}
inline bool End(uint64_t session)
{
  auto& state = Detail::State();
  std::lock_guard<std::mutex> lock(state.mutex);
  if (session == 0 || state.session != session || state.sealed)
    return false;
  // Explicit coordinator recovery only. Never reuse a session generation.
  state.session = 0;
  return true;
}
inline uint64_t ThreadFailureSerial() { return Detail::failureSerial; }
inline void RecordFailure(const char* detail)
{
  ++Detail::failureSerial;
  auto& state = Detail::State();
  {
    std::lock_guard<std::mutex> lock(state.mutex);
    if (state.session != 0)
      ++state.failures;
  }
  // QUIESCE may still be draining accepted native/Python work before Begin.
  // Preserve failures in the authoritative coordinator across that interval.
  // Never call back while holding the database registry mutex.
#if defined(TARGET_ANDROID) && !defined(INFINITY_DATABASE_BARRIER_TEST)
  if (InfinityAndroidCheckpoint::IsActive())
    InfinityAndroidCheckpoint::RecordPersistenceFailure("native_databases", detail);
#else
  (void)detail;
#endif
}
inline void SetTransaction(const void* owner, bool transaction)
{
  auto& state = Detail::State();
  std::lock_guard<std::mutex> lock(state.mutex);
  state.owners[owner].transaction = transaction;
}
inline void SetQueued(const void* owner, bool queued)
{
  auto& state = Detail::State();
  std::lock_guard<std::mutex> lock(state.mutex);
  state.owners[owner].queued = queued;
}
inline void SetUnsupported(const void* owner, bool unsupported)
{
  auto& state = Detail::State();
  std::lock_guard<std::mutex> lock(state.mutex);
  state.owners[owner].unsupported = unsupported;
  if (unsupported)
    state.unsupportedBackendEncountered = true;
}
inline void ForgetOwner(const void* owner)
{
  auto& state = Detail::State();
  std::lock_guard<std::mutex> lock(state.mutex);
  auto found = state.owners.find(owner);
  if (found == state.owners.end())
    return;
  if (found->second.operations != 0 || found->second.transaction || found->second.queued)
  {
    ++state.abandonedOwners;
    if (state.session != 0)
      ++state.failures;
  }
  state.owners.erase(found);
}

class CheckpointWriteScope
{
public:
  explicit CheckpointWriteScope(uint64_t session) : m_previous(Detail::permissionSession)
  {
    auto& state = Detail::State();
    std::lock_guard<std::mutex> lock(state.mutex);
    m_valid = session != 0 && state.session == session && !state.sealed;
    if (m_valid)
      Detail::permissionSession = session;
  }
  ~CheckpointWriteScope() { Detail::permissionSession = m_previous; }
  bool IsValid() const { return m_valid; }
  CheckpointWriteScope(const CheckpointWriteScope&) = delete;
  CheckpointWriteScope& operator=(const CheckpointWriteScope&) = delete;
private:
  uint64_t m_previous;
  bool m_valid{false};
};

// Scope includes the entire SQLite call, including preparation/callbacks and
// final transaction-state publication. Merely checking a counter before calling
// SQLite would leave a window in which the coordinator could falsely seal.
class Operation
{
public:
  explicit Operation(const void* owner) : m_owner(owner), m_previous(s_current)
  {
    auto& state = Detail::State();
    std::lock_guard<std::mutex> lock(state.mutex);
    auto& tracked = state.owners[owner];
    m_admitted = Detail::PermittedLocked(state) || (!state.sealed && tracked.transaction) ||
                 (!state.sealed && m_previous != nullptr && m_previous->m_admitted);
    ++tracked.operations;
    s_current = this;
  }
  ~Operation()
  {
    auto& state = Detail::State();
    std::lock_guard<std::mutex> lock(state.mutex);
    auto& tracked = state.owners[m_owner];
    if (tracked.operations > 0)
      --tracked.operations;
    s_current = m_previous;
  }
  bool AllowWrite()
  {
    auto& state = Detail::State();
    std::lock_guard<std::mutex> lock(state.mutex);
    if (!state.sealed && (m_admitted || Detail::PermittedLocked(state)))
      return true;
    Detail::RejectLocked(state);
    return false;
  }
  static bool AuthorizeWrite(const void* owner)
  {
    for (Operation* current = s_current; current != nullptr; current = current->m_previous)
      if (current->m_owner == owner)
        return current->AllowWrite();
    // Unscoped raw-handle access cannot participate in an active checkpoint.
    auto& state = Detail::State();
    std::lock_guard<std::mutex> lock(state.mutex);
    if (state.session == 0 && !state.sealed)
      return true;
    Detail::RejectLocked(state);
    return false;
  }
  Operation(const Operation&) = delete;
  Operation& operator=(const Operation&) = delete;
private:
  const void* m_owner;
  Operation* m_previous;
  bool m_admitted{false};
  static inline thread_local Operation* s_current{nullptr};
};

// Accepted SQL buffers may finish on their owner thread after admission closes.
// Only a queue that was already registered may grant this continuation scope.
class QueueDrainScope
{
public:
  explicit QueueDrainScope(const void* owner) : m_operation(owner)
  {
    auto& state = Detail::State();
    std::lock_guard<std::mutex> lock(state.mutex);
    const auto found = state.owners.find(owner);
    m_valid = !state.sealed && (Detail::PermittedLocked(state) ||
              (found != state.owners.end() && found->second.queued));
    if (m_valid)
      ++Detail::drainDepth;
    else
      Detail::RejectLocked(state);
  }
  ~QueueDrainScope()
  {
    if (m_valid)
      --Detail::drainDepth;
  }
  bool IsValid() const { return m_valid; }
private:
  Operation m_operation;
  bool m_valid{false};
};
} // namespace InfinityDatabaseBarrier
