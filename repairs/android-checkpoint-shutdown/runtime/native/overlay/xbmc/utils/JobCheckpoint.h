#pragma once

#include <chrono>
#include <cstdint>
#include <memory>
#include <map>
#include <algorithm>
#include <mutex>
#include <string>
#include <vector>
#include <utility>
#include <functional>

enum class CJobDurability { Pending, VerifiedUnchanged, VerifiedCommitted, VerifiedRestored, Unresolved };

struct CJobCheckpointRecord
{
  uint64_t token{0};
  uint64_t jobId{0};
  bool required{true};
  bool unknown{true};
  std::string owner;
  std::string operation;
  std::string type;
  std::string phase;
  std::string resource;
  std::string failureDetail;
  bool retained{false};
  bool resolved{false};
  bool receiptRequired{false};
  CJobDurability durability{CJobDurability::Pending};
  bool operationSucceeded{false};
  bool outcomeReviewed{false};
  bool completionRecorded{false};
  bool completionCallbackVerified{true};
  std::function<bool()> recoveryProof;
  size_t recoveryBytes{0};
  std::chrono::steady_clock::time_point admitted;
};

namespace JobCheckpoint
{
struct Entry
{
  uint64_t token{0};
  uint64_t jobId{0};
  bool required{true};
  bool unknown{true};
  std::string owner;
  std::string operation;
  std::string type;
  std::string phase;
  int64_t elapsedMs{0};
  std::string resource{};
  std::string failureDetail{};
};
struct Snapshot
{
  size_t required{0};
  size_t nonPersistent{0};
  size_t unknown{0};
  std::vector<Entry> blockers;
  std::vector<Entry> resolvedHistory;
  uint64_t resolvedCount{0};
};
struct Registry
{
  std::mutex mutex;
  uint64_t next{0};
  std::vector<std::weak_ptr<CJobCheckpointRecord>> jobs;
  std::map<std::string, std::shared_ptr<CJobCheckpointRecord>> unresolved;
  std::map<uint64_t, std::shared_ptr<CJobCheckpointRecord>> pendingReceipts;
  bool receiptOverflow{false};
  std::vector<Entry> resolvedHistory;
  uint64_t resolvedCount{0};
  size_t recoveryBytes{0};
};
inline Registry& Get()
{
  static auto* registry = new Registry;
  return *registry;
}
// Work and callback use the same admitted operation. Synchronous and nested
// operations still create their own receipts; identity labels grant no bypass.
inline thread_local std::shared_ptr<CJobCheckpointRecord> currentOperation;
class WorkBinding
{
public:
  explicit WorkBinding(std::shared_ptr<CJobCheckpointRecord> record)
    : m_previous(currentOperation) { currentOperation = std::move(record); }
  ~WorkBinding() { currentOperation = std::move(m_previous); }
  WorkBinding(const WorkBinding&) = delete;
  WorkBinding& operator=(const WorkBinding&) = delete;
private:
  std::shared_ptr<CJobCheckpointRecord> m_previous;
};
inline void WorkResult(const std::shared_ptr<CJobCheckpointRecord>& job,
                       CJobDurability durability, bool operationSucceeded,
                       const std::string& failureDetail = {})
{
  if (!job || job->unknown) return;
  std::lock_guard<std::mutex> lock(Get().mutex);
  job->durability = durability;
  job->operationSucceeded = operationSucceeded;
  job->outcomeReviewed = true;
  job->failureDetail = failureDetail.substr(0, 160);
}
inline void RecoveryProof(const std::shared_ptr<CJobCheckpointRecord>& job,
                          std::function<bool()> proof, size_t bytes)
{
  if (!job || !proof) return;
  auto& registry = Get(); std::lock_guard<std::mutex> lock(registry.mutex);
  if (!job->completionCallbackVerified || job->recoveryProof ||
      bytes > 64U * 1024U * 1024U - registry.recoveryBytes) return;
  registry.recoveryBytes += bytes; job->recoveryBytes = bytes; job->recoveryProof = std::move(proof);
}
// A later operation may retire only the exact outstanding scopes whose saved
// preimages have actually been restored and synced. Labels/success alone grant
// no recovery. Proof executes outside the registry lock and without mutation.
inline void RecoverRestored(const std::string& operation, const std::string& resource,
                            uint64_t currentToken)
{
  auto& registry = Get();
  std::vector<std::pair<std::shared_ptr<CJobCheckpointRecord>, std::function<bool()>>> candidates;
  auto peer = [&]() {
    for (const auto& weak : registry.jobs) if (auto job = weak.lock())
      if (job->token != currentToken && !job->resolved && !job->completionRecorded &&
          job->resource == resource) return true;
    return false;
  };
  {
    std::lock_guard<std::mutex> lock(registry.mutex);
    if (peer()) return;
    for (const auto& value : registry.unresolved)
      if (value.second->operation == operation && value.second->resource == resource &&
          value.second->completionRecorded && value.second->completionCallbackVerified &&
          value.second->recoveryProof) candidates.emplace_back(value.second, value.second->recoveryProof);
  }
  for (const auto& candidate : candidates)
  {
    const auto& job = candidate.first;
    bool verified = false;
    try { verified = candidate.second(); } catch (...) { verified = false; }
    if (!verified) continue;
    std::lock_guard<std::mutex> lock(registry.mutex);
    if (job->resolved || !job->completionCallbackVerified || peer()) continue;
    job->resolved = true; job->retained = false; job->durability = CJobDurability::VerifiedRestored;
    for (auto i = registry.unresolved.begin(); i != registry.unresolved.end();)
      if (i->second == job) i = registry.unresolved.erase(i); else ++i;
    ++registry.resolvedCount;
    if (registry.resolvedHistory.size() == 16) registry.resolvedHistory.erase(registry.resolvedHistory.begin());
    registry.resolvedHistory.push_back({job->token, job->jobId, job->required, job->unknown,
        job->owner, job->operation, job->type, "installation_failed_verified_restored",
        std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - job->admitted).count(), job->resource});
    registry.recoveryBytes -= job->recoveryBytes; job->recoveryBytes = 0; job->recoveryProof = {};
  }
}
inline std::shared_ptr<CJobCheckpointRecord> Admit(bool required, bool unknown, std::string owner, std::string operation,
                                                   std::string type, const char* phase, bool receiptRequired=false, std::string resource={})
{
  auto& registry = Get();
  std::lock_guard<std::mutex> lock(registry.mutex);
  auto job = std::make_shared<CJobCheckpointRecord>();
  job->token = ++registry.next;
  job->required = required;
  job->unknown = unknown;
  job->owner = owner.substr(0, 96);
  job->operation = operation.empty() ? "unclassified_native_job" : operation.substr(0, 96);
  job->type = type.substr(0, 128);
  job->resource = std::move(resource);
  job->phase = phase;
  job->receiptRequired=receiptRequired && !unknown;
  job->admitted = std::chrono::steady_clock::now();
  if ((registry.next % 64) == 0)
    registry.jobs.erase(std::remove_if(registry.jobs.begin(), registry.jobs.end(),
        [](const auto& entry) { return entry.expired(); }), registry.jobs.end());
  registry.jobs.emplace_back(job);
  // Retain one unresolved obligation per actual implementation/operation. A
  // frequently repeated anonymous task must not grow history per invocation.
  if (unknown && registry.unresolved.size() < 512)
    job->retained = registry.unresolved.emplace(job->type + "\n" + job->operation + "\n" + job->resource, job).second;
  if(job->receiptRequired) {
    if(registry.pendingReceipts.size()<4096) {
      registry.pendingReceipts.emplace(job->token,job);job->retained=true;
    } else registry.receiptOverflow=true; // A bounded ledger must fail closed.
  }
  return job;
}
inline void Phase(const std::shared_ptr<CJobCheckpointRecord>& job, const char* phase,
                  uint64_t jobId = 0)
{
  if (!job) return;
  std::lock_guard<std::mutex> lock(Get().mutex);
  job->phase = phase;
  if (jobId) job->jobId = jobId;
}
inline void Complete(const std::shared_ptr<CJobCheckpointRecord>& job, bool success,
                     bool verifiedReplacement=false, bool callbackSucceeded=true)
{
  if(!job || job->unknown)return; // Unknown work still requires its own reviewed contract.
  auto& registry=Get();std::lock_guard<std::mutex> lock(registry.mutex);
  if (job->completionRecorded) return;
  if (job->outcomeReviewed && (job->durability == CJobDurability::Unresolved || job->durability == CJobDurability::Pending)) success = false;
  job->completionRecorded = true;
  job->completionCallbackVerified = callbackSucceeded;
  if (success || !callbackSucceeded)
  {
    registry.recoveryBytes -= job->recoveryBytes;
    job->recoveryBytes = 0; job->recoveryProof = {};
  }
  // General installation success cannot prove recovery of a prior operation's
  // staging, package-cache, dependency or database resources.
  (void)verifiedReplacement;
  job->phase=success?"completion_receipt_verified":"completed_write_failed";
  if (success && job->durability == CJobDurability::Pending)
    job->durability = CJobDurability::VerifiedCommitted;
  if (!success) job->durability = CJobDurability::Unresolved;
  registry.pendingReceipts.erase(job->token);
  job->retained=false;
  if (success && job->outcomeReviewed && !job->operationSucceeded && job->receiptRequired &&
      (job->durability == CJobDurability::VerifiedUnchanged ||
       job->durability == CJobDurability::VerifiedRestored ||
       job->durability == CJobDurability::VerifiedCommitted))
  {
    const char* outcome = job->durability == CJobDurability::VerifiedUnchanged ?
        "installation_failed_verified_unchanged" :
        job->durability == CJobDurability::VerifiedRestored ?
        "installation_failed_verified_restored" : "installation_failed_verified_committed";
    ++registry.resolvedCount;
    if (registry.resolvedHistory.size() == 16) registry.resolvedHistory.erase(registry.resolvedHistory.begin());
    registry.resolvedHistory.push_back({job->token, job->jobId, job->required, job->unknown,
        job->owner, job->operation, job->type, outcome,
        std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - job->admitted).count(), job->resource});
  }
  if(!success) {
    // Keep semantic write/callback failure even if it occurred before Close.
    const auto key=job->type+"\n"+job->operation+"\n"+job->resource+"\n"+std::to_string(job->token);
    if (registry.unresolved.count(key) || registry.unresolved.size() < 512) {
      job->retained=true;
      registry.unresolved[key]=job;
    } else registry.receiptOverflow=true;
  }
}
inline Snapshot GetSnapshot()
{
  Snapshot result;
  auto& registry = Get();
  std::lock_guard<std::mutex> lock(registry.mutex);
  const auto now = std::chrono::steady_clock::now();
  for (auto it = registry.jobs.begin(); it != registry.jobs.end();)
  {
    const auto job = it->lock();
    if (!job) { it = registry.jobs.erase(it); continue; }
    ++it;
    if (job->resolved) continue;
    if (!job->required) { ++result.nonPersistent; continue; }
    if (job->unknown) ++result.unknown;
    ++result.required;
    if (result.blockers.size() < 32)
      result.blockers.push_back({job->token, job->jobId, job->required, job->unknown, job->owner, job->operation,
        job->type, job->retained && job.use_count() == 2 && job->phase!="completed_write_failed" ? "completed_without_owner_receipt" : job->phase,
        std::chrono::duration_cast<std::chrono::milliseconds>(now - job->admitted).count(), job->resource, job->failureDetail});
  }
  result.resolvedHistory = registry.resolvedHistory;
  result.resolvedCount = registry.resolvedCount;
  if(registry.receiptOverflow) {
    ++result.required;++result.unknown;
    if(result.blockers.size()<32)result.blockers.push_back({0,0,true,true,"background_jobs",
        "completion_receipt_inventory_limit","JobCheckpoint","completed_write_failed",0});
  }
  return result;
}
} // namespace JobCheckpoint
