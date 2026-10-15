#!/usr/bin/env python3
"""RC2: prune only audited nonpersistent queued jobs before unpausing Kodi's scheduler.

This does not waive Python or database save receipts. A job with any callback,
required completion receipt, or unknown checkpoint contract is never discarded.
"""
from pathlib import Path
import hashlib
import json

CPP="xbmc/utils/JobManager.cpp"
HEADER="xbmc/utils/JobManager.h"
CHECKPOINT="xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"

def replace_once(text, before, after, label):
    if text.count(before)!=1:
        raise ValueError("RC2 unexpected source anchor: "+label+" count="+str(text.count(before)))
    return text.replace(before,after,1)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def apply(source):
    source=Path(source)
    paths={key:source/key for key in (CPP,HEADER,CHECKPOINT)}
    text={key:paths[key].read_text() for key in paths}

    text[HEADER]=replace_once(text[HEADER],
        "  void BeginShutdown();",
        """  void BeginShutdown();
#if defined(TARGET_ANDROID)
  // Eliminate audited, never-started display/cache jobs before releasing the
  // paused queue. Required, unknown and callback-owned jobs remain untouched.
  void PruneCheckpointOptionalQueuedJobs();
#endif""",
        "JobManager checkpoint declaration")

    implementation="""#if defined(TARGET_ANDROID)
void CJobManager::PruneCheckpointOptionalQueuedJobs()
{
  // Do not affect ordinary playback, Home/background, or any failed/retried
  // checkpoint that has not been admitted by the native coordinator.
  if (!InfinityAndroidCheckpoint::IsActive())
    return;
  std::vector<CWorkItem> discarded;
  {
    std::unique_lock<CCriticalSection> lock(m_section);
    for (auto& queue : m_jobQueue)
    {
      for (auto it = queue.begin(); it != queue.end();)
      {
        CJob* job = it->m_job;
        const auto record = job ? job->m_checkpointRecord : nullptr;
        // The cached record already includes exact job implementation/owner
        // classification. Never infer safety from priority or a network URL.
        // Queue-owned callbacks can themselves create essential work, so they
        // must follow the original completion path, not this prune path.
        const bool provenOptional = job && record && !record->required &&
            !record->unknown && it->m_callback == nullptr &&
            !job->RequiresCheckpointCallback() &&
            !job->RequiresCheckpointCompletionReceipt();
        if (!provenOptional)
        {
          ++it;
          continue;
        }
        discarded.push_back(*it);
        it = queue.erase(it);
      }
    }
  }
  // Destruction must occur outside the job-manager lock; it can call back
  // into Kodi. Never fabricate a save receipt for canceled optional work.
  for (auto& item : discarded)
  {
    JobCheckpoint::Phase(item.m_job->m_checkpointRecord,
                         "optional_queued_before_execution_cancelled", item.m_id);
    item.FreeJob();
  }
  if (!discarded.empty())
    InfinityShutdownTrace::Event("milestone", "jobs.optional_queued_pruned",
                                 static_cast<long long>(discarded.size()));
}
#endif

"""
    text[CPP]=replace_once(text[CPP],
        "void CJobManager::BeginShutdown()\n{",
        implementation+"void CJobManager::BeginShutdown()\n{",
        "JobManager optional queue implementation")
    text[CHECKPOINT]=replace_once(text[CHECKPOINT],
        "      CServiceBroker::GetJobManager()->UnPauseJobs(); // Drain previously accepted low-priority work.",
        """      // Eliminate verified nonpersistent work first; otherwise UnPauseJobs
      // needlessly starts queued artwork/weather/cache jobs while closing.
      // Preserve all callback-owned/required jobs and their original drain.
      CServiceBroker::GetJobManager()->PruneCheckpointOptionalQueuedJobs();
      CServiceBroker::GetJobManager()->UnPauseJobs(); // Drain required accepted work.""",
        "checkpoint unpause before optional prune")

    out={}
    for key,path in paths.items():
        path.write_text(text[key])
        out[key]=sha(path)
    return {"changed":sorted(out),"after":out,
            "required_or_unknown_jobs_abandoned":False,
            "checkpoint_save_or_termination_authority_changed":False,
            "only_verified_optional_no_callback_queued":True,
            "active_python_invokers_modified":False,
            "unverified_socket_cancellation_claimed":False}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(apply(a.source),sort_keys=True,indent=2)+"\n")
