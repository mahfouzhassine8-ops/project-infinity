/*
 *  Copyright (C) 2005-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "JobManager.h"

#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityShutdownTrace.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif

#include "ServiceBroker.h"
#include "utils/XTimeUtils.h"
#include "utils/log.h"

#include <algorithm>
#include <functional>
#include <mutex>
#include <stdexcept>
#include <typeinfo>

using namespace std::chrono_literals;

namespace
{
struct CheckpointQueues
{
  std::mutex mutex;
  std::vector<std::weak_ptr<std::atomic<std::size_t>>> queues;
};
CheckpointQueues& QueueRegistry()
{
  static auto* registry = new CheckpointQueues;
  return *registry;
}
}

bool CJob::ShouldCancel(unsigned int progress, unsigned int total) const
{
  if (m_callback)
    return m_callback->OnJobProgress(progress, total, this);
  return false;
}

CJobWorker::CJobWorker(CJobManager *manager) : CThread("JobWorker")
{
  m_jobManager = manager;
  Create(true); // start work immediately, and kill ourselves when we're done
}

CJobWorker::~CJobWorker()
{
  m_jobManager->RemoveWorker(this);
  if(!IsAutoDelete())
    StopThread();
}

void CJobWorker::Process()
{
  SetPriority(ThreadPriority::LOWEST);
  while (true)
  {
    // request an item from our manager (this call is blocking)
    CJob* job = m_jobManager->GetNextJob();
    if (!job)
      break;

    const unsigned int jobId = m_jobManager->GetJobId(job);
    const char* rawJobType = job->GetType();
    const std::string jobType = rawJobType != nullptr ? rawJobType : "";
#if defined(TARGET_ANDROID)
    InfinityShutdownTrace::Scope jobEvidence("jobs.worker_execute", jobId, jobType.c_str());
#endif
    bool success = false;
    try
    {
      success = job->DoWork();
    }
    catch (...)
    {
      CLog::Log(LOGERROR, "{} error processing job {}", __FUNCTION__, jobType);
    }
#if defined(TARGET_ANDROID)
    const std::string checkpointType = typeid(*job).name();
    const bool databaseOwnedJob =
        checkpointType.find("CRepositoryUpdateJob") != std::string::npos ||
        checkpointType.find("CVideoLibraryScanningJob") != std::string::npos;
    if (CJobManager::IsRequiredCheckpointJob(job) && !job->CheckpointSucceeded(success) &&
        !databaseOwnedJob && InfinityAndroidCheckpoint::IsActive())
    {
      const char* operation = job->GetCheckpointOperation();
      const std::string failure = std::string("job_failed:") +
          (operation && *operation ? operation : checkpointType);
      InfinityAndroidCheckpoint::RecordFailure("background_jobs", failure.c_str());
    }
#endif
    m_jobManager->OnJobComplete(success, job);
  }
}

void CJobQueue::CJobPointer::CancelJob()
{
  CServiceBroker::GetJobManager()->CancelJob(m_id);
  m_id = 0;
}

CJobQueue::CJobQueue(bool lifo, unsigned int jobsAtOnce, CJob::PRIORITY priority, const char* checkpointOwner)
: m_jobsAtOnce(jobsAtOnce), m_priority(priority), m_lifo(lifo),
  m_checkpointOwner(checkpointOwner ? checkpointOwner : "")
{
  auto& registry = QueueRegistry();
  std::lock_guard<std::mutex> lock(registry.mutex);
  registry.queues.push_back(m_checkpointCount);
}

CJobQueue::~CJobQueue()
{
  CancelJobs();
}

void CJobQueue::OnJobComplete(unsigned int jobID, bool success, CJob *job)
{
  OnJobNotify(job);
}

void CJobQueue::OnJobAbort(unsigned int jobID, CJob* job)
{
  OnJobNotify(job);
}

void CJobQueue::CancelJob(const CJob *job)
{
  std::unique_lock<CCriticalSection> lock(m_section);
  Processing::iterator i = find(m_processing.begin(), m_processing.end(), job);
  if (i != m_processing.end())
  {
    i->CancelJob();
    m_processing.erase(i);
    UpdateCheckpointCountLocked();
    return;
  }
  Queue::iterator j = find(m_jobQueue.begin(), m_jobQueue.end(), job);
  if (j != m_jobQueue.end())
  {
    j->FreeJob();
    m_jobQueue.erase(j);
  }
  UpdateCheckpointCountLocked();
}

bool CJobQueue::AddJob(CJob *job)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard admission("jobs");
  if (!admission)
  {
    delete job;
    return false;
  }
#endif
  std::unique_lock<CCriticalSection> lock(m_section);
  // check if we have this job already.  If so, we're done.
  if (find(m_jobQueue.begin(), m_jobQueue.end(), job) != m_jobQueue.end() ||
      find(m_processing.begin(), m_processing.end(), job) != m_processing.end())
  {
    delete job;
    return false;
  }

  CJobManager::TrackCheckpointJob(job, this, "queue_pending", m_checkpointOwner);
  if (m_lifo)
    m_jobQueue.emplace_back(job);
  else
    m_jobQueue.emplace_front(job);
  UpdateCheckpointCountLocked();
  QueueNextJob();

  return true;
}

void CJobQueue::OnJobNotify(CJob* job)
{
  std::unique_lock<CCriticalSection> lock(m_section);

  // check if this job is in our processing list
  const auto it = std::find(m_processing.begin(), m_processing.end(), job);
  if (it != m_processing.end())
    m_processing.erase(it);
  // request a new job be queued
  QueueNextJob();
}

void CJobQueue::QueueNextJob()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  while (m_jobQueue.size() && m_processing.size() < m_jobsAtOnce)
  {
    CJobPointer &job = m_jobQueue.back();
    job.m_id = CServiceBroker::GetJobManager()->AddJob(job.m_job, this, m_priority, true);
    if (job.m_id > 0)
    {
      m_processing.emplace_back(job);
      m_jobQueue.pop_back();
      UpdateCheckpointCountLocked();
      return;
    }
    m_jobQueue.pop_back();
  }
  UpdateCheckpointCountLocked();
}

void CJobQueue::CancelJobs()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  for_each(m_processing.begin(), m_processing.end(), [](CJobPointer& jp) { jp.CancelJob(); });
  for_each(m_jobQueue.begin(), m_jobQueue.end(), [](CJobPointer& jp) { jp.FreeJob(); });
  m_jobQueue.clear();
  m_processing.clear();
  UpdateCheckpointCountLocked();
}

void CJobQueue::UpdateCheckpointCountLocked()
{
  m_checkpointCount->store(m_processing.size() + m_jobQueue.size());
}

bool CJobQueue::IsProcessing() const
{
  std::unique_lock<CCriticalSection> lock(m_section);
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive())
    return !m_processing.empty() || !m_jobQueue.empty();
#endif
  return CServiceBroker::GetJobManager()->m_running &&
         (!m_processing.empty() || !m_jobQueue.empty());
}

bool CJobQueue::QueueEmpty() const
{
  std::unique_lock<CCriticalSection> lock(m_section);
  return m_jobQueue.empty();
}

std::size_t CJobQueue::AndroidCheckpointOutstandingQueues()
{
  auto& registry = QueueRegistry();
  std::lock_guard<std::mutex> registryLock(registry.mutex);
  std::size_t count = 0;
  for (auto it = registry.queues.begin(); it != registry.queues.end();)
  {
    if (auto counter = it->lock())
    {
      count += counter->load();
      ++it;
    }
    else
      it = registry.queues.erase(it);
  }
  return count;
}

CJobManager::CJobManager()
{
  m_jobCounter = 0;
  m_running = true;
  m_pauseJobs = false;
}

void CJobManager::Restart()
{
  std::unique_lock<CCriticalSection> lock(m_section);

  if (m_running)
    throw std::logic_error("CJobManager already running");
  m_running = true;
}

unsigned int CJobManager::GetJobId(const CJob* job) const
{
  std::unique_lock<CCriticalSection> lock(m_section);
  const auto it = std::find(m_processing.begin(), m_processing.end(), job);
  return it != m_processing.end() ? it->m_id : 0;
}

void CJobManager::BeginShutdown()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  if (!m_running)
  {
#if defined(TARGET_ANDROID)
    InfinityShutdownTrace::Event("milestone", "jobs.begin_shutdown_repeat",
                                 static_cast<long long>(m_processing.size()));
#endif
    m_jobEvent.Set();
    return;
  }

  m_running = false;
#if defined(TARGET_ANDROID)
  InfinityShutdownTrace::Event("milestone", "jobs.begin_shutdown",
                               static_cast<long long>(m_processing.size()));
#endif

  // Reject new jobs and release work that has not started. Preserve the existing
  // OnJobAbort contract before deleting queued jobs.
  for (unsigned int priority = CJob::PRIORITY_LOW_PAUSABLE;
       priority <= CJob::PRIORITY_DEDICATED; ++priority)
  {
    for (CWorkItem& wi : m_jobQueue[priority])
    {
#if defined(TARGET_ANDROID)
      InfinityShutdownTrace::Event("milestone", "jobs.cancel_queued", wi.m_id,
                                   0, 0, 0,
                                   wi.m_job != nullptr ? wi.m_job->GetType() : nullptr);
#endif
      if (wi.m_callback)
        wi.m_callback->OnJobAbort(wi.m_id, wi.m_job);
      wi.FreeJob();
    }
    m_jobQueue[priority].clear();
  }

  // Jobs already inside DoWork keep their worker and object alive. Remove their
  // client callbacks so ShouldCancel() observes cancellation, but do not detach,
  // delete, force-stop or pretend that the worker completed.
  for (CWorkItem& wi : m_processing)
  {
#if defined(TARGET_ANDROID)
    InfinityShutdownTrace::Event("milestone", "jobs.cancel_active", wi.m_id,
                                 0, 0, 0,
                                 wi.m_job != nullptr ? wi.m_job->GetType() : nullptr);
#endif
    if (wi.m_callback)
      wi.m_callback->OnJobAbort(wi.m_id, wi.m_job);
    wi.Cancel();
  }

  m_jobEvent.Set();
}

void CJobManager::CancelJobs()
{
  // Normal Android close calls BeginShutdown during the cooperative pre-destroy
  // window. This repeat is intentional and keeps the ordinary Kodi contract for
  // every other route while preserving the final worker join below.
  BeginShutdown();

  std::unique_lock<CCriticalSection> lock(m_section);
  auto nextEvidence = std::chrono::steady_clock::now();

  // Final teardown still waits for every JobWorker. Periodic records identify
  // the exact job ID/type and worker TID if a non-cooperative job holds this join.
  while (!m_workers.empty())
  {
#if defined(TARGET_ANDROID)
    const auto now = std::chrono::steady_clock::now();
    if (now >= nextEvidence)
    {
      InfinityShutdownTrace::Event("milestone", "jobs.waiting_workers",
                                   static_cast<long long>(m_workers.size()));
      for (const CWorkItem& wi : m_processing)
      {
        InfinityShutdownTrace::Event("milestone", "jobs.waiting_active", wi.m_id,
                                     0, 0, 0,
                                     wi.m_job != nullptr ? wi.m_job->GetType() : nullptr);
      }
      nextEvidence = now + std::chrono::seconds(1);
    }
#endif
    lock.unlock();
    m_jobEvent.Set();
    std::this_thread::yield();
    lock.lock();
  }

#if defined(TARGET_ANDROID)
  InfinityShutdownTrace::Event("milestone", "jobs.cancel_complete");
#endif
}

unsigned int CJobManager::AddJob(CJob *job, IJobCallback *callback, CJob::PRIORITY priority,
                               bool checkpointPreviouslyAccepted)
{
#if defined(TARGET_ANDROID)
  // Direct admissions need the same lease as queue admissions. A boolean
  // pre-check alone could pass immediately before PREPARE and publish a job
  // after the required-owner snapshot was already empty.
  std::unique_ptr<InfinityAndroidCheckpoint::CheckpointWriteGuard> admission;
  if (!checkpointPreviouslyAccepted)
  {
    admission = std::make_unique<InfinityAndroidCheckpoint::CheckpointWriteGuard>("jobs");
    if (!*admission)
    {
      delete job;
      return 0;
    }
  }
#endif
  std::unique_lock<CCriticalSection> lock(m_section);

#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive() && !checkpointPreviouslyAccepted &&
      !InfinityAndroidCheckpoint::IsPersistingOnThisThread() &&
      !InfinityAndroidCheckpoint::IsAcceptedPlaybackWorkOnThisThread())
  {
    delete job;
    return 0;
  }
#else
  (void)checkpointPreviouslyAccepted;
#endif

  if (!m_running)
  {
    delete job;
    return 0;
  }

  // increment the job counter, ensuring 0 (invalid job) is never hit
  m_jobCounter++;
  if (m_jobCounter == 0)
    m_jobCounter++;

  TrackCheckpointJob(job, callback, "manager_pending");
  TrackCheckpointPhase(job, "manager_pending", m_jobCounter);

  // create a work item for this job
  CWorkItem work(job, m_jobCounter, priority, callback);
  m_jobQueue[priority].push_back(work);

  StartWorkers(priority);
  return work.m_id;
}

void CJobManager::TrackCheckpointJob(CJob* job, IJobCallback* callback, const char* phase,
                                     const std::string& queueOwner)
{
#if defined(TARGET_ANDROID)
  if (!job->m_checkpointRecord)
  {
    auto role = job->GetCheckpointResponsibility(callback);
    std::string owner = queueOwner.empty() ? job->GetCheckpointPersistenceOwner() : queueOwner;
    std::string operation = job->GetCheckpointOperation() ? job->GetCheckpointOperation() : "";
    const std::string actualType = typeid(*job).name();

    // Fold inventory 2103353 exposed the exact remaining stock-Kodi job
    // implementations. Classify only those proven types; every unrecognized
    // implementation remains fail-closed and is retained in the inventory.
    if (queueOwner.empty() && role == CJob::CheckpointResponsibility::Unknown)
    {
      if (actualType.find("CRepositoryUpdateJob") != std::string::npos)
      {
        role = CJob::CheckpointResponsibility::Required;
        owner = "native_databases";
        operation = "repository_update";
      }
      else if (actualType.find("CVideoLibraryScanningJob") != std::string::npos)
      {
        role = CJob::CheckpointResponsibility::Required;
        owner = "native_databases";
        operation = "video_library_scan";
      }
      else if (actualType.find("CApplication10Initialize") != std::string::npos)
      {
        // Startup database/font/add-on initialization is complete long before
        // close in the observed session. If one is still active, wait for it;
        // database writes are independently sealed by native_databases.
        role = CJob::CheckpointResponsibility::Required;
        owner = "native_databases";
        operation = "application_initialize";
      }
      else if (actualType.find("CEventSource") != std::string::npos &&
               actualType.find("Publish") != std::string::npos)
      {
        role = CJob::CheckpointResponsibility::Required;
        owner = "native_admission";
        operation = "event_dispatch";
      }
      else if (actualType.find("CDirectoryJob") != std::string::npos ||
               actualType.find("CWeatherJob") != std::string::npos ||
               actualType.find("CRecentlyAddedJob") != std::string::npos ||
               actualType.find("CImageLoader") != std::string::npos)
      {
        // GUI directory/weather/recently-added work and large-art decoding
        // produce display state or reconstructible caches. Any child Python,
        // database or newly admitted job is independently tracked.
        role = CJob::CheckpointResponsibility::NonPersistent;
        operation = "reconstructible_or_display_job";
      }
    }

    const bool required = !queueOwner.empty() || role != CJob::CheckpointResponsibility::NonPersistent;
    const bool unknown = required && (!InfinityAndroidCheckpoint::IsRequiredOwner(owner) ||
        (queueOwner.empty() && role == CJob::CheckpointResponsibility::Unknown));
    job->m_checkpointRecord = JobCheckpoint::Admit(required, unknown, owner,
        operation, actualType, phase);
  }
#else
  (void)job; (void)callback; (void)phase; (void)queueOwner;
#endif
}
void CJobManager::TrackCheckpointPhase(CJob* job, const char* phase, uint64_t id)
{
  JobCheckpoint::Phase(job->m_checkpointRecord, phase, id);
}
bool CJobManager::IsRequiredCheckpointJob(const CJob* job)
{
  return !job->m_checkpointRecord || job->m_checkpointRecord->required;
}
JobCheckpoint::Snapshot CJobManager::AndroidCheckpointSnapshot()
{
  return JobCheckpoint::GetSnapshot();
}

std::size_t CJobManager::AndroidCheckpointOutstandingJobs() const
{
  std::unique_lock<CCriticalSection> lock(m_section);
  std::size_t count = m_processing.size() + m_checkpointCompletingJobs;
  for (const auto& queue : m_jobQueue)
    count += queue.size();
  return count;
}

void CJobManager::CancelJob(unsigned int jobID)
{
  std::unique_lock<CCriticalSection> lock(m_section);

  // check whether we have this job in the queue
  for (unsigned int priority = CJob::PRIORITY_LOW_PAUSABLE; priority <= CJob::PRIORITY_DEDICATED; ++priority)
  {
    JobQueue::iterator i = find(m_jobQueue[priority].begin(), m_jobQueue[priority].end(), jobID);
    if (i != m_jobQueue[priority].end())
    {
      delete i->m_job;
      m_jobQueue[priority].erase(i);
      return;
    }
  }
  // or if we're processing it
  Processing::iterator it = find(m_processing.begin(), m_processing.end(), jobID);
  if (it != m_processing.end())
    it->m_callback = NULL; // job is in progress, so only thing to do is to remove callback
}

void CJobManager::StartWorkers(CJob::PRIORITY priority)
{
  std::unique_lock<CCriticalSection> lock(m_section);

  // check how many free threads we have
  if (m_processing.size() >= GetMaxWorkers(priority))
    return;

  // do we have any sleeping threads?
  if (m_processing.size() < m_workers.size())
  {
    m_jobEvent.Set();
    return;
  }

  // everyone is busy - we need more workers
  m_workers.push_back(new CJobWorker(this));
}

CJob *CJobManager::PopJob()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  for (int priority = CJob::PRIORITY_DEDICATED; priority >= CJob::PRIORITY_LOW_PAUSABLE; --priority)
  {
    // Check whether we're pausing pausable jobs
    if (priority == CJob::PRIORITY_LOW_PAUSABLE && m_pauseJobs)
      continue;

    if (m_jobQueue[priority].size() && m_processing.size() < GetMaxWorkers(CJob::PRIORITY(priority)))
    {
      // pop the job off the queue
      CWorkItem job = m_jobQueue[priority].front();
      m_jobQueue[priority].pop_front();

      // add to the processing vector
      m_processing.push_back(job);
      job.m_job->m_callback = this;
      TrackCheckpointPhase(job.m_job, "running", job.m_id);
      return job.m_job;
    }
  }
  return NULL;
}

void CJobManager::PauseJobs()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  m_pauseJobs = true;
}

void CJobManager::UnPauseJobs()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  m_pauseJobs = false;
}

bool CJobManager::IsProcessing(const CJob::PRIORITY &priority) const
{
  std::unique_lock<CCriticalSection> lock(m_section);

  if (m_pauseJobs)
    return false;

  for(Processing::const_iterator it = m_processing.begin(); it < m_processing.end(); ++it)
  {
    if (priority == it->m_priority)
      return true;
  }
  return false;
}

int CJobManager::IsProcessing(const std::string &type) const
{
  int jobsMatched = 0;
  std::unique_lock<CCriticalSection> lock(m_section);

  if (m_pauseJobs)
    return 0;

  for(Processing::const_iterator it = m_processing.begin(); it < m_processing.end(); ++it)
  {
    if (type == std::string(it->m_job->GetType()))
      jobsMatched++;
  }
  return jobsMatched;
}

CJob* CJobManager::GetNextJob()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  while (m_running)
  {
    // grab a job off the queue if we have one
    CJob *job = PopJob();
    if (job)
      return job;
    // no jobs are left - sleep for 30 seconds to allow new jobs to come in
    lock.unlock();
    bool newJob = m_jobEvent.Wait(30000ms);
    lock.lock();
    if (!newJob)
      break;
  }
  // ensure no jobs have come in during the period after
  // timeout and before we held the lock
  return PopJob();
}

bool CJobManager::OnJobProgress(unsigned int progress, unsigned int total, const CJob *job) const
{
  std::unique_lock<CCriticalSection> lock(m_section);
  // find the job in the processing queue, and check whether it's cancelled (no callback)
  Processing::const_iterator i = find(m_processing.begin(), m_processing.end(), job);
  if (i != m_processing.end())
  {
    CWorkItem item(*i);
    lock.unlock(); // leave section prior to call
    if (item.m_callback)
    {
      item.m_callback->OnJobProgress(item.m_id, progress, total, job);
      return false;
    }
  }
  return true; // couldn't find the job, or it's been cancelled
}

void CJobManager::OnJobComplete(bool success, CJob *job)
{
  std::unique_lock<CCriticalSection> lock(m_section);
  // remove the job from the processing queue
  Processing::iterator i = find(m_processing.begin(), m_processing.end(), job);
  if (i != m_processing.end())
  {
    // tell any listeners we're done with the job, then delete it
    CWorkItem item(*i);
    TrackCheckpointPhase(job, "callback", item.m_id);
    lock.unlock();
    try
    {
      if (item.m_callback)
        item.m_callback->OnJobComplete(item.m_id, success, item.m_job);
    }
    catch (...)
    {
      CLog::Log(LOGERROR, "{} error processing job {}", __FUNCTION__, item.m_job->GetType());
#if defined(TARGET_ANDROID)
      if (IsRequiredCheckpointJob(item.m_job) && InfinityAndroidCheckpoint::IsActive())
        InfinityAndroidCheckpoint::RecordFailure("background_jobs", "required_job_callback_exception");
#endif
    }
    lock.lock();
    Processing::iterator j = find(m_processing.begin(), m_processing.end(), job);
    if (j != m_processing.end())
      m_processing.erase(j);
    ++m_checkpointCompletingJobs;
    lock.unlock();
    TrackCheckpointPhase(item.m_job, "destructor", item.m_id);
    item.FreeJob();
    lock.lock();
    --m_checkpointCompletingJobs;
  }
}

void CJobManager::RemoveWorker(const CJobWorker *worker)
{
  std::unique_lock<CCriticalSection> lock(m_section);
  // remove our worker
  Workers::iterator i = find(m_workers.begin(), m_workers.end(), worker);
  if (i != m_workers.end())
  {
#if defined(TARGET_ANDROID)
    InfinityShutdownTrace::Event("milestone", "jobs.worker_removed",
                                 static_cast<long long>(m_workers.size()));
#endif
    m_workers.erase(i); // workers auto-delete
  }
}

unsigned int CJobManager::GetMaxWorkers(CJob::PRIORITY priority)
{
  static const unsigned int max_workers = 5;
  if (priority == CJob::PRIORITY_DEDICATED)
    return 10000; // A large number..
  return max_workers - (CJob::PRIORITY_HIGH - priority);
}
