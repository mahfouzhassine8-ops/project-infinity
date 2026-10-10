#pragma once

#include <chrono>
#include <cstdint>
#include <memory>
#include <map>
#include <algorithm>
#include <mutex>
#include <string>
#include <vector>

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
  bool retained{false};
  bool receiptRequired{false};
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
};
struct Snapshot
{
  size_t required{0};
  size_t nonPersistent{0};
  size_t unknown{0};
  std::vector<Entry> blockers;
};
struct Registry
{
  std::mutex mutex;
  uint64_t next{0};
  std::vector<std::weak_ptr<CJobCheckpointRecord>> jobs;
  std::map<std::string, std::shared_ptr<CJobCheckpointRecord>> unresolved;
  std::map<uint64_t, std::shared_ptr<CJobCheckpointRecord>> pendingReceipts;
  bool receiptOverflow{false};
};
inline Registry& Get()
{
  static auto* registry = new Registry;
  return *registry;
}
inline std::shared_ptr<CJobCheckpointRecord> Admit(bool required, bool unknown, std::string owner, std::string operation,
                                                   std::string type, const char* phase, bool receiptRequired=false)
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
    job->retained = registry.unresolved.emplace(job->type + "\n" + job->operation, job).second;
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
inline void Complete(const std::shared_ptr<CJobCheckpointRecord>& job, bool success)
{
  if(!job || job->unknown)return; // Unknown work still requires its own reviewed contract.
  auto& registry=Get();std::lock_guard<std::mutex> lock(registry.mutex);
  job->phase=success?"completion_receipt_verified":"completed_write_failed";
  registry.pendingReceipts.erase(job->token);
  job->retained=false;
  if(!success) {
    // Keep semantic write/callback failure even if it occurred before Close.
    job->retained=true;
    registry.unresolved[job->type+"\n"+job->operation]=job;
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
    if (!job->required) { ++result.nonPersistent; continue; }
    if (job->unknown) ++result.unknown;
    ++result.required;
    if (result.blockers.size() < 32)
      result.blockers.push_back({job->token, job->jobId, job->required, job->unknown, job->owner, job->operation,
        job->type, job->retained && job.use_count() == 2 && job->phase!="completed_write_failed" ? "completed_without_owner_receipt" : job->phase,
        std::chrono::duration_cast<std::chrono::milliseconds>(now - job->admitted).count()});
  }
  if(registry.receiptOverflow) {
    ++result.required;++result.unknown;
    if(result.blockers.size()<32)result.blockers.push_back({0,0,true,true,"background_jobs",
        "completion_receipt_inventory_limit","JobCheckpoint","completed_write_failed",0});
  }
  return result;
}
} // namespace JobCheckpoint
