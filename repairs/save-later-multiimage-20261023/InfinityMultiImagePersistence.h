#pragma once

// An observation scope for the exact GUI multi-image job. This grants no write
// permission and never changes a directory dispatch, result, callback or error.
#include "utils/JobCheckpoint.h"

#include <memory>
#include <string>

namespace InfinityMultiImagePersistence
{
struct Observation
{
  std::shared_ptr<CJobCheckpointRecord> record;
  bool verified{true};
  unsigned int factories{0};
  std::string failure;

  void Reject(const char* reason)
  {
    verified = false;
    if (failure.empty()) failure = reason;
  }
};
inline thread_local Observation* current{nullptr};

class Scope
{
public:
  explicit Scope(std::shared_ptr<CJobCheckpointRecord> record)
    : m_previous(current)
  {
    m_observation.record = std::move(record);
    const auto& owner = m_observation.record;
    if (!owner || owner != JobCheckpoint::currentOperation || owner->unknown ||
        owner->owner != "background_jobs" || owner->operation != "multiimage-enumeration")
      m_observation.Reject("multiimage_native_operation_ownership_unverified");
    current = &m_observation;
  }
  ~Scope()
  {
    current = m_previous;
    if (!m_finished)
    {
      // An escaping exception is not evidence that nothing was changed.
      // Keep the original exception and leave the owning job unresolved.
      JobCheckpoint::WorkResult(m_observation.record, CJobDurability::Unresolved, false,
          "multiimage_operation_did_not_reach_verified_boundary");
    }
  }
  Scope(const Scope&) = delete;
  Scope& operator=(const Scope&) = delete;

  void Reject(const char* reason) { m_observation.Reject(reason); }
  bool Finish(bool operationResult)
  {
    JobCheckpoint::WorkResult(m_observation.record,
        m_observation.verified ? CJobDurability::VerifiedUnchanged : CJobDurability::Unresolved,
        operationResult, m_observation.failure);
    m_finished = true;
    return m_observation.verified;
  }

private:
  Observation m_observation;
  Observation* m_previous;
  bool m_finished{false};
};

class DirectoryFactoryObservation
{
public:
  explicit DirectoryFactoryObservation(bool noFileDirectoryDispatch)
    : m_observation(current)
  {
    if (!m_observation) return;
    if (++m_observation->factories > 65536)
      m_observation->Reject("multiimage_directory_observation_limit");
    // The factory may call arbitrary binary add-on ContainsFiles handlers for
    // a file extension BEFORE it selects a final directory implementation.
    if (!noFileDirectoryDispatch)
      m_observation->Reject("multiimage_file_directory_dispatch_unverified");
  }
  ~DirectoryFactoryObservation()
  {
    if (m_observation && !m_reviewed)
      m_observation->Reject("multiimage_directory_backend_unverified");
  }
  DirectoryFactoryObservation(const DirectoryFactoryObservation&) = delete;
  DirectoryFactoryObservation& operator=(const DirectoryFactoryObservation&) = delete;

  // Called only at the two audited concrete constructor return sites in the
  // original native factory. No type-name string or caller claim is accepted.
  template<class T> T* Reviewed(T* directory)
  {
    m_reviewed = directory != nullptr;
    return directory;
  }

private:
  Observation* m_observation;
  bool m_reviewed{false};
};
} // namespace InfinityMultiImagePersistence
